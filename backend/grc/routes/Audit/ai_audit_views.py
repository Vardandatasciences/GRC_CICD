"""
AI Audit Views - Document Upload and AI Processing
Handles document upload for AI audits and automated audit processing
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction, connection
import os
import tempfile
import mimetypes
import shutil
import uuid
from datetime import datetime
import json

from ...models import Audit, AuditDocument, AuditDocumentMapping, Policy, SubPolicy, Compliance, Users
from ...routes.Global.logging_service import send_log
from ...routes.Consent import require_consent
from ...rbac.permissions import (
    AuditViewPermission, AuditConductPermission, AuditReviewPermission,
    AuditAssignPermission, AuditAnalyticsPermission, AuditViewAllPermission
)
from ...rbac.decorators import (
    audit_assign_required,
    audit_conduct_required,
    audit_view_reports_required,
    audit_view_all_required,
    audit_review_required
)
from .framework_filter_helper import get_active_framework_filter, apply_framework_filter_to_audits, get_framework_sql_filter

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditReviewPermission])
@audit_review_required
def review_ai_audit_findings(request, audit_id):
    """
    Review and approve/reject AI audit findings
    """
    try:
        data = request.data
        mapping_id = data.get('mapping_id')
        compliance_status = data.get('compliance_status')
        review_comments = data.get('review_comments', '')
        
        if not mapping_id or not compliance_status:
            return Response({
                'success': False,
                'error': 'Mapping ID and compliance status are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the mapping (this would need to be implemented with raw SQL if needed)
        try:
            mapping = AuditDocumentMapping.objects.get(
                MappingId=mapping_id,
                DocumentId__AuditId=audit_id
            )
        except AuditDocumentMapping.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Mapping not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update the mapping with reviewer input
        mapping.ComplianceStatus = compliance_status
        mapping.ReviewComments = review_comments
        mapping.ReviewedBy_id = request.session.get('user_id')
        mapping.ReviewedDate = timezone.now()
        mapping.save()
        
        # Log the review
        send_log(
            module="AI_Audit",
            actionType="AI_FINDING_REVIEWED",
            description=f"Reviewed AI finding for audit {audit_id}",
            userId=request.session.get('user_id'),
            entityType="AuditDocumentMapping",
            entityId=str(mapping_id),
            additionalInfo={
                "audit_id": audit_id,
                "mapping_id": mapping_id,
                "compliance_status": compliance_status,
                "review_comments": review_comments
            }
        )
        
        return Response({
            'success': True,
            'message': 'AI finding reviewed successfully',
            'mapping_id': mapping_id,
            'compliance_status': compliance_status,
            'reviewed_date': mapping.ReviewedDate.isoformat()
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error reviewing AI finding: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)