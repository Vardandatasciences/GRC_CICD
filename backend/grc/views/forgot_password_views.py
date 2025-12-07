from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from ..forgot_password_service import ForgotPasswordService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def initiate_password_reset(request):
    """Initiate password reset process"""
    try:
        # Parse request data
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email address is required.'
            }, status=400)
        
        # Get client IP and user agent
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Initialize forgot password service
        forgot_password_service = ForgotPasswordService()
        
        # Initiate password reset
        result = forgot_password_service.initiate_password_reset(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Always return success message for security (don't reveal if user exists)
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'If an account with this email exists, you will receive a password reset OTP.'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'If an account with this email exists, you will receive a password reset OTP.'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in initiate_password_reset: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again later.'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def verify_otp_and_reset_password(request):
    """Verify OTP and reset password"""
    try:
        # Parse request data
        data = json.loads(request.body)
        email = data.get('email')
        otp = data.get('otp')
        new_password = data.get('new_password')
        
        # Validate required fields
        if not email or not otp or not new_password:
            return JsonResponse({
                'success': False,
                'message': 'Email, OTP, and new password are required.'
            }, status=400)
        
        # Validate password strength (basic validation)
        if len(new_password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 8 characters long.'
            }, status=400)
        
        # Get client IP and user agent
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Initialize forgot password service
        forgot_password_service = ForgotPasswordService()
        
        # Verify OTP and reset password
        result = forgot_password_service.verify_otp_and_reset_password(
            email=email,
            otp=otp,
            new_password=new_password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Password has been reset successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result['message']
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in verify_otp_and_reset_password: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again later.'
        }, status=500)

@require_http_methods(["GET"])
def check_otp_status(request):
    """Check if OTP is still valid"""
    try:
        email = request.GET.get('email')
        otp = request.GET.get('otp')
        
        if not email or not otp:
            return JsonResponse({
                'success': False,
                'message': 'Email and OTP are required.'
            }, status=400)
        
        # Initialize forgot password service
        forgot_password_service = ForgotPasswordService()
        
        # Validate OTP
        otp_validation = forgot_password_service.validate_otp(email, otp)
        
        return JsonResponse({
            'success': True,
            'valid': otp_validation['valid'],
            'message': 'OTP is valid.' if otp_validation['valid'] else 'OTP is invalid or expired.'
        })
        
    except Exception as e:
        logger.error(f"Error in check_otp_status: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while checking OTP status.'
        }, status=500)

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Class-based views for better organization
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordView(View):
    """Class-based view for forgot password functionality"""
    
    def post(self, request):
        """Handle POST request for initiating password reset"""
        return initiate_password_reset(request)

@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordView(View):
    """Class-based view for resetting password with OTP"""
    
    def post(self, request):
        """Handle POST request for resetting password"""
        return verify_otp_and_reset_password(request)

class OTPStatusView(View):
    """Class-based view for checking OTP status"""
    
    def get(self, request):
        """Handle GET request for checking OTP status"""
        return check_otp_status(request) 