"""
Framework context module for storing and retrieving framework ID
This provides an alternative to session-based storage
"""
import threading
from typing import Dict, Any, Optional

# Thread-local storage for framework context
_local_storage = threading.local()

# In-memory cache as fallback
_memory_cache: Dict[str, Dict[str, Any]] = {}

def set_framework_context(user_id: str, framework_id: str, request=None) -> None:
    """
    Store framework ID for a user
    
    Args:
        user_id: The user ID
        framework_id: The framework ID
        request: Optional Django request object to also clear session
    """
    # Normalize user_id and framework_id to strings for consistency
    user_id_str = str(user_id)
    framework_id_str = str(framework_id)
    
    # Store in thread-local storage
    if not hasattr(_local_storage, 'framework_context'):
        _local_storage.framework_context = {}
    
    _local_storage.framework_context[user_id_str] = framework_id_str
    
    # Also store in memory cache as fallback
    if user_id_str not in _memory_cache:
        _memory_cache[user_id_str] = {}
    
    _memory_cache[user_id_str]['framework_id'] = framework_id_str
    
    # Clear session if provided (to prevent conflicts)
    if request and hasattr(request, 'session'):
        try:
            if 'selected_framework_id' in request.session:
                del request.session['selected_framework_id']
            if 'grc_framework_selected' in request.session:
                del request.session['grc_framework_selected']
            request.session.save()
            print(f"🧹 DEBUG: Cleared old session data when setting new framework")
        except Exception as e:
            print(f"⚠️ DEBUG: Could not clear session: {str(e)}")
    
    print(f"✅ Framework context set: User {user_id_str}, Framework {framework_id_str}")
    print(f"🔍 Thread-local keys: {list(_local_storage.framework_context.keys()) if hasattr(_local_storage, 'framework_context') else []}")
    print(f"🔍 Memory cache keys: {list(_memory_cache.keys())}")
    print(f"🔍 Memory cache: {_memory_cache}")

def get_framework_context(user_id: str) -> Optional[str]:
    """
    Get framework ID for a user
    
    Args:
        user_id: The user ID
        
    Returns:
        The framework ID or None if not found
    """
    # Ensure user_id is a string for consistent comparison
    user_id_str = str(user_id)
    
    # Try thread-local storage first - check all key types
    if hasattr(_local_storage, 'framework_context'):
        for key, value in _local_storage.framework_context.items():
            if str(key) == user_id_str:
                print(f"✅ Framework context from thread-local: User {user_id}, Framework {value}")
                return value
    
    # Fall back to memory cache - check all key types
    for key, value_dict in _memory_cache.items():
        if str(key) == user_id_str and 'framework_id' in value_dict:
            framework_id = value_dict['framework_id']
            print(f"✅ Framework context from memory cache: User {user_id}, Framework {framework_id}")
            return framework_id
    
    print(f"❌ Framework context not found for user {user_id}")
    return None

def clear_framework_context(user_id: str, request=None) -> None:
    """
    Clear framework ID for a user
    
    Args:
        user_id: The user ID
        request: Optional Django request object to also clear session
    """
    print(f"🧹 DEBUG: clear_framework_context called for user {user_id}")
    
    # Ensure user_id is a string for consistent comparison
    user_id_str = str(user_id)
    
    # Clear from thread-local storage - check both string and original format
    if hasattr(_local_storage, 'framework_context'):
        # Try to find and clear the user's context regardless of type
        keys_to_delete = []
        for key in _local_storage.framework_context.keys():
            if str(key) == user_id_str:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            old_value = _local_storage.framework_context[key]
            del _local_storage.framework_context[key]
            print(f"🧹 DEBUG: Cleared from thread-local storage: {old_value} (key: {key})")
    
    # Clear from memory cache - check both string and original format
    keys_to_delete = []
    for key in list(_memory_cache.keys()):
        if str(key) == user_id_str and 'framework_id' in _memory_cache[key]:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        old_value = _memory_cache[key]['framework_id']
        del _memory_cache[key]['framework_id']
        print(f"🧹 DEBUG: Cleared from memory cache: {old_value} (key: {key})")
    
    # Clear from session if provided
    if request and hasattr(request, 'session'):
        try:
            if 'selected_framework_id' in request.session:
                del request.session['selected_framework_id']
                print(f"🧹 DEBUG: Cleared 'selected_framework_id' from session")
            if 'grc_framework_selected' in request.session:
                del request.session['grc_framework_selected']
                print(f"🧹 DEBUG: Cleared 'grc_framework_selected' from session")
            request.session.save()
        except Exception as e:
            print(f"⚠️ DEBUG: Could not clear session: {str(e)}")
    
    print(f"✅ Framework context cleared for user {user_id}")
    print(f"🔍 DEBUG: Thread-local after clear: {getattr(_local_storage, 'framework_context', {})}")
    print(f"🔍 DEBUG: Memory cache after clear: {_memory_cache}")
