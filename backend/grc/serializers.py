from rest_framework import serializers
from .models import Framework, Policy, SubPolicy, PolicyApproval, ComplianceApproval, ExportTask, Notification, S3File, PolicyCategory ,Entity
from datetime import date
from django.contrib.auth.models import User
from datetime import date

# Import all models
from .models import (
    Audit, Framework, Policy, GRCLog, Users, SubPolicy, Compliance, 
    AuditFinding, Incident, Risk, RiskInstance, Workflow, PolicyApproval, 
    ComplianceApproval, ExportTask, LastChecklistItemVerified, Notification, S3File, 
    PolicyCategory, RiskAssignment
)

# =============================================================================
# FRAMEWORK MODULE SERIALIZERS
# =============================================================================

class FrameworkSerializer(serializers.ModelSerializer):
    policies = serializers.SerializerMethodField()
    CreatedByName = serializers.CharField(required=False, allow_blank=True)
    Reviewer = serializers.CharField(required=False, allow_blank=True)
    
    def get_policies(self, obj):
        # Filter policies to only include Approved and Active ones
        policies = obj.policy_set.filter(Status='Approved', ActiveInactive='Active')
        return PolicySerializer(policies, many=True).data
    
    class Meta:
        model = Framework
        fields = [
            'FrameworkId', 'FrameworkName', 'CurrentVersion', 'FrameworkDescription',
            'EffectiveDate', 'CreatedByName', 'CreatedByDate', 'Category',
            'DocURL', 'Identifier', 'StartDate', 'EndDate', 'Status',
            'ActiveInactive', 'policies', 'Reviewer'
        ]


# =============================================================================
# POLICY MODULE SERIALIZERS
# =============================================================================



class PolicySerializer(serializers.ModelSerializer):
    FrameworkCategory = serializers.CharField(source='FrameworkId.Category', read_only=True)
    FrameworkName = serializers.CharField(source='FrameworkId.FrameworkName', read_only=True)
    subpolicies = serializers.SerializerMethodField()
    CreatedByName = serializers.CharField(required=False, allow_blank=True)
    Reviewer = serializers.CharField(required=False, allow_blank=True)
    Status = serializers.CharField(required=False, default='Under Review')
    ActiveInactive = serializers.CharField(required=False, default='Inactive')
    CoverageRate = serializers.FloatField(required=False, allow_null=True)

    def get_subpolicies(self, obj):
        # Get all subpolicies without filtering by status
        subpolicies = obj.subpolicy_set.all()
        return SubPolicySerializer(subpolicies, many=True).data

    class Meta:
        model = Policy
        fields = [
            'PolicyId', 'CurrentVersion', 'Status', 'PolicyName', 'PolicyDescription',
            'StartDate', 'EndDate', 'Department', 'CreatedByName', 'CreatedByDate',
            'Applicability', 'DocURL', 'Scope', 'Objective', 'Identifier',
            'PermanentTemporary', 'ActiveInactive', 'FrameworkId', 'Reviewer',
            'FrameworkCategory', 'FrameworkName', 'subpolicies', 'CoverageRate','PolicyType',
            'PolicyCategory', 'PolicySubCategory', 'Entities'
        ]


class PolicyApprovalSerializer(serializers.ModelSerializer):
    ApprovedDate = serializers.DateField(read_only=True)
    PolicyId = serializers.PrimaryKeyRelatedField(source='PolicyId.PolicyId', read_only=True)
    
    class Meta:
        model = PolicyApproval
        fields = [
            'ApprovalId', 'ExtractedData', 'UserId', 
            'ReviewerId', 'Version', 'ApprovedNot', 'ApprovedDate', 'PolicyId'
        ]


class ComplianceApprovalSerializer(serializers.ModelSerializer):
    ApprovedDate = serializers.DateField(read_only=True)
    PolicyId = serializers.PrimaryKeyRelatedField(source='PolicyId.PolicyId', read_only=True, allow_null=True)
    FrameworkId = serializers.SerializerMethodField()
    
    def get_FrameworkId(self, obj):
        """Safely get FrameworkId, handling None and missing relationships"""
        try:
            if obj.FrameworkId_id:
                # If FrameworkId relationship exists, return the ID
                return obj.FrameworkId_id
            return None
        except (AttributeError, TypeError):
            # If FrameworkId is None or doesn't exist, return None
            return None
    
    class Meta:
        model = ComplianceApproval
        fields = [
            'ApprovalId', 'Identifier', 'ExtractedData', 'UserId', 
            'ReviewerId', 'Version', 'ApprovedNot', 'ApprovedDate', 'PolicyId',
            'ApprovalDueDate', 'FrameworkId'
        ]


