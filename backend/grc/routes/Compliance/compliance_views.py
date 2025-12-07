# Django ORM type checking suppression for this entire file
# mypy: disable-error-code="attr-defined"
# pylint: disable=no-member
# type: ignore
import logging
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from ...routes.Consent import require_consent
from ...rbac.decorators import (
    compliance_view_required, compliance_create_required, compliance_edit_required,
    compliance_approve_required, compliance_delete_required, compliance_analytics_required,
    compliance_dashboard_required, compliance_kpi_required, compliance_audit_required,
    compliance_versioning_required, compliance_toggle_required, compliance_deactivate_required,
    compliance_framework_required, compliance_policy_required, compliance_subpolicy_required,
    compliance_review_required, compliance_clone_required, compliance_export_required,
    compliance_notification_required, compliance_category_required, compliance_business_unit_required
)
from ...rbac.permissions import (
    ComplianceViewPermission, ComplianceCreatePermission, ComplianceEditPermission,
    ComplianceApprovePermission, ComplianceAnalyticsPermission, ComplianceDashboardPermission,
    ComplianceKPIPermission, ComplianceAuditPermission, ComplianceVersioningPermission,
    ComplianceTogglePermission, ComplianceDeactivatePermission, ComplianceFrameworkPermission,
    ComplianceReviewPermission, ComplianceClonePermission, ComplianceExportPermission,
    ComplianceNotificationPermission, ComplianceCategoryPermission, ComplianceBusinessUnitPermission,
    ComplianceFrameworkAccessPermission
)
from ...rbac.utils import RBACUtils
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ...serializers import UserSerializer
from ...models import (
    User, Framework, Policy, SubPolicy, Compliance, PolicyApproval, ComplianceApproval, 
    Notification, FrameworkVersion, PolicyVersion, LastChecklistItemVerified,
    AuditVersion, AuditFinding, RiskInstance, ExportTask, GRCLog
    # CategoryBusinessUnit will be imported locally in functions
)
from ...serializers import *
from django.utils import timezone   
import datetime
import uuid
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ...routes.Global.s3_fucntions import (
    export_to_excel,
    export_to_csv,
    export_to_pdf,
    export_to_json,
    export_to_xml
)
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from django.db import connection
import json, requests
from datetime import timedelta
from celery import shared_task
import re
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from django.core.exceptions import ValidationError
import math

# Django model type hints compatibility
if TYPE_CHECKING:
    from django.db.models import Manager
from django.contrib.auth.hashers import make_password, check_password
from ...routes.Global.notification_service import NotificationService
from ...routes.Global.notifications import notifications_storage
from django.contrib.auth.models import User
from ...models import Users


# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


LOGGING_SERVICE_URL = None


def create_in_app_notification(user_id, title, message, category: str = "compliance", priority: str = "medium") -> None:
    """
    Helper to create lightweight in-app notifications for the compliance module.
    Uses the shared notifications_storage structure consumed by the notifications API
    and Sidebar.vue, mirroring the pattern used by policy acknowledgements.
    """
    try:
        from datetime import datetime as dt
        import uuid

        notification = {
            "id": str(uuid.uuid4()),
            "title": title,
            "message": message,
            "category": category,
            "priority": priority,
            "createdAt": dt.now().isoformat(),
            "status": {
                "isRead": False,
                "readAt": None,
            },
            "user_id": str(user_id),
        }

        notifications_storage.append(notification)

        # Keep only last 100 notifications in memory, same safeguard as Global.notifications
        if len(notifications_storage) > 100:
            notifications_storage.pop(0)
    except Exception as e:
        # Never break core flows because of in-app notification issues
        print(f"Error creating in-app notification for user {user_id}: {str(e)}")

# Django ORM type checking suppression for all model operations in this file
# mypy: disable-error-code="attr-defined"

