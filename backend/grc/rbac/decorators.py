"""
RBAC Decorators for GRC System

This module provides decorators for checking RBAC permissions on view functions.
These decorators provide an additional layer of security beyond the permission classes.
"""

from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
import logging
import jwt
from django.conf import settings
from .utils import RBACUtils
from ..models import RBAC

logger = logging.getLogger(__name__)

def get_user_id_from_jwt(request):
    """
    Extract user_id from JWT token in Authorization header
    
    Args:
        request: Django request object
        
    Returns:
        int or None: User ID from JWT token
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("[RBAC] No Bearer token found in Authorization header")
            return None
        
        token = auth_header.split(' ')[1]
        
        # Decode JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if user_id:
            #logger.info(f"[RBAC] Successfully extracted user_id from JWT: {user_id}")
            return user_id
        else:
            logger.warning("[RBAC] No user_id found in JWT payload")
            return None
            
    except jwt.ExpiredSignatureError:
        logger.error("[RBAC] JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"[RBAC] Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"[RBAC] Error extracting user_id from JWT: {e}")
        return None

def rbac_required(required_permission=None, endpoint_name=None):
    """
    Decorator to check RBAC permissions for view functions
    
    Args:
        required_permission: Specific permission to check (e.g., 'view_all_policy', 'create_policy')
        endpoint_name: Name of the endpoint for automatic permission lookup
    
    Usage:
        @rbac_required(required_permission='view_all_policy')
        def my_view(request):
            # Your view logic here
            pass
        
        # Or use endpoint name for automatic lookup
        @rbac_required(endpoint_name='get_policy_kpis')
        def get_policy_kpis(request):
            # Your view logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Check RBAC permissions (bypass disabled)
                user_id_dev = RBACUtils.get_user_id_from_request(request)
                if not user_id_dev:
                    logger.warning(f"[RBAC] No user_id found for {endpoint_name or view_func.__name__}")
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid session or JWT token required'
                    }, status=401)

                # Get user_id from JWT token or session (fallback)
                # Use central utility that supports both auth methods
                user_id = RBACUtils.get_user_id_from_request(request)
                
                if not user_id:
                    logger.warning(f"[RBAC] No user_id found in JWT for endpoint: {endpoint_name or view_func.__name__}")
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check RBAC permissions
                permission_result = RBACUtils.check_endpoint_permission(
                    request, 
                    endpoint_name or view_func.__name__, 
                    required_permission
                )
                
                if not permission_result['allowed']:
                    logger.warning(f"[RBAC] Access denied for user {user_id} to {endpoint_name or view_func.__name__}")
                    log_permission_access(endpoint_name or view_func.__name__, user_id, False, permission_result.get('message', 'Permission denied'))
                    
                    return JsonResponse({
                        'error': 'Access denied',
                        'message': permission_result.get('message', 'You do not have permission to access this resource'),
                        'required_permission': required_permission
                    }, status=403)
                
                # Log successful access
                #logger.info(f"[RBAC] Access granted for user {user_id} to {endpoint_name or view_func.__name__}")
                log_permission_access(endpoint_name or view_func.__name__, user_id, True)
                
                # Call the original view function
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC] Error in RBAC decorator: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking permissions'
                }, status=500)
        
        return wrapper
    return decorator

def policy_view_required(view_func):
    """Decorator for functions that require policy view permission"""
    return rbac_required(required_permission='view_all_policy')(view_func)

def policy_create_required(view_func):
    """Decorator for functions that require policy create permission"""
    return rbac_required(required_permission='create_policy')(view_func)

def policy_edit_required(view_func):
    """Decorator for functions that require policy edit permission"""
    return rbac_required(required_permission='edit_policy')(view_func)

def policy_approve_required(view_func):
    """Decorator for functions that require policy approve permission"""
    return rbac_required(required_permission='approve_policy')(view_func)

def policy_delete_required(view_func):
    """Decorator for functions that require policy delete permission (uses edit permission)"""
    return rbac_required(required_permission='edit_policy')(view_func)

def policy_assign_required(view_func):
    """Decorator for functions that require policy assign permission (uses edit permission)"""
    return rbac_required(required_permission='edit_policy')(view_func)