class PolicyAllocationSerializer(serializers.Serializer):
    framework = serializers.IntegerField(required=True, error_messages={'required': 'Framework is required', 'invalid': 'Framework must be a valid integer'})
    policy = serializers.IntegerField(required=False, allow_null=True)
    subpolicy = serializers.IntegerField(required=False, allow_null=True)
    assignee = serializers.IntegerField(required=True, error_messages={'required': 'Assignee is required', 'invalid': 'Assignee must be a valid user ID'})
    auditor = serializers.IntegerField(required=True, error_messages={'required': 'Auditor is required', 'invalid': 'Auditor must be a valid user ID'})
    reviewer = serializers.IntegerField(required=False, allow_null=True)
    duedate = serializers.DateField(required=True, error_messages={'required': 'Due date is required', 'invalid': 'Due date must be in YYYY-MM-DD format'})
    frequency = serializers.IntegerField(required=True, error_messages={'required': 'Frequency is required', 'invalid': 'Frequency must be a valid integer'})
    audit_type = serializers.CharField(max_length=1, required=True, error_messages={'required': 'Audit type is required', 'invalid': 'Audit type must be either Internal (I) or External (E)'})
   
    def validate_policy(self, value):
        # Convert empty string to null
        if value == '':
            return None
        return value
   
    def validate_subpolicy(self, value):
        # Convert empty string to null
        if value == '':
            return None
        return value
   
    def validate_reviewer(self, value):
        # Convert empty string to null
        if value == '':
            return None
        return value
 
    # Custom validation for due date
    def validate_duedate(self, value):
        if value < date.today():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value
   
    def validate_audit_type(self, value):
        # Convert 'Internal' to 'I' and 'External' to 'E'
        if value == 'Internal':
            return 'I'
        elif value == 'External':
            return 'E'
        # If already the single character, just return it
        elif value in ['I', 'E']:
            return value
        else:
            raise serializers.ValidationError("Invalid audit type. Must be 'Internal' or 'External'.")


class PolicyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyCategory
        fields = '__all__'  # Includes: Id, PolicyType, PolicyCategory, PolicySubCategory


# =============================================================================
# SUB-POLICY MODULE SERIALIZERS
# =============================================================================

class SubPolicySerializer(serializers.ModelSerializer):
    CreatedByName = serializers.CharField(required=False, allow_blank=True)
    Status = serializers.CharField(required=False, default='Under Review')
    PermanentTemporary = serializers.CharField(required=False, default='Permanent')

    def validate_SubPolicyName(self, value):
        """
        Validate that SubPolicyName is unique within the same policy
        """
        # Get the policy_id from the context or data
        policy_id = None
        if self.context and 'policy_id' in self.context:
            policy_id = self.context['policy_id']
        elif 'PolicyId' in self.initial_data:
            policy_id = self.initial_data['PolicyId']
        
        if policy_id:
            # Check if a subpolicy with the same name already exists in this policy
            from .models import SubPolicy
            if SubPolicy.objects.filter(PolicyId=policy_id, SubPolicyName=value).exists():
                raise serializers.ValidationError(
                    f"A subpolicy with the name '{value}' already exists in this policy. "
                    "Subpolicy names must be unique within a policy."
                )
        
        return value

    class Meta:
        model = SubPolicy
        fields = [
            'SubPolicyId', 'SubPolicyName', 'CreatedByName', 'CreatedByDate',
            'Identifier', 'Description', 'Status', 'PermanentTemporary',
            'Control', 'PolicyId'
        ]


# =============================================================================
# COMPLIANCE MODULE SERIALIZERS
# =============================================================================

