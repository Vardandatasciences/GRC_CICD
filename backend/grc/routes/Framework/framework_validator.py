"""
Framework validator module for validating framework-related inputs.
"""
import re
from datetime import date
from typing import Dict, Any, Union, Optional, List

class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass

def validate_string(value: Any, field_name: str, max_length: int = 255, 
                    allow_empty: bool = False, allowed_pattern: Optional[str] = None) -> str:
    """
    Validate a string value.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are allowed
        allowed_pattern: Optional regex pattern for allowed characters
        
    Returns:
        The validated string
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_empty:
            return ""
        raise ValidationError(f"{field_name} cannot be None")
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    if not allow_empty and not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length}")
    
    if allowed_pattern and not re.match(allowed_pattern, value):
        raise ValidationError(f"{field_name} contains invalid characters")
    
    return value

def validate_date(value: Any, field_name: str, allow_none: bool = False) -> Optional[date]:
    """
    Validate a date value.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        allow_none: Whether None is allowed
        
    Returns:
        The validated date or None
        
    Raises:
        ValidationError: If validation fails
    """
    # Treat None or empty string as None
    if value is None or (isinstance(value, str) and not value.strip()):
        if allow_none:
            return None
        raise ValidationError(f"{field_name} cannot be None or empty")
    
    if isinstance(value, date):
        return value
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string in YYYY-MM-DD format")
    
    try:
        year, month, day = map(int, value.split('-'))
        return date(year, month, day)
    except (ValueError, AttributeError):
        raise ValidationError(f"{field_name} must be a valid date in YYYY-MM-DD format")

def validate_boolean_string(value: Any, field_name: str) -> str:
    """
    Validate a string that should be either 'true' or 'false'.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated string ('true' or 'false')
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    value_lower = value.lower()
    if value_lower not in ['true', 'false']:
        raise ValidationError(f"{field_name} must be either 'true' or 'false'")
    
    return value_lower

def validate_framework_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate query parameters for framework list endpoint.
    
    Args:
        params: The query parameters to validate
        
    Returns:
        Dict of validated parameters
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Validate include_all_status parameter if present
    if 'include_all_status' in params:
        validated['include_all_status'] = validate_boolean_string(
            params.get('include_all_status', 'false'),
            'include_all_status'
        ) == 'true'
    else:
        validated['include_all_status'] = False
    
    # Validate include_all_for_identifiers parameter if present
    if 'include_all_for_identifiers' in params:
        validated['include_all_for_identifiers'] = validate_boolean_string(
            params.get('include_all_for_identifiers', 'false'),
            'include_all_for_identifiers'
        ) == 'true'
    else:
        validated['include_all_for_identifiers'] = False
    
    return validated

def validate_framework_post_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate POST data for framework creation.
    
    Args:
        data: The data to validate
        
    Returns:
        Dict of validated data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    validated = {}
    
    # Required fields
    validated['FrameworkName'] = validate_string(
        data.get('FrameworkName'), 
        'FrameworkName', 
        max_length=255, 
        allow_empty=False
    )
    
    # Optional fields with defaults
    validated['FrameworkDescription'] = validate_string(
        data.get('FrameworkDescription', ''), 
        'FrameworkDescription', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Category'] = validate_string(
        data.get('Category', ''), 
        'Category', 
        max_length=100, 
        allow_empty=False
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL', ''), 
        'DocURL', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        'Identifier', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['InternalExternal'] = validate_string(
        data.get('InternalExternal', ''), 
        'InternalExternal', 
        max_length=45, 
        allow_empty=False
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        'StartDate', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        'EndDate', 
        allow_none=True
    )
    
    # Creator fields
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName'), 
        'CreatedByName', 
        max_length=255, 
        allow_empty=False
    )
    
    # If CreatedByName is empty, try to get from the first policy
    if not validated['CreatedByName'] and 'policies' in data and isinstance(data['policies'], list) and len(data['policies']) > 0:
        validated['CreatedByName'] = validate_string(
            data['policies'][0].get('CreatedByName', ''),
            'CreatedByName from first policy',
            max_length=255,
            allow_empty=False
        )
    
    # Reviewer field
    validated['Reviewer'] = data.get('Reviewer')
    
    # If Reviewer is empty, try to get from the first policy
    if not validated['Reviewer'] and 'policies' in data and isinstance(data['policies'], list) and len(data['policies']) > 0:
        validated['Reviewer'] = data['policies'][0].get('Reviewer')
    
    # Validate policies if present
    if 'policies' in data:
        if not isinstance(data['policies'], list):
            raise ValidationError("Policies must be a list")
        
        validated_policies = []
        for i, policy_data in enumerate(data['policies']):
            if not isinstance(policy_data, dict):
                raise ValidationError(f"Policy at index {i} must be a JSON object")
            
            validated_policy = validate_policy_data(policy_data, i)
            validated_policies.append(validated_policy)
        
        validated['policies'] = validated_policies
    
    # Add additional fields needed for framework creation
    validated['CreatedByDate'] = date.today()
    validated['Status'] = 'Under Review'
    validated['ActiveInactive'] = 'InActive'
    validated['CurrentVersion'] = 1.0
    
    return validated