# =====================================================
# AUDIT MODULE DECORATORS
# =====================================================

def audit_view_reports_required(view_func):
    """Decorator for functions that require audit view reports permission"""
    return rbac_required(required_permission='view_audit_reports')(view_func)

def audit_conduct_required(view_func):
    """Decorator for functions that require audit conduct permission"""
    return rbac_required(required_permission='conduct_audit')(view_func)

def audit_review_required(view_func):
    """Decorator for functions that require audit review permission"""
    return rbac_required(required_permission='review_audit')(view_func)

def audit_assign_required(view_func):
    """Decorator for functions that require audit assign permission"""
    return rbac_required(required_permission='assign_audit')(view_func)

def audit_analytics_required(view_func):
    """Decorator for functions that require audit analytics permission"""
    return rbac_required(required_permission='audit_performance_analytics')(view_func)

def audit_view_all_required(view_func):
    """Decorator for functions that require view all audits permission"""
    return rbac_required(required_permission='assign_audit')(view_func)

def audit_or_conduct_required(view_func):
    """Decorator for functions that require either audit view or conduct permission"""
    return require_any_permission('view_audit_reports', 'conduct_audit')(view_func)

def audit_manage_required(view_func):
    """Decorator for functions that require audit management permissions (assign, conduct, or review)"""
    return require_any_permission('assign_audit', 'conduct_audit', 'review_audit')(view_func)

def check_user_permissions(request):
    """
    Helper function to check user permissions and return detailed info
    
    Returns:
        dict: User permission details or None if no access
    """
    try:
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return None
        
        return RBACUtils.get_user_permissions_summary(user_id)
        
    except Exception as e:
        logger.error(f"[RBAC] Error checking user permissions: {e}")
        return None

def log_permission_access(endpoint_name, user_id, granted=True, reason=""):
    """
    Log permission access attempts for auditing
    
    Args:
        endpoint_name: Name of the endpoint accessed
        user_id: ID of the user attempting access
        granted: Whether access was granted
        reason: Reason for denial (if applicable)
    """
    try:
        access_type = "GRANTED" if granted else "DENIED"
        #logger.info(f"[RBAC ACCESS LOG] {access_type} - User {user_id} -> {endpoint_name}")
        
        if not granted and reason:
            logger.info(f"[RBAC ACCESS LOG] DENIAL REASON: {reason}")

            
        
        # Here you could also save to database for audit trail
        # AuditLog.objects.create(user_id=user_id, endpoint=endpoint_name, granted=granted, reason=reason)
        
    except Exception as e:
        logger.error(f"[RBAC ACCESS LOG] Error logging access: {e}")

