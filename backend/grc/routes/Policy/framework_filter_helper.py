"""
Helper module for applying framework-based filtering to policy queries
This centralizes the logic for getting framework context and applying filters
"""
from typing import Optional
from django.db.models import QuerySet
from ...framework_context import get_framework_context


def get_active_framework_filter(request) -> Optional[str]:
    """
    Get the active framework filter from session/context.
    Uses the same comprehensive user ID extraction as get_selected_framework.
    
    Args:
        request: The Django request object
        
    Returns:
        Framework ID if a specific framework is selected, None if "All" is selected
    """
    try:
        # Try to get user_id from various sources (same as get_selected_framework)
        user_id = None
        
        # Try from session
        session_user_id = request.session.get('user_id') or request.session.get('grc_user_id')
        if session_user_id:
            user_id = session_user_id
            print(f"✅ DEBUG: Found user_id in session: {user_id}")
        
        # If not in session, try from request user
        if not user_id and hasattr(request, 'user') and hasattr(request.user, 'id'):
            user_id = request.user.id
            print(f"✅ DEBUG: Found user_id in request.user: {user_id}")
        
        # If not in request.user, try from query parameters
        if not user_id and request.GET.get('userId'):
            user_id = request.GET.get('userId')
            print(f"✅ DEBUG: Found user_id in query parameters: {user_id}")
        
        # If still no user_id, try JWT token
        if not user_id:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                from ...authentication import verify_jwt_token
                token = auth_header.split(' ')[1]
                try:
                    payload = verify_jwt_token(token)
                    if payload and 'user_id' in payload:
                        user_id = payload['user_id']
                        print(f"✅ DEBUG: Found user_id in JWT token: {user_id}")
                except Exception as jwt_error:
                    print(f"⚠️ DEBUG: JWT extraction failed: {str(jwt_error)}")
        
        if not user_id:
            print("⚠️ No user ID found - returning no framework filter")
            return None
        
        # Try to get framework_id from various sources (same as get_selected_framework)
        framework_id = None
        
        # Try from framework context FIRST (more reliable and up-to-date)
        if user_id:
            framework_id = get_framework_context(str(user_id))
            if framework_id:
                print(f"✅ DEBUG: Found framework_id in framework context: {framework_id}")
        
        # Fall back to session if not in framework context (for backward compatibility)
        if not framework_id:
            session_framework_id = request.session.get('selected_framework_id') or request.session.get('grc_framework_selected')
            if session_framework_id:
                framework_id = session_framework_id
                print(f"⚠️ DEBUG: Found framework_id in session (fallback): {framework_id}")
        
        # If still no framework_id, try query parameters
        if not framework_id and request.GET.get('frameworkId'):
            framework_id = request.GET.get('frameworkId')
            print(f"✅ DEBUG: Found framework_id in query parameters: {framework_id}")
        
        if framework_id:
            print(f"✅ Framework filter active: {framework_id} for user {user_id}")
        else:
            print(f"ℹ️ No framework filter (All frameworks selected) for user {user_id}")
        
        # Debug: Show all session keys to help troubleshoot
        if hasattr(request, 'session'):
            session_keys = list(request.session.keys())
            print(f"🔍 DEBUG: Session keys: {session_keys}")
            for key in session_keys:
                if 'framework' in key.lower() or 'selected' in key.lower():
                    print(f"🔍 DEBUG: Session key '{key}': {request.session.get(key)}")
        
        return framework_id
        
    except Exception as e:
        print(f"❌ Error getting framework filter: {str(e)}")
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
            print(f"📊 No framework filter - returning all results")
            return queryset
        
        # Apply framework filter
        filter_kwargs = {framework_field: framework_id}
        filtered_queryset = queryset.filter(**filter_kwargs)
        
        count = filtered_queryset.count()
        print(f"📊 Framework filter applied: {framework_id}, Results: {count}")
        
        return filtered_queryset
        
    except Exception as e:
        print(f"❌ Error applying framework filter: {str(e)}")
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

