"""
Database Update Utilities for External Integrations

This module provides utilities for updating external integration statuses
in the database, including disconnect operations.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import json
import logging

from ...models import ExternalApplication, ExternalApplicationConnection, ExternalApplicationSyncLog, Users

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def disconnect_integration(request):
    """
    Disconnect from any external integration and update database
    
    This is a generic disconnect function that can handle any integration type
    """
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        application_name = data.get('application_name')  # Alternative to application_id
        user_id = data.get('user_id', 1)
        
        logger.info(f"Disconnect request: app_id={application_id}, app_name={application_name}, user_id={user_id}")
        
        if not application_id and not application_name:
            return JsonResponse({'error': 'Application ID or name is required'}, status=400)
        
        # Get application by ID or name
        try:
            if application_id:
                application = ExternalApplication.objects.get(id=application_id, is_active=True)
            else:
                application = ExternalApplication.objects.get(name=application_name, is_active=True)
        except ExternalApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)
        
        # Get user
        try:
            user = Users.objects.get(UserId=user_id)
        except Users.DoesNotExist:
            return JsonResponse({'error': f'User with ID {user_id} not found'}, status=404)
        
        with transaction.atomic():
            # Get all active connections for this user and application
            connections = ExternalApplicationConnection.objects.filter(
                application=application,
                user=user,
                connection_status='active'
            )
            
            if not connections.exists():
                logger.warning(f"No active connections found for {application.name} and user {user_id}")
                return JsonResponse({
                    'success': True,
                    'message': f'No active connection found for {application.name}',
                    'already_disconnected': True
                })
            
            # Revoke all active connections
            revoked_count = 0
            for connection in connections:
                connection.connection_status = 'revoked'
                connection.save()
                revoked_count += 1
                logger.info(f"Revoked connection {connection.id} for {application.name}")
            
            # Check if there are any other active connections for this application
            remaining_active_connections = ExternalApplicationConnection.objects.filter(
                application=application,
                connection_status='active'
            ).count()
            
            # If no active connections remain, update application status
            if remaining_active_connections == 0:
                application.status = 'disconnected'
                application.save()
                logger.info(f"Updated {application.name} status to disconnected")
            
            # Log the disconnection
            ExternalApplicationSyncLog.objects.create(
                application=application,
                user=user,
                sync_type='manual',
                sync_status='success',
                records_synced=0,
                sync_started_at=timezone.now(),
                sync_completed_at=timezone.now(),
                error_message=f'User disconnected - {revoked_count} connections revoked'
            )
            
            logger.info(f"Successfully disconnected {application.name} for user {user_id} - {revoked_count} connections revoked")
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully disconnected from {application.name}',
                'connections_revoked': revoked_count,
                'application_status': application.status
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error disconnecting integration: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def connect_integration(request):
    """
    Connect to any external integration and update database
    
    This is a generic connect function that can handle any integration type
    """
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        application_name = data.get('application_name')  # Alternative to application_id
        user_id = data.get('user_id', 1)
        connection_token = data.get('connection_token', '')
        refresh_token = data.get('refresh_token', '')
        token_expires_at = data.get('token_expires_at')
        
        logger.info(f"Connect request: app_id={application_id}, app_name={application_name}, user_id={user_id}")
        
        if not application_id and not application_name:
            return JsonResponse({'error': 'Application ID or name is required'}, status=400)
        
        # Get application by ID or name
        try:
            if application_id:
                application = ExternalApplication.objects.get(id=application_id, is_active=True)
            else:
                application = ExternalApplication.objects.get(name=application_name, is_active=True)
        except ExternalApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)
        
        # Get user
        try:
            user = Users.objects.get(UserId=user_id)
        except Users.DoesNotExist:
            return JsonResponse({'error': f'User with ID {user_id} not found'}, status=404)
        
        with transaction.atomic():
            # Create or update connection
            connection, created = ExternalApplicationConnection.objects.update_or_create(
                application=application,
                user=user,
                defaults={
                    'connection_token': connection_token,
                    'refresh_token': refresh_token,
                    'token_expires_at': timezone.datetime.fromisoformat(token_expires_at) if token_expires_at else None,
                    'connection_status': 'active',
                    'last_used': timezone.now()
                }
            )
            
            # Update application status
            application.status = 'connected'
            application.last_sync = timezone.now()
            application.save()
            
            # Log the connection
            ExternalApplicationSyncLog.objects.create(
                application=application,
                user=user,
                sync_type='manual',
                sync_status='success',
                records_synced=1,
                sync_started_at=timezone.now(),
                sync_completed_at=timezone.now()
            )
            
            action = 'created' if created else 'updated'
            logger.info(f"Successfully {action} connection for {application.name} and user {user_id}")
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully connected to {application.name}',
                'connection_id': connection.id,
                'created': created,
                'application_status': application.status
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error connecting integration: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_integration_status(request):
    """
    Get the connection status for any integration
    """
    try:
        application_id = request.GET.get('application_id')
        application_name = request.GET.get('application_name')
        user_id = request.GET.get('user_id', 1)
        
        if not application_id and not application_name:
            return JsonResponse({'error': 'Application ID or name is required'}, status=400)
        
        # Get application by ID or name
        try:
            if application_id:
                application = ExternalApplication.objects.get(id=application_id, is_active=True)
            else:
                application = ExternalApplication.objects.get(name=application_name, is_active=True)
        except ExternalApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)
        
        # Get user
        try:
            user = Users.objects.get(UserId=user_id)
        except Users.DoesNotExist:
            return JsonResponse({'error': f'User with ID {user_id} not found'}, status=404)
        
        # Check connection status
        connection = ExternalApplicationConnection.objects.filter(
            application=application,
            user=user,
            connection_status='active'
        ).first()
        
        if connection:
            return JsonResponse({
                'success': True,
                'connected': True,
                'application_name': application.name,
                'connection_id': connection.id,
                'last_used': connection.last_used.isoformat() if connection.last_used else None,
                'token_expires_at': connection.token_expires_at.isoformat() if connection.token_expires_at else None,
                'is_token_expired': connection.is_token_expired() if hasattr(connection, 'is_token_expired') else False
            })
        else:
            return JsonResponse({
                'success': True,
                'connected': False,
                'application_name': application.name,
                'message': 'No active connection found'
            })
            
    except Exception as e:
        logger.error(f"Error getting integration status: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def bulk_update_integration_status(request):
    """
    Bulk update integration statuses for multiple applications
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id', 1)
        updates = data.get('updates', [])  # List of {application_id, status, connection_token, etc.}
        
        if not updates:
            return JsonResponse({'error': 'Updates list is required'}, status=400)
        
        results = []
        
        with transaction.atomic():
            for update in updates:
                application_id = update.get('application_id')
                application_name = update.get('application_name')
                status = update.get('status')  # 'connected' or 'disconnected'
                connection_token = update.get('connection_token', '')
                refresh_token = update.get('refresh_token', '')
                token_expires_at = update.get('token_expires_at')
                
                try:
                    # Get application
                    if application_id:
                        application = ExternalApplication.objects.get(id=application_id, is_active=True)
                    else:
                        application = ExternalApplication.objects.get(name=application_name, is_active=True)
                    
                    # Get user
                    user = Users.objects.get(UserId=user_id)
                    
                    if status == 'connected':
                        # Create or update connection
                        connection, created = ExternalApplicationConnection.objects.update_or_create(
                            application=application,
                            user=user,
                            defaults={
                                'connection_token': connection_token,
                                'refresh_token': refresh_token,
                                'token_expires_at': timezone.datetime.fromisoformat(token_expires_at) if token_expires_at else None,
                                'connection_status': 'active',
                                'last_used': timezone.now()
                            }
                        )
                        
                        application.status = 'connected'
                        application.last_sync = timezone.now()
                        application.save()
                        
                        results.append({
                            'application_name': application.name,
                            'status': 'connected',
                            'success': True,
                            'connection_id': connection.id,
                            'created': created
                        })
                        
                    elif status == 'disconnected':
                        # Revoke connections
                        connections = ExternalApplicationConnection.objects.filter(
                            application=application,
                            user=user,
                            connection_status='active'
                        )
                        
                        revoked_count = 0
                        for connection in connections:
                            connection.connection_status = 'revoked'
                            connection.save()
                            revoked_count += 1
                        
                        # Check if no other active connections
                        remaining_active = ExternalApplicationConnection.objects.filter(
                            application=application,
                            connection_status='active'
                        ).count()
                        
                        if remaining_active == 0:
                            application.status = 'disconnected'
                            application.save()
                        
                        results.append({
                            'application_name': application.name,
                            'status': 'disconnected',
                            'success': True,
                            'connections_revoked': revoked_count
                        })
                    
                except Exception as e:
                    logger.error(f"Error updating {application_name or application_id}: {str(e)}")
                    results.append({
                        'application_name': application_name or f'ID:{application_id}',
                        'status': status,
                        'success': False,
                        'error': str(e)
                    })
        
        return JsonResponse({
            'success': True,
            'message': f'Bulk update completed for {len(updates)} applications',
            'results': results
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
