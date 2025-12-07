"""
RBAC Test Views for verifying permission system
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.views.decorators.csrf import csrf_exempt
from ...rbac.permissions import (
    PolicyViewPermission, PolicyCreatePermission, PolicyEditPermission,
    AuditViewPermission, AuditConductPermission, AuditReviewPermission
)
from ...rbac.decorators import (
    policy_view_required, policy_create_required, policy_edit_required,
    audit_view_reports_required, audit_conduct_required, audit_review_required
)

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyViewPermission])
@policy_view_required
def test_policy_view_permission(request):
    """Test endpoint that requires policy view permission"""
    return Response({
        'message': 'Policy view permission granted',
        'status': 'success',
        'permission': 'view_all_policy'
    }, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyCreatePermission])
@policy_create_required
def test_policy_create_permission(request):
    """Test endpoint that requires policy create permission"""
    return Response({
        'message': 'Policy create permission granted',
        'status': 'success',
        'permission': 'create_policy'
    }, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyEditPermission])
@policy_edit_required
def test_policy_edit_permission(request):
    """Test endpoint that requires policy edit permission"""
    return Response({
        'message': 'Policy edit permission granted',
        'status': 'success',
        'permission': 'edit_policy'
    }, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditViewPermission])
@audit_view_reports_required
def test_audit_view_permission(request):
    """Test endpoint that requires audit view permission"""
    return Response({
        'message': 'Audit view permission granted',
        'status': 'success',
        'permission': 'view_audit_reports'
    }, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def test_audit_conduct_permission(request):
    """Test endpoint that requires audit conduct permission"""
    return Response({
        'message': 'Audit conduct permission granted',
        'status': 'success',
        'permission': 'conduct_audit'
    }, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditReviewPermission])
@audit_review_required
def test_audit_review_permission(request):
    """Test endpoint that requires audit review permission"""
    return Response({
        'message': 'Audit review permission granted',
        'status': 'success',
        'permission': 'review_audit'
    }, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
def test_public_endpoint(request):
    """Test endpoint that doesn't require any permissions"""
    return Response({
        'message': 'Public endpoint - no permissions required',
        'status': 'success',
        'permission': 'none'
    }, status=status.HTTP_200_OK)




