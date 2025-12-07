"""
Public Policy Acknowledgement API endpoints
These endpoints allow users to acknowledge policies via external links without logging in
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from ...models import PolicyAcknowledgementUser, PolicyAcknowledgementRequest, Policy
from ..Global.logging_service import send_log
from urllib.parse import unquote
import os


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


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_acknowledgement_by_token(request, token):
    """
    Get policy acknowledgement details by token (public access)
    
    This endpoint allows users to view acknowledgement details without logging in
    
    URL: /api/policy-acknowledgements/public/<token>/
    Method: GET
    
    Response:
    {
        "success": true,
        "data": {
            "acknowledgement_user_id": 1,
            "policy": {
                "policy_id": 1,
                "policy_name": "Security Policy",
                "policy_version": "1.0",
                "policy_description": "...",
                "policy_content": "...",
                "policy_document_url": "..."
            },
            "request": {
                "title": "Acknowledge Security Policy",
                "description": "Please review and acknowledge...",
                "due_date": "2025-12-31",
                "created_at": "2025-11-20"
            },
            "user": {
                "user_name": "John Doe",
                "email": "john@example.com"
            },
            "status": "Pending",
            "is_overdue": false
        }
    }
    """
    try:
        # URL decode the token in case it was encoded
        decoded_token = unquote(token)
        
        # Debug: Print token for troubleshooting
        print(f"DEBUG: Received token (raw): {token}")
        print(f"DEBUG: Received token (decoded): {decoded_token}")
        print(f"DEBUG: Token length: {len(decoded_token) if decoded_token else 0}")
        
        # Try with decoded token first
        ack_user = PolicyAcknowledgementUser.objects.filter(Token=decoded_token).first()
        
        # If not found, try with original token (in case it wasn't URL encoded)
        if not ack_user and decoded_token != token:
            print(f"DEBUG: Trying with original token...")
            ack_user = PolicyAcknowledgementUser.objects.filter(Token=token).first()
        
        if not ack_user:
            # Debug: Check if any tokens exist
            total_with_tokens = PolicyAcknowledgementUser.objects.filter(Token__isnull=False).count()
            print(f"DEBUG: Token not found. Total records with tokens: {total_with_tokens}")
            
            # Try to find similar tokens (first 20 chars)
            if len(decoded_token) > 20:
                sample_token = decoded_token[:20]
                similar = PolicyAcknowledgementUser.objects.filter(Token__startswith=sample_token).first()
                if similar:
                    print(f"DEBUG: Found similar token starting with: {sample_token}")
            
            return Response({
                'success': False,
                'error': 'Invalid or expired acknowledgement link',
                'debug_info': {
                    'token_received': decoded_token[:30] + '...' if len(decoded_token) > 30 else decoded_token,
                    'token_length': len(decoded_token),
                    'total_with_tokens': total_with_tokens
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get related data (needed for both acknowledged and pending states)
        ack_request = ack_user.AcknowledgementRequest
        policy = ack_request.PolicyId
        user = ack_user.UserId
        
        # Use the token that was found (either decoded or original)
        found_token = decoded_token if PolicyAcknowledgementUser.objects.filter(Token=decoded_token).exists() else token
        
        # Check if already acknowledged
        if ack_user.Status == 'Acknowledged':
            return Response({
                'success': True,
                'already_acknowledged': True,
                'acknowledged_at': ack_user.AcknowledgedAt.isoformat() if ack_user.AcknowledgedAt else None,
                'message': 'This policy has already been acknowledged',
                'data': {
                    'acknowledgement_user_id': ack_user.AcknowledgementUserId,
                    'token': found_token,
                    'policy': {
                        'policy_id': policy.PolicyId,
                        'policy_name': policy.PolicyName,
                        'policy_version': ack_request.PolicyVersion,
                        'policy_description': getattr(policy, 'PolicyDescription', '') or '',
                        'policy_objective': getattr(policy, 'Objective', '') or '',
                        'policy_status': getattr(policy, 'Status', ''),
                        'effective_date': policy.StartDate.isoformat() if hasattr(policy, 'StartDate') and policy.StartDate else None,
                        'review_date': policy.EndDate.isoformat() if hasattr(policy, 'EndDate') and policy.EndDate else None,
                        'scope': getattr(policy, 'Scope', '') or '',
                        'applicability': getattr(policy, 'Applicability', '') or '',
                        'policy_document_url': getattr(policy, 'DocURL', None) or None,
                    },
                    'request': {
                        'title': ack_request.Title,
                        'description': ack_request.Description or '',
                        'due_date': ack_request.DueDate.isoformat() if ack_request.DueDate else None,
                        'created_at': ack_request.CreatedAt.isoformat(),
                    },
                    'user': {
                        'user_name': user.UserName or user.Email,
                        'email': user.Email,
                        'first_name': user.FirstName or '',
                        'last_name': user.LastName or '',
                    },
                    'status': ack_user.Status,
                    'is_overdue': ack_user.is_overdue,
                    'assigned_at': ack_user.AssignedAt.isoformat(),
                }
            }, status=status.HTTP_200_OK)
        
        # Use the token that was found (either decoded or original)
        found_token = decoded_token if PolicyAcknowledgementUser.objects.filter(Token=decoded_token).exists() else token
        
        # Prepare response data (ack_request, policy, user already retrieved above)
        response_data = {
            'success': True,
            'data': {
                'acknowledgement_user_id': ack_user.AcknowledgementUserId,
                'token': found_token,
                'policy': {
                    'policy_id': policy.PolicyId,
                    'policy_name': policy.PolicyName,
                    'policy_version': ack_request.PolicyVersion,
                    'policy_description': getattr(policy, 'PolicyDescription', '') or '',
                    'policy_objective': getattr(policy, 'Objective', '') or '',
                    'policy_status': getattr(policy, 'Status', ''),
                    'effective_date': policy.StartDate.isoformat() if hasattr(policy, 'StartDate') and policy.StartDate else None,
                    'review_date': policy.EndDate.isoformat() if hasattr(policy, 'EndDate') and policy.EndDate else None,
                    'scope': getattr(policy, 'Scope', '') or '',
                    'applicability': getattr(policy, 'Applicability', '') or '',
                    # Include policy document URL if available
                    'policy_document_url': getattr(policy, 'DocURL', None) or None,
                },
                'request': {
                    'title': ack_request.Title,
                    'description': ack_request.Description or '',
                    'due_date': ack_request.DueDate.isoformat() if ack_request.DueDate else None,
                    'created_at': ack_request.CreatedAt.isoformat(),
                },
                'user': {
                    'user_name': user.UserName or user.Email,
                    'email': user.Email,
                    'first_name': user.FirstName or '',
                    'last_name': user.LastName or '',
                },
                'status': ack_user.Status,
                'is_overdue': ack_user.is_overdue,
                'assigned_at': ack_user.AssignedAt.isoformat(),
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error getting acknowledgement by token: {str(e)}")
        print(f"Full traceback: {error_trace}")
        return Response({
            'success': False,
            'error': 'An error occurred while retrieving acknowledgement details',
            'debug_error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def acknowledge_policy_by_token(request, token):
    """
    Acknowledge a policy using external token (public access)
    
    This endpoint allows users to acknowledge policies without logging in
    
    URL: /api/policy-acknowledgements/public/<token>/acknowledge/
    Method: POST
    
    Request body:
    {
        "comments": "I have read and understood the policy" (optional)
    }
    
    Response:
    {
        "success": true,
        "message": "Policy acknowledged successfully",
        "acknowledged_at": "2025-11-21T10:30:00Z"
    }
    """
    try:
        # URL decode the token
        decoded_token = unquote(token)
        
        # Get comments from request body
        data = request.data
        comments = data.get('comments', '')
        
        # Find acknowledgement user by token (try decoded first, then original)
        ack_user = PolicyAcknowledgementUser.objects.filter(Token=decoded_token).first()
        if not ack_user and decoded_token != token:
            ack_user = PolicyAcknowledgementUser.objects.filter(Token=token).first()
        
        if not ack_user:
            return Response({
                'success': False,
                'error': 'Invalid or expired acknowledgement link'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already acknowledged
        if ack_user.Status == 'Acknowledged':
            return Response({
                'success': False,
                'error': 'This policy has already been acknowledged',
                'acknowledged_at': ack_user.AcknowledgedAt.isoformat() if ack_user.AcknowledgedAt else None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client IP and user agent
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        
        # Acknowledge the policy
        ack_user.acknowledge(
            ip_address=ip_address,
            user_agent=user_agent,
            comments=comments
        )
        
        # Log the action
        ack_request = ack_user.AcknowledgementRequest
        policy = ack_request.PolicyId
        user = ack_user.UserId
        
        # Mark acknowledgement notification as read
        mark_acknowledgement_notification_as_read(
            user_id=user.UserId,
            policy_name=policy.PolicyName,
            acknowledgement_request_id=ack_request.AcknowledgementRequestId
        )
        
        send_log(
            module="Policy",
            actionType="POLICY_ACKNOWLEDGED_EXTERNAL",
            description=f"Policy '{policy.PolicyName}' (v{ack_request.PolicyVersion}) acknowledged by {user.Email} via external link",
            userId=user.UserId,
            userName=user.UserName or user.Email,
            logLevel="INFO",
            ipAddress=ip_address,
            additionalInfo={
                "policy_id": policy.PolicyId,
                "policy_name": policy.PolicyName,
                "policy_version": ack_request.PolicyVersion,
                "acknowledgement_request_id": ack_request.AcknowledgementRequestId,
                "acknowledgement_user_id": ack_user.AcknowledgementUserId,
                "access_method": "external_link",
                "comments": comments
            }
        )
        
        return Response({
            'success': True,
            'message': 'Policy acknowledged successfully',
            'acknowledged_at': ack_user.AcknowledgedAt.isoformat(),
            'policy_name': policy.PolicyName,
            'policy_version': ack_request.PolicyVersion
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error acknowledging policy by token: {str(e)}")
        print(f"Full traceback: {error_trace}")
        return Response({
            'success': False,
            'error': 'An error occurred while acknowledging the policy',
            'debug_error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_policy_document_by_token(request, token):
    """
    Get policy document/content by token (public access)
    
    This endpoint allows users to view the full policy document without logging in
    
    URL: /api/policy-acknowledgements/public/<token>/document/
    Method: GET
    """
    try:
        # URL decode the token
        decoded_token = unquote(token)
        
        # Find acknowledgement user by token (try decoded first, then original)
        ack_user = PolicyAcknowledgementUser.objects.filter(Token=decoded_token).first()
        if not ack_user and decoded_token != token:
            ack_user = PolicyAcknowledgementUser.objects.filter(Token=token).first()
        
        if not ack_user:
            return Response({
                'success': False,
                'error': 'Invalid or expired acknowledgement link'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get policy details
        ack_request = ack_user.AcknowledgementRequest
        policy = ack_request.PolicyId
        
        # Return policy document details
        response_data = {
            'success': True,
            'data': {
                'policy_name': policy.PolicyName,
                'policy_version': ack_request.PolicyVersion,
                'policy_description': getattr(policy, 'PolicyDescription', '') or '',
                'policy_objective': getattr(policy, 'Objective', '') or '',
                'policy_scope': getattr(policy, 'Scope', '') or '',
                'policy_document_path': getattr(policy, 'DocURL', None) or None,
                'effective_date': policy.StartDate.isoformat() if hasattr(policy, 'StartDate') and policy.StartDate else None,
                'review_date': policy.EndDate.isoformat() if hasattr(policy, 'EndDate') and policy.EndDate else None,
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error getting policy document by token: {str(e)}")
        return Response({
            'success': False,
            'error': 'An error occurred while retrieving policy document'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