def require_any_permission(*required_permissions):
    """
    Decorator that requires user to have ANY of the specified permissions
    
    Args:
        *required_permissions: Variable number of permission names
    
    Usage:
        @require_any_permission('view_all_policy', 'approve_policy')
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from JWT token
                user_id = get_user_id_from_jwt(request)
                
                if not user_id:
                    logger.warning(f"[RBAC] No user_id found in JWT for endpoint: {view_func.__name__}")
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check if user has ANY of the required permissions
                has_permission = False
                for permission in required_permissions:
                    if RBACUtils.has_permission(user_id, 'policy', permission):
                        has_permission = True
                        break
                
                if not has_permission:
                    logger.warning(f"[RBAC] Access denied for user {user_id} to {view_func.__name__} (any permission)")
                    log_permission_access(view_func.__name__, user_id, False, f"Required any of: {', '.join(required_permissions)}")
                    
                    return JsonResponse({
                        'error': 'Access denied',
                        'message': f'You need at least one of the following permissions: {", ".join(required_permissions)}',
                        'required_permissions': required_permissions
                    }, status=403)
                
                # Log successful access
                #logger.info(f"[RBAC] Access granted for user {user_id} to {view_func.__name__} (any permission)")
                log_permission_access(view_func.__name__, user_id, True)
                
                # Call the original view function
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC] Error in RBAC decorator: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking permissions'
                }, status=500)
        
        return wrapper
    return decorator

def require_all_permissions(*required_permissions):
    """
    Decorator that requires user to have ALL of the specified permissions
    
    Args:
        *required_permissions: Variable number of permission names
    
    Usage:
        @require_all_permissions('view_all_policy', 'approve_policy')
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from JWT token
                user_id = get_user_id_from_jwt(request)
                
                if not user_id:
                    logger.warning(f"[RBAC] No user_id found in JWT for endpoint: {view_func.__name__}")
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check if user has ALL of the required permissions
                missing_permissions = []
                for permission in required_permissions:
                    if not RBACUtils.has_permission(user_id, 'policy', permission):
                        missing_permissions.append(permission)
                
                if missing_permissions:
                    logger.warning(f"[RBAC] Access denied for user {user_id} to {view_func.__name__} (all permissions)")
                    log_permission_access(view_func.__name__, user_id, False, f"Missing permissions: {', '.join(missing_permissions)}")
                    
                    return JsonResponse({
                        'error': 'Access denied',
                        'message': f'You need all of the following permissions: {", ".join(required_permissions)}. Missing: {", ".join(missing_permissions)}',
                        'required_permissions': required_permissions,
                        'missing_permissions': missing_permissions
                    }, status=403)
                
                # Log successful access
                #logger.info(f"[RBAC] Access granted for user {user_id} to {view_func.__name__} (all permissions)")
                log_permission_access(view_func.__name__, user_id, True)
                
                # Call the original view function
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC] Error in RBAC decorator: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking permissions'
                }, status=500)
        
        return wrapper
    return decorator

# =====================================================
# COMPLIANCE MODULE RBAC DECORATORS - 5 MAIN FEATURES
# =====================================================

def create_compliance_required(view_func):
    """Decorator for CreateCompliance feature - creating new compliance items"""
    return rbac_required(required_permission='create_compliance')(view_func)

def edit_compliance_required(view_func):
    """Decorator for EditCompliance feature - editing existing compliance items"""
    return rbac_required(required_permission='edit_compliance')(view_func)

def approve_compliance_required(view_func):
    """Decorator for ApproveCompliance feature - approving compliance items"""
    return rbac_required(required_permission='approve_compliance')(view_func)

def view_all_compliance_required(view_func):
    """Decorator for ViewAllCompliance feature - viewing compliance data"""
    return rbac_required(required_permission='view_all_compliance')(view_func)

def compliance_performance_analytics_required(view_func):
    """Decorator for CompliancePerformanceAnalytics feature - analytics and reporting"""
    return rbac_required(required_permission='compliance_performance_analytics')(view_func)

# =====================================================
# COMPLIANCE FEATURE MAPPING FUNCTIONS
# =====================================================

def map_compliance_operation_to_permission(operation):
    """
    Map specific compliance operations to one of the 5 main features
    
    Args:
        operation: The specific operation being performed
        
    Returns:
        The main feature permission required
    """
    operation_mapping = {
        # CreateCompliance operations
        'create': 'create_compliance',
        'clone': 'create_compliance',
        'add': 'create_compliance',
        'initialize': 'create_compliance',
        
        # EditCompliance operations  
        'edit': 'edit_compliance',
        'update': 'edit_compliance',
        'modify': 'edit_compliance',
        'toggle': 'edit_compliance',
        'deactivate': 'edit_compliance',
        'activate': 'edit_compliance',
        'delete': 'edit_compliance',
        'manage_categories': 'edit_compliance',
        'manage_business_units': 'edit_compliance',
        
        # ApproveCompliance operations
        'approve': 'approve_compliance',
        'reject': 'approve_compliance',
        'review': 'approve_compliance',
        'submit_review': 'approve_compliance',
        'resubmit': 'approve_compliance',
        
        # ViewAllCompliance operations
        'view': 'view_all_compliance',
        'list': 'view_all_compliance',
        'get': 'view_all_compliance',
        'read': 'view_all_compliance',
        'export': 'view_all_compliance',
        'dashboard': 'view_all_compliance',
        'versioning': 'view_all_compliance',
        'audit_info': 'view_all_compliance',
        'framework_info': 'view_all_compliance',
        'details': 'view_all_compliance',
        
        # CompliancePerformanceAnalytics operations
        'analytics': 'compliance_performance_analytics',
        'kpi': 'compliance_performance_analytics',
        'metrics': 'compliance_performance_analytics',
        'reports': 'compliance_performance_analytics',
        'statistics': 'compliance_performance_analytics'
    }
    
    return operation_mapping.get(operation, 'view_all_compliance')  # Default to view permission

