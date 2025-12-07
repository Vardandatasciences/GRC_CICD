import jwt
import logging
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import Users
from .authentication import verify_jwt_token
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    JWT Authentication Middleware
    Verifies JWT tokens and sets user in request
    Supports both JWT and session authentication
    """
    
    def process_request(self, request):
        """Process incoming request and verify JWT token or session"""
        
        # Skip authentication for certain paths
        skip_paths = [
            '/api/login/',
            '/api/jwt/login/',
            '/api/jwt/refresh/',
            '/api/jwt/verify/',
            '/api/jwt/accept-consent/',
            '/api/jwt/test-consent-simple/',
            '/media/',  # Allow access to media files without authentication
            '/api/risks-for-dropdown/',  # Allow access to risks dropdown without authentication
            '/api/risks/',  # Temporarily allow access to risks creation without authentication for testing
            '/oauth/callback/',  # Allow OAuth callbacks without authentication
            '/api/register/',
            '/api/send-otp/',
            '/api/verify-otp/',
            '/api/reset-password/',
            '/api/get-user-email/',
            '/admin/',
            '/api/test-connection/',
            '/api/departments/',
            '/api/rbac/roles/',
            '/api/policy-categories/',
            '/api/frameworks/',
            '/api/frameworks/rejected/',
            '/api/frameworks/approved-active/',  # Skip authentication for approved frameworks (home page)
            '/api/frameworks/get-selected/',  # Skip authentication for getting selected framework (home page)
            '/api/frameworks/set-selected/',  # Skip authentication for setting selected framework (home page)
            '/api/home/policies-by-status-public/',  # Skip authentication for public home page policies
            '/api/get-notifications/',
            '/api/push-notification/',
            '/jwt/refresh/',
            '/api/test-submit-review/',  # Add test endpoint to skip list
            '/api/policies/',  # Skip authentication for policy endpoints temporarily
            '/api/tailoring/',  # Skip authentication for tailoring endpoints temporarily
            '/api/policy-approvals/',  # Skip authentication for policy approval endpoints temporarily
            '/api/users/',  # Skip authentication for users endpoint
            '/api/policy-acknowledgements/',  # Skip authentication for policy acknowledgement endpoints
            # '/api/generate-audit-report/',  # Re-enabled authentication for audit report generation
            # External Integration endpoints - some require auth, some don't
            '/api/jira/',
            '/api/test-integration-auth/',
            '/api/streamline/',
            # BambooHR integration endpoints - no authentication required
            '/api/bamboohr/',
            # Public, read-only endpoints
            '/api/compliance/frameworks/public/',
            '/api/audits/public/',
            '/api/compliance/all-for-audit-management/public/',
            # Checked sections endpoints
            '/api/checked-sections/',
            '/api/checked-sections/pdf/',  # Allow PDF access without authentication
            # Save endpoints - allow without authentication for now
            '/api/save-complete-policy-package/',
            '/api/save-framework-to-database/',
            '/api/risk/analytics-with-filters/',
            '/api/risk/dashboard-with-filters/',
            '/api/risk/frameworks-for-filter/',
            '/api/risk/policies-for-filter/',
            '/risk/frameworks-for-filter/',
            '/risk/policies-for-filter/',
            # Document endpoints - allow without authentication
            '/api/documents/',
            '/api/events/archived/',  # Skip authentication for archived events endpoints
            '/api/events/archived-queue-items/',  # Skip authentication for archived queue items endpoints
            '/api/events/', 
            '/api/upload-evidence-file/',  # Skip authentication for evidence file uploads (matches existing file upload pattern)
            '/api/incident-categories/',
            '/api/upload-risk-evidence-file/',  # Skip authentication for incident categories endpoints
            # Risk AI Document Ingestion endpoints - skip authentication for testing
            '/api/ai-risk-doc-upload/',
            '/api/ai-risk-save/',
            '/api/ai-risk-test/',
            '/api/ai-risk-test-upload/',
            # Risk Instance AI Document Ingestion endpoints - skip authentication (no permission required)
            '/api/ai-risk-instance-upload/',
            '/api/ai-risk-instance-save/',
            '/api/ai-risk-instance-test/',
            # Incident AI Document Ingestion endpoints - skip authentication (no permission required)
            '/api/ai-incident-upload/',
            '/api/ai-incident-save/',
            '/api/ai-incident-test/',
            # AI Upload endpoints - allow without authentication for default data loading
            '/api/ai-upload/',  # Allow all AI upload endpoints including load-default-data
            # Risk KPI endpoints - allow without authentication for development
            '/api/risk/kpi-data/',
            '/api/risk/active-risks-kpi/',
            '/api/risk/exposure-trend/',
            '/api/risk/reduction-trend/',
            '/api/risk/high-criticality/',
            '/api/risk/mitigation-completion-rate/',
            '/api/risk/avg-remediation-time/',
            '/api/risk/recurrence-rate/',
            '/api/risk/avg-incident-response-time/',
            '/api/risk/classification-accuracy/',
            '/api/risk/severity/',
            '/api/risk/exposure-score/',
            '/api/risk/assessment-frequency/',
            '/api/risk/assessment-consensus/',
            '/api/risk/identification-rate/',
            '/api/risk/register-update-frequency/',
            '/api/risk/recurrence-probability/',
            '/api/risk/tolerance-thresholds/',
            '/api/risk/appetite/',
            '/auth/sentinel/',
            '/auth/sentinel/callback/',
            '/api/sentinel/status/',
            '/api/sentinel/',

        ]
        
        # Check if path should be skipped
        path = request.path_info
        
        # Special handling for OAuth callback - exact match
        if path == '/oauth/callback' or path == '/oauth/callback/':
            #logger.debug(f"[JWT Middleware] Skipping authentication for OAuth callback: {path}")
            return None
        # Special handling for Gmail OAuth callback - skip authentication
        if path.startswith('/api/gmail/oauth-callback'):
            #logger.debug(f"[JWT Middleware] Skipping authentication for Gmail OAuth callback: {path}")
            return None
       
        # Special handling for Gmail test headers - skip authentication for debugging (temporary)
        if path.startswith('/api/gmail/test-headers'):
            #logger.debug(f"[JWT Middleware] Skipping authentication for Gmail test headers: {path}")
            return None
        # Special handling for external applications - skip all external app endpoints
        if path.startswith('/api/external-applications/'):
            #logger.debug(f"[JWT Middleware] Skipping authentication for external applications: {path}")
            return None
        
        # Check other skip paths
        if any(skip_path in path for skip_path in skip_paths):
            #logger.debug(f"[JWT Middleware] Skipping authentication for path: {path}")
            return None
        
        # Try JWT authentication first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            #logger.debug(f"[JWT Middleware] Processing JWT token for path: {path}")
            #logger.debug(f"[JWT Middleware] Token length: {len(token)}")
            #logger.debug(f"[JWT Middleware] Token starts with: {token[:20]}...")
            #logger.debug(f"[JWT Middleware] Full Authorization header: {auth_header}")
            
            try:
                # Verify JWT token using custom verification (since tokens are generated with custom method)
                payload = verify_jwt_token(token)
                user_id = payload.get('user_id') if payload else None
                
                if payload and user_id:
                    logger.debug(f"[JWT Middleware] Successfully decoded token with custom verification, user_id: {user_id}")
                else:
                    logger.warning(f"[JWT Middleware] No user_id in JWT payload for path: {path}")
                    return JsonResponse({'error': 'Invalid token payload'}, status=401)
                
                if payload and user_id:
                    # Get user from database
                    user = Users.objects.get(UserId=user_id)
                    
                    # Check if user is active
                    is_active = user.IsActive
                    if isinstance(is_active, str):
                        is_active = is_active.upper() == 'Y'
                    elif isinstance(is_active, bool):
                        is_active = is_active
                    else:
                        is_active = False
                    
                    if is_active:
                        # Set user in request for Django REST Framework
                        request.user = user
                        #logger.info(f"[JWT Middleware] User {user.UserName} (ID: {user.UserId}) authenticated via JWT for {request.method} {path}")
                        return None
                    else:
                        logger.warning(f"[JWT Middleware] Inactive user {user.UserName} (ID: {user.UserId}) attempted access")
                        return JsonResponse({'error': 'User account is inactive'}, status=401)
                else:
                    logger.warning(f"[JWT Middleware] No user_id in JWT payload for path: {path}")
                    return JsonResponse({'error': 'Invalid token payload'}, status=401)
            except Users.DoesNotExist:
                logger.warning(f"[JWT Middleware] User not found in database for path: {path}")
                return JsonResponse({'error': 'User not found'}, status=401)
            except Exception as e:
                logger.error(f"[JWT Middleware] JWT authentication error for path {path}: {str(e)}")
                logger.error(f"[JWT Middleware] Exception type: {type(e).__name__}")
                logger.error(f"[JWT Middleware] Exception details: {str(e)}")
                return JsonResponse({'error': 'Authentication error'}, status=401)
        
        # Try session authentication as fallback
        elif request.session.get('user_id'):
            user_id = request.session['user_id']
            #logger.debug(f"[JWT Middleware] Processing session authentication for user ID: {user_id}")
            
            try:
                user = Users.objects.get(UserId=user_id)
                
                # Check if user is active
                is_active = user.IsActive
                if isinstance(is_active, str):
                    is_active = is_active.upper() == 'Y'
                elif isinstance(is_active, bool):
                    is_active = is_active
                else:
                    is_active = False
                
                if is_active:
                    # Set user in request for Django REST Framework
                    request.user = user
                    #logger.info(f"[JWT Middleware] User {user.UserName} (ID: {user.UserId}) authenticated via session for {request.method} {path}")
                    return None
                else:
                    logger.warning(f"[JWT Middleware] Inactive user {user.UserName} (ID: {user.UserId}) attempted access via session")
                    return JsonResponse({'error': 'User account is inactive'}, status=401)
                    
            except Users.DoesNotExist:
                logger.warning(f"[JWT Middleware] Session user not found in database: {user_id}")
                return JsonResponse({'error': 'User not found'}, status=401)
            except Exception as e:
                logger.error(f"[JWT Middleware] Session authentication error: {str(e)}")
                return JsonResponse({'error': 'Authentication error'}, status=401)
        
        # No authentication found
        logger.warning(f"[JWT Middleware] No authentication found for path: {path}")
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    def process_response(self, request, response):
        """Process outgoing response"""
        # Add CORS headers if needed
        if hasattr(response, 'headers'):
            # Instead of hardcoding '*', use the Origin from the request
            origin = request.headers.get('Origin')
            if origin:
                response.headers['Access-Control-Allow-Origin'] = origin
            else:
                response.headers['Access-Control-Allow-Origin'] = '*'
                
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRFToken'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response

class CORSMiddleware(MiddlewareMixin):
    """
    CORS Middleware for handling preflight requests
    """
    
    def process_request(self, request):
        """Handle preflight OPTIONS requests"""
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            # Get the Origin header from the request
            origin = request.headers.get('Origin')
            if origin:
                response['Access-Control-Allow-Origin'] = origin
            else:
                response['Access-Control-Allow-Origin'] = '*'
                
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRFToken'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response
        return None

class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Audit Logging Middleware
    Logs user actions for audit purposes
    """
    
    def process_request(self, request):
        """Log request details"""
        # Skip logging for certain paths
        skip_paths = [
            '/api/jwt/verify/',
            '/api/test-connection/',
            '/admin/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Get user from request
        user = getattr(request, 'user', None)
        if user and hasattr(user, 'UserId'):
            logger.info(f"User {user.UserName} (ID: {user.UserId}) accessing {request.method} {request.path}")
        
        return None
