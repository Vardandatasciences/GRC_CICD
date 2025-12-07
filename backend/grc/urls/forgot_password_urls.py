from django.urls import path
from ..views.forgot_password_views import (
    initiate_password_reset,
    verify_otp_and_reset_password,
    check_otp_status,
    ForgotPasswordView,
    ResetPasswordView,
    OTPStatusView
)

app_name = 'forgot_password'

urlpatterns = [
    # Function-based views
    path('initiate/', initiate_password_reset, name='initiate_password_reset'),
    path('reset/', verify_otp_and_reset_password, name='verify_otp_and_reset_password'),
    path('check-otp/', check_otp_status, name='check_otp_status'),
    
    # Class-based views
    path('forgot/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('otp-status/', OTPStatusView.as_view(), name='otp_status'),
] 