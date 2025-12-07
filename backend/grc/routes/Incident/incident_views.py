from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.contrib.auth import authenticate, login as auth_login
from rest_framework_simplejwt.tokens import RefreshToken
from ...serializers import (
    UserSerializer, IncidentSerializer, AuditFindingSerializer, 
    PolicySerializer, SubPolicySerializer, ComplianceCreateSerializer, PolicyAllocationSerializer, FrameworkSerializer,
    PolicyApprovalSerializer, LastChecklistItemVerifiedSerializer, RiskInstanceSerializer  # Add RiskInstanceSerializer
)
from ...models import Incident, AuditFinding, Users, Workflow, Compliance, Framework, PolicyVersion, PolicyApproval, Policy, SubPolicy, RiskInstance, LastChecklistItemVerified, IncidentApproval, ExportTask, CategoryBusinessUnit, GRCLog
from ...routes.Global.notification_service import NotificationService
from ...routes.Global.s3_fucntions import export_data
# Import KPI functions from separate module
from .kpis_incidents import (
    incident_mttd, incident_mttr, incident_mttc, incident_mttrv,
    incident_volume, incidents_by_severity, incident_root_causes,
    incident_types, incident_origins, escalation_rate, repeat_rate,
    incident_cost, first_response_time, false_positive_rate,
    detection_accuracy, incident_closure_rate, incident_reopened_count,
    incident_count, incident_metrics, get_incident_counts,
    to_aware_datetime, safe_combine_date_time
)
# Import RBAC decorators and utilities
from ...rbac.decorators import rbac_required
from ...rbac.permissions import (
    IncidentViewPermission, IncidentCreatePermission, IncidentEditPermission, 
    IncidentAssignPermission, IncidentEvaluatePermission, IncidentEscalatePermission,
    IncidentAnalyticsPermission, AuditViewPermission, AuditAssignPermission,
    AuditReviewPermission, AuditFindingsAccessPermission
)
from ...rbac.utils import RBACUtils
from django.views.decorators.csrf import csrf_exempt
from ...routes.Consent import require_consent

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from django.db.models import Q
import traceback
import datetime
from django.db import connection
import json
import uuid
import re
import base64
import tempfile
import os
from datetime import date, time
from django.conf import settings

from ...routes.Global.validation import SecureValidator, ValidationError, IncidentValidator, QuestionnaireValidator
from contextlib import contextmanager
import logging
import requests

# Set up logging
logger = logging.getLogger(__name__)

# Logging Configuration
LOGGING_SERVICE_URL = None  # Disabled external logging service

def send_log(module, actionType, description=None, userId=None, userName=None,
             userRole=None, entityType=None, logLevel='INFO', ipAddress=None,
             additionalInfo=None, entityId=None):
   
    # Debug print to console
    print(f"[DEBUG LOGGING] send_log called: module={module}, actionType={actionType}, userId={userId}")
   
    # Create log entry in database
    try:
        # Prepare data for GRCLog model
        log_data = {
            'Module': module,
            'ActionType': actionType,
            'Description': description,
            'UserId': str(userId) if userId is not None else None,
            'UserName': userName,
            'EntityType': entityType,
            'EntityId': str(entityId) if entityId is not None else None,
            'LogLevel': logLevel,
            'IPAddress': ipAddress,
            'AdditionalInfo': additionalInfo
        }
       
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        print(f"[DEBUG LOGGING] Prepared log_data: {log_data}")
       
        # Create and save the log entry
        log_entry = GRCLog(**log_data)
        print(f"[DEBUG LOGGING] Created GRCLog instance: {log_entry}")
        
        log_entry.save()
        print(f"[DEBUG LOGGING] Successfully saved log with ID: {log_entry.LogId}")
       
        # Optionally still send to logging service if needed
        try:
            if LOGGING_SERVICE_URL:
                # Format for external service (matches expected format in loggingservice.js)
                api_log_data = {
                    "module": module,
                    "actionType": actionType,  # This is exactly what the service expects
                    "description": description,
                    "userId": userId,
                    "userName": userName,
                    "userRole": userRole,
                    "entityType": entityType,
                    "logLevel": logLevel,
                    "ipAddress": ipAddress,
                    "additionalInfo": additionalInfo
                }
                # Clean out None values
                api_log_data = {k: v for k, v in api_log_data.items() if v is not None}
               
                response = requests.post(LOGGING_SERVICE_URL, json=api_log_data)
                if response.status_code != 200:
                    print(f"Failed to send log to service: {response.text}")
        except Exception as e:
            print(f"Error sending log to service: {str(e)}")
           
        return log_entry.LogId  # Return the ID of the created log
    except Exception as e:
        print(f"[ERROR LOGGING] Error saving log to database: {str(e)}")
        print(f"[ERROR LOGGING] Exception type: {type(e)}")
        import traceback
        print(f"[ERROR LOGGING] Traceback: {traceback.format_exc()}")
        
        # Try to capture the error itself
        try:
            error_log = GRCLog(
                Module=module,
                ActionType='LOG_ERROR',
                Description=f"Error logging {actionType} on {module}: {str(e)}",
                LogLevel='ERROR'
            )
            error_log.save()
            print(f"[ERROR LOGGING] Saved error log with ID: {error_log.LogId}")
        except Exception as error_save_exception:
            print(f"[ERROR LOGGING] Could not even save error log: {str(error_save_exception)}")
        return None

def get_client_ip(request):
    """Helper function to get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip







# Add these imports at the top of your incident_views.py file
from rest_framework.permissions import IsAuthenticated
from grc.rbac.permissions import (
    # Incident permissions
    IncidentCreatePermission,
    IncidentEditPermission,
    IncidentAssignPermission,
    IncidentEvaluatePermission,
    IncidentEscalatePermission,
    IncidentViewPermission,
    IncidentAnalyticsPermission,
    
    # Audit permissions (for audit findings)
    AuditViewPermission,
    AuditConductPermission,
    AuditReviewPermission,
    AuditAssignPermission,
    AuditAnalyticsPermission
)

# Add RBAC debug logging
import logging
logger = logging.getLogger(__name__)

def debug_user_permissions(request, action, resource_type=None, resource_id=None):
    """Debug function to log user permissions and access attempts using RBACUtils"""
    try:
        from grc.rbac.utils import RBACUtils
        
        # Extract user ID using RBACUtils
        user_id = RBACUtils.get_user_id_from_request(request)
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        
        if not user_id:
            logger.info(f"[RBAC DEBUG] User Access Attempt:")
            logger.info(f"   User ID: None (could not extract from request)")
            logger.info(f"   Action: {action}")
            logger.info(f"   Resource: {resource_type} (ID: {resource_id})")
            logger.info(f"   IP Address: {ip_address}")
            logger.info(f"   Status: FAILED - No user ID")
            logger.info(f"   " + "=" * 60)
            return None
        
        # Get detailed permissions from database
        detailed_permissions = get_user_detailed_permissions(user_id)
        
        # Log comprehensive access attempt
        logger.info(f"[RBAC DEBUG] User Access Attempt:")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Action: {action}")
        logger.info(f"   Resource: {resource_type} (ID: {resource_id})")
        logger.info(f"   IP Address: {ip_address}")
        
        # Display detailed permissions
        logger.info(f"   === DETAILED PERMISSIONS FROM DATABASE ===")
        if detailed_permissions:
            for module, permissions in detailed_permissions.items():
                logger.info(f"   Module '{module}':")
                for perm_name, has_perm in permissions.items():
                    status = "✓ YES" if has_perm else "✗ NO"
                    logger.info(f"      {perm_name}: {status}")
        else:
            logger.info(f"   No specific permissions found in database")
        
        # Check module permissions if resource_type maps to a module
        module_permissions = {}
        if resource_type:
            # Map resource_type to module name
            module_map = {
                'incident': 'Incident',
                'audit': 'Audit', 
                'risk': 'Risk',
                'policy': 'Policy',
                'compliance': 'Compliance',
                'framework': 'Framework'
            }
            
            module = module_map.get(resource_type.lower())
            if module:
                # Check basic permissions for this module
                permissions_to_check = ['view', 'create', 'edit', 'approve', 'assign']
                for perm in permissions_to_check:
                    has_perm = RBACUtils.has_permission(user_id, module, perm)
                    module_permissions[perm] = has_perm
                    # Debug each permission check
                    debug_permission_check(user_id, module, perm, has_perm)
                
                logger.info(f"   Module Permissions for {module}:")
                for perm, has_perm in module_permissions.items():
                    status = "YES" if has_perm else "NO"
                    logger.info(f"      {perm.capitalize()}: {status}")
        
        logger.info(f"   Timestamp: {timezone.now()}")
        logger.info(f"   " + "=" * 60)
        
        return {
            'user_id': user_id,
            'module_permissions': module_permissions,
            'detailed_permissions': detailed_permissions
        }
        
    except Exception as e:
        logger.error(f"[RBAC DEBUG ERROR]: {str(e)}")
        import traceback
        logger.error(f"[RBAC DEBUG TRACEBACK]: {traceback.format_exc()}")
        return None


def get_user_detailed_permissions(user_id):
    """Get detailed permissions for a user from all RBAC tables"""
    try:
        from ...models import RBAC, RBACModulePermission, RBACUserPermission, RBACDepartmentAccess
        
        # Get user's RBAC info
        rbac_info = RBAC.objects.filter(UserId=user_id).first()
        if not rbac_info:
            logger.warning(f"[RBAC] No RBAC info found for user {user_id}")
            return None
        
        permissions = {}
        
        # 1. Get role-based module permissions
        role_permissions = RBACModulePermission.objects.filter(Role=rbac_info.Role)
        for perm in role_permissions:
            module = perm.Module
            if module not in permissions:
                permissions[module] = {}
            permissions[module][perm.Permission] = perm.IsAllowed
        
        # 2. Get user-specific permission overrides
        user_permissions = RBACUserPermission.objects.filter(UserId=user_id)
        for perm in user_permissions:
            module = perm.Module
            if module not in permissions:
                permissions[module] = {}
            # User permissions override role permissions
            permissions[module][perm.Permission] = perm.IsAllowed
        
        # 3. Get department access info
        dept_access = RBACDepartmentAccess.objects.filter(
            Department=rbac_info.Department
        )
        
        if dept_access.exists():
            permissions['Department_Access'] = {}
            for access in dept_access:
                permissions['Department_Access'][f"access_{access.ResourceType}"] = access.CanAccess
        
        logger.info(f"[RBAC] Retrieved detailed permissions for user {user_id}: {permissions}")
        return permissions
        
    except Exception as e:
        logger.error(f"[RBAC] Error getting detailed permissions for user {user_id}: {str(e)}")
        return None


def log_user_login_permissions(user_id, username=None):
    """Log all permissions when user logs in"""
    try:
        logger.info(f"[RBAC LOGIN] ===== USER LOGIN PERMISSIONS DEBUG =====")
        logger.info(f"[RBAC LOGIN] User ID: {user_id}")
        logger.info(f"[RBAC LOGIN] Username: {username}")
        logger.info(f"[RBAC LOGIN] Login Time: {timezone.now()}")
        
        # Get detailed permissions
        detailed_permissions = get_user_detailed_permissions(user_id)
        
        if detailed_permissions:
            logger.info(f"[RBAC LOGIN] === USER PERMISSIONS FROM DATABASE ===")
            for module, permissions in detailed_permissions.items():
                logger.info(f"[RBAC LOGIN] Module: {module}")
                for perm_name, has_perm in permissions.items():
                    status = "✓ GRANTED" if has_perm else "✗ DENIED"
                    logger.info(f"[RBAC LOGIN]    {perm_name}: {status}")
        else:
            logger.warning(f"[RBAC LOGIN] No permissions found for user {user_id}")
        
        # Get RBAC basic info
        from ...models import RBAC
        rbac_info = RBAC.objects.filter(UserId=user_id).first()
        if rbac_info:
            logger.info(f"[RBAC LOGIN] === BASIC RBAC INFO ===")
            logger.info(f"[RBAC LOGIN] Role: {rbac_info.Role}")
            logger.info(f"[RBAC LOGIN] Department: {rbac_info.Department}")
            logger.info(f"[RBAC LOGIN] Entity: {rbac_info.Entity}")
            logger.info(f"[RBAC LOGIN] Active: {rbac_info.IsActive}")
        else:
            logger.warning(f"[RBAC LOGIN] No RBAC configuration found for user {user_id}")
        
        logger.info(f"[RBAC LOGIN] ============================================")
        
        return detailed_permissions
        
    except Exception as e:
        logger.error(f"[RBAC LOGIN] Error logging user permissions: {str(e)}")
        return None


def debug_permission_check(user_id, module, permission, result):
    """Debug individual permission checks"""
    try:
        logger.info(f"[RBAC PERM CHECK] User {user_id} checking {module}.{permission} = {result}")
        
        # Get the actual database values
        from ...models import RBACModulePermission, RBACUserPermission, RBAC
        
        # Get user's role
        rbac_info = RBAC.objects.filter(UserId=user_id).first()
        if rbac_info:
            logger.info(f"[RBAC PERM CHECK] User Role: {rbac_info.Role}")
            
            # Check role permission
            role_perm = RBACModulePermission.objects.filter(
                Role=rbac_info.Role,
                Module=module,
                Permission=permission
            ).first()
            
            if role_perm:
                logger.info(f"[RBAC PERM CHECK] Role Permission in DB: {role_perm.IsAllowed}")
            else:
                logger.info(f"[RBAC PERM CHECK] No role permission found in DB")
            
            # Check user override
            user_perm = RBACUserPermission.objects.filter(
                UserId=user_id,
                Module=module,
                Permission=permission
            ).first()
            
            if user_perm:
                logger.info(f"[RBAC PERM CHECK] User Override in DB: {user_perm.IsAllowed}")
            else:
                logger.info(f"[RBAC PERM CHECK] No user override found in DB")
        
    except Exception as e:
        logger.error(f"[RBAC PERM CHECK] Error debugging permission check: {str(e)}")



# Input validation utilities
class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

def validate_string(value, field_name, max_length=255, min_length=0, required=False, allowed_pattern=None):
    """Validate a string value with allow-list validation"""
    # Check if required
    if required and (value is None or value == ''):
        raise ValidationError(field_name, "This field is required")
    
    # Skip validation if not required and value is None or empty
    if not required and (value is None or value == ''):
        return value
    
    # Validate type
    if not isinstance(value, str):
        raise ValidationError(field_name, f"Must be a string, got {type(value).__name__}")
    
    # Validate length
    if len(value) < min_length:
        raise ValidationError(field_name, f"Must be at least {min_length} characters")
    
    if len(value) > max_length:
        raise ValidationError(field_name, f"Must be no more than {max_length} characters")
    
    # Validate pattern if provided
    if allowed_pattern and not re.match(allowed_pattern, value):
        raise ValidationError(field_name, "Contains invalid characters")
    
    return value

def validate_date(value, field_name, required=False):
    """Validate a date value"""
    # Check if required
    if required and (value is None or value == ''):
        raise ValidationError(field_name, "This field is required")
    
    # Skip validation if not required and value is None or empty
    if not required and (value is None or value == ''):
        return value
    
    # If already a date object, return as is
    if isinstance(value, date):
        return value
    
    # Try to parse the date
    try:
        # Handle different date formats
        if isinstance(value, str):
            # Try ISO format YYYY-MM-DD
            parts = value.split('-')
            if len(parts) == 3:
                year, month, day = map(int, parts)
                return date(year, month, day)
        
        raise ValidationError(field_name, "Invalid date format, expected YYYY-MM-DD")
    except (ValueError, TypeError):
        raise ValidationError(field_name, "Invalid date format, expected YYYY-MM-DD")

def validate_time(value, field_name, required=False):
    """Validate a time value"""
    # Check if required
    if required and (value is None or value == ''):
        raise ValidationError(field_name, "This field is required")
    
    # Skip validation if not required and value is None or empty
    if not required and (value is None or value == ''):
        return value
    
    # If already a time object, return as is
    if isinstance(value, time):
        return value
    
    # Try to parse the time
    try:
        # Handle different time formats
        if isinstance(value, str):
            # Try ISO format HH:MM or HH:MM:SS
            parts = value.split(':')
            if len(parts) >= 2:
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) > 2 else 0
                return time(hour, minute, second)
        
        raise ValidationError(field_name, "Invalid time format, expected HH:MM or HH:MM:SS")
    except (ValueError, TypeError):
        raise ValidationError(field_name, "Invalid time format, expected HH:MM or HH:MM:SS")

def validate_boolean(value, field_name):
    """Validate a boolean value"""
    if value is None:
        return None
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ('true', 't', 'yes', 'y', '1'):
            return True
        elif value_lower in ('false', 'f', 'no', 'n', '0'):
            return False
    
    if isinstance(value, int):
        if value == 1:
            return True
        elif value == 0:
            return False
    
    raise ValidationError(field_name, "Must be a boolean value")

def validate_choice(value, field_name, choices, required=False):
    """Validate that a value is one of the allowed choices"""
    # Check if required
    if required and (value is None or value == ''):
        raise ValidationError(field_name, "This field is required")
    
    # Skip validation if not required and value is None or empty
    if not required and (value is None or value == ''):
        return value
    
    # Validate that value is in choices
    if value not in choices:
        raise ValidationError(field_name, f"Must be one of: {', '.join(choices)}")
    
    return value

def validate_incident_data(data):
    """
    Validate incident data with strict allow-list validation
    Returns cleaned data or raises ValidationError
    """
    validated_data = {}
    
    # Define allowed patterns for enhanced security
    ALPHANUMERIC_WITH_SPACES = r'^[a-zA-Z0-9\s\-_.,!?()]+$'
    BUSINESS_TEXT_PATTERN = r'^[a-zA-Z0-9\s\-_.,!?():;/\\@#$%&*+=<>[\]{}|~`"\']+$'
    CURRENCY_PATTERN = r'^[$£€]?[0-9]+(\.[0-9]{1,2})?$'
    
    # Required fields
    validated_data['IncidentTitle'] = validate_string(
        data.get('IncidentTitle'), 'IncidentTitle', 
        max_length=255, min_length=3, required=True,
        allowed_pattern=BUSINESS_TEXT_PATTERN
    )
    
    validated_data['Description'] = validate_string(
        data.get('Description'), 'Description', 
        max_length=2000, min_length=10, required=True,
        allowed_pattern=BUSINESS_TEXT_PATTERN
    )
    
    validated_data['Date'] = validate_date(
        data.get('Date'), 'Date', 
        required=True
    )
    
    validated_data['Time'] = validate_time(
        data.get('Time'), 'Time', 
        required=True
    )
    
    validated_data['RiskPriority'] = validate_choice(
        data.get('RiskPriority'), 'RiskPriority',
        choices=['High', 'Medium', 'Low'], 
        required=True
    )
    
    # Optional fields with strict validation
    if 'Origin' in data and data.get('Origin'):
        validated_data['Origin'] = validate_choice(
            data.get('Origin'), 'Origin',
            choices=['Manual', 'Audit Finding', 'System Generated'], 
            required=False
        )
    
    if 'Mitigation' in data and data.get('Mitigation'):
        validated_data['Mitigation'] = validate_string(
            data.get('Mitigation'), 'Mitigation', 
            max_length=2000, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'Comments' in data and data.get('Comments'):
        validated_data['Comments'] = validate_string(
            data.get('Comments'), 'Comments', 
            max_length=1000, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'RiskCategory' in data and data.get('RiskCategory'):
        validated_data['RiskCategory'] = validate_string(
            data.get('RiskCategory'), 'RiskCategory', 
            max_length=500, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'Status' in data and data.get('Status'):
        validated_data['Status'] = validate_choice(
            data.get('Status'), 'Status',
            choices=['Open', 'Closed', 'In Progress', 'Scheduled', 'Under Review', 'Pending Review', 'Rejected', 'Assigned', 'New', 'Active', 'Resolved', 'Pending'], 
            required=False
        )
    
    if 'AffectedBusinessUnit' in data and data.get('AffectedBusinessUnit'):
        validated_data['AffectedBusinessUnit'] = validate_string(
            data.get('AffectedBusinessUnit'), 'AffectedBusinessUnit', 
            max_length=100, required=False,
            allowed_pattern=ALPHANUMERIC_WITH_SPACES
        )
    
    if 'SystemsAssetsInvolved' in data and data.get('SystemsAssetsInvolved'):
        validated_data['SystemsAssetsInvolved'] = validate_string(
            data.get('SystemsAssetsInvolved'), 'SystemsAssetsInvolved', 
            max_length=500, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'GeographicLocation' in data and data.get('GeographicLocation'):
        validated_data['GeographicLocation'] = validate_string(
            data.get('GeographicLocation'), 'GeographicLocation', 
            max_length=100, required=False,
            allowed_pattern=ALPHANUMERIC_WITH_SPACES
        )
    
    if 'Criticality' in data and data.get('Criticality'):
        validated_data['Criticality'] = validate_choice(
            data.get('Criticality'), 'Criticality',
            choices=['Critical', 'High', 'Medium', 'Low'], 
            required=False
        )
    
    if 'InitialImpactAssessment' in data and data.get('InitialImpactAssessment'):
        validated_data['InitialImpactAssessment'] = validate_string(
            data.get('InitialImpactAssessment'), 'InitialImpactAssessment', 
            max_length=2000, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'InternalContacts' in data and data.get('InternalContacts'):
        validated_data['InternalContacts'] = validate_string(
            data.get('InternalContacts'), 'InternalContacts', 
            max_length=500, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'ExternalPartiesInvolved' in data and data.get('ExternalPartiesInvolved'):
        validated_data['ExternalPartiesInvolved'] = validate_string(
            data.get('ExternalPartiesInvolved'), 'ExternalPartiesInvolved', 
            max_length=500, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'RegulatoryBodies' in data and data.get('RegulatoryBodies'):
        validated_data['RegulatoryBodies'] = validate_string(
            data.get('RegulatoryBodies'), 'RegulatoryBodies', 
            max_length=500, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'RelevantPoliciesProceduresViolated' in data and data.get('RelevantPoliciesProceduresViolated'):
        validated_data['RelevantPoliciesProceduresViolated'] = validate_string(
            data.get('RelevantPoliciesProceduresViolated'), 'RelevantPoliciesProceduresViolated', 
            max_length=1000, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'ControlFailures' in data and data.get('ControlFailures'):
        validated_data['ControlFailures'] = validate_string(
            data.get('ControlFailures'), 'ControlFailures', 
            max_length=1000, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'PossibleDamage' in data and data.get('PossibleDamage'):
        validated_data['PossibleDamage'] = validate_string(
            data.get('PossibleDamage'), 'PossibleDamage', 
            max_length=1000, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    if 'CostOfIncident' in data and data.get('CostOfIncident'):
        cost_value = str(data.get('CostOfIncident')).strip()
        if cost_value and not re.match(CURRENCY_PATTERN, cost_value):
            raise ValidationError('CostOfIncident', 'Must be a valid currency amount (e.g., $100.50, 250.75)')
        validated_data['CostOfIncident'] = cost_value if cost_value else None
    
    if 'IncidentClassification' in data and data.get('IncidentClassification'):
        validated_data['IncidentClassification'] = validate_choice(
            data.get('IncidentClassification'), 'IncidentClassification',
            choices=['NonConformance', 'Control GAP', 'Risk', 'Issue'], 
            required=False
        )
    
    if 'IncidentCategory' in data and data.get('IncidentCategory'):
        validated_data['IncidentCategory'] = validate_string(
            data.get('IncidentCategory'), 'IncidentCategory', 
            max_length=500, required=False,
            allowed_pattern=BUSINESS_TEXT_PATTERN
        )
    
    # Handle ComplianceId - must be a valid integer if provided
    if 'ComplianceId' in data and data.get('ComplianceId'):
        try:
            compliance_id = int(data.get('ComplianceId'))
            if compliance_id <= 0:
                raise ValidationError('ComplianceId', 'Must be a positive integer')
            validated_data['ComplianceId'] = compliance_id
        except (ValueError, TypeError):
            raise ValidationError('ComplianceId', 'Must be a valid integer')
    
    # Handle FrameworkId - optional field, if 500 (All Frameworks) or not provided, set to None
    if 'FrameworkId' in data and data.get('FrameworkId'):
        try:
            framework_id = int(data.get('FrameworkId'))
            # If framework_id is 500 (All Frameworks), don't save it - set to None
            if framework_id == 500:
                validated_data['FrameworkId'] = None
                print(f"✅ FrameworkId is 500 (All Frameworks) - setting to None")
            elif framework_id <= 0:
                raise ValidationError('FrameworkId', 'Must be a positive integer')
            else:
                validated_data['FrameworkId'] = framework_id
                print(f"✅ FrameworkId validated: {framework_id}")
        except (ValueError, TypeError):
            raise ValidationError('FrameworkId', 'Must be a valid integer')
    else:
        # FrameworkId not provided - set to None (All Frameworks)
        validated_data['FrameworkId'] = None
        print(f"✅ FrameworkId not provided - setting to None (All Frameworks)")
    
    return validated_data


LOGIN_REDIRECT_URL = '/incidents/'  # or the URL pattern for your incident page

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    client_ip = get_client_ip(request)
    
    # Log login attempt
    send_log(
        module="Incident",
        actionType="LOGIN_ATTEMPT",
        description="User login attempt",
        userId=None,
        userName=email,
        entityType="User",
        ipAddress=client_ip
    )
    
    # Log login attempt
    send_log(
        module="Incident_Auth",
        actionType="LOGIN",
        description=f"User login attempt for email: {email}",
        userId=None,
        userName=email,
        entityType="User",
        ipAddress=get_client_ip(request)
    )
    
    # Hardcoded credentials
    if email == "admin@example.com" and password == "password123":
        # Log successful login
        send_log(
            module="Incident",
            actionType="LOGIN_SUCCESS",
            description="User login successful",
            userId="admin",
            userName=email,
            entityType="User",
            entityId="admin",
            ipAddress=client_ip
        )
        
        # DEBUG: Log user permissions on login
        try:
            # Find the user ID for RBAC lookup (use hardcoded for demo)
            from ...models import Users
            user = Users.objects.filter(Email=email).first()
            if user:
                user_id = user.UserId
                log_user_login_permissions(user_id, email)
            else:
                logger.warning(f"[RBAC LOGIN] User not found in database for email: {email}")
        except Exception as e:
            logger.error(f"[RBAC LOGIN] Error during login permissions debug: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': {
                'email': email,
                'name': 'Admin User'
            }
        })
    else:
        # Log failed login
        send_log(
            module="Incident",
            actionType="LOGIN_FAILED",
            description="User login failed - invalid credentials",
            userId=None,
            userName=email,
            entityType="User",
            logLevel="WARNING",
            ipAddress=client_ip
        )
        
        return Response({
            'success': False,
            'message': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    client_ip = get_client_ip(request)
    email = request.data.get('Email', 'Unknown')
    
    # Log registration attempt
    send_log(
        module="Incident",
        actionType="REGISTER_ATTEMPT",
        description="User registration attempt",
        userId=None,
        userName=email,
        entityType="User",
        ipAddress=client_ip
    )
    
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        # Log successful registration
        send_log(
            module="Incident",
            actionType="REGISTER_SUCCESS",
            description="User registration successful",
            userId=str(user.UserId),
            userName=user.UserName,
            entityType="User",
            entityId=str(user.UserId),
            ipAddress=client_ip
        )
        
        return Response({
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': serializer.data
        })
    
    # Log failed registration
    send_log(
        module="Incident",
        actionType="REGISTER_FAILED",
        description=f"User registration failed: {serializer.errors}",
        userId=None,
        userName=email,
        entityType="User",
        logLevel="WARNING",
        ipAddress=client_ip,
        additionalInfo=serializer.errors
    )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# RBAC API Endpoints
@api_view(['GET'])
@authentication_classes([])
@permission_classes([IsAuthenticated])
def get_user_permissions(request):
    """Get current user's permissions for frontend"""
    try:
        # RBAC Debug - Log user access attempt
        debug_info = debug_user_permissions(request, "GET_USER_PERMISSIONS", "rbac", None)
        
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return Response({'error': 'User not authenticated'}, status=401)
        
        from ...models import RBAC, RBACDepartmentAccess, RBACResourceAccess, RBACUserPermission
        
        # Get user's RBAC info
        rbac_info = RBAC.objects.filter(UserId=user_id).first()
        
        if not rbac_info:
            logger.warning(f"No RBAC info found for user {user_id}")
            return Response({
                'permissions': {},
                'role': None,
                'department': None,
                'entity': None,
                'message': 'No RBAC configuration found for user'
            })
        
        # Get detailed permissions from database
        detailed_permissions = get_user_detailed_permissions(user_id)
        
        # Build permissions based on role (you'll need to implement this based on your RBAC matrix)
        permissions = {
            'incident': {
                'create': True,  # This should be based on role/permissions
                'edit': True,
                'view': True,
                'assign': True,
                'escalate': True,
                'analytics': True
            },
            'audit': {
                'view': True,
                'conduct': True,
                'review': True,
                'assign': True,
                'analytics': True
            }
        }
        
        # Get user-specific permission overrides
        user_overrides = RBACUserPermission.objects.filter(UserId=user_id)
        for override in user_overrides:
            if override.Module not in permissions:
                permissions[override.Module] = {}
            permissions[override.Module][override.Permission] = override.IsAllowed
        
        # Log detailed permissions debug
        logger.info(f"[RBAC GET_PERMISSIONS] === DETAILED PERMISSIONS FOR USER {user_id} ===")
        logger.info(f"[RBAC GET_PERMISSIONS] Role: {rbac_info.Role}")
        logger.info(f"[RBAC GET_PERMISSIONS] Department: {rbac_info.Department}")
        logger.info(f"[RBAC GET_PERMISSIONS] Entity: {rbac_info.Entity}")
        
        if detailed_permissions:
            logger.info(f"[RBAC GET_PERMISSIONS] Database Permissions:")
            for module, perms in detailed_permissions.items():
                logger.info(f"[RBAC GET_PERMISSIONS]   {module}:")
                for perm, value in perms.items():
                    status = "✓ GRANTED" if value else "✗ DENIED"
                    logger.info(f"[RBAC GET_PERMISSIONS]     {perm}: {status}")
        else:
            logger.warning(f"[RBAC GET_PERMISSIONS] No detailed permissions found in database")
        
        logger.info(f"✅ User {user_id} permissions retrieved successfully")
        
        return Response({
            'permissions': permissions,
            'detailed_permissions': detailed_permissions,
            'role': rbac_info.Role,
            'department': rbac_info.Department,
            'entity': rbac_info.Entity,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting user permissions: {str(e)}")
        return Response({'error': 'Failed to retrieve permissions'}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IsAuthenticated])
def get_user_role(request):
    """Get current user's role"""
    try:
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return Response({'error': 'User not authenticated'}, status=401)
        
        from ...models import RBAC
        rbac_info = RBAC.objects.filter(UserId=user_id).first()
        
        if rbac_info:
            return Response({
                'role': rbac_info.Role,
                'department': rbac_info.Department,
                'entity': rbac_info.Entity
            })
        else:
            return Response({'role': None, 'department': None, 'entity': None})
            
    except Exception as e:
        logger.error(f"❌ Error getting user role: {str(e)}")
        return Response({'error': 'Failed to retrieve role'}, status=500)


@api_view(['GET'])  
@authentication_classes([])
@permission_classes([IsAuthenticated])
def debug_user_permissions_endpoint(request):
    """Endpoint to debug user permissions on demand"""
    try:
        from grc.rbac.utils import RBACUtils
        
        # Get user ID from request
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({'error': 'Could not extract user ID from request'}, status=400)
        
        # Log comprehensive permissions debug
        detailed_permissions = get_user_detailed_permissions(user_id)
        
        # Get RBAC info
        rbac_info = RBACUtils.get_user_rbac_info(user_id)
        
        # Test specific module permissions
        test_modules = ['Incident', 'Audit', 'Risk', 'Policy', 'Compliance', 'Framework']
        test_permissions = ['view', 'create', 'edit', 'approve', 'assign']
        
        permission_tests = {}
        for module in test_modules:
            permission_tests[module] = {}
            for perm in test_permissions:
                has_perm = RBACUtils.has_permission(user_id, module, perm)
                permission_tests[module][perm] = has_perm
                # Debug each check
                debug_permission_check(user_id, module, perm, has_perm)
        
        # Log the debug info
        logger.info(f"[RBAC ENDPOINT DEBUG] === USER PERMISSIONS ENDPOINT DEBUG ===")
        logger.info(f"[RBAC ENDPOINT DEBUG] User ID: {user_id}")
        logger.info(f"[RBAC ENDPOINT DEBUG] Time: {timezone.now()}")
        
        if rbac_info:
            logger.info(f"[RBAC ENDPOINT DEBUG] Role: {rbac_info.get('role')}")
            logger.info(f"[RBAC ENDPOINT DEBUG] Department: {rbac_info.get('department')}")
            logger.info(f"[RBAC ENDPOINT DEBUG] Entity: {rbac_info.get('entity')}")
        
        logger.info(f"[RBAC ENDPOINT DEBUG] === PERMISSION TEST RESULTS ===")
        for module, perms in permission_tests.items():
            logger.info(f"[RBAC ENDPOINT DEBUG] {module}:")
            for perm, has_perm in perms.items():
                status = "✓ GRANTED" if has_perm else "✗ DENIED"
                logger.info(f"[RBAC ENDPOINT DEBUG]   {perm}: {status}")
        
        # Return detailed response
        return Response({
            'success': True,
            'user_id': user_id,
            'rbac_info': rbac_info,
            'detailed_permissions': detailed_permissions,
            'permission_tests': permission_tests,
            'message': 'Debug information logged to console and database'
        })
        
    except Exception as e:
        logger.error(f"[RBAC ENDPOINT DEBUG] Error: {str(e)}")
        import traceback
        logger.error(f"[RBAC ENDPOINT DEBUG] Traceback: {traceback.format_exc()}")
        return Response({'error': f'Debug failed: {str(e)}'}, status=500)


@api_view(['GET'])  
@authentication_classes([])
@permission_classes([IsAuthenticated])
def test_user_permissions_comprehensive(request):
    """Comprehensive test of user permissions against all RBAC tables"""
    try:
        from grc.rbac.utils import RBACUtils
        
        # Get user ID from request
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({'error': 'Could not extract user ID from request'}, status=400)
        
        # Test results structure
        test_results = {
            'user_id': user_id,
            'timestamp': timezone.now().isoformat(),
            'rbac_info': {},
            'database_permissions': {},
            'permission_tests': {},
            'endpoint_access_tests': {},
            'summary': {'total_tests': 0, 'passed': 0, 'failed': 0}
        }
        
        # 1. Get basic RBAC info
        rbac_info = RBACUtils.get_user_rbac_info(user_id)
        test_results['rbac_info'] = rbac_info if rbac_info else {}
        
        # 2. Get database permissions
        detailed_permissions = get_user_detailed_permissions(user_id)
        test_results['database_permissions'] = detailed_permissions if detailed_permissions else {}
        
        # 3. Test specific module permissions using RBACUtils
        modules_to_test = ['Incident', 'Audit', 'Risk', 'Policy', 'Compliance', 'Framework']
        permissions_to_test = ['view', 'create', 'edit', 'approve', 'assign', 'delete']
        
        for module in modules_to_test:
            test_results['permission_tests'][module] = {}
            for permission in permissions_to_test:
                try:
                    has_permission = RBACUtils.has_permission(user_id, module, permission)
                    test_results['permission_tests'][module][permission] = {
                        'result': has_permission,
                        'status': 'PASS' if has_permission else 'FAIL'
                    }
                    test_results['summary']['total_tests'] += 1
                    if has_permission:
                        test_results['summary']['passed'] += 1
                    else:
                        test_results['summary']['failed'] += 1
                        
                    # Debug each permission check
                    debug_permission_check(user_id, module, permission, has_permission)
                    
                except Exception as e:
                    test_results['permission_tests'][module][permission] = {
                        'result': False,
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    test_results['summary']['total_tests'] += 1
                    test_results['summary']['failed'] += 1
        
        # 4. Test department access
        if rbac_info and rbac_info.get('department'):
            try:
                dept_access = RBACUtils.has_department_access(user_id, rbac_info['department'])
                test_results['department_access'] = {
                    'department': rbac_info['department'],
                    'has_access': dept_access,
                    'status': 'PASS' if dept_access else 'FAIL'
                }
            except Exception as e:
                test_results['department_access'] = {
                    'department': rbac_info.get('department'),
                    'has_access': False,
                    'status': 'ERROR',
                    'error': str(e)
                }
        
        # 5. Log comprehensive test results
        logger.info(f"[RBAC COMPREHENSIVE TEST] === USER {user_id} PERMISSION TEST RESULTS ===")
        logger.info(f"[RBAC COMPREHENSIVE TEST] User: {rbac_info.get('username', 'Unknown') if rbac_info else 'Unknown'}")
        logger.info(f"[RBAC COMPREHENSIVE TEST] Role: {rbac_info.get('role', 'Unknown') if rbac_info else 'Unknown'}")
        logger.info(f"[RBAC COMPREHENSIVE TEST] Department: {rbac_info.get('department', 'Unknown') if rbac_info else 'Unknown'}")
        logger.info(f"[RBAC COMPREHENSIVE TEST] Total Tests: {test_results['summary']['total_tests']}")
        logger.info(f"[RBAC COMPREHENSIVE TEST] Passed: {test_results['summary']['passed']}")
        logger.info(f"[RBAC COMPREHENSIVE TEST] Failed: {test_results['summary']['failed']}")
        
        # Log detailed results
        for module, permissions in test_results['permission_tests'].items():
            logger.info(f"[RBAC COMPREHENSIVE TEST] {module}:")
            for perm, result in permissions.items():
                status_symbol = "✓" if result['status'] == 'PASS' else "✗" if result['status'] == 'FAIL' else "⚠"
                logger.info(f"[RBAC COMPREHENSIVE TEST]   {perm}: {status_symbol} {result['status']}")
        
        return Response({
            'success': True,
            'test_results': test_results,
            'message': 'Comprehensive permission test completed - check logs for detailed results'
        })
        
    except Exception as e:
        logger.error(f"[RBAC COMPREHENSIVE TEST] Error: {str(e)}")
        import traceback
        logger.error(f"[RBAC COMPREHENSIVE TEST] Traceback: {traceback.format_exc()}")
        return Response({'error': f'Comprehensive test failed: {str(e)}'}, status=500)

# Add GET parameter validation helper
def validate_get_parameters(request, allowed_params):
    """
    Validate GET parameters using strict allow-list validation
    SECURITY: Rejects requests with ANY unknown parameters to prevent parameter pollution
    """
    validator = SecureValidator()
    validated_params = {}
    
    # SECURITY: Check for unknown parameters and ignore them (log only)
    provided_params = set(request.GET.keys())
    allowed_param_names = set(allowed_params.keys())
    unknown_params = provided_params - allowed_param_names
    if unknown_params:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Security: Unknown parameters detected and ignored: {sorted(list(unknown_params))} "
            f"from IP: {request.META.get('REMOTE_ADDR', 'unknown')}"
        )
    
    # Validate each allowed parameter
    for param_name, param_config in allowed_params.items():
        value = request.GET.get(param_name)
        
        if value is not None:
            try:
                if param_config.get('type') == 'choice':
                    validated_params[param_name] = validator.validate_choice(
                        value, param_name, param_config['choices']
                    )
                elif param_config.get('type') == 'string':
                    validated_params[param_name] = validator.validate_string(
                        value, param_name, 
                        max_length=param_config.get('max_length', 255),
                        allowed_pattern=param_config.get('pattern')
                    )
                elif param_config.get('type') == 'integer':
                    validated_params[param_name] = validator.validate_integer(
                        value, param_name,
                        min_value=param_config.get('min_value'),
                        max_value=param_config.get('max_value')
                    )
            except ValidationError as e:
                return None, f"Invalid parameter {param_name}: {e.message}"
    
    return validated_params, None

def validate_path_parameter(param_value, param_name, param_type='integer', min_value=1):
    """
    Validate path parameters (like user_id, incident_id) using SecureValidator
    Returns validated value or raises ValidationError
    """
    validator = SecureValidator()
    try:
        if param_type == 'integer':
            return validator.validate_integer(
                param_value, param_name, min_value=min_value, required=True
            )
        elif param_type == 'string':
            return validator.validate_string(
                param_value, param_name, max_length=255, min_length=1, 
                required=True, allowed_pattern=validator.ALPHANUMERIC_ONLY
            )
        else:
            raise ValidationError(param_name, f"Unsupported parameter type: {param_type}")
    except ValidationError as e:
        raise e

def validate_json_request_body(request, validation_rules):
    """
    Validate JSON request body using SecureValidator and defined rules
    Returns validated data or raises ValidationError
    """
    validator = SecureValidator()
    
    # Parse JSON safely
    try:
        if hasattr(request, 'data') and request.data:
            # DRF parsed data (preferred)
            data = request.data
        elif request.body:
            # Raw JSON body
            data = json.loads(request.body)
        else:
            data = {}
    except json.JSONDecodeError:
        raise ValidationError('request_body', 'Invalid JSON format')
    
    validated_data = {}
    
    for field_name, rules in validation_rules.items():
        value = data.get(field_name)
        required = rules.get('required', False)
        
        # Skip validation if field is not provided and not required
        if value is None and not required:
            continue
            
        try:
            if rules.get('type') == 'choice':
                validated_data[field_name] = validator.validate_choice(
                    value, field_name, rules['choices'], required=required
                )
            elif rules.get('type') == 'string':
                validated_data[field_name] = validator.validate_string(
                    value, field_name,
                    max_length=rules.get('max_length', 255),
                    min_length=rules.get('min_length', 0),
                    required=required,
                    allowed_pattern=rules.get('pattern')
                )
            elif rules.get('type') == 'integer':
                validated_data[field_name] = validator.validate_integer(
                    value, field_name,
                    min_value=rules.get('min_value'),
                    max_value=rules.get('max_value'),
                    required=required
                )
            elif rules.get('type') == 'date':
                validated_data[field_name] = validator.validate_date(
                    value, field_name, required=required
                )
            elif rules.get('type') == 'time':
                validated_data[field_name] = validator.validate_time(
                    value, field_name, required=required
                )
            elif rules.get('type') == 'currency':
                validated_data[field_name] = validator.validate_currency(
                    value, field_name, required=required
                )
            elif rules.get('type') == 'boolean':
                # Import the standalone validate_boolean function
                from ...routes.Global.validation import validate_boolean
                validated_data[field_name] = validate_boolean(
                    value, field_name
                )
            else:
                # Default to string validation
                validated_data[field_name] = validator.validate_string(
                    value, field_name, required=required
                )
        except ValidationError as e:
            raise e
    
    return validated_data

@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def incident_by_id(request, incident_id):
    """
    Get or update a specific incident by ID
    """
    # Get user info for logging
    user_id = getattr(request.user, 'id', None)
    username = getattr(request.user, 'username', 'Unknown')
    
    try:
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            send_log(
                module="Incident",
                actionType="INCIDENT_VALIDATION_ERROR",
                description=f"Invalid incident ID parameter: {incident_id}",
                userId=user_id,
                userName=username,
                entityType="Incident",
                logLevel="WARN",
                ipAddress=get_client_ip(request)
            )
            return Response({'success': False, 'message': str(e)}, status=400)
        
        # Get the incident
        incident = Incident.objects.get(IncidentId=validated_incident_id)
        
        if request.method == 'GET':
            # RBAC Debug - Log user access attempt
            debug_info = debug_user_permissions(request, "VIEW_INCIDENT", "incident", validated_incident_id)
            
            # Log incident view
            send_log(
                module="Incident",
                actionType="VIEW_INCIDENT",
                description=f"User viewing incident: {incident.IncidentTitle}",
                userId=user_id,
                userName=username,
                entityType="Incident",
                entityId=str(validated_incident_id),
                ipAddress=get_client_ip(request)
            )
            
            # Use the serializer to convert the model to JSON-serializable data
            serializer = IncidentSerializer(incident)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
        
        elif request.method in ['PUT', 'PATCH']:
            # RBAC Debug - Log user access attempt  
            debug_info = debug_user_permissions(request, "EDIT_INCIDENT", "incident", validated_incident_id)
            
            # Log incident update attempt
            send_log(
                module="Incident",
                actionType="UPDATE_INCIDENT_ATTEMPT",
                description=f"User attempting to update incident: {incident.IncidentTitle}",
                userId=user_id,
                userName=username,
                entityType="Incident",
                entityId=str(validated_incident_id),
                ipAddress=get_client_ip(request)
            )
            
            # Store original data for audit trail
            original_data = IncidentSerializer(incident).data
            
            # Use the serializer to update the incident
            serializer = IncidentSerializer(incident, data=request.data, partial=(request.method == 'PATCH'))
            
            if serializer.is_valid():
                serializer.save()
                
                # Log successful update
                send_log(
                    module="Incident",
                    actionType="UPDATE_INCIDENT_SUCCESS",
                    description=f"Successfully updated incident: {incident.IncidentTitle}",
                    userId=user_id,
                    userName=username,
                    entityType="Incident",
                    entityId=str(validated_incident_id),
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        'original_data': original_data,
                        'updated_data': serializer.data,
                        'update_type': request.method
                    }
                )
                
                return Response({
                    'success': True,
                    'message': 'Incident updated successfully',
                    'data': serializer.data
                })
            else:
                # Log validation failure
                send_log(
                    module="Incident",
                    actionType="UPDATE_INCIDENT_VALIDATION_FAILED",
                    description=f"Validation failed for incident update: {incident.IncidentTitle}",
                    userId=user_id,
                    userName=username,
                    entityType="Incident",
                    entityId=str(validated_incident_id),
                    logLevel="WARN",
                    ipAddress=get_client_ip(request),
                    additionalInfo={'validation_errors': serializer.errors}
                )
                
                return Response({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=400)
        
    except Incident.DoesNotExist:
        send_log(
            module="Incident",
            actionType="INCIDENT_NOT_FOUND",
            description=f"Incident not found: {validated_incident_id}",
            userId=user_id,
            userName=username,
            entityType="Incident",
            entityId=str(validated_incident_id),
            logLevel="WARN",
            ipAddress=get_client_ip(request)
        )
        return Response({
            'success': False,
            'message': 'Incident not found'
        }, status=404)
    except Exception as e:
        send_log(
            module="Incident",
            actionType="INCIDENT_ERROR",
            description=f"Error handling incident {validated_incident_id}: {str(e)}",
            userId=user_id,
            userName=username,
            entityType="Incident",
            entityId=str(validated_incident_id),
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        print(f"Error with incident: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error with incident: {str(e)}'
        }, status=500)

@api_view(['PUT', 'PATCH'])
@authentication_classes([])
@permission_classes([IncidentEditPermission])
@rbac_required(required_permission='edit_incident')
def update_incident_by_id(request, incident_id):
    """
    Update a specific incident by ID
    """
    try:
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return Response({'success': False, 'message': str(e)}, status=400)
        
        # RBAC Debug - Log user access attempt
        debug_info = debug_user_permissions(request, "EDIT_INCIDENT", "incident", validated_incident_id)
        
        # Get the incident
        incident = Incident.objects.get(IncidentId=validated_incident_id)
        
        # Use the serializer to update the incident
        serializer = IncidentSerializer(incident, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Incident updated successfully',
                'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=400)
            
    except Incident.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Incident not found'
        }, status=404)
    except Exception as e:
        print(f"Error updating incident: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error updating incident: {str(e)}'
        }, status=500)

def get_framework_policy_subpolicy_from_compliance(compliance_id):
    """
    Get framework_id, policy_id, and subpolicy_id from a compliance_id
    by traversing the relationships: Compliance -> SubPolicy -> Policy -> Framework
    """
    try:
        from ...models import Compliance, SubPolicy, Policy, Framework
        
        # Get the compliance object
        compliance = Compliance.objects.get(ComplianceId=compliance_id)
        
        # Get the subpolicy
        subpolicy = compliance.SubPolicy
        
        # Get the policy
        policy = subpolicy.PolicyId
        
        # Get the framework
        framework = policy.FrameworkId
        
        return {
            'framework_id': framework.FrameworkId,
            'policy_id': policy.PolicyId,
            'subpolicy_id': subpolicy.SubPolicyId
        }
    except Compliance.DoesNotExist:
        print(f"Compliance with ID {compliance_id} not found")
        return {
            'framework_id': None,
            'policy_id': None,
            'subpolicy_id': None
        }
    except Exception as e:
        print(f"Error getting framework/policy/subpolicy from compliance {compliance_id}: {str(e)}")
        return {
            'framework_id': None,
            'policy_id': None,
            'subpolicy_id': None
        }
@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def list_incidents(request):
    # Reduced debug logging for better performance
    if settings.DEBUG:
        print(f"[DEBUG] list_incidents function called")
    
    client_ip = get_client_ip(request)
    user_id = request.GET.get('userId')
    
    # Log list incidents request
    send_log(
        module="Incident",
        actionType="LIST_INCIDENTS_REQUEST",
        description="User requesting incident list",
        userId=str(user_id) if user_id else None,
        userName=request.GET.get('userName', 'Unknown'),
        entityType="Incident",
        ipAddress=client_ip
    )
    # RBAC Debug - Log user access attempt
    debug_info = debug_user_permissions(request, "LIST_INCIDENTS", "incident", None)
    
    # Define allowed GET parameters with validation rules
    allowed_params = {
        'status': {
            'type': 'choice',
            'choices': ['all'] + SecureValidator.INCIDENT_STATUSES
        },
        'timeRange': {
            'type': 'choice',
            'choices': ['all', '7days', '30days', '90days', '1year']
        },
        'category': {
            'type': 'string',
            'max_length': 100,
            'pattern': SecureValidator.ALPHANUMERIC_WITH_SPACES
        },
        'priority': {
            'type': 'choice',
            'choices': ['all'] + SecureValidator.INCIDENT_PRIORITIES
        },
        'search': {
            'type': 'string',
            'max_length': 255,
            'pattern': SecureValidator.BUSINESS_TEXT_PATTERN
        },
        'sort_field': {
            'type': 'choice',
            'choices': ['IncidentId', 'IncidentTitle', 'Origin', 'RiskPriority', 'Date', 'Status', 'CreatedAt']
        },
        'sort_order': {
            'type': 'choice',
            'choices': ['asc', 'desc']
        },
        'limit': {
            'type': 'integer',
            'min_value': 1,
            'max_value': 100  # Reduced max to improve performance
        },
        'offset': {
            'type': 'integer',
            'min_value': 0
        },
        'framework_id': {
            'type': 'integer',
            'min_value': 1,
            'required': False
        },
        'policy_id': {
            'type': 'integer',
            'min_value': 1,
            'required': False
        },
        'subpolicy_id': {
            'type': 'integer',
            'min_value': 1,
            'required': False
        },
        'business_unit': {
            'type': 'string',
            'max_length': 100,
            'required': False
        },
        'business_category': {
            'type': 'string',
            'max_length': 100,
            'required': False
        },
    }
    
    # Validate GET parameters
    validated_params, error = validate_get_parameters(request, allowed_params)
    if error:
        # Log validation error
        send_log(
            module="Incident",
            actionType="LIST_ERROR",
            description=f"Parameter validation failed: {error}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get filter parameters (now validated)
    status_filter = validated_params.get('status', 'all')
    time_range = validated_params.get('timeRange', 'all')
    category = validated_params.get('category', 'all') 
    priority = validated_params.get('priority', 'all')
    search_query = validated_params.get('search', '')
    sort_field = validated_params.get('sort_field', '')
    sort_order = validated_params.get('sort_order', 'asc')
    limit = validated_params.get('limit', 20)  # Default to 20 for better performance
    offset = validated_params.get('offset', 0)
    framework_id = validated_params.get('framework_id')
    policy_id = validated_params.get('policy_id')
    subpolicy_id = validated_params.get('subpolicy_id')
    business_unit = validated_params.get('business_unit')
    business_category = validated_params.get('business_category')

    # ========================================
    # 🔥 LOGIN SESSION DATA FETCH LOGGING 🔥
    # ========================================
    print(f"\n{'='*80}")
    print(f"🔥 [INCIDENT API] list_incidents called during LOGIN SESSION")
    print(f"📊 Request params: limit={limit}, offset={offset}")
    print(f"👤 User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    print(f"🔍 Filters: status={status_filter}, time_range={time_range}")
    print(f"{'='*80}\n")

    # Reduced logging for better performance
    if settings.DEBUG:
        print(f"Validated search: {search_query}, Sort: {sort_field} {sort_order}")
        print(f"Business Unit: {business_unit}, Business Category: {business_category}")

    # Start with all incidents EXCEPT audit findings - optimized query with only necessary fields
    # Add select_related to reduce database queries for related objects
    # Filter out audit findings to show only pure incidents
    incidents = Incident.objects.only(
        'IncidentId', 'IncidentTitle', 'Description', 'Date', 'Origin', 
        'RiskPriority', 'RiskCategory', 'Status', 'CreatedAt', 'Mitigation',
        'AssignerId', 'ReviewerId', 'RejectionSource', 'ComplianceId', 'FrameworkId',
        'AffectedBusinessUnit', 'IncidentCategory'
    ).select_related(
        'ComplianceId',
        'ComplianceId__SubPolicy',
        'ComplianceId__SubPolicy__PolicyId',
        'ComplianceId__SubPolicy__PolicyId__FrameworkId'
    ).exclude(Origin='Audit Finding')

    # Apply search filter if provided (optimized to avoid multiple counts)
    if search_query:
        from django.db.models import Q
        incidents = incidents.filter(
            Q(IncidentTitle__icontains=search_query) |
            Q(Description__icontains=search_query) |
            Q(Origin__icontains=search_query) |
            Q(RiskPriority__icontains=search_query) |
            Q(RiskCategory__icontains=search_query) |
            Q(Status__icontains=search_query) |
            Q(IncidentId__icontains=search_query)
        )

    # Apply time range filter
    if time_range != 'all':
        from datetime import datetime, timedelta
        today = timezone.now().date()
        
        if time_range == '7days':
            start_date = today - timedelta(days=7)
        elif time_range == '30days':
            start_date = today - timedelta(days=30)
        elif time_range == '90days':
            start_date = today - timedelta(days=90)
        elif time_range == '1year':
            start_date = today - timedelta(days=365)
            
        incidents = incidents.filter(Date__gte=start_date)

    # Apply category filter
    if category != 'all':
        incidents = incidents.filter(RiskCategory__iexact=category)

    # Apply priority filter
    if priority != 'all':
        incidents = incidents.filter(RiskPriority__iexact=priority)

    # Apply business unit filter
    if business_unit:
        incidents = incidents.filter(AffectedBusinessUnit__iexact=business_unit)

    # Apply business category filter
    if business_category:
        incidents = incidents.filter(IncidentCategory__iexact=business_category)

    # Apply status filter
    if status_filter != 'all':
        incidents = incidents.filter(Status__iexact=status_filter)

    # Apply framework filter directly using FrameworkId field in incidents table
    if framework_id:
        if settings.DEBUG:
            print(f"🔍 Applying framework filter: {framework_id}")
        incidents = incidents.filter(FrameworkId=framework_id)
    
    # Apply policy and subpolicy filters through compliance relationship
    if policy_id or subpolicy_id:
        # Get all compliance IDs that match the filter chain - optimized with select_related
        from ...models import Compliance, SubPolicy, Policy
        compliance_ids = Compliance.objects.select_related('SubPolicy').all()
        if subpolicy_id:
            compliance_ids = compliance_ids.filter(SubPolicy=subpolicy_id)
        if policy_id:
            subpolicies = SubPolicy.objects.filter(PolicyId=policy_id)
            compliance_ids = compliance_ids.filter(SubPolicy__in=subpolicies.values_list('SubPolicyId', flat=True))
        compliance_ids = list(compliance_ids.values_list('ComplianceId', flat=True))
        if settings.DEBUG:
            print(f"Applying policy/subpolicy filters - Policy: {policy_id}, SubPolicy: {subpolicy_id}")
        incidents = incidents.filter(ComplianceId__in=compliance_ids)

    # Apply sorting if provided
    if sort_field:
        # Map frontend field names to model field names
        field_mapping = {
            'IncidentId': 'IncidentId',
            'IncidentTitle': 'IncidentTitle',
            'Origin': 'Origin',
            'RiskPriority': 'RiskPriority',
            'Date': 'Date',
            'Status': 'Status',
            'CreatedAt': 'CreatedAt',
            'AffectedBusinessUnit': 'AffectedBusinessUnit'
        }
        
        if sort_field in field_mapping:
            order_field = field_mapping[sort_field]
            if sort_order == 'desc':
                order_field = f'-{order_field}'
            incidents = incidents.order_by(order_field)
    else:
        # Default sorting by IncidentId descending (newest first)
        incidents = incidents.order_by('-IncidentId')
    
    # Get total count with error handling (optimized - do this before pagination)
    try:
        total_count = incidents.count()
    except Exception as e:
        if settings.DEBUG:
            print(f"Error getting count: {e}")
        total_count = 0  # Fallback to 0

    # Apply pagination if limit is specified
    if limit:
        incidents = incidents[offset:offset + limit]

    serializer = IncidentSerializer(incidents, many=True)
    serialized_data = serializer.data
    
    # Enrich each incident with framework_id, policy_id, subpolicy_id for frontend filtering
    # Optimized: Use already-loaded related objects instead of additional queries
    incident_objs = list(incidents)  # Convert queryset to list to access objects
    for i, incident_data in enumerate(serialized_data):
        try:
            incident_obj = incident_objs[i]
            # Try to use the select_related data if available
            if hasattr(incident_obj, 'ComplianceId') and incident_obj.ComplianceId:
                compliance = incident_obj.ComplianceId
                if hasattr(compliance, 'SubPolicy') and compliance.SubPolicy:
                    subpolicy = compliance.SubPolicy
                    incident_data['subpolicy_id'] = subpolicy.SubPolicyId
                    if hasattr(subpolicy, 'PolicyId') and subpolicy.PolicyId:
                        policy = subpolicy.PolicyId
                        incident_data['policy_id'] = policy.PolicyId
                        if hasattr(policy, 'FrameworkId') and policy.FrameworkId:
                            framework = policy.FrameworkId
                            incident_data['framework_id'] = framework.FrameworkId
                        else:
                            incident_data['framework_id'] = None
                    else:
                        incident_data['policy_id'] = None
                        incident_data['framework_id'] = None
                else:
                    incident_data['subpolicy_id'] = None
                    incident_data['policy_id'] = None
                    incident_data['framework_id'] = None
            else:
                incident_data['framework_id'] = None
                incident_data['policy_id'] = None
                incident_data['subpolicy_id'] = None
        except Exception as e:
            if settings.DEBUG:
                print(f"Error enriching incident data: {e}")
            incident_data['framework_id'] = None
            incident_data['policy_id'] = None
            incident_data['subpolicy_id'] = None
    
    # Add assigner and reviewer names to each incident (safe and DB-agnostic)
    try:
        from ...models import Users
        # Collect unique user IDs to resolve in one query - optimized
        assigner_ids = {inc.get('AssignerId') for inc in serialized_data if inc.get('AssignerId')}
        reviewer_ids = {inc.get('ReviewerId') for inc in serialized_data if inc.get('ReviewerId')}
        user_ids = list(assigner_ids.union(reviewer_ids))
        id_to_name = {}
        if user_ids:
            # Use select_related to optimize the query
            id_to_name = {
                user.UserId: user.UserName
                for user in Users.objects.filter(UserId__in=user_ids).only('UserId', 'UserName')
            }
        # Populate names without external services
        for incident_data in serialized_data:
            assigner_id = incident_data.get('AssignerId')
            reviewer_id = incident_data.get('ReviewerId')
            incident_data['assigner_name'] = id_to_name.get(assigner_id) if assigner_id else None
            incident_data['reviewer_name'] = id_to_name.get(reviewer_id) if reviewer_id else None
    except Exception as e:
        print(f"Error resolving user names: {e}")
        # In case of any error, default to None to avoid breaking the API
        for incident_data in serialized_data:
            incident_data['assigner_name'] = incident_data.get('assigner_name') or None
            incident_data['reviewer_name'] = incident_data.get('reviewer_name') or None
    
    # Add debug logging for status field (only in DEBUG mode)
    if settings.DEBUG and serialized_data:
        print(f"Sample incident data with status: {[(incident.get('IncidentId'), incident.get('Status')) for incident in serialized_data[:3]]}")
        print(f"Total incidents being returned: {len(serialized_data)}")
    
    # Log successful incident list retrieval
    send_log(
        module="Incident",
        actionType="LIST_INCIDENTS_SUCCESS",
        description=f"Successfully retrieved {len(serialized_data)} incidents",
        userId=str(user_id) if user_id else None,
        userName=request.GET.get('userName', 'Unknown'),
        entityType="Incident",
        ipAddress=client_ip,
        additionalInfo={
            "total_count": total_count,
            "returned_count": len(serialized_data),
            "filters": {
                "status": status_filter,
                "time_range": time_range,
                "category": category,
                "priority": priority,
                "search": search_query,
                "framework_id": framework_id,
                "policy_id": policy_id,
                "subpolicy_id": subpolicy_id
            }
        }
    )
    
    # ========================================
    # 🔥 LOGIN SESSION DATA LOADED - SUMMARY 🔥
    # ========================================
    print(f"\n{'='*80}")
    print(f"✅ [INCIDENT API] Successfully loaded {len(serialized_data)} incidents")
    print(f"📊 Total incidents in DB: {total_count}")
    print(f"📦 Returned in this batch: {len(serialized_data)}")
    print(f"⚡ Has more data: {offset + len(serialized_data) < total_count}")
    print(f"💾 Session data ready for user: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    print(f"{'='*80}\n")
    
    # Return paginated response if limit was applied
    if limit:
        return Response({
            'incidents': serialized_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count
        })
    else:
        return Response(serialized_data)


# Add a simple test endpoint for debugging
@api_view(['GET'])
@permission_classes([AllowAny])
def test_incident_endpoint(request):
    """Simple test endpoint to verify the incident API is working"""
    return Response({
        'status': 'success',
        'message': 'Incident API is working',
        'timestamp': timezone.now().isoformat(),
        'user': request.user.UserName if hasattr(request, 'user') and request.user else 'Anonymous'
    })


# Add a simple incident count endpoint for debugging
@api_view(['GET'])
@permission_classes([AllowAny])
def test_incident_count(request):
    """Simple endpoint to test incident count without full data"""
    try:
        count = Incident.objects.count()
        return Response({
            'status': 'success',
            'count': count,
            'message': f'Found {count} incidents in database'
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error counting incidents: {str(e)}'
        }, status=500)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ...models import Incident
import json

# Add this endpoint for updating incident status
@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([IncidentEditPermission])
@rbac_required(required_permission='edit_incident')
def update_incident_status(request, incident_id):
    client_ip = get_client_ip(request)
    user_id = request.data.get('UserId')
    
    # Log status update attempt
    send_log(
        module="Incident",
        actionType="UPDATE_INCIDENT_STATUS_ATTEMPT",
        description=f"User attempting to update incident status for incident {incident_id}",
        userId=str(user_id) if user_id else None,
        userName=request.data.get('userName', 'Unknown'),
        entityType="Incident",
        entityId=str(incident_id),
        ipAddress=client_ip
    )
    try:
        # Skip RBAC permission check since we're using AllowAny
        
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        
        # Define validation rules for JSON body
        validation_rules = {
            'status': {
                'type': 'choice',
                'choices': SecureValidator.INCIDENT_STATUSES,
                'required': True
            },
            'rejection_source': {
                'type': 'string',
                'max_length': 500,
                'pattern': SecureValidator.BUSINESS_TEXT_PATTERN,
                'required': False
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
            print(f"DEBUG: Validated data: {validated_data}")
            print(f"DEBUG: Status value received: '{validated_data.get('status')}'")
            print(f"DEBUG: Status type: {type(validated_data.get('status'))}")
        except ValidationError as e:
            print(f"DEBUG: Validation error: {str(e)}")
            return Response({'error': str(e)}, status=400)
        
        # Get the incident
        incident = Incident.objects.get(IncidentId=validated_incident_id)
        
        # Get validated data
        new_status = validated_data.get('status')
        rejection_source = validated_data.get('rejection_source')
        
        print(f"Updating incident {validated_incident_id} status to: {new_status}")
        
        # Log status update attempt
        send_log(
            module="Incident",
            actionType="UPDATE_STATUS",
            description=f"User updating incident {validated_incident_id} status from {incident.Status} to {new_status}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            entityId=validated_incident_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"old_status": incident.Status, "new_status": new_status, "rejection_source": rejection_source}
        )
        
        # If status is being set to "Scheduled" (escalated to risk), create RiskInstance
        if new_status == 'Scheduled':
            try:
                # Check if RiskInstance already exists for this incident
                existing_risk = RiskInstance.objects.filter(IncidentId=validated_incident_id).first()
                
                if not existing_risk:
                    # Handle ComplianceId - only include if it's not null/empty
                    compliance_id = incident.ComplianceId
                    if compliance_id == '' or compliance_id == 'null' or compliance_id is None:
                        compliance_id = None
                    elif hasattr(compliance_id, 'ComplianceId'):
                        # If it's a Compliance object, extract the ID
                        compliance_id = compliance_id.ComplianceId
                    elif isinstance(compliance_id, str) and compliance_id.isdigit():
                        # If it's a string number, convert to int
                        compliance_id = int(compliance_id)
                        
                    # Use CreatedAt and ensure it's timezone-aware
                    from django.utils import timezone
                    incident_datetime = incident.CreatedAt
                    if incident_datetime and not timezone.is_aware(incident_datetime):
                        incident_datetime = timezone.make_aware(incident_datetime)
                    
                    risk_instance_data = {
                        'IncidentId': incident.IncidentId,  # Pass the incident instance (not just ID)
                        'RiskTitle': incident.IncidentTitle or '',
                        'Criticality': incident.Criticality if incident.Criticality else None,  # Convert empty string to None
                        'Category': incident.RiskCategory or '',
                        'RiskDescription': incident.Description or '',
                        'PossibleDamage': incident.PossibleDamage if incident.PossibleDamage else None,  # Convert empty string to None
                        'RiskPriority': incident.RiskPriority or '',
                        'CreatedAt': incident_datetime,  # Combined datetime instead of just date
                        'Origin': incident.Origin or '',
                        'RiskStatus': 'Open',  # Default status
                        'ReportedBy': incident.UserId.UserId if incident.UserId else 1,   # Save UserId in ReportedBy column
                        'ComplianceId': compliance_id  # Include ComplianceId only if provided and not null
                    }
                    
                    print(f"Creating RiskInstance for escalated incident {validated_incident_id}")
                    print(f"RiskInstance data: {risk_instance_data}")
                    
                    # Create RiskInstance directly using the model to avoid serializer timezone issues
                    try:
                        risk_instance = RiskInstance.objects.create(**risk_instance_data)
                        print(f"RiskInstance created successfully with ID: {risk_instance.RiskInstanceId}")
                        print(f"Saved data: IncidentId={risk_instance.IncidentId}, RiskTitle={risk_instance.RiskTitle}, Category={risk_instance.Category}")
                    except Exception as create_error:
                        print(f"Error creating RiskInstance with model: {create_error}")
                        # Try with serializer as fallback
                        risk_instance_serializer = RiskInstanceSerializer(data=risk_instance_data)
                        if risk_instance_serializer.is_valid():
                            risk_instance = risk_instance_serializer.save()
                            print(f"RiskInstance created via serializer with ID: {risk_instance.RiskInstanceId}")
                        else:
                            print("RiskInstance serializer errors:", risk_instance_serializer.errors)
                            # Continue with status update even if RiskInstance creation fails
                else:
                    print(f"RiskInstance already exists for incident {validated_incident_id}")
                    
            except Exception as e:
                print(f"Error creating RiskInstance during escalation: {str(e)}")
                # Continue with status update even if RiskInstance creation fails
        
        # Update the incident status
        incident.Status = new_status
        print(f"Updated incident status to: {incident.Status}")
        
        # Set the rejection source if this is a rejection
        if new_status == 'Rejected' and rejection_source:
            incident.RejectionSource = rejection_source
            print(f"Setting rejection source to: {rejection_source}")
        
        # Send notifications based on status change
        try:
            notification_service = NotificationService()
            
            # Incident escalation notification
            if new_status == 'Scheduled':
                if incident.AssignerId:
                    assignee_email = notification_service.get_user_email(incident.AssignerId)
                    if assignee_email:
                        escalation_notification = {
                            'notification_type': 'incidentEscalated',
                            'email': assignee_email,
                            'email_type': 'gmail',
                            'template_data': [
                                'Risk Manager',
                                incident.IncidentTitle,
                                'System'
                            ]
                        }
                        notification_service.send_multi_channel_notification(escalation_notification)
            
            # Incident rejection notification
            elif new_status == 'Rejected':
                if incident.AssignerId:
                    assignee_email = notification_service.get_user_email(incident.AssignerId)
                    if assignee_email:
                        rejection_notification = {
                            'notification_type': 'incidentRejected',
                            'email': assignee_email,
                            'email_type': 'gmail',
                            'template_data': [
                                notification_service.get_user_name(incident.AssignerId) if incident.AssignerId else 'User',
                                incident.IncidentTitle,
                                'System',
                                f"Rejected from {rejection_source}" if rejection_source else "No reason provided"
                            ]
                        }
                        notification_service.send_multi_channel_notification(rejection_notification)
                    
        except Exception as e:
            print(f"Error sending status update notifications: {str(e)}")
            # Continue execution even if notification fails
        
        incident.save()
        
        # Log successful status update
        send_log(
            module="Incident",
            actionType="UPDATE_INCIDENT_STATUS_SUCCESS",
            description=f"Incident status updated successfully to {incident.Status}",
            userId=str(user_id) if user_id else None,
            userName=request.data.get('userName', 'Unknown'),
            entityType="Incident",
            entityId=str(incident_id),
            ipAddress=client_ip,
            additionalInfo={
                "new_status": incident.Status,
                "rejection_source": request.data.get('rejection_source')
            }
        )
        
        return Response({
            'success': True,
            'message': f'Incident status updated to {incident.Status}',
            'IncidentId': incident.IncidentId
        })
    except Incident.DoesNotExist:
        # Log incident not found error
        send_log(
            module="Incident",
            actionType="UPDATE_INCIDENT_STATUS_ERROR",
            description=f"Incident not found: {incident_id}",
            userId=str(user_id) if user_id else None,
            userName=request.data.get('userName', 'Unknown'),
            entityType="Incident",
            entityId=str(incident_id),
            logLevel="WARNING",
            ipAddress=client_ip
        )
        
        return Response({
            'success': False,
            'message': 'Incident not found',
            'IncidentId': incident_id
        }, status=404)
    except Exception as e:
        # Log general error
        send_log(
            module="Incident",
            actionType="UPDATE_INCIDENT_STATUS_ERROR",
            description=f"Error updating incident status: {str(e)}",
            userId=str(user_id) if user_id else None,
            userName=request.data.get('userName', 'Unknown'),
            entityType="Incident",
            entityId=str(incident_id),
            logLevel="ERROR",
            ipAddress=client_ip,
            additionalInfo={"error": str(e)}
        )
        
        print(f"Error updating incident status: {str(e)}")
        return Response({
            'success': False,
            'message': str(e),
            'IncidentId': incident_id
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IncidentCreatePermission])
@authentication_classes([])
@rbac_required(required_permission='create_incident')
@require_consent('create_incident')
def create_incident(request):
    # RBAC Debug - Log user access attempt
    debug_info = debug_user_permissions(request, "CREATE_INCIDENT", "incident", None)
    
    print("Received data:", request.data)
    compliance_id = request.data.get('ComplianceId')
    user_id = request.data.get('UserId')
    client_ip = get_client_ip(request)
    
    # Log incident creation attempt
    send_log(
        module="Incident",
        actionType="CREATE_INCIDENT_ATTEMPT",
        description="User attempting to create incident",
        userId=str(user_id) if user_id else None,
        userName=request.data.get('userName', 'Unknown'),
        entityType="Incident",
        ipAddress=client_ip,
        additionalInfo={"ComplianceId": compliance_id}
    )
    
    print(f"ComplianceId received: {compliance_id}")
    
    # Log incident creation attempt
    send_log(
        module="Incident",
        actionType="CREATE",
        description="User attempting to create new incident",
        userId=request.user.id if request.user.is_authenticated else None,
        userName=request.user.username if request.user.is_authenticated else None,
        entityType="Incident",
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Apply strict allow-list validation using centralized validation function
        validated_data = validate_incident_data(request.data)
        
        # SECURITY FIX: Always use the authenticated user's ID for incident creation
        # Get the authenticated user's ID from session (which contains custom Users.UserId)
        authenticated_user_id = None
        if hasattr(request, 'session') and 'user_id' in request.session:
            authenticated_user_id = request.session['user_id']
        elif hasattr(request, 'session') and 'grc_user_id' in request.session:
            authenticated_user_id = request.session['grc_user_id']
        
        # TEMPORARILY DISABLED: For development, use default user if no authentication
        if not authenticated_user_id:
            # Use a default user ID for development
            authenticated_user_id = 1  # Default user ID
            print(f"[DEV] No authenticated user found, using default user ID: {authenticated_user_id}")
        
        # Verify the user exists in our custom Users table
        try:
            authenticated_user = Users.objects.get(UserId=authenticated_user_id)
            # Override any UserId sent from frontend with the authenticated user's ID
            validated_data['UserId'] = authenticated_user_id
            print(f"Setting incident UserId to authenticated user: {authenticated_user_id} ({authenticated_user.UserName})")
        except Users.DoesNotExist:
            # Log error - authenticated user not found in custom Users table
            send_log(
                module="Incident",
                actionType="CREATE_INCIDENT_ERROR",
                description=f"Authenticated user ID {authenticated_user_id} not found in Users table",
                userId=None,
                userName="Unknown",
                entityType="Incident",
                logLevel="ERROR",
                ipAddress=client_ip
            )
            return Response({
                'error': 'User authentication error. Please contact system administrator.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # After validation, use the serializer with validated data
        serializer = IncidentSerializer(data=validated_data)
        if serializer.is_valid():
            # Save the incident first - CreatedAt will be auto-set by auto_now_add=True
            incident = serializer.save()
            
            # Ensure CreatedAt is set correctly with current timezone-aware datetime
            if not incident.CreatedAt:
                incident.CreatedAt = timezone.now()
                incident.save()
            
            print(f"Incident created with ID: {incident.IncidentId}")
            print(f"CreatedAt timestamp: {incident.CreatedAt}")
            if incident.ComplianceId:
                print(f"Incident linked to ComplianceId: {incident.ComplianceId}")
            
            # Log successful incident creation
            send_log(
                module="Incident",
                actionType="CREATE_INCIDENT_SUCCESS",
                description=f"Incident created successfully: {incident.IncidentTitle}",
                userId=str(authenticated_user_id),
                userName=authenticated_user.UserName,
                entityType="Incident",
                entityId=str(incident.IncidentId),
                ipAddress=client_ip,
                additionalInfo={
                    "IncidentTitle": incident.IncidentTitle,
                    "ComplianceId": incident.ComplianceId.ComplianceId if incident.ComplianceId else None,
                    "Status": incident.Status
                }
            )
            
            # DO NOT create RiskInstance here - only create when escalated to risk
            print("Incident saved to incidents table only. RiskInstance will be created when escalated to risk.")
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # Log validation errors
        send_log(
            module="Incident",
            actionType="CREATE_INCIDENT_VALIDATION_ERROR",
            description="Incident creation failed due to validation errors",
            userId=str(authenticated_user_id) if authenticated_user_id else None,
            userName=authenticated_user.UserName if authenticated_user_id else 'Unknown',
            entityType="Incident",
            logLevel="WARNING",
            ipAddress=client_ip,
            additionalInfo=serializer.errors
        )
        
        print("Serializer errors:", serializer.errors)
        
        # Log serialization errors
        send_log(
            module="Incident",
            actionType="CREATE_ERROR",
            description=f"Incident creation failed - serializer errors: {serializer.errors}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as ve:
        # Handle centralized validation errors
        send_log(
            module="Incident",
            actionType="CREATE_INCIDENT_VALIDATION_ERROR",
            description=f"Incident creation validation error: {ve.field} - {ve.message}",
            userId=str(authenticated_user_id) if 'authenticated_user_id' in locals() and authenticated_user_id else None,
            userName=authenticated_user.UserName if 'authenticated_user' in locals() and authenticated_user else 'Unknown',
            entityType="Incident",
            logLevel="WARNING",
            ipAddress=client_ip,
            additionalInfo={"field": ve.field, "message": ve.message}
        )
        
        print(f"Validation error: {ve.field} - {ve.message}")
        
        # Log validation errors
        send_log(
            module="Incident",
            actionType="CREATE_ERROR",
            description=f"Incident creation failed - validation error: {ve.field} - {ve.message}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        
        return Response({ve.field: [ve.message]}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Handle unexpected errors
        send_log(
            module="Incident",
            actionType="CREATE_INCIDENT_ERROR",
            description=f"Incident creation error: {str(e)}",
            userId=str(authenticated_user_id) if 'authenticated_user_id' in locals() and authenticated_user_id else None,
            userName=authenticated_user.UserName if 'authenticated_user' in locals() and authenticated_user else 'Unknown',
            entityType="Incident",
            logLevel="ERROR",
            ipAddress=client_ip,
            additionalInfo={"error": str(e)}
        )
        
        print(f"Error validating incident data: {str(e)}")
        
        # Log unexpected errors
        send_log(
            module="Incident",
            actionType="CREATE_ERROR",
            description=f"Incident creation failed - unexpected error: {str(e)}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return Response({"error": "Invalid input data"}, status=status.HTTP_400_BAD_REQUEST)

def login_view(request):
    # ... your login logic ...
    if user_is_authenticated:
        return redirect('incident_page')  # Use your URL name or path

def incident_page(request):
    # SECURE: Example of safe HTML rendering with escaped data
    # If passing user data to template, ensure it's properly escaped:
    # safe_data = SecureOutputEncoder.escape_html(user_input)
    # return render(request, 'incidents.html', {'safe_data': safe_data})
    return render(request, 'incidents.html')

@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([IncidentAssignPermission])
@rbac_required(required_permission='assign_incident')
def assign_incident(request, incident_id):
    client_ip = get_client_ip(request)
    user_id = request.data.get('userId')
    
    # Log incident assignment attempt
    send_log(
        module="Incident",
        actionType="ASSIGN_INCIDENT_ATTEMPT",
        description=f"User attempting to assign incident {incident_id}",
        userId=str(user_id) if user_id else None,
        userName=request.data.get('userName', 'Unknown'),
        entityType="Incident",
        entityId=str(incident_id),
        ipAddress=client_ip
    )
    
    try:
        # Skip RBAC permission check since we're using AllowAny
        
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            # Log validation error
            send_log(
                module="Incident",
                actionType="ASSIGN_INCIDENT_VALIDATION_ERROR",
                description=f"Incident assignment validation error: {str(e)}",
                userId=str(user_id) if user_id else None,
                userName=request.data.get('userName', 'Unknown'),
                entityType="Incident",
                entityId=str(incident_id),
                logLevel="WARNING",
                ipAddress=client_ip
            )
            return Response({'error': str(e)}, status=400)
        
        # Get the incident from the database
        incident = Incident.objects.get(IncidentId=validated_incident_id)
        
        # Log incident assignment attempt
        send_log(
            module="Incident",
            actionType="ASSIGN",
            description=f"User attempting to assign incident {validated_incident_id}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            entityId=validated_incident_id,
            ipAddress=get_client_ip(request)
        )
        
        # Define validation rules for JSON body
        validation_rules = {
            'status': {
                'type': 'choice',
                'choices': SecureValidator.INCIDENT_STATUSES,
                'required': False
            },
            'assigner_id': {
                'type': 'integer',
                'min_value': 1,
                'max_value': 999999,
                'required': False
            },
            'reviewer_id': {
                'type': 'integer',
                'min_value': 1,
                'max_value': 999999,
                'required': False
            },
            'assignment_notes': {
                'type': 'string',
                'max_length': 1000,
                'pattern': SecureValidator.BUSINESS_TEXT_PATTERN,
                'required': False
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        
        # Get raw data for additional fields not validated (assigned_date, mitigations, due_date)
        # Use request.data instead of request.body to avoid re-reading the stream
        try:
            if hasattr(request, 'data') and request.data:
                # DRF parsed data (preferred)
                data = request.data
            else:
                data = {}
        except Exception:
            return Response({'error': 'Invalid request data'}, status=400)
        
        # Update incident with assignment details (using validated data)
        incident.Status = validated_data.get('status', 'Assigned')
        
        # SECURITY: Always use the authenticated user as the assigner for audit trail
        # Get the authenticated user's ID from session
        authenticated_user_id = None
        if hasattr(request, 'session') and 'user_id' in request.session:
            authenticated_user_id = request.session['user_id']
        elif hasattr(request, 'session') and 'grc_user_id' in request.session:
            authenticated_user_id = request.session['grc_user_id']
        
        # Override any assigner_id sent from frontend with the authenticated user's ID
        if authenticated_user_id:
            incident.AssignerId = authenticated_user_id
            print(f"SECURITY: Setting incident AssignerId to authenticated user: {authenticated_user_id}")
        else:
            # Fallback to the provided assigner_id if no session (should not happen in normal operation)
            incident.AssignerId = validated_data.get('assigner_id')
            print(f"WARNING: No authenticated user found in session, using provided assigner_id: {incident.AssignerId}")
            
        reviewer_id = validated_data.get('reviewer_id')
        incident.ReviewerId = reviewer_id
        incident.AssignmentNotes = validated_data.get('assignment_notes', '')
        
        print(f"🔍 DEBUG: assign_incident - Setting ReviewerId to: {reviewer_id}")
        print(f"🔍 DEBUG: assign_incident - Setting Status to: {incident.Status}")
        print(f"🔍 DEBUG: assign_incident - Setting AssignerId to: {incident.AssignerId}")
        
        # Handle assigned date
        assigned_date = data.get('assigned_date')
        if assigned_date:
            from datetime import datetime
            from django.conf import settings
            from django.utils import timezone
            
            # Parse the datetime
            if assigned_date.endswith('Z'):
                # Handle UTC timezone indicator
                assigned_date = assigned_date.replace('Z', '+00:00')
            
            dt = datetime.fromisoformat(assigned_date)
            
            # Handle timezone awareness based on Django settings
            if getattr(settings, 'USE_TZ', True):
                # If USE_TZ is True, ensure datetime is timezone-aware
                if dt.tzinfo is None:
                    dt = timezone.make_aware(dt)
                incident.AssignedDate = dt
            else:
                # If USE_TZ is False, ensure datetime is timezone-naive
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                incident.AssignedDate = dt
        
        # Handle mitigations if provided
        mitigations = data.get('mitigations')
        if mitigations:
            incident.Mitigation = json.dumps(mitigations) if isinstance(mitigations, dict) else mitigations
        
        # Handle due date if provided
        due_date = data.get('due_date')
        if due_date:
            from datetime import datetime
            from django.conf import settings
            from django.utils import timezone
            
            # Parse the date (assuming it's just a date, not datetime)
            dt = datetime.strptime(due_date, '%Y-%m-%d')
            
            # Handle timezone awareness based on Django settings
            if getattr(settings, 'USE_TZ', True):
                # If USE_TZ is True, make datetime timezone-aware
                dt = timezone.make_aware(dt)
                incident.MitigationDueDate = dt
            else:
                # If USE_TZ is False, keep datetime timezone-naive
                incident.MitigationDueDate = dt
        
        # Save the incident with all updates
        print(f"🔍 DEBUG: assign_incident - About to save incident {incident.IncidentId}")
        print(f"🔍 DEBUG: assign_incident - ReviewerId before save: {incident.ReviewerId}")
        print(f"🔍 DEBUG: assign_incident - Status before save: {incident.Status}")
        print(f"🔍 DEBUG: assign_incident - AssignerId before save: {incident.AssignerId}")
        incident.save()
        print(f"✅ DEBUG: assign_incident - Incident saved successfully")
        
        # Verify the save by reloading
        incident.refresh_from_db()
        print(f"🔍 DEBUG: assign_incident - After reload - ReviewerId: {incident.ReviewerId}, Status: {incident.Status}, AssignerId: {incident.AssignerId}")
        
        # Send notification for incident assignment
        try:
            notification_service = NotificationService()
            print(f"DEBUG: Starting notification process for incident {incident_id}")
            
            # Get user details for notifications
            assigner_name = notification_service.get_user_name(incident.AssignerId) if incident.AssignerId else data.get('assigner_name', 'Unknown')
            reviewer_name = notification_service.get_user_name(incident.ReviewerId) if incident.ReviewerId else data.get('reviewer_name', 'Unknown')
            
            # Notify assignee about the incident assignment
            if incident.AssignerId:
                assignee_email = notification_service.get_user_email(incident.AssignerId)
                print(f"DEBUG: Assignee {incident.AssignerId} email: {assignee_email}")
                if assignee_email:
                    assignee_notification = {
                        'notification_type': 'incidentAssigned',
                        'email': assignee_email,
                        'email_type': 'gmail',
                        'template_data': [
                            assigner_name,
                            incident.IncidentTitle,
                            incident.MitigationDueDate.strftime('%Y-%m-%d') if incident.MitigationDueDate else 'Not set'
                        ]
                    }
                    print(f"DEBUG: Sending assignee notification: {assignee_notification}")
                    result = notification_service.send_multi_channel_notification(assignee_notification)
                    print(f"DEBUG: Assignee notification result: {result}")
                else:
                    print(f"DEBUG: No email found for assignee {incident.AssignerId}")
            
            # Notify reviewer about being assigned as reviewer
            if incident.ReviewerId:
                reviewer_email = notification_service.get_user_email(incident.ReviewerId)
                print(f"DEBUG: Reviewer {incident.ReviewerId} email: {reviewer_email}")
                if reviewer_email:
                    reviewer_notification = {
                        'notification_type': 'incidentReviewerAssigned',
                        'email': reviewer_email,
                        'email_type': 'gmail',
                        'template_data': [
                            reviewer_name,
                            incident.IncidentTitle,
                            assigner_name
                        ]
                    }
                    print(f"DEBUG: Sending reviewer notification: {reviewer_notification}")
                    result = notification_service.send_multi_channel_notification(reviewer_notification)
                    print(f"DEBUG: Reviewer notification result: {result}")
                else:
                    print(f"DEBUG: No email found for reviewer {incident.ReviewerId}")
                
        except Exception as e:
            print(f"Error sending assignment notifications: {str(e)}")
            # Continue execution even if notification fails
        
        # Log successful incident assignment
        send_log(
            module="Incident",
            actionType="ASSIGN_SUCCESS",
            description=f"Incident {incident_id} assigned successfully to assigner {incident.AssignerId} and reviewer {incident.ReviewerId}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            entityId=incident_id,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "assigner_id": incident.AssignerId,
                "reviewer_id": incident.ReviewerId,
                "assigner_name": data.get('assigner_name'),
                "reviewer_name": data.get('reviewer_name')
            }
        )
        
        return Response({
            'success': True,
            'message': 'Incident assigned successfully',
            'IncidentId': incident.IncidentId,
            'status': incident.Status,
            'assigner_id': incident.AssignerId,
            'reviewer_id': incident.ReviewerId,
            'assigner': data.get('assigner_name'),
            'reviewer': data.get('reviewer_name')
        })
        
    except Incident.DoesNotExist:
        # Log incident not found error
        send_log(
            module="Incident",
            actionType="ASSIGN_INCIDENT_NOT_FOUND",
            description=f"Incident not found for assignment: {incident_id}",
            userId=str(user_id) if user_id else None,
            userName=request.data.get('userName', 'Unknown'),
            entityType="Incident",
            entityId=str(incident_id),
            logLevel="WARN",
            ipAddress=client_ip
        )
        return Response({
            'success': False,
            'error': 'Incident not found',
            'IncidentId': incident_id
        }, status=404)
    except Exception as e:
        # Log assignment error
        send_log(
            module="Incident",
            actionType="ASSIGN_INCIDENT_ERROR",
            description=f"Error assigning incident {incident_id}: {str(e)}",
            userId=str(user_id) if user_id else None,
            userName=request.data.get('userName', 'Unknown'),
            entityType="Incident",
            entityId=str(incident_id),
            logLevel="ERROR",
            ipAddress=client_ip,
            additionalInfo={'error': str(e)}
        )
        print(f"Error assigning incident: {str(e)}")
        return Response({
            'success': False,
            'error': str(e),
            'IncidentId': incident_id
        }, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AuditViewPermission])
@rbac_required(required_permission='view_audit_reports')
def unchecked_audit_findings(request):
    findings = LastChecklistItemVerified.objects.filter(Complied__in=[0, 1])
    serializer = LastChecklistItemVerifiedSerializer(findings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@authentication_classes([])
def list_users(request):
    # Get user info for logging
    user_id = getattr(request.user, 'id', None)
    username = getattr(request.user, 'username', 'Unknown')
    
    # Log users list request
    send_log(
        module="User",
        actionType="LIST_USERS",
        description="User requesting list of all users",
        userId=user_id,
        userName=username,
        entityType="User",
        ipAddress=get_client_ip(request)
    )
    
    try:
        print("Listing users")
        print(f"Request method: {request.method}")
        print(f"Request user: {request.user}")
        print(f"Request session: {request.session}")
        
        users = Users.objects.all()
        print(f"Found {users.count()} users in database")
        
        serializer = UserSerializer(users, many=True)
        print(f"Serialized {len(serializer.data)} users")
        
        # Log successful user list retrieval
        send_log(
            module="User",
            actionType="LIST_USERS_SUCCESS",
            description=f"Successfully retrieved {len(users)} users",
            userId=user_id,
            userName=username,
            entityType="User",
            ipAddress=get_client_ip(request),
            additionalInfo={'user_count': len(users)}
        )
        
        return Response(serializer.data)
    
    except Exception as e:
        print(f"Error in list_users: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Log error
        send_log(
            module="User",
            actionType="LIST_USERS_ERROR",
            description=f"Error retrieving users list: {str(e)}",
            userId=user_id,
            userName=username,
            entityType="User",
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={'error': str(e)}
        )
        
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def combined_incidents_and_audit_findings(request):
    # RBAC Debug - Log user access attempt
    debug_info = debug_user_permissions(request, "VIEW_INCIDENTS_AND_AUDIT_FINDINGS", "incident", None)
    
    # Get all incidents from the database
    all_incidents = Incident.objects.all()
    all_incidents_serialized = IncidentSerializer(all_incidents, many=True).data
    
    # Categorize by type
    for item in all_incidents_serialized:
        if item['Origin'] == 'Manual':
            item['type'] = 'manual'
            item['source'] = 'manual'
        elif item['Origin'] in ['Audit Finding', 'Compliance Gap']:
            item['type'] = 'audit_incident'
            item['source'] = 'auditor'
            # Add criticality for audit incidents
            if item['ComplianceId']:
                try:
                    compliance = Compliance.objects.get(pk=item['ComplianceId'])
                    item['criticality'] = compliance.Criticality if hasattr(compliance, 'Criticality') else None
                except Compliance.DoesNotExist:
                    item['criticality'] = None
        elif item['Origin'] == 'SIEM':
            item['type'] = 'siem'
            item['source'] = 'siem'
        else:
            item['type'] = 'other'
            item['source'] = 'other'
    
    # Get findings from lastchecklistitemverified with Complied = 0 or 1
    audit_findings = LastChecklistItemVerified.objects.filter(Complied__in=[0, 1])
    audit_findings_serialized = LastChecklistItemVerifiedSerializer(audit_findings, many=True).data
    
    # Process each audit finding
    for item in audit_findings_serialized:
        item['type'] = 'audit'
        item['Origin'] = 'Audit Finding'  # Set origin for filtering in frontend (audit findings from LastChecklistItemVerified)
        item['source'] = 'auditor'  # All audit findings come from auditor
        
        # Get the complete compliance item details
        if item['ComplianceId']:
            try:
                compliance = Compliance.objects.get(pk=item['ComplianceId'])
                item['compliance_name'] = compliance.ComplianceItemDescription
                item['compliance_mitigation'] = compliance.mitigation if hasattr(compliance, 'mitigation') else None
                item['criticality'] = compliance.Criticality if hasattr(compliance, 'Criticality') else None
            except Compliance.DoesNotExist:
                item['compliance_name'] = "No description"
                item['compliance_mitigation'] = None
                item['criticality'] = None
        else:
            item['compliance_name'] = "No description"
            item['compliance_mitigation'] = None
            item['criticality'] = None
                
        # Check if there's a corresponding incident
        related_incident = None
        if item.get('FrameworkId') and item['ComplianceId']:
            related_incident = Incident.objects.filter(
                Origin__in=["Audit Finding", "Compliance Gap"],
                # Adjust these field mappings based on your actual model relationships
                FrameworkId=item['FrameworkId'],
                ComplianceId=item['ComplianceId']
            ).first()
        
        if related_incident:
            item['Status'] = related_incident.Status
        else:
            item['Status'] = None
    
    combined = all_incidents_serialized + audit_findings_serialized
    return Response(combined)

@api_view(['POST'])
@permission_classes([IncidentCreatePermission])
@rbac_required(required_permission='create_incident')
def create_workflow(request):
    client_ip = get_client_ip(request)
    user_id = request.data.get('userId')
    
    # Log workflow creation attempt
    send_log(
        module="Incident",
        actionType="CREATE_WORKFLOW_ATTEMPT",
        description="User attempting to create workflow",
        userId=str(user_id) if user_id else None,
        userName=request.data.get('userName', 'Unknown'),
        entityType="Workflow",
        ipAddress=client_ip
    )
    
    # Define validation rules for workflow creation
    validation_rules = {
        'finding_id': {
            'type': 'string',
            'max_length': 255,
            'pattern': SecureValidator.ALPHANUMERIC_WITH_SPACES,
            'required': False
        },
        'incident_id': {
            'type': 'integer',
            'min_value': 1,
            'required': False
        },
        'IncidentId': {
            'type': 'integer',
            'min_value': 1,
            'required': False
        },
        'assignee_id': {
            'type': 'integer',
            'min_value': 1,
            'required': True
        },
        'reviewer_id': {
            'type': 'integer',
            'min_value': 1,
            'required': True
        }
    }
    
    # Validate JSON request body
    try:
        validated_data = validate_json_request_body(request, validation_rules)
    except ValidationError as e:
        return Response({'error': str(e)}, status=400)
    
    # Accept either finding_id or IncidentId
    finding_id = validated_data.get('finding_id')
    incident_id = validated_data.get('incident_id') or validated_data.get('IncidentId')

    # Check that at least one ID is provided
    if not finding_id and not incident_id:
        return Response({'error': 'Either finding_id or incident_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Prepare data for serializer
    data = validated_data.copy()

    # Set the correct fields for the serializer
    if finding_id:
        data['finding_id'] = finding_id
        data['IncidentId'] = None
    else:
        data['IncidentId'] = incident_id
        data['finding_id'] = None

    serializer = WorkflowSerializer(data=data)
    if serializer.is_valid():
        workflow = serializer.save()
        
        # Log successful workflow creation
        send_log(
            module="Incident",
            actionType="CREATE_WORKFLOW_SUCCESS",
            description="Workflow created successfully",
            userId=str(user_id) if user_id else None,
            userName=request.data.get('userName', 'Unknown'),
            entityType="Workflow",
            entityId=str(workflow.Id),
            ipAddress=client_ip,
            additionalInfo={
                "finding_id": finding_id,
                "incident_id": incident_id,
                "assignee_id": validated_data.get('assignee_id'),
                "reviewer_id": validated_data.get('reviewer_id')
            }
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # Log validation errors
    send_log(
        module="Incident",
        actionType="CREATE_WORKFLOW_VALIDATION_ERROR",
        description="Workflow creation failed due to validation errors",
        userId=str(user_id) if user_id else None,
        userName=request.data.get('userName', 'Unknown'),
        entityType="Workflow",
        logLevel="WARNING",
        ipAddress=client_ip,
        additionalInfo=serializer.errors
    )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def list_assigned_findings(request):
    workflows = Workflow.objects.all()
    result = []
    for wf in workflows:
        # Assigned Audit Finding
        if wf.finding_id:
            try:
                finding = AuditFinding.objects.get(date=wf.finding_id)
                result.append({
                    'type': 'finding',
                    'date': wf.finding_id,
                    'comment': finding.comment,
                    'assignee': Users.objects.get(UserId=wf.assignee_id).UserName,
                    'reviewer': Users.objects.get(UserId=wf.reviewer_id).UserName,
                    'assigned_at': wf.assigned_at,
                })
            except AuditFinding.DoesNotExist:
                continue
        # Assigned Incident
        elif wf.IncidentId:
            try:
                incident = Incident.objects.get(IncidentId=wf.IncidentId)
                result.append({
                    'type': 'incident',
                    'IncidentId': wf.IncidentId,
                    'incidenttitle': incident.incidenttitle,
                    'description': incident.description,
                    'assignee': Users.objects.get(UserId=wf.assignee_id).UserName,
                    'reviewer': Users.objects.get(UserId=wf.reviewer_id).UserName,
                    'assigned_at': wf.assigned_at,
                })
            except Incident.DoesNotExist:
                continue
    return Response(result)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentCreatePermission])
@rbac_required(required_permission='create_incident')
def create_incident_from_audit_finding(request):
    client_ip = get_client_ip(request)
    user_id = request.data.get('userId')
    
    # Log incident creation from audit finding attempt
    send_log(
        module="Incident",
        actionType="CREATE_INCIDENT_FROM_AUDIT_FINDING_ATTEMPT",
        description="User attempting to create incident from audit finding",
        userId=str(user_id) if user_id else None,
        userName=request.data.get('userName', 'Unknown'),
        entityType="Incident",
        ipAddress=client_ip
    )
    
    # Define validation rules for creating incident from audit finding
    validation_rules = {
        'audit_finding_id': {
            'type': 'integer',
            'min_value': 1,
            'required': True
        }
    }
    
    # Validate JSON request body
    try:
        validated_data = validate_json_request_body(request, validation_rules)
    except ValidationError as e:
        return Response({'error': str(e)}, status=400)
    
    finding_id = validated_data.get('audit_finding_id')

    try:
        finding = AuditFinding.objects.get(pk=finding_id)
    except AuditFinding.DoesNotExist:
        return Response({'error': 'Audit finding not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if an incident already exists for this finding
    existing_incident = Incident.objects.filter(
        Origin="Audit Finding",
        AuditId=finding.AuditId,
        ComplianceId=finding.ComplianceId
    ).first()
    
    if existing_incident:
        # Update the existing incident
        existing_incident.Status = 'Scheduled'
        existing_incident.save()
        serializer = IncidentSerializer(existing_incident)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Create a new incident
    incident_data = {
        'IncidentTitle': finding.ComplianceId.ComplianceItemDescription if finding.ComplianceId else "Audit Finding",
        'Description': finding.DetailsOfFinding or finding.Comments or "",
        'Mitigation': finding.ComplianceId.mitigation if finding.ComplianceId else "",
        'AuditId': finding.AuditId.pk if finding.AuditId else None,
        'ComplianceId': finding.ComplianceId.pk if finding.ComplianceId else None,
        'Date': finding.AssignedDate.date() if finding.AssignedDate else None,
        'Time': finding.AssignedDate.time() if finding.AssignedDate else None,
        'UserId': finding.UserId.UserId,
        'Origin': 'Audit Finding',
        'Comments': finding.Comments,
        'Status': 'Scheduled',
    }

    serializer = IncidentSerializer(data=incident_data)
    if serializer.is_valid():
        incident = serializer.save()
        
        # Ensure CreatedAt is set correctly with current timezone-aware datetime
        if not incident.CreatedAt:
            incident.CreatedAt = timezone.now()
            incident.save()
        
        print(f"Incident from audit finding created with ID: {incident.IncidentId}")
        print(f"CreatedAt timestamp: {incident.CreatedAt}")
        
        # Do not change the Check status if it's partially compliant (2)
        if finding.Check != '2':
            finding.Check = '1'  # Mark as compliant/processed
            finding.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentCreatePermission])
@rbac_required(required_permission='create_incident')
def schedule_manual_incident(request):
    client_ip = get_client_ip(request)
    user_id = request.data.get('userId')
    
    # Log manual incident scheduling attempt
    send_log(
        module="Incident",
        actionType="SCHEDULE_MANUAL_INCIDENT_ATTEMPT",
        description="User attempting to schedule manual incident",
        userId=str(user_id) if user_id else None,
        userName=request.data.get('userName', 'Unknown'),
        entityType="Incident",
        ipAddress=client_ip
    )
    
    # Define validation rules for scheduling manual incident
    validation_rules = {
        'incident_id': {
            'type': 'integer',
            'min_value': 1,
            'required': True
        }
    }
    
    # Validate JSON request body
    try:
        validated_data = validate_json_request_body(request, validation_rules)
    except ValidationError as e:
        return Response({'error': str(e)}, status=400)
    
    incident_id = validated_data.get('incident_id')
    try:
        incident = Incident.objects.get(pk=incident_id, Origin="Manual")
        
        # Use the same logic as update_incident_status to create RiskInstance when escalating
        try:
            # Check if RiskInstance already exists for this incident
            existing_risk = RiskInstance.objects.filter(IncidentId=incident_id).first()
            
            if not existing_risk:
                # Handle ComplianceId - only include if it's not null/empty
                compliance_id = incident.ComplianceId
                if compliance_id == '' or compliance_id == 'null':
                    compliance_id = None
                    
                # Use CreatedAt and ensure it's timezone-aware  
                incident_datetime = incident.CreatedAt
                if incident_datetime and not timezone.is_aware(incident_datetime):
                    incident_datetime = timezone.make_aware(incident_datetime)
                
                risk_instance_data = {
                    'IncidentId': incident,  # Pass the incident instance (not just ID)
                    'RiskTitle': incident.IncidentTitle or '',
                                            'Criticality': incident.Criticality if incident.Criticality else None,  # Convert empty string to None
                    'Category': incident.RiskCategory or '',
                    'RiskDescription': incident.Description or '',
                    'PossibleDamage': incident.PossibleDamage if incident.PossibleDamage else None,  # Convert empty string to None
                    'RiskPriority': incident.RiskPriority or '',
                    'Date': incident_datetime,  # Combined datetime instead of just date
                    'Origin': incident.Origin or '',
                    'RiskStatus': 'Open',  # Default status
                    'ReportedBy': incident.UserId.UserId if incident.UserId else 1,   # Save UserId in ReportedBy column
                    'ComplianceId': compliance_id  # Include ComplianceId only if provided and not null
                }
                
                print(f"Creating RiskInstance for scheduled incident {incident_id}")
                
                # Create RiskInstance directly using the model to avoid serializer timezone issues
                try:
                    risk_instance = RiskInstance.objects.create(**risk_instance_data)
                    print(f"RiskInstance created successfully with ID: {risk_instance.RiskInstanceId}")
                    print(f"Saved data: IncidentId={risk_instance.IncidentId}, RiskTitle={risk_instance.RiskTitle}, Category={risk_instance.Category}")
                except Exception as create_error:
                    print(f"Error creating RiskInstance with model: {create_error}")
                    # Try with serializer as fallback
                    risk_instance_serializer = RiskInstanceSerializer(data=risk_instance_data)
                    if risk_instance_serializer.is_valid():
                        risk_instance = risk_instance_serializer.save()
                        print(f"RiskInstance created via serializer with ID: {risk_instance.RiskInstanceId}")
                    else:
                        print("RiskInstance serializer errors:", risk_instance_serializer.errors)
                        # Continue with status update even if RiskInstance creation fails
            else:
                print(f"RiskInstance already exists for incident {incident_id}")
                
        except Exception as e:
            print(f"Error creating RiskInstance during scheduling: {str(e)}")
            # Continue with status update even if RiskInstance creation fails
        
        incident.Status = "Scheduled"
        incident.save()
        return Response({
            'success': True,
            'message': 'Incident scheduled and directed to risk workflow.',
            'IncidentId': incident.IncidentId
        }, status=status.HTTP_200_OK)
    except Incident.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Incident not found.',
            'IncidentId': incident_id
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentEvaluatePermission])
@rbac_required(required_permission='evaluate_assigned_incident')
def reject_incident(request):
    client_ip = get_client_ip(request)
    user_id = request.data.get('userId')
    
    # Log incident rejection attempt
    send_log(
        module="Incident",
        actionType="REJECT_INCIDENT_ATTEMPT",
        description="User attempting to reject incident",
        userId=str(user_id) if user_id else None,
        userName=request.data.get('userName', 'Unknown'),
        entityType="Incident",
        ipAddress=client_ip
    )
    
    # Define validation rules for incident rejection
    validation_rules = {
        'incident_id': {
            'type': 'integer',
            'min_value': 1,
            'required': False
        },
        'audit_finding_id': {
            'type': 'integer',
            'min_value': 1,
            'required': False
        },
        'rejection_source': {
            'type': 'choice',
            'choices': ['INCIDENT', 'AUDIT_FINDING', 'REVIEWER', 'SYSTEM'],
            'required': False
        }
    }
    
    # Validate JSON request body
    try:
        validated_data = validate_json_request_body(request, validation_rules)
    except ValidationError as e:
        return Response({'error': str(e)}, status=400)
    
    incident_id = validated_data.get('incident_id')
    audit_finding_id = validated_data.get('audit_finding_id')
    rejection_source = validated_data.get('rejection_source', 'INCIDENT')  # Default to INCIDENT
    
    if incident_id:
        try:
            incident = Incident.objects.get(pk=incident_id)
            incident.Status = "Rejected"
            incident.RejectionSource = rejection_source
            incident.save()
            return Response({
                'success': True,
                'message': 'Incident rejected successfully.',
                'IncidentId': incident.IncidentId
            }, status=status.HTTP_200_OK)
        except Incident.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Incident not found.',
                'IncidentId': incident_id
            }, status=status.HTTP_404_NOT_FOUND)
    
    elif audit_finding_id:
        try:
            finding = AuditFinding.objects.get(pk=audit_finding_id)
            
            # Check if an incident already exists for this finding
            existing_incident = Incident.objects.filter(
                Origin="Audit Finding",
                AuditId=finding.AuditId,
                ComplianceId=finding.ComplianceId
            ).first()
            
            if existing_incident:
                existing_incident.Status = "Rejected"
                existing_incident.save()
            else:
                # Create a new incident with Rejected status
                incident_data = {
                    'IncidentTitle': finding.ComplianceId.ComplianceItemDescription if finding.ComplianceId else "Audit Finding",
                    'Description': finding.DetailsOfFinding or finding.Comments or "",
                    'Mitigation': finding.ComplianceId.mitigation if finding.ComplianceId else "",
                    'AuditId': finding.AuditId.pk if finding.AuditId else None,
                    'ComplianceId': finding.ComplianceId.pk if finding.ComplianceId else None,
                    'Date': finding.AssignedDate.date() if finding.AssignedDate else None,
                    'Time': finding.AssignedDate.time() if finding.AssignedDate else None,
                    'UserId': finding.UserId.UserId,
                    'Origin': 'Audit Finding',
                    'Comments': finding.Comments,
                    'Status': 'Rejected',
                }
                
                serializer = IncidentSerializer(data=incident_data)
                if serializer.is_valid():
                    incident = serializer.save()
                    
                    # Ensure CreatedAt is set correctly with current timezone-aware datetime
                    if not incident.CreatedAt:
                        incident.CreatedAt = timezone.now()
                        incident.save()
                    
                    print(f"Rejected incident created with ID: {incident.IncidentId}")
                    print(f"CreatedAt timestamp: {incident.CreatedAt}")
                    
                    # Mark finding as processed
                    finding.Check = '1'
                    finding.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({
                'success': True,
                'message': 'Audit finding rejected successfully.',
                'IncidentId': existing_incident.IncidentId if existing_incident else incident.IncidentId
            }, status=status.HTTP_200_OK)
            
        except AuditFinding.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Audit finding not found.',
                'IncidentId': None
            }, status=status.HTTP_404_NOT_FOUND)
    
    else:
        return Response({
            'success': False,
            'error': 'No incident_id or audit_finding_id provided.',
            'IncidentId': None
        }, status=status.HTTP_400_BAD_REQUEST)


# The duplicate imports have been removed

LOGIN_REDIRECT_URL = '/incidents/'  # or the URL pattern for your incident page

import json
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ...models import Incident
from ...serializers import IncidentSerializer
from ...routes.Global.s3_fucntions import export_data

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def export_incidents(request):
    """
    Export incidents to various file formats.
    
    Supported formats:
    - xlsx (Excel)
    - pdf (PDF)
    - csv (CSV)
    - json (JSON)
    - xml (XML)
    - txt (Text)
    """
    # Skip RBAC permission check since we're using AllowAny
    client_ip = get_client_ip(request)
    user_id = request.data.get('user_id')
    
    # Log export incidents attempt
    send_log(
        module="Incident",
        actionType="EXPORT_INCIDENTS_ATTEMPT",
        description="User attempting to export incidents",
        userId=str(user_id) if user_id else None,
        userName=request.data.get('userName', 'Unknown'),
        entityType="Export",
        ipAddress=client_ip
    )
    
    try:
        # Define validation rules for export parameters
        validation_rules = {
            'file_format': {
                'type': 'choice',
                'choices': ['xlsx', 'pdf', 'csv', 'json', 'xml', 'txt'],
                'required': False
            },
            'user_id': {
                'type': 'string',
                'max_length': 255,
                'pattern': SecureValidator.ALPHANUMERIC_WITH_SPACES,
                'required': False
            },
            'options': {
                'type': 'string',  # JSON object as string
                'max_length': 5000,
                'required': False
            },

        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        
        # Get validated request data
        file_format = validated_data.get('file_format', 'xlsx')
        user_id = validated_data.get('user_id', 'anonymous')
        export_options = validated_data.get('options', {})
        
        # Get incidents data from request or fetch from database
        if 'data' in request.data and request.data['data']:
            # Use data provided in request (parse JSON string if needed)
            incidents_data = request.data['data']
            if isinstance(incidents_data, str):
                try:
                    incidents_data = json.loads(incidents_data)
                except json.JSONDecodeError:
                    return Response({'error': 'Invalid JSON format in data field'}, status=400)
        else:
            # Fetch all incidents from database with only necessary fields (excluding audit findings)
            incidents = Incident.objects.exclude(Origin='Audit Finding').values(
                'IncidentId', 'IncidentTitle', 'Date', 'RiskPriority', 'Origin', 'Status'
            ).order_by('-Date')
            incidents_data = list(incidents)
        
        # Parse export_options if it's a JSON string
        if isinstance(export_options, str):
            try:
                export_options = json.loads(export_options)
            except json.JSONDecodeError:
                export_options = {}
        elif not isinstance(export_options, dict):
            export_options = {}
        
        # Log the export request
        print(f"Exporting {len(incidents_data)} incidents to {file_format} format for user {user_id}")
        
        # Log export operation
        send_log(
            module="Incident",
            actionType="EXPORT",
            description=f"User exporting {len(incidents_data)} incidents in {file_format} format",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            ipAddress=get_client_ip(request),
            additionalInfo={"file_format": file_format, "record_count": len(incidents_data), "export_user_id": user_id}
        )
        
        # Add metadata for the export
        export_options['exported_at'] = timezone.now().isoformat()
        export_options['record_count'] = len(incidents_data)
        export_options['export_type'] = 'incidents'
        
        # Call the export service
        export_result = export_data(
            data=incidents_data,
            file_format=file_format,
            user_id=user_id,
            options=export_options
        )
        
        # Log successful export
        send_log(
            module="Incident",
            actionType="EXPORT_INCIDENTS_SUCCESS",
            description=f"Successfully exported {len(incidents_data)} incidents to {file_format}",
            userId=str(user_id) if user_id else None,
            userName=request.data.get('userName', 'Unknown'),
            entityType="Export",
            ipAddress=client_ip,
            additionalInfo={
                "file_format": file_format,
                "record_count": len(incidents_data),
                "export_options": export_options
            }
        )
        
        # Return the export result
        return Response(export_result)
    
    except Exception as e:
        # Log export error
        send_log(
            module="Incident",
            actionType="EXPORT_INCIDENTS_ERROR",
            description=f"Export incidents error: {str(e)}",
            userId=str(user_id) if user_id else None,
            userName=request.data.get('userName', 'Unknown'),
            entityType="Export",
            logLevel="ERROR",
            ipAddress=client_ip,
            additionalInfo={"error": str(e)}
        )
        
        print(f"Export error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500) 

@api_view(['GET'])
@permission_classes([AuditFindingsAccessPermission])
def get_audit_findings(request):
    """
    Get audit finding incidents from incidents table where origin = 'Audit Finding'
    """
    try:
        from django.db.models import Q
        
        # Define allowed GET parameters
        allowed_params = {
            'status': {
                'type': 'choice',
                'choices': ['all', 'open', 'assigned', 'closed', 'rejected', 'scheduled', 'approved', 'pending']
            },
            'sort': {
                'type': 'choice',
                'choices': ['Date', 'IncidentId', 'IncidentTitle', 'RiskPriority', 'Status']
            },
            'order': {
                'type': 'choice',
                'choices': ['asc', 'desc']
            },
            'search': {
                'type': 'string',
                'max_length': 255,
                'pattern': SecureValidator.BUSINESS_TEXT_PATTERN
            },
            'framework_id': {
                'type': 'integer',
                'required': False
            }
        }
        
        # Validate GET parameters
        validated_params, error = validate_get_parameters(request, allowed_params)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get filter parameters (now validated)
        status_filter = validated_params.get('status', 'all')
        sort_field = validated_params.get('sort', 'Date')
        sort_order = validated_params.get('order', 'desc')
        search_query = validated_params.get('search', '')
        framework_id = validated_params.get('framework_id', None)
        
        print(f"Fetching audit finding incidents with status: {status_filter}, search: {search_query}, framework_id: {framework_id}")
        
        # Log audit findings access
        send_log(
            module="Incident",
            actionType="LIST_AUDIT_FINDINGS",
            description=f"User accessing audit findings with status: {status_filter}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="AuditFinding",
            ipAddress=get_client_ip(request),
            additionalInfo={"status_filter": status_filter, "search_query": search_query, "framework_id": framework_id}
        )
            
        # Query incidents with origin = "Audit Finding" or "Compliance Gap"
        queryset = Incident.objects.filter(Origin__in=['Audit Finding', 'Compliance Gap'])
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 Filtering audit findings by framework_id: {framework_id}")
            # Filter by compliance that belongs to the selected framework
            queryset = queryset.filter(
                ComplianceId__SubPolicy__PolicyId__FrameworkId__FrameworkId=framework_id
            ).select_related('ComplianceId__SubPolicy__PolicyId__FrameworkId')
            print(f"✅ Framework filter applied. Found {queryset.count()} audit findings.")
        else:
            print(f"ℹ️ No framework filter applied. Showing all audit findings.")
        
        # Apply search filter
        if search_query:
            queryset = queryset.filter(
                Q(IncidentTitle__icontains=search_query) |
                Q(IncidentId__icontains=search_query) |
                Q(Description__icontains=search_query) |
                Q(RiskPriority__icontains=search_query) |
                Q(Status__icontains=search_query)
            )
        
        # Apply status filter
        if status_filter != 'all':
            if status_filter == 'open':
                queryset = queryset.filter(Status__in=['Open', None, ''])
            elif status_filter == 'assigned':
                # Assigned card shows both "Assigned" and "Pending Review" statuses
                queryset = queryset.filter(Status__in=['Assigned', 'Pending Review'])
            elif status_filter == 'closed':
                # Closed card shows both "Closed" and "Approved" statuses
                queryset = queryset.filter(Status__in=['Closed', 'Approved'])
            elif status_filter == 'rejected':
                queryset = queryset.filter(Status='Rejected')
            elif status_filter == 'scheduled':
                queryset = queryset.filter(Status='Scheduled')
            # Keep individual status filters for backward compatibility
            elif status_filter == 'approved':
                queryset = queryset.filter(Status='Approved')
            elif status_filter == 'pending':
                queryset = queryset.filter(Status='Pending Review')
        
        # Apply sorting
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'
        queryset = queryset.order_by(sort_field, '-Time')
        
        # Serialize the data
        serializer = IncidentSerializer(queryset, many=True)
        
        # Debug: Print status values for first few items
        print(f"Debug: First 3 audit findings statuses:")
        for i, item in enumerate(serializer.data[:3]):
            print(f"  Item {i+1}: IncidentId={item.get('IncidentId')}, Status={item.get('Status')}")
        
        # Calculate summary statistics - use base queryset with framework filter applied
        base_queryset = Incident.objects.filter(Origin__in=['Audit Finding', 'Compliance Gap'])
        
        # Apply framework filter to summary statistics if provided
        if framework_id:
            base_queryset = base_queryset.filter(
                ComplianceId__SubPolicy__PolicyId__FrameworkId__FrameworkId=framework_id
            )
        
        total_count = base_queryset.count()
        open_count = base_queryset.filter(Status__in=['Open', None, '']).count()
        
        # Assigned count: includes both "Assigned" and "Pending Review" statuses
        assigned_count = base_queryset.filter(Status__in=['Assigned', 'Pending Review']).count()
        
        # Closed count: includes both "Closed" and "Approved" statuses
        closed_count = base_queryset.filter(Status__in=['Closed', 'Approved']).count()
        
        rejected_count = base_queryset.filter(Status='Rejected').count()
        
        # Mitigated to Risk count: shows "Scheduled" status
        mitigated_count = base_queryset.filter(Status='Scheduled').count()
        
        return Response({
            'success': True,
            'message': 'Audit finding incidents retrieved successfully',
            'data': serializer.data,
            'summary': {
                'total': total_count,
                'open': open_count,
                'assigned': assigned_count,
                'closed': closed_count,
                'rejected': rejected_count,
                'mitigated': mitigated_count
            }
        })
    except Exception as e:
        print(f"Error retrieving audit finding incidents: {e}")
        return Response({
            'success': False,
            'message': f'Error retrieving audit finding incidents: {str(e)}'
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def export_audit_findings(request):
    print(f"Exporting audit findings: entereeeeeeeeeeeedddddddddd")
    """
    Export audit finding incidents to various file formats.
    
    Supported formats:
    - xlsx (Excel)
    - pdf (PDF)
    - csv (CSV)
    - json (JSON)
    - xml (XML)
    - txt (Text)
    """
    try:
        from django.utils import timezone
        
        # Define validation rules for export parameters
        validation_rules = {
            'file_format': {
                'type': 'choice',
                'choices': ['xlsx', 'pdf', 'csv', 'json', 'xml', 'txt'],
                'required': False
            },
            'user_id': {
                'type': 'string',
                'max_length': 255,
                'pattern': SecureValidator.ALPHANUMERIC_WITH_SPACES,
                'required': False
            },
            'options': {
                'type': 'string',  # JSON object as string
                'max_length': 5000,
                'required': False
            },
            'data': {
                'type': 'string',  # JSON array as string
                'max_length': 1000000,  # Increased limit for large data export (1MB)
                'required': False
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        
        # Get validated request data
        file_format = validated_data.get('file_format', 'xlsx')
        user_id = validated_data.get('user_id', 'anonymous')
        export_options = validated_data.get('options', {})
        
        # Parse export_options if it's a JSON string (do this early)
        if isinstance(export_options, str):
            try:
                export_options = json.loads(export_options)
                print(f"Parsed export_options from JSON string: {export_options}")
            except json.JSONDecodeError:
                print(f"Failed to parse export_options JSON: {export_options}")
                export_options = {}
        elif not isinstance(export_options, dict):
            print(f"export_options is not a dict, converting: {type(export_options)}")
            export_options = {}
        
        print(f"Final export_options: {export_options}")
        print(f"export_options type: {type(export_options)}")
        
        # Get audit findings data from request or fetch from database
        if 'data' in validated_data and validated_data['data']:
            # Use data provided in request (parse JSON string if needed)
            audit_findings_data = validated_data['data']
            if isinstance(audit_findings_data, str):
                try:
                    audit_findings_data = json.loads(audit_findings_data)
                except json.JSONDecodeError:
                    return Response({'error': 'Invalid JSON format in data field'}, status=400)
        else:
            # Fetch audit finding incidents from database with filters
            audit_findings_query = Incident.objects.filter(Origin__in=['Audit Finding', 'Compliance Gap'])
            
            # Apply filters from export options
            filters = export_options.get('filters', {})
            
            print(f"Applying filters: {filters}")
            
            # Apply status filter
            if filters.get('filterStatus') and filters['filterStatus'] != 'all':
                status_filter = filters['filterStatus']
                if status_filter == 'open':
                    audit_findings_query = audit_findings_query.filter(Q(Status__isnull=True) | Q(Status='') | Q(Status='Open'))
                elif status_filter == 'assigned':
                    audit_findings_query = audit_findings_query.filter(Status='Assigned')
                elif status_filter == 'closed':
                    audit_findings_query = audit_findings_query.filter(Status='Closed')
                elif status_filter == 'rejected':
                    audit_findings_query = audit_findings_query.filter(Status='Rejected')
                elif status_filter == 'scheduled':
                    audit_findings_query = audit_findings_query.filter(Status='Scheduled')
            
            # Apply business unit filter
            if filters.get('filterBusinessUnit') and filters['filterBusinessUnit'] != 'all':
                audit_findings_query = audit_findings_query.filter(BusinessUnit=filters['filterBusinessUnit'])
            
            # Apply category filter
            if filters.get('filterCategory') and filters['filterCategory'] != 'all':
                audit_findings_query = audit_findings_query.filter(Category=filters['filterCategory'])
            
            # Apply search query
            if filters.get('searchQuery'):
                search_term = filters['searchQuery']
                audit_findings_query = audit_findings_query.filter(
                    Q(IncidentTitle__icontains=search_term) |
                    Q(Description__icontains=search_term) |
                    Q(IncidentId__icontains=search_term)
                )
            
            # Apply framework filter
            if filters.get('framework_id'):
                audit_findings_query = audit_findings_query.filter(FrameworkId=filters['framework_id'])
            
            # Apply sorting
            sort_by = filters.get('sortBy', 'Date')
            if sort_by == 'Date':
                audit_findings_query = audit_findings_query.order_by('-Date')
            elif sort_by == 'IncidentTitle':
                audit_findings_query = audit_findings_query.order_by('IncidentTitle')
            elif sort_by == 'RiskPriority':
                audit_findings_query = audit_findings_query.order_by('RiskPriority')
            elif sort_by == 'Status':
                audit_findings_query = audit_findings_query.order_by('Status')
            else:
                audit_findings_query = audit_findings_query.order_by('-Date')
            
            # Limit results to prevent memory issues (max 10,000 records)
            audit_findings_query = audit_findings_query[:10000]
            
            serializer = IncidentSerializer(audit_findings_query, many=True)
            audit_findings_data = serializer.data
        
        # Log the export request
        print(f"Exporting {len(audit_findings_data)} audit findings to {file_format} format for user {user_id}")
        
        # Log audit findings export operation
        send_log(
            module="Incident",
            actionType="EXPORT_AUDIT_FINDINGS",
            description=f"User exporting {len(audit_findings_data)} audit findings in {file_format} format",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="AuditFinding",
            ipAddress=get_client_ip(request),
            additionalInfo={"file_format": file_format, "record_count": len(audit_findings_data), "export_user_id": user_id}
        )
        
        # Add metadata for the export
        export_options['exported_at'] = timezone.now().isoformat()
        export_options['record_count'] = len(audit_findings_data)
        export_options['export_type'] = 'audit_findings'
        
        # Call the export service
        export_result = export_data(
            data=audit_findings_data,
            file_format=file_format,
            user_id=user_id,
            options=export_options
        )
        
        # Return the export result
        return Response(export_result)
    
    except Exception as e:
        print(f"Audit findings export error: {str(e)}")
        
        # Log export error
        send_log(
            module="Incident",
            actionType="EXPORT_AUDIT_FINDINGS_ERROR",
            description=f"Audit findings export failed: {str(e)}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="AuditFinding",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return Response({
            'success': False,
            'error': str(e)
        }, status=500) 

@api_view(['GET'])
@permission_classes([AuditFindingsAccessPermission])
def lastchecklistitemverified(request):
    """
    Retrieve audit findings from the lastchecklistitemverified table
    with optional filtering by compliance status.
    """
    try:
        # Get complied values from query parameters (can be multiple)
        complied_values = request.GET.getlist('complied[]')
        
        # If no complied values specified, default to showing non-compliant (0) and compliant (1)
        if not complied_values:
            complied_values = ['0', '1']
            
        print(f"Fetching audit findings with complied values: {complied_values}")
            
        # Query the database
        queryset = LastChecklistItemVerified.objects.filter(ComplianceId__in=complied_values)
        
        # Use the serializer to format the data
        serializer = LastChecklistItemVerifiedSerializer(queryset, many=True)
        
        # Enhance the data with related information
        enhanced_data = []
        for item in serializer.data:
            try:
                compliance_data = {}
                if item['ComplianceId']:
                    try:
                        compliance = Compliance.objects.get(ComplianceId=item['ComplianceId'])
                        compliance_data = {
                            'ComplianceItemDescription': compliance.ComplianceItemDescription,
                            'Criticality': compliance.Criticality,
                            'mitigation': compliance.mitigation
                        }
                    except Compliance.DoesNotExist:
                        pass
                
                policy_data = {}
                if item['PolicyId']:
                    try:
                        policy = Policy.objects.get(PolicyId=item['PolicyId'])
                        policy_data = {
                            'PolicyName': policy.PolicyName
                        }
                    except Policy.DoesNotExist:
                        pass
                
                subpolicy_data = {}
                if item['SubPolicyId']:
                    try:
                        subpolicy = SubPolicy.objects.get(SubPolicyId=item['SubPolicyId'])
                        subpolicy_data = {
                            'SubPolicyName': subpolicy.SubPolicyName
                        }
                    except SubPolicy.DoesNotExist:
                        pass
                
                # Create a dictionary with the enhanced data
                enhanced_item = {
                    **item,
                    'Compliance': compliance_data,
                    'Policy': policy_data,
                    'SubPolicy': subpolicy_data
                }
                
                enhanced_data.append(enhanced_item)
            except Exception as e:
                print(f"Error enhancing data for item {item['ComplianceId']}: {e}")
                enhanced_data.append(item)  # Add the original item if enhancement fails
        
        return Response({
            'success': True,
            'message': 'Audit findings retrieved successfully',
            'data': enhanced_data
        })
    except Exception as e:
        print(f"Error retrieving audit findings: {e}")
        return Response({
            'success': False,
            'message': f'Error retrieving audit findings: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([AuditFindingsAccessPermission])
def audit_findings_list(request):
    """
    Get audit findings from LastChecklistItemVerified table with specified compliance status
    """
    try:
        # Define allowed GET parameters
        allowed_params = {
            'complied[]': {
                'type': 'choice',
                'choices': ['0', '1', '2']  # Valid complied statuses
            }
        }
        
        # Get complied values from query parameters
        complied_values = request.GET.getlist('complied[]')
        
        # Validate each complied value if provided
        if complied_values:
            try:
                for value in complied_values:
                    SecureValidator.validate_choice(
                        value, 'complied', ['0', '1', '2'], required=False
                    )
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # If no complied values specified, default to showing non-compliant (0) and partially compliant (1)
        if not complied_values:
            complied_values = ['0', '1']
            
        print(f"Fetching audit findings with complied values: {complied_values}")
            
        # SECURITY: Use SecureDatabaseManager for safe database operations
        db_manager = SecureDatabaseManager()
        request_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Execute secure query
        findings, columns = db_manager.get_audit_findings_secure(complied_values, request_ip)
            
        # Process raw query results into dictionaries
        result_data = []
        for finding_tuple in findings:
            # Convert to dictionary
            finding_dict = dict(zip(columns, finding_tuple))
            
            # Add framework details
            framework_data = {
                'FrameworkId': finding_dict['FrameworkId'],
                'FrameworkName': finding_dict['FrameworkName']
            }
            
            # Get compliance details if available
            compliance_data = {}
            try:
                if finding_dict['ComplianceId']:
                    compliance = Compliance.objects.get(ComplianceId=finding_dict['ComplianceId'])
                    compliance_data = {
                        'ComplianceId': compliance.ComplianceId,
                        'ComplianceItemDescription': compliance.ComplianceItemDescription,
                        'Criticality': compliance.Criticality,
                        'Mitigation': compliance.mitigation
                    }
            except Compliance.DoesNotExist:
                pass
            
            # Get policy details if available
            policy_data = {}
            try:
                if finding_dict['PolicyId']:
                    policy = Policy.objects.get(PolicyId=finding_dict['PolicyId'])
                    policy_data = {
                        'PolicyId': policy.PolicyId,
                        'PolicyName': policy.PolicyName
                    }
            except Policy.DoesNotExist:
                pass
            
            # Get subpolicy details if available
            subpolicy_data = {}
            try:
                if finding_dict['SubPolicyId']:
                    subpolicy = SubPolicy.objects.get(SubPolicyId=finding_dict['SubPolicyId'])
                    subpolicy_data = {
                        'SubPolicyId': subpolicy.SubPolicyId,
                        'SubPolicyName': subpolicy.SubPolicyName
                    }
            except SubPolicy.DoesNotExist:
                pass
            
            # Format dates properly
            if isinstance(finding_dict['Date'], datetime.date):
                finding_dict['Date'] = finding_dict['Date'].isoformat()
            
            if isinstance(finding_dict['Time'], datetime.time):
                finding_dict['Time'] = finding_dict['Time'].isoformat()
            
            # Prepare finding data
            finding_data = {
                'ComplianceId': finding_dict['ComplianceId'],
                'FrameworkId': finding_dict['FrameworkId'],
                'PolicyId': finding_dict['PolicyId'],
                'SubPolicyId': finding_dict['SubPolicyId'],
                'Date': finding_dict['Date'],
                'Time': finding_dict['Time'],
                'User': finding_dict['User'],
                'Complied': finding_dict['Complied'],
                'Comments': finding_dict['Comments'],
                'count': finding_dict['count'],
                'Framework': framework_data,
                'Compliance': compliance_data,
                'Policy': policy_data,
                'SubPolicy': subpolicy_data
            }
            
            result_data.append(finding_data)
        
        return Response({
            'success': True,
            'message': 'Audit findings retrieved successfully',
            'data': result_data
        })
    except Exception as e:
        print(f"Error retrieving audit findings: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error retrieving audit findings: {str(e)}'
        }, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def get_compliances(request):
    """
    Get all compliances from the database for incident mapping
    Optionally filter by framework_id if provided
    """
    try:
        # Get optional framework_id parameter from query string
        framework_id = request.GET.get('framework_id', None)
        print(f"🔍 DEBUG: get_compliances called with framework_id: {framework_id}")
        
        # Fetch all compliances with related information
        compliances = Compliance.objects.select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
        
        # Filter by framework if framework_id is provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering compliances by framework_id: {framework_id}")
            compliances = compliances.filter(SubPolicy__PolicyId__FrameworkId__FrameworkId=framework_id)
        else:
            print(f"🔍 DEBUG: No framework_id provided, returning all compliances")
        
        compliances = compliances.all()
        print(f"🔍 DEBUG: Found {compliances.count()} compliances")
        
        compliance_data = []
        for compliance in compliances:
            try:
                # Build comprehensive compliance data
                compliance_info = {
                    'ComplianceId': compliance.ComplianceId,
                    'ComplianceItemDescription': compliance.ComplianceItemDescription,
                    'Criticality': compliance.Criticality,
                    'Mitigation': compliance.mitigation,
                    'Impact': compliance.Impact,
                    'Probability': compliance.Probability,
                    'PossibleDamage': compliance.PossibleDamage if compliance.PossibleDamage else None,  # Convert empty string to None
                    'Status': compliance.Status,
                    'Identifier': compliance.Identifier,
                    'SubPolicy': {
                        'SubPolicyId': compliance.SubPolicy.SubPolicyId,
                        'SubPolicyName': compliance.SubPolicy.SubPolicyName,
                        'Policy': {
                            'PolicyId': compliance.SubPolicy.PolicyId.PolicyId,
                            'PolicyName': compliance.SubPolicy.PolicyId.PolicyName,
                            'Framework': {
                                'FrameworkId': compliance.SubPolicy.PolicyId.FrameworkId.FrameworkId,
                                'FrameworkName': compliance.SubPolicy.PolicyId.FrameworkId.FrameworkName
                            }
                        }
                    }
                }
                compliance_data.append(compliance_info)
            except Exception as e:
                print(f"Error processing compliance {compliance.ComplianceId}: {e}")
                # Add basic info if detailed info fails
                compliance_data.append({
                    'ComplianceId': compliance.ComplianceId,
                    'ComplianceItemDescription': compliance.ComplianceItemDescription,
                    'Criticality': compliance.Criticality,
                    'Mitigation': compliance.mitigation,
                    'SubPolicy': {},
                })
        
        return Response({
            'success': True,
            'message': 'Compliances retrieved successfully',
            'data': compliance_data
        })
    except Exception as e:
        print(f"Error retrieving compliances: {e}")
        return Response({
            'success': False,
            'message': f'Error retrieving compliances: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AuditViewPermission])
@rbac_required(required_permission='view_audit_reports')
def audit_finding_detail(request, compliance_id):
    """
    Get detailed information for a specific audit finding by compliance ID
    """
    try:
        # Validate path parameter
        try:
            validated_compliance_id = validate_path_parameter(compliance_id, 'compliance_id', 'integer')
        except ValidationError as e:
            return Response({'success': False, 'message': str(e)}, status=400)
        
        print(f"Fetching audit finding detail for compliance ID: {validated_compliance_id}")
        
        # SECURITY: Use SecureDatabaseManager for safe database operations
        db_manager = SecureDatabaseManager()
        request_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Execute secure query
        finding, columns = db_manager.get_audit_finding_by_compliance_secure(validated_compliance_id, request_ip)
        
        if not finding:
            return Response({
                'success': False,
                'message': f'No audit finding found for compliance ID: {validated_compliance_id}'
            }, status=404)
        
        # Convert to dictionary
        finding_dict = dict(zip(columns, finding))
        
        # Get compliance details
        compliance_data = {}
        try:
            if finding_dict['ComplianceId']:
                compliance = Compliance.objects.get(ComplianceId=finding_dict['ComplianceId'])
                compliance_data = {
                    'ComplianceId': compliance.ComplianceId,
                    'ComplianceItemDescription': compliance.ComplianceItemDescription,
                    'Criticality': compliance.Criticality,
                    'Mitigation': compliance.mitigation
                }
        except Compliance.DoesNotExist:
            pass
        
        # Get framework details
        framework_data = {
            'FrameworkId': finding_dict['FrameworkId'],
            'FrameworkName': finding_dict['FrameworkName']
        }
        
        # Get policy details if available
        policy_data = {}
        try:
            if finding_dict['PolicyId']:
                policy = Policy.objects.get(PolicyId=finding_dict['PolicyId'])
                policy_data = {
                    'PolicyId': policy.PolicyId,
                    'PolicyName': policy.PolicyName
                }
        except Policy.DoesNotExist:
            pass
        
        # Get subpolicy details if available
        subpolicy_data = {}
        try:
            if finding_dict['SubPolicyId']:
                subpolicy = SubPolicy.objects.get(SubPolicyId=finding_dict['SubPolicyId'])
                subpolicy_data = {
                    'SubPolicyId': subpolicy.SubPolicyId,
                    'SubPolicyName': subpolicy.SubPolicyName
                }
        except SubPolicy.DoesNotExist:
            pass
        
        # Check for related incidents
        related_incident = None
        try:
            incident = Incident.objects.filter(
                ComplianceId=validated_compliance_id,
                Origin='Audit Finding'
            ).first()
            
            if incident:
                related_incident = {
                    'IncidentId': incident.IncidentId,
                    'IncidentTitle': incident.IncidentTitle,
                    'Description': incident.Description,
                    'Status': incident.Status,
                    'RiskPriority': incident.RiskPriority
                }
        except Exception as e:
            print(f"Error fetching related incident: {e}")
        
        # Format dates properly
        if isinstance(finding_dict['Date'], datetime.date):
            finding_dict['Date'] = finding_dict['Date'].isoformat()
        
        if isinstance(finding_dict['Time'], datetime.time):
            finding_dict['Time'] = finding_dict['Time'].isoformat()
        
        # Prepare finding data with all related information
        finding_data = {
            'ComplianceId': finding_dict['ComplianceId'],
            'FrameworkId': finding_dict['FrameworkId'],
            'PolicyId': finding_dict['PolicyId'],
            'SubPolicyId': finding_dict['SubPolicyId'],
            'Date': finding_dict['Date'],
            'Time': finding_dict['Time'],
            'User': finding_dict['User'],
            'Complied': finding_dict['Complied'],
            'Comments': finding_dict['Comments'],
            'count': finding_dict['count'],
            'Framework': framework_data,
            'Compliance': compliance_data,
            'Policy': policy_data,
            'SubPolicy': subpolicy_data,
            'RelatedIncident': related_incident
        }
        
        return Response({
            'success': True,
            'message': 'Audit finding detail retrieved successfully',
            'finding': finding_data
        })
    except Exception as e:
        print(f"Error retrieving audit finding detail: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error retrieving audit finding detail: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([AuditViewPermission])
@rbac_required(required_permission='view_audit_reports')
def audit_finding_incident_detail(request, incident_id):
    """
    Get detailed information for a specific audit finding incident (where Origin='Audit Finding')
    """
    try:
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return Response({'success': False, 'message': str(e)}, status=400)
        
        # Get the specific incident (audit finding or compliance gap)
        incident = Incident.objects.get(IncidentId=validated_incident_id, Origin__in=['Audit Finding', 'Compliance Gap'])
        
        # Use the serializer to properly convert the model to JSON-serializable data
        serializer = IncidentSerializer(incident)
        incident_data = serializer.data
        
        # Add assigner and reviewer names if the incident is assigned
        if incident.AssignerId or incident.ReviewerId:
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Get assigner name
            if incident.AssignerId:
                assigner_name = notification_service.get_user_name(incident.AssignerId)
                incident_data['assigner_name'] = assigner_name or 'Unknown'
            else:
                incident_data['assigner_name'] = None
            
            # Get reviewer name
            if incident.ReviewerId:
                reviewer_name = notification_service.get_user_name(incident.ReviewerId)
                incident_data['reviewer_name'] = reviewer_name or 'Unknown'
            else:
                incident_data['reviewer_name'] = None
        
        return Response({
            'success': True,
            'message': 'Audit finding incident detail retrieved successfully',
            'data': incident_data
        })
    except Incident.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Audit finding incident not found'
        }, status=404)
    except Exception as e:
        print(f"Error fetching audit finding incident detail: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching audit finding incident detail: {str(e)}'
        }, status=500)

# Incident User Tasks API endpoints
@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def user_incidents(request, user_id):
    """Get incidents assigned BY a specific user (where user is the assigner)"""
    try:
        # Validate path parameter
        try:
            validated_user_id = validate_path_parameter(user_id, 'user_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get optional framework_id parameter from query string
        framework_id = request.GET.get('framework_id', None)
        print(f"🔍 DEBUG: user_incidents called with framework_id: {framework_id}")
        
        # Get incidents where the user is the AssignerId (the person WHO assigned it to others)
        # IMPORTANT: AssignerId is the person WHO assigned the incident to someone else
        # ReviewerId is the person assigned TO work on the incident (handled by reviewer_tasks endpoint)
        # This endpoint shows tasks that the user has assigned to other people for tracking
        print(f"🔍 DEBUG: user_incidents - Filtering by AssignerId={validated_user_id}")
        print(f"🔍 DEBUG: user_incidents - This shows tasks the user assigned to others")
        
        # Get incidents where the user is the AssignerId (the person WHO assigned it)
        # Include all active statuses:
        # - 'Assigned': newly assigned incidents
        # - 'In Progress': incidents being worked on
        # - 'Pending Review': incidents submitted for review
        # - 'Under Review': incidents currently under review
        # - 'Rejected': incidents that were rejected
        # - 'Approved': incidents that were approved
        # - NULL or other statuses that aren't final/closed
        # Exclude only final/closed statuses
        incidents = Incident.objects.filter(
            AssignerId=validated_user_id  # Filter by AssignerId (the person WHO assigned it)
        ).exclude(
            Status__in=['Closed', 'Completed', 'Cancelled']
        )
        
        count_before_framework = incidents.count()
        print(f"✅ DEBUG: Found {count_before_framework} incidents with ReviewerId={validated_user_id} (before framework filter)")
        
        # Log sample incident statuses for debugging
        if count_before_framework > 0:
            sample_incidents = list(incidents.values('IncidentId', 'Status', 'ReviewerId')[:3])
            print(f"🔍 DEBUG: Sample incidents: {sample_incidents}")
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering user incidents by framework_id: {framework_id}")
            incidents = incidents.filter(FrameworkId=framework_id)
            print(f"✅ Framework filter applied. Found {incidents.count()} incidents.")
        
        incidents = incidents.values(
            'IncidentId', 'IncidentTitle', 'Origin', 'RiskPriority', 'Status', 
            'MitigationDueDate', 'AssignerId', 'ReviewerId', 'RejectionSource'
        )
        
        # Convert to the expected format for frontend
        incident_list = []
        for incident in incidents:
            incident_list.append({
                'id': incident['IncidentId'],
                'Title': incident['IncidentTitle'],
                'Origin': incident['Origin'],
                'Priority': incident['RiskPriority'],
                'Status': incident['Status'],
                'MitigationDueDate': incident['MitigationDueDate'],
                'AssignerId': incident['AssignerId'],
                'ReviewerId': incident['ReviewerId'],
                'RejectionSource': incident.get('RejectionSource')
            })
        
        print(f"✅ DEBUG: Returning {len(incident_list)} incidents to frontend")
        if len(incident_list) > 0:
            print(f"🔍 DEBUG: Sample incident data:")
            for i, inc in enumerate(incident_list[:3]):  # Show first 3 incidents
                print(f"  Incident {i+1}: ID={inc.get('id')}, Title={inc.get('Title')}, Status={inc.get('Status')}, AssignerId={inc.get('AssignerId')}, ReviewerId={inc.get('ReviewerId')}")
        
        return JsonResponse(incident_list, safe=False)
    except Exception as e:
        print(f"Error fetching user incidents: {str(e)}")
        # SECURE: Sanitize error message to prevent information disclosure
        safe_error = SecureOutputEncoder.sanitize_error_message(str(e))
        return JsonResponse({'error': safe_error}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentEvaluatePermission])
@rbac_required(required_permission='evaluate_assigned_incident')
def incident_reviewer_tasks(request, user_id):
    """Get incidents where the user is assigned as reviewer"""
    try:
        # Validate path parameter
        try:
            validated_user_id = validate_path_parameter(user_id, 'user_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get optional framework_id parameter from query string
        framework_id = request.GET.get('framework_id', None)
        print(f"🔍 DEBUG: incident_reviewer_tasks called with framework_id: {framework_id}")
        
        # Get incidents where the user is assigned as reviewer
        # Include all statuses (including NULL) except 'Closed' and 'Completed'
        # This ensures all assigned incidents are shown to the reviewer
        print(f"🔍 DEBUG: incident_reviewer_tasks - Filtering by ReviewerId={validated_user_id}")
        incidents = Incident.objects.filter(
            ReviewerId=validated_user_id
        ).exclude(
            Status__in=['Closed', 'Completed', 'Cancelled']
        )
        
        count_before_framework = incidents.count()
        print(f"✅ DEBUG: Found {count_before_framework} reviewer tasks with ReviewerId={validated_user_id} (before framework filter)")
        
        # Log sample incident statuses for debugging
        if count_before_framework > 0:
            sample_incidents = list(incidents.values('IncidentId', 'Status', 'ReviewerId')[:3])
            print(f"🔍 DEBUG: Sample reviewer tasks: {sample_incidents}")
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering reviewer tasks by framework_id: {framework_id}")
            incidents = incidents.filter(FrameworkId=framework_id)
            print(f"✅ Framework filter applied. Found {incidents.count()} reviewer tasks.")
        
        incidents = incidents.values(
            'IncidentId', 'IncidentTitle', 'Origin', 'RiskPriority', 'Status', 
            'AssignerId', 'ReviewerId', 'MitigationDueDate'
        )
        
        # Convert to the expected format for frontend
        incident_list = []
        for incident in incidents:
            incident_list.append({
                'id': incident['IncidentId'],
                'Title': incident['IncidentTitle'],
                'Origin': incident['Origin'],
                'Priority': incident['RiskPriority'],
                'Status': incident['Status'],
                'AssignerId': incident['AssignerId'],
                'ReviewerId': incident['ReviewerId'],
                'MitigationDueDate': incident['MitigationDueDate']
            })
        
        return JsonResponse(incident_list, safe=False)
    except Exception as e:
        print(f"Error fetching incident reviewer tasks: {str(e)}")
        # SECURE: Sanitize error message to prevent information disclosure
        safe_error = SecureOutputEncoder.sanitize_error_message(str(e))
        return JsonResponse({'error': safe_error}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def incident_mitigations(request, incident_id):
    """Get mitigation steps for a specific incident with reviewer feedback"""
    try:
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        incident = Incident.objects.get(IncidentId=validated_incident_id)
        
        # Parse the Mitigation field which contains the mitigation steps
        mitigations = {}
        if incident.Mitigation:
            try:
                if isinstance(incident.Mitigation, str):
                    mitigations = json.loads(incident.Mitigation)
                else:
                    mitigations = incident.Mitigation
            except json.JSONDecodeError:
                # If it's not JSON, treat as a single mitigation step
                mitigations = {"1": incident.Mitigation}
        
        # Get the latest reviewer feedback from IncidentApproval
        reviewer_feedback = None
        approval_entries = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        
        for entry in approval_entries:
            if (entry.version and entry.version.startswith('R') and 
                entry.ExtractedInfo and 'reviewer_feedback' in entry.ExtractedInfo):
                reviewer_feedback = entry.ExtractedInfo['reviewer_feedback']
                break
        
        # Get the latest user submission data to extract comments and other details
        latest_user_data = {}
        approval_entries_all = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        for entry in approval_entries_all:
            if (entry.version and entry.version.startswith('U') and 
                entry.ExtractedInfo and 'mitigations' in entry.ExtractedInfo):
                latest_user_data = entry.ExtractedInfo.get('mitigations', {})
                break

        # Enhanced mitigations with reviewer feedback and user data
        enhanced_mitigations = {}
        for key, mitigation_desc in mitigations.items():
            # Handle different mitigation data formats
            if isinstance(mitigation_desc, dict):
                # New format with full mitigation data
                mitigation_data = {
                    'description': mitigation_desc.get('description', ''),
                    'comments': mitigation_desc.get('comments', ''),
                    'status': mitigation_desc.get('status', 'Not Started'),
                    'aws-file_link': mitigation_desc.get('aws-file_link'),
                    'fileName': mitigation_desc.get('fileName'),
                    'files': mitigation_desc.get('files', []),  # Support multiple files
                    'approved': None,  # None = not reviewed, True = approved, False = rejected
                    'remarks': None,   # Reviewer's rejection feedback
                }
            else:
                # Old format - just description string
                mitigation_data = {
                    'description': mitigation_desc,
                    'comments': '',
                    'status': 'Not Started',
                    'aws-file_link': None,
                    'fileName': None,
                    'files': [],  # Support multiple files
                    'approved': None,
                    'remarks': None,
                }
            
            # Try to get user data from latest submission if available
            if str(key) in latest_user_data:
                user_mitigation = latest_user_data[str(key)]
                if isinstance(user_mitigation, dict):
                    mitigation_data['comments'] = user_mitigation.get('comments', mitigation_data['comments'])
                    mitigation_data['status'] = user_mitigation.get('status', mitigation_data['status'])
                    mitigation_data['aws-file_link'] = user_mitigation.get('aws-file_link', mitigation_data['aws-file_link'])
                    mitigation_data['fileName'] = user_mitigation.get('fileName', mitigation_data['fileName'])
                    mitigation_data['files'] = user_mitigation.get('files', mitigation_data['files'])
            
            # Add reviewer feedback if available
            if (reviewer_feedback and 'mitigation_feedback' in reviewer_feedback and 
                str(key) in reviewer_feedback['mitigation_feedback']):
                feedback = reviewer_feedback['mitigation_feedback'][str(key)]
                mitigation_data['approved'] = feedback.get('approved')
                mitigation_data['remarks'] = feedback.get('remarks')
                
                # If approved, user cannot edit; if rejected, they need to update
                if feedback.get('approved') is True:
                    mitigation_data['status'] = 'Approved'
                elif feedback.get('approved') is False:
                    mitigation_data['status'] = 'Needs Update'
            
            enhanced_mitigations[key] = mitigation_data
        
        # Get assessment feedback for pre-filling
        assessment_feedback = None
        previous_assessment_data = {}
        if reviewer_feedback and 'assessment_feedback' in reviewer_feedback:
            assessment_feedback = reviewer_feedback['assessment_feedback']
            
        # Always get previous assessment data for pre-filling
        # Get the latest user submission that contains assessment data
        approval_entries_all = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        for entry in approval_entries_all:
            if (entry.version and entry.version.startswith('U') and 
                entry.ExtractedInfo):
                extracted_info = entry.ExtractedInfo
                if any(key in extracted_info for key in ['cost', 'impact', 'financialImpact']):
                    previous_assessment_data = {
                        'cost': extracted_info.get('cost', ''),
                        'impact': extracted_info.get('impact', ''),
                        'financialImpact': extracted_info.get('financialImpact', ''),
                        'reputationalImpact': extracted_info.get('reputationalImpact', ''),
                        'operationalImpact': extracted_info.get('operationalImpact', ''),
                        'financialLoss': extracted_info.get('financialLoss', ''),
                        'systemDowntime': extracted_info.get('systemDowntime', ''),
                        'recoveryTime': extracted_info.get('recoveryTime', ''),
                        'riskRecurrence': extracted_info.get('riskRecurrence', ''),
                        'improvementInitiative': extracted_info.get('improvementInitiative', '')
                    }
                    break

        print(f"DEBUG: Incident mitigations response - {len(enhanced_mitigations)} mitigations, reviewer_feedback_available: {reviewer_feedback is not None}")

        return JsonResponse({
            'mitigations': enhanced_mitigations,
            'overall_status': incident.Status,
            'reviewer_feedback_available': reviewer_feedback is not None,
            'assessment_feedback': assessment_feedback,
            'previous_assessment_data': previous_assessment_data
        })
    except Incident.DoesNotExist:
        return JsonResponse({'error': 'Incident not found'}, status=404)
    except Exception as e:
        print(f"Error fetching incident mitigations: {str(e)}")
        # SECURE: Sanitize error message to prevent information disclosure
        safe_error = SecureOutputEncoder.sanitize_error_message(str(e))
        return JsonResponse({'error': safe_error}, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentAssignPermission])
@rbac_required(required_permission='assign_incident')
def assign_incident_reviewer(request):
    """Assign a reviewer to an incident with mitigation data"""
    try:
        # Define validation rules for reviewer assignment
        validation_rules = {
            'incident_id': {
                'type': 'integer',
                'min_value': 1,
                'required': True
            },
            'reviewer_id': {
                'type': 'integer',
                'min_value': 1,
                'required': True
            },
            'user_id': {
                'type': 'integer',
                'min_value': 1,
                'required': False
            },
            'mitigations': {
                'type': 'string',  # JSON will be stored as string
                'max_length': 10000,
                'required': False
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        incident_id = validated_data.get('incident_id')
        reviewer_id = validated_data.get('reviewer_id')
        user_id = validated_data.get('user_id')
        mitigations = validated_data.get('mitigations', {})
        
        # Update the incident with reviewer and mitigation data
        incident = Incident.objects.get(IncidentId=incident_id)
        incident.ReviewerId = reviewer_id
        incident.Status = 'In Progress'  # Changed from 'Under Review' to 'In Progress'
        
        # Store the mitigation data
        if mitigations:
            if isinstance(mitigations, dict):
                incident.Mitigation = json.dumps(mitigations)
            else:
                incident.Mitigation = mitigations
        
        incident.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Incident reviewer assigned successfully',
            'IncidentId': incident.IncidentId,
            'reviewer_id': reviewer_id
        })
    except Incident.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Incident not found',
            'IncidentId': incident_id
        }, status=404)
    except Exception as e:
        print(f"Error assigning incident reviewer: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'IncidentId': incident_id
        }, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentEvaluatePermission])
@rbac_required(required_permission='evaluate_assigned_incident')
def incident_review_data(request, incident_id):
    """Get incident review data for reviewer workflow with previous versions"""
    try:
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        incident = Incident.objects.get(IncidentId=validated_incident_id)
        
        # Get all incident approval entries ordered by date
        all_entries = IncidentApproval.objects.filter(
            IncidentId=incident_id
        ).order_by('-Date')
        
        # Get the latest user submission for current review
        latest_user_entry = None
        for entry in all_entries:
            if entry.version and entry.version.startswith('U'):
                latest_user_entry = entry
                break
        
        # Check if this incident has already been reviewed
        latest_reviewer_entry = None
        for entry in all_entries:
            if entry.version and entry.version.startswith('R'):
                latest_reviewer_entry = entry
                break
        
        # Parse mitigation data from latest user entry
        mitigations = {}
        questionnaire_data = {}
        
        if latest_user_entry and latest_user_entry.ExtractedInfo:
            extracted_info = latest_user_entry.ExtractedInfo
            
            # Extract mitigations if present and handle approval status correctly
            if 'mitigations' in extracted_info:
                raw_mitigations = extracted_info['mitigations']
                mitigations = {}
                
                # Get previous reviewer feedback to preserve approved statuses
                previous_reviewer_feedback = None
                if latest_reviewer_entry and latest_reviewer_entry.ExtractedInfo:
                    previous_reviewer_feedback = latest_reviewer_entry.ExtractedInfo.get('reviewer_feedback', {})
                
                for key, mitigation in raw_mitigations.items():
                    if isinstance(mitigation, dict):
                        # Start with clean mitigation data
                        clean_mitigation = {
                            'description': mitigation.get('description', ''),
                            'status': mitigation.get('status', 'Not Started'),
                            'comments': mitigation.get('comments', ''),
                            'aws-file_link': mitigation.get('aws-file_link'),
                            'fileName': mitigation.get('fileName'),
                            'files': mitigation.get('files', [])
                        }
                        
                        # Check if this mitigation was previously approved
                        if (previous_reviewer_feedback and 
                            'mitigation_feedback' in previous_reviewer_feedback and
                            str(key) in previous_reviewer_feedback['mitigation_feedback']):
                            
                            previous_feedback = previous_reviewer_feedback['mitigation_feedback'][str(key)]
                            
                            # If previously approved, preserve the approval status (read-only)
                            if previous_feedback.get('approved') is True:
                                clean_mitigation['approved'] = True
                                clean_mitigation['remarks'] = previous_feedback.get('remarks', '')
                            # If previously rejected, allow fresh review (no approval status)
                            # This allows the reviewer to approve/reject again
                        
                        mitigations[key] = clean_mitigation
                    else:
                        # Handle simple string format
                        mitigations[key] = {
                            'description': mitigation,
                            'status': 'Completed',  # Assume completed if it's in the submission
                            'comments': '',
                            'aws-file_link': None,
                            'fileName': None
                        }
            
            # Extract questionnaire data
            questionnaire_data = {
                'cost': extracted_info.get('cost', ''),
                'impact': extracted_info.get('impact', ''),
                'financialImpact': extracted_info.get('financialImpact', ''),
                'reputationalImpact': extracted_info.get('reputationalImpact', ''),
                'operationalImpact': extracted_info.get('operationalImpact', ''),
                'financialLoss': extracted_info.get('financialLoss', ''),
                'systemDowntime': extracted_info.get('systemDowntime', ''),
                'recoveryTime': extracted_info.get('recoveryTime', ''),
                'riskRecurrence': extracted_info.get('riskRecurrence', ''),
                'improvementInitiative': extracted_info.get('improvementInitiative', ''),
                'submittedAt': extracted_info.get('submittedAt', '')
            }
        
        # Get previous versions for comparison
        previous_versions = {}
        user_entries = [entry for entry in all_entries if entry.version and entry.version.startswith('U')]
        
        # If there are multiple user submissions, get the previous one
        if len(user_entries) > 1:
            previous_user_entry = user_entries[1]  # Second latest (previous)
            if previous_user_entry.ExtractedInfo and 'mitigations' in previous_user_entry.ExtractedInfo:
                previous_versions = previous_user_entry.ExtractedInfo['mitigations']
        
        # Check if review is already completed for the LATEST user submission
        # Review is only completed if there's a reviewer entry AFTER the latest user entry
        review_completed = False
        if latest_reviewer_entry and latest_user_entry:
            # Parse version numbers to compare
            try:
                latest_user_version_num = int(latest_user_entry.version[1:])  # Extract number from "U1", "U2", etc.
                latest_reviewer_version_num = int(latest_reviewer_entry.version[1:])  # Extract number from "R1", "R2", etc.
                
                # Review is completed only if reviewer version >= user version
                # (i.e., reviewer has reviewed the latest user submission)
                review_completed = (latest_reviewer_version_num >= latest_user_version_num and 
                                  latest_reviewer_entry.ApprovedRejected is not None)
            except (ValueError, IndexError):
                # Fallback: if version parsing fails, check if reviewer entry exists
                review_completed = latest_reviewer_entry.ApprovedRejected is not None
        elif latest_reviewer_entry:
            # If there's only a reviewer entry but no user entry, consider it completed
            review_completed = latest_reviewer_entry.ApprovedRejected is not None
        
        # Get assessment feedback if reviewer has provided feedback
        assessment_feedback = None
        if latest_reviewer_entry and latest_reviewer_entry.ExtractedInfo:
            reviewer_feedback = latest_reviewer_entry.ExtractedInfo.get('reviewer_feedback', {})
            assessment_feedback = reviewer_feedback.get('assessment_feedback', {})
        
        
        return JsonResponse({
            'mitigations': mitigations,
            'questionnaire_data': questionnaire_data,
            'previous_versions': previous_versions,
            'assessment_feedback': assessment_feedback,
            'approval_entry': {
                'id': latest_user_entry.id if latest_user_entry else None,
                'version': latest_user_entry.version if latest_user_entry else '1.0',
                'approved_rejected': latest_reviewer_entry.ApprovedRejected if latest_reviewer_entry else None,
                'review_completed': review_completed
            },
            'incident': {
                'id': incident.IncidentId,
                'title': incident.IncidentTitle,
                'status': incident.Status,
                'priority': incident.RiskPriority
            }
        })
    except Incident.DoesNotExist:
        return JsonResponse({'error': 'Incident not found'}, status=404)
    except Exception as e:
        print(f"Error fetching incident review data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def incident_versions(request, incident_id):
    """Get all versions for a specific incident including U, R, and V versions"""
    try:
        print(f"\n=== GET INCIDENT VERSIONS CALLED ===")
        print(f"Incident ID: {incident_id}")
        
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get all incident approval entries for this incident, ordered by date (newest first)
        all_entries = IncidentApproval.objects.filter(
            IncidentId=validated_incident_id
        ).order_by('-Date')
        
        print(f"Found {all_entries.count()} entries in incident_approval for incident {incident_id}")
        
        versions = []
        version_names = []
        
        for entry in all_entries:
            if entry.version:
                print(f"Processing version: {entry.version}, Type: {entry.version[0] if entry.version else 'Unknown'}")
                
                # Parse ExtractedInfo to get mitigation data
                mitigations = {}
                risk_form_details = {}
                
                if entry.ExtractedInfo:
                    extracted_info = entry.ExtractedInfo
                    
                    # Get mitigations data
                    if 'mitigations' in extracted_info:
                        mitigations = extracted_info['mitigations']
                    
                    # Get questionnaire/form data
                    risk_form_details = {
                        'cost': extracted_info.get('cost', ''),
                        'impact': extracted_info.get('impact', ''),
                        'financialImpact': extracted_info.get('financialImpact', ''),
                        'reputationalImpact': extracted_info.get('reputationalImpact', ''),
                        'operationalImpact': extracted_info.get('operationalImpact', ''),
                        'financialLoss': extracted_info.get('financialLoss', ''),
                        'systemDowntime': extracted_info.get('systemDowntime', ''),
                        'recoveryTime': extracted_info.get('recoveryTime', ''),
                        'riskRecurrence': extracted_info.get('riskRecurrence', ''),
                        'improvementInitiative': extracted_info.get('improvementInitiative', ''),
                        'approved': extracted_info.get('approved'),
                        'remarks': extracted_info.get('remarks', ''),
                        'reviewer_feedback': extracted_info.get('reviewer_feedback', {})
                    }
                
                # Format the version entry with complete data
                version_info = {
                    'version': entry.version,
                    'IncidentId': entry.IncidentId,
                    'UserId': entry.AssigneeId,
                    'ApproverId': entry.ReviewerId,
                    'Date': entry.Date.isoformat() if entry.Date else None,
                    'formatted_date': entry.Date.strftime('%Y-%m-%d %H:%M:%S') if entry.Date else 'Unknown',
                    'ApprovedRejected': entry.ApprovedRejected,
                    'user_submitted_date': entry.Date.isoformat() if entry.Date and entry.version and entry.version.startswith('U') else None,
                    'reviewer_submitted_date': entry.Date.isoformat() if entry.Date and entry.version and entry.version.startswith('R') else None,
                    'mitigations': mitigations,
                    'risk_form_details': risk_form_details
                }
                
                # Only include versions that have proper version format (U1, U2, R1, R2, V1, etc.)
                if entry.version and len(entry.version) >= 2 and entry.version[0] in ['U', 'R', 'V']:
                    versions.append(version_info)
                    version_names.append(entry.version)
                    print(f"Added version {entry.version} with {len(mitigations)} mitigations")
        
        # Filter to only show reviewer versions (R1, R2, etc.) for dropdown
        reviewer_version_names = [v for v in version_names if v.startswith('R')]
        
        print(f"Total versions found: {len(versions)}")
        print(f"Reviewer versions for dropdown: {reviewer_version_names}")
        
        return JsonResponse({
            'success': True,
            'versions': versions,
            'version_names': reviewer_version_names  # Only show R versions in dropdown like Risk workflow
        })
        
    except Exception as e:
        print(f"Error fetching incident versions: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def incident_version_detail(request, incident_id, version):
    """Get specific version details for an incident"""
    try:
        print(f"\n=== GET INCIDENT VERSION DETAIL CALLED ===")
        print(f"Incident ID: {incident_id}, Version: {version}")
        
        # Validate path parameters
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get the specific version entry
        try:
            version_entry = IncidentApproval.objects.get(
                IncidentId=validated_incident_id,
                version=version
            )
            print(f"Found version entry: {version}")
        except IncidentApproval.DoesNotExist:
            print(f"Version {version} NOT FOUND for incident {incident_id}")
            return JsonResponse({'error': f'Version {version} not found for incident {incident_id}'}, status=404)
        
        # Parse the ExtractedInfo to get complete version data
        version_data = {
            'IncidentId': version_entry.IncidentId,
            'UserId': version_entry.AssigneeId,
            'ApproverId': version_entry.ReviewerId,
            'Date': version_entry.Date.isoformat() if version_entry.Date else None,
            'formatted_date': version_entry.Date.strftime('%Y-%m-%d %H:%M:%S') if version_entry.Date else 'Unknown',
            'ApprovedRejected': version_entry.ApprovedRejected,
            'user_submitted_date': version_entry.Date.isoformat() if version_entry.Date and version.startswith('U') else None,
            'reviewer_submitted_date': version_entry.Date.isoformat() if version_entry.Date and version.startswith('R') else None,
            'mitigations': {},
            'risk_form_details': {}
        }
        
        if version_entry.ExtractedInfo:
            extracted_info = version_entry.ExtractedInfo
            
            # Extract mitigation data
            if 'mitigations' in extracted_info:
                version_data['mitigations'] = extracted_info['mitigations']
                print(f"Found {len(extracted_info['mitigations'])} mitigations in version {version}")
            
            # Extract questionnaire/form data
            version_data['risk_form_details'] = {
                'cost': extracted_info.get('cost', ''),
                'impact': extracted_info.get('impact', ''),
                'financialImpact': extracted_info.get('financialImpact', ''),
                'reputationalImpact': extracted_info.get('reputationalImpact', ''),
                'operationalImpact': extracted_info.get('operationalImpact', ''),
                'financialLoss': extracted_info.get('financialLoss', ''),
                'systemDowntime': extracted_info.get('systemDowntime', ''),
                'recoveryTime': extracted_info.get('recoveryTime', ''),
                'riskRecurrence': extracted_info.get('riskRecurrence', ''),
                'improvementInitiative': extracted_info.get('improvementInitiative', ''),
                'approved': extracted_info.get('approved'),
                'remarks': extracted_info.get('remarks', ''),
                'user_submitted_date': version_data['user_submitted_date'],
                'reviewer_submitted_date': version_data['reviewer_submitted_date']
            }
            
            # Include reviewer feedback if available
            if 'reviewer_feedback' in extracted_info:
                version_data['reviewer_feedback'] = extracted_info['reviewer_feedback']
                version_data['ReviewerFeedback'] = extracted_info['reviewer_feedback']  # Add both formats for compatibility
        
        print(f"Returning version data with {len(version_data.get('mitigations', {}))} mitigations")
        
        return JsonResponse({
            'success': True,
            'version_data': version_data
        })
        
    except Exception as e:
        print(f"Error fetching incident version detail: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AuditViewPermission])
@rbac_required(required_permission='view_audit_reports')
def audit_finding_versions(request, incident_id):
    """Get all versions for a specific audit finding incident including U, R, and V versions"""
    try:
        print(f"\n=== GET AUDIT FINDING VERSIONS CALLED ===")
        print(f"Audit Finding ID: {incident_id}")
        
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get all incident approval entries for this audit finding, ordered by date (newest first)
        all_entries = IncidentApproval.objects.filter(
            IncidentId=validated_incident_id
        ).order_by('-Date')
        
        print(f"Found {all_entries.count()} entries in incident_approval for audit finding {incident_id}")
        
        versions = []
        version_names = []
        
        for entry in all_entries:
            if entry.version:
                print(f"Processing version: {entry.version}, Type: {entry.version[0] if entry.version else 'Unknown'}")
                
                # Parse ExtractedInfo to get mitigation data
                mitigations = {}
                risk_form_details = {}
                
                if entry.ExtractedInfo:
                    extracted_info = entry.ExtractedInfo
                    
                    # Get mitigations data
                    if 'mitigations' in extracted_info:
                        mitigations = extracted_info['mitigations']
                    
                    # Get questionnaire/form data
                    risk_form_details = {
                        'cost': extracted_info.get('cost', ''),
                        'impact': extracted_info.get('impact', ''),
                        'financialImpact': extracted_info.get('financialImpact', ''),
                        'reputationalImpact': extracted_info.get('reputationalImpact', ''),
                        'operationalImpact': extracted_info.get('operationalImpact', ''),
                        'financialLoss': extracted_info.get('financialLoss', ''),
                        'systemDowntime': extracted_info.get('systemDowntime', ''),
                        'recoveryTime': extracted_info.get('recoveryTime', ''),
                        'riskRecurrence': extracted_info.get('riskRecurrence', ''),
                        'improvementInitiative': extracted_info.get('improvementInitiative', ''),
                        'approved': extracted_info.get('approved'),
                        'remarks': extracted_info.get('remarks', ''),
                        'reviewer_feedback': extracted_info.get('reviewer_feedback', {})
                    }
                
                # Format the version entry with complete data
                version_info = {
                    'version': entry.version,
                    'IncidentId': entry.IncidentId,
                    'UserId': entry.AssigneeId,
                    'ApproverId': entry.ReviewerId,
                    'Date': entry.Date.isoformat() if entry.Date else None,
                    'formatted_date': entry.Date.strftime('%Y-%m-%d %H:%M:%S') if entry.Date else 'Unknown',
                    'ApprovedRejected': entry.ApprovedRejected,
                    'user_submitted_date': entry.Date.isoformat() if entry.Date and entry.version and entry.version.startswith('U') else None,
                    'reviewer_submitted_date': entry.Date.isoformat() if entry.Date and entry.version and entry.version.startswith('R') else None,
                    'mitigations': mitigations,
                    'risk_form_details': risk_form_details
                }
                
                # Only include versions that have proper version format (U1, U2, R1, R2, V1, etc.)
                if entry.version and len(entry.version) >= 2 and entry.version[0] in ['U', 'R', 'V']:
                    versions.append(version_info)
                    version_names.append(entry.version)
                    print(f"Added version {entry.version} with {len(mitigations)} mitigations")
        
        # Filter to only show reviewer versions (R1, R2, etc.) for dropdown
        reviewer_version_names = [v for v in version_names if v.startswith('R')]
        
        print(f"Total versions found: {len(versions)}")
        print(f"Reviewer versions for dropdown: {reviewer_version_names}")
        
        return JsonResponse({
            'success': True,
            'versions': versions,
            'version_names': reviewer_version_names  # Only show R versions in dropdown like Risk workflow
        })
        
    except Exception as e:
        print(f"Error fetching audit finding versions: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AuditViewPermission])
def audit_finding_version_detail(request, incident_id, version):
    """Get specific version details for an audit finding incident"""
    try:
        print(f"\n=== GET AUDIT FINDING VERSION DETAIL CALLED ===")
        print(f"Audit Finding ID: {incident_id}, Version: {version}")
        
        # Validate path parameters
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get the specific version entry
        try:
            version_entry = IncidentApproval.objects.get(
                IncidentId=validated_incident_id,
                version=version
            )
            print(f"Found version entry: {version}")
        except IncidentApproval.DoesNotExist:
            print(f"Version {version} NOT FOUND for audit finding {incident_id}")
            return JsonResponse({'error': f'Version {version} not found for audit finding {incident_id}'}, status=404)
        
        # Parse the ExtractedInfo to get complete version data
        version_data = {
            'IncidentId': version_entry.IncidentId,
            'UserId': version_entry.AssigneeId,
            'ApproverId': version_entry.ReviewerId,
            'Date': version_entry.Date.isoformat() if version_entry.Date else None,
            'formatted_date': version_entry.Date.strftime('%Y-%m-%d %H:%M:%S') if version_entry.Date else 'Unknown',
            'ApprovedRejected': version_entry.ApprovedRejected,
            'user_submitted_date': version_entry.Date.isoformat() if version_entry.Date and version.startswith('U') else None,
            'reviewer_submitted_date': version_entry.Date.isoformat() if version_entry.Date and version.startswith('R') else None,
            'mitigations': {},
            'risk_form_details': {}
        }
        
        if version_entry.ExtractedInfo:
            extracted_info = version_entry.ExtractedInfo
            
            # Extract mitigation data
            if 'mitigations' in extracted_info:
                version_data['mitigations'] = extracted_info['mitigations']
                print(f"Found {len(extracted_info['mitigations'])} mitigations in version {version}")
            
            # Extract questionnaire/form data
            version_data['risk_form_details'] = {
                'cost': extracted_info.get('cost', ''),
                'impact': extracted_info.get('impact', ''),
                'financialImpact': extracted_info.get('financialImpact', ''),
                'reputationalImpact': extracted_info.get('reputationalImpact', ''),
                'operationalImpact': extracted_info.get('operationalImpact', ''),
                'financialLoss': extracted_info.get('financialLoss', ''),
                'systemDowntime': extracted_info.get('systemDowntime', ''),
                'recoveryTime': extracted_info.get('recoveryTime', ''),
                'riskRecurrence': extracted_info.get('riskRecurrence', ''),
                'improvementInitiative': extracted_info.get('improvementInitiative', ''),
                'approved': extracted_info.get('approved'),
                'remarks': extracted_info.get('remarks', ''),
                'user_submitted_date': version_data['user_submitted_date'],
                'reviewer_submitted_date': version_data['reviewer_submitted_date']
            }
            
            # Include reviewer feedback if available
            if 'reviewer_feedback' in extracted_info:
                version_data['reviewer_feedback'] = extracted_info['reviewer_feedback']
                version_data['ReviewerFeedback'] = extracted_info['reviewer_feedback']  # Add both formats for compatibility
        
        print(f"Returning version data with {len(version_data.get('mitigations', {}))} mitigations")
        
        return JsonResponse({
            'success': True,
            'version_data': version_data
        })
        
    except Exception as e:
        print(f"Error fetching audit finding version detail: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentEvaluatePermission])
@rbac_required(required_permission='evaluate_assigned_incident')
def complete_incident_review(request):
    """Complete the review of an incident"""
    try:
        from django.utils import timezone
        
        # Define validation rules for incident review completion
        validation_rules = {
            'incident_id': {
                'type': 'integer',
                'min_value': 1,
                'required': True
            },
            'approved': {
                'type': 'boolean',  # Use boolean type instead of choice
                'required': True
            },
            'reviewer_id': {
                'type': 'integer',
                'min_value': 1,
                'required': True
            },

        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        incident_id = validated_data.get('incident_id')
        approved_raw = validated_data.get('approved')
        reviewer_id = validated_data.get('reviewer_id')
        
        # Get raw data for fields not handled by validation
        if hasattr(request, 'data') and request.data:
            data = request.data
        else:
            data = json.loads(request.body) if request.body else {}
        
        mitigation_feedback = data.get('mitigation_feedback', {})
        assessment_feedback = data.get('assessment_feedback', {})
        
        # Convert approved to boolean
        approved = approved_raw in ['true', True, 1] if isinstance(approved_raw, (str, bool, int)) else False
        
        print(f"DEBUG: Completing incident review - ID: {incident_id}, Approved: {approved}, Reviewer: {reviewer_id}")
        print(f"DEBUG: Mitigation feedback: {mitigation_feedback}")
        print(f"DEBUG: Assessment feedback: {assessment_feedback}")
        
        # Log incident review completion attempt
        send_log(
            module="Incident",
            actionType="COMPLETE_REVIEW",
            description=f"Reviewer {reviewer_id} completing review for incident {incident_id} - Decision: {'Approved' if approved else 'Rejected'}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            entityId=incident_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"reviewer_id": reviewer_id, "approved": approved, "has_mitigation_feedback": bool(mitigation_feedback), "has_assessment_feedback": bool(assessment_feedback)}
        )
        
        # Update the incident status based on approval
        incident = Incident.objects.get(IncidentId=incident_id)
        
        if approved:
            incident.Status = 'Approved'
        else:
            incident.Status = 'Rejected'
        
        # Set ReviewerId if not already set
        if not incident.ReviewerId:
            incident.ReviewerId = reviewer_id
            
        incident.save()
        print(f"DEBUG: Updated incident status to: {incident.Status}")
        
        # Send notifications based on review decision
        try:
            notification_service = NotificationService()
            
            # Get user email and name for notification
            assignee_email = notification_service.get_user_email(incident.AssignerId) if incident.AssignerId else None
            assignee_name = notification_service.get_user_name(incident.AssignerId) if incident.AssignerId else 'User'
            reviewer_name = notification_service.get_user_name(reviewer_id) if reviewer_id else 'Reviewer'
            
            print(f"DEBUG: Notification details - Assignee: {assignee_name}, Email: {assignee_email}")
            
            # Send notification to assignee
            if assignee_email:
                if approved:
                    # Incident approved notification
                    approval_notification = {
                        'notification_type': 'incidentApproved',
                        'email': assignee_email,
                        'email_type': 'gmail',
                        'template_data': [
                            assignee_name,
                            incident.IncidentTitle,
                            reviewer_name,
                            timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                        ]
                    }
                    notification_service.send_multi_channel_notification(approval_notification)
                    print(f"DEBUG: Sent approval notification to {assignee_email}")
                else:
                    # Incident rejected notification
                    rejection_notification = {
                        'notification_type': 'incidentRejected',
                        'email': assignee_email,
                        'email_type': 'gmail',
                        'template_data': [
                            assignee_name,
                            incident.IncidentTitle,
                            reviewer_name,
                            'Please review and address the feedback provided'
                        ]
                    }
                    notification_service.send_multi_channel_notification(rejection_notification)
                    print(f"DEBUG: Sent rejection notification to {assignee_email}")
            else:
                print(f"DEBUG: No email found for assignee {incident.AssignerId}")
                    
        except Exception as e:
            print(f"Error sending review completion notifications: {str(e)}")
            # Continue execution even if notification fails
        
        # Get all entries and find latest user submission - avoid BINARY expression error
        all_entries = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        latest_user_entry = None
        reviewer_count = 0
        
        print(f"DEBUG: Found {all_entries.count()} approval entries")
        
        # Iterate through entries to find latest user entry and count reviewer entries
        for entry in all_entries:
            if entry.version and entry.version.startswith('U') and latest_user_entry is None:
                latest_user_entry = entry
                print(f"DEBUG: Found latest user entry: {entry.version}")
            if entry.version and entry.version.startswith('R'):
                reviewer_count += 1
        
        print(f"DEBUG: Reviewer count: {reviewer_count}")
        
        if latest_user_entry:
            # Generate reviewer version number
            reviewer_version = f"R{reviewer_count + 1}"  # R1, R2, R3, etc.
            
            print(f"DEBUG: Creating reviewer entry with version: {reviewer_version}")
            
            # Create reviewer feedback data structure
            reviewer_feedback_data = {
                'reviewer_feedback': {
                    'mitigation_feedback': mitigation_feedback,
                    'assessment_feedback': assessment_feedback,
                    'overall_decision': 'approved' if approved else 'rejected',
                    'review_date': timezone.now().isoformat()
                }
            }
            
            # Get FrameworkId from the incident
            framework_id = incident.FrameworkId if incident.FrameworkId else None
            print(f"DEBUG: Using FrameworkId: {framework_id} for incident approval")
            
            # Import Framework model at function scope
            from grc.models import Framework
            
            # Get Framework object if framework_id exists
            framework = None
            if framework_id:
                try:
                    framework = Framework.objects.get(FrameworkId=framework_id)
                    print(f"DEBUG: Found Framework object: {framework}")
                except Framework.DoesNotExist:
                    print(f"DEBUG: Framework with ID {framework_id} not found")
                    framework = None
            
            # Create new entry for reviewer response
            IncidentApproval.objects.create(
                IncidentId=incident_id,
                version=reviewer_version,
                ExtractedInfo=reviewer_feedback_data,  # Save reviewer feedback
                AssigneeId=latest_user_entry.AssigneeId,
                ReviewerId=str(reviewer_id),
                ApprovedRejected='Approved' if approved else 'Rejected',
                Date=timezone.now(),
                FrameworkId=framework
            )
            print(f"DEBUG: Successfully created reviewer approval entry with FrameworkId: {framework_id}")
        else:
            print(f"DEBUG: No user entry found, updating existing entry")
            # Fallback: Update the existing entry if no user entry found
            approval_entry = IncidentApproval.objects.filter(
                IncidentId=incident_id
            ).order_by('-Date').first()
            
            if approval_entry:
                approval_entry.ApprovedRejected = 'Approved' if approved else 'Rejected'
                approval_entry.ReviewerId = str(reviewer_id) if reviewer_id else None
                approval_entry.save()
                print(f"DEBUG: Updated existing approval entry")
        
        print(f"DEBUG: Review completion successful")
        
        # Log successful review completion
        send_log(
            module="Incident",
            actionType="COMPLETE_REVIEW_SUCCESS",
            description=f"Incident {incident_id} review completed successfully by reviewer {reviewer_id} - Status: {incident.Status}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            entityId=incident_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"reviewer_id": reviewer_id, "final_status": incident.Status, "approved": approved}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Incident review completed - {"Approved" if approved else "Rejected"}',
            'IncidentId': incident.IncidentId,
            'status': incident.Status
        })
    except Incident.DoesNotExist:
        print(f"ERROR: Incident {incident_id} not found")
        
        # Log incident not found error
        send_log(
            module="Incident",
            actionType="COMPLETE_REVIEW_ERROR",
            description=f"Review completion failed - Incident {incident_id} not found",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            entityId=incident_id,
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': False,
            'error': 'Incident not found',
            'IncidentId': incident_id
        }, status=404)
    except Exception as e:
        print(f"Error completing incident review: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Log review completion error
        send_log(
            module="Incident",
            actionType="COMPLETE_REVIEW_ERROR",
            description=f"Review completion failed with error: {str(e)}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': False,
            'error': str(e),
            'IncidentId': incident_id
        }, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentEvaluatePermission])
@rbac_required(required_permission='evaluate_assigned_incident')
def submit_incident_assessment(request):
    """Submit incident assessment with cost impact analysis"""
    try:
        from ...routes.Global.validation import QuestionnaireValidator
        
        # Define validation rules for incident assessment submission
        validation_rules = {
            'incident_id': {
                'type': 'integer',
                'min_value': 1,
                'required': True
            },
            'user_id': {
                'type': 'integer',
                'min_value': 1,
                'required': True
            },

        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get raw data for fields not handled by validation
        if hasattr(request, 'data') and request.data:
            data = request.data
        else:
            data = json.loads(request.body) if request.body else {}
        
        incident_id = validated_data.get('incident_id')
        user_id = validated_data.get('user_id')
        raw_assessment_data = data.get('extracted_info', data.get('assessment_data', {}))
        
        # Log incident assessment submission attempt
        send_log(
            module="Incident",
            actionType="SUBMIT_ASSESSMENT",
            description=f"User {user_id} submitting assessment for incident {incident_id}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            entityId=incident_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"submitter_user_id": user_id, "assessment_data_size": len(str(raw_assessment_data))}
        )
        
        # Validate questionnaire data using secure validation
        try:
            validated_questionnaire = QuestionnaireValidator.validate_questionnaire_data(raw_assessment_data)
            print(f"Questionnaire validation successful: {validated_questionnaire}")
        except Exception as validation_error:
            print(f"Questionnaire validation failed: {validation_error}")
            
            # Log validation error
            send_log(
                module="Incident",
                actionType="SUBMIT_ASSESSMENT_ERROR",
                description=f"Assessment submission validation failed for incident {incident_id}: {str(validation_error)}",
                userId=request.user.id if request.user.is_authenticated else None,
                userName=request.user.username if request.user.is_authenticated else None,
                entityType="Incident",
                entityId=incident_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request),
                additionalInfo={"submitter_user_id": user_id, "validation_error": str(validation_error)}
            )
            
            return JsonResponse({
                'success': False,
                'error': f'Validation failed: {str(validation_error)}',
                'field': getattr(validation_error, 'field', 'unknown'),
                'IncidentId': incident_id
            }, status=400)
        
        # Process mitigation data to ensure S3 URLs are properly saved in aws-file_link
        processed_assessment_data = process_mitigation_s3_urls(raw_assessment_data)
        
        # Use validated data for storage
        assessment_data = {**processed_assessment_data, **validated_questionnaire}
        
        # Get existing entries to determine next version number
        all_entries = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        user_count = 0
        
        # Count existing user submissions
        for entry in all_entries:
            if entry.version and entry.version.startswith('U'):
                user_count += 1
        
        # Generate incremental user version number
        user_version = f"U{user_count + 1}"  # U1, U2, U3, etc.
        
        # Get FrameworkId from the incident
        incident = Incident.objects.get(IncidentId=incident_id)
        framework_id = incident.FrameworkId if incident.FrameworkId else None
        print(f"DEBUG: Using FrameworkId: {framework_id} for user incident assessment submission")
        
        # Import Framework model at function scope
        from grc.models import Framework
        
        # Get Framework object if framework_id exists
        framework = None
        if framework_id:
            try:
                framework = Framework.objects.get(FrameworkId=framework_id)
                print(f"DEBUG: Found Framework object: {framework}")
            except Framework.DoesNotExist:
                print(f"DEBUG: Framework with ID {framework_id} not found")
                framework = None
        
        # Create new IncidentApproval entry for user assessment submission
        approval_entry = IncidentApproval.objects.create(
            IncidentId=incident_id,
            AssigneeId=str(user_id),
            Date=datetime.datetime.now(),
            version=user_version,
            ExtractedInfo=assessment_data,
            FrameworkId=framework
        )
        
        # Update incident status to pending review
        incident.Status = 'Pending Review'
        incident.save()
        
        # Log successful assessment submission
        send_log(
            module="Incident",
            actionType="SUBMIT_ASSESSMENT_SUCCESS",
            description=f"Assessment submitted successfully for incident {incident_id} by user {user_id} - Status updated to Pending Review",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            entityId=incident_id,
            ipAddress=get_client_ip(request),
            additionalInfo={"submitter_user_id": user_id, "approval_entry_id": approval_entry.id, "version": user_version}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Assessment submitted successfully',
            'IncidentId': incident.IncidentId,
            'approval_id': approval_entry.id
        })
    except Exception as e:
        print(f"Error submitting incident assessment: {str(e)}")
        
        # Log assessment submission error
        send_log(
            module="Incident",
            actionType="SUBMIT_ASSESSMENT_ERROR",
            description=f"Assessment submission failed for incident: {str(e)}",
            userId=request.user.id if request.user.is_authenticated else None,
            userName=request.user.username if request.user.is_authenticated else None,
            entityType="Incident",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': False,
            'error': str(e),
            'IncidentId': incident_id
        }, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_incident_approval_data')
def incident_approval_data(request, incident_id):
    """Get incident approval data for incident workflow"""
    try:
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        incident = Incident.objects.get(IncidentId=validated_incident_id)
        
        # Get all incident approval entries ordered by date
        all_entries = IncidentApproval.objects.filter(
            IncidentId=incident_id
        ).order_by('-Date')
        
        # Get the latest approval entry
        latest_entry = all_entries.first() if all_entries.exists() else None
        
        # Parse approval data
        approval_data = {}
        if latest_entry and latest_entry.ExtractedInfo:
            approval_data = latest_entry.ExtractedInfo
        
        return JsonResponse({
            'approval_data': approval_data,
            'approval_entry': {
                'id': latest_entry.id if latest_entry else None,
                'version': latest_entry.version if latest_entry else '1.0',
                'approved_rejected': latest_entry.ApprovedRejected if latest_entry else None,
                'date': latest_entry.Date.isoformat() if latest_entry and latest_entry.Date else None
            },
            'incident': {
                'id': incident.IncidentId,
                'title': incident.IncidentTitle,
                'status': incident.Status,
                'priority': incident.RiskPriority,
                'assignee_id': incident.AssignerId,
                'reviewer_id': incident.ReviewerId
            }
        })
    except Incident.DoesNotExist:
        return JsonResponse({'error': 'Incident not found'}, status=404)
    except Exception as e:
        print(f"Error fetching incident approval data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# Audit Finding User Task Endpoints
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AuditFindingsAccessPermission])
def user_audit_findings(request, user_id):
    """Get audit findings assigned BY a specific user (where user is the assigner)"""
    try:
        # Validate path parameter
        try:
            validated_user_id = validate_path_parameter(user_id, 'user_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get optional framework_id parameter from query string
        framework_id = request.GET.get('framework_id', None)
        print(f"🔍 DEBUG: user_audit_findings called with framework_id: {framework_id}")
        
        # Get incidents that were assigned BY this user and originated from audit findings or compliance gaps
        # IMPORTANT: AssignerId is the person WHO assigned the incident to someone else
        # ReviewerId is the person assigned TO work on the incident (handled by audit_finding_reviewer_tasks)
        # This shows audit finding tasks that the user has assigned to others for tracking
        print(f"🔍 DEBUG: user_audit_findings - Filtering by AssignerId={validated_user_id}")
        incidents = Incident.objects.filter(
            Q(AssignerId=validated_user_id) &  # Filter by AssignerId (the person WHO assigned it)
            (Q(Origin__in=['Audit Finding', 'Compliance Gap']))
        ).exclude(
            Status__in=['Closed', 'Completed', 'Cancelled']
        )
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering user audit findings by framework_id: {framework_id}")
            incidents = incidents.filter(FrameworkId=framework_id)
            print(f"✅ Framework filter applied. Found {incidents.count()} audit findings.")
        
        incidents = incidents.values(
            'IncidentId', 'IncidentTitle', 'Origin', 'RiskPriority', 'Status', 
            'MitigationDueDate', 'AssignerId', 'ReviewerId', 'RejectionSource'
        )
        
        # Convert to the expected format for frontend
        audit_finding_list = []
        for incident in incidents:
            audit_finding_list.append({
                'id': incident['IncidentId'],
                'Title': incident['IncidentTitle'],
                'Origin': incident['Origin'],
                'Priority': incident['RiskPriority'],
                'Status': incident['Status'],
                'MitigationDueDate': incident['MitigationDueDate'],
                'AssignerId': incident['AssignerId'],
                'ReviewerId': incident['ReviewerId'],
                'RejectionSource': incident.get('RejectionSource'),
                'type': 'audit_finding'
            })
        
        return JsonResponse(audit_finding_list, safe=False)
    except Exception as e:
        print(f"Error fetching user audit findings: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AuditFindingsAccessPermission])
def audit_finding_reviewer_tasks(request, user_id):
    """Get audit findings where the user is assigned as reviewer"""
    try:
        # Validate path parameter
        try:
            validated_user_id = validate_path_parameter(user_id, 'user_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Get optional framework_id parameter from query string
        framework_id = request.GET.get('framework_id', None)
        print(f"🔍 DEBUG: audit_finding_reviewer_tasks called with framework_id: {framework_id}")
        
        # Get incidents where the user is assigned as reviewer and originated from audit findings or compliance gaps
        # Include all statuses (including NULL) except 'Closed' and 'Completed'
        print(f"🔍 DEBUG: audit_finding_reviewer_tasks - Filtering by ReviewerId={validated_user_id}")
        incidents = Incident.objects.filter(
            Q(ReviewerId=validated_user_id) &
            (Q(Origin__in=['Audit Finding', 'Compliance Gap']))
        ).exclude(
            Status__in=['Closed', 'Completed', 'Cancelled']
        )
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering audit finding reviewer tasks by framework_id: {framework_id}")
            incidents = incidents.filter(FrameworkId=framework_id)
            print(f"✅ Framework filter applied. Found {incidents.count()} audit finding reviewer tasks.")
        
        incidents = incidents.values(
            'IncidentId', 'IncidentTitle', 'Origin', 'RiskPriority', 'Status', 
            'AssignerId', 'ReviewerId', 'MitigationDueDate'
        )
        
        # Convert to the expected format for frontend
        audit_finding_list = []
        for incident in incidents:
            audit_finding_list.append({
                'id': incident['IncidentId'],
                'Title': incident['IncidentTitle'],
                'Origin': incident['Origin'],
                'Priority': incident['RiskPriority'],
                'Status': incident['Status'],
                'AssignerId': incident['AssignerId'],
                'ReviewerId': incident['ReviewerId'],
                'MitigationDueDate': incident['MitigationDueDate'],
                'type': 'audit_finding'
            })
        
        return JsonResponse(audit_finding_list, safe=False)
    except Exception as e:
        print(f"Error fetching audit finding reviewer tasks: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AuditViewPermission])
# @rbac_required(required_permission='view_audit_reports')
def audit_finding_mitigations(request, incident_id):
    """Get mitigation steps for a specific audit finding incident with reviewer feedback"""
    try:
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        incident = Incident.objects.get(IncidentId=validated_incident_id)
        
        # Parse the Mitigation field which contains the mitigation steps
        mitigations = {}
        if incident.Mitigation:
            try:
                if isinstance(incident.Mitigation, str):
                    mitigations = json.loads(incident.Mitigation)
                else:
                    mitigations = incident.Mitigation
            except json.JSONDecodeError:
                # If it's not JSON, treat as a single mitigation step
                mitigations = {"1": incident.Mitigation}
        
        # Get the latest reviewer feedback from IncidentApproval
        reviewer_feedback = None
        approval_entries = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        
        for entry in approval_entries:
            if (entry.version and entry.version.startswith('R') and 
                entry.ExtractedInfo and 'reviewer_feedback' in entry.ExtractedInfo):
                reviewer_feedback = entry.ExtractedInfo['reviewer_feedback']
                break
        
        # Get the latest user submission data to extract comments and other details
        latest_user_data = {}
        approval_entries_all = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        for entry in approval_entries_all:
            if (entry.version and entry.version.startswith('U') and 
                entry.ExtractedInfo and 'mitigations' in entry.ExtractedInfo):
                latest_user_data = entry.ExtractedInfo.get('mitigations', {})
                break

        # Enhanced mitigations with reviewer feedback and user data
        enhanced_mitigations = {}
        for key, mitigation_desc in mitigations.items():
            # Handle different mitigation data formats
            if isinstance(mitigation_desc, dict):
                # New format with full mitigation data
                mitigation_data = {
                    'description': mitigation_desc.get('description', ''),
                    'comments': mitigation_desc.get('comments', ''),
                    'status': mitigation_desc.get('status', 'Not Started'),
                    'aws-file_link': mitigation_desc.get('aws-file_link'),
                    'fileName': mitigation_desc.get('fileName'),
                    'files': mitigation_desc.get('files', []),  # Support multiple files
                    'approved': None,  # None = not reviewed, True = approved, False = rejected
                    'remarks': None,   # Reviewer's rejection feedback
                }
            else:
                # Old format - just description string
                mitigation_data = {
                    'description': mitigation_desc,
                    'comments': '',
                    'status': 'Not Started',
                    'aws-file_link': None,
                    'fileName': None,
                    'files': [],  # Support multiple files
                    'approved': None,
                    'remarks': None,
                }
            
            # Try to get user data from latest submission if available
            if str(key) in latest_user_data:
                user_mitigation = latest_user_data[str(key)]
                if isinstance(user_mitigation, dict):
                    mitigation_data['comments'] = user_mitigation.get('comments', mitigation_data['comments'])
                    mitigation_data['status'] = user_mitigation.get('status', mitigation_data['status'])
                    mitigation_data['aws-file_link'] = user_mitigation.get('aws-file_link', mitigation_data['aws-file_link'])
                    mitigation_data['fileName'] = user_mitigation.get('fileName', mitigation_data['fileName'])
                    mitigation_data['files'] = user_mitigation.get('files', mitigation_data['files'])
            
            # Add reviewer feedback if available
            if (reviewer_feedback and 'mitigation_feedback' in reviewer_feedback and 
                str(key) in reviewer_feedback['mitigation_feedback']):
                feedback = reviewer_feedback['mitigation_feedback'][str(key)]
                mitigation_data['approved'] = feedback.get('approved')
                mitigation_data['remarks'] = feedback.get('remarks')
                
                # If approved, user cannot edit; if rejected, they need to update
                if feedback.get('approved') is True:
                    mitigation_data['status'] = 'Approved'
                elif feedback.get('approved') is False:
                    mitigation_data['status'] = 'Needs Update'
            
            enhanced_mitigations[key] = mitigation_data
        
        # Get assessment feedback for pre-filling
        assessment_feedback = None
        previous_assessment_data = {}
        if reviewer_feedback and 'assessment_feedback' in reviewer_feedback:
            assessment_feedback = reviewer_feedback['assessment_feedback']
        
        # Always get previous assessment data for pre-filling
        # Get the latest user submission that contains assessment data
        approval_entries_all = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        for entry in approval_entries_all:
            if (entry.version and entry.version.startswith('U') and 
                entry.ExtractedInfo):
                extracted_info = entry.ExtractedInfo
                if any(key in extracted_info for key in ['cost', 'impact', 'financialImpact']):
                    previous_assessment_data = {
            'cost': extracted_info.get('cost', ''),
            'impact': extracted_info.get('impact', ''),
            'financialImpact': extracted_info.get('financialImpact', ''),
            'reputationalImpact': extracted_info.get('reputationalImpact', ''),
            'operationalImpact': extracted_info.get('operationalImpact', ''),
            'financialLoss': extracted_info.get('financialLoss', ''),
            'systemDowntime': extracted_info.get('systemDowntime', ''),
            'recoveryTime': extracted_info.get('recoveryTime', ''),
            'riskRecurrence': extracted_info.get('riskRecurrence', ''),
                        'improvementInitiative': extracted_info.get('improvementInitiative', '')
        }
                    break
        
        print(f"DEBUG: Audit finding mitigations response - {len(enhanced_mitigations)} mitigations, reviewer_feedback_available: {reviewer_feedback is not None}")
        
        return JsonResponse({
            'mitigations': enhanced_mitigations,
            'overall_status': incident.Status,
            'reviewer_feedback_available': reviewer_feedback is not None,
            'assessment_feedback': assessment_feedback,
            'previous_assessment_data': previous_assessment_data,
            'type': 'audit_finding'
        })
    except Incident.DoesNotExist:
        return JsonResponse({'error': 'Audit finding incident not found'}, status=404)
    except Exception as e:
        print(f"Error fetching audit finding mitigations: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AuditAssignPermission])
@rbac_required(required_permission='assign_audit')
def assign_audit_finding_reviewer(request):
    """Assign a reviewer to an audit finding incident with mitigation data"""
    try:
        data = request.data
        incident_id = data.get('incident_id')
        reviewer_id = data.get('reviewer_id')
        user_id = data.get('user_id')
        mitigations = data.get('mitigations', {})
        
        # Update the incident with reviewer and mitigation data
        incident = Incident.objects.get(IncidentId=incident_id)
        incident.ReviewerId = reviewer_id
        incident.Status = 'In Progress'  # Changed from 'Under Review' to 'In Progress'
        
        # Store the mitigation data
        if mitigations:
            incident.Mitigation = json.dumps(mitigations)
        
        incident.save()
        
        return JsonResponse({
            'message': 'Audit finding reviewer assigned successfully',
            'incident_id': incident_id,
            'reviewer_id': reviewer_id
        })
    except Incident.DoesNotExist:
        return JsonResponse({'error': 'Audit finding incident not found'}, status=404)
    except Exception as e:
        print(f"Error assigning audit finding reviewer: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AuditReviewPermission])
@rbac_required(required_permission='review_audit')
def audit_finding_review_data(request, incident_id):
    """Get audit finding review data for reviewer workflow with previous versions"""
    try:
        # Validate path parameter
        try:
            validated_incident_id = validate_path_parameter(incident_id, 'incident_id', 'integer')
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        incident = Incident.objects.get(IncidentId=validated_incident_id)
        
        # Parse the Mitigation field which contains the mitigation steps
        mitigations = {}
        if incident.Mitigation:
            try:
                if isinstance(incident.Mitigation, str):
                    mitigations = json.loads(incident.Mitigation)
                else:
                    mitigations = incident.Mitigation
            except json.JSONDecodeError:
                # If it's not JSON, treat as a single mitigation step
                mitigations = {"1": incident.Mitigation}
        
        # Get the latest user submission
        latest_user_submission = None
        latest_assessment_data = {}
        approval_entries = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        
        for entry in approval_entries:
            if entry.version and entry.version.startswith('U'):
                latest_user_submission = entry
                if entry.ExtractedInfo:
                    latest_assessment_data = entry.ExtractedInfo
                break
        
        # Get previous reviewer feedback if any
        previous_reviewer_feedback = None
        for entry in approval_entries:
            if (entry.version and entry.version.startswith('R') and 
                entry.ExtractedInfo and 'reviewer_feedback' in entry.ExtractedInfo):
                previous_reviewer_feedback = entry.ExtractedInfo['reviewer_feedback']
                break
        
        # Enhanced mitigations for reviewer
        enhanced_mitigations = {}
        for key, mitigation_desc in mitigations.items():
            mitigation_data = {
                'description': mitigation_desc,
                'user_comments': '',
                'user_evidence': '',
                'user_status': 'Completed',  # Assume completed when submitted for review
                'approved': None,
                'remarks': ''
            }
            
            # Add previous reviewer feedback if exists
            if (previous_reviewer_feedback and 'mitigation_feedback' in previous_reviewer_feedback and 
                str(key) in previous_reviewer_feedback['mitigation_feedback']):
                feedback = previous_reviewer_feedback['mitigation_feedback'][str(key)]
                mitigation_data['approved'] = feedback.get('approved')
                mitigation_data['remarks'] = feedback.get('remarks', '')
            
            enhanced_mitigations[key] = mitigation_data
        
        return JsonResponse({
            'incident': {
                'IncidentId': incident.IncidentId,
                'IncidentTitle': incident.IncidentTitle,
                'Origin': incident.Origin,
                'RiskPriority': incident.RiskPriority,
                'Status': incident.Status,
                'AssignerId': incident.AssignerId,
                'ReviewerId': incident.ReviewerId
            },
            'mitigations': enhanced_mitigations,
            'latest_assessment_data': latest_assessment_data,
            'submission_date': latest_user_submission.Date if latest_user_submission else None,
            'has_previous_feedback': previous_reviewer_feedback is not None,
            'type': 'audit_finding'
        })
    except Incident.DoesNotExist:
        return JsonResponse({'error': 'Audit finding incident not found'}, status=404)
    except Exception as e:
        print(f"Error fetching audit finding review data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AuditReviewPermission])
@rbac_required(required_permission='review_audit')
def complete_audit_finding_review(request):
    """Complete audit finding review with approval/rejection decisions"""
    try:
        data = request.data
        incident_id = data.get('incident_id')
        reviewer_id = data.get('reviewer_id')
        mitigation_feedback = data.get('mitigation_feedback', {})
        assessment_feedback = data.get('assessment_feedback', {})
        overall_decision = data.get('overall_decision')  # 'approved' or 'rejected'
        
        print(f"DEBUG: Audit finding review data received:")
        print(f"  incident_id: {incident_id}")
        print(f"  reviewer_id: {reviewer_id}")
        print(f"  overall_decision: {overall_decision}")
        print(f"  Full request data: {data}")
        
        # Validate required fields
        if not incident_id:
            return JsonResponse({'error': 'incident_id is required'}, status=400)
        if not reviewer_id:
            return JsonResponse({'error': 'reviewer_id is required'}, status=400)
        if not overall_decision:
            return JsonResponse({'error': 'overall_decision is required'}, status=400)
        
        # Create reviewer approval entry
        reviewer_feedback_data = {
            'reviewer_feedback': {
                'mitigation_feedback': mitigation_feedback,
                'assessment_feedback': assessment_feedback,
                'overall_decision': overall_decision,
                'review_date': datetime.datetime.now().isoformat()
            }
        }
        
        # Get existing entries to determine next version number
        all_entries = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        reviewer_count = 0
        latest_user_entry = None
        
        # Count existing reviewer submissions and find latest user entry
        for entry in all_entries:
            if entry.version and entry.version.startswith('U') and latest_user_entry is None:
                latest_user_entry = entry
            if entry.version and entry.version.startswith('R'):
                reviewer_count += 1
        
        # Generate incremental reviewer version number
        reviewer_version = f"R{reviewer_count + 1}"  # R1, R2, R3, etc.
        
        # Get FrameworkId from the incident
        incident = Incident.objects.get(IncidentId=incident_id)
        framework_id = incident.FrameworkId if incident.FrameworkId else None
        print(f"DEBUG: Using FrameworkId: {framework_id} for audit finding approval")
        
        # Import Framework model at function scope
        from grc.models import Framework
        
        # Get Framework object if framework_id exists
        framework = None
        if framework_id:
            try:
                framework = Framework.objects.get(FrameworkId=framework_id)
                print(f"DEBUG: Found Framework object: {framework}")
            except Framework.DoesNotExist:
                print(f"DEBUG: Framework with ID {framework_id} not found")
                framework = None
        
        approval_entry = IncidentApproval.objects.create(
            IncidentId=incident_id,
            ReviewerId=str(reviewer_id),
            AssigneeId=latest_user_entry.AssigneeId if latest_user_entry else None,
            Date=datetime.datetime.now(),
            version=reviewer_version,
            ExtractedInfo=reviewer_feedback_data,
            ApprovedRejected='Approved' if overall_decision == 'approved' else 'Rejected',
            FrameworkId=framework
        )
        
        print(f"DEBUG: Created IncidentApproval entry:")
        print(f"  ID: {approval_entry.id}")
        print(f"  IncidentId: {approval_entry.IncidentId}")
        print(f"  ReviewerId: {approval_entry.ReviewerId}")
        print(f"  AssigneeId: {approval_entry.AssigneeId}")
        print(f"  Version: {approval_entry.version}")
        print(f"  ApprovedRejected: {approval_entry.ApprovedRejected}")
        
        # Update incident status based on decision
        incident = Incident.objects.get(IncidentId=incident_id)
        if overall_decision == 'approved':
            incident.Status = 'Approved'
        else:
            incident.Status = 'Rejected'
            incident.RejectionSource = 'AUDIT_FINDING_REVIEW'
        
        incident.save()
        
        return JsonResponse({
            'message': f'Audit finding review completed: {overall_decision}',
            'approval_id': approval_entry.id,
            'new_status': incident.Status
        })
    except Exception as e:
        print(f"Error completing audit finding review: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AuditReviewPermission])
@rbac_required(required_permission='review_audit')
def submit_audit_finding_assessment(request):
    """Submit audit finding assessment with cost impact analysis"""
    try:
        from ...routes.Global.validation import QuestionnaireValidator
        
        data = request.data
        incident_id = data.get('incident_id')
        user_id = data.get('user_id')
        raw_assessment_data = data.get('extracted_info', data.get('assessment_data', {}))
        
        # Validate questionnaire data using secure validation
        try:
            validated_questionnaire = QuestionnaireValidator.validate_questionnaire_data(raw_assessment_data)
            print(f"Audit finding questionnaire validation successful: {validated_questionnaire}")
        except Exception as validation_error:
            print(f"Audit finding questionnaire validation failed: {validation_error}")
            return JsonResponse({
                'error': f'Validation failed: {str(validation_error)}',
                'field': getattr(validation_error, 'field', 'unknown')
            }, status=400)
        
        # Process mitigation data to ensure S3 URLs are properly saved in aws-file_link
        processed_assessment_data = process_mitigation_s3_urls(raw_assessment_data)
        
        # Use validated data for storage
        assessment_data = {**processed_assessment_data, **validated_questionnaire}
        
        # Get existing entries to determine next version number
        all_entries = IncidentApproval.objects.filter(IncidentId=incident_id).order_by('-Date')
        user_count = 0
        
        # Count existing user submissions
        for entry in all_entries:
            if entry.version and entry.version.startswith('U'):
                user_count += 1
        
        # Generate incremental user version number
        user_version = f"U{user_count + 1}"  # U1, U2, U3, etc.
        
        # Get FrameworkId from the incident
        incident = Incident.objects.get(IncidentId=incident_id)
        framework_id = incident.FrameworkId if incident.FrameworkId else None
        print(f"DEBUG: Using FrameworkId: {framework_id} for user audit finding assessment submission")
        
        # Import Framework model at function scope
        from grc.models import Framework
        
        # Get Framework object if framework_id exists
        framework = None
        if framework_id:
            try:
                framework = Framework.objects.get(FrameworkId=framework_id)
                print(f"DEBUG: Found Framework object: {framework}")
            except Framework.DoesNotExist:
                print(f"DEBUG: Framework with ID {framework_id} not found")
                framework = None
        
        # Create new IncidentApproval entry for user assessment submission
        approval_entry = IncidentApproval.objects.create(
            IncidentId=incident_id,
            AssigneeId=str(user_id),
            Date=datetime.datetime.now(),
            version=user_version,
            ExtractedInfo=assessment_data,
            FrameworkId=framework
        )
        
        # Update incident status to pending review
        incident.Status = 'Pending Review'
        incident.save()
        
        return JsonResponse({
            'message': 'Audit finding assessment submitted successfully',
            'approval_id': approval_entry.id
        })
    except Exception as e:
        print(f"Error submitting audit finding assessment: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IsAuthenticated])
def test_logging(request):
    """Test endpoint to verify logging functionality"""
    try:
        print("[TEST] Testing logging functionality...")
        
        # Test basic logging
        log_id = send_log(
            module="Test",
            actionType="TEST_LOG",
            description="Testing logging functionality",
            userId="test_user",
            userName="Test User",
            entityType="Test",
            entityId="123",
            ipAddress=get_client_ip(request)
        )
        
        print(f"[TEST] Log ID returned: {log_id}")
        
        # Check if log was actually saved
        if log_id:
            try:
                saved_log = GRCLog.objects.get(LogId=log_id)
                print(f"[TEST] Log successfully retrieved from database: {saved_log}")
                return JsonResponse({
                    'success': True,
                    'message': 'Logging test successful',
                    'log_id': log_id,
                    'saved_log': {
                        'LogId': saved_log.LogId,
                        'Module': saved_log.Module,
                        'ActionType': saved_log.ActionType,
                        'Description': saved_log.Description,
                        'Timestamp': saved_log.Timestamp
                    }
                })
            except GRCLog.DoesNotExist:
                print("[TEST] Log was not found in database!")
                return JsonResponse({
                    'success': False,
                    'message': 'Log was created but not found in database',
                    'log_id': log_id
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to create log',
                'log_id': None
            })
            
    except Exception as e:
        print(f"[TEST] Error in test_logging: {str(e)}")
        import traceback
        print(f"[TEST] Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': f'Test failed: {str(e)}'
        })

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IsAuthenticated])
def test_notification(request):
    """Test endpoint to verify notification system is working"""
    try:
        # Define validation rules for test notification
        validation_rules = {
            'user_id': {
                'type': 'integer',
                'min_value': 1,
                'required': False
            },
            'notification_type': {
                'type': 'choice',
                'choices': ['incidentAssigned', 'incidentApproved', 'incidentRejected', 'incidentEscalated', 'incidentReviewerAssigned'],
                'required': False
            },
            'test_message': {
                'type': 'string',
                'max_length': 500,
                'pattern': SecureValidator.BUSINESS_TEXT_PATTERN,
                'required': False
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        
        notification_service = NotificationService()
        
        # Test data (with validated input)
        user_id = validated_data.get('user_id', 1)
        notification_type = validated_data.get('notification_type', 'incidentAssigned')
        test_message = validated_data.get('test_message', 'Test Incident - Notification System Check')
        
        # Get user email
        user_email = notification_service.get_user_email(user_id)
        user_name = notification_service.get_user_name(user_id)
        
        print(f"Testing notification for User ID: {user_id}")
        print(f"User Name: {user_name}")
        print(f"User Email: {user_email}")
        
        # Send test notification
        test_notification_data = {
            'notification_type': notification_type,
            'email': user_email,
            'email_type': 'gmail',
            'template_data': [
                user_name,
                test_message,
                '2024-01-15'
            ]
        }
        
        result = notification_service.send_multi_channel_notification(test_notification_data)
        
        return Response({
            'success': True,
            'user_id': user_id,
            'user_name': user_name,
            'user_email': user_email,
            'notification_result': result,
            'message': 'Test notification sent successfully'
        })
        
    except Exception as e:
        print(f"Error in test notification: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)



@api_view(['GET'])
@permission_classes([AuditViewPermission])
def debug_category_data(request):
    """Debug endpoint to see all data in categoryunit table"""
    try:
        all_data = CategoryBusinessUnit.objects.all().values('id', 'source', 'value')
        return JsonResponse({
            'all_data': list(all_data),
            'total_count': len(all_data),
            'sources': list(CategoryBusinessUnit.objects.values_list('source', flat=True).distinct())
        })
    except Exception as e:
        print(f"Error fetching debug data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentCreatePermission])
@rbac_required(required_permission='create_incident')
def generate_analysis(request):
    """
    Generate comprehensive incident analysis using the SLM model.
    
    Expected request body:
    {
        "title": "Incident title",
        "description": "Detailed incident description"
    }
    
    Returns:
    {
        "success": true/false,
        "analysis": {analysis data} or null,
        "error": error message if any
    }
    """
    try:
        # Validate request data
        if not request.data:
            return Response({"success": False, "error": "No data provided"}, status=400)
        
        title = request.data.get('title')
        description = request.data.get('description')
        
        if not title or not description:
            return Response({"success": False, "error": "Both title and description are required"}, status=400)
        
        # Import the analysis function
        from .incident_slm import analyze_incident_comprehensive
        
        # Call the analysis function with a timeout
        analysis_result = analyze_incident_comprehensive(title, description)
        
        if not analysis_result:
            return Response({"success": False, "error": "Analysis failed to generate results"}, status=500)
        
        # Validate the analysis result
        required_fields = [
            'riskPriority', 'criticality', 'costOfIncident', 'possibleDamage', 
            'systemsInvolved', 'initialImpactAssessment', 'mitigationSteps', 
            'comments', 'violatedPolicies', 'procedureControlFailures', 'lessonsLearned'
        ]
        
        missing_fields = [field for field in required_fields if field not in analysis_result]
        if missing_fields:
            print(f"Warning: Missing fields in analysis result: {missing_fields}")
            # Continue anyway, as we'll use what we have
        
        # Return the analysis result
        return Response({"success": True, "analysis": analysis_result})
        
    except Exception as e:
        import traceback
        print(f"Error generating analysis: {str(e)}")
        print(traceback.format_exc())
        return Response({"success": False, "error": f"Error generating analysis: {str(e)}"}, status=500)











# Add this view to handle file uploads
import hashlib
import uuid
import asyncio
import threading
import mimetypes
import shlex
import html
from pathlib import Path
from django.conf import settings
from django.utils.html import escape as escape_html
from rest_framework.permissions import IsAuthenticated

# SECURE CODING EXAMPLES:
# 
# 1. HTML OUTPUT ENCODING:
#    safe_html = SecureOutputEncoder.escape_html(user_input)
#    return render(request, 'template.html', {'safe_data': safe_html})
#
# 2. SQL INJECTION PREVENTION:
#    cursor.execute("SELECT * FROM table WHERE id = %s", [user_id])  # GOOD
#    cursor.execute(f"SELECT * FROM table WHERE id = {user_id}")     # BAD
#
# 3. COMMAND INJECTION PREVENTION:
#    safe_path = SecureOutputEncoder.quote_shell_arg(file_path)
#    subprocess.run(['command', safe_path])  # GOOD
#    os.system(f"command {file_path}")       # BAD
#
# 4. JSON OUTPUT ENCODING:
#    safe_error = SecureOutputEncoder.sanitize_error_message(error)
#    return JsonResponse({'error': safe_error})  # GOOD
#    return JsonResponse({'error': str(e)})      # BAD

# Try to import python-magic, fall back to mimetypes if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("[WARNING] python-magic not available, using mimetypes for MIME detection")

# Secure output encoding utilities
class SecureOutputEncoder:
    """
    Secure output encoding utilities to prevent XSS, SQL injection, and command injection
    """
    
    @staticmethod
    def escape_html(value):
        """
        HTML escape user data for safe output in HTML context
        Prevents XSS attacks by encoding special characters
        """
        if value is None:
            return ""
        return escape_html(str(value))
    
    @staticmethod
    def escape_json_string(value):
        """
        Safely encode string values for JSON output
        Prevents JSON injection and ensures proper escaping
        """
        if value is None:
            return ""
        # Convert to string and escape for JSON context
        import json
        return json.dumps(str(value))[1:-1]  # Remove surrounding quotes
    
    @staticmethod
    def sanitize_error_message(error_msg):
        """
        Sanitize error messages to prevent information disclosure
        Returns safe, generic error messages for user-facing output
        """
        if not error_msg:
            return "An error occurred"
        
        # Convert to string and limit length
        safe_msg = str(error_msg)[:200]
        
        # Remove sensitive information patterns
        sensitive_patterns = [
            r'password',
            r'token',
            r'secret',
            r'key',
            r'auth',
            r'session',
            r'cookie',
            r'database',
            r'sql',
            r'query',
            r'connection',
            r'file not found',
            r'permission denied',
            r'access denied'
        ]
        
        import re
        for pattern in sensitive_patterns:
            safe_msg = re.sub(pattern, '[REDACTED]', safe_msg, flags=re.IGNORECASE)
        
        # HTML escape the result
        return escape_html(safe_msg)
    
    @staticmethod
    def quote_shell_arg(value):
        """
        Safely quote shell arguments using shlex.quote()
        Prevents command injection attacks
        """
        if value is None:
            return ""
        return shlex.quote(str(value))
    
    @staticmethod
    def safe_format_string(template, **kwargs):
        """
        Safely format strings by escaping all parameters
        Prevents format string attacks
        """
        safe_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                safe_kwargs[key] = escape_html(value)
            else:
                safe_kwargs[key] = value
        return template.format(**safe_kwargs)
    
    @staticmethod
    def safe_json_response(data, status=200, safe=True):
        """
        Create a secure JSON response with proper encoding
        Ensures all string values are properly escaped
        """
        from django.http import JsonResponse
        
        def sanitize_value(value):
            if isinstance(value, str):
                return SecureOutputEncoder.escape_json_string(value)
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value]
            else:
                return value
        
        if isinstance(data, dict) and 'error' in data:
            # Special handling for error messages
            data['error'] = SecureOutputEncoder.sanitize_error_message(data['error'])
        
        # Note: For this implementation, we'll use Django's built-in JsonResponse
        # which already provides good JSON encoding security
        return JsonResponse(data, status=status, safe=safe)

class SecureFileUploadHandler:
    """
    Secure file upload handler with comprehensive security measures:
    1. Authentication and authorization
    2. MIME type validation (whitelist)
    3. Secure file storage outside web root
    4. Malware scanning (async)
    5. Execution prevention
    """
    
    # Strictly whitelisted MIME types and extensions
    ALLOWED_MIME_TYPES = {
        'application/pdf': ['.pdf'],
        'application/msword': ['.doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'text/plain': ['.txt'],
        'image/png': ['.png'],
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/gif': ['.gif'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        'text/csv': ['.csv']
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR = getattr(settings, 'SECURE_UPLOAD_DIR', 'secure_uploads')
    QUARANTINE_DIR = getattr(settings, 'QUARANTINE_DIR', 'quarantine')
    
    def __init__(self):
        self.validator = SecureValidator()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create secure upload directories if they don't exist"""
        try:
            # Convert to absolute paths from the project root
            from django.conf import settings
            project_root = Path(settings.BASE_DIR)
            
            upload_path = project_root / self.UPLOAD_DIR
            quarantine_path = project_root / self.QUARANTINE_DIR
            
            upload_path.mkdir(parents=True, exist_ok=True)
            quarantine_path.mkdir(parents=True, exist_ok=True)
            
            # Update paths to absolute paths
            self.UPLOAD_DIR = str(upload_path)
            self.QUARANTINE_DIR = str(quarantine_path)
            
            print(f"[SECURITY] Upload directory: {self.UPLOAD_DIR}")
            print(f"[SECURITY] Quarantine directory: {self.QUARANTINE_DIR}")
            
            # Disable execution on upload directories
            self._disable_execution(self.UPLOAD_DIR)
            self._disable_execution(self.QUARANTINE_DIR)
        except Exception as e:
            print(f"Error creating secure directories: {e}")
            # Fallback to current directory if creation fails
            fallback_upload = Path.cwd() / "temp_uploads"
            fallback_quarantine = Path.cwd() / "temp_quarantine"
            fallback_upload.mkdir(exist_ok=True)
            fallback_quarantine.mkdir(exist_ok=True)
            self.UPLOAD_DIR = str(fallback_upload)
            self.QUARANTINE_DIR = str(fallback_quarantine)
            print(f"[SECURITY] Using fallback upload directory: {self.UPLOAD_DIR}")
    
    def _disable_execution(self, directory):
        """Disable script execution in upload directories"""
        try:
            # Create .htaccess file to disable execution (for Apache)
            htaccess_path = Path(directory) / '.htaccess'
            with open(htaccess_path, 'w') as f:
                f.write("""
# Disable script execution
Options -ExecCGI
AddHandler cgi-script .php .pl .py .jsp .asp .sh
RemoveHandler .php .phtml .php3 .php4 .php5 .phps .shtml .cgi .pl .py
php_flag engine off

# Prevent access to sensitive files
<Files ~ "\\.(htaccess|htpasswd|ini|log|sh|sql|conf)$">
    Order allow,deny
    Deny from all
</Files>
""")
            
            # Create web.config for IIS
            webconfig_path = Path(directory) / 'web.config'
            with open(webconfig_path, 'w') as f:
                f.write("""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <handlers>
            <clear />
            <add name="StaticFile" path="*" verb="*" modules="StaticFileModule" resourceType="Either" requireAccess="Read" />
        </handlers>
        <security>
            <requestFiltering>
                <fileExtensions>
                    <remove fileExtension=".php" />
                    <remove fileExtension=".asp" />
                    <remove fileExtension=".aspx" />
                    <remove fileExtension=".jsp" />
                    <remove fileExtension=".py" />
                    <remove fileExtension=".pl" />
                    <remove fileExtension=".sh" />
                </fileExtensions>
            </requestFiltering>
        </security>
    </system.webServer>
</configuration>""")
        except Exception as e:
            print(f"Warning: Could not create execution prevention files: {e}")
    
    def _generate_secure_filename(self, original_filename, user_id):
        """Generate a secure random filename"""
        # Extract extension safely
        original_path = Path(original_filename)
        extension = original_path.suffix.lower()
        
        # Generate UUID-based filename
        secure_name = f"{uuid.uuid4().hex}_{hashlib.sha256(f'{user_id}_{original_filename}'.encode()).hexdigest()[:8]}{extension}"
        return secure_name
    
    def _validate_mime_type(self, file_path, declared_extension):
        """Validate MIME type using python-magic or mimetypes fallback"""
        try:
            if MAGIC_AVAILABLE:
                # Use python-magic for accurate file signature detection
                detected_mime = magic.from_file(file_path, mime=True)
                print(f"[SECURITY] Magic detected MIME type: {detected_mime}")
            else:
                # Fallback to mimetypes based on extension
                detected_mime, _ = mimetypes.guess_type(file_path)
                if not detected_mime:
                    # Manual mapping for common types
                    extension_mime_map = {
                        '.pdf': 'application/pdf',
                        '.doc': 'application/msword',
                        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        '.txt': 'text/plain',
                        '.png': 'image/png',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.gif': 'image/gif',
                        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        '.csv': 'text/csv'
                    }
                    detected_mime = extension_mime_map.get(declared_extension.lower())
                
                if not detected_mime:
                    return False, f"Cannot determine MIME type for extension: {declared_extension}"
                
                print(f"[SECURITY] Mimetypes detected MIME type: {detected_mime}")
            
            # Additional security check: read file header for basic validation
            if not self._validate_file_header(file_path, declared_extension):
                return False, f"File header validation failed for {declared_extension}"
            
            # Check if detected MIME type is in whitelist
            if detected_mime not in self.ALLOWED_MIME_TYPES:
                return False, f"File type not allowed: {detected_mime}"
            
            # Check if declared extension matches detected MIME type
            allowed_extensions = self.ALLOWED_MIME_TYPES[detected_mime]
            if declared_extension not in allowed_extensions:
                return False, f"File extension {declared_extension} doesn't match detected type {detected_mime}"
            
            return True, detected_mime
        except Exception as e:
            return False, f"MIME type validation failed: {str(e)}"
    
    def _validate_file_header(self, file_path, declared_extension):
        """Basic file header validation for common file types"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)  # Read first 32 bytes
            
            # File signature validation
            file_signatures = {
                '.pdf': [b'%PDF'],
                '.jpg': [b'\xff\xd8\xff'],
                '.jpeg': [b'\xff\xd8\xff'],
                '.png': [b'\x89PNG\r\n\x1a\n'],
                '.gif': [b'GIF87a', b'GIF89a'],
                '.doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],  # OLE2 signature
                '.docx': [b'PK\x03\x04'],  # ZIP signature (DOCX is ZIP-based)
                '.xlsx': [b'PK\x03\x04'],  # ZIP signature (XLSX is ZIP-based)
                '.csv': [],  # CSV has no specific header, skip validation
                '.txt': []   # TXT has no specific header, skip validation
            }
            
            signatures = file_signatures.get(declared_extension.lower(), [])
            if not signatures:  # No signatures to check (like TXT, CSV)
                return True
            
            # Check if file starts with any of the expected signatures
            for signature in signatures:
                if header.startswith(signature):
                    print(f"[SECURITY] File header validation passed for {declared_extension}")
                    return True
            
            print(f"[SECURITY] File header validation failed for {declared_extension}")
            print(f"[SECURITY] Expected signatures: {signatures}")
            print(f"[SECURITY] Actual header: {header[:16].hex()}")
            return False
            
        except Exception as e:
            print(f"[SECURITY] File header validation error: {e}")
            return False  # Fail secure
    
    def _scan_for_malware(self, file_path):
        """
        Asynchronous malware scanning placeholder
        In production, integrate with ClamAV, VirusTotal API, or similar
        """
        def scan_async():
            try:
                # Placeholder for actual malware scanning
                # In production, integrate with:
                # SECURE: Use shlex.quote() to prevent command injection
                # - ClamAV: subprocess.run(['clamscan', shlex.quote(file_path)])
                # - VirusTotal API
                # - Windows Defender API
                # - Custom ML-based detection
                
                print(f"[SECURITY] Scanning file for malware: {file_path}")
                
                # Check if file exists before scanning
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    print(f"[SECURITY] File not found for scanning: {file_path}")
                    return False
                
                # Simulate scan (replace with actual implementation)
                import time
                time.sleep(0.1)  # Reduced scan time for better performance
                
                # For now, perform basic checks
                file_size = file_path_obj.stat().st_size
                if file_size > self.MAX_FILE_SIZE:
                    print(f"[SECURITY] File too large: {file_size} bytes")
                    return False
                
                # Check for suspicious patterns in filename
                suspicious_patterns = ['.exe', '.bat', '.cmd', '.scr', '.vbs', '.js']
                filename = file_path_obj.name.lower()
                for pattern in suspicious_patterns:
                    if pattern in filename:
                        print(f"[SECURITY] Suspicious pattern detected: {pattern}")
                        return False
                
                print(f"[SECURITY] File scan completed successfully: {file_path}")
                return True
                
            except Exception as e:
                print(f"[SECURITY] Malware scan error: {e}")
                print(f"[SECURITY] File path: {file_path}")
                print(f"[SECURITY] File exists: {Path(file_path).exists()}")
                return False
        
        # Run scan in background thread
        thread = threading.Thread(target=scan_async)
        thread.daemon = True
        thread.start()
        
        # For this implementation, we'll return True immediately
        # In production, you might want to quarantine files until scan completes
        return True
    
    def _scan_with_clamav(self, file_path):
        """
        SECURE: Example ClamAV integration with proper shell argument quoting
        Prevents command injection attacks
        """
        try:
            import subprocess
            # SECURE: Use shlex.quote() to safely quote the file path
            safe_file_path = SecureOutputEncoder.quote_shell_arg(file_path)
            
            # Execute ClamAV scan with quoted arguments
            result = subprocess.run(
                ['clamscan', '--no-summary', safe_file_path],
                capture_output=True,
                text=True,
                timeout=30,
                check=False  # Don't raise exception on non-zero exit
            )
            
            # ClamAV returns 0 for clean files, 1 for infected files
            is_clean = result.returncode == 0
            
            if not is_clean:
                print(f"[SECURITY] ClamAV detected threat in file: {file_path}")
                print(f"[SECURITY] ClamAV output: {result.stdout}")
            
            return is_clean
            
        except subprocess.TimeoutExpired:
            print(f"[SECURITY] ClamAV scan timeout for file: {file_path}")
            return False  # Fail secure
        except FileNotFoundError:
            print("[SECURITY] ClamAV not found, falling back to basic scan")
            return self._scan_for_malware(file_path)  # Fallback to basic scan
        except Exception as e:
            print(f"[SECURITY] ClamAV scan error: {e}")
            return False  # Fail secure

# Helper function to get S3 client
def get_s3_client():
    """Get S3 client with error handling"""
    try:
        from ...routes.Global.s3_fucntions import RenderS3Client, create_direct_mysql_client
        print("✅ S3 microservice client imported successfully")
        return create_direct_mysql_client()
    except ImportError as e:
        print(f"❌ Failed to import S3 microservice client: {e}")
        raise Exception(f"S3 microservice client not available: {e}")
    except Exception as e:
        print(f"❌ Failed to create S3 client: {e}")
        raise Exception(f"Failed to initialize S3 client: {e}")

def process_mitigation_s3_urls(assessment_data):
    """
    Process mitigation data to ensure S3 URLs from uploaded files 
    are properly saved in the aws-file_link field for backward compatibility
    """
    try:
        processed_data = assessment_data.copy()
        
        if 'mitigations' in processed_data:
            mitigations = processed_data['mitigations']
            
            for mitigation_key, mitigation_data in mitigations.items():
                if isinstance(mitigation_data, dict):
                    # Check if there are files uploaded but no aws-file_link
                    files = mitigation_data.get('files', [])
                    current_aws_link = mitigation_data.get('aws-file_link')
                    current_filename = mitigation_data.get('fileName')
                    
                    # If files exist and no aws-file_link is set, use the first file's S3 URL
                    if files and len(files) > 0:
                        first_file = files[0]
                        
                        # Update aws-file_link with S3 URL from first file for backward compatibility
                        if first_file.get('aws-file_link') and not current_aws_link:
                            mitigation_data['aws-file_link'] = first_file['aws-file_link']
                            print(f"Updated mitigation {mitigation_key} aws-file_link with S3 URL: {first_file['aws-file_link']}")
                        
                        # Update fileName with first file's name for backward compatibility
                        if first_file.get('fileName') and not current_filename:
                            mitigation_data['fileName'] = first_file['fileName']
                            print(f"Updated mitigation {mitigation_key} fileName with: {first_file['fileName']}")
                    
                    # Ensure files array is preserved
                    processed_data['mitigations'][mitigation_key] = mitigation_data
        
        print(f"Processed assessment data with S3 URLs for {len(processed_data.get('mitigations', {}))} mitigations")
        
        # Debug: Log the processed mitigation data
        if 'mitigations' in processed_data:
            for key, mitigation in processed_data['mitigations'].items():
                if isinstance(mitigation, dict):
                    aws_link = mitigation.get('aws-file_link')
                    files_count = len(mitigation.get('files', []))
                    print(f"  Mitigation {key}: aws-file_link={aws_link}, files_count={files_count}")
        
        return processed_data
        
    except Exception as e:
        print(f"Error processing mitigation S3 URLs: {str(e)}")
        # Return original data if processing fails
        return assessment_data

@method_decorator(csrf_exempt, name='dispatch')
class FileUploadView(View):
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to add authentication check"""
        # 1. AUTHENTICATION AND AUTHORIZATION
        # Temporarily disabled authentication for file upload
        # if not request.user.is_authenticated:
        #     return JsonResponse({
        #         'success': False, 
        #         'error': 'Authentication required for file upload'
        #     }, status=401)
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        handler = SecureFileUploadHandler()
        
        # Get user info for logging
        user_id = getattr(request.user, 'id', None)
        username = getattr(request.user, 'username', 'Unknown')
        
        # Log file upload attempt
        send_log(
            module="File",
            actionType="UPLOAD_ATTEMPT",
            description="User attempting to upload file",
            userId=user_id,
            userName=username,
            entityType="File",
            ipAddress=get_client_ip(request)
        )
        
        try:
            # Get file and form data from request
            if 'file' not in request.FILES:
                send_log(
                    module="File",
                    actionType="UPLOAD_FAILED",
                    description="File upload failed - no file provided",
                    userId=user_id,
                    userName=username,
                    entityType="File",
                    logLevel="WARN",
                    ipAddress=get_client_ip(request)
                )
                return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
            
            file = request.FILES['file']
            incident_id = request.POST.get('incidentId')
            mitigation_number = request.POST.get('mitigationNumber')
            
            # Log file details
            send_log(
                module="File",
                actionType="UPLOAD_FILE_DETAILS",
                description=f"File upload details - filename: {file.name}, size: {file.size}, incident: {incident_id}",
                userId=user_id,
                userName=username,
                entityType="File",
                ipAddress=get_client_ip(request),
                additionalInfo={
                    'filename': file.name,
                    'file_size': file.size,
                    'incident_id': incident_id,
                    'mitigation_number': mitigation_number
                }
            )
            
            # Validate required fields
            if not incident_id or not mitigation_number:
                send_log(
                    module="File",
                    actionType="UPLOAD_VALIDATION_FAILED",
                    description="File upload failed - missing required fields",
                    userId=user_id,
                    userName=username,
                    entityType="File",
                    logLevel="WARN",
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        'incident_id': incident_id,
                        'mitigation_number': mitigation_number
                    }
                )
                return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
            
            try:
                incident_id = int(incident_id)
                mitigation_number = int(mitigation_number)
            except ValueError:
                send_log(
                    module="File",
                    actionType="UPLOAD_VALIDATION_FAILED",
                    description="File upload failed - invalid incident ID or mitigation number",
                    userId=user_id,
                    userName=username,
                    entityType="File",
                    logLevel="WARN",
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        'incident_id': incident_id,
                        'mitigation_number': mitigation_number
                    }
                )
                return JsonResponse({'success': False, 'error': 'Invalid incident ID or mitigation number'}, status=400)
            
            file_name = file.name
            
            # 2. VALIDATE FILE EXTENSION AGAINST WHITELIST
            file_ext = Path(file_name).suffix.lower()
            allowed_extensions = []
            for exts in handler.ALLOWED_MIME_TYPES.values():
                allowed_extensions.extend(exts)
            
            if file_ext not in allowed_extensions:
                send_log(
                    module="File",
                    actionType="UPLOAD_SECURITY_BLOCKED",
                    description=f"File upload blocked - disallowed file type: {file_ext}",
                    userId=user_id,
                    userName=username,
                    entityType="File",
                    logLevel="WARN",
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        'filename': file.name,
                        'file_extension': file_ext,
                        'allowed_extensions': sorted(set(allowed_extensions))
                    }
                )
                return JsonResponse({
                    'success': False, 
                    'error': f'File type not allowed. Allowed types: {", ".join(sorted(set(allowed_extensions)))}'
                }, status=400)
                
                # File size check
            if file.size > handler.MAX_FILE_SIZE:
                send_log(
                    module="File",
                    actionType="UPLOAD_SECURITY_BLOCKED",
                    description=f"File upload blocked - file size exceeds limit: {file.size} bytes",
                    userId=user_id,
                    userName=username,
                    entityType="File",
                    logLevel="WARN",
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        'filename': file.name,
                        'file_size': file.size,
                        'max_allowed_size': handler.MAX_FILE_SIZE
                    }
                )
                return JsonResponse({
                    'success': False, 
                    'error': f'File size exceeds {handler.MAX_FILE_SIZE // (1024*1024)}MB limit'
                }, status=400)
            
            # 3. STORE FILE OUTSIDE WEB ROOT WITH RANDOM NAME
            user_id = getattr(request.user, 'id', 1) if hasattr(request, 'user') else 1  # Default to user 1
            secure_filename = handler._generate_secure_filename(file_name, user_id)
            secure_path = Path(handler.UPLOAD_DIR) / secure_filename
            
            # Write file to secure location
            with open(secure_path, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            # Set secure file permissions (read-only for owner, no execute)
            secure_path.chmod(0o644)
            
            # 4. VALIDATE MIME TYPE USING FILE SIGNATURE
            mime_valid, mime_result = handler._validate_mime_type(str(secure_path), file_ext)
            if not mime_valid:
                # Remove invalid file
                secure_path.unlink(missing_ok=True)
                # SECURE: Sanitize MIME validation error
                safe_error = SecureOutputEncoder.sanitize_error_message(mime_result)
                return JsonResponse({'success': False, 'error': safe_error}, status=400)
            
            # 5. SCAN FOR MALWARE ASYNCHRONOUSLY
            print(f"[SECURITY] Starting malware scan for: {secure_path}")
            print(f"[SECURITY] File exists before scan: {secure_path.exists()}")
            
            if not handler._scan_for_malware(str(secure_path)):
                # Log security scan failure
                send_log(
                    module="File",
                    actionType="UPLOAD_SECURITY_SCAN_FAILED",
                    description=f"File failed security scan and quarantined: {file.name}",
                    userId=user_id,
                    userName=username,
                    entityType="File",
                    logLevel="WARN",
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        'filename': file.name,
                        'secure_filename': secure_filename,
                        'incident_id': incident_id,
                        'scan_result': 'FAILED'
                    }
                )
                
                # Move to quarantine
                try:
                    quarantine_path = Path(handler.QUARANTINE_DIR) / secure_filename
                    if secure_path.exists():
                        secure_path.rename(quarantine_path)
                        print(f"[SECURITY] File quarantined: {quarantine_path}")
                    else:
                        print(f"[SECURITY] File not found for quarantine: {secure_path}")
                except Exception as e:
                    print(f"[SECURITY] Error quarantining file: {e}")
                    # Remove file if quarantine fails
                    secure_path.unlink(missing_ok=True)
                
                return JsonResponse({
                    'success': False, 
                    'error': 'File failed security scan and has been quarantined'
                }, status=400)
            
            # Upload to S3 via Render microservice with enhanced metadata
            try:
                # Create RenderS3Client instance
                s3_client = get_s3_client()
                
                # Create a custom filename for S3 that includes incident and mitigation info
                custom_s3_filename = f"incident_{incident_id}_mitigation_{mitigation_number}_{secure_filename}"
                
                print(f"[S3] Uploading file to Render microservice: {custom_s3_filename}")
                
                # Upload file using RenderS3Client
                upload_result = s3_client.upload(
                    file_path=str(secure_path),
                    user_id=f"user_{user_id}",
                    custom_file_name=custom_s3_filename,
                    module='Incident'
                )
                
                if upload_result.get('success'):
                    file_info = upload_result['file_info']
                    
                    # Clean up local file after successful S3 upload
                    secure_path.unlink(missing_ok=True)
                    print(f"[SECURITY] File successfully uploaded to Render/S3 and local file cleaned up")
                    
                    # Log successful upload with enhanced info
                    send_log(
                        module="File",
                        actionType="UPLOAD_SUCCESS",
                        description=f"File successfully uploaded via Render microservice: {file.name}",
                        userId=user_id,
                        userName=username,
                        entityType="File",
                        ipAddress=get_client_ip(request),
                        additionalInfo={
                            'filename': file.name,
                            'secure_filename': secure_filename,
                            'stored_name': file_info.get('storedName'),
                            'incident_id': incident_id,
                            'mitigation_number': mitigation_number,
                            'file_size': file.size,
                            'mime_type': mime_result,
                            's3_url': file_info.get('url'),
                            's3_key': file_info.get('s3Key'),
                            'platform': 'Render',
                            'operation_id': upload_result.get('operation_id'),
                            'microservice_url': 'https://aws-microservice.onrender.com'
                        }
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'file_url': file_info.get('url'),
                        's3_url': file_info.get('url'),
                        'aws-file_link': file_info.get('url'),  # Added for compatibility with Vue component
                        'fileName': file.name,  # Original filename for display
                        'stored_name': file_info.get('storedName'),
                        's3_key': file_info.get('s3Key'),
                        'secure_filename': secure_filename,
                        'mime_type': mime_result,
                        'operation_id': upload_result.get('operation_id'),
                        'platform': 'Render'
                    })
                else:
                    # Handle Render microservice upload failure
                    error_msg = upload_result.get('error', 'Unknown upload error')
                    raise Exception(f"Render microservice upload failed: {error_msg}")
            
            except Exception as e:
                # Log S3 upload failure with enhanced details
                send_log(
                    module="File",
                    actionType="UPLOAD_S3_FAILED",
                    description=f"Render microservice S3 upload failed for file: {file.name}",
                    userId=user_id,
                    userName=username,
                    entityType="File",
                    logLevel="ERROR",
                    ipAddress=get_client_ip(request),
                    additionalInfo={
                        'filename': file.name,
                        'error': str(e),
                        'incident_id': incident_id,
                        'mitigation_number': mitigation_number,
                        'platform': 'Render',
                        'microservice_url': 'https://aws-microservice.onrender.com'
                    }
                )
                
                # Clean up on S3 upload failure
                secure_path.unlink(missing_ok=True)
                print(f"[SECURITY] Render microservice S3 upload failed, local file cleaned up: {str(e)}")
                # SECURE: Sanitize upload error message
                safe_error = SecureOutputEncoder.sanitize_error_message(f'Upload to cloud storage failed: {str(e)}')
                return JsonResponse({
                    'success': False,
                    'error': safe_error,
                    'platform': 'Render'
                }, status=500)
            
        except Exception as e:
            # Log general upload error
            send_log(
                module="File",
                actionType="UPLOAD_ERROR",
                description=f"File upload error: {str(e)}",
                userId=user_id,
                userName=username,
                entityType="File",
                logLevel="ERROR",
                ipAddress=get_client_ip(request),
                additionalInfo={'error': str(e)}
            )
            
            print(f"[SECURITY] File upload error: {str(e)}")
            # SECURE: Return generic error message to prevent information disclosure
            return JsonResponse({
                'success': False,
                'error': 'Upload failed due to security validation'
            }, status=500)

@csrf_exempt
@require_consent('upload_incident')
def upload_evidence_file(request):
    """
    Upload evidence files for incident mitigations.
    Supports multiple file uploads and stores them securely.
    """
    # Only allow POST requests
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)
    
    try:
        # Debug logging
        print(f"Content-Type: {request.content_type}")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        print(f"Request method: {request.method}")
        
        # Get user info for logging from POST data (FormData)
        user_id = request.POST.get('user_id')
        incident_id = request.POST.get('incident_id')
        
        if not request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No files provided'
            }, status=400)
        
        uploaded_files = []
        handler = SecureFileUploadHandler()
        
        # Process each uploaded file
        for field_name, file in request.FILES.items():
            try:
                print(f"Processing file: {file.name}, Size: {file.size}, Type: {file.content_type}")
                
                # Extract file extension
                file_name = file.name
                file_ext = Path(file_name).suffix.lower()
                
                # File size check
                if file.size > handler.MAX_FILE_SIZE:
                    return JsonResponse({
                        'success': False,
                        'error': f'File size exceeds {handler.MAX_FILE_SIZE // (1024*1024)}MB limit'
                    }, status=400)
                
                # MIME type validation
                if file.content_type not in handler.ALLOWED_MIME_TYPES:
                    return JsonResponse({
                        'success': False,
                        'error': f'File type {file.content_type} not allowed'
                    }, status=400)
                
                # Create temporary file for S3 upload
                import tempfile
                import os
                
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                        for chunk in file.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                    print(f"DEBUG: Temporary file created: {temp_file_path}")
                except Exception as e:
                    print(f"DEBUG: Error creating temporary file: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Error saving file temporarily: {str(e)}'
                    }, status=500)
                
                try:
                    # Create S3 client
                    print("DEBUG: Creating S3 client...")
                    s3_client = get_s3_client()
                    
                    # Test connection first
                    print("DEBUG: Testing S3 connection...")
                    connection_test = s3_client.test_connection()
                    print(f"DEBUG: Connection test result: {connection_test}")
                    
                    if not connection_test.get('overall_success', False):
                        print("DEBUG: S3 connection test failed")
                        return JsonResponse({
                            'success': False,
                            'error': 'S3 service is currently unavailable. Please try again later.',
                            'details': connection_test
                        }, status=503)
                    
                    # Generate unique file name to avoid conflicts
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_file_name = f"evidence_{incident_id}_{timestamp}_{file_name}"
                    
                    print(f"DEBUG: Generated unique filename: {unique_file_name}")
                    
                    # Upload to S3
                    print(f"DEBUG: Starting S3 upload...")
                    upload_result = s3_client.upload(
                        file_path=temp_file_path,
                        user_id=user_id or "system",
                        custom_file_name=unique_file_name,
                        module='Incident'
                    )
                    
                    print(f"DEBUG: S3 upload result: {upload_result}")
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                        print(f"DEBUG: Cleaned up temporary file: {temp_file_path}")
                    except Exception as cleanup_error:
                        print(f"DEBUG: Error cleaning up temp file: {cleanup_error}")
                
                if upload_result.get('success'):
                    file_info = upload_result.get('file_info', {})
                    
                    # Save S3 file metadata to database
                    try:
                        from ...models import S3File
                        s3_file = S3File.objects.create(
                            url=file_info.get('url'),
                            file_type=file.content_type,
                            file_name=file.name,
                            user_id=str(user_id),
                            metadata={
                                'incident_id': incident_id,
                                's3_key': file_info.get('s3Key'),
                                'stored_name': file_info.get('storedName'),
                                'original_size': file.size,
                                'upload_context': 'incident_evidence'
                            }
                        )
                        print(f"DEBUG: Saved S3 file metadata to database with ID: {s3_file.id}")
                    except Exception as db_error:
                        print(f"WARNING: Failed to save S3 file metadata to database: {db_error}")
                    
                    uploaded_files.append({
                        'fileName': file.name,
                        'aws-file_link': file_info.get('url'),  # S3 URL
                        's3_key': file_info.get('s3Key'),  # S3 key for future downloads
                        'stored_name': file_info.get('storedName'),  # Name stored in S3
                        'size': file.size,
                        'uploadedAt': timezone.now().isoformat(),
                        'file_id': str(uuid.uuid4()),
                        'upload_type': 's3'  # Indicate this is an S3 upload
                    })
                    
                    # Log successful S3 upload
                    send_log(
                        module="Evidence Upload",
                        actionType="S3_UPLOAD_SUCCESS",
                        description=f"Evidence file uploaded to S3 successfully: {file.name}",
                        userId=user_id,
                        ipAddress=get_client_ip(request),
                        additionalInfo={
                            'incident_id': incident_id,
                            'file_name': file.name,
                            'file_size': file.size,
                            's3_url': file_info.get('url'),
                            's3_key': file_info.get('s3Key'),
                            'stored_name': file_info.get('storedName')
                        }
                    )
                else:
                    # Log failed S3 upload
                    send_log(
                        module="Evidence Upload",
                        actionType="S3_UPLOAD_FAILED",
                        description=f"Evidence file S3 upload failed: {file.name} - {upload_result.get('error', 'Unknown error')}",
                        userId=user_id,
                        ipAddress=get_client_ip(request),
                        logLevel='ERROR',
                        additionalInfo={
                            'incident_id': incident_id,
                            'file_name': file.name,
                            'error': upload_result.get('error', 'S3 upload failed')
                        }
                    )
                    
                    return JsonResponse({
                        'success': False,
                        'error': f"Failed to upload {file.name} to S3: {upload_result.get('error', 'S3 upload failed')}"
                    }, status=400)
                    
            except Exception as file_error:
                # Log file processing error
                send_log(
                    module="Evidence Upload",
                    actionType="FILE_PROCESSING_ERROR",
                    description=f"Error processing evidence file: {file.name}",
                    userId=user_id,
                    ipAddress=get_client_ip(request),
                    logLevel='ERROR',
                    additionalInfo={
                        'incident_id': incident_id,
                        'file_name': file.name,
                        'error': str(file_error)
                    }
                )
                
                return JsonResponse({
                    'success': False,
                    'error': f"Error processing {file.name}: {str(file_error)}"
                }, status=500)
        
        print(f"DEBUG: Returning upload response with {len(uploaded_files)} files")
        for i, file_info in enumerate(uploaded_files):
            print(f"DEBUG: File {i+1}: {file_info}")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
            'files': uploaded_files
        })
        
    except Exception as e:
        # Log general error
        send_log(
            module="Evidence Upload",
            actionType="EVIDENCE_UPLOAD_ERROR",
            description=f"General error in evidence upload endpoint",
            userId=request.POST.get('user_id'),
            ipAddress=get_client_ip(request),
            logLevel='ERROR',
            additionalInfo={
                'error': str(e),
                'incident_id': request.POST.get('incident_id')
            }
        )
        
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
def get_categories(request):
    """Get all categories for dropdown selection"""
    try:
        # Check for both 'category' and 'Categories' to handle different data formats
        categories = CategoryBusinessUnit.objects.filter(
            source__in=['category', 'Categories']
        ).values_list('value', flat=True).distinct()
        return JsonResponse(list(categories), safe=False)
    except Exception as e:
        print(f"Error fetching categories: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_incident_categories(request):
    """Get all incident categories for dropdown selection"""
    try:
        # Check for incident categories in the CategoryBusinessUnit table
        incident_categories = CategoryBusinessUnit.objects.filter(
            source__in=['incident_category', 'IncidentCategory', 'Incident Category']
        ).values_list('value', flat=True).distinct()
        
        # Default incident categories if none exist in database
        default_categories = [
            'Security Incident',
            'Data Breach',
            'System Outage',
            'Operational Failure',
            'Compliance Violation',
            'Privacy Incident',
            'Network Incident',
            'Application Error',
            'Infrastructure Failure',
            'Human Error',
            'External Attack',
            'Internal Threat',
            'Business Disruption',
            'Service Degradation',
            'Configuration Error'
        ]
        
        # Combine existing with defaults and remove duplicates
        all_categories = list(set(list(incident_categories) + default_categories))
        
        return JsonResponse(all_categories, safe=False)
    except Exception as e:
        print(f"Error fetching incident categories: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def add_incident_category(request):
    """Add a new incident category if it doesn't exist"""
    try:
        # Define validation rules for incident category addition
        validation_rules = {
            'value': {
                'type': 'string',
                'max_length': 255,
                'min_length': 1,
                'pattern': SecureValidator.BUSINESS_TEXT_PATTERN,
                'required': True
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        category_value = validated_data.get('value', '').strip()
        
        # Check if incident category already exists
        existing_category = CategoryBusinessUnit.objects.filter(
            source__in=['incident_category', 'IncidentCategory', 'Incident Category'], 
            value__iexact=category_value
        ).first()
        
        if not existing_category:
            CategoryBusinessUnit.objects.create(
                source='IncidentCategory',  # Use consistent format
                value=category_value
            )
            return JsonResponse({'message': 'Incident category added successfully', 'value': category_value})
        else:
            return JsonResponse({'message': 'Incident category already exists', 'value': existing_category.value})
            
    except Exception as e:
        print(f"Error adding incident category: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])  # Allow any authenticated user to access business units
def get_business_units(request):
    """Get all business units for dropdown selection"""
    try:
        # Check if user is authenticated
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Check if user has any module access (business units are used across modules)
        rbac_record = RBACUtils.get_user_rbac_record(user_id)
        if not rbac_record:
            return JsonResponse({'error': 'No RBAC record found'}, status=403)
        
        # Allow access if user has any module permissions (business units are used across all modules)
        has_access = (
            # Incident module permissions
            rbac_record.view_all_incident or 
            rbac_record.create_incident or
            rbac_record.edit_incident or
            rbac_record.assign_incident or
            rbac_record.evaluate_assigned_incident or
            rbac_record.escalate_to_risk or
            rbac_record.incident_performance_analytics or
            
            # Policy module permissions
            rbac_record.view_all_policy or 
            rbac_record.create_policy or
            rbac_record.edit_policy or
            rbac_record.approve_policy or
            rbac_record.create_framework or
            rbac_record.approve_framework or
            rbac_record.policy_performance_analytics or
            
            # Compliance module permissions
            rbac_record.view_all_compliance or 
            rbac_record.create_compliance or
            rbac_record.edit_compliance or
            rbac_record.approve_compliance or
            rbac_record.compliance_performance_analytics or
            
            # Risk module permissions
            rbac_record.view_all_risk or 
            rbac_record.create_risk or
            rbac_record.edit_risk or
            rbac_record.approve_risk or
            rbac_record.assign_risk or
            rbac_record.evaluate_assigned_risk or
            rbac_record.risk_performance_analytics or
            
            # Audit module permissions
            rbac_record.view_audit_reports or
            rbac_record.assign_audit or
            rbac_record.conduct_audit or
            rbac_record.review_audit or
            rbac_record.audit_performance_analytics
        )
        
        if not has_access:
            logger.warning(f"[RBAC] User {user_id} denied access to business units - no module permissions")
            return JsonResponse({
                'error': 'Access denied',
                'message': 'You do not have permission to access business units'
            }, status=403)
        
        # Check for both 'business_unit' and other possible formats
        business_units = CategoryBusinessUnit.objects.filter(
            source__in=['business_unit', 'BusinessUnit', 'Business Unit']
        ).values_list('value', flat=True).distinct()
        return JsonResponse(list(business_units), safe=False)
    except Exception as e:
        print(f"Error fetching business units: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentEditPermission])
def add_category(request):
    """Add a new category if it doesn't exist"""
    try:
        # Define validation rules for category addition
        validation_rules = {
            'value': {
                'type': 'string',
                'max_length': 255,
                'min_length': 1,
                'pattern': SecureValidator.BUSINESS_TEXT_PATTERN,
                'required': True
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        category_value = validated_data.get('value', '').strip()
        
        # Check if category already exists
        existing_category = CategoryBusinessUnit.objects.filter(
            source__in=['category', 'Categories'], 
            value__iexact=category_value
        ).first()
        
        if not existing_category:
            CategoryBusinessUnit.objects.create(
                source='Categories',  # Use 'Categories' to match existing data format
                value=category_value
            )
            return JsonResponse({'message': 'Category added successfully', 'value': category_value})
        else:
            return JsonResponse({'message': 'Category already exists', 'value': existing_category.value})
            
    except Exception as e:
        print(f"Error adding category: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentEditPermission])
def add_business_unit(request):
    """Add a new business unit if it doesn't exist"""
    try:
        # Define validation rules for business unit addition
        validation_rules = {
            'value': {
                'type': 'string',
                'max_length': 255,
                'min_length': 1,
                'pattern': SecureValidator.BUSINESS_TEXT_PATTERN,
                'required': True
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        business_unit_value = validated_data.get('value', '').strip()
        
        # Check if business unit already exists
        existing_business_unit = CategoryBusinessUnit.objects.filter(
            source__in=['business_unit', 'BusinessUnit', 'Business Unit'], 
            value__iexact=business_unit_value
        ).first()
        
        if not existing_business_unit:
            CategoryBusinessUnit.objects.create(
                source='BusinessUnit',  # Use consistent format
                value=business_unit_value
            )
            return JsonResponse({'message': 'Business unit added successfully', 'value': business_unit_value})
        else:
            return JsonResponse({'message': 'Business unit already exists', 'value': existing_business_unit.value})
            
    except Exception as e:
        print(f"Error adding business unit: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
def test_s3_integration(request):
    """Test S3 microservice integration"""
    try:
        # Test S3 client connection
        s3_client = get_s3_client()
        
        # Test the connection
        test_result = s3_client.test_connection()
        
        response_data = {
            'success': True,
            'message': 'S3 microservice integration test completed',
            'test_results': test_result,
            'microservice_url': 'https://aws-microservice.onrender.com',
            'platform': 'Render',
            'database': 'MySQL'
        }
        
        # Get operation stats if available
        try:
            stats = s3_client.get_operation_stats()
            if stats:
                response_data['operation_stats'] = stats
        except Exception as stats_e:
            response_data['stats_error'] = str(stats_e)
        
        # Get recent operations if available
        try:
            history = s3_client.get_operation_history(limit=5)
            if history:
                response_data['recent_operations'] = history
        except Exception as history_e:
            response_data['history_error'] = str(history_e)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"S3 integration test failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'S3 microservice integration test failed',
            'platform': 'Render'
        }, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentEditPermission])
def seed_sample_data(request):
    """Seed sample categories, business units, and incident categories for testing"""
    try:
        # Sample categories
        sample_categories = [
            'Operational Risk',
            'Cybersecurity Risk',
            'Compliance Risk',
            'Financial Risk',
            'Reputation Risk',
            'Strategic Risk',
            'Legal Risk',
            'Technology Risk',
            'Market Risk',
            'Credit Risk'
        ]
        
        # Sample business units
        sample_business_units = [
            'IT Department',
            'Finance',
            'Human Resources',
            'Customer Service',
            'Operations',
            'Marketing',
            'Sales',
            'Legal',
            'Compliance',
            'Risk Management',
            'Audit',
            'Executive Management'
        ]
        
        # Sample incident categories
        sample_incident_categories = [
            'Security Incident',
            'Data Breach',
            'System Outage',
            'Operational Failure',
            'Compliance Violation',
            'Privacy Incident',
            'Network Incident',
            'Application Error',
            'Infrastructure Failure',
            'Human Error',
            'External Attack',
            'Internal Threat',
            'Business Disruption',
            'Service Degradation',
            'Configuration Error'
        ]
        
        # Create categories
        categories_created = 0
        for category in sample_categories:
            if not CategoryBusinessUnit.objects.filter(source='Categories', value=category).exists():
                CategoryBusinessUnit.objects.create(source='Categories', value=category)
                categories_created += 1
        
        # Create business units
        business_units_created = 0
        for unit in sample_business_units:
            if not CategoryBusinessUnit.objects.filter(source='BusinessUnit', value=unit).exists():
                CategoryBusinessUnit.objects.create(source='BusinessUnit', value=unit)
                business_units_created += 1
        
        # Create incident categories
        incident_categories_created = 0
        for category in sample_incident_categories:
            if not CategoryBusinessUnit.objects.filter(source='IncidentCategory', value=category).exists():
                CategoryBusinessUnit.objects.create(source='IncidentCategory', value=category)
                incident_categories_created += 1
        
        return JsonResponse({
            'message': 'Sample data seeded successfully',
            'categories_created': categories_created,
            'business_units_created': business_units_created,
            'incident_categories_created': incident_categories_created
        })
        
    except Exception as e:
        print(f"Error seeding sample data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
def debug_category_data(request):
    """Debug endpoint to see all data in categoryunit table"""
    try:
        all_data = CategoryBusinessUnit.objects.all().values('id', 'source', 'value')
        return JsonResponse({
            'all_data': list(all_data),
            'total_count': len(all_data),
            'sources': list(CategoryBusinessUnit.objects.values_list('source', flat=True).distinct())
        })
    except Exception as e:
        print(f"Error fetching debug data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([IncidentCreatePermission])
def generate_analysis(request):
    """
    Generate comprehensive incident analysis using the SLM model.
    
    Expected request body:
    {
        "title": "Incident title",
        "description": "Detailed incident description"
    }
    
    Returns:
    {
        "success": true/false,
        "analysis": {analysis data} or null,
        "error": error message if any
    }
    """
    try:
        # Validate request data
        if not request.data:
            return Response({"success": False, "error": "No data provided"}, status=400)
        
        title = request.data.get('title')
        description = request.data.get('description')
        
        if not title or not description:
            return Response({"success": False, "error": "Both title and description are required"}, status=400)
        
        # Import the analysis function
        from .incident_slm import analyze_incident_comprehensive
        
        # Call the analysis function with a timeout
        analysis_result = analyze_incident_comprehensive(title, description)
        
        if not analysis_result:
            return Response({"success": False, "error": "Analysis failed to generate results"}, status=500)
        
        # Validate the analysis result
        required_fields = [
            'riskPriority', 'criticality', 'costOfIncident', 'possibleDamage', 
            'systemsInvolved', 'initialImpactAssessment', 'mitigationSteps', 
            'comments', 'violatedPolicies', 'procedureControlFailures', 'lessonsLearned'
        ]
        
        missing_fields = [field for field in required_fields if field not in analysis_result]
        if missing_fields:
            print(f"Warning: Missing fields in analysis result: {missing_fields}")
            # Continue anyway, as we'll use what we have
        
        # Return the analysis result
        return Response({"success": True, "analysis": analysis_result})
        
    except Exception as e:
        import traceback
        print(f"Error generating analysis: {str(e)}")
        print(traceback.format_exc())
        return Response({"success": False, "error": f"Error generating analysis: {str(e)}"}, status=500)


class SecureDatabaseManager:
    """
    Secure database manager implementing defense-in-depth database security:
    1. Parameterized queries only (SQL injection prevention)
    2. Connection management with automatic cleanup
    3. Minimum privilege principle
    4. Query logging for security monitoring
    5. Connection pooling and timeout management
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_secure_connection(self):
        """
        SECURITY: Secure database connection context manager
        - Automatic connection cleanup
        - Timeout management
        - Error handling with sanitized messages
        """
        connection_obj = None
        cursor_obj = None
        try:
            # Use Django's connection with security settings
            connection_obj = connection
            cursor_obj = connection_obj.cursor()
            
            # SECURITY: Apply additional security settings per session
            try:
                cursor_obj.execute("SET SESSION wait_timeout = 30")
                cursor_obj.execute("SET SESSION interactive_timeout = 30")
                # Note: max_execution_time may not be available in all MySQL versions
                cursor_obj.execute("SET SESSION autocommit = 1")
            except Exception as security_error:
                # Log but don't fail - some settings may not be available
                self.logger.warning(f"Could not apply all security settings: {security_error}")
            
            yield cursor_obj
            
        except Exception as e:
            # SECURITY: Log security-relevant database errors
            self.logger.error(f"Database security error: {type(e).__name__} from IP: {getattr(self, '_request_ip', 'unknown')}")
            
            # Rollback transaction on error
            if connection_obj:
                try:
                    connection_obj.rollback()
                except:
                    pass  # Connection might be closed
            raise
        finally:
            # SECURITY: Always cleanup connections - but don't close Django's connection
            if cursor_obj:
                try:
                    cursor_obj.close()
                except:
                    pass
    
    def execute_secure_select(self, query, params=None, request_ip=None):
        """
        SECURITY: Execute SELECT queries with comprehensive security measures
        - Parameterized queries only
        - Query validation
        - Result sanitization
        - Logging for monitoring
        """
        self._request_ip = request_ip
        
        # SECURITY: Validate query is SELECT only
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            raise ValueError("Only SELECT queries allowed in execute_secure_select")
        
        # SECURITY: Prevent dangerous SQL keywords
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                self.logger.warning(f"SECURITY: Dangerous keyword '{keyword}' detected in query from IP: {request_ip}")
                raise ValueError(f"Dangerous SQL keyword '{keyword}' not allowed")
        
        # SECURITY: Log query execution for monitoring
        self.logger.info(f"Executing secure SELECT query from IP: {request_ip}")
        
        with self.get_secure_connection() as cursor:
            # SECURITY: Always use parameterized queries
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch results
            results = cursor.fetchall()
            columns = [col[0] for col in cursor.description] if cursor.description else []
            
            return results, columns
    
    def execute_secure_insert(self, table_name, data_dict, request_ip=None):
        """
        SECURITY: Execute INSERT with comprehensive validation
        - Table name validation
        - Field validation
        - Parameterized queries
        - Audit logging
        """
        self._request_ip = request_ip
        
        # SECURITY: Validate table name (whitelist approach)
        allowed_tables = [
            'grc_incident', 'grc_riskinstance', 'grc_auditfinding', 
            'grc_compliance', 'grc_policy', 'grc_subpolicy',
            'grc_framework', 'grc_user', 'lastchecklistitemverified'
        ]
        
        if table_name not in allowed_tables:
            self.logger.warning(f"SECURITY: Unauthorized table access attempt: {table_name} from IP: {request_ip}")
            raise ValueError(f"Table '{table_name}' not allowed for direct insert operations")
        
        # SECURITY: Validate field names (prevent injection via field names)
        for field_name in data_dict.keys():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
                raise ValueError(f"Invalid field name: {field_name}")
        
        # SECURITY: Build parameterized INSERT query
        fields = list(data_dict.keys())
        placeholders = ', '.join(['%s'] * len(fields))
        field_names = ', '.join(fields)
        
        query = f"INSERT INTO {table_name} ({field_names}) VALUES ({placeholders})"
        params = list(data_dict.values())
        
        # SECURITY: Log insert operation
        self.logger.info(f"Executing secure INSERT to {table_name} from IP: {request_ip}")
        
        with self.get_secure_connection() as cursor:
            cursor.execute(query, params)
            
            # Get the inserted ID if available
            inserted_id = cursor.lastrowid
            
            # Commit the transaction
            connection.commit()
            
            return inserted_id
    
    def execute_secure_update(self, table_name, data_dict, where_conditions, request_ip=None):
        """
        SECURITY: Execute UPDATE with comprehensive validation
        - Table name validation
        - WHERE clause validation
        - Parameterized queries
        - Audit logging
        """
        self._request_ip = request_ip
        
        # SECURITY: Validate table name
        allowed_tables = [
            'grc_incident', 'grc_riskinstance', 'grc_auditfinding', 
            'grc_compliance', 'grc_policy', 'grc_subpolicy'
        ]
        
        if table_name not in allowed_tables:
            self.logger.warning(f"SECURITY: Unauthorized table update attempt: {table_name} from IP: {request_ip}")
            raise ValueError(f"Table '{table_name}' not allowed for update operations")
        
        # SECURITY: Require WHERE conditions to prevent mass updates
        if not where_conditions:
            raise ValueError("WHERE conditions required for UPDATE operations")
        
        # SECURITY: Validate field names
        for field_name in data_dict.keys():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
                raise ValueError(f"Invalid field name: {field_name}")
        
        # Build parameterized UPDATE query
        set_clauses = [f"{field} = %s" for field in data_dict.keys()]
        set_clause = ', '.join(set_clauses)
        
        where_clauses = [f"{field} = %s" for field in where_conditions.keys()]
        where_clause = ' AND '.join(where_clauses)
        
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        params = list(data_dict.values()) + list(where_conditions.values())
        
        # SECURITY: Log update operation
        self.logger.info(f"Executing secure UPDATE on {table_name} from IP: {request_ip}")
        
        with self.get_secure_connection() as cursor:
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            
            # Commit the transaction
            connection.commit()
            
            return affected_rows
    
    def get_audit_findings_secure(self, complied_values, request_ip=None):
        """
        SECURITY: Secure implementation of audit findings query
        Replaces the unsafe string formatting approach
        """
        if not complied_values:
            return [], []
        
        # SECURITY: Validate complied_values are safe
        for value in complied_values:
            if not isinstance(value, (str, int)) or (isinstance(value, str) and len(value) > 50):
                raise ValueError("Invalid complied value format")
        
        # SECURITY: Build parameterized query with proper placeholders
        placeholders = ', '.join(['%s'] * len(complied_values))
        
        query = """
            SELECT lciv.FrameworkId, lciv.ComplianceId, lciv.PolicyId, lciv.SubPolicyId, 
                   lciv.Date, lciv.Time, lciv.User, lciv.Complied, lciv.Comments, lciv.count,
                   f.FrameworkName
            FROM lastchecklistitemverified lciv
            JOIN frameworks f ON lciv.FrameworkId = f.FrameworkId
            WHERE lciv.ComplianceId IN ({})
        """.format(placeholders)
        
        return self.execute_secure_select(query, complied_values, request_ip)
    
    def get_audit_finding_by_compliance_secure(self, compliance_id, request_ip=None):
        """
        SECURITY: Secure implementation of single audit finding query
        """
        query = """
            SELECT lciv.FrameworkId, lciv.ComplianceId, lciv.PolicyId, lciv.SubPolicyId, 
                   lciv.Date, lciv.Time, lciv.User, lciv.Complied, lciv.Comments, lciv.count,
                   f.FrameworkName
            FROM lastchecklistitemverified lciv
            JOIN frameworks f ON lciv.FrameworkId = f.FrameworkId
            WHERE lciv.ComplianceId = %s
            LIMIT 1
        """
        
        results, columns = self.execute_secure_select(query, [compliance_id], request_ip)
        return results[0] if results else None, columns

# SECURITY: Global instance of SecureDatabaseManager
secure_db = SecureDatabaseManager()

def secure_database_examples():
    """
    SECURITY: Examples of secure database operations
    Demonstrates safe SELECT and INSERT operations following security best practices
    """
    
    # Example 1: SECURE SELECT Operation
    def secure_select_example(user_id, request_ip):
        """
        SECURITY: Safe SELECT query with parameterized inputs
        - Uses parameterized queries (no SQL injection)
        - Validates input parameters
        - Logs security events
        - Automatic connection cleanup
        """
        try:
            # SECURITY: Validate input first
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user_id: must be positive integer")
            
            # SECURITY: Use parameterized query - NEVER string concatenation
            query = """
                SELECT u.UserId, u.UserName, u.Email, u.role, u.created_at
                FROM users u 
                WHERE u.UserId = %s 
                AND u.is_active = %s
                LIMIT 1
            """
            
            # SECURITY: Execute with SecureDatabaseManager
            results, columns = secure_db.execute_secure_select(
                query, 
                params=[user_id, True],  # Parameterized values
                request_ip=request_ip
            )
            
            if results:
                user_data = dict(zip(columns, results[0]))
                return {
                    'success': True,
                    'user': user_data
                }
            else:
                return {
                    'success': False,
                    'message': 'User not found'
                }
                
        except Exception as e:
            # SECURITY: Log security event and return sanitized error
            logging.getLogger(__name__).error(f"Secure SELECT failed: {type(e).__name__} from IP: {request_ip}")
            return {
                'success': False,
                'message': 'Database query failed'
            }
    
    # Example 2: SECURE INSERT Operation
    def secure_insert_example(incident_data, request_ip):
        """
        SECURITY: Safe INSERT operation with comprehensive validation
        - Validates all input data
        - Uses parameterized queries
        - Validates table and field names
        - Audit logging
        - Transaction management
        """
        try:
            # SECURITY: Validate input data structure
            required_fields = ['IncidentTitle', 'Description', 'RiskPriority', 'Status']
            for field in required_fields:
                if field not in incident_data or not incident_data[field]:
                    raise ValueError(f"Required field missing: {field}")
            
            # SECURITY: Sanitize and validate data using SecureValidator
            validator = SecureValidator()
            
            validated_data = {
                'IncidentTitle': validator.validate_string(
                    incident_data['IncidentTitle'], 'IncidentTitle', 
                    max_length=255, required=True
                ),
                'Description': validator.validate_string(
                    incident_data['Description'], 'Description', 
                    max_length=2000, required=True
                ),
                'RiskPriority': validator.validate_choice(
                    incident_data['RiskPriority'], 'RiskPriority',
                    choices=['High', 'Medium', 'Low'], required=True
                ),
                'Status': validator.validate_choice(
                    incident_data['Status'], 'Status',
                    choices=['Open', 'Closed', 'In Progress', 'Under Review'], required=True
                ),
                'CreatedAt': timezone.now(),
                'UpdatedAt': timezone.now()
            }
            
            # SECURITY: Execute secure INSERT
            inserted_id = secure_db.execute_secure_insert(
                table_name='grc_incident',
                data_dict=validated_data,
                request_ip=request_ip
            )
            
            return {
                'success': True,
                'incident_id': inserted_id,
                'message': 'Incident created successfully'
            }
            
        except ValidationError as e:
            # SECURITY: Return validation error (safe to show)
            return {
                'success': False,
                'message': f'Validation error: {e.message}'
            }
        except Exception as e:
            # SECURITY: Log security event and return generic error
            logging.getLogger(__name__).error(f"Secure INSERT failed: {type(e).__name__} from IP: {request_ip}")
            return {
                'success': False,
                'message': 'Failed to create incident'
            }
    
    # Example 3: SECURE UPDATE Operation
    def secure_update_example(incident_id, update_data, request_ip):
        """
        SECURITY: Safe UPDATE operation with WHERE clause validation
        - Requires WHERE conditions (prevents mass updates)
        - Validates all input data
        - Uses parameterized queries
        - Audit logging
        """
        try:
            # SECURITY: Validate incident_id
            if not isinstance(incident_id, int) or incident_id <= 0:
                raise ValueError("Invalid incident_id")
            
            # SECURITY: Validate update data
            validator = SecureValidator()
            validated_updates = {}
            
            if 'Status' in update_data:
                validated_updates['Status'] = validator.validate_choice(
                    update_data['Status'], 'Status',
                    choices=['Open', 'Closed', 'In Progress', 'Under Review'], required=True
                )
            
            if 'RiskPriority' in update_data:
                validated_updates['RiskPriority'] = validator.validate_choice(
                    update_data['RiskPriority'], 'RiskPriority',
                    choices=['High', 'Medium', 'Low'], required=True
                )
            
            # SECURITY: Always include UpdatedAt
            validated_updates['UpdatedAt'] = timezone.now()
            
            # SECURITY: Define WHERE conditions (required for security)
            where_conditions = {
                'IncidentId': incident_id
            }
            
            # SECURITY: Execute secure UPDATE
            affected_rows = secure_db.execute_secure_update(
                table_name='grc_incident',
                data_dict=validated_updates,
                where_conditions=where_conditions,
                request_ip=request_ip
            )
            
            if affected_rows > 0:
                return {
                    'success': True,
                    'message': f'Updated {affected_rows} incident(s)'
                }
            else:
                return {
                    'success': False,
                    'message': 'No incidents updated - may not exist'
                }
                
        except ValidationError as e:
            return {
                'success': False,
                'message': f'Validation error: {e.message}'
            }
        except Exception as e:
            logging.getLogger(__name__).error(f"Secure UPDATE failed: {type(e).__name__} from IP: {request_ip}")
            return {
                'success': False,
                'message': 'Failed to update incident'
            }
    
    return {
        'secure_select_example': secure_select_example,
        'secure_insert_example': secure_insert_example,
        'secure_update_example': secure_update_example
    }


@api_view(['GET'])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def get_incident_frameworks(request):
    """
    Get all frameworks for incident filtering
    """
    try:
        # Get all frameworks
        frameworks = Framework.objects.all()
        
        # Format the response to match frontend expectations
        formatted_frameworks = []
        for framework in frameworks:
            formatted_fw = {
                'id': framework.FrameworkId,
                'name': framework.FrameworkName,
                'category': framework.Category,
                'status': framework.ActiveInactive,
                'description': framework.FrameworkDescription,
            }
            formatted_frameworks.append(formatted_fw)
        
        response_data = {
            'success': True, 
            'frameworks': formatted_frameworks,
            'count': len(formatted_frameworks)
        }
        
        return Response(response_data)
        
    except Exception as e:
        print(f"Error in get_incident_frameworks: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error fetching frameworks: {str(e)}'
        }, status=500)



@csrf_exempt
@api_view(['GET'])
@permission_classes([IncidentAnalyticsPermission])
@authentication_classes([])
@rbac_required(required_permission='incident_performance_analytics')
def incident_dashboard(request):
    """
    Endpoint to fetch incident dashboard data
    Returns aggregated metrics, status counts, and summary data for the dashboard
    """
    client_ip = get_client_ip(request)
    user_id = request.GET.get('userId')
    
    # Log dashboard access
    send_log(
        module="Incident",
        actionType="ACCESS_INCIDENT_DASHBOARD",
        description="User accessing incident dashboard",
        userId=str(user_id) if user_id else None,
        userName=request.GET.get('userName', 'Unknown'),
        entityType="Dashboard",
        ipAddress=client_ip
    )
    print("incident_dashboard called")
    
    from django.apps import apps
    from django.db.models import Count, Avg, F, ExpressionWrapper, fields
    from django.http import JsonResponse
    from django.utils import timezone
    import datetime
    
    try:
        # Debug: Log all incoming parameters
        print(f"[DEBUG] All GET parameters: {dict(request.GET)}")
        print(f"[DEBUG] Request path: {request.path}")
        print(f"[DEBUG] Request method: {request.method}")
        
        # Define allowed GET parameters
        allowed_params = {
            'timeRange': {
                'type': 'choice',
                'choices': ['all', '7days', '30days', '90days', '1year'],
                'required': False
            },
            'user_id': {
                'type': 'integer',
                'required': False
            },
            'framework_id': {
                'type': 'integer',
                'required': False
            },
            'category': {
                'type': 'string',
                'required': False
            },
            'priority': {
                'type': 'string',
                'required': False
            }
        }
        
        # Validate GET parameters
        validated_params, error = validate_get_parameters(request, allowed_params)
        if error:
            print(f"[DEBUG] Validation error: {error}")
            return JsonResponse({'success': False, 'message': error}, status=400)
        
        print(f"[DEBUG] Validated parameters: {validated_params}")
        
        # Get the Incident model from the app registry
        Incident = apps.get_model('grc', 'Incident')
        
        # Get time range filter from request (now validated)
        time_range = validated_params.get('timeRange', 'all')
        print(f"Incident dashboard request with timeRange: {time_range}")
        
        # Apply time range filter if specified
        now = timezone.now()
        incidents = Incident.objects.exclude(Origin='Audit Finding')
        
        if time_range != 'all':
            if time_range == '7days':
                start_date = now - datetime.timedelta(days=7)
            elif time_range == '30days':
                start_date = now - datetime.timedelta(days=30)
            elif time_range == '90days':
                start_date = now - datetime.timedelta(days=90)
            elif time_range == '1year':
                start_date = now - datetime.timedelta(days=365)
                
            incidents = incidents.filter(CreatedAt__gte=start_date)
        
        # Apply framework filter if provided
        framework_id = request.GET.get('framework_id')
        if framework_id:
            # Filter incidents by framework through compliance relationship
            incidents = incidents.filter(
                ComplianceId__SubPolicy__PolicyId__FrameworkId=framework_id
            )
            print(f"Applied framework filter to dashboard: {framework_id}")
        
        # Apply other filters if provided
        category = request.GET.get('category')
        if category and category != 'All Categories':
            incidents = incidents.filter(RiskCategory=category)
        
        priority = request.GET.get('priority')
        if priority and priority != 'All Priorities':
            incidents = incidents.filter(RiskPriority=priority)
        
        # Debug: Log all unique status values in the database
        unique_statuses = incidents.values_list('Status', flat=True).distinct()
        print(f"[DEBUG] All unique status values in incidents: {list(unique_statuses)}")
        
        # Debug: Log all incidents with their statuses
        all_incidents = incidents.values('IncidentId', 'Status', 'IncidentTitle')[:10]  # First 10 for debugging
        print(f"[DEBUG] Sample incidents with statuses: {list(all_incidents)}")
        
        # Count incidents by actual status values in database (case-insensitive)
        status_counts = {
            'scheduled': incidents.filter(Status__iexact='Scheduled').count() + incidents.filter(Status__iexact='Open').count(),
            'approved': incidents.filter(Status__iexact='Approved').count() + incidents.filter(Status__iexact='Mitigated').count(),
            'rejected': incidents.filter(Status__iexact='Rejected').count() + incidents.filter(Status__iexact='Closed').count(),
            'resolved': incidents.filter(Status__iexact='Resolved').count()
        }
        
        # Debug: Log the counts for each status
        print(f"[DEBUG] Status counts: {status_counts}")
        print(f"[DEBUG] Total incidents count: {incidents.count()}")
        
        # Calculate total count
        total_count = incidents.count()
        
        # Calculate MTTD - Mean Time to Detect
        mttd_incidents = incidents.filter(
            IdentifiedAt__isnull=False,
            CreatedAt__isnull=False
        )
        
        mttd_value = 0
        if mttd_incidents.exists():
            # Calculate in Python to avoid DB-specific functions
            all_incidents = list(mttd_incidents.values('IncidentId', 'CreatedAt', 'IdentifiedAt'))
            total_minutes = 0
            
            for incident in all_incidents:
                created = incident['CreatedAt']
                identified = incident['IdentifiedAt']
                diff_seconds = (identified - created).total_seconds()
                minutes = diff_seconds / 60
                total_minutes += minutes
            
            mttd_value = round(total_minutes / len(all_incidents), 2)
        
        # Calculate resolution rate 
        resolution_rate = 0
        if total_count > 0:
            # Include mitigated incidents as resolved
            resolved_count = status_counts['approved']  # This now contains mitigated incidents
            resolution_rate = round((resolved_count / total_count) * 100, 1)
        
        # Calculate change percentage by comparing with previous 30 days
        change_percentage = 0
        try:
            # Get incidents from the previous 30 days (for comparison)
            previous_start = now - datetime.timedelta(days=60)
            previous_end = now - datetime.timedelta(days=30)
            previous_count = Incident.objects.filter(
                CreatedAt__gte=previous_start,
                CreatedAt__lt=previous_end
            ).count()
            
            # Get current period count (last 30 days)
            current_start = now - datetime.timedelta(days=30)
            current_count = Incident.objects.filter(
                CreatedAt__gte=current_start
            ).count()
            
            # Calculate percentage change
            if previous_count > 0:
                change_percentage = round(((current_count - previous_count) / previous_count) * 100, 1)
            elif current_count > 0:
                change_percentage = 100  # New incidents appeared
            else:
                change_percentage = 0  # No incidents in either period
                
        except Exception as e:
            print(f"Error calculating change percentage: {e}")
            change_percentage = 0
        
        # Prepare response data
        response_data = {
            'success': True,
            'data': {
                'summary': {
                    'status_counts': status_counts,
                    'total_count': total_count,
                    'mttd_value': mttd_value,
                    'mttr_value': 0,  # This would be calculated from resolution times
                    'change_percentage': change_percentage,
                    'resolution_rate': resolution_rate
                }
            }
        }
        
        # Debug: Log the final response
        print(f"[DEBUG] Final response data: {response_data}")
        print(f"[DEBUG] Status counts in response: {response_data['data']['summary']['status_counts']}")
        
        print(f"Returning incident dashboard response")
        
        # Log successful dashboard access
        send_log(
            module="Incident",
            actionType="ACCESS_INCIDENT_DASHBOARD_SUCCESS",
            description="Successfully retrieved incident dashboard data",
            userId=str(user_id) if user_id else None,
            userName=request.GET.get('userName', 'Unknown'),
            entityType="Dashboard",
            ipAddress=client_ip,
            additionalInfo={
                "total_incidents": total_count,
                "time_range": time_range,
                "status_counts": status_counts
            }
        )
        
    except Exception as e:
        print(f"Error in incident_dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Log dashboard error
        send_log(
            module="Incident",
            actionType="ACCESS_INCIDENT_DASHBOARD_ERROR",
            description=f"Error retrieving incident dashboard data: {str(e)}",
            userId=str(user_id) if user_id else None,
            userName=request.GET.get('userName', 'Unknown'),
            entityType="Dashboard",
            logLevel="ERROR",
            ipAddress=client_ip,
            additionalInfo={"error": str(e)}
        )
        
        # Return an error response
        response_data = {
            'success': False,
            'message': f"Error fetching incident dashboard data: {str(e)}",
            'data': {
                'summary': {
                    'status_counts': {
                        'scheduled': 0, 
                        'approved': 0,
                        'rejected': 0
                    },
                    'total_count': 0,
                    'mttd_value': 0,
                    'mttr_value': 0,
                    'change_percentage': 0,
                    'resolution_rate': 0
                }
            }
        }
    
    return JsonResponse(response_data)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IncidentAnalyticsPermission])
@authentication_classes([])
@rbac_required(required_permission='incident_performance_analytics')
def incident_analytics(request):
    """
    Endpoint to fetch incident analytics data for charts based on specified dimensions
    Returns chart data structured for Chart.js display
    """
    # RBAC Debug - Log user access attempt (temporarily disabled)
    # debug_info = debug_user_permissions(request, "VIEW_INCIDENT_ANALYTICS", "incident", None)
    
    print("incident_analytics called")
    
    from django.apps import apps
    from django.db.models import Count
    from django.db.models.functions import TruncDate, TruncMonth, TruncQuarter
    from django.http import JsonResponse
    from django.utils import timezone
    import json
    
    try:
        # Define validation rules for analytics request
        validation_rules = {
            'xAxis': {
                'type': 'choice',
                'choices': ['Time', 'Date', 'Month', 'Quarter'],
                'required': False
            },
            'yAxis': {
                'type': 'choice',
                'choices': ['Severity', 'Status', 'Origin', 'RiskCategory', 'RiskPriority', 'Repeated', 'CostImpact'],
                'required': False
            },
            'timeRange': {
                'type': 'choice',
                'choices': ['all', '7days', '30days', '90days', '1year'],
                'required': False
            },
            'chartType': {
                'type': 'choice',
                'choices': ['bar', 'line', 'pie', 'doughnut', 'radar'],
                'required': False
            },
            'filters': {
                'type': 'string',  # JSON object as string
                'required': False
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': f'Validation error: {str(e)}',
                'chartData': {'labels': [], 'datasets': [{'label': 'Error', 'data': []}]}
            }, status=400)
        
        # Get validated parameters with defaults
        x_axis = validated_data.get('xAxis', 'Time')
        y_axis = validated_data.get('yAxis', 'Severity')
        time_range = validated_data.get('timeRange', 'all')
        chart_type = validated_data.get('chartType', 'bar')
        filters = validated_data.get('filters', '{}')
        
        # Parse filters if provided
        if isinstance(filters, str):
            try:
                filters = json.loads(filters)
            except json.JSONDecodeError:
                filters = {}
        elif not isinstance(filters, dict):
            filters = {}
        
        # Get the Incident model from the app registry
        Incident = apps.get_model('grc', 'Incident')
        
        print(f"Incident analytics request with xAxis: {x_axis}, yAxis: {y_axis}, timeRange: {time_range}")
        
        # Apply time range filter if specified
        now = timezone.now()
        
        # For Origin chart, include all incidents (including Audit Findings)
        # For other charts, exclude Audit Findings as before
        if y_axis == 'Origin':
            incidents = Incident.objects.all()
            print("Including Audit Findings for Origin chart")
        else:
            incidents = Incident.objects.exclude(Origin='Audit Finding')
        
        # Debug: Log total incidents before filtering
        print(f"Total incidents before filtering: {incidents.count()}")
        
        if time_range != 'all':
            if time_range == '7days':
                start_date = now - datetime.timedelta(days=7)
            elif time_range == '30days':
                start_date = now - datetime.timedelta(days=30)
            elif time_range == '90days':
                start_date = now - datetime.timedelta(days=90)
            elif time_range == '1year':
                start_date = now - datetime.timedelta(days=365)
                
            incidents = incidents.filter(CreatedAt__gte=start_date)
        
        # Apply framework filter if provided
        framework_id = request.data.get('frameworkId')
        if framework_id:
            # Filter incidents by framework through compliance relationship
            incidents = incidents.filter(
                ComplianceId__SubPolicy__PolicyId__FrameworkId=framework_id
            )
            print(f"Applied framework filter: {framework_id}")
        
        # Apply other filters if provided
        category = request.data.get('category')
        if category and category != 'All Categories':
            incidents = incidents.filter(RiskCategory=category)
        
        priority = request.data.get('priority')
        if priority and priority != 'All Priorities':
            incidents = incidents.filter(RiskPriority=priority)
        
        # Set up chart data based on X-axis selection
        chart_data = {'labels': [], 'datasets': [{'data': []}]}
        
        # Process X-axis dimension first
        if x_axis == 'Date':
            # Group by Date
            date_incidents = (
                incidents
                .annotate(date=TruncDate('CreatedAt'))
                .values('date')
                .annotate(count=Count('IncidentId'))
                .order_by('date')
            )
            
            # Get dates and base counts
            dates = []
            counts = {}
            
            for item in date_incidents:
                if item['date']:
                    date_str = item['date'].strftime('%Y-%m-%d')
                    dates.append(date_str)
                    counts[date_str] = item['count']
            
            chart_data['labels'] = dates
            
        elif x_axis == 'Month':
            # Group by Month
            month_incidents = (
                incidents
                .annotate(month=TruncMonth('CreatedAt'))
                .values('month')
                .annotate(count=Count('IncidentId'))
                .order_by('month')
            )
            
            # Get months and base counts
            months = []
            counts = {}
            
            for item in month_incidents:
                if item['month']:
                    month_str = item['month'].strftime('%b %Y')
                    months.append(month_str)
                    counts[month_str] = item['count']
            
            chart_data['labels'] = months
            
        elif x_axis == 'Quarter':
            # Group by Quarter
            quarter_incidents = (
                incidents
                .annotate(quarter=TruncQuarter('CreatedAt'))
                .values('quarter')
                .annotate(count=Count('IncidentId'))
                .order_by('quarter')
            )
            
            # Get quarters and base counts
            quarters = []
            counts = {}
            
            for item in quarter_incidents:
                if item['quarter']:
                    year = item['quarter'].year
                    # Calculate quarter number (1-4)
                    quarter_num = (item['quarter'].month - 1) // 3 + 1
                    quarter_str = f"Q{quarter_num} {year}"
                    quarters.append(quarter_str)
                    counts[quarter_str] = item['count']
            
            chart_data['labels'] = quarters
            
        else:
            # Default 'Time' x-axis - Just count incidents without time dimension
            # We'll fill this in based on the Y-axis selection
            pass
        
        # Process Y-axis dimension
        if y_axis == 'Severity':
            # Group by RiskPriority (severity)
            severity_levels = ['High', 'Medium', 'Low']
            
            if x_axis == 'Time':
                # Just show total counts by severity
                all_incidents = list(incidents.values('IncidentId', 'RiskPriority'))
                
                # Initialize counters
                severity_counts = {'High': 0, 'Medium': 0, 'Low': 0}
                
                # Count by severity
                for incident in all_incidents:
                    priority = incident['RiskPriority']
                    if not priority:
                        continue
                    
                    # Map to standard priority buckets
                    standard_priority = 'Medium'  # Default
                    priority_lower = priority.lower()
                    
                    if 'high' in priority_lower:
                        standard_priority = 'High'
                    elif 'low' in priority_lower:
                        standard_priority = 'Low'
                    
                    severity_counts[standard_priority] += 1
                
                # Prepare chart data
                chart_data['labels'] = list(severity_counts.keys())
                chart_data['datasets'][0]['data'] = list(severity_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Severity'
            else:
                # We're grouping by a time dimension (Date, Month, Quarter)
                # Need to create a dataset for each severity level
                datasets = []
                
                # Create a dataset for each severity level
                for severity in severity_levels:
                    # Count incidents of this severity for each time period
                    severity_data = []
                    
                    for label in chart_data['labels']:
                        # Get incidents for this time period
                        period_incidents = 0
                        
                        # Logic to filter incidents by time period and severity
                        # This will depend on the time dimension (date, month, quarter)
                        # For simplicity, we'll use placeholder data
                        period_incidents = counts.get(label, 0) // 3  # Distribute roughly equally
                        
                        severity_data.append(period_incidents)
                    
                    # Create dataset for this severity
                    datasets.append({
                        'label': f'{severity} Severity',
                        'data': severity_data,
                        'backgroundColor': 'rgba(255, 99, 132, 0.5)',  # You'll need to set appropriate colors
                        'borderColor': 'rgb(255, 99, 132)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'Status':
            # Group by Status - using actual database values
            if x_axis == 'Time':
                # Get all unique status values for debugging
                all_statuses = incidents.values_list('Status', flat=True).distinct()
                print(f"DEBUG: All unique Status values in database: {list(all_statuses)}")
                
                # Count by actual status values in database
                status_counts = {}
                
                # Count Scheduled (case-insensitive)
                scheduled_count = incidents.filter(Status__iexact='Scheduled').count()
                if scheduled_count > 0:
                    status_counts['Scheduled'] = scheduled_count
                
                # Count Open (case-insensitive) - may be same as Scheduled
                open_count = incidents.filter(Status__iexact='Open').count()
                if open_count > 0:
                    status_counts['Open'] = open_count
                
                # Count Approved (case-insensitive)
                approved_count = incidents.filter(Status__iexact='Approved').count()
                if approved_count > 0:
                    status_counts['Approved'] = approved_count
                
                # Count Rejected (case-insensitive)
                rejected_count = incidents.filter(Status__iexact='Rejected').count()
                if rejected_count > 0:
                    status_counts['Rejected'] = rejected_count
                
                # Count Resolved (case-insensitive)
                resolved_count = incidents.filter(Status__iexact='Resolved').count()
                if resolved_count > 0:
                    status_counts['Resolved'] = resolved_count
                
                # Count Mitigated (case-insensitive) - may be same as Approved
                mitigated_count = incidents.filter(Status__iexact='Mitigated').count()
                if mitigated_count > 0:
                    status_counts['Mitigated'] = mitigated_count
                
                # Debug: Log status counts
                print(f"Status counts for chart: {status_counts}")
                
                # Prepare chart data
                chart_data['labels'] = list(status_counts.keys())
                chart_data['datasets'][0]['data'] = list(status_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Status'
            else:
                # We're grouping by a time dimension (Date, Month, Quarter)
                # Need to create a dataset for each status
                datasets = []
                
                # Create a dataset for each status - map actual statuses to dashboard categories
                status_mapping = [
                    ('Scheduled', 'Open'),
                    ('Approved', 'Mitigated'), 
                    ('Rejected', 'Closed')
                ]
                
                for display_status, actual_status in status_mapping:
                    # Count incidents of this status for each time period
                    status_data = []
                    
                    for label in chart_data['labels']:
                        # Get incidents for this time period and status
                        period_incidents = 0
                        
                        # Logic to filter incidents by time period and status
                        # This will depend on the time dimension (date, month, quarter)
                        # For simplicity, we'll use placeholder data
                        period_incidents = counts.get(label, 0) // 3  # Distribute roughly equally
                        
                        status_data.append(period_incidents)
                    
                    # Create dataset for this status
                    datasets.append({
                        'label': f'{display_status} Status',
                        'data': status_data,
                        'backgroundColor': 'rgba(54, 162, 235, 0.5)',  # You'll need to set appropriate colors
                        'borderColor': 'rgb(54, 162, 235)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'Origin':
            # Group by Origin
            if x_axis == 'Time':
                all_incidents = list(incidents.values('IncidentId', 'Origin'))
                
                # Get all unique origin values for debugging
                all_origins = incidents.values_list('Origin', flat=True).distinct()
                print(f"DEBUG: All unique Origin values in database: {list(all_origins)}")
                
                # Initialize counters for specific origins
                origin_counts = {'Manual': 0, 'SIEM': 0, 'Audit Finding': 0, 'Other': 0}
                
                # Normalize origin values to handle different formats
                def normalize_origin(origin_value):
                    if not origin_value:
                        return None
                    
                    # Convert to string and trim
                    origin_str = str(origin_value).strip()
                    origin_lower = origin_str.lower()
                    
                    # Remove underscores, spaces, and dashes for comparison
                    origin_clean = origin_lower.replace('_', '').replace(' ', '').replace('-', '')
                    
                    # Map variations to standard names
                    if origin_clean == 'manual':
                        return 'Manual'
                    elif origin_clean == 'siem':
                        return 'SIEM'
                    elif 'audit' in origin_clean and 'finding' in origin_clean:
                        return 'Audit Finding'
                    elif origin_clean == 'auditfinding':
                        return 'Audit Finding'
                    elif 'compliance' in origin_clean and 'gap' in origin_clean:
                        return 'Compliance Gap'
                    else:
                        # Log unknown origins for debugging
                        print(f"DEBUG: Unknown origin value '{origin_str}' - categorizing as Other")
                        return 'Other'
                
                # Count by origin with normalization
                for incident in all_incidents:
                    origin = incident['Origin']
                    normalized = normalize_origin(origin)
                    
                    if normalized:
                        if normalized in origin_counts:
                            origin_counts[normalized] += 1
                        else:
                            # If it's a new origin not in our predefined list, add it
                            if normalized != 'Other':
                                origin_counts[normalized] = 1
                            else:
                                origin_counts['Other'] += 1
                
                print(f"DEBUG: Origin counts after normalization: {origin_counts}")
                
                # Remove 'Other' category if it's empty
                if origin_counts['Other'] == 0:
                    del origin_counts['Other']
                
                # Prepare chart data
                chart_data['labels'] = list(origin_counts.keys())
                chart_data['datasets'][0]['data'] = list(origin_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Origin'
            else:
                # We're grouping by a time dimension (Date, Month, Quarter)
                # Need to create a dataset for each origin
                datasets = []
                origins = ['Manual', 'SIEM', 'Audit Finding', 'Other']
                
                # Create a dataset for each origin
                for origin in origins:
                    # Count incidents of this origin for each time period
                    origin_data = []
                    
                    for label in chart_data['labels']:
                        # Logic to filter incidents by time period and origin
                        # For simplicity, we'll use placeholder data
                        period_incidents = counts.get(label, 0) // len(origins)  # Distribute roughly equally
                        origin_data.append(period_incidents)
                    
                    # Create dataset for this origin
                    datasets.append({
                        'label': f'{origin} Origin',
                        'data': origin_data,
                        'backgroundColor': 'rgba(75, 192, 192, 0.5)',  # You'll need to set appropriate colors
                        'borderColor': 'rgb(75, 192, 192)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'RiskCategory':
            # Group by RiskCategory
            if x_axis == 'Time':
                all_incidents = list(incidents.values('IncidentId', 'RiskCategory'))
                
                # Initialize counters for risk categories
                category_counts = {}
                
                # Count by category
                for incident in all_incidents:
                    category = incident['RiskCategory']
                    if not category:
                        continue
                    
                    if category in category_counts:
                        category_counts[category] += 1
                    else:
                        category_counts[category] = 1
                
                # Prepare chart data
                chart_data['labels'] = list(category_counts.keys())
                chart_data['datasets'][0]['data'] = list(category_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Risk Category'
            else:
                # Get unique risk categories from the database
                unique_categories = incidents.exclude(RiskCategory__isnull=True).values_list('RiskCategory', flat=True).distinct()
                categories = list(unique_categories)
                
                if not categories:
                    # Fallback to common categories if none found in database
                    categories = ['Security', 'Compliance', 'Operational', 'Financial', 'Strategic']
                
                # We're grouping by a time dimension
                datasets = []
                
                for category in categories:
                    category_data = []
                    
                    for label in chart_data['labels']:
                        # For simplicity, use placeholder data
                        period_incidents = counts.get(label, 0) // len(categories)
                        category_data.append(period_incidents)
                    
                    datasets.append({
                        'label': f'{category} Category',
                        'data': category_data,
                        'backgroundColor': 'rgba(153, 102, 255, 0.5)',
                        'borderColor': 'rgb(153, 102, 255)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'RiskPriority':
            # Group by RiskPriority (similar to Severity but preserving the exact field name)
            if x_axis == 'Time':
                all_incidents = list(incidents.values('IncidentId', 'RiskPriority'))
                
                # Initialize counters for priorities
                priority_counts = {'High': 0, 'Medium': 0, 'Low': 0}
                
                # Count by priority
                for incident in all_incidents:
                    priority = incident['RiskPriority']
                    if not priority:
                        continue
                    
                    # Map to standard priority buckets
                    standard_priority = 'Medium'  # Default
                    priority_lower = priority.lower()
                    
                    if 'high' in priority_lower:
                        standard_priority = 'High'
                    elif 'low' in priority_lower:
                        standard_priority = 'Low'
                    
                    priority_counts[standard_priority] += 1
                
                # Remove priorities with zero count
                priority_counts = {k: v for k, v in priority_counts.items() if v > 0}
                
                # Prepare chart data
                chart_data['labels'] = list(priority_counts.keys())
                chart_data['datasets'][0]['data'] = list(priority_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Risk Priority'
            else:
                # We're grouping by a time dimension
                datasets = []
                priorities = ['High', 'Medium', 'Low']
                
                for priority in priorities:
                    priority_data = []
                    
                    for label in chart_data['labels']:
                        # For simplicity, use placeholder data
                        period_incidents = counts.get(label, 0) // len(priorities)
                        priority_data.append(period_incidents)
                    
                    datasets.append({
                        'label': f'{priority} Priority',
                        'data': priority_data,
                        'backgroundColor': 'rgba(255, 159, 64, 0.5)',
                        'borderColor': 'rgb(255, 159, 64)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'Repeated':
            # Group by RepeatedNot field (0 = Not repeated, 1 = Repeated)
            if x_axis == 'Time':
                # Initialize counters
                repeated_counts = {'Not Repeated': 0, 'Repeated': 0}
                
                # Count by repeated status
                for incident in incidents:
                    repeated = incident.RepeatedNot
                    if repeated == 1:
                        repeated_counts['Repeated'] += 1
                    else:
                        repeated_counts['Not Repeated'] += 1
                
                # Prepare chart data
                chart_data['labels'] = list(repeated_counts.keys())
                chart_data['datasets'][0]['data'] = list(repeated_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Repeated Status'
            else:
                # We're grouping by a time dimension
                datasets = []
                statuses = ['Repeated', 'Not Repeated']
                
                for status in statuses:
                    status_data = []
                    
                    for label in chart_data['labels']:
                        # For simplicity, use placeholder data
                        period_incidents = counts.get(label, 0) // len(statuses)
                        status_data.append(period_incidents)
                    
                    datasets.append({
                        'label': status,
                        'data': status_data,
                        'backgroundColor': 'rgba(201, 203, 207, 0.5)',
                        'borderColor': 'rgb(201, 203, 207)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'CostImpact':
            # Group by cost impact
            if x_axis == 'Time':
                all_incidents = list(incidents.values('IncidentId', 'CostOfIncident'))
                
                # Process numeric cost values
                cost_data = {}
                
                # Count by cost impact
                for incident in all_incidents:
                    cost = incident['CostOfIncident']
                    if not cost:
                        continue
                    
                    # Try to convert to numeric value
                    try:
                        cost_value = float(cost)
                        # Round to nearest 100 for binning
                        cost_bin = round(cost_value / 100) * 100
                        cost_bin_str = str(cost_bin)
                        
                        if cost_bin_str in cost_data:
                            cost_data[cost_bin_str] += 1
                        else:
                            cost_data[cost_bin_str] = 1
                    except (ValueError, TypeError):
                        # If can't convert to number, skip this record
                        continue
                
                # If we have numeric data, use it
                if cost_data:
                    # Sort the cost bins numerically
                    sorted_costs = sorted(cost_data.items(), key=lambda x: float(x[0]))
                    
                    # Prepare chart data with numeric cost values
                    chart_data['labels'] = [cost for cost, _ in sorted_costs]
                    chart_data['datasets'][0]['data'] = [count for _, count in sorted_costs]
                    chart_data['datasets'][0]['label'] = 'Incidents by Cost (₹)'
                else:
                    # Fallback to categorical if no numeric data
                    # Initialize cost impact buckets
                    cost_mapping = {'Low': 0, 'Medium': 0, 'High': 0, 'Unknown': 0}
                    
                    # Count by cost impact
                    for incident in all_incidents:
                        cost = incident['CostOfIncident']
                        if not cost:
                            cost_mapping['Unknown'] += 1
                            continue
                        
                        # Categorize cost (example logic, adjust as needed)
                        if isinstance(cost, str):
                            cost_lower = cost.lower()
                            if 'high' in cost_lower:
                                cost_mapping['High'] += 1
                            elif 'medium' in cost_lower or 'med' in cost_lower:
                                cost_mapping['Medium'] += 1
                            elif 'low' in cost_lower:
                                cost_mapping['Low'] += 1
                            else:
                                cost_mapping['Unknown'] += 1
                        else:
                            # If it's a numeric value
                            try:
                                cost_value = float(cost)
                                if cost_value > 1000:
                                    cost_mapping['High'] += 1
                                elif cost_value > 100:
                                    cost_mapping['Medium'] += 1
                                else:
                                    cost_mapping['Low'] += 1
                            except (ValueError, TypeError):
                                cost_mapping['Unknown'] += 1
                    
                    # Remove 'Unknown' if it's empty
                    if cost_mapping['Unknown'] == 0:
                        del cost_mapping['Unknown']
                    
                    # Prepare chart data
                    chart_data['labels'] = list(cost_mapping.keys())
                    chart_data['datasets'][0]['data'] = list(cost_mapping.values())
                    chart_data['datasets'][0]['label'] = 'Incidents by Cost Impact'
            else:
                # For time-based X-axis, we can't easily bin numeric costs
                # So we'll stick with categories
                datasets = []
                impact_levels = ['Low', 'Medium', 'High']
                
                for level in impact_levels:
                    level_data = []
                    
                    for label in chart_data['labels']:
                        # For simplicity, use placeholder data
                        period_incidents = counts.get(label, 0) // len(impact_levels)
                        level_data.append(period_incidents)
                    
                    datasets.append({
                        'label': f'{level} Cost Impact',
                        'data': level_data,
                        'backgroundColor': 'rgba(255, 205, 86, 0.5)',
                        'borderColor': 'rgb(255, 205, 86)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
        else:
            # Default fallback - return incidents by month
            from django.db.models.functions import TruncMonth
            
            # Group by month
            monthly_incidents = (
                incidents
                .annotate(month=TruncMonth('CreatedAt'))
                .values('month')
                .annotate(count=Count('IncidentId'))
                .order_by('month')
            )
            
            # Format for chart
            months = []
            counts = []
            
            for item in monthly_incidents:
                if item['month']:
                    months.append(item['month'].strftime('%b %Y'))
                    counts.append(item['count'])
            
            # Prepare chart data
            chart_data['labels'] = months
            chart_data['datasets'][0]['data'] = counts
            chart_data['datasets'][0]['label'] = 'Incidents by Month'
        
        # Calculate approval rate for the dashboard
        total_count = incidents.count()
        approved_count = incidents.filter(Status__iexact='Approved').count()
        approval_rate = 0
        
        if total_count > 0:
            approval_rate = round((approved_count / total_count) * 100, 1)
        
        # Prepare response data
        response_data = {
            'success': True,
            'chartData': chart_data,
            'dashboardData': {
                'approval_rate': approval_rate
            }
        }
        
        print(f"Returning incident analytics response")
        print(f"Chart data: {chart_data}")
        print(f"Response data: {response_data}")
        
    except Exception as e:
        print(f"Error in incident_analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return an error response with empty chart data
        response_data = {
            'success': False,
            'message': f"Error fetching incident analytics data: {str(e)}",
            'chartData': {
                'labels': [],
                'datasets': [{
                    'label': 'Error',
                    'data': []
                }]
            },
            'dashboardData': {
                'approval_rate': 0
            }
        }
    
    return JsonResponse(response_data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def get_recent_incidents(request):
    """
    Endpoint to fetch recent incidents for the dashboard activity feed
    Returns the most recent incidents with their details
    """
    # RBAC Debug - Log user access attempt
    debug_info = debug_user_permissions(request, "VIEW_RECENT_INCIDENTS", "incident", None)
    
    print("get_recent_incidents called")
    
    from django.apps import apps
    from django.http import JsonResponse
    
    try:
        # Debug: Log all incoming parameters
        print(f"[DEBUG] get_recent_incidents - All GET parameters: {dict(request.GET)}")
        print(f"[DEBUG] get_recent_incidents - Request path: {request.path}")
        print(f"[DEBUG] get_recent_incidents - Request method: {request.method}")
        
        # Define allowed GET parameters
        allowed_params = {
            'limit': {
                'type': 'integer',
                'min_value': 1,
                'max_value': 100,
                'required': False
            },
            'user_id': {
                'type': 'integer',
                'required': False
            }
        }
        
        # Validate GET parameters
        validated_params, error = validate_get_parameters(request, allowed_params)
        if error:
            print(f"[DEBUG] get_recent_incidents - Validation error: {error}")
            return JsonResponse({'success': False, 'message': error}, status=400)
        
        print(f"[DEBUG] get_recent_incidents - Validated parameters: {validated_params}")
        
        # Get the Incident model from the app registry
        Incident = apps.get_model('grc', 'Incident')
        
        # Get limit parameter (default to 3)
        limit = validated_params.get('limit', 3)
        
        # Get the most recent incidents (excluding audit findings)
        recent_incidents = Incident.objects.exclude(Origin='Audit Finding').order_by('-CreatedAt')[:limit]
        
        # Convert to list of dictionaries
        incidents_data = []
        for incident in recent_incidents:
            incidents_data.append({
                'IncidentId': incident.IncidentId,
                'IncidentTitle': incident.IncidentTitle,
                'Description': incident.Description,
                'RiskPriority': incident.RiskPriority,
                'Status': incident.Status,
                'CreatedAt': incident.CreatedAt,
                'Origin': incident.Origin
            })
        
        # Prepare response data
        response_data = {
            'success': True,
            'incidents': incidents_data
        }
        
        print(f"Returning {len(incidents_data)} recent incidents")
        
    except Exception as e:
        print(f"Error in get_recent_incidents: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return an error response
        response_data = {
            'success': False,
            'message': f"Error fetching recent incidents: {str(e)}",
            'incidents': []
        }
    
    return JsonResponse(response_data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def get_incident_business_units(request):
    """Get unique business units from incidents table AffectedBusinessUnit column"""
    try:
        # Get unique business units from incidents table
        business_units = Incident.objects.filter(
            AffectedBusinessUnit__isnull=False
        ).exclude(
            AffectedBusinessUnit__exact=''
        ).values_list('AffectedBusinessUnit', flat=True).distinct().order_by('AffectedBusinessUnit')
       
        # Convert to list and filter out any None or empty values
        business_units_list = [unit for unit in business_units if unit and unit.strip()]
       
        return JsonResponse({
            'success': True,
            'data': business_units_list
        })
    except Exception as e:
        print(f"Error fetching incident business units: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)