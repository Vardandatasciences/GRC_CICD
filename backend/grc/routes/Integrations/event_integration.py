from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import json
import logging

from ...models import ExternalApplication, ExternalApplicationConnection, ExternalApplicationSyncLog, Users
from .jira_backend import jira_backend

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def test_integration_auth(request):
    """
    Test endpoint to verify authentication is working for integrations
    """
    try:
        logger.info(f"Test integration auth request: {request.method} {request.path}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Get user from middleware (set by JWT middleware)
        user = getattr(request, 'user', None)
        logger.info(f"User from middleware: {user}")
        
        if not user:
            logger.warning("No user found in request - authentication required")
            return JsonResponse({
                'status': 'error',
                'message': 'Authentication required',
                'debug': {
                    'headers': dict(request.headers),
                    'path': request.path,
                    'method': request.method
                }
            }, status=401)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Authentication working',
            'user': {
                'id': user.UserId,
                'username': user.UserName,
                'email': user.Email
            }
        })
        
    except Exception as e:
        logger.error(f"Test integration auth error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Test failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_external_applications(request):
    """
    Get all external applications with their connection status for the current user
    """
    try:
        # Debug logging
        logger.info(f"External applications request: {request.method} {request.path}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Get user ID from request (default to 1 for demo purposes)
        user_id = request.GET.get('user_id', 1)
        logger.info(f"Getting external applications for user_id: {user_id}")
        
        # Get all active external applications
        applications = ExternalApplication.objects.filter(is_active=True).order_by('name')
        logger.info(f"Found {applications.count()} active external applications")
        
        applications_data = []
        connected_count = 0
        
        for app in applications:
            # Check if user has an active connection to this application
            connection = ExternalApplicationConnection.objects.filter(
                application=app,
                user_id=user_id,
                connection_status='active'
            ).first()
            
            # Determine connection status and last sync
            if connection:
                connection_status = 'connected'
                last_sync = connection.last_used or connection.created_at
                connected_count += 1
                logger.info(f"User {user_id} has active connection to {app.name}")
            else:
                connection_status = 'disconnected'
                last_sync = None
                logger.info(f"User {user_id} has no connection to {app.name}")

            app_data = {
                'id': app.id,
                'name': app.name,
                'category': app.category,
                'type': app.type,
                'description': app.description,
                'icon': app.icon_class,
                'version': app.version,
                'status': connection_status,
                'lastSync': last_sync.isoformat() if last_sync else None,
                'features': app.features or [],
                'api_endpoint': app.api_endpoint,
                'oauth_url': app.oauth_url
            }
            applications_data.append(app_data)

        # Calculate statistics
        total_apps = len(applications_data)
        disconnected_apps = total_apps - connected_count

        logger.info(f"Returning {total_apps} applications: {connected_count} connected, {disconnected_apps} disconnected")

        return JsonResponse({
            'success': True,
            'applications': applications_data,
            'statistics': {
                'total': total_apps,
                'connected': connected_count,
                'disconnected': disconnected_apps
            }
        })

    except Exception as e:
        logger.error(f"Error getting external applications: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def connect_external_application(request):
    """
    Connect to an external application
    """
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        connection_token = data.get('connection_token')
        refresh_token = data.get('refresh_token')
        token_expires_at = data.get('token_expires_at')
        user_id = data.get('user_id', 1)  # Default to user 1 for demo

        if not application_id:
            return JsonResponse({'error': 'Application ID is required'}, status=400)

        try:
            application = ExternalApplication.objects.get(id=application_id, is_active=True)
        except ExternalApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)

        # Get user by ID
        try:
            user = Users.objects.get(UserId=user_id)
        except Users.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

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

        return JsonResponse({
            'success': True,
            'message': f'Successfully connected to {application.name}',
            'connection_id': connection.id
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error connecting to external application: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def disconnect_external_application(request):
    """
    Disconnect from an external application
    """
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        user_id = data.get('user_id', 1)  # Default to user 1 for demo

        if not application_id:
            return JsonResponse({'error': 'Application ID is required'}, status=400)

        try:
            application = ExternalApplication.objects.get(id=application_id, is_active=True)
            user = Users.objects.get(UserId=user_id)
            connection = ExternalApplicationConnection.objects.get(
                application=application,
                user=user,
                connection_status='active'
            )
        except (ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist, Users.DoesNotExist):
            return JsonResponse({'error': 'Connection not found'}, status=404)

        with transaction.atomic():
            # Update connection status
            connection.connection_status = 'revoked'
            connection.save()

            # Update application status if no other active connections
            active_connections = ExternalApplicationConnection.objects.filter(
                application=application,
                connection_status='active'
            ).count()

            if active_connections == 0:
                application.status = 'disconnected'
                application.save()

            # Log the disconnection
            ExternalApplicationSyncLog.objects.create(
                application=application,
                user=user,
                sync_type='manual',
                sync_status='success',
                records_synced=0,
                sync_started_at=timezone.now(),
                sync_completed_at=timezone.now(),
                error_message='User disconnected'
            )

        return JsonResponse({
            'success': True,
            'message': f'Successfully disconnected from {application.name}'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error disconnecting from external application: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_application_details(request, application_id):
    """
    Get detailed information about a specific external application
    """
    try:
        # Get user from middleware (set by JWT middleware)
        user = getattr(request, 'user', None)
        
        # Check if user is authenticated and is a Users model instance
        is_authenticated = user and hasattr(user, 'UserId') and not user.is_anonymous

        try:
            application = ExternalApplication.objects.get(id=application_id, is_active=True)
        except ExternalApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)

        # Get user's connection status (only if authenticated)
        if is_authenticated:
            try:
                connection = ExternalApplicationConnection.objects.get(
                    application=application,
                    user=user,
                    connection_status='active'
                )
                connection_status = 'connected'
                last_used = connection.last_used
                token_expires_at = connection.token_expires_at
            except ExternalApplicationConnection.DoesNotExist:
                connection_status = 'disconnected'
                last_used = None
                token_expires_at = None

            # Get recent sync logs
            recent_syncs = ExternalApplicationSyncLog.objects.filter(
                application=application,
                user=user
            ).order_by('-sync_started_at')[:5]
        else:
            # Default values when not authenticated
            connection_status = 'disconnected'
            last_used = None
            token_expires_at = None
            recent_syncs = []

        sync_logs = []
        for sync in recent_syncs:
            sync_logs.append({
                'id': sync.id,
                'sync_type': sync.get_sync_type_display(),
                'sync_status': sync.get_sync_status_display(),
                'records_synced': sync.records_synced,
                'sync_started_at': sync.sync_started_at.isoformat(),
                'sync_completed_at': sync.sync_completed_at.isoformat() if sync.sync_completed_at else None,
                'duration_seconds': sync.duration_seconds,
                'error_message': sync.error_message
            })

        application_data = {
            'id': application.id,
            'name': application.name,
            'category': application.category,
            'type': application.type,
            'description': application.description,
            'icon': application.icon_class,
            'version': application.version,
            'status': connection_status,
            'lastSync': last_used.isoformat() if last_used else None,
            'features': application.features or [],
            'api_endpoint': application.api_endpoint,
            'oauth_url': application.oauth_url,
            'created_at': application.created_at.isoformat(),
            'updated_at': application.updated_at.isoformat(),
            'token_expires_at': token_expires_at.isoformat() if token_expires_at else None,
            'recent_syncs': sync_logs
        }

        return JsonResponse({
            'success': True,
            'application': application_data
        })

    except Exception as e:
        logger.error(f"Error getting application details: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_application_status(request):
    """
    Refresh the status of all external applications for the current user
    """
    try:
        # Get user from middleware (set by JWT middleware)
        user = getattr(request, 'user', None)
        
        # Check if user is authenticated and is a Users model instance
        if not user or not hasattr(user, 'UserId') or user.is_anonymous:
            # Simplified response when not authenticated
            return JsonResponse({
                'success': True,
                'message': 'Status refresh completed (simplified mode - no authentication)',
                'refreshed_count': 0
            })

        # Get all user's active connections
        connections = ExternalApplicationConnection.objects.filter(
            user=user,
            connection_status='active'
        ).select_related('application')

        refreshed_count = 0
        for connection in connections:
            # Check if token is expired
            if connection.is_token_expired():
                connection.connection_status = 'expired'
                connection.save()
                
                # Update application status if no other active connections
                active_connections = ExternalApplicationConnection.objects.filter(
                    application=connection.application,
                    connection_status='active'
                ).count()
                
                if active_connections == 0:
                    connection.application.status = 'disconnected'
                    connection.application.save()
            else:
                refreshed_count += 1

        return JsonResponse({
            'success': True,
            'message': f'Refreshed {refreshed_count} active connections',
            'refreshed_count': refreshed_count
        })

    except Exception as e:
        logger.error(f"Error refreshing application status: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_sync_logs(request, application_id):
    """
    Get sync logs for a specific external application
    """
    try:
        # Get user from middleware (set by JWT middleware)
        user = getattr(request, 'user', None)
        
        # Check if user is authenticated and is a Users model instance
        if not user or not hasattr(user, 'UserId') or user.is_anonymous:
            # Simplified response when not authenticated
            return JsonResponse({
                'success': True,
                'sync_logs': [],
                'total_count': 0
            })

        try:
            application = ExternalApplication.objects.get(id=application_id, is_active=True)
        except ExternalApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)

        # Get sync logs for this application and user
        sync_logs = ExternalApplicationSyncLog.objects.filter(
            application=application,
            user=user
        ).order_by('-sync_started_at')

        logs_data = []
        for sync in sync_logs:
            logs_data.append({
                'id': sync.id,
                'sync_type': sync.get_sync_type_display(),
                'sync_status': sync.get_sync_status_display(),
                'records_synced': sync.records_synced,
                'sync_started_at': sync.sync_started_at.isoformat(),
                'sync_completed_at': sync.sync_completed_at.isoformat() if sync.sync_completed_at else None,
                'duration_seconds': sync.duration_seconds,
                'error_message': sync.error_message
            })

        return JsonResponse({
            'success': True,
            'sync_logs': logs_data,
            'total_count': len(logs_data)
        })

    except Exception as e:
        logger.error(f"Error getting sync logs: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# Jira-specific endpoints
@csrf_exempt
@require_http_methods(["POST"])
def jira_oauth_callback(request):
    """
    Handle Jira OAuth callback and create connection
    """
    try:
        logger.info("Jira OAuth callback received")

        data = json.loads(request.body)
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        expires_in = data.get('expires_in')
        user_id = data.get('user_id', 1)  # Default to user ID 1 if not provided
        jira_account_info = data.get('account_info')  # Optional Jira account information

        if not access_token:
            return JsonResponse({'error': 'Access token is required'}, status=400)

        # Calculate token expiration
        token_expires_at = None
        if expires_in:
            token_expires_at = timezone.now() + timezone.timedelta(seconds=int(expires_in))

        # Save Jira connection using backend manager
        result = jira_backend.save_jira_connection(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            jira_account_info=jira_account_info
        )

        if result['success']:
            logger.info(f"Jira OAuth callback processed successfully for user {user_id}")
            return JsonResponse({
                'success': True,
                'message': 'Jira OAuth callback processed successfully',
                'application': 'Jira',
                'connection_id': result.get('connection_id'),
                'created': result.get('created', False)
            })
        else:
            logger.error(f"Failed to save Jira connection: {result['error']}")
            return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error handling Jira OAuth callback: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def get_jira_projects(request):
    """
    Get Jira projects and optionally save them to database
    """
    try:
        if request.method == 'GET':
            # Get projects from database or return mock data
            logger.info("Getting Jira projects")
            
            # For now, return mock data (can be enhanced to fetch from database)
            projects = [
                {
                    'id': '10001',
                    'key': 'PROJ1',
                    'name': 'Sample Project 1',
                    'projectTypeKey': 'software',
                    'description': 'A sample software project'
                },
                {
                    'id': '10002',
                    'key': 'PROJ2',
                    'name': 'Sample Project 2',
                    'projectTypeKey': 'business',
                    'description': 'A sample business project'
                }
            ]

            return JsonResponse({
                'success': True,
                'projects': projects,
                'message': 'Jira projects retrieved successfully'
            })
        
        elif request.method == 'POST':
            # Save projects data to database
            logger.info("Saving Jira projects to database")
            
            data = json.loads(request.body)
            projects_data = data.get('projects', [])
            user_id = data.get('user_id', 1)  # Default to user ID 1 if not provided
            
            if not projects_data:
                return JsonResponse({'error': 'Projects data is required'}, status=400)
            
            # Save projects using backend manager
            result = jira_backend.save_jira_projects(
                user_id=user_id,
                projects_data=projects_data
            )
            
            if result['success']:
                logger.info(f"Successfully saved {result['projects_count']} Jira projects for user {user_id}")
                return JsonResponse({
                    'success': True,
                    'message': result['message'],
                    'projects_count': result['projects_count']
                })
            else:
                logger.error(f"Failed to save Jira projects: {result['error']}")
                return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error handling Jira projects: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_jira_project_details(request):
    """
    Save detailed Jira project information
    """
    try:
        logger.info("Saving Jira project details")
        
        data = json.loads(request.body)
        project_id = data.get('project_id')
        project_details = data.get('project_details')
        user_id = data.get('user_id', 1)  # Default to user ID 1 if not provided
        
        if not project_id or not project_details:
            return JsonResponse({'error': 'Project ID and project details are required'}, status=400)
        
        # Save project details using backend manager
        result = jira_backend.save_jira_project_details(
            user_id=user_id,
            project_id=project_id,
            project_details=project_details
        )
        
        if result['success']:
            logger.info(f"Successfully saved Jira project details for project {project_id}, user {user_id}")
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'project_id': result['project_id']
            })
        else:
            logger.error(f"Failed to save Jira project details: {result['error']}")
            return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error saving Jira project details: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def disconnect_jira(request):
    """
    Disconnect Jira for a user
    """
    try:
        logger.info("Disconnecting Jira")
        
        data = json.loads(request.body)
        user_id = data.get('user_id', 1)  # Default to user ID 1 if not provided
        
        # Disconnect Jira using backend manager
        result = jira_backend.disconnect_jira(user_id=user_id)
        
        if result['success']:
            logger.info(f"Successfully disconnected Jira for user {user_id}")
            return JsonResponse({
                'success': True,
                'message': result['message']
            })
        else:
            logger.error(f"Failed to disconnect Jira: {result['error']}")
            return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error disconnecting Jira: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_jira_connection_status(request):
    """
    Get Jira connection status for a user
    """
    try:
        user_id = request.GET.get('user_id', 1)  # Default to user ID 1 if not provided
        
        # Get connection status using backend manager
        result = jira_backend.get_jira_connection_status(user_id=user_id)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'connected': result['connected'],
                'connection_id': result.get('connection_id'),
                'last_used': result.get('last_used'),
                'token_expires_at': result.get('token_expires_at'),
                'is_token_expired': result.get('is_token_expired', False)
            })
        else:
            return JsonResponse({'error': result['error']}, status=400)

    except Exception as e:
        logger.error(f"Error getting Jira connection status: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_jira_data(request):
    """
    Get all Jira data for a user (projects, configuration, etc.)
    """
    try:
        user_id = request.GET.get('user_id', 1)  # Default to user ID 1 if not provided
        
        # Get Jira data using backend manager
        result = jira_backend.get_jira_data(user_id=user_id)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'application': result['application'],
                'connection': result['connection']
            })
        else:
            return JsonResponse({'error': result['error']}, status=400)

    except Exception as e:
        logger.error(f"Error getting Jira data: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_stored_projects_data(request):
    """
    Get stored projects data from database for a user
    """
    try:
        user_id = request.GET.get('user_id', 1)  # Default to user ID 1 if not provided
        
        result = jira_backend.get_stored_projects_data(user_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error getting stored projects data: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_jira_project_details_from_db(request):
    """
    Get Jira project details from database for a user
    """
    try:
        user_id = request.GET.get('user_id', 1)  # Default to user ID 1 if not provided
        project_id = request.GET.get('project_id')
        
        if not project_id:
            return JsonResponse({'error': 'project_id parameter is required'}, status=400)
        
        result = jira_backend.get_jira_project_details(user_id, project_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error getting Jira project details: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_all_users(request):
    """
    Get all active users from the database
    """
    try:
        result = jira_backend.get_all_users()
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def assign_project_to_users(request):
    """
    Assign a Jira project to selected users
    """
    try:
        data = json.loads(request.body)
        
        assigned_by_user_id = data.get('assigned_by_user_id')
        project_data = data.get('project_data')
        selected_users = data.get('selected_users', [])
        
        if not assigned_by_user_id:
            return JsonResponse({'error': 'assigned_by_user_id is required'}, status=400)
        
        if not project_data:
            return JsonResponse({'error': 'project_data is required'}, status=400)
        
        if not selected_users:
            return JsonResponse({'error': 'selected_users is required'}, status=400)
        
        result = jira_backend.assign_project_to_users(
            assigned_by_user_id=assigned_by_user_id,
            project_data=project_data,
            selected_users=selected_users
        )
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error assigning project to users: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_project_assignments(request):
    """
    Get project assignments
    """
    try:
        user_id = request.GET.get('user_id')
        project_id = request.GET.get('project_id')
        
        result = jira_backend.get_project_assignments(
            user_id=user_id,
            project_id=project_id
        )
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error getting project assignments: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
