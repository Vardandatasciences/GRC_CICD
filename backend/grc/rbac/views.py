"""
RBAC Views for GRC System

This module provides views for RBAC functionality including user permissions.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import logging
from .utils import RBACUtils
from .decorators import rbac_required
import jwt
from django.conf import settings

logger = logging.getLogger(__name__)

def get_user_id_from_jwt(request):
    """
    Extract user_id from JWT token in Authorization header
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("[RBAC VIEWS] No Bearer token found in Authorization header")
            return None
        
        token = auth_header.split(' ')[1]
        
        # Decode JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if user_id:
            #logger.info(f"[RBAC VIEWS] Successfully extracted user_id from JWT: {user_id}")
            return user_id
        else:
            logger.warning("[RBAC VIEWS] No user_id found in JWT payload")
            return None
            
    except jwt.ExpiredSignatureError:
        logger.error("[RBAC VIEWS] JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"[RBAC VIEWS] Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"[RBAC VIEWS] Error extracting user_id from JWT: {e}")
        return None

@csrf_exempt
@require_http_methods(["GET"])
def get_user_permissions(request):
    """
    Get user permissions for frontend RBAC service
    
    Returns:
        JSON response with user permissions organized by module
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        # Get user permissions summary
        permissions_summary = RBACUtils.get_user_permissions_summary(user_id)
        
        if not permissions_summary:
            return JsonResponse({
                'error': 'User not found',
                'message': 'User not found in RBAC system'
            }, status=404)
        
        # Organize permissions by module
        organized_permissions = {
            'policy': {},
            'compliance': {},
            'audit': {},
            'risk': {},
            'incident': {}
        }
        
        # Map permissions to modules
        permission_mapping = {
            # Policy permissions
            'view_all_policy': 'policy',
            'create_policy': 'policy',
            'edit_policy': 'policy',
            'approve_policy': 'policy',
            'delete_policy': 'policy',
            'assign_policy': 'policy',
            'policy_performance_analytics': 'policy',
            
            # Compliance permissions
            'view_all_compliance': 'compliance',
            'create_compliance': 'compliance',
            'edit_compliance': 'compliance',
            'approve_compliance': 'compliance',
            'delete_compliance': 'compliance',
            'compliance_performance_analytics': 'compliance',
            
            # Audit permissions
            'view_audit_reports': 'audit',
            'conduct_audit': 'audit',
            'review_audit': 'audit',
            'assign_audit': 'audit',
            'audit_performance_analytics': 'audit',
            
            # Risk permissions
            'view_all_risk': 'risk',
            'create_risk': 'risk',
            'edit_risk': 'risk',
            'approve_risk': 'risk',
            'delete_risk': 'risk',
            'risk_performance_analytics': 'risk',
            
            # Incident permissions
            'view_all_incident': 'incident',
            'create_incident': 'incident',
            'edit_incident': 'incident',
            'approve_incident': 'incident',
            'delete_incident': 'incident',
            'incident_performance_analytics': 'incident'
        }
        
        # Process permissions from the summary
        permissions_data = permissions_summary.get('permissions', {})
        
        # Process each module's permissions directly
        for module_name, module_permissions in permissions_data.items():
            if module_name in organized_permissions:
                for field_name, has_permission in module_permissions.items():
                    # Map field names to frontend permission names based on module
                    if module_name == 'policy':
                        if field_name == 'create':
                            permission_name = 'create_policy'
                        elif field_name == 'view_all':
                            permission_name = 'view_all_policy'
                        elif field_name == 'edit':
                            permission_name = 'edit_policy'
                        elif field_name == 'approve':
                            permission_name = 'approve_policy'
                        elif field_name == 'analytics':
                            permission_name = 'policy_performance_analytics'
                        elif field_name == 'create_framework':
                            permission_name = 'create_framework'
                        elif field_name == 'approve_framework':
                            permission_name = 'approve_framework'
                        else:
                            continue
                    elif module_name == 'compliance':
                        if field_name == 'create':
                            permission_name = 'create_compliance'
                        elif field_name == 'view_all':
                            permission_name = 'view_all_compliance'
                        elif field_name == 'edit':
                            permission_name = 'edit_compliance'
                        elif field_name == 'approve':
                            permission_name = 'approve_compliance'
                        elif field_name == 'analytics':
                            permission_name = 'compliance_performance_analytics'
                        else:
                            continue
                    elif module_name == 'audit':
                        if field_name == 'assign':
                            permission_name = 'assign_audit'
                        elif field_name == 'conduct':
                            permission_name = 'conduct_audit'
                        elif field_name == 'review':
                            permission_name = 'review_audit'
                        elif field_name == 'view_reports':
                            permission_name = 'view_audit_reports'
                        elif field_name == 'analytics':
                            permission_name = 'audit_performance_analytics'
                        else:
                            continue
                    elif module_name == 'risk':
                        if field_name == 'create':
                            permission_name = 'create_risk'
                        elif field_name == 'view_all':
                            permission_name = 'view_all_risk'
                        elif field_name == 'edit':
                            permission_name = 'edit_risk'
                        elif field_name == 'approve':
                            permission_name = 'approve_risk'
                        elif field_name == 'assign':
                            permission_name = 'assign_risk'
                        elif field_name == 'evaluate':
                            permission_name = 'evaluate_assigned_risk'
                        elif field_name == 'analytics':
                            permission_name = 'risk_performance_analytics'
                        else:
                            continue
                    elif module_name == 'incident':
                        if field_name == 'create':
                            permission_name = 'create_incident'
                        elif field_name == 'view_all':
                            permission_name = 'view_all_incident'
                        elif field_name == 'edit':
                            permission_name = 'edit_incident'
                        elif field_name == 'assign':
                            permission_name = 'assign_incident'
                        elif field_name == 'evaluate':
                            permission_name = 'evaluate_assigned_incident'
                        elif field_name == 'escalate':
                            permission_name = 'escalate_to_risk'
                        elif field_name == 'analytics':
                            permission_name = 'incident_performance_analytics'
                        else:
                            continue
                    else:
                        continue
                    
                    organized_permissions[module_name][permission_name] = has_permission
        

        
        # Add user info
        response_data = {
            'user_id': user_id,
            'username': permissions_summary.get('username'),
            'role': permissions_summary.get('role'),
            'permissions': organized_permissions,
            'is_admin': permissions_summary.get('is_admin', False)
        }
        
        #logger.info(f"[RBAC VIEWS] Returning permissions for user {user_id}")
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC VIEWS] Error getting user permissions: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': 'Error retrieving user permissions'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_permission(request):
    """
    Check if user has a specific permission
    
    Query parameters:
        module: Module name (e.g., 'policy', 'compliance')
        permission: Permission name (e.g., 'view_all_policy')
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        # Get query parameters
        module = request.GET.get('module')
        permission = request.GET.get('permission')
        
        if not module or not permission:
            return JsonResponse({
                'error': 'Missing parameters',
                'message': 'Both module and permission parameters are required'
            }, status=400)
        
        # Check permission
        has_permission = RBACUtils.has_permission(user_id, module, permission)
        
        response_data = {
            'user_id': user_id,
            'module': module,
            'permission': permission,
            'has_permission': has_permission
        }
        
        #logger.info(f"[RBAC VIEWS] Permission check: user {user_id} - {module}.{permission} = {has_permission}")
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC VIEWS] Error checking permission: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': 'Error checking permission'
        }, status=500) 