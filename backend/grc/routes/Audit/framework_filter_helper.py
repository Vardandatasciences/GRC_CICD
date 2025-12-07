"""
Helper module for applying framework-based filtering to audit queries
This centralizes the logic for getting framework context and applying filters
"""
from typing import Optional
from django.db.models import QuerySet
from ...framework_context import get_framework_context


def get_active_framework_filter(request) -> Optional[str]:
    """
    Get the active framework filter from session/context.
    
    Args:
        request: The Django request object
        
    Returns:
        Framework ID if a specific framework is selected, None if "All" is selected
    """
    try:
        # Try to get user ID from request
        user_id = None
        
        # Check authenticated user
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = str(request.user.id)
        # Fallback to session
        elif hasattr(request, 'session') and 'user_id' in request.session:
            user_id = str(request.session.get('user_id'))
        # Fallback to localStorage user_id passed in headers
        elif hasattr(request, 'headers') and 'X-User-Id' in request.headers:
            user_id = request.headers.get('X-User-Id')
        # Fallback to Authorization header with JWT token
        elif hasattr(request, 'headers') and 'Authorization' in request.headers:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    from ...authentication import verify_jwt_token
                    token = auth_header.split(' ')[1]
                    payload = verify_jwt_token(token)
                    if payload and 'user_id' in payload:
                        user_id = str(payload['user_id'])
                        print(f"✅ [AUDIT] Found user_id in JWT token: {user_id}")
                except Exception as jwt_error:
                    print(f"⚠️ [AUDIT] JWT extraction failed: {str(jwt_error)}")
        
        # If still no user_id, use default user for testing
        if not user_id:
            user_id = '1'  # Default to user ID 1 for testing
            print(f"⚠️ [AUDIT] No user ID found - using default user ID: {user_id}")
        
        # Get framework from context
        framework_id = get_framework_context(user_id)
        
        if framework_id:
            print(f"✅ [AUDIT] Framework filter active: {framework_id} for user {user_id}")
        else:
            print(f"ℹ️ [AUDIT] No framework filter (All frameworks selected) for user {user_id}")
        
        return framework_id
        
    except Exception as e:
        print(f"❌ [AUDIT] Error getting framework filter: {str(e)}")
        return None


def apply_framework_filter(queryset: QuerySet, request, framework_field: str = 'FrameworkId') -> QuerySet:
    """
    Apply framework filter to a Django queryset.
    
    Args:
        queryset: The Django queryset to filter
        request: The Django request object
        framework_field: The field name to filter on (default: 'FrameworkId')
        
    Returns:
        Filtered queryset if framework is selected, original queryset if "All" is selected
    """
    try:
        framework_id = get_active_framework_filter(request)
        
        # If no framework filter (All selected), return original queryset
        if framework_id is None:
            print(f"📊 [AUDIT] No framework filter - returning all results")
            return queryset
        
        # Apply framework filter
        filter_kwargs = {framework_field: framework_id}
        filtered_queryset = queryset.filter(**filter_kwargs)
        
        count = filtered_queryset.count()
        print(f"📊 [AUDIT] Framework filter applied: {framework_id}, Results: {count}")
        
        return filtered_queryset
        
    except Exception as e:
        print(f"❌ [AUDIT] Error applying framework filter: {str(e)}")
        # Return original queryset on error
        return queryset


def apply_framework_filter_to_audit_findings(queryset: QuerySet, request) -> QuerySet:
    """
    Apply framework filter to AuditFinding queryset.
    
    Args:
        queryset: The AuditFinding queryset to filter
        request: The Django request object
        
    Returns:
        Filtered queryset if framework is selected, original queryset if "All" is selected
    """
    return apply_framework_filter(queryset, request, 'FrameworkId')


def apply_framework_filter_to_audits(queryset: QuerySet, request) -> QuerySet:
    """
    Apply framework filter to Audit queryset.
    
    Args:
        queryset: The Audit queryset to filter
        request: The Django request object
        
    Returns:
        Filtered queryset if framework is selected, original queryset if "All" is selected
    """
    return apply_framework_filter(queryset, request, 'FrameworkId')


def get_framework_filter_info(request) -> dict:
    """
    Get information about the current framework filter state.
    
    Args:
        request: The Django request object
        
    Returns:
        Dictionary with filter information
    """
    framework_id = get_active_framework_filter(request)
    
    return {
        'is_filtered': framework_id is not None,
        'framework_id': framework_id,
        'filter_mode': 'specific' if framework_id else 'all'
    }


def get_framework_sql_filter(request, table_alias: str = 'a') -> tuple:
    """
    Get SQL WHERE clause and parameters for framework filtering in raw SQL queries.
    
    Args:
        request: The Django request object
        table_alias: The table alias used in the SQL query (default: 'a' for audit)
        
    Returns:
        Tuple of (where_clause: str, params: dict)
        Example: ("AND a.FrameworkId = %(framework_id)s", {"framework_id": 1})
        Or: ("", {}) if no filter should be applied
    """
    try:
        framework_id = get_active_framework_filter(request)
        
        if framework_id is None:
            print(f"📊 [AUDIT] No framework filter for SQL query")
            return ("", {})
        
        print(f"📊 [AUDIT] Adding framework SQL filter: {framework_id}")
        return (f"AND {table_alias}.FrameworkId = %(framework_id)s", {"framework_id": framework_id})
        
    except Exception as e:
        print(f"❌ [AUDIT] Error getting framework SQL filter: {str(e)}")
        return ("", {})




