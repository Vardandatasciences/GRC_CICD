import jwt
import json
import logging
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.core.cache import cache

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.hashers import make_password, check_password
from .models import Users, GRCLog
from .rbac.utils import RBACUtils

logger = logging.getLogger(__name__)

# JWT Settings
JWT_SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = timedelta(hours=1)  # 1 hour
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)  # 7 days

def generate_jwt_tokens(user):
    """Generate JWT access and refresh tokens for a user"""
    try:
        # Create refresh token
        refresh = RefreshToken()
        refresh['user_id'] = user.UserId
        refresh['username'] = user.UserName
        refresh['email'] = user.Email
        refresh['first_name'] = user.FirstName
        refresh['last_name'] = user.LastName
        
        # Create access token
        access_token = refresh.access_token
        access_token['user_id'] = user.UserId
        access_token['username'] = user.UserName
        access_token['email'] = user.Email
        access_token['first_name'] = user.FirstName
        access_token['last_name'] = user.LastName
        
        return {
            'access': str(access_token),
            'refresh': str(refresh),
            'access_token_expires': access_token.current_time + JWT_ACCESS_TOKEN_LIFETIME,
            'refresh_token_expires': refresh.current_time + JWT_REFRESH_TOKEN_LIFETIME
        }
    except Exception as e:
        logger.error(f"Error generating JWT tokens: {str(e)}")
        raise

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error verifying JWT token: {str(e)}")
        return None

def get_user_from_token(token):
    """Get user from JWT token"""
    try:
        payload = verify_jwt_token(token)
        if payload and 'user_id' in payload:
            user = Users.objects.get(UserId=payload['user_id'])
            return user
        return None
    except Users.DoesNotExist:
        logger.warning(f"User not found for token payload: {payload}")
        return None
    except Exception as e:
        logger.error(f"Error getting user from token: {str(e)}")
        return None