class ComplianceSerializer(serializers.ModelSerializer):
    Impact = serializers.CharField(max_length=50, required=True)
    Probability = serializers.CharField(max_length=50, required=True)
    ComplianceTitle = serializers.CharField(max_length=145, required=True)
    ComplianceItemDescription = serializers.CharField(required=True)
    ComplianceType = serializers.CharField(max_length=100, required=True)
    Scope = serializers.CharField(required=True)
    Objective = serializers.CharField(required=True)
    Criticality = serializers.ChoiceField(choices=['High', 'Medium', 'Low'], required=True)
    MandatoryOptional = serializers.ChoiceField(choices=['Mandatory', 'Optional'], required=False)
    ManualAutomatic = serializers.ChoiceField(choices=['Manual', 'Automatic'], required=False)
    MaturityLevel = serializers.ChoiceField(
        choices=['Initial', 'Developing', 'Defined', 'Managed', 'Optimizing'],
        required=False
    )
    Status = serializers.CharField(default='Under Review')
    ActiveInactive = serializers.CharField(default='Active')
    ComplianceVersion = serializers.CharField(required=True)
    mitigation = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = Compliance
        fields = '__all__'

    def validate_ComplianceTitle(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        if len(value) > 145:
            raise serializers.ValidationError("Title cannot exceed 145 characters")
        return value

    def validate_ComplianceItemDescription(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long")
        return value

    def validate_Scope(self, value):
        if len(value) < 15:
            raise serializers.ValidationError("Scope must be at least 15 characters long")
        return value

    def validate_Objective(self, value):
        if len(value) < 15:
            raise serializers.ValidationError("Objective must be at least 15 characters long")
        return value

    def validate_Impact(self, value):
        try:
            impact = float(value)
            if not (0 <= impact <= 10):
                raise serializers.ValidationError("Impact must be between 0 and 10")
        except ValueError:
            raise serializers.ValidationError("Impact must be a number between 0 and 10")
        return str(impact)

    def validate_Probability(self, value):
        try:
            probability = float(value)
            if not (0 <= probability <= 10):
                raise serializers.ValidationError("Probability must be between 0 and 10")
        except ValueError:
            raise serializers.ValidationError("Probability must be a number between 0 and 10")
        return str(probability)

    def validate_mitigation(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("Mitigation must be a dictionary")
        # Ensure all values are strings and not empty
        cleaned = {}
        for key, step in value.items():
            if isinstance(step, str) and step.strip():
                cleaned[key] = step.strip()
        return cleaned


class ComplianceCreateSerializer(serializers.ModelSerializer):
    SubPolicyId = serializers.PrimaryKeyRelatedField(queryset=SubPolicy.objects.all())
    Identifier = serializers.CharField(max_length=50)
    IsRisk = serializers.BooleanField()
    Criticality = serializers.ChoiceField(choices=['High', 'Medium', 'Low'])
    ManualAutomatic = serializers.ChoiceField(choices=['Manual', 'Automatic'])
    
    # Change these to CharFields to match the model
    Impact = serializers.CharField(max_length=50)
    Probability = serializers.CharField(max_length=50)
    
    ActiveInactive = serializers.ChoiceField(choices=['Active', 'Inactive'], required=False)
    PermanentTemporary = serializers.ChoiceField(choices=['Permanent', 'Temporary'])
    Status = serializers.ChoiceField(choices=['Approved', 'Active', 'Schedule', 'Rejected', 'Under Review'], required=False)
    
    class Meta:
        model = Compliance
        fields = [
            'SubPolicyId', 'Identifier', 'ComplianceItemDescription', 'IsRisk',
            'PossibleDamage', 'mitigation', 'Criticality',
            'MandatoryOptional', 'ManualAutomatic', 'Impact',
            'Probability', 'ActiveInactive', 'PermanentTemporary',
            'Status'
        ]
    
    def create(self, validated_data):
        # Auto-generate ComplianceVersion
        subpolicy = validated_data['SubPolicyId']
        latest = Compliance.objects.filter(SubPolicyId=subpolicy).order_by('-ComplianceVersion').first()
        
        if latest:
            try:
                current_version = float(latest.ComplianceVersion)
                new_version = current_version + 0.1
                validated_data['ComplianceVersion'] = f"{new_version:.1f}"
            except (ValueError, TypeError):
                validated_data['ComplianceVersion'] = "1.0"
        else:
            validated_data['ComplianceVersion'] = "1.0"
        
        return super().create(validated_data)


class ComplianceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compliance
        fields = [
            'ComplianceId', 'SubPolicy', 'ComplianceItemDescription', 'IsRisk',
            'PossibleDamage', 'mitigation', 'Criticality', 'MandatoryOptional',
            'ManualAutomatic', 'Impact', 'Probability', 'MaturityLevel', 'ActiveInactive',
            'PermanentTemporary', 'ComplianceVersion', 'Status', 'Identifier', 
            'PreviousComplianceVersionId', 'CreatedByName', 'CreatedByDate',
            'PotentialRiskScenarios', 'RiskType', 'RiskCategory', 'RiskBusinessImpact',
            'ComplianceTitle', 'Scope', 'Objective', 'BusinessUnitsCovered', 'Applicability'
        ]


class LastChecklistItemVerifiedSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(source='FrameworkId.FrameworkName', read_only=True)
    
    class Meta:
        model = LastChecklistItemVerified
        fields = ['FrameworkId', 'ComplianceId', 'PolicyId', 'SubPolicyId', 'Date', 
                 'Time', 'User', 'Complied', 'Comments', 'count', 'framework_name']


# =============================================================================
# AUDIT MODULE SERIALIZERS
# =============================================================================

class AuditSerializer(serializers.ModelSerializer):
    # FrameworkId is a ForeignKey, so use PrimaryKeyRelatedField - OPTIONAL (can be None)
    FrameworkId = serializers.PrimaryKeyRelatedField(
        queryset=Framework.objects.all(),
        required=False,
        allow_null=True,
        help_text="Framework ID is optional - only add if framework is selected"
    )
    
    class Meta:
        model = Audit
        fields = ['AuditId', 'Assignee', 'Auditor', 'Reviewer', 'FrameworkId', 'PolicyId', 'DueDate', 'Frequency', 'AuditType', 'Status']


class AuditFindingSerializer(serializers.ModelSerializer):
    ComplianceDetails = serializers.SerializerMethodField()
    compliance_name = serializers.SerializerMethodField()
    compliance_mitigation = serializers.SerializerMethodField()
    comments = serializers.CharField(source='Comments', required=False)
    # FrameworkId is a ForeignKey, so use PrimaryKeyRelatedField - OPTIONAL (can be None)
    FrameworkId = serializers.PrimaryKeyRelatedField(
        queryset=Framework.objects.all(),
        required=False,
        allow_null=True,
        help_text="Framework ID is optional - only add if framework is selected"
    )

    class Meta:
        model = AuditFinding
        fields = '__all__'

    def get_ComplianceDetails(self, obj):
        if obj.ComplianceId:
            return {
                'description': obj.ComplianceId.ComplianceItemDescription,
                'mitigation': obj.ComplianceId.mitigation if hasattr(obj.ComplianceId, 'mitigation') else None,
            }
        return None

    def get_compliance_name(self, obj):
        return obj.ComplianceId.ComplianceItemDescription if obj.ComplianceId else "No description"

    def get_compliance_mitigation(self, obj):
        return obj.ComplianceId.mitigation if obj.ComplianceId and hasattr(obj.ComplianceId, 'mitigation') else None


# =============================================================================
# INCIDENT MODULE SERIALIZERS
# =============================================================================

class IncidentSerializer(serializers.ModelSerializer):
    has_risk_instance = serializers.SerializerMethodField()
    
    class Meta:
        model = Incident
        fields = '__all__'
    
    def get_has_risk_instance(self, obj):
        return RiskInstance.objects.filter(IncidentId=obj.IncidentId).exists()


# =============================================================================
# RISK MODULE SERIALIZERS
# =============================================================================

class RiskSerializer(serializers.ModelSerializer):
    # Handle multiplier fields - convert from 1-10 range to 0.1-1.0 range for storage
    RiskMultiplierX = serializers.FloatField(required=False, allow_null=True)
    RiskMultiplierY = serializers.FloatField(required=False, allow_null=True)
    # FrameworkId is an IntegerField, so use IntegerField - OPTIONAL (can be None)
    FrameworkId = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Framework ID is optional - only add if framework is selected"
    )
   
    class Meta:
        model = Risk
        fields = [
            'RiskId', 'ComplianceId', 'RiskTitle', 'Criticality', 'PossibleDamage',
            'Category', 'RiskType', 'BusinessImpact', 'RiskPriority', 'RiskDescription',
            'RiskLikelihood', 'RiskImpact', 'RiskExposureRating', 'RiskMultiplierX',
            'RiskMultiplierY', 'RiskMitigation', 'CreatedAt', 'FrameworkId'
        ]  # Explicitly list fields that exist in the model
   
    def to_internal_value(self, data):
        # Convert the QueryDict or dict to a mutable dict
        if hasattr(data, '_mutable'):
            mutable_data = data.copy()
        else:
            mutable_data = dict(data)
       
        # Convert multiplier fields from 1-10 range to 0.1-1.0 range for storage
        if 'RiskMultiplierX' in mutable_data and mutable_data['RiskMultiplierX'] is not None:
            try:
                multiplier_x = float(mutable_data['RiskMultiplierX'])
                # Handle values that are already in 0.1-1.0 range (from frontend)
                if 0.1 <= multiplier_x <= 1.0:
                    # Value is already in correct range, keep as is
                    mutable_data['RiskMultiplierX'] = multiplier_x
                elif 1 <= multiplier_x <= 10:
                    # Convert from 1-10 range to 0.1-1.0 range
                    mutable_data['RiskMultiplierX'] = multiplier_x / 10.0
                else:
                    raise serializers.ValidationError({
                        'RiskMultiplierX': 'Ensure this value is between 0.1 and 1.0 or between 1 and 10.'
                    })
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'RiskMultiplierX': 'Enter a valid number.'
                })
       
        if 'RiskMultiplierY' in mutable_data and mutable_data['RiskMultiplierY'] is not None:
            try:
                multiplier_y = float(mutable_data['RiskMultiplierY'])
                # Handle values that are already in 0.1-1.0 range (from frontend)
                if 0.1 <= multiplier_y <= 1.0:
                    # Value is already in correct range, keep as is
                    mutable_data['RiskMultiplierY'] = multiplier_y
                elif 1 <= multiplier_y <= 10:
                    # Convert from 1-10 range to 0.1-1.0 range
                    mutable_data['RiskMultiplierY'] = multiplier_y / 10.0
                else:
                    raise serializers.ValidationError({
                        'RiskMultiplierY': 'Ensure this value is between 0.1 and 1.0 or between 1 and 10.'
                    })
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'RiskMultiplierY': 'Enter a valid number.'
                })
        
        # Normalize integer-like fields: convert empty strings to None and cast numbers
        integer_fields = ['ComplianceId', 'RiskLikelihood', 'RiskImpact', 'FrameworkId']
        for field in integer_fields:
            if field in mutable_data:
                value = mutable_data[field]
                if value == '' or value is None:
                    mutable_data[field] = None
                else:
                    try:
                        # Only cast if it's not already an int
                        if not isinstance(value, int):
                            mutable_data[field] = int(value)
                    except (ValueError, TypeError):
                        # Leave as-is; DRF will handle invalid types later
                        pass
       
        try:
            result = super().to_internal_value(mutable_data)
            return result
        except Exception as e:
            print(f"RiskSerializer validation error: {e}")
            print(f"Data being validated: {mutable_data}")
            raise
 