# =====================================================
# LEGACY DECORATOR ALIASES (for backward compatibility)
# =====================================================

# Alias the new decorators to old names for compatibility
compliance_create_required = create_compliance_required
compliance_edit_required = edit_compliance_required
compliance_approve_required = approve_compliance_required
compliance_view_required = view_all_compliance_required
compliance_analytics_required = compliance_performance_analytics_required

# Map other operations to main features
compliance_delete_required = edit_compliance_required
compliance_toggle_required = edit_compliance_required
compliance_deactivate_required = edit_compliance_required
compliance_clone_required = create_compliance_required
compliance_review_required = approve_compliance_required
compliance_dashboard_required = view_all_compliance_required
compliance_versioning_required = view_all_compliance_required
compliance_export_required = view_all_compliance_required
compliance_kpi_required = compliance_performance_analytics_required
compliance_framework_required = view_all_compliance_required
compliance_policy_required = view_all_compliance_required
compliance_subpolicy_required = view_all_compliance_required
compliance_audit_required = view_all_compliance_required
compliance_notification_required = view_all_compliance_required
compliance_category_required = edit_compliance_required
compliance_business_unit_required = edit_compliance_required


# =====================================================
# EVENT MODULE DECORATORS
# =====================================================

def event_view_all_required(view_func):
    """
    Decorator to require view_all_event permission
    """
    def wrapper(request, *args, **kwargs):
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not RBACUtils.has_event_permission(user_id, 'view_all'):
            return JsonResponse({'error': 'Insufficient permissions to view all events'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def event_view_module_required(view_func):
    """
    Decorator to require view_module_event permission
    """
    def wrapper(request, *args, **kwargs):
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not RBACUtils.has_event_permission(user_id, 'view_module'):
            return JsonResponse({'error': 'Insufficient permissions to view module events'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def event_create_required(view_func):
    """
    Decorator to require create_event permission
    """
    def wrapper(request, *args, **kwargs):
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not RBACUtils.has_event_permission(user_id, 'create'):
            return JsonResponse({'error': 'Insufficient permissions to create events'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def event_edit_required(view_func):
    """
    Decorator to require edit_event permission
    """
    def wrapper(request, *args, **kwargs):
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not RBACUtils.has_event_permission(user_id, 'edit'):
            return JsonResponse({'error': 'Insufficient permissions to edit events'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def event_approve_required(view_func):
    """
    Decorator to require approve_event permission
    """
    def wrapper(request, *args, **kwargs):
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not RBACUtils.has_event_permission(user_id, 'approve'):
            return JsonResponse({'error': 'Insufficient permissions to approve events'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def event_reject_required(view_func):
    """
    Decorator to require reject_event permission
    """
    def wrapper(request, *args, **kwargs):
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not RBACUtils.has_event_permission(user_id, 'reject'):
            return JsonResponse({'error': 'Insufficient permissions to reject events'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def event_archive_required(view_func):
    """
    Decorator to require archive_event permission
    """
    def wrapper(request, *args, **kwargs):
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not RBACUtils.has_event_permission(user_id, 'archive'):
            return JsonResponse({'error': 'Insufficient permissions to archive events'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def event_analytics_required(view_func):
    """
    Decorator to require event_performance_analytics permission
    """
    def wrapper(request, *args, **kwargs):
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not RBACUtils.has_event_permission(user_id, 'analytics'):
            return JsonResponse({'error': 'Insufficient permissions to view event analytics'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

# Alias decorators for common operations
event_view_required = event_view_all_required
event_dashboard_required = event_view_all_required
event_queue_required = event_view_all_required
event_calendar_required = event_view_all_required
event_export_required = event_view_all_required

# Map other operations to main features
event_delete_required = event_edit_required
event_update_required = event_edit_required
event_status_required = event_edit_required

