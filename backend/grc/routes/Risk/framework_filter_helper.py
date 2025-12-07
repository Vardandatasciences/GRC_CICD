"""
Helper module for applying framework-based filtering to risk queries
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
                        print(f"✅ [RISK] Found user_id in JWT token: {user_id}")
                except Exception as jwt_error:
                    print(f"⚠️ [RISK] JWT extraction failed: {str(jwt_error)}")
        
        # If still no user_id, use default user for testing
        if not user_id:
            user_id = '1'  # Default to user ID 1 for testing
            print(f"⚠️ [RISK] No user ID found - using default user ID: {user_id}")
        
        # Get framework from context
        framework_id = get_framework_context(user_id)
        
        if framework_id:
            print(f"✅ [RISK] Framework filter active: {framework_id} for user {user_id}")
        else:
            print(f"ℹ️ [RISK] No framework filter (All frameworks selected) for user {user_id}")
        
        return framework_id
        
    except Exception as e:
        print(f"❌ [RISK] Error getting framework filter: {str(e)}")
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
            print(f"📊 [RISK] No framework filter - returning all results")
            return queryset
        
        # Apply framework filter
        filter_kwargs = {framework_field: framework_id}
        filtered_queryset = queryset.filter(**filter_kwargs)
        
        count = filtered_queryset.count()
        print(f"📊 [RISK] Framework filter applied: {framework_id}, Results: {count}")
        
        return filtered_queryset
        
    except Exception as e:
        print(f"❌ [RISK] Error applying framework filter: {str(e)}")
        # Return original queryset on error
        return queryset


def apply_framework_filter_with_relation(queryset: QuerySet, request, framework_field: str = 'FrameworkId_id') -> QuerySet:
    """
    Apply framework filter to a Django queryset where framework is a foreign key.
    
    Args:
        queryset: The Django queryset to filter
        request: The Django request object
        framework_field: The field name to filter on (default: 'FrameworkId_id' for FK relations)
        
    Returns:
        Filtered queryset if framework is selected, original queryset if "All" is selected
    """
    return apply_framework_filter(queryset, request, framework_field)


def apply_framework_filter_to_risk_instances(queryset: QuerySet, request) -> QuerySet:
    """
    Apply framework filter to RiskInstance queryset through Risk relation.
    
    Args:
        queryset: The RiskInstance queryset to filter
        request: The Django request object
        
    Returns:
        Filtered queryset if framework is selected, original queryset if "All" is selected
    """
    try:
        framework_id = get_active_framework_filter(request)
        
        # If no framework filter (All selected), return original queryset
        if framework_id is None:
            print(f"📊 [RISK] No framework filter - returning all risk instances")
            return queryset
        
        # Apply framework filter through Risk relation
        # RiskInstance -> RiskId (FK to Risk) -> FrameworkId (FK to Framework)
        filtered_queryset = queryset.filter(RiskId__FrameworkId=framework_id)
        
        count = filtered_queryset.count()
        print(f"📊 [RISK] Framework filter applied to risk instances: {framework_id}, Results: {count}")
        
        return filtered_queryset
        
    except Exception as e:
        print(f"❌ [RISK] Error applying framework filter to risk instances: {str(e)}")
        # Return original queryset on error
        return queryset


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


def get_framework_sql_filter(request) -> tuple:
    """
    Get SQL WHERE clause and parameters for framework filtering in raw SQL queries.
    
    Args:
        request: The Django request object
        
    Returns:
        Tuple of (where_clause: str, params: dict)
        Example: ("AND r.FrameworkId = %(framework_id)s", {"framework_id": 1})
        Or: ("", {}) if no filter should be applied
    """
    try:
        framework_id = get_active_framework_filter(request)
        
        if framework_id is None:
            print(f"📊 [RISK] No framework filter for SQL query")
            return ("", {})
        
        print(f"📊 [RISK] Adding framework SQL filter: {framework_id}")
        return ("AND r.FrameworkId = %(framework_id)s", {"framework_id": framework_id})
        
    except Exception as e:
        print(f"❌ [RISK] Error getting framework SQL filter: {str(e)}")
        return ("", {})