class RiskInstanceSerializer(serializers.ModelSerializer):
    # Add this custom field to handle any format of RiskMitigation
    RiskMitigation = serializers.JSONField(required=False, allow_null=True)
    # Use SerializerMethodField for date fields to prevent utcoffset errors
    # This ensures dates are converted to strings before DRF tries to serialize them
    MitigationDueDate = serializers.SerializerMethodField()
    MitigationCompletedDate = serializers.SerializerMethodField()
    CreatedAt = serializers.SerializerMethodField()
    FirstResponseAt = serializers.SerializerMethodField()
    ModifiedMitigations = serializers.JSONField(required=False, allow_null=True)
    RiskFormDetails = serializers.JSONField(required=False, allow_null=True)
    # Handle MitigationStatus with proper choices validation
    MitigationStatus = serializers.ChoiceField(
        choices=RiskInstance.MITIGATION_STATUS_CHOICES,
        required=False,
        allow_null=True,
        default='Pending'
    )
    # Handle multiplier fields - convert from 1-10 range to 0.1-1.0 range for storage
    RiskMultiplierX = serializers.FloatField(required=False, allow_null=True)
    RiskMultiplierY = serializers.FloatField(required=False, allow_null=True)
    # FrameworkId is a ForeignKey, so use PrimaryKeyRelatedField - OPTIONAL (can be None)
    FrameworkId = serializers.PrimaryKeyRelatedField(
        queryset=Framework.objects.all(),
        required=False,
        allow_null=True,
        help_text="Framework ID is optional - only add if framework is selected"
    )
   
    class Meta:
        model = RiskInstance
        fields = '__all__'
   
    def to_internal_value(self, data):
        # Convert the QueryDict or dict to a mutable dict
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
        
        # Remove Date field if present as it's been replaced with CreatedAt
        if 'Date' in mutable_data:
            mutable_data.pop('Date')
        
        # Handle date fields for writes (SerializerMethodField is read-only, so we need to handle writes here)
        # These fields will be handled by the model's field definitions during create/update
        date_fields = ['MitigationDueDate', 'MitigationCompletedDate', 'CreatedAt']
        for field in date_fields:
            if field in mutable_data:
                # If empty string, set to None
                if mutable_data[field] == '':
                    mutable_data[field] = None
                # If it's already a date object, keep it
                elif hasattr(mutable_data[field], 'isoformat'):
                    pass  # Already a date object
                # If it's a string, try to parse it
                elif isinstance(mutable_data[field], str):
                    try:
                        from datetime import datetime
                        # Try parsing as date string
                        mutable_data[field] = datetime.strptime(mutable_data[field], '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        # If parsing fails, set to None
                        mutable_data[field] = None
        
        # Handle datetime fields for writes
        if 'FirstResponseAt' in mutable_data:
            if mutable_data['FirstResponseAt'] == '':
                mutable_data['FirstResponseAt'] = None
            elif isinstance(mutable_data['FirstResponseAt'], str):
                try:
                    from datetime import datetime
                    # Try parsing as datetime string
                    mutable_data['FirstResponseAt'] = datetime.strptime(mutable_data['FirstResponseAt'], '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    mutable_data['FirstResponseAt'] = None
        
        # Set default values for required fields
        if not mutable_data.get('RiskOwner'):
            mutable_data['RiskOwner'] = 'System Owner'
        
        if not mutable_data.get('RiskStatus'):
            mutable_data['RiskStatus'] = 'Not Assigned'
        
        # Handle MitigationStatus - ensure it's a valid choice
        if 'MitigationStatus' in mutable_data:
            mitigation_status = mutable_data['MitigationStatus']
            valid_choices = [choice[0] for choice in RiskInstance.MITIGATION_STATUS_CHOICES]
            if mitigation_status and mitigation_status not in valid_choices:
                # Default to 'Pending' if invalid status provided
                mutable_data['MitigationStatus'] = 'Pending'
        else:
            # Set default if not provided
            mutable_data['MitigationStatus'] = 'Pending'
        
        # Handle integer fields that might be sent as strings
        integer_fields = ['ReportedBy', 'UserId', 'RiskId', 'IncidentId', 'ComplianceId', 'ReviewerId', 'ReviewerCount', 'RecurrenceCount']
        for field in integer_fields:
            if field in mutable_data and mutable_data[field] is not None:
                try:
                    if isinstance(mutable_data[field], str) and mutable_data[field].strip():
                        mutable_data[field] = int(mutable_data[field])
                    elif mutable_data[field] == '':
                        mutable_data[field] = None
                except (ValueError, TypeError):
                    mutable_data[field] = None
        
        # Handle RiskMitigation if it's present but empty
        if 'RiskMitigation' in mutable_data and not mutable_data['RiskMitigation']:
            mutable_data['RiskMitigation'] = {}
            
        # Handle ModifiedMitigations if it's present but empty
        if 'ModifiedMitigations' in mutable_data and not mutable_data['ModifiedMitigations']:
            mutable_data['ModifiedMitigations'] = None
            
        # Handle RiskFormDetails if it's present but empty
        if 'RiskFormDetails' in mutable_data and not mutable_data['RiskFormDetails']:
            mutable_data['RiskFormDetails'] = None
       
        # Handle multiplier fields - convert from 1-10 range to 0.1-1.0 range for storage
        if 'RiskMultiplierX' in mutable_data and mutable_data['RiskMultiplierX'] is not None:
            try:
                multiplier_x = float(mutable_data['RiskMultiplierX'])
                # Handle values that are already in 0.1-1.0 range (from frontend)
                if 0.1 <= multiplier_x <= 1.0:
                    # Value is already in correct range, keep as is
                    mutable_data['RiskMultiplierX'] = multiplier_x
                elif 1 <= multiplier_x <= 10:
                    # Convert from 1-10 range to 0.1-1.0 range
                    mutable_data['RiskMultiplierX'] = multiplier_x / 10.0
                else:
                    raise serializers.ValidationError({
                        'RiskMultiplierX': 'Ensure this value is between 0.1 and 1.0 or between 1 and 10.'
                    })
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'RiskMultiplierX': 'Enter a valid number.'
                })
       
        if 'RiskMultiplierY' in mutable_data and mutable_data['RiskMultiplierY'] is not None:
            try:
                multiplier_y = float(mutable_data['RiskMultiplierY'])
                # Handle values that are already in 0.1-1.0 range (from frontend)
                if 0.1 <= multiplier_y <= 1.0:
                    # Value is already in correct range, keep as is
                    mutable_data['RiskMultiplierY'] = multiplier_y
                elif 1 <= multiplier_y <= 10:
                    # Convert from 1-10 range to 0.1-1.0 range
                    mutable_data['RiskMultiplierY'] = multiplier_y / 10.0
                else:
                    raise serializers.ValidationError({
                        'RiskMultiplierY': 'Ensure this value is between 0.1 and 1.0 or between 1 and 10.'
                    })
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'RiskMultiplierY': 'Enter a valid number.'
                })
       
        try:
            result = super().to_internal_value(mutable_data)
            return result
        except Exception as e:
            print(f"Serializer validation error: {e}")
            print(f"Data being validated: {mutable_data}")
            raise
    
    def create(self, validated_data):
        # Clean up the data before creating the instance
        for field in ['RiskMitigation', 'ModifiedMitigations', 'RiskFormDetails']:
            if field in validated_data and validated_data[field] == '':
                if field == 'RiskMitigation':
                    validated_data[field] = {}
                else:
                    validated_data[field] = None
        
        # Create the instance with cleaned data
        return RiskInstance.objects.create(**validated_data)
        
    def get_MitigationDueDate(self, obj):
        """Convert MitigationDueDate to string to avoid utcoffset error"""
        if obj.MitigationDueDate:
            try:
                if hasattr(obj.MitigationDueDate, 'isoformat'):
                    return obj.MitigationDueDate.isoformat()
                elif hasattr(obj.MitigationDueDate, 'strftime'):
                    return obj.MitigationDueDate.strftime('%Y-%m-%d')
                return str(obj.MitigationDueDate)
            except Exception as e:
                print(f"Warning: Error converting MitigationDueDate: {e}")
                return str(obj.MitigationDueDate) if obj.MitigationDueDate else None
        return None
    
    def get_MitigationCompletedDate(self, obj):
        """Convert MitigationCompletedDate to string to avoid utcoffset error"""
        if obj.MitigationCompletedDate:
            try:
                if hasattr(obj.MitigationCompletedDate, 'isoformat'):
                    return obj.MitigationCompletedDate.isoformat()
                elif hasattr(obj.MitigationCompletedDate, 'strftime'):
                    return obj.MitigationCompletedDate.strftime('%Y-%m-%d')
                return str(obj.MitigationCompletedDate)
            except Exception as e:
                print(f"Warning: Error converting MitigationCompletedDate: {e}")
                return str(obj.MitigationCompletedDate) if obj.MitigationCompletedDate else None
        return None
    
    def get_CreatedAt(self, obj):
        """Convert CreatedAt to string to avoid utcoffset error"""
        if obj.CreatedAt:
            try:
                if hasattr(obj.CreatedAt, 'isoformat'):
                    return obj.CreatedAt.isoformat()
                elif hasattr(obj.CreatedAt, 'strftime'):
                    return obj.CreatedAt.strftime('%Y-%m-%d')
                return str(obj.CreatedAt)
            except Exception as e:
                print(f"Warning: Error converting CreatedAt: {e}")
                return str(obj.CreatedAt) if obj.CreatedAt else None
        return None
    
    def get_FirstResponseAt(self, obj):
        """Convert FirstResponseAt to string to avoid utcoffset error"""
        if obj.FirstResponseAt:
            try:
                if hasattr(obj.FirstResponseAt, 'isoformat'):
                    return obj.FirstResponseAt.isoformat()
                elif hasattr(obj.FirstResponseAt, 'strftime'):
                    return obj.FirstResponseAt.strftime('%Y-%m-%d %H:%M:%S')
                return str(obj.FirstResponseAt)
            except Exception as e:
                print(f"Warning: Error converting FirstResponseAt: {e}")
                return str(obj.FirstResponseAt) if obj.FirstResponseAt else None
        return None
    
    def to_representation(self, instance):
        """
        Override to ensure all fields are properly serialized
        """
        # Get the default representation
        representation = super().to_representation(instance)
        
        # The SerializerMethodField methods above handle date/datetime fields
        # This method can be used for any additional processing if needed
        
        return representation


class RiskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAssignment
        fields = '__all__'


class RiskWorkflowSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SerializerMethodField()
    
    class Meta:
        model = Risk
        fields = ['id', 'title', 'description', 'severity', 'status', 'assigned_to']
        
    def get_assigned_to(self, obj):
        assignment = obj.assignments.first()
        if assignment:
            return assignment.assigned_to.username
        return None


# =============================================================================
# USER & SYSTEM MODULE SERIALIZERS
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    Role = serializers.SerializerMethodField()  # Add Role field for frontend compatibility
    
    class Meta:
        model = Users  # Use your custom Users model
        fields = ['UserId', 'UserName', 'FirstName', 'LastName', 'Email', 'CreatedAt', 'UpdatedAt', 'role', 'Role']
    
    def get_role(self, obj):
        return self.get_Role(obj)  # Use same logic for both fields
    
    def get_Role(self, obj):
        # Now you can use UserName and UserId
        name = obj.UserName.lower()
        user_id = obj.UserId
        
        # Assign roles based on name patterns or user ID
        if 'admin' in name or 'manager' in name:
            return 'Security Manager'
        elif 'analyst' in name or user_id % 4 == 1:
            return 'Security Analyst'
        elif 'auditor' in name or 'audit' in name or user_id % 4 == 2:
            return 'Audit Manager'
        elif 'compliance' in name or user_id % 4 == 3:
            return 'Compliance Officer'
        elif 'specialist' in name or 'senior' in name:
            return 'Senior Analyst'
        elif 'risk' in name:
            return 'Risk Analyst'
        elif 'operations' in name:
            return 'Operations Manager'
        else:
            # Default roles for other users
            roles = ['Security Analyst', 'Risk Analyst', 'Compliance Officer', 'IT Security Specialist']
            return roles[user_id % len(roles)]



class GRCLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GRCLog
        fields = '__all__'


class ExportTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportTask
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class S3FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = S3File
        fields = '__all__'


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = '__all__'  # Includes: Id, EntityName, Location


# =============================================================================
# CONSENT MANAGEMENT SERIALIZERS
# =============================================================================

from .models import ConsentConfiguration, ConsentAcceptance

class ConsentConfigurationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.UserName', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.UserName', read_only=True)
    framework_id = serializers.IntegerField(source='framework.FrameworkId', read_only=True)
    
    class Meta:
        model = ConsentConfiguration
        fields = [
            'config_id', 'action_type', 'action_label', 'is_enabled', 
            'consent_text', 'framework', 'framework_id', 'created_by', 'created_by_name',
            'created_at', 'updated_by', 'updated_by_name', 'updated_at'
        ]
        read_only_fields = ['config_id', 'created_at', 'updated_at', 'created_by_name', 'updated_by_name', 'framework_id']


class ConsentAcceptanceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.UserName', read_only=True)
    action_label = serializers.CharField(source='config.action_label', read_only=True)
    
    class Meta:
        model = ConsentAcceptance
        fields = [
            'acceptance_id', 'user', 'user_name', 'config', 'action_type', 
            'action_label', 'accepted_at', 'ip_address', 'user_agent', 'framework'
        ]
        read_only_fields = ['acceptance_id', 'accepted_at', 'user_name', 'action_label']