def validate_policy_data(data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate policy data within a framework.
    
    Args:
        data: The policy data to validate
        index: Index of the policy in the list for error messages
        
    Returns:
        Dict of validated policy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['PolicyName'] = validate_string(
        data.get('PolicyName'), 
        f'PolicyName for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyDescription'] = validate_string(
        data.get('PolicyDescription'), 
        f'PolicyDescription for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        f'StartDate for policy {index}', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        f'EndDate for policy {index}', 
        allow_none=True
    )
    
    # Optional fields
    validated['Department'] = validate_string(
        data.get('Department', ''), 
        f'Department for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName'), 
        f'CreatedByName for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Applicability'] = validate_string(
        data.get('Applicability'), 
        f'Applicability for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL'), 
        f'DocURL for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Scope'] = validate_string(
        data.get('Scope'), 
        f'Scope for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Objective'] = validate_string(
        data.get('Objective'), 
        f'Objective for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier'), 
        f'Identifier for policy {index}', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        f'PermanentTemporary for policy {index}', 
        max_length=45, 
        allow_empty=True
    )
    
    # Store reviewer ID for later lookup, but don't store directly in the validated data
    validated['ReviewerId'] = data.get('Reviewer')
    
    # For the actual Reviewer field, we'll set this to empty string initially
    # The actual name will be looked up and set in the framework_list function
    validated['Reviewer'] = ''
    
    # Coverage rate - numeric field
    coverage_rate = data.get('CoverageRate')
    if coverage_rate is None:
        raise ValidationError(f"CoverageRate for policy {index} is required")
    try:
        validated['CoverageRate'] = float(coverage_rate)
    except (ValueError, TypeError):
        raise ValidationError(f"CoverageRate for policy {index} must be a valid number")
    
    # Policy category fields
    validated['PolicyType'] = validate_string(
        data.get('PolicyType'), 
        f'PolicyType for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyCategory'] = validate_string(
        data.get('PolicyCategory'), 
        f'PolicyCategory for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicySubCategory'] = validate_string(
        data.get('PolicySubCategory'), 
        f'PolicySubCategory for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    # Entities field - can be a string "all" or a list of entity IDs
    entities = data.get('Entities', [])
    if entities == 'all' or entities == "all":
        validated['Entities'] = 'all'
    elif isinstance(entities, list):
        validated['Entities'] = entities
    else:
        # Default to empty list if invalid type
        validated['Entities'] = []
    
    # Validate subpolicies if present
    if 'subpolicies' in data:
        if not isinstance(data['subpolicies'], list):
            raise ValidationError(f"Subpolicies for policy {index} must be a list")
        
        validated_subpolicies = []
        for j, subpolicy_data in enumerate(data['subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"Subpolicy at index {j} for policy {index} must be a JSON object")
            
            validated_subpolicy = validate_subpolicy_data(subpolicy_data, index, j)
            validated_subpolicies.append(validated_subpolicy)
        
        validated['subpolicies'] = validated_subpolicies
    
    return validated

def validate_subpolicy_data(data: Dict[str, Any], policy_index: int, subpolicy_index: int) -> Dict[str, Any]:
    """
    Validate subpolicy data within a policy.
    
    Args:
        data: The subpolicy data to validate
        policy_index: Index of the parent policy for error messages
        subpolicy_index: Index of the subpolicy for error messages
        
    Returns:
        Dict of validated subpolicy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['SubPolicyName'] = validate_string(
        data.get('SubPolicyName'), 
        f'SubPolicyName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName'), 
        f'CreatedByName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier'), 
        f'Identifier for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['Description'] = validate_string(
        data.get('Description'), 
        f'Description for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    # Optional fields with defaults
    validated['Status'] = 'Under Review'
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        f'PermanentTemporary for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=50, 
        allow_empty=True
    )
    
    validated['Control'] = validate_string(
        data.get('Control'), 
        f'Control for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    # Set creation date to today
    validated['CreatedByDate'] = date.today()
    
    return validated

def validate_add_policy_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate request data for adding policies to a framework.
    
    Args:
        data: The request data to validate
        
    Returns:
        Dict of validated data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    validated = {}
    
    # Check if the request has a 'policies' key
    if 'policies' in data:
        if not isinstance(data['policies'], list):
            raise ValidationError("'policies' must be a list")
        
        # Validate each policy in the list
        validated_policies = []
        for i, policy_data in enumerate(data['policies']):
            if not isinstance(policy_data, dict):
                raise ValidationError(f"Policy at index {i} must be a JSON object")
            
            validated_policy = validate_policy_for_add(policy_data, i)
            validated_policies.append(validated_policy)
        
        validated['policies'] = validated_policies
    else:
        # If no 'policies' key, check if the data itself is a policy
        if 'PolicyName' in data:
            validated_policy = validate_policy_for_add(data, 0)
            validated['policies'] = [validated_policy]
        else:
            raise ValidationError("Invalid request format. Expected 'policies' array or policy object")
    
    return validated

def validate_policy_for_add(data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate policy data for adding to a framework.
    
    Args:
        data: The policy data to validate
        index: Index of the policy in the list for error messages
        
    Returns:
        Dict of validated policy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['PolicyName'] = validate_string(
        data.get('PolicyName'), 
        f'PolicyName for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyDescription'] = validate_string(
        data.get('PolicyDescription'), 
        f'PolicyDescription for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        f'StartDate for policy {index}', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        f'EndDate for policy {index}', 
        allow_none=True
    )
    
    # Optional fields
    validated['Department'] = validate_string(
        data.get('Department', ''), 
        f'Department for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName'), 
        f'CreatedByName for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedById'] = data.get('CreatedById')
    
    validated['Applicability'] = validate_string(
        data.get('Applicability'), 
        f'Applicability for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL'), 
        f'DocURL for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Scope'] = validate_string(
        data.get('Scope'), 
        f'Scope for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Objective'] = validate_string(
        data.get('Objective'), 
        f'Objective for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier'), 
        f'Identifier for policy {index}', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        f'PermanentTemporary for policy {index}', 
        max_length=45, 
        allow_empty=True
    )
    
    # Store reviewer ID for later lookup
    validated['Reviewer'] = data.get('Reviewer')
    
    # Coverage rate - numeric field
    coverage_rate = data.get('CoverageRate')
    if coverage_rate is None:
        raise ValidationError(f"CoverageRate for policy {index} is required")
    try:
        validated['CoverageRate'] = float(coverage_rate)
    except (ValueError, TypeError):
        raise ValidationError(f"CoverageRate for policy {index} must be a valid number")
    
    # Policy category fields
    validated['PolicyType'] = validate_string(
        data.get('PolicyType'), 
        f'PolicyType for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyCategory'] = validate_string(
        data.get('PolicyCategory'), 
        f'PolicyCategory for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicySubCategory'] = validate_string(
        data.get('PolicySubCategory'), 
        f'PolicySubCategory for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    # Entities field - can be a string "all" or a list of entity IDs
    entities = data.get('Entities', [])
    if entities == 'all' or entities == "all":
        validated['Entities'] = 'all'
    elif isinstance(entities, list):
        validated['Entities'] = entities
    else:
        # Default to empty list if invalid type
        validated['Entities'] = []
    
    # Validate subpolicies if present
    if 'subpolicies' in data:
        if not isinstance(data['subpolicies'], list):
            raise ValidationError(f"Subpolicies for policy {index} must be a list")
        
        validated_subpolicies = []
        for j, subpolicy_data in enumerate(data['subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"Subpolicy at index {j} for policy {index} must be a JSON object")
            
            validated_subpolicy = validate_subpolicy_for_add(subpolicy_data, index, j)
            validated_subpolicies.append(validated_subpolicy)
        
        validated['subpolicies'] = validated_subpolicies
    
    return validated

def validate_subpolicy_for_add(data: Dict[str, Any], policy_index: int, subpolicy_index: int) -> Dict[str, Any]:
    """
    Validate subpolicy data for adding to a policy.
    
    Args:
        data: The subpolicy data to validate
        policy_index: Index of the parent policy for error messages
        subpolicy_index: Index of the subpolicy for error messages
        
    Returns:
        Dict of validated subpolicy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['SubPolicyName'] = validate_string(
        data.get('SubPolicyName'), 
        f'SubPolicyName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName'), 
        f'CreatedByName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier'), 
        f'Identifier for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['Description'] = validate_string(
        data.get('Description'), 
        f'Description for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    # Optional fields with defaults
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        f'PermanentTemporary for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=50, 
        allow_empty=True
    )
    
    validated['Control'] = validate_string(
        data.get('Control'), 
        f'Control for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    return validated

def safe_isoformat(d: Optional[date]) -> Optional[str]:
    """
    Safely convert a date to ISO format string.
    
    Args:
        d: The date to convert
        
    Returns:
        ISO format string or None
    """
    return d.isoformat() if d else None

def validate_tailored_framework_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate POST data for tailored framework creation.
    
    Args:
        data: The data to validate
        
    Returns:
        Dict of validated data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    validated = {}
    
    # Required fields
    validated['title'] = validate_string(
        data.get('title'), 
        'title', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['createdByName'] = validate_string(
        data.get('createdByName'), 
        'createdByName', 
        max_length=255, 
        allow_empty=False
    )
    
    # All fields are required
    validated['description'] = validate_string(
        data.get('description'), 
        'description', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['category'] = validate_string(
        data.get('category'), 
        'category', 
        max_length=100, 
        allow_empty=False
    )
    
    validated['docURL'] = validate_string(
        data.get('docURL', ''), 
        'docURL', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['identifier'] = validate_string(
        data.get('identifier'), 
        'identifier', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['reviewer'] = validate_string(
        data.get('reviewer'), 
        'reviewer', 
        max_length=255, 
        allow_empty=False
    )
    
    # Date fields
    validated['startDate'] = validate_date(
        data.get('startDate'), 
        'startDate', 
        allow_none=False
    )
    
    validated['endDate'] = validate_date(
        data.get('endDate'), 
        'endDate', 
        allow_none=True
    )
    
    # Validate policies if present
    if 'policies' in data:
        if not isinstance(data['policies'], list):
            raise ValidationError("Policies must be a list")
        
        validated_policies = []
        for i, policy_data in enumerate(data['policies']):
            if not isinstance(policy_data, dict):
                raise ValidationError(f"Policy at index {i} must be a JSON object")
            
            validated_policy = validate_tailored_policy_data(policy_data, i)
            validated_policies.append(validated_policy)
        
        validated['policies'] = validated_policies
    else:
        validated['policies'] = []
    
    return validated

def validate_tailored_policy_data(data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate policy data within a tailored framework.
    
    Args:
        data: The policy data to validate
        index: Index of the policy in the list for error messages
        
    Returns:
        Dict of validated policy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Exclude flag
    validated['exclude'] = bool(data.get('exclude', False))

    # If policy is excluded, no other fields are required
    if validated['exclude']:
        return validated
    
    # Required fields
    validated['title'] = validate_string(
        data.get('title'), 
        f'title for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['description'] = validate_string(
        data.get('description'), 
        f'description for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    # Date fields
    validated['startDate'] = validate_date(
        data.get('startDate'), 
        f'startDate for policy {index}', 
        allow_none=False
    )
    
    validated['endDate'] = validate_date(
        data.get('endDate'), 
        f'endDate for policy {index}', 
        allow_none=True
    )
    
    # All fields are required
    validated['department'] = validate_string(
        data.get('department'), 
        f'department for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['createdByName'] = validate_string(
        data.get('createdByName', ''), 
        f'createdByName for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['reviewer'] = validate_string(
        data.get('reviewer', ''), 
        f'reviewer for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['applicability'] = validate_string(
        data.get('applicability'), 
        f'applicability for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['docURL'] = validate_string(
        data.get('docURL'), 
        f'docURL for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['scope'] = validate_string(
        data.get('scope'), 
        f'scope for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['objective'] = validate_string(
        data.get('objective'), 
        f'objective for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['identifier'] = validate_string(
        data.get('identifier'), 
        f'identifier for policy {index}', 
        max_length=45, 
        allow_empty=False
    )
    
    # Policy category fields
    validated['PolicyType'] = validate_string(
        data.get('PolicyType'), 
        f'PolicyType for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyCategory'] = validate_string(
        data.get('PolicyCategory'), 
        f'PolicyCategory for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicySubCategory'] = validate_string(
        data.get('PolicySubCategory'), 
        f'PolicySubCategory for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    # Entities field - can be a string "all" or a list of entity IDs
    entities = data.get('Entities', [])
    if entities == 'all' or entities == "all":
        validated['Entities'] = 'all'
    elif isinstance(entities, list):
        validated['Entities'] = entities
    else:
        # Default to empty list if invalid type
        validated['Entities'] = []
    
    # Coverage rate - numeric field
    coverage_rate = data.get('coverageRate')
    if coverage_rate is None:
        raise ValidationError(f"CoverageRate for policy {index} is required")
    try:
        validated['coverageRate'] = float(coverage_rate)
    except (ValueError, TypeError):
        raise ValidationError(f"CoverageRate for policy {index} must be a valid number")
    
    # Validate subpolicies if present
    if 'subPolicies' in data:
        if not isinstance(data['subPolicies'], list):
            raise ValidationError(f"subPolicies for policy {index} must be a list")
        
        validated_subpolicies = []
        for j, subpolicy_data in enumerate(data['subPolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"Subpolicy at index {j} for policy {index} must be a JSON object")
            
            validated_subpolicy = validate_tailored_subpolicy_data(subpolicy_data, index, j)
            validated_subpolicies.append(validated_subpolicy)
        
        validated['subPolicies'] = validated_subpolicies
    else:
        validated['subPolicies'] = []
    
    return validated

def validate_tailored_subpolicy_data(data: Dict[str, Any], policy_index: int, subpolicy_index: int) -> Dict[str, Any]:
    """
    Validate subpolicy data within a tailored policy.
    
    Args:
        data: The subpolicy data to validate
        policy_index: Index of the parent policy for error messages
        subpolicy_index: Index of the subpolicy for error messages
        
    Returns:
        Dict of validated subpolicy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Exclude flag
    validated['exclude'] = bool(data.get('exclude', False))

    # If subpolicy is excluded, no other fields are required
    if validated['exclude']:
        return validated
    
    # Required fields
    validated['title'] = validate_string(
        data.get('title'), 
        f'title for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['description'] = validate_string(
        data.get('description'), 
        f'description for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['identifier'] = validate_string(
        data.get('identifier'), 
        f'identifier for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['control'] = validate_string(
        data.get('control'), 
        f'control for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    return validated

def validate_tailored_framework_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate query parameters for tailored framework creation.
    
    Args:
        params: The query parameters to validate
        
    Returns:
        Dict of validated parameters
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Currently no specific query parameters for tailored framework creation
    # This function is included for consistency and future extensibility
    
    return validated

def validate_tailored_policy_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate POST data for tailored policy creation.
    
    Args:
        data: The data to validate
        
    Returns:
        Dict of validated data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    validated = {}
    
    # Required fields
    validated['TargetFrameworkId'] = validate_framework_id(
        data.get('TargetFrameworkId'), 
        'TargetFrameworkId'
    )
    
    validated['PolicyName'] = validate_string(
        data.get('PolicyName'), 
        'PolicyName', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName'), 
        'CreatedByName', 
        max_length=255, 
        allow_empty=False
    )
    
    # Optional fields with defaults
    validated['PolicyDescription'] = validate_string(
        data.get('PolicyDescription', ''), 
        'PolicyDescription', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Department'] = validate_string(
        data.get('Department', ''), 
        'Department', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Reviewer'] = validate_string(
        data.get('Reviewer', ''), 
        'Reviewer', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Applicability'] = validate_string(
        data.get('Applicability', ''), 
        'Applicability', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL', ''), 
        'DocURL', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Scope'] = validate_string(
        data.get('Scope', ''), 
        'Scope', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Objective'] = validate_string(
        data.get('Objective', ''), 
        'Objective', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        'Identifier', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        'PermanentTemporary', 
        max_length=45, 
        allow_empty=True
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        'StartDate', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        'EndDate', 
        allow_none=True
    )
    
    # Policy category fields
    validated['PolicyType'] = validate_string(
        data.get('PolicyType', ''), 
        'PolicyType', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyCategory'] = validate_string(
        data.get('PolicyCategory', ''), 
        'PolicyCategory', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicySubCategory'] = validate_string(
        data.get('PolicySubCategory', ''), 
        'PolicySubCategory', 
        max_length=255, 
        allow_empty=False
    )
    
    # Entities field - can be a string "all" or a list of entity IDs
    entities = data.get('Entities', [])
    if entities == 'all' or entities == "all":
        validated['Entities'] = 'all'
    elif isinstance(entities, list):
        validated['Entities'] = entities
    else:
        # Default to empty list if invalid type
        validated['Entities'] = []
    
    # Coverage rate - numeric field
    coverage_rate = data.get('CoverageRate')
    if coverage_rate is None:
        raise ValidationError("CoverageRate is required")
    try:
        validated['coverageRate'] = float(coverage_rate)
    except (ValueError, TypeError):
        raise ValidationError("CoverageRate must be a valid number")
    
    # Validate subpolicies if present
    if 'subpolicies' in data:
        if not isinstance(data['subpolicies'], list):
            raise ValidationError("Subpolicies must be a list")
        
        validated_subpolicies = []
        for i, subpolicy_data in enumerate(data['subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"Subpolicy at index {i} must be a JSON object")
            
            validated_subpolicy = validate_tailored_policy_subpolicy_data(subpolicy_data, i)
            validated_subpolicies.append(validated_subpolicy)
        
        validated['subpolicies'] = validated_subpolicies
    else:
        validated['subpolicies'] = []
    
    return validated

def validate_tailored_policy_subpolicy_data(data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate subpolicy data within a tailored policy request.
    
    Args:
        data: The subpolicy data to validate
        index: Index of the subpolicy in the list for error messages
        
    Returns:
        Dict of validated subpolicy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields
    validated['SubPolicyName'] = validate_string(
        data.get('SubPolicyName', ''), 
        f'SubPolicyName for subpolicy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Description'] = validate_string(
        data.get('Description', ''), 
        f'Description for subpolicy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        f'Identifier for subpolicy {index}', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['Control'] = validate_string(
        data.get('Control', ''), 
        f'Control for subpolicy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        f'PermanentTemporary for subpolicy {index}', 
        max_length=50, 
        allow_empty=True
    )
    
    # Exclude flag
    validated['exclude'] = bool(data.get('exclude', False))
    
    return validated

def validate_framework_id(value: Any, field_name: str) -> int:
    """
    Validate a framework ID value.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated framework ID as integer
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise ValidationError(f"{field_name} cannot be None")
    
    try:
        framework_id = int(value)
        if framework_id <= 0:
            raise ValidationError(f"{field_name} must be a positive integer")
        return framework_id
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer")

def validate_policy_category_combination(policy_type: str, policy_category: str, policy_subcategory: str) -> bool:
    """
    Validate that all policy category fields are provided together or none at all.
    
    Args:
        policy_type: Policy type value
        policy_category: Policy category value
        policy_subcategory: Policy subcategory value
        
    Returns:
        True if validation passes
        
    Raises:
        ValidationError: If validation fails
    """
    # Strip whitespace from all values
    policy_type = policy_type.strip() if policy_type else ''
    policy_category = policy_category.strip() if policy_category else ''
    policy_subcategory = policy_subcategory.strip() if policy_subcategory else ''
    
    # Check if any of them is filled
    if any([policy_type, policy_category, policy_subcategory]):
        # If any is filled, all must be filled
        if not all([policy_type, policy_category, policy_subcategory]):
            raise ValidationError("All of PolicyType, PolicyCategory, and PolicySubCategory are required together")
    
    return True

def validate_framework_version_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate POST data for framework version creation.
    
    Args:
        data: The data to validate
        
    Returns:
        Dict of validated data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    validated = {}
    
    # Required fields
    validated['FrameworkName'] = validate_string(
        data.get('FrameworkName'), 
        'FrameworkName', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName'), 
        'CreatedByName', 
        max_length=255, 
        allow_empty=False
    )
    
    # Optional fields with defaults
    validated['FrameworkDescription'] = validate_string(
        data.get('FrameworkDescription', ''), 
        'FrameworkDescription', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Category'] = validate_string(
        data.get('Category', ''), 
        'Category', 
        max_length=100, 
        allow_empty=False
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL', ''), 
        'DocURL', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        'Identifier', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['ReviewerName'] = validate_string(
        data.get('ReviewerName', ''), 
        'ReviewerName', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Reviewer'] = data.get('Reviewer')  # Can be ID or name
    
    validated['InternalExternal'] = validate_string(
        data.get('InternalExternal', ''), 
        'InternalExternal', 
        max_length=45, 
        allow_empty=True
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        'StartDate', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        'EndDate', 
        allow_none=True
    )
    
    # Validate policies if present
    if 'policies' in data:
        if not isinstance(data['policies'], list):
            raise ValidationError("Policies must be a list")
        
        validated_policies = []
        for i, policy_data in enumerate(data['policies']):
            if not isinstance(policy_data, dict):
                raise ValidationError(f"Policy at index {i} must be a JSON object")
            
            validated_policy = validate_framework_version_policy_data(policy_data, i)
            validated_policies.append(validated_policy)
        
        validated['policies'] = validated_policies
    else:
        validated['policies'] = []
    
    # Validate new policies if present
    if 'new_policies' in data:
        if not isinstance(data['new_policies'], list):
            raise ValidationError("New policies must be a list")
        
        validated_new_policies = []
        for i, policy_data in enumerate(data['new_policies']):
            if not isinstance(policy_data, dict):
                raise ValidationError(f"New policy at index {i} must be a JSON object")
            
            validated_policy = validate_framework_version_new_policy_data(policy_data, i)
            validated_new_policies.append(validated_policy)
        
        validated['new_policies'] = validated_new_policies
    else:
        validated['new_policies'] = []
    
    return validated

def validate_framework_version_policy_data(data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate policy data within a framework version (existing policies).
    
    Args:
        data: The policy data to validate
        index: Index of the policy in the list for error messages
        
    Returns:
        Dict of validated policy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Exclude flag
    validated['exclude'] = bool(data.get('exclude', False))
    
    # If policy is excluded, no other fields are required
    if validated['exclude']:
        validated['original_policy_id'] = data.get('original_policy_id')
        return validated
    
    # Required fields for existing policies
    validated['original_policy_id'] = validate_policy_id(
        data.get('original_policy_id'), 
        f'original_policy_id for policy {index}'
    )
    
    validated['PolicyName'] = validate_string(
        data.get('PolicyName', ''), 
        f'PolicyName for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyDescription'] = validate_string(
        data.get('PolicyDescription', ''), 
        f'PolicyDescription for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        f'StartDate for policy {index}', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        f'EndDate for policy {index}', 
        allow_none=True
    )
    
    # Optional fields
    validated['Department'] = validate_string(
        data.get('Department', ''), 
        f'Department for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName', ''), 
        f'CreatedByName for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['ReviewerName'] = validate_string(
        data.get('ReviewerName', ''), 
        f'ReviewerName for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Reviewer'] = data.get('Reviewer')  # Can be ID or name
    
    validated['Applicability'] = validate_string(
        data.get('Applicability', ''), 
        f'Applicability for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL', ''), 
        f'DocURL for policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Scope'] = validate_string(
        data.get('Scope', ''), 
        f'Scope for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Objective'] = validate_string(
        data.get('Objective', ''), 
        f'Objective for policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        f'Identifier for policy {index}', 
        max_length=45, 
        allow_empty=False
    )
    
    # Policy category fields
    validated['PolicyType'] = validate_string(
        data.get('PolicyType', ''), 
        f'PolicyType for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyCategory'] = validate_string(
        data.get('PolicyCategory', ''), 
        f'PolicyCategory for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicySubCategory'] = validate_string(
        data.get('PolicySubCategory', ''), 
        f'PolicySubCategory for policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    # Entities field - can be a string "all" or a list of entity IDs
    entities = data.get('Entities', [])
    if entities == 'all' or entities == "all":
        validated['Entities'] = 'all'
    elif isinstance(entities, list):
        # Validate that all items in the list are valid entity IDs (integers or strings that can be converted to integers)
        validated_entities = []
        for entity_id in entities:
            if entity_id == 'all':
                validated['Entities'] = 'all'
                break
            try:
                # Try to convert to int to validate it's a proper entity ID
                int(entity_id)
                validated_entities.append(entity_id)
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid entity ID '{entity_id}' in Entities for policy {index}")
        else:
            validated['Entities'] = validated_entities
    else:
        validated['Entities'] = []
    
    # Coverage rate - numeric field
    coverage_rate = data.get('CoverageRate')
    if coverage_rate is None:
        raise ValidationError(f"CoverageRate for policy {index} is required")
    try:
        validated['CoverageRate'] = float(coverage_rate)
    except (ValueError, TypeError):
        raise ValidationError(f"CoverageRate for policy {index} must be a valid number")
    
    # Validate subpolicies if present
    if 'subpolicies' in data:
        if not isinstance(data['subpolicies'], list):
            raise ValidationError(f"Subpolicies for policy {index} must be a list")
        
        validated_subpolicies = []
        for j, subpolicy_data in enumerate(data['subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"Subpolicy at index {j} for policy {index} must be a JSON object")
            
            validated_subpolicy = validate_framework_version_subpolicy_data(subpolicy_data, index, j)
            validated_subpolicies.append(validated_subpolicy)
        
        validated['subpolicies'] = validated_subpolicies
    else:
        validated['subpolicies'] = []
    
    # Validate new subpolicies if present (for existing policies)
    if 'new_subpolicies' in data:
        if not isinstance(data['new_subpolicies'], list):
            raise ValidationError(f"New subpolicies for policy {index} must be a list")
        
        validated_new_subpolicies = []
        for j, subpolicy_data in enumerate(data['new_subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"New subpolicy at index {j} for policy {index} must be a JSON object")
            
            validated_subpolicy = validate_framework_version_new_subpolicy_data(subpolicy_data, index, j)
            validated_new_subpolicies.append(validated_subpolicy)
        
        validated['new_subpolicies'] = validated_new_subpolicies
    else:
        validated['new_subpolicies'] = []
    
    return validated

def validate_framework_version_new_policy_data(data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate new policy data within a framework version.
    
    Args:
        data: The new policy data to validate
        index: Index of the policy in the list for error messages
        
    Returns:
        Dict of validated policy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields for new policies
    validated['PolicyName'] = validate_string(
        data.get('PolicyName', ''), 
        f'PolicyName for new policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName', ''), 
        f'CreatedByName for new policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['PolicyDescription'] = validate_string(
        data.get('PolicyDescription', ''), 
        f'PolicyDescription for new policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        f'StartDate for new policy {index}', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        f'EndDate for new policy {index}', 
        allow_none=True
    )
    
    # Optional fields
    validated['Department'] = validate_string(
        data.get('Department', ''), 
        f'Department for new policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['ReviewerName'] = validate_string(
        data.get('ReviewerName', ''), 
        f'ReviewerName for new policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Applicability'] = validate_string(
        data.get('Applicability', ''), 
        f'Applicability for new policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL', ''), 
        f'DocURL for new policy {index}', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Scope'] = validate_string(
        data.get('Scope', ''), 
        f'Scope for new policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Objective'] = validate_string(
        data.get('Objective', ''), 
        f'Objective for new policy {index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        f'Identifier for new policy {index}', 
        max_length=45, 
        allow_empty=False
    )
    
    # Policy category fields
    validated['PolicyType'] = validate_string(
        data.get('PolicyType', ''), 
        f'PolicyType for new policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyCategory'] = validate_string(
        data.get('PolicyCategory', ''), 
        f'PolicyCategory for new policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicySubCategory'] = validate_string(
        data.get('PolicySubCategory', ''), 
        f'PolicySubCategory for new policy {index}', 
        max_length=255, 
        allow_empty=False
    )
    
    # Entities field - can be a string "all" or a list of entity IDs
    entities = data.get('Entities', [])
    if entities == 'all' or entities == "all":
        validated['Entities'] = 'all'
    elif isinstance(entities, list):
        # Validate that all items in the list are valid entity IDs (integers or strings that can be converted to integers)
        validated_entities = []
        for entity_id in entities:
            if entity_id == 'all':
                validated['Entities'] = 'all'
                break
            try:
                # Try to convert to int to validate it's a proper entity ID
                int(entity_id)
                validated_entities.append(entity_id)
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid entity ID '{entity_id}' in Entities for new policy {index}")
        else:
            validated['Entities'] = validated_entities
    else:
        validated['Entities'] = []
    
    # Coverage rate - numeric field
    coverage_rate = data.get('CoverageRate')
    if coverage_rate is None:
        raise ValidationError(f"CoverageRate for new policy {index} is required")
    try:
        validated['CoverageRate'] = float(coverage_rate)
    except (ValueError, TypeError):
        raise ValidationError(f"CoverageRate for new policy {index} must be a valid number")
    
    # Validate subpolicies if present
    if 'subpolicies' in data:
        if not isinstance(data['subpolicies'], list):
            raise ValidationError(f"Subpolicies for new policy {index} must be a list")
        
        validated_subpolicies = []
        for j, subpolicy_data in enumerate(data['subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"Subpolicy at index {j} for new policy {index} must be a JSON object")
            
            # Use the new subpolicy validator for new policies
            validated_subpolicy = validate_framework_version_new_subpolicy_data(subpolicy_data, index, j)
            validated_subpolicies.append(validated_subpolicy)
        
        validated['subpolicies'] = validated_subpolicies
    else:
        validated['subpolicies'] = []
    
    return validated

def validate_framework_version_subpolicy_data(data: Dict[str, Any], policy_index: int, subpolicy_index: int) -> Dict[str, Any]:
    """
    Validate subpolicy data within a framework version (existing subpolicies).
    
    Args:
        data: The subpolicy data to validate
        policy_index: Index of the parent policy for error messages
        subpolicy_index: Index of the subpolicy for error messages
        
    Returns:
        Dict of validated subpolicy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Exclude flag
    validated['exclude'] = bool(data.get('exclude', False))

    # If subpolicy is excluded, no other fields are required
    if validated['exclude']:
        validated['original_subpolicy_id'] = data.get('original_subpolicy_id')
        return validated
    
    # Check if this is a new subpolicy (no original_subpolicy_id) or existing subpolicy
    original_subpolicy_id = data.get('original_subpolicy_id')
    
    if original_subpolicy_id is not None:
        # This is an existing subpolicy being modified
        validated['original_subpolicy_id'] = validate_subpolicy_id(
            original_subpolicy_id, 
            f'original_subpolicy_id for subpolicy {subpolicy_index} of policy {policy_index}'
        )
    else:
        # This is a new subpolicy being added to an existing policy
        validated['original_subpolicy_id'] = None
    
    validated['SubPolicyName'] = validate_string(
        data.get('SubPolicyName', ''), 
        f'SubPolicyName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Description'] = validate_string(
        data.get('Description', ''), 
        f'Description for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        f'Identifier for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['Control'] = validate_string(
        data.get('Control', ''), 
        f'Control for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        f'PermanentTemporary for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=50, 
        allow_empty=True
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName', ''), 
        f'CreatedByName for subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=True
    )
    
    return validated

def validate_framework_version_new_subpolicy_data(data: Dict[str, Any], policy_index: int, subpolicy_index: int) -> Dict[str, Any]:
    """
    Validate new subpolicy data within a framework version.
    
    Args:
        data: The new subpolicy data to validate
        policy_index: Index of the parent policy for error messages
        subpolicy_index: Index of the subpolicy for error messages
        
    Returns:
        Dict of validated subpolicy data
        
    Raises:
        ValidationError: If validation fails
    """
    validated = {}
    
    # Required fields for new subpolicies
    validated['SubPolicyName'] = validate_string(
        data.get('SubPolicyName', ''), 
        f'SubPolicyName for new subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Description'] = validate_string(
        data.get('Description', ''), 
        f'Description for new subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier', ''), 
        f'Identifier for new subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['Control'] = validate_string(
        data.get('Control', ''), 
        f'Control for new subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        f'PermanentTemporary for new subpolicy {subpolicy_index} of policy {policy_index}', 
        max_length=50, 
        allow_empty=True
    )
    
    return validated

def validate_policy_id(value: Any, field_name: str) -> int:
    """
    Validate a policy ID value.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated policy ID as integer
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise ValidationError(f"{field_name} cannot be None")
    
    try:
        policy_id = int(value)
        if policy_id <= 0:
            raise ValidationError(f"{field_name} must be a positive integer")
        return policy_id
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer")

def validate_subpolicy_id(value: Any, field_name: str) -> int:
    """
    Validate a subpolicy ID value.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated subpolicy ID as integer
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise ValidationError(f"{field_name} cannot be None")
    
    try:
        subpolicy_id = int(value)
        if subpolicy_id <= 0:
            raise ValidationError(f"{field_name} must be a positive integer")
        return subpolicy_id
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer")

def validate_policy_version_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate POST data for policy version creation.
    
    Args:
        data: The data to validate
        
    Returns:
        Dict of validated data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    validated = {}
    
    # Required fields
    validated['PolicyName'] = validate_string(
        data.get('PolicyName'), 
        'PolicyName', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyDescription'] = validate_string(
        data.get('PolicyDescription'), 
        'PolicyDescription', 
        max_length=65535, 
        allow_empty=False
    )
    
    # Date fields
    validated['StartDate'] = validate_date(
        data.get('StartDate'), 
        'StartDate', 
        allow_none=False
    )
    
    validated['EndDate'] = validate_date(
        data.get('EndDate'), 
        'EndDate', 
        allow_none=True
    )
    
    # All fields are required except for DocURL, PermanentTemporary, and excluded subpolicies
    validated['Department'] = validate_string(
        data.get('Department'), 
        'Department', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['CreatedByName'] = validate_string(
        data.get('CreatedByName'), 
        'CreatedByName', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['Reviewer'] = data.get('Reviewer')  # Can be ID or name

    validated['Applicability'] = validate_string(
        data.get('Applicability'), 
        'Applicability', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['DocURL'] = validate_string(
        data.get('DocURL', ''), 
        'DocURL', 
        max_length=255, 
        allow_empty=True
    )
    
    validated['Scope'] = validate_string(
        data.get('Scope'), 
        'Scope', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Objective'] = validate_string(
        data.get('Objective'), 
        'Objective', 
        max_length=65535, 
        allow_empty=False
    )
    
    validated['Identifier'] = validate_string(
        data.get('Identifier'), 
        'Identifier', 
        max_length=45, 
        allow_empty=False
    )
    
    validated['PermanentTemporary'] = validate_string(
        data.get('PermanentTemporary', ''), 
        'PermanentTemporary', 
        max_length=45, 
        allow_empty=True
    )
    
    # Policy category fields
    validated['PolicyType'] = validate_string(
        data.get('PolicyType'), 
        'PolicyType', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicyCategory'] = validate_string(
        data.get('PolicyCategory'), 
        'PolicyCategory', 
        max_length=255, 
        allow_empty=False
    )
    
    validated['PolicySubCategory'] = validate_string(
        data.get('PolicySubCategory'), 
        'PolicySubCategory', 
        max_length=255, 
        allow_empty=False
    )
    
    # Entities field - can be a string "all" or a list of entity IDs
    entities = data.get('Entities', [])
    if entities == 'all' or entities == "all":
        validated['Entities'] = 'all'
    elif isinstance(entities, list):
        # Validate that all items in the list are valid entity IDs (integers or strings that can be converted to integers)
        validated_entities = []
        for entity_id in entities:
            if entity_id == 'all':
                validated['Entities'] = 'all'
                break
            try:
                # Try to convert to int to validate it's a proper entity ID
                int(entity_id)
                validated_entities.append(entity_id)
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid entity ID '{entity_id}' in Entities")
        else:
            validated['Entities'] = validated_entities
    else:
        validated['Entities'] = []
    
    # Coverage rate - numeric field
    coverage_rate = data.get('CoverageRate')
    if coverage_rate is None:
        raise ValidationError("CoverageRate is required")
    try:
        validated['CoverageRate'] = float(coverage_rate)
    except (ValueError, TypeError):
        raise ValidationError("CoverageRate must be a valid number")

    # Validate subpolicies if present
    if 'subpolicies' in data:
        if not isinstance(data['subpolicies'], list):
            raise ValidationError("Subpolicies must be a list")
        
        validated_subpolicies = []
        for i, subpolicy_data in enumerate(data['subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"Subpolicy at index {i} must be a JSON object")
            
            validated_subpolicy = validate_framework_version_subpolicy_data(subpolicy_data, 0, i)
            validated_subpolicies.append(validated_subpolicy)
        
        validated['subpolicies'] = validated_subpolicies
    else:
        validated['subpolicies'] = []

    # Validate new subpolicies if present
    if 'new_subpolicies' in data:
        if not isinstance(data['new_subpolicies'], list):
            raise ValidationError(f"New subpolicies must be a list")
        
        validated_new_subpolicies = []
        for i, subpolicy_data in enumerate(data['new_subpolicies']):
            if not isinstance(subpolicy_data, dict):
                raise ValidationError(f"New subpolicy at index {i} must be a JSON object")
            
            validated_subpolicy = validate_framework_version_new_subpolicy_data(subpolicy_data, 0, i)
            validated_new_subpolicies.append(validated_subpolicy)
        
        validated['new_subpolicies'] = validated_new_subpolicies
    else:
        validated['new_subpolicies'] = []

    # Validate new policies if present
    if 'new_policies' in data:
        if not isinstance(data['new_policies'], list):
            raise ValidationError("New policies must be a list")
        
        validated_new_policies = []
        for i, policy_data in enumerate(data['new_policies']):
            if not isinstance(policy_data, dict):
                raise ValidationError(f"New policy at index {i} must be a JSON object")
            
            validated_policy = validate_framework_version_new_policy_data(policy_data, i)
            validated_new_policies.append(validated_policy)
        
        validated['new_policies'] = validated_new_policies
    else:
        validated['new_policies'] = []
    
    return validated 