# Centralized validation module for allow-list input validation
class ComplianceInputValidator:
    """Centralized validation for all compliance input fields following allow-list pattern"""
    
    # Character sets for validation
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9\s\.\-_]+$')
    TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\.\,\!\?\-_\(\)\[\]\:\;\'\"\&\%\$\#\@\+\=\<\>\/\\\|\*\^\~\`\n\r\t]+$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]+$')
    VERSION_PATTERN = re.compile(r'^[0-9]+\.[0-9]+$')
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    # Allowed values for choice fields
    ALLOWED_CRITICALITY = ['High', 'Medium', 'Low']
    ALLOWED_MANDATORY_OPTIONAL = ['Mandatory', 'Optional']
    ALLOWED_MANUAL_AUTOMATIC = ['Manual', 'Automatic']
    ALLOWED_MATURITY_LEVELS = ['Initial', 'Developing', 'Defined', 'Managed', 'Optimizing']
    ALLOWED_STATUS = ['Under Review', 'Approved', 'Rejected', 'Active', 'Inactive']
    ALLOWED_ACTIVE_INACTIVE = ['Active', 'Inactive']
    ALLOWED_PERMANENT_TEMPORARY = ['Permanent', 'Temporary']
    ALLOWED_VERSIONING_TYPE = ['Minor', 'Major']
    ALLOWED_RISK_TYPES = ['Current', 'Residual', 'Inherent', 'Emerging', 'Accepted']
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input by removing potentially dangerous characters"""
        if not isinstance(value, str):
            return str(value) if value is not None else ''
        # Remove null bytes and control characters except newline, tab, carriage return
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value).strip()
    
    @staticmethod
    def validate_required_string(value: Any, field_name: str, max_length: Optional[int] = None, 
                                min_length: int = 1, pattern = None) -> str:
        """Validate required string fields with allow-list pattern"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required and cannot be empty")
        
        # Convert to string and sanitize
        str_value = ComplianceInputValidator.sanitize_string(value)
        
        if len(str_value) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters long")
        
        if max_length and len(str_value) > max_length:
            raise ValidationError(f"{field_name} must not exceed {max_length} characters")
        
        # Check against allowed pattern
        if pattern and not pattern.match(str_value):
            raise ValidationError(f"{field_name} contains invalid characters")
        
        return str_value
    
    @staticmethod
    def validate_optional_string(value: Any, field_name: str, max_length: Optional[int] = None, 
                                pattern = None) -> str:
        """Validate optional string fields with allow-list pattern"""
        if value is None or value == '':
            return ''
        
        str_value = ComplianceInputValidator.sanitize_string(value)
        
        if max_length and len(str_value) > max_length:
            raise ValidationError(f"{field_name} must not exceed {max_length} characters")
        
        if pattern and str_value and not pattern.match(str_value):
            raise ValidationError(f"{field_name} contains invalid characters")
        
        return str_value
    
    @staticmethod
    def validate_choice_field(value: Any, field_name: str, allowed_choices: List[str]) -> str:
        """Validate choice fields against allowed values"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        str_value = str(value).strip()
        if str_value not in allowed_choices:
            raise ValidationError(f"{field_name} must be one of: {', '.join(allowed_choices)}")
        
        return str_value
    
    @staticmethod
    def validate_boolean_field(value: Any, field_name: str) -> bool:
        """Validate boolean fields"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ['true', '1', 'yes']:
                return True
            elif value.lower() in ['false', '0', 'no', '']:
                return False
        if isinstance(value, int):
            return bool(value)
        
        raise ValidationError(f"{field_name} must be a valid boolean value")
    
    @staticmethod
    def validate_numeric_field(value: Any, field_name: str, min_val: Optional[float] = None, 
                              max_val: Optional[float] = None) -> float:
        """Validate numeric fields with range checking"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number")
        
        if min_val is not None and num_value < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and num_value > max_val:
            raise ValidationError(f"{field_name} must not exceed {max_val}")
        
        return num_value
    
    @staticmethod
    def validate_integer_field(value: Any, field_name: str, min_val: Optional[int] = None, 
                              max_val: Optional[int] = None) -> int:
        """Validate integer fields with range checking"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid integer")
        
        if min_val is not None and int_value < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and int_value > max_val:
            raise ValidationError(f"{field_name} must not exceed {max_val}")
        
        return int_value
    
    @staticmethod
    def validate_date_field(value: Any, field_name: str) -> str:
        """Validate date fields"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        str_value = str(value).strip()
        
        if not ComplianceInputValidator.DATE_PATTERN.match(str_value):
            raise ValidationError(f"{field_name} must be in YYYY-MM-DD format")
        
        try:
            datetime.datetime.strptime(str_value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(f"{field_name} must be a valid date")
        
        return str_value
    
    @staticmethod
    def calculate_new_version(current_version: str, versioning_type: str) -> str:
        """Calculate new version based on versioning type"""
        # print(f"  calculate_new_version called with: current_version='{current_version}', versioning_type='{versioning_type}'")
        try:
            # Parse current version (e.g., "2.3" becomes 2.3)
            current_float = float(current_version) if current_version else 1.0
            # print(f"  Parsed current_float: {current_float}")
            
            if versioning_type == 'Minor':
                # For minor: add 0.1 to current version (e.g., 2.3 -> 2.4)
                new_version = round(current_float + 0.1, 1)
                # print(f"  Minor version calculation: {current_float} + 0.1 = {new_version}")
            elif versioning_type == 'Major':
                # For major: increment major version and reset minor to 0 (e.g., 2.3 -> 3.0)
                major = int(current_float)
                new_version = float(major + 1)
                # print(f"  Major version calculation: int({current_float}) + 1 = {new_version}")
            else:
                # Default behavior (Major)
                major = int(current_float)
                new_version = float(major + 1)
                # print(f"  Default (Major) version calculation: int({current_float}) + 1 = {new_version}")
            
            result = str(new_version)
            # print(f"  Returning: '{result}'")
            return result
        except (ValueError, TypeError) as e:
            # If parsing fails, default to incrementing major version
            # print(f"  Error in version calculation: {e}, returning '2.0'")
            return "2.0"
    
    @staticmethod
    def clean_mitigation_data(mitigation_data: str) -> str:
        """
        Clean and format mitigation data for consistent storage and display.
        Handles simple JSON format: {"1": "First step", "2": "Second step"}
        """
        if not mitigation_data:
            return "{}"
        
        # If it's already a JSON string, try to parse and validate
        if isinstance(mitigation_data, str) and (mitigation_data.strip().startswith('{') or mitigation_data.strip().startswith('[')):
            try:
                import json
                parsed = json.loads(mitigation_data)
                
                # Handle the simple step format: {"1": "First step", "2": "Second step"}
                if isinstance(parsed, dict):
                    cleaned_mitigation = {}
                    
                    # Check if all keys are numeric strings and values are strings
                    for key, value in parsed.items():
                        if isinstance(key, str) and key.isdigit() and isinstance(value, str):
                            if value.strip():  # Only include non-empty steps
                                cleaned_mitigation[key] = value.strip()
                        elif isinstance(key, int) and isinstance(value, str):
                            if value.strip():  # Only include non-empty steps
                                cleaned_mitigation[str(key)] = value.strip()
                    
                    # If we have valid steps, return the cleaned version
                    if cleaned_mitigation:
                        return json.dumps(cleaned_mitigation, separators=(',', ':'))
                
                # Handle legacy array format - convert to simple format
                if isinstance(parsed, list):
                    cleaned_mitigation = {}
                    for i, step in enumerate(parsed):
                        if isinstance(step, str) and step.strip():
                            cleaned_mitigation[str(i + 1)] = step.strip()
                    
                    if cleaned_mitigation:
                        return json.dumps(cleaned_mitigation, separators=(',', ':'))
                
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as plain text
                pass
        
        # Handle plain text - convert to simple JSON format
        if isinstance(mitigation_data, str) and mitigation_data.strip():
            import json
            
            # Try to split by common delimiters to create steps
            text = mitigation_data.strip()
            
            # Split by numbered patterns (1., 2., etc.) or newlines
            import re
            steps_text = re.split(r'(?:^|\n)\s*\d+\.\s*', text)
            if len(steps_text) > 1:
                # Remove empty first element if it exists
                if not steps_text[0].strip():
                    steps_text = steps_text[1:]
            else:
                # Split by newlines or semicolons
                steps_text = [s.strip() for s in re.split(r'[;\n]', text) if s.strip()]
            
            # If no clear steps found, treat as single step
            if not steps_text or (len(steps_text) == 1 and not steps_text[0].strip()):
                steps_text = [text]
            
            # Create step objects in simple format
            cleaned_mitigation = {}
            for i, step_text in enumerate(steps_text):
                if step_text.strip():
                    cleaned_mitigation[str(i + 1)] = step_text.strip()
            
            if cleaned_mitigation:
                return json.dumps(cleaned_mitigation, separators=(',', ':'))
        
        return "{}"
    
    @staticmethod
    def validate_mitigation_json(mitigation_data: str) -> bool:
        """
        Validate that mitigation data is properly formatted JSON with valid structure
        Expected format: {"1": "First step", "2": "Second step"}
        """
        if not mitigation_data:
            return True  # Empty is valid
        
        try:
            import json
            parsed = json.loads(mitigation_data)
            
            # Must be a dictionary
            if not isinstance(parsed, dict):
                return False
            
            # Check if all keys are numeric strings and values are non-empty strings
            for key, value in parsed.items():
                # Key must be a string representation of a number
                if not isinstance(key, str) or not key.isdigit():
                    return False
                
                # Value must be a non-empty string
                if not isinstance(value, str) or not value.strip():
                    return False
            
            return True
            
        except json.JSONDecodeError:
            return False
    
    @classmethod
    def validate_compliance_data(cls, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main validation method for compliance data using allow-list approach"""
        validated_data = {}
        errors = {}
        
        try:
            # Validate SubPolicy (required foreign key)
            validated_data['SubPolicy'] = cls.validate_integer_field(
                request_data.get('SubPolicy'), 'SubPolicy', min_val=1
            )
        except ValidationError as e:
            errors['SubPolicy'] = [str(e)]
        
        try:
            # Validate ComplianceTitle (required, max 145 chars)
            validated_data['ComplianceTitle'] = cls.validate_required_string(
                request_data.get('ComplianceTitle'), 'ComplianceTitle', 
                max_length=145, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceTitle'] = [str(e)]
        
        try:
            # Validate ComplianceItemDescription (required text field)
            validated_data['ComplianceItemDescription'] = cls.validate_required_string(
                request_data.get('ComplianceItemDescription'), 'ComplianceItemDescription',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceItemDescription'] = [str(e)]
        
        try:
            # Validate ComplianceType (required, max 100 chars)
            validated_data['ComplianceType'] = cls.validate_required_string(
                request_data.get('ComplianceType'), 'ComplianceType',
                max_length=100, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceType'] = [str(e)]
        
        try:
            # Validate Scope (required text field)
            validated_data['Scope'] = cls.validate_required_string(
                request_data.get('Scope'), 'Scope',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['Scope'] = [str(e)]
        
        try:
            # Validate Objective (required text field)
            validated_data['Objective'] = cls.validate_required_string(
                request_data.get('Objective'), 'Objective',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['Objective'] = [str(e)]
        
        try:
            # Validate BusinessUnitsCovered (required, max 225 chars)
            validated_data['BusinessUnitsCovered'] = cls.validate_required_string(
                request_data.get('BusinessUnitsCovered'), 'BusinessUnitsCovered',
                max_length=225, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['BusinessUnitsCovered'] = [str(e)]
        
        try:
            # Validate IsRisk (boolean)
            validated_data['IsRisk'] = cls.validate_boolean_field(
                request_data.get('IsRisk', False), 'IsRisk'
            )
        except ValidationError as e:
            errors['IsRisk'] = [str(e)]
        
        # If IsRisk is True, validate risk-related fields
        if validated_data.get('IsRisk', False):
            try:
                validated_data['PossibleDamage'] = cls.validate_required_string(
                    request_data.get('PossibleDamage'), 'PossibleDamage',
                    max_length=5000, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['PossibleDamage'] = [str(e)]
            
            try:
                validated_data['PotentialRiskScenarios'] = cls.validate_required_string(
                    request_data.get('PotentialRiskScenarios'), 'PotentialRiskScenarios',
                    max_length=5000, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['PotentialRiskScenarios'] = [str(e)]
            
            try:
                validated_data['RiskType'] = cls.validate_required_string(
                    request_data.get('RiskType'), 'RiskType',
                    max_length=45, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['RiskType'] = [str(e)]
            
            try:
                validated_data['RiskCategory'] = cls.validate_required_string(
                    request_data.get('RiskCategory'), 'RiskCategory',
                    max_length=45, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['RiskCategory'] = [str(e)]
            
            try:
                validated_data['RiskBusinessImpact'] = cls.validate_required_string(
                    request_data.get('RiskBusinessImpact'), 'RiskBusinessImpact',
                    max_length=45, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['RiskBusinessImpact'] = [str(e)]
        else:
            # Optional fields when IsRisk is False
            validated_data['PossibleDamage'] = cls.validate_optional_string(
                request_data.get('PossibleDamage'), 'PossibleDamage',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
            validated_data['PotentialRiskScenarios'] = cls.validate_optional_string(
                request_data.get('PotentialRiskScenarios'), 'PotentialRiskScenarios',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
            validated_data['RiskType'] = cls.validate_optional_string(
                request_data.get('RiskType'), 'RiskType',
                max_length=45, pattern=cls.TEXT_PATTERN
            )
            validated_data['RiskCategory'] = cls.validate_optional_string(
                request_data.get('RiskCategory'), 'RiskCategory',
                max_length=45, pattern=cls.TEXT_PATTERN
            )
            validated_data['RiskBusinessImpact'] = cls.validate_optional_string(
                request_data.get('RiskBusinessImpact'), 'RiskBusinessImpact',
                max_length=45, pattern=cls.TEXT_PATTERN
            )
        
        try:
            # Validate and clean mitigation (JSON step-by-step format)
            raw_mitigation = request_data.get('mitigation')
            # Always use format_mitigation_data to handle both string and object types
            formatted_mitigation = format_mitigation_data(raw_mitigation)
            # If risk requires mitigation but none provided, add error
            if validated_data.get('IsRisk', False) and not formatted_mitigation:
                errors['mitigation'] = ["At least one mitigation step is required for risks"]
            else:
                validated_data['mitigation'] = formatted_mitigation
                # Debug log
                #print(f"DEBUG: Validated mitigation data: {formatted_mitigation}")
        except Exception as e:
            errors['mitigation'] = [f"Error processing mitigation data: {str(e)}"]
        
        try:
            # Validate Criticality (required choice field)
            validated_data['Criticality'] = cls.validate_choice_field(
                request_data.get('Criticality'), 'Criticality', cls.ALLOWED_CRITICALITY
            )
        except ValidationError as e:
            errors['Criticality'] = [str(e)]
        
        try:
            # Validate MandatoryOptional (required choice field)
            validated_data['MandatoryOptional'] = cls.validate_choice_field(
                request_data.get('MandatoryOptional'), 'MandatoryOptional', cls.ALLOWED_MANDATORY_OPTIONAL
            )
        except ValidationError as e:
            errors['MandatoryOptional'] = [str(e)]
        
        try:
            # Validate ManualAutomatic (required choice field)
            validated_data['ManualAutomatic'] = cls.validate_choice_field(
                request_data.get('ManualAutomatic'), 'ManualAutomatic', cls.ALLOWED_MANUAL_AUTOMATIC
            )
        except ValidationError as e:
            errors['ManualAutomatic'] = [str(e)]
        
        try:
            # Validate Impact (required numeric field, 1-10)
            validated_data['Impact'] = cls.validate_numeric_field(
                request_data.get('Impact'), 'Impact', min_val=1.0, max_val=10.0
            )
        except ValidationError as e:
            errors['Impact'] = [str(e)]
        
        try:
            # Validate Probability (required numeric field, 1-10)
            validated_data['Probability'] = cls.validate_numeric_field(
                request_data.get('Probability'), 'Probability', min_val=1.0, max_val=10.0
            )
        except ValidationError as e:
            errors['Probability'] = [str(e)]
        
        try:
            # Validate ComplianceVersion (required, max 50 chars, version pattern)
            validated_data['ComplianceVersion'] = cls.validate_required_string(
                request_data.get('ComplianceVersion', '1.0'), 'ComplianceVersion',
                max_length=50, pattern=cls.VERSION_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceVersion'] = [str(e)]
        
        try:
            # Validate Applicability (optional, max 450 chars)
            validated_data['Applicability'] = cls.validate_optional_string(
                request_data.get('Applicability'), 'Applicability',
                max_length=450, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['Applicability'] = [str(e)]
        
        try:
            # Validate Identifier (optional, max 45 chars, identifier pattern)
            identifier = request_data.get('Identifier', '').strip()
            if identifier:
                validated_data['Identifier'] = cls.validate_optional_string(
                    identifier, 'Identifier', max_length=45, pattern=cls.IDENTIFIER_PATTERN
                )
            else:
                validated_data['Identifier'] = ''
        except ValidationError as e:
            errors['Identifier'] = [str(e)]
            # Set to empty string if validation fails, so auto-generation will be used
            validated_data['Identifier'] = ''
        
        try:
            # Validate reviewer (required integer)
            validated_data['reviewer'] = cls.validate_integer_field(
                request_data.get('reviewer'), 'reviewer', min_val=1
            )
        except ValidationError as e:
            errors['reviewer'] = [str(e)]
        
        try:
            # Validate ApprovalDueDate (required date)
            validated_data['ApprovalDueDate'] = cls.validate_date_field(
                request_data.get('ApprovalDueDate'), 'ApprovalDueDate'
            )
        except ValidationError as e:
            errors['ApprovalDueDate'] = [str(e)]
        
        # Set default values for system fields
        validated_data['Status'] = 'Under Review'
        validated_data['ActiveInactive'] = 'Inactive'
        validated_data['PermanentTemporary'] = 'Permanent'
        validated_data['MaturityLevel'] = 'Initial'
        
        # Always copy CreatedByName from request_data if present (no validation, just sanitize)
        if 'CreatedByName' in request_data:
            validated_data['CreatedByName'] = str(request_data['CreatedByName']).strip()
        
        if errors:
            raise ValidationError(errors)
        
        return validated_data

 
# Create your views here.
 
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
   
    # Hardcoded credentials
    if email == "admin@example.com" and password == "password123":
        # Set user_id in session for RBAC
        request.session['user_id'] = 1  # Default admin user ID
        request.session['email'] = email
        request.session['name'] = 'Admin User'
        request.session.save()  # Ensure session is saved
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': {
                'email': email,
                'name': 'Admin User',
                'user_id': 1
            }
        })
    else:
        return Response({
            'success': False,
            'message': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
 
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Instead of using JWT tokens which expect Django's User model,
        # create a simple token-like response with user data
        return Response({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'UserId': user.UserId,
                'UserName': user.UserName
            }
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_log(module, actionType, description=None, userId=None, userName=None,
             userRole=None, entityType=None, logLevel='INFO', ipAddress=None,
             additionalInfo=None, entityId=None):
   
    # Create log entry in database
    try:
        # Prepare data for GRCLog model
        log_data = {
            'Module': module,
            'ActionType': actionType,
            'Description': description,
            'UserId': userId,
            'UserName': userName,
            'EntityType': entityType,
            'EntityId': entityId,
            'LogLevel': logLevel,
            'IPAddress': ipAddress,
            'AdditionalInfo': additionalInfo
        }
       
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
       
        # Create and save the log entry
        log_entry = GRCLog(**log_data)
        log_entry.save()
       
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
        print(f"Error saving log to database: {str(e)}")
        # Try to capture the error itself
        try:
            error_log = GRCLog(
                Module=module,
                ActionType='LOG_ERROR',
                Description=f"Error logging {actionType} on {module}: {str(e)}",
                LogLevel='ERROR'
            )
            error_log.save()
        except:
            pass  # If we can't even log the error, just continue
        return None
 
@api_view(['GET'])
def test_connection(request):
    return Response({"message": "Connection successful!"})


 
@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_frameworks(request):
    # print(f"\n=== GET_FRAMEWORKS DEBUG ===")
    
    try:
        # Get all frameworks (remove ActiveInactive filter for now to see all data)
        # Note: We don't filter frameworks list - users need to see all frameworks to select from
        frameworks = Framework.objects.all()  # type: ignore
        # print(f"Found {frameworks.count()} frameworks in total")
        
        # # Debug: Print each framework
        # for fw in frameworks:
        #     print(f"Framework: ID={fw.FrameworkId}, Name={fw.FrameworkName}, Status={fw.ActiveInactive}")
        
        serializer = FrameworkSerializer(frameworks, many=True)
        serialized_data = serializer.data
        
        # print(f"Serialized data: {serialized_data}")
        
        # Format the response to match frontend expectations
        formatted_frameworks = []
        for fw_data in serialized_data:
            formatted_fw = {
                'id': fw_data.get('FrameworkId'),
                'name': fw_data.get('FrameworkName'),
                'category': fw_data.get('Category', ''),
                'status': fw_data.get('ActiveInactive', ''),
                'description': fw_data.get('FrameworkDescription', ''),
            }
            formatted_frameworks.append(formatted_fw)
            # print(f"Formatted framework: {formatted_fw}")
        
        response_data = {
            'success': True, 
            'frameworks': formatted_frameworks,  # Change 'data' to 'frameworks'
            'count': len(formatted_frameworks)
        }
        
        # print(f"Final response: {response_data}")
        print("=== END GET_FRAMEWORKS DEBUG ===\n")
        
        return Response(response_data)
        
    except Exception as e:
        print(f"Error in get_frameworks: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error fetching frameworks: {str(e)}'
        }, status=500)
 
@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_policies(request, framework_id):
    print(f"\n=== GET_POLICIES DEBUG ===")
    print(f"Received framework_id: {framework_id} (type: {type(framework_id)})")
    
    try:
        # Get all policies for this framework (remove ActiveInactive filter for now to see all data)
        policies = Policy.objects.filter(FrameworkId=framework_id)  # type: ignore
        print(f"Found {policies.count()} policies for framework {framework_id}")
        
        # Debug: Print each policy
        for p in policies:
            print(f"Policy: ID={p.PolicyId}, Name={p.PolicyName}, Status={p.ActiveInactive}")
        
        # Format the response to match frontend expectations
        formatted_policies = []
        for p in policies:
            formatted_policy = {
                'id': p.PolicyId,
                'name': p.PolicyName,
                'applicability': p.Applicability or '',
                'status': p.ActiveInactive or '',
                'scope': p.Applicability or '',  # Add scope field for compatibility
            }
            formatted_policies.append(formatted_policy)
            print(f"Formatted policy: {formatted_policy}")
        
        response_data = {
            'success': True, 
            'policies': formatted_policies,  # Change 'data' to 'policies'
            'count': len(formatted_policies)
        }
        
        print(f"Final response: {response_data}")
        print("=== END GET_POLICIES DEBUG ===\n")
        
        return Response(response_data)
        
    except Exception as e:
        print(f"Error in get_policies: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error fetching policies: {str(e)}'
        }, status=500)
 
@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_subpolicies(request, policy_id):
    print(f"\n=== GET_SUBPOLICIES DEBUG ===")
    print(f"Received policy_id: {policy_id} (type: {type(policy_id)})")
    
    try:
        # Get all subpolicies for this policy (remove Status filter for now to see all data)
        subpolicies = SubPolicy.objects.filter(PolicyId=policy_id)  # type: ignore
        print(f"Found {subpolicies.count()} subpolicies for policy {policy_id}")
        
        # Debug: Print each subpolicy
        for sp in subpolicies:
            print(f"SubPolicy: ID={sp.SubPolicyId}, Name={sp.SubPolicyName}, Status={sp.Status}")
        
        serializer = SubPolicySerializer(subpolicies, many=True)
        serialized_data = serializer.data
        
        print(f"Serialized data: {serialized_data}")
        
        # Format the response to match frontend expectations
        formatted_subpolicies = []
        for sp_data in serialized_data:
            formatted_sp = {
                'id': sp_data.get('SubPolicyId'),
                'name': sp_data.get('SubPolicyName'),
                'status': sp_data.get('Status'),
                'description': sp_data.get('Description', ''),
                'control': sp_data.get('Control', ''),
                'identifier': sp_data.get('Identifier', ''),
            }
            formatted_subpolicies.append(formatted_sp)
            print(f"Formatted subpolicy: {formatted_sp}")
        
        response_data = {
            'success': True, 
            'subpolicies': formatted_subpolicies,  # Change 'data' to 'subpolicies'
            'count': len(formatted_subpolicies)
        }
        
        print(f"Final response: {response_data}")
        print("=== END GET_SUBPOLICIES DEBUG ===\n")
        
        return Response(response_data)
        
    except Exception as e:
        print(f"Error in get_subpolicies: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error fetching subpolicies: {str(e)}'
        }, status=500)
 
def ensure_user_has_email(user_id, default_email=None):
    """
    Utility function to ensure a user has an email address.
    Returns True if the user has an email (existing or newly added), False otherwise.
    """
    try:
        from ...models import User
        if not Users.objects.filter(UserName=user_id).exists():  # type: ignore
            print(f"User with ID {user_id} not found - creating")
            username = f"User{user_id}"
            email = default_email or f"user{user_id}@example.com"
            Users.objects.create(  # type: ignore
                UserId=user_id,
                UserName=username,
                Password="",
                email=email
            )
            print(f"Created user {username} with email {email}")
            return True
            
        user = Users.objects.get(UserName=user_id)  # type: ignore
        if not user.email:
            email = default_email or f"user{user_id}@example.com"
            user.email = email
            user.save()
            print(f"Updated user {user.UserName} with email {email}")
            
        return bool(user.email)
    except Exception as e:
        print(f"Error ensuring user has email: {str(e)}")
        return False

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([ComplianceCreatePermission])
@compliance_create_required
@require_consent('create_compliance')
def create_compliance(request):

    print(f"Received request data: {request.data}")
    
    # Determine the user performing this action (prefer JWT, then session)
    try:
        user_id = RBACUtils.get_user_id_from_request(request)
    except Exception:
        user_id = None
    if not user_id and hasattr(request, 'user') and getattr(request.user, 'UserId', None):
        user_id = request.user.UserId
    if not user_id:
        user_id = request.session.get('user_id')
    if not user_id and request.data.get('user_id'):
        # Fallback from payload if provided
        try:
            user_id = int(request.data.get('user_id'))
        except Exception:
            user_id = None
    print(f"Resolved creator user_id: {user_id}")
    
    try:
        # Validate input data using centralized validator
        validated_data = ComplianceInputValidator.validate_compliance_data(request.data)
    except ValidationError as e:
        return Response({
            'success': False,
            'message': 'Input validation failed',
            'errors': e.message_dict if hasattr(e, 'message_dict') else {'general': [str(e)]}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle identifier - use user-provided or generate auto identifier
    if not validated_data['Identifier']:
        # Generate identifier if not provided by user
        subpolicy_id = validated_data['SubPolicy']
        identifier = f"COMP-{subpolicy_id}-{datetime.date.today().strftime('%y%m%d')}-{uuid.uuid4().hex[:6]}"
        validated_data['Identifier'] = identifier
    else:
        # Use the user-provided identifier
        identifier = validated_data['Identifier']
    
    # Use resolved user_id as creator; ignore client-supplied CreatedByName for integrity
    created_by_id = user_id
    logger = logging.getLogger(__name__)
    logger.debug(f'Creating compliance: created_by_id={created_by_id}')
    # Fetch the user's name from the custom Users model
    from ...models import Users
    try:
        user_obj = Users.objects.get(UserId=created_by_id) if created_by_id else None
        created_by_name = (user_obj.FirstName + ' ' + user_obj.LastName).strip() if user_obj.FirstName or user_obj.LastName else user_obj.UserName
        logger.debug(f'User lookup success: {created_by_name}')
    except Exception as e:
        logger.warning(f'User lookup failed for id {created_by_id}: {e}')
        created_by_name = 'Unknown User'
    # Get reviewer ID from validated_data['reviewer']
    reviewer_id = validated_data.get('reviewer')
    
    # Create new compliance
    try:
        # Get the SubPolicy object
        from ...models import SubPolicy
        try:
            subpolicy = SubPolicy.objects.get(SubPolicyId=validated_data['SubPolicy'])
        except SubPolicy.DoesNotExist:
            print(f"WARNING: SubPolicy {validated_data['SubPolicy']} not found")
            return Response({
                'success': False,
                'message': 'Failed to create compliance',
                'errors': {'general': ['SubPolicy not found']}
            }, status=status.HTTP_400_BAD_REQUEST)
        # Always use format_mitigation_data to ensure correct type
        mitigation_for_db = format_mitigation_data(validated_data['mitigation'])
        
        # Get FrameworkId from the subpolicy's policy (use _id to get the integer ID)
        framework_id = subpolicy.PolicyId.FrameworkId_id
        #print(f"DEBUG: Using FrameworkId_id: {framework_id} for compliance creation")
        
        new_compliance = Compliance.objects.create(
            SubPolicy=subpolicy,
            ComplianceTitle=validated_data['ComplianceTitle'],
            ComplianceItemDescription=validated_data['ComplianceItemDescription'],
            ComplianceType=validated_data['ComplianceType'],
            Scope=validated_data['Scope'],
            Objective=validated_data['Objective'],
            BusinessUnitsCovered=validated_data['BusinessUnitsCovered'],
            IsRisk=validated_data['IsRisk'],
            PossibleDamage=validated_data['PossibleDamage'],
            mitigation=mitigation_for_db,
            PotentialRiskScenarios=validated_data.get('PotentialRiskScenarios', ''),
            RiskType=validated_data.get('RiskType', ''),
            RiskCategory=validated_data.get('RiskCategory', ''),
            RiskBusinessImpact=validated_data.get('RiskBusinessImpact', ''),
            Criticality=validated_data['Criticality'],
            MandatoryOptional=validated_data['MandatoryOptional'],
            ManualAutomatic=validated_data['ManualAutomatic'],
            Impact=validated_data['Impact'],
            Probability=validated_data['Probability'],
            MaturityLevel=validated_data.get('MaturityLevel', 'Initial'),
            ActiveInactive=validated_data.get('ActiveInactive', 'Inactive'),
            PermanentTemporary=validated_data.get('PermanentTemporary', 'Permanent'),
            CreatedByName=created_by_name,
            CreatedByDate=datetime.date.today(),
            ComplianceVersion='1.0',
            Status='Under Review',
            Identifier=identifier,
            Applicability=validated_data['Applicability'],
            FrameworkId_id=framework_id  # Use _id suffix to assign foreign key directly by ID
        )
        
        # Prepare extracted data for policy approval
        extracted_data = {
            'type': 'compliance',
            'ComplianceItemDescription': validated_data['ComplianceItemDescription'],
            'Criticality': validated_data['Criticality'],
            'Impact': validated_data['Impact'],
            'Probability': validated_data['Probability'],
            'mitigation': format_mitigation_data(validated_data['mitigation']),
            'PossibleDamage': validated_data['PossibleDamage'],
            'IsRisk': validated_data['IsRisk'],
            'MandatoryOptional': validated_data['MandatoryOptional'],
            'ManualAutomatic': validated_data['ManualAutomatic'],
            'CreatedByName': validated_data.get('CreatedByName', created_by_name),
            'CreatedByDate': datetime.date.today().isoformat(),
            'Status': 'Under Review',
            'ComplianceId': new_compliance.ComplianceId,
            'ComplianceVersion': '1.0',
            'SubPolicy': validated_data['SubPolicy'],
            'Identifier': validated_data['Identifier'],
        }
        
        extracted_data['compliance_approval'] = {
            'approved': None,
            'remarks': ''
            # 'ApprovalDueDate': approval_due_date
        }
       
        # Use session user_id or fall back to validated data
        session_user_id = user_id
        
        # Ensure users have emails for notifications
        ensure_user_has_email(session_user_id, "system@example.com")
        reviewer_has_email = ensure_user_has_email(reviewer_id, f"reviewer{reviewer_id}@example.com")
        if not reviewer_has_email:
            print(f"WARNING: Reviewer {reviewer_id} has no email, notifications may fail")
       
        # Get the policy ID from the subpolicy
        policy = subpolicy.PolicyId  # Get the actual Policy instance through the foreign key
            
        # Create the compliance approval
        compliance_approval = ComplianceApproval.objects.create(
            Identifier=validated_data['Identifier'],
            ExtractedData=extracted_data,
            UserId=session_user_id,
            ReviewerId=reviewer_id,
            ApprovedNot=None,
            Version="u1",
            PolicyId=policy,  # Use the actual Policy instance from the foreign key
            FrameworkId_id=framework_id  # Add FrameworkId to compliance approval (use _id suffix for foreign key)
            # ApprovalDueDate=approval_due_date
        )
        
        # Send notification to reviewer (email)
        try:
            print("=== NOTIFICATION DEBUGGING - COMPLIANCE CLONE ===")
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Make sure reviewer has a valid email
            try:
                reviewer = Users.objects.get(UserId=reviewer_id)
                if not reviewer.Email or '@' not in reviewer.Email:
                    reviewer.Email = f"reviewer{reviewer_id}@example.com"
                    reviewer.save()
                    print(f"Updated reviewer {reviewer_id} with email {reviewer.Email}")
                
                print(f"Found reviewer: {reviewer.UserName} with email: {reviewer.Email}")
            except Users.DoesNotExist:
                print(f"ERROR: Reviewer with ID {reviewer_id} does not exist")
            
            # Send email notification to reviewer
            print(f"Sending clone notification for compliance {new_compliance.ComplianceId} to reviewer {reviewer_id}")
            notification_result = notification_service.send_compliance_clone_notification(
                compliance=new_compliance,
                reviewer_id=reviewer_id
            )
            
            if notification_result.get('success'):
                print(f"Successfully sent compliance clone notification to reviewer {reviewer_id}")
            else:
                print(f"Failed to send notification: {notification_result.get('error', 'Unknown error')}")
                print(f"Error details: {notification_result.get('errors', [])}") 
            
            # Log the notification directly in the database
            from ...models import Notification
            try:
                reviewer_email, reviewer_name = notification_service.get_user_email_by_id(reviewer_id)
                if reviewer_email:
                    Notification.objects.create(
                        recipient=reviewer_email,
                        type='compliance_clone',
                        channel='email',
                        success=notification_result.get('success', False)
                    )
                    print(f"Created clone notification record for {reviewer_email}")
            except Exception as db_error:
                print(f"ERROR creating notification record: {str(db_error)}")
                
            print("=== END NOTIFICATION DEBUGGING ===")
        except Exception as e:
            print(f"Error sending compliance clone notification: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Continue even if notification fails

        # In-app notifications (push-style) for creator and reviewer
        try:
            # Creator gets a "submitted" notification
            if session_user_id:
                create_in_app_notification(
                    user_id=session_user_id,
                    title="Compliance Submitted for Review",
                    message=f"Compliance {new_compliance.ComplianceId} has been created and sent to reviewer {reviewer_id}.",
                    category="compliance",
                    priority="medium",
                )

            # Reviewer gets an "assigned" notification
            if reviewer_id:
                create_in_app_notification(
                    user_id=reviewer_id,
                    title="Compliance Review Assigned",
                    message=f"You have been assigned to review compliance {new_compliance.ComplianceId}.",
                    category="compliance",
                    priority="high",
                )
        except Exception as e:
            print(f"Error creating in-app notifications for compliance creation: {str(e)}")

        return Response({
            'success': True,
            'message': 'Compliance created successfully and sent for review',
            'compliance_id': new_compliance.ComplianceId,
            'Identifier': identifier,
            'version': new_compliance.ComplianceVersion,
            'reviewer_id': reviewer_id
        }, status=status.HTTP_201_CREATED)
 
    except Exception as e:
        print(f"Error creating compliance: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliance_dashboard(request):
    try:
        # Get all filter parameters from request
        status = request.query_params.get('status')
        active_inactive = request.query_params.get('active_inactive')
        criticality = request.query_params.get('criticality')
        mandatory_optional = request.query_params.get('mandatory_optional')
        manual_automatic = request.query_params.get('manual_automatic')
        impact = request.query_params.get('impact')
        probability = request.query_params.get('probability')
        permanent_temporary = request.query_params.get('permanent_temporary')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        framework_id = request.query_params.get('framework_id')
        time_range = request.query_params.get('timeRange')
        category = request.query_params.get('category')
        priority = request.query_params.get('priority')
        policy_id = request.query_params.get('policy_id')
        subpolicy_id = request.query_params.get('subpolicy_id')

        print(f"Dashboard request filters - Framework: {framework_id}, Time: {time_range}, Category: {category}, Priority: {priority}")

        # Start with base queryset
        queryset = Compliance.objects.all()

        # Apply framework filter
        if framework_id and framework_id != '':
            print(f"Applying framework filter: {framework_id}")
            queryset = queryset.filter(SubPolicy__PolicyId__FrameworkId=framework_id)
        
        # Apply time range filter
        if time_range and time_range != 'Last 6 Months':
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if time_range == 'Last 3 Months':
                start_date = now - timedelta(days=90)
            elif time_range == 'Last Month':
                start_date = now - timedelta(days=30)
            elif time_range == 'Last Week':
                start_date = now - timedelta(days=7)
            else:
                start_date = now - timedelta(days=180)  # Default to 6 months
                
            queryset = queryset.filter(CreatedByDate__gte=start_date)
        
        # Apply category filter (if you have category field in Compliance model)
        if category and category != 'All Categories':
            # Assuming you have a category field, adjust as needed
            # queryset = queryset.filter(Category=category)
            pass
        
        # Apply priority filter (if you have priority field in Compliance model)
        if priority and priority != 'All Priorities':
            # Assuming you have a priority field, adjust as needed
            # queryset = queryset.filter(Priority=priority)
            pass

        # Apply other filters if they exist
        if status:
            queryset = queryset.filter(Status=status)
        if active_inactive:
            queryset = queryset.filter(ActiveInactive=active_inactive)
        if criticality:
            queryset = queryset.filter(Criticality=criticality)
        if mandatory_optional:
            queryset = queryset.filter(MandatoryOptional=mandatory_optional)
        if manual_automatic:
            queryset = queryset.filter(ManualAutomatic=manual_automatic)
        if impact:
            queryset = queryset.filter(Impact=impact)
        if probability:
            queryset = queryset.filter(Probability=probability)
        if permanent_temporary:
            queryset = queryset.filter(PermanentTemporary=permanent_temporary)
        if start_date:
            queryset = queryset.filter(CreatedByDate__gte=start_date)
        if end_date:
            queryset = queryset.filter(CreatedByDate__lte=end_date)
        if subpolicy_id:
            queryset = queryset.filter(SubPolicy=subpolicy_id)
        elif policy_id:
            queryset = queryset.filter(SubPolicy__PolicyId=policy_id)

        print(f"Filtered queryset count: {queryset.count()}")
        print("Executing Query:", queryset.query) 
        
        # Get counts for different statuses
        status_counts = {
            'approved': queryset.filter(Status='Approved').count(),
            'active': queryset.filter(Status='Active').count(),
            'scheduled': queryset.filter(Status='Schedule').count(),
            'rejected': queryset.filter(Status='Rejected').count(),
            'under_review': queryset.filter(Status='Under Review').count(),
            'active_compliance': queryset.filter(ActiveInactive='Active').count()
        }

        # Get counts for criticality levels
        criticality_counts = {
            'high': queryset.filter(Criticality='High').count(),
            'medium': queryset.filter(Criticality='Medium').count(),
            'low': queryset.filter(Criticality='Low').count()
        }

        # Calculate total findings
        total_findings = queryset.filter(IsRisk=True).count()
        
        # Calculate approval rate
        total_count = queryset.count()
        approval_rate = (status_counts['approved'] / total_count * 100) if total_count > 0 else 0

        return Response({
            'success': True,
            'data': {
                'summary': {
                    'status_counts': status_counts,
                    'criticality_counts': criticality_counts,
                    'total_count': total_count,
                    'total_findings': total_findings,
                    'approval_rate': round(approval_rate, 2)
                }
            }
        })

    except Exception as e:
        print(f"Error in get_compliance_dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliance_dashboard(request):
    """Centralized validation for all compliance input fields following allow-list pattern"""
    
    # Character sets for validation
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9\s\.\-_]+$')
    TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\.\,\!\?\-_\(\)\[\]\:\;\'\"\&\%\$\#\@\+\=\<\>\/\\\|\*\^\~\`\n\r\t]+$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]+$')
    VERSION_PATTERN = re.compile(r'^[0-9]+\.[0-9]+$')
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    # Allowed values for choice fields
    ALLOWED_CRITICALITY = ['High', 'Medium', 'Low']
    ALLOWED_MANDATORY_OPTIONAL = ['Mandatory', 'Optional']
    ALLOWED_MANUAL_AUTOMATIC = ['Manual', 'Automatic']
    ALLOWED_MATURITY_LEVELS = ['Initial', 'Developing', 'Defined', 'Managed', 'Optimizing']
    ALLOWED_STATUS = ['Under Review', 'Approved', 'Rejected', 'Active', 'Inactive']
    ALLOWED_ACTIVE_INACTIVE = ['Active', 'Inactive']
    ALLOWED_PERMANENT_TEMPORARY = ['Permanent', 'Temporary']
    ALLOWED_VERSIONING_TYPE = ['Minor', 'Major']
    ALLOWED_RISK_TYPES = ['Current', 'Residual', 'Inherent', 'Emerging', 'Accepted']
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input by removing potentially dangerous characters"""
        if not isinstance(value, str):
            return str(value) if value is not None else ''
        # Remove null bytes and control characters except newline, tab, carriage return
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value).strip()
    
    @staticmethod
    def validate_required_string(value: Any, field_name: str, max_length: Optional[int] = None, 
                                min_length: int = 1, pattern = None) -> str:
        """Validate required string fields with allow-list pattern"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required and cannot be empty")
        
        # Convert to string and sanitize
        str_value = ComplianceInputValidator.sanitize_string(value)
        
        if len(str_value) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters long")
        
        if max_length and len(str_value) > max_length:
            raise ValidationError(f"{field_name} must not exceed {max_length} characters")
        
        # Check against allowed pattern
        if pattern and not pattern.match(str_value):
            raise ValidationError(f"{field_name} contains invalid characters")
        
        return str_value
    
    @staticmethod
    def validate_optional_string(value: Any, field_name: str, max_length: Optional[int] = None, 
                                pattern = None) -> str:
        """Validate optional string fields with allow-list pattern"""
        if value is None or value == '':
            return ''
        
        str_value = ComplianceInputValidator.sanitize_string(value)
        
        if max_length and len(str_value) > max_length:
            raise ValidationError(f"{field_name} must not exceed {max_length} characters")
        
        if pattern and str_value and not pattern.match(str_value):
            raise ValidationError(f"{field_name} contains invalid characters")
        
        return str_value
    
    @staticmethod
    def validate_choice_field(value: Any, field_name: str, allowed_choices: List[str]) -> str:
        """Validate choice fields against allowed values"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        str_value = str(value).strip()
        if str_value not in allowed_choices:
            raise ValidationError(f"{field_name} must be one of: {', '.join(allowed_choices)}")
        
        return str_value
    
    @staticmethod
    def validate_boolean_field(value: Any, field_name: str) -> bool:
        """Validate boolean fields"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ['true', '1', 'yes']:
                return True
            elif value.lower() in ['false', '0', 'no', '']:
                return False
        if isinstance(value, int):
            return bool(value)
        
        raise ValidationError(f"{field_name} must be a valid boolean value")
    
    @staticmethod
    def validate_numeric_field(value: Any, field_name: str, min_val: Optional[float] = None, 
                              max_val: Optional[float] = None) -> float:
        """Validate numeric fields with range checking"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number")
        
        if min_val is not None and num_value < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and num_value > max_val:
            raise ValidationError(f"{field_name} must not exceed {max_val}")
        
        return num_value
    
    @staticmethod
    def validate_integer_field(value: Any, field_name: str, min_val: Optional[int] = None, 
                              max_val: Optional[int] = None) -> int:
        """Validate integer fields with range checking"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid integer")
        
        if min_val is not None and int_value < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and int_value > max_val:
            raise ValidationError(f"{field_name} must not exceed {max_val}")
        
        return int_value
    
    @staticmethod
    def validate_date_field(value: Any, field_name: str) -> str:
        """Validate date fields"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        str_value = str(value).strip()
        
        if not ComplianceInputValidator.DATE_PATTERN.match(str_value):
            raise ValidationError(f"{field_name} must be in YYYY-MM-DD format")
        
        try:
            datetime.datetime.strptime(str_value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(f"{field_name} must be a valid date")
        
        return str_value
    
    @staticmethod
    def calculate_new_version(current_version: str, versioning_type: str) -> str:
        """Calculate new version based on versioning type"""
        # print(f"  calculate_new_version called with: current_version='{current_version}', versioning_type='{versioning_type}'")
        try:
            # Parse current version (e.g., "2.3" becomes 2.3)
            current_float = float(current_version) if current_version else 1.0
            # print(f"  Parsed current_float: {current_float}")
            
            if versioning_type == 'Minor':
                # For minor: add 0.1 to current version (e.g., 2.3 -> 2.4)
                new_version = round(current_float + 0.1, 1)
                # print(f"  Minor version calculation: {current_float} + 0.1 = {new_version}")
            elif versioning_type == 'Major':
                # For major: increment major version and reset minor to 0 (e.g., 2.3 -> 3.0)
                major = int(current_float)
                new_version = float(major + 1)
                # print(f"  Major version calculation: int({current_float}) + 1 = {new_version}")
            else:
                # Default behavior (Major)
                major = int(current_float)
                new_version = float(major + 1)
                # print(f"  Default (Major) version calculation: int({current_float}) + 1 = {new_version}")
            
            result = str(new_version)
            # print(f"  Returning: '{result}'")
            return result
        except (ValueError, TypeError) as e:
            # If parsing fails, default to incrementing major version
            # print(f"  Error in version calculation: {e}, returning '2.0'")
            return "2.0"
    
    @staticmethod
    def clean_mitigation_data(mitigation_data: str) -> str:
        """
        Clean and format mitigation data for consistent storage and display.
        Handles simple JSON format: {"1": "First step", "2": "Second step"}
        """
        if not mitigation_data:
            return "{}"
        
        # If it's already a JSON string, try to parse and validate
        if isinstance(mitigation_data, str) and (mitigation_data.strip().startswith('{') or mitigation_data.strip().startswith('[')):
            try:
                import json
                parsed = json.loads(mitigation_data)
                
                # Handle the simple step format: {"1": "First step", "2": "Second step"}
                if isinstance(parsed, dict):
                    cleaned_mitigation = {}
                    
                    # Check if all keys are numeric strings and values are strings
                    for key, value in parsed.items():
                        if isinstance(key, str) and key.isdigit() and isinstance(value, str):
                            if value.strip():  # Only include non-empty steps
                                cleaned_mitigation[key] = value.strip()
                        elif isinstance(key, int) and isinstance(value, str):
                            if value.strip():  # Only include non-empty steps
                                cleaned_mitigation[str(key)] = value.strip()
                    
                    # If we have valid steps, return the cleaned version
                    if cleaned_mitigation:
                        return json.dumps(cleaned_mitigation, separators=(',', ':'))
                
                # Handle legacy array format - convert to simple format
                if isinstance(parsed, list):
                    cleaned_mitigation = {}
                    for i, step in enumerate(parsed):
                        if isinstance(step, str) and step.strip():
                            cleaned_mitigation[str(i + 1)] = step.strip()
                    
                    if cleaned_mitigation:
                        return json.dumps(cleaned_mitigation, separators=(',', ':'))
                
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as plain text
                pass
        
        # Handle plain text - convert to simple JSON format
        if isinstance(mitigation_data, str) and mitigation_data.strip():
            import json
            
            # Try to split by common delimiters to create steps
            text = mitigation_data.strip()
            
            # Split by numbered patterns (1., 2., etc.) or newlines
            import re
            steps_text = re.split(r'(?:^|\n)\s*\d+\.\s*', text)
            if len(steps_text) > 1:
                # Remove empty first element if it exists
                if not steps_text[0].strip():
                    steps_text = steps_text[1:]
            else:
                # Split by newlines or semicolons
                steps_text = [s.strip() for s in re.split(r'[;\n]', text) if s.strip()]
            
            # If no clear steps found, treat as single step
            if not steps_text or (len(steps_text) == 1 and not steps_text[0].strip()):
                steps_text = [text]
            
            # Create step objects in simple format
            cleaned_mitigation = {}
            for i, step_text in enumerate(steps_text):
                if step_text.strip():
                    cleaned_mitigation[str(i + 1)] = step_text.strip()
            
            if cleaned_mitigation:
                return json.dumps(cleaned_mitigation, separators=(',', ':'))
        
        return "{}"
    
    @staticmethod
    def validate_mitigation_json(mitigation_data: str) -> bool:
        """
        Validate that mitigation data is properly formatted JSON with valid structure
        Expected format: {"1": "First step", "2": "Second step"}
        """
        if not mitigation_data:
            return True  # Empty is valid
        
        try:
            import json
            parsed = json.loads(mitigation_data)
            
            # Must be a dictionary
            if not isinstance(parsed, dict):
                return False
            
            # Check if all keys are numeric strings and values are non-empty strings
            for key, value in parsed.items():
                # Key must be a string representation of a number
                if not isinstance(key, str) or not key.isdigit():
                    return False
                
                # Value must be a non-empty string
                if not isinstance(value, str) or not value.strip():
                    return False
            
            return True
            
        except json.JSONDecodeError:
            return False
    
    @classmethod
    def validate_compliance_data(cls, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main validation method for compliance data using allow-list approach"""
        validated_data = {}
        errors = {}
        
        try:
            # Validate SubPolicy (required foreign key)
            validated_data['SubPolicy'] = cls.validate_integer_field(
                request_data.get('SubPolicy'), 'SubPolicy', min_val=1
            )
        except ValidationError as e:
            errors['SubPolicy'] = [str(e)]
        
        try:
            # Validate ComplianceTitle (required, max 145 chars)
            validated_data['ComplianceTitle'] = cls.validate_required_string(
                request_data.get('ComplianceTitle'), 'ComplianceTitle', 
                max_length=145, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceTitle'] = [str(e)]
        
        try:
            # Validate ComplianceItemDescription (required text field)
            validated_data['ComplianceItemDescription'] = cls.validate_required_string(
                request_data.get('ComplianceItemDescription'), 'ComplianceItemDescription',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceItemDescription'] = [str(e)]
        
        try:
            # Validate ComplianceType (required, max 100 chars)
            validated_data['ComplianceType'] = cls.validate_required_string(
                request_data.get('ComplianceType'), 'ComplianceType',
                max_length=100, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceType'] = [str(e)]
        
        try:
            # Validate Scope (required text field)
            validated_data['Scope'] = cls.validate_required_string(
                request_data.get('Scope'), 'Scope',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['Scope'] = [str(e)]
        
        try:
            # Validate Objective (required text field)
            validated_data['Objective'] = cls.validate_required_string(
                request_data.get('Objective'), 'Objective',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['Objective'] = [str(e)]
        
        try:
            # Validate BusinessUnitsCovered (required, max 225 chars)
            validated_data['BusinessUnitsCovered'] = cls.validate_required_string(
                request_data.get('BusinessUnitsCovered'), 'BusinessUnitsCovered',
                max_length=225, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['BusinessUnitsCovered'] = [str(e)]
        
        try:
            # Validate IsRisk (boolean)
            validated_data['IsRisk'] = cls.validate_boolean_field(
                request_data.get('IsRisk', False), 'IsRisk'
            )
        except ValidationError as e:
            errors['IsRisk'] = [str(e)]
        
        # If IsRisk is True, validate risk-related fields
        if validated_data.get('IsRisk', False):
            try:
                validated_data['PossibleDamage'] = cls.validate_required_string(
                    request_data.get('PossibleDamage'), 'PossibleDamage',
                    max_length=5000, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['PossibleDamage'] = [str(e)]
            
            try:
                validated_data['PotentialRiskScenarios'] = cls.validate_required_string(
                    request_data.get('PotentialRiskScenarios'), 'PotentialRiskScenarios',
                    max_length=5000, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['PotentialRiskScenarios'] = [str(e)]
            
            try:
                validated_data['RiskType'] = cls.validate_required_string(
                    request_data.get('RiskType'), 'RiskType',
                    max_length=45, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['RiskType'] = [str(e)]
            
            try:
                validated_data['RiskCategory'] = cls.validate_required_string(
                    request_data.get('RiskCategory'), 'RiskCategory',
                    max_length=45, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['RiskCategory'] = [str(e)]
            
            try:
                validated_data['RiskBusinessImpact'] = cls.validate_required_string(
                    request_data.get('RiskBusinessImpact'), 'RiskBusinessImpact',
                    max_length=45, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['RiskBusinessImpact'] = [str(e)]
        else:
            # Optional fields when IsRisk is False
            validated_data['PossibleDamage'] = cls.validate_optional_string(
                request_data.get('PossibleDamage'), 'PossibleDamage',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
            validated_data['PotentialRiskScenarios'] = cls.validate_optional_string(
                request_data.get('PotentialRiskScenarios'), 'PotentialRiskScenarios',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
            validated_data['RiskType'] = cls.validate_optional_string(
                request_data.get('RiskType'), 'RiskType',
                max_length=45, pattern=cls.TEXT_PATTERN
            )
            validated_data['RiskCategory'] = cls.validate_optional_string(
                request_data.get('RiskCategory'), 'RiskCategory',
                max_length=45, pattern=cls.TEXT_PATTERN
            )
            validated_data['RiskBusinessImpact'] = cls.validate_optional_string(
                request_data.get('RiskBusinessImpact'), 'RiskBusinessImpact',
                max_length=45, pattern=cls.TEXT_PATTERN
            )
        
        try:
            # Validate and clean mitigation (JSON step-by-step format)
            raw_mitigation = request_data.get('mitigation')
            # Always use format_mitigation_data to handle both string and object types
            formatted_mitigation = format_mitigation_data(raw_mitigation)
            # If risk requires mitigation but none provided, add error
            if validated_data.get('IsRisk', False) and not formatted_mitigation:
                errors['mitigation'] = ["At least one mitigation step is required for risks"]
            else:
                validated_data['mitigation'] = formatted_mitigation
                # Debug log
                #print(f"DEBUG: Validated mitigation data: {formatted_mitigation}")
        except Exception as e:
            errors['mitigation'] = [f"Error processing mitigation data: {str(e)}"]
        
        try:
            # Validate Criticality (required choice field)
            validated_data['Criticality'] = cls.validate_choice_field(
                request_data.get('Criticality'), 'Criticality', cls.ALLOWED_CRITICALITY
            )
        except ValidationError as e:
            errors['Criticality'] = [str(e)]
        
        try:
            # Validate MandatoryOptional (required choice field)
            validated_data['MandatoryOptional'] = cls.validate_choice_field(
                request_data.get('MandatoryOptional'), 'MandatoryOptional', cls.ALLOWED_MANDATORY_OPTIONAL
            )
        except ValidationError as e:
            errors['MandatoryOptional'] = [str(e)]
        
        try:
            # Validate ManualAutomatic (required choice field)
            validated_data['ManualAutomatic'] = cls.validate_choice_field(
                request_data.get('ManualAutomatic'), 'ManualAutomatic', cls.ALLOWED_MANUAL_AUTOMATIC
            )
        except ValidationError as e:
            errors['ManualAutomatic'] = [str(e)]
        
        try:
            # Validate Impact (required numeric field, 1-10)
            validated_data['Impact'] = cls.validate_numeric_field(
                request_data.get('Impact'), 'Impact', min_val=1.0, max_val=10.0
            )
        except ValidationError as e:
            errors['Impact'] = [str(e)]
        
        try:
            # Validate Probability (required numeric field, 1-10)
            validated_data['Probability'] = cls.validate_numeric_field(
                request_data.get('Probability'), 'Probability', min_val=1.0, max_val=10.0
            )
        except ValidationError as e:
            errors['Probability'] = [str(e)]
        
        try:
            # Validate ComplianceVersion (required, max 50 chars, version pattern)
            validated_data['ComplianceVersion'] = cls.validate_required_string(
                request_data.get('ComplianceVersion', '1.0'), 'ComplianceVersion',
                max_length=50, pattern=cls.VERSION_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceVersion'] = [str(e)]
        
        try:
            # Validate Applicability (optional, max 450 chars)
            validated_data['Applicability'] = cls.validate_optional_string(
                request_data.get('Applicability'), 'Applicability',
                max_length=450, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['Applicability'] = [str(e)]
        
        try:
            # Validate Identifier (optional, max 45 chars, identifier pattern)
            identifier = request_data.get('Identifier', '').strip()
            if identifier:
                validated_data['Identifier'] = cls.validate_optional_string(
                    identifier, 'Identifier', max_length=45, pattern=cls.IDENTIFIER_PATTERN
                )
            else:
                validated_data['Identifier'] = ''
        except ValidationError as e:
            errors['Identifier'] = [str(e)]
            # Set to empty string if validation fails, so auto-generation will be used
            validated_data['Identifier'] = ''
        
        try:
            # Validate reviewer (required integer)
            validated_data['reviewer'] = cls.validate_integer_field(
                request_data.get('reviewer'), 'reviewer', min_val=1
            )
        except ValidationError as e:
            errors['reviewer'] = [str(e)]
        
        try:
            # Validate ApprovalDueDate (required date)
            validated_data['ApprovalDueDate'] = cls.validate_date_field(
                request_data.get('ApprovalDueDate'), 'ApprovalDueDate'
            )
        except ValidationError as e:
            errors['ApprovalDueDate'] = [str(e)]
        
        # Set default values for system fields
        validated_data['Status'] = 'Under Review'
        validated_data['ActiveInactive'] = 'Inactive'
        validated_data['PermanentTemporary'] = 'Permanent'
        validated_data['MaturityLevel'] = 'Initial'
        
        # Always copy CreatedByName from request_data if present (no validation, just sanitize)
        if 'CreatedByName' in request_data:
            validated_data['CreatedByName'] = str(request_data['CreatedByName']).strip()
        
        if errors:
            raise ValidationError(errors)
        
        return validated_data

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliances_by_subpolicy(request, subpolicy_id):
    try:
        # Verify subpolicy exists first
        subpolicy = get_object_or_404(SubPolicy, SubPolicyId=subpolicy_id)
       
        # Get all compliances for this subpolicy
        compliances = Compliance.objects.filter(SubPolicy=subpolicy_id)
       
        # Create a dictionary to store compliance groups
        compliance_groups = {}
       
        # First pass: Create groups based on Identifier
        for compliance in compliances:
            if compliance.Identifier not in compliance_groups:
                compliance_groups[compliance.Identifier] = []
            compliance_groups[compliance.Identifier].append(compliance)
       
        # Second pass: Sort each group by version number
        for identifier in compliance_groups:
            compliance_groups[identifier].sort(
                key=lambda x: float(x.ComplianceVersion) if x.ComplianceVersion and x.ComplianceVersion.strip() else 0.0,
                reverse=True
            )
       
        # Convert to list and sort groups by latest version's creation date
        sorted_groups = sorted(
            compliance_groups.values(),
            key=lambda group: group[0].CreatedByDate if group[0].CreatedByDate else datetime.now(),
            reverse=True
        )
       
        # Create grouped structure for the frontend
        serialized_groups = []
        for group in sorted_groups:
            group_data = []
            for compliance in group:
                serializer = ComplianceListSerializer(compliance)
                compliance_data = serializer.data
                
                # Add previous version ID reference if it exists
                if compliance.PreviousComplianceVersionId:
                    compliance_data['PreviousComplianceVersionId'] = compliance.PreviousComplianceVersionId.ComplianceId
                else:
                    compliance_data['PreviousComplianceVersionId'] = None
                
                group_data.append(compliance_data)
            serialized_groups.append(group_data)
       
        return Response({
            'success': True,
            'data': serialized_groups
        })
    except SubPolicy.DoesNotExist:
        return Response({
            'success': False,
            'message': f'SubPolicy with id {subpolicy_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error in get_compliances_by_subpolicy: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while fetching compliances'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([ComplianceApprovePermission])
@compliance_approve_required
def submit_compliance_review(request, approval_id):
    try:
        print(f"\n=== SUBMIT COMPLIANCE REVIEW DEBUG ===")
        print(f"Approval ID: {approval_id}")
        print(f"Request data: {request.data}")
        
        approval = get_object_or_404(ComplianceApproval, ApprovalId=approval_id)
        print(f"Found approval: {approval.ApprovalId}, Identifier: {approval.Identifier}")
        
        if 'ApprovedNot' in request.data:
            approved_not = request.data.get('ApprovedNot')
        elif 'ExtractedData' in request.data and 'compliance_approval' in request.data['ExtractedData']:
            approved_not = request.data['ExtractedData']['compliance_approval'].get('approved')
        else:
            approved_not = request.data.get('approved', False)
        if isinstance(approved_not, str):
            approved_not = approved_not.lower() == 'true'
        print(f"Received approval request with approved_not value: {approved_not} (type: {type(approved_not)})")
        
        # Get remarks from multiple possible sources
        remarks = ''
        if 'remarks' in request.data:
            remarks = request.data.get('remarks', '')
        elif 'ExtractedData' in request.data and 'compliance_approval' in request.data['ExtractedData']:
            remarks = request.data['ExtractedData']['compliance_approval'].get('remarks', '')
        
        print(f"Remarks: {remarks}")
        
        extracted_data = approval.ExtractedData
        # --- Ensure compliance_approval is saved in ExtractedData for both approvals and rejections ---
        if 'compliance_approval' not in extracted_data:
            extracted_data['compliance_approval'] = {}
        
        # Update the original approval record's ExtractedData but keep ApprovedNot as NULL
        # This ensures the user version remains pending while the reviewer version gets the approval status
        if approved_not is False:
            # For rejections, save remarks and set approved to false in ExtractedData only
            extracted_data['compliance_approval']['remarks'] = remarks
            extracted_data['compliance_approval']['approved'] = False
            
            print(f"Saved rejection remarks for compliance review: {remarks}")
            print(f"Updated ExtractedData compliance_approval: {extracted_data['compliance_approval']}")
        else:
            # For approvals, set approved to true and clear any previous remarks in ExtractedData only
            extracted_data['compliance_approval']['approved'] = True
            extracted_data['compliance_approval']['remarks'] = ''
            
            print(f"Saved approval status for compliance review")
            print(f"Updated ExtractedData compliance_approval: {extracted_data['compliance_approval']}")
            
        # Update ExtractedData but keep ApprovedNot as NULL for user version
        approval.ExtractedData = extracted_data
        approval.save()
        print(f"Updated original approval record ExtractedData")
        
        current_version = approval.Version
        # Resolve creator/reviewer from the user edit being reviewed (the specific u*),
        # not necessarily from the very first u1 submission
        all_versions = ComplianceApproval.objects.filter(Identifier=approval.Identifier)
        if approval.Version and approval.Version.startswith('u'):
            # The provided approval is the user-submitted edit under review
            original_user_id = approval.UserId
            original_reviewer_id = approval.ReviewerId
        else:
            # Fallback: use the latest user-submitted version for this Identifier
            latest_user_version = all_versions.filter(Version__startswith='u').order_by('-ApprovalId').first()
            original_user_id = latest_user_version.UserId if latest_user_version else approval.UserId
            original_reviewer_id = latest_user_version.ReviewerId if latest_user_version else approval.ReviewerId
        
        print(f"Version info - Current: {current_version}, Original User ID: {original_user_id}, Original Reviewer ID: {original_reviewer_id}")
        
        # Create a new approval record for both approvals and rejections
        # This ensures proper versioning with "r" versions for reviewer actions
        highest_r_version = 0
        for pa in all_versions:
            if pa.Version and pa.Version.startswith('r'):
                try:
                    version_num = int(pa.Version[1:])
                    if version_num > highest_r_version:
                        highest_r_version = version_num
                except ValueError:
                    continue
        new_version = f"r{highest_r_version + 1}"
        
        print(f"Creating new reviewer version: {new_version}")
        
        # --- Ensure compliance_approval is properly set in new reviewer version ---
        if 'compliance_approval' not in extracted_data:
            extracted_data['compliance_approval'] = {}
        
        if approved_not is False:
            # For rejections, save remarks and set approved to false
            extracted_data['compliance_approval']['remarks'] = remarks
            extracted_data['compliance_approval']['approved'] = False
            extracted_data['Status'] = 'Rejected'
        else:
            # For approvals, set approved to true and clear any previous remarks
            extracted_data['compliance_approval']['approved'] = True
            extracted_data['compliance_approval']['remarks'] = ''
            extracted_data['Status'] = 'Approved'
        
        # Create new reviewer version for both approvals and rejections
        try:
            print(f"Creating new approval with data:")
            print(f"  Identifier: {approval.Identifier}")
            print(f"  UserId: {original_user_id}")
            print(f"  ReviewerId: {original_reviewer_id}")
            print(f"  ApprovedNot: {approved_not}")
            print(f"  Version: {new_version}")
            print(f"  PolicyId: {approval.PolicyId}")
            print(f"  FrameworkId: {approval.FrameworkId_id}")
            
            # Validate required fields
            if not approval.Identifier:
                raise ValueError("Identifier is required")
            if not original_user_id:
                raise ValueError("UserId is required")
            if not original_reviewer_id:
                raise ValueError("ReviewerId is required")
            if not new_version:
                raise ValueError("Version is required")
            
            # Prepare creation data
            creation_data = {
                'Identifier': approval.Identifier,
                'ExtractedData': extracted_data,
                'UserId': original_user_id,
                'ReviewerId': original_reviewer_id,
                'ApprovedNot': approved_not,
                'Version': new_version,
                'ApprovalDueDate': approval.ApprovalDueDate,
                'PolicyId': approval.PolicyId,
            }
            
            # Only add FrameworkId if it's not None and is a valid integer
            if approval.FrameworkId_id is not None:
                try:
                    # Ensure FrameworkId is a valid integer
                    framework_id = int(approval.FrameworkId_id)
                    # Use _id suffix to assign the foreign key ID directly
                    creation_data['FrameworkId_id'] = framework_id
                    print(f"  Adding FrameworkId_id: {framework_id}")
                except (ValueError, TypeError) as e:
                    print(f"  Warning: Invalid FrameworkId '{approval.FrameworkId_id}', skipping: {e}")
                    # Don't add FrameworkId if it's invalid
            else:
                print(f"  FrameworkId is None, not adding to creation data")
            
            print(f"Final creation data keys: {list(creation_data.keys())}")
            
            new_approval = ComplianceApproval.objects.create(**creation_data)
            print(f"✅ Successfully created new approval record with ID: {new_approval.ApprovalId}")
        except Exception as create_error:
            print(f"❌ ERROR creating ComplianceApproval: {str(create_error)}")
            print(f"Error type: {type(create_error)}")
            import traceback
            traceback.print_exc()
            raise create_error
        
        # Set approval date on the new reviewer version
        new_approval.ApprovedDate = datetime.date.today()
        new_approval.save()
        
        print(f"Created new reviewer approval record with ID {new_approval.ApprovalId}, Version: {new_version}, Status: {'Approved' if approved_not else 'Rejected'}")
        
        # ===== CRITICAL: UPDATE THE ACTUAL COMPLIANCE RECORD =====
        if 'SubPolicy' in extracted_data or approval.Identifier:
            try:
                # Find the compliance being reviewed by Identifier (not by Status)
                # This allows updating compliance status even after it has been approved/rejected before
                current_compliance = Compliance.objects.filter(
                    Identifier=approval.Identifier
                ).order_by('-ComplianceId').first()  # Get the latest compliance with this identifier
                
                if current_compliance:
                    print(f"\n=== UPDATING COMPLIANCE RECORD ===")
                    print(f"Processing compliance: {current_compliance.ComplianceId}")
                    print(f"Current compliance status before update: {current_compliance.Status}")
                    print(f"Current compliance ActiveInactive before update: {current_compliance.ActiveInactive}")
                    
                    if approved_not is True:
                        # If approved, set current to Approved and Active
                        current_compliance.Status = 'Approved'
                        current_compliance.ActiveInactive = 'Active'
                        print(f"Setting compliance to Approved and Active")
                        
                        # Get and deactivate the previous version if it exists
                        if current_compliance.PreviousComplianceVersionId:
                            try:
                                prev_compliance = current_compliance.PreviousComplianceVersionId
                                if prev_compliance.ActiveInactive == 'Active':
                                    prev_compliance.ActiveInactive = 'Inactive'
                                    prev_compliance.save()
                                    print(f"Deactivated previous version: {prev_compliance.ComplianceId}")
                            except Exception as e:
                                print(f"Error deactivating previous version: {e}")
                    else:
                        # If rejected, mark as rejected
                        current_compliance.Status = 'Rejected'
                        current_compliance.ActiveInactive = 'Inactive'
                        print(f"Setting compliance to Rejected and Inactive")
                        
                    current_compliance.save()
                    print(f"✅ SUCCESSFULLY UPDATED compliance status to: {current_compliance.Status}")
                    print(f"✅ SUCCESSFULLY UPDATED compliance ActiveInactive to: {current_compliance.ActiveInactive}")
                    
                    # Double-check the update worked
                    updated_compliance = Compliance.objects.get(ComplianceId=current_compliance.ComplianceId)
                    print(f"Verification - Compliance {updated_compliance.ComplianceId} now has Status: {updated_compliance.Status}, ActiveInactive: {updated_compliance.ActiveInactive}")

                    # Send notification to compliance creator (email)
                    try:
                        from ...routes.Global.notification_service import NotificationService
                        notification_service = NotificationService()
                        
                        # Get creator's email
                        creator_id = approval.UserId
                        creator_email, creator_name = notification_service.get_user_email_by_id(creator_id)
                        
                        if creator_email:
                            # Send notification email
                            notification_result = notification_service.send_compliance_review_notification(
                                compliance=current_compliance,
                                reviewer_decision=approved_not,
                                creator_id=creator_id,
                                remarks=remarks
                            )
                            print(f"Review notification sent to {creator_name} ({creator_email}): {notification_result}")
                        else:
                            print(f"No email found for creator ID {creator_id}")
                    except Exception as e:
                        print(f"Error sending compliance review notification: {str(e)}")
                        # Continue even if notification fails
                    
                else:
                    print(f"❌ ERROR: No compliance found for Identifier {approval.Identifier}")
                    print(f"Available compliances with this identifier:")
                    all_compliances = Compliance.objects.filter(Identifier=approval.Identifier)
                    for comp in all_compliances:
                        print(f"  - ComplianceId: {comp.ComplianceId}, Status: {comp.Status}, ActiveInactive: {comp.ActiveInactive}")
                        
                    # Try finding by other criteria if identifier search fails
                    if extracted_data.get('SubPolicy'):
                        subpolicy_id = extracted_data.get('SubPolicy')
                        title = extracted_data.get('ComplianceTitle', '')
                        description = extracted_data.get('ComplianceItemDescription', '')
                        
                        print(f"Trying to find compliance by SubPolicy {subpolicy_id}, Title: {title}")
                        alternative_compliance = Compliance.objects.filter(
                            SubPolicy_id=subpolicy_id
                        ).filter(
                            models.Q(ComplianceTitle__icontains=title[:50]) |
                            models.Q(ComplianceItemDescription__icontains=description[:50])
                        ).order_by('-ComplianceId').first()
                        
                        if alternative_compliance:
                            print(f"Found alternative compliance: {alternative_compliance.ComplianceId}")
                            # Update this compliance instead
                            if approved_not is True:
                                alternative_compliance.Status = 'Approved'
                                alternative_compliance.ActiveInactive = 'Active'
                            else:
                                alternative_compliance.Status = 'Rejected'
                                alternative_compliance.ActiveInactive = 'Inactive'
                            alternative_compliance.save()
                            print(f"✅ Updated alternative compliance status to: {alternative_compliance.Status}")
                        else:
                            print(f"❌ No alternative compliance found either")
                            
            except Exception as e:
                print(f"❌ ERROR processing compliance update: {str(e)}")
                import traceback
                traceback.print_exc()
                
        # In-app notifications (push-style) for creator and reviewer about the review decision
        try:
            decision_label = "Approved" if approved_not is True else ("Rejected" if approved_not is False else "Updated")

            # Notify creator
            creator_id = approval.UserId
            if creator_id:
                create_in_app_notification(
                    user_id=creator_id,
                    title="Compliance Review Completed",
                    message=f"Your compliance {current_compliance.ComplianceId} has been {decision_label}.",
                    category="compliance",
                    priority="high",
                )

            # Notify reviewer
            reviewer_user_id = approval.ReviewerId
            if reviewer_user_id:
                create_in_app_notification(
                    user_id=reviewer_user_id,
                    title="Compliance Review Submitted",
                    message=f"You submitted a review for compliance {current_compliance.ComplianceId} with status {decision_label}.",
                    category="compliance",
                    priority="medium",
                )
        except Exception as e:
            print(f"Error creating in-app notifications for compliance review: {str(e)}")

        # Prepare response data
        response_data = {
            'success': True,
            'message': 'Review submitted successfully',
            'approved': approved_not,
            'approval_id': new_approval.ApprovalId,
            'version': new_version
        }
        
        print(f"✅ REVIEW SUBMISSION COMPLETE")
        print(f"Response data: {response_data}")
        print(f"=== END SUBMIT COMPLIANCE REVIEW DEBUG ===\n")
        
        return Response(response_data)
        
    except Exception as e:
        print(f"❌ ERROR in submit_compliance_review: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([ComplianceApprovePermission])
@compliance_approve_required
def resubmit_compliance_approval(request, approval_id):
    try:
        # Use only() to fetch only needed fields for faster query
        approval = ComplianceApproval.objects.only(
            'ApprovalId', 'Identifier', 'ExtractedData', 'UserId', 'ReviewerId', 
            'Version', 'PolicyId', 'ApprovalDueDate', 'FrameworkId_id'
        ).get(ApprovalId=approval_id)
        extracted_data = request.data.get('ExtractedData')
        if not extracted_data:
            return Response({'error': 'ExtractedData is required'}, status=status.HTTP_400_BAD_REQUEST)
        # Get the current user who is resubmitting (the latest creator)
        from ...rbac.utils import RBACUtils
        from ...models import Users
        
        try:
            current_user_id = RBACUtils.get_user_id_from_request(request)
        except Exception:
            current_user_id = None
        if not current_user_id and hasattr(request, 'user') and getattr(request.user, 'UserId', None):
            current_user_id = request.user.UserId
        if not current_user_id:
            current_user_id = request.session.get('user_id')
        if not current_user_id:
            # Fallback: use the most recent user edit (latest u*) - single optimized query
            latest_user_version = ComplianceApproval.objects.filter(
                Identifier=approval.Identifier,
                Version__startswith='u'
            ).order_by('-ApprovalId').only('UserId', 'ReviewerId').first()
            current_user_id = latest_user_version.UserId if latest_user_version else approval.UserId
        
        # Get the current user's name (the latest creator)
        current_user_name = 'Unknown User'
        if current_user_id:
            try:
                user_obj = Users.objects.only('FirstName', 'LastName', 'UserName').get(UserId=current_user_id)
                current_user_name = (user_obj.FirstName + ' ' + user_obj.LastName).strip() if user_obj.FirstName or user_obj.LastName else user_obj.UserName
            except Exception:
                current_user_name = 'Unknown User'
        
        # Keep reviewer consistent for resubmissions - reuse the query result if available
        if 'latest_user_version' not in locals():
            latest_user_version = ComplianceApproval.objects.filter(
                Identifier=approval.Identifier,
                Version__startswith='u'
            ).order_by('-ApprovalId').only('ReviewerId').first()
        original_user_id = current_user_id  # Use the current logged-in user as the latest creator
        original_reviewer_id = latest_user_version.ReviewerId if latest_user_version else approval.ReviewerId
        
        # Update CreatedByName in extracted_data to the current user
        extracted_data['CreatedByName'] = current_user_name
        
        # Find the next user version (uN) for this Identifier
        # Use values_list to only fetch Version field, minimizing data transfer
        u_versions = ComplianceApproval.objects.filter(
            Identifier=approval.Identifier,
            Version__startswith='u'
        ).only('Version').values_list('Version', flat=True)
        
        # Find the highest version number
        highest_u_version = 0
        for version_str in u_versions:
            if version_str and len(version_str) > 1:
                try:
                    version_num = int(version_str[1:])  # Extract number after 'u'
                    if version_num > highest_u_version:
                        highest_u_version = version_num
                except ValueError:
                    continue
        
        new_version = f"u{highest_u_version + 1}"
        
        if 'compliance_approval' in extracted_data:
            extracted_data['compliance_approval']['approved'] = None
            extracted_data['compliance_approval']['remarks'] = ''
            extracted_data['compliance_approval']['inResubmission'] = True
            extracted_data['compliance_approval'].pop('reviewer_id', None)
            extracted_data['compliance_approval'].pop('reviewed_date', None)
        else:
            extracted_data['compliance_approval'] = {
                'approved': None,
                'remarks': '',
                'inResubmission': True
            }
        
        # Clear any old rejection remarks fields for consistency
        if 'rejection_remarks' in extracted_data:
            del extracted_data['rejection_remarks']
        
        # Ensure Impact and Probability fields are present
        # Fetch compliance once if needed for both Impact and Probability
        compliance_for_fields = None
        if ('Impact' not in extracted_data or not extracted_data['Impact']) or ('Probability' not in extracted_data or not extracted_data['Probability']):
            # Try to get from the original approval first
            if approval.ExtractedData:
                if ('Impact' not in extracted_data or not extracted_data['Impact']) and approval.ExtractedData.get('Impact'):
                    extracted_data['Impact'] = approval.ExtractedData['Impact']
                if ('Probability' not in extracted_data or not extracted_data['Probability']) and approval.ExtractedData.get('Probability'):
                    extracted_data['Probability'] = approval.ExtractedData['Probability']
            
            # If still missing, fetch from Compliance table (only once)
            if ('Impact' not in extracted_data or not extracted_data['Impact']) or ('Probability' not in extracted_data or not extracted_data['Probability']):
                try:
                    compliance_for_fields = Compliance.objects.only('Impact', 'Probability').get(Identifier=approval.Identifier)
                    if 'Impact' not in extracted_data or not extracted_data['Impact']:
                        extracted_data['Impact'] = compliance_for_fields.Impact
                    if 'Probability' not in extracted_data or not extracted_data['Probability']:
                        extracted_data['Probability'] = compliance_for_fields.Probability
                except Compliance.DoesNotExist:
                    pass
        
        extracted_data['Status'] = 'Under Review'
        extracted_data['ActiveInactive'] = 'Inactive'
        
        # Validate FrameworkId from original approval
        framework_id = approval.FrameworkId_id
        if framework_id is None:
            return Response({
                'error': 'Original approval must have a FrameworkId. Cannot resubmit without a framework.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure framework_id is an integer
        try:
            framework_id = int(framework_id)
        except (ValueError, TypeError) as e:
            return Response({
                'error': f'Invalid FrameworkId in original approval: {str(e)}. FrameworkId must be a valid integer.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize reviewer_id and user_id to integers
        try:
            original_reviewer_id = int(original_reviewer_id) if original_reviewer_id else None
            original_user_id = int(original_user_id) if original_user_id else None
        except (ValueError, TypeError) as e:
            return Response({
                'error': f'Invalid ReviewerId or UserId: {str(e)}. Both must be valid integers.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not original_reviewer_id:
            return Response({
                'error': 'ReviewerId is required. Cannot resubmit without a reviewer.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        new_approval = ComplianceApproval.objects.create(
            Identifier=approval.Identifier,
            ExtractedData=extracted_data,
            UserId=original_user_id,
            ReviewerId=original_reviewer_id,  # Ensure this is an integer
            ApprovedNot=0,
            Version=new_version,
            PolicyId=approval.PolicyId,
            ApprovalDueDate=approval.ApprovalDueDate,
            FrameworkId_id=framework_id  # Copy FrameworkId from original approval (use _id suffix for foreign key)
        )
        
        # Return response immediately for fast UI feedback
        response_data = {
            'success': True,
            'message': 'Compliance review resubmitted successfully',
            'ApprovalId': new_approval.ApprovalId,
            'Version': new_version
        }
        
        # Update compliance status asynchronously (non-blocking)
        # This runs after the response is sent, so it doesn't delay the user
        def update_compliance_async():
            try:
                if not compliance_for_fields:
                    compliance = Compliance.objects.filter(Identifier=approval.Identifier).order_by('-ComplianceVersion').only('ComplianceId', 'Status', 'ActiveInactive', 'CreatedByName', 'CreatedByDate').first()
                else:
                    compliance = compliance_for_fields
                
                if compliance:
                    compliance.Status = 'Under Review'
                    compliance.ActiveInactive = 'Inactive'
                    compliance.CreatedByName = current_user_name
                    compliance.CreatedByDate = datetime.date.today()
                    compliance.save(update_fields=['Status', 'ActiveInactive', 'CreatedByName', 'CreatedByDate'])
            except Exception as e:
                # Log error but don't fail the request
                print(f"Error updating compliance status (non-blocking): {str(e)}")
        
        # Use threading to update compliance after response
        import threading
        threading.Thread(target=update_compliance_async, daemon=True).start()
        
        return Response(response_data)
    except PolicyApproval.DoesNotExist:
        return Response({'error': 'Policy approval not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("Error in resubmit_compliance_approval:", str(e))
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
@api_view(['GET'])
@permission_classes([ComplianceVersioningPermission])
@compliance_versioning_required
def get_compliance_versioning(request):
    """
    Returns compliance versioning data for the frontend.
    """
    try:
        # You can customize this to return whatever versioning data you need
        # For now, we'll just return a success message
        return Response({
            'success': True,
            'message': 'Compliance versioning API endpoint',
            'data': []
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_policy_approvals_by_reviewer(request):
    try:
        from ...routes.Policy.framework_filter_helper import get_active_framework_filter
        from ...models import Users
        
        # Helper function to get user name by ID
        def get_user_name_by_id(user_id):
            """Get user's full name or username by UserId"""
            if not user_id:
                return None
            try:
                user = Users.objects.get(UserId=user_id)
                # Try to get full name first
                if user.FirstName or user.LastName:
                    full_name = f"{user.FirstName or ''} {user.LastName or ''}".strip()
                    if full_name:
                        return full_name
                # Fallback to username
                return user.UserName if user.UserName else None
            except Users.DoesNotExist:
                return None
            except Exception:
                return None
        
        # Get reviewer ID from session first, then from request params, then default
        reviewer_id = request.session.get('user_id')
        if not reviewer_id:
            reviewer_id = request.query_params.get('reviewer_id', 1)
        
        # Get framework filter from session
        framework_id = get_active_framework_filter(request)
        
        # print(f"Session user_id: {request.session.get('user_id')}")
        # print(f"Using reviewer_id: {reviewer_id}")
        # print(f"Framework filter: {framework_id}")
        # print(f"\n\n==== DEBUGGING DEACTIVATION REQUESTS ====")
        # print(f"Fetching approvals for reviewer_id: {reviewer_id}")
        
        # First get all compliances that are Under Review
        under_review_compliances = Compliance.objects.filter(
            Status='Under Review',
            Identifier__isnull=False,
            Identifier__gt=''  # Exclude empty strings
        ).select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
        
        # Apply framework filter if one is selected
        if framework_id:
            under_review_compliances = under_review_compliances.filter(
                SubPolicy__PolicyId__FrameworkId__FrameworkId=framework_id
            )
        
        # print(f"Found {under_review_compliances.count()} compliances under review")
        
        # Get their corresponding policy approvals
        approvals = []
        for compliance in under_review_compliances:
            # Determine the original creator for this identifier as a NUMERIC id (no defaults)
            first_user_version = ComplianceApproval.objects.filter(
                Identifier=compliance.Identifier,
                Version__startswith='u'
            ).order_by('ApprovalId').first()
            creator_id = None
            if first_user_version:
                creator_id = first_user_version.UserId
            else:
                any_version = ComplianceApproval.objects.filter(
                    Identifier=compliance.Identifier
                ).order_by('ApprovalId').first()
                if any_version:
                    creator_id = any_version.UserId
            # If still unknown, try resolve by CreatedByName -> Users.UserId
            if not creator_id and getattr(compliance, 'CreatedByName', None):
                try:
                    from ...models import Users
                    user_match = Users.objects.filter(UserName=compliance.CreatedByName).values('UserId').first()
                    if user_match:
                        creator_id = user_match['UserId']
                except Exception:
                    pass
            # Finally, fall back to the requester if provided (but never a hardcoded default)
            if not creator_id:
                from ...rbac.utils import RBACUtils
                try:
                    creator_id = RBACUtils.get_user_id_from_request(request)
                except Exception:
                    creator_id = request.query_params.get('user_id') or request.data.get('user_id')
            # Validate numeric creator_id
            try:
                if isinstance(creator_id, str):
                    creator_id = int(creator_id)
            except Exception:
                return Response({
                    'success': False,
                    'message': "Unable to determine numeric creator user id for this compliance; cannot create u1"
                }, status=status.HTTP_400_BAD_REQUEST)
            # Get ALL user-submitted (u*) ComplianceApproval versions for this compliance and reviewer that are pending review
            pending_user_versions = ComplianceApproval.objects.filter(
                Identifier=compliance.Identifier,
                ReviewerId=reviewer_id,
                Version__startswith='u',
                ApprovedNot=None
            ).order_by('ApprovalId')

            if pending_user_versions.exists():
                for approval in pending_user_versions:
                    # Debug logging for Impact and Probability fields
                    extracted_data = approval.ExtractedData or {}
                    #print(f"DEBUG: Approval {approval.ApprovalId} - Impact: {extracted_data.get('Impact')}, Probability: {extracted_data.get('Probability')}")
                    #print(f"DEBUG: Approval {approval.ApprovalId} - All ExtractedData keys: {list(extracted_data.keys()) if extracted_data else 'None'}")
                    
                    # Ensure Impact and Probability fields are present in ExtractedData
                    if approval.ExtractedData:
                        if 'Impact' not in approval.ExtractedData or not approval.ExtractedData['Impact']:
                            approval.ExtractedData['Impact'] = compliance.Impact
                        if 'Probability' not in approval.ExtractedData or not approval.ExtractedData['Probability']:
                            approval.ExtractedData['Probability'] = compliance.Probability
                        # Ensure CreatedByName is present in ExtractedData
                        if 'CreatedByName' not in approval.ExtractedData or not approval.ExtractedData.get('CreatedByName'):
                            user_name = get_user_name_by_id(approval.UserId)
                            if user_name:
                                approval.ExtractedData['CreatedByName'] = user_name
                    else:
                        # If ExtractedData is None, create it with CreatedByName
                        approval.ExtractedData = {}
                        user_name = get_user_name_by_id(approval.UserId)
                        if user_name:
                            approval.ExtractedData['CreatedByName'] = user_name
                    
                    approval_dict = {
                        'ApprovalId': approval.ApprovalId,
                        'Identifier': approval.Identifier,
                        'ExtractedData': approval.ExtractedData,
                        'UserId': approval.UserId,
                        'ReviewerId': approval.ReviewerId,
                        'ApprovedNot': approval.ApprovedNot,
                        'Version': approval.Version,
                        'ApprovedDate': approval.ApprovedDate.strftime('%Y-%m-%d %H:%M:%S') if approval.ApprovedDate and hasattr(approval.ApprovedDate, 'strftime') else None,
                        'ApprovalDueDate': approval.ApprovalDueDate.strftime('%Y-%m-%d') if approval.ApprovalDueDate and hasattr(approval.ApprovalDueDate, 'strftime') else None
                    }
                    approvals.append(approval_dict)
            else:
                # Fallback to previous logic if no pending user version exists
                latest_approval = ComplianceApproval.objects.filter(
                    Identifier=compliance.Identifier,
                    ReviewerId=reviewer_id,
                ).order_by('-Version', '-ApprovalId').first()
                if not latest_approval or latest_approval.ApprovedNot is None or (
                    latest_approval.Version and latest_approval.Version.startswith('u') and latest_approval.ApprovedNot is None
                ):
                    if latest_approval:
                        # Debug logging for Impact and Probability fields
                        extracted_data = latest_approval.ExtractedData or {}
                        #print(f"DEBUG: Using existing approval {latest_approval.ApprovalId} for compliance {compliance.Identifier}")
                        #print(f"DEBUG: Approval Impact: {extracted_data.get('Impact')}, Probability: {extracted_data.get('Probability')}")
                        #print(f"DEBUG: Compliance Impact: {compliance.Impact}, Probability: {compliance.Probability}")
                        
                        # Ensure Impact and Probability fields are present in ExtractedData
                        if latest_approval.ExtractedData:
                            if 'Impact' not in latest_approval.ExtractedData or not latest_approval.ExtractedData['Impact']:
                                latest_approval.ExtractedData['Impact'] = compliance.Impact
                            if 'Probability' not in latest_approval.ExtractedData or not latest_approval.ExtractedData['Probability']:
                                latest_approval.ExtractedData['Probability'] = compliance.Probability
                            # Ensure CreatedByName is present in ExtractedData
                            if 'CreatedByName' not in latest_approval.ExtractedData or not latest_approval.ExtractedData.get('CreatedByName'):
                                user_name = get_user_name_by_id(latest_approval.UserId)
                                if user_name:
                                    latest_approval.ExtractedData['CreatedByName'] = user_name
                        else:
                            # If ExtractedData is None, create it with CreatedByName
                            latest_approval.ExtractedData = {}
                            user_name = get_user_name_by_id(latest_approval.UserId)
                            if user_name:
                                latest_approval.ExtractedData['CreatedByName'] = user_name
                        
                        approval_dict = {
                            'ApprovalId': latest_approval.ApprovalId,
                            'Identifier': latest_approval.Identifier,
                            'ExtractedData': latest_approval.ExtractedData,
                            'UserId': latest_approval.UserId,
                            'ReviewerId': latest_approval.ReviewerId,
                            'ApprovedNot': latest_approval.ApprovedNot,
                            'Version': latest_approval.Version,
                            'ApprovedDate': latest_approval.ApprovedDate.strftime('%Y-%m-%d %H:%M:%S') if latest_approval.ApprovedDate and hasattr(latest_approval.ApprovedDate, 'strftime') else None,
                            'ApprovalDueDate': latest_approval.ApprovalDueDate.strftime('%Y-%m-%d') if latest_approval.ApprovalDueDate and hasattr(latest_approval.ApprovalDueDate, 'strftime') else None
                        }
                        approvals.append(approval_dict)
                    else:
                        # Get user name for creator
                        creator_name = compliance.CreatedByName
                        if not creator_name and creator_id:
                            creator_name = get_user_name_by_id(creator_id)
                        if not creator_name:
                            creator_name = 'Unknown User'
                        
                        extracted_data = {
                            'type': 'compliance',
                            'ComplianceItemDescription': compliance.ComplianceItemDescription,
                            'IsRisk': compliance.IsRisk,
                            'PossibleDamage': compliance.PossibleDamage,
                            'mitigation': compliance.mitigation,
                            'Criticality': compliance.Criticality,
                            'MandatoryOptional': compliance.MandatoryOptional,
                            'ManualAutomatic': compliance.ManualAutomatic,
                            'Impact': compliance.Impact,
                            'Probability': compliance.Probability,
                            'MaturityLevel': compliance.MaturityLevel,
                            'ActiveInactive': compliance.ActiveInactive,
                            'PermanentTemporary': compliance.PermanentTemporary,
                            'Status': compliance.Status,
                            'ComplianceVersion': compliance.ComplianceVersion,
                            'CreatedByName': creator_name,
                            'CreatedByDate': compliance.CreatedByDate.isoformat() if compliance.CreatedByDate else None,
                            'SubPolicy': compliance.SubPolicy.SubPolicyId if compliance.SubPolicy else None,
                            'compliance_approval': {
                                'approved': None,
                                'remarks': '',
                                'ApprovalDueDate': None
                            }
                        }
                        
                        # Debug logging for Impact and Probability fields
                        #print(f"DEBUG: Creating new approval for compliance {compliance.Identifier}")
                        #print(f"DEBUG: Compliance Impact: {compliance.Impact}, Probability: {compliance.Probability}")
                        #print(f"DEBUG: ExtractedData Impact: {extracted_data.get('Impact')}, Probability: {extracted_data.get('Probability')}")
                        from datetime import datetime, timedelta
                        default_due_date = datetime.now().date() + timedelta(days=7)
                        
                        # Check for existing policy approval to prevent duplicates
                        existing_approval = PolicyApproval.objects.filter(
                            Identifier=compliance.Identifier,
                            UserId=creator_id,
                            ReviewerId=reviewer_id,
                            Version="u1",
                            ApprovedNot=None  # Only check for pending approvals
                        ).first()
                        
                        if existing_approval:
                            print(f"DEBUG: ⚠️ Duplicate prevention: Policy approval already exists for Identifier {compliance.Identifier} with ApprovalId: {existing_approval.ApprovalId}")
                            print(f"  - Skipping duplicate creation")
                            new_approval = existing_approval
                        else:
                            new_approval = PolicyApproval.objects.create(
                            Identifier=compliance.Identifier,
                            ExtractedData=extracted_data,
                            UserId=creator_id,
                            ReviewerId=reviewer_id,
                            ApprovedNot=None,
                            Version="u1",
                            ApprovalDueDate=default_due_date
                        )
                            print(f"DEBUG: ✅ Created new PolicyApproval for Identifier {compliance.Identifier} with ApprovalId: {new_approval.ApprovalId}")
                        approval_dict = {
                            'ApprovalId': new_approval.ApprovalId,
                            'Identifier': new_approval.Identifier,
                            'ExtractedData': extracted_data,
                            'UserId': new_approval.UserId,
                            'ReviewerId': new_approval.ReviewerId,
                            'ApprovedNot': new_approval.ApprovedNot,
                            'Version': new_approval.Version,
                            'ApprovedDate': None,
                            'ApprovalDueDate': new_approval.ApprovalDueDate.strftime('%Y-%m-%d') if new_approval.ApprovalDueDate else None
                        }
                        approvals.append(approval_dict)
        
        # Get pending deactivation requests
        # print("\n=== QUERYING DEACTIVATION REQUESTS ===")
        # print("Fetching pending deactivation requests...")
        deactivation_requests = PolicyApproval.objects.filter(
            ReviewerId=reviewer_id,
            ApprovedNot=None
        ).exclude(ExtractedData=None)
        
        # print(f"Found {deactivation_requests.count()} total pending requests with non-null ExtractedData")
        
        # Debug: Print all request identifiers
        print("All pending request identifiers:")
        # for req in deactivation_requests:
        #     print(f" - {req.Identifier} | Type: {req.ExtractedData.get('type', 'unknown')} | RequestType: {req.ExtractedData.get('RequestType', 'unknown')}")
        
        # Filter to only include records with type='compliance_deactivation'
        deactivation_approvals = []
        for approval in deactivation_requests:
            extracted_data = approval.ExtractedData
            # print(f"\nChecking approval {approval.ApprovalId} with identifier {approval.Identifier}")
            
            # # Debug approval's ExtractedData
            # print(f"ExtractedData type: {extracted_data.get('type', 'None')}")
            # print(f"RequestType: {extracted_data.get('RequestType', 'None')}")
            
            is_deactivation = False
            reason = "none"
            
            if extracted_data and (
                extracted_data.get('type') == 'compliance_deactivation' or 
                (approval.Identifier and 'COMP-DEACTIVATE' in approval.Identifier)
            ):
                is_deactivation = True
                reason = "matched type or identifier"
            elif extracted_data and extracted_data.get('RequestType') == 'Change Status to Inactive':
                is_deactivation = True
                reason = "matched RequestType"
                
            # print(f"Is deactivation? {is_deactivation} (Reason: {reason})")
            
            if is_deactivation:
                # print(f"Found deactivation request: {approval.Identifier}")
                # Make sure we don't duplicate approvals
                duplicate = False
                for a in approvals:
                    if a['ApprovalId'] == approval.ApprovalId:
                        duplicate = True
                        # print(f"Skipping duplicate approval {approval.ApprovalId}")
                        break
                
                if not duplicate:
                    # Ensure CreatedByName is present in ExtractedData for deactivation requests
                    if approval.ExtractedData:
                        if 'CreatedByName' not in approval.ExtractedData or not approval.ExtractedData.get('CreatedByName'):
                            user_name = get_user_name_by_id(approval.UserId)
                            if user_name:
                                approval.ExtractedData['CreatedByName'] = user_name
                    else:
                        approval.ExtractedData = {}
                        user_name = get_user_name_by_id(approval.UserId)
                        if user_name:
                            approval.ExtractedData['CreatedByName'] = user_name
                    
                    approval_dict = {
                        'ApprovalId': approval.ApprovalId,
                        'Identifier': approval.Identifier,
                        'ExtractedData': approval.ExtractedData,
                        'UserId': approval.UserId,
                        'ReviewerId': approval.ReviewerId,
                        'ApprovedNot': approval.ApprovedNot,
                        'Version': approval.Version,
                        'ApprovedDate': approval.ApprovedDate.strftime('%Y-%m-%d %H:%M:%S') if approval.ApprovedDate and hasattr(approval.ApprovedDate, 'strftime') else None,
                        'ApprovalDueDate': approval.ApprovalDueDate.strftime('%Y-%m-%d') if approval.ApprovalDueDate and hasattr(approval.ApprovalDueDate, 'strftime') else None
                    }
                    approvals.append(approval_dict)
                    print(f"Added deactivation request {approval.Identifier} to response")
        
        # Also fetch recently approved compliances (last 30)
        # print("\n=== QUERYING APPROVED COMPLIANCES ===")
        # print("Fetching recently approved compliances...")
        
        # Get approved compliances from the database
        approved_compliances = Compliance.objects.filter(
            Status='Approved',
            Identifier__isnull=False,
            Identifier__gt=''  # Exclude empty strings
        ).select_related('SubPolicy').order_by('-CreatedByDate')[:30]
        
        # print(f"Found {approved_compliances.count()} approved compliances in database")
        
        # For each approved compliance, get the latest approval record
        for compliance in approved_compliances:
            # Find the approval record for this compliance
            latest_approval = PolicyApproval.objects.filter(
                Identifier=compliance.Identifier,
                ReviewerId=reviewer_id,
                ApprovedNot=True
            ).order_by('-ApprovalId').first()
            
            if latest_approval:
                # print(f"Found approval for approved compliance {compliance.Identifier}")
                
                # Make sure we don't duplicate approvals
                if not any(a['ApprovalId'] == latest_approval.ApprovalId for a in approvals):
                    # Ensure CreatedByName is present in ExtractedData
                    if latest_approval.ExtractedData:
                        if 'CreatedByName' not in latest_approval.ExtractedData or not latest_approval.ExtractedData.get('CreatedByName'):
                            user_name = get_user_name_by_id(latest_approval.UserId)
                            if user_name:
                                latest_approval.ExtractedData['CreatedByName'] = user_name
                        # Ensure the ExtractedData has the correct status
                        latest_approval.ExtractedData['Status'] = 'Approved'
                        latest_approval.ExtractedData['ActiveInactive'] = 'Active'
                    else:
                        latest_approval.ExtractedData = {}
                        user_name = get_user_name_by_id(latest_approval.UserId)
                        if user_name:
                            latest_approval.ExtractedData['CreatedByName'] = user_name
                        latest_approval.ExtractedData['Status'] = 'Approved'
                        latest_approval.ExtractedData['ActiveInactive'] = 'Active'
                    
                    # Format for JSON serialization
                    approval_dict = {
                        'ApprovalId': latest_approval.ApprovalId,
                        'Identifier': latest_approval.Identifier,
                        'ExtractedData': latest_approval.ExtractedData,
                        'UserId': latest_approval.UserId,
                        'ReviewerId': latest_approval.ReviewerId,
                        'ApprovedNot': latest_approval.ApprovedNot,
                        'Version': latest_approval.Version,
                        'ApprovedDate': latest_approval.ApprovedDate.strftime('%Y-%m-%d %H:%M:%S') if latest_approval.ApprovedDate and hasattr(latest_approval.ApprovedDate, 'strftime') else None,
                        'ApprovalDueDate': latest_approval.ApprovalDueDate.strftime('%Y-%m-%d') if latest_approval.ApprovalDueDate and hasattr(latest_approval.ApprovalDueDate, 'strftime') else None
                    }
                    
                    approvals.append(approval_dict)
        
        # Alternative: get directly from PolicyApproval table
        recently_approved = PolicyApproval.objects.filter(
            ReviewerId=reviewer_id,
            ApprovedNot=True,
            Identifier__isnull=False,
            Identifier__gt=''  # Exclude empty strings
        ).order_by('-ApprovalId')[:30]  # Limit to last 30
        
        # print(f"Found {recently_approved.count()} approved policy approvals")
        
        for approval in recently_approved:
            # Make sure we don't duplicate approvals
            if not any(a['ApprovalId'] == approval.ApprovalId for a in approvals):
                # Ensure CreatedByName is present in ExtractedData
                if approval.ExtractedData:
                    if 'CreatedByName' not in approval.ExtractedData or not approval.ExtractedData.get('CreatedByName'):
                        user_name = get_user_name_by_id(approval.UserId)
                        if user_name:
                            approval.ExtractedData['CreatedByName'] = user_name
                    # Ensure the ExtractedData has the correct status
                    approval.ExtractedData['Status'] = 'Approved'
                    approval.ExtractedData['ActiveInactive'] = 'Active'
                else:
                    approval.ExtractedData = {}
                    user_name = get_user_name_by_id(approval.UserId)
                    if user_name:
                        approval.ExtractedData['CreatedByName'] = user_name
                    approval.ExtractedData['Status'] = 'Approved'
                    approval.ExtractedData['ActiveInactive'] = 'Active'
                
                # Format for JSON serialization
                approval_dict = {
                    'ApprovalId': approval.ApprovalId,
                    'Identifier': approval.Identifier,
                    'ExtractedData': approval.ExtractedData,
                    'UserId': approval.UserId,
                    'ReviewerId': approval.ReviewerId,
                    'ApprovedNot': approval.ApprovedNot,
                    'Version': approval.Version,
                    'ApprovedDate': approval.ApprovedDate.strftime('%Y-%m-%d %H:%M:%S') if approval.ApprovedDate and hasattr(approval.ApprovedDate, 'strftime') else None,
                    'ApprovalDueDate': approval.ApprovalDueDate.strftime('%Y-%m-%d') if approval.ApprovalDueDate and hasattr(approval.ApprovalDueDate, 'strftime') else None
                }
                
                approvals.append(approval_dict)
                # print(f"Added approved policy {approval.Identifier} to response")
        
        # CRITICAL FIX: Check for any identifiers that have both pending (uN) and approved (rN) versions
        # and ensure we show the approved version instead of the pending one
        # print("\n=== CHECKING FOR MIXED STATUS IDENTIFIERS ===")
        all_identifiers = set(a['Identifier'] for a in approvals)
        
        for identifier in all_identifiers:
            # Get all approvals for this identifier
            identifier_approvals = PolicyApproval.objects.filter(
                Identifier=identifier,
                ReviewerId=reviewer_id
            ).order_by('-ApprovalId')
            
            # Check if there are both pending and approved versions
            has_pending = any(a.ApprovedNot is None for a in identifier_approvals)
            has_approved = any(a.ApprovedNot is True for a in identifier_approvals)
            
            if has_pending and has_approved:
                # print(f"Identifier {identifier} has both pending and approved versions")
                
                # Remove any pending versions from our response - they should not appear in pending after approval
                approvals = [a for a in approvals if not (a['Identifier'] == identifier and a['ApprovedNot'] is None)]
                
                # Add the most recent approved version to the approved list (not pending)
                latest_approved = identifier_approvals.filter(ApprovedNot=True).order_by('-ApprovalId').first()
                if latest_approved:
                    # Ensure CreatedByName is present in ExtractedData
                    if latest_approved.ExtractedData:
                        if 'CreatedByName' not in latest_approved.ExtractedData or not latest_approved.ExtractedData.get('CreatedByName'):
                            user_name = get_user_name_by_id(latest_approved.UserId)
                            if user_name:
                                latest_approved.ExtractedData['CreatedByName'] = user_name
                        # Ensure the ExtractedData has the correct status
                        latest_approved.ExtractedData['Status'] = 'Approved'
                        latest_approved.ExtractedData['ActiveInactive'] = 'Active'
                    else:
                        latest_approved.ExtractedData = {}
                        user_name = get_user_name_by_id(latest_approved.UserId)
                        if user_name:
                            latest_approved.ExtractedData['CreatedByName'] = user_name
                        latest_approved.ExtractedData['Status'] = 'Approved'
                        latest_approved.ExtractedData['ActiveInactive'] = 'Active'
                    
                    approval_dict = {
                        'ApprovalId': latest_approved.ApprovalId,
                        'Identifier': latest_approved.Identifier,
                        'ExtractedData': latest_approved.ExtractedData,
                        'UserId': latest_approved.UserId,
                        'ReviewerId': latest_approved.ReviewerId,
                        'ApprovedNot': latest_approved.ApprovedNot,
                        'Version': latest_approved.Version,
                        'ApprovedDate': latest_approved.ApprovedDate.strftime('%Y-%m-%d %H:%M:%S') if latest_approved.ApprovedDate and hasattr(latest_approved.ApprovedDate, 'strftime') else None,
                        'ApprovalDueDate': latest_approved.ApprovalDueDate.strftime('%Y-%m-%d') if latest_approved.ApprovalDueDate and hasattr(latest_approved.ApprovalDueDate, 'strftime') else None
                    }
                    
                    approvals.append(approval_dict)
                    # print(f"Removed pending version and added approved version for {identifier}")
            elif has_approved and not has_pending:
                # If there's only an approved version, make sure it's marked as approved
                # print(f"Identifier {identifier} has only approved version")
                for a in approvals:
                    if a['Identifier'] == identifier:
                        a['ApprovedNot'] = True
                        if a['ExtractedData']:
                            # Ensure CreatedByName is present
                            if 'CreatedByName' not in a['ExtractedData'] or not a['ExtractedData'].get('CreatedByName'):
                                user_name = get_user_name_by_id(a.get('UserId'))
                                if user_name:
                                    a['ExtractedData']['CreatedByName'] = user_name
                            a['ExtractedData']['Status'] = 'Approved'
                            a['ExtractedData']['ActiveInactive'] = 'Active'
                        # print(f"Marked {identifier} as approved")
                        break
        
        # Debug: print identifiers of all items in the response
        # print("\n=== FINAL RESPONSE CONTENTS ===")
        # print(f"Total approvals to return: {len(approvals)}")
        
        # print("Identifiers in final response:")
        # for item in approvals:
        #     print(f" - {item['Identifier']} | Type: {item['ExtractedData'].get('type', 'unknown')} | ApprovedNot: {item['ApprovedNot']}")
        
        # Debug: count how many approved items we're returning
        approved_count = sum(1 for a in approvals if a.get('ApprovedNot') is True)
        # print(f"Returning {approved_count} approved items in the response")
        
        # Get counts from the actual approvals data being returned
        counts = {
            'pending': sum(1 for a in approvals if a.get('ApprovedNot') is None),
            'approved': sum(1 for a in approvals if a.get('ApprovedNot') is True),
            'rejected': sum(1 for a in approvals if a.get('ApprovedNot') is False)
        }
        
        # print(f"Approval counts: {counts}")
        # print("==== END DEBUGGING DEACTIVATION REQUESTS ====\n\n")
        
        return Response({
            'success': True,
            'data': approvals,
            'counts': counts
        })
        
    except Exception as e:
        # print(f"Error in get_policy_approvals_by_reviewer: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
 
@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_rejected_approvals(request, reviewer_id):
    try:
        # Use session user_id if available, otherwise use URL parameter
        session_user_id = request.session.get('user_id')
        if session_user_id:
            reviewer_id = session_user_id
            print(f"Using session user_id: {reviewer_id}")
        else:
            print(f"Using URL parameter reviewer_id: {reviewer_id}")
        
        print(f"Fetching rejected approvals for reviewer_id: {reviewer_id}")
        
        # Get all policy approvals that have been rejected for this reviewer
        approvals = PolicyApproval.objects.filter(
            ReviewerId=reviewer_id,
            ApprovedNot=False
        ).order_by('-ApprovalId')
       
        print(f"Found {approvals.count()} rejected approvals for reviewer {reviewer_id}")
        
        # Convert to list for JSON serialization
        approvals_list = []
        for approval in approvals:
            # Create a dictionary with approval data
            approval_dict = {
                'ApprovalId': approval.ApprovalId,
                'Identifier': approval.Identifier,
                'ExtractedData': approval.ExtractedData,
                'UserId': approval.UserId,
                'ReviewerId': approval.ReviewerId,
                'ApprovedNot': approval.ApprovedNot,
                'Version': approval.Version,
                'rejection_reason': approval.ExtractedData.get('compliance_approval', {}).get('remarks', ''),
                'ApprovalDueDate': approval.ApprovalDueDate.strftime('%Y-%m-%d') if approval.ApprovalDueDate and hasattr(approval.ApprovalDueDate, 'strftime') else None
            }
            if approval.ApprovedDate:
                approval_dict['ApprovedDate'] = approval.ApprovedDate.strftime('%Y-%m-%d %H:%M:%S') if hasattr(approval.ApprovedDate, 'strftime') else str(approval.ApprovedDate)
            is_resubmitted = approval.ExtractedData.get('compliance_approval', {}).get('inResubmission', False)
            # NEW LOGIC: Only show truly rejected (finalized) approvals, not pending resubmissions
            status = approval.ExtractedData.get('Status', '').lower()
            approved_val = approval.ExtractedData.get('compliance_approval', {}).get('approved', None)
            if not is_resubmitted and status == 'rejected' and approved_val is False:
                approvals_list.append(approval_dict)
                print(f"Added rejection for {approval.Identifier} (ID: {approval.ApprovalId})")
            else:
                print(f"Skipping {approval.Identifier} as it's already in resubmission process or under review")
        print(f"Returning {len(approvals_list)} rejections")
        return Response(approvals_list)
       
    except Exception as e:
        print("Error in get_rejected_approvals:", str(e))
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_all_users(request):
    """
    Get all users from the database except system user.
    Returns a list of users with their IDs and usernames only.
    """
    try:
        from django.db import connection
        from ...models import Users   
        
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Get all users (frontend will exclude the currently logged-in user for reviewer dropdown)
        users = Users.objects.values('UserId', 'UserName').order_by('UserName')
        
        # Convert to list
        users_list = list(users)
        
        return Response({
            'success': True,
            'users': users_list,
            'total_count': len(users_list)
        })
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error in get_all_users: {error_msg}")
        
        return Response({
            'success': False,
            'message': 'Failed to fetch users',
            'error': error_msg
        }, status=500)
 
@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([ComplianceTogglePermission])
@compliance_toggle_required
def toggle_compliance_version(request, compliance_id):
    """
    Toggle compliance version active/inactive status with strict rules:
    1. Only "Approved" compliances can be made Active
    2. Only one version can be Active at a time
    3. When active version is turned off, either deactivate or activate latest version
    """
    try:
        print(f"\n=== TOGGLE_COMPLIANCE_VERSION DEBUG ===")
        print(f"Toggling compliance with ID: {compliance_id}")
        
        # Get the target compliance
        compliance = get_object_or_404(Compliance, ComplianceId=compliance_id)
        print(f"Found compliance: {compliance.Identifier}, Status: {compliance.Status}, ActiveInactive: {compliance.ActiveInactive}")
       
        # RULE 1: Only allow toggling if compliance is approved
        if compliance.Status != 'Approved':
            print(f"Cannot toggle - compliance status is {compliance.Status}, not Approved")
            return Response({
                'success': False,
                'message': 'Only approved compliances can be toggled between active and inactive'
            }, status=status.HTTP_400_BAD_REQUEST)
 
        # Helper function to get all approved versions by identifier
        def get_approved_versions_by_identifier(identifier):
            """Get all approved versions for the same compliance identifier"""
            try:
                versions = Compliance.objects.filter(
                    Identifier=identifier, 
                    Status='Approved'
                ).order_by('-ComplianceVersion')
                print(f"Found {versions.count()} approved versions for identifier {identifier}")
                return versions
            except Exception as e:
                print(f"Error getting approved versions: {str(e)}")
                return Compliance.objects.none()
        
        # Helper function to ensure only one active version
        def ensure_single_active_version(versions_queryset, target_compliance_id, should_be_active):
            """Ensure only one version is active at a time"""
            updated_count = 0
            
            for version in versions_queryset:
                try:
                    if version.ComplianceId == target_compliance_id:
                        # Set target compliance to desired state
                        new_status = 'Active' if should_be_active else 'Inactive'
                        if version.ActiveInactive != new_status:
                            version.ActiveInactive = new_status
                            version.save()
                            updated_count += 1
                            print(f"Set compliance {version.ComplianceId} to {new_status}")
                    else:
                        # Set all other versions to inactive
                        if version.ActiveInactive != 'Inactive':
                            version.ActiveInactive = 'Inactive'
                            version.save()
                            updated_count += 1
                            print(f"Set compliance {version.ComplianceId} to Inactive")
                except Exception as version_error:
                    print(f"Error updating version {version.ComplianceId}: {str(version_error)}")
                    continue
            
            return updated_count
        
        # Get all approved versions with the same identifier
        approved_versions = get_approved_versions_by_identifier(compliance.Identifier)
        
        if not approved_versions.exists():
            print(f"No approved versions found for identifier {compliance.Identifier}")
            return Response({
                'success': False,
                'message': 'No approved versions found for this compliance'
            }, status=status.HTTP_400_BAD_REQUEST)
       
        # Determine the action based on current status
        is_currently_active = compliance.ActiveInactive == 'Active'
        print(f"Current status: {'Active' if is_currently_active else 'Inactive'}")
        
        if is_currently_active:
            # RULE 3: When turning off active version
            print("Deactivating currently active version")
            
            # Find the latest version that's not the current one
            latest_other_version = approved_versions.exclude(ComplianceId=compliance_id).first()
            
            if latest_other_version:
                print(f"Found latest other version: {latest_other_version.ComplianceId} (v{latest_other_version.ComplianceVersion})")
                # Deactivate current and activate latest other version
                updated_count = ensure_single_active_version(approved_versions, latest_other_version.ComplianceId, True)
                message = f'Compliance version {compliance.ComplianceVersion} deactivated. Latest version {latest_other_version.ComplianceVersion} is now active.'
            else:
                print("No other approved versions found, just deactivating current")
                # Just deactivate current version
                updated_count = ensure_single_active_version(approved_versions, compliance_id, False)
                message = f'Compliance version {compliance.ComplianceVersion} deactivated. No other approved versions available.'
        else:
            # RULE 2: When activating a version, ensure only one is active
            print("Activating version and ensuring single active state")
            updated_count = ensure_single_active_version(approved_versions, compliance_id, True)
            message = f'Compliance version {compliance.ComplianceVersion} activated successfully'

        print(f"Successfully updated {updated_count} compliance versions")

        # Send notification to affected users
        try:
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Get affected users (creator and reviewer)
            affected_users = set()
            
            # Add creator's email
            try:
                creator_id = compliance.CreatedByName
                creator_email, creator_name = notification_service.get_user_email_by_id(creator_id)
                if creator_email:
                    affected_users.add(creator_email)
            except Exception as ce:
                print(f"Error getting creator email: {str(ce)}")
            
            # Add reviewer's email from policy approval
            try:
                policy_approval = PolicyApproval.objects.filter(
                    Identifier=compliance.Identifier
                ).first()
                if policy_approval:
                    reviewer_email, reviewer_name = notification_service.get_user_email_by_id(policy_approval.ReviewerId)
                    if reviewer_email:
                        affected_users.add(reviewer_email)
            except Exception as re:
                print(f"Error getting reviewer email: {str(re)}")
            
            if affected_users:
                notification_result = notification_service.send_compliance_version_toggle_notification(
                    compliance=compliance,
                    affected_users=list(affected_users)
                )
                print(f"Version toggle notification result: {notification_result}")
            else:
                print("No affected users found for notifications")
        except Exception as e:
            print(f"Error sending version toggle notification: {str(e)}")
            # Continue even if notification fails
       
        # Get the final status of the target compliance
        compliance.refresh_from_db()
        final_status = compliance.ActiveInactive
        
        print("=== END TOGGLE_COMPLIANCE_VERSION DEBUG ===\n")
        return Response({
            'success': True,
            'message': message,
            'compliance_id': compliance_id,
            'new_status': final_status,
            'updated_count': updated_count
        })
        
    except Compliance.DoesNotExist:
        print(f"Compliance with ID {compliance_id} not found")
        return Response({
            'success': False,
            'message': f'Compliance with ID {compliance_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error in toggle_compliance_version: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error toggling compliance version: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Compliance versioning validation helpers
class ComplianceVersioningValidator:
    """Helper class for compliance versioning validation and rules"""
    
    @staticmethod
    def can_be_activated(compliance):
        """Check if a compliance version can be activated"""
        if compliance.Status != 'Approved':
            return False, "Only approved compliances can be activated"
        return True, "Compliance can be activated"
    
    @staticmethod
    def get_active_version_for_identifier(identifier):
        """Get the currently active version for a compliance identifier"""
        try:
            active_version = Compliance.objects.filter(
                Identifier=identifier,
                Status='Approved',
                ActiveInactive='Active'
            ).first()
            return active_version
        except Exception as e:
            print(f"Error getting active version: {str(e)}")
            return None
    
    @staticmethod
    def get_all_approved_versions(identifier):
        """Get all approved versions for a compliance identifier"""
        try:
            return Compliance.objects.filter(
                Identifier=identifier,
                Status='Approved'
            ).order_by('-ComplianceVersion')
        except Exception as e:
            print(f"Error getting approved versions: {str(e)}")
            return Compliance.objects.none()
    
    @staticmethod
    def get_latest_version(identifier, exclude_id=None):
        """Get the latest approved version for a compliance identifier"""
        try:
            queryset = Compliance.objects.filter(
                Identifier=identifier,
                Status='Approved'
            ).order_by('-ComplianceVersion')
            
            if exclude_id:
                queryset = queryset.exclude(ComplianceId=exclude_id)
            
            return queryset.first()
        except Exception as e:
            print(f"Error getting latest version: {str(e)}")
            return None
    
    @staticmethod
    def validate_versioning_rules(compliance_id, action='toggle'):
        """Validate compliance versioning rules before performing actions"""
        try:
            compliance = Compliance.objects.get(ComplianceId=compliance_id)
            
            # Check if compliance can be activated
            can_activate, message = ComplianceVersioningValidator.can_be_activated(compliance)
            if not can_activate:
                return False, message
            
            # Get all approved versions
            approved_versions = ComplianceVersioningValidator.get_all_approved_versions(compliance.Identifier)
            if not approved_versions.exists():
                return False, "No approved versions found for this compliance"
            
            # Check current active version
            current_active = ComplianceVersioningValidator.get_active_version_for_identifier(compliance.Identifier)
            
            if action == 'activate':
                if current_active and current_active.ComplianceId != compliance_id:
                    return True, f"Will deactivate version {current_active.ComplianceVersion} and activate version {compliance.ComplianceVersion}"
                elif current_active and current_active.ComplianceId == compliance_id:
                    return False, "This version is already active"
                else:
                    return True, f"Will activate version {compliance.ComplianceVersion}"
            
            elif action == 'deactivate':
                if not current_active or current_active.ComplianceId != compliance_id:
                    return False, "This version is not currently active"
                
                latest_other = ComplianceVersioningValidator.get_latest_version(compliance.Identifier, exclude_id=compliance_id)
                if latest_other:
                    return True, f"Will deactivate version {compliance.ComplianceVersion} and activate version {latest_other.ComplianceVersion}"
                else:
                    return True, f"Will deactivate version {compliance.ComplianceVersion}. No other approved versions available."
            
            return True, "Validation passed"
            
        except Compliance.DoesNotExist:
            return False, "Compliance not found"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def get_version_status_info(identifier):
        """Get detailed status information for all versions of a compliance"""
        try:
            versions = Compliance.objects.filter(Identifier=identifier).order_by('-ComplianceVersion')
            status_info = []
            
            for version in versions:
                status_info.append({
                    'compliance_id': version.ComplianceId,
                    'version': version.ComplianceVersion,
                    'status': version.Status,
                    'active_inactive': version.ActiveInactive,
                    'can_be_activated': version.Status == 'Approved' and version.ActiveInactive != 'Active',
                    'is_current_active': version.Status == 'Approved' and version.ActiveInactive == 'Active'
                })
            
            return status_info
        except Exception as e:
            print(f"Error getting version status info: {str(e)}")
            return []

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([ComplianceDeactivatePermission])
@compliance_deactivate_required
def deactivate_compliance(request, compliance_id):
    try:
        print("\n\n==== DEBUGGING DEACTIVATE_COMPLIANCE ====")
        print(f"Received deactivation request for compliance_id: {compliance_id}")
        print(f"Request data: {request.data}")
        
        # Get the target compliance
        compliance = get_object_or_404(Compliance, ComplianceId=compliance_id)
        print(f"Found compliance: {compliance.Identifier}, Status: {compliance.Status}")
        
        # Only allow deactivation for active compliances
        if compliance.ActiveInactive != 'Active':
            return Response({
                'success': False,
                'message': 'Only active compliances can be deactivated'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the reason from the request
        reason = request.data.get('reason', 'No longer needed')
        
        # Get reviewer ID and user ID from the request (required)
        reviewer_id = request.data.get('reviewer_id')
        user_id = request.data.get('user_id')
        if not reviewer_id or not user_id:
            return Response({
                'success': False,
                'message': 'Both reviewer_id and user_id are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        print(f"Using reviewer_id: {reviewer_id}, user_id: {user_id}")
        
        # Create a unique identifier for this deactivation request
        deactivation_identifier = f"COMP-DEACTIVATE-{compliance.Identifier}"
        print(f"Created deactivation identifier: {deactivation_identifier}")
        
        # Build the ExtractedData for the deactivation request
        extracted_data = {
            'type': 'compliance_deactivation',
            'compliance_id': compliance_id,
            'identifier': compliance.Identifier,
            'version': compliance.ComplianceVersion,
            'reason': reason,
            'current_status': 'Active',
            'requested_status': 'Inactive',
            'RequestType': 'Change Status to Inactive',
            'affected_policies_count': 0,  # Could be updated with actual count
            'cascade_to_policies': 'Yes' if request.data.get('cascade_to_policies', True) else 'No'
        }
        
        # Determine next user version for this identifier
        all_versions = ComplianceApproval.objects.filter(Identifier=deactivation_identifier)
        highest_u_version = 0
        for pa in all_versions:
            if pa.Version and pa.Version.startswith('u'):
                try:
                    version_num = int(pa.Version[1:]) if len(pa.Version) > 1 else 1
                    if version_num > highest_u_version:
                        highest_u_version = version_num
                except ValueError:
                    continue
        new_version = f"u{highest_u_version + 1}"
        print(f"Assigning user version: {new_version}")
        
        # Create a ComplianceApproval record for the deactivation request
        creation_data = {
            'Identifier': deactivation_identifier,
            'UserId': user_id,
            'ReviewerId': reviewer_id,
            'Version': new_version,
            'ApprovedNot': None,  # Null initially
            'PolicyId': compliance.SubPolicy.PolicyId if hasattr(compliance, 'SubPolicy') and hasattr(compliance.SubPolicy, 'PolicyId') else None,
            'ExtractedData': extracted_data
        }
        
        # Add FrameworkId from the compliance record (through SubPolicy->Policy->FrameworkId)
        try:
            if compliance.SubPolicy and compliance.SubPolicy.PolicyId and hasattr(compliance.SubPolicy.PolicyId, 'FrameworkId_id'):
                framework_id = compliance.SubPolicy.PolicyId.FrameworkId_id
                if framework_id is not None:
                    # Use _id suffix to assign the foreign key ID directly
                    creation_data['FrameworkId_id'] = int(framework_id)
                    print(f"Adding FrameworkId_id to deactivation request: {framework_id}")
                else:
                    print(f"FrameworkId_id is None in deactivation request, not adding to creation data")
            else:
                print(f"Cannot get FrameworkId from compliance SubPolicy/Policy chain")
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Warning: Error getting FrameworkId in deactivation request, skipping: {e}")
        
        approval = ComplianceApproval.objects.create(**creation_data)
        
        print(f"Created PolicyApproval record: {approval.ApprovalId}, ReviewerId: {approval.ReviewerId}, Version: {approval.Version}")
        
        # Verify the approval was created correctly
        try:
            verify_approval = ComplianceApproval.objects.get(ApprovalId=approval.ApprovalId)
            print(f"Verification - ApprovalId: {verify_approval.ApprovalId}, Identifier: {verify_approval.Identifier}")
            print(f"Verification - ReviewerId: {verify_approval.ReviewerId}, ApprovedNot: {verify_approval.ApprovedNot}")
            print(f"Verification - ExtractedData type: {verify_approval.ExtractedData.get('type', 'Not set')}")
        except Exception as ve:
            print(f"Error verifying approval: {str(ve)}")
            
        # Send notification to reviewer
        try:
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Get reviewer's email
            reviewer_email, reviewer_name = notification_service.get_user_email_by_id(reviewer_id)
            
            if reviewer_email:
                # Send notification
                notification_data = {
                    'notification_type': 'compliance_creation',  # Reuse creation template
                    'email': reviewer_email,
                    'email_type': 'gmail',  # Default to gmail
                    'template_data': [
                        reviewer_name or reviewer_email.split('@')[0],  # Use name or extract from email
                        compliance.ComplianceId,
                        f"REQUEST TO DEACTIVATE: {compliance.ComplianceItemDescription or 'No description provided'}",
                        compliance.ComplianceVersion,
                        compliance.CreatedByName or "Unknown",
                        datetime.now().strftime('%Y-%m-%d')
                    ]
                }
                
                # Send the notification
                result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Deactivation request notification sent to {reviewer_email}: {result}")
            else:
                print(f"No email found for reviewer ID {reviewer_id}")
        except Exception as e:
            print(f"Error sending deactivation request notification: {str(e)}")
            # Continue even if notification fails
        
        print("==== END DEBUGGING DEACTIVATE_COMPLIANCE ====\n\n")
        
        return Response({
            'success': True,
            'message': 'Deactivation request submitted successfully. Awaiting approval.',
            'approval_id': approval.ApprovalId
        })
        
    except Exception as e:
        print(f"Error in deactivate_compliance: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([ComplianceApprovePermission])
@compliance_approve_required
def approve_compliance_deactivation(request, approval_id):
    try:
        print(f"\n\n==== DEBUGGING APPROVE_DEACTIVATION ====")
        print(f"Approving deactivation request for approval_id: {approval_id}")
        
        # Get the approval record (user's uN row)
        approval = get_object_or_404(ComplianceApproval, ApprovalId=approval_id)
        print(f"Found approval: {approval.Identifier}")
        
        # Verify it's a compliance deactivation request
        extracted_data = approval.ExtractedData
        if extracted_data.get('type') != 'compliance_deactivation' or extracted_data.get('RequestType') != 'Change Status to Inactive':
            return Response({
                'success': False,
                'message': 'Invalid approval request type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the compliance record
        compliance_id = extracted_data.get('compliance_id')
        print(f"Looking for compliance ID: {compliance_id}")
        compliance = get_object_or_404(Compliance, ComplianceId=compliance_id)
        print(f"Found compliance: {compliance.Identifier}, Current status: {compliance.ActiveInactive}")
        
        # Update the compliance status
        compliance.ActiveInactive = 'Inactive'
        compliance.save()
        print(f"Updated compliance {compliance.Identifier} to Inactive")
        
        # Determine next reviewer version for this identifier
        all_versions = ComplianceApproval.objects.filter(Identifier=approval.Identifier)
        highest_r_version = 0
        for pa in all_versions:
            if pa.Version and pa.Version.startswith('r'):
                try:
                    version_num = int(pa.Version[1:]) if len(pa.Version) > 1 else 1
                    if version_num > highest_r_version:
                        highest_r_version = version_num
                except ValueError:
                    continue
        new_version = f"r{highest_r_version + 1}"
        print(f"Assigning reviewer version: {new_version}")
        
        # Create a new ComplianceApproval row for the reviewer action (ApprovedNot=1 for approve)
        creation_data = {
            'Identifier': approval.Identifier,
            'UserId': approval.UserId,
            'ReviewerId': approval.ReviewerId,
            'Version': new_version,
            'ApprovedNot': 1,  # 1 for approve
            'ApprovedDate': timezone.now(),
            'PolicyId': approval.PolicyId,
            'ExtractedData': {**extracted_data, 'current_status': 'Inactive'}
        }
        
        # Only add FrameworkId if it's not None and is a valid integer
        if approval.FrameworkId_id is not None:
            try:
                framework_id = int(approval.FrameworkId_id)
                # Use _id suffix to assign the foreign key ID directly
                creation_data['FrameworkId_id'] = framework_id
                print(f"Adding FrameworkId_id to deactivation approval: {framework_id}")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid FrameworkId '{approval.FrameworkId_id}' in deactivation approval, skipping: {e}")
        else:
            print(f"FrameworkId is None in deactivation approval, not adding to creation data")
        
        reviewer_approval = ComplianceApproval.objects.create(**creation_data)
        print(f"Created reviewer ComplianceApproval record: {reviewer_approval.ApprovalId}, Version: {reviewer_approval.Version}")
        # The user (uN) row remains with ApprovedNot=NULL
        # Send notification to compliance creator
        try:
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            creator_id = approval.UserId
            creator_email, creator_name = notification_service.get_user_email_by_id(creator_id)
            if creator_email:
                notification_result = notification_service.send_compliance_review_notification(
                    compliance=compliance,
                    reviewer_decision=True,  # Approved
                    creator_id=creator_id,
                    remarks="Your request to deactivate this compliance item has been approved."
                )
                print(f"Deactivation approval notification result: {notification_result}")
            else:
                print(f"No email found for creator ID {creator_id}")
        except Exception as e:
            print(f"Error sending deactivation approval notification: {str(e)}")
        print("==== END DEBUGGING APPROVE_DEACTIVATION ====\n\n")
        return Response({
            'success': True,
            'message': f'Compliance {compliance.Identifier} has been deactivated successfully',
            'compliance': {
                'ComplianceId': compliance.ComplianceId,
                'Identifier': compliance.Identifier,
                'Status': compliance.Status,
                'ActiveInactive': compliance.ActiveInactive
            },
            'approval_id': reviewer_approval.ApprovalId,
            'version': new_version
        })
    except Exception as e:
        print(f"Error in approve_compliance_deactivation: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([ComplianceApprovePermission])
@compliance_approve_required
def reject_compliance_deactivation(request, approval_id):
    try:
        print(f"\n\n==== DEBUGGING REJECT_DEACTIVATION ====")
        print(f"Rejecting deactivation request for approval_id: {approval_id}")
        
        # Get the approval record (user's uN row)
        approval = get_object_or_404(ComplianceApproval, ApprovalId=approval_id)
        print(f"Found approval: {approval.Identifier}")
        
        # Verify it's a compliance deactivation request
        extracted_data = approval.ExtractedData
        if extracted_data.get('type') != 'compliance_deactivation' or extracted_data.get('RequestType') != 'Change Status to Inactive':
            return Response({
                'success': False,
                'message': 'Invalid approval request type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the compliance ID from extracted data
        compliance_id = extracted_data.get('compliance_id')
        print(f"Referenced compliance ID: {compliance_id}")
        
        # Fetch compliance to notify about
        compliance = None
        try:
            compliance = Compliance.objects.get(ComplianceId=compliance_id)
            print(f"Found compliance: {compliance.Identifier}, Current status: {compliance.ActiveInactive}")
            if compliance.ActiveInactive != 'Active':
                compliance.ActiveInactive = 'Active'
                compliance.save()
                print(f"Ensured compliance {compliance.Identifier} remains Active")
        except Compliance.DoesNotExist:
            print(f"Warning: Compliance with ID {compliance_id} not found")
        
        # Get rejection remarks
        remarks = request.data.get('remarks', 'No reason provided')
        if request.data.get('remarks'):
            # Store rejection remarks in the same location as regular compliance rejections
            if 'compliance_approval' not in extracted_data:
                extracted_data['compliance_approval'] = {}
            extracted_data['compliance_approval']['remarks'] = remarks
            extracted_data['compliance_approval']['approved'] = False
            # Also keep the old field for backward compatibility
            extracted_data['rejection_remarks'] = remarks
            
            print(f"Saved rejection remarks for deactivation request: {remarks}")
            print(f"Updated ExtractedData compliance_approval: {extracted_data['compliance_approval']}")
        
        # Determine next reviewer version for this identifier
        all_versions = ComplianceApproval.objects.filter(Identifier=approval.Identifier)
        highest_r_version = 0
        for pa in all_versions:
            if pa.Version and pa.Version.startswith('r'):
                try:
                    version_num = int(pa.Version[1:]) if len(pa.Version) > 1 else 1
                    if version_num > highest_r_version:
                        highest_r_version = version_num
                except ValueError:
                    continue
        new_version = f"r{highest_r_version + 1}"
        print(f"Assigning reviewer version: {new_version}")
        
        # Create a new ComplianceApproval row for the reviewer rejection (ApprovedNot=0 for reject)
        creation_data = {
            'Identifier': approval.Identifier,
            'UserId': approval.UserId,
            'ReviewerId': approval.ReviewerId,
            'Version': new_version,
            'ApprovedNot': 0,  # 0 for reject
            'ApprovedDate': timezone.now(),
            'PolicyId': approval.PolicyId,
            'ExtractedData': extracted_data
        }
        
        # Only add FrameworkId if it's not None and is a valid integer
        if approval.FrameworkId_id is not None:
            try:
                framework_id = int(approval.FrameworkId_id)
                # Use _id suffix to assign the foreign key ID directly
                creation_data['FrameworkId_id'] = framework_id
                print(f"Adding FrameworkId_id to deactivation rejection: {framework_id}")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid FrameworkId '{approval.FrameworkId_id}' in deactivation rejection, skipping: {e}")
        else:
            print(f"FrameworkId is None in deactivation rejection, not adding to creation data")
        
        reviewer_approval = ComplianceApproval.objects.create(**creation_data)
        print(f"Created reviewer ComplianceApproval record: {reviewer_approval.ApprovalId}, Version: {reviewer_approval.Version}")
        # The user (uN) row remains with ApprovedNot=NULL
        # Send notification to compliance creator
        if compliance:
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                creator_id = approval.UserId
                creator_email, creator_name = notification_service.get_user_email_by_id(creator_id)
                if creator_email:
                    notification_result = notification_service.send_compliance_review_notification(
                        compliance=compliance,
                        reviewer_decision=False,  # Rejected
                        creator_id=creator_id,
                        remarks=f"Your request to deactivate this compliance item has been rejected. Reason: {remarks}"
                    )
                    print(f"Deactivation rejection notification result: {notification_result}")
                else:
                    print(f"No email found for creator ID {creator_id}")
            except Exception as e:
                print(f"Error sending deactivation rejection notification: {str(e)}")
        print("==== END DEBUGGING REJECT_DEACTIVATION ====\n\n")
        return Response({
            'success': True,
            'message': 'Deactivation request has been rejected',
            'approval_id': reviewer_approval.ApprovalId,
            'version': new_version
        })
    except Exception as e:
        print(f"Error in reject_compliance_deactivation: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
def test_analytics_endpoint(request):
    return Response({
        'success': True,
        'message': 'Analytics endpoint is reachable'
    })

@api_view(['POST'])
@csrf_exempt
@authentication_classes([])
@permission_classes([ComplianceAnalyticsPermission])
@compliance_analytics_required
def get_compliance_analytics(request):
    try:
        print("Received analytics request with data:", request.data)
        x_axis = request.data.get('xAxis')
        y_axis = request.data.get('yAxis')
        
        # Get filter parameters
        framework_id = request.data.get('frameworkId')
        time_range = request.data.get('timeRange')
        category = request.data.get('category')
        priority = request.data.get('priority')

        if not x_axis or not y_axis:
            return Response({
                'success': False,
                'message': 'Both X and Y axis parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get base queryset
        queryset = Compliance.objects.all()
        
        # Apply framework filtering using the standard framework filter helper
        try:
            from ..Policy.framework_filter_helper import get_active_framework_filter
            
            # Get framework filter info for logging
            framework_filter_id = get_active_framework_filter(request)
            print(f"🔍 DEBUG: Compliance Analytics - Active framework filter: {framework_filter_id}")
            
            # Apply framework filter to compliance using direct FrameworkId relationship
            if framework_filter_id:
                queryset = queryset.filter(FrameworkId=framework_filter_id)
                print(f"Applied session framework filter via FrameworkId: {framework_filter_id}")
            else:
                print("No framework filter applied - showing all frameworks")
            
        except ImportError as e:
            #print(f"DEBUG: Could not import framework filter helper: {e}")
            # Fallback to manual framework filtering if helper is not available
            if framework_id and framework_id != '':
                queryset = queryset.filter(FrameworkId=framework_id)
                print(f"Applied manual framework filter via FrameworkId: {framework_id}")
        except Exception as e:
            #print(f"DEBUG: Error applying framework filter: {e}")
            # Fallback to manual framework filtering on error
            if framework_id and framework_id != '':
                queryset = queryset.filter(FrameworkId=framework_id)
                print(f"Applied manual framework filter via FrameworkId: {framework_id}")
        
        # Apply explicit framework filter if provided (for backward compatibility)
        if framework_id and framework_id != '':
            print(f"Applying explicit framework filter via FrameworkId: {framework_id}")
            queryset = queryset.filter(FrameworkId=framework_id)
        
        # Apply time range filter
        if time_range and time_range != 'Last 6 Months':
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if time_range == 'Last 3 Months':
                start_date = now - timedelta(days=90)
            elif time_range == 'Last Month':
                start_date = now - timedelta(days=30)
            elif time_range == 'Last Week':
                start_date = now - timedelta(days=7)
            else:
                start_date = now - timedelta(days=180)  # Default to 6 months
                
            queryset = queryset.filter(CreatedByDate__gte=start_date)
        
        # Apply category filter using ComplianceType field - now supports dynamic categories from DB
        if category and category != 'All Categories':
            queryset = queryset.filter(ComplianceType__icontains=category)
            print(f"Applied category filter: {category}")
        
        # Apply priority filter using Criticality field
        if priority and priority != 'All Priorities':
            queryset = queryset.filter(Criticality=priority)
            print(f"Applied priority filter: {priority}")
        
        print(f"Filtered queryset count: {queryset.count()}")
        
        # Get counts for dashboard metrics
        total_compliances = queryset.count()
        approved_compliances = queryset.filter(Status='Approved').count()
        active_compliances = queryset.filter(ActiveInactive='Active').count()
        under_review_compliances = queryset.filter(Status='Under Review').count()

        # Calculate approval rate
        approval_rate = (approved_compliances / total_compliances * 100) if total_compliances > 0 else 0

        # Initialize chart data based on Y axis selection
        labels = []
        data = []

        if y_axis == 'Criticality':
            counts = queryset.values('Criticality').annotate(
                count=models.Count('ComplianceId')
            ).exclude(Criticality__isnull=True).exclude(Criticality='')
            labels = ['High', 'Medium', 'Low']
            data = [
                next((item['count'] for item in counts if item['Criticality'] == 'High'), 0),
                next((item['count'] for item in counts if item['Criticality'] == 'Medium'), 0),
                next((item['count'] for item in counts if item['Criticality'] == 'Low'), 0)
            ]

        elif y_axis == 'Status':
            counts = queryset.values('Status').annotate(
                count=models.Count('ComplianceId')
            ).exclude(Status__isnull=True).exclude(Status='')
            labels = ['Approved', 'Under Review', 'Rejected', 'Active']
            data = [
                next((item['count'] for item in counts if item['Status'] == 'Approved'), 0),
                next((item['count'] for item in counts if item['Status'] == 'Under Review'), 0),
                next((item['count'] for item in counts if item['Status'] == 'Rejected'), 0),
                next((item['count'] for item in counts if item['Status'] == 'Active'), 0)
            ]

        elif y_axis == 'ActiveInactive':
            counts = queryset.values('ActiveInactive').annotate(
                count=models.Count('ComplianceId')
            ).exclude(ActiveInactive__isnull=True).exclude(ActiveInactive='')
            labels = ['Active', 'Inactive']
            data = [
                next((item['count'] for item in counts if item['ActiveInactive'] == 'Active'), 0),
                next((item['count'] for item in counts if item['ActiveInactive'] == 'Inactive'), 0)
            ]

        elif y_axis == 'ManualAutomatic':
            counts = queryset.values('ManualAutomatic').annotate(
                count=models.Count('ComplianceId')
            ).exclude(ManualAutomatic__isnull=True).exclude(ManualAutomatic='')
            labels = ['Manual', 'Automatic']
            data = [
                next((item['count'] for item in counts if item['ManualAutomatic'] == 'Manual'), 0),
                next((item['count'] for item in counts if item['ManualAutomatic'] == 'Automatic'), 0)
            ]

        elif y_axis == 'MandatoryOptional':
            counts = queryset.values('MandatoryOptional').annotate(
                count=models.Count('ComplianceId')
            ).exclude(MandatoryOptional__isnull=True).exclude(MandatoryOptional='')
            labels = ['Mandatory', 'Optional']
            data = [
                next((item['count'] for item in counts if item['MandatoryOptional'] == 'Mandatory'), 0),
                next((item['count'] for item in counts if item['MandatoryOptional'] == 'Optional'), 0)
            ]

        elif y_axis == 'MaturityLevel':
            counts = queryset.values('MaturityLevel').annotate(
                count=models.Count('ComplianceId')
            ).exclude(MaturityLevel__isnull=True).exclude(MaturityLevel='')
            labels = ['Initial', 'Developing', 'Defined', 'Managed', 'Optimizing']
            data = [
                next((item['count'] for item in counts if item['MaturityLevel'] == level), 0)
                for level in labels
            ]

        # Prepare dashboard data
        dashboard_data = {
            'status_counts': {
                'approved': approved_compliances,
                'active': active_compliances,
                'under_review': under_review_compliances
            },
            'total_count': total_compliances,
            'total_findings': queryset.filter(IsRisk=True).count(),
            'approval_rate': round(approval_rate, 2)
        }

        # Prepare chart data
        chart_data = {
            'labels': labels,
            'datasets': [{
                'label': f'Compliance by {y_axis.replace("By ", "")}',
                'data': data
            }]
        }

        print("Sending response with dashboard_data:", dashboard_data)
        print("Chart data:", chart_data)

        return Response({
            'success': True,
            'chartData': chart_data,
            'dashboardData': dashboard_data
        })

    except Exception as e:
        print(f"Error in get_compliance_analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 
 #---------------------------------KPI Dashboard---------------------------------
 
@api_view(['GET'])
@authentication_classes([])
@permission_classes([ComplianceKPIPermission])
@compliance_kpi_required
def get_compliance_kpi(request):
    try:
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        # Get all compliances
        compliances = Compliance.objects.all()
        
        # Filter by framework if provided (through SubPolicy → Policy → Framework relationship)
        if framework_id:
            compliances = compliances.filter(SubPolicy__PolicyId__FrameworkId=framework_id)
        
        # Calculate KPIs
        total_compliances = compliances.count()
        active_compliances = compliances.filter(ActiveInactive='Active').count()
        approved_compliances = compliances.filter(Status='Approved').count()
        
        # Calculate compliance rate
        compliance_rate = (approved_compliances / total_compliances * 100) if total_compliances > 0 else 0
        
        # Get risk distribution
        high_risk = compliances.filter(Criticality='High').count()
        medium_risk = compliances.filter(Criticality='Medium').count()
        low_risk = compliances.filter(Criticality='Low').count()
        
        # Calculate maturity levels distribution
        maturity_levels = {
            'Initial': compliances.filter(MaturityLevel='Initial').count(),
            'Developing': compliances.filter(MaturityLevel='Developing').count(),
            'Defined': compliances.filter(MaturityLevel='Defined').count(),
            'Managed': compliances.filter(MaturityLevel='Managed').count(),
            'Optimizing': compliances.filter(MaturityLevel='Optimizing').count()
        }
        
        # Calculate average maturity score
        maturity_scores = {
            'Initial': 1,
            'Developing': 2,
            'Defined': 3,
            'Managed': 4,
            'Optimizing': 5
        }
        total_score = sum(maturity_scores[level] * count for level, count in maturity_levels.items())
        avg_maturity = total_score / total_compliances if total_compliances > 0 else 0
        
        # Get control types distribution
        manual_controls = compliances.filter(ManualAutomatic='Manual').count()
        automatic_controls = compliances.filter(ManualAutomatic='Automatic').count()
        
        # Get mandatory vs optional distribution
        mandatory_controls = compliances.filter(MandatoryOptional='Mandatory').count()
        optional_controls = compliances.filter(MandatoryOptional='Optional').count()
        
        return Response({
            'success': True,
            'data': {
                'compliance_rate': round(compliance_rate, 2),
                'active_controls': active_compliances,
                'maturity_score': round(avg_maturity, 2),
                'risk_distribution': {
                    'high': high_risk,
                    'medium': medium_risk,
                    'low': low_risk
                },
                'maturity_levels': maturity_levels,
                'control_types': {
                    'manual': manual_controls,
                    'automatic': automatic_controls
                },
                'control_requirements': {
                    'mandatory': mandatory_controls,
                    'optional': optional_controls
                },
                'total_compliances': total_compliances,
                'approved_compliances': approved_compliances
            }
        })
        
    except Exception as e:
        print(f"Error in get_compliance_kpi: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceKPIPermission])
@compliance_kpi_required
def get_maturity_level_kpi(request):
    try:
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        print(f"[MATURITY KPI] Framework ID requested: {framework_id}")
        
        # Get only active and approved compliances
        compliances = Compliance.objects.filter(
            ActiveInactive='Active',
            Status='Approved'
        )
        
        print(f"[MATURITY KPI] Total active+approved compliances (before framework filter): {compliances.count()}")
        
        # Filter by framework if provided (through SubPolicy → Policy → Framework relationship)
        if framework_id:
            compliances = compliances.filter(SubPolicy__PolicyId__FrameworkId=framework_id)
            print(f"[MATURITY KPI] Compliances after framework filter: {compliances.count()}")
        
        # Calculate counts for each maturity level
        maturity_counts = {
            'Initial': compliances.filter(MaturityLevel='Initial').count(),
            'Developing': compliances.filter(MaturityLevel='Developing').count(),
            'Defined': compliances.filter(MaturityLevel='Defined').count(),
            'Managed': compliances.filter(MaturityLevel='Managed').count(),
            'Optimizing': compliances.filter(MaturityLevel='Optimizing').count()
        }
        
        print(f"[MATURITY KPI] Maturity counts: {maturity_counts}")
        
        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_by_maturity': maturity_counts,
                    'total_compliances': compliances.count()
                }
            }
        })
        
    except Exception as e:
        print(f"Error in get_maturity_level_kpi: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceKPIPermission])
@compliance_kpi_required
def get_non_compliance_count(request):
    try:
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        # Get all verified records (Count > 0) to calculate proper percentages
        all_verified_records = LastChecklistItemVerified.objects.filter(Count__gt=0)
        
        # Filter by framework if provided
        if framework_id:
            all_verified_records = all_verified_records.filter(FrameworkId=framework_id)
        
        # Get non-compliance records - only count items where Complied = '0' (non-compliant)
        non_compliance_records = all_verified_records.filter(Complied='0')
        
        # Get compliant records for comparison
        compliant_records = all_verified_records.filter(Complied='1')

        # Get all relevant Frameworks in one query for efficiency
        framework_ids = set(record.FrameworkId for record in all_verified_records if record.FrameworkId)
        frameworks = Framework.objects.filter(FrameworkId__in=framework_ids)
        framework_id_to_name = {fw.FrameworkId: fw.FrameworkName for fw in frameworks}

        # Get total counts
        total_non_compliant = non_compliance_records.count()
        total_compliant = compliant_records.count()
        total_verified = all_verified_records.count()

        # Group by framework for non-compliant items
        framework_breakdown = {}
        for record in non_compliance_records:
            framework_id = record.FrameworkId
            framework_name = framework_id_to_name.get(framework_id, f"Framework {framework_id}") if framework_id else "Unknown Framework"
            if framework_name not in framework_breakdown:
                framework_breakdown[framework_name] = 0
            framework_breakdown[framework_name] += 1

        # Convert to list format for frontend with proper percentages
        framework_data = []
        for framework_name, count in framework_breakdown.items():
            # Calculate percentage based on total verified items, not just non-compliant
            percentage = round((count / total_verified * 100), 1) if total_verified > 0 else 0
            framework_data.append({
                'framework_name': framework_name,
                'count': count,
                'percentage': percentage
            })

        # Sort by count descending
        framework_data.sort(key=lambda x: x['count'], reverse=True)

        # Calculate overall compliance percentage
        compliance_percentage = round((total_compliant / total_verified * 100), 1) if total_verified > 0 else 0
        non_compliance_percentage = round((total_non_compliant / total_verified * 100), 1) if total_verified > 0 else 0

        # Debug logging
        #print(f"DEBUG: Non-compliance count breakdown:")
        print(f"  Total verified items: {total_verified}")
        print(f"  Non-compliant items: {total_non_compliant}")
        print(f"  Compliant items: {total_compliant}")
        print(f"  Non-compliance percentage: {non_compliance_percentage}%")
        print(f"  Framework breakdown: {framework_data}")

        return Response({
            'success': True,
            'data': {
                'total_non_compliance_count': total_non_compliant,
                'total_compliant_count': total_compliant,
                'total_verified_count': total_verified,
                'compliance_percentage': compliance_percentage,
                'non_compliance_percentage': non_compliance_percentage,
                'framework_breakdown': framework_data,
                'framework_count': len(framework_data)
            }
        })

    except Exception as e:
        print(f"Error in get_non_compliance_count: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceKPIPermission])
@compliance_kpi_required
def get_mitigated_risks_count(request):
    try:
        # Count risks that have been mitigated (MitigationStatus = 'Completed')
        mitigated_count = RiskInstance.objects.filter(
            MitigationStatus=RiskInstance.MITIGATION_COMPLETED
        ).count()
        
        return Response({
            'success': True,
            'data': {
                'mitigated_count': mitigated_count
            }
        })
        
    except Exception as e:
        print(f"Error in get_mitigated_risks_count: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceKPIPermission])
@compliance_kpi_required
def get_automated_controls_count(request):
    try:
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        print(f"[AUTOMATED KPI] Framework ID requested: {framework_id}")
        
        # Get base queryset for active and approved compliances
        base_query = Compliance.objects.filter(
            Status='Approved',
            ActiveInactive='Active'
        )
        
        print(f"[AUTOMATED KPI] Total compliances before framework filter: {base_query.count()}")
        
        # Filter by framework if provided (through SubPolicy → Policy → Framework relationship)
        if framework_id:
            base_query = base_query.filter(SubPolicy__PolicyId__FrameworkId=framework_id)
            print(f"[AUTOMATED KPI] Compliances after framework filter: {base_query.count()}")
        
        # Count automated and manual controls
        automated_count = base_query.filter(ManualAutomatic='Automatic').count()
        manual_count = base_query.filter(ManualAutomatic='Manual').count()
        
        print(f"[AUTOMATED KPI] Automated: {automated_count}, Manual: {manual_count}")
        
        # Calculate percentages
        total = automated_count + manual_count
        automated_percentage = round((automated_count / total * 100) if total > 0 else 0, 1)
        manual_percentage = round((manual_count / total * 100) if total > 0 else 0, 1)
        
        return Response({
            'success': True,
            'data': {
                'automated_count': automated_count,
                'manual_count': manual_count,
                'total_count': total,
                'automated_percentage': automated_percentage,
                'manual_percentage': manual_percentage
            }
        })
        
    except Exception as e:
        print(f"Error in get_automated_controls_count: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceKPIPermission])
@compliance_kpi_required
def get_non_compliance_repetitions(request):
    try:
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        # Get items with non-zero count
        repetitions = LastChecklistItemVerified.objects.filter(
            Count__gt=0
        )
        
        # Filter by framework if provided
        if framework_id:
            repetitions = repetitions.filter(FrameworkId=framework_id)
        
        repetitions = repetitions.order_by('-Count')

        # Calculate statistics
        total_items = repetitions.count()
        max_repetitions = repetitions.aggregate(max_count=models.Max('Count'))['max_count'] or 0
        avg_repetitions = repetitions.aggregate(avg_count=models.Avg('Count'))['avg_count'] or 0

        # Get distribution of repetitions
        distribution = {}
        for item in repetitions:
            count = item.Count
            if count in distribution:
                distribution[count] += 1
            else:
                distribution[count] = 1

        # Convert distribution to sorted list for chart
        chart_data = [
            {'repetitions': count, 'occurrences': freq}
            for count, freq in sorted(distribution.items())
        ]

        return Response({
            'success': True,
            'data': {
                'total_items': total_items,
                'max_repetitions': max_repetitions,
                'avg_repetitions': round(avg_repetitions, 1),
                'distribution': chart_data
            }
        })
        
    except Exception as e:
        print(f"Error in get_non_compliance_repetitions: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
#----------------------------------Compliance List---------------------------------
@api_view(['GET'])
@permission_classes([ComplianceFrameworkAccessPermission])
def all_policies_get_frameworks(request):
    """
    API endpoint to get all frameworks for AllPolicies.vue component.
    """
    try:
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
           
        return Response(frameworks_data)
   
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([ComplianceFrameworkAccessPermission])
def all_policies_get_framework_version_policies(request, version_id):
    """
    API endpoint to get all policies for a specific framework version for AllPolicies.vue component.
    """
    try:
        # Get the framework version
        framework_version = get_object_or_404(FrameworkVersion, VersionId=version_id)
        framework = framework_version.FrameworkId
       
        # Get policies for this framework
        policies = Policy.objects.filter(
            Framework=framework,
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
           
        return Response(policies_data)
       
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([ComplianceFrameworkAccessPermission])
def all_policies_get_policies(request):
    """
    API endpoint to get all policies for AllPolicies.vue component.
    Automatically applies framework filter from session if no explicit filter provided.
    """
    try:
        from ...routes.Policy.framework_filter_helper import apply_framework_filter, get_active_framework_filter
        
        # Optional framework filter from query params
        framework_id = request.GET.get('framework_id')
       
        # Start with all policies
        policies_query = Policy.objects.all()
       
        # Apply explicit framework filter if provided in query params
        if framework_id:
            policies_query = policies_query.filter(FrameworkId=framework_id)
        else:
            # Apply session-based framework filter if no explicit filter
            policies_query = apply_framework_filter(policies_query, request, 'FrameworkId')
       
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
           
        return Response(policies_data)
       
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([ComplianceFrameworkPermission])
@compliance_policy_required
def all_policies_get_policy_versions(request, policy_id):
    """
    API endpoint to get all versions of a specific policy for AllPolicies.vue component.
    Implements a dedicated version that handles version chains through PreviousVersionId.
    """
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
        return Response(versions_data)
       
    except Exception as e:
        import traceback
        print(f"Error in all_policies_get_policy_versions: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([ComplianceFrameworkAccessPermission])
def all_policies_get_subpolicies(request):
    """
    API endpoint to get all subpolicies for AllPolicies.vue component.
    Now supports filtering by policy_id (GET param) in addition to framework_id.
    """
    try:
        print("Request received for all subpolicies")
       
        # Optional framework and policy filter
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        print(f"Framework filter: {framework_id}")
        print(f"Policy filter: {policy_id}")
       
        # Start with all subpolicies
        subpolicies_query = SubPolicy.objects.all()
       
        # If policy filter is provided, filter by policy_id
        if policy_id:
            try:
                subpolicies_query = subpolicies_query.filter(PolicyId=policy_id)
                print(f"Filtered subpolicies by policy_id: {policy_id}")
            except Exception as e:
                print(f"Error filtering by policy: {str(e)}")
                # Continue with all subpolicies if filtering fails
        # Else, if framework filter is provided, filter through policies
        elif framework_id:
            try:
                policy_ids = Policy.objects.filter(FrameworkId=framework_id).values_list('PolicyId', flat=True)
                print(f"Found {len(policy_ids)} policies for framework {framework_id}")
                subpolicies_query = subpolicies_query.filter(PolicyId__in=policy_ids)
            except Exception as e:
                print(f"Error filtering by framework: {str(e)}")
                # Continue with all subpolicies if framework filtering fails
       
        print(f"Found {subpolicies_query.count()} subpolicies")
       
        subpolicies_data = []
        for subpolicy in subpolicies_query:
            try:
                # Get the policy this subpolicy belongs to
                try:
                    policy = subpolicy.PolicyId  # Use the ForeignKey relationship directly
                    policy_name = policy.PolicyName
                    department = policy.Department
                except (Policy.DoesNotExist, AttributeError):
                    print(f"Policy not found for subpolicy {subpolicy.SubPolicyId}")
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
                    'policy_id': subpolicy.PolicyId.PolicyId,  # Get the actual PolicyId value
                    'policy_name': policy_name,
                    'created_by': subpolicy.CreatedByName,
                    'created_date': subpolicy.CreatedByDate
                }
                subpolicies_data.append(subpolicy_data)
                # print(f"Added subpolicy: {subpolicy.SubPolicyId} - {subpolicy.SubPolicyName}")
            except Exception as e:
                print(f"Error processing subpolicy {subpolicy.SubPolicyId}: {str(e)}")
                # Continue to next subpolicy
       
        print(f"Returning {len(subpolicies_data)} subpolicies")
        return Response(subpolicies_data)
       
    except Exception as e:
        import traceback
        print(f"Error in all_policies_get_subpolicies: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([ComplianceFrameworkAccessPermission])
def all_policies_get_subpolicy_details(request, subpolicy_id):
    """
    API endpoint to get details of a specific subpolicy for AllPolicies.vue component.
    """
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
       
        return Response(subpolicy_data)
       
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([ComplianceFrameworkAccessPermission])
def all_policies_get_framework_versions(request, framework_id):
    try:
        print(f"Request received for framework versions, framework_id: {framework_id}")
       
        # Get the base framework
        try:
            framework = Framework.objects.get(FrameworkId=framework_id)
            print(f"Found framework: {framework.FrameworkName}")
        except Framework.DoesNotExist:
            print(f"Framework with ID {framework_id} not found")
            return Response({'error': f'Framework with ID {framework_id} not found'},
                           status=status.HTTP_404_NOT_FOUND)
       
        # Get direct versions that belong to this framework
        direct_versions = list(FrameworkVersion.objects.filter(FrameworkId=framework))
        print(f"Found {len(direct_versions)} direct versions")
       
        versions_data = []
        for version in direct_versions:
            try:
                # Count policies for this framework version
                policy_count = Policy.objects.filter(
                    Framework=framework
                ).count()
               
                # Get previous version details if available
                previous_version = None
                if version.PreviousVersionId:
                    try:
                        previous_version = FrameworkVersion.objects.get(VersionId=version.PreviousVersionId)
                    except FrameworkVersion.DoesNotExist:
                        pass
               
                formatted_name = f"{version.FrameworkName} v{version.Version}"
               
                version_data = {
                    'id': version.VersionId,
                    'name': formatted_name,
                    'version': version.Version,
                    'category': framework.Category or 'General',
                    'status': framework.ActiveInactive or 'Unknown',
                    'description': framework.FrameworkDescription or '',
                    'created_date': version.CreatedDate,
                    'created_by': version.CreatedBy,
                    'policy_count': policy_count,
                    'previous_version_id': version.PreviousVersionId,
                    'previous_version_name': previous_version.FrameworkName + f" v{previous_version.Version}" if previous_version else None,
                    'framework_id': framework.FrameworkId
                }
                versions_data.append(version_data)
                print(f"Added version: {version.VersionId} - {formatted_name}")
            except Exception as e:
                print(f"Error processing version {version.VersionId}: {str(e)}")
                continue
       
        # Sort versions by version number (descending)
        versions_data.sort(key=lambda x: float(x['version']), reverse=True)
       
        print(f"Returning {len(versions_data)} versions")
        return Response(versions_data)
       
    except Exception as e:
        import traceback
        print(f"Error in all_policies_get_framework_versions: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
@permission_classes([ComplianceFrameworkPermission])
@compliance_subpolicy_required
def all_policies_get_policy_version_subpolicies(request, version_id):
    """
    API endpoint to get all subpolicies for a specific policy version for AllPolicies.vue component.
    Implements a dedicated version instead of using the existing get_policy_version_subpolicies function.
    """
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
                    'created_date': subpolicy.CreatedByDate
                }
                subpolicies_data.append(subpolicy_data)
                print(f"Added subpolicy: {subpolicy.SubPolicyId} - {subpolicy.SubPolicyName}")
            except Exception as e:
                print(f"Error processing subpolicy {subpolicy.SubPolicyId}: {str(e)}")
                # Continue to next subpolicy
       
        print(f"Returning {len(subpolicies_data)} subpolicies")
        return Response(subpolicies_data)
       
    except Exception as e:
        import traceback
        print(f"Error in all_policies_get_policy_version_subpolicies: {str(e)}")
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def all_policies_get_subpolicy_compliances(request, subpolicy_id):
    """Get all compliances for a specific subpolicy"""
    try:
        subpolicy = get_object_or_404(SubPolicy, SubPolicyId=subpolicy_id)
        # Filter for approved compliances only
        compliances = Compliance.objects.filter(
            SubPolicy=subpolicy_id,
            Status='Approved'
        ).select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
        
        print(f"Found {compliances.count()} approved compliances for subpolicy {subpolicy_id}")
        
        # Debug: Check all compliances for this subpolicy regardless of status
        all_compliances = Compliance.objects.filter(SubPolicy=subpolicy_id)
        print(f"Total compliances for subpolicy {subpolicy_id}: {all_compliances.count()}")
        for comp in all_compliances:
            print(f"  Compliance {comp.ComplianceId}: Status='{comp.Status}', Title='{comp.ComplianceTitle}'")
        
        compliances_data = []
        for compliance in compliances:
            compliances_data.append({
                'ComplianceId': compliance.ComplianceId,
                'ComplianceItemDescription': compliance.ComplianceItemDescription,
                'ComplianceTitle': compliance.ComplianceTitle,
                'Status': compliance.Status,
                'ActiveInactive': compliance.ActiveInactive,
                'Criticality': compliance.Criticality,
                'MaturityLevel': compliance.MaturityLevel,
                'MandatoryOptional': compliance.MandatoryOptional,
                'ManualAutomatic': compliance.ManualAutomatic,
                'CreatedByName': compliance.CreatedByName,
                'CreatedByDate': compliance.CreatedByDate.strftime('%Y-%m-%d') if compliance.CreatedByDate else None,
                'ComplianceVersion': compliance.ComplianceVersion,
                'Identifier': compliance.Identifier,
                'mitigation': compliance.mitigation,
                'Scope': compliance.Scope,
                'Objective': compliance.Objective,
                'IsRisk': compliance.IsRisk,
                'PossibleDamage': compliance.PossibleDamage,
                'Impact': compliance.Impact,
                'Probability': compliance.Probability,
                'SubPolicyName': compliance.SubPolicy.SubPolicyName,
                'PolicyName': compliance.SubPolicy.PolicyId.PolicyName,
                'FrameworkName': compliance.SubPolicy.PolicyId.FrameworkId.FrameworkName
            })
        
        return Response({
            'success': True,
            'name': subpolicy.SubPolicyName,
            'compliances': compliances_data
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([ComplianceVersioningPermission])
@compliance_versioning_required
def all_policies_get_compliance_versions(request, compliance_id):
    """
    API endpoint to get all versions of a specific compliance.
    """
    try:
        # Get the initial compliance
        compliance = get_object_or_404(Compliance, ComplianceId=compliance_id)
        
        # Initialize list to store all versions
        versions = []
        current = compliance
        
        # First, get all previous versions
        while current:
            versions.append(current)
            current = current.PreviousComplianceVersionId
            
        # Then, get all next versions
        current = compliance
        while True:
            next_versions = Compliance.objects.filter(PreviousComplianceVersionId=current.ComplianceId)
            if not next_versions.exists():
                break
            current = next_versions.first()
            versions.append(current)
            
        # Sort versions by version number
        versions.sort(key=lambda x: float(x.ComplianceVersion), reverse=True)
        
        # Convert to response format
        versions_data = []
        for version in versions:
            version_data = {
                'ComplianceId': version.ComplianceId,
                'ComplianceVersion': version.ComplianceVersion,
                'ComplianceItemDescription': version.ComplianceItemDescription,
                'Status': version.Status,
                'Criticality': version.Criticality,
                'MaturityLevel': version.MaturityLevel,
                'ActiveInactive': version.ActiveInactive,
                'CreatedByName': version.CreatedByName,
                'CreatedByDate': version.CreatedByDate.isoformat() if version.CreatedByDate else None,
                'Identifier': version.Identifier,
                'IsRisk': version.IsRisk,
                'MandatoryOptional': version.MandatoryOptional,
                'ManualAutomatic': version.ManualAutomatic,
                'PreviousVersionId': version.PreviousComplianceVersionId.ComplianceId if version.PreviousComplianceVersionId else None
            }
            versions_data.append(version_data)
            
        return Response(versions_data)
        
    except Exception as e:
        print(f"Error in all_policies_get_compliance_versions: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.db import connection
import logging

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_framework_compliances(request, framework_id):
    """Get all compliances under a framework"""

    logging.info(f"Getting compliances for framework_id: {framework_id}")
    try:
        framework = get_object_or_404(Framework, FrameworkId=framework_id)
        logging.info(f"Found framework: {framework.FrameworkName}")

        # Log the SQL query before executing it
        compliances = Compliance.objects.filter(
            SubPolicy__PolicyId__FrameworkId=framework
        ).select_related('SubPolicy', 'SubPolicy__PolicyId')
        
        logging.info(f"SQL Query: {connection.queries[-1]}")
        
        compliances_data = []
        for compliance in compliances:
            compliances_data.append({
                'ComplianceId': compliance.ComplianceId,
                'ComplianceItemDescription': compliance.ComplianceItemDescription,
                'Status': compliance.Status,
                'Criticality': compliance.Criticality,
                'MaturityLevel': compliance.MaturityLevel,
                'MandatoryOptional': compliance.MandatoryOptional,
                'ManualAutomatic': compliance.ManualAutomatic,
                'CreatedByName': compliance.CreatedByName,
                'CreatedByDate': compliance.CreatedByDate,
                'ComplianceVersion': compliance.ComplianceVersion,
                'Identifier': compliance.Identifier,
                'PermanentTemporary': compliance.PermanentTemporary,
                'SubPolicyName': compliance.SubPolicy.SubPolicyName,
                'PolicyName': compliance.SubPolicy.PolicyId.PolicyName
            })
        
        return Response({
            'success': True,
            'name': framework.FrameworkName,
            'compliances': compliances_data
        })
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)


@shared_task
def process_export_task(task_id, item_type=None, item_id=None):
    try:
        # Get the task
        task = ExportTask.objects.get(id=task_id)
        task.status = 'processing'
        task.save()
        
        # Process the export
        try:
            # Fetch compliance data based on filters
            compliances_data = []
            
            if item_type == 'framework' and item_id:
                # Export all compliances for a specific framework
                compliances = Compliance.objects.filter(
                    SubPolicy__PolicyId__FrameworkId=item_id
                ).select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
            elif item_type == 'policy' and item_id:
                # Export all compliances for a specific policy
                compliances = Compliance.objects.filter(
                    SubPolicy__PolicyId=item_id
                ).select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
            elif item_type == 'subpolicy' and item_id:
                # Export all compliances for a specific subpolicy
                compliances = Compliance.objects.filter(
                    SubPolicy_id=item_id
                ).select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
            else:
                # Export all compliances
                compliances = Compliance.objects.all().select_related(
                    'SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId'
                )
            
            # Format compliance data for export
            for compliance in compliances:
                compliances_data.append({
                    'Compliance ID': compliance.ComplianceId,
                    'Description': compliance.ComplianceItemDescription or '',
                    'Status': compliance.Status or '',
                    'Criticality': compliance.Criticality or '',
                    'Maturity Level': compliance.MaturityLevel or '',
                    'Type': compliance.ComplianceType or '',
                    'Implementation': compliance.ManualAutomatic or '',
                    'Created By': compliance.CreatedByName or '',
                    'Created Date': compliance.CreatedByDate.strftime('%Y-%m-%d') if compliance.CreatedByDate else '',
                    'Version': compliance.ComplianceVersion or '',
                    'Identifier': compliance.Identifier or '',
                    'Active/Inactive': compliance.ActiveInactive or '',
                    'Is Risk': 'Yes' if compliance.IsRisk else 'No',
                    'SubPolicy': compliance.SubPolicy.SubPolicyName if compliance.SubPolicy else '',
                    'Policy': compliance.SubPolicy.PolicyId.PolicyName if compliance.SubPolicy and compliance.SubPolicy.PolicyId else '',
                    'Framework': compliance.SubPolicy.PolicyId.FrameworkId.FrameworkName if compliance.SubPolicy and compliance.SubPolicy.PolicyId and compliance.SubPolicy.PolicyId.FrameworkId else ''
                })
            
            # Use the export_data function from export_service1
            from ...routes.Global.s3_fucntions import export_data
            result = export_data(
                data=compliances_data,
                file_format=task.file_type,
                user_id=task.user_id,
                options={'item_type': item_type, 'item_id': item_id},
                export_id=task.id
            )
            
            # Task is already updated by export_data function
            # Just refresh the task to get updated values
            task.refresh_from_db()
            
            # Send notification
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                
                # Send notification directly with user_id
                notification_result = notification_service.send_export_completion_notification(
                    user_id=int(task.user_id),
                    export_details={
                        'id': task.id,
                        'file_name': task.file_name,
                        'file_type': task.file_type,
                        's3_url': task.s3_url,
                        'completed_at': task.completed_at.strftime('%Y-%m-%d %H:%M:%S') if task.completed_at else None
                    }
                )
                print(f"Export completion notification result: {notification_result}")
            except Exception as e:
                print(f"Error sending export completion notification: {str(e)}")
                # Continue even if notification fails
            
        except Exception as e:
            # Update task with error
            task.status = 'failed'
            task.error = str(e)
            task.save()
            raise
            
    except ExportTask.DoesNotExist:
        print(f"Export task {task_id} not found")
    except Exception as e:
        print(f"Error processing export task: {str(e)}")
        # Ensure task is marked as failed
        try:
            task = ExportTask.objects.get(id=task_id)
            task.status = 'failed'
            task.error = str(e)
            task.save()
        except:
            pass

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_subpolicy_compliances(request, subpolicy_id):
    """Get all compliances for a specific subpolicy"""
    try:
        subpolicy = get_object_or_404(SubPolicy, id=subpolicy_id)
        compliances = Compliance.objects.filter(
            SubPolicy=subpolicy
        ).select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
        
        compliances_data = []
        for compliance in compliances:
            compliances_data.append({
                'ComplianceId': compliance.id,
                'ComplianceItemDescription': compliance.description,
                'Status': compliance.status,
                'Criticality': compliance.criticality,
                'MaturityLevel': compliance.maturity_level,
                'MandatoryOptional': compliance.mandatory_optional,
                'ManualAutomatic': compliance.manual_automatic,
                'CreatedByName': compliance.created_by_name,
                'CreatedByDate': compliance.created_at.strftime('%Y-%m-%d') if compliance.created_at else None,
                'ComplianceVersion': compliance.version,
                'Identifier': compliance.identifier,
                'SubPolicyName': compliance.SubPolicy.name,
                'PolicyName': compliance.SubPolicy.PolicyId.name if compliance.SubPolicy and compliance.SubPolicy.PolicyId else '',
                'FrameworkName': compliance.SubPolicy.PolicyId.FrameworkId.name if compliance.SubPolicy and compliance.SubPolicy.PolicyId and compliance.SubPolicy.PolicyId.FrameworkId else ''
            })
        
        return Response({
            'success': True,
            'compliances': compliances_data
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([ComplianceKPIPermission])
@compliance_kpi_required
def get_ontime_mitigation_percentage(request):
    try:
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        # Get all risk instances that have been completed
        completed_risks = RiskInstance.objects.filter(
            MitigationStatus=RiskInstance.MITIGATION_COMPLETED,
            MitigationDueDate__isnull=False,
            MitigationCompletedDate__isnull=False
        )
        
        # Filter by framework if provided
        if framework_id:
            completed_risks = completed_risks.filter(FrameworkId=framework_id)
        
        total_completed = completed_risks.count()
        if total_completed == 0:
            return Response({
                'success': True,
                'data': {
                    'on_time_percentage': 0,
                    'total_completed': 0,
                    'completed_on_time': 0,
                    'completed_late': 0
                }
            })
        
        # Count how many were completed on or before due date
        completed_on_time = completed_risks.filter(
            MitigationCompletedDate__lte=models.F('MitigationDueDate')
        ).count()
        
        # Calculate percentage
        on_time_percentage = (completed_on_time / total_completed) * 100
        completed_late = total_completed - completed_on_time
        
        return Response({
            'success': True,
            'data': {
                'on_time_percentage': round(on_time_percentage, 1),
                'total_completed': total_completed,
                'completed_on_time': completed_on_time,
                'completed_late': completed_late
            }
        })
        
    except Exception as e:
        print(f"Error in get_ontime_mitigation_percentage: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliance_status_overview(request):
    try:
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        print(f"[STATUS OVERVIEW] Framework ID requested: {framework_id}")
        
        # Get all compliances
        compliances = Compliance.objects.all()
        
        print(f"[STATUS OVERVIEW] Total compliances before framework filter: {compliances.count()}")
        
        # Filter by framework if provided (through SubPolicy → Policy → Framework relationship)
        if framework_id:
            compliances = compliances.filter(SubPolicy__PolicyId__FrameworkId=framework_id)
            print(f"[STATUS OVERVIEW] Compliances after framework filter: {compliances.count()}")
        
        # Get counts for different statuses (excluding 'Active')
        status_counts = {
            'Approved': compliances.filter(Status='Approved').count(),
            'Under Review': compliances.filter(Status='Under Review').count(),
            'Rejected': compliances.filter(Status='Rejected').count()
        }
        
        print(f"[STATUS OVERVIEW] Status counts: {status_counts}")
        
        # Calculate percentages
        total = sum(status_counts.values())
        status_percentages = {
            status: round((count / total * 100), 1) if total > 0 else 0
            for status, count in status_counts.items()
        }
        
        return Response({
            'success': True,
            'data': {
                'counts': status_counts,
                'percentages': status_percentages,
                'total': total
            }
        })
        
    except Exception as e:
        print(f"Error in get_compliance_status_overview: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceAnalyticsPermission])
@compliance_analytics_required
def get_reputational_impact_assessment(request):
    try:
        import json
        from django.db import connection
        
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        # Use raw SQL to avoid Django ORM timezone conversion issues
        with connection.cursor() as cursor:
            if framework_id:
                cursor.execute("""
                    SELECT RiskFormDetails 
                    FROM risk_instance 
                    WHERE RiskFormDetails IS NOT NULL AND FrameworkId = %s
                """, [framework_id])
            else:
                cursor.execute("""
                    SELECT RiskFormDetails 
                    FROM risk_instance 
                    WHERE RiskFormDetails IS NOT NULL
                """)
            rows = cursor.fetchall()
        
        # Initialize counters for each impact level
        impact_counts = {
            'low': 0,
            'medium': 0,
            'high': 0
        }
        
        # Process each row to extract reputationalimpact values
        for row in rows:
            try:
                # Parse JSON if it's a string
                risk_details = row[0]
                if isinstance(risk_details, str):
                    risk_details = json.loads(risk_details)
                
                # Extract reputationalimpact value if exists
                if risk_details and 'reputationalimpact' in risk_details:
                    impact_level = risk_details['reputationalimpact'].lower()
                    if impact_level in impact_counts:
                        impact_counts[impact_level] += 1
            except Exception as e:
                print(f"Error processing risk details: {str(e)}")
                continue
        
        # Calculate total risks and percentages
        total_risks = sum(impact_counts.values())
        impact_percentages = {
            level: round((count / total_risks * 100), 2) if total_risks > 0 else 0
            for level, count in impact_counts.items()
        }
        
        return Response({
            'success': True,
            'data': {
                'impact_counts': impact_counts,
                'impact_percentages': impact_percentages,
                'total_risks': total_risks
            }
        })
        
    except Exception as e:
        print(f"Error in get_reputational_impact_assessment: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceAuditPermission])
@compliance_audit_required
def get_compliance_audit_info(request, compliance_id):
    """
    Get audit information for a specific compliance:
    1. Audit Performed By: UserId from lastchecklistitemverified
    2. Audit Approved By: UserId from audit_version
    3. Date of Audit Completion: Date from lastchecklistitemverified
    4. Audit Findings Status: Complied from lastchecklistitemverified
    """
    try:
        print(f"Fetching audit info for compliance ID: {compliance_id}")
        
        # First, get the LastChecklistItemVerified record for this compliance
        try:
            checklist_item = LastChecklistItemVerified.objects.filter(
                ComplianceId=compliance_id
            ).order_by('-Date', '-Time').first()
            
            if not checklist_item:
                print(f"No audit information found for compliance ID {compliance_id}")
                return Response({
                    'success': False,
                    'message': f'No audit information found for compliance ID {compliance_id}'
                }, status=404)
            
            print(f"Found checklist item: ComplianceId={checklist_item.ComplianceId}, User: {checklist_item.User}, Date: {checklist_item.Date}")
                
            # Get audit findings record if it exists
            audit_findings_id = checklist_item.AuditFindingsId
            audit_approver = None
            audit_id = None
            
            if audit_findings_id:
                try:
                    print(f"Found audit findings ID: {audit_findings_id}")
                    # Get the audit findings
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT AuditId 
                            FROM audit_findings 
                            WHERE AuditFindingsId = %s
                        """, [audit_findings_id])
                        result = cursor.fetchone()
                        
                        if result:
                            audit_id = result[0]
                            print(f"Found audit ID: {audit_id}")
                            
                            # Try to get audit approver from multiple sources
                            # First, try the audit table's reviewer field
                            cursor.execute("""
                                SELECT reviewer 
                                FROM audit 
                                WHERE AuditId = %s
                            """, [audit_id])
                            audit_result = cursor.fetchone()
                            
                            if audit_result and audit_result[0]:
                                audit_approver = audit_result[0]
                                print(f"Found audit approver from audit table: {audit_approver}")
                            else:
                                # Try the audit_version table
                                cursor.execute("""
                                    SELECT UserId
                                    FROM audit_version
                                    WHERE AuditId = %s AND ApprovedRejected = 'Approved'
                                    ORDER BY Date DESC
                                    LIMIT 1
                                """, [audit_id])
                                approver_result = cursor.fetchone()
                                
                                if approver_result:
                                    audit_approver = approver_result[0]
                                    print(f"Found audit approver from audit_version: {audit_approver}")
                except Exception as e:
                    print(f"Error getting audit approver: {str(e)}")
                    # Continue without audit approver
            
            # Get user names if possible
            performer_name = None
            approver_name = None
            
            try:
                with connection.cursor() as cursor:
                    if checklist_item.User:
                        cursor.execute("""
                            SELECT UserName FROM users WHERE UserId = %s
                        """, [checklist_item.User])
                        user_result = cursor.fetchone()
                        if user_result:
                            performer_name = user_result[0]
                            print(f"Found performer name: {performer_name}")
                    
                    if audit_approver:
                        cursor.execute("""
                            SELECT UserName FROM users WHERE UserId = %s
                        """, [audit_approver])
                        approver_result = cursor.fetchone()
                        if approver_result:
                            approver_name = approver_result[0]
                            print(f"Found approver name: {approver_name}")
            except Exception as e:
                print(f"Error getting user names: {str(e)}")
                # Continue without user names
            
            # Map compliance status
            compliance_status_map = {
                '0': 'Non Compliant',
                '1': 'Partially Compliant',
                '2': 'Fully Compliant',
                '3': 'Not Applicable'
            }
            
            compliance_status = compliance_status_map.get(checklist_item.Complied, 'Unknown')
            print(f"Compliance status: {compliance_status} (from value: {checklist_item.Complied})")
            
            # Build response data
            response_data = {
                'audit_id': audit_id,
                'audit_performer_id': checklist_item.User,
                'audit_performer_name': performer_name,
                'audit_approver_id': audit_approver,
                'audit_approver_name': approver_name,
                'audit_date': checklist_item.Date.strftime('%Y-%m-%d') if checklist_item.Date else None,
                'audit_time': checklist_item.Time.strftime('%H:%M:%S') if checklist_item.Time else None,
                'audit_findings_status': compliance_status,
                'audit_findings_id': audit_findings_id,
                'comments': checklist_item.Comments
            }
            
            print(f"Returning audit data: {response_data}")
            
            # Return the audit information
            return Response({
                'success': True,
                'data': response_data
            })
            
        except LastChecklistItemVerified.DoesNotExist:
            print(f"LastChecklistItemVerified.DoesNotExist for compliance ID {compliance_id}")
            return Response({
                'success': False,
                'message': f'No audit information found for compliance ID {compliance_id}'
            }, status=404)
            
    except Exception as e:
        print(f"Error in get_compliance_audit_info: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliance_details(request, compliance_id):
    """
    Get detailed information for a specific compliance by ID.
    This endpoint returns all fields of the compliance model.
    """
    try:
        compliance = get_object_or_404(Compliance, ComplianceId=compliance_id)
        

        
        # Prepare the detailed response with all available fields
        response_data = {
            'ComplianceId': compliance.ComplianceId,
            'ComplianceTitle': compliance.ComplianceTitle,
            'ComplianceItemDescription': compliance.ComplianceItemDescription,
            'ComplianceType': compliance.ComplianceType,
            'Scope': compliance.Scope,
            'Objective': compliance.Objective,
            'BusinessUnitsCovered': compliance.BusinessUnitsCovered,
            'IsRisk': compliance.IsRisk,
            'PossibleDamage': compliance.PossibleDamage,
            'mitigation': compliance.mitigation,
            'Criticality': compliance.Criticality,
            'MandatoryOptional': compliance.MandatoryOptional,
            'ManualAutomatic': compliance.ManualAutomatic,
            'Impact': compliance.Impact,
            'Probability': compliance.Probability,
            'MaturityLevel': compliance.MaturityLevel,
            'ActiveInactive': compliance.ActiveInactive,
            'PermanentTemporary': compliance.PermanentTemporary,
            'Status': compliance.Status,
            'ComplianceVersion': compliance.ComplianceVersion,
            'Identifier': compliance.Identifier,
            'Applicability': compliance.Applicability,
            'CreatedByName': compliance.CreatedByName,
            'CreatedByDate': compliance.CreatedByDate.isoformat() if compliance.CreatedByDate else None,
            'SubPolicy': compliance.SubPolicy_id,
            'PotentialRiskScenarios': compliance.PotentialRiskScenarios,
            'RiskType': compliance.RiskType,
            'RiskCategory': compliance.RiskCategory,
            'RiskBusinessImpact': compliance.RiskBusinessImpact
        }
        
        # Add the subpolicy and policy names
        try:
            response_data['SubPolicyName'] = compliance.SubPolicy.SubPolicyName
            response_data['PolicyName'] = compliance.SubPolicy.PolicyId.PolicyName
        except Exception as e:
            print(f"Error getting related names: {str(e)}")
            # Continue without related names
            
        # Get reviewer information from PolicyApproval table
        try:
            from ...models import PolicyApproval
            # Find the latest policy approval for this compliance
            latest_approval = PolicyApproval.objects.filter(
                Identifier=compliance.Identifier
            ).order_by('-ApprovalId').first()
            
            if latest_approval and latest_approval.ReviewerId:
                response_data['reviewer_id'] = latest_approval.ReviewerId
                print(f"Found reviewer_id: {latest_approval.ReviewerId} for compliance {compliance_id}")
            else:
                response_data['reviewer_id'] = None
                print(f"No reviewer found for compliance {compliance_id}, Identifier: {compliance.Identifier}")
        except Exception as e:
            print(f"Error getting reviewer information: {str(e)}")
            response_data['reviewer_id'] = None
            
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        print(f"Error in get_compliance_details: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([ComplianceKPIPermission])
@compliance_kpi_required
def get_remediation_cost_kpi(request):
    try:
        import json
        from django.db import connection
        from datetime import datetime, timedelta
        
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        # Use raw SQL to get all risk instances with RiskFormDetails
        with connection.cursor() as cursor:
            if framework_id:
                cursor.execute("""
                    SELECT RiskFormDetails,CreatedAt
                    FROM risk_instance 
                    WHERE RiskFormDetails IS NOT NULL AND FrameworkId = %s
                    ORDER BY CreatedAt
                """, [framework_id])
            else:
                cursor.execute("""
                    SELECT RiskFormDetails,CreatedAt
                    FROM risk_instance 
                    WHERE RiskFormDetails IS NOT NULL
                    ORDER BY CreatedAt
                """)
            rows = cursor.fetchall()
        
        # Initialize data structure
        cost_data = {
            'total_cost': 0,
            'average_cost': 0,
            'cost_by_category': {},
            'cost_by_month': {},
            'count': 0
        }
        
        # Process each row to extract cost values
        for row in rows:
            try:
                # Parse JSON if it's a string
                risk_details = row[0]
                risk_date = row[1]
                
                if isinstance(risk_details, str):
                    risk_details = json.loads(risk_details)
                
                # Extract cost value if exists
                if risk_details and 'cost' in risk_details:
                    try:
                        cost_value = float(risk_details['cost'])
                        cost_data['total_cost'] += cost_value
                        cost_data['count'] += 1
                        
                        # Add to category if exists
                        if 'category' in risk_details:
                            category = risk_details['category']
                            if category not in cost_data['cost_by_category']:
                                cost_data['cost_by_category'][category] = 0
                            cost_data['cost_by_category'][category] += cost_value
                        
                        # Format date to month-year
                        if risk_date:
                            if isinstance(risk_date, str):
                                date_obj = datetime.strptime(risk_date.split(' ')[0], '%Y-%m-%d')
                            else:
                                date_obj = risk_date
                                
                            month_year = date_obj.strftime('%b %Y')
                            if month_year not in cost_data['cost_by_month']:
                                cost_data['cost_by_month'][month_year] = 0
                            cost_data['cost_by_month'][month_year] += cost_value
                    except (ValueError, TypeError):
                        # Skip if cost is not a valid number
                        continue
            except Exception as e:
                print(f"Error processing risk details: {str(e)}")
                continue
        
        # Calculate average cost
        if cost_data['count'] > 0:
            cost_data['average_cost'] = round(cost_data['total_cost'] / cost_data['count'], 2)
        
        # Sort month-year data chronologically
        sorted_months = {}
        month_entries = sorted([(datetime.strptime(k, '%b %Y'), k, v) for k, v in cost_data['cost_by_month'].items()])
        for _, month_str, value in month_entries:
            sorted_months[month_str] = value
        
        cost_data['cost_by_month'] = sorted_months
        
        # Format for chart display
        chart_data = {
            'labels': list(sorted_months.keys()),
            'values': list(sorted_months.values())
        }
        
        # Get top categories by cost
        top_categories = sorted(cost_data['cost_by_category'].items(), key=lambda x: x[1], reverse=True)
        category_chart = {
            'labels': [cat for cat, _ in top_categories[:5]],  # Top 5 categories
            'values': [val for _, val in top_categories[:5]]
        }
        
        return Response({
            'success': True,
            'data': {
                'cost_summary': cost_data,
                'time_series_chart': chart_data,
                'category_chart': category_chart
            }
        })
        
    except Exception as e:
        print(f"Error in get_remediation_cost_kpi: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceAnalyticsPermission])
@compliance_analytics_required
def get_non_compliant_incidents_by_time(request):
    try:
        # Get framework_id from query parameters
        framework_id = request.GET.get('framework_id', None)
        
        # Get time period filter from request
        time_period = request.query_params.get('period', 'month')  # Default to last month
        print(f"Received request for non-compliant incidents with period: {time_period}")
        
        # Current date for calculations
        current_date = timezone.now().date()
        
        # Calculate date ranges based on period filter
        if time_period == 'week':
            # Last 7 days
            start_date = current_date - timedelta(days=7)
            period_name = 'Last 7 Days'
        elif time_period == 'month':
            # Last 30 days
            start_date = current_date - timedelta(days=30)
            period_name = 'Last 30 Days'
        elif time_period == 'quarter':
            # Last 90 days
            start_date = current_date - timedelta(days=90)
            period_name = 'Last 3 Months'
        elif time_period == 'year':
            # Last 365 days
            start_date = current_date - timedelta(days=365)
            period_name = 'Last 12 Months'
        else:
            # Invalid period, default to month
            print(f"Invalid time period: {time_period}, defaulting to month")
            start_date = current_date - timedelta(days=30)
            period_name = 'Last 30 Days'
            time_period = 'month'
            
        print(f"Using period: {period_name}, start_date: {start_date}, end_date: {current_date}")
            
        # Query non-compliant records within the date range
        # Non-compliant is where Complied = '0'
        non_compliant_records = LastChecklistItemVerified.objects.filter(
            Date__gte=start_date,
            Date__lte=current_date,
            Complied='0'
        )
        
        # Filter by framework if provided
        if framework_id:
            non_compliant_records = non_compliant_records.filter(FrameworkId=framework_id)
        
        print(f"Found {non_compliant_records.count()} non-compliant records")
        
        # Get the count
        non_compliant_count = non_compliant_records.count()
        
        # Get compliance item details grouped by item (ComplianceId)
        non_compliant_items = {}
        compliance_ids = set()
        
        for record in non_compliant_records:
            compliance_id = record.ComplianceId
            compliance_ids.add(compliance_id)
            
            if compliance_id not in non_compliant_items:
                non_compliant_items[compliance_id] = {
                    'count': 0,
                    'compliance_id': compliance_id,
                    'last_date': None,
                    'comments': []
                }
                
            non_compliant_items[compliance_id]['count'] += 1
            
            # Track most recent date
            record_date = record.Date
            if not non_compliant_items[compliance_id]['last_date'] or record_date > non_compliant_items[compliance_id]['last_date']:
                non_compliant_items[compliance_id]['last_date'] = record_date
                
            # Store comments (limit to avoid excessive data)
            if record.Comments and len(non_compliant_items[compliance_id]['comments']) < 5:
                non_compliant_items[compliance_id]['comments'].append(record.Comments)
        
        # Convert to list and sort by count
        non_compliant_list = sorted(
            list(non_compliant_items.values()),
            key=lambda x: x['count'],
            reverse=True
        )
        
        # Get compliance item details for top 10 items
        top_items_with_details = []
        for item in non_compliant_list[:10]:  # Limit to top 10
            try:
                compliance = Compliance.objects.get(ComplianceId=item['compliance_id'])
                item_details = {
                    'compliance_id': item['compliance_id'],
                    'count': item['count'],
                    'last_date': item['last_date'].isoformat() if item['last_date'] else None,
                    'comments': item['comments'],
                    'description': compliance.ComplianceItemDescription,
                    'criticality': compliance.Criticality,
                    'maturity_level': compliance.MaturityLevel
                }
                top_items_with_details.append(item_details)
            except Compliance.DoesNotExist:
                # Just add the basic item without compliance details
                item_details = {
                    'compliance_id': item['compliance_id'],
                    'count': item['count'],
                    'last_date': item['last_date'].isoformat() if item['last_date'] else None,
                    'comments': item['comments'],
                    'description': 'Unknown Compliance Item',
                    'criticality': 'Unknown',
                    'maturity_level': 'Unknown'
                }
                top_items_with_details.append(item_details)
        
        # Get trend data by grouping counts by day or week depending on period
        trend_data = {}
        if time_period in ['week', 'month']:
            # Group by day
            for record in non_compliant_records:
                day_key = record.Date.isoformat()
                if day_key not in trend_data:
                    trend_data[day_key] = 0
                trend_data[day_key] += 1
        else:
            # Group by week
            for record in non_compliant_records:
                # Get the week start date (Monday)
                week_start = record.Date - timedelta(days=record.Date.weekday())
                week_key = week_start.isoformat()
                if week_key not in trend_data:
                    trend_data[week_key] = 0
                trend_data[week_key] += 1
        
        # Sort the trend data by date
        sorted_trend = sorted(trend_data.items())
        
        # Format for chart display
        chart_data = {
            'labels': [item[0] for item in sorted_trend],
            'values': [item[1] for item in sorted_trend]
        }
        
        # Calculate percentage change from previous period
        previous_start_date = start_date - (current_date - start_date)
        previous_count = LastChecklistItemVerified.objects.filter(
            Date__gte=previous_start_date,
            Date__lt=start_date,
            Complied='0'
        ).count()
        
        if previous_count > 0:
            percentage_change = ((non_compliant_count - previous_count) / previous_count) * 100
        else:
            percentage_change = 100 if non_compliant_count > 0 else 0
        
        # Format percentage with proper sign
        percentage_formatted = f"{'+' if percentage_change > 0 else ''}{percentage_change:.1f}%"
        
        print(f"Sending response with non_compliant_count: {non_compliant_count}, unique_items: {len(compliance_ids)}")
        
        response_data = {
            'success': True,
            'data': {
                'non_compliant_count': non_compliant_count,
                'period': period_name,
                'start_date': start_date.isoformat(),
                'end_date': current_date.isoformat(),
                'percentage_change': percentage_formatted,
                'previous_period_count': previous_count,
                'top_non_compliant_items': top_items_with_details,
                'trend_data': chart_data,
                'unique_compliance_items': len(compliance_ids)
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        print(f"Error in get_non_compliant_incidents_by_time: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceNotificationPermission])
@compliance_notification_required
def test_notification(request):
    """Test endpoint to check if notifications are working"""
    try:
        from ...routes.Global.notification_service import NotificationService
        from ...models import Notification
        
        notification_service = NotificationService()
        
        # Test parameters
        test_email = request.query_params.get('email', 'test@example.com')
        notification_type = request.query_params.get('type', 'all')
        
        results = {}
        
        # Test compliance creation notification
        if notification_type in ['all', 'creation']:
            creation_data = {
                'notification_type': 'compliance_creation',
                'email': test_email,
                'email_type': 'gmail',
                'template_data': [
                    'Test Reviewer',
                    '12345',
                    'This is a test compliance description',
                    '1.0',
                    'Test Creator',
                    '2023-06-10'
                ]
            }
            results['creation'] = notification_service.send_multi_channel_notification(creation_data)
            
        # Test compliance edit notification
        if notification_type in ['all', 'edit']:
            edit_data = {
                'notification_type': 'compliance_edit',
                'email': test_email,
                'email_type': 'gmail',
                'template_data': [
                    'Test Reviewer',
                    '12345',
                    'Updated compliance description',
                    '1.1',
                    '1.0',
                    'Test Editor',
                    '2023-06-12'
                ]
            }
            results['edit'] = notification_service.send_multi_channel_notification(edit_data)
            
        # Test compliance approval notification
        if notification_type in ['all', 'approval']:
            approval_data = {
                'notification_type': 'compliance_review',
                'email': test_email,
                'email_type': 'gmail',
                'template_data': [
                    'Test Creator',
                    '12345',
                    'Approved compliance description',
                    '1.0',
                    'approved',
                    'This compliance looks good!'
                ]
            }
            results['approval'] = notification_service.send_multi_channel_notification(approval_data)
            
        # Test compliance rejection notification
        if notification_type in ['all', 'rejection']:
            rejection_data = {
                'notification_type': 'compliance_review',
                'email': test_email,
                'email_type': 'gmail',
                'template_data': [
                    'Test Creator',
                    '12345',
                    'Rejected compliance description',
                    '1.0',
                    'rejected',
                    'This compliance needs more work.'
                ]
            }
            results['rejection'] = notification_service.send_multi_channel_notification(rejection_data)
            
        # Test version toggle notification
        if notification_type in ['all', 'toggle']:
            toggle_data = {
                'notification_type': 'policyStatusChange',
                'email': test_email,
                'email_type': 'gmail',
                'template_data': [
                    'Test User',
                    'Compliance COMP-12345 v1.0',
                    'Activated',
                    'Administrator',
                    '2023-06-15'
                ]
            }
            results['toggle'] = notification_service.send_multi_channel_notification(toggle_data)
        
        # Check if notifications were logged in the database
        recent_notifications = Notification.objects.filter(recipient=test_email).order_by('-created_at')[:10]
        notification_records = [{
            'id': n.id,
            'type': n.type,
            'channel': n.channel,
            'success': n.success,
            'created_at': n.created_at.isoformat() if n.created_at else None
        } for n in recent_notifications]
        
        return Response({
            'success': True,
            'message': 'Test notifications sent',
            'email': test_email,
            'results': results,
            'notification_records': notification_records,
            'db_record_count': recent_notifications.count()
        })
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'message': f'Error testing notification: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=500)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliance_framework_info(request, compliance_id):
    """
    Get framework information for a compliance item to restrict copying within the same framework
    """
    try:
        # Get the source compliance
        compliance = get_object_or_404(Compliance, ComplianceId=compliance_id)
        
        # Get the framework information
        try:
            subpolicy = SubPolicy.objects.get(SubPolicyId=compliance.SubPolicy_id)
            policy = subpolicy.PolicyId
            framework = policy.FrameworkId
            
            return Response({
                'success': True,
                'data': {
                    'compliance_id': compliance.ComplianceId,
                    'framework_id': framework.FrameworkId,
                    'framework_name': framework.FrameworkName,
                    'policy_id': policy.PolicyId,
                    'policy_name': policy.PolicyName,
                    'subpolicy_id': subpolicy.SubPolicyId,
                    'subpolicy_name': subpolicy.SubPolicyName
                }
            })
        except Exception as e:
            print(f"Error getting framework info: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving framework information'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Compliance.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Compliance not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceCategoryPermission])
@compliance_category_required
def get_category_values(request, source):
    """
    Get all values for a specific category source from CategoryBusinessUnit table
    """
    try:
        from ...models import CategoryBusinessUnit
        
        # Validate source parameter
        allowed_sources = ['BusinessUnitsCovered', 'RiskType', 'RiskCategory', 'RiskBusinessImpact', 'Categories']
        if source not in allowed_sources:
            return Response({
                'success': False,
                'message': f'Invalid source. Allowed sources: {", ".join(allowed_sources)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get values for the specified source
        categories = CategoryBusinessUnit.objects.filter(source=source).values_list('value', flat=True).distinct().order_by('value')
        
        return Response({
            'success': True,
            'data': list(categories)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching category values: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@require_http_methods(["POST"])
@csrf_exempt
@permission_classes([ComplianceCategoryPermission])
@compliance_category_required
def add_category_value(request):
    """
    Add a new value to CategoryBusinessUnit table
    """
    try:
        from ...models import CategoryBusinessUnit
        
        # Parse JSON data from request body
        try:
            data = json.loads(request.body.decode('utf-8'))
            source = data.get('source')
            value = data.get('value')
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        
        # Validate required fields
        if not source or not value:
            return JsonResponse({
                'success': False,
                'message': 'Both source and value are required'
            }, status=400)
        
        # Validate source parameter
        allowed_sources = ['BusinessUnitsCovered', 'RiskType', 'RiskCategory', 'RiskBusinessImpact']
        if source not in allowed_sources:
            return JsonResponse({
                'success': False,
                'message': f'Invalid source. Allowed sources: {", ".join(allowed_sources)}'
            }, status=400)
        
        # Check if the value already exists for this source
        existing = CategoryBusinessUnit.objects.filter(source=source, value=value).first()
        if existing:
            return JsonResponse({
                'success': True,
                'message': 'Value already exists',
                'data': {'id': existing.id, 'source': existing.source, 'value': existing.value}
            })
        
        # Create new category entry
        new_category = CategoryBusinessUnit.objects.create(
            source=source,
            value=value.strip()
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Category value added successfully',
            'data': {'id': new_category.id, 'source': new_category.source, 'value': new_category.value}
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error adding category value: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([ComplianceCategoryPermission])
@compliance_category_required
def initialize_default_categories(request):
    print("Initializing default categories")
    try:
        from ...models import CategoryBusinessUnit

        # Log incoming request data
        print(f"Request Data: {request.data}")

        # Default values for each source
        default_values = {
            'BusinessUnitsCovered': [
                'Sales & Marketing',
                'Finance & Accounting',
                'Human Resources',
                'Information Technology',
                'Operations',
                'Legal & Compliance',
                'Customer Service',
                'Research & Development',
                'Procurement',
                'Risk Management'
            ],
            'RiskType': [
                'Operational Risk',
                'Financial Risk',
                'Strategic Risk',
                'Compliance Risk',
                'Reputational Risk',
                'Technology Risk',
                'Market Risk',
                'Credit Risk',
                'Legal Risk',
                'Environmental Risk'
            ],
            'RiskCategory': [
                'People Risk',
                'Process Risk',
                'Technology Risk',
                'External Risk',
                'Information Risk',
                'Physical Risk',
                'Systems Risk',
                'Vendor Risk',
                'Regulatory Risk',
                'Fraud Risk'
            ],
            'RiskBusinessImpact': [
                'Revenue Loss',
                'Customer Impact',
                'Operational Disruption',
                'Brand Damage',
                'Regulatory Penalties',
                'Legal Costs',
                'Data Loss',
                'Service Downtime',
                'Productivity Loss',
                'Compliance Violations'
            ]
        }

        added_count = 0
        for source, values in default_values.items():
            for value in values:
                # Check if the value already exists
                existing = CategoryBusinessUnit.objects.filter(source=source, value=value).first()
                if not existing:
                    CategoryBusinessUnit.objects.create(source=source, value=value)
                    added_count += 1

        return Response({
            'success': True,
            'message': f'Default categories initialized. Added {added_count} new values.',
            'added_count': added_count
        })

    except Exception as e:
        # Log the error and the exception message
        print(f"Error initializing default categories: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error initializing default categories: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_category_business_units(request):
    """
    API endpoint to get CategoryBusinessUnit values by source
    """
    try:
        from ...models import CategoryBusinessUnit
        
        source = request.query_params.get('source')
        if not source:
            return Response({"error": "Source parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        units = CategoryBusinessUnit.objects.filter(source=source)
        units_data = [{"id": unit.id, "value": unit.value} for unit in units]
        
        return Response({
            "success": True,
            "data": units_data
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([ComplianceBusinessUnitPermission])
@compliance_business_unit_required
def add_category_business_unit(request):
    """
    API endpoint to add a new CategoryBusinessUnit
    """
    try:
        from ...models import CategoryBusinessUnit
        
        data = request.data
        source = data.get('source')
        value = data.get('value')
        
        if not source or not value:
            return Response({"error": "Both source and value are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the value already exists for this source
        if CategoryBusinessUnit.objects.filter(source=source, value=value).exists():
            return Response({"error": f"Value '{value}' already exists for source '{source}'"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new record
        new_unit = CategoryBusinessUnit.objects.create(source=source, value=value)
        
        return Response({
            "success": True,
            "data": {
                "id": new_unit.id,
                "source": new_unit.source,
                "value": new_unit.value
            }
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([ComplianceEditPermission])
@compliance_edit_required
def edit_compliance(request, compliance_id):
    """
    Edit an existing compliance item
    """
    try:
        # Debug logging
        #print(f"DEBUG: Received edit_compliance request for ID {compliance_id}")
        #print(f"DEBUG: Request data: {request.data}")
        
        # Get the current user who is editing (the latest creator)
        from ...rbac.utils import RBACUtils
        from ...models import Users
        
        try:
            current_user_id = RBACUtils.get_user_id_from_request(request)
        except Exception:
            current_user_id = None
        if not current_user_id and hasattr(request, 'user') and getattr(request.user, 'UserId', None):
            current_user_id = request.user.UserId
        if not current_user_id:
            current_user_id = request.session.get('user_id')
        if not current_user_id and request.data.get('user_id'):
            try:
                current_user_id = int(request.data.get('user_id'))
            except Exception:
                current_user_id = None
        
        # Get the current user's name (the latest creator) - only fetch needed fields
        current_user_name = 'Unknown User'
        if current_user_id:
            try:
                user_obj = Users.objects.only('FirstName', 'LastName', 'UserName').get(UserId=current_user_id)
                current_user_name = (user_obj.FirstName + ' ' + user_obj.LastName).strip() if user_obj.FirstName or user_obj.LastName else user_obj.UserName
            except Exception:
                current_user_name = 'Unknown User'
        
        # Get the compliance item with related objects to avoid N+1 queries
        compliance = get_object_or_404(
            Compliance.objects.select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId'),
            ComplianceId=compliance_id
        )
        
        # Get the latest version of this compliance by Identifier
        latest_version = Compliance.objects.filter(
            Identifier=compliance.Identifier
        ).order_by('-ComplianceVersion').first()
        
        # Get version type from request data
        version_type = request.data.get('versionType')
        if not version_type:
            return Response({
                'success': False,
                'message': 'versionType is required. Must be either Major or Minor',
                'received_data': list(request.data.keys())
            }, status=status.HTTP_400_BAD_REQUEST)
        if version_type not in ['Major', 'Minor']:
            return Response({
                'success': False,
                'message': f'Invalid version type: {version_type}. Must be either Major or Minor',
                'received_version_type': version_type
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use the version calculated by the frontend
        new_version = request.data.get('ComplianceVersion')
        if not new_version:
            return Response({
                'success': False,
                'message': 'ComplianceVersion is required',
                'received_data': list(request.data.keys())
            }, status=status.HTTP_400_BAD_REQUEST)
        
        #print(f"DEBUG: Using frontend-calculated version: {new_version}")
        #print(f"DEBUG: Version type: {version_type}")

        # Get the policy through the subpolicy relationship
        policy = compliance.SubPolicy.PolicyId

        # Process mitigation data to ensure it's in the correct format
        mitigation_data = request.data.get('mitigation', {})
        
        # Use the helper function to format mitigation data
        processed_mitigation = format_mitigation_data(mitigation_data)
        
        #print(f"DEBUG: Original mitigation data: {mitigation_data}")
        #print(f"DEBUG: Processed mitigation data: {processed_mitigation}")

        # Get FrameworkId from the subpolicy's policy (use _id to get the integer ID)
        # Validate the relationship chain exists
        if not compliance.SubPolicy:
            return Response({
                'success': False,
                'message': 'Compliance must have a SubPolicy to determine FrameworkId'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not compliance.SubPolicy.PolicyId:
            return Response({
                'success': False,
                'message': 'SubPolicy must have a PolicyId to determine FrameworkId'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get framework_id and validate it's not None
        try:
            framework_id = compliance.SubPolicy.PolicyId.FrameworkId_id
            if framework_id is None:
                return Response({
                    'success': False,
                    'message': 'Policy must have a FrameworkId. Cannot create compliance approval without a framework.'
                }, status=status.HTTP_400_BAD_REQUEST)
            # Ensure framework_id is an integer
            framework_id = int(framework_id)
        except (AttributeError, ValueError, TypeError) as e:
            return Response({
                'success': False,
                'message': f'Invalid FrameworkId: {str(e)}. Cannot determine framework for this compliance.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        #print(f"DEBUG: Using FrameworkId_id: {framework_id} for compliance editing")
        
        # Create a new compliance instance with updated data
        new_compliance = Compliance.objects.create(
            SubPolicy=compliance.SubPolicy,  # Use the ForeignKey field directly
            PreviousComplianceVersionId=latest_version,  # Store reference to the latest version object
            ComplianceTitle=request.data.get('ComplianceTitle', ''),
            ComplianceItemDescription=request.data.get('ComplianceItemDescription', ''),
            ComplianceType=request.data.get('ComplianceType', ''),
            Scope=request.data.get('Scope', ''),
            Objective=request.data.get('Objective', ''),
            BusinessUnitsCovered=request.data.get('BusinessUnitsCovered', ''),
            IsRisk=request.data.get('IsRisk', False),
            PossibleDamage=request.data.get('PossibleDamage', ''),
            mitigation=processed_mitigation,  # Use the processed mitigation object
            PotentialRiskScenarios=request.data.get('PotentialRiskScenarios', ''),
            RiskType=request.data.get('RiskType', ''),
            RiskCategory=request.data.get('RiskCategory', ''),
            RiskBusinessImpact=request.data.get('RiskBusinessImpact', ''),
            Criticality=request.data.get('Criticality', 'Medium'),
            MandatoryOptional=request.data.get('MandatoryOptional', 'Mandatory'),
            ManualAutomatic=request.data.get('ManualAutomatic', 'Manual'),
            Impact=request.data.get('Impact', '5.0'),
            Probability=request.data.get('Probability', '5.0'),
            Status='Under Review',
            ComplianceVersion=new_version,
            Applicability=request.data.get('Applicability', ''),
            MaturityLevel=request.data.get('MaturityLevel', 'Initial'),
            ActiveInactive='Inactive',  # Set to Inactive by default for new versions
            PermanentTemporary=request.data.get('PermanentTemporary', 'Permanent'),
            CreatedByName=current_user_name,  # Use the current user (latest creator) who is editing
            CreatedByDate=datetime.date.today(),
            Identifier=compliance.Identifier,  # Preserve the original identifier
            FrameworkId_id=framework_id  # Use _id suffix to assign foreign key directly by ID
        )

        # Create extracted data for PolicyApproval
        extracted_data = {
            'type': 'compliance',
            'compliance_id': new_compliance.ComplianceId,  # Use compliance_id instead of ComplianceId
            'ComplianceTitle': new_compliance.ComplianceTitle,
            'ComplianceItemDescription': new_compliance.ComplianceItemDescription,
            'ComplianceType': new_compliance.ComplianceType,
            'Scope': new_compliance.Scope,
            'Objective': new_compliance.Objective,
            'BusinessUnitsCovered': new_compliance.BusinessUnitsCovered,
            'IsRisk': new_compliance.IsRisk,
            'PossibleDamage': new_compliance.PossibleDamage,
            'mitigation': processed_mitigation,  # Include mitigation in response for debugging
            'Criticality': new_compliance.Criticality,
            'Status': new_compliance.Status,
            'version_type': version_type,
            'Identifier': new_compliance.Identifier,
            'CreatedByName': current_user_name,  # Use the current user (latest creator) who is editing
            'CreatedByDate': new_compliance.CreatedByDate.isoformat() if new_compliance.CreatedByDate else None,  # Add CreatedByDate
            'ComplianceVersion': new_compliance.ComplianceVersion,  # Add ComplianceVersion
            'Impact': new_compliance.Impact,  # Add Impact field
            'Probability': new_compliance.Probability  # Add Probability field
        }

        # Create PolicyApproval for the new version
        # Resolve the effective logged-in user id (prefer JWT/session over payload)
        reviewer_id = request.data.get('reviewer_id') or request.data.get('ReviewerId')
        effective_user_id = None
        try:
            effective_user_id = RBACUtils.get_user_id_from_request(request)
        except Exception:
            effective_user_id = None
        if not effective_user_id and hasattr(request, 'user') and getattr(request.user, 'UserId', None):
            effective_user_id = request.user.UserId
        if not effective_user_id:
            effective_user_id = request.session.get('user_id')
        if not effective_user_id:
            effective_user_id = request.data.get('UserId')
        # Normalize to int when possible
        try:
            if isinstance(effective_user_id, str):
                effective_user_id = int(effective_user_id)
        except Exception:
            pass
        
        # Enforce that both user_id and reviewer_id are provided/derived
        if not effective_user_id:
            return Response({
                'success': False,
                'message': 'Unable to resolve logged-in user. Please re-authenticate.'
            }, status=status.HTTP_400_BAD_REQUEST)
        if not reviewer_id:
            return Response({
                'success': False,
                'message': 'ReviewerId is required and must be set to the selected reviewer.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize reviewer_id and effective_user_id to integers
        try:
            reviewer_id = int(reviewer_id) if reviewer_id else None
            effective_user_id = int(effective_user_id) if effective_user_id else None
        except (ValueError, TypeError) as e:
            return Response({
                'success': False,
                'message': f'Invalid ReviewerId or UserId: {str(e)}. Both must be valid integers.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # For version tracking, compute next user version for this Identifier
        # Use database query with only() to minimize data transfer
        identifier = new_compliance.Identifier
        u_versions = ComplianceApproval.objects.filter(
            Identifier=identifier,
            Version__startswith='u'
        ).only('Version').values_list('Version', flat=True)
        
        # Find the highest version number
        highest_u_version = 0
        for version_str in u_versions:
            if version_str and len(version_str) > 1:
                try:
                    version_num = int(version_str[1:])  # Extract number after 'u'
                    if version_num > highest_u_version:
                        highest_u_version = version_num
                except ValueError:
                    continue
        
        next_user_version = f"u{highest_u_version + 1}"
        
        # Validate framework_id is valid before creating ComplianceApproval
        if framework_id is None:
            return Response({
                'success': False,
                'message': 'FrameworkId is required for ComplianceApproval. Cannot create approval without a framework.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure framework_id is an integer
        try:
            framework_id = int(framework_id)
        except (ValueError, TypeError) as e:
            return Response({
                'success': False,
                'message': f'Invalid FrameworkId: {str(e)}. FrameworkId must be a valid integer.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        compliance_approval = ComplianceApproval.objects.create(
            Identifier=identifier,
            ExtractedData=extracted_data,
            UserId=effective_user_id,  # Set to the current logged-in user
            ReviewerId=reviewer_id,  # Set to the selected reviewer
            Version=next_user_version,  # Increment user version
            ApprovedNot=None,  # Pending approval
            ApprovalDueDate=datetime.date.today() + datetime.timedelta(days=7),  # Due in 7 days
            PolicyId=policy,  # Set the policy relationship correctly
            FrameworkId_id=framework_id  # Add FrameworkId to compliance approval (use _id suffix for foreign key)
        )

        #print(f"DEBUG: Successfully created compliance with mitigation: {new_compliance.mitigation}")
        #print(f"DEBUG: Mitigation type in database: {type(new_compliance.mitigation)}")
        #print(f"DEBUG: Mitigation JSON representation: {json.dumps(new_compliance.mitigation) if new_compliance.mitigation else 'None'}")
        
        return Response({
            'success': True,
            'message': 'Compliance updated successfully',
            'data': {
                'ComplianceId': new_compliance.ComplianceId,
                'Version': new_version,
                'Status': new_compliance.Status,
                'ApprovalId': compliance_approval.ApprovalId,
                'mitigation': processed_mitigation  # Include mitigation in response for debugging
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to update compliance: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([ComplianceClonePermission])
@compliance_clone_required
def clone_compliance(request, compliance_id):
    """
    Clone an existing compliance item
    """
    try:
        print(f"\n=== CLONE_COMPLIANCE DEBUG ===")
        print(f"Cloning compliance ID: {compliance_id}")
        print(f"Request data: {request.data}")
        
        # Get the source compliance
        source_compliance = get_object_or_404(Compliance, ComplianceId=compliance_id)
        print(f"Found source compliance: {source_compliance.ComplianceId}, {source_compliance.ComplianceTitle}")
        
        # Get data from request
        data = request.data.copy()
        
        # Get target subpolicy ID from request data
        target_subpolicy_id = data.get('target_subpolicy_id') or data.get('SubPolicy')
        if not target_subpolicy_id:
            print(f"ERROR: No target subpolicy ID provided in request")
            return Response({
                'success': False,
                'message': 'Target SubPolicy ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        print(f"Target SubPolicy ID: {target_subpolicy_id}")
        
        # Verify target subpolicy exists
        try:
            target_subpolicy = SubPolicy.objects.get(SubPolicyId=target_subpolicy_id)
            print(f"Found target subpolicy: {target_subpolicy.SubPolicyId}, {target_subpolicy.SubPolicyName}")
        except SubPolicy.DoesNotExist:
            print(f"ERROR: Target SubPolicy {target_subpolicy_id} not found")
            return Response({
                'success': False,
                'message': f'Target SubPolicy with ID {target_subpolicy_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Set default values if not provided
        data.setdefault('Status', 'Under Review')
        data.setdefault('ActiveInactive', 'Inactive')  # Set to Inactive by default for new versions
        data.setdefault('CreatedByDate', datetime.date.today())
        data.setdefault('ComplianceVersion', '1.0')
        data.setdefault('CreatedByName', source_compliance.CreatedByName)  # Preserve original creator's name
        
        # Get ComplianceTitle from request or use source compliance title
        compliance_title = data.get('ComplianceTitle', source_compliance.ComplianceTitle)
        print(f"Using compliance title: {compliance_title}")
        
        # Process mitigation data to ensure it's in JSON format
        mitigation_data = data.get('mitigation', source_compliance.mitigation)
        formatted_mitigation = {}
        
        # If mitigation is already a dict, use it
        if isinstance(mitigation_data, dict):
            formatted_mitigation = mitigation_data
            print(f"Mitigation is already a dict: {formatted_mitigation}")
        # If it's a string, try to parse as JSON
        elif isinstance(mitigation_data, str) and mitigation_data.strip():
            try:
                # Try to parse as JSON
                if mitigation_data.strip().startswith('{'):
                    formatted_mitigation = json.loads(mitigation_data)
                    print(f"Parsed mitigation from JSON string: {formatted_mitigation}")
                else:
                    # Not JSON, use as single entry
                    formatted_mitigation = {"1": mitigation_data}
                    print(f"Created numbered mitigation from string: {formatted_mitigation}")
            except json.JSONDecodeError:
                # Not valid JSON, use as single entry
                formatted_mitigation = {"1": mitigation_data}
                print(f"Created numbered mitigation from invalid JSON: {formatted_mitigation}")
        else:
            # Default empty object
            formatted_mitigation = {}
            print("Using empty mitigation object")
        
        # Store mitigation as JSON object (not string) for proper database storage
        print(f"Final mitigation object: {formatted_mitigation}")
        
        # Create new compliance instance
        new_compliance = Compliance.objects.create(
            SubPolicy_id=target_subpolicy_id,  # Use target subpolicy ID from request
            ComplianceTitle=compliance_title,
            ComplianceItemDescription=data.get('ComplianceItemDescription', source_compliance.ComplianceItemDescription),
            ComplianceType=data.get('ComplianceType', source_compliance.ComplianceType),
            Scope=data.get('Scope', source_compliance.Scope),
            Objective=data.get('Objective', source_compliance.Objective),
            BusinessUnitsCovered=data.get('BusinessUnitsCovered', source_compliance.BusinessUnitsCovered),
            IsRisk=data.get('IsRisk', source_compliance.IsRisk),
            PossibleDamage=data.get('PossibleDamage', source_compliance.PossibleDamage),
            mitigation=formatted_mitigation,  # Store as JSON object, not string
            PotentialRiskScenarios=data.get('PotentialRiskScenarios', source_compliance.PotentialRiskScenarios),
            RiskType=data.get('RiskType', source_compliance.RiskType),
            RiskCategory=data.get('RiskCategory', source_compliance.RiskCategory),
            RiskBusinessImpact=data.get('RiskBusinessImpact', source_compliance.RiskBusinessImpact),
            Criticality=data.get('Criticality', source_compliance.Criticality),
            MandatoryOptional=data.get('MandatoryOptional', source_compliance.MandatoryOptional),
            ManualAutomatic=data.get('ManualAutomatic', source_compliance.ManualAutomatic),
            Impact=data.get('Impact', source_compliance.Impact),
            Probability=data.get('Probability', source_compliance.Probability),
            Status='Under Review',
            ActiveInactive='Active',
            PermanentTemporary=data.get('PermanentTemporary', source_compliance.PermanentTemporary),
            CreatedByDate=datetime.date.today(),
            ComplianceVersion='1.0',
            MaturityLevel=data.get('MaturityLevel', source_compliance.MaturityLevel),
            CreatedByName=data.get('CreatedByName', source_compliance.CreatedByName),
            Applicability=data.get('Applicability', source_compliance.Applicability)
        )
        
        print(f"Created new compliance with ID: {new_compliance.ComplianceId}")
        
        # Generate a new identifier
        identifier = f"COMP-{target_subpolicy_id}-{datetime.date.today().strftime('%y%m%d')}-{uuid.uuid4().hex[:6]}"
        new_compliance.Identifier = identifier
        new_compliance.save()
        # print(f"Generated identifier: {identifier}")
        
        # Get reviewer ID from request
        # Resolve reviewer from payload only; do not default to 1
        reviewer_id = data.get('reviewer_id') or data.get('reviewer')
        if not reviewer_id:
            return Response({'success': False, 'message': 'ReviewerId is required'}, status=status.HTTP_400_BAD_REQUEST)
        print(f"Using reviewer ID: {reviewer_id}")
        
        # Get the policy through the subpolicy relationship
        policy = target_subpolicy.PolicyId
        print(f"Using policy ID: {policy.PolicyId}")
        
        # Set approval due date
        approval_due_date = data.get('ApprovalDueDate', (datetime.date.today() + datetime.timedelta(days=7)).isoformat())
        print(f"Using approval due date: {approval_due_date}")
        
        # Create extracted data for PolicyApproval
        extracted_data = {
            'type': 'compliance',
            'ComplianceTitle': new_compliance.ComplianceTitle,
            'ComplianceItemDescription': new_compliance.ComplianceItemDescription,
            'Criticality': new_compliance.Criticality,
            'Impact': new_compliance.Impact,
            'Probability': new_compliance.Probability,
            'mitigation': formatted_mitigation,  # Use the formatted mitigation object (not the JSON string)
            'PossibleDamage': new_compliance.PossibleDamage,
            'IsRisk': new_compliance.IsRisk,
            'MandatoryOptional': new_compliance.MandatoryOptional,
            'ManualAutomatic': new_compliance.ManualAutomatic,
            'CreatedByName': new_compliance.CreatedByName,
            'CreatedByDate': new_compliance.CreatedByDate.isoformat(),
            'Status': new_compliance.Status,
            'ComplianceId': new_compliance.ComplianceId,
            'ComplianceVersion': new_compliance.ComplianceVersion,
            'SubPolicy': target_subpolicy_id,
            'Identifier': new_compliance.Identifier,  # Add the missing Identifier field
            'compliance_approval': {
                'approved': None,
                'remarks': '',
                'ApprovalDueDate': approval_due_date
            }
        }
        
        # Create ComplianceApproval entry
        # Resolve effective creator user id from JWT/session
        try:
            effective_user_id = RBACUtils.get_user_id_from_request(request)
        except Exception:
            effective_user_id = None
        if not effective_user_id and hasattr(request, 'user') and getattr(request.user, 'UserId', None):
            effective_user_id = request.user.UserId
        if not effective_user_id:
            effective_user_id = request.session.get('user_id')
        if not effective_user_id:
            effective_user_id = data.get('UserId')
        
        # Prepare creation data
        creation_data = {
            'PolicyId': policy,
            'Identifier': identifier,
            'ExtractedData': extracted_data,
            'UserId': effective_user_id,
            'ReviewerId': reviewer_id,
            'Version': 'u1',
            'ApprovedNot': None,  # Not yet approved
            'ApprovalDueDate': approval_due_date
        }
        
        # Add FrameworkId if available from the policy
        # Use FrameworkId_id to get the foreign key ID directly
        if hasattr(policy, 'FrameworkId_id') and policy.FrameworkId_id is not None:
            try:
                framework_id = int(policy.FrameworkId_id)
                # Use _id suffix to assign the foreign key ID directly
                creation_data['FrameworkId_id'] = framework_id
                print(f"Adding FrameworkId_id from policy: {framework_id}")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid FrameworkId '{policy.FrameworkId_id}' from policy, skipping: {e}")
        else:
            print(f"FrameworkId_id is None from policy, not adding to creation data")
        
        compliance_approval = ComplianceApproval.objects.create(**creation_data)
        
        print(f"Created compliance approval with ID: {compliance_approval.ApprovalId}")
        
        # Send notification to reviewer
        try:
            print("=== NOTIFICATION DEBUGGING - COMPLIANCE CLONE ===")
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Make sure reviewer has a valid email
            try:
                reviewer = Users.objects.get(UserId=reviewer_id)
                if not reviewer.Email or '@' not in reviewer.Email:
                    reviewer.Email = f"reviewer{reviewer_id}@example.com"
                    reviewer.save()
                    print(f"Updated reviewer {reviewer_id} with email {reviewer.Email}")
                
                print(f"Found reviewer: {reviewer.UserName} with email: {reviewer.Email}")
            except Users.DoesNotExist:
                print(f"ERROR: Reviewer with ID {reviewer_id} does not exist")
            
            # Send notification
            print(f"Sending clone notification for compliance {new_compliance.ComplianceId} to reviewer {reviewer_id}")
            notification_result = notification_service.send_compliance_clone_notification(
                compliance=new_compliance,
                reviewer_id=reviewer_id
            )
            
            if notification_result.get('success'):
                print(f"Successfully sent compliance clone notification to reviewer {reviewer_id}")
            else:
                print(f"Failed to send notification: {notification_result.get('error', 'Unknown error')}")
                print(f"Error details: {notification_result.get('errors', [])}") 
            
            # Log the notification directly in the database
            from ...models import Notification
            try:
                reviewer_email, reviewer_name = notification_service.get_user_email_by_id(reviewer_id)
                if reviewer_email:
                    Notification.objects.create(
                        recipient=reviewer_email,
                        type='compliance_clone',
                        channel='email',
                        success=notification_result.get('success', False)
                    )
                    print(f"Created clone notification record for {reviewer_email}")
            except Exception as db_error:
                print(f"ERROR creating notification record: {str(db_error)}")
                
            print("=== END NOTIFICATION DEBUGGING ===")
        except Exception as e:
            print(f"Error sending compliance clone notification: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Continue even if notification fails
        
        print("=== END CLONE_COMPLIANCE DEBUG ===\n")
        return Response({
            'success': True,
            'message': 'Compliance cloned successfully and sent for review',
            'compliance_id': new_compliance.ComplianceId,
            'Identifier': identifier,
            'version': new_compliance.ComplianceVersion,
            'reviewer_id': reviewer_id
        }, status=status.HTTP_201_CREATED)
        
    except Compliance.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Source compliance not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error in clone_compliance: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# for temporary use

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliances_by_type(request, type, id):
    print(f"\n=== GET_COMPLIANCES_BY_TYPE DEBUG ===")
    print(f"Received type: '{type}', id: {id} (type: {type(id)})")
    
    try:
        compliances = None
        
        if type == 'framework':
            print(f"Getting compliances for framework {id}")
            compliances = Compliance.objects.filter(SubPolicy__PolicyId__FrameworkId=id)
        elif type == 'policy':
            print(f"Getting compliances for policy {id}")
            compliances = Compliance.objects.filter(SubPolicy__PolicyId=id)
        elif type == 'subpolicy':
            print(f"Getting compliances for subpolicy {id}")
            compliances = Compliance.objects.filter(SubPolicy=id)
        else:
            print(f"Invalid type: {type}")
            return Response({
                'success': False,
                'message': f'Invalid type: {type}. Valid types are: framework, policy, subpolicy'
            }, status=400)
        
        print(f"Found {compliances.count()} compliances for {type} {id}")
        
        # Debug: Print each compliance
        for comp in compliances:
            print(f"Compliance: ID={comp.ComplianceId}, Title={comp.ComplianceTitle}, Status={comp.Status}")
        
        # Serialize the data
        serializer = ComplianceListSerializer(compliances, many=True)
        serialized_data = serializer.data
        
        print(f"Serialized {len(serialized_data)} compliances")
        
        # Format the response
        response_data = {
            'success': True, 
            'compliances': serialized_data,
            'count': len(serialized_data)
        }
        
        print(f"Final response: {response_data}")
        print("=== END GET_COMPLIANCES_BY_TYPE DEBUG ===\n")
        
        return Response(response_data)
        
    except Exception as e:
        print(f"Error in get_compliances_by_type: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error fetching compliances: {str(e)}'
        }, status=500)

def format_mitigation_data(mitigation_data):
    """
    Helper function to format and sanitize mitigation data
    Returns a properly formatted JSON-serializable object
    """
    processed_mitigation = {}
    
    try:
        #print(f"DEBUG: format_mitigation_data - Input data: {mitigation_data}")
        #print(f"DEBUG: format_mitigation_data - Input type: {type(mitigation_data)}")
        
        # Handle different input types
        if mitigation_data is None:
            #print(f"DEBUG: Mitigation data is None, using empty object")
            return {}
            
        if isinstance(mitigation_data, dict):
            # If it's already a dict, ensure values are strings and include all steps
            for key, value in mitigation_data.items():
                # Include all steps, including empty ones, to maintain step order
                processed_mitigation[str(key)] = str(value).strip() if value else ''
            #print(f"DEBUG: Processed dictionary mitigation data")
        elif isinstance(mitigation_data, str):
            try:
                # Try to parse as JSON
                import json
                if mitigation_data.strip().startswith('{') or mitigation_data.strip().startswith('['):
                    parsed = json.loads(mitigation_data)
                    
                    if isinstance(parsed, dict):
                        # Process dictionary format - include all steps
                        for key, value in parsed.items():
                            processed_mitigation[str(key)] = str(value).strip() if value else ''
                    elif isinstance(parsed, list):
                        # Process array format - include all steps
                        for i, item in enumerate(parsed):
                            if isinstance(item, dict) and 'description' in item:
                                processed_mitigation[str(i+1)] = str(item['description']).strip() if item['description'] else ''
                            else:
                                processed_mitigation[str(i+1)] = str(item).strip() if item else ''
                    
                    #print(f"DEBUG: Successfully parsed mitigation JSON string")
                else:
                    # Not JSON, use as single entry if not empty
                    if mitigation_data.strip():
                        processed_mitigation["1"] = mitigation_data.strip()
                    #print(f"DEBUG: Using mitigation data as single string entry")
            except json.JSONDecodeError as e:
                # Not valid JSON, use as single entry if not empty
                if mitigation_data.strip():
                    processed_mitigation["1"] = mitigation_data.strip()
                #print(f"DEBUG: JSON decode error: {str(e)}")
        elif isinstance(mitigation_data, list):
            # Process array format - include all steps
            for i, item in enumerate(mitigation_data):
                if isinstance(item, dict) and 'description' in item:
                    processed_mitigation[str(i+1)] = str(item['description']).strip() if item['description'] else ''
                else:
                    processed_mitigation[str(i+1)] = str(item).strip() if item else ''
            #print(f"DEBUG: Processed list mitigation data")
        else:
            # Unknown type
            print(f"DEBUG: Unknown mitigation data type: {type(mitigation_data)}, using empty object")
            
        # Validate that the processed data is JSON serializable
        import json
        json.dumps(processed_mitigation)
        
        #print(f"DEBUG: Final processed mitigation: {processed_mitigation}")
        return processed_mitigation
        
    except Exception as e:
        #print(f"DEBUG: Error formatting mitigation data: {str(e)}")
        return {}  # Return empty object on error

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def test_compliance_versioning_edge_cases(request):
    """
    Test endpoint to verify compliance versioning edge cases
    """
    try:
        print(f"\n=== TESTING COMPLIANCE VERSIONING EDGE CASES ===")
        
        test_results = []
        
        # Test Case 1: No approved versions
        print("Test Case 1: Testing with no approved versions...")
        test_compliance_with_no_approved = Compliance.objects.filter(
            Status__in=['Under Review', 'Rejected']
        ).first()
        
        if test_compliance_with_no_approved:
            can_validate, message = ComplianceVersioningValidator.validate_versioning_rules(
                test_compliance_with_no_approved.ComplianceId, 
                'activate'
            )
            test_results.append({
                'test_case': 'No approved versions',
                'compliance_id': test_compliance_with_no_approved.ComplianceId,
                'expected_result': 'Should fail',
                'actual_result': 'Passed' if can_validate else 'Failed',
                'message': message,
                'passed': not can_validate  # Should fail
            })
        
        # Test Case 2: All versions inactive
        print("Test Case 2: Testing with all versions inactive...")
        sample_identifier = Compliance.objects.filter(
            Status='Approved',
            ActiveInactive='Inactive'
        ).values_list('Identifier', flat=True).first()
        
        if sample_identifier:
            inactive_versions = Compliance.objects.filter(
                Identifier=sample_identifier,
                Status='Approved',
                ActiveInactive='Inactive'
            )
            
            if inactive_versions.exists():
                first_inactive = inactive_versions.first()
                can_validate, message = ComplianceVersioningValidator.validate_versioning_rules(
                    first_inactive.ComplianceId, 
                    'activate'
                )
                test_results.append({
                    'test_case': 'All versions inactive - activation',
                    'compliance_id': first_inactive.ComplianceId,
                    'expected_result': 'Should pass',
                    'actual_result': 'Passed' if can_validate else 'Failed',
                    'message': message,
                    'passed': can_validate  # Should pass
                })
        
        # Test Case 3: Already active version
        print("Test Case 3: Testing with already active version...")
        active_compliance = Compliance.objects.filter(
            Status='Approved',
            ActiveInactive='Active'
        ).first()
        
        if active_compliance:
            can_validate, message = ComplianceVersioningValidator.validate_versioning_rules(
                active_compliance.ComplianceId, 
                'activate'
            )
            test_results.append({
                'test_case': 'Already active version - activation',
                'compliance_id': active_compliance.ComplianceId,
                'expected_result': 'Should fail',
                'actual_result': 'Passed' if can_validate else 'Failed',
                'message': message,
                'passed': not can_validate  # Should fail
            })
        
        # Test Case 4: Deactivation without other versions
        print("Test Case 4: Testing deactivation without other versions...")
        single_version_identifier = Compliance.objects.filter(
            Status='Approved'
        ).values('Identifier').annotate(
            count=Count('Identifier')
        ).filter(count=1).first()
        
        if single_version_identifier:
            single_version = Compliance.objects.filter(
                Identifier=single_version_identifier['Identifier'],
                Status='Approved',
                ActiveInactive='Active'
            ).first()
            
            if single_version:
                can_validate, message = ComplianceVersioningValidator.validate_versioning_rules(
                    single_version.ComplianceId, 
                    'deactivate'
                )
                test_results.append({
                    'test_case': 'Deactivation without other versions',
                    'compliance_id': single_version.ComplianceId,
                    'expected_result': 'Should pass',
                    'actual_result': 'Passed' if can_validate else 'Failed',
                    'message': message,
                    'passed': can_validate  # Should pass
                })
        
        # Test Case 5: Multiple versions with one active
        print("Test Case 5: Testing multiple versions with one active...")
        multi_version_identifier = Compliance.objects.filter(
            Status='Approved'
        ).values('Identifier').annotate(
            count=Count('Identifier')
        ).filter(count__gt=1).first()
        
        if multi_version_identifier:
            versions = Compliance.objects.filter(
                Identifier=multi_version_identifier['Identifier'],
                Status='Approved'
            ).order_by('-ComplianceVersion')
            
            active_version = versions.filter(ActiveInactive='Active').first()
            inactive_version = versions.filter(ActiveInactive='Inactive').first()
            
            if active_version and inactive_version:
                # Test activating inactive version
                can_validate, message = ComplianceVersioningValidator.validate_versioning_rules(
                    inactive_version.ComplianceId, 
                    'activate'
                )
                test_results.append({
                    'test_case': 'Multiple versions - activate inactive',
                    'compliance_id': inactive_version.ComplianceId,
                    'expected_result': 'Should pass',
                    'actual_result': 'Passed' if can_validate else 'Failed',
                    'message': message,
                    'passed': can_validate  # Should pass
                })
                
                # Test deactivating active version
                can_validate, message = ComplianceVersioningValidator.validate_versioning_rules(
                    active_version.ComplianceId, 
                    'deactivate'
                )
                test_results.append({
                    'test_case': 'Multiple versions - deactivate active',
                    'compliance_id': active_version.ComplianceId,
                    'expected_result': 'Should pass',
                    'actual_result': 'Passed' if can_validate else 'Failed',
                    'message': message,
                    'passed': can_validate  # Should pass
                })
        
        # Test Case 6: Version status information
        print("Test Case 6: Testing version status information...")
        if multi_version_identifier:
            status_info = ComplianceVersioningValidator.get_version_status_info(
                multi_version_identifier['Identifier']
            )
            test_results.append({
                'test_case': 'Version status information',
                'compliance_id': 'N/A',
                'expected_result': 'Should return status info',
                'actual_result': f'Returned info for {len(status_info)} versions',
                'message': f'Status info: {status_info}',
                'passed': len(status_info) > 0
            })
        
        # Calculate overall results
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result['passed'])
        
        print(f"=== COMPLIANCE VERSIONING EDGE CASES TEST COMPLETED ===")
        print(f"Total tests: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}")
        
        return Response({
            'success': True,
            'message': 'Edge cases testing completed',
            'results': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'test_results': test_results
            }
        })
        
    except Exception as e:
        print(f"Error in edge cases testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error testing edge cases: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from ...serializers import PolicyApprovalSerializer
from ...models import PolicyApproval

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliance_approvals_by_user(request, user_id):
    """
    Get all compliance approvals where UserId matches the given user_id (My Tasks)
    Automatically applies framework filter from session if no explicit filter provided
    """
    try:
        from ...routes.Policy.framework_filter_helper import get_active_framework_filter
        from ...models import Users
        
        # Helper function to get user name by ID
        def get_user_name_by_id(user_id):
            """Get user's full name or username by UserId"""
            if not user_id:
                return None
            try:
                user = Users.objects.get(UserId=user_id)
                # Try to get full name first
                if user.FirstName or user.LastName:
                    full_name = f"{user.FirstName or ''} {user.LastName or ''}".strip()
                    if full_name:
                        return full_name
                # Fallback to username
                return user.UserName if user.UserName else None
            except Users.DoesNotExist:
                return None
            except Exception:
                return None
        
        # Check for explicit framework filter in query params
        framework_id = request.GET.get('framework_id', None)
        
        # If no explicit filter, check session-based framework filter
        if not framework_id:
            framework_id = get_active_framework_filter(request)
        
        print(f"🔍 DEBUG: get_compliance_approvals_by_user called with framework_id: {framework_id}")
        
        approvals = ComplianceApproval.objects.filter(UserId=user_id).order_by('-ApprovalId')
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering compliance approvals by framework_id: {framework_id}")
            approvals = approvals.filter(FrameworkId=framework_id)
            print(f"✅ Framework filter applied. Found {approvals.count()} compliance approvals.")
        
        # Serialize the approvals first
        serializer = ComplianceApprovalSerializer(approvals, many=True)
        serialized_data = serializer.data
        
        # Ensure CreatedByName is present in ExtractedData for all serialized approvals
        for approval_data in serialized_data:
            if approval_data.get('ExtractedData'):
                # Ensure CreatedByName is present
                if 'CreatedByName' not in approval_data['ExtractedData'] or not approval_data['ExtractedData'].get('CreatedByName'):
                    user_name = get_user_name_by_id(approval_data.get('UserId'))
                    if user_name:
                        approval_data['ExtractedData']['CreatedByName'] = user_name
            else:
                # If ExtractedData is None or missing, create it with CreatedByName
                approval_data['ExtractedData'] = {}
                user_name = get_user_name_by_id(approval_data.get('UserId'))
                if user_name:
                    approval_data['ExtractedData']['CreatedByName'] = user_name
        
        return Response(serialized_data, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliance_approvals_by_reviewer(request, user_id):
    """
    Get all compliance approvals where ReviewerId matches the given user_id (Reviewer Tasks)
    Automatically applies framework filter from session if no explicit filter provided
    """
    try:
        from ...routes.Policy.framework_filter_helper import get_active_framework_filter
        from ...models import Users
        
        # Helper function to get user name by ID
        def get_user_name_by_id(user_id):
            """Get user's full name or username by UserId"""
            if not user_id:
                return None
            try:
                user = Users.objects.get(UserId=user_id)
                # Try to get full name first
                if user.FirstName or user.LastName:
                    full_name = f"{user.FirstName or ''} {user.LastName or ''}".strip()
                    if full_name:
                        return full_name
                # Fallback to username
                return user.UserName if user.UserName else None
            except Users.DoesNotExist:
                return None
            except Exception:
                return None
        
        # Check for explicit framework filter in query params
        framework_id = request.GET.get('framework_id', None)
        
        # If no explicit filter, check session-based framework filter
        if not framework_id:
            framework_id = get_active_framework_filter(request)
        
        print(f"🔍 DEBUG: get_compliance_approvals_by_reviewer called with framework_id: {framework_id}")
        
        # Normalize user_id to integer to ensure proper matching
        try:
            reviewer_id = int(user_id) if user_id else None
            if not reviewer_id:
                return Response({'error': 'Invalid reviewer_id. Must be a valid integer.'}, status=400)
        except (ValueError, TypeError) as e:
            return Response({'error': f'Invalid reviewer_id: {str(e)}. Must be a valid integer.'}, status=400)
        
        print(f"🔍 DEBUG: Filtering compliance approvals by ReviewerId: {reviewer_id}")
        approvals = ComplianceApproval.objects.filter(ReviewerId=reviewer_id).order_by('-ApprovalId')
        print(f"✅ Found {approvals.count()} compliance approvals for reviewer {reviewer_id} (before framework filter)")
        
        # Log all framework IDs in the results before filtering
        if approvals.exists():
            framework_ids_before = approvals.values_list('FrameworkId_id', flat=True).distinct()
            print(f"🔍 DEBUG: Framework IDs in results before filter: {list(framework_ids_before)}")
        
        # Apply framework filter if provided
        if framework_id:
            # Normalize framework_id to integer for proper matching
            try:
                framework_id_int = int(framework_id) if framework_id else None
            except (ValueError, TypeError):
                framework_id_int = None
            
            if framework_id_int:
                print(f"🔍 DEBUG: Filtering compliance reviewer tasks by framework_id: {framework_id_int}")
                approvals_before_count = approvals.count()
                # Use FrameworkId_id for direct integer comparison (more reliable)
                approvals = approvals.filter(FrameworkId_id=framework_id_int)
                approvals_after_count = approvals.count()
                print(f"✅ Framework filter applied. Before: {approvals_before_count}, After: {approvals_after_count} compliance reviewer tasks.")
                
                # If framework filter resulted in 0 results, log a warning
                if approvals_after_count == 0 and approvals_before_count > 0:
                    print(f"⚠️ WARNING: Framework filter {framework_id_int} excluded all {approvals_before_count} records for reviewer {reviewer_id}")
                    print(f"⚠️ Consider checking if framework_id filter should be applied or if records have correct FrameworkId")
            else:
                print(f"⚠️ WARNING: Invalid framework_id '{framework_id}' - skipping framework filter")
        else:
            print(f"ℹ️ No framework filter applied - returning all records for reviewer {reviewer_id}")
        
        # Serialize the approvals first
        try:
            serializer = ComplianceApprovalSerializer(approvals, many=True)
            serialized_data = serializer.data
            
            # Ensure CreatedByName is present in ExtractedData for all serialized approvals
            for approval_data in serialized_data:
                if approval_data.get('ExtractedData'):
                    # Ensure CreatedByName is present
                    if 'CreatedByName' not in approval_data['ExtractedData'] or not approval_data['ExtractedData'].get('CreatedByName'):
                        user_name = get_user_name_by_id(approval_data.get('UserId'))
                        if user_name:
                            approval_data['ExtractedData']['CreatedByName'] = user_name
                else:
                    # If ExtractedData is None or missing, create it with CreatedByName
                    approval_data['ExtractedData'] = {}
                    user_name = get_user_name_by_id(approval_data.get('UserId'))
                    if user_name:
                        approval_data['ExtractedData']['CreatedByName'] = user_name
            
            print(f"✅ Successfully serialized {len(serialized_data)} compliance approvals")
            return Response(serialized_data, status=200)
        except Exception as serialize_error:
            print(f"❌ ERROR during serialization: {str(serialize_error)}")
            import traceback
            traceback.print_exc()
            # Try to get at least some data even if serialization fails partially
            try:
                # Get basic data without serializer
                basic_data = []
                for approval in approvals[:10]:  # Limit to first 10 to avoid too much data
                    basic_data.append({
                        'ApprovalId': approval.ApprovalId,
                        'Identifier': approval.Identifier,
                        'ReviewerId': approval.ReviewerId,
                        'UserId': approval.UserId,
                        'Version': approval.Version,
                        'ApprovedNot': approval.ApprovedNot,
                        'FrameworkId': approval.FrameworkId_id if hasattr(approval, 'FrameworkId_id') else None,
                        'error': f'Serialization failed: {str(serialize_error)}'
                    })
                return Response({
                    'error': f'Serialization error: {str(serialize_error)}',
                    'partial_data': basic_data,
                    'total_count': approvals.count()
                }, status=200)  # Return 200 with error message so frontend can handle it
            except Exception as fallback_error:
                print(f"❌ ERROR in fallback serialization: {str(fallback_error)}")
                return Response({
                    'error': f'Serialization failed: {str(serialize_error)}. Fallback also failed: {str(fallback_error)}'
                }, status=400)
    except Exception as e:
        print(f"❌ ERROR in get_compliance_approvals_by_reviewer: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e),
            'type': type(e).__name__
        }, status=400)


# Corrupted content removed - continuing with clean content
        """Validate numeric fields with range checking"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number")
        
        if min_val is not None and num_value < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and num_value > max_val:
            raise ValidationError(f"{field_name} must not exceed {max_val}")
        
        return num_value
    
    @staticmethod
    def validate_integer_field(value: Any, field_name: str, min_val: Optional[int] = None, 
                              max_val: Optional[int] = None) -> int:
        """Validate integer fields with range checking"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid integer")
        
        if min_val is not None and int_value < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and int_value > max_val:
            raise ValidationError(f"{field_name} must not exceed {max_val}")
        
        return int_value
    
    @staticmethod
    def validate_date_field(value: Any, field_name: str) -> str:
        """Validate date fields"""
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required")
        
        str_value = str(value).strip()
        
        if not ComplianceInputValidator.DATE_PATTERN.match(str_value):
            raise ValidationError(f"{field_name} must be in YYYY-MM-DD format")
        
        try:
            datetime.datetime.strptime(str_value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(f"{field_name} must be a valid date")
        
        return str_value
    
    @staticmethod
    def calculate_new_version(current_version: str, versioning_type: str) -> str:
        """Calculate new version based on versioning type"""
        # print(f"  calculate_new_version called with: current_version='{current_version}', versioning_type='{versioning_type}'")
        try:
            # Parse current version (e.g., "2.3" becomes 2.3)
            current_float = float(current_version) if current_version else 1.0
            # print(f"  Parsed current_float: {current_float}")
            
            if versioning_type == 'Minor':
                # For minor: add 0.1 to current version (e.g., 2.3 -> 2.4)
                new_version = round(current_float + 0.1, 1)
                # print(f"  Minor version calculation: {current_float} + 0.1 = {new_version}")
            elif versioning_type == 'Major':
                # For major: increment major version and reset minor to 0 (e.g., 2.3 -> 3.0)
                major = int(current_float)
                new_version = float(major + 1)
                # print(f"  Major version calculation: int({current_float}) + 1 = {new_version}")
            else:
                # Default behavior (Major)
                major = int(current_float)
                new_version = float(major + 1)
                # print(f"  Default (Major) version calculation: int({current_float}) + 1 = {new_version}")
            
            result = str(new_version)
            # print(f"  Returning: '{result}'")
            return result
        except (ValueError, TypeError) as e:
            # If parsing fails, default to incrementing major version
            # print(f"  Error in version calculation: {e}, returning '2.0'")
            return "2.0"
    
    @staticmethod
    def clean_mitigation_data(mitigation_data: str) -> str:
        """
        Clean and format mitigation data for consistent storage and display.
        Handles simple JSON format: {"1": "First step", "2": "Second step"}
        """
        if not mitigation_data:
            return "{}"
        
        # If it's already a JSON string, try to parse and validate
        if isinstance(mitigation_data, str) and (mitigation_data.strip().startswith('{') or mitigation_data.strip().startswith('[')):
            try:
                import json
                parsed = json.loads(mitigation_data)
                
                # Handle the simple step format: {"1": "First step", "2": "Second step"}
                if isinstance(parsed, dict):
                    cleaned_mitigation = {}
                    
                    # Check if all keys are numeric strings and values are strings
                    for key, value in parsed.items():
                        if isinstance(key, str) and key.isdigit() and isinstance(value, str):
                            if value.strip():  # Only include non-empty steps
                                cleaned_mitigation[key] = value.strip()
                        elif isinstance(key, int) and isinstance(value, str):
                            if value.strip():  # Only include non-empty steps
                                cleaned_mitigation[str(key)] = value.strip()
                    
                    # If we have valid steps, return the cleaned version
                    if cleaned_mitigation:
                        return json.dumps(cleaned_mitigation, separators=(',', ':'))
                
                # Handle legacy array format - convert to simple format
                if isinstance(parsed, list):
                    cleaned_mitigation = {}
                    for i, step in enumerate(parsed):
                        if isinstance(step, str) and step.strip():
                            cleaned_mitigation[str(i + 1)] = step.strip()
                    
                    if cleaned_mitigation:
                        return json.dumps(cleaned_mitigation, separators=(',', ':'))
                
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as plain text
                pass
        
        # Handle plain text - convert to simple JSON format
        if isinstance(mitigation_data, str) and mitigation_data.strip():
            import json
            
            # Try to split by common delimiters to create steps
            text = mitigation_data.strip()
            
            # Split by numbered patterns (1., 2., etc.) or newlines
            import re
            steps_text = re.split(r'(?:^|\n)\s*\d+\.\s*', text)
            if len(steps_text) > 1:
                # Remove empty first element if it exists
                if not steps_text[0].strip():
                    steps_text = steps_text[1:]
            else:
                # Split by newlines or semicolons
                steps_text = [s.strip() for s in re.split(r'[;\n]', text) if s.strip()]
            
            # If no clear steps found, treat as single step
            if not steps_text or (len(steps_text) == 1 and not steps_text[0].strip()):
                steps_text = [text]
            
            # Create step objects in simple format
            cleaned_mitigation = {}
            for i, step_text in enumerate(steps_text):
                if step_text.strip():
                    cleaned_mitigation[str(i + 1)] = step_text.strip()
            
            if cleaned_mitigation:
                return json.dumps(cleaned_mitigation, separators=(',', ':'))
        
        return "{}"
    
    @staticmethod
    def validate_mitigation_json(mitigation_data: str) -> bool:
        """
        Validate that mitigation data is properly formatted JSON with valid structure
        Expected format: {"1": "First step", "2": "Second step"}
        """
        if not mitigation_data:
            return True  # Empty is valid
        
        try:
            import json
            parsed = json.loads(mitigation_data)
            
            # Must be a dictionary
            if not isinstance(parsed, dict):
                return False
            
            # Check if all keys are numeric strings and values are non-empty strings
            for key, value in parsed.items():
                # Key must be a string representation of a number
                if not isinstance(key, str) or not key.isdigit():
                    return False
                
                # Value must be a non-empty string
                if not isinstance(value, str) or not value.strip():
                    return False
            
            return True
            
        except json.JSONDecodeError:
            return False
    
    @classmethod
    def validate_compliance_data(cls, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main validation method for compliance data using allow-list approach"""
        validated_data = {}
        errors = {}
        
        try:
            # Validate SubPolicy (required foreign key)
            validated_data['SubPolicy'] = cls.validate_integer_field(
                request_data.get('SubPolicy'), 'SubPolicy', min_val=1
            )
        except ValidationError as e:
            errors['SubPolicy'] = [str(e)]
        
        try:
            # Validate ComplianceTitle (required, max 145 chars)
            validated_data['ComplianceTitle'] = cls.validate_required_string(
                request_data.get('ComplianceTitle'), 'ComplianceTitle', 
                max_length=145, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceTitle'] = [str(e)]
        
        try:
            # Validate ComplianceItemDescription (required text field)
            validated_data['ComplianceItemDescription'] = cls.validate_required_string(
                request_data.get('ComplianceItemDescription'), 'ComplianceItemDescription',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceItemDescription'] = [str(e)]
        
        try:
            # Validate ComplianceType (required, max 100 chars)
            validated_data['ComplianceType'] = cls.validate_required_string(
                request_data.get('ComplianceType'), 'ComplianceType',
                max_length=100, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceType'] = [str(e)]
        
        try:
            # Validate Scope (required text field)
            validated_data['Scope'] = cls.validate_required_string(
                request_data.get('Scope'), 'Scope',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['Scope'] = [str(e)]
        
        try:
            # Validate Objective (required text field)
            validated_data['Objective'] = cls.validate_required_string(
                request_data.get('Objective'), 'Objective',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['Objective'] = [str(e)]
        
        try:
            # Validate BusinessUnitsCovered (required, max 225 chars)
            validated_data['BusinessUnitsCovered'] = cls.validate_required_string(
                request_data.get('BusinessUnitsCovered'), 'BusinessUnitsCovered',
                max_length=225, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['BusinessUnitsCovered'] = [str(e)]
        
        try:
            # Validate IsRisk (boolean)
            validated_data['IsRisk'] = cls.validate_boolean_field(
                request_data.get('IsRisk', False), 'IsRisk'
            )
        except ValidationError as e:
            errors['IsRisk'] = [str(e)]
        
        # If IsRisk is True, validate risk-related fields
        if validated_data.get('IsRisk', False):
            try:
                validated_data['PossibleDamage'] = cls.validate_required_string(
                    request_data.get('PossibleDamage'), 'PossibleDamage',
                    max_length=5000, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['PossibleDamage'] = [str(e)]
            
            try:
                validated_data['PotentialRiskScenarios'] = cls.validate_required_string(
                    request_data.get('PotentialRiskScenarios'), 'PotentialRiskScenarios',
                    max_length=5000, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['PotentialRiskScenarios'] = [str(e)]
            
            try:
                validated_data['RiskType'] = cls.validate_required_string(
                    request_data.get('RiskType'), 'RiskType',
                    max_length=45, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['RiskType'] = [str(e)]
            
            try:
                validated_data['RiskCategory'] = cls.validate_required_string(
                    request_data.get('RiskCategory'), 'RiskCategory',
                    max_length=45, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['RiskCategory'] = [str(e)]
            
            try:
                validated_data['RiskBusinessImpact'] = cls.validate_required_string(
                    request_data.get('RiskBusinessImpact'), 'RiskBusinessImpact',
                    max_length=45, pattern=cls.TEXT_PATTERN
                )
            except ValidationError as e:
                errors['RiskBusinessImpact'] = [str(e)]
        else:
            # Optional fields when IsRisk is False
            validated_data['PossibleDamage'] = cls.validate_optional_string(
                request_data.get('PossibleDamage'), 'PossibleDamage',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
            validated_data['PotentialRiskScenarios'] = cls.validate_optional_string(
                request_data.get('PotentialRiskScenarios'), 'PotentialRiskScenarios',
                max_length=5000, pattern=cls.TEXT_PATTERN
            )
            validated_data['RiskType'] = cls.validate_optional_string(
                request_data.get('RiskType'), 'RiskType',
                max_length=45, pattern=cls.TEXT_PATTERN
            )
            validated_data['RiskCategory'] = cls.validate_optional_string(
                request_data.get('RiskCategory'), 'RiskCategory',
                max_length=45, pattern=cls.TEXT_PATTERN
            )
            validated_data['RiskBusinessImpact'] = cls.validate_optional_string(
                request_data.get('RiskBusinessImpact'), 'RiskBusinessImpact',
                max_length=45, pattern=cls.TEXT_PATTERN
            )
        
        try:
            # Validate and clean mitigation (JSON step-by-step format)
            raw_mitigation = request_data.get('mitigation')
            # Always use format_mitigation_data to handle both string and object types
            formatted_mitigation = format_mitigation_data(raw_mitigation)
            # If risk requires mitigation but none provided, add error
            if validated_data.get('IsRisk', False) and not formatted_mitigation:
                errors['mitigation'] = ["At least one mitigation step is required for risks"]
            else:
                validated_data['mitigation'] = formatted_mitigation
                # Debug log
                #print(f"DEBUG: Validated mitigation data: {formatted_mitigation}")
        except Exception as e:
            errors['mitigation'] = [f"Error processing mitigation data: {str(e)}"]
        
        try:
            # Validate Criticality (required choice field)
            validated_data['Criticality'] = cls.validate_choice_field(
                request_data.get('Criticality'), 'Criticality', cls.ALLOWED_CRITICALITY
            )
        except ValidationError as e:
            errors['Criticality'] = [str(e)]
        
        try:
            # Validate MandatoryOptional (required choice field)
            validated_data['MandatoryOptional'] = cls.validate_choice_field(
                request_data.get('MandatoryOptional'), 'MandatoryOptional', cls.ALLOWED_MANDATORY_OPTIONAL
            )
        except ValidationError as e:
            errors['MandatoryOptional'] = [str(e)]
        
        try:
            # Validate ManualAutomatic (required choice field)
            validated_data['ManualAutomatic'] = cls.validate_choice_field(
                request_data.get('ManualAutomatic'), 'ManualAutomatic', cls.ALLOWED_MANUAL_AUTOMATIC
            )
        except ValidationError as e:
            errors['ManualAutomatic'] = [str(e)]
        
        try:
            # Validate Impact (required numeric field, 1-10)
            validated_data['Impact'] = cls.validate_numeric_field(
                request_data.get('Impact'), 'Impact', min_val=1.0, max_val=10.0
            )
        except ValidationError as e:
            errors['Impact'] = [str(e)]
        
        try:
            # Validate Probability (required numeric field, 1-10)
            validated_data['Probability'] = cls.validate_numeric_field(
                request_data.get('Probability'), 'Probability', min_val=1.0, max_val=10.0
            )
        except ValidationError as e:
            errors['Probability'] = [str(e)]
        
        try:
            # Validate ComplianceVersion (required, max 50 chars, version pattern)
            validated_data['ComplianceVersion'] = cls.validate_required_string(
                request_data.get('ComplianceVersion', '1.0'), 'ComplianceVersion',
                max_length=50, pattern=cls.VERSION_PATTERN
            )
        except ValidationError as e:
            errors['ComplianceVersion'] = [str(e)]
        
        try:
            # Validate Applicability (optional, max 450 chars)
            validated_data['Applicability'] = cls.validate_optional_string(
                request_data.get('Applicability'), 'Applicability',
                max_length=450, pattern=cls.TEXT_PATTERN
            )
        except ValidationError as e:
            errors['Applicability'] = [str(e)]
        
        try:
            # Validate Identifier (optional, max 45 chars, identifier pattern)
            identifier = request_data.get('Identifier', '').strip()
            if identifier:
                validated_data['Identifier'] = cls.validate_optional_string(
                    identifier, 'Identifier', max_length=45, pattern=cls.IDENTIFIER_PATTERN
                )
            else:
                validated_data['Identifier'] = ''
        except ValidationError as e:
            errors['Identifier'] = [str(e)]
            # Set to empty string if validation fails, so auto-generation will be used
            validated_data['Identifier'] = ''
        
        try:
            # Validate reviewer (required integer)
            validated_data['reviewer'] = cls.validate_integer_field(
                request_data.get('reviewer'), 'reviewer', min_val=1
            )
        except ValidationError as e:
            errors['reviewer'] = [str(e)]
        
        try:
            # Validate ApprovalDueDate (required date)
            validated_data['ApprovalDueDate'] = cls.validate_date_field(
                request_data.get('ApprovalDueDate'), 'ApprovalDueDate'
            )
        except ValidationError as e:
            errors['ApprovalDueDate'] = [str(e)]
        
        # Set default values for system fields
        validated_data['Status'] = 'Under Review'
        validated_data['ActiveInactive'] = 'Inactive'
        validated_data['PermanentTemporary'] = 'Permanent'
        validated_data['MaturityLevel'] = 'Initial'
        
        # Always copy CreatedByName from request_data if present (no validation, just sanitize)
        if 'CreatedByName' in request_data:
            validated_data['CreatedByName'] = str(request_data['CreatedByName']).strip()
        
        if errors:
            raise ValidationError(errors)
        
        return validated_data


@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_framework_compliances(request, framework_id):
    """Get all compliances under a framework"""

    logging.info(f"Getting compliances for framework_id: {framework_id}")
    try:
        framework = get_object_or_404(Framework, FrameworkId=framework_id)
        logging.info(f"Found framework: {framework.FrameworkName}")

        # Log the SQL query before executing it
        compliances = Compliance.objects.filter(
            SubPolicy__PolicyId__FrameworkId=framework
        ).select_related('SubPolicy', 'SubPolicy__PolicyId')
        
        logging.info(f"SQL Query: {connection.queries[-1]}")
        
        compliances_data = []
        for compliance in compliances:
            compliances_data.append({
                'ComplianceId': compliance.ComplianceId,
                'ComplianceItemDescription': compliance.ComplianceItemDescription,
                'Status': compliance.Status,
                'Criticality': compliance.Criticality,
                'MaturityLevel': compliance.MaturityLevel,
                'MandatoryOptional': compliance.MandatoryOptional,
                'ManualAutomatic': compliance.ManualAutomatic,
                'CreatedByName': compliance.CreatedByName,
                'CreatedByDate': compliance.CreatedByDate,
                'ComplianceVersion': compliance.ComplianceVersion,
                'Identifier': compliance.Identifier,
                'PermanentTemporary': compliance.PermanentTemporary,
                'SubPolicyName': compliance.SubPolicy.SubPolicyName,
                'PolicyName': compliance.SubPolicy.PolicyId.PolicyName
            })
        
        return Response({
            'success': True,
            'name': framework.FrameworkName,
            'compliances': compliances_data
        })
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_policy_compliances(request, policy_id):
    """Get all compliances under a policy"""
    try:
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        compliances = Compliance.objects.filter(
            SubPolicy__PolicyId=policy
        ).select_related('SubPolicy')
        
        compliances_data = []
        for compliance in compliances:
            compliances_data.append({
                'ComplianceId': compliance.ComplianceId,
                'ComplianceItemDescription': compliance.ComplianceItemDescription,
                'Status': compliance.Status,
                'Criticality': compliance.Criticality,
                'MaturityLevel': compliance.MaturityLevel,
                'MandatoryOptional': compliance.MandatoryOptional,
                'ManualAutomatic': compliance.ManualAutomatic,
                'CreatedByName': compliance.CreatedByName,
                'CreatedByDate': compliance.CreatedByDate,
                'ComplianceVersion': compliance.ComplianceVersion,
                'Identifier': compliance.Identifier,
                'PermanentTemporary': compliance.PermanentTemporary,
                'SubPolicyName': compliance.SubPolicy.SubPolicyName
            })
        
        return Response({
            'success': True,
            'name': policy.PolicyName,
            'compliances': compliances_data
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@csrf_exempt
@permission_classes([ComplianceExportPermission])
@compliance_export_required
def export_compliances(request, export_format, item_type=None, item_id=None):
    """Export compliances based on format and optional filters"""
    try:
        # Get user ID from request
        user_id = request.user.id if request.user.is_authenticated else 1  # Default to system user
        
        # Create export task
        export_task = ExportTask.objects.create(
            export_data={
                'file_type': export_format,
                'user_id': str(user_id),
                'item_type': item_type,
                'item_id': item_id
            },
            file_type=export_format,
            user_id=str(user_id),
            status='pending'
        )
        
        # Get user email for notification
        try:
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            user_email, user_name = notification_service.get_user_email_by_id(user_id)
        except Exception as e:
            print(f"Error getting user email: {str(e)}")
            user_email = None
            user_name = None
        
        # Process the export
        try:
            # Fetch compliance data based on filters
            compliances_data = []
            
            if item_type == 'framework' and item_id:
                # Export all compliances for a specific framework
                compliances = Compliance.objects.filter(
                    SubPolicy__PolicyId__FrameworkId=item_id
                ).select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
            elif item_type == 'policy' and item_id:
                # Export all compliances for a specific policy
                compliances = Compliance.objects.filter(
                    SubPolicy__PolicyId=item_id
                ).select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
            elif item_type == 'subpolicy' and item_id:
                # Export all compliances for a specific subpolicy
                compliances = Compliance.objects.filter(
                    SubPolicy_id=item_id
                ).select_related('SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId')
            else:
                # Export all compliances
                compliances = Compliance.objects.all().select_related(
                    'SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId'
                )
            
            # Format compliance data for export
            for compliance in compliances:
                compliances_data.append({
                    'Compliance ID': compliance.ComplianceId,
                    'Description': compliance.ComplianceItemDescription or '',
                    'Status': compliance.Status or '',
                    'Criticality': compliance.Criticality or '',
                    'Maturity Level': compliance.MaturityLevel or '',
                    'Type': compliance.ComplianceType or '',
                    'Implementation': compliance.ManualAutomatic or '',
                    'Created By': compliance.CreatedByName or '',
                    'Created Date': compliance.CreatedByDate.strftime('%Y-%m-%d') if compliance.CreatedByDate else '',
                    'Version': compliance.ComplianceVersion or '',
                    'Identifier': compliance.Identifier or '',
                    'Active/Inactive': compliance.ActiveInactive or '',
                    'Is Risk': 'Yes' if compliance.IsRisk else 'No',
                    'SubPolicy': compliance.SubPolicy.SubPolicyName if compliance.SubPolicy else '',
                    'Policy': compliance.SubPolicy.PolicyId.PolicyName if compliance.SubPolicy and compliance.SubPolicy.PolicyId else '',
                    'Framework': compliance.SubPolicy.PolicyId.FrameworkId.FrameworkName if compliance.SubPolicy and compliance.SubPolicy.PolicyId and compliance.SubPolicy.PolicyId.FrameworkId else ''
                })
            
            # Use the export_data function from export_service1
            from ...routes.Global.s3_fucntions import export_data
            result = export_data(
                data=compliances_data,
                file_format=export_format,
                user_id=str(user_id),
                options={'item_type': item_type, 'item_id': item_id},
                export_id=export_task.id
            )
            
            # Task is already updated by export_data function
            # Just refresh the task to get updated values
            export_task.refresh_from_db()
            
            # Send completion notification if we have user email
            if user_email:
                try:
                    from ...routes.Global.notification_service import NotificationService
                    notification_service = NotificationService()
                    notification_result = notification_service.send_export_completion_notification(
                        user_id=user_id,
                        export_details={
                            'id': export_task.id,
                            'file_name': export_task.file_name,
                            'file_type': export_task.file_type,
                            's3_url': export_task.s3_url,
                            'completed_at': export_task.completed_at.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    )
                    print(f"Export completion notification result: {notification_result}")
                except Exception as e:
                    print(f"Error sending export completion notification: {str(e)}")
            
        except Exception as e:
            # Update task with error
            export_task.status = 'failed'
            export_task.error = str(e)
            export_task.save()
            raise
        
        return Response({
            'success': True,
            'message': 'Export completed successfully',
            'task_id': export_task.id,
            'download_url': export_task.s3_url
        })
        
    except Exception as e:
        print(f"Error in export_compliances: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






@api_view(['POST'])
@csrf_exempt
@authentication_classes([])
@permission_classes([ComplianceExportPermission])
def export_compliances_post(request):
    """Export compliances via POST request with data (similar to incident export)"""
    try:
        print(f"Export request received: {request.data}")
        
        # Get user ID from request
        user_id = request.user.id if request.user.is_authenticated else 1  # Default to system user
        
        # Get request data
        data = request.data.get('data', '[]')
        file_format = request.data.get('file_format', 'xlsx')
        options = request.data.get('options', '{}')
        
        print(f"Export parameters: user_id={user_id}, file_format={file_format}")
        
        # Parse data and options
        try:
            compliances_data = json.loads(data) if isinstance(data, str) else data
            export_options = json.loads(options) if isinstance(options, str) else options
        except json.JSONDecodeError as e:
            return Response({
                'success': False,
                'message': f'Invalid JSON data: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create export task
        export_task = ExportTask.objects.create(
            export_data={
                'file_type': file_format,
                'user_id': str(user_id),
                'data': compliances_data,
                'options': export_options
            },
            file_type=file_format,
            user_id=str(user_id),
            status='pending'
        )
        
        # Get user email for notification
        try:
            from ...routes.Global.notification_service import NotificationService
            notification_service = NotificationService()
            user_email = notification_service.get_user_email(user_id)
            user_name = notification_service.get_user_name(user_id)
        except Exception as e:
            print(f"Error getting user email: {str(e)}")
            # Fallback: try to get user info directly from database
            try:
                from ...models import Users
                user = Users.objects.get(UserId=user_id)
                user_email = user.Email if hasattr(user, 'Email') else None
                user_name = user.UserName if hasattr(user, 'UserName') else None
            except Exception as db_error:
                print(f"Error getting user from database: {str(db_error)}")
                user_email = None
                user_name = None
        
        # Process the export
        try:
            # Use the export_data function from export_service1
            from ...routes.Global.s3_fucntions import export_data
            result = export_data(
                data=compliances_data,
                file_format=file_format,
                user_id=str(user_id),
                options=export_options
            )
            
            # Task is already updated by export_data function
            # Just refresh the task to get updated values
            export_task.refresh_from_db()
            
            # Send completion notification if we have user email
            if user_email:
                try:
                    from ...routes.Global.notification_service import NotificationService
                    notification_service = NotificationService()
                    notification_result = notification_service.send_export_completion_notification(
                        user_id=user_id,
                        export_details={
                            'id': export_task.id,
                            'file_name': export_task.file_name,
                            'file_type': export_task.file_type,
                            's3_url': export_task.s3_url,
                            'completed_at': export_task.completed_at.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    )
                    print(f"Export completion notification result: {notification_result}")
                except Exception as e:
                    print(f"Error sending export completion notification: {str(e)}")
            
        except Exception as e:
            # Update task with error
            export_task.status = 'failed'
            export_task.error = str(e)
            export_task.save()
            raise
        
        return Response({
            'success': True,
            'message': 'Export completed successfully',
            'task_id': export_task.id,
            'file_url': export_task.s3_url,
            'file_name': export_task.file_name
        })
        
    except Exception as e:
        print(f"Error in export_compliances_post: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_all_compliances_for_audit_management(request):
    """
    Get all compliances with audit information for audit management view
    Automatically applies framework filter from session if one is selected
    """
    try:
        from ...routes.Policy.framework_filter_helper import get_active_framework_filter
        
        print("DEBUG: get_all_compliances_for_audit_management was called")
        
        # Get framework filter from session
        framework_filter = get_active_framework_filter(request)
        
        # Build SQL query with optional framework filter
        base_query = """
            SELECT 
                c.ComplianceId,
                c.ComplianceItemDescription,
                c.Criticality,
                c.Identifier,
                c.RiskCategory,
                c.RiskBusinessImpact,
                f.FrameworkName,
                p.PolicyName,
                sp.SubPolicyName,
                c.Status,
                c.ActiveInactive,
                c.CreatedDate,
                c.UpdatedDate
            FROM 
                compliance c
            LEFT JOIN 
                subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
            LEFT JOIN 
                policies p ON sp.PolicyId = p.PolicyId
            LEFT JOIN 
                frameworks f ON p.FrameworkId = f.FrameworkId
        """
        
        # Add WHERE clause if framework filter is active (using parameterized query)
        query_params = []
        if framework_filter:
            base_query += " WHERE f.FrameworkId = %s"
            query_params.append(framework_filter)
            print(f"DEBUG: Applying framework filter: {framework_filter}")
        
        base_query += """
            ORDER BY 
                f.FrameworkName, p.PolicyName, sp.SubPolicyName, c.ComplianceId
        """
        
        # Get all compliances with framework, policy, and subpolicy information
        with connection.cursor() as cursor:
            if query_params:
                cursor.execute(base_query, query_params)
            else:
                cursor.execute(base_query)
            
            columns = [col[0] for col in cursor.description]
            compliances = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            #print(f"DEBUG: Fetched {len(compliances)} compliance records")
            
            # Debug: Extract unique categories and business units
            unique_categories = set()
            unique_business_units = set()
            
            for compliance in compliances:
                if compliance.get('RiskCategory'):
                    unique_categories.add(compliance['RiskCategory'])
                if compliance.get('RiskBusinessImpact'):
                    unique_business_units.add(compliance['RiskBusinessImpact'])
            
            #print(f"DEBUG: Found {len(unique_categories)} unique categories: {sorted(unique_categories)}")
            #print(f"DEBUG: Found {len(unique_business_units)} unique business units: {sorted(list(unique_business_units)[:10])}...")  # Show first 10
        
        # Format dates
        for compliance in compliances:
            if compliance.get('CreatedDate'):
                compliance['CreatedDate'] = compliance['CreatedDate'].strftime('%Y-%m-%d')
            if compliance.get('UpdatedDate'):
                compliance['UpdatedDate'] = compliance['UpdatedDate'].strftime('%Y-%m-%d')
        
        return Response({
            'success': True,
            'compliances': compliances,
            'count': len(compliances)
        })
        
    except Exception as e:
        print(f"ERROR in get_all_compliances_for_audit_management: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error fetching compliances: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_compliance_categories_and_business_units(request):
    """
    Get unique categories and business units from compliance table
    """
    try:
        print("DEBUG: get_compliance_categories_and_business_units was called")
        
        with connection.cursor() as cursor:
            # Get unique categories
            cursor.execute("""
                SELECT DISTINCT RiskCategory as category
                FROM compliance 
                WHERE RiskCategory IS NOT NULL AND RiskCategory != ''
                ORDER BY RiskCategory
            """)
            categories = [row[0] for row in cursor.fetchall()]
            
            # Get unique business units
            cursor.execute("""
                SELECT DISTINCT RiskBusinessImpact as business_unit
                FROM compliance 
                WHERE RiskBusinessImpact IS NOT NULL AND RiskBusinessImpact != ''
                ORDER BY RiskBusinessImpact
            """)
            business_units = [row[0] for row in cursor.fetchall()]
            
            #print(f"DEBUG: Found {len(categories)} unique categories: {categories}")
            #print(f"DEBUG: Found {len(business_units)} unique business units")
        
        return Response({
            'success': True,
            'categories': categories,
            'business_units': business_units,
            'categories_count': len(categories),
            'business_units_count': len(business_units)
        })
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_compliances_for_audit_management_public(request):
    """
    Public version of all compliances for audit management with audit details
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.ComplianceId,
                    c.ComplianceItemDescription,
                    c.Criticality,
                    c.Identifier,
                    f.FrameworkName,
                    p.PolicyName,
                    sp.SubPolicyName,
                    c.Status,
                    c.ActiveInactive,
                    -- Business Units and Categories
                    c.BusinessUnitsCovered,
                    c.RiskCategory,
                    -- Audit information
                    af.AuditFindingsId,
                    af.AuditId,
                    af.Check as CompletionStatus,
                    af.CheckedDate as CompletionDate,
                    af.UserId as CompliancePerform,
                    -- Additional audit details
                    a.Title as AuditTitle,
                    a.Scope as AuditDescription,
                    -- User information
                    assignee.UserName as AssigneeName,
                    auditor.UserName as AuditorName,
                    reviewer.UserName as ReviewerName
                FROM 
                    compliance c
                LEFT JOIN 
                    subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                LEFT JOIN 
                    policies p ON sp.PolicyId = p.PolicyId
                LEFT JOIN 
                    frameworks f ON p.FrameworkId = f.FrameworkId
                LEFT JOIN 
                    audit_findings af ON c.ComplianceId = af.ComplianceId
                LEFT JOIN 
                    audit a ON af.AuditId = a.AuditId
                LEFT JOIN 
                    users assignee ON a.assignee = assignee.UserId
                LEFT JOIN 
                    users auditor ON a.auditor = auditor.UserId
                LEFT JOIN 
                    users reviewer ON a.reviewer = reviewer.UserId
                ORDER BY 
                    f.FrameworkName, p.PolicyName, sp.SubPolicyName, c.ComplianceId
            """)
            columns = [col[0] for col in cursor.description]
            compliances = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Process the data to handle multiple audit findings per compliance
        processed_compliances = []
        compliance_map = {}
        
        for compliance in compliances:
            compliance_id = compliance['ComplianceId']
            
            if compliance_id not in compliance_map:
                # First occurrence of this compliance
                base_compliance = {
                    'ComplianceId': compliance['ComplianceId'],
                    'ComplianceItemDescription': compliance['ComplianceItemDescription'],
                    'Criticality': compliance['Criticality'],
                    'Identifier': compliance['Identifier'],
                    'FrameworkName': compliance['FrameworkName'],
                    'PolicyName': compliance['PolicyName'],
                    'SubPolicyName': compliance['SubPolicyName'],
                    'Status': compliance['Status'],
                    'ActiveInactive': compliance['ActiveInactive'],
                    'BusinessUnitsCovered': compliance['BusinessUnitsCovered'] or 'N/A',
                    'RiskCategory': compliance['RiskCategory'] or 'N/A',
                    'AuditFindings': []
                }
                compliance_map[compliance_id] = base_compliance
                processed_compliances.append(base_compliance)
            
            # Add audit finding if it exists
            if compliance['AuditFindingsId']:
                audit_finding = {
                    'AuditFindingsId': compliance['AuditFindingsId'],
                    'AuditId': compliance['AuditId'],
                    'AuditTitle': compliance['AuditTitle'],
                    'AuditDescription': compliance['AuditDescription'],
                    'CompletionStatus': compliance['CompletionStatus'],
                    'CompletionDate': compliance['CompletionDate'],
                    'CompliancePerform': compliance['CompliancePerform'],
                    'ComplianceApprove': compliance['ReviewerName'] or compliance['AuditorName'] or 'N/A'
                }
                compliance_map[compliance_id]['AuditFindings'].append(audit_finding)

        return Response({
            'success': True,
            'compliances': processed_compliances,
            'count': len(processed_compliances)
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_categories_for_audit_management(request):
    """
    Get all categories for audit management filters
    """
    try:
        from ...models import CategoryBusinessUnit
        from django.db import connection
        
        # First, let's check if we have any data in the table
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM categoryunit")
            count = cursor.fetchone()[0]
            print(f"Total records in categoryunit table: {count}")
            
            if count == 0:
                # If no data, initialize default categories
                print("No data found, initializing default categories...")
                initialize_default_categories_data()
        
        # Get all unique categories from the RiskCategory source
        categories = CategoryBusinessUnit.objects.filter(
            source='RiskCategory'
        ).values_list('value', flat=True).distinct().order_by('value')
        
        # If still no categories, try alternative sources
        if not categories:
            categories = CategoryBusinessUnit.objects.filter(
                source__icontains='risk'
            ).values_list('value', flat=True).distinct().order_by('value')
        
        # If still no data, return some default categories
        if not categories:
            categories = [
                'People Risk',
                'Process Risk', 
                'Technology Risk',
                'External Risk',
                'Information Risk',
                'Physical Risk',
                'Systems Risk',
                'Vendor Risk',
                'Regulatory Risk',
                'Fraud Risk'
            ]
        
        print(f"Returning {len(categories)} categories: {list(categories)}")
        
        return Response({
            'success': True,
            'categories': list(categories)
        })
    except Exception as e:
        print(f"Error in get_categories_for_audit_management: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_business_units_for_audit_management(request):
    """
    Get all business units for audit management filters
    """
    try:
        from ...models import CategoryBusinessUnit
        from django.db import connection
        
        # First, let's check if we have any data in the table
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM categoryunit")
            count = cursor.fetchone()[0]
            print(f"Total records in categoryunit table: {count}")
            
            if count == 0:
                # If no data, initialize default categories
                print("No data found, initializing default categories...")
                initialize_default_categories_data()
        
        # Get all unique business units from the BusinessUnitsCovered source
        business_units = CategoryBusinessUnit.objects.filter(
            source='BusinessUnitsCovered'
        ).values_list('value', flat=True).distinct().order_by('value')
        
        # If still no business units, try alternative sources
        if not business_units:
            business_units = CategoryBusinessUnit.objects.filter(
                source__icontains='business'
            ).values_list('value', flat=True).distinct().order_by('value')
        
        # If still no data, return some default business units
        if not business_units:
            business_units = [
                'Sales & Marketing',
                'Finance & Accounting',
                'Human Resources',
                'Information Technology',
                'Operations',
                'Legal & Compliance',
                'Customer Service',
                'Research & Development',
                'Procurement',
                'Risk Management'
            ]
        
        print(f"Returning {len(business_units)} business units: {list(business_units)}")
        
        return Response({
            'success': True,
            'business_units': list(business_units)
        })
    except Exception as e:
        print(f"Error in get_business_units_for_audit_management: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def initialize_default_categories_data():
    """
    Initialize default categories and business units in the database
    """
    try:
        from ...models import CategoryBusinessUnit
        
        # Default values for each source
        default_values = {
            'BusinessUnitsCovered': [
                'Sales & Marketing',
                'Finance & Accounting',
                'Human Resources',
                'Information Technology',
                'Operations',
                'Legal & Compliance',
                'Customer Service',
                'Research & Development',
                'Procurement',
                'Risk Management'
            ],
            'RiskCategory': [
                'People Risk',
                'Process Risk',
                'Technology Risk',
                'External Risk',
                'Information Risk',
                'Physical Risk',
                'Systems Risk',
                'Vendor Risk',
                'Regulatory Risk',
                'Fraud Risk'
            ]
        }

        added_count = 0
        for source, values in default_values.items():
            for value in values:
                # Check if the value already exists
                existing = CategoryBusinessUnit.objects.filter(source=source, value=value).first()
                if not existing:
                    CategoryBusinessUnit.objects.create(source=source, value=value)
                    added_count += 1
                    print(f"Added: {source} - {value}")

        print(f"Initialized {added_count} default categories and business units")
        return added_count
    except Exception as e:
        print(f"Error initializing default categories: {str(e)}")
        return 0

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_categories_and_business_units(request):
    """
    Debug endpoint to check what's in the categoryunit table
    """
    try:
        from ...models import CategoryBusinessUnit
        from django.db import connection
        
        # Get all data from the table
        all_data = CategoryBusinessUnit.objects.all().values('id', 'source', 'value')
        
        # Get distinct sources
        sources = CategoryBusinessUnit.objects.values_list('source', flat=True).distinct()
        
        # Get counts by source
        source_counts = {}
        for source in sources:
            count = CategoryBusinessUnit.objects.filter(source=source).count()
            source_counts[source] = count
        
        return Response({
            'success': True,
            'all_data': list(all_data),
            'sources': list(sources),
            'source_counts': source_counts,
            'total_count': len(all_data)
        })
    except Exception as e:
        print(f"Error in debug endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def test_compliance_export(request):
    """Test endpoint to verify compliance export routing"""
    return Response({
        'success': True,
        'message': 'Compliance export endpoint is working',
        'method': request.method,
        'data': request.data if request.method == 'POST' else None
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_frameworks_public(request):
    """
    Fetch all frameworks for public access (no permission required)
    """
    try:
        print("DEBUG: get_frameworks_public was called")
        # Get all frameworks (remove ActiveInactive filter for now to see all data)
        frameworks = Framework.objects.all()  # type: ignore
        print(f"Found {frameworks.count()} frameworks in total")
        
        serializer = FrameworkSerializer(frameworks, many=True)
        serialized_data = serializer.data
        
        # Format the response to match frontend expectations
        formatted_frameworks = []
        for fw_data in serialized_data:
            formatted_fw = {
                'FrameworkId': fw_data.get('FrameworkId'),
                'FrameworkName': fw_data.get('FrameworkName'),
                'Category': fw_data.get('Category', ''),
                'ActiveInactive': fw_data.get('ActiveInactive', ''),
                'FrameworkDescription': fw_data.get('FrameworkDescription', ''),
            }
            formatted_frameworks.append(formatted_fw)
        
        response_data = {
            'success': True, 
            'frameworks': formatted_frameworks,
            'count': len(formatted_frameworks)
        }
        
        #print(f"DEBUG: get_frameworks_public returning {len(formatted_frameworks)} frameworks")
        return Response(response_data)
        
    except Exception as e:
        print(f"Error in get_frameworks_public: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error fetching frameworks: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_iso_framework_compliance_status(request):
    """
    Get compliance status overview for ISO frameworks (default view)
    """
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.ComplianceId,
                    c.ComplianceItemDescription,
                    c.Criticality,
                    f.FrameworkName,
                    p.PolicyName,
                    sp.SubPolicyName,
                    c.Status,
                    -- Audit information
                    af.AuditFindingsId,
                    af.Check as CompletionStatus
                FROM 
                    compliance c
                LEFT JOIN 
                    subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                LEFT JOIN 
                    policies p ON sp.PolicyId = p.PolicyId
                LEFT JOIN 
                    frameworks f ON p.FrameworkId = f.FrameworkId
                LEFT JOIN 
                    audit_findings af ON c.ComplianceId = af.ComplianceId
                WHERE 
                    f.FrameworkName LIKE '%ISO%' OR f.FrameworkName LIKE '%iso%'
                ORDER BY 
                    f.FrameworkName, p.PolicyName, sp.SubPolicyName, c.ComplianceId
            """)
            columns = [col[0] for col in cursor.description]
            compliances = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Process the data to count statuses
        status_counts = {
            'Fully Compliant': 0,
            'Partially Compliant': 0,
            'Non Compliant': 0,
            'Not Audited': 0
        }
        
        processed_compliances = []
        compliance_map = {}
        
        for compliance in compliances:
            compliance_id = compliance['ComplianceId']
            
            if compliance_id not in compliance_map:
                # First occurrence of this compliance
                base_compliance = {
                    'ComplianceId': compliance['ComplianceId'],
                    'ComplianceItemDescription': compliance['ComplianceItemDescription'],
                    'Criticality': compliance['Criticality'],
                    'FrameworkName': compliance['FrameworkName'],
                    'PolicyName': compliance['PolicyName'],
                    'SubPolicyName': compliance['SubPolicyName'],
                    'Status': compliance['Status'],
                    'AuditFindings': []
                }
                compliance_map[compliance_id] = base_compliance
                processed_compliances.append(base_compliance)
            
            # Add audit finding if it exists
            if compliance['AuditFindingsId']:
                audit_finding = {
                    'AuditFindingsId': compliance['AuditFindingsId'],
                    'CompletionStatus': compliance['CompletionStatus']
                }
                compliance_map[compliance_id]['AuditFindings'].append(audit_finding)

        # Count statuses
        for compliance in processed_compliances:
            if compliance['AuditFindings'] and len(compliance['AuditFindings']) > 0:
                # Check each audit finding
                for finding in compliance['AuditFindings']:
                    status = finding['CompletionStatus']
                    if status == '2' or str(status).lower() == 'fully compliant':
                        status_counts['Fully Compliant'] += 1
                    elif status == '1' or str(status).lower() == 'partially compliant':
                        status_counts['Partially Compliant'] += 1
                    elif status == '3' or str(status).lower() == 'non compliant':
                        status_counts['Non Compliant'] += 1
                    else:
                        status_counts['Not Audited'] += 1
            else:
                # No audit findings - count as not audited
                status_counts['Not Audited'] += 1

        total = sum(status_counts.values())
        status_percentages = {
            status: round((count / total * 100), 1) if total > 0 else 0
            for status, count in status_counts.items()
        }
        
        return Response({
            'success': True,
            'data': {
                'counts': status_counts,
                'percentages': status_percentages,
                'total': total,
                'framework_type': 'ISO'
            }
        })
        
    except Exception as e:
        print(f"Error in get_iso_framework_compliance_status: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def get_policy_compliance_status(request):
    """
    Get compliance status overview for a specific policy
    """
    try:
        from django.db import connection
        
        # Get policy_id from query parameters
        policy_id = request.query_params.get('policy_id')
        
        if not policy_id:
            return Response({
                'success': False,
                'message': 'Policy ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.ComplianceId,
                    c.ComplianceItemDescription,
                    c.Criticality,
                    f.FrameworkName,
                    p.PolicyName,
                    p.PolicyId,
                    sp.SubPolicyName,
                    c.Status,
                    -- Audit information
                    af.AuditFindingsId,
                    af.Check as CompletionStatus
                FROM 
                    compliance c
                LEFT JOIN 
                    subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                LEFT JOIN 
                    policies p ON sp.PolicyId = p.PolicyId
                LEFT JOIN 
                    frameworks f ON p.FrameworkId = f.FrameworkId
                LEFT JOIN 
                    audit_findings af ON c.ComplianceId = af.ComplianceId
                WHERE 
                    p.PolicyId = %s
                ORDER BY 
                    sp.SubPolicyName, c.ComplianceId
            """, [policy_id])
            columns = [col[0] for col in cursor.description]
            compliances = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Process the data to count statuses
        status_counts = {
            'Fully Compliant': 0,
            'Partially Compliant': 0,
            'Non Compliant': 0,
            'Not Audited': 0
        }
        
        processed_compliances = []
        compliance_map = {}
        
        for compliance in compliances:
            compliance_id = compliance['ComplianceId']
            
            if compliance_id not in compliance_map:
                # First occurrence of this compliance
                base_compliance = {
                    'ComplianceId': compliance['ComplianceId'],
                    'ComplianceItemDescription': compliance['ComplianceItemDescription'],
                    'Criticality': compliance['Criticality'],
                    'FrameworkName': compliance['FrameworkName'],
                    'PolicyName': compliance['PolicyName'],
                    'PolicyId': compliance['PolicyId'],
                    'SubPolicyName': compliance['SubPolicyName'],
                    'Status': compliance['Status'],
                    'AuditFindings': []
                }
                compliance_map[compliance_id] = base_compliance
                processed_compliances.append(base_compliance)
            
            # Add audit finding if it exists
            if compliance['AuditFindingsId']:
                audit_finding = {
                    'AuditFindingsId': compliance['AuditFindingsId'],
                    'CompletionStatus': compliance['CompletionStatus']
                }
                compliance_map[compliance_id]['AuditFindings'].append(audit_finding)

        # Count statuses
        for compliance in processed_compliances:
            if compliance['AuditFindings'] and len(compliance['AuditFindings']) > 0:
                # Check each audit finding
                for finding in compliance['AuditFindings']:
                    status = finding['CompletionStatus']
                    if status == '2' or str(status).lower() == 'fully compliant':
                        status_counts['Fully Compliant'] += 1
                    elif status == '1' or str(status).lower() == 'partially compliant':
                        status_counts['Partially Compliant'] += 1
                    elif status == '3' or str(status).lower() == 'non compliant':
                        status_counts['Non Compliant'] += 1
                    else:
                        status_counts['Not Audited'] += 1
            else:
                # No audit findings - count as not audited
                status_counts['Not Audited'] += 1

        total = sum(status_counts.values())
        status_percentages = {
            status: round((count / total * 100), 1) if total > 0 else 0
            for status, count in status_counts.items()
        }
        
        # Get policy details
        policy_name = processed_compliances[0]['PolicyName'] if processed_compliances else 'Unknown Policy'
        
        return Response({
            'success': True,
            'data': {
                'counts': status_counts,
                'percentages': status_percentages,
                'total': total,
                'policy_id': policy_id,
                'policy_name': policy_name
            }
        })
        
    except Exception as e:
        print(f"Error in get_policy_compliance_status: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@csrf_exempt
@permission_classes([ComplianceViewPermission])
@compliance_view_required
def export_audit_management_compliances(request, format):
    """Export compliances for audit management view using export_service1"""
    try:
        print(f"Audit management export request received: format={format}")
        
        # Get user ID from request
        user_id = request.user.id if request.user.is_authenticated else 1
        
        # Get all compliances for audit management (same as get_all_compliances_for_audit_management_public)
        compliances_data = []
        
        try:
            # Get all compliances with related data
            compliances = Compliance.objects.all().select_related(
                'SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId'
            ).prefetch_related('AuditFindings')
            
            for compliance in compliances:
                compliance_data = {
                    'ComplianceId': compliance.ComplianceId,
                    'ComplianceItemDescription': compliance.ComplianceItemDescription,
                    'Criticality': compliance.Criticality,
                    'FrameworkName': compliance.SubPolicy.PolicyId.FrameworkId.FrameworkName if compliance.SubPolicy and compliance.SubPolicy.PolicyId and compliance.SubPolicy.PolicyId.FrameworkId else 'N/A',
                    'PolicyName': compliance.SubPolicy.PolicyId.PolicyName if compliance.SubPolicy and compliance.SubPolicy.PolicyId else 'N/A',
                    'SubPolicyName': compliance.SubPolicy.SubPolicyName if compliance.SubPolicy else 'N/A',
                    'AuditFindings': []
                }
                
                # Add audit findings if they exist
                if hasattr(compliance, 'AuditFindings') and compliance.AuditFindings.exists():
                    for finding in compliance.AuditFindings.all():
                        finding_data = {
                            'AuditId': finding.AuditId,
                            'AuditFindingsId': finding.AuditFindingsId,
                            'CompletionStatus': finding.CompletionStatus,
                            'CompliancePerform': finding.CompliancePerform,
                            'ComplianceApprove': finding.ComplianceApprove,
                            'CompletionDate': finding.CompletionDate.isoformat() if finding.CompletionDate else None
                        }
                        compliance_data['AuditFindings'].append(finding_data)
                
                compliances_data.append(compliance_data)
            
            print(f"Processed {len(compliances_data)} compliances for audit management export")
            
        except Exception as e:
            print(f"Error fetching compliances: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error fetching compliances: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Use the export_data function from export_service1
        try:
            from ...routes.Global.s3_fucntions import export_data
            
            # Create file name with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"audit_management_compliances_{timestamp}.{format}"
            
            result = export_data(
                data=compliances_data,
                file_format=format,
                user_id=str(user_id),
                options={
                    'file_name': file_name,
                    'filters': {'view': 'audit_management'},
                    'columns': ['ComplianceId', 'ComplianceItemDescription', 'Criticality', 'FrameworkName', 'PolicyName', 'SubPolicyName', 'AuditFindings']
                }
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Export completed successfully',
                    'file_url': result['file_url'],
                    'file_name': result['file_name'],
                    'metadata': result['metadata']
                })
            else:
                return Response({
                    'success': False,
                    'message': result.get('error', 'Export failed')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            print(f"Error in export_data: {str(e)}")
            return Response({
                'success': False,
                'message': f'Export processing error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        print(f"Error in export_audit_management_compliances: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Import the export compliance functions
from .export_compliance import (
    export_compliance_management,
    get_export_status,
    list_export_history
)