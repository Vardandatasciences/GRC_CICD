"""
Consent Management Decorator
Common module for enforcing consent requirements across the GRC system
"""

from functools import wraps
from rest_framework.response import Response
from rest_framework import status as http_status
from ...models import ConsentConfiguration
import logging

logger = logging.getLogger(__name__)


def require_consent(action_type):
    """
    Decorator to enforce consent requirements for specific actions
    
    Usage:
        @require_consent('create_policy')
        def create_policy_view(request):
            # Your view logic here
            pass
    
    How it works:
    1. Checks if consent is configured and enabled for the action in the database
    2. Expects the request to include a 'consent_accepted' flag and 'consent_config_id'
    3. If consent is required but not provided, returns a 403 error
    4. If consent is properly accepted, allows the request to proceed
    
    Args:
        action_type (str): The action type (e.g., 'create_policy', 'upload_audit')
    
    Returns:
        Decorated function that enforces consent
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            try:
                # Get framework_id from request
                framework_id = None
                
                # Try multiple sources for framework_id
                if request.method == 'POST' or request.method == 'PUT':
                    framework_id = request.data.get('framework_id') or request.data.get('FrameworkId')
                elif request.method == 'GET':
                    framework_id = request.GET.get('framework_id') or request.GET.get('FrameworkId')
                
                # Try to get from session if not in request
                if not framework_id:
                    framework_id = request.session.get('framework_id') or request.session.get('selected_framework_id')
                
                # If no framework_id found, allow the request (backward compatibility)
                if not framework_id:
                    logger.warning(f"[Consent] No framework_id found for action {action_type}. Allowing request to proceed.")
                    return view_func(request, *args, **kwargs)
                
                # Check if consent is required for this action
                try:
                    consent_config = ConsentConfiguration.objects.get(
                        action_type=action_type,
                        framework_id=framework_id
                    )
                    
                    # If consent is not enabled, allow the request
                    if not consent_config.is_enabled:
                        logger.debug(f"[Consent] Consent not enabled for {action_type}. Allowing request.")
                        return view_func(request, *args, **kwargs)
                    
                    # Consent is enabled - check if user has accepted
                    consent_accepted = request.data.get('consent_accepted', False) if request.method in ['POST', 'PUT'] else False
                    consent_config_id = request.data.get('consent_config_id') if request.method in ['POST', 'PUT'] else None
                    
                    if not consent_accepted or not consent_config_id:
                        logger.warning(f"[Consent] Consent required but not provided for {action_type}")
                        return Response({
                            'status': 'error',
                            'error': 'CONSENT_REQUIRED',
                            'message': 'Consent is required for this action',
                            'consent_required': True,
                            'consent_config': {
                                'config_id': consent_config.config_id,
                                'action_type': consent_config.action_type,
                                'action_label': consent_config.action_label,
                                'consent_text': consent_config.consent_text
                            }
                        }, status=http_status.HTTP_403_FORBIDDEN)
                    
                    # Verify the consent_config_id matches
                    if int(consent_config_id) != consent_config.config_id:
                        logger.error(f"[Consent] Consent config ID mismatch for {action_type}")
                        return Response({
                            'status': 'error',
                            'message': 'Invalid consent configuration'
                        }, status=http_status.HTTP_400_BAD_REQUEST)
                    
                    # Consent is properly accepted - allow the request
                    logger.info(f"[Consent] Consent verified for {action_type}. Proceeding with request.")
                    return view_func(request, *args, **kwargs)
                
                except ConsentConfiguration.DoesNotExist:
                    # No consent configuration exists - allow the request (backward compatibility)
                    logger.debug(f"[Consent] No consent configuration found for {action_type}. Allowing request.")
                    return view_func(request, *args, **kwargs)
            
            except Exception as e:
                logger.error(f"[Consent] Error in consent decorator: {str(e)}")
                # In case of error, allow the request to proceed (fail open for availability)
                return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


def check_consent_programmatically(action_type, framework_id):
    """
    Programmatically check if consent is required for an action
    Useful for non-decorator use cases
    
    Args:
        action_type (str): The action type
        framework_id (int): The framework ID
    
    Returns:
        tuple: (is_required, config_dict or None)
    """
    try:
        consent_config = ConsentConfiguration.objects.get(
            action_type=action_type,
            framework_id=framework_id
        )
        
        if consent_config.is_enabled:
            return True, {
                'config_id': consent_config.config_id,
                'action_type': consent_config.action_type,
                'action_label': consent_config.action_label,
                'consent_text': consent_config.consent_text
            }
        else:
            return False, None
    
    except ConsentConfiguration.DoesNotExist:
        return False, None
    except Exception as e:
        logger.error(f"Error checking consent: {str(e)}")
        return False, None