@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_login(request):
    """JWT Login endpoint with rate limiting and account lockout"""
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')
        login_type = data.get('login_type', 'username')  # Default to username if not specified
        
        if not username or not password:
            return Response({
                'status': 'error',
                'message': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========================================
        # RATE LIMITING - PER IP
        # ========================================
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        ip_cache_key = f"login_rate_limit_ip_{client_ip}"
        ip_attempts = cache.get(ip_cache_key, 0)
        
        if ip_attempts >= 10:  # Max 10 login attempts per minute per IP
            return Response({
                'status': 'error',
                'message': 'Too many login attempts from this IP. Please wait 1 minute and try again.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Increment IP counter
        cache.set(ip_cache_key, ip_attempts + 1, 60)  # 60 seconds
        
        # ========================================
        # RATE LIMITING - PER USERNAME (LOCKOUT)
        # ========================================
        # Normalize username for cache key
        username_normalized = str(username).lower().strip()
        user_cache_key = f"login_failed_attempts_{username_normalized}"
        lockout_cache_key = f"login_locked_until_{username_normalized}"
        
        # Check if account is locked
        locked_until = cache.get(lockout_cache_key)
        if locked_until:
            remaining_seconds = int(locked_until - time.time())
            if remaining_seconds > 0:
                remaining_minutes = remaining_seconds // 60
                return Response({
                    'status': 'error',
                    'message': f'Account temporarily locked due to too many failed login attempts. Please try again in {remaining_minutes + 1} minute(s).',
                    'locked_until': remaining_seconds
                }, status=status.HTTP_403_FORBIDDEN)
            else:
                # Lock expired, clear it
                cache.delete(lockout_cache_key)
                cache.delete(user_cache_key)
        
        # Authenticate user with our custom user model based on login type
        user = None
        try:
            if login_type == 'userid':
                # Login with User ID
                user_id = int(username)  # Convert to integer
                candidate = Users.objects.get(UserId=user_id)
                logger.debug(f"User found by ID: {candidate.UserId} - {candidate.UserName}")
            else:
                # Login with Username (default)
                candidate = Users.objects.get(UserName=username)
                logger.debug(f"User found by username: {candidate.UserId} - {candidate.UserName}")

            # Check hashed password first
            if check_password(password, candidate.Password):
                user = candidate
            # Backward compatibility: migrate legacy plain-text passwords
            elif candidate.Password == password:
                candidate.Password = make_password(password)
                candidate.save(update_fields=['Password'])
                user = candidate
                logger.warning(f"Password for user {candidate.UserName} was stored in plain text and has been hashed.")
        except Users.DoesNotExist:
            user = None
        except ValueError:
            logger.warning(f"Login failed - invalid user ID format: {username}")
            return Response({
                'status': 'error',
                'message': 'Invalid user ID format. Please enter a valid number.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user:
            # ========================================
            # FAILED LOGIN - INCREMENT COUNTER & CHECK LOCKOUT
            # ========================================
            failed_attempts = cache.get(user_cache_key, 0) + 1
            cache.set(user_cache_key, failed_attempts, 900)  # Keep counter for 15 minutes
            
            if failed_attempts >= 5:
                # Lock account for 15 minutes
                lockout_time = time.time() + 900  # 15 minutes from now
                cache.set(lockout_cache_key, lockout_time, 900)
                cache.delete(user_cache_key)  # Clear attempt counter
                
                return Response({
                    'status': 'error',
                    'message': f'Too many failed login attempts. Account locked for 15 minutes. (Attempt {failed_attempts}/5)'
                }, status=status.HTTP_403_FORBIDDEN)
            
            return Response({
                'status': 'error',
                'message': f'Invalid {login_type} or password. ({failed_attempts}/5 attempts)'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is active
        is_active = user.IsActive
        if isinstance(is_active, str):
            is_active = is_active.upper() == 'Y'
        elif isinstance(is_active, bool):
            is_active = is_active
        else:
            is_active = False
            
        if not is_active:
            return Response({
                'status': 'error',
                'message': 'User account is inactive'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # ========================================
        # LICENSE KEY VALIDATION PROCESS - JWT LOGIN
        # ========================================
        if not getattr(settings, 'LICENSE_CHECK_ENABLED', True):
            logger.warning("🔕 LICENSE CHECK DISABLED via settings. Proceeding without external verification.")
        else:
            # Step 1: Check if user has a license key assigned
            license_verification_result = None
            if user.license_key:
                logger.info(f"🔐 LICENSE VALIDATION: User {user.UserName} has license key: {user.license_key[:10]}...")
                try:
                    # Step 2: Import and initialize the licensing system
                    from licensing_system import VardaanLicensingSystem
                    licensing_system = VardaanLicensingSystem()
                    logger.info(f"🔐 LICENSE VALIDATION: Licensing system initialized for user {user.UserName}")
                    # Step 3: Call external API to verify the license key
                    logger.info(f"🔐 LICENSE VALIDATION: Calling external API to verify license for user {user.UserName}")
                    license_verification_result = licensing_system.verify_license(user.license_key)
                    # Step 4: Check if license verification was successful
                    if not license_verification_result.get("success"):
                        logger.warning(f"❌ LICENSE VALIDATION FAILED: User {user.UserName} - {license_verification_result.get('error')}")
                        return Response({
                            'status': 'error',
                            'message': 'License verification failed. Please contact your administrator.',
                            'license_error': license_verification_result.get('error', 'Unknown license error')
                        }, status=status.HTTP_403_FORBIDDEN)
                    else:
                        logger.info(f"✅ LICENSE VALIDATION SUCCESS: User {user.UserName} license verified successfully")
                except Exception as license_error:
                    logger.error(f"❌ LICENSE VALIDATION ERROR: User {user.UserName} - {str(license_error)}")
                    return Response({
                        'status': 'error',
                        'message': 'License verification error. Please contact your administrator.',
                        'license_error': str(license_error)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Step 5: Handle case where user has no license key
                logger.warning(f"❌ LICENSE VALIDATION: User {user.UserName} has no license key assigned")
                return Response({
                    'status': 'error',
                    'message': 'No license key assigned to this user. Please contact your administrator.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # ========================================
        # SUCCESSFUL LOGIN - CLEAR FAILED ATTEMPT COUNTERS
        # ========================================
        cache.delete(user_cache_key)
        cache.delete(lockout_cache_key)
        
        # Generate JWT tokens
        tokens = generate_jwt_tokens(user)
        
        # Store user info in session for compatibility with consistent naming
        request.session['user_id'] = user.UserId
        request.session['username'] = user.UserName
        request.session['grc_user_id'] = user.UserId  # Backup key for RBAC
        request.session['grc_username'] = user.UserName
        
        # Initialize framework session keys if needed
        if 'grc_framework_selected' not in request.session:
            request.session['grc_framework_selected'] = None
        if 'selected_framework_id' not in request.session:
            request.session['selected_framework_id'] = None
        
        # CRITICAL: Explicitly save the session to persist changes
        request.session.save()
        
        logger.info(f"✅ JWT LOGIN SUCCESS: User {user.UserName} (ID: {user.UserId}) logged in successfully with license verification")
        logger.info(f"JWT login successful for user {user.UserName} (ID: {user.UserId}) using {login_type}")
        logger.info(f"🔑 Session key created: {request.session.session_key}")
        
        # Check if user has accepted consent
        # Handle both string and potential null/None values
        consent_accepted_value = str(user.consent_accepted) if user.consent_accepted is not None else '0'
        consent_required = consent_accepted_value != '1'
        
        return Response({
            'status': 'success',
            'message': 'Login successful',
            'license_verified': True,  # This indicates license validation was successful
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'access_token_expires': tokens['access_token_expires'].isoformat(),
            'refresh_token_expires': tokens['refresh_token_expires'].isoformat(),
             'consent_required': consent_required,
            'user': {
                'UserId': user.UserId,
                'UserName': user.UserName,
                'Email': user.Email,
                'FirstName': user.FirstName,
                'LastName': user.LastName,
                'IsActive': user.IsActive,
                'consent_accepted': consent_accepted_value,
                'license_key': user.license_key  # Include the validated license 
            }
        })
        
    except Exception as e:
        logger.error(f"JWT login error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Login failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_refresh(request):
    """JWT Refresh endpoint with rate limiting"""
    try:
        # Rate limiting: Allow max 100 refresh attempts per minute per IP for production
        # High limit to avoid blocking legitimate clients with multiple tabs/windows
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        cache_key = f"jwt_refresh_rate_limit_{client_ip}"
        
        # Check rate limit
        attempts = cache.get(cache_key, 0)
        if attempts >= 100:  # Very high limit to avoid false positives
            # Silently return 429 without logging to avoid terminal spam
            return Response({
                'status': 'error',
                'message': 'Too many refresh attempts. Please wait before trying again.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Increment rate limit counter
        cache.set(cache_key, attempts + 1, 60)  # 60 seconds
        
        data = request.data
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'status': 'error',
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify refresh token
        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh['user_id']
            user = Users.objects.get(UserId=user_id)

            # IMPORTANT: Blacklist the old refresh token so it cannot be reused
            try:
                refresh.blacklist()
            except Exception:
                # Silently handle blacklist errors - don't log to avoid terminal spam
                pass
            
            # Generate new tokens (SimpleJWT will rotate refresh tokens as configured)
            tokens = generate_jwt_tokens(user)
            
            # No logging for successful refresh to keep terminal clean
            
            return Response({
                'status': 'success',
                'message': 'Token refreshed successfully',
                'access_token': tokens['access'],
                'refresh_token': tokens['refresh'],
                'access_token_expires': tokens['access_token_expires'].isoformat(),
                'refresh_token_expires': tokens['refresh_token_expires'].isoformat()
            })
            
        except (InvalidToken, TokenError):
            # Invalid or blacklisted refresh token - silently return 401 without logging
            return Response({
                'status': 'error',
                'message': 'Invalid refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Users.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'User not found'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"JWT refresh error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Token refresh failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def jwt_logout(request):
    """JWT Logout endpoint"""
    try:
        # Clear session data
        request.session.flush()
        
        logger.info(f"JWT logout successful for user {getattr(request.user, 'UserName', 'Unknown')}")
        
        return Response({
            'status': 'success',
            'message': 'Logout successful'
        })
        
    except Exception as e:
        logger.error(f"JWT logout error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow any authenticated user
def accept_consent(request):
    """Accept user consent endpoint"""
    logger.info("=== ACCEPT CONSENT FUNCTION CALLED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    try:
        logger.info("Accept consent endpoint called")
        
        # Always get user from token since middleware is skipped for this endpoint
        auth_header = request.headers.get('Authorization')
        logger.info(f"Authorization header: {auth_header}")
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return Response({
                'status': 'error',
                'message': 'Authorization header with Bearer token is required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token = auth_header.split(' ')[1]
        logger.info(f"Extracted token: {token[:20]}...")
        user = get_user_from_token(token)
        logger.info(f"User from token: {user}")
        
        if not user:
            logger.error("User not found from token")
            return Response({
                'status': 'error',
                'message': 'Invalid or expired token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Update user consent status
        logger.info(f"Updating consent for user {user.UserName} from '{user.consent_accepted}' to '1'")
        user.consent_accepted = '1'
        user.save()
        
        logger.info(f"User {user.UserName} (ID: {user.UserId}) accepted consent successfully")
        
        return Response({
            'status': 'success',
            'message': 'Consent accepted successfully',
            'user': {
                'UserId': user.UserId,
                'UserName': user.UserName,
                'Email': user.Email,
                'FirstName': user.FirstName,
                'LastName': user.LastName,
                'consent_accepted': user.consent_accepted
            }
        })
        
    except Exception as e:
        logger.error(f"Accept consent error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to accept consent'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_user_from_jwt(request):
    """Helper function to get user from JWT token in request headers"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        try:
            user = Users.objects.get(UserId=user_id)
            return user
        except Users.DoesNotExist:
            return None
            
    except Exception as e:
        logger.error(f"JWT verification error: {str(e)}")
        return None

@api_view(['GET'])
@permission_classes([AllowAny])
def jwt_verify(request):
    """JWT Verify endpoint"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({
                'status': 'error',
                'message': 'Authorization header with Bearer token is required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            return Response({
                'status': 'error',
                'message': 'Invalid or expired token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user_id = payload.get('user_id')
        if not user_id:
            return Response({
                'status': 'error',
                'message': 'Invalid token payload'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = Users.objects.get(UserId=user_id)
            return Response({
                'status': 'success',
                'message': 'Token is valid',
                'user': {
                    'UserId': user.UserId,
                    'UserName': user.UserName,
                    'Email': user.Email,
                    'FirstName': user.FirstName,
                    'LastName': user.LastName
                }
            })
        except Users.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'User not found'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"JWT verify error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Token verification failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def test_consent_auth(request):
    """Test endpoint to verify authentication for consent"""
    logger.info("=== TEST CONSENT AUTH FUNCTION CALLED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    # Get user from request (set by middleware)
    user = getattr(request, 'user', None)
    logger.info(f"User from request: {user}")
    
    if user:
        return Response({
            'status': 'success',
            'message': 'Authentication working correctly',
            'user': {
                'UserId': user.UserId,
                'UserName': user.UserName,
                'Email': user.Email
            }
        })
    else:
        return Response({
            'status': 'error',
            'message': 'No user found in request'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def test_consent_simple(request):
    """Simple test endpoint for consent without authentication"""
    logger.info("=== TEST CONSENT SIMPLE FUNCTION CALLED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    return Response({
        'status': 'success',
        'message': 'Test consent endpoint is working',
        'timestamp': datetime.now().isoformat()
    })
