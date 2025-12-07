"""
Risk validation module for centralized input validation.
This module implements secure input validation following the allow-list pattern.
"""

from typing import Dict, Any, Union, Optional
from django.core.exceptions import ValidationError
import re


class RiskValidator:
    """Centralized validator for risk-related inputs."""

    # Allowed values for choice fields
    ALLOWED_CRITICALITY = ['Critical', 'High', 'Medium', 'Low']
    ALLOWED_RISK_PRIORITY = ['High', 'Medium', 'Low']
    ALLOWED_ORIGIN = ['Manual', 'SIEM', 'AuditFindings']
    ALLOWED_RISK_TYPE = ['Current', 'Residual', 'Inherent', 'Emerging', 'Accept']
    ALLOWED_APPETITE = ['Yes', 'No']
    ALLOWED_RISK_RESPONSE_TYPE = ['Mitigate', 'Avoid', 'Accept', 'Transfer']

    # Numeric field ranges
    RISK_LIKELIHOOD_RANGE = (1, 10)
    RISK_IMPACT_RANGE = (1, 10)
    RISK_MULTIPLIER_X_RANGE = (1, 10)  # Displayed as 1-10, stored as 0.1-1.0
    RISK_MULTIPLIER_Y_RANGE = (1, 10)  # Displayed as 1-10, stored as 0.1-1.0

    # Text field patterns
    TEXT_PATTERN = r'^[A-Za-z0-9\s.,;:!?\'"()\-_\[\]]{0,}$'

    @classmethod
    def validate_choice_field(cls, value: str, field_name: str, allowed_values: list) -> str:
        """Validate a choice field against a list of allowed values."""
        if not value:
            raise ValidationError(f"{field_name} is required")
        
        if value not in allowed_values:
            raise ValidationError(
                f"Invalid {field_name}. Must be one of: {', '.join(allowed_values)}"
            )
        return value

    @classmethod
    def validate_numeric_field(cls, value: Union[int, str], field_name: str, min_val: int, max_val: int) -> int:
        """Validate a numeric field within a specified range."""
        try:
            numeric_value = int(value)
            if not min_val <= numeric_value <= max_val:
                raise ValidationError(
                    f"{field_name} must be between {min_val} and {max_val}"
                )
            return numeric_value
        except (TypeError, ValueError):
            raise ValidationError(f"{field_name} must be a number")

    @classmethod
    def validate_multiplier_field(cls, value: Union[int, float, str], field_name: str, min_val: int, max_val: int) -> float:
        """Validate a multiplier field and convert to 0.1-1.0 range for storage."""
        try:
            numeric_value = float(value)
            if not min_val <= numeric_value <= max_val:
                raise ValidationError(
                    f"{field_name} must be between {min_val} and {max_val}"
                )
            # Convert from 1-10 range to 0.1-1.0 range for storage
            return numeric_value / 10.0
        except (TypeError, ValueError):
            raise ValidationError(f"{field_name} must be a number")

    @classmethod
    def validate_text_field(cls, value: Optional[str], field_name: str, required: bool = False) -> Optional[str]:
        """Validate a text field against the allowed pattern."""
        if not value and required:
            raise ValidationError(f"{field_name} is required")
        
        if value and not re.match(cls.TEXT_PATTERN, value):
            raise ValidationError(
                f"{field_name} contains invalid characters"
            )
        return value

    @classmethod
    def validate_risk_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all risk-related input data."""
        if not isinstance(data, dict):
            raise ValidationError("Risk data must be a dictionary")

        errors = {}
        validated_data = {}

        try:
            # Validate Criticality
            if 'Criticality' in data:
                validated_data['Criticality'] = cls.validate_choice_field(
                    data['Criticality'], 'Criticality', cls.ALLOWED_CRITICALITY
                )

            # Validate RiskPriority
            if 'RiskPriority' in data:
                validated_data['RiskPriority'] = cls.validate_choice_field(
                    data['RiskPriority'], 'RiskPriority', cls.ALLOWED_RISK_PRIORITY
                )

            # Validate Origin
            if 'Origin' in data:
                validated_data['Origin'] = cls.validate_choice_field(
                    data['Origin'], 'Origin', cls.ALLOWED_ORIGIN
                )

            # Validate RiskType
            if 'RiskType' in data:
                validated_data['RiskType'] = cls.validate_choice_field(
                    data['RiskType'], 'RiskType', cls.ALLOWED_RISK_TYPE
                )

            # Validate Appetite
            if 'Appetite' in data:
                validated_data['Appetite'] = cls.validate_choice_field(
                    data['Appetite'], 'Appetite', cls.ALLOWED_APPETITE
                )

            # Validate RiskResponseType
            if 'RiskResponseType' in data:
                validated_data['RiskResponseType'] = cls.validate_choice_field(
                    data['RiskResponseType'], 'RiskResponseType', cls.ALLOWED_RISK_RESPONSE_TYPE
                )

            # Validate RiskLikelihood
            if 'RiskLikelihood' in data:
                validated_data['RiskLikelihood'] = cls.validate_numeric_field(
                    data['RiskLikelihood'], 'RiskLikelihood',
                    cls.RISK_LIKELIHOOD_RANGE[0], cls.RISK_LIKELIHOOD_RANGE[1]
                )

            # Validate RiskImpact
            if 'RiskImpact' in data:
                validated_data['RiskImpact'] = cls.validate_numeric_field(
                    data['RiskImpact'], 'RiskImpact',
                    cls.RISK_IMPACT_RANGE[0], cls.RISK_IMPACT_RANGE[1]
                )

            # Validate RiskMultiplierX
            if 'RiskMultiplierX' in data:
                validated_data['RiskMultiplierX'] = cls.validate_multiplier_field(
                    data['RiskMultiplierX'], 'RiskMultiplierX',
                    cls.RISK_MULTIPLIER_X_RANGE[0], cls.RISK_MULTIPLIER_X_RANGE[1]
                )

            # Validate RiskMultiplierY
            if 'RiskMultiplierY' in data:
                validated_data['RiskMultiplierY'] = cls.validate_multiplier_field(
                    data['RiskMultiplierY'], 'RiskMultiplierY',
                    cls.RISK_MULTIPLIER_Y_RANGE[0], cls.RISK_MULTIPLIER_Y_RANGE[1]
                )

            # Pass through fields that don't require validation
            passthrough_fields = [
                'RiskExposureRating', 'Category', 'BusinessImpact',
                'ComplianceId', 'RiskTitle', 'RiskDescription',
                'PossibleDamage', 'RiskMitigation', 'RiskId',
                'RiskOwner', 'RiskResponseDescription'
            ]
            for field in passthrough_fields:
                if field in data:
                    validated_data[field] = data[field]

        except ValidationError as e:
            errors[e.args[1] if len(e.args) > 1 else 'general'] = e.args[0]

        if errors:
            raise ValidationError(errors)

        return validated_data

    @classmethod
    def validate_risk_instance_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate risk instance data with additional instance-specific fields."""
        # First validate the base risk data
        validated_data = cls.validate_risk_data(data)

        # Add validation for instance-specific fields here if needed
        # For now, we're just passing them through as they don't require validation
        instance_fields = [
            'RiskInstanceId', 'IncidentId', 'ReportedBy', 'UserId',
            'MitigationDueDate', 'ModifiedMitigations', 'MitigationStatus',
            'MitigationCompletedDate', 'ReviewerCount', 'RiskFormDetails',
            'RecurrenceCount', 'Reviewer', 'ReviewerId', 'FirstResponseAt'
        ]
        for field in instance_fields:
            if field in data:
                validated_data[field] = data[field]

        return validated_data 