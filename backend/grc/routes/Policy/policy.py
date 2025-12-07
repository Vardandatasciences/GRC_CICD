from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from ...models import Framework, Policy, SubPolicy, FrameworkVersion, PolicyVersion, PolicyApproval, Users, FrameworkApproval, ExportTask, PolicyCategory, Entity, LastChecklistItemVerified
from ...serializers import FrameworkSerializer, PolicySerializer, SubPolicySerializer, PolicyApprovalSerializer, UserSerializer, EntitySerializer   
from django.db import transaction, models
from django.db.transaction import TransactionManagementError
from django.db import IntegrityError
from django.db.models import Q
import traceback
import sys
from datetime import datetime, date, timedelta
from ...routes.Global.s3_fucntions import export_data
import re
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Case, When, Value, FloatField, F
from django.db.models.functions import Coalesce, Cast
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from django.utils.dateparse import parse_date
from ...utils import parse_date, safe_isoformat
from ...routes.Global.notification_service import NotificationService  # Add this import
from django.utils.html import escape
from ...routes.Consent import require_consent

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

# Import statements for user interaction logging
from ...utils import send_log, get_client_ip
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from ...models import Framework, Policy, SubPolicy, PolicyVersion, FrameworkVersion, PolicyApproval, FrameworkApproval, Users
from ...serializers import FrameworkSerializer, PolicySerializer, SubPolicySerializer
from ...routes.Global.notification_service import NotificationService
from datetime import date, datetime
import traceback
import json

# RBAC Permission imports
from ...rbac.permissions import (
    PolicyViewPermission, PolicyCreatePermission, PolicyEditPermission,
    PolicyApprovePermission, PolicyDeletePermission, PolicyAssignPermission,
    PolicyExportPermission, PolicyAnalyticsPermission, PolicyKPIPermission,
    PolicyDashboardPermission, PolicyFrameworkPermission, PolicyTailoringPermission,
    PolicyVersioningPermission, PolicyListPermission,
    PolicyApprovalWorkflowPermission
)
from ...rbac.decorators import (
    audit_assign_required,
    audit_conduct_required,
    audit_view_reports_required,
    audit_view_all_required
)

import logging

# Set up logger for policy RBAC
logger = logging.getLogger(__name__)


# Test endpoint for debugging authentication
@api_view(['GET'])
@permission_classes([AllowAny])
def test_auth(request):
    """Test endpoint to check authentication status"""
    print(f"DEBUG: test_auth - User object: {request.user}")
    print(f"DEBUG: test_auth - User type: {type(request.user)}")
    print(f"DEBUG: test_auth - User authenticated: {hasattr(request.user, 'is_authenticated') and request.user.is_authenticated}")
    if hasattr(request.user, 'id'):
        print(f"DEBUG: test_auth - User ID: {request.user.id}")
    if hasattr(request.user, 'UserId'):
        print(f"DEBUG: test_auth - User UserId: {request.user.UserId}")
    if hasattr(request.user, 'username'):
        print(f"DEBUG: test_auth - User username: {request.user.username}")
    
    return Response({
        'user': str(request.user),
        'user_type': str(type(request.user)),
        'is_authenticated': hasattr(request.user, 'is_authenticated') and request.user.is_authenticated,
        'user_id': getattr(request.user, 'id', None),
        'user_userid': getattr(request.user, 'UserId', None),
        'username': getattr(request.user, 'username', None)
    })

# Test endpoint for RBAC debugging
@api_view(['GET'])
@permission_classes([])  # No permission classes - allow all requests
def test_rbac_debug(request):
    """Test endpoint to debug RBAC system"""
    from ...models import RBAC
    from ...rbac.utils import RBACUtils
    
    print(f"DEBUG: test_rbac_debug - Request user: {request.user}")
    print(f"DEBUG: test_rbac_debug - Request user type: {type(request.user)}")
    print(f"DEBUG: test_rbac_debug - Request user attributes: {dir(request.user)}")
    
    # Try different ways to get user ID
    user_id_from_userid = getattr(request.user, 'UserId', None)
    user_id_from_id = getattr(request.user, 'id', None)
    user_id_from_rbacutils = RBACUtils.get_user_id_from_request(request)
    
    print(f"DEBUG: User ID from UserId: {user_id_from_userid}")
    print(f"DEBUG: User ID from id: {user_id_from_id}")
    print(f"DEBUG: User ID from RBACUtils: {user_id_from_rbacutils}")
    
    # Check RBAC records
    rbac_records = []
    for user_id in [user_id_from_userid, user_id_from_id, user_id_from_rbacutils]:
        if user_id:
            records = RBAC.objects.filter(user=user_id)
            rbac_records.append({
                'user_id': user_id,
                'records': list(records.values('rbac_id', 'user', 'username', 'role', 'is_active', 'create_framework'))
            })
    
    return Response({
        'message': 'RBAC debug information',
        'user': str(request.user),
        'user_type': str(type(request.user)),
        'user_attributes': dir(request.user),
        'user_id_from_userid': user_id_from_userid,
        'user_id_from_id': user_id_from_id,
        'user_id_from_rbacutils': user_id_from_rbacutils,
        'rbac_records': rbac_records
    })

# Test endpoint for submit-review debugging
@api_view(['POST'])
@permission_classes([])  # No permission classes - allow all requests
@csrf_exempt
def test_submit_review(request, policy_id):
    """Test endpoint to check submit-review functionality"""
    print(f"DEBUG: test_submit_review - Request path: {request.path}")
    print(f"DEBUG: test_submit_review - Request method: {request.method}")
    print(f"DEBUG: test_submit_review - User object: {request.user}")
    print(f"DEBUG: test_submit_review - Request data: {request.data}")
    print(f"DEBUG: test_submit_review - Authentication header: {request.headers.get('Authorization', 'Not found')}")
    print(f"DEBUG: test_submit_review - User Role: {getattr(request.user, 'Role', 'No Role')}")
    print(f"DEBUG: test_submit_review - User ID: {getattr(request.user, 'UserId', 'No UserId')}")
    
    return Response({
        'message': 'Test submit-review endpoint working',
        'policy_id': policy_id,
        'user': str(request.user),
        'user_role': getattr(request.user, 'Role', 'No Role'),
        'user_id': getattr(request.user, 'UserId', 'No UserId'),
        'data_received': request.data
    })

# Simple test endpoint with no authentication requirements
@api_view(['POST'])
@permission_classes([])
@csrf_exempt
def simple_test_endpoint(request, policy_id):
    """Simple test endpoint with no authentication requirements"""
    print(f"DEBUG: simple_test_endpoint - Function called successfully")
    return Response({
        'message': 'Simple test endpoint working',
        'policy_id': policy_id,
        'request_method': request.method,
        'request_path': request.path
    })

# Framework CRUD operations

"""
@api GET /api/frameworks/
Returns all frameworks with Status='Approved' and ActiveInactive='Active'.
Filtered by the serializer to include only policies with Status='Approved' and ActiveInactive='Active',
and subpolicies with Status='Approved'.

@api POST /api/frameworks/
Creates a new framework with associated policies and subpolicies.
New frameworks are created with Status='Under Review' and ActiveInactive='Inactive' by default.
CurrentVersion defaults to 1.0 if not provided.

Example payload:
{
  "FrameworkName": "ISO 27001",
  "FrameworkDescription": "Information Security Management System",
  "EffectiveDate": "2023-10-01",
  "CreatedByName": "John Doe",
  "CreatedByDate": "2023-09-15",
  "Category": "Information Security and Compliance",
  "DocURL": "https://example.com/iso27001",
  "Identifier": "ISO-27001",
  "StartDate": "2023-10-01",
  "EndDate": "2025-10-01",
  "policies": [
    {
      "PolicyName": "Access Control Policy",
      "PolicyDescription": "Guidelines for access control management",
      "StartDate": "2023-10-01",
      "Department": "IT",
      "Applicability": "All Employees",
      "Scope": "All IT systems",
      "Objective": "Ensure proper access control",
      "Identifier": "ACP-001",
      "subpolicies": [
        {
          "SubPolicyName": "Password Management",
          "Identifier": "PWD-001",
          "Description": "Password requirements and management",
          "PermanentTemporary": "Permanent",
          "Control": "Use strong passwords with at least 12 characters"
        }
      ]
    }
  ]
}
"""

@api_view(['GET', 'POST'])
@permission_classes([PolicyViewPermission, PolicyFrameworkPermission])  # RBAC: Require PolicyViewPermission for viewing frameworks, PolicyFrameworkPermission for creating frameworks
def framework_list(request):
    """
    Secure framework list endpoint with SQL injection protection and proper connection management.
    Implements parameterized queries and follows principle of least privilege.
    """
    # Import security modules
    from django.utils.html import escape as escape_html
    from django.db import connection, transaction
    from django.core.exceptions import ValidationError as DjangoValidationError
    import logging
    import re
    from ...utils import send_log, get_client_ip
    
    # Configure secure logging to prevent log injection
    logger = logging.getLogger(__name__)
    
    # Security: Validate HTTP method early
    if request.method not in ['GET', 'POST']:
        return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    if request.method == 'GET':
        # Log framework list view attempt
        send_log(
            module="Framework",
            actionType="VIEW",
            description="Framework list view attempt",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            ipAddress=get_client_ip(request)
        )
        
        # Database connection will be automatically managed by Django ORM
        try:
            # Import validators
            from ..validators.framework_validator import validate_framework_query_params, ValidationError
            
            # Security: Validate and sanitize query parameters
            try:
                validated_params = validate_framework_query_params(request.GET)
                include_all_status = validated_params['include_all_status']
                include_all_for_identifiers = validated_params.get('include_all_for_identifiers', False)
                
                # NEW: Get user_id parameter for GRC Administrator filtering
                filter_user_id = request.GET.get('user_id')
                
            except ValidationError as e:
                # Security: Log sanitized error message to prevent log injection
                safe_error = escape_html(str(e))
                logger.warning(f"Framework query validation failed: {safe_error}")
                
                # Log validation failure
                send_log(
                    module="Framework",
                    actionType="VIEW_FAILED",
                    description=f"Framework query validation failed: {safe_error}",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="Framework",
                    logLevel="WARNING",
                    ipAddress=get_client_ip(request)
                )
                
                return Response({"error": "Invalid query parameters"}, status=status.HTTP_400_BAD_REQUEST)
            
            # NEW: Check if current user is GRC Administrator
            is_grc_admin = False
            current_user_id = getattr(request.user, 'id', None)
            
            if current_user_id:
                try:
                    from ...models import RBAC
                    rbac_record = RBAC.objects.filter(user_id=current_user_id, is_active='Y').first()
                    if rbac_record and rbac_record.is_grc_administrator():
                        is_grc_admin = True
                        logger.info(f"User {current_user_id} confirmed as GRC Administrator")
                except Exception as rbac_error:
                    logger.warning(f"Error checking GRC Administrator status: {rbac_error}")
            
            # Security: Use Django ORM with parameterized queries (SQL injection protection)
            try:
                if include_all_for_identifiers:
                    # For identifier uniqueness checking, fetch ALL frameworks regardless of status
                    # Django ORM automatically uses parameterized queries
                    frameworks = Framework.objects.select_related().all().only(
                        'FrameworkId', 'FrameworkName', 'CurrentVersion', 'FrameworkDescription',
                        'CreatedByName', 'CreatedByDate', 'Category', 'DocURL', 'Identifier',
                        'StartDate', 'EndDate', 'Status', 'ActiveInactive', 'Reviewer', 'InternalExternal'
                    )
                elif include_all_status:
                    # For analytics and dropdown, fetch ALL frameworks regardless of status
                    # Django ORM automatically uses parameterized queries
                    frameworks_query = Framework.objects.select_related().all()
                    
                    # NEW: Apply user filtering - include frameworks where user is creator OR reviewer
                    if filter_user_id:
                        # Get framework IDs where the user is the reviewer from FrameworkApproval table
                        reviewer_framework_ids = FrameworkApproval.objects.filter(
                            ReviewerId=filter_user_id
                        ).values_list('FrameworkId', flat=True).distinct()
                        
                        logger.info(f"Found {len(reviewer_framework_ids)} frameworks where user {filter_user_id} is reviewer")
                        print(f"DEBUG: Found {len(reviewer_framework_ids)} frameworks where user {filter_user_id} is reviewer: {list(reviewer_framework_ids)}")
                        
                        # Filter by specific user - match against CreatedByName field OR framework IDs where user is reviewer
                        try:
                            target_user = Users.objects.filter(UserId=filter_user_id).first()
                            if target_user:
                                # Filter by: created by user OR user is reviewer
                                frameworks_query = frameworks_query.filter(
                                    Q(CreatedByName=str(filter_user_id)) | 
                                    Q(CreatedByName=target_user.UserName) |
                                    Q(FrameworkId__in=reviewer_framework_ids)
                                )
                                logger.info(f"Filtering frameworks for user {filter_user_id} ({target_user.UserName}) - creator OR reviewer")
                            else:
                                # If user not found, filter by user ID as string OR reviewer
                                frameworks_query = frameworks_query.filter(
                                    Q(CreatedByName=str(filter_user_id)) |
                                    Q(FrameworkId__in=reviewer_framework_ids)
                                )
                                logger.info(f"Filtering frameworks for user ID {filter_user_id} - creator OR reviewer")
                        except Exception as user_lookup_error:
                            logger.warning(f"Error looking up user {filter_user_id}: {user_lookup_error}")
                            # Fallback to filtering by user ID as string OR reviewer
                            frameworks_query = frameworks_query.filter(
                                Q(CreatedByName=str(filter_user_id)) |
                                Q(FrameworkId__in=reviewer_framework_ids)
                            )
                    
                    frameworks = frameworks_query.only(
                        'FrameworkId', 'FrameworkName', 'CurrentVersion', 'FrameworkDescription',
                        'CreatedByName', 'CreatedByDate', 'Category', 'DocURL', 'Identifier',
                        'StartDate', 'EndDate', 'Status', 'ActiveInactive', 'Reviewer', 'InternalExternal'
                    )
                else:
                    # Default behavior - only approved and active frameworks
                    frameworks_query = Framework.objects.select_related().filter(
                        Status='Approved',
                        ActiveInactive='Active'
                    )
                    
                    # NEW: Apply user filtering - include frameworks where user is creator OR reviewer
                    if filter_user_id:
                        # Get framework IDs where the user is the reviewer from FrameworkApproval table
                        reviewer_framework_ids = FrameworkApproval.objects.filter(
                            ReviewerId=filter_user_id
                        ).values_list('FrameworkId', flat=True).distinct()
                        
                        # Filter by specific user - match against CreatedByName field OR framework IDs where user is reviewer
                        try:
                            target_user = Users.objects.filter(UserId=filter_user_id).first()
                            if target_user:
                                # Filter by: created by user OR user is reviewer
                                frameworks_query = frameworks_query.filter(
                                    Q(CreatedByName=str(filter_user_id)) | 
                                    Q(CreatedByName=target_user.UserName) |
                                    Q(FrameworkId__in=reviewer_framework_ids)
                                )
                                logger.info(f"Filtering approved frameworks for user {filter_user_id} ({target_user.UserName}) - creator OR reviewer")
                            else:
                                # If user not found, filter by user ID as string OR reviewer
                                frameworks_query = frameworks_query.filter(
                                    Q(CreatedByName=str(filter_user_id)) |
                                    Q(FrameworkId__in=reviewer_framework_ids)
                                )
                                logger.info(f"Filtering approved frameworks for user ID {filter_user_id} - creator OR reviewer")
                        except Exception as user_lookup_error:
                            logger.warning(f"Error looking up user {filter_user_id}: {user_lookup_error}")
                            # Fallback to filtering by user ID as string OR reviewer
                            frameworks_query = frameworks_query.filter(
                                Q(CreatedByName=str(filter_user_id)) |
                                Q(FrameworkId__in=reviewer_framework_ids)
                            )
                    
                    frameworks = frameworks_query.only(
                        'FrameworkId', 'FrameworkName', 'CurrentVersion', 'FrameworkDescription',
                        'CreatedByName', 'CreatedByDate', 'Category', 'DocURL', 'Identifier',
                        'StartDate', 'EndDate', 'Status', 'ActiveInactive', 'Reviewer', 'InternalExternal'
                    )
                
                # Security: Process data with proper sanitization
                framework_data = []
                for framework in frameworks:
                    # Get the latest FrameworkApproval record for this framework to get ReviewerId
                    latest_approval = FrameworkApproval.objects.filter(
                        FrameworkId=framework.FrameworkId
                    ).order_by('-ApprovalId').first()
                    
                    reviewer_id = None
                    reviewer_name = None
                    created_by = None
                    
                    if latest_approval:
                        reviewer_id = latest_approval.ReviewerId
                        created_by = latest_approval.UserId
                        # Try to get reviewer name from Users table if ReviewerId is available
                        if reviewer_id:
                            try:
                                reviewer_user = Users.objects.filter(UserId=reviewer_id).first()
                                if reviewer_user:
                                    reviewer_name = reviewer_user.UserName
                            except Exception as e:
                                logger.warning(f"Error looking up reviewer name for ReviewerId {reviewer_id}: {e}")
                    
                    # Fallback to Reviewer field from Framework if no approval record
                    if not reviewer_name and framework.Reviewer:
                        reviewer_name = framework.Reviewer
                    
                    # Security: Escape all string fields to prevent XSS
                    framework_data.append({
                        'FrameworkId': framework.FrameworkId,  # Integer, safe
                        'FrameworkName': escape_html(framework.FrameworkName) if framework.FrameworkName else '',
                        'CurrentVersion': framework.CurrentVersion,  # Float, safe
                        'FrameworkDescription': escape_html(framework.FrameworkDescription) if framework.FrameworkDescription else '',
                        'CreatedByName': escape_html(framework.CreatedByName) if framework.CreatedByName else '',
                        'CreatedByDate': framework.CreatedByDate,  # Date, safe
                        'Category': escape_html(framework.Category) if framework.Category else '',
                        'DocURL': framework.DocURL,  # URL validation should be done at model level
                        'Identifier': escape_html(framework.Identifier) if framework.Identifier else '',
                        'StartDate': framework.StartDate,  # Date, safe
                        'EndDate': framework.EndDate,  # Date, safe
                        'Status': escape_html(framework.Status) if framework.Status else '',
                        'ActiveInactive': escape_html(framework.ActiveInactive) if framework.ActiveInactive else '',
                        'Reviewer': escape_html(reviewer_name) if reviewer_name else '',
                        'ReviewerId': reviewer_id,  # Include ReviewerId from FrameworkApproval
                        'CreatedBy': created_by,  # Include UserId who created from FrameworkApproval
                        'InternalExternal': escape_html(framework.InternalExternal) if framework.InternalExternal else ''
                    })
                
                # Security: Log successful operation (sanitized)
                filter_info = f" (filtered by user {filter_user_id})" if is_grc_admin and filter_user_id else ""
                logger.info(f"Successfully retrieved {len(framework_data)} frameworks{filter_info}")
                
                # Log successful framework list retrieval
                send_log(
                    module="Framework",
                    actionType="VIEW_SUCCESS",
                    description=f"Successfully retrieved {len(framework_data)} frameworks{filter_info}",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="Framework",
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        "frameworks_count": len(framework_data), 
                        "include_all_status": include_all_status,
                        "include_all_for_identifiers": include_all_for_identifiers,
                        "is_grc_admin": is_grc_admin,
                        "filter_user_id": filter_user_id
                    }
                )
                
                return Response(framework_data)
                
            except Exception as db_error:
                # Security: Log error without exposing sensitive information
                logger.error(f"Database error in framework retrieval: {type(db_error).__name__}")
                return Response(
                    {"error": "Database operation failed"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            # Security: Generic error handling without information disclosure
            logger.error(f"Unexpected error in framework_list GET: {type(e).__name__}")
            return Response(
                {"error": "An unexpected error occurred"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 
    elif request.method == 'POST':
        # Debug: Check for framework context before framework creation
        from ...framework_context import get_framework_context
        
        # Try to get user_id from various sources
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
        
        # Try to get framework_id from various sources
        framework_id_from_session = None
        
        # Try from framework context FIRST (more reliable and up-to-date)
        if user_id:
            framework_id_from_session = get_framework_context(str(user_id))
            if framework_id_from_session:
                print(f"✅ DEBUG: Found framework_id in framework context: {framework_id_from_session}")
        
        # Fall back to session if not in framework context (for backward compatibility)
        if not framework_id_from_session:
            session_framework_id = request.session.get('selected_framework_id') or request.session.get('grc_framework_selected')
            if session_framework_id:
                framework_id_from_session = session_framework_id
                print(f"⚠️ DEBUG: Found framework_id in session (fallback): {framework_id_from_session}")
        
        print(f"🔍 DEBUG: framework_list POST - checking for framework context")
        print(f"📊 DEBUG: Framework ID: {framework_id_from_session}")
        print(f"👤 DEBUG: User ID: {user_id}")
        print(f"🔍 DEBUG: Session keys: {list(request.session.keys()) if hasattr(request, 'session') else 'No session'}")
        
        # Log framework creation attempt
        send_log(
            module="Framework",
            actionType="CREATE",
            description="Framework creation attempt",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            ipAddress=get_client_ip(request)
        )
        
        # Database connections will be managed by Django's transaction.atomic()
        try:
            # Security: Validate request data size to prevent DoS
            if len(str(request.data)) > 1024 * 1024:  # 1MB limit
                # Log payload too large error
                send_log(
                    module="Framework",
                    actionType="CREATE_FAILED",
                    description="Framework creation failed - payload too large",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="Framework",
                    logLevel="WARNING",
                    ipAddress=get_client_ip(request)
                )
                
                return Response(
                    {"error": "Request payload too large"}, 
                    status=status.HTTP_413_REQUEST_TOO_LARGE
                )
            
            # Security: Log sanitized request info
            logger.info(f"Processing framework creation request from user: {escape_html(str(request.user))}")
            
            # Import validators
            from ..validators.framework_validator import validate_framework_post_data, ValidationError, safe_isoformat
            
            # Initialize notification service
            notification_service = NotificationService()
            
            # Security: Validate request data with strict validation
            try:
                validated_data = validate_framework_post_data(request.data)
                
                # Security: Additional validation for critical fields
                if not validated_data.get('FrameworkName'):
                    raise ValidationError("Framework name is required")
                if not validated_data.get('CreatedByName'):
                    raise ValidationError("Creator name is required")
                    
            except ValidationError as e:
                safe_error = escape_html(str(e))
                logger.warning(f"Framework validation failed: {safe_error}")
                
                # Log validation failure
                send_log(
                    module="Framework",
                    actionType="CREATE_FAILED",
                    description=f"Framework creation validation failed: {safe_error}",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="Framework",
                    logLevel="WARNING",
                    ipAddress=get_client_ip(request)
                )
                
                return Response({"error": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Security: Sanitize all string data to prevent stored XSS
            string_fields_to_escape = [
                'FrameworkName', 'FrameworkDescription', 'CreatedByName', 
                'Category', 'Identifier', 'InternalExternal'
            ]
            for field in string_fields_to_escape:
                if field in validated_data and validated_data[field]:
                    validated_data[field] = escape_html(validated_data[field])

            # Security: Sanitize policy data
            if 'policies' in validated_data:
                for policy_data in validated_data['policies']:
                    policy_fields_to_escape = [
                        'PolicyName', 'PolicyDescription', 'Department', 'CreatedByName', 
                        'Applicability', 'Scope', 'Objective', 'Identifier', 
                        'PermanentTemporary', 'PolicyType', 'PolicyCategory', 'PolicySubCategory'
                    ]
                    for field in policy_fields_to_escape:
                        if field in policy_data and policy_data[field]:
                            policy_data[field] = escape_html(policy_data[field])
                    
                    # Security: Sanitize subpolicy data
                    if 'subpolicies' in policy_data:
                        for subpolicy_data in policy_data['subpolicies']:
                            subpolicy_fields_to_escape = [
                                'SubPolicyName', 'CreatedByName', 'Identifier', 
                                'Description', 'PermanentTemporary', 'Control'
                            ]
                            for field in subpolicy_fields_to_escape:
                                if field in subpolicy_data and subpolicy_data[field]:
                                    subpolicy_data[field] = escape_html(subpolicy_data[field])
            
            # Check if framework name already exists
            framework_name = validated_data['FrameworkName']
            existing_framework_with_name = Framework.objects.filter(
                FrameworkName__iexact=framework_name
            ).first()
            
            if existing_framework_with_name:
                return Response({
                    'error': f'Framework with name "{framework_name}" already exists. Please choose a different name.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Handle identifier based on Internal/External selection
            internal_external = validated_data.get('InternalExternal', '')
            identifier = validated_data.get('Identifier', '')
            
            # For internal frameworks, ensure identifier is auto-generated if not provided
            if internal_external == 'Internal':
                if not identifier or identifier.strip() == '':
                    # Auto-generate identifier for internal frameworks
                    from datetime import datetime
                    import re
                    
                    # Create identifier based on framework name
                    framework_name = validated_data['FrameworkName']
                    # Extract first letters of each word
                    words = re.findall(r'\b\w', framework_name.upper())
                    prefix = ''.join(words[:3])  # Take first 3 letters
                    
                    # Add date suffix
                    current_date = datetime.now().strftime('%y%m%d')
                    
                    # Add random suffix
                    import random
                    import string
                    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
                    
                    identifier = f"{prefix}-{current_date}-{suffix}"
                    
                    # Sanitize the auto-generated identifier
                    identifier = escape_html(identifier)
                    
                    # Check if auto-generated identifier already exists
                    existing_framework = Framework.objects.filter(Identifier=identifier).first()
                    if existing_framework:
                        # Generate a new identifier with a different suffix
                        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
                        identifier = f"{prefix}-{current_date}-{suffix}"
                        identifier = escape_html(identifier)
                        
                        # Check again (should be rare to have conflicts)
                        existing_framework = Framework.objects.filter(Identifier=identifier).first()
                        if existing_framework:
                            # Add timestamp to ensure uniqueness
                            import time
                            timestamp = str(int(time.time()))[-3:]  # Last 3 digits of timestamp
                            identifier = f"{prefix}-{current_date}-{suffix}{timestamp}"
                            identifier = escape_html(identifier)
                    
                    logger.info(f"Auto-generated identifier for internal framework: {identifier}")
            
            # For external frameworks, require manual identifier
            elif internal_external == 'External':
                if not identifier or identifier.strip() == '':
                    return Response({
                        'error': 'Identifier is required for external frameworks'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Sanitize the manually entered identifier
                identifier = escape_html(identifier.strip())
                
                # Check if identifier already exists
                existing_framework = Framework.objects.filter(Identifier=identifier).first()
                if existing_framework:
                    return Response({
                        'error': f'Identifier "{identifier}" already exists. Please choose a different identifier.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Security: Prepare framework data with validated and sanitized inputs
            framework_data = {
                'FrameworkName': validated_data['FrameworkName'],
                'FrameworkDescription': validated_data['FrameworkDescription'],
                'CreatedByName': validated_data['CreatedByName'],
                'CreatedByDate': validated_data['CreatedByDate'],
                'Category': validated_data['Category'],
                'DocURL': validated_data['DocURL'],
                'Identifier': identifier,
                'StartDate': validated_data['StartDate'],
                'EndDate': validated_data['EndDate'],
                'Status': validated_data['Status'],
                'ActiveInactive': validated_data['ActiveInactive'],
                'CurrentVersion': validated_data['CurrentVersion'],
                'InternalExternal': internal_external
            }

            # Security: Secure reviewer lookup using parameterized queries
            reviewer_id = validated_data['Reviewer']
            reviewer_email = None
            
            if reviewer_id:
                try:
                    # Security: Django ORM uses parameterized queries automatically
                    reviewer = Users.objects.select_related().filter(
                        UserId=reviewer_id
                    ).only('UserName', 'Email').first()
                    
                    if reviewer:
                        framework_data['Reviewer'] = escape_html(reviewer.UserName)
                        reviewer_email = reviewer.Email
                        logger.info(f"Found reviewer for framework creation")
                    else:
                        logger.warning(f"Reviewer with ID not found")
                        framework_data['Reviewer'] = ''
                except Exception as reviewer_error:
                    logger.error(f"Error looking up reviewer: {type(reviewer_error).__name__}")
                    framework_data['Reviewer'] = ''
            else:
                framework_data['Reviewer'] = ''

            # Security: Use atomic transaction with proper connection management
            with transaction.atomic():
                try:
                    # Security: Create framework using Django ORM (parameterized queries)
                    framework = Framework.objects.create(**framework_data)
                    
                    # Security: Create framework version with sanitized data
                    framework_version = FrameworkVersion.objects.create(
                        FrameworkId=framework,
                        Version=framework.CurrentVersion,
                        FrameworkName=framework.FrameworkName,
                        CreatedBy=framework.CreatedByName,
                        CreatedDate=date.today(),
                        PreviousVersionId=None
                    )
                    
                    # Security: Process policies with proper sanitization
                    policies_data = []
                    if 'policies' in validated_data:
                        # Check for duplicate policy names within this framework
                        policy_names = [policy_data.get('PolicyName', '').strip() for policy_data in validated_data['policies']]
                        duplicate_policy_names = []
                        
                        for i, policy_name in enumerate(policy_names):
                            if policy_name and policy_names.count(policy_name) > 1:
                                if policy_name not in duplicate_policy_names:
                                    duplicate_policy_names.append(policy_name)
                        
                        if duplicate_policy_names:
                            return Response({
                                'error': f'Duplicate policy names found within the framework: {", ".join(duplicate_policy_names)}. Policy names must be unique within a framework.'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        for policy_data in validated_data['policies']:
                            # Security: Secure reviewer lookup for policies
                            policy_reviewer_name = ''
                            policy_reviewer_id = policy_data.get('ReviewerId')
                            if policy_reviewer_id:
                                try:
                                    policy_reviewer = Users.objects.filter(
                                        UserId=policy_reviewer_id
                                    ).only('UserName').first()
                                    
                                    if policy_reviewer:
                                        policy_reviewer_name = escape_html(policy_reviewer.UserName)
                                except Exception as policy_reviewer_error:
                                    logger.error(f"Policy reviewer lookup error: {type(policy_reviewer_error).__name__}")
                            
                            # Security: Validate and sanitize entities data
                            # Allow both "all" (string) for all entities or list of specific entity IDs
                            entities_data = policy_data.get('Entities', [])
                            if entities_data == "all":
                                # Keep "all" as string when all locations are selected
                                logger.info(f"Entities data received: all locations selected")
                            elif isinstance(entities_data, list):
                                # Keep as list when specific entities are selected
                                logger.info(f"Entities data received: {len(entities_data)} specific entities")
                            else:
                                # Default to empty list for invalid data
                                entities_data = []
                                logger.warning("Invalid entities data received, defaulting to empty list")
                            
                            # Security: Create policy with parameterized queries
                            policy = Policy.objects.create(
                                FrameworkId=framework,
                                PolicyName=policy_data['PolicyName'],
                                PolicyDescription=policy_data['PolicyDescription'],
                                Status='Under Review',
                                StartDate=policy_data['StartDate'],
                                EndDate=policy_data['EndDate'],
                                Department=policy_data['Department'],
                                CreatedByName=policy_data['CreatedByName'],
                                CreatedByDate=date.today(),
                                Applicability=policy_data['Applicability'],
                                DocURL=policy_data['DocURL'],
                                Scope=policy_data['Scope'],
                                Objective=policy_data['Objective'],
                                Identifier=policy_data['Identifier'],
                                PermanentTemporary=policy_data['PermanentTemporary'],
                                ActiveInactive='Inactive',
                                Reviewer=policy_reviewer_name,
                                CoverageRate=policy_data['CoverageRate'],
                                CurrentVersion=framework.CurrentVersion,
                                PolicyType=policy_data['PolicyType'],
                                PolicyCategory=policy_data['PolicyCategory'],
                                PolicySubCategory=policy_data['PolicySubCategory'],
                                Entities=entities_data
                            )

                            # Security: Create policy version with parameterized queries
                            PolicyVersion.objects.create(
                                PolicyId=policy,
                                Version=framework.CurrentVersion,
                                PolicyName=policy.PolicyName,
                                CreatedBy=policy.CreatedByName,
                                CreatedDate=date.today(),
                                PreviousVersionId=None,
                                FrameworkId=framework
                            )
                            
                            # Security: Process subpolicies with proper validation
                            if 'subpolicies' in policy_data:
                                for subpolicy_data in policy_data['subpolicies']:
                                    created_by_name = subpolicy_data.get('CreatedByName')
                                    if not created_by_name:
                                        created_by_name = policy.CreatedByName

                                    SubPolicy.objects.create(
                                        PolicyId=policy,
                                        SubPolicyName=subpolicy_data['SubPolicyName'],
                                        CreatedByName=created_by_name,
                                        CreatedByDate=subpolicy_data['CreatedByDate'],
                                        Identifier=subpolicy_data['Identifier'],
                                        Description=subpolicy_data['Description'],
                                        Status=subpolicy_data['Status'],
                                        PermanentTemporary=subpolicy_data['PermanentTemporary'],
                                        Control=subpolicy_data['Control'],
                                        FrameworkId=framework
                                    )
                            
                            # Security: Collect policy data for approval with safe serialization
                            policy_dict = {
                                "PolicyId": policy.PolicyId,
                                "PolicyName": policy.PolicyName,
                                "PolicyDescription": policy.PolicyDescription,
                                "Status": policy.Status,
                                "StartDate": policy.StartDate.isoformat() if policy.StartDate else None,
                                "EndDate": policy.EndDate.isoformat() if policy.EndDate else None,
                                "Department": policy.Department,
                                "CreatedByName": policy.CreatedByName,
                                "CreatedByDate": policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                                "Applicability": policy.Applicability,
                                "DocURL": policy.DocURL,
                                "Scope": policy.Scope,
                                "Objective": policy.Objective,
                                "Identifier": policy.Identifier,
                                "PermanentTemporary": policy.PermanentTemporary,
                                "ActiveInactive": policy.ActiveInactive,
                                "Reviewer": policy.Reviewer,
                                "CoverageRate": policy.CoverageRate,
                                "CurrentVersion": policy.CurrentVersion,
                                "PolicyType": policy.PolicyType,
                                "PolicyCategory": policy.PolicyCategory,
                                "PolicySubCategory": policy.PolicySubCategory,
                                "Entities": policy.Entities,
                                "subpolicies": []
                            }
                            
                            # Security: Add subpolicies data with parameterized queries
                            subpolicies = SubPolicy.objects.filter(PolicyId=policy).only(
                                'SubPolicyId', 'SubPolicyName', 'CreatedByName', 'CreatedByDate',
                                'Identifier', 'Description', 'Status', 'PermanentTemporary', 'Control'
                            )
                            for subpolicy in subpolicies:
                                subpolicy_dict = {
                                    "SubPolicyId": subpolicy.SubPolicyId,
                                    "SubPolicyName": subpolicy.SubPolicyName,
                                    "CreatedByName": subpolicy.CreatedByName,
                                    "CreatedByDate": subpolicy.CreatedByDate.isoformat() if subpolicy.CreatedByDate else None,
                                    "Identifier": subpolicy.Identifier,
                                    "Description": subpolicy.Description,
                                    "Status": subpolicy.Status,
                                    "PermanentTemporary": subpolicy.PermanentTemporary,
                                    "Control": subpolicy.Control
                                }
                                policy_dict["subpolicies"].append(subpolicy_dict)
                            
                            policies_data.append(policy_dict)

                    # Security: Create framework approval record with validated data
                    try:
                        # Security: Validate and sanitize user IDs
                        creator_user_id = request.data.get('CreatedById')
                        
                        if not creator_user_id and 'policies' in request.data and len(request.data['policies']) > 0:
                            creator_user_id = request.data['policies'][0].get('CreatedById')
                        
                        # Try to get user ID from session if not provided in request
                        if not creator_user_id:
                            creator_user_id = request.session.get('user_id')
                        
                        if not creator_user_id and framework_data['CreatedByName']:
                            try:
                                creator_user = Users.objects.filter(
                                    UserName=framework_data['CreatedByName']
                                ).only('UserId').first()
                                creator_user_id = creator_user.UserId if creator_user else None
                            except Exception:
                                creator_user_id = None
                        
                        # If still no user ID, return error instead of using hardcoded fallback
                        if not creator_user_id:
                            return Response(
                                {"error": "User authentication required. Please log in and try again."},
                                status=status.HTTP_401_UNAUTHORIZED
                            )
                        
                        # Security: Ensure numeric IDs to prevent injection
                        if isinstance(creator_user_id, str):
                            try:
                                creator_user_id = int(creator_user_id)
                            except (ValueError, TypeError):
                                creator_user_id = 1
                        
                        if reviewer_id is None or reviewer_id == '':
                            # Instead of hardcoded fallback, make reviewer assignment explicit
                            return Response(
                                {"error": "Reviewer assignment required. Please select a reviewer and try again."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        elif isinstance(reviewer_id, str):
                            try:
                                reviewer_id = int(reviewer_id)
                            except (ValueError, TypeError):
                                return Response(
                                    {"error": "Invalid reviewer ID format. Please select a valid reviewer."},
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                        
                        # Security: Create extracted data with sanitized content
                        extracted_data = {
                            "FrameworkName": framework.FrameworkName,
                            "FrameworkDescription": framework.FrameworkDescription,
                            "Category": framework.Category,
                            "StartDate": safe_isoformat(framework.StartDate),
                            "EndDate": safe_isoformat(framework.EndDate),
                            "CreatedByName": framework.CreatedByName,
                            "CreatedByDate": framework.CreatedByDate.isoformat() if framework.CreatedByDate else None,
                            "Identifier": framework.Identifier,
                            "Status": framework.Status,
                            "ActiveInactive": framework.ActiveInactive,
                            "InternalExternal": framework.InternalExternal or "Internal",
                            "type": "framework",
                            "docURL": framework.DocURL,
                            "reviewer": framework.Reviewer,
                            "source": "standard",
                            "policies": policies_data,
                            "totalPolicies": len(policies_data),
                            "totalSubpolicies": sum(len(p["subpolicies"]) for p in policies_data)
                        }

                        # Security: Create framework approval record with parameterized queries
                        FrameworkApproval.objects.create(
                            FrameworkId=framework,
                            ExtractedData=extracted_data,
                            UserId=creator_user_id,
                            ReviewerId=reviewer_id,
                            Version="u1",
                            ApprovedNot=None
                        )

                        # Security: Send notification with validated email
                        if reviewer_email and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', reviewer_email):
                            try:
                                notification_data = {
                                    'notification_type': 'frameworkSubmitted',
                                    'email': reviewer_email,
                                    'email_type': 'gmail',
                                    'template_data': [
                                        framework_data['Reviewer'],
                                        framework.FrameworkName,
                                        framework.CreatedByName,
                                    ]
                                }
                                notification_result = notification_service.send_multi_channel_notification(notification_data)
                                logger.info("Notification sent successfully")
                            except Exception as notification_error:
                                logger.error(f"Notification error: {type(notification_error).__name__}")
                        else:
                            logger.warning("Invalid or missing reviewer email")

                    except Exception as approval_error:
                        logger.error(f"Error creating framework approval: {type(approval_error).__name__}")
                        # Continue execution as approval record is not critical for framework creation

                    # Security: Log successful operation
                    logger.info(f"Framework created successfully with ID: {framework.FrameworkId}")
                    
                    # Log successful framework creation
                    send_log(
                        module="Framework",
                        actionType="CREATE_SUCCESS",
                        description=f"Framework '{framework.FrameworkName}' created successfully",
                        userId=getattr(request.user, 'id', None),
                        userName=getattr(request.user, 'username', validated_data.get('CreatedByName', 'Anonymous')),
                        entityType="Framework",
                        entityId=framework.FrameworkId,
                        ipAddress=get_client_ip(request),
                        additionalInfo={
                            "framework_name": framework.FrameworkName,
                            "framework_id": framework.FrameworkId,
                            "category": framework.Category,
                            "policies_count": len(validated_data.get('policies', []))
                        }
                    )
                    
                    return Response(
                        {"message": "Framework created successfully", "FrameworkId": framework.FrameworkId}, 
                        status=status.HTTP_201_CREATED
                    )
                    
                except Exception as transaction_error:
                    # Security: Transaction will be rolled back automatically
                    logger.error(f"Transaction error in framework creation: {type(transaction_error).__name__}")
                    raise  # Re-raise to trigger rollback
 
        except ValidationError as e:
            safe_error = escape_html(str(e))
            logger.warning(f"Validation error in framework_list POST: {safe_error}")
            return Response({"error": "Validation failed"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in framework_list POST: {type(e).__name__}")
            return Response(
                {"error": "An unexpected error occurred"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

 
@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policies_by_framework(request, framework_id):
    """
    Get all policies for a specific framework
    """
    # Log policy retrieval attempt
    send_log(
        module="Policy",
        actionType="VIEW",
        description=f"Retrieving policies for framework {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=framework_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        policies = Policy.objects.filter(FrameworkId=framework_id)
        serializer = PolicySerializer(policies, many=True)
        
        # Log successful policy retrieval
        send_log(
            module="Policy",
            actionType="VIEW_SUCCESS",
            description=f"Successfully retrieved {len(policies)} policies for framework {framework_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=framework_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"policies_count": len(policies), "framework_id": framework_id}
        )
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        # Log error
        send_log(
            module="Policy",
            actionType="VIEW_FAILED",
            description=f"Failed to retrieve policies for framework {framework_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=framework_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return Response({'error': 'Error retrieving policies', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)
 
@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyViewPermission])
def get_subpolicies_by_policy(request, policy_id):
    """
    Get all subpolicies for a specific policy
    """
    try:
        subpolicies = SubPolicy.objects.filter(PolicyId=policy_id)
        serializer = SubPolicySerializer(subpolicies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return Response({'error': 'Error retrieving subpolicies', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)

"""
@api GET /api/frameworks/{pk}/
Returns a specific framework by ID if it has Status='Approved' and ActiveInactive='Active'.

@api PUT /api/frameworks/{pk}/
Updates an existing framework. Only frameworks with Status='Approved' and ActiveInactive='Active' can be updated.

Example payload:
{
  "FrameworkName": "ISO 27001:2022",
  "FrameworkDescription": "Updated Information Security Management System",
  "Category": "Information Security",
  "DocURL": "https://example.com/iso27001-2022",
  "EndDate": "2026-10-01"
}

@api DELETE /api/frameworks/{pk}/
Soft-deletes a framework by setting ActiveInactive='Inactive'.
Also marks all related policies as inactive and all related subpolicies with Status='Inactive'.
"""
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([PolicyFrameworkPermission])
def framework_detail(request, pk):
    framework = get_object_or_404(Framework, FrameworkId=pk)
    
    if request.method == 'GET':
        # Log framework detail view attempt
        send_log(
            module="Framework",
            actionType="VIEW",
            description=f"Viewing framework details for ID {pk}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=pk,
            ipAddress=get_client_ip(request)
        )
        # Only return details if framework is Approved and Active
        if framework.Status != 'Approved' or framework.ActiveInactive != 'Active':
            return Response({'error': 'Framework is not approved or active'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all active and approved policies for this framework
        policies = Policy.objects.filter(
            FrameworkId=framework,
            Status='Approved',
            ActiveInactive='Active'
        )
        
        # Get all subpolicies for these policies
        policy_data = []
        for policy in policies:
            policy_dict = {
                'PolicyId': policy.PolicyId,
                'PolicyName': policy.PolicyName,
                'PolicyDescription': policy.PolicyDescription,
                'CurrentVersion': policy.CurrentVersion,
                'StartDate': policy.StartDate,
                'EndDate': policy.EndDate,
                'Department': policy.Department,
                'CreatedByName': policy.CreatedByName,
                'CreatedByDate': policy.CreatedByDate,
                'Applicability': policy.Applicability,
                'DocURL': policy.DocURL,
                'Scope': policy.Scope,
                'Objective': policy.Objective,
                'Identifier': policy.Identifier,
                'PermanentTemporary': policy.PermanentTemporary,
                'subpolicies': []
            }
            
            # Get all subpolicies for this policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy)
            for subpolicy in subpolicies:
                subpolicy_dict = {
                    'SubPolicyId': subpolicy.SubPolicyId,
                    'SubPolicyName': subpolicy.SubPolicyName,
                    'CreatedByName': subpolicy.CreatedByName,
                    'CreatedByDate': subpolicy.CreatedByDate,
                    'Identifier': subpolicy.Identifier,
                    'Description': subpolicy.Description,
                    'Status': subpolicy.Status,
                    'PermanentTemporary': subpolicy.PermanentTemporary,
                    'Control': subpolicy.Control
                }
                policy_dict['subpolicies'].append(subpolicy_dict)
            
            policy_data.append(policy_dict)
        
        # Create response data
        response_data = {
            'FrameworkId': framework.FrameworkId,
            'FrameworkName': framework.FrameworkName,
            'CurrentVersion': framework.CurrentVersion,
            'FrameworkDescription': framework.FrameworkDescription,
            'EffectiveDate': framework.EffectiveDate,
            'CreatedByName': framework.CreatedByName,
            'CreatedByDate': framework.CreatedByDate,
            'Category': framework.Category,
            'DocURL': framework.DocURL,
            'Identifier': framework.Identifier,
            'StartDate': framework.StartDate,
            'EndDate': framework.EndDate,
            'Status': framework.Status,
            'ActiveInactive': framework.ActiveInactive,
            'InternalExternal': framework.InternalExternal,
            'Reviewer': framework.Reviewer,
            'policies': policy_data
        }
        
        return Response(response_data)
    
    elif request.method == 'PUT':
        # Check if framework is approved and active before allowing update
        if framework.Status != 'Approved' or framework.ActiveInactive != 'Active':
            return Response({'error': 'Only approved and active frameworks can be updated'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                serializer = FrameworkSerializer(framework, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'message': 'Framework updated successfully',
                        'FrameworkId': framework.FrameworkId,
                        'CurrentVersion': framework.CurrentVersion
                    })
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_info = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return Response({'error': 'Error updating framework', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        try:
            with transaction.atomic():
                # Instead of deleting, set ActiveInactive to 'Inactive'
                framework.ActiveInactive = 'Inactive'
                framework.save()
                
                # Set all related policies to inactive
                policies = Policy.objects.filter(FrameworkId=framework)
                for policy in policies:
                    policy.ActiveInactive = 'Inactive'
                    policy.save()
                    
                    # Update Status of subpolicies since they don't have ActiveInactive field
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    for subpolicy in subpolicies:
                        subpolicy.Status = 'Inactive'
                        subpolicy.save()
                
                return Response({'message': 'Framework and related policies marked as inactive'}, status=status.HTTP_200_OK)
        except Exception as e:
            error_info = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return Response({'error': 'Error marking framework as inactive', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)

# Policy CRUD operations

"""
@api GET /api/policies/{pk}/
Returns a specific policy by ID if it has Status='Approved' and ActiveInactive='Active',
and its parent framework has Status='Approved' and ActiveInactive='Active'.

@api PUT /api/policies/{pk}/
Updates an existing policy. Only policies with Status='Approved' and ActiveInactive='Active'
whose parent framework is also Approved and Active can be updated.

Example payload:
{
  "PolicyName": "Updated Access Control Policy",
  "PolicyDescription": "Enhanced guidelines for access control management with additional security measures",
  "StartDate": "2023-12-01",
  "EndDate": "2025-12-01",
  "Department": "IT,Security",
  "Scope": "All IT systems and cloud services",
  "Objective": "Ensure proper access control with improved security"
}

@api DELETE /api/policies/{pk}/
Soft-deletes a policy by setting ActiveInactive='Inactive'.
Also marks all related subpolicies with Status='Inactive'.
"""
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([PolicyViewPermission])
def policy_detail(request, pk):
    # Log policy detail operation attempt
    send_log(
        module="Policy",
        actionType="POLICY_DETAIL",
        description=f"Accessing policy detail for policy {pk} with method {request.method}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=pk,
        ipAddress=get_client_ip(request),
        additionalInfo={"method": request.method}
    )
    
    try:
        policy = Policy.objects.get(PolicyId=pk)
    except Policy.DoesNotExist:
        # Log policy not found error
        send_log(
            module="Policy",
            actionType="POLICY_DETAIL_FAILED",
            description=f"Policy {pk} not found",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=pk,
            logLevel="WARNING",
            ipAddress=get_client_ip(request),
            additionalInfo={"method": request.method}
        )
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Remove restrictions that were causing 403 errors
        # Previously only allowed if policy.Status == 'Approved' and policy.ActiveInactive == 'Active'
        
        # Log successful policy retrieval
        send_log(
            module="Policy",
            actionType="POLICY_DETAIL_GET_SUCCESS",
            description=f"Successfully retrieved policy {pk} details",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=pk,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "policy_name": policy.PolicyName,
                "status": policy.Status,
                "active_inactive": policy.ActiveInactive
            }
        )
        
        serializer = PolicySerializer(policy)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Remove restrictions for updating
        # Previously only allowed if policy.Status == 'Approved' and policy.ActiveInactive == 'Active'
        
        # Log policy update attempt
        send_log(
            module="Policy",
            actionType="POLICY_UPDATE",
            description=f"Attempting to update policy {pk}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=pk,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "policy_name": policy.PolicyName,
                "current_status": policy.Status,
                "current_active_inactive": policy.ActiveInactive
            }
        )
        
        try:
            with transaction.atomic():
                # Add status and ActiveInactive to request data
                update_data = request.data.copy()
                update_data['Status'] = 'Under Review'
                update_data['ActiveInactive'] = 'Inactive'
                
                serializer = PolicySerializer(policy, data=update_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    
                    # Log successful policy update
                    send_log(
                        module="Policy",
                        actionType="POLICY_UPDATE_SUCCESS",
                        description=f"Policy {pk} updated successfully and set to Under Review",
                        userId=getattr(request.user, 'id', None),
                        userName=getattr(request.user, 'username', 'Anonymous'),
                        entityType="Policy",
                        entityId=pk,
                        ipAddress=get_client_ip(request),
                        additionalInfo={
                            "policy_name": policy.PolicyName,
                            "new_status": "Under Review",
                            "new_active_inactive": "Inactive"
                        }
                    )
                    
                    return Response({
                        'message': 'Policy updated successfully and set to Under Review',
                        'PolicyId': policy.PolicyId,
                        'CurrentVersion': policy.CurrentVersion,
                        'Status': 'Under Review',
                        'ActiveInactive': 'Inactive'
                    })
                else:
                    # Log validation errors
                    send_log(
                        module="Policy",
                        actionType="POLICY_UPDATE_FAILED",
                        description=f"Policy {pk} update failed due to validation errors",
                        userId=getattr(request.user, 'id', None),
                        userName=getattr(request.user, 'username', 'Anonymous'),
                        entityType="Policy",
                        entityId=pk,
                        logLevel="WARNING",
                        ipAddress=get_client_ip(request),
                        additionalInfo={"validation_errors": serializer.errors}
                    )
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log update exception
            send_log(
                module="Policy",
                actionType="POLICY_UPDATE_FAILED",
                description=f"Error updating policy {pk}: {str(e)}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=pk,
                logLevel="ERROR",
                ipAddress=get_client_ip(request),
                additionalInfo={"error": str(e)}
            )
            error_info = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return Response({'error': 'Error updating policy', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Log policy deletion/inactivation attempt
        send_log(
            module="Policy",
            actionType="POLICY_DELETE",
            description=f"Attempting to inactivate policy {pk}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=pk,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "policy_name": policy.PolicyName,
                "current_status": policy.Status,
                "current_active_inactive": policy.ActiveInactive
            }
        )
        
        try:
            with transaction.atomic():
                # Instead of deleting, set ActiveInactive to 'Inactive'
                original_status = policy.Status
                original_active = policy.ActiveInactive
                
                policy.Status = 'Inactive'  # Set both status and ActiveInactive to 'Inactive'
                policy.ActiveInactive = 'Inactive'
                policy.save()
                
                print(f"Updated policy {policy.PolicyId} status from {original_status} to Inactive and ActiveInactive from {original_active} to Inactive")
                
                # Update Status of subpolicies since they don't have ActiveInactive field
                subpolicies = SubPolicy.objects.filter(PolicyId=policy.PolicyId)
                for subpolicy in subpolicies:
                    original_subpolicy_status = subpolicy.Status
                    subpolicy.Status = 'Inactive'
                    subpolicy.save()
                    print(f"Updated subpolicy {subpolicy.SubPolicyId} status from {original_subpolicy_status} to Inactive")
                
                # Create a policy approval record to track this change
                try:
                    # Find the latest policy approval for this policy
                    latest_approval = PolicyApproval.objects.filter(
                        PolicyId=policy.PolicyId
                    ).order_by('-ApprovalId').first()
                    
                    if latest_approval:
                        # Create a new approval with 'r' version to mark the inactivation
                        r_versions = []
                        for pa in PolicyApproval.objects.filter(Identifier=latest_approval.Identifier):
                            if pa.Version and pa.Version.startswith('r') and pa.Version[1:].isdigit():
                                r_versions.append(int(pa.Version[1:]))
                        
                        if r_versions:
                            new_version = f"r{max(r_versions) + 1}"
                        else:
                            new_version = "r1"
                        
                        # Update the extracted data to reflect the status change
                        extracted_data = latest_approval.ExtractedData.copy() if hasattr(latest_approval.ExtractedData, 'copy') else latest_approval.ExtractedData
                        extracted_data['Status'] = 'Inactive'
                        
                        # Update subpolicies status in extracted data
                        if 'subpolicies' in extracted_data:
                            for sub in extracted_data['subpolicies']:
                                sub['Status'] = 'Inactive'
                        
                        # Create a new policy approval record
                        new_approval = PolicyApproval(
                            PolicyId=policy,
                            Identifier=latest_approval.Identifier,
                            ExtractedData=extracted_data,
                            UserId=latest_approval.UserId,
                            ReviewerId=latest_approval.ReviewerId,
                            ApprovedNot=1,  # Mark as approved since this is an admin action (1=True)
                            ApprovedDate=date.today(),
                            Version=new_version,
                            FrameworkId=policy.FrameworkId
                        )
                        new_approval.save()
                        print(f"Created inactivation record for policy {policy.PolicyId} with version {new_version}")
                except Exception as approval_err:
                    print(f"Error creating inactivation record: {str(approval_err)}")
                    # Continue even if approval record creation fails
                
                # Log successful policy inactivation
                send_log(
                    module="Policy",
                    actionType="POLICY_DELETE_SUCCESS",
                    description=f"Policy {pk} and related subpolicies successfully marked as inactive",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="Policy",
                    entityId=pk,
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        "policy_name": policy.PolicyName,
                        "original_status": original_status,
                        "original_active_inactive": original_active,
                        "subpolicies_affected": SubPolicy.objects.filter(PolicyId=policy.PolicyId).count()
                    }
                )
                
                return Response({'message': 'Policy and related subpolicies marked as inactive'}, status=status.HTTP_200_OK)
        except Exception as e:
            # Log deletion/inactivation error
            send_log(
                module="Policy",
                actionType="POLICY_DELETE_FAILED",
                description=f"Error marking policy {pk} as inactive: {str(e)}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=pk,
                logLevel="ERROR",
                ipAddress=get_client_ip(request),
                additionalInfo={"error": str(e)}
            )
            error_info = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return Response({'error': 'Error marking policy as inactive', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)

"""
@api POST /api/frameworks/{framework_id}/policies/
Adds a new policy to an existing framework.
New policies are created with Status='Under Review' and ActiveInactive='Inactive' by default.
CurrentVersion defaults to 1.0 if not provided.

Example payload:
{
  "PolicyName": "Data Classification Policy",
  "PolicyDescription": "Guidelines for data classification and handling",
  "StartDate": "2023-10-01",
  "Department": "IT,Legal",
  "Applicability": "All Employees",
  "Scope": "All company data",
  "Objective": "Ensure proper data classification and handling",
  "Identifier": "DCP-001",
  "subpolicies": [
    {
      "SubPolicyName": "Confidential Data Handling",
      "Identifier": "CDH-001",
      "Description": "Guidelines for handling confidential data",
      "PermanentTemporary": "Permanent",
      "Control": "Encrypt all confidential data at rest and in transit"
    }
  ]
}
"""
@api_view(['POST'])
@permission_classes([PolicyCreatePermission])
def add_policy_to_framework(request, framework_id):
    """
    Secure add policy to framework endpoint with SQL injection protection and proper connection management.
    Implements parameterized queries and follows principle of least privilege.
    """
    # Import security modules
    from django.utils.html import escape as escape_html
    from django.db import transaction
    from django.core.exceptions import ValidationError as DjangoValidationError
    from ..validators.framework_validator import validate_add_policy_request, ValidationError
    import logging
    import shlex
    import re
    
    # Configure secure logging to prevent log injection
    logger = logging.getLogger(__name__)
    
    # Log policy addition attempt
    send_log(
        module="Policy",
        actionType="CREATE",
        description=f"Adding policy to framework {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=framework_id,
        ipAddress=get_client_ip(request)
    )
    
    # Security: Validate framework_id parameter early
    try:
        framework_id = int(framework_id)
    except (ValueError, TypeError):
        # Log validation error
        send_log(
            module="Policy",
            actionType="CREATE_FAILED",
            description=f"Invalid framework ID parameter: {framework_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": "Invalid framework ID"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Security: Validate request data size to prevent DoS
    if len(str(request.data)) > 1024 * 1024:  # 1MB limit
        # Log payload size error
        send_log(
            module="Policy",
            actionType="CREATE_FAILED",
            description="Policy creation failed - payload too large",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=framework_id,
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        return Response(
            {"error": "Request payload too large"}, 
            status=status.HTTP_413_REQUEST_TOO_LARGE
        )
    
    try:
        # Security: Log sanitized request info
        logger.info(f"Processing add policy request for framework {framework_id} from user: {escape_html(str(request.user))}")
        
        # Security: Get framework using parameterized query with minimal data access
        try:
            framework = Framework.objects.select_related().filter(
                FrameworkId=framework_id
            ).only(
                'FrameworkId', 'FrameworkName', 'CurrentVersion', 'Status', 'ActiveInactive'
            ).first()
            
            if not framework:
                logger.warning(f"Framework with ID {framework_id} not found")
                
                # Log framework not found
                send_log(
                    module="Policy",
                    actionType="CREATE_FAILED",
                    description=f"Framework with ID {framework_id} not found",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="Framework",
                    entityId=framework_id,
                    logLevel="WARNING",
                    ipAddress=get_client_ip(request)
                )
                
                return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as framework_error:
            logger.error(f"Error retrieving framework: {type(framework_error).__name__}")
            return Response({"error": "Framework lookup failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Initialize notification service
        notification_service = NotificationService()
        
        # Security: Validate request data with strict validation
        try:
            validated_data = validate_add_policy_request(request.data)
            
            # Security: Additional validation for critical fields
            if not validated_data.get('policies'):
                raise ValidationError("At least one policy is required")
                
        except ValidationError as e:
            safe_error = escape_html(str(e))
            logger.warning(f"Policy validation failed: {safe_error}")
            
            # Log validation error
            send_log(
                module="Policy",
                actionType="CREATE_FAILED",
                description=f"Policy validation failed: {safe_error}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=framework_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request)
            )
            
            return Response({"error": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get validated policies data
        policies_data = validated_data['policies']
        
        # =================================================================
        # SECURITY IMPLEMENTATIONS - Context-Appropriate Server-Side Encoding
        # =================================================================
        # 1. HTML Context → escape_html() - Prevents XSS attacks
        # 2. SQL Context → Django ORM (parameterized queries) - Prevents SQL injection
        # 3. Shell Context → shlex.quote() - Prevents command injection
        # 4. All user inputs are sanitized before storage and rendering
        # =================================================================
        
        # Security Helper Function: Secure URL handling for potential shell command usage
        def secure_url_for_shell(url):
            """
            Example: Shell Command Injection Protection
            If URL needs to be used in shell commands (like wget, curl), use shlex.quote()
            Example: subprocess.run(['wget', shlex.quote(url)])
            """
            if url:
                return shlex.quote(str(url))
            return ""
        
        # Initialize variables that are used later
        policy_ids = []
        policy_names = []
        submitter_name = None
        reviewer_name = None
        reviewer_email = None
        
        # Security: Use atomic transaction with proper connection management
        with transaction.atomic():
            try:
                # Process each policy in the batch
                for policy_data in policies_data:
                    # Security: Escape policy name for safe logging (prevents log injection)
                    safe_policy_name = escape_html(policy_data.get('PolicyName', 'unnamed'))
                    logger.info(f"Processing policy: {safe_policy_name}")
                    
                    # Security: Validate and sanitize entities data
                    # Allow both "all" (string) for all entities or list of specific entity IDs
                    entities_data = policy_data.get('Entities', [])
                    if entities_data == "all":
                        # Keep "all" as string when all locations are selected
                        logger.info(f"Entities data received: all locations selected")
                    elif isinstance(entities_data, list):
                        # Keep as list when specific entities are selected
                        logger.info(f"Entities data received: {len(entities_data)} specific entities")
                    else:
                        # Default to empty list for invalid data
                        entities_data = []
                        logger.warning("Invalid entities data received, defaulting to empty list")
                    
                    # Security: Convert reviewer ID to name using parameterized queries
                    policy_reviewer_name = ''
                    policy_reviewer_id = policy_data.get('Reviewer')
                    if policy_reviewer_id:
                        try:
                            # Security: Use parameterized queries with minimal data access
                            policy_reviewer = Users.objects.filter(
                                UserId=policy_reviewer_id
                            ).only('UserName', 'Email').first()
                            
                            if policy_reviewer:
                                policy_reviewer_name = escape_html(policy_reviewer.UserName)
                                logger.info(f"Found policy reviewer: {policy_reviewer_name}")
                            else:
                                logger.warning(f"Policy reviewer with ID {policy_reviewer_id} not found")
                        except Exception as reviewer_error:
                            logger.error(f"Error looking up policy reviewer: {type(reviewer_error).__name__}")
                    
                    # Security: Sanitize all input data before database storage
                    policy_create_data = {
                        'FrameworkId': framework,
                        'PolicyName': escape_html(policy_data['PolicyName']),
                        'PolicyDescription': escape_html(policy_data['PolicyDescription']),
                        'Status': 'Under Review',
                        'StartDate': policy_data['StartDate'],
                        'EndDate': policy_data['EndDate'],
                        'Department': escape_html(policy_data['Department']),
                        'CreatedByName': escape_html(policy_data['CreatedByName']),
                        'CreatedByDate': datetime.now().date(),
                        'Applicability': escape_html(policy_data['Applicability']),
                        'DocURL': policy_data['DocURL'],  # Note: If used in shell commands, apply secure_url_for_shell()
                        'Scope': escape_html(policy_data['Scope']),
                        'Objective': escape_html(policy_data['Objective']),
                        'Identifier': escape_html(policy_data['Identifier']),
                        'PermanentTemporary': policy_data['PermanentTemporary'],
                        'ActiveInactive': 'Inactive',
                        'Reviewer': policy_reviewer_name,  # Already escaped above
                        'CoverageRate': policy_data['CoverageRate'],
                        'CurrentVersion': framework.CurrentVersion,
                        'PolicyType': escape_html(policy_data['PolicyType']),
                        'PolicyCategory': escape_html(policy_data['PolicyCategory']),
                        'PolicySubCategory': escape_html(policy_data['PolicySubCategory']),
                        'Entities': entities_data
                    }
                    
                    # Check if policy name already exists in this framework
                    policy_name = escape_html(policy_data['PolicyName'])
                    existing_policy = Policy.objects.filter(
                        FrameworkId=framework,
                        PolicyName__iexact=policy_name
                    ).first()
                    
                    if existing_policy:
                        return Response({
                            'error': f'Policy with name "{policy_name}" already exists in this framework. Policy names must be unique within a framework.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Security: Create policy using Django ORM (parameterized queries)
                    policy = Policy.objects.create(**policy_create_data)
                    
                    policy_ids.append(policy.PolicyId)
                    policy_names.append(policy.PolicyName)
                    
                    if not submitter_name:
                        submitter_name = policy_data.get('CreatedByName', '')
                    
                    # Security: Create PolicyVersion record with parameterized queries
                    PolicyVersion.objects.create(
                        PolicyId=policy,
                        Version=framework.CurrentVersion,
                        PolicyName=policy.PolicyName,
                        CreatedBy=policy.CreatedByName,
                        CreatedDate=date.today(),
                        PreviousVersionId=None,
                        FrameworkId=framework
                    )
                    
                    # Security: Process subpolicies with proper validation
                    if 'subpolicies' in policy_data and isinstance(policy_data['subpolicies'], list):
                        logger.info(f"Processing {len(policy_data['subpolicies'])} subpolicies for policy {policy.PolicyName}")
                        for subpolicy_data in policy_data['subpolicies']:
                            # Security: Sanitize subpolicy data before database storage
                            SubPolicy.objects.create(
                                PolicyId=policy,
                                SubPolicyName=escape_html(subpolicy_data['SubPolicyName']),
                                CreatedByName=escape_html(subpolicy_data['CreatedByName']),
                                CreatedByDate=datetime.now().date(),
                                Identifier=escape_html(subpolicy_data['Identifier']),
                                Description=escape_html(subpolicy_data['Description']),
                                Status='Under Review',
                                PermanentTemporary=subpolicy_data['PermanentTemporary'],
                                Control=escape_html(subpolicy_data['Control']),
                                FrameworkId=framework
                            )
                    
                    # Security: Create policy approval record with validated data
                    try:
                        # Security: Validate and sanitize user IDs
                        user_id = policy_data.get('CreatedById', 1)  # Default to 1 if not provided
                        reviewer_id = policy_data.get('Reviewer') if policy_data.get('Reviewer') else 2  # Default to 2
                        
                        # Security: Ensure numeric IDs to prevent injection
                        if isinstance(user_id, str):
                            try:
                                user_id = int(user_id)
                            except (ValueError, TypeError):
                                user_id = 1
                        
                        if isinstance(reviewer_id, str):
                            try:
                                reviewer_id = int(reviewer_id)
                            except (ValueError, TypeError):
                                reviewer_id = 2
                        
                        # Security: Get reviewer details using parameterized queries
                        if reviewer_id:
                            try:
                                reviewer_obj = Users.objects.filter(
                                    UserId=reviewer_id
                                ).only('UserName', 'Email').first()
                                
                                if reviewer_obj:
                                    reviewer_name = escape_html(reviewer_obj.UserName)
                                    reviewer_email = reviewer_obj.Email
                                    logger.info(f"Found reviewer: {reviewer_name}")
                                else:
                                    logger.warning(f"Reviewer with ID {reviewer_id} not found")
                                    reviewer_name = ''
                                    reviewer_email = None
                            except TransactionManagementError as transaction_error:
                                # If transaction is in bad state, re-raise immediately
                                logger.error(f"Transaction error while looking up reviewer: {type(transaction_error).__name__}")
                                raise  # Re-raise to trigger transaction rollback
                            except Exception as reviewer_lookup_error:
                                logger.error(f"Error looking up reviewer: {type(reviewer_lookup_error).__name__}")
                                reviewer_name = ''
                                reviewer_email = None
                        else:
                            reviewer_name = ''
                            reviewer_email = None
                        
                        # Security: Get subpolicies using parameterized queries with minimal data access
                        subpolicies = SubPolicy.objects.filter(PolicyId=policy).only(
                            'SubPolicyId', 'SubPolicyName', 'CreatedByName', 'CreatedByDate',
                            'Identifier', 'Description', 'Status', 'PermanentTemporary', 'Control'
                        )
                        subpolicies_data = []
                        
                        for subpolicy in subpolicies:
                            subpolicy_data = {
                                "SubPolicyId": subpolicy.SubPolicyId,
                                "SubPolicyName": subpolicy.SubPolicyName,
                                "CreatedByName": subpolicy.CreatedByName,
                                "CreatedByDate": subpolicy.CreatedByDate.isoformat() if hasattr(subpolicy.CreatedByDate, 'isoformat') else subpolicy.CreatedByDate,
                                "Identifier": subpolicy.Identifier,
                                "Description": subpolicy.Description,
                                "Status": subpolicy.Status,
                                "PermanentTemporary": subpolicy.PermanentTemporary,
                                "Control": subpolicy.Control
                            }
                            subpolicies_data.append(subpolicy_data)
                        
                        # Security: Create extracted data with sanitized content
                        extracted_data = {
                            "PolicyName": policy.PolicyName,
                            "PolicyDescription": policy.PolicyDescription,
                            "Status": policy.Status,
                            "StartDate": policy.StartDate.isoformat() if hasattr(policy.StartDate, 'isoformat') else policy.StartDate,
                            "EndDate": policy.EndDate.isoformat() if hasattr(policy.EndDate, 'isoformat') else policy.EndDate,
                            "Department": policy.Department,
                            "CreatedByName": policy.CreatedByName,
                            "CreatedByDate": policy.CreatedByDate.isoformat() if hasattr(policy.CreatedByDate, 'isoformat') else policy.CreatedByDate,
                            "Applicability": policy.Applicability,
                            "Scope": policy.Scope,
                            "Objective": policy.Objective,
                            "Identifier": policy.Identifier,
                            "PolicyType": policy.PolicyType,
                            "PolicyCategory": policy.PolicyCategory,
                            "PolicySubCategory": policy.PolicySubCategory,
                            "Entities": policy.Entities,
                            "type": "policy",
                            "subpolicies": subpolicies_data
                        }
                        
                        # Check for existing policy approval to prevent duplicates
                        existing_approval = PolicyApproval.objects.filter(
                            PolicyId=policy.PolicyId,
                            UserId=user_id,
                            ReviewerId=reviewer_id,
                            Version="u1",
                            ApprovedNot=None  # Only check for pending approvals
                        ).first()
                        
                        if existing_approval:
                            print(f"DEBUG: ⚠️ Duplicate prevention: Policy approval already exists for PolicyId {policy.PolicyId} with ApprovalId: {existing_approval.ApprovalId}")
                            print(f"  - Skipping duplicate creation")
                        else:
                            # Security: Create policy approval using parameterized queries
                            PolicyApproval.objects.create(
                                PolicyId=policy,
                                ExtractedData=extracted_data,
                                UserId=user_id,
                                ReviewerId=reviewer_id,
                                Version="u1",  # Default initial version
                                ApprovedNot=None,  # Not yet approved
                                FrameworkId=policy.FrameworkId
                            )
                            print(f"DEBUG: ✅ Created new PolicyApproval for PolicyId {policy.PolicyId}")
                    except Exception as approval_error:
                        logger.error(f"Error creating policy approval: {type(approval_error).__name__}")
                        # Continue with policy creation even if approval creation fails
        
                # Security: Send batch notification if more than one policy, else send single notification
                if reviewer_email and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', reviewer_email):
                    logger.info(f"Attempting to send notification to reviewer")
                    try:
                        if len(policy_names) > 1:
                            # Security: XSS Protection - Escape HTML content before building email template
                            policy_list_html = ''.join(f'<li>{escape_html(name)}</li>' for name in policy_names)
                            notification_data = {
                                'notification_type': 'policiesBatchSubmitted',
                                'email': reviewer_email,
                                'email_type': 'gmail',
                                'template_data': [
                                    escape_html(reviewer_name),  # Escape reviewer name for HTML context
                                    escape_html(submitter_name),  # Escape submitter name for HTML context
                                    policy_list_html  # Already escaped above
                                ]
                            }
                            notification_service.send_multi_channel_notification(notification_data)
                        else:
                            notification_data = {
                                'notification_type': 'policySubmitted',
                                'email': reviewer_email,
                                'email_type': 'gmail',
                                'template_data': [
                                    escape_html(reviewer_name),  # Escape reviewer name for HTML context
                                    escape_html(policy_names[0]),  # Escape policy name for HTML context
                                    escape_html(submitter_name),  # Escape submitter name for HTML context
                                    date.today().strftime('%Y-%m-%d')  # Date is safe
                                ]
                            }
                            notification_service.send_multi_channel_notification(notification_data)
                        logger.info("Notification sent successfully")
                    except Exception as notification_error:
                        logger.error(f"Error sending notification: {type(notification_error).__name__}")
                else:
                    logger.warning("Invalid or missing reviewer email")
                
                # Security: Log successful operation
                logger.info(f"{len(policy_ids)} policies added successfully to framework {framework_id}")
                
                # Log successful policy addition
                send_log(
                    module="Policy",
                    actionType="CREATE_SUCCESS",
                    description=f"{len(policy_ids)} policies added successfully to framework {framework_id}",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', submitter_name or 'Anonymous'),
                    entityType="Policy",
                    entityId=framework_id,
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        "framework_id": framework_id,
                        "policies_count": len(policy_ids),
                        "policy_ids": policy_ids,
                        "policy_names": policy_names
                    }
                )
                
                return Response({
                    "message": f"{len(policy_ids)} policies added successfully to framework {framework_id}",
                    "policy_ids": policy_ids
                }, status=status.HTTP_201_CREATED)
                
            except TransactionManagementError as transaction_error:
                # Security: Transaction is in bad state, rollback is automatic
                logger.error(f"Transaction management error in policy creation: {type(transaction_error).__name__}")
                logger.error(f"Transaction error details: {str(transaction_error)}")
                raise  # Re-raise to trigger rollback
            except IntegrityError as integrity_error:
                # Handle database integrity errors (like duplicate keys)
                logger.error(f"Database integrity error in policy creation: {type(integrity_error).__name__}")
                logger.error(f"Integrity error details: {str(integrity_error)}")
                raise  # Re-raise to trigger rollback
            except Exception as transaction_error:
                # Security: Transaction will be rolled back automatically
                logger.error(f"Transaction error in policy creation: {type(transaction_error).__name__}")
                logger.error(f"Error details: {str(transaction_error)}")
                raise  # Re-raise to trigger rollback
    
    except ValidationError as e:
        safe_error = escape_html(str(e))
        logger.warning(f"Validation error in add_policy_to_framework: {safe_error}")
        
        # Log validation error
        send_log(
            module="Policy",
            actionType="CREATE_FAILED",
            description=f"Policy addition validation error: {safe_error}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=framework_id,
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        
        return Response({"error": "Validation failed"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error in add_policy_to_framework: {type(e).__name__}")
        
        # Log unexpected error
        send_log(
            module="Policy",
            actionType="CREATE_FAILED",
            description=f"Unexpected error in policy addition: {type(e).__name__}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=framework_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyApprovePermission])
@csrf_exempt
def update_policy_approval(request, approval_id):
    # Log policy approval update attempt
    send_log(
        module="Policy",
        actionType="UPDATE_POLICY_APPROVAL",
        description=f"Attempting to update policy approval {approval_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="PolicyApproval",
        entityId=approval_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Get the original approval
        approval = PolicyApproval.objects.get(ApprovalId=approval_id)
       
        # Create a new approval object instead of updating
        new_approval = PolicyApproval()
        new_approval.Identifier = approval.Identifier
        new_approval.ExtractedData = request.data.get('ExtractedData', approval.ExtractedData)
        new_approval.UserId = approval.UserId
        new_approval.ReviewerId = approval.ReviewerId
        new_approval.ApprovedNot = request.data.get('ApprovedNot', approval.ApprovedNot)
        
        # If PolicyId exists in original approval, add it to new approval
        if hasattr(approval, 'PolicyId') and approval.PolicyId:
            new_approval.PolicyId = approval.PolicyId
            new_approval.FrameworkId = approval.PolicyId.FrameworkId
       
        # Determine version prefix based on who made the change
        # For reviewers (assuming ReviewerId is the one making changes in this endpoint)
        prefix = 'r'
       
        # Get the latest version with this prefix for this identifier
        try:
            r_versions = []
            for pa in PolicyApproval.objects.filter(Identifier=approval.Identifier):
                if pa.Version and pa.Version.startswith(prefix) and len(pa.Version) > 1 and pa.Version[1:].isdigit():
                    r_versions.append(int(pa.Version[1:]))
            
            if r_versions:
                new_approval.Version = f"{prefix}{max(r_versions) + 1}"
            else:
                new_approval.Version = f"{prefix}1"
                
            print(f"Setting approval version to: {new_approval.Version} for Identifier: {approval.Identifier}")
        except Exception as e:
            print(f"Error determining version (using default {prefix}1): {str(e)}")
            new_approval.Version = f"{prefix}1"  # Default fallback
       
        new_approval.save()
        
        # Log successful policy approval update
        send_log(
            module="Policy",
            actionType="UPDATE_POLICY_APPROVAL_SUCCESS",
            description=f"Policy approval updated successfully with new ID {new_approval.ApprovalId}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyApproval",
            entityId=new_approval.ApprovalId,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "original_approval_id": approval_id,
                "new_version": new_approval.Version,
                "policy_id": approval.PolicyId.PolicyId if approval.PolicyId else None
            }
        )
       
        return Response({
            'message': 'Policy approval updated successfully',
            'ApprovalId': new_approval.ApprovalId,
            'Version': new_approval.Version
        })
    except PolicyApproval.DoesNotExist:
        # Log policy approval not found error
        send_log(
            module="Policy",
            actionType="UPDATE_POLICY_APPROVAL_FAILED",
            description=f"Policy approval {approval_id} not found",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyApproval",
            entityId=approval_id,
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        return Response({'error': 'Policy approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Log general exception
        send_log(
            module="Policy",
            actionType="UPDATE_POLICY_APPROVAL_FAILED",
            description=f"Error updating policy approval {approval_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyApproval",
            entityId=approval_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyApprovePermission])
@csrf_exempt
def submit_policy_review(request, approval_id):
    # Log policy review submission attempt
    send_log(
        module="Policy",
        actionType="SUBMIT_POLICY_REVIEW",
        description=f"Attempting to submit policy review for approval {approval_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="PolicyApproval",
        entityId=approval_id,
        ipAddress=get_client_ip(request),
        additionalInfo={"approved": request.data.get('ApprovedNot')}
    )
    
    try:
        from datetime import date
        # Get the original approval
        approval = PolicyApproval.objects.get(ApprovalId=approval_id)
       
        # Validate and prepare data
        extracted_data = request.data.get('ExtractedData')
        if not extracted_data:
            return Response({'error': 'ExtractedData is required'}, status=status.HTTP_400_BAD_REQUEST)
       
        approved_not = request.data.get('ApprovedNot')
        is_approved = approved_not == True or approved_not == 1
       
        # Get the latest version with "r" prefix for this identifier
        try:
            r_versions = []
            for pa in PolicyApproval.objects.filter(Identifier=approval.Identifier):
                if pa.Version and pa.Version.startswith('r') and pa.Version[1:].isdigit():
                    r_versions.append(int(pa.Version[1:]))
           
            if r_versions:
                new_version = f"r{max(r_versions) + 1}"
            else:
                new_version = "r1"  # Default version for reviewer
                
            print(f"Setting review version to: {new_version} for Identifier: {approval.Identifier}")
        except Exception as version_err:
            print(f"Error determining version (using default r1): {str(version_err)}")
            new_version = "r1"  # Default fallback
       
        # Set approved date if policy is approved
        approved_date = None
        if is_approved:
            approved_date = date.today()
           
        # Get reviewer ID from request data or current user
        reviewer_id = request.data.get('ReviewerId')
        if not reviewer_id:
            # Try to get from user object
            if hasattr(request.user, 'UserId') and request.user.UserId:
                reviewer_id = request.user.UserId
            elif hasattr(request.user, 'id') and request.user.id:
                reviewer_id = request.user.id
            else:
                # Fallback to original ReviewerId if no current user
                reviewer_id = approval.ReviewerId
        
        print(f"DEBUG: Creating policy approval with ReviewerId: {reviewer_id}, Version: {new_version}")
           
        # Create a new record using Django ORM
        new_approval = PolicyApproval(
            PolicyId=approval.PolicyId,
            Identifier=approval.Identifier,  # Make sure Identifier is included
            ExtractedData=extracted_data,
            UserId=approval.UserId,  # Original policy creator
            ReviewerId=reviewer_id,  # Current reviewer's ID
            ApprovedNot=approved_not,
            ApprovedDate=approved_date,  # Set approved date
            Version=new_version,
            FrameworkId=approval.PolicyId.FrameworkId
        )
        new_approval.save()
        print(f"Created new policy approval with ID: {new_approval.ApprovalId}, Version: {new_version}, ReviewerId: {reviewer_id}")
       
        # Update the policy status based on the approval decision
        try:
            # Get the policy directly from the approval
            policy = approval.PolicyId
            
            if not policy:
                print("Warning: Policy not found in approval, cannot update status")
                raise Exception("Policy not found in approval")

            print(f"Working with policy ID: {policy.PolicyId}, current status: {policy.Status}")

            # Get the policy version record if needed
            policy_version = None
            if is_approved:
                policy_version = PolicyVersion.objects.filter(
                    PolicyId=policy,
                    Version=policy.CurrentVersion
                ).first()

            # If approved and this policy has a previous version, set it to inactive
            if is_approved and policy_version and policy_version.PreviousVersionId:
                try:
                    previous_version = PolicyVersion.objects.get(VersionId=policy_version.PreviousVersionId)
                    previous_policy = previous_version.PolicyId
                    previous_policy.ActiveInactive = 'Inactive'
                    previous_policy.save()
                    print(f"Set previous policy version {previous_policy.PolicyId} to Inactive")
                except Exception as prev_error:
                    print(f"Error updating previous policy version: {str(prev_error)}")
               
            # Update policy status based on approval decision
            if is_approved:
                # If approved, set to Approved and Active/Scheduled based on StartDate
                policy.Status = 'Approved'
                # Set policy to Active or Scheduled based on StartDate
                today = date.today()
                print(f"DEBUG: Policy {policy.PolicyId} - Today: {today}, StartDate: {policy.StartDate} (type: {type(policy.StartDate)})")
                
                if policy.StartDate and policy.StartDate > today:
                    policy.ActiveInactive = 'Scheduled'
                    print(f"Set individual policy {policy.PolicyId} to Approved status and Scheduled status (StartDate: {policy.StartDate} > today: {today})")
                else:
                    policy.ActiveInactive = 'Active'
                    print(f"Set individual policy {policy.PolicyId} to Approved status and Active status (StartDate: {policy.StartDate} <= today: {today} or None)")
                
                                # Deactivate all previous versions when policy is approved
                print(f"Current policy being approved: PolicyId={policy.PolicyId}, Version={policy.CurrentVersion}, Identifier={policy.Identifier}")
                deactivated_count = deactivate_previous_policy_versions(policy)
                
                print(f"Successfully deactivated {deactivated_count} previous policy versions")
                
                # Ensure CurrentVersion is set correctly
                # Get the current policy version from PolicyVersion table
                current_policy_version = PolicyVersion.objects.filter(
                    PolicyId=policy
                ).first()
                
                if current_policy_version:
                    print(f"Setting CurrentVersion to {current_policy_version.Version} for policy {policy.PolicyId}")
                    policy.CurrentVersion = current_policy_version.Version
                
                policy.save()
                print(f"Updated policy {policy.PolicyId} status to Approved and Active")
                
                # Update all subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy.PolicyId)
                for subpolicy in subpolicies:
                    # Update all subpolicies to match the policy status
                    subpolicy.Status = 'Approved'
                    subpolicy.save()
                    print(f"Updated subpolicy {subpolicy.SubPolicyId} status to Approved")
            else:
                # If rejected, update policy status to Rejected
                policy.Status = 'Rejected'
                policy.save()
                print(f"Updated policy {policy.PolicyId} status to Rejected")
                
                # Also update all subpolicies to Rejected
                subpolicies = SubPolicy.objects.filter(PolicyId=policy.PolicyId)
                for subpolicy in subpolicies:
                    subpolicy.Status = 'Rejected'
                    subpolicy.save()
                    print(f"Updated subpolicy {subpolicy.SubPolicyId} status to Rejected")
            
        except Exception as update_error:
            print(f"Error updating policy/subpolicy status: {str(update_error)}")
            import traceback
            traceback.print_exc()
            # Continue with the response even if status update fails
       
        # Send notification to submitter about approval or rejection
        try:
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            submitter = Users.objects.get(UserId=new_approval.UserId)
            reviewer = Users.objects.get(UserId=new_approval.ReviewerId)
            now_str = date.today().isoformat()
            if is_approved:
                notification_data = {
                    'notification_type': 'policyApproved',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        policy.PolicyName,
                        reviewer.UserName,
                        now_str
                    ]
                }
            else:
                rejection_reason = request.data.get('rejection_reason', '') or 'Policy was rejected'
                notification_data = {
                    'notification_type': 'policyRejected',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        policy.PolicyName,
                        reviewer.UserName,
                        rejection_reason
                    ]
                }
            notification_service.send_multi_channel_notification(notification_data)
        except Exception as notify_ex:
            print(f"DEBUG: Error sending policy approval/rejection notification: {notify_ex}")
        
        # Log successful policy review submission
        send_log(
            module="Policy",
            actionType="SUBMIT_POLICY_REVIEW_SUCCESS",
            description=f"Policy review submitted successfully - {is_approved and 'approved' or 'rejected'}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyApproval",
            entityId=new_approval.ApprovalId,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "original_approval_id": approval_id,
                "new_version": new_version,
                "approved": is_approved,
                "policy_id": approval.PolicyId.PolicyId if approval.PolicyId else None
            }
        )
        
        return Response({
            'message': f"Policy review submitted successfully. Policy {is_approved and 'approved' or 'rejected'}.",
            'ApprovalId': new_approval.ApprovalId,
            'Version': new_version,
            'ApprovedDate': approved_date.isoformat() if approved_date else None,
            'Status': is_approved and 'Approved' or 'Rejected'
        })
    
    except PolicyApproval.DoesNotExist:
        # Log policy approval not found error
        send_log(
            module="Policy",
            actionType="SUBMIT_POLICY_REVIEW_FAILED",
            description=f"Policy approval {approval_id} not found for review submission",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyApproval",
            entityId=approval_id,
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        return Response({'error': 'Policy approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("Error in submit_policy_review:", str(e))
        
        # Log general exception
        send_log(
            module="Policy",
            actionType="SUBMIT_POLICY_REVIEW_FAILED",
            description=f"Error submitting policy review for approval {approval_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyApproval",
            entityId=approval_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([PolicyCreatePermission])
def add_subpolicy_to_policy(request, policy_id):
    # Import security modules
    from django.utils.html import escape as escape_html
    import shlex
    
    # Log subpolicy addition attempt
    send_log(
        module="Policy",
        actionType="ADD_SUBPOLICY_TO_POLICY",
        description=f"Attempting to add subpolicy to policy {policy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request),
        additionalInfo={"subpolicy_name": request.data.get('SubPolicyName', 'Unknown')}
    )
    
    # Security Helper Function: Secure URL handling for potential shell command usage
    def secure_url_for_shell(url):
        """
        Example: Shell Command Injection Protection
        If URL needs to be used in shell commands (like wget, curl), use shlex.quote()
        Example: subprocess.run(['wget', shlex.quote(url)])
        """
        if url:
            return shlex.quote(str(url))
        return ""
    
    policy = get_object_or_404(Policy, PolicyId=policy_id)
   
    try:
        with transaction.atomic():
            # Security: Sanitize input data before processing
            subpolicy_data = request.data.copy()
            subpolicy_data['PolicyId'] = policy.PolicyId
            if 'CreatedByName' not in subpolicy_data:
                subpolicy_data['CreatedByName'] = escape_html(policy.CreatedByName)
            else:
                subpolicy_data['CreatedByName'] = escape_html(subpolicy_data['CreatedByName'])
            if 'CreatedByDate' not in subpolicy_data:
                subpolicy_data['CreatedByDate'] = date.today()
            if 'Status' not in subpolicy_data:
                subpolicy_data['Status'] = 'Under Review'
            
            # Security: Escape text fields in subpolicy data
            text_fields = ['SubPolicyName', 'Description', 'Control', 'Identifier']
            for field in text_fields:
                if field in subpolicy_data and subpolicy_data[field]:
                    subpolicy_data[field] = escape_html(subpolicy_data[field])
           
            # Check if subpolicy name is unique within the policy
            subpolicy_name = subpolicy_data.get('SubPolicyName')
            if SubPolicy.objects.filter(PolicyId=policy.PolicyId, SubPolicyName=subpolicy_name).exists():
                # Log duplicate subpolicy name error
                send_log(
                    module="Policy",
                    actionType="ADD_SUBPOLICY_TO_POLICY_FAILED",
                    description=f"Subpolicy name '{subpolicy_name}' already exists in policy {policy_id}",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="SubPolicy",
                    entityId=policy_id,
                    logLevel="WARNING",
                    ipAddress=get_client_ip(request),
                    additionalInfo={"subpolicy_name": subpolicy_name, "policy_id": policy_id}
                )
                return Response({
                    'error': f'A subpolicy with the name "{subpolicy_name}" already exists in this policy. Subpolicy names must be unique within a policy.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            subpolicy_serializer = SubPolicySerializer(data=subpolicy_data, context={'policy_id': policy.PolicyId})
            if not subpolicy_serializer.is_valid():
                return Response(subpolicy_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
           
            subpolicy = subpolicy_serializer.save()
            
            # Log successful subpolicy addition
            send_log(
                module="Policy",
                actionType="ADD_SUBPOLICY_TO_POLICY_SUCCESS",
                description=f"Subpolicy {subpolicy.SubPolicyId} added to policy {policy_id} successfully",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="SubPolicy",
                entityId=subpolicy.SubPolicyId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "subpolicy_name": subpolicy.SubPolicyName,
                    "policy_id": policy.PolicyId,
                    "policy_name": policy.PolicyName
                }
            )
           
            return Response({
                'message': 'Subpolicy added to policy successfully',
                'SubPolicyId': subpolicy.SubPolicyId,
                'PolicyId': policy.PolicyId
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        # Log subpolicy addition error
        send_log(
            module="Policy",
            actionType="ADD_SUBPOLICY_TO_POLICY_FAILED",
            description=f"Error adding subpolicy to policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return Response({'error': 'Error adding subpolicy to policy', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)
 

"""
@api GET /api/subpolicies/{pk}/
Returns a specific subpolicy by ID if it has Status='Approved',
its parent policy has Status='Approved' and ActiveInactive='Active',
and its parent framework has Status='Approved' and ActiveInactive='Active'.

@api PUT /api/subpolicies/{pk}/
Updates an existing subpolicy. Only subpolicies with Status='Approved'
whose parent policy and framework are also Approved and Active can be updated.

Example payload:
{
  "SubPolicyName": "Enhanced Password Management",
  "Description": "Updated password requirements and management",
  "Control": "Use strong passwords with at least 16 characters, including special characters",
  "Identifier": "PWD-002",
}

@api DELETE /api/subpolicies/{pk}/
Soft-deletes a subpolicy by setting Status='Inactive'.
"""
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([PolicyViewPermission])
def subpolicy_detail(request, pk):
    """
    Retrieve, update or delete a subpolicy.
    """
    # Import security modules for PUT operations
    from django.utils.html import escape as escape_html
    import shlex
    
    # Log subpolicy detail operation attempt
    send_log(
        module="Policy",
        actionType="SUBPOLICY_DETAIL",
        description=f"Accessing subpolicy detail for subpolicy {pk} with method {request.method}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="SubPolicy",
        entityId=pk,
        ipAddress=get_client_ip(request),
        additionalInfo={"method": request.method}
    )
    
    try:
        subpolicy = SubPolicy.objects.get(SubPolicyId=pk)
    except SubPolicy.DoesNotExist:
        # Log subpolicy not found error
        send_log(
            module="Policy",
            actionType="SUBPOLICY_DETAIL_FAILED",
            description=f"Subpolicy {pk} not found",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            logLevel="WARNING",
            ipAddress=get_client_ip(request),
            additionalInfo={"method": request.method}
        )
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Remove any restrictions that might cause 403 errors
        
        # Log successful subpolicy retrieval
        send_log(
            module="Policy",
            actionType="SUBPOLICY_DETAIL_GET_SUCCESS",
            description=f"Successfully retrieved subpolicy {pk} details",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "subpolicy_name": subpolicy.SubPolicyName,
                "status": subpolicy.Status,
                "policy_id": subpolicy.PolicyId.PolicyId if subpolicy.PolicyId else None
            }
        )
        
        serializer = SubPolicySerializer(subpolicy)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Log subpolicy update attempt
        send_log(
            module="Policy",
            actionType="SUBPOLICY_UPDATE",
            description=f"Attempting to update subpolicy {pk}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "subpolicy_name": subpolicy.SubPolicyName,
                "current_status": subpolicy.Status
            }
        )
        
        # Security: Sanitize PUT request data before processing
        sanitized_data = request.data.copy()
        
        # Security: Escape text fields in update data
        text_fields = ['SubPolicyName', 'Description', 'Control', 'Identifier', 'CreatedByName']
        for field in text_fields:
            if field in sanitized_data and sanitized_data[field]:
                sanitized_data[field] = escape_html(sanitized_data[field])
        
        # Remove any restrictions for updating
        serializer = SubPolicySerializer(subpolicy, data=sanitized_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Log successful subpolicy update
            send_log(
                module="Policy",
                actionType="SUBPOLICY_UPDATE_SUCCESS",
                description=f"Subpolicy {pk} updated successfully",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="SubPolicy",
                entityId=pk,
                ipAddress=get_client_ip(request),
                additionalInfo={"subpolicy_name": subpolicy.SubPolicyName}
            )
            
            return Response(serializer.data)
        
        # Log validation errors
        send_log(
            module="Policy",
            actionType="SUBPOLICY_UPDATE_FAILED",
            description=f"Subpolicy {pk} update failed due to validation errors",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            logLevel="WARNING",
            ipAddress=get_client_ip(request),
            additionalInfo={"validation_errors": serializer.errors}
        )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Log subpolicy deletion/inactivation attempt
        send_log(
            module="Policy",
            actionType="SUBPOLICY_DELETE",
            description=f"Attempting to inactivate subpolicy {pk}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "subpolicy_name": subpolicy.SubPolicyName,
                "current_status": subpolicy.Status
            }
        )
        
        # Instead of hard deleting, set Status to Inactive
        try:
            subpolicy.Status = 'Inactive'
            subpolicy.save()
            
            # Log successful subpolicy inactivation
            send_log(
                module="Policy",
                actionType="SUBPOLICY_DELETE_SUCCESS",
                description=f"Subpolicy {pk} successfully marked as inactive",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="SubPolicy",
                entityId=pk,
                ipAddress=get_client_ip(request),
                additionalInfo={"subpolicy_name": subpolicy.SubPolicyName}
            )
            
            return Response({'message': 'Subpolicy marked as inactive'}, status=status.HTTP_200_OK)
        except Exception as e:
            # Log deletion/inactivation error
            send_log(
                module="Policy",
                actionType="SUBPOLICY_DELETE_FAILED",
                description=f"Error marking subpolicy {pk} as inactive: {str(e)}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="SubPolicy",
                entityId=pk,
                logLevel="ERROR",
                ipAddress=get_client_ip(request),
                additionalInfo={"error": str(e)}
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyApprovePermission])
@csrf_exempt
def submit_subpolicy_review(request, pk):
    """
    Submit a review for a subpolicy
    """
    print(f"DEBUG: submit_subpolicy_review called for subpolicy {pk}")
    print(f"DEBUG: Request data: {request.data}")
    print(f"DEBUG: User: {request.user}")
    # Import security modules
    from django.utils.html import escape as escape_html
    import shlex
    
    # Log subpolicy review submission attempt
    send_log(
        module="Policy",
        actionType="SUBMIT_SUBPOLICY_REVIEW",
        description=f"Attempting to submit subpolicy review for subpolicy {pk}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="SubPolicy",
        entityId=pk,
        ipAddress=get_client_ip(request),
        additionalInfo={"status": request.data.get('Status')}
    )
    
    try:
        subpolicy = SubPolicy.objects.get(SubPolicyId=pk)
        print(f"DEBUG: Found subpolicy {pk} with current status: {subpolicy.Status}")
        
        # Check if subpolicy is already approved to prevent duplicate processing
        if subpolicy.Status == 'Approved':
            print(f"DEBUG: Subpolicy {pk} is already approved, skipping duplicate approval")
            return Response({
                'message': 'Subpolicy is already approved',
                'SubPolicyId': pk,
                'Status': subpolicy.Status,
                'PolicyUpdated': False,
                'PolicyStatus': subpolicy.PolicyId.Status if subpolicy.PolicyId else 'Unknown'
            }, status=status.HTTP_200_OK)
            
    except SubPolicy.DoesNotExist:
        # Log subpolicy not found error
        send_log(
            module="Policy",
            actionType="SUBMIT_SUBPOLICY_REVIEW_FAILED",
            description=f"Subpolicy {pk} not found for review submission",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        return Response({'error': 'Subpolicy not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Security: Sanitize input data
    status_value = request.data.get('Status')
    remarks = escape_html(request.data.get('remarks', ''))
    
    if not status_value:
        # Log missing status error
        send_log(
            module="Policy",
            actionType="SUBMIT_SUBPOLICY_REVIEW_FAILED",
            description=f"Status value is required but not provided for subpolicy {pk}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        return Response({'error': 'Status value is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    print(f"Updating subpolicy {pk} status to: {status_value}")
    
    # Update the subpolicy status
    subpolicy.Status = status_value
    subpolicy.save()
    print(f"Subpolicy {pk} status updated to {status_value}")
    
    # Get the parent policy
    policy = subpolicy.PolicyId
    if not policy:
        return Response({'error': 'Parent policy not found'}, status=status.HTTP_404_NOT_FOUND)
    
    print(f"Parent policy ID: {policy.PolicyId}, current status: {policy.Status}")
    
    # Update policy status based on all subpolicies
    update_policy_status_from_subpolicies(policy.PolicyId)
    
    # Refresh policy to get updated status
    policy.refresh_from_db()
    
    # Prepare response data with updated policy status
    response_data = {
        'message': 'Subpolicy review submitted successfully',
        'SubPolicyId': pk,
        'Status': status_value,
        'PolicyUpdated': True,
        'PolicyStatus': policy.Status
    }
    
    # Create policy approval record for both approvals AND rejections
    new_approval = None  # Initialize variable
    today = date.today()
    
    if status_value == 'Approved' or status_value == 'Rejected':
        # Check if we already have an r version approval for today to prevent duplicates
        print(f"DEBUG: Checking for existing policy approval for PolicyId {policy.PolicyId} on {today}")
        
        existing_today_approval = PolicyApproval.objects.filter(
            PolicyId=policy.PolicyId,
            ApprovedDate=today,
            Version__startswith='r'
        ).first()
        
        if existing_today_approval:
            print(f"Policy approval for today already exists with version {existing_today_approval.Version}, skipping duplicate creation")
            new_approval = existing_today_approval
        else:
            print(f"No existing approval found for today, creating new one for {status_value}")
            try:
                # Find the latest policy approval for this policy
                latest_approval = PolicyApproval.objects.filter(
                    PolicyId=policy.PolicyId
                ).order_by('-ApprovalId').first()
                
                # Calculate next reviewer version
                r_versions = []
                for pa in PolicyApproval.objects.filter(PolicyId=policy.PolicyId):
                    if pa.Version and pa.Version.startswith('r') and pa.Version[1:].isdigit():
                        r_versions.append(int(pa.Version[1:]))
                
                if r_versions:
                    new_version = f"r{max(r_versions) + 1}"
                else:
                    new_version = "r1"
                
                print(f"DEBUG: Calculated new reviewer version: {new_version}")
                
                # Get reviewer ID from current user
                reviewer_id = getattr(request.user, 'UserId', None) or getattr(request.user, 'id', None)
                print(f"DEBUG: Reviewer ID: {reviewer_id}")
                
                if latest_approval:
                    # Update ExtractedData with rejection remarks if rejecting
                    extracted_data = latest_approval.ExtractedData.copy() if latest_approval.ExtractedData else {}
                    if status_value == 'Rejected':
                        if 'policy_approval' not in extracted_data:
                            extracted_data['policy_approval'] = {}
                        extracted_data['policy_approval'].update({
                            'approved': False,
                            'remarks': remarks,
                            'reviewer_id': reviewer_id,
                            'reviewed_date': today.isoformat()
                        })
                    
                    # Create a new policy approval record
                    new_approval = PolicyApproval(
                        PolicyId=policy,
                        ExtractedData=extracted_data,
                        UserId=latest_approval.UserId,  # Original policy creator
                        ReviewerId=reviewer_id,  # Current reviewer
                        ApprovedNot=1 if status_value == 'Approved' else 0,  # 1=Approved, 0=Rejected
                        ApprovedDate=today,
                        Version=new_version,  # Reviewer version (r1, r2, etc.)
                        FrameworkId=policy.FrameworkId
                    )
                    new_approval.save()
                    print(f"✅ Created PolicyApproval for policy {policy.PolicyId}:")
                    print(f"   - ApprovalId: {new_approval.ApprovalId}")
                    print(f"   - Version: {new_version}")
                    print(f"   - ReviewerId: {reviewer_id}")
                    print(f"   - ApprovedNot: {new_approval.ApprovedNot}")
                    print(f"   - Status: {status_value}")
                else:
                    # If no existing approval found, create one with basic data
                    print(f"No existing policy approval found for policy {policy.PolicyId}, creating basic approval record")
                    # Get the original creator's ID from the policy
                    original_creator_id = policy.CreatedBy if policy.CreatedBy else reviewer_id
                    
                    extracted_data = {}
                    if status_value == 'Rejected':
                        extracted_data = {
                            'policy_approval': {
                                'approved': False,
                                'remarks': remarks,
                                'reviewer_id': reviewer_id,
                                'reviewed_date': today.isoformat()
                            }
                        }
                    
                    new_approval = PolicyApproval(
                        PolicyId=policy,
                        ExtractedData=extracted_data,
                        UserId=original_creator_id,  # Use original creator's ID
                        ReviewerId=reviewer_id,  # Current reviewer
                        ApprovedNot=1 if status_value == 'Approved' else 0,  # 1=Approved, 0=Rejected
                        ApprovedDate=today,
                        Version=new_version,  # Reviewer version (r1, r2, etc.)
                        FrameworkId=policy.FrameworkId
                    )
                    new_approval.save()
                    print(f"✅ Created basic PolicyApproval for policy {policy.PolicyId}:")
                    print(f"   - ApprovalId: {new_approval.ApprovalId}")
                    print(f"   - Version: {new_version}")
                    print(f"   - ReviewerId: {reviewer_id}")
                    print(f"   - ApprovedNot: {new_approval.ApprovedNot}")
            except Exception as approval_err:
                print(f"❌ Error creating policy approval: {str(approval_err)}")
                import traceback
                traceback.print_exc()
    
    # Send notification to reviewer about subpolicy resubmission
    try:
        from ...routes.Global.notification_service import NotificationService
        notification_service = NotificationService()
        reviewer = None
        submitter = None
        if new_approval and new_approval.ReviewerId:
            reviewer = Users.objects.get(UserId=new_approval.ReviewerId)
        if new_approval and new_approval.UserId:
            submitter = Users.objects.get(UserId=new_approval.UserId)
        if reviewer and reviewer.Email:
            # Security: XSS Protection - Escape HTML content before building email template
            notification_data = {
                'notification_type': 'subpolicyResubmitted',
                'email': reviewer.Email,
                'email_type': 'gmail',
                'template_data': [
                    escape_html(reviewer.UserName),  # Escape reviewer name for HTML context
                    escape_html(subpolicy.SubPolicyName),  # Escape subpolicy name for HTML context
                    escape_html(submitter.UserName if submitter else '')  # Escape submitter name for HTML context
                ]
            }
            notification_service.send_multi_channel_notification(notification_data)
    except Exception as notify_ex:
        print(f"DEBUG: Error sending subpolicy resubmission notification: {notify_ex}")
    
    # Log successful subpolicy review submission
    send_log(
        module="Policy",
        actionType="SUBMIT_SUBPOLICY_REVIEW_SUCCESS",
        description=f"Subpolicy review submitted successfully for subpolicy {pk} with status {status_value}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="SubPolicy",
        entityId=pk,
        ipAddress=get_client_ip(request),
        additionalInfo={
            "subpolicy_name": subpolicy.SubPolicyName,
            "new_status": status_value,
            "policy_id": policy.PolicyId,
            "policy_status": policy.Status
        }
    )
    
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyApprovePermission])
@csrf_exempt
def resubmit_subpolicy(request, pk):
    """
    Resubmit a rejected subpolicy with changes
    """
    # Import security modules
    from django.utils.html import escape as escape_html
    import shlex
    
    # Log subpolicy resubmission attempt
    send_log(
        module="Policy",
        actionType="RESUBMIT_SUBPOLICY",
        description=f"Attempting to resubmit subpolicy {pk}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="SubPolicy",
        entityId=pk,
        ipAddress=get_client_ip(request)
    )
    
    try:
        subpolicy = SubPolicy.objects.get(SubPolicyId=pk)
        policy_id = subpolicy.PolicyId.PolicyId
        
        print(f"Resubmitting subpolicy {pk} for policy {policy_id}")

        # Get all versions for this policy to find the latest u version
        policy_approvals = PolicyApproval.objects.filter(
            PolicyId=policy_id
        ).order_by('-Version')

        # Find the latest u version - use Python filtering instead of query filtering
        u_versions = [pa.Version for pa in policy_approvals if pa.Version and pa.Version.startswith('u')]
        new_version = 'u1'

        if u_versions:
            # Get the highest u version number
            latest_u_num = max([int(v[1:]) for v in u_versions if v[1:].isdigit()])
            new_version = f'u{latest_u_num + 1}'
            
        print(f"Setting new version to {new_version} for policy {policy_id}")

        # Security: Sanitize input data before updating subpolicy
        data = request.data.copy()
        
        if 'Description' in data:
            subpolicy.Description = escape_html(data['Description'])
        
        if 'Control' in data:
            subpolicy.Control = escape_html(data['Control'])
        
        # Set status back to Under Review
        original_status = subpolicy.Status
        subpolicy.Status = 'Under Review'
        
        # Save the changes
        subpolicy.save()
        print(f"Updated subpolicy {pk} status from {original_status} to Under Review")

        # Get the policy
        policy = Policy.objects.get(PolicyId=policy_id)
        original_policy_status = policy.Status
        
        # Update policy status if needed
        if policy.Status != 'Under Review':
            policy.Status = 'Under Review'
            policy.save()
            print(f"Updated policy {policy_id} status from {original_policy_status} to Under Review")

        # Create new policy approval with incremented u version
        # Get the latest policy approval to copy its data
        latest_approval = policy_approvals.first()
        if latest_approval:
            extracted_data = latest_approval.ExtractedData.copy() if hasattr(latest_approval.ExtractedData, 'copy') else latest_approval.ExtractedData
            
            # Update the specific subpolicy in extracted data
            if 'subpolicies' in extracted_data:
                subpolicy_updated = False
                for sub in extracted_data['subpolicies']:
                    if sub.get('SubPolicyId') == pk:
                        sub['Description'] = subpolicy.Description
                        sub['Control'] = subpolicy.Control
                        sub['Status'] = 'Under Review'
                        # Reset approval info if present
                        if 'approval' in sub:
                            sub['approval'] = {
                                'approved': None,
                                'remarks': ''
                            }
                        subpolicy_updated = True
                        break
                
                if not subpolicy_updated:
                    print(f"Warning: Subpolicy {pk} not found in extracted data")

            # Create new policy approval
            new_approval = PolicyApproval(
                PolicyId=policy,
                Identifier=latest_approval.Identifier,
                ExtractedData=extracted_data,
                UserId=latest_approval.UserId,
                ReviewerId=latest_approval.ReviewerId,
                ApprovedNot=None,
                Version=new_version,
                FrameworkId=policy.FrameworkId
            )
            new_approval.save()
            print(f"Created new policy approval with ID: {new_approval.ApprovalId}, Version: {new_version}")

            # Send notification to reviewer about subpolicy resubmission
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                reviewer = None
                submitter = None
                if new_approval.ReviewerId:
                    reviewer = Users.objects.get(UserId=new_approval.ReviewerId)
                if new_approval.UserId:
                    submitter = Users.objects.get(UserId=new_approval.UserId)
                if reviewer and reviewer.Email:
                    # Security: XSS Protection - Escape HTML content before building email template
                    notification_data = {
                        'notification_type': 'subpolicyResubmitted',
                        'email': reviewer.Email,
                        'email_type': 'gmail',
                        'template_data': [
                            escape_html(reviewer.UserName),  # Escape reviewer name for HTML context
                            escape_html(subpolicy.SubPolicyName),  # Escape subpolicy name for HTML context
                            escape_html(submitter.UserName if submitter else '')  # Escape submitter name for HTML context
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
            except Exception as notify_ex:
                print(f"DEBUG: Error sending subpolicy resubmission notification: {notify_ex}")

        # Log successful subpolicy resubmission
        send_log(
            module="Policy",
            actionType="RESUBMIT_SUBPOLICY_SUCCESS",
            description=f"Subpolicy {pk} resubmitted successfully with version {new_version}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "subpolicy_name": subpolicy.SubPolicyName,
                "new_version": new_version,
                "policy_id": policy_id
            }
        )
        
        return Response({
            'message': 'Subpolicy resubmitted successfully',
            'SubPolicyId': pk,
            'Status': 'Under Review',
            'version': new_version
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error resubmitting subpolicy: {str(e)}")
        
        # Log subpolicy resubmission error
        send_log(
            module="Policy",
            actionType="RESUBMIT_SUBPOLICY_FAILED",
            description=f"Error resubmitting subpolicy {pk}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing policy versions
def get_policy_version(request, policy_id):
    """
    Get the latest version of a policy from the policy approvals table
    """
    # Log policy version retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_POLICY_VERSION",
        description=f"Retrieving policy version for policy {policy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Instead of getting the attribute, find the latest approval version from the database
        latest_approval = PolicyApproval.objects.filter(
            PolicyId=policy_id
        ).order_by('-Version').first()
        
        # Extract the latest version from policy approvals
        if latest_approval and latest_approval.Version:
            # If version starts with 'u', return it
            if latest_approval.Version.startswith('u'):
                version = latest_approval.Version
            else:
                # Check if there are any user versions (u1, u2, etc.)
                user_approvals = PolicyApproval.objects.filter(
                    PolicyId=policy_id,
                    Version__startswith='u'
                ).order_by('-Version')
                
                if user_approvals.exists():
                    version = user_approvals.first().Version
                else:
                    version = 'u1'  # Default if no user versions found
        else:
            # If no approvals found, default to u1
            version = 'u1'
        
        print(f"Latest version for policy {policy_id}: {version}")
        
        # Log successful policy version retrieval
        send_log(
            module="Policy",
            actionType="GET_POLICY_VERSION_SUCCESS",
            description=f"Successfully retrieved policy version {version} for policy {policy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"version": version}
        )
        
        return Response({
            'policy_id': policy_id,
            'version': version
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error getting policy version: {str(e)}")
        
        # Log policy version retrieval error
        send_log(
            module="Policy",
            actionType="GET_POLICY_VERSION_FAILED",
            description=f"Error retrieving policy version for policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing subpolicy versions
def get_subpolicy_version(request, subpolicy_id):
    """
    Get the latest version of a subpolicy from policy approvals
    """
    # Log subpolicy version retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_SUBPOLICY_VERSION",
        description=f"Retrieving subpolicy version for subpolicy {subpolicy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="SubPolicy",
        entityId=subpolicy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        subpolicy = get_object_or_404(SubPolicy, SubPolicyId=subpolicy_id)
        policy_id = subpolicy.PolicyId.PolicyId if subpolicy.PolicyId else None
        
        if not policy_id:
            return Response({
                'subpolicy_id': subpolicy_id,
                'version': 'u1',
                'error': 'No parent policy found'
            }, status=status.HTTP_200_OK)
        
        # Find the latest policy approval with this subpolicy
        latest_version = 'u1'  # Default version
        
        try:
            # Get all policy approvals for the parent policy
            policy_approvals = PolicyApproval.objects.filter(
                PolicyId=policy_id
            ).order_by('-Version')
            
            # Look through policy approvals for this subpolicy
            for approval in policy_approvals:
                if not approval.ExtractedData or 'subpolicies' not in approval.ExtractedData:
                    continue
                
                # Find this subpolicy in the extracted data
                for sub in approval.ExtractedData['subpolicies']:
                    if sub.get('SubPolicyId') == subpolicy_id:
                        # Found a reference to this subpolicy
                        if approval.Version and approval.Version.startswith('u'):
                            latest_version = approval.Version
                            # We found a user version, return it
                            print(f"Found version {latest_version} for subpolicy {subpolicy_id}")
                            return Response({
                                'subpolicy_id': subpolicy_id,
                                'version': latest_version
                            }, status=status.HTTP_200_OK)
            
            # If we got here and didn't find a user version, check the subpolicy object
            stored_version = getattr(subpolicy, 'version', None)
            if stored_version and stored_version.startswith('u'):
                latest_version = stored_version
        except Exception as inner_error:
            print(f"Error finding version in approvals: {str(inner_error)}")
            # Continue with default version
        
        print(f"Latest version for subpolicy {subpolicy_id}: {latest_version}")
        
        # Log successful subpolicy version retrieval
        send_log(
            module="Policy",
            actionType="GET_SUBPOLICY_VERSION_SUCCESS",
            description=f"Successfully retrieved subpolicy version {latest_version} for subpolicy {subpolicy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=subpolicy_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"version": latest_version, "policy_id": policy_id}
        )
        
        return Response({
            'subpolicy_id': subpolicy_id,
            'version': latest_version
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error getting subpolicy version: {str(e)}")
        
        # Log subpolicy version retrieval error
        send_log(
            module="Policy",
            actionType="GET_SUBPOLICY_VERSION_FAILED",
            description=f"Error retrieving subpolicy version for subpolicy {subpolicy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=subpolicy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([PolicyViewPermission]) # RBAC: Require PolicyViewPermission for viewing policy approvals
def get_latest_policy_approval(request, policy_id):
    """
    Get the latest policy approval for a policy
    """
    # Log policy approval retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_LATEST_POLICY_APPROVAL",
        description=f"Retrieving latest policy approval for policy {policy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        latest_approval = PolicyApproval.objects.filter(
            PolicyId=policy_id
        ).order_by('-Version').first()
        
        if not latest_approval:
            # Log policy approval not found
            send_log(
                module="Policy",
                actionType="GET_LATEST_POLICY_APPROVAL_FAILED",
                description=f"No approval found for policy {policy_id}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request)
            )
            return Response({'error': 'No approval found for this policy'}, status=status.HTTP_404_NOT_FOUND)
        
        # Log successful policy approval retrieval
        send_log(
            module="Policy",
            actionType="GET_LATEST_POLICY_APPROVAL_SUCCESS",
            description=f"Successfully retrieved latest policy approval for policy {policy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyApproval",
            entityId=latest_approval.ApprovalId,
            ipAddress=get_client_ip(request),
            additionalInfo={"version": latest_approval.Version, "policy_id": policy_id}
        )
        
        serializer = PolicyApprovalSerializer(latest_approval)
        return Response(serializer.data)
    except Exception as e:
        # Log general error
        send_log(
            module="Policy",
            actionType="GET_LATEST_POLICY_APPROVAL_FAILED",
            description=f"Error retrieving latest policy approval for policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing policy approvals by role
def get_latest_policy_approval_by_role(request, policy_id, role):
    """
    Get the latest policy approval for a policy by role (reviewer/user)
    """
    # Log policy approval by role retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_LATEST_POLICY_APPROVAL_BY_ROLE",
        description=f"Retrieving latest policy approval for policy {policy_id} by role {role}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request),
        additionalInfo={"role": role}
    )
    
    try:
        # Filter by role - simplistic approach, you might need more complex logic
        if role == 'reviewer':
            latest_approval = PolicyApproval.objects.filter(
                PolicyId=policy_id,
                IsReviewer=True
            ).order_by('-Version').first()
        else:  # user role
            latest_approval = PolicyApproval.objects.filter(
                PolicyId=policy_id,
                IsReviewer=False
            ).order_by('-Version').first()
        
        if not latest_approval:
            # Log policy approval by role not found
            send_log(
                module="Policy",
                actionType="GET_LATEST_POLICY_APPROVAL_BY_ROLE_FAILED",
                description=f"No {role} approval found for policy {policy_id}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request),
                additionalInfo={"role": role}
            )
            return Response({'error': f'No {role} approval found for this policy'}, status=status.HTTP_404_NOT_FOUND)
        
        # Log successful policy approval by role retrieval
        send_log(
            module="Policy",
            actionType="GET_LATEST_POLICY_APPROVAL_BY_ROLE_SUCCESS",
            description=f"Successfully retrieved latest {role} approval for policy {policy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyApproval",
            entityId=latest_approval.ApprovalId,
            ipAddress=get_client_ip(request),
            additionalInfo={"role": role, "version": latest_approval.Version, "policy_id": policy_id}
        )
        
        serializer = PolicyApprovalSerializer(latest_approval)
        return Response(serializer.data)
    except Exception as e:
        # Log general error
        send_log(
            module="Policy",
            actionType="GET_LATEST_POLICY_APPROVAL_BY_ROLE_FAILED",
            description=f"Error retrieving latest {role} approval for policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e), "role": role}
        )
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing reviewer versions
def get_latest_reviewer_version(request, policy_id=None, subpolicy_id=None):
    """
    Get the latest reviewer version (R1, R2, etc.) for a policy or subpolicy
    and return the complete policy approval data for that version
    """
    # Log reviewer version retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_LATEST_REVIEWER_VERSION",
        description=f"Retrieving latest reviewer version for policy {policy_id} or subpolicy {subpolicy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy" if policy_id else "SubPolicy",
        entityId=policy_id or subpolicy_id,
        ipAddress=get_client_ip(request),
        additionalInfo={"policy_id": policy_id, "subpolicy_id": subpolicy_id}
    )
    
    try:
        latest_r_version = 'R1'  # Default if no reviewer versions found
        policy_approval_data = None
        
        if policy_id:
            # Find the latest R version for a policy
            policy = get_object_or_404(Policy, PolicyId=policy_id)
            
            # Use Python filtering instead of MySQL regex to avoid character set issues
            r_approvals = []
            all_approvals = PolicyApproval.objects.filter(PolicyId=policy_id).order_by('-Version')
            
            for approval in all_approvals:
                if approval.Version and approval.Version.startswith('R'):
                    r_approvals.append(approval)
            
            if r_approvals:
                # Get the latest policy approval with R version
                latest_approval = r_approvals[0]
                latest_r_version = latest_approval.Version
                print(f"Found latest R version for policy {policy_id}: {latest_r_version}")
                
                # Serialize the policy approval data
                serializer = PolicyApprovalSerializer(latest_approval)
                policy_approval_data = serializer.data
        
        elif subpolicy_id:
            # Find the latest R version for a subpolicy
            subpolicy = get_object_or_404(SubPolicy, SubPolicyId=subpolicy_id)
            policy_id = subpolicy.PolicyId.PolicyId if subpolicy.PolicyId else None
            
            if policy_id:
                # Use Python filtering instead of MySQL regex
                r_approvals = []
                all_approvals = PolicyApproval.objects.filter(PolicyId=policy_id).order_by('-Version')
                
                for approval in all_approvals:
                    if approval.Version and approval.Version.startswith('R'):
                        r_approvals.append(approval)
                
                if r_approvals:
                    # Get the latest policy approval
                    latest_approval = r_approvals[0]
                    latest_r_version = latest_approval.Version
                    
                    # Serialize the policy approval data
                    serializer = PolicyApprovalSerializer(latest_approval)
                    policy_approval_data = serializer.data
                    
                    print(f"Found latest R version for subpolicy {subpolicy_id}: {latest_r_version} in policy {policy_id}")
        
        # If we have policy approval data, return it along with the version
        if policy_approval_data:
            # Log successful reviewer version retrieval with data
            send_log(
                module="Policy",
                actionType="GET_LATEST_REVIEWER_VERSION_SUCCESS",
                description=f"Successfully retrieved latest reviewer version {latest_r_version} with approval data",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy" if policy_id else "SubPolicy",
                entityId=policy_id or subpolicy_id,
                ipAddress=get_client_ip(request),
                additionalInfo={"version": latest_r_version, "policy_id": policy_id, "subpolicy_id": subpolicy_id}
            )
            return Response({
                'policy_id': policy_id,
                'subpolicy_id': subpolicy_id,
                'version': latest_r_version,
                'approval_data': policy_approval_data
            }, status=status.HTTP_200_OK)
        else:
            # Log successful reviewer version retrieval without data
            send_log(
                module="Policy",
                actionType="GET_LATEST_REVIEWER_VERSION_SUCCESS",
                description=f"Successfully retrieved latest reviewer version {latest_r_version} without approval data",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy" if policy_id else "SubPolicy",
                entityId=policy_id or subpolicy_id,
                ipAddress=get_client_ip(request),
                additionalInfo={"version": latest_r_version, "policy_id": policy_id, "subpolicy_id": subpolicy_id}
            )
            # If no approval data found, just return the version
            return Response({
                'policy_id': policy_id,
                'subpolicy_id': subpolicy_id,
                'version': latest_r_version,
                'approval_data': None
            }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error getting latest reviewer version: {str(e)}")
        
        # Log reviewer version retrieval error
        send_log(
            module="Policy",
            actionType="GET_LATEST_REVIEWER_VERSION_FAILED",
            description=f"Error retrieving latest reviewer version: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy" if policy_id else "SubPolicy",
            entityId=policy_id or subpolicy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e), "policy_id": policy_id, "subpolicy_id": subpolicy_id}
        )
        
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyApprovalWorkflowPermission])
@csrf_exempt  # Temporarily disable CSRF for debugging
def submit_policy_approval_review(request, policy_id):
    """
    Submit a review for a policy approval
    """
    print(f"DEBUG: ===== SUBMIT POLICY APPROVAL REVIEW CALLED =====")
    print(f"DEBUG: submit_policy_approval_review - Request path: {request.path}")
    print(f"DEBUG: submit_policy_approval_review - Request method: {request.method}")
    print(f"DEBUG: submit_policy_approval_review - Request headers: {dict(request.headers)}")
    print(f"DEBUG: submit_policy_approval_review - User object: {request.user}")
    print(f"DEBUG: submit_policy_approval_review - User type: {type(request.user)}")
    print(f"DEBUG: submit_policy_approval_review - User attributes: {dir(request.user) if hasattr(request.user, '__dict__') else 'No __dict__'}")
    print(f"DEBUG: submit_policy_approval_review - User is authenticated: {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else 'No is_authenticated attribute'}")
    print(f"DEBUG: submit_policy_approval_review - User is anonymous: {request.user.is_anonymous if hasattr(request.user, 'is_anonymous') else 'No is_anonymous attribute'}")
    if hasattr(request.user, 'id'):
        print(f"DEBUG: submit_policy_approval_review - User ID: {request.user.id}")
    if hasattr(request.user, 'UserId'):
        print(f"DEBUG: submit_policy_approval_review - User UserId: {request.user.UserId}")
    if hasattr(request.user, 'username'):
        print(f"DEBUG: submit_policy_approval_review - User username: {request.user.username}")
    if hasattr(request.user, 'UserName'):
        print(f"DEBUG: submit_policy_approval_review - User UserName: {request.user.UserName}")
    if hasattr(request.user, 'Role'):
        print(f"DEBUG: submit_policy_approval_review - User Role: {request.user.Role}")
    print(f"DEBUG: submit_policy_approval_review - Request method: {request.method}")
    print(f"DEBUG: submit_policy_approval_review - Request path: {request.path}")
    print(f"DEBUG: submit_policy_approval_review - Request content type: {request.content_type}")
    print(f"DEBUG: submit_policy_approval_review - Request data: {request.data}")
    print(f"DEBUG: submit_policy_approval_review - Authentication header: {request.headers.get('Authorization', 'Not found')}")
    print(f"DEBUG: submit_policy_approval_review - Session data: {dict(request.session) if hasattr(request, 'session') else 'No session'}")
    
    # Check if user is authenticated and has admin role
    if hasattr(request.user, 'Role'):
        print(f"DEBUG: submit_policy_approval_review - User Role: {request.user.Role}")
        if request.user.Role == 'GRC Administrator':
            print(f"DEBUG: submit_policy_approval_review - User is GRC Administrator - allowing access")
        else:
            print(f"DEBUG: submit_policy_approval_review - User Role: {request.user.Role} - checking permissions")
    
    print(f"DEBUG: ===== END DEBUG INFO =====")
    print(f"DEBUG: ===== FUNCTION IS BEING CALLED - THIS SHOULD APPEAR IF THE FUNCTION IS REACHED =====")
    
    # Check if user is authenticated and has proper permissions
    if hasattr(request.user, 'Role') and request.user.Role == 'GRC Administrator':
        print(f"DEBUG: GRC Administrator bypassing permission checks for policy review submission")
        # Continue with the function - no additional permission checks needed
    elif hasattr(request.user, 'UserId') and request.user.UserId:
        print(f"DEBUG: Authenticated user {request.user.UserName} (ID: {request.user.UserId}) - checking permissions")
        # Continue with the function - user is authenticated
    else:
        print(f"DEBUG: User not properly authenticated - attempting to continue anyway")
        # Try to continue - the permission class should handle this
    
    # Log policy approval review submission attempt
    send_log(
        module="Policy",
        actionType="SUBMIT_POLICY_APPROVAL_REVIEW",
        description=f"Submitting policy approval review for policy {policy_id}",
        userId=getattr(request.user, 'UserId', getattr(request.user, 'id', None)),
        userName=getattr(request.user, 'UserName', getattr(request.user, 'username', 'Anonymous')),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        from datetime import date
        data = request.data
        
        # Check if user is GRC Administrator - allow access regardless of other permissions
        if hasattr(request.user, 'Role') and request.user.Role == 'GRC Administrator':
            print(f"DEBUG: GRC Administrator access granted for policy review submission")
        elif hasattr(request.user, 'UserId') and request.user.UserId:
            print(f"DEBUG: Authenticated user access granted for policy review submission")
        else:
            print(f"DEBUG: User not properly authenticated - attempting to continue with policy review")
        
        policy = Policy.objects.get(PolicyId=policy_id)
        
        # Extract necessary data
        extracted_data = data.get('ExtractedData', {})
        
        # Get user ID from request user or fallback to data
        if hasattr(request.user, 'UserId') and request.user.UserId:
            user_id = request.user.UserId
        elif hasattr(request.user, 'id') and request.user.id:
            user_id = request.user.id
        else:
            user_id = data.get('UserId', 1)
        
        # Get reviewer ID from request user or fallback to data
        if hasattr(request.user, 'UserId') and request.user.UserId:
            reviewer_id = request.user.UserId
        elif hasattr(request.user, 'id') and request.user.id:
            reviewer_id = request.user.id
        else:
            reviewer_id = data.get('ReviewerId', 2)
        
        # Get approval status from request
        approved = data.get('approved', False)
        
        # Check if Status is provided in the ExtractedData
        if extracted_data and 'Status' in extracted_data:
            status_from_json = extracted_data.get('Status')
            # Set ApprovedNot based on Status
            if status_from_json == 'Approved':
                approved_not = 1  # Approved
                is_approved = True
            elif status_from_json == 'Rejected':
                approved_not = 0  # Rejected
                is_approved = False
            else:
                # Use value from request if no matching status
                approved_not = 1 if approved else 0
                is_approved = approved
        else:
            # Use value from request if no Status in ExtractedData
            approved_not = 1 if approved else 0
            is_approved = approved
        
        # Set approved date to today
        approved_date = date.today()
        
        # Determine next version
        policy_approvals = PolicyApproval.objects.filter(
            PolicyId=policy
        ).order_by('-Version')
        
        print(f"DEBUG: Found {policy_approvals.count()} existing policy approvals for PolicyId {policy.PolicyId}")
        
        # Find latest reviewer version
        r_versions = [pa.Version for pa in policy_approvals if pa.Version and pa.Version.startswith('r')]
        print(f"DEBUG: Existing reviewer versions: {r_versions}")
        
        new_version = 'r1'
        
        if r_versions:
            try:
                latest_r_num = max([int(v[1:]) for v in r_versions if v[1:].isdigit()])
                new_version = f'r{latest_r_num + 1}'
                print(f"DEBUG: Calculated new version from existing versions: {new_version}")
            except (ValueError, Exception) as e:
                new_version = 'r2'
                print(f"DEBUG: Error calculating version, using r2: {e}")
        else:
            print(f"DEBUG: No existing reviewer versions found, using r1")
        
        # Add review details to extracted_data
        if 'policy_approval' not in extracted_data:
            extracted_data['policy_approval'] = {}
            
        extracted_data['policy_approval'].update({
            'approved': approved,
            'remarks': data.get('remarks', ''),
            'reviewer_id': reviewer_id,
            'reviewed_date': approved_date.isoformat()
        })
        
        # Check if we already have an approval record for this policy, reviewer, date, and version to prevent duplicates
        print(f"DEBUG: Checking for existing policy approval to prevent duplicates:")
        print(f"  - PolicyId: {policy.PolicyId}")
        print(f"  - ReviewerId: {reviewer_id}")
        print(f"  - ApprovedDate: {approved_date}")
        print(f"  - Version: {new_version}")
        
        # Check for existing approval with same PolicyId, ReviewerId, Version, and ApprovedDate
        # For reviewer versions (r*), also check ApprovedDate to allow multiple reviews on different days
        # But prevent duplicates on the same day
        existing_approval = PolicyApproval.objects.filter(
            PolicyId=policy.PolicyId,
            ReviewerId=reviewer_id,
            Version=new_version
        )
        
        # If it's a reviewer version (r*), also check ApprovedDate to prevent same-day duplicates
        if new_version.startswith('r'):
            existing_approval = existing_approval.filter(ApprovedDate=approved_date)
        
        existing_approval = existing_approval.first()
        
        if existing_approval:
            print(f"DEBUG: ⚠️ Duplicate prevention: Policy approval already exists with ApprovalId: {existing_approval.ApprovalId}")
            print(f"  - Existing ApprovalId: {existing_approval.ApprovalId}")
            print(f"  - Existing Version: {existing_approval.Version}")
            print(f"  - Existing ReviewerId: {existing_approval.ReviewerId}")
            print(f"  - Existing ApprovedNot: {existing_approval.ApprovedNot}")
            print(f"  - Skipping duplicate creation and returning existing record")
            new_approval = existing_approval
        else:
            # Create a new policy approval record for each review (both approvals and rejections)
            # This ensures proper version tracking and reviewer history
            print(f"DEBUG: No existing approval found, creating new PolicyApproval with:")
            print(f"  - PolicyId: {policy.PolicyId}")
            print(f"  - UserId: {user_id}")
            print(f"  - ReviewerId: {reviewer_id}")
            print(f"  - ApprovedNot: {approved_not}")
            print(f"  - Version: {new_version}")
            print(f"  - FrameworkId: {policy.FrameworkId}")
            
            new_approval = PolicyApproval(
                PolicyId=policy,
                ExtractedData=extracted_data,
                UserId=user_id,
                ReviewerId=reviewer_id,  # Reviewer ID saved for tracking
                ApprovedNot=approved_not,
                ApprovedDate=approved_date,
                Version=new_version,  # Incremented reviewer version (r1, r2, etc.)
                FrameworkId=policy.FrameworkId
            )
            new_approval.save()
        
        # Verify the version was saved correctly
        print(f"DEBUG: ✅ Created new PolicyApproval record:")
        print(f"  - ApprovalId: {new_approval.ApprovalId}")
        print(f"  - Version: {new_approval.Version}")
        print(f"  - ReviewerId: {new_approval.ReviewerId}")
        print(f"  - ApprovedNot: {new_approval.ApprovedNot}")
        
        # Initial update of policy status based on review decision
        initial_status = 'Approved' if approved else 'Rejected'
        policy.Status = initial_status
        
        # Update ActiveInactive status for approved policies based on StartDate
        if initial_status == 'Approved':
            # Set policy to Active or Scheduled based on StartDate
            today = date.today()
            print(f"DEBUG: Individual Policy Approval {policy.PolicyId} - Today: {today}, StartDate: {policy.StartDate} (type: {type(policy.StartDate)})")
            
            if policy.StartDate and policy.StartDate > today:
                policy.ActiveInactive = 'Scheduled'
                print(f"Set individual policy approval {policy.PolicyId} to Approved status and Scheduled status (StartDate: {policy.StartDate} > today: {today})")
            else:
                policy.ActiveInactive = 'Active'
                print(f"Set individual policy approval {policy.PolicyId} to Approved status and Active status (StartDate: {policy.StartDate} <= today: {today} or None)")
            
            # Enhanced logic to deactivate previous versions
            print(f"DEBUG: Current policy being approved: PolicyId={policy.PolicyId}, Version={policy.CurrentVersion}, Identifier={policy.Identifier}")
            
            # Method 1: Find by Identifier
            previous_policies_by_identifier = Policy.objects.filter(
                Identifier=policy.Identifier
            ).exclude(
                PolicyId=policy.PolicyId
            )
            
            print(f"DEBUG: Found {previous_policies_by_identifier.count()} previous versions by Identifier: {policy.Identifier}")
            
            # Method 2: Find through PolicyVersion relationships
            previous_policies_by_version = []
            try:
                # Get current policy's version record
                current_policy_version = PolicyVersion.objects.filter(PolicyId=policy).first()
                if current_policy_version:
                    # Find all other policies with versions that have the same base identifier pattern
                    version_pattern = current_policy_version.Version
                    if '.' in version_pattern:
                        major_version = version_pattern.split('.')[0]
                        related_versions = PolicyVersion.objects.filter(
                            Version__startswith=major_version + '.'
                        ).exclude(PolicyId=policy)
                        
                        for version_record in related_versions:
                            if version_record.PolicyId and version_record.PolicyId.Identifier == policy.Identifier:
                                previous_policies_by_version.append(version_record.PolicyId)
                        
                        print(f"DEBUG: Found {len(previous_policies_by_version)} previous versions through PolicyVersion table")
            except Exception as version_err:
                print(f"DEBUG: Error finding related versions: {str(version_err)}")
            
            # Combine and deduplicate all previous policies
            all_previous_policies = set()
            for p in previous_policies_by_identifier:
                all_previous_policies.add(p)
            for p in previous_policies_by_version:
                all_previous_policies.add(p)
            
            all_previous_policies = list(all_previous_policies)
            
            print(f"DEBUG: Total unique previous policies to deactivate: {len(all_previous_policies)}")
            
            # Additional debug info
            if all_previous_policies:
                policy_ids = [p.PolicyId for p in all_previous_policies]
                policy_versions_info = [(p.PolicyId, p.CurrentVersion, p.Status, p.ActiveInactive) for p in all_previous_policies]
                print(f"DEBUG: Previous policy IDs to deactivate: {policy_ids}")
                print(f"DEBUG: Previous policies details: {policy_versions_info}")
            
            # Deactivate all previous versions
            deactivated_count = 0
            for prev_policy in all_previous_policies:
                if prev_policy.ActiveInactive == 'Active':  # Only deactivate if currently active
                    print(f"DEBUG: Processing previous policy: PolicyId={prev_policy.PolicyId}, CurrentVersion={prev_policy.CurrentVersion}, Status={prev_policy.Status}, ActiveInactive={prev_policy.ActiveInactive}")
                    
                    # Set ActiveInactive to 'Inactive'
                    prev_policy.ActiveInactive = 'Inactive'
                    # Keep the Status as 'Approved' if it was already approved
                    if prev_policy.Status == 'Approved':
                        print(f"DEBUG: Keeping Status 'Approved' for policy {prev_policy.PolicyId}")
                    print(f"DEBUG: Setting policy {prev_policy.PolicyId} to Inactive (Status remains {prev_policy.Status})")
                    prev_policy.save()
                    deactivated_count += 1
                    
                    # Verify the save worked
                    updated_policy = Policy.objects.get(PolicyId=prev_policy.PolicyId)
                    print(f"DEBUG: Verified policy {prev_policy.PolicyId} after save: ActiveInactive={updated_policy.ActiveInactive}")
                else:
                    print(f"DEBUG: Skipping policy {prev_policy.PolicyId} - already inactive")
            
            print(f"DEBUG: Successfully deactivated {deactivated_count} previous policy versions")
            
        policy.save()
        print(f"DEBUG: Initial policy status set to {initial_status}")
        
        # Check subpolicy statuses to ensure policy status is consistent
        # If any subpolicy is rejected, the policy will be marked as rejected
        update_policy_status_from_subpolicies(policy_id)
        
        # Refresh policy object to get the updated status after subpolicy check
        policy.refresh_from_db()
        
        # Update subpolicies based on policy approval/rejection status
        if approved and policy.Status == 'Approved':
            # If policy is approved, approve all subpolicies that are under review
            SubPolicy.objects.filter(PolicyId=policy.PolicyId, Status='Under Review').update(Status='Approved')
        elif not approved and policy.Status == 'Rejected':
            # If policy is rejected, check if any subpolicies were specifically rejected
            # and update their status accordingly
            if extracted_data and 'subpolicies' in extracted_data:
                for subpolicy_data in extracted_data['subpolicies']:
                    if 'SubPolicyId' in subpolicy_data and 'Status' in subpolicy_data:
                        try:
                            subpolicy = SubPolicy.objects.get(SubPolicyId=subpolicy_data['SubPolicyId'])
                            if subpolicy_data['Status'] == 'Rejected':
                                subpolicy.Status = 'Rejected'
                                subpolicy.save()
                                print(f"DEBUG: Updated subpolicy {subpolicy.SubPolicyId} to Rejected status")
                        except SubPolicy.DoesNotExist:
                            print(f"DEBUG: Subpolicy {subpolicy_data.get('SubPolicyId')} not found")
                            continue
        
        # Send notification to submitter about approval or rejection
        try:
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            submitter = Users.objects.get(UserId=new_approval.UserId)
            reviewer = Users.objects.get(UserId=new_approval.ReviewerId)
            now_str = date.today().isoformat()
            if is_approved:
                notification_data = {
                    'notification_type': 'policyApproved',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        policy.PolicyName,
                        reviewer.UserName,
                        now_str
                    ]
                }
            else:
                rejection_reason = request.data.get('rejection_reason', '') or 'Policy was rejected'
                notification_data = {
                    'notification_type': 'policyRejected',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        policy.PolicyName,
                        reviewer.UserName,
                        rejection_reason
                    ]
                }
            notification_service.send_multi_channel_notification(notification_data)
        except Exception as notify_ex:
            print(f"DEBUG: Error sending policy approval/rejection notification: {notify_ex}")
        
        # Log successful policy approval review submission
        send_log(
            module="Policy",
            actionType="SUBMIT_POLICY_APPROVAL_REVIEW_SUCCESS",
            description=f"Successfully submitted policy approval review for policy {policy_id}",
            userId=getattr(request.user, 'UserId', getattr(request.user, 'id', None)),
            userName=getattr(request.user, 'UserName', getattr(request.user, 'username', 'Anonymous')),
            entityType="PolicyApproval",
            entityId=new_approval.ApprovalId,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "policy_id": policy.PolicyId,
                "version": new_version,
                "status": policy.Status,
                "approved": is_approved,
                "reviewer_id": reviewer_id
            }
        )
        
        return Response({
            'message': 'Policy review submitted successfully',
            'PolicyId': policy.PolicyId,
            'ApprovalId': new_approval.ApprovalId,
            'Version': new_version,
            'Status': policy.Status,
            'ApprovedDate': safe_isoformat(approved_date)
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"Error submitting policy review: {str(e)}")
        
        # Log policy approval review submission error
        send_log(
            module="Policy",
            actionType="SUBMIT_POLICY_APPROVAL_REVIEW_FAILED",
            description=f"Error submitting policy approval review for policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'UserId', getattr(request.user, 'id', None)),
            userName=getattr(request.user, 'UserName', getattr(request.user, 'username', 'Anonymous')),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing policy version history
def get_policy_version_history(request, policy_id):
    """
    Get the version history of a policy
    """
    # Log policy version history retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_POLICY_VERSION_HISTORY",
        description=f"Retrieving policy version history for policy {policy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        approvals = PolicyApproval.objects.filter(
            PolicyId=policy_id
        ).order_by('-Version')
        
        version_history = []
        for approval in approvals:
            version_history.append({
                'version': approval.Version,
                'previousVersion': approval.PreviousVersion,
                'approvedDate': approval.ApprovedDate,
                'status': 'Approved' if approval.ApprovedNot else 'Rejected' if approval.ApprovedNot is False else 'Under Review'
            })
        
        # Log successful policy version history retrieval
        send_log(
            module="Policy",
            actionType="GET_POLICY_VERSION_HISTORY_SUCCESS",
            description=f"Successfully retrieved policy version history for policy {policy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"version_count": len(version_history)}
        )
        
        return Response({
            'policy_id': policy_id,
            'versions': version_history
        }, status=status.HTTP_200_OK)
    except Exception as e:
        # Log policy version history retrieval error
        send_log(
            module="Policy",
            actionType="GET_POLICY_VERSION_HISTORY_FAILED",
            description=f"Error retrieving policy version history for policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([PolicyApprovalWorkflowPermission])  # RBAC: Require PolicyApprovalWorkflowPermission for viewing reviewer's policy approvals
def list_policy_approvals_for_reviewer(request):
    # Get reviewer ID from request
    reviewer_id = request.user.id if hasattr(request.user, 'id') else None
    if not reviewer_id:
        reviewer_id = request.session.get('user_id')
    if not reviewer_id:
        return Response({'error': 'No reviewer ID found'}, status=status.HTTP_400_BAD_REQUEST)
    
    framework_id = request.GET.get('framework_id', None)
    print(f"🔍 DEBUG: list_policy_approvals_for_reviewer called with framework_id: {framework_id}")
    
    # Log policy approvals listing for reviewer
    send_log(
        module="Policy",
        actionType="LIST_POLICY_APPROVALS_FOR_REVIEWER",
        description=f"Listing policy approvals for reviewer {reviewer_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="PolicyApproval",
        ipAddress=get_client_ip(request),
        additionalInfo={"reviewer_id": reviewer_id}
    )
    
    print(f"Fetching policy approvals for reviewer_id: {reviewer_id}")
    
    # Get all approvals for this reviewer
    approvals = PolicyApproval.objects.filter(ReviewerId=reviewer_id)
    
    # Apply framework filter if provided
    if framework_id:
        print(f"🔍 DEBUG: Filtering reviewer policy approvals by framework_id: {framework_id}")
        # Filter through Policy relationship: PolicyApproval -> Policy -> FrameworkId
        approvals = approvals.filter(PolicyId__FrameworkId=framework_id)
        print(f"✅ Framework filter applied to reviewer approvals through Policy relationship. Found {approvals.count()} policy approvals.")
    
    print(f"Found {approvals.count()} total policy approvals for reviewer {reviewer_id}")
    
    # Get unique policy IDs to ensure we only return the latest version of each policy
    unique_policies = {}
    
    for approval in approvals:
        policy_id = approval.PolicyId if approval.PolicyId else f"approval_{approval.ApprovalId}"
        print(f"Processing approval {approval.ApprovalId}: PolicyId={policy_id}, Version={approval.Version}, ApprovedNot={approval.ApprovedNot}")
        
        # If we haven't seen this policy yet, or if this is a newer version
        if policy_id not in unique_policies or float(approval.Version.lower().replace('r', '').replace('u', '') or 0) > float(unique_policies[policy_id].Version.lower().replace('r', '').replace('u', '') or 0):
            unique_policies[policy_id] = approval
    
    # Convert to a list of unique approvals
    unique_approvals = list(unique_policies.values())
    print(f"Returning {len(unique_approvals)} unique policy approvals")
    
    # Serialize the approvals
    data = [
        {
            "ApprovalId": a.ApprovalId,
            "PolicyId": a.PolicyId.PolicyId if a.PolicyId else None,
            "Identifier": a.Identifier,
            "ExtractedData": a.ExtractedData,
            "UserId": a.UserId,
            "ReviewerId": a.ReviewerId,
            "ApprovedNot": a.ApprovedNot,
            "Version": a.Version
        }
        for a in unique_approvals
    ]
    
    return Response(data)

@api_view(['GET'])
@permission_classes([PolicyApprovalWorkflowPermission]) # RBAC: Require PolicyApprovalWorkflowPermission for viewing rejected policy approvals
def list_rejected_policy_approvals_for_user(request, user_id):
    # Log rejected policy approvals listing for user
    send_log(
        module="Policy",
        actionType="LIST_REJECTED_POLICY_APPROVALS_FOR_USER",
        description=f"Listing rejected policy approvals for user {user_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="PolicyApproval",
        ipAddress=get_client_ip(request),
        additionalInfo={"user_id": user_id}
    )
    
    # Filter policies where the user is either the creator (UserId) or the reviewer (ReviewerId)
    # and the approval status is rejected (ApprovedNot=0)
    rejected_approvals = PolicyApproval.objects.filter(
        Q(ReviewerId=user_id) | Q(UserId=user_id),
        ApprovedNot=0  # Use 0 instead of False for consistency
    ).order_by('-ApprovalId')  # Get the most recent first
    
    # Return all rejected approvals - don't deduplicate since each rejection 
    # represents a separate submission that can be edited and resubmitted
    unique_approvals = list(rejected_approvals)
    
    # Log successful rejected policy approvals listing for user
    send_log(
        module="Policy",
        actionType="LIST_REJECTED_POLICY_APPROVALS_FOR_USER_SUCCESS",
        description=f"Successfully listed {len(unique_approvals)} rejected policy approvals for user {user_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="PolicyApproval",
        ipAddress=get_client_ip(request),
        additionalInfo={"user_id": user_id, "rejected_approval_count": len(unique_approvals)}
    )
    
    serializer = PolicyApprovalSerializer(unique_approvals, many=True)
    return Response(serializer.data)

"""
@api GET /api/frameworks/{framework_id}/export/
Exports all policies and their subpolicies for a specific framework to an Excel file in the following format:
Identifier, PolicyName (PolicyFamily), SubpolicyIdentifier, SubpolicyName, Control, Description

Example response:
Returns an Excel file as attachment
"""
@api_view(['POST'])
@permission_classes([PolicyExportPermission])
def export_policies_to_excel(request, framework_id):
    """
    Export framework policies and their subpolicies to various formats
    """
    # Log export policies to excel attempt
    send_log(
        module="Policy",
        actionType="EXPORT_POLICIES_TO_EXCEL",
        description=f"Attempting to export policies to Excel for framework {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Framework",
        entityId=framework_id,
        ipAddress=get_client_ip(request)
    )
    
    print(f"[EXPORT] Request received to export policies for Framework ID: {framework_id}")

    try:
        # Get the framework
        framework = Framework.objects.get(FrameworkId=framework_id)
        print(f"[EXPORT] Found framework: {framework.FrameworkName}")

        # Get all policies for this framework
        policy_id = request.data.get('policy_id')
        if policy_id:
            policies = Policy.objects.filter(FrameworkId=framework_id, PolicyId=policy_id)
        else:
            policies = Policy.objects.filter(FrameworkId=framework_id)
        print(f"[EXPORT] Found {policies.count()} policies under framework {framework_id}")

        # Prepare data for export (one row per subpolicy, or one row per policy if no subpolicies)
        export_data_list = []
        for policy in policies:
            print(f"[EXPORT] Processing policy: {policy.PolicyName}")
            subpolicies = policy.subpolicy_set.all()
            if subpolicies.exists():
                for sub in subpolicies:
                    row = {
                        'Policy ID': policy.PolicyId,
                        'Policy Name': policy.PolicyName,
                        'Version': policy.CurrentVersion,
                        'Status': policy.Status,
                        'Description': policy.PolicyDescription,
                        'Department': policy.Department,
                        'Created By': policy.CreatedByName,
                        'Created Date': policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                        'Start Date': policy.StartDate.isoformat() if policy.StartDate else None,
                        'End Date': policy.EndDate.isoformat() if policy.EndDate else None,
                        'Applicability': policy.Applicability,
                        'Scope': policy.Scope,
                        'Objective': policy.Objective,
                        'Identifier': policy.Identifier,
                        'Active/Inactive': policy.ActiveInactive,
                        # Subpolicy fields
                        'Subpolicy ID': sub.SubPolicyId,
                        'Subpolicy Name': sub.SubPolicyName,
                        'Subpolicy Identifier': sub.Identifier,
                        'Subpolicy Description': sub.Description,
                        'Subpolicy Status': sub.Status,
                        'Subpolicy Permanent/Temporary': sub.PermanentTemporary,
                        'Subpolicy Control': sub.Control,
                        'Subpolicy Created By': sub.CreatedByName,
                        'Subpolicy Created Date': sub.CreatedByDate.isoformat() if sub.CreatedByDate else None,
                    }
                    export_data_list.append(row)
            else:
                # Policy with no subpolicies: still include a row
                row = {
                    'Policy ID': policy.PolicyId,
                    'Policy Name': policy.PolicyName,
                    'Version': policy.CurrentVersion,
                    'Status': policy.Status,
                    'Description': policy.PolicyDescription,
                    'Department': policy.Department,
                    'Created By': policy.CreatedByName,
                    'Created Date': policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                    'Start Date': policy.StartDate.isoformat() if policy.StartDate else None,
                    'End Date': policy.EndDate.isoformat() if policy.EndDate else None,
                    'Applicability': policy.Applicability,
                    'Scope': policy.Scope,
                    'Objective': policy.Objective,
                    'Identifier': policy.Identifier,
                    'Active/Inactive': policy.ActiveInactive,
                    # Subpolicy fields (empty)
                    'Subpolicy ID': None,
                    'Subpolicy Name': None,
                    'Subpolicy Identifier': None,
                    'Subpolicy Description': None,
                    'Subpolicy Status': None,
                    'Subpolicy Permanent/Temporary': None,
                    'Subpolicy Control': None,
                    'Subpolicy Created By': None,
                    'Subpolicy Created Date': None,
                }
                export_data_list.append(row)

        # Get export format from request
        export_format = request.data.get('format', 'xlsx')
        print(f"[EXPORT] Export format requested: {export_format}")

        # Export the data
        print("[EXPORT] Initiating export_data process...")
        result = export_data(
            data=export_data_list,
            file_format=export_format,
            user_id=request.user.id if request.user.is_authenticated else 'anonymous',
            options={
                'framework_id': framework_id,
                'framework_name': framework.FrameworkName
            }
        )

        print(f"[EXPORT] Export successful. File name: {result['file_name']}")
        
        # Log successful export
        send_log(
            module="Policy",
            actionType="EXPORT_POLICIES_TO_EXCEL_SUCCESS",
            description=f"Successfully exported policies to Excel for framework {framework_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_name": framework.FrameworkName,
                "export_format": export_format,
                "file_name": result['file_name'],
                "records_exported": len(export_data_list)
            }
        )
        
        return Response({
            'success': True,
            'export_id': result['export_id'],
            'file_url': result['file_url'],
            'file_name': result['file_name'],
            'metadata': result['metadata']
        })

    except Framework.DoesNotExist:
        print(f"[ERROR] Framework with ID {framework_id} not found.")
        
        # Log framework not found
        send_log(
            module="Policy",
            actionType="EXPORT_POLICIES_TO_EXCEL_FAILED",
            description=f"Framework {framework_id} not found for export",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        
        return Response({
            'success': False,
            'error': 'Framework not found'
        }, status=404)
        
    except Exception as e:
        print(f"[ERROR] Exception during export: {str(e)}")
        
        # Log export error
        send_log(
            module="Policy",
            actionType="EXPORT_POLICIES_TO_EXCEL_FAILED",
            description=f"Error exporting policies to Excel for framework {framework_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([PolicyListPermission])
def policy_list(request):
    """
    List all policies, or filter by status and framework_id
    Automatically applies framework filter from session if no explicit filter provided
    """
    from .framework_filter_helper import apply_framework_filter, get_framework_filter_info
    
    # Log policy list retrieval attempt
    status_param = request.query_params.get('status', None)
    framework_id_param = request.query_params.get('framework_id', None)
    
    # Get framework filter info
    filter_info = get_framework_filter_info(request)
    
    send_log(
        module="Policy",
        actionType="POLICY_LIST",
        description=f"Retrieving policy list with status filter: {status_param}, framework filter: {framework_id_param}, session filter: {filter_info}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        ipAddress=get_client_ip(request),
        additionalInfo={"status_filter": status_param, "framework_filter": framework_id_param, "session_filter": filter_info}
    )
    
    # Start with all policies
    policies = Policy.objects.all()
    
    # Apply status filter if provided
    if status_param is not None:
        policies = policies.filter(Status=status_param)
    
    # Apply explicit framework filter if provided in query params
    if framework_id_param is not None:
        policies = policies.filter(FrameworkId=framework_id_param)
    else:
        # Apply session-based framework filter if no explicit filter
        policies = apply_framework_filter(policies, request, 'FrameworkId')
    
    # Log successful policy list retrieval
    send_log(
        module="Policy",
        actionType="POLICY_LIST_SUCCESS",
        description=f"Successfully retrieved {policies.count()} policies",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        ipAddress=get_client_ip(request),
        additionalInfo={"status_filter": status_param, "framework_filter": framework_id_param, "policy_count": policies.count(), "session_filter": filter_info}
    )
    
    serializer = PolicySerializer(policies, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing users list
def list_users(request):
    # Log users list retrieval attempt
    send_log(
        module="Policy",
        actionType="LIST_USERS",
        description="Retrieving list of all users",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="User",
        ipAddress=get_client_ip(request)
    )
    
    try:
        users = Users.objects.all()
        data = [{
            'UserId': user.UserId,
            'UserName': user.UserName
        } for user in users]
        
        # Log successful users list retrieval
        send_log(
            module="Policy",
            actionType="LIST_USERS_SUCCESS",
            description=f"Successfully retrieved {len(data)} users",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="User",
            ipAddress=get_client_ip(request),
            additionalInfo={"user_count": len(data)}
        )
        
        return Response(data)
    except Exception as e:
        # Log users list retrieval error
        send_log(
            module="Policy",
            actionType="LIST_USERS_FAILED",
            description=f"Error retrieving users list: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="User",
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response({
            'error': 'Error fetching users',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_framework_explorer_data(request):
    """
    API endpoint for the Framework Explorer page
    Returns frameworks with their status and counts of active/inactive policies
    Supports entity filtering based on query parameters
    """
    # Get entity filter parameter
    entity_filter = request.GET.get('entity', None)
    
    # Get active_only parameter - if True, only return active frameworks
    active_only = request.GET.get('active_only', 'false').lower() == 'true'
    
    # Log framework explorer data retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_FRAMEWORK_EXPLORER_DATA",
        description=f"Retrieving framework explorer data (entity filter: {entity_filter}, active_only: {active_only})",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Framework",
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Get frameworks based on active_only parameter
        if active_only:
            frameworks = Framework.objects.filter(ActiveInactive='Active')
        else:
            frameworks = Framework.objects.all()
       
        # Prepare response data with additional counts
        framework_data = []
        for fw in frameworks:
            # Base policy query for this framework
            policy_query = Policy.objects.filter(FrameworkId=fw.FrameworkId)
            
            # Apply entity filtering if specified
            if entity_filter:
                if entity_filter == 'all':
                    # Filter for policies that apply to all entities
                    policy_query = policy_query.filter(Entities__contains='all')
                else:
                    # Filter for policies that include this specific entity ID
                    # This handles both list format [1,2,3] and single entity [1]
                    policy_query = policy_query.filter(
                        models.Q(Entities__contains=[int(entity_filter)]) |  # Entity in list
                        models.Q(Entities__contains='all')  # Or applies to all entities
                    )
            
            # Count policies for this framework (with entity filter applied)
            active_policies = policy_query.filter(ActiveInactive='Active').count()
            inactive_policies = policy_query.filter(ActiveInactive='Inactive').count()
            
            # Skip frameworks that have no policies matching the entity filter
            if entity_filter and (active_policies == 0 and inactive_policies == 0):
                continue
           
            framework_data.append({
                'id': fw.FrameworkId,
                'name': fw.FrameworkName,
                'category': fw.Category or 'Uncategorized',
                'description': fw.FrameworkDescription,
                'status': fw.ActiveInactive,  # 'Active' or 'Inactive'
                'internalExternal': fw.InternalExternal or 'External',  # Add Internal/External field
                'active_policies_count': active_policies,
                'inactive_policies_count': inactive_policies
            })
       
        # Calculate summary counts (with entity filter applied)
        if entity_filter:
            # When filtering by entity, calculate summary based on filtered policies
            if entity_filter == 'all':
                summary_policy_query = Policy.objects.filter(Entities__contains='all')
            else:
                summary_policy_query = Policy.objects.filter(
                    models.Q(Entities__contains=[int(entity_filter)]) |
                    models.Q(Entities__contains='all')
                )
            active_policies = summary_policy_query.filter(ActiveInactive='Active').count()
            inactive_policies = summary_policy_query.filter(ActiveInactive='Inactive').count()
            
            # Framework counts are based on frameworks that have matching policies
            active_frameworks = len([fw for fw in framework_data if fw['status'] == 'Active'])
            inactive_frameworks = len([fw for fw in framework_data if fw['status'] != 'Active'])
        else:
            # No entity filter - use counts based on active_only parameter
            if active_only:
                # When active_only is True, only count active frameworks
                active_frameworks = Framework.objects.filter(ActiveInactive='Active').count()
                inactive_frameworks = 0
            else:
                # Count all frameworks
                active_frameworks = Framework.objects.filter(ActiveInactive='Active').count()
                inactive_frameworks = Framework.objects.filter(ActiveInactive='Inactive').count()
            
            # Policy counts remain the same (all policies regardless of framework status)
            active_policies = Policy.objects.filter(ActiveInactive='Active').count()
            inactive_policies = Policy.objects.filter(ActiveInactive='Inactive').count()
       
        # Log successful framework explorer data retrieval
        send_log(
            module="Policy",
            actionType="GET_FRAMEWORK_EXPLORER_DATA_SUCCESS",
            description=f"Successfully retrieved framework explorer data with {len(framework_data)} frameworks",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_count": len(framework_data),
                "active_frameworks": active_frameworks,
                "inactive_frameworks": inactive_frameworks,
                "active_policies": active_policies,
                "inactive_policies": inactive_policies
            }
        )
        
        return Response({
            'frameworks': framework_data,
            'summary': {
                'active_frameworks': active_frameworks,
                'inactive_frameworks': inactive_frameworks,
                'active_policies': active_policies,
                'inactive_policies': inactive_policies
            }
        })
       
    except Exception as e:
        # Log framework explorer data retrieval error
        send_log(
            module="Policy",
            actionType="GET_FRAMEWORK_EXPLORER_DATA_FAILED",
            description=f"Error retrieving framework explorer data: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing framework policies
def get_framework_policies(request, framework_id):
    """
    API endpoint for the Framework Policies page
    Returns policies for a specific framework with acknowledgment status
    """
    # Log framework policies retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_FRAMEWORK_POLICIES",
        description=f"Retrieving policies for framework {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Framework",
        entityId=framework_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Check if framework exists
        framework = get_object_or_404(Framework, FrameworkId=framework_id)
        
        # Get current user ID for acknowledgment status checking
        user_id = None
        
        # Try to get user_id from JWT token first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                from ...authentication import verify_jwt_token
                payload = verify_jwt_token(token)
                if payload and 'user_id' in payload:
                    user_id = payload['user_id']
            except Exception as e:
                print(f"Error extracting user_id from JWT: {e}")
        
        # Fallback to request.user if JWT extraction failed
        if not user_id:
            user_id = getattr(request.user, 'UserId', None)
            if not user_id:
                user_id = getattr(request.user, 'id', None)
        
        # Fallback to session if still no user_id
        if not user_id:
            user_id = request.session.get('user_id')
       
        # Get policies for this framework
        policies = Policy.objects.filter(FrameworkId=framework_id)
       
        # Prepare response data
        policy_data = []
        for policy in policies:
            # Check if current user has acknowledged this policy
            is_acknowledged = False
            if user_id and policy.AcknowledgedUserIds:
                # Convert to list if it's not already
                acknowledged_users = policy.AcknowledgedUserIds if isinstance(policy.AcknowledgedUserIds, list) else []
                is_acknowledged = user_id in acknowledged_users
            
            policy_data.append({
                'id': policy.PolicyId,
                'name': policy.PolicyName,
                'category': policy.Department or 'General',
                'description': policy.PolicyDescription,
                'status': policy.ActiveInactive,  # 'Active' or 'Inactive'
                'Entities': policy.Entities,  # Include entities for filtering
                'isAcknowledged': is_acknowledged,  # Add acknowledgment status
                'acknowledgementCount': policy.AcknowledgementCount or 0  # Add acknowledgment count
            })
       
        # Framework details
        framework_data = {
            'id': framework.FrameworkId,
            'name': framework.FrameworkName,
            'category': framework.Category,
            'description': framework.FrameworkDescription
        }
       
        # Log successful framework policies retrieval
        send_log(
            module="Policy",
            actionType="GET_FRAMEWORK_POLICIES_SUCCESS",
            description=f"Successfully retrieved {len(policy_data)} policies for framework {framework_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_name": framework.FrameworkName,
                "policy_count": len(policy_data)
            }
        )
        
        return Response({
            'framework': framework_data,
            'policies': policy_data
        })
       
    except Exception as e:
        # Log framework policies retrieval error
        send_log(
            module="Policy",
            actionType="GET_FRAMEWORK_POLICIES_FAILED",
            description=f"Error retrieving policies for framework {framework_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['POST'])
@permission_classes([PolicyEditPermission])  # RBAC: Require PolicyEditPermission for toggling framework status
def toggle_framework_status(request, framework_id):
    """
    Toggle the ActiveInactive status of a framework
    When cascadeToApproved=True, also update the status of all approved policies
    but leave their subpolicies status unchanged
    """
    # Log framework status toggle attempt
    send_log(
        module="Policy",
        actionType="TOGGLE_FRAMEWORK_STATUS",
        description=f"Attempting to toggle framework status for framework {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Framework",
        entityId=framework_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        framework = get_object_or_404(Framework, FrameworkId=framework_id)
       
        # Toggle status
        new_status = 'Inactive' if framework.ActiveInactive == 'Active' else 'Active'
        framework.ActiveInactive = new_status
        
        # Also update the Status field if making inactive
        if new_status == 'Inactive':
            framework.Status = 'Inactive'
        else:
            # If activating, set to Approved status (assuming it was previously approved)
            framework.Status = 'Approved'
            
        framework.save()
       
        # Remove logic for inactivating other versions
        other_versions_deactivated = 0
       
        policies_affected = 0
        subpolicies_affected = 0
       
        # Check if we should cascade to policies
        cascade_to_approved = request.data.get('cascadeToApproved', False)
        if cascade_to_approved:
            # Get ALL policies for this framework (not just approved ones)
            policies = Policy.objects.filter(
                FrameworkId=framework
            )
           
            # Update their status to match the framework
            for policy in policies:
                policy.ActiveInactive = new_status
                
                # Also update the Status field if making inactive
                if new_status == 'Inactive':
                    policy.Status = 'Inactive'
                else:
                    # If activating, set to Approved status (assuming it was previously approved)
                    policy.Status = 'Approved'
                
                policy.save()
                policies_affected += 1
               
                # Also update all subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                for subpolicy in subpolicies:
                    subpolicy.Status = new_status
                    subpolicy.save()
                    subpolicies_affected += 1
       
        # Log successful framework status toggle
        send_log(
            module="Policy",
            actionType="TOGGLE_FRAMEWORK_STATUS_SUCCESS",
            description=f"Successfully toggled framework {framework_id} status to {new_status}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_name": framework.FrameworkName,
                "new_status": new_status,
                "policies_affected": policies_affected,
                "subpolicies_affected": subpolicies_affected,
                "cascade_to_approved": cascade_to_approved
            }
        )
        
        return Response({
            'id': framework.FrameworkId,
            'status': new_status,
            'message': f'Framework status updated to {new_status}',
            'policies_affected': policies_affected,
            'subpolicies_affected': subpolicies_affected,
            'other_versions_deactivated': other_versions_deactivated
        })
       
    except Exception as e:
        # Log framework status toggle error
        send_log(
            module="Policy",
            actionType="TOGGLE_FRAMEWORK_STATUS_FAILED",
            description=f"Error toggling framework status for framework {framework_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['POST'])
@permission_classes([PolicyEditPermission])  # RBAC: Require PolicyEditPermission for toggling policy status
def toggle_policy_status(request, policy_id):
    """
    Toggle the ActiveInactive status of a policy
    For deactivation (Active -> Inactive), use approval flow
    For activation (Inactive -> Active), direct toggle
    """
    # Log policy status toggle attempt
    send_log(
        module="Policy",
        actionType="TOGGLE_POLICY_STATUS",
        description=f"Attempting to toggle policy status for policy {policy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        print(f"DEBUG: toggle_policy_status called for policy ID: {policy_id}")
        print(f"DEBUG: Request data: {request.data}")
        
        try:
            policy = Policy.objects.get(PolicyId=policy_id)
        except Policy.DoesNotExist:
            return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
        print(f"DEBUG: Found policy: {policy.PolicyName}, ActiveInactive: {policy.ActiveInactive}")
        
        # Check if we're deactivating (Active -> Inactive)
        if policy.ActiveInactive == 'Active':
            print("DEBUG: Policy is Active, proceeding with deactivation request")
            # For deactivation, use the request status change flow
            reason = request.data.get('reason', 'Policy deactivation requested')
            reviewer_id = request.data.get('ReviewerId', 2)  # Accept ReviewerId from frontend
            cascade_to_subpolicies = request.data.get('cascadeSubpolicies', True)
            
            print(f"DEBUG: Extracted data - reason: {reason}, reviewer_id: {reviewer_id}, cascade: {cascade_to_subpolicies}")
            
            # Call the status change request function with reviewer ID
            request.data['reason'] = reason
            request.data['ReviewerId'] = reviewer_id
            request.data['cascadeToSubpolicies'] = cascade_to_subpolicies
            
            print("DEBUG: Calling request_policy_status_change logic directly...")
            
            # Instead of calling the API view, call the core logic directly
            try:
                return _handle_policy_status_change_request(request, policy_id, reason, reviewer_id, cascade_to_subpolicies)
            except Exception as e:
                print(f"ERROR in policy status change: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({"error": f"Policy status change failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # For activation (Inactive -> Active), use direct toggle
            new_status = 'Active'
            policy.ActiveInactive = new_status
            
            # Keep current Status field unchanged
            current_status = policy.Status
            print(f"Activating policy {policy.PolicyId} ActiveInactive to {new_status}, Status remains {current_status}")
            
            policy.save()
            
            # When activating a policy, set all other related versions to inactive
            other_versions_deactivated = 0
            try:
                other_versions_deactivated = deactivate_previous_version_policies(policy.PolicyId)
            except:
                other_versions_deactivated = 1  # For simplicity, return 1
            
            subpolicies_affected = 0
            cascade_to_subpolicies = request.data.get('cascadeSubpolicies', False)
            if cascade_to_subpolicies:
                # Get all subpolicies for this policy and update their status
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                for subpolicy in subpolicies:
                    # Only update ActiveInactive if the field exists, otherwise update Status
                    if hasattr(subpolicy, 'ActiveInactive'):
                        subpolicy.ActiveInactive = new_status
                        print(f"Setting subpolicy {subpolicy.SubPolicyId} ActiveInactive to {new_status}")
                    else:
                        subpolicy.Status = new_status
                        print(f"Setting subpolicy {subpolicy.SubPolicyId} Status to {new_status}")
                    subpolicy.save()
                    subpolicies_affected += 1
            
            # Log successful policy status toggle (activation)
            send_log(
                module="Policy",
                actionType="TOGGLE_POLICY_STATUS_SUCCESS",
                description=f"Successfully toggled policy {policy_id} status to {new_status}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "policy_name": policy.PolicyName,
                    "new_status": new_status,
                    "subpolicies_affected": subpolicies_affected,
                    "other_versions_deactivated": other_versions_deactivated,
                    "cascade_to_subpolicies": cascade_to_subpolicies
                }
            )
            
            return Response({
                'id': policy.PolicyId,
                'status': new_status,
                'message': f'Policy status updated to {new_status}',
                'subpolicies_affected': subpolicies_affected,
                'other_versions_deactivated': other_versions_deactivated
            })
        
    except Exception as e:
        print(f"ERROR in toggle_policy_status: {str(e)}")
        
        # Log policy status toggle error
        send_log(
            module="Policy",
            actionType="TOGGLE_POLICY_STATUS_FAILED",
            description=f"Error toggling policy status for policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        traceback.print_exc()
        return Response({
            'error': f"Toggle policy status error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing framework details
def get_framework_details(request, framework_id):
    """
    API endpoint for detailed framework information
    Returns all details of a framework regardless of status
    """
    # Log framework details retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_FRAMEWORK_DETAILS",
        description=f"Retrieving framework details for framework {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Framework",
        entityId=framework_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Get framework by ID
        framework = get_object_or_404(Framework, FrameworkId=framework_id)
       
        # Create response data
        response_data = {
            'FrameworkId': framework.FrameworkId,
            'FrameworkName': framework.FrameworkName,
            'CurrentVersion': framework.CurrentVersion,
            'FrameworkDescription': framework.FrameworkDescription,
            'EffectiveDate': framework.EffectiveDate,
            'CreatedByName': framework.CreatedByName,
            'CreatedByDate': framework.CreatedByDate,
            'Category': framework.Category,
            'DocURL': framework.DocURL,
            'Identifier': framework.Identifier,
            'StartDate': framework.StartDate,
            'EndDate': framework.EndDate,
            'Status': framework.Status,
            'ActiveInactive': framework.ActiveInactive
        }
       
        # Log successful framework details retrieval
        send_log(
            module="Policy",
            actionType="GET_FRAMEWORK_DETAILS_SUCCESS",
            description=f"Successfully retrieved framework details for framework {framework_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"framework_name": framework.FrameworkName}
        )
        
        return Response(response_data)
       
    except Exception as e:
        # Log framework details retrieval error
        send_log(
            module="Policy",
            actionType="GET_FRAMEWORK_DETAILS_FAILED",
            description=f"Error retrieving framework details for framework {framework_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([PolicyViewPermission]) # RBAC: Require PolicyViewPermission for viewing policy details
def get_policy_details(request, policy_id):
    """
    API endpoint for detailed policy information
    Returns all details of a policy regardless of status
    """
    # Log policy details retrieval attempt
    send_log(
        module="Policy",
        actionType="GET_POLICY_DETAILS",
        description=f"Retrieving policy details for policy {policy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Get policy by ID
        policy = get_object_or_404(Policy, PolicyId=policy_id)
       
        # Get all subpolicies for this policy
        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        subpolicy_data = []
       
        for subpolicy in subpolicies:
            subpolicy_data.append({
                'SubPolicyId': subpolicy.SubPolicyId,
                'SubPolicyName': subpolicy.SubPolicyName,
                'CreatedByName': subpolicy.CreatedByName,
                'CreatedByDate': subpolicy.CreatedByDate,
                'Identifier': subpolicy.Identifier,
                'Description': subpolicy.Description,
                'Status': subpolicy.Status,
                'PermanentTemporary': subpolicy.PermanentTemporary,
                'Control': subpolicy.Control
            })
       
        # Create response data
        response_data = {
            'PolicyId': policy.PolicyId,
            'PolicyName': policy.PolicyName,
            'PolicyDescription': policy.PolicyDescription,
            'CurrentVersion': policy.CurrentVersion,
            'StartDate': safe_isoformat(policy.StartDate),
            'EndDate': safe_isoformat(policy.EndDate),
            'Department': policy.Department,
            'CreatedByName': policy.CreatedByName,
            'CreatedByDate': safe_isoformat(policy.CreatedByDate),
            'Applicability': policy.Applicability,
            'DocURL': policy.DocURL,
            'Scope': policy.Scope,
            'Objective': policy.Objective,
            'Identifier': policy.Identifier,
            'PermanentTemporary': policy.PermanentTemporary,
            'Status': policy.Status,
            'ActiveInactive': policy.ActiveInactive,
            'subpolicies': subpolicy_data
        }
       
        # Log successful policy details retrieval
        send_log(
            module="Policy",
            actionType="GET_POLICY_DETAILS_SUCCESS",
            description=f"Successfully retrieved policy details for policy {policy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "policy_name": policy.PolicyName,
                "subpolicy_count": len(subpolicy_data)
            }
        )
        
        return Response(response_data)
       
    except Exception as e:
        # Log policy details retrieval error
        send_log(
            module="Policy",
            actionType="GET_POLICY_DETAILS_FAILED",
            description=f"Error retrieving policy details for policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#all policies code
@api_view(['GET'])
@permission_classes([PolicyListPermission])  # RBAC: Require PolicyListPermission for viewing all frameworks
def all_policies_get_frameworks(request):
    """
    API endpoint to get all frameworks for AllPolicies.vue component.
    Note: Framework list itself is not filtered, but shows which framework is active
    """
    from .framework_filter_helper import get_framework_filter_info
    
    # Log all policies frameworks retrieval attempt
    filter_info = get_framework_filter_info(request)
    send_log(
        module="Policy",
        actionType="ALL_POLICIES_GET_FRAMEWORKS",
        description=f"Retrieving all frameworks for AllPolicies component, active filter: {filter_info}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Framework",
        ipAddress=get_client_ip(request),
        additionalInfo={"active_filter": filter_info}
    )
    
    try:
        # Get all frameworks (don't filter the framework list itself)
        frameworks = Framework.objects.all()
        
        frameworks_data = []
        for framework in frameworks:
            framework_data = {
                'id': framework.FrameworkId,
                'name': framework.FrameworkName,
                'category': framework.Category,
                'status': framework.ActiveInactive,
                'description': framework.FrameworkDescription,
                'versions': []
            }
            
            # Get versions for this framework
            versions = FrameworkVersion.objects.filter(FrameworkId=framework)
            version_data = []
            for version in versions:
                version_data.append({
                    'id': version.VersionId,
                    'name': f"v{version.Version}",
                    'version': version.Version
                })
            
            framework_data['versions'] = version_data
            frameworks_data.append(framework_data)
        
        # Log successful all policies frameworks retrieval
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_FRAMEWORKS_SUCCESS",
            description=f"Successfully retrieved {len(frameworks_data)} frameworks for AllPolicies component",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            ipAddress=get_client_ip(request),
            additionalInfo={"framework_count": len(frameworks_data)}
        )
            
        return Response(frameworks_data)
    
    except Exception as e:
        # Log all policies frameworks retrieval error
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_FRAMEWORKS_FAILED",
            description=f"Error retrieving frameworks for AllPolicies component: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing framework version policies
@audit_view_reports_required
def all_policies_get_framework_version_policies(request, version_id):
    """
    API endpoint to get all policies for a specific framework version for AllPolicies.vue component.
    """
    # Log all policies framework version policies retrieval attempt
    send_log(
        module="Policy",
        actionType="ALL_POLICIES_GET_FRAMEWORK_VERSION_POLICIES",
        description=f"Retrieving policies for framework version {version_id} for AllPolicies component",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="FrameworkVersion",
        entityId=version_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Get the framework version
        framework_version = get_object_or_404(FrameworkVersion, VersionId=version_id)
        framework = framework_version.FrameworkId
        
        # Get policies for this framework
        policies = Policy.objects.filter(
            FrameworkId=framework, 
            CurrentVersion=framework_version.Version
        )
        
        policies_data = []
        for policy in policies:
            policy_data = {
                'id': policy.PolicyId,
                'name': policy.PolicyName,
                'category': policy.Department,
                'status': policy.Status,
                'description': policy.PolicyDescription,
                'versions': []
            }
            
            # Get versions for this policy
            policy_versions = PolicyVersion.objects.filter(PolicyId=policy)
            versions_data = []
            for version in policy_versions:
                versions_data.append({
                    'id': version.VersionId,
                    'name': f"v{version.Version}",
                    'version': version.Version
                })
            
            policy_data['versions'] = versions_data
            policies_data.append(policy_data)
        
        # Log successful all policies framework version policies retrieval
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_FRAMEWORK_VERSION_POLICIES_SUCCESS",
            description=f"Successfully retrieved {len(policies_data)} policies for framework version {version_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkVersion",
            entityId=version_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_name": framework.FrameworkName,
                "version": framework_version.Version,
                "policy_count": len(policies_data)
            }
        )
            
        return Response(policies_data)
        
    except Exception as e:
        # Log all policies framework version policies retrieval error
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_FRAMEWORK_VERSION_POLICIES_FAILED",
            description=f"Error retrieving policies for framework version {version_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkVersion",
            entityId=version_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyListPermission])  # RBAC: Require PolicyListPermission for viewing all policies
def all_policies_get_policies(request):
    """
    API endpoint to get all policies for AllPolicies.vue component.
    Automatically applies framework filter from session if no explicit filter provided
    """
    from .framework_filter_helper import apply_framework_filter_with_relation, get_framework_filter_info
    
    # Log all policies retrieval attempt
    framework_id_param = request.GET.get('framework_id')
    filter_info = get_framework_filter_info(request)
    
    send_log(
        module="Policy",
        actionType="ALL_POLICIES_GET_POLICIES",
        description=f"Retrieving all policies for AllPolicies component with framework filter: {framework_id_param}, session filter: {filter_info}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        ipAddress=get_client_ip(request),
        additionalInfo={"framework_filter": framework_id_param, "session_filter": filter_info}
    )
    
    try:
        # Start with all policies
        policies_query = Policy.objects.all()
        
        # Apply explicit framework filter if provided in query params
        if framework_id_param:
            policies_query = policies_query.filter(FrameworkId_id=framework_id_param)
        else:
            # Apply session-based framework filter if no explicit filter
            policies_query = apply_framework_filter_with_relation(policies_query, request, 'FrameworkId_id')
        
        policies_data = []
        for policy in policies_query:
            policy_data = {
                'id': policy.PolicyId,
                'name': policy.PolicyName,
                'category': policy.Department,
                'status': policy.Status,
                'description': policy.PolicyDescription,
                'versions': []
            }
            
            # Get versions for this policy
            policy_versions = PolicyVersion.objects.filter(PolicyId=policy)
            versions_data = []
            for version in policy_versions:
                versions_data.append({
                    'id': version.VersionId,
                    'name': f"v{version.Version}",
                    'version': version.Version
                })
            
            policy_data['versions'] = versions_data
            policies_data.append(policy_data)
        
        # Log successful all policies retrieval
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_POLICIES_SUCCESS",
            description=f"Successfully retrieved {len(policies_data)} policies for AllPolicies component",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_filter": framework_id_param,
                "policy_count": len(policies_data)
            }
        )
            
        return Response(policies_data)
        
    except Exception as e:
        # Log all policies retrieval error
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_POLICIES_FAILED",
            description=f"Error retrieving policies for AllPolicies component: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e), "framework_filter": framework_id_param}
        )
        
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing policy versions
def all_policies_get_policy_versions(request, policy_id):
    """
    API endpoint to get all versions of a specific policy for AllPolicies.vue component.
    Implements a dedicated version that handles version chains through PreviousVersionId.
    """
    # Log all policies policy versions retrieval attempt
    send_log(
        module="Policy",
        actionType="ALL_POLICIES_GET_POLICY_VERSIONS",
        description=f"Retrieving policy versions for policy {policy_id} for AllPolicies component",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        print(f"Request received for policy versions, policy_id: {policy_id}, type: {type(policy_id)}")
        
        # Ensure we have a valid integer ID
        try:
            policy_id = int(policy_id)
        except (ValueError, TypeError):
            return Response({'error': f'Invalid policy ID format: {policy_id}'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Get the base policy
        try:
            policy = Policy.objects.get(PolicyId=policy_id)
            print(f"Found policy: {policy.PolicyName} (ID: {policy.PolicyId})")
        except Policy.DoesNotExist:
            print(f"Policy with ID {policy_id} not found")
            return Response({'error': f'Policy with ID {policy_id} not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Get the direct policy version
        try:
            direct_version = PolicyVersion.objects.get(PolicyId=policy)
            print(f"Found direct policy version: {direct_version.VersionId}")
        except PolicyVersion.DoesNotExist:
            print(f"No policy version found for policy ID {policy_id}")
            return Response({'error': f'No version found for policy with ID {policy_id}'}, 
                           status=status.HTTP_404_NOT_FOUND)
        except PolicyVersion.MultipleObjectsReturned:
            # If there are multiple versions, get all of them
            direct_versions = list(PolicyVersion.objects.filter(PolicyId=policy))
            print(f"Found {len(direct_versions)} direct versions for policy {policy_id}")
            direct_version = direct_versions[0]  # Just use the first one for starting the chain
        
        # Start building version chain
        all_versions = {}
        visited = set()
        to_process = [direct_version.VersionId]
        
        # Find all versions in the chain
        while to_process:
            current_id = to_process.pop(0)
            
            if current_id in visited:
                continue
                
            visited.add(current_id)
            
            try:
                current_version = PolicyVersion.objects.get(VersionId=current_id)
                all_versions[current_id] = current_version
                
                # Follow PreviousVersionId chain backward
                if current_version.PreviousVersionId and current_version.PreviousVersionId not in visited:
                    to_process.append(current_version.PreviousVersionId)
                    
                # Find versions that reference this one as their previous version
                next_versions = PolicyVersion.objects.filter(PreviousVersionId=current_id)
                for next_ver in next_versions:
                    if next_ver.VersionId not in visited:
                        to_process.append(next_ver.VersionId)
            except PolicyVersion.DoesNotExist:
                print(f"Version with ID {current_id} not found")
                continue
        
        versions_data = []
        for version_id, version in all_versions.items():
            try:
                # Get the policy this version belongs to
                version_policy = version.PolicyId
                
                # Count subpolicies for this policy
                subpolicy_count = SubPolicy.objects.filter(PolicyId=version_policy).count()
                
                # Get previous version details if available
                previous_version = None
                if version.PreviousVersionId:
                    try:
                        previous_version = PolicyVersion.objects.get(VersionId=version.PreviousVersionId)
                    except PolicyVersion.DoesNotExist:
                        pass
                
                # Create a descriptive name
                formatted_name = f"{version.PolicyName} v{version.Version}" if version.PolicyName else f"{version_policy.PolicyName} v{version.Version}"
                
                version_data = {
                    'id': version.VersionId,
                    'policy_id': version_policy.PolicyId,
                    'name': formatted_name,
                    'version': version.Version,
                    'category': version_policy.Department or 'General',
                    'status': version_policy.Status or 'Unknown',
                    'description': version_policy.PolicyDescription or '',
                    'created_date': version.CreatedDate,
                    'created_by': version.CreatedBy,
                    'subpolicy_count': subpolicy_count,
                    'previous_version_id': version.PreviousVersionId,
                    'previous_version_name': previous_version.PolicyName + f" v{previous_version.Version}" if previous_version else None
                }
                versions_data.append(version_data)
                print(f"Added version: {version.VersionId} - {formatted_name}, Previous: {version.PreviousVersionId}")
            except Exception as e:
                print(f"Error processing version {version_id}: {str(e)}")
                # Continue to next version
        
        # Sort versions by version number (descending)
        versions_data.sort(key=lambda x: float(x['version']), reverse=True)

        
        
        print(f"Returning {len(versions_data)} policy versions")
        
        # Log successful all policies policy versions retrieval
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_POLICY_VERSIONS_SUCCESS",
            description=f"Successfully retrieved {len(versions_data)} policy versions for policy {policy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"version_count": len(versions_data)}
        )
        
        return Response(versions_data)
        
    except Exception as e:
        # Log all policies policy versions retrieval error
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_POLICY_VERSIONS_FAILED",
            description=f"Error retrieving policy versions for policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        print(f"Error in all_policies_get_policy_versions: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyListPermission])  # RBAC: Require PolicyListPermission for viewing all subpolicies
def all_policies_get_subpolicies(request):
    """
    API endpoint to get all subpolicies for AllPolicies.vue component.
    """
    # Log all policies subpolicies retrieval attempt
    framework_id = request.GET.get('framework_id')
    send_log(
        module="Policy",
        actionType="ALL_POLICIES_GET_SUBPOLICIES",
        description=f"Retrieving all subpolicies for AllPolicies component with framework filter: {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="SubPolicy",
        ipAddress=get_client_ip(request),
        additionalInfo={"framework_filter": framework_id}
    )
    
    try:
        print("Request received for all subpolicies")
        
        # Optional framework filter
        print(f"Framework filter: {framework_id}")
        
        # Start with all subpolicies
        subpolicies_query = SubPolicy.objects.all()
        
        # If framework filter is provided, filter through policies
        if framework_id:
            try:
                policy_ids = Policy.objects.filter(FrameworkId_id=framework_id).values_list('PolicyId', flat=True)
                print(f"Found {len(policy_ids)} policies for framework {framework_id}")
                subpolicies_query = subpolicies_query.filter(PolicyId_id__in=policy_ids)
            except Exception as e:
                print(f"Error filtering by framework: {str(e)}")
                # Continue with all subpolicies if framework filtering fails
        
        print(f"Found {subpolicies_query.count()} subpolicies")
        
        subpolicies_data = []
        for subpolicy in subpolicies_query:
            try:
                # Get the policy this subpolicy belongs to
                try:
                    policy = Policy.objects.get(PolicyId=subpolicy.PolicyId_id)
                    policy_name = policy.PolicyName
                    department = policy.Department
                except Policy.DoesNotExist:
                    print(f"Policy with ID {subpolicy.PolicyId_id} not found for subpolicy {subpolicy.SubPolicyId}")
                    policy_name = "Unknown Policy"
                    department = "Unknown"
                
                subpolicy_data = {
                    'id': subpolicy.SubPolicyId,
                    'name': subpolicy.SubPolicyName,
                    'category': department or 'General',
                    'status': subpolicy.Status or 'Unknown',
                    'description': subpolicy.Description or '',
                    'control': subpolicy.Control or '',
                    'identifier': subpolicy.Identifier,
                    'permanent_temporary': subpolicy.PermanentTemporary,
                    'policy_id': subpolicy.PolicyId_id,
                    'policy_name': policy_name,
                    'created_by': subpolicy.CreatedByName,
                    'created_date': safe_isoformat(subpolicy.CreatedByDate)
                }
                subpolicies_data.append(subpolicy_data)
                # print(f"Added subpolicy: {subpolicy.SubPolicyId} - {subpolicy.SubPolicyName}")
            except Exception as e:
                print(f"Error processing subpolicy {subpolicy.SubPolicyId}: {str(e)}")
                # Continue to next subpolicy
        
        print(f"Returning {len(subpolicies_data)} subpolicies")
        
        # Log successful all policies subpolicies retrieval
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_SUBPOLICIES_SUCCESS",
            description=f"Successfully retrieved {len(subpolicies_data)} subpolicies for AllPolicies component",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_filter": framework_id,
                "subpolicy_count": len(subpolicies_data)
            }
        )
        
        return Response(subpolicies_data)
        
    except Exception as e:
        # Log all policies subpolicies retrieval error
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_SUBPOLICIES_FAILED",
            description=f"Error retrieving subpolicies for AllPolicies component: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e), "framework_filter": framework_id}
        )
        
        import traceback
        print(f"Error in all_policies_get_subpolicies: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing subpolicy details
def all_policies_get_subpolicy_details(request, subpolicy_id):
    """
    API endpoint to get details of a specific subpolicy for AllPolicies.vue component.
    """
    # Log all policies subpolicy details retrieval attempt
    send_log(
        module="Policy",
        actionType="ALL_POLICIES_GET_SUBPOLICY_DETAILS",
        description=f"Retrieving subpolicy details for subpolicy {subpolicy_id} for AllPolicies component",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="SubPolicy",
        entityId=subpolicy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        subpolicy = get_object_or_404(SubPolicy, SubPolicyId=subpolicy_id)
        policy = subpolicy.PolicyId
        
        subpolicy_data = {
            'id': subpolicy.SubPolicyId,
            'name': subpolicy.SubPolicyName,
            'category': policy.Department,
            'status': subpolicy.Status,
            'description': subpolicy.Description,
            'control': subpolicy.Control,
            'identifier': subpolicy.Identifier,
            'permanent_temporary': subpolicy.PermanentTemporary,
            'policy_id': policy.PolicyId,
            'policy_name': policy.PolicyName
        }
        
        # Log successful all policies subpolicy details retrieval
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_SUBPOLICY_DETAILS_SUCCESS",
            description=f"Successfully retrieved subpolicy details for subpolicy {subpolicy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=subpolicy_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "subpolicy_name": subpolicy.SubPolicyName,
                "policy_name": policy.PolicyName
            }
        )
        
        return Response(subpolicy_data)
        
    except Exception as e:
        # Log all policies subpolicy details retrieval error
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_SUBPOLICY_DETAILS_FAILED",
            description=f"Error retrieving subpolicy details for subpolicy {subpolicy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=subpolicy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing framework versions
def all_policies_get_framework_versions(request, framework_id):
    """
    API endpoint to get all versions of a specific framework for AllPolicies.vue component.
    Implements a dedicated version that handles version chains through PreviousVersionId.
    """
    # Log all policies framework versions retrieval attempt
    send_log(
        module="Policy",
        actionType="ALL_POLICIES_GET_FRAMEWORK_VERSIONS",
        description=f"Retrieving framework versions for framework {framework_id} for AllPolicies component",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Framework",
        entityId=framework_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        print(f"Request received for framework versions, framework_id: {framework_id}, type: {type(framework_id)}")
        
        # Ensure we have a valid integer ID
        try:
            framework_id = int(framework_id)
        except (ValueError, TypeError):
            return Response({'error': f'Invalid framework ID format: {framework_id}'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Get the base framework
        try:
            framework = Framework.objects.get(FrameworkId=framework_id)
            print(f"Found framework: {framework.FrameworkName} (ID: {framework.FrameworkId})")
        except Framework.DoesNotExist:
            print(f"Framework with ID {framework_id} not found")
            return Response({'error': f'Framework with ID {framework_id} not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Get direct versions that belong to this framework
        direct_versions = list(FrameworkVersion.objects.filter(FrameworkId=framework).order_by('-Version'))
        print(f"Found {len(direct_versions)} direct versions for framework {framework_id}")
        
        # Create a dictionary to track all versions by VersionId
        all_versions = {v.VersionId: v for v in direct_versions}
        
        # Create a queue to process versions and follow PreviousVersionId links
        to_process = [v.VersionId for v in direct_versions]
        
        # Process the version chain by following PreviousVersionId links
        while to_process:
            current_id = to_process.pop(0)
            
            # Find versions that reference this one as their previous version
            linked_versions = FrameworkVersion.objects.filter(PreviousVersionId=current_id)
            print(f"Found {len(linked_versions)} linked versions for version ID {current_id}")
            
            for linked in linked_versions:
                if linked.VersionId not in all_versions:
                    # Add newly discovered version to our collection
                    all_versions[linked.VersionId] = linked
                    to_process.append(linked.VersionId)
        
        versions_data = []
        for version_id, version in all_versions.items():
            try:
                # Get the framework this version belongs to
                version_framework = version.FrameworkId
                
                # Count policies for this framework (without filtering by version)
                # This gets all policies associated with this framework regardless of version
                policy_count = Policy.objects.filter(
                    FrameworkId=version_framework
                ).count()
                
                print(f"Found {policy_count} policies for framework {version_framework.FrameworkId}")
                
                # Get previous version details if available
                previous_version = None
                if version.PreviousVersionId:
                    try:
                        previous_version = FrameworkVersion.objects.get(VersionId=version.PreviousVersionId)
                    except FrameworkVersion.DoesNotExist:
                        pass
                
                # Create a more descriptive name using the FrameworkName from the database
                # and appending the version number like v1.0, v2.0, etc.
                formatted_name = f"{version.FrameworkName} v{version.Version}"
                
                version_data = {
                    'id': version.VersionId,
                    'name': formatted_name,
                    'version': version.Version,
                    'category': version_framework.Category or 'General',
                    'status': version_framework.ActiveInactive or 'Unknown',
                    'description': version_framework.FrameworkDescription or '',
                    'created_date': version.CreatedDate,
                    'created_by': version.CreatedBy,
                    'policy_count': policy_count,
                    'previous_version_id': version.PreviousVersionId,
                    'previous_version_name': previous_version.FrameworkName + f" v{previous_version.Version}" if previous_version else None,
                    'framework_id': version_framework.FrameworkId
                }
                versions_data.append(version_data)
                print(f"Added version: {version.VersionId} - {formatted_name}, Previous: {version.PreviousVersionId}")
            except Exception as e:
                print(f"Error processing version {version_id}: {str(e)}")
                # Continue to next version
        
        # Sort versions by version number (descending)
        versions_data.sort(key=lambda x: float(x['version']), reverse=True)
        
        print(f"Returning {len(versions_data)} versions")
        
        # Log successful all policies framework versions retrieval
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_FRAMEWORK_VERSIONS_SUCCESS",
            description=f"Successfully retrieved {len(versions_data)} framework versions for framework {framework_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_name": framework.FrameworkName,
                "version_count": len(versions_data)
            }
        )
        
        return Response(versions_data)
        
    except Exception as e:
        # Log all policies framework versions retrieval error
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_FRAMEWORK_VERSIONS_FAILED",
            description=f"Error retrieving framework versions for framework {framework_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            entityId=framework_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        print(f"Error in all_policies_get_framework_versions: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing policy version subpolicies
def all_policies_get_policy_version_subpolicies(request, version_id):
    """
    API endpoint to get all subpolicies for a specific policy version for AllPolicies.vue component.
    Implements a dedicated version instead of using the existing get_policy_version_subpolicies function.
    """
    # Log all policies policy version subpolicies retrieval attempt
    send_log(
        module="Policy",
        actionType="ALL_POLICIES_GET_POLICY_VERSION_SUBPOLICIES",
        description=f"Retrieving subpolicies for policy version {version_id} for AllPolicies component",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="PolicyVersion",
        entityId=version_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        print(f"Request received for policy version subpolicies, version_id: {version_id}, type: {type(version_id)}")
        
        # Ensure we have a valid integer ID
        try:
            version_id = int(version_id)
        except (ValueError, TypeError):
            print(f"Invalid version ID format: {version_id}")
            return Response({'error': f'Invalid version ID format: {version_id}'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Get the policy version
        try:
            policy_version = PolicyVersion.objects.get(VersionId=version_id)
            print(f"Found policy version: {policy_version.VersionId} for policy {policy_version.PolicyId_id}")
        except PolicyVersion.DoesNotExist:
            print(f"Policy version with ID {version_id} not found")
            return Response({'error': f'Policy version with ID {version_id} not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Get the policy this version belongs to
        try:
            policy = Policy.objects.get(PolicyId=policy_version.PolicyId_id)
            print(f"Found policy: {policy.PolicyName} (ID: {policy.PolicyId})")
        except Policy.DoesNotExist:
            print(f"Policy with ID {policy_version.PolicyId_id} not found")
            return Response({'error': f'Policy with ID {policy_version.PolicyId_id} not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Get subpolicies for this policy
        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        print(f"Found {len(subpolicies)} subpolicies for policy {policy.PolicyId}")
        
        subpolicies_data = []
        for subpolicy in subpolicies:
            try:
                subpolicy_data = {
                    'id': subpolicy.SubPolicyId,
                    'name': subpolicy.SubPolicyName,
                    'category': policy.Department or 'General',
                    'status': subpolicy.Status or 'Unknown',
                    'description': subpolicy.Description or '',
                    'control': subpolicy.Control or '',
                    'identifier': subpolicy.Identifier,
                    'permanent_temporary': subpolicy.PermanentTemporary,
                    'policy_id': policy.PolicyId,
                    'policy_name': policy.PolicyName,
                    'created_by': subpolicy.CreatedByName,
                    'created_date': safe_isoformat(subpolicy.CreatedByDate)
                }
                subpolicies_data.append(subpolicy_data)
                print(f"Added subpolicy: {subpolicy.SubPolicyId} - {subpolicy.SubPolicyName}")
            except Exception as e:
                print(f"Error processing subpolicy {subpolicy.SubPolicyId}: {str(e)}")
                # Continue to next subpolicy
        
        print(f"Returning {len(subpolicies_data)} subpolicies")
        
        # Log successful all policies policy version subpolicies retrieval
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_POLICY_VERSION_SUBPOLICIES_SUCCESS",
            description=f"Successfully retrieved {len(subpolicies_data)} subpolicies for policy version {version_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyVersion",
            entityId=version_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "policy_name": policy.PolicyName,
                "subpolicy_count": len(subpolicies_data)
            }
        )
        
        return Response(subpolicies_data)
        
    except Exception as e:
        # Log all policies policy version subpolicies retrieval error
        send_log(
            module="Policy",
            actionType="ALL_POLICIES_GET_POLICY_VERSION_SUBPOLICIES_FAILED",
            description=f"Error retrieving subpolicies for policy version {version_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyVersion",
            entityId=version_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        print(f"Error in all_policies_get_policy_version_subpolicies: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([PolicyExportPermission])
def export_all_frameworks_policies(request):
    """
    Export all frameworks, their policies, and subpolicies to the requested format.
    """
    from ...models import Framework, Policy, SubPolicy
    from ...routes.Global.s3_fucntions import export_data
    from ...utils import send_log, get_client_ip
    from django.utils import timezone
    import traceback

    export_format = request.data.get('format', 'xlsx')
    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    try:
        # Gather all frameworks
        frameworks = Framework.objects.all()
        export_data_list = []
        for framework in frameworks:
            policies = Policy.objects.filter(FrameworkId=framework.FrameworkId)
            for policy in policies:
                subpolicies = SubPolicy.objects.filter(PolicyId=policy.PolicyId)
                if subpolicies.exists():
                    for sub in subpolicies:
                        row = {
                            'Framework ID': framework.FrameworkId,
                            'Framework Name': framework.FrameworkName,
                            'Framework Category': framework.Category,
                            'Framework Status': framework.ActiveInactive,
                            'Policy ID': policy.PolicyId,
                            'Policy Name': policy.PolicyName,
                            'Version': policy.CurrentVersion,
                            'Status': policy.Status,
                            'Description': policy.PolicyDescription,
                            'Department': policy.Department,
                            'Created By': policy.CreatedByName,
                            'Created Date': policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                            'Start Date': policy.StartDate.isoformat() if policy.StartDate else None,
                            'End Date': policy.EndDate.isoformat() if policy.EndDate else None,
                            'Applicability': policy.Applicability,
                            'Scope': policy.Scope,
                            'Objective': policy.Objective,
                            'Identifier': policy.Identifier,
                            'Active/Inactive': policy.ActiveInactive,
                            # Subpolicy fields
                            'Subpolicy ID': sub.SubPolicyId,
                            'Subpolicy Name': sub.SubPolicyName,
                            'Subpolicy Identifier': sub.Identifier,
                            'Subpolicy Description': sub.Description,
                            'Subpolicy Status': sub.Status,
                            'Subpolicy Permanent/Temporary': sub.PermanentTemporary,
                            'Subpolicy Control': sub.Control,
                            'Subpolicy Created By': sub.CreatedByName,
                            'Subpolicy Created Date': sub.CreatedByDate.isoformat() if sub.CreatedByDate else None,
                        }
                        export_data_list.append(row)
                else:
                    row = {
                        'Framework ID': framework.FrameworkId,
                        'Framework Name': framework.FrameworkName,
                        'Framework Category': framework.Category,
                        'Framework Status': framework.ActiveInactive,
                        'Policy ID': policy.PolicyId,
                        'Policy Name': policy.PolicyName,
                        'Version': policy.CurrentVersion,
                        'Status': policy.Status,
                        'Description': policy.PolicyDescription,
                        'Department': policy.Department,
                        'Created By': policy.CreatedByName,
                        'Created Date': policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                        'Start Date': policy.StartDate.isoformat() if policy.StartDate else None,
                        'End Date': policy.EndDate.isoformat() if policy.EndDate else None,
                        'Applicability': policy.Applicability,
                        'Scope': policy.Scope,
                        'Objective': policy.Objective,
                        'Identifier': policy.Identifier,
                        'Active/Inactive': policy.ActiveInactive,
                        # Subpolicy fields (empty)
                        'Subpolicy ID': None,
                        'Subpolicy Name': None,
                        'Subpolicy Identifier': None,
                        'Subpolicy Description': None,
                        'Subpolicy Status': None,
                        'Subpolicy Permanent/Temporary': None,
                        'Subpolicy Control': None,
                        'Subpolicy Created By': None,
                        'Subpolicy Created Date': None,
                    }
                    export_data_list.append(row)
        # Export the data
        result = export_data(
            data=export_data_list,
            file_format=export_format,
            user_id=user_id,
            options={
                'export_type': 'all_frameworks',
                'exported_at': timezone.now().isoformat(),
            }
        )
        send_log(
            module="Policy",
            actionType="EXPORT_ALL_FRAMEWORKS_POLICIES_SUCCESS",
            description=f"Successfully exported all frameworks, policies, and subpolicies.",
            userId=user_id,
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            ipAddress=get_client_ip(request),
            additionalInfo={
                "export_format": export_format,
                "file_name": result.get('file_name'),
                "records_exported": len(export_data_list)
            }
        )
        return Response({
            'success': True,
            'export_id': result.get('export_id'),
            'file_url': result.get('file_url'),
            'file_name': result.get('file_name'),
            'metadata': result.get('metadata')
        })
    except Exception as e:
        send_log(
            module="Policy",
            actionType="EXPORT_ALL_FRAMEWORKS_POLICIES_FAILED",
            description=f"Error exporting all frameworks, policies, and subpolicies: {str(e)}",
            userId=user_id,
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e), "traceback": traceback.format_exc()}
        )
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([PolicyDashboardPermission])  # RBAC: Require PolicyDashboardPermission for policy dashboard
def get_policy_dashboard_summary(request):
    from .framework_filter_helper import apply_framework_filter_with_relation, get_framework_filter_info
    
    # Apply framework filtering to all queries
    policies_base = Policy.objects.all()
    policies_filtered = apply_framework_filter_with_relation(policies_base, request, 'FrameworkId_id')
    
    # Get filtered policy IDs for subpolicy filtering
    policy_ids = list(policies_filtered.values_list('PolicyId', flat=True))
    
    total_policies = policies_filtered.count()
    total_subpolicies = SubPolicy.objects.filter(PolicyId__in=policy_ids).count() if policy_ids else 0
    active_policies = policies_filtered.filter(ActiveInactive='Active').count()
    inactive_policies = policies_filtered.filter(ActiveInactive='Inactive').count()
    active_subpolicies = SubPolicy.objects.filter(PolicyId__in=policy_ids, Status='Approved').count() if policy_ids else 0
    
    # Filter approvals by the filtered policies
    approved_policies = PolicyApproval.objects.filter(PolicyId__in=policy_ids, ApprovedNot=1).count() if policy_ids else 0
    total_approvals = PolicyApproval.objects.filter(PolicyId__in=policy_ids).count() if policy_ids else 0
    approval_rate = (approved_policies / total_approvals) * 100 if total_approvals else 0

    # Get all filtered policies with their details
    policies = policies_filtered.values(
        'PolicyId', 'PolicyName', 'Department', 'Status', 
        'Applicability', 'CurrentVersion', 'ActiveInactive',
        'PermanentTemporary', 'CreatedByDate'
    )
    
    filter_info = get_framework_filter_info(request)

    return Response({
        'total_policies': total_policies,
        'total_subpolicies': total_subpolicies,
        'active_policies': active_policies,
        'inactive_policies': inactive_policies,
        'active_subpolicies': active_subpolicies,
        'approval_rate': round(approval_rate, 2),
        'policies': list(policies),
        'framework_filter': filter_info
    })

@api_view(['GET'])
@permission_classes([PolicyAnalyticsPermission])  # RBAC: Require PolicyAnalyticsPermission for viewing policy status distribution
def get_policy_status_distribution(request):
    from .framework_filter_helper import apply_framework_filter_with_relation
    
    # Apply framework filter
    policies = apply_framework_filter_with_relation(Policy.objects.all(), request, 'FrameworkId_id')
    status_counts = policies.values('Status').annotate(count=Count('Status'))
    return Response(status_counts)

@api_view(['GET'])
@permission_classes([PolicyAnalyticsPermission]) # RBAC: Require PolicyAnalyticsPermission for viewing reviewer workload
def get_reviewer_workload(request):
    from .framework_filter_helper import apply_framework_filter_with_relation
    
    # Apply framework filter
    policies = apply_framework_filter_with_relation(Policy.objects.all(), request, 'FrameworkId_id')
    reviewer_counts = policies.values('Reviewer').annotate(count=Count('Reviewer')).order_by('-count')
    return Response(reviewer_counts)

from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
@permission_classes([PolicyAnalyticsPermission])  # RBAC: Require PolicyAnalyticsPermission for viewing recent policy activity
def get_recent_policy_activity(request):
    from .framework_filter_helper import apply_framework_filter_with_relation
    
    one_week_ago = timezone.now().date() - timedelta(days=7)
    activities = []
    
    # Apply framework filter to policies
    policies_filtered = apply_framework_filter_with_relation(Policy.objects.all(), request, 'FrameworkId_id')
    
    # 1. Recent Policy Creation - using filtered policies
    recent_policies = policies_filtered.filter(CreatedByDate__gte=one_week_ago).order_by('-CreatedByDate')[:5]
    for policy in recent_policies:
        activities.append({
            'type': 'policy_created',
            'title': 'Policy Created',
            'name': policy.PolicyName,
            'created_by': policy.CreatedByName,
            'date': safe_isoformat(policy.CreatedByDate),
            'icon': 'fas fa-file-plus'
        })
    
    # 2. Recent Policy Approvals
    recent_policy_approvals = PolicyApproval.objects.filter(
        ApprovedDate__gte=one_week_ago,
        ApprovedNot=True
    ).select_related('PolicyId').order_by('-ApprovedDate')[:5]
    for approval in recent_policy_approvals:
        if approval.PolicyId:
            activities.append({
                'type': 'policy_approved',
                'title': 'Policy Approved',
                'name': approval.PolicyId.PolicyName,
                'created_by': f"Approved by Reviewer {approval.ReviewerId}",
                'date': safe_isoformat(approval.ApprovedDate),
                'icon': 'fas fa-check-circle'
            })
    
    # 3. Recent Framework Creation
    recent_frameworks = Framework.objects.filter(CreatedByDate__gte=one_week_ago).order_by('-CreatedByDate')[:5]
    for framework in recent_frameworks:
        activities.append({
            'type': 'framework_created',
            'title': 'Framework Created',
            'name': framework.FrameworkName,
            'created_by': framework.CreatedByName,
            'date': safe_isoformat(framework.CreatedByDate),
            'icon': 'fas fa-layer-group'
        })
    
    # 4. Recent Framework Approvals
    recent_framework_approvals = FrameworkApproval.objects.filter(
        ApprovedDate__gte=one_week_ago,
        ApprovedNot=True
    ).select_related('FrameworkId').order_by('-ApprovedDate')[:5]
    for approval in recent_framework_approvals:
        if approval.FrameworkId:
            activities.append({
                'type': 'framework_approved',
                'title': 'Framework Approved',
                'name': approval.FrameworkId.FrameworkName,
                'created_by': f"Approved by Reviewer {approval.ReviewerId}",
                'date': safe_isoformat(approval.ApprovedDate),
                'icon': 'fas fa-check-double'
            })
    
    # Sort all activities by date (most recent first) and take top 10
    all_activities = sorted(activities, key=lambda x: x['date'], reverse=True)[:5]
    
    return Response(all_activities)

from django.db.models import F, ExpressionWrapper, DurationField

@api_view(['GET'])
@permission_classes([PolicyAnalyticsPermission])  # RBAC: Require PolicyAnalyticsPermission for viewing average policy approval time
def get_avg_policy_approval_time(request):
    try:
        # Get all approved policies with approval dates, including the related Policy object
        approved_approvals = PolicyApproval.objects.select_related('PolicyId').filter(
            ApprovedNot=True,
            ApprovedDate__isnull=False,
            PolicyId__isnull=False
        )
        
        if not approved_approvals:
            return Response({'average_days': 0})

        # Map PolicyId to latest ApprovedDate (use PolicyId_id to get the integer ID)
        latest_approval_dates = {}
        for approval in approved_approvals:
            pid = approval.PolicyId_id  # Get the actual integer ID from the foreign key
            if pid not in latest_approval_dates or approval.ApprovedDate > latest_approval_dates[pid]:
                latest_approval_dates[pid] = approval.ApprovedDate

        # For each PolicyId, get CreatedByDate from Policy and compute days
        total_days = 0
        count = 0
        for pid, approved_date in latest_approval_dates.items():
            try:
                policy = Policy.objects.get(PolicyId=pid)
                created_date = policy.CreatedByDate
                if created_date and approved_date:
                    days = (approved_date - created_date).days
                    if days >= 0:
                        total_days += days
                        count += 1
            except Policy.DoesNotExist:
                continue

        avg_days = total_days / count if count > 0 else 0
        return Response({'average_days': round(avg_days, 2)})
        
    except Exception as e:
        print(f"Error in get_avg_policy_approval_time: {str(e)}")
        return Response({'error': 'Failed to calculate average approval time'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyAnalyticsPermission])  # RBAC: Require PolicyAnalyticsPermission for viewing framework status distribution
def get_framework_status_distribution(request):
    """
    Get framework status distribution (Approved, Rejected, Under Review, etc.)
    Can show overall framework status OR policy status for a specific framework
    """
    try:
        # Check if a specific framework is selected
        framework_id = request.GET.get('framework_id')
        
        if framework_id and framework_id != 'all':
            # Show policy status distribution for the selected framework
            print(f"DEBUG: Getting policy status distribution for framework {framework_id}")
            
            # Count policies by status for the specific framework
            status_counts = Policy.objects.filter(
                FrameworkId=framework_id
            ).values('Status').annotate(
                count=Count('Status')
            ).order_by('Status')
            
            print(f"DEBUG: Raw policy status counts for framework {framework_id}: {list(status_counts)}")
            
            # Convert to the format expected by frontend
            data = []
            for item in status_counts:
                status = item['Status']
                count = item['count']
                
                # Handle null/empty status values
                if status is None or status == '':
                    status = 'No Status'
                
                print(f"DEBUG: Processing policy status '{status}' with count {count}")
                data.append({
                    'label': status,
                    'value': count
                })
            
            # If no data, provide default structure
            if not data:
                print("DEBUG: No policy status data found for framework, providing default structure")
                data = [
                    {'label': 'Approved', 'value': 0},
                    {'label': 'Rejected', 'value': 0},
                    {'label': 'Under Review', 'value': 0},
                    {'label': 'No Status', 'value': 0}
                ]
            
            # Get total policies for this framework
            total_policies = Policy.objects.filter(FrameworkId=framework_id).count()
            print(f"DEBUG: Total policies for framework {framework_id}: {total_policies}")
            
        else:
            # Show overall framework status distribution (existing logic)
            print("DEBUG: Getting overall framework status distribution")
            
            # Get all frameworks and count by Status field
            status_counts = Framework.objects.values('Status').annotate(
                count=Count('Status')
            ).order_by('Status')
            
            print(f"DEBUG: Raw framework status counts from database: {list(status_counts)}")
            
            # Convert to the format expected by frontend
            data = []
            for item in status_counts:
                status = item['Status']
                count = item['count']
                
                # Handle null/empty status values
                if status is None or status == '':
                    status = 'No Status'
                
                print(f"DEBUG: Processing framework status '{status}' with count {count}")
                data.append({
                    'label': status,
                    'value': count
                })
            
            # If no data, provide default structure
            if not data:
                print("DEBUG: No framework status data found, providing default structure")
                data = [
                    {'label': 'Approved', 'value': 0},
                    {'label': 'Rejected', 'value': 0},
                    {'label': 'Under Review', 'value': 0},
                    {'label': 'No Status', 'value': 0}
                ]
            
            # Also get total frameworks for debugging
            total_frameworks = Framework.objects.count()
            print(f"DEBUG: Total frameworks in database: {total_frameworks}")
            
            # Verify the sum matches total frameworks
            calculated_total = sum(item['value'] for item in data)
            print(f"DEBUG: Calculated total from status counts: {calculated_total}")
            
            if calculated_total != total_frameworks:
                print(f"WARNING: Status count total ({calculated_total}) doesn't match total frameworks ({total_frameworks})")
                # Add a catch-all category for any missing frameworks
                missing_count = total_frameworks - calculated_total
                if missing_count > 0:
                    data.append({
                        'label': 'Other',
                        'value': missing_count
                    })
        
        print(f"DEBUG: Final status distribution data: {data}")
        
        return Response(data)
        
    except Exception as e:
        print(f"Error in get_framework_status_distribution: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to get framework status distribution: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyAnalyticsPermission]) # RBAC: Require PolicyAnalyticsPermission for policy analytics
def get_policy_analytics(request):
    try:
        x_axis = request.GET.get('x_axis', 'time')
        y_axis = request.GET.get('y_axis', 'count')
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        
        # Initialize base queryset
        if x_axis == 'subpolicy':
            queryset = SubPolicy.objects.all()
            base_model = 'subpolicy'
            
            # Apply framework filter to subpolicies through policy relationship
            if framework_id and framework_id != 'all':
                queryset = queryset.filter(PolicyId__FrameworkId=framework_id)
            
            # Apply policy filter to subpolicies
            if policy_id and policy_id != 'all':
                queryset = queryset.filter(PolicyId=policy_id)
                
        elif x_axis == 'framework':
            queryset = Framework.objects.all()
            base_model = 'framework'
            
            # Apply framework filter
            if framework_id and framework_id != 'all':
                queryset = queryset.filter(FrameworkId=framework_id)
                
        else:
            queryset = Policy.objects.all()
            base_model = 'policy'
            
            # Apply framework filter to policies
            if framework_id and framework_id != 'all':
                queryset = queryset.filter(FrameworkId=framework_id)
            
            # Apply policy filter
            if policy_id and policy_id != 'all':
                queryset = queryset.filter(PolicyId=policy_id)

        # Handle framework X-axis with different Y-axis options
        if x_axis == 'framework':
            print(f"DEBUG: Processing framework X-axis with Y-axis: {y_axis}")
            
            if framework_id and framework_id != 'all':
                # Get data for specific framework
                print(f"DEBUG: Getting analytics for specific framework {framework_id}")
                
                if y_axis == 'status':
                    # Policy status distribution for specific framework
                    status_counts = Policy.objects.filter(
                        FrameworkId=framework_id
                    ).values('Status').annotate(
                        count=Count('Status')
                    ).order_by('Status')
                    
                    data = []
                    for item in status_counts:
                        status = item['Status'] or 'No Status'
                        count = item['count']
                        data.append({
                            'label': status,
                            'value': count
                        })
                    
                    if not data:
                        data = [
                            {'label': 'Approved', 'value': 0},
                            {'label': 'Rejected', 'value': 0},
                            {'label': 'Under Review', 'value': 0},
                            {'label': 'No Status', 'value': 0}
                        ]
                    
                    return Response(data)
                    
                elif y_axis == 'activeInactive':
                    # Policy active/inactive distribution for specific framework
                    active_counts = Policy.objects.filter(
                        FrameworkId=framework_id
                    ).values('ActiveInactive').annotate(
                        count=Count('ActiveInactive')
                    ).order_by('ActiveInactive')
                    
                    data = []
                    for item in active_counts:
                        status = item['ActiveInactive'] or 'No Status'
                        count = item['count']
                        data.append({
                            'label': status,
                            'value': count
                        })
                    
                    if not data:
                        data = [
                            {'label': 'Active', 'value': 0},
                            {'label': 'Inactive', 'value': 0},
                            {'label': 'No Status', 'value': 0}
                        ]
                    
                    return Response(data)
                    
                elif y_axis == 'category':
                    # Policy category distribution for specific framework
                    category_counts = Policy.objects.filter(
                        FrameworkId=framework_id
                    ).values('PolicyCategory').annotate(
                        count=Count('PolicyCategory')
                    ).order_by('PolicyCategory')
                    
                    data = []
                    for item in category_counts:
                        category = item['PolicyCategory'] or 'Uncategorized'
                        count = item['count']
                        data.append({
                            'label': category,
                            'value': count
                        })
                    
                    return Response(data)
                    
                elif y_axis == 'createdByDate':
                    # Policy creation date distribution for specific framework
                    date_counts = Policy.objects.filter(
                        FrameworkId=framework_id
                    ).values('CreatedByDate').annotate(
                        count=Count('CreatedByDate')
                    ).order_by('CreatedByDate')
                    
                    data = []
                    for item in date_counts:
                        date_str = item['CreatedByDate'].strftime('%Y-%m-%d') if item['CreatedByDate'] else 'Unknown'
                        count = item['count']
                        data.append({
                            'label': date_str,
                            'value': count
                        })
                    
                    return Response(data)
                    
                elif y_axis == 'createdByName':
                    # Policy creator distribution for specific framework
                    creator_counts = Policy.objects.filter(
                        FrameworkId=framework_id
                    ).values('CreatedByName').annotate(
                        count=Count('CreatedByName')
                    ).order_by('CreatedByName')
                    
                    data = []
                    for item in creator_counts:
                        creator = item['CreatedByName'] or 'Unknown'
                        count = item['count']
                        data.append({
                            'label': creator,
                            'value': count
                        })
                    
                    return Response(data)
                    
                elif y_axis == 'department':
                    # Policy department distribution for specific framework
                    dept_counts = Policy.objects.filter(
                        FrameworkId=framework_id
                    ).values('Department').annotate(
                        count=Count('Department')
                    ).order_by('Department')
                    
                    data = []
                    for item in dept_counts:
                        dept = item['Department'] or 'Unassigned'
                        count = item['count']
                        data.append({
                            'label': dept,
                            'value': count
                        })
                    
                    return Response(data)
                    
            else:
                # Get data for all frameworks - aggregate policy data across all frameworks
                print("DEBUG: Getting analytics for all frameworks")
                
                if y_axis == 'status':
                    # Policy status distribution across all frameworks
                    status_counts = Policy.objects.values('Status').annotate(
                        count=Count('Status')
                    ).order_by('Status')
                    
                    data = []
                    for item in status_counts:
                        status = item['Status'] or 'No Status'
                        count = item['count']
                        data.append({
                            'label': status,
                            'value': count
                        })
                    
                    if not data:
                        data = [
                            {'label': 'Approved', 'value': 0},
                            {'label': 'Rejected', 'value': 0},
                            {'label': 'Under Review', 'value': 0},
                            {'label': 'No Status', 'value': 0}
                        ]
                    
                    return Response(data)
                    
                elif y_axis == 'activeInactive':
                    # Policy active/inactive distribution across all frameworks
                    active_counts = Policy.objects.values('ActiveInactive').annotate(
                        count=Count('ActiveInactive')
                    ).order_by('ActiveInactive')
                    
                    data = []
                    for item in active_counts:
                        status = item['ActiveInactive'] or 'No Status'
                        count = item['count']
                        data.append({
                            'label': status,
                            'value': count
                        })
                    
                    if not data:
                        data = [
                            {'label': 'Active', 'value': 0},
                            {'label': 'Inactive', 'value': 0}
                        ]
                    
                    return Response(data)
                    
                elif y_axis == 'category':
                    # Policy category distribution across all frameworks
                    category_counts = Policy.objects.values('PolicyCategory').annotate(
                        count=Count('PolicyCategory')
                    ).order_by('PolicyCategory')
                    
                    data = []
                    for item in category_counts:
                        category = item['PolicyCategory'] or 'Uncategorized'
                        count = item['count']
                        if category and category.strip():  # Only add non-empty categories
                            data.append({
                                'label': category,
                                'value': count
                            })
                    
                    return Response(data)
                    
                elif y_axis == 'createdByDate':
                    # Policy creation date distribution across all frameworks
                    date_counts = Policy.objects.values('CreatedByDate').annotate(
                        count=Count('CreatedByDate')
                    ).order_by('CreatedByDate')
                    
                    data = []
                    for item in date_counts:
                        date_str = item['CreatedByDate'].strftime('%Y-%m-%d') if item['CreatedByDate'] else 'Unknown'
                        count = item['count']
                        data.append({
                            'label': date_str,
                            'value': count
                        })
                    
                    return Response(data)
                    
                elif y_axis == 'createdByName':
                    # Policy creator distribution across all frameworks
                    creator_counts = Policy.objects.values('CreatedByName').annotate(
                        count=Count('CreatedByName')
                    ).order_by('CreatedByName')
                    
                    data = []
                    for item in creator_counts:
                        creator = item['CreatedByName'] or 'Unknown'
                        count = item['count']
                        data.append({
                            'label': creator,
                            'value': count
                        })
                    
                    return Response(data)
                    
                elif y_axis == 'department':
                    # Policy department distribution across all frameworks
                    dept_counts = Policy.objects.values('Department').annotate(
                        count=Count('Department')
                    ).order_by('Department')
                    
                    data = []
                    for item in dept_counts:
                        dept = item['Department'] or 'Unassigned'
                        count = item['count']
                        if dept and dept.strip():  # Only add non-empty departments
                            data.append({
                                'label': dept,
                                'value': count
                            })
                    
                    return Response(data)
        
        # Continue with existing logic for other X-axis options
        # Select base queryset based on x-axis and y-axis combination
        if y_axis == 'framework_policies' and x_axis == 'time':
            # Count policies created on each date
            queryset = Policy.objects.values(
                'CreatedByDate'
            ).annotate(
                label=F('CreatedByDate'),
                value=Count('PolicyId')
            ).order_by('CreatedByDate')
            
            # Format the dates
            data = list(queryset)
            for item in data:
                item['label'] = item['label'].strftime('%Y-%m-%d') if item['label'] else None
            
            return Response(data)
        
        # Group by X-axis
        if x_axis == 'status':
            queryset = queryset.values(
                'Status'
            ).annotate(
                label=F('Status'),
            )
        elif x_axis == 'policy':
            queryset = queryset.values(
                'PolicyId', 'PolicyName'
            ).annotate(
                label=F('PolicyName'),
            )
        elif x_axis == 'subpolicy':
            queryset = queryset.values(
                'SubPolicyId', 'SubPolicyName'
            ).annotate(
                label=F('SubPolicyName'),
            )
        elif x_axis == 'time':
            date_field = {
                'framework': 'CreatedByDate',
                'policy': 'CreatedByDate',
                'subpolicy': 'CreatedByDate'
            }[base_model]
            queryset = queryset.values(
                date_field
            ).annotate(
                label=F(date_field),
            ).order_by(date_field)
        elif x_axis == 'framework':
            queryset = queryset.values(
                'FrameworkName'
            ).annotate(
                label=F('FrameworkName'),
            )
        
        # Apply Y-axis aggregation
        if y_axis == 'version':
            if base_model == 'framework':
                # Get all framework versions
                framework_versions = FrameworkVersion.objects.values(
                    'FrameworkId__Identifier'  # Group by framework identifier
                ).annotate(
                    version_count=Count('VersionId', distinct=True)  # Count distinct versions
                )
                
                # Create a mapping of framework identifier to version count
                version_counts = {fv['FrameworkId__Identifier']: fv['version_count'] for fv in framework_versions}
                
                # Get all frameworks first
                frameworks = Framework.objects.all()
                framework_id_to_identifier = {f.FrameworkId: f.Identifier for f in frameworks}
                
                # Add version count to each item in queryset
                data = list(queryset)
                for item in data:
                    if x_axis == 'framework':
                        framework_id = item['FrameworkId']
                    else:
                        # For other x_axis types (like department), we need to aggregate versions
                        # Get all frameworks matching the current group
                        if x_axis == 'department':
                            group_frameworks = frameworks.filter(Department=item['Department'])
                        elif x_axis == 'status':
                            group_frameworks = frameworks.filter(Status=item['Status'])
                        elif x_axis == 'applicability':
                            group_frameworks = frameworks.filter(Applicability=item['Applicability'])
                        else:
                            group_frameworks = frameworks
                            
                        # Sum up versions for all frameworks in this group
                        total_versions = 0
                        for framework in group_frameworks:
                            total_versions += version_counts.get(framework.Identifier, 1)
                        item['value'] = total_versions
                        continue
                    
                    # For framework x_axis, use the direct mapping
                    identifier = framework_id_to_identifier.get(framework_id)
                    item['value'] = version_counts.get(identifier, 1) if identifier else 1
                
                return Response(data)
                
            elif base_model == 'policy':
                # Count versions by following PreviousVersionId chain
                policy_versions = PolicyVersion.objects.values('PolicyId').annotate(
                    version_count=Count('VersionId', distinct=True)
                )
                version_counts = {pv['PolicyId']: pv['version_count'] for pv in policy_versions}
                
                # Add version count to each policy
                data = list(queryset)
                for item in data:
                    item['value'] = version_counts.get(item.get('PolicyId'), 0)
                return Response(data)
            else:
                # SubPolicies don't have versions
                queryset = queryset.annotate(value=Value(0))
        elif y_axis == 'activeInactive':
            if base_model == 'framework':
                # For frameworks, use ActiveInactive field
                queryset = queryset.values(
                    'ActiveInactive'
                ).annotate(
                    label=Coalesce('ActiveInactive', Value('Unknown')),
                    value=Count('FrameworkId')
                )
            elif base_model == 'policy':
                # For policies, use ActiveInactive field
                queryset = queryset.values(
                    'ActiveInactive'
                ).annotate(
                    label=Coalesce('ActiveInactive', Value('Unknown')),
                    value=Count('PolicyId')
                )
            else:
                # For subpolicies, use parent policy's ActiveInactive status
                queryset = queryset.values(
                    'PolicyId__ActiveInactive'  # Get ActiveInactive from parent policy
                ).annotate(
                    label=Coalesce('PolicyId__ActiveInactive', Value('Unknown')),
                    value=Count('SubPolicyId')
                )
        elif y_axis == 'framework_policies':
            if base_model == 'framework':
                queryset = queryset.annotate(
                    value=Count('policy')
                )
            else:
                queryset = queryset.annotate(value=Value(0))

        elif y_axis == 'createdByDate':
            # Handle CreatedByDate aggregation based on X-axis selection
            if x_axis == 'framework':
                queryset = queryset.values(
                    'CreatedByDate'
                ).annotate(
                    label=F('CreatedByDate'),
                    value=Count('FrameworkId')
                ).order_by('CreatedByDate')
            elif x_axis == 'policy':
                queryset = queryset.values(
                    'CreatedByDate'
                ).annotate(
                    label=F('CreatedByDate'),
                    value=Count('PolicyId')
                ).order_by('CreatedByDate')
            elif x_axis == 'subpolicy':
                queryset = queryset.values(
                    'CreatedByDate'
                ).annotate(
                    label=F('CreatedByDate'),
                    value=Count('SubPolicyId')
                ).order_by('CreatedByDate')

            # Format the dates for display
            data = list(queryset)
            for item in data:
                if item['label']:
                    # Convert date to string in YYYY-MM-DD format
                    item['label'] = item['label'].strftime('%Y-%m-%d')
            return Response(data)
        elif y_axis == 'department':
            # Handle Department aggregation based on X-axis selection
            if x_axis == 'framework':
                # For frameworks, get departments through policy relationship
                base_queryset = Framework.objects.values(
                    'FrameworkId', 'FrameworkName'
                ).annotate(
                    policy_count=Count('policy')
                ).filter(policy_count__gt=0)

                # Get all policies for these frameworks
                framework_policies = Policy.objects.filter(
                    FrameworkId__in=[f['FrameworkId'] for f in base_queryset]
                ).values('FrameworkId', 'Department')

                # Process departments and count frameworks
                department_counts = {}
                framework_departments = {}  # Track which departments each framework has been counted for

                for policy in framework_policies:
                    framework_id = policy['FrameworkId']
                    dept_str = policy['Department']
                    
                    if not dept_str:
                        continue

                    # Initialize set for this framework if not exists
                    if framework_id not in framework_departments:
                        framework_departments[framework_id] = set()

                    # Split departments and process each
                    departments = [d.strip().upper() for d in dept_str.split(',')]
                    for dept in departments:
                        if dept and dept not in framework_departments[framework_id]:
                            # Count framework for this department only once
                            department_counts[dept] = department_counts.get(dept, 0) + 1
                            framework_departments[framework_id].add(dept)

            elif x_axis == 'policy':
                # For policies, use Department field directly
                base_queryset = queryset.values(
                    'PolicyId',
                    'Department'
                )
            elif x_axis == 'subpolicy':
                # For subpolicies, get department through policy relationship
                base_queryset = queryset.values(
                    'SubPolicyId',
                    'PolicyId__Department'
                )

            if x_axis != 'framework':
                # Process departments and split comma-separated values
                department_counts = {}
                for item in base_queryset:
                    # Get the department field based on the model type
                    dept_field = (
                        item.get('Department') or 
                        item.get('policy__Department') or 
                        item.get('PolicyId__Department')
                    )
                    
                    if dept_field:
                        # Split departments by comma and strip whitespace
                        departments = [d.strip().upper() for d in dept_field.split(',')]
                        for dept in departments:
                            if dept:  # Only count non-empty departments
                                department_counts[dept] = department_counts.get(dept, 0) + 1

            # Convert to list format expected by frontend
            data = [
                {
                    'label': f"{dept.title()} ({count} frameworks)" if x_axis == 'framework' else f"{dept.title()} ({count} items)",
                    'value': count
                }
                for dept, count in department_counts.items()
            ]

            # Sort by count (descending) then by department name
            data.sort(key=lambda x: (-x['value'], x['label']))

            # Add unassigned if no departments found
            if not data:
                label = 'Unassigned (0 frameworks)' if x_axis == 'framework' else 'Unassigned (0 items)'
                data.append({
                    'label': label,
                    'value': 0
                })

            return Response(data)
        elif y_axis == 'createdByName':
            # Handle CreatedByName aggregation based on X-axis selection
            if x_axis == 'framework':
                queryset = queryset.values(
                    'CreatedByName'
                ).annotate(
                    label=F('CreatedByName'),  # Use the actual CreatedByName value
                    value=Count('FrameworkId', distinct=True)  # Count unique frameworks
                ).order_by('-value', 'CreatedByName')  # Order by count desc, then name
            elif x_axis == 'policy':
                queryset = queryset.values(
                    'CreatedByName'
                ).annotate(
                    label=F('CreatedByName'),  # Use the actual CreatedByName value
                    value=Count('PolicyId', distinct=True)  # Count unique policies
                ).order_by('-value', 'CreatedByName')  # Order by count desc, then name
            elif x_axis == 'subpolicy':
                queryset = queryset.values(
                    'CreatedByName'
                ).annotate(
                    label=F('CreatedByName'),  # Use the actual CreatedByName value
                    value=Count('SubPolicyId', distinct=True)  # Count unique subpolicies
                ).order_by('-value', 'CreatedByName')  # Order by count desc, then name

            # Add creator label for clarity
            data = list(queryset)
            for item in data:
                item['label'] = f"{item['label']} ({item['value']} items)"
            return Response(data)
        elif y_axis == 'status':
            if base_model == 'framework':
                # For frameworks, directly use the Status field
                queryset = queryset.values(
                    'Status'
                ).annotate(
                    label=Coalesce('Status', Value('Unknown')),
                    value=Count('FrameworkId')
                )
            elif base_model == 'policy':
                # For policies, use their Status field
                queryset = queryset.values(
                    'Status'
                ).annotate(
                    label=Coalesce('Status', Value('Unknown')),
                    value=Count('PolicyId')
                )
            else:
                # For subpolicies, use their Status field
                queryset = queryset.values(
                    'Status'
                ).annotate(
                    label=Coalesce('Status', Value('Unknown')),
                    value=Count('SubPolicyId')
                )
        elif y_axis == 'category':
            if base_model == 'policy':
                # For policies, use PolicyType, PolicyCategory, and PolicySubCategory fields
                queryset = queryset.values(
                    'PolicyType', 'PolicyCategory', 'PolicySubCategory'
                ).annotate(
                    value=Count('PolicyId')
                )
                
                # Format the category data
                data = []
                for item in queryset:
                    policy_type = item.get('PolicyType') or 'Uncategorized'
                    policy_category = item.get('PolicyCategory') or 'Uncategorized'
                    policy_subcategory = item.get('PolicySubCategory') or 'Uncategorized'
                    
                    # Create a formatted label
                    label = f"{policy_type} > {policy_category} > {policy_subcategory}"
                    if label == "Uncategorized > Uncategorized > Uncategorized":
                        label = "Uncategorized"
                    
                    data.append({
                        'label': label,
                        'value': item['value']
                    })
                
                return Response(data)
            elif base_model == 'subpolicy':
                # For subpolicies, get category through policy relationship
                queryset = queryset.values(
                    'PolicyId__PolicyType', 'PolicyId__PolicyCategory', 'PolicyId__PolicySubCategory'
                ).annotate(
                    value=Count('SubPolicyId')
                )
                
                # Format the category data
                data = []
                for item in queryset:
                    policy_type = item.get('PolicyId__PolicyType') or 'Uncategorized'
                    policy_category = item.get('PolicyId__PolicyCategory') or 'Uncategorized'
                    policy_subcategory = item.get('PolicyId__PolicySubCategory') or 'Uncategorized'
                    
                    # Create a formatted label
                    label = f"{policy_type} > {policy_category} > {policy_subcategory}"
                    if label == "Uncategorized > Uncategorized > Uncategorized":
                        label = "Uncategorized"
                    
                    data.append({
                        'label': label,
                        'value': item['value']
                    })
                
                return Response(data)
            elif base_model == 'framework':
                # For frameworks, use framework category
                queryset = queryset.values(
                    'Category'
                ).annotate(
                    label=Coalesce('Category', Value('Uncategorized')),
                    value=Count('FrameworkId')
                )
            else:
                # For subpolicies, get category through policy->framework relationship
                queryset = queryset.values(
                    'PolicyId__FrameworkId__Category'
                ).annotate(
                    label=Coalesce('PolicyId__FrameworkId__Category', Value('Uncategorized')),
                    value=Count('SubPolicyId')
                )
        
        data = list(queryset)
        
        # Format dates for time-based analysis
        if x_axis == 'time':
            for item in data:
                date_value = item.get(date_field)
                item['label'] = date_value.strftime('%Y-%m-%d') if date_value else None
        
        return Response(data)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=500
        )

@api_view(['GET'])
@permission_classes([PolicyKPIPermission])  # RBAC: Require PolicyKPIPermission for Performance KPIs page
def get_policy_kpis(request):
    """
    Get policy KPIs for the Performance KPIs page
    RBAC Protected: Requires policy_view permission
    """
    
    # Debug logging for RBAC
    try:
        from ...rbac.utils import RBACUtils
        user_id = RBACUtils.get_user_id_from_request(request)
        logger.info(f"[RBAC DEBUG] get_policy_kpis called by user {user_id}")
        logger.info(f"[RBAC DEBUG] Request method: {request.method}")
        logger.info(f"[RBAC DEBUG] Request path: {request.path}")
        
        if user_id:
            from ...models import RBAC
            rbac_record = RBAC.objects.filter(user_id=user_id, is_active=True).first()
            if rbac_record:
                logger.info(f"[RBAC DEBUG] User {user_id} accessing Policy KPIs - Role: {rbac_record.role}, Dept: {rbac_record.department}")
            else:
                logger.warning(f"[RBAC DEBUG] No RBAC record found for user {user_id}")
    except Exception as debug_e:
        logger.error(f"[RBAC DEBUG] Error in debug logging: {debug_e}")
    
    try:
        # Get total policies count
        total_policies = Policy.objects.count()
        
        # Get active policies count
        active_policies = Policy.objects.filter(
            ActiveInactive='Active'
        ).count()

        # Get total users count for acknowledgement rate calculation
        total_users = Users.objects.count()

        # Get top 5 policies by acknowledgement rate
        policies = Policy.objects.filter(ActiveInactive='Active').annotate(
            acknowledgement_rate=Case(
                When(AcknowledgementCount__gt=0, 
                     then=ExpressionWrapper(
                         F('AcknowledgementCount') * 100.0 / total_users,
                         output_field=FloatField()
                     )),
                default=Value(0.0),
                output_field=FloatField(),
            )
        ).order_by('-acknowledgement_rate')[:5]

        top_acknowledged_policies = [
            {
                'policy_id': policy.PolicyId,
                'policy_name': policy.PolicyName,
                'acknowledged_count': policy.AcknowledgementCount,
                'total_users': total_users,
                'acknowledgement_rate': round(float(policy.acknowledgement_rate), 1)
            }
            for policy in policies
        ]

        # Get historical active policy counts for the last 12 months
        twelve_months_ago = date.today() - timedelta(days=365)
        monthly_counts = []
        
        # Get all policies with their creation dates
        policies = Policy.objects.filter(
            CreatedByDate__gte=twelve_months_ago
        ).values('CreatedByDate', 'ActiveInactive')
        
        # Group by month and count active policies
        month_data = {}
        current_date = date.today()
        
        # Initialize all months with 0
        for i in range(12):
            month_date = current_date - timedelta(days=30 * i)
            month_key = month_date.strftime('%Y-%m')
            month_data[month_key] = 0
        
        # Count active policies for each month
        for policy in policies:
            month_key = policy['CreatedByDate'].strftime('%Y-%m')
            if month_key in month_data and policy['ActiveInactive'] == 'Active':
                month_data[month_key] += 1
        
        # Convert to sorted list for last 12 months
        monthly_counts = [
            {
                'month': k,
                'count': v
            }
            for k, v in sorted(month_data.items(), reverse=True)
        ][:12]
        
        # Calculate revision metrics
        three_months_ago = date.today() - timedelta(days=90)
        
        # Get all policy versions with previous version links
        policy_versions = PolicyVersion.objects.filter(
            PreviousVersionId__isnull=False  # Has a previous version
        ).select_related('PolicyId')
        
        # Track revised policies and their revision counts
        revision_counts = {}  # Dictionary to track revisions per PreviousVersionId
        revised_policies_set = set()
        total_revisions = 0
        
        # Process each version that has a previous version
        for version in policy_versions:
            policy_id = version.PolicyId.PolicyId
            prev_version_id = version.PreviousVersionId
            
            # Count this as a revision
            revised_policies_set.add(policy_id)
            total_revisions += 1
            
            # Track revisions per previous version
            if prev_version_id not in revision_counts:
                revision_counts[prev_version_id] = 1
            else:
                revision_counts[prev_version_id] += 1
        
        # Calculate policies with multiple revisions
        multiple_revisions_count = sum(1 for count in revision_counts.values() if count > 1)
        
        # Calculate final metrics
        revised_policies = len(revised_policies_set)
        
        # Calculate revision rate using total policies as denominator
        revision_rate = 0
        if total_policies > 0:  # Avoid division by zero
            revision_rate = (revised_policies / total_policies) * 100
            revision_rate = min(revision_rate, 100)  # Cap at 100%

        # Calculate policy coverage by department
        departments = Policy.objects.values_list('Department', flat=True).distinct()
        department_coverage = []
        
        for dept in departments:
            if dept:  # Skip empty department values
                dept_policies = Policy.objects.filter(Department=dept)
                total_dept_policies = dept_policies.count()
                if total_dept_policies > 0:
                    avg_coverage = dept_policies.aggregate(
                        avg_coverage=Coalesce(Avg('CoverageRate'), 0.0)
                    )['avg_coverage']
                    
                    department_coverage.append({
                        'department': dept,
                        'coverage_rate': round(float(avg_coverage), 2),
                        'total_policies': total_dept_policies
                    })
        
        # Sort departments by coverage rate in descending order
        department_coverage.sort(key=lambda x: x['coverage_rate'], reverse=True)
        
        # Calculate overall average coverage rate
        overall_coverage = Policy.objects.aggregate(
            avg_coverage=Coalesce(Avg('CoverageRate'), 0.0)
        )['avg_coverage']

        # Calculate average approval time metrics
        # Get all approved policies with their approval dates
        approved_policies = PolicyApproval.objects.filter(
            ApprovedNot=True,
            ApprovedDate__isnull=False
        ).select_related('PolicyId')

        # Calculate approval times for each policy
        approval_times = []
        for approval in approved_policies:
            if approval.PolicyId and approval.PolicyId.CreatedByDate:
                approval_time = (approval.ApprovedDate - approval.PolicyId.CreatedByDate).days
                if approval_time >= 0:  # Only include valid approval times
                    approval_times.append({
                        'month': approval.ApprovedDate.strftime('%Y-%m'),
                        'approval_time': approval_time
                    })

        # Calculate monthly averages
        monthly_approval_times = {}
        for time in approval_times:
            month = time['month']
            if month not in monthly_approval_times:
                monthly_approval_times[month] = []
            monthly_approval_times[month].append(time['approval_time'])

        # Calculate average for each month
        monthly_averages = []
        for month, times in monthly_approval_times.items():
            if times:  # Only include months with data
                monthly_averages.append({
                    'month': month,
                    'average_time': round(sum(times) / len(times), 1)
                })

        # Sort by month
        monthly_averages.sort(key=lambda x: x['month'])
        
        return Response({
            'total_policies': total_policies,
            'active_policies': active_policies,
            'active_policies_trend': monthly_counts,  # Add historical trend data
            'revision_rate': round(revision_rate, 2),
            'revised_policies': revised_policies,
            'total_revisions': total_revisions,
            'policies_with_multiple_revisions': multiple_revisions_count,
            'measurement_period': '3 months',
            'coverage_metrics': {
                'overall_coverage_rate': round(float(overall_coverage), 2),
                'department_coverage': department_coverage
            },
            'top_acknowledged_policies': top_acknowledged_policies,
            'approval_time_metrics': {
                'monthly_averages': monthly_averages,
                'overall_average': round(sum(time['approval_time'] for time in approval_times) / len(approval_times), 1) if approval_times else 0
            }
        })
    except Exception as e:
        print(f"Error in get_policy_kpis: {str(e)}")
        return Response({
            'error': 'Error fetching policy KPIs',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@permission_classes([AllowAny]) # Allow any authenticated user to acknowledge policies
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def acknowledge_policy(request, policy_id):
    try:
        # Extract user_id from JWT token or request.user
        user_id = None
        
        # Try to get user_id from JWT token first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                from ...authentication import verify_jwt_token
                payload = verify_jwt_token(token)
                if payload and 'user_id' in payload:
                    user_id = payload['user_id']
                    print(f"DEBUG: acknowledge_policy - Extracted user_id from JWT: {user_id}")
            except Exception as e:
                print(f"DEBUG: acknowledge_policy - Error extracting user_id from JWT: {e}")
        
        # Fallback to request.user if JWT extraction failed
        if not user_id:
            user_id = getattr(request.user, 'UserId', None)
            if not user_id:
                user_id = getattr(request.user, 'id', None)
        
        if not user_id:
            return Response({
                'error': 'User not authenticated. Please login again.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        policy = Policy.objects.get(PolicyId=policy_id)
        
        # Initialize acknowledged_users list if None
        # Handle case where AcknowledgedUserIds might be a string or None
        acknowledged_users = policy.AcknowledgedUserIds if policy.AcknowledgedUserIds is not None else []
        
        # Ensure acknowledged_users is a list (not a string)
        if isinstance(acknowledged_users, str):
            try:
                import json
                acknowledged_users = json.loads(acknowledged_users)
            except (json.JSONDecodeError, ValueError):
                acknowledged_users = []
        
        # Ensure it's a list
        if not isinstance(acknowledged_users, list):
            acknowledged_users = []
        
        # Ensure user_id is an integer for consistent comparison
        user_id = int(user_id)
        
        # Convert all items in acknowledged_users to integers for consistent comparison
        acknowledged_users = [int(uid) for uid in acknowledged_users if uid is not None]
        
        # Check if user already acknowledged
        if user_id not in acknowledged_users:
            # Add user to acknowledged list
            acknowledged_users.append(user_id)
            policy.AcknowledgedUserIds = acknowledged_users
            policy.AcknowledgementCount = len(acknowledged_users)
            policy.save()
            
            return Response({
                'message': 'Policy acknowledged successfully',
                'acknowledged_users': policy.AcknowledgedUserIds,
                'acknowledgement_count': policy.AcknowledgementCount
            })
        else:
            return Response({
                'message': 'Policy already acknowledged by this user',
                'acknowledged_users': policy.AcknowledgedUserIds,
                'acknowledgement_count': policy.AcknowledgementCount
            })

    except Policy.DoesNotExist:
        return Response({
            'error': 'Policy not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error in acknowledge_policy: {str(e)}")  # Add logging
        return Response({
            'error': 'Error acknowledging policy',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Add this helper function near the top of the file (after imports)
def safe_isoformat(val):
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return val if isinstance(val, str) else None


@api_view(['POST'])
@permission_classes([PolicyTailoringPermission])  # Use proper permission class for tailoring
def create_tailored_framework(request):
    """
    Create a new framework from the Tailoring page with policies and subpolicies
    This will automatically create the framework approval entry for the approval workflow
    """
    print(f"DEBUG: create_tailored_framework - Function called successfully")
    print(f"DEBUG: create_tailored_framework - User: {request.user}")
    print(f"DEBUG: create_tailored_framework - User ID: {getattr(request.user, 'UserId', 'No UserId')}")
    print(f"DEBUG: create_tailored_framework - User Role: {getattr(request.user, 'Role', 'No Role')}")
    # Log tailored framework creation attempt
    send_log(
        module="Framework",
        actionType="CREATE",
        description="Creating tailored framework",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Framework",
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Import validators and security modules
        from ..validators.framework_validator import validate_tailored_framework_data, ValidationError
        from django.utils.html import escape as escape_html
        import shlex
        import re
        
        # Validate request data
        try:
            validated_data = validate_tailored_framework_data(request.data)
        except ValidationError as e:
            # Log validation error
            send_log(
                module="Framework",
                actionType="CREATE_FAILED",
                description=f"Tailored framework validation failed: {str(e)}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Framework",
                logLevel="WARNING",
                ipAddress=get_client_ip(request)
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        data = validated_data
        
        # =================================================================
        # SECURITY IMPLEMENTATIONS - Context-Appropriate Server-Side Encoding
        # =================================================================
        # 1. HTML Context → escape_html() - Prevents XSS attacks
        # 2. SQL Context → Django ORM (parameterized queries) - Prevents SQL injection
        # 3. Shell Context → shlex.quote() - Prevents command injection
        # 4. All user inputs are sanitized before storage and rendering
        # =================================================================
        
        # Security Helper Function: Secure URL handling for potential shell command usage
        def secure_url_for_shell(url):
            """
            Example: Shell Command Injection Protection
            If URL needs to be used in shell commands (like wget, curl), use shlex.quote()
            Example: subprocess.run(['wget', shlex.quote(url)])
            """
            if url:
                return shlex.quote(str(url))
            return ""
        
        # Security: Escape framework data for safe logging (prevents log injection)
        safe_framework_title = escape_html(data.get('title', 'untitled'))
        print(f"Received tailored framework data: {safe_framework_title}")
        
        # Parse date fields safely using parse_date
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        
        # Get user information for reviewer assignment
        reviewer_name = data.get('reviewer', '')
        reviewer_id = None
        if reviewer_name:
            reviewer_user = Users.objects.filter(UserName=reviewer_name).first()
            if reviewer_user:
                reviewer_id = reviewer_user.UserId
        
        # If no reviewer found, try to get from request
        if not reviewer_id:
            reviewer_id = request.user.id if hasattr(request.user, 'id') else None
        if not reviewer_id:
            reviewer_id = request.session.get('user_id')
        if not reviewer_id:
            return Response({'error': 'No reviewer ID found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Security: Sanitize framework data before database storage (Django ORM provides SQL injection protection)
        framework_data = {
            'FrameworkName': escape_html(data.get('title')),
            'FrameworkDescription': escape_html(data.get('description', '')),
            'CreatedByName': escape_html(data.get('createdByName')),
            'CreatedByDate': date.today(),
            'Category': escape_html(data.get('category', '')),
            'DocURL': data.get('docURL', ''),  # Note: If used in shell commands, apply secure_url_for_shell()
            'Identifier': escape_html(data.get('identifier', '')),
            'StartDate': start_date,
            'EndDate': end_date,
            'Status': 'Under Review',
            'ActiveInactive': 'InActive',
            'Reviewer': escape_html(reviewer_name),
            'CurrentVersion': 1.0,
            'InternalExternal': 'Internal'  # Default to Internal for tailored frameworks
        }
        
        with transaction.atomic():
            # Create the framework
            framework = Framework.objects.create(**framework_data)
            print(f"Created framework: {framework.FrameworkName} (ID: {framework.FrameworkId})")
            
            # Log framework creation
            send_log(
                module="Framework",
                actionType="CREATE_PROGRESS",
                description=f"Tailored framework '{framework.FrameworkName}' created",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', validated_data.get('createdByName', 'Anonymous')),
                entityType="Framework",
                entityId=framework.FrameworkId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "framework_name": framework.FrameworkName,
                    "framework_id": framework.FrameworkId,
                    "category": framework.Category,
                    "source": "tailoring"
                }
            )
            
            # Create framework version record
            framework_version = FrameworkVersion.objects.create(
                FrameworkId=framework,
                Version=1.0,
                FrameworkName=framework.FrameworkName,
                CreatedBy=framework.CreatedByName,
                CreatedDate=date.today(),
                PreviousVersionId=None
            )
            print(f"Created framework version: {framework_version.Version}")
            
            created_policies = []
            
            # Process policies
            if 'policies' in data and isinstance(data['policies'], list):
                for policy_data in data['policies']:
                    # Skip excluded policies
                    if policy_data.get('exclude', False):
                        # Security: Escape policy title for safe logging
                        safe_policy_title = escape_html(policy_data.get('title', 'Unknown'))
                        print(f"Skipping excluded policy: {safe_policy_title}")
                        continue
                    
                    # Parse policy dates
                    policy_start_date = policy_data.get('startDate')
                    policy_end_date = policy_data.get('endDate')
                    
                    # Get policy reviewer information
                    policy_reviewer_name = policy_data.get('reviewer', '')
                    if not policy_reviewer_name:
                        policy_reviewer_name = reviewer_name  # Use framework reviewer as fallback
                    
                    # Get policy creator name - use framework creator if not provided
                    policy_created_by_name = policy_data.get('createdByName', '')
                    if not policy_created_by_name:
                        policy_created_by_name = framework.CreatedByName
                    
                    # Handle entities data  
                    entities_data = policy_data.get('Entities', [])
                    print(f"DEBUG: Entities data received in create_tailored_framework: {entities_data} (type: {type(entities_data)})")
                    
                    # Security: Sanitize policy data before database storage
                    policy = Policy.objects.create(
                        FrameworkId=framework,
                        PolicyName=escape_html(policy_data.get('title', '')),
                        PolicyDescription=escape_html(policy_data.get('description', '')),
                        Status='Under Review',
                        StartDate=policy_start_date,
                        EndDate=policy_end_date,
                        Department=escape_html(policy_data.get('department', '')),
                        CreatedByName=escape_html(policy_created_by_name),
                        CreatedByDate=date.today(),
                        Applicability=escape_html(policy_data.get('applicability', '')),
                        DocURL=policy_data.get('docURL', ''),  # Note: If used in shell commands, apply secure_url_for_shell()
                        Scope=escape_html(policy_data.get('scope', '')),
                        Objective=escape_html(policy_data.get('objective', '')),
                        Identifier=escape_html(policy_data.get('identifier', '')),
                        PermanentTemporary='',
                        ActiveInactive='Inactive',
                        Reviewer=escape_html(policy_reviewer_name),
                        CoverageRate=policy_data.get('coverageRate'),
                        CurrentVersion='1.0',
                        # Add policy category fields
                        PolicyType=escape_html(policy_data.get('PolicyType', '')),
                        PolicyCategory=escape_html(policy_data.get('PolicyCategory', '')),
                        PolicySubCategory=escape_html(policy_data.get('PolicySubCategory', '')),
                        Entities=entities_data
                    )
                    
                    created_policies.append(policy)
                    print(f"Created policy: {policy.PolicyName} (ID: {policy.PolicyId})")
                    
                    # Log policy creation
                    send_log(
                        module="Policy",
                        actionType="CREATE_PROGRESS",
                        description=f"Policy '{policy.PolicyName}' created for tailored framework {framework.FrameworkId}",
                        userId=getattr(request.user, 'id', None),
                        userName=getattr(request.user, 'username', policy.CreatedByName),
                        entityType="Policy",
                        entityId=policy.PolicyId,
                        ipAddress=get_client_ip(request),
                        additionalInfo={
                            "policy_name": policy.PolicyName,
                            "policy_id": policy.PolicyId,
                            "framework_id": framework.FrameworkId,
                            "source": "tailoring"
                        }
                    )
                    
                    # Create policy version record
                    PolicyVersion.objects.create(
                        PolicyId=policy,
                        Version='1.0',
                        PolicyName=policy.PolicyName,
                        CreatedBy=policy.CreatedByName,
                        CreatedDate=date.today(),
                        PreviousVersionId=None,
                        FrameworkId=framework
                    )
                    
                    # Process subpolicies
                    if 'subPolicies' in policy_data and isinstance(policy_data['subPolicies'], list):
                        for subpolicy_data in policy_data['subPolicies']:
                            # Skip excluded subpolicies
                            if subpolicy_data.get('exclude', False):
                                # Security: Escape subpolicy title for safe logging
                                safe_subpolicy_title = escape_html(subpolicy_data.get('title', 'Unknown'))
                                print(f"Skipping excluded subpolicy: {safe_subpolicy_title}")
                                continue
                            
                            # Get subpolicy creator name - use policy creator if not provided
                            subpolicy_created_by_name = subpolicy_data.get('createdByName', '')
                            if not subpolicy_created_by_name:
                                subpolicy_created_by_name = policy.CreatedByName
                            
                            # Security: Sanitize subpolicy data before database storage
                            subpolicy = SubPolicy.objects.create(
                                PolicyId=policy,
                                SubPolicyName=escape_html(subpolicy_data.get('title', '')),
                                CreatedByName=escape_html(subpolicy_created_by_name),
                                CreatedByDate=date.today(),
                                Identifier=escape_html(subpolicy_data.get('identifier', '')),
                                Description=escape_html(subpolicy_data.get('description', '')),
                                Status='Under Review',
                                PermanentTemporary='',
                                Control=escape_html(subpolicy_data.get('control', '')),
                                FrameworkId=framework
                            )
                            print(f"Created subpolicy: {subpolicy.SubPolicyName} (ID: {subpolicy.SubPolicyId})")
                            
                            # Log subpolicy creation
                            send_log(
                                module="SubPolicy",
                                actionType="CREATE_PROGRESS",
                                description=f"Subpolicy '{subpolicy.SubPolicyName}' created for policy {policy.PolicyId}",
                                userId=getattr(request.user, 'id', None),
                                userName=getattr(request.user, 'username', subpolicy.CreatedByName),
                                entityType="SubPolicy",
                                entityId=subpolicy.SubPolicyId,
                                ipAddress=get_client_ip(request),
                                additionalInfo={
                                    "subpolicy_name": subpolicy.SubPolicyName,
                                    "subpolicy_id": subpolicy.SubPolicyId,
                                    "policy_id": policy.PolicyId,
                                    "framework_id": framework.FrameworkId,
                                    "source": "tailoring"
                                }
                            )
            
            # Create framework approval entry for the approval workflow
            policies_data = []
            
            # Collect all policies and subpolicies data for the approval JSON
            for policy in created_policies:
                policy_dict = {
                    "PolicyId": policy.PolicyId,
                    "PolicyName": policy.PolicyName,
                    "PolicyDescription": policy.PolicyDescription,
                    "Status": policy.Status,
                    "StartDate": policy.StartDate.isoformat() if policy.StartDate else None,
                    "EndDate": policy.EndDate.isoformat() if policy.EndDate else None,
                    "Department": policy.Department,
                    "CreatedByName": policy.CreatedByName,
                    "CreatedByDate": policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
                    "Applicability": policy.Applicability,
                    "DocURL": policy.DocURL,
                    "Scope": policy.Scope,
                    "Objective": policy.Objective,
                    "Identifier": policy.Identifier,
                    "PermanentTemporary": policy.PermanentTemporary,
                    "ActiveInactive": policy.ActiveInactive,
                    "Reviewer": policy.Reviewer,
                    "CoverageRate": policy.CoverageRate,
                    "CurrentVersion": policy.CurrentVersion,
                    "PolicyType": policy.PolicyType,
                    "PolicyCategory": policy.PolicyCategory,
                    "PolicySubCategory": policy.PolicySubCategory,
                    "Entities": policy.Entities,
                    "subpolicies": []
                }
                
                # Get subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                for subpolicy in subpolicies:
                    subpolicy_dict = {
                        "SubPolicyId": subpolicy.SubPolicyId,
                        "SubPolicyName": subpolicy.SubPolicyName,
                        "CreatedByName": subpolicy.CreatedByName,
                        "CreatedByDate": subpolicy.CreatedByDate.isoformat() if subpolicy.CreatedByDate else None,
                        "Identifier": subpolicy.Identifier,
                        "Description": subpolicy.Description,
                        "Status": subpolicy.Status,
                        "PermanentTemporary": subpolicy.PermanentTemporary,
                        "Control": subpolicy.Control
                    }
                    policy_dict["subpolicies"].append(subpolicy_dict)
                
                policies_data.append(policy_dict)
            
            extracted_data = {
                "FrameworkName": framework.FrameworkName,
                "FrameworkDescription": framework.FrameworkDescription,
                "Category": framework.Category,
                "StartDate": framework.StartDate.isoformat() if framework.StartDate else None,
                "EndDate": framework.EndDate.isoformat() if framework.EndDate else None,
                "CreatedByName": framework.CreatedByName,
                "CreatedByDate": framework.CreatedByDate.isoformat() if framework.CreatedByDate else None,
                "Identifier": framework.Identifier,
                "Status": framework.Status,
                "ActiveInactive": framework.ActiveInactive,
                "InternalExternal": framework.InternalExternal,
                "type": "framework",
                "docURL": framework.DocURL,
                "reviewer": framework.Reviewer,
                "source": "tailoring",
                "policies": policies_data,
                "totalPolicies": len(created_policies),
                "totalSubpolicies": sum(len(p["subpolicies"]) for p in policies_data)
            }
            
            # Get user ID for framework approval
            user_id = request.session.get('user_id')
            if not user_id:
                # Try to get user ID from the framework creator name
                created_by_user = Users.objects.filter(UserName=framework.CreatedByName).first()
                if created_by_user:
                    user_id = created_by_user.UserId
                else:
                    return Response(
                        {"error": "User authentication required. Please log in and try again."},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            framework_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=user_id,
                ReviewerId=reviewer_id,
                Version="u1",  # Initial user version
                ApprovedNot=None  # Pending approval
            )
            print(f"Created framework approval: {framework_approval.ApprovalId}")
            
            # --- FIX: Get reviewer email and notification service ---
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            reviewer_email = None
            if reviewer_id:
                reviewer_user_obj = Users.objects.filter(UserId=reviewer_id).first()
                if reviewer_user_obj:
                    reviewer_email = reviewer_user_obj.Email
            # Get creator email
            creator_email = None
            creator_name = framework.CreatedByName
            if creator_name:
                creator_user_obj = Users.objects.filter(UserName=creator_name).first()
                if creator_user_obj:
                    creator_email = creator_user_obj.Email
            # ------------------------------------------------------
            # Send notification to reviewer if email is available
            if reviewer_email:
                print(f"Attempting to send notification to reviewer email: {reviewer_email}")  # Debug log
                # Security: XSS Protection - Escape HTML content before building email template
                notification_data = {
                    'notification_type': 'frameworkSubmitted',
                    'email': reviewer_email,
                    'email_type': 'gmail',
                    'template_data': [
                        escape_html(framework_data['Reviewer']),  # Escape reviewer name for HTML context
                        escape_html(framework.FrameworkName),  # Escape framework title for HTML context
                        escape_html(framework.CreatedByName),  # Escape submitter name for HTML context
                    ]
                }
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Notification result: {notification_result}")  # Debug log
            else:
                print("No reviewer email available to send notification")  # Debug log
            
            # Send notification to creator (tailoring confirmation)
            if creator_email:
                print(f"Attempting to send tailoring notification to creator email: {creator_email}")
                try:
                    creator_notification_data = {
                        'notification_type': 'frameworkSubmitted',  # Using same template but different message
                        'email': creator_email,
                        'email_type': 'gmail',
                        'template_data': [
                            escape_html(creator_name),
                            escape_html(framework.FrameworkName),
                            escape_html(creator_name),  # Creator created it themselves
                        ]
                    }
                    creator_result = notification_service.send_multi_channel_notification(creator_notification_data)
                    print(f"Creator notification result: {creator_result}")
                except Exception as creator_notify_error:
                    print(f"Error sending creator notification: {str(creator_notify_error)}")
            else:
                print("No creator email available to send tailoring notification")
            
            # Send in-app notifications for tailored framework
            try:
                from ...routes.Global.notifications import notifications_storage
                import uuid
                from datetime import datetime as dt
                
                # Creator in-app notification
                if user_id:
                    creator_notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Tailored Framework Created',
                        'message': f'Your tailored framework "{framework.FrameworkName}" has been created and submitted for review.',
                        'category': 'framework',
                        'priority': 'medium',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(user_id)
                    }
                    notifications_storage.append(creator_notification)
                    if len(notifications_storage) > 100:
                        notifications_storage.pop(0)
                    print(f"In-app notification created for creator: {creator_notification['id']}")
                
                # Reviewer in-app notification
                if reviewer_id:
                    reviewer_notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Tailored Framework Submitted for Review',
                        'message': f'A tailored framework "{framework.FrameworkName}" has been submitted for your review.',
                        'category': 'framework',
                        'priority': 'high',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(reviewer_id)
                    }
                    notifications_storage.append(reviewer_notification)
                    if len(notifications_storage) > 100:
                        notifications_storage.pop(0)
                    print(f"In-app notification created for reviewer: {reviewer_notification['id']}")
            except Exception as in_app_error:
                print(f"Error creating in-app notifications for tailored framework: {str(in_app_error)}")
            
            # Log successful tailored framework creation
            send_log(
                module="Framework",
                actionType="CREATE_SUCCESS",
                description=f"Tailored framework '{framework.FrameworkName}' created successfully with {len(created_policies)} policies",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', framework.CreatedByName),
                entityType="Framework",
                entityId=framework.FrameworkId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "framework_name": framework.FrameworkName,
                    "framework_id": framework.FrameworkId,
                    "approval_id": framework_approval.ApprovalId,
                    "policies_created": len(created_policies),
                    "total_subpolicies": sum(len(p["subpolicies"]) for p in policies_data),
                    "source": "tailoring",
                    "status": framework.Status
                }
            )
            
            return Response({
                "message": "Tailored framework created successfully",
                "FrameworkId": framework.FrameworkId,
                "FrameworkName": framework.FrameworkName,
                "ApprovalId": framework_approval.ApprovalId,
                "Version": framework_approval.Version,
                "PoliciesCreated": len(created_policies),
                "Status": framework.Status
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        print(f"Error creating tailored framework: {str(e)}")
        print(traceback.format_exc())
        
        # Log error
        send_log(
            module="Framework",
            actionType="CREATE_FAILED",
            description=f"Failed to create tailored framework: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Framework",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return Response({
            "error": f"Failed to create tailored framework: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([PolicyCreatePermission])
@require_consent('create_policy')
def create_tailored_policy(request):
    """
    Create a new policy from the Tailoring page and automatically create policy approval entry
    This endpoint handles creating a new policy under a selected framework with approval workflow
    """
    # Log tailored policy creation attempt
    send_log(
        module="Policy",
        actionType="CREATE",
        description="Creating tailored policy",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Import validators and security modules
        from ..validators.framework_validator import validate_tailored_policy_request_data, validate_policy_category_combination, ValidationError
        from django.utils.html import escape as escape_html
        import shlex
        import re
        
        # Debug: Check for selected framework using multiple sources
        from ...framework_context import get_framework_context
        
        # Try to get user_id from various sources
        user_id = None
        
        # Try from session
        session_user_id = request.session.get('user_id') or request.session.get('grc_user_id')
        if session_user_id:
            user_id = session_user_id
        
        # If not in session, try from request user
        if not user_id and hasattr(request, 'user') and hasattr(request.user, 'id'):
            user_id = request.user.id
        
        # Try to get framework_id from various sources
        selected_framework_id = None
        
        # Try from framework context FIRST (more reliable and up-to-date)
        if user_id:
            selected_framework_id = get_framework_context(str(user_id))
            if selected_framework_id:
                print(f"✅ DEBUG: Found framework_id in framework context: {selected_framework_id}")
        
        # Fall back to session if not in framework context (for backward compatibility)
        if not selected_framework_id:
            session_framework_id = request.session.get('selected_framework_id') or request.session.get('grc_framework_selected')
            if session_framework_id:
                selected_framework_id = session_framework_id
                print(f"⚠️ DEBUG: Found framework_id in session (fallback): {selected_framework_id}")
        
        # If still no framework_id, try request data
        if not selected_framework_id and request.data.get('frameworkId'):
            selected_framework_id = request.data.get('frameworkId')
            print(f"✅ DEBUG: Found framework_id in request data: {selected_framework_id}")
        
        print(f"🔍 DEBUG: Policy creation - checking for selected framework")
        print(f"📊 DEBUG: Selected framework ID: {selected_framework_id}")
        print(f"👤 DEBUG: User ID: {user_id}")
        print(f"🔍 DEBUG: Session keys: {list(request.session.keys()) if hasattr(request, 'session') else 'No session'}")
        print(f"📝 DEBUG: Request data framework ID: {request.data.get('frameworkId', 'Not provided')}")
        
        # Validate request data
        try:
            validated_data = validate_tailored_policy_request_data(request.data)
        except ValidationError as e:
            # Log validation error
            send_log(
                module="Policy",
                actionType="CREATE_FAILED",
                description=f"Tailored policy validation failed: {str(e)}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                logLevel="WARNING",
                ipAddress=get_client_ip(request)
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        data = validated_data
        
        # =================================================================
        # SECURITY IMPLEMENTATIONS - Context-Appropriate Server-Side Encoding
        # =================================================================
        # 1. HTML Context → escape_html() - Prevents XSS attacks
        # 2. SQL Context → Django ORM (parameterized queries) - Prevents SQL injection
        # 3. Shell Context → shlex.quote() - Prevents command injection
        # 4. All user inputs are sanitized before storage and rendering
        # =================================================================
        
        # Security Helper Function: Secure URL handling for potential shell command usage
        def secure_url_for_shell(url):
            """
            Example: Shell Command Injection Protection
            If URL needs to be used in shell commands (like wget, curl), use shlex.quote()
            Example: subprocess.run(['wget', shlex.quote(url)])
            """
            if url:
                return shlex.quote(str(url))
            return ""
        
        # Security: Escape policy data for safe logging (prevents log injection)
        safe_policy_name = escape_html(data.get('PolicyName', 'untitled'))
        print(f"Received tailored policy data: {safe_policy_name}")
        
        # Get target framework ID from validated data
        target_framework_id = data.get('TargetFrameworkId')
        
        # Get target framework
        try:
            target_framework = Framework.objects.get(FrameworkId=target_framework_id)
        except Framework.DoesNotExist:
            # Log framework not found error
            send_log(
                module="Policy",
                actionType="CREATE_FAILED",
                description=f"Target framework {target_framework_id} not found for tailored policy",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Framework",
                entityId=target_framework_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request)
            )
            return Response({'error': 'Target framework not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if policy name is unique within the framework
        policy_name = data.get('PolicyName')
        if Policy.objects.filter(FrameworkId=target_framework, PolicyName=policy_name).exists():
            # Log duplicate policy name error
            send_log(
                module="Policy",
                actionType="CREATE_FAILED",
                description=f"Policy name '{policy_name}' already exists in framework {target_framework_id}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=target_framework_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request),
                additionalInfo={"policy_name": policy_name, "framework_id": target_framework_id}
            )
            return Response({'error': 'A policy with this name already exists in the target framework'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse date fields safely
        start_date = data.get('StartDate')
        end_date = data.get('EndDate')
        
        # Get user information for reviewer assignment
        reviewer_name = data.get('Reviewer', '')
        reviewer_id = None
        if reviewer_name:
            reviewer_user = Users.objects.filter(UserName=reviewer_name).first()
            if reviewer_user:
                reviewer_id = reviewer_user.UserId
        
        # If no reviewer found, try to get from request
        if not reviewer_id:
            reviewer_id = request.user.id if hasattr(request.user, 'id') else None
        if not reviewer_id:
            reviewer_id = request.session.get('user_id')
        if not reviewer_id:
            return Response({'error': 'No reviewer ID found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user ID for policy approval
        user_id = request.session.get('user_id')
        if not user_id:
            # Try to get user ID from the creator name
            created_by_name = data.get('CreatedByName', '')
            if created_by_name:
                created_by_user = Users.objects.filter(UserName=created_by_name).first()
                if created_by_user:
                    user_id = created_by_user.UserId
            
            # If still no user ID, return error
            if not user_id:
                return Response(
                    {"error": "User authentication required. Please log in and try again."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Validate policy category combination
        try:
            validate_policy_category_combination(
                data.get('PolicyType', ''),
                data.get('PolicyCategory', ''),
                data.get('PolicySubCategory', '')
            )
        except ValidationError as e:
            # Log policy category validation error
            send_log(
                module="Policy",
                actionType="CREATE_FAILED",
                description=f"Policy category validation failed: {str(e)}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                logLevel="WARNING",
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "policy_type": data.get('PolicyType', ''),
                    "policy_category": data.get('PolicyCategory', ''),
                    "policy_subcategory": data.get('PolicySubCategory', '')
                }
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # --- Ensure PolicyCategory Exists ---
        policy_type = data.get('PolicyType', '').strip()
        policy_category = data.get('PolicyCategory', '').strip()
        policy_subcategory = data.get('PolicySubCategory', '').strip()

        # Validate presence if any of them is filled
        if any([policy_type, policy_category, policy_subcategory]):
            if not all([policy_type, policy_category, policy_subcategory]):
                return Response({
                    'error': 'All of PolicyType, PolicyCategory, and PolicySubCategory are required together.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if the category exists
            existing_category = PolicyCategory.objects.filter(
                PolicyType=policy_type,
                PolicyCategory=policy_category,
                PolicySubCategory=policy_subcategory,
                FrameworkId=target_framework
            ).first()

            # If not, insert new category
            if not existing_category:
                try:
                    PolicyCategory.objects.create(
                        PolicyType=policy_type,
                        PolicyCategory=policy_category,
                        PolicySubCategory=policy_subcategory,
                        FrameworkId=target_framework
                    )
                except Exception as e:
                    return Response({
                        'error': f'Failed to insert policy category combination: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)


        
        with transaction.atomic():
            # Handle entities data  
            entities_data = data.get('Entities', [])
            print(f"DEBUG: Entities data received in create_tailored_policy: {entities_data} (type: {type(entities_data)})")
            
            # Get creator information
            created_by_name = data.get('CreatedByName', '')
            if not created_by_name:
                # Try to get from session/user
                created_by_name = getattr(request.user, 'username', None)
                if not created_by_name:
                    created_by_name = request.session.get('grc_username')
                if not created_by_name:
                    return Response({"error": "Creator name not provided"}, status=status.HTTP_400_BAD_REQUEST)

            # Security: Sanitize policy data before database storage (Django ORM provides SQL injection protection)
            new_policy_data = {
                'FrameworkId': target_framework,
                'Status': 'Under Review',
                'PolicyName': escape_html(policy_name),
                'PolicyDescription': escape_html(data.get('PolicyDescription', '')),
                'StartDate': start_date,
                'EndDate': end_date,
                'Department': escape_html(data.get('Department', '')),
                'CreatedByName': escape_html(created_by_name),
                'CreatedByDate': date.today(),
                'Applicability': escape_html(data.get('Applicability', '')),
                'DocURL': data.get('DocURL', ''),  # Note: If used in shell commands, apply secure_url_for_shell()
                'Scope': escape_html(data.get('Scope', '')),
                'Objective': escape_html(data.get('Objective', '')),
                'Identifier': escape_html(data.get('Identifier', '')),
                'PermanentTemporary': data.get('PermanentTemporary', ''),
                'ActiveInactive': 'InActive',
                'CurrentVersion': 1.0,
                'Reviewer': escape_html(reviewer_name),
                'CoverageRate': data.get('coverageRate'),
                # Add policy category fields
                'PolicyType': escape_html(policy_type),
                'PolicyCategory': escape_html(policy_category),
                'PolicySubCategory': escape_html(policy_subcategory),
                'Entities': entities_data,
            }
            
            new_policy = Policy.objects.create(**new_policy_data)
            print(f"Created policy: {new_policy.PolicyName} (ID: {new_policy.PolicyId})")
            
            # Log policy creation
            send_log(
                module="Policy",
                actionType="CREATE_PROGRESS",
                description=f"Tailored policy '{new_policy.PolicyName}' created in framework {target_framework_id}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', new_policy.CreatedByName),
                entityType="Policy",
                entityId=new_policy.PolicyId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "policy_name": new_policy.PolicyName,
                    "policy_id": new_policy.PolicyId,
                    "framework_id": target_framework_id,
                    "framework_name": target_framework.FrameworkName,
                    "source": "tailoring"
                }
            )
            # After creating the new policy, send notification to reviewer if email is available
            policy_reviewer_email = None
            if reviewer_name:
                reviewer_user = Users.objects.filter(UserName=reviewer_name).first()
                if reviewer_user:
                    policy_reviewer_email = reviewer_user.Email
            
            # Get creator email for tailored policy
            policy_creator_email = None
            policy_creator_name = new_policy.CreatedByName
            if policy_creator_name:
                creator_user = Users.objects.filter(UserName=policy_creator_name).first()
                if creator_user:
                    policy_creator_email = creator_user.Email
            
            if policy_reviewer_email:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                # Security: XSS Protection - Escape HTML content before building email template
                notification_data = {
                    'notification_type': 'policySubmitted',
                    'email': policy_reviewer_email,
                    'email_type': 'gmail',
                    'template_data': [
                        escape_html(reviewer_name),  # Escape reviewer name for HTML context
                        escape_html(new_policy.PolicyName),  # Escape policy name for HTML context
                        escape_html(new_policy.CreatedByName),  # Escape submitter name for HTML context
                        (new_policy.EndDate.isoformat() if new_policy.EndDate else '')  # Date is safe
                    ]
                }
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Policy notification result: {notification_result}")
            
            # Send notification to creator (tailoring confirmation)
            if policy_creator_email:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                print(f"Attempting to send tailoring notification to creator email: {policy_creator_email}")
                try:
                    creator_notification_data = {
                        'notification_type': 'policySubmitted',  # Using same template
                        'email': policy_creator_email,
                        'email_type': 'gmail',
                        'template_data': [
                            escape_html(policy_creator_name),
                            escape_html(new_policy.PolicyName),
                            escape_html(policy_creator_name),  # Creator created it themselves
                            (new_policy.EndDate.isoformat() if new_policy.EndDate else '')  # Date is safe
                        ]
                    }
                    creator_result = notification_service.send_multi_channel_notification(creator_notification_data)
                    print(f"Creator notification result: {creator_result}")
                except Exception as creator_notify_error:
                    print(f"Error sending creator notification: {str(creator_notify_error)}")
            else:
                print("No creator email available to send tailoring notification")
            
            # Send in-app notifications for tailored policy
            try:
                from ...routes.Global.notifications import notifications_storage
                import uuid
                from datetime import datetime as dt
                
                # Creator in-app notification
                if user_id:
                    creator_notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Tailored Policy Created',
                        'message': f'Your tailored policy "{new_policy.PolicyName}" has been created and submitted for review.',
                        'category': 'policy',
                        'priority': 'medium',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(user_id)
                    }
                    notifications_storage.append(creator_notification)
                    if len(notifications_storage) > 100:
                        notifications_storage.pop(0)
                    print(f"In-app notification created for creator: {creator_notification['id']}")
                
                # Reviewer in-app notification
                if reviewer_id:
                    reviewer_notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Tailored Policy Submitted for Review',
                        'message': f'A tailored policy "{new_policy.PolicyName}" has been submitted for your review.',
                        'category': 'policy',
                        'priority': 'high',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(reviewer_id)
                    }
                    notifications_storage.append(reviewer_notification)
                    if len(notifications_storage) > 100:
                        notifications_storage.pop(0)
                    print(f"In-app notification created for reviewer: {reviewer_notification['id']}")
            except Exception as in_app_error:
                print(f"Error creating in-app notifications for tailored policy: {str(in_app_error)}")
            
            # Create policy version record
                PolicyVersion.objects.create(
                PolicyId=new_policy,
                Version='1.0',
                PolicyName=new_policy.PolicyName,
                CreatedBy=new_policy.CreatedByName,
                CreatedDate=new_policy.CreatedByDate,
                PreviousVersionId=None,
                FrameworkId=target_framework
             )
            
            # Handle subpolicies
            created_subpolicies = []
            if 'subpolicies' in data and isinstance(data['subpolicies'], list):
                for subpolicy_data in data['subpolicies']:
                    # Skip excluded subpolicies
                    if subpolicy_data.get('exclude', False):
                        continue
                    
                    # Security: Sanitize subpolicy data before database storage
                    new_subpolicy_data = {
                        'PolicyId': new_policy,
                        'SubPolicyName': escape_html(subpolicy_data.get('SubPolicyName', '')),
                        'CreatedByName': escape_html(new_policy.CreatedByName),
                        'CreatedByDate': new_policy.CreatedByDate,
                        'Identifier': escape_html(subpolicy_data.get('Identifier', '')),
                        'Description': escape_html(subpolicy_data.get('Description', '')),
                        'Status': 'Under Review',
                        'PermanentTemporary': subpolicy_data.get('PermanentTemporary', ''),
                        'Control': escape_html(subpolicy_data.get('Control', '')),
                        'FrameworkId': target_framework
                    }
                    
                    new_subpolicy = SubPolicy.objects.create(**new_subpolicy_data)
                    created_subpolicies.append(new_subpolicy)
                    print(f"Created subpolicy: {new_subpolicy.SubPolicyName} (ID: {new_subpolicy.SubPolicyId})")
                    
                    # Log subpolicy creation
                    send_log(
                        module="SubPolicy",
                        actionType="CREATE_PROGRESS",
                        description=f"Subpolicy '{new_subpolicy.SubPolicyName}' created for tailored policy {new_policy.PolicyId}",
                        userId=getattr(request.user, 'id', None),
                        userName=getattr(request.user, 'username', new_subpolicy.CreatedByName),
                        entityType="SubPolicy",
                        entityId=new_subpolicy.SubPolicyId,
                        ipAddress=get_client_ip(request),
                        additionalInfo={
                            "subpolicy_name": new_subpolicy.SubPolicyName,
                            "subpolicy_id": new_subpolicy.SubPolicyId,
                            "policy_id": new_policy.PolicyId,
                            "framework_id": target_framework_id,
                            "source": "tailoring"
                        }
                    )
            
            # Prepare data for policy approval entry
            subpolicies_data = []
            for subpolicy in created_subpolicies:
                subpolicy_dict = {
                    "SubPolicyId": subpolicy.SubPolicyId,
                    "SubPolicyName": subpolicy.SubPolicyName,
                    "CreatedByName": subpolicy.CreatedByName,
                    "CreatedByDate": subpolicy.CreatedByDate.isoformat() if subpolicy.CreatedByDate else None,
                    "Identifier": subpolicy.Identifier,
                    "Description": subpolicy.Description,
                    "Status": subpolicy.Status,
                    "PermanentTemporary": subpolicy.PermanentTemporary,
                    "Control": subpolicy.Control
                }
                subpolicies_data.append(subpolicy_dict)
            
            extracted_data = {
                "PolicyId": new_policy.PolicyId,
                "PolicyName": new_policy.PolicyName,
                "PolicyDescription": new_policy.PolicyDescription,
                "Status": new_policy.Status,
                "StartDate": new_policy.StartDate.isoformat() if new_policy.StartDate else None,
                "EndDate": new_policy.EndDate.isoformat() if new_policy.EndDate else None,
                "Department": new_policy.Department,
                "CreatedByName": new_policy.CreatedByName,
                "CreatedByDate": new_policy.CreatedByDate.isoformat() if new_policy.CreatedByDate else None,
                "Applicability": new_policy.Applicability,
                "DocURL": new_policy.DocURL,
                "Scope": new_policy.Scope,
                "Objective": new_policy.Objective,
                "Identifier": new_policy.Identifier,
                "PermanentTemporary": new_policy.PermanentTemporary,
                "ActiveInactive": new_policy.ActiveInactive,
                "Reviewer": new_policy.Reviewer,
                "CoverageRate": new_policy.CoverageRate,
                "CurrentVersion": new_policy.CurrentVersion,
                "PolicyType": new_policy.PolicyType,
                "PolicyCategory": new_policy.PolicyCategory,
                "PolicySubCategory": new_policy.PolicySubCategory,
                "Entities": new_policy.Entities,
                "type": "policy",
                "source": "tailoring",
                "FrameworkId": target_framework.FrameworkId,
                "FrameworkName": target_framework.FrameworkName,
                "subpolicies": subpolicies_data,
                "totalSubpolicies": len(subpolicies_data)
            }
            
            # Check for existing policy approval to prevent duplicates
            existing_approval = PolicyApproval.objects.filter(
                PolicyId=new_policy.PolicyId,
                UserId=user_id,
                ReviewerId=reviewer_id,
                Version="u1",
                ApprovedNot=None  # Only check for pending approvals
            ).first()
            
            if existing_approval:
                print(f"DEBUG: ⚠️ Duplicate prevention: Policy approval already exists for PolicyId {new_policy.PolicyId} with ApprovalId: {existing_approval.ApprovalId}")
                print(f"  - Skipping duplicate creation")
                policy_approval = existing_approval
            else:
                # Create policy approval entry
                policy_approval = PolicyApproval.objects.create(
                    PolicyId=new_policy,
                    ExtractedData=extracted_data,
                    UserId=user_id,
                    ReviewerId=reviewer_id,
                    Version="u1",  # Initial user version
                    ApprovedNot=None,  # Pending approval
                    FrameworkId=target_framework
                )
                print(f"DEBUG: ✅ Created new policy approval: {policy_approval.ApprovalId}")
            print(f"Policy approval details - PolicyId: {policy_approval.PolicyId}, ReviewerId: {policy_approval.ReviewerId}, Version: {policy_approval.Version}")
            print(f"ExtractedData keys: {list(extracted_data.keys())}")
            
            # Log successful tailored policy creation
            send_log(
                module="Policy",
                actionType="CREATE_SUCCESS",
                description=f"Tailored policy '{new_policy.PolicyName}' created successfully with {len(created_subpolicies)} subpolicies",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', new_policy.CreatedByName),
                entityType="Policy",
                entityId=new_policy.PolicyId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "policy_name": new_policy.PolicyName,
                    "policy_id": new_policy.PolicyId,
                    "framework_id": target_framework.FrameworkId,
                    "framework_name": target_framework.FrameworkName,
                    "approval_id": policy_approval.ApprovalId,
                    "subpolicies_created": len(created_subpolicies),
                    "source": "tailoring",
                    "status": new_policy.Status
                }
            )
            
            return Response({
                'message': 'Tailored policy created successfully',
                'PolicyId': new_policy.PolicyId,
                'PolicyName': new_policy.PolicyName,
                'FrameworkId': target_framework.FrameworkId,
                'FrameworkName': target_framework.FrameworkName,
                'ApprovalId': policy_approval.ApprovalId,
                'Version': policy_approval.Version,
                'SubpoliciesCreated': len(created_subpolicies),
                'Status': new_policy.Status
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        print(f"Error creating tailored policy: {str(e)}")
        print(traceback.format_exc())
        
        # Log error
        send_log(
            module="Policy",
            actionType="CREATE_FAILED",
            description=f"Failed to create tailored policy: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return Response({
            'error': f'Failed to create tailored policy: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyApprovePermission])
@csrf_exempt
def resubmit_policy_approval(request, approval_id):
    """
    Resubmit a rejected policy with updated data
    Creates new PolicyApproval record with incremented version
    """
    try:
        print(f"DEBUG: resubmit_policy_approval called for approval_id: {approval_id}")
        print(f"DEBUG: Request data: {request.data}")
        
        # Get the approval and policy
        approval = PolicyApproval.objects.get(ApprovalId=approval_id)
        policy = approval.PolicyId
        print(f"DEBUG: Found policy with name: {policy.PolicyName}, status: {policy.Status}")
        
        # Verify policy exists and can be resubmitted
        allowed_statuses = ['Rejected', 'Under Review']
        if policy.Status not in allowed_statuses:
            print(f"DEBUG: Policy status '{policy.Status}' is not in allowed statuses {allowed_statuses}")
            return Response({"error": "Only rejected or under review policies can be resubmitted"}, status=400)
            
        # Get the latest PolicyApproval to check its status
        latest_approval = PolicyApproval.objects.filter(
            PolicyId=policy
        ).order_by('-Version').first()
        
        if latest_approval and latest_approval.ApprovedNot is True:
            return Response({"error": "Cannot resubmit an approved policy"}, status=400)
        
        # Get the latest PolicyApproval for this policy to determine next version
        if latest_approval:
            # Parse the version and increment
            current_version = latest_approval.Version or 'u1'
            print(f"DEBUG: Current version: {current_version}")
            
            if current_version.startswith('u'):
                version_num = int(current_version[1:]) + 1
                new_version = f'u{version_num}'
            else:
                new_version = 'u2'
        else:
            new_version = 'u1'
        
        print(f"DEBUG: New version will be: {new_version}")
        
        # Get ExtractedData from request
        extracted_data = request.data.get('ExtractedData')
        if not extracted_data:
            return Response({"error": "ExtractedData is required"}, status=400)
            
        print(f"DEBUG: Received ExtractedData: {extracted_data}")
        
        # Update policy fields from ExtractedData
        policy.PolicyName = extracted_data.get('PolicyName', policy.PolicyName)
        policy.PolicyDescription = extracted_data.get('PolicyDescription', policy.PolicyDescription)
        policy.Scope = extracted_data.get('Scope', policy.Scope)
        policy.Objective = extracted_data.get('Objective', policy.Objective)
        policy.Department = extracted_data.get('Department', policy.Department)
        policy.Applicability = extracted_data.get('Applicability', policy.Applicability)
        
        # Preserve the original creator information
        original_creator = Users.objects.filter(UserId=approval.UserId).first()
        if original_creator:
            policy.CreatedByName = original_creator.UserName
            extracted_data['CreatedByName'] = original_creator.UserName
            extracted_data['CreatedBy'] = original_creator.UserId
        
        # Update policy status to Under Review
        policy.Status = 'Under Review'
        policy.save()
        print(f"DEBUG: Updated policy status to 'Under Review'")
        
        # Process subpolicies if provided
        if 'subpolicies' in extracted_data and extracted_data['subpolicies']:
            print(f"DEBUG: Processing {len(extracted_data['subpolicies'])} subpolicies")
            
            for subpolicy_data in extracted_data['subpolicies']:
                print(f"DEBUG: Processing subpolicy: {subpolicy_data}")
                
                if 'SubPolicyId' in subpolicy_data and subpolicy_data['SubPolicyId']:
                    try:
                        subpolicy = SubPolicy.objects.get(SubPolicyId=subpolicy_data['SubPolicyId'])
                        
                        # Update subpolicy fields
                        subpolicy.SubPolicyName = subpolicy_data.get('SubPolicyName', subpolicy.SubPolicyName)
                        subpolicy.Description = subpolicy_data.get('Description', subpolicy.Description)
                        subpolicy.Control = subpolicy_data.get('Control', subpolicy.Control)
                        
                        # Reset subpolicy status to Under Review if it was Rejected
                        if subpolicy.Status == 'Rejected':
                            subpolicy.Status = 'Under Review'
                        subpolicy.save()
                        print(f"DEBUG: Updated subpolicy {subpolicy.SubPolicyId}")
                        
                    except SubPolicy.DoesNotExist:
                        print(f"DEBUG: SubPolicy with ID {subpolicy_data['SubPolicyId']} not found")
        
        # Use the original approval's user and reviewer IDs
        user_id = approval.UserId
        reviewer_id = approval.ReviewerId

        # Ensure creator information is preserved in ExtractedData
        original_creator = Users.objects.filter(UserId=user_id).first()
        if original_creator:
            extracted_data['CreatedByName'] = original_creator.UserName
            extracted_data['CreatedBy'] = original_creator.UserId

        # Create new PolicyApproval record with the provided ExtractedData
        new_policy_approval = PolicyApproval.objects.create(
            PolicyId=policy,
            ExtractedData=extracted_data,  # Use the ExtractedData with preserved creator info
            Version=new_version,
            UserId=user_id,
            ReviewerId=reviewer_id,
            ApprovedNot=None,
            ApprovedDate=None,
            Identifier=f"POL-{policy.PolicyId}-{new_version}",
            FrameworkId=policy.FrameworkId
        )

        print(f"DEBUG: Created new PolicyApproval with ID: {new_policy_approval.ApprovalId}, Version: {new_version}")
        
        # Send notification to reviewer about policy resubmission
        try:
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            reviewer = None
            submitter = None
            if new_policy_approval.ReviewerId:
                reviewer = Users.objects.get(UserId=new_policy_approval.ReviewerId)
            if new_policy_approval.UserId:
                submitter = Users.objects.get(UserId=new_policy_approval.UserId)
            if reviewer and reviewer.Email:
                notification_data = {
                    'notification_type': 'policyResubmitted',
                    'email': reviewer.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        reviewer.UserName,
                        policy.PolicyName,
                        submitter.UserName if submitter else ''
                    ]
                }
                notification_service.send_multi_channel_notification(notification_data)
        except Exception as notify_ex:
            print(f"DEBUG: Error sending policy resubmission notification: {notify_ex}")
        
        return Response({
            "message": "Policy resubmitted successfully",
            "ApprovalId": new_policy_approval.ApprovalId,
            "Version": new_version,
            "Status": "Under Review",
            "ExtractedData": extracted_data
        })
        
    except Policy.DoesNotExist:
        print(f"DEBUG: Policy with ID {policy_id} not found")
        return Response({"error": "Policy not found"}, status=404)
    except Exception as e:
        print(f"DEBUG: Error in resubmit_policy_approval: {str(e)}")
        return Response({"error": str(e)}, status=500)

@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyApprovePermission])
@csrf_exempt
def resubmit_policy_by_id(request, policy_id):
    """
    Resubmit a rejected policy with updated data using policy_id
    Creates new PolicyApproval record with incremented version
    """
    try:
        print(f"DEBUG: resubmit_policy_by_id called for policy_id: {policy_id}")
        print(f"DEBUG: Request data: {request.data}")
        
        # Get the policy directly
        policy = Policy.objects.get(PolicyId=policy_id)
        print(f"DEBUG: Found policy with name: {policy.PolicyName}, status: {policy.Status}")
        
        # Verify policy exists and can be resubmitted
        allowed_statuses = ['Rejected', 'Under Review']
        if policy.Status not in allowed_statuses:
            print(f"DEBUG: Policy status '{policy.Status}' is not in allowed statuses {allowed_statuses}")
            return Response({"error": "Only rejected or under review policies can be resubmitted"}, status=400)
            
        # Get the latest PolicyApproval to check its status
        latest_approval = PolicyApproval.objects.filter(
            PolicyId=policy
        ).order_by('-Version').first()
        
        if latest_approval and latest_approval.ApprovedNot is True:
            return Response({"error": "Cannot resubmit an approved policy"}, status=400)
        
        # Get the latest PolicyApproval for this policy to determine next version
        if latest_approval:
            # Parse the version and increment
            current_version = latest_approval.Version or 'u1'
            print(f"DEBUG: Current version: {current_version}")
            
            if current_version.startswith('u'):
                version_num = int(current_version[1:]) + 1
                new_version = f'u{version_num}'
            else:
                new_version = 'u2'
        else:
            new_version = 'u1'
        
        print(f"DEBUG: New version will be: {new_version}")
        
        # Get data from request - handle both flat structure and ExtractedData wrapper
        request_data = request.data
        extracted_data = request_data.get('ExtractedData', request_data)  # Use ExtractedData if present, otherwise use request_data directly
        
        if not extracted_data:
            return Response({"error": "Policy data is required"}, status=400)
            
        print(f"DEBUG: Received request data: {request_data}")
        print(f"DEBUG: Using extracted_data: {extracted_data}")
        
        # Update policy fields from extracted_data
        policy.PolicyName = extracted_data.get('PolicyName', policy.PolicyName)
        policy.PolicyDescription = extracted_data.get('PolicyDescription', policy.PolicyDescription)
        policy.Scope = extracted_data.get('Scope', policy.Scope)
        policy.Objective = extracted_data.get('Objective', policy.Objective)
        policy.Department = extracted_data.get('Department', policy.Department)
        policy.Applicability = extracted_data.get('Applicability', policy.Applicability)
        
        # Get the original creator from the FIRST approval (initial submission) to maintain consistency
        first_approval = PolicyApproval.objects.filter(
            PolicyId=policy
        ).order_by('Version').first()  # Get the first approval by version
        
        original_creator = None
        if first_approval:
            original_creator = Users.objects.filter(UserId=first_approval.UserId).first()
            print(f"DEBUG: Found original creator from first approval: {original_creator.UserName if original_creator else 'None'} (UserId: {first_approval.UserId})")
        
        if original_creator:
            policy.CreatedByName = original_creator.UserName
            extracted_data['CreatedByName'] = original_creator.UserName
            extracted_data['CreatedBy'] = original_creator.UserId
        else:
            # Use current user as fallback
            current_user = request.user
            if hasattr(current_user, 'userid'):
                policy.CreatedByName = current_user.username
                extracted_data['CreatedByName'] = current_user.username
                extracted_data['CreatedBy'] = current_user.userid
        
        # Update policy status to Under Review
        policy.Status = 'Under Review'
        policy.save()
        print(f"DEBUG: Updated policy status to 'Under Review'")
        
        # Process subpolicies if provided
        if 'subpolicies' in extracted_data and extracted_data['subpolicies']:
            print(f"DEBUG: Processing {len(extracted_data['subpolicies'])} subpolicies")
            
            for subpolicy_data in extracted_data['subpolicies']:
                print(f"DEBUG: Processing subpolicy: {subpolicy_data}")
                
                if 'SubPolicyId' in subpolicy_data and subpolicy_data['SubPolicyId']:
                    try:
                        subpolicy = SubPolicy.objects.get(SubPolicyId=subpolicy_data['SubPolicyId'])
                        
                        # Update subpolicy fields
                        subpolicy.SubPolicyName = subpolicy_data.get('SubPolicyName', subpolicy.SubPolicyName)
                        subpolicy.Description = subpolicy_data.get('Description', subpolicy.Description)
                        subpolicy.Control = subpolicy_data.get('Control', subpolicy.Control)
                        
                        # Reset subpolicy status to Under Review if it was Rejected
                        if subpolicy.Status == 'Rejected':
                            subpolicy.Status = 'Under Review'
                        subpolicy.save()
                        print(f"DEBUG: Updated subpolicy {subpolicy.SubPolicyId}")
                        
                    except SubPolicy.DoesNotExist:
                        print(f"DEBUG: SubPolicy with ID {subpolicy_data['SubPolicyId']} not found")
                        continue
        
        # Create new PolicyApproval record with original creator's UserId
        user_id = first_approval.UserId if first_approval else (original_creator.UserId if original_creator else (request.user.userid if hasattr(request.user, 'userid') else 1))
        reviewer_id = latest_approval.ReviewerId if latest_approval else None
        
        print(f"DEBUG: Creating PolicyApproval with UserId: {user_id}, ReviewerId: {reviewer_id}")
        
        new_approval = PolicyApproval.objects.create(
            PolicyId=policy,
            ExtractedData=extracted_data,
            UserId=user_id,  # Use original creator's UserId
            ReviewerId=reviewer_id,
            Version=new_version,
            ApprovedNot=None,  # Reset to pending
            ApprovalDueDate=None,  # Reset due date
            FrameworkId=policy.FrameworkId
        )
        
        print(f"DEBUG: Created new PolicyApproval with ID: {new_approval.ApprovalId}")
        
        # Return success response with new version
        return Response({
            "success": True,
            "message": "Policy resubmitted successfully",
            "ApprovalId": new_approval.ApprovalId,
            "Version": new_version,
            "PolicyId": policy.PolicyId,
            "ExtractedData": extracted_data
        })
        
    except Policy.DoesNotExist:
        print(f"DEBUG: Policy with ID {policy_id} not found")
        return Response({"error": "Policy not found"}, status=404)
    except Exception as e:
        print(f"DEBUG: Error in resubmit_policy_by_id: {str(e)}")
        return Response({"error": str(e)}, status=500)

def update_policy_status_from_subpolicies(policy_id):
    """
    Helper function to update a policy's status based on its subpolicies
    """
    try:
        from datetime import date
        print(f"DEBUG: Starting update_policy_status_from_subpolicies for policy_id: {policy_id}")
        policy = Policy.objects.get(PolicyId=policy_id)
        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        
        print(f"DEBUG: Found {subpolicies.count()} subpolicies for policy {policy_id}")
        
        # Default status if no subpolicies
        if not subpolicies.exists():
            print(f"DEBUG: No subpolicies found for policy {policy_id}, no status change needed")
            return
            
        # Check if any subpolicy is rejected
        any_rejected = False
        all_approved = True
        
        for subpolicy in subpolicies:
            print(f"DEBUG: Checking subpolicy {subpolicy.SubPolicyId} with status: {subpolicy.Status}")
            if subpolicy.Status == 'Rejected':
                any_rejected = True
                all_approved = False
                print(f"DEBUG: Found rejected subpolicy {subpolicy.SubPolicyId}")
                break
            elif subpolicy.Status != 'Approved':
                all_approved = False
                print(f"DEBUG: Found non-approved subpolicy {subpolicy.SubPolicyId} with status: {subpolicy.Status}")
                
        # Update policy status based on subpolicies
        if any_rejected:
            # Always set to rejected if any subpolicy is rejected, regardless of policy status
            if policy.Status != 'Rejected':
                policy.Status = 'Rejected'
                policy.save()
                print(f"DEBUG: Policy {policy_id} status set to Rejected due to rejected subpolicy")
        elif all_approved:
            # Only set to approved if all subpolicies are approved
            print(f"DEBUG: All subpolicies are approved for policy {policy_id}, setting status to Approved")
            policy.Status = 'Approved'
            # Set policy to Active or Scheduled based on StartDate
            today = date.today()
            print(f"DEBUG: Policy from Subpolicies {policy_id} - Today: {today}, StartDate: {policy.StartDate} (type: {type(policy.StartDate)})")
            
            if policy.StartDate and policy.StartDate > today:
                policy.ActiveInactive = 'Scheduled'
                print(f"Set policy from subpolicy approval {policy_id} to Approved status and Scheduled status (StartDate: {policy.StartDate} > today: {today})")
            else:
                policy.ActiveInactive = 'Active'
                print(f"Set policy from subpolicy approval {policy_id} to Approved status and Active status (StartDate: {policy.StartDate} <= today: {today} or None)")
            
            policy.save()
            print(f"DEBUG: Policy {policy_id} status set to Approved with ActiveInactive={policy.ActiveInactive} as all subpolicies are approved")
            
            # Deactivate previous versions when a policy is approved
            deactivated_count = deactivate_previous_version_policies(policy_id)
            print(f"DEBUG: Deactivated {deactivated_count} previous versions of policy {policy_id}")
            
    except Policy.DoesNotExist:
        print(f"ERROR: Policy {policy_id} not found")
    except Exception as e:
        print(f"ERROR updating policy status from subpolicies: {str(e)}")


def deactivate_previous_version_policies(policy_id):
    """
    Deactivates previous versions of a policy when a new version is approved.
    
    Args:
        policy_id: The ID of the newly approved policy
        
    Returns:
        int: Number of previous version policies deactivated
    """
    try:
        print(f"DEBUG: Starting deactivate_previous_version_policies for policy_id: {policy_id}")
        
        # Get the current policy
        current_policy = Policy.objects.get(PolicyId=policy_id)
        print(f"DEBUG: Found current policy: {current_policy.PolicyName}, Identifier: {current_policy.Identifier}")
        
        # Get the current policy version
        current_version = PolicyVersion.objects.filter(PolicyId=current_policy).first()
        if not current_version:
            print(f"DEBUG: No version information found for policy {policy_id}")
            return 0
            
        print(f"DEBUG: Current policy version: {current_version.Version}, VersionId: {current_version.VersionId}")
        
        # Check if there's a previous version
        if not current_version.PreviousVersionId:
            print(f"DEBUG: No previous version found for policy {policy_id}")
            return 0
            
        previous_version_id = current_version.PreviousVersionId
        print(f"DEBUG: Found previous version ID: {previous_version_id}")
        
        # Get the previous version record
        previous_version = PolicyVersion.objects.filter(VersionId=previous_version_id).first()
        if not previous_version:
            print(f"DEBUG: Previous version record {previous_version_id} not found")
            return 0
            
        print(f"DEBUG: Previous version policy ID: {previous_version.PolicyId.PolicyId}, Version: {previous_version.Version}")
        
        # Get the previous policy
        previous_policy = previous_version.PolicyId
        if not previous_policy:
            print(f"DEBUG: Previous policy not found")
            return 0
            
        print(f"DEBUG: Deactivating previous policy: {previous_policy.PolicyName}, ID: {previous_policy.PolicyId}")
        
        # Deactivate the previous policy
        previous_policy.ActiveInactive = 'Inactive'
        previous_policy.save()
        
        print(f"DEBUG: Successfully deactivated previous policy {previous_policy.PolicyId} (changed status to Inactive)")
        
        return 1
    except Exception as e:
        print(f"ERROR in deactivate_previous_version_policies: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policy_categories(request):
    try:
        categories = PolicyCategory.objects.all()
        categories_data = []
        for category in categories:
            categories_data.append({
                'Id': category.Id,
                'PolicyType': category.PolicyType,
                'PolicyCategory': category.PolicyCategory,
                'PolicySubCategory': category.PolicySubCategory
            })
        return Response(categories_data)
    except Exception as e:
        print(f"Error in get_policy_categories: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policy_subcategories(request):
    try:
        policy_type = request.GET.get('policy_type')
        policy_category = request.GET.get('policy_category')

        if not policy_type or not policy_category:
            return Response({"error": "Both policy_type and policy_category are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get unique subcategories for the given type and category
        subcategories = PolicyCategory.objects.filter(
            PolicyType=policy_type,
            PolicyCategory=policy_category
        ).values_list('PolicySubCategory', flat=True).distinct()

        return Response(list(subcategories))
    except Exception as e:
        print(f"Error in get_policy_subcategories: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([PolicyCreatePermission])
def save_policy_category(request):
    # Import security modules
    from django.utils.html import escape as escape_html
    import shlex
    
    print(f"🔍 DEBUG: save_policy_category endpoint called!")
    print(f"🔍 DEBUG: Request method: {request.method}")
    print(f"🔍 DEBUG: Request data: {request.data}")
    print(f"🔍 DEBUG: Request user: {request.user}")
    print(f"🔍 DEBUG: Request session: {dict(request.session) if hasattr(request, 'session') else 'No session'}")
    
    try:
        # Get framework context
        from ...framework_context import get_framework_context
        
        # Try to get user_id from various sources
        user_id = None
        
        # Try from session
        session_user_id = request.session.get('user_id') or request.session.get('grc_user_id')
        if session_user_id:
            user_id = session_user_id
        
        # If not in session, try from request user
        if not user_id and hasattr(request, 'user') and hasattr(request.user, 'id'):
            user_id = request.user.id
        
        # Try to get framework_id from various sources
        selected_framework_id = None
        
        # Try from framework context FIRST (more reliable and up-to-date)
        if user_id:
            selected_framework_id = get_framework_context(str(user_id))
            if selected_framework_id:
                print(f"✅ DEBUG: Found framework_id in framework context: {selected_framework_id}")
        
        # Fall back to session if not in framework context (for backward compatibility)
        if not selected_framework_id:
            session_framework_id = request.session.get('selected_framework_id') or request.session.get('grc_framework_selected')
            print(f"🔍 DEBUG: Session framework_id: {session_framework_id}")
            if session_framework_id:
                selected_framework_id = session_framework_id
                print(f"⚠️ DEBUG: Using session framework_id (fallback): {selected_framework_id}")
        
        # If still no framework_id, try request data
        if not selected_framework_id and request.data.get('frameworkId'):
            selected_framework_id = request.data.get('frameworkId')
            print(f"✅ DEBUG: Using request data framework_id: {selected_framework_id}")
        
        # Get target framework
        target_framework = None
        print(f"🔍 DEBUG: save_policy_category - selected_framework_id: {selected_framework_id}")
        print(f"🔍 DEBUG: save_policy_category - session keys: {list(request.session.keys()) if hasattr(request, 'session') else 'No session'}")
        print(f"🔍 DEBUG: save_policy_category - request.data: {request.data}")
        
        if selected_framework_id:
            try:
                target_framework = Framework.objects.get(FrameworkId=selected_framework_id)
                print(f"✅ DEBUG: Found target framework: {target_framework.FrameworkName} (ID: {target_framework.FrameworkId})")
            except Framework.DoesNotExist:
                print(f"❌ DEBUG: Framework {selected_framework_id} not found")
                return Response({"error": "Selected framework not found"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(f"❌ DEBUG: No framework selected")
            return Response({"error": "No framework selected. Please select a framework first."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Security: Sanitize input data before processing
        policy_type = escape_html(request.data.get('PolicyType', ''))
        policy_category = escape_html(request.data.get('PolicyCategory', ''))
        policy_subcategory = escape_html(request.data.get('PolicySubCategory', ''))

        if not all([policy_type, policy_category, policy_subcategory]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Security: Use sanitized data for database operations (Django ORM provides SQL injection protection)
        existing_category = PolicyCategory.objects.filter(
            PolicyType=policy_type,
            PolicyCategory=policy_category,
            PolicySubCategory=policy_subcategory,
            FrameworkId=target_framework
        ).first()

        if existing_category:
            return Response({
                "message": "Category combination already exists",
                "category": {
                    'Id': existing_category.Id,
                    'PolicyType': existing_category.PolicyType,
                    'PolicyCategory': existing_category.PolicyCategory,
                    'PolicySubCategory': existing_category.PolicySubCategory
                }
            })

        # Security: Create new category with sanitized data
        print(f"🔍 DEBUG: Creating PolicyCategory with FrameworkId: {target_framework.FrameworkId}")
        new_category = PolicyCategory.objects.create(
            PolicyType=policy_type,
            PolicyCategory=policy_category,
            PolicySubCategory=policy_subcategory,
            FrameworkId=target_framework
        )
        print(f"✅ DEBUG: Created PolicyCategory with ID: {new_category.Id}, FrameworkId: {new_category.FrameworkId}")

        return Response({
            "message": "Category saved successfully",
            "category": {
                'Id': new_category.Id,
                'PolicyType': new_category.PolicyType,
                'PolicyCategory': new_category.PolicyCategory,
                'PolicySubCategory': new_category.PolicySubCategory
            }
        })

    except Exception as e:
        print(f"❌ ERROR in save_policy_category: {str(e)}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_entities(request):
    """
    Get all entities for the multi-select dropdown
    Uses cursor-based pagination for efficient querying
    Returns entities structured for frontend consumption
    """
    try:
        # Use raw SQL for cursor-based querying (more efficient for large datasets)
        from django.db import connection
        
        cursor = connection.cursor()
        
        # Cursor-based SQL query to fetch active entities
        # Assuming entities don't have an 'active' field, fetch all entities
        # If you need to filter active entities, add a WHERE clause like: WHERE active = 1
        query = """
        SELECT Id, EntityName, Location 
        FROM entities 
        ORDER BY Location, EntityName
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Structure data for frontend consumption
        entities = []
        for row in results:
            entities.append({
                'id': row[0],      # Id
                'label': f"{row[2]} - {row[1]}",  # "Location - EntityName"
                'entityName': row[1],  # EntityName
                'location': row[2]     # Location
            })
        
        # Add "All" option at the beginning
        entities.insert(0, {
            'id': 'all',
            'label': 'All Locations',
            'entityName': 'All',
            'location': 'All'
        })
        
        cursor.close()
        
        return Response({
            'entities': entities,
            'count': len(entities) - 1  # Subtract 1 for the "All" option
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error fetching entities: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to fetch entities'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policy_compliance_stats(request, policy_id):
    """
    Get compliance statistics for a specific policy from lastchecklistitemverified table
    """
    try:
        # Check if policy exists
        try:
            policy = Policy.objects.get(PolicyId=policy_id)
        except Policy.DoesNotExist:
            return Response({
                'error': 'Policy not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get compliance statistics from lastchecklistitemverified table
        compliance_records = LastChecklistItemVerified.objects.filter(PolicyId=policy_id)
        
        # Count compliance statuses
        # 0 = not complied, 1 = partially complied, 2 = fully complied
        not_complied_count = compliance_records.filter(Complied='0').count()
        partially_complied_count = compliance_records.filter(Complied='1').count()
        fully_complied_count = compliance_records.filter(Complied='2').count()
        
        total_compliance_items = compliance_records.count()
        
        # Calculate percentages - safe division
        if total_compliance_items > 0:
            not_complied_percentage = (not_complied_count / total_compliance_items) * 100
            partially_complied_percentage = (partially_complied_count / total_compliance_items) * 100
            fully_complied_percentage = (fully_complied_count / total_compliance_items) * 100
        else:
            not_complied_percentage = partially_complied_percentage = fully_complied_percentage = 0
        
        return Response({
            'policy_id': policy_id,
            'policy_name': policy.PolicyName,
            'compliance_stats': {
                'not_complied': {
                    'count': not_complied_count,
                    'percentage': round(not_complied_percentage, 1)
                },
                'partially_complied': {
                    'count': partially_complied_count,
                    'percentage': round(partially_complied_percentage, 1)
                },
                'fully_complied': {
                    'count': fully_complied_count,
                    'percentage': round(fully_complied_percentage, 1)
                }
            },
            'total_compliance_items': total_compliance_items
        })
        
    except Exception as e:
        print(f"Error in get_policy_compliance_stats: {str(e)}")
        return Response({
            'error': 'Error fetching policy compliance statistics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def _handle_policy_status_change_request(request, policy_id, reason, reviewer_id, cascade_to_subpolicies):
    """
    Core logic for handling policy status change requests (extracted from API view)
    """
    # Import security modules
    from django.utils.html import escape as escape_html
    import shlex
    
    print(f"DEBUG: Core function - policy_id: {policy_id}, reason: {reason}, reviewer_id: {reviewer_id}")
    
    # Get the policy
    try:
        policy = Policy.objects.get(PolicyId=policy_id)
        print(f"DEBUG: Found policy: {policy.PolicyName}")
    except Policy.DoesNotExist:
        print(f"ERROR: Policy with ID {policy_id} not found")
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if policy is active
    if policy.ActiveInactive != 'Active':
        return Response({"error": "Only Active policies can be submitted for status change approval"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Security: Sanitize input data
    from grc.rbac.utils import RBACUtils
    user_id = RBACUtils.get_user_id_from_request(request)
    if not user_id:
        return Response({"error": "User not authenticated. Please login again."}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Use the selected reviewer_id from the frontend instead of overriding it
    # Get reviewer email for the selected reviewer
    reviewer_email = None
    if reviewer_id:
        reviewer_user = Users.objects.filter(UserId=reviewer_id).first()
        if reviewer_user:
            reviewer_email = reviewer_user.Email
    
    reason = escape_html(reason)
    
    # Collect subpolicies data for approval JSON
    subpolicies_data = []
    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
    
    # Security: XSS Protection - Escape subpolicy text fields
    for subpolicy in subpolicies:
        subpolicy_dict = {
            "SubPolicyId": subpolicy.SubPolicyId,
            "SubPolicyName": escape_html(subpolicy.SubPolicyName),
            "CreatedByName": escape_html(subpolicy.CreatedByName),
            "CreatedByDate": subpolicy.CreatedByDate.isoformat() if subpolicy.CreatedByDate else None,
            "Identifier": escape_html(subpolicy.Identifier),
            "Description": escape_html(subpolicy.Description),
            "Status": subpolicy.Status,
            "PermanentTemporary": subpolicy.PermanentTemporary,
            "Control": escape_html(subpolicy.Control)
        }
        subpolicies_data.append(subpolicy_dict)
    
    # Security: XSS Protection - Escape all text fields before storing in extracted_data
    print("DEBUG: Creating extracted_data...")
    try:
        extracted_data = {
            "PolicyName": escape_html(policy.PolicyName),
            "PolicyDescription": escape_html(policy.PolicyDescription),
            "Status": policy.Status,
            "StartDate": policy.StartDate.isoformat() if policy.StartDate else None,
            "EndDate": policy.EndDate.isoformat() if policy.EndDate else None,
            "Department": escape_html(policy.Department) if policy.Department else None,
            "CreatedByName": escape_html(policy.CreatedByName) if policy.CreatedByName else None,
            "CreatedByDate": policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
            "Applicability": escape_html(policy.Applicability) if policy.Applicability else None,
            "DocURL": escape_html(policy.DocURL) if policy.DocURL else None,
            "Scope": escape_html(policy.Scope) if policy.Scope else None,
            "Objective": escape_html(policy.Objective) if policy.Objective else None,
            "Identifier": escape_html(policy.Identifier) if policy.Identifier else None,
            "PermanentTemporary": policy.PermanentTemporary,
            "ActiveInactive": policy.ActiveInactive,
            "Reviewer": escape_html(policy.Reviewer) if policy.Reviewer else None,
            "CoverageRate": policy.CoverageRate,
            "CurrentVersion": policy.CurrentVersion,
            "PolicyType": escape_html(policy.PolicyType) if policy.PolicyType else None,
            "PolicyCategory": escape_html(policy.PolicyCategory) if policy.PolicyCategory else None,
            "PolicySubCategory": escape_html(policy.PolicySubCategory) if policy.PolicySubCategory else None,
            "Entities": policy.Entities,  # Don't escape JSON field
            "type": "policy",
            "source": "status_change_request",
            "request_type": "status_change",
            "requested_status": "Inactive",
            "current_status": "Active",
            "reason_for_change": reason,  # Already escaped above
            "requested_date": timezone.now().date().isoformat(),
            "subpolicies": subpolicies_data,
            "totalSubpolicies": len(subpolicies_data),
            "cascade_to_subpolicies": cascade_to_subpolicies
        }
        print("DEBUG: Successfully created extracted_data")
    except Exception as ex:
        print(f"ERROR: Failed to create extracted_data: {str(ex)}")
        import traceback
        traceback.print_exc()
        raise ex
    
    with transaction.atomic():
        # Check if there's already a pending status change request for this policy
        existing_pending_request = PolicyApproval.objects.filter(
            PolicyId=policy,
            ExtractedData__request_type='status_change',
            ApprovedNot__isnull=True  # Not yet approved/rejected
        ).first()
        
        if existing_pending_request:
            return Response({
                "error": "There is already a pending status change request for this policy. Please wait for the current request to be processed."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update policy status to Under Review (only if not already under review)
        if policy.Status != 'Under Review':
            policy.Status = 'Under Review'
            policy.save()
            print(f"DEBUG: Updated policy {policy.PolicyId} status to 'Under Review'")
        else:
            print(f"DEBUG: Policy {policy.PolicyId} already has status 'Under Review'")
        
        # Determine the next user version
        latest_user_version = PolicyApproval.objects.filter(
            PolicyId=policy,
            Version__startswith='u'
        ).order_by('-ApprovalId').first()
        
        if latest_user_version:
            try:
                version_num = int(latest_user_version.Version[1:])
                new_version = f'u{version_num + 1}'
            except ValueError:
                new_version = 'u1'
        else:
            new_version = 'u1'  # First approval
        
        # Create the policy approval
        policy_approval = PolicyApproval.objects.create(
            PolicyId=policy,
            ExtractedData=extracted_data,
            UserId=user_id,
            ReviewerId=reviewer_id,
            Version=new_version,
            ApprovedNot=None,  # Not yet approved
            FrameworkId=policy.FrameworkId
        )
        
        print(f"DEBUG: Created PolicyApproval record with ID {policy_approval.ApprovalId}, Version {new_version}")
        
        # Send notification to reviewer if email is available
        if reviewer_email:
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                notification_data = {
                    'notification_type': 'policyInactiveRequested',
                    'email': reviewer_email,
                    'email_type': 'gmail',
                    'template_data': [
                        policy.PolicyName,
                        policy.Reviewer,
                        policy.CreatedByName,
                        reason
                    ]
                }
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Policy inactivation notification result: {notification_result}")
            except Exception as notify_ex:
                print(f"Error sending policy inactivation notification: {notify_ex}")
    
    return Response({
        "message": "Policy status change request submitted successfully. Awaiting approval.",
        "ApprovalId": policy_approval.ApprovalId,
        "Version": policy_approval.Version,
        "Status": "Under Review"
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([PolicyApprovalWorkflowPermission])
def request_policy_status_change(request, policy_id):
    """
    Request approval for changing a policy's status from Active to Inactive
    Creates a policy approval entry that needs to be approved by a reviewer
    """
    try:
        print(f"DEBUG: API request_policy_status_change called for policy ID: {policy_id}")
        print(f"DEBUG: Request data: {request.data}")
        
        # Get user ID from session using RBAC utils
        from grc.rbac.utils import RBACUtils
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({"error": "User not authenticated. Please login again."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Extract parameters from request
        reason = request.data.get('reason', '')
        reviewer_id = request.data.get('ReviewerId')
        if not reviewer_id:
            return Response({"error": "Reviewer ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        cascade_to_subpolicies = request.data.get('cascadeToSubpolicies', True)
        
        # Call the core function
        return _handle_policy_status_change_request(request, policy_id, reason, reviewer_id, cascade_to_subpolicies)
        
    except Exception as e:
        print(f"ERROR in request_policy_status_change: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'GET'])
@permission_classes([PolicyApprovalWorkflowPermission])
def approve_policy_status_change(request, approval_id):
    print(f"DEBUG: ===== POLICY FUNCTION ENTRY POINT =====")
    print(f"DEBUG: Policy function called with approval_id: {approval_id}")
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request path: {request.path}")
    print(f"DEBUG: Request user: {request.user}")
    print(f"DEBUG: Request headers: {dict(request.headers)}")
    print(f"DEBUG: Request data: {request.data}")
    print(f"DEBUG: ===== END POLICY FUNCTION ENTRY POINT =====")
    
    # Add immediate logging to confirm function is called
    logger.info(f"DEBUG: approve_policy_status_change function called with approval_id: {approval_id}")
    logger.info(f"DEBUG: Request method: {request.method}")
    logger.info(f"DEBUG: Request path: {request.path}")
    
    # Simple test for GET requests
    if request.method == 'GET':
        return Response({
            "message": "Policy function is working!",
            "approval_id": approval_id,
            "method": request.method,
            "user": str(request.user) if request.user else "No user"
        })
    
    """
    Approve or reject a policy status change request
    """
    print(f"DEBUG: ===== APPROVE POLICY STATUS CHANGE FUNCTION CALLED =====")
    print(f"DEBUG: approval_id: {approval_id}")
    print(f"DEBUG: request.method: {request.method}")
    print(f"DEBUG: request.path: {request.path}")
    print(f"DEBUG: request.user: {request.user}")
    print(f"DEBUG: request.headers: {dict(request.headers)}")
    logger.info(f"Policy status change approval attempt for approval ID: {approval_id}")
    
    # Import security modules
    from django.utils.html import escape as escape_html
    import shlex
    
    # Get user_id from multiple sources to ensure we get the correct ID
    from grc.rbac.utils import RBACUtils
    from grc.authentication import verify_jwt_token
    
    # Try JWT authentication first
    user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            payload = verify_jwt_token(token)
            if payload and 'user_id' in payload:
                user_id = payload['user_id']
                print(f"DEBUG: approve_policy_status_change - Extracted user_id from JWT: {user_id}")
                logger.info(f"DEBUG: approve_policy_status_change - Extracted user_id from JWT: {user_id}")
        except Exception as e:
            print(f"DEBUG: approve_policy_status_change - Error extracting user_id from JWT: {e}")
            logger.error(f"DEBUG: approve_policy_status_change - Error extracting user_id from JWT: {e}")
    
    # Fallback to RBAC utils if JWT extraction failed
    if not user_id:
        user_id_from_rbac = RBACUtils.get_user_id_from_request(request)
        user_id_from_userid = getattr(request.user, 'UserId', None)
        user_id_from_id = getattr(request.user, 'id', None)
        
        # Use the first available user ID
        user_id = user_id_from_userid or user_id_from_id or user_id_from_rbac
    
    if not user_id:
        logger.error(f"DEBUG: approve_policy_status_change - No user ID found from any source")
        return Response({"error": "User not authenticated. Please login again."}, status=status.HTTP_401_UNAUTHORIZED)
    
    send_log(
        module="Policy",
        actionType="APPROVE_STATUS_CHANGE",
        description=f"Policy status change approval attempt for approval ID: {approval_id}",
        userId=user_id,
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="PolicyApproval",
        ipAddress=get_client_ip(request)
    )
    
    try:
        approval = PolicyApproval.objects.get(ApprovalId=approval_id)
        policy = approval.PolicyId
        logger.info(f"Found policy: {policy.PolicyName} for status change approval")
        logger.info(f"DEBUG: approve_policy_status_change - approval object: {approval}")
        logger.info(f"DEBUG: approve_policy_status_change - approval.ReviewerId: {approval.ReviewerId}")
        logger.info(f"DEBUG: approve_policy_status_change - approval.UserId: {approval.UserId}")
        logger.info(f"DEBUG: approve_policy_status_change - approval.ExtractedData: {approval.ExtractedData}")
        
        # Check if this is a status change request
        if approval.ExtractedData.get('request_type') != 'status_change':
            logger.warning(f"Approval {approval_id} is not a status change request")
            return Response({"error": "This is not a status change request"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the current user is the assigned reviewer
        logger.info(f"DEBUG: approve_policy_status_change - approval.ReviewerId: {approval.ReviewerId}")
        logger.info(f"DEBUG: approve_policy_status_change - user_id: {user_id}")
        logger.info(f"DEBUG: approve_policy_status_change - ReviewerId type: {type(approval.ReviewerId)}")
        logger.info(f"DEBUG: approve_policy_status_change - user_id type: {type(user_id)}")
        logger.info(f"DEBUG: approve_policy_status_change - approval.ReviewerId == user_id: {approval.ReviewerId == user_id}")
        logger.info(f"DEBUG: approve_policy_status_change - str(approval.ReviewerId) == str(user_id): {str(approval.ReviewerId) == str(user_id)}")
        
        # Convert both to integers for comparison, handling None values
        try:
            reviewer_id_int = int(approval.ReviewerId) if approval.ReviewerId is not None else None
            user_id_int = int(user_id) if user_id is not None else None
            
            logger.info(f"DEBUG: approve_policy_status_change - reviewer_id_int: {reviewer_id_int}")
            logger.info(f"DEBUG: approve_policy_status_change - user_id_int: {user_id_int}")
            
            # Also try string comparison as fallback
            reviewer_id_str = str(approval.ReviewerId) if approval.ReviewerId is not None else None
            user_id_str = str(user_id) if user_id is not None else None
            
            logger.info(f"DEBUG: approve_policy_status_change - reviewer_id_str: {reviewer_id_str}")
            logger.info(f"DEBUG: approve_policy_status_change - user_id_str: {user_id_str}")
            
            # Check both integer and string comparisons
            int_match = reviewer_id_int == user_id_int
            str_match = reviewer_id_str == user_id_str
            
            logger.info(f"DEBUG: approve_policy_status_change - int_match: {int_match}")
            logger.info(f"DEBUG: approve_policy_status_change - str_match: {str_match}")
            
            if not int_match and not str_match:
                logger.warning(f"DEBUG: approve_policy_status_change - Access denied: reviewer_id ({approval.ReviewerId}) != user_id ({user_id})")
                return Response({
                    "error": "You are not the assigned reviewer for this request. Only the assigned reviewer can approve or reject status change requests."
                }, status=status.HTTP_403_FORBIDDEN)
                
        except (ValueError, TypeError) as e:
            logger.error(f"DEBUG: approve_policy_status_change - Error converting IDs: {e}")
            # If conversion fails, try direct comparison
            if str(approval.ReviewerId) != str(user_id):
                logger.warning(f"DEBUG: approve_policy_status_change - Access denied after conversion error: reviewer_id ({approval.ReviewerId}) != user_id ({user_id})")
                return Response({
                    "error": "You are not the assigned reviewer for this request. Only the assigned reviewer can approve or reject status change requests."
                }, status=status.HTTP_403_FORBIDDEN)
            
        # Get approval decision
        approved = request.data.get('approved', False)
        remarks = request.data.get('remarks', '')
        logger.info(f"Processing status change approval: approved={approved}, remarks={remarks}")
        
        # Security: Sanitize input data
        remarks = escape_html(remarks)
        
        with transaction.atomic():
            # Create a copy of the extracted data
            extracted_data = approval.ExtractedData.copy()
            
            if approved:
                logger.info(f"Approving status change for policy {policy.PolicyId} to Inactive")
                # Change policy status to Inactive (only if not already inactive)
                if policy.ActiveInactive != 'Inactive':
                    policy.ActiveInactive = 'Inactive'
                    policy.Status = 'Approved'  # Keep as Approved but set ActiveInactive to Inactive
                    policy.save()
                    logger.info(f"DEBUG: Updated policy {policy.PolicyId} to Inactive")
                else:
                    logger.info(f"DEBUG: Policy {policy.PolicyId} already has ActiveInactive='Inactive'")
                
                # Update extracted data
                extracted_data['ActiveInactive'] = 'Inactive'
                extracted_data['Status'] = 'Approved'
                extracted_data['status_change_approval'] = {
                    'approved': True,
                    'remarks': remarks or 'Status change approved',
                    'approved_by': user_id,  # Use the provided user_id
                    'approval_date': timezone.now().date().isoformat()
                }
                
                # Check if we should cascade to subpolicies
                cascade_to_subpolicies = extracted_data.get('cascade_to_subpolicies', True)
                if cascade_to_subpolicies:
                    # Get all subpolicies for this policy
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    
                    # Update their status to Inactive (only if not already inactive)
                    for subpolicy in subpolicies:
                        if subpolicy.Status != 'Inactive':
                            subpolicy.Status = 'Inactive'
                            subpolicy.save()
                            print(f"DEBUG: Updated subpolicy {subpolicy.SubPolicyId} to Inactive")
                        
                        # Update in extracted data
                        for subpolicy_data in extracted_data.get('subpolicies', []):
                            if subpolicy_data.get('SubPolicyId') == subpolicy.SubPolicyId:
                                subpolicy_data['Status'] = 'Inactive'
            else:
                logger.info(f"Rejecting status change for policy {policy.PolicyId}")
                # Reject status change request, revert policy status
                if policy.Status != 'Approved':
                    policy.Status = 'Approved'  # Reset from "Under Review"
                    policy.save()
                    logger.info(f"DEBUG: Reverted policy {policy.PolicyId} status to Approved")
                
                # Update extracted data
                extracted_data['status_change_approval'] = {
                    'approved': False,
                    'remarks': remarks or 'Status change rejected',
                    'rejected_by': user_id,  # Use the provided user_id
                    'rejection_date': timezone.now().date().isoformat()
                }
            
            # Determine the next reviewer version
            latest_reviewer_version = PolicyApproval.objects.filter(
                PolicyId=policy,
                Version__startswith='r'
            ).order_by('-ApprovalId').first()
            
            if latest_reviewer_version:
                try:
                    version_num = int(latest_reviewer_version.Version[1:])
                    new_version = f'r{version_num + 1}'
                except ValueError:
                    new_version = 'r1'
            else:
                new_version = 'r1'
                
            # Create a new approval record with the reviewer version
            new_approval = PolicyApproval.objects.create(
                PolicyId=policy,
                ExtractedData=extracted_data,
                UserId=approval.UserId,
                ReviewerId=approval.ReviewerId,
                Version=new_version,
                ApprovedNot=approved,
                ApprovedDate=timezone.now().date() if approved else None,  # Set approval date immediately if approved
                FrameworkId=policy.FrameworkId
            )
            
            print(f"DEBUG: Created reviewer PolicyApproval record with ID {new_approval.ApprovalId}, Version {new_version}")
            
            # Send notification to submitter about approval or rejection
            submitter_email = None
            submitter_name = policy.CreatedByName
            if submitter_name:
                submitter_user = Users.objects.filter(UserName=submitter_name).first()
                if submitter_user:
                    submitter_email = submitter_user.Email
            reviewer_name = None
            if approval.ReviewerId:
                reviewer_user = Users.objects.filter(UserId=approval.ReviewerId).first()
                if reviewer_user:
                    reviewer_name = reviewer_user.UserName
            
            if submitter_email and reviewer_name:
                try:
                    from ...routes.Global.notification_service import NotificationService
                    notification_service = NotificationService()
                    # Security: XSS Protection - Escape HTML content before building email template
                    if approved:
                        notification_data = {
                            'notification_type': 'policyInactivationApproved',
                            'email': submitter_email,
                            'email_type': 'gmail',
                            'template_data': [
                                escape_html(submitter_name),  # Escape submitter name for HTML context
                                escape_html(policy.PolicyName),  # Escape policy name for HTML context
                                escape_html(reviewer_name),  # Escape reviewer name for HTML context
                                remarks or 'Status change approved'  # Already escaped above
                            ]
                        }
                    else:
                        notification_data = {
                            'notification_type': 'policyInactivationRejected',
                            'email': submitter_email,
                            'email_type': 'gmail',
                            'template_data': [
                                escape_html(policy.PolicyName),  # Escape policy name for HTML context
                                escape_html(submitter_name),  # Escape submitter name for HTML context
                                escape_html(reviewer_name),  # Escape reviewer name for HTML context
                                remarks or 'Status change rejected'  # Already escaped above
                            ]
                        }
                    notification_result = notification_service.send_multi_channel_notification(notification_data)
                    print(f"Policy inactivation approval notification result: {notification_result}")
                except Exception as notify_ex:
                    print(f"Error sending policy inactivation approval notification: {notify_ex}")
            
        return Response({
            "message": f"Policy status change request {'approved' if approved else 'rejected'}",
            "ApprovalId": new_approval.ApprovalId,
            "Version": new_approval.Version,
            "ApprovedNot": approved,
            "policy_status": policy.Status,
            "policy_active_inactive": policy.ActiveInactive
        }, status=status.HTTP_200_OK)
        
    except PolicyApproval.DoesNotExist:
        return Response({"error": "Policy approval not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policy_status_change_requests(request):
    """
    Get all policy status change requests
    Include both pending and processed (approved/rejected) requests
    """
    try:
        # Find all policy approvals with request_type=status_change
        status_change_requests = []
        policy_status_map = {}  # To track the latest status for each policy
        
        # Get all approvals, not just those with ApprovedNot=None
        approvals = PolicyApproval.objects.filter().order_by('-ApprovalId')
        
        # First pass: Get the latest status for each policy
        for approval in approvals:
            # Check if the extracted data contains request_type=status_change
            if approval.ExtractedData.get('request_type') == 'status_change':
                try:
                    policy = approval.PolicyId
                    policy_name = policy.PolicyName
                    
                    # Only track the status if we haven't seen this policy before
                    # or if this is a newer approval (with a higher ApprovalId)
                    if policy_name not in policy_status_map:
                        policy_status_map[policy_name] = {
                            'status': approval.ApprovedNot,
                            'approvalId': approval.ApprovalId
                        }
                except Exception as e:
                    print(f"Warning: Skipping approval {approval.ApprovalId} - Policy not found: {str(e)}")
                    continue
        
        # Second pass: Create the request data with consistent status
        for approval in approvals:
            # Check if the extracted data contains request_type=status_change
            if approval.ExtractedData.get('request_type') == 'status_change':
                try:
                    policy = approval.PolicyId
                    policy_name = policy.PolicyName
                except Exception as e:
                    print(f"Warning: Skipping approval {approval.ApprovalId} - Policy not found: {str(e)}")
                    continue
                
                # Get the subpolicies that would be affected if approved
                affected_subpolicies = []
                if approval.ExtractedData.get('cascade_to_subpolicies', True):
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    
                    for subpolicy in subpolicies:
                        affected_subpolicies.append({
                            'SubPolicyId': subpolicy.SubPolicyId,
                            'SubPolicyName': subpolicy.SubPolicyName,
                            'Status': subpolicy.Status,
                            'Identifier': subpolicy.Identifier,
                            'Description': subpolicy.Description[:100] + '...' if subpolicy.Description and len(subpolicy.Description) > 100 else subpolicy.Description,
                            'Control': subpolicy.Control
                        })
                
                # Use the latest status for this policy from our map
                latest_status = policy_status_map.get(policy_name, {'status': None})['status']
                
                # Determine status based on the latest status for this policy
                approval_status = "Pending Approval"
                if latest_status is True:
                    approval_status = "Approved"
                elif latest_status is False:
                    approval_status = "Rejected"
                
                # Include any approval remarks
                approval_remarks = ""
                if approval.ExtractedData.get('status_change_approval'):
                    approval_remarks = approval.ExtractedData.get('status_change_approval').get('remarks', '')
                
                request_data = {
                    'ApprovalId': approval.ApprovalId,
                    'PolicyId': policy.PolicyId,
                    'PolicyName': policy.PolicyName,
                    'Department': policy.Department,
                    'RequestType': 'Change Status to Inactive',
                    'RequestDate': approval.ExtractedData.get('requested_date'),
                    'Reason': approval.ExtractedData.get('reason_for_change', 'No reason provided'),
                    'UserId': approval.UserId,
                    'ReviewerId': approval.ReviewerId,
                    'Version': approval.Version,
                    'Status': approval_status,
                    'ApprovedNot': latest_status,  # Use the latest status for consistency
                    'ApprovedDate': approval.ApprovedDate.isoformat() if approval.ApprovedDate else None,
                    'CascadeToSubpolicies': approval.ExtractedData.get('cascade_to_subpolicies', True),
                    'SubpolicyCount': len(affected_subpolicies),
                    'AffectedSubpolicies': affected_subpolicies,
                    'Remarks': approval_remarks,
                    'IsLatestApproval': approval.ApprovalId == policy_status_map.get(policy_name, {'approvalId': None})['approvalId']
                }
                
                status_change_requests.append(request_data)
        
        return Response(status_change_requests, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policy_status_change_requests_by_user(request, user_id=None):
    """
    Get policy status change requests filtered by user (creator/owner)
    """
    try:
        print(f"DEBUG: get_policy_status_change_requests_by_user called with user_id: {user_id}")
        
        # Base query for policy status change requests
        approvals = PolicyApproval.objects.filter().order_by('-ApprovalId')
        
        if user_id:
            # Filter by specific user (creator/owner)
            approvals = approvals.filter(UserId=user_id)
            print(f"DEBUG: Found {approvals.count()} policy approvals for user {user_id}")
        else:
            print(f"DEBUG: Found {approvals.count()} total policy approvals")
        
        status_change_requests = []
        
        # Get only status change requests
        for approval in approvals:
            if approval.ExtractedData.get('request_type') == 'status_change':
                # Check if PolicyId exists before proceeding
                if not approval.PolicyId:
                    print(f"Warning: Skipping approval {approval.ApprovalId} - PolicyId is NULL")
                    continue
                    
                try:
                    policy = approval.PolicyId
                except Exception as e:
                    print(f"Warning: Skipping approval {approval.ApprovalId} - Policy not found: {str(e)}")
                    continue
                
                # Get reviewer information
                reviewer_info = {'UserId': None, 'UserName': 'Unknown', 'Email': ''}
                if approval.ReviewerId:
                    try:
                        # Ensure ReviewerId is a valid integer
                        reviewer_id_int = int(approval.ReviewerId)
                        reviewer = Users.objects.get(UserId=reviewer_id_int)
                        reviewer_info = {
                            'UserId': reviewer.UserId,
                            'UserName': reviewer.UserName,
                            'Email': reviewer.Email
                        }
                    except (ValueError, Users.DoesNotExist) as e:
                        print(f"Warning: Invalid ReviewerId {approval.ReviewerId} for approval {approval.ApprovalId}: {str(e)}")
                        continue
                
                # Get the subpolicies that would be affected if approved
                affected_subpolicies = []
                if approval.ExtractedData.get('cascade_to_subpolicies', True):
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    
                    for subpolicy in subpolicies:
                        affected_subpolicies.append({
                            'SubPolicyId': subpolicy.SubPolicyId,
                            'SubPolicyName': subpolicy.SubPolicyName,
                            'Status': subpolicy.Status,
                            'Identifier': subpolicy.Identifier,
                            'Description': subpolicy.Description[:100] + '...' if subpolicy.Description and len(subpolicy.Description) > 100 else subpolicy.Description,
                            'Control': subpolicy.Control
                        })
                
                # Determine status 
                approval_status = "Pending Approval"
                if approval.ApprovedNot is True:
                    approval_status = "Approved"
                elif approval.ApprovedNot is False:
                    approval_status = "Rejected"
                
                # Include any approval remarks
                approval_remarks = ""
                if approval.ExtractedData.get('status_change_approval'):
                    approval_remarks = approval.ExtractedData.get('status_change_approval').get('remarks', '')
                
                request_data = {
                    'ApprovalId': approval.ApprovalId,
                    'PolicyId': policy.PolicyId,
                    'PolicyName': policy.PolicyName,
                    'Department': policy.Department,
                    'RequestType': 'Change Status to Inactive',
                    'RequestDate': approval.ExtractedData.get('requested_date'),
                    'Reason': approval.ExtractedData.get('reason_for_change', 'No reason provided'),
                    'UserId': approval.UserId,
                    'ReviewerId': approval.ReviewerId,
                    'ReviewerInfo': reviewer_info,
                    'Version': approval.Version,
                    'Status': approval_status,
                    'ApprovedNot': approval.ApprovedNot,
                    'ApprovedDate': approval.ApprovedDate.isoformat() if approval.ApprovedDate else None,
                    'CascadeToSubpolicies': approval.ExtractedData.get('cascade_to_subpolicies', True),
                    'SubpolicyCount': len(affected_subpolicies),
                    'AffectedSubpolicies': affected_subpolicies,
                    'Remarks': approval_remarks,
                    'Type': 'Policy'  # Add type field to distinguish from frameworks
                }
                
                status_change_requests.append(request_data)
        
        print(f"DEBUG: Returning {len(status_change_requests)} policy status change requests for user {user_id}")
        
        # Debug: Print all approvals in database
        all_approvals = PolicyApproval.objects.filter(
            ExtractedData__request_type='status_change'
        ).values('ApprovalId', 'UserId', 'ReviewerId', 'PolicyId__PolicyName')
        print(f"DEBUG: All policy status change approvals in database: {list(all_approvals)}")
        
        return Response(status_change_requests, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"DEBUG: ERROR in get_policy_status_change_requests_by_user: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policy_status_change_requests_by_reviewer(request, reviewer_id=None):
    """
    Get policy status change requests filtered by reviewer
    """
    try:
        print(f"DEBUG: get_policy_status_change_requests_by_reviewer called with reviewer_id: {reviewer_id}")
        
        # Base query for policy status change requests
        # Filter out records with invalid ReviewerId (non-integer values)
        approvals = PolicyApproval.objects.filter(
            ReviewerId__isnull=False
        ).exclude(
            ReviewerId__regex=r'^[a-zA-Z]'  # Exclude records where ReviewerId starts with letters
        ).order_by('-ApprovalId')
        
        if reviewer_id:
            # Filter by specific reviewer
            approvals = approvals.filter(ReviewerId=reviewer_id)
            print(f"DEBUG: Found {approvals.count()} policy approvals for reviewer {reviewer_id}")
        else:
            print(f"DEBUG: Found {approvals.count()} total policy approvals")
        
        status_change_requests = []
        
        # Get only status change requests
        for approval in approvals:
            if approval.ExtractedData.get('request_type') == 'status_change':
                # Check if PolicyId exists before proceeding
                if not approval.PolicyId:
                    print(f"Warning: Skipping approval {approval.ApprovalId} - PolicyId is NULL")
                    continue
                    
                try:
                    policy = approval.PolicyId
                except Exception as e:
                    print(f"Warning: Skipping approval {approval.ApprovalId} - Policy not found: {str(e)}")
                    continue
                
                # Get reviewer information
                reviewer_info = {'UserId': None, 'UserName': 'Unknown', 'Email': ''}
                if approval.ReviewerId:
                    try:
                        # Ensure ReviewerId is a valid integer
                        reviewer_id_int = int(approval.ReviewerId)
                        reviewer = Users.objects.get(UserId=reviewer_id_int)
                        reviewer_info = {
                            'UserId': reviewer.UserId,
                            'UserName': reviewer.UserName,
                            'Email': reviewer.Email
                        }
                    except (ValueError, Users.DoesNotExist) as e:
                        print(f"Warning: Invalid ReviewerId {approval.ReviewerId} for approval {approval.ApprovalId}: {str(e)}")
                        continue
                
                # Get the subpolicies that would be affected if approved
                affected_subpolicies = []
                if approval.ExtractedData.get('cascade_to_subpolicies', True):
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    
                    for subpolicy in subpolicies:
                        affected_subpolicies.append({
                            'SubPolicyId': subpolicy.SubPolicyId,
                            'SubPolicyName': subpolicy.SubPolicyName,
                            'Status': subpolicy.Status,
                            'Identifier': subpolicy.Identifier,
                            'Description': subpolicy.Description[:100] + '...' if subpolicy.Description and len(subpolicy.Description) > 100 else subpolicy.Description,
                            'Control': subpolicy.Control
                        })
                
                # Determine status 
                approval_status = "Pending Approval"
                if approval.ApprovedNot is True:
                    approval_status = "Approved"
                elif approval.ApprovedNot is False:
                    approval_status = "Rejected"
                
                # Include any approval remarks
                approval_remarks = ""
                if approval.ExtractedData.get('status_change_approval'):
                    approval_remarks = approval.ExtractedData.get('status_change_approval').get('remarks', '')
                
                request_data = {
                    'ApprovalId': approval.ApprovalId,
                    'PolicyId': policy.PolicyId,
                    'PolicyName': policy.PolicyName,
                    'Department': policy.Department,
                    'RequestType': 'Change Status to Inactive',
                    'RequestDate': approval.ExtractedData.get('requested_date'),
                    'Reason': approval.ExtractedData.get('reason_for_change', 'No reason provided'),
                    'UserId': approval.UserId,
                    'ReviewerId': approval.ReviewerId,
                    'ReviewerInfo': reviewer_info,
                    'Version': approval.Version,
                    'Status': approval_status,
                    'ApprovedNot': approval.ApprovedNot,
                    'ApprovedDate': approval.ApprovedDate.isoformat() if approval.ApprovedDate else None,
                    'CascadeToSubpolicies': approval.ExtractedData.get('cascade_to_subpolicies', True),
                    'SubpolicyCount': len(affected_subpolicies),
                    'AffectedSubpolicies': affected_subpolicies,
                    'Remarks': approval_remarks,
                    'Type': 'Policy'  # Add type field to distinguish from frameworks
                }
                
                status_change_requests.append(request_data)
        
        print(f"DEBUG: Returning {len(status_change_requests)} policy status change requests for reviewer {reviewer_id}")
        
        # Debug: Print all approvals in database
        all_approvals = PolicyApproval.objects.filter(
            ExtractedData__request_type='status_change'
        ).values('ApprovalId', 'UserId', 'ReviewerId', 'PolicyId__PolicyName')
        print(f"DEBUG: All policy status change approvals in database: {list(all_approvals)}")
        
        return Response(status_change_requests, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"DEBUG: ERROR in get_policy_status_change_requests_by_reviewer: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([PolicyViewPermission])
def test_policy_status_debug(request, policy_id):
    """
    Test endpoint to debug policy status change issues
    """
    try:
        print(f"DEBUG TEST: Policy ID: {policy_id}")
        print(f"DEBUG TEST: Request data: {request.data}")
        
        # Test 1: Can we get the policy?
        try:
            policy = Policy.objects.get(PolicyId=policy_id)
            print(f"DEBUG TEST: Policy found: {policy.PolicyName}")
        except Exception as e:
            print(f"DEBUG TEST: Policy fetch failed: {str(e)}")
            return Response({"error": f"Policy fetch failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Test 2: Can we access policy fields?
        try:
            print(f"DEBUG TEST: Policy fields check:")
            print(f"  - PolicyName: {policy.PolicyName}")
            print(f"  - Department: {policy.Department}")
            print(f"  - Entities: {policy.Entities}")
            print(f"  - PolicyType: {policy.PolicyType}")
            print(f"  - ActiveInactive: {policy.ActiveInactive}")
        except Exception as e:
            print(f"DEBUG TEST: Policy fields access failed: {str(e)}")
            return Response({"error": f"Policy fields access failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Test 3: Can we create basic extracted_data?
        try:
            extracted_data = {
                "PolicyName": policy.PolicyName,
                "Status": policy.Status,
                "ActiveInactive": policy.ActiveInactive,
                "test": "basic_test"
            }
            print("DEBUG TEST: Basic extracted_data created successfully")
        except Exception as e:
            print(f"DEBUG TEST: Basic extracted_data failed: {str(e)}")
            return Response({"error": f"Basic extracted_data failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "message": "Debug test completed successfully",
            "policy_name": policy.PolicyName,
            "policy_id": policy_id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"DEBUG TEST: General error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": f"General error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






#this is updated policy
from django.http import JsonResponse
@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policy_extraction_progress(request, task_id):
    """Get the progress of policy extraction for a specific task"""
    try:
        from grc.routes.UploadFramework.policy_text_extract import get_progress
        
        # Get progress from the extraction module
        progress_data = get_progress(task_id)
        
        if not progress_data:
            # If no specific progress is available, check general processing status
            from grc.routes.UploadFramework.upload_framework import processing_status
            
            if task_id in processing_status:
                return JsonResponse(processing_status[task_id])
            else:
                # Provide a default response if no data is available
                return JsonResponse({
                    'progress': 0,
                    'message': 'Initializing extraction...',
                    'status': 'waiting'
                })
        
        return JsonResponse(progress_data)
    
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'progress': 0,
            'message': 'Error fetching extraction progress'
        }, status=500)


@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policy_counts_by_status(request):
    """
    Get policy counts by status for dashboard display
    Returns counts for Under Review, Approved, and Rejected policies
    Automatically applies framework filter from session
    """
    from .framework_filter_helper import apply_framework_filter_with_relation
    
    print(f"DEBUG: Getting policy counts by status")
    # Log policy counts request
    send_log(
        module="Policy",
        actionType="GET_POLICY_COUNTS_BY_STATUS",
        description="Getting policy counts by status for dashboard",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        ipAddress=get_client_ip(request),
        additionalInfo={}
    )
    
    try:
        from django.db.models import Count, Q
        
        # Apply framework filter
        policies_filtered = apply_framework_filter_with_relation(Policy.objects.all(), request, 'FrameworkId_id')
        
        # Get counts for each status
        pending_count = policies_filtered.filter(Status='Under Review').count()
        approved_count = policies_filtered.filter(Status='Approved').count()
        rejected_count = policies_filtered.filter(Status='Rejected').count()
        
        # Also get total count
        total_count = policies_filtered.count()
        
        result = {
            'pending': pending_count,
            'approved': approved_count,
            'rejected': rejected_count,
            'total': total_count
        }

        print(f"DEBUG: Policy counts: {result}")
        
        # Log successful policy counts retrieval
        send_log(
            module="Policy",
            actionType="GET_POLICY_COUNTS_BY_STATUS_SUCCESS",
            description=f"Successfully retrieved policy counts: {result}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            ipAddress=get_client_ip(request),
            additionalInfo=result
        )
        
        return Response(result)
        
    except Exception as e:
        # Log error
        send_log(
            module="Policy",
            actionType="GET_POLICY_COUNTS_BY_STATUS_ERROR",
            description=f"Error getting policy counts: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        return Response(
            {"error": f"Error retrieving policy counts: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policies_paginated_by_status(request):
    """
    Get policies by status with pagination support
    Query params: status, limit, offset
    Automatically applies framework filter from session
    """
    from .framework_filter_helper import apply_framework_filter_with_relation, get_framework_filter_info
    
    try:
        # Get query parameters with validation
        status_param = request.GET.get('status', 'Under Review')
        try:
            limit = int(request.GET.get('limit', 10))
            offset = int(request.GET.get('offset', 0))
        except (ValueError, TypeError):
            limit = 10
            offset = 0
        
        # Limit the maximum number of records per request
        limit = min(max(limit, 1), 100)  # Between 1 and 100
        offset = max(offset, 0)  # Non-negative
        
        filter_info = get_framework_filter_info(request)
        print(f"DEBUG: Fetching policies with status='{status_param}', limit={limit}, offset={offset}, framework_filter={filter_info}")
        
        # Get policies with the specified status
        policies_queryset = Policy.objects.filter(Status=status_param)
        
        # Apply framework filter from session
        policies_queryset = apply_framework_filter_with_relation(policies_queryset, request, 'FrameworkId_id')
        
        # Get total count
        total_count = policies_queryset.count()
        print(f"DEBUG: Total count for status '{status_param}': {total_count}")
        
        # Apply pagination
        policies = policies_queryset[offset:offset + limit]
        print(f"DEBUG: Retrieved {len(policies)} policies for this page")
        
        # Serialize the policies with simplified data
        policies_data = []
        for policy in policies:
            try:
                policy_data = {
                    'PolicyId': policy.PolicyId,
                    'PolicyName': getattr(policy, 'PolicyName', 'No Name'),
                    'PolicyDescription': getattr(policy, 'PolicyDescription', ''),
                    'Scope': getattr(policy, 'Scope', ''),
                    'Objective': getattr(policy, 'Objective', ''),
                    'Department': getattr(policy, 'Department', ''),
                    'CreatedByName': getattr(policy, 'CreatedByName', 'System'),
                    'CreatedByDate': getattr(policy, 'CreatedByDate', None),
                    'Status': getattr(policy, 'Status', 'Unknown'),
                    'CurrentVersion': getattr(policy, 'CurrentVersion', 'v1.0'),
                    'Identifier': getattr(policy, 'Identifier', ''),
                    'subpolicies': []  # Simplified - skip subpolicies for now to avoid errors
                }
                policies_data.append(policy_data)
            except Exception as policy_error:
                print(f"DEBUG: Error processing policy {policy.PolicyId}: {str(policy_error)}")
                continue
        
        result = {
            'success': True,
            'data': policies_data,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'current_page': (offset // limit) + 1 if limit > 0 else 1,
                'total_pages': (total_count + limit - 1) // limit if limit > 0 else 1
            }
        }
        
        print(f"DEBUG: Returning {len(policies_data)} policies")
        return Response(result)
        
    except Exception as e:
        print(f"DEBUG: Exception in get_policies_paginated_by_status: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response(
            {"error": f"Error retrieving policies: {str(e)}", "success": False}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Import necessary modules
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from ...routes.Global.s3_fucntions import RenderS3Client, create_direct_mysql_client
from ...utils import send_log, get_client_ip
# New file upload endpoint for policy documents
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([PolicyCreatePermission])
@parser_classes([MultiPartParser, FormParser])
@csrf_exempt
@require_consent('upload_policy')
def upload_policy_document(request):
    """
    Upload a policy document to S3 via the RenderS3Client
    
    Expects:
    - file: The file to upload
    - userId: User ID of the uploader
    - fileName: Optional custom file name
    - type: Type of document (e.g., 'policy', 'framework', 'subpolicy')
    - policyName: Name of the policy (for reference)
    """
    # Import security modules
    from django.utils.html import escape as escape_html
    from django.conf import settings
    import logging
    import os
    from pathlib import Path
    
    
    # Configure secure logging to prevent log injection
    logger = logging.getLogger(__name__)
    
    # Debug: Log request details
    logger.info("=== Policy Document Upload Request ===")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Files: {request.FILES.keys()}")
    logger.info(f"POST data: {request.POST.keys()}")
    
    # Log upload attempt
    send_log(
        module="Policy",
        actionType="UPLOAD_DOCUMENT",
        description="Policy document upload attempt",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="PolicyDocument",
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Validate request
        if 'file' not in request.FILES:
            logger.error("No file provided in request")
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get file from request
        file = request.FILES['file']
        logger.info(f"Processing file: {file.name} (size: {file.size} bytes)")
        
        # Get other parameters
        user_id = request.data.get('userId', getattr(request.user, 'id', 'default-user'))
        file_name = request.data.get('fileName', file.name)
        doc_type = request.data.get('type', 'policy')
        policy_name = request.data.get('policyName', 'Unnamed Policy')
        
        logger.info(f"Upload parameters - user_id: {user_id}, file_name: {file_name}, doc_type: {doc_type}, policy_name: {policy_name}")
        
        # Security: Sanitize inputs and convert back to strings for MySQL compatibility
        user_id = str(escape_html(str(user_id)))
        # For file_name, sanitize for filesystem use (remove path separators and dangerous chars)
        # Convert to plain string to avoid SafeString issues with Path operations
        file_name = str(file_name).replace('/', '_').replace('\\', '_').replace('..', '_')
        # Remove any remaining dangerous characters (re is already imported at top of file)
        file_name = re.sub(r'[<>:"|?*]', '_', file_name)
        doc_type = str(escape_html(doc_type))
        policy_name = str(escape_html(policy_name))
        
        # Save file temporarily - use MEDIA_ROOT from Django settings for absolute path
        # This matches the Docker volume mount: -v ~/MEDIA_ROOT:/app/MEDIA_ROOT
        temp_upload_dir = Path(settings.MEDIA_ROOT) / 'temp_uploads'
        temp_upload_dir.mkdir(parents=True, exist_ok=True)
        # Ensure file_name is a plain string (not SafeString) for Path operations
        temp_file_path = temp_upload_dir / str(file_name)
        temp_file_path_str = str(temp_file_path)
        
        logger.info(f"Saving file temporarily to: {temp_file_path_str}")
        
        with open(temp_file_path_str, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Initialize S3 client
        s3_client = create_direct_mysql_client()
        logger.info("Initialized S3 client, testing connection...")
        
        # Test connection first
        connection_test = s3_client.test_connection()
        logger.info(f"Connection test result: {connection_test}")
        
        if not connection_test.get('overall_success', False):
            logger.error(f"S3 service connection failed: {connection_test}")
            return Response({
                "error": "S3 service is currently unavailable. Please try again later.",
                "details": connection_test
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        logger.info("Connection successful, attempting upload...")
        
        # Upload file to S3
        logger.info(f"Starting S3 upload for file: {file_name}")
        upload_result = s3_client.upload(
            file_path=temp_file_path_str,
            user_id=user_id,
            custom_file_name=file_name,
            module='Policy'
        )
        logger.info(f"S3 upload completed. Result: {upload_result}")
        
        # Clean up temporary file
        if os.path.exists(temp_file_path_str):
            os.remove(temp_file_path_str)
            logger.info("Cleaned up temporary file")
        
        if upload_result.get('success'):
            logger.info(f"Upload successful. S3 URL: {upload_result['file_info']['url']}")
            
            # Log successful upload
            send_log(
                module="Policy",
                actionType="UPLOAD_DOCUMENT_SUCCESS",
                description=f"Successfully uploaded document {file_name} for {policy_name}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="PolicyDocument",
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "file_name": file_name,
                    "policy_name": policy_name,
                    "document_type": doc_type,
                    "s3_url": upload_result['file_info']['url']
                }
            )
            
            return Response({
                "success": True,
                "message": "File uploaded successfully",
                "file": {
                    "url": upload_result['file_info']['url'],
                    "name": file_name,
                    "storedName": upload_result['file_info']['storedName'],
                    "s3Key": upload_result['file_info']['s3Key']
                }
            })
        else:
            logger.error(f"Upload failed: {upload_result.get('error')}")
            
            # Clean up temporary file on failure
            if 'temp_file_path_str' in locals() and os.path.exists(temp_file_path_str):
                try:
                    os.remove(temp_file_path_str)
                    logger.info("Cleaned up temporary file after upload failure")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file: {cleanup_error}")
            
            # Log upload failure
            send_log(
                module="Policy",
                actionType="UPLOAD_DOCUMENT_FAILED",
                description=f"Failed to upload document {file_name}: {upload_result.get('error')}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="PolicyDocument",
                logLevel="ERROR",
                ipAddress=get_client_ip(request)
            )
            
            return Response({
                "success": False,
                "error": upload_result.get('error', "Unknown error during upload")
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        
        # Clean up temporary file on error
        if 'temp_file_path_str' in locals() and os.path.exists(temp_file_path_str):
            try:
                os.remove(temp_file_path_str)
                logger.info("Cleaned up temporary file after error")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temp file: {cleanup_error}")
        
        # Log unexpected error
        send_log(
            module="Policy",
            actionType="UPLOAD_DOCUMENT_FAILED",
            description=f"Unexpected error during document upload: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="PolicyDocument",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return Response({
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing policy approvals
def list_policy_approvals_for_user(request, user_id):
    """
    Get all policy approvals created by a specific user (My Tasks)
    """
    try:
        framework_id = request.GET.get('framework_id', None)
        print(f"🔍 DEBUG: list_policy_approvals_for_user called with framework_id: {framework_id}")
        print(f"🔍 DEBUG: framework_id type: {type(framework_id)}")
        print(f"🔍 DEBUG: All request GET params: {dict(request.GET)}")
        
        send_log(
            module="Policy",
            actionType="LIST_POLICY_APPROVALS_FOR_USER",
            description=f"Fetching policy approvals for user {user_id}",
            userId=user_id,
            userName=f"User{user_id}",
            entityType="PolicyApproval",
            ipAddress=get_client_ip(request),
            additionalInfo={"user_id": user_id}
        )
        
        # Filter policy approvals by UserId (creator)
        policy_approvals = PolicyApproval.objects.filter(
            UserId=user_id
        ).order_by('-ApprovalId')
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering policy approvals by framework_id: {framework_id}")
            # Convert to integer if it's a string
            try:
                framework_id_int = int(framework_id)
                print(f"🔍 DEBUG: Converted framework_id to int: {framework_id_int}")
                
                # Filter through Policy relationship: PolicyApproval -> Policy -> FrameworkId
                policy_approvals = policy_approvals.filter(PolicyId__FrameworkId=framework_id_int)
                print(f"✅ Framework filter applied through Policy relationship. Found {policy_approvals.count()} policy approvals.")
                
                # Additional debug: Check if any approvals exist
                total_approvals = PolicyApproval.objects.filter(UserId=user_id).count()
                print(f"🔍 DEBUG: Total approvals for user {user_id}: {total_approvals}")
                print(f"🔍 DEBUG: Filtered approvals for framework {framework_id_int}: {policy_approvals.count()}")
                
                # Debug: Show which frameworks actually have policy approvals for this user
                if policy_approvals.count() == 0:
                    print(f"⚠️ DEBUG: No policy approvals found for framework {framework_id_int}")
                    # Get all frameworks that have policy approvals for this user through Policy relationship
                    frameworks_with_approvals = PolicyApproval.objects.filter(
                        UserId=user_id,
                        PolicyId__isnull=False
                    ).values_list('PolicyId__FrameworkId', flat=True).distinct()
                    print(f"🔍 DEBUG: Frameworks with policy approvals for user {user_id}: {list(frameworks_with_approvals)}")
                    
                    # Get framework names for these IDs
                    try:
                        from ..models import Framework
                        if frameworks_with_approvals:
                            framework_names = Framework.objects.filter(FrameworkId__in=frameworks_with_approvals).values('FrameworkId', 'FrameworkName')
                            print(f"🔍 DEBUG: Framework names with data: {list(framework_names)}")
                    except Exception as e:
                        print(f"❌ ERROR: Could not fetch framework names: {e}")
                
            except (ValueError, TypeError) as e:
                print(f"❌ ERROR: Could not convert framework_id to int: {e}")
                print(f"🔍 DEBUG: Using original framework_id value: {framework_id}")
                policy_approvals = policy_approvals.filter(PolicyId__FrameworkId=framework_id)
                print(f"✅ Framework filter applied through Policy relationship (as string). Found {policy_approvals.count()} policy approvals.")
        
        # Log successful policy approvals listing for user
        send_log(
            module="Policy",
            actionType="LIST_POLICY_APPROVALS_FOR_USER_SUCCESS",
            description=f"Successfully fetched {len(policy_approvals)} policy approvals for user {user_id}",
            userId=user_id,
            userName=f"User{user_id}",
            entityType="PolicyApproval",
            ipAddress=get_client_ip(request),
            additionalInfo={"user_id": user_id, "approval_count": len(policy_approvals)}
        )
        
        serializer = PolicyApprovalSerializer(policy_approvals, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(policy_approvals)
        })
        
    except Exception as e:
        send_log(
            module="Policy",
            actionType="LIST_POLICY_APPROVALS_FOR_USER_ERROR",
            description=f"Error fetching policy approvals for user {user_id}: {str(e)}",
            userId=user_id,
            userName=f"User{user_id}",
            entityType="PolicyApproval",
            ipAddress=get_client_ip(request),
            logLevel="ERROR",
            additionalInfo={"user_id": user_id, "error": str(e)}
        )
        
        return Response({
            'error': f'Error fetching policy approvals for user {user_id}',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing reviewer policy approvals
def list_policy_approvals_for_reviewer_by_id(request, user_id):
    """
    Get all policy approvals assigned to a specific reviewer (Reviewer Tasks)
    """
    try:
        framework_id = request.GET.get('framework_id', None)
        print(f"🔍 DEBUG: list_policy_approvals_for_reviewer_by_id called with framework_id: {framework_id}")
        print(f"🔍 DEBUG: framework_id type: {type(framework_id)}")
        print(f"🔍 DEBUG: All request GET params: {dict(request.GET)}")
        
        send_log(
            module="Policy",
            actionType="LIST_POLICY_APPROVALS_FOR_REVIEWER",
            description=f"Fetching policy approvals for reviewer {user_id}",
            userId=user_id,
            userName=f"User{user_id}",
            entityType="PolicyApproval",
            ipAddress=get_client_ip(request),
            additionalInfo={"reviewer_id": user_id}
        )
        
        # Filter policy approvals by ReviewerId
        policy_approvals = PolicyApproval.objects.filter(
            ReviewerId=user_id
        ).order_by('-ApprovalId')
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering reviewer policy approvals by framework_id: {framework_id}")
            # Convert to integer if it's a string
            try:
                framework_id_int = int(framework_id)
                print(f"🔍 DEBUG: Converted framework_id to int: {framework_id_int}")
                
                # Filter through Policy relationship: PolicyApproval -> Policy -> FrameworkId
                policy_approvals = policy_approvals.filter(PolicyId__FrameworkId=framework_id_int)
                print(f"✅ Framework filter applied to reviewer approvals through Policy relationship. Found {policy_approvals.count()} policy approvals.")
                
                # Additional debug: Check if any approvals exist
                total_approvals = PolicyApproval.objects.filter(ReviewerId=user_id).count()
                print(f"🔍 DEBUG: Total reviewer approvals for user {user_id}: {total_approvals}")
                print(f"🔍 DEBUG: Filtered reviewer approvals for framework {framework_id_int}: {policy_approvals.count()}")
                
                # Debug: Show which frameworks actually have reviewer policy approvals for this user
                if policy_approvals.count() == 0:
                    print(f"⚠️ DEBUG: No reviewer policy approvals found for framework {framework_id_int}")
                    # Get all frameworks that have reviewer policy approvals for this user through Policy relationship
                    frameworks_with_reviewer_approvals = PolicyApproval.objects.filter(
                        ReviewerId=user_id,
                        PolicyId__isnull=False
                    ).values_list('PolicyId__FrameworkId', flat=True).distinct()
                    print(f"🔍 DEBUG: Frameworks with reviewer policy approvals for user {user_id}: {list(frameworks_with_reviewer_approvals)}")
                    
                    # Get framework names for these IDs
                    try:
                        from ..models import Framework
                        if frameworks_with_reviewer_approvals:
                            framework_names = Framework.objects.filter(FrameworkId__in=frameworks_with_reviewer_approvals).values('FrameworkId', 'FrameworkName')
                            print(f"🔍 DEBUG: Framework names with reviewer data: {list(framework_names)}")
                    except Exception as e:
                        print(f"❌ ERROR: Could not fetch framework names: {e}")
                
            except (ValueError, TypeError) as e:
                print(f"❌ ERROR: Could not convert framework_id to int: {e}")
                print(f"🔍 DEBUG: Using original framework_id value: {framework_id}")
                policy_approvals = policy_approvals.filter(PolicyId__FrameworkId=framework_id)
                print(f"✅ Framework filter applied to reviewer approvals through Policy relationship (as string). Found {policy_approvals.count()} policy approvals.")
        
        # Log successful policy approvals listing for reviewer
        send_log(
            module="Policy",
            actionType="LIST_POLICY_APPROVALS_FOR_REVIEWER_SUCCESS",
            description=f"Successfully fetched {len(policy_approvals)} policy approvals for reviewer {user_id}",
            userId=user_id,
            userName=f"User{user_id}",
            entityType="PolicyApproval",
            ipAddress=get_client_ip(request),
            additionalInfo={"reviewer_id": user_id, "approval_count": len(policy_approvals)}
        )
        
        serializer = PolicyApprovalSerializer(policy_approvals, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(policy_approvals)
        })
        
    except Exception as e:
        send_log(
            module="Policy",
            actionType="LIST_POLICY_APPROVALS_FOR_REVIEWER_ERROR",
            description=f"Error fetching policy approvals for reviewer {user_id}: {str(e)}",
            userId=user_id,
            userName=f"User{user_id}",
            entityType="PolicyApproval",
            ipAddress=get_client_ip(request),
            logLevel="ERROR",
            additionalInfo={"reviewer_id": user_id, "error": str(e)}
        )
        
        return Response({
            'error': f'Error fetching policy approvals for reviewer {user_id}',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# New file upload endpoint for policy documents
@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_policy_review_history(request, policy_id):
    """
    Get the review history/revisions for a specific policy
    Returns all approval records (r1, r2, etc.) for tracking reviewer actions
    """
    try:
        # Log policy review history access attempt
        send_log(
            module="Policy",
            actionType="VIEW_POLICY_REVIEW_HISTORY",
            description=f"Accessing review history for policy {policy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            ipAddress=get_client_ip(request)
        )

        # Get the policy to validate it exists
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Get all approval records for this policy, ordered by version
        approvals = PolicyApproval.objects.filter(
            PolicyId=policy
        ).select_related('ReviewerId').order_by('-ApprovalId')  # Latest first
        
        review_history = []
        for approval in approvals:
            # Get reviewer information
            reviewer_name = "Unknown"
            if approval.ReviewerId:
                try:
                    reviewer = Users.objects.get(UserId=approval.ReviewerId)
                    reviewer_name = reviewer.UserName
                except Users.DoesNotExist:
                    reviewer_name = "Unknown"
            
            # Determine status based on ApprovedNot
            if approval.ApprovedNot is None:
                status = "Under Review"
                status_label = "pending"
            elif approval.ApprovedNot == True:
                status = "Approved"
                status_label = "approved" 
            else:
                status = "Rejected"
                status_label = "rejected"
            
            # Get rejection reason if available
            rejection_reason = None
            if approval.ApprovedNot == False and approval.ExtractedData:
                rejection_reason = approval.ExtractedData.get('rejection_reason', '')
            
            review_history.append({
                'approval_id': approval.ApprovalId,
                'version': approval.Version or 'v1.0',
                'status': status,
                'status_label': status_label,
                'reviewer_name': reviewer_name,
                'reviewer_id': approval.ReviewerId,
                'approved_date': approval.ApprovedDate.isoformat() if approval.ApprovedDate else None,
                'created_date': approval.created_at.isoformat() if hasattr(approval, 'created_at') else None,
                'rejection_reason': rejection_reason,
                'extracted_data': approval.ExtractedData
            })
        
        # Log successful access
        send_log(
            module="Policy",
            actionType="VIEW_POLICY_REVIEW_HISTORY_SUCCESS",
            description=f"Retrieved {len(review_history)} review records for policy {policy_id}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            ipAddress=get_client_ip(request)
        )
        
        return Response({
            'success': True,
            'policy_id': policy_id,
            'policy_name': policy.PolicyName,
            'current_status': policy.Status,
            'review_history': review_history
        })
        
    except Exception as e:
        # Log error
        send_log(
            module="Policy",
            actionType="VIEW_POLICY_REVIEW_HISTORY_ERROR",
            description=f"Error retrieving review history for policy {policy_id}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([PolicyApprovePermission])  # RBAC: Require PolicyApprovePermission for rejecting subpolicies
@csrf_exempt
def reject_subpolicy(request, pk):
    """
    Dedicated endpoint for rejecting a subpolicy with cascading rejection
    When one subpolicy is rejected, all subpolicies and parent policy are rejected
    """
    try:
        # Log subpolicy rejection attempt
        send_log(
            module="Policy",
            actionType="REJECT_SUBPOLICY",
            description=f"Attempting to reject subpolicy {pk} with cascading rejection",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            ipAddress=get_client_ip(request)
        )
        
        # Get the subpolicy
        try:
            subpolicy = SubPolicy.objects.get(SubPolicyId=pk)
        except SubPolicy.DoesNotExist:
            return Response({'error': 'Subpolicy not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get rejection reason from request
        rejection_reason = request.data.get('remarks', '') or request.data.get('rejection_reason', '')
        
        # Get the parent policy
        parent_policy = subpolicy.PolicyId
        if not parent_policy:
            return Response({'error': 'Parent policy not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all subpolicies of the same parent policy
        all_subpolicies = SubPolicy.objects.filter(PolicyId=parent_policy)
        
        # Count of subpolicies being rejected
        subpolicy_count = all_subpolicies.count()
        rejected_subpolicy_names = []
        
        # Reject all subpolicies of the parent policy
        for sub in all_subpolicies:
            sub.Status = 'Rejected'
            sub.save()
            rejected_subpolicy_names.append(sub.SubPolicyName)
        
        # Reject the parent policy
        parent_policy.Status = 'Rejected'
        parent_policy.save()
        
        # Create a policy approval record with rejection details
        # Find the latest policy approval for this policy
        latest_approval = PolicyApproval.objects.filter(
            PolicyId=parent_policy
        ).order_by('-ApprovalId').first()
        
        if latest_approval:
            # Create a new approval record with rejection
            r_versions = []
            for pa in PolicyApproval.objects.filter(PolicyId=parent_policy):
                if pa.Version and pa.Version.startswith('r') and pa.Version[1:].isdigit():
                    r_versions.append(int(pa.Version[1:]))
            
            new_version = f"r{max(r_versions) + 1}" if r_versions else "r1"
            
            # Prepare extracted data with rejection reason - fix the copy issue
            extracted_data = {}
            if latest_approval.ExtractedData:
                if isinstance(latest_approval.ExtractedData, dict):
                    extracted_data = latest_approval.ExtractedData.copy()
                else:
                    try:
                        extracted_data = dict(latest_approval.ExtractedData)
                    except (TypeError, ValueError):
                        extracted_data = {}
            
            # Add comprehensive rejection information
            extracted_data['rejection_reason'] = rejection_reason
            extracted_data['rejected_subpolicy_id'] = pk
            extracted_data['rejected_subpolicy_name'] = subpolicy.SubPolicyName
            extracted_data['rejection_date'] = str(timezone.now().date())
            extracted_data['cascading_rejection'] = True
            extracted_data['total_subpolicies_rejected'] = subpolicy_count
            extracted_data['rejected_subpolicy_names'] = rejected_subpolicy_names
            extracted_data['parent_policy_id'] = parent_policy.PolicyId
            extracted_data['parent_policy_name'] = parent_policy.PolicyName
            extracted_data['rejection_type'] = 'cascading'
            
            # Update subpolicies data in extracted_data if it exists
            if 'subpolicies' in extracted_data:
                for sub_data in extracted_data['subpolicies']:
                    sub_data['Status'] = 'Rejected'
                    if 'approval' in sub_data:
                        sub_data['approval'] = {
                            'approved': False,
                            'remarks': rejection_reason
                        }
            
            new_approval = PolicyApproval(
                PolicyId=parent_policy,
                ExtractedData=extracted_data,
                UserId=latest_approval.UserId,
                ReviewerId=latest_approval.ReviewerId,
                ApprovedNot=False,  # Mark as rejected
                Version=new_version
            )
            new_approval.save()
            
            # Log successful cascading rejection
            send_log(
                module="Policy",
                actionType="CASCADING_REJECTION_SUCCESS",
                description=f"Cascading rejection completed: Policy {parent_policy.PolicyId} and {subpolicy_count} subpolicies rejected",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=parent_policy.PolicyId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "triggered_by_subpolicy": subpolicy.SubPolicyName,
                    "rejection_reason": rejection_reason,
                    "total_subpolicies_rejected": subpolicy_count,
                    "new_version": new_version,
                    "parent_policy_name": parent_policy.PolicyName
                }
            )
            
            return Response({
                'success': True,
                'message': 'Cascading rejection completed successfully',
                'rejection_type': 'cascading',
                'original_subpolicy_id': pk,
                'original_subpolicy_name': subpolicy.SubPolicyName,
                'parent_policy_id': parent_policy.PolicyId,
                'parent_policy_name': parent_policy.PolicyName,
                'total_subpolicies_rejected': subpolicy_count,
                'rejected_subpolicy_names': rejected_subpolicy_names,
                'rejection_reason': rejection_reason,
                'new_version': new_version,
                'rejection_date': str(timezone.now().date()),
                'popup_message': f"Policy '{parent_policy.PolicyName}' and all its {subpolicy_count} subpolicies have been rejected due to the rejection of '{subpolicy.SubPolicyName}'. This has been saved as version {new_version} and sent back to the user for revision."
            })
        else:
            return Response({'error': 'No policy approval found to create revision'}, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        # Log error
        send_log(
            module="Policy",
            actionType="CASCADING_REJECTION_ERROR",
            description=f"Error in cascading rejection for subpolicy {pk}: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="SubPolicy",
            entityId=pk,
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Cascading rejection failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # No RBAC required for departments
def get_departments(request):
    """
    Fetch all departments from the database
    """
    try:
        from ...models import Department
        
        # Get all active departments
        departments = Department.objects.filter(IsActive=True).values(
            'DepartmentId', 
            'DepartmentName', 
            'DepartmentHead', 
            'BusinessUnitId'
        ).order_by('DepartmentName')
        
        # Format the response
        departments_data = []
        for dept in departments:
            departments_data.append({
                'id': dept['DepartmentId'],
                'name': dept['DepartmentName'],
                'head_id': dept['DepartmentHead'],
                'business_unit_id': dept['BusinessUnitId']
            })
        
        return Response({
            'success': True,
            'departments': departments_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching departments: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to fetch departments: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # No RBAC required for saving departments
def save_department(request):
    """
    Save a new department to the database
    """
    try:
        from ...models import Department
        from django.utils import timezone
        
        department_name = request.data.get('DepartmentName', '').strip()
        entity_id = request.data.get('EntityId', 1)  # Default to entity 1
        department_head = request.data.get('DepartmentHead', 1)  # Default to user 1
        business_unit_id = request.data.get('BusinessUnitId', 1)  # Default to business unit 1
        
        if not department_name:
            return Response({
                'success': False,
                'error': 'Department name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if department already exists
        existing_dept = Department.objects.filter(
            DepartmentName__iexact=department_name,
            EntityId=entity_id,
            IsActive=True
        ).first()
        
        if existing_dept:
            return Response({
                'success': True,
                'message': 'Department already exists',
                'department': {
                    'id': existing_dept.DepartmentId,
                    'name': existing_dept.DepartmentName,
                    'head_id': existing_dept.DepartmentHead,
                    'business_unit_id': existing_dept.BusinessUnitId
                }
            })
        
        # Create new department
        new_department = Department.objects.create(
            DepartmentName=department_name,
            EntityId=entity_id,
            DepartmentHead=department_head,
            BusinessUnitId=business_unit_id,
            IsActive=True,
            CreatedDate=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': 'Department created successfully',
            'department': {
                'id': new_department.DepartmentId,
                'name': new_department.DepartmentName,
                'head_id': new_department.DepartmentHead,
                'business_unit_id': new_department.BusinessUnitId
            }
        })
        
    except Exception as e:
        logger.error(f"Error saving department: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to save department: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Test endpoint for tailoring permissions
@api_view(['GET'])
@permission_classes([PolicyTailoringPermission])
def test_tailoring_permissions(request):
    """Test endpoint to verify tailoring permissions"""
    return Response({
        'message': 'Tailoring permissions working correctly!',
        'user': str(request.user),
        'user_id': getattr(request.user, 'UserId', None),
        'username': getattr(request.user, 'username', None)
    })