"""
Policy Acknowledgement Routes
Handles all operations related to policy acknowledgements
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date
import secrets
import os

from ...models import (
    Policy, PolicyAcknowledgementRequest, PolicyAcknowledgementUser,
    Users, GRCLog
)
from ..Global.logging_service import send_log


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def mark_acknowledgement_notification_as_read(user_id, policy_name, acknowledgement_request_id=None):
    """
    Mark acknowledgement notification as read when policy is acknowledged
    """
    try:
        from ...routes.Global.notifications import notifications_storage
        from datetime import datetime
        
        # Find and mark matching acknowledgement notifications as read
        marked_count = 0
        for notification in notifications_storage:
            if (notification.get('user_id') == str(user_id) and 
                not notification['status'].get('isRead', False)):
                
                # Check if this is an acknowledgement notification for this policy
                title = notification.get('title', '')
                message = notification.get('message', '')
                
                is_acknowledgement = (
                    'Acknowledgement Request' in title or 
                    'Policy Acknowledgement' in title
                )
                
                # Match by policy name in message or title
                matches_policy = (
                    policy_name.lower() in message.lower() or
                    policy_name.lower() in title.lower()
                )
                
                if is_acknowledgement and matches_policy:
                    notification['status']['isRead'] = True
                    notification['status']['readAt'] = datetime.now().isoformat()
                    marked_count += 1
                    print(f"✅ Marked notification {notification.get('id')} as read for policy '{policy_name}'")
        
        return marked_count
    except Exception as e:
        print(f"Error marking acknowledgement notification as read: {str(e)}")
        return 0


@api_view(['POST'])
@permission_classes([])  # Empty list = no permission check
@csrf_exempt
def create_acknowledgement_request(request):
    """
    Create a new policy acknowledgement request
    
    Request body:
    {
        "policy_id": 1,
        "policy_version": "1.0",
        "title": "Acknowledge Updated Security Policy",
        "description": "Please review and acknowledge...",
        "due_date": "2025-12-31",  // optional
        "target_user_ids": [1, 2, 3],
        "target_groups": ["Compliance Team"],  // optional
        "send_notifications": true  // optional
    }
    """
    print(f"DEBUG: create_acknowledgement_request called - Method: {request.method}, Path: {request.path}")
    print(f"DEBUG: User: {request.user if hasattr(request, 'user') else 'No user'}")
    print(f"DEBUG: Data: {request.data if hasattr(request, 'data') else 'No data'}")
    
    try:
        data = request.data
        policy_id = data.get('policy_id')
        
        # Validate policy exists
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Get current user - handle multiple ways user might be set
        user_id = None
        if hasattr(request, 'user') and request.user:
            user_id = getattr(request.user, 'UserId', None) or getattr(request.user, 'id', None)
        
        # If no user_id from request.user, try to get from JWT or session
        if not user_id:
            # Try to get from JWT token in header
            auth_header = request.headers.get('Authorization', '')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    token = auth_header.split(' ')[1]
                    from ...authentication import verify_jwt_token
                    payload = verify_jwt_token(token)
                    if payload and 'user_id' in payload:
                        user_id = payload['user_id']
                except:
                    pass
        
        # If still no user_id, try session
        if not user_id and hasattr(request, 'session'):
            user_id = request.session.get('user_id') or request.session.get('grc_user_id')
        
        if not user_id:
            return Response({
                'error': 'User not authenticated. Please login again.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = get_object_or_404(Users, UserId=user_id)
        
        # Get policy version (use current if not provided)
        policy_version = data.get('policy_version', policy.CurrentVersion)
        
        # Get target users and manual email
        target_user_ids = data.get('target_user_ids', [])
        manual_email_raw = data.get('manual_email')
        
        # Handle manual_email: support both string (single email) and list (multiple emails)
        manual_emails = []
        if manual_email_raw:
            if isinstance(manual_email_raw, list):
                # Already a list, use as is and remove duplicates
                manual_emails = list(set([email.strip() for email in manual_email_raw if email and email.strip()]))
            elif isinstance(manual_email_raw, str):
                # Single email string, convert to list for backward compatibility
                manual_emails = [manual_email_raw.strip()] if manual_email_raw.strip() else []
        
        # Validate: either target_user_ids or manual_emails must be provided
        if not target_user_ids and not manual_emails:
            return Response({
                'error': 'Either target_user_ids or manual_email must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate email format for all manual emails
        if manual_emails:
            import re
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            invalid_emails = [email for email in manual_emails if not re.match(email_pattern, email)]
            if invalid_emails:
                return Response({
                    'error': f'Invalid email format(s): {", ".join(invalid_emails)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate all target users exist (if provided)
        if target_user_ids:
            valid_users = Users.objects.filter(UserId__in=target_user_ids, IsActive='Y')
            if valid_users.count() != len(target_user_ids):
                return Response({
                    'error': 'Some target users do not exist or are inactive'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle manual emails: find or create users for each email
        manual_users = []
        if manual_emails:
            # Get a default framework (use the policy's framework or first available)
            default_framework = policy.FrameworkId
            if not default_framework:
                from ...models import Framework
                default_framework = Framework.objects.first()
                if not default_framework:
                    return Response({
                        'error': 'No framework available. Cannot create user for manual email.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            for manual_email in manual_emails:
                # Check if we already have this user in manual_users (avoid duplicates)
                existing_manual_user = next((mu for mu in manual_users if mu.Email == manual_email), None)
                if existing_manual_user:
                    print(f"User for email {manual_email} already processed (UserId: {existing_manual_user.UserId})")
                    continue
                
                # Try to find existing user by email
                try:
                    manual_user = Users.objects.get(Email=manual_email, IsActive='Y')
                    manual_users.append(manual_user)
                    print(f"Found existing user for manual email: {manual_email} (UserId: {manual_user.UserId})")
                except Users.DoesNotExist:
                    # User doesn't exist, create a minimal user record
                    try:
                        manual_user = Users.objects.create(
                            UserName=manual_email.split('@')[0],  # Use email prefix as username
                            Email=manual_email,
                            FirstName=manual_email.split('@')[0],
                            LastName='',
                            Password='',  # No password for external users
                            IsActive='Y',
                            DepartmentId='0',  # Default to '0' for manual email users
                            FrameworkId=default_framework
                        )
                        manual_users.append(manual_user)
                        print(f"Created user record for manual email: {manual_email} (UserId: {manual_user.UserId})")
                    except Exception as e:
                        print(f"Error creating user for email {manual_email}: {str(e)}")
                        return Response({
                            'error': f'Error creating user for email {manual_email}: {str(e)}'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Parse due date if provided
        due_date = None
        if data.get('due_date'):
            try:
                # Parse the date string and convert to date object
                parsed_datetime = datetime.strptime(data['due_date'], '%Y-%m-%d')
                due_date = parsed_datetime.date()
            except (ValueError, TypeError) as e:
                return Response({
                    'error': f'Invalid due_date format. Use YYYY-MM-DD. Error: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate total users (database users + manual email users if provided)
        # Filter out any manual user IDs that are already in target_user_ids to avoid duplicates
        manual_user_ids = [mu.UserId for mu in manual_users if mu.UserId not in target_user_ids]
        total_users = len(target_user_ids) + len(manual_user_ids)
        
        # Create acknowledgement request
        ack_request = PolicyAcknowledgementRequest.objects.create(
            PolicyId=policy,
            PolicyVersion=policy_version,
            Title=data.get('title', f'Acknowledge {policy.PolicyName}'),
            Description=data.get('description', ''),
            DueDate=due_date,
            TargetUserIds=target_user_ids + manual_user_ids,
            TargetGroups=data.get('target_groups', []),
            TotalUsers=total_users,
            CreatedBy=user,
            FrameworkId=policy.FrameworkId
        )
        
        # Create individual user acknowledgement records with unique tokens
        user_acks = []
        
        # Add database users
        for target_user_id in target_user_ids:
            target_user = Users.objects.get(UserId=target_user_id)
            
            # Generate unique token for external access
            unique_token = secrets.token_urlsafe(32)
            
            user_ack = PolicyAcknowledgementUser.objects.create(
                AcknowledgementRequest=ack_request,
                UserId=target_user,
                Token=unique_token
            )
            user_acks.append(user_ack)
        
        # Add manual email users if provided (only those not already in target_user_ids)
        for manual_user in manual_users:
            if manual_user.UserId not in target_user_ids:
                # Generate unique token for external access
                unique_token = secrets.token_urlsafe(32)
                
                user_ack = PolicyAcknowledgementUser.objects.create(
                    AcknowledgementRequest=ack_request,
                    UserId=manual_user,
                    Token=unique_token
                )
                user_acks.append(user_ack)
        
        # Update counts
        ack_request.PendingCount = len(user_acks)
        ack_request.save()
        
        # Log the action (Requirement 8: Audit Log)
        send_log(
            module="Policy",
            actionType="CREATE_ACKNOWLEDGEMENT_REQUEST",
            description=f"Created acknowledgement request for policy {policy_id} version {policy_version}",
            userId=user_id,
            userName=getattr(user, 'UserName', getattr(user, 'username', 'Unknown')),
            entityType="PolicyAcknowledgementRequest",
            entityId=ack_request.AcknowledgementRequestId,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "policy_id": policy_id,
                "policy_version": policy_version,
                "total_users": len(target_user_ids),
                "due_date": str(due_date) if due_date else None,
                "title": ack_request.Title
            }
        )
        
        # Send notifications to assigned users (Requirement 3: Notify Users)
        send_notifications = data.get('send_notifications', True)
        send_email = data.get('send_email', True)
        
        if send_notifications or send_email:
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                
                # Get frontend URL from environment variable or use default
                frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')
                
                # Send notification to each assigned user
                for user_ack in user_acks:
                    try:
                        target_user = user_ack.UserId
                        
                        # Construct external acknowledgement link with token
                        acknowledgement_link = f"{frontend_url}/acknowledge-policy/{user_ack.Token}"
                        
                        # Send email notification if requested
                        # For manual emails, always send email; for database users, check send_email flag
                        should_send_email = send_email and target_user.Email
                        is_manual_email = target_user.Email in manual_emails if manual_emails else False
                        
                        if should_send_email or is_manual_email:
                            # Prepare email notification data with external link
                            email_notification_data = {
                                'notification_type': 'policyAcknowledgementRequired',
                                'email': target_user.Email,
                                'email_type': 'gmail',
                                'template_data': [
                                    target_user.UserName or target_user.Email,
                                    policy.PolicyName,
                                    policy_version,
                                    ack_request.Title,
                                    ack_request.Description or 'Please review and acknowledge this policy.',
                                    str(due_date) if due_date else 'No due date',
                                    acknowledgement_link  # External acknowledgement link with token
                                ]
                            }
                            
                            # Send notification via email
                            email_result = notification_service.send_multi_channel_notification(email_notification_data)
                            print(f"Email notification sent to user {target_user.UserId}: {email_result}")
                        
                        # Send in-app notification if requested
                        if send_notifications:
                            try:
                                # Create in-app notification for the user
                                from ...routes.Global.notifications import notifications_storage
                                import uuid
                                
                                notification = {
                                    'id': str(uuid.uuid4()),
                                    'title': 'Acknowledgement Request Created',
                                    'message': f'Acknowledgement request created for "{policy.PolicyName}". {ack_request.TotalUsers} users assigned.',
                                    'category': 'policy',
                                    'priority': 'high',
                                    'createdAt': datetime.now().isoformat(),
                                    'status': {
                                        'isRead': False,  # Always unread when created
                                        'readAt': None
                                    },
                                    'user_id': str(target_user.UserId)
                                }
                                
                                # Store notification
                                notifications_storage.append(notification)
                                
                                # Keep only last 100 notifications to prevent memory issues
                                if len(notifications_storage) > 100:
                                    notifications_storage.pop(0)
                                
                                print(f"In-app notification created for user {target_user.UserId}: {notification['id']}")
                            except Exception as e:
                                print(f"Error creating in-app notification for user {target_user.UserId}: {str(e)}")
                        
                        # Update NotifiedAt for the user acknowledgement record
                        user_ack.NotifiedAt = timezone.now()
                        user_ack.save()
                    except Exception as e:
                        print(f"Error sending notification to user {target_user.UserId}: {str(e)}")
            except Exception as e:
                print(f"Error in notification service: {str(e)}")
                # Don't fail the request if notifications fail
        
        return Response({
            'success': True,
            'message': 'Acknowledgement request created successfully',
            'acknowledgement_request_id': ack_request.AcknowledgementRequestId,
            'total_users': ack_request.TotalUsers,
            'pending_count': ack_request.PendingCount
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        send_log(
            module="Policy",
            actionType="CREATE_ACKNOWLEDGEMENT_REQUEST_ERROR",
            description=f"Error creating acknowledgement request: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Unknown'),
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_policy_acknowledgement_requests(request, policy_id):
    """
    Get all acknowledgement requests for a specific policy
    """
    try:
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Get all acknowledgement requests for this policy
        requests = PolicyAcknowledgementRequest.objects.filter(
            PolicyId=policy
        ).select_related('CreatedBy').order_by('-CreatedAt')
        
        requests_data = []
        for req in requests:
            requests_data.append({
                'acknowledgement_request_id': req.AcknowledgementRequestId,
                'title': req.Title,
                'description': req.Description,
                'policy_version': req.PolicyVersion,
                'due_date': req.DueDate.isoformat() if req.DueDate else None,
                'status': req.Status,
                'total_users': req.TotalUsers,
                'acknowledged_count': req.AcknowledgedCount,
                'pending_count': req.PendingCount,
                'completion_percentage': req.completion_percentage,
                'created_by': req.CreatedBy.UserName,
                'created_at': req.CreatedAt.isoformat(),
                'completed_at': req.CompletedAt.isoformat() if req.CompletedAt else None
            })
        
        return Response({
            'success': True,
            'policy_id': policy_id,
            'policy_name': policy.PolicyName,
            'acknowledgement_requests': requests_data
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_pending_acknowledgements(request):
    """
    Get all pending acknowledgements for the current user
    """
    try:
        print(f"DEBUG: get_user_pending_acknowledgements called")
        print(f"DEBUG: User: {request.user if hasattr(request, 'user') else 'No user'}")
        
        # Get current user - handle multiple ways user might be set
        user_id = None
        if hasattr(request, 'user') and request.user:
            user_id = getattr(request.user, 'UserId', None) or getattr(request.user, 'id', None)
        
        # If no user_id from request.user, try to get from JWT or session
        if not user_id:
            # Try to get from JWT token in header
            auth_header = request.headers.get('Authorization', '')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    token = auth_header.split(' ')[1]
                    from ...authentication import verify_jwt_token
                    payload = verify_jwt_token(token)
                    if payload and 'user_id' in payload:
                        user_id = payload['user_id']
                except Exception as e:
                    print(f"DEBUG: Error extracting from JWT: {str(e)}")
        
        # If still no user_id, try session
        if not user_id and hasattr(request, 'session'):
            user_id = request.session.get('user_id') or request.session.get('grc_user_id')
        
        print(f"DEBUG: Resolved user_id: {user_id}")
        
        if not user_id:
            return Response({
                'error': 'User not authenticated. Please login again.',
                'success': False,
                'pending_count': 0,
                'pending_acknowledgements': []
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = Users.objects.get(UserId=user_id)
            print(f"DEBUG: Found user: {user.UserName}")
        except Users.DoesNotExist:
            print(f"DEBUG: User {user_id} not found")
            return Response({
                'error': f'User with ID {user_id} not found',
                'success': False,
                'pending_count': 0,
                'pending_acknowledgements': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all pending acknowledgements for this user
        pending_acks = PolicyAcknowledgementUser.objects.filter(
            UserId=user,
            Status__in=['Pending', 'Overdue']
        ).select_related('AcknowledgementRequest', 'AcknowledgementRequest__PolicyId')
        
        print(f"DEBUG: Found {pending_acks.count()} pending acknowledgements")
        
        acks_data = []
        for ack in pending_acks:
            req = ack.AcknowledgementRequest
            policy = req.PolicyId
            
            acks_data.append({
                'acknowledgement_user_id': ack.AcknowledgementUserId,
                'acknowledgement_request_id': req.AcknowledgementRequestId,
                'policy_id': policy.PolicyId,
                'policy_name': policy.PolicyName,
                'policy_version': req.PolicyVersion,
                'title': req.Title,
                'description': req.Description,
                'due_date': req.DueDate.isoformat() if req.DueDate else None,
                'status': ack.Status,
                'is_overdue': ack.is_overdue,
                'assigned_at': ack.AssignedAt.isoformat(),
                'notified_at': ack.NotifiedAt.isoformat() if ack.NotifiedAt else None
            })
        
        return Response({
            'success': True,
            'user_id': user_id,
            'pending_count': len(acks_data),
            'pending_acknowledgements': acks_data
        })
        
    except Exception as e:
        print(f"DEBUG: Exception in get_user_pending_acknowledgements: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e),
            'success': False,
            'pending_count': 0,
            'pending_acknowledgements': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # Empty list = no permission check
@csrf_exempt
def acknowledge_policy(request, acknowledgement_user_id):
    """
    Record user acknowledgement
    
    Request body:
    {
        "comments": "I have reviewed and understood the policy"  // optional
    }
    """
    try:
        print(f"DEBUG: acknowledge_policy called for acknowledgement_user_id={acknowledgement_user_id}")
        
        # Get current user - handle multiple ways user might be set
        user_id = None
        if hasattr(request, 'user') and request.user:
            user_id = getattr(request.user, 'UserId', None) or getattr(request.user, 'id', None)
        
        # If no user_id from request.user, try to get from JWT or session
        if not user_id:
            # Try to get from JWT token in header
            auth_header = request.headers.get('Authorization', '')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    token = auth_header.split(' ')[1]
                    from ...authentication import verify_jwt_token
                    payload = verify_jwt_token(token)
                    if payload and 'user_id' in payload:
                        user_id = payload['user_id']
                except Exception as e:
                    print(f"DEBUG: Error extracting from JWT: {str(e)}")
        
        # If still no user_id, try session
        if not user_id and hasattr(request, 'session'):
            user_id = request.session.get('user_id') or request.session.get('grc_user_id')
        
        print(f"DEBUG: Resolved user_id: {user_id}")
        
        if not user_id:
            return Response({
                'error': 'User not authenticated. Please login again.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get acknowledgement user record
        ack_user = get_object_or_404(
            PolicyAcknowledgementUser,
            AcknowledgementUserId=acknowledgement_user_id
        )
        
        print(f"DEBUG: Found ack_user for acknowledgement_user_id={acknowledgement_user_id}")
        print(f"DEBUG: ack_user.UserId.UserId={ack_user.UserId.UserId}, current user_id={user_id}")
        
        # Verify it belongs to current user
        if ack_user.UserId.UserId != user_id:
            return Response({
                'error': f'Unauthorized: This acknowledgement belongs to user {ack_user.UserId.UserId}, but you are user {user_id}'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if already acknowledged
        if ack_user.Status == 'Acknowledged':
            return Response({
                'error': 'This policy has already been acknowledged'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get IP and user agent
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        
        # Get policy info before acknowledging (Requirement 5: Record and Store)
        policy = ack_user.AcknowledgementRequest.PolicyId
        policy_id = policy.PolicyId
        policy_version = ack_user.AcknowledgementRequest.PolicyVersion
        user = ack_user.UserId
        
        # Record acknowledgement (Requirement 4 & 5: User Acknowledgement Action & Record and Store)
        comments = request.data.get('comments', '')
        ack_user.acknowledge(
            ip_address=ip_address,
            user_agent=user_agent,
            comments=comments
        )
        
        # Refresh to get updated counts
        ack_request = ack_user.AcknowledgementRequest
        ack_request.refresh_from_db()
        
        # Mark acknowledgement notification as read
        mark_acknowledgement_notification_as_read(
            user_id=user_id,
            policy_name=policy.PolicyName,
            acknowledgement_request_id=ack_request.AcknowledgementRequestId
        )
        
        # Log the acknowledgement (Requirement 8: Minimum Audit Log - When acknowledgement was recorded)
        send_log(
            module="Policy",
            actionType="ACKNOWLEDGE_POLICY",
            description=f"User acknowledged policy {policy_id} version {policy_version}",
            userId=user_id,
            userName=getattr(user, 'UserName', getattr(user, 'username', 'Unknown')),
            entityType="PolicyAcknowledgementUser",
            entityId=ack_user.AcknowledgementUserId,
            ipAddress=ip_address,
            additionalInfo={
                "acknowledgement_request_id": ack_request.AcknowledgementRequestId,
                "policy_id": policy_id,
                "policy_version": policy_version,
                "policy_name": policy.PolicyName,
                "acknowledged_at": ack_user.AcknowledgedAt.isoformat() if ack_user.AcknowledgedAt else None,
                "status": ack_user.Status,
                "comments": comments,
                "completion_percentage": ack_request.completion_percentage
            }
        )
        
        # Return response with all stored data (Requirement 5: Record and Store Acknowledgement)
        return Response({
            'success': True,
            'message': 'Policy acknowledged successfully',
            'acknowledgement_data': {
                'user_id': user_id,
                'policy_id': policy_id,
                'policy_version': policy_version,
                'acknowledged_timestamp': ack_user.AcknowledgedAt.isoformat() if ack_user.AcknowledgedAt else None,
                'status': ack_user.Status,
                'ip_address': ip_address,
                'comments': comments
            },
            'request_status': {
                'acknowledgement_request_id': ack_request.AcknowledgementRequestId,
                'total_users': ack_request.TotalUsers,
                'acknowledged_count': ack_request.AcknowledgedCount,
                'pending_count': ack_request.PendingCount,
                'completion_percentage': ack_request.completion_percentage,
                'request_status': ack_request.Status
            }
        })
        
    except Exception as e:
        send_log(
            module="Policy",
            actionType="ACKNOWLEDGE_POLICY_ERROR",
            description=f"Error acknowledging policy: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Unknown'),
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_acknowledgement_report(request, acknowledgement_request_id):
    """
    Get detailed report for an acknowledgement request (Admin view)
    """
    try:
        # Get acknowledgement request
        ack_request = get_object_or_404(
            PolicyAcknowledgementRequest,
            AcknowledgementRequestId=acknowledgement_request_id
        )
        
        # Get all user acknowledgements
        user_acks = PolicyAcknowledgementUser.objects.filter(
            AcknowledgementRequest=ack_request
        ).select_related('UserId').order_by('-AcknowledgedAt', 'UserId__UserName')
        
        users_data = []
        for ack in user_acks:
            users_data.append({
                'user_id': ack.UserId.UserId,
                'user_name': ack.UserId.UserName,
                'email': ack.UserId.Email,
                'status': ack.Status,
                'assigned_at': ack.AssignedAt.isoformat(),
                'acknowledged_at': ack.AcknowledgedAt.isoformat() if ack.AcknowledgedAt else None,
                'is_overdue': ack.is_overdue,
                'comments': ack.Comments,
                'ip_address': ack.IPAddress,
                'user_agent': ack.UserAgent,
                'access_method': 'External Link' if ack.UserAgent and ('Mozilla' in ack.UserAgent or 'Chrome' in ack.UserAgent or 'Safari' in ack.UserAgent) else 'In-App',
                'reminder_count': ack.ReminderCount
            })
        
        # Group by status
        status_summary = {}
        for status_choice in ['Pending', 'Acknowledged', 'Overdue']:
            count = user_acks.filter(Status=status_choice).count()
            status_summary[status_choice.lower()] = count
        
        return Response({
            'success': True,
            'acknowledgement_request': {
                'acknowledgement_request_id': ack_request.AcknowledgementRequestId,
                'title': ack_request.Title,
                'description': ack_request.Description,
                'policy_id': ack_request.PolicyId.PolicyId,
                'policy_name': ack_request.PolicyId.PolicyName,
                'policy_version': ack_request.PolicyVersion,
                'due_date': ack_request.DueDate.isoformat() if ack_request.DueDate else None,
                'status': ack_request.Status,
                'total_users': ack_request.TotalUsers,
                'acknowledged_count': ack_request.AcknowledgedCount,
                'pending_count': ack_request.PendingCount,
                'completion_percentage': ack_request.completion_percentage,
                'created_by': ack_request.CreatedBy.UserName,
                'created_at': ack_request.CreatedAt.isoformat(),
                'completed_at': ack_request.CompletedAt.isoformat() if ack_request.CompletedAt else None
            },
            'status_summary': status_summary,
            'users': users_data
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_users_for_acknowledgement(request):
    """
    Get list of users that can be assigned acknowledgements
    """
    try:
        # Get all active users
        users = Users.objects.filter(IsActive='Y').order_by('UserName')
        
        # Get role information from RBAC table
        from ...models import RBAC
        
        users_data = []
        for user in users:
            # Try to get role from RBAC table
            role = 'User'  # Default role
            try:
                rbac_user = RBAC.objects.filter(user_id=user.UserId, is_active='Y').first()
                if rbac_user:
                    role = rbac_user.role
            except Exception:
                pass  # If RBAC lookup fails, use default role
            
            users_data.append({
                'user_id': user.UserId,
                'user_name': user.UserName,
                'email': user.Email,
                'first_name': user.FirstName,
                'last_name': user.LastName,
                'full_name': f"{user.FirstName} {user.LastName}".strip(),
                'role': role
            })
        
        return Response({
            'success': True,
            'users': users_data,
            'total_count': len(users_data)
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def cancel_acknowledgement_request(request, acknowledgement_request_id):
    """
    Cancel an acknowledgement request
    """
    try:
        # Get acknowledgement request
        ack_request = get_object_or_404(
            PolicyAcknowledgementRequest,
            AcknowledgementRequestId=acknowledgement_request_id
        )
        
        # Check if already completed
        if ack_request.Status == 'Completed':
            return Response({
                'error': 'Cannot cancel a completed acknowledgement request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update status
        ack_request.Status = 'Cancelled'
        ack_request.save()
        
        # Log the action
        user_id = getattr(request.user, 'id', None) or getattr(request.user, 'UserId', None)
        send_log(
            module="Policy",
            actionType="CANCEL_ACKNOWLEDGEMENT_REQUEST",
            description=f"Cancelled acknowledgement request {acknowledgement_request_id}",
            userId=user_id,
            userName=getattr(request.user, 'username', 'Unknown'),
            entityType="PolicyAcknowledgementRequest",
            entityId=acknowledgement_request_id,
            ipAddress=get_client_ip(request)
        )
        
        return Response({
            'success': True,
            'message': 'Acknowledgement request cancelled successfully'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

