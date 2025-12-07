from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from datetime import datetime, date
from django.shortcuts import get_object_or_404
import traceback
from ...models import Policy, PolicyApproval, SubPolicy, PolicyVersion, Framework, Users
from ..validators.framework_validator import ValidationError, validate_policy_version_data
from ...utils import send_log, get_client_ip

# RBAC Permission imports - Add comprehensive RBAC permissions
from ...rbac.permissions import (
    PolicyCreatePermission, PolicyViewPermission,
    PolicyApprovePermission, PolicyEditPermission, PolicyVersioningPermission
)


@api_view(['POST'])
@permission_classes([PolicyVersioningPermission])  # RBAC: Require PolicyVersioningPermission for creating policy versions
def create_policy_version(request, policy_id):
    """
    Create a new version of a policy with its subpolicies.
    Supports both major and minor versioning.
    
    Expected request data:
    - version_type: 'major' or 'minor' (default: 'minor')
    - Other policy data...
    
    This is used from the Versioning.vue component.
    """
    print(f"DEBUG: Received version creation request for policy {policy_id}")
    print(f"DEBUG: Request data: {request.data}")
    print(f"DEBUG: Request user: {getattr(request.user, 'username', 'Anonymous')}")
    
    # Log policy version creation attempt
    send_log(
        module="Policy",
        actionType="VERSION_CREATE",
        description=f"Creating new version for policy {policy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Import security modules
        from django.utils.html import escape as escape_html
        import shlex
        import re
        
        # Validate request data
        try:
            policy_data = validate_policy_version_data(request.data)
        except ValidationError as e:
            # Log validation error
            send_log(
                module="Policy",
                actionType="VERSION_CREATE_FAILED",
                description=f"Policy version validation failed: {str(e)}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request)
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        print(f"DEBUG: Starting policy version creation for policy ID: {policy_id}")
        print(f"DEBUG: Request headers: {request.headers}")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request data: {policy_data}")
        
        # Get the original policy - use get_object_or_404 for better error handling
        original_policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Verify policy exists and is active
        if original_policy.ActiveInactive != 'Active':
            print(f"DEBUG: Policy with ID {policy_id} is not active, status: {original_policy.ActiveInactive}")
            
            # Log inactive policy error
            send_log(
                module="Policy",
                actionType="VERSION_CREATE_FAILED",
                description=f"Cannot version inactive policy {policy_id}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request),
                additionalInfo={"policy_status": original_policy.ActiveInactive}
            )
            
            return Response({"error": "Only active policies can be versioned"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract version type from request data (default to 'minor')
        version_type = request.data.get('version_type', 'minor').lower()
        if version_type not in ['major', 'minor']:
            # Log invalid version type error
            send_log(
                module="Policy",
                actionType="VERSION_CREATE_FAILED",
                description=f"Invalid version type '{version_type}' for policy {policy_id}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request),
                additionalInfo={"version_type": version_type}
            )
            return Response({"error": "version_type must be 'major' or 'minor'"}, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"DEBUG: Version type: {version_type}")
        
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
        safe_policy_name = escape_html(policy_data.get('PolicyName', 'unnamed'))
        print(f"DEBUG: Received policy data: {safe_policy_name}")
        
        # Validate policy name - already validated
        policy_name = policy_data.get('PolicyName')
        
        # Start database transaction
        with transaction.atomic():
            print(f"DEBUG: Started transaction for policy version creation")
            
            # Enhanced version calculation logic with major/minor support
            current_version = str(original_policy.CurrentVersion).strip()
            print(f"DEBUG: Current version: {current_version}")
            
            if version_type == 'major':
                # Major version increment: 1.0 -> 2.0, 1.5 -> 2.0, 2.3 -> 3.0
                try:
                    current_major = int(float(current_version.split('.')[0]))
                    new_version = f"{current_major + 1}.0"
                    print(f"DEBUG: Major version increment: {current_version} -> {new_version}")
                except (ValueError, IndexError) as e:
                    print(f"ERROR: Invalid current version format: {current_version}, error: {str(e)}")
                    
                    # Log version calculation error
                    send_log(
                        module="Policy",
                        actionType="VERSION_CREATE_FAILED",
                        description=f"Invalid current policy version for major increment: {current_version}",
                        userId=getattr(request.user, 'id', None),
                        userName=getattr(request.user, 'username', 'Anonymous'),
                        entityType="Policy",
                        entityId=policy_id,
                        logLevel="ERROR",
                        ipAddress=get_client_ip(request),
                        additionalInfo={"current_version": current_version, "version_type": "major", "error": str(e)}
                    )
                    
                    return Response({"error": f"Invalid current version format: {current_version}"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Minor version increment: 1.0 -> 1.1, 1.5 -> 1.6  
                try:
                    current_version_float = float(current_version)
                    new_version_float = round(current_version_float + 0.1, 1)
                    new_version = str(new_version_float)
                    print(f"DEBUG: Policy minor version increment: {current_version} -> {new_version}")
                except ValueError as e:
                    print(f"ERROR: Invalid current policy version format: {current_version}, error: {str(e)}")
                    
                    # Log version calculation error
                    send_log(
                        module="Policy",
                        actionType="VERSION_CREATE_FAILED",
                        description=f"Invalid current policy version for minor increment: {current_version}",
                        userId=getattr(request.user, 'id', None),
                        userName=getattr(request.user, 'username', 'Anonymous'),
                        entityType="Policy",
                        entityId=policy_id,
                        logLevel="ERROR",
                        ipAddress=get_client_ip(request),
                        additionalInfo={"current_version": current_version, "version_type": "minor", "error": str(e)}
                    )
                    
                    return Response({"error": f"Invalid current policy version format: {current_version}"}, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"DEBUG: Creating new policy with version: {new_version}")
            
            # Handle Reviewer field - can be either UserId or UserName
            reviewer_input = policy_data.get('Reviewer')
            reviewer_name = None
            reviewer_id = None
            if reviewer_input:
                # First check if it's a numeric UserId
                try:
                    reviewer_id = int(reviewer_input)
                    user_obj = Users.objects.filter(UserId=reviewer_id).first()
                    if user_obj:
                        reviewer_name = user_obj.UserName
                except (ValueError, TypeError):
                    # If not numeric, treat as UserName directly
                    reviewer_name = str(reviewer_input)
                    # Verify the username exists and get the UserId
                    user_obj = Users.objects.filter(UserName=reviewer_name).first()
                    if user_obj:
                        reviewer_id = user_obj.UserId
                    else:
                        print(f"DEBUG: Reviewer username '{reviewer_name}' not found, using original policy reviewer")
                        reviewer_name = original_policy.Reviewer
                        # Get the original reviewer's UserId
                        orig_user_obj = Users.objects.filter(UserName=original_policy.Reviewer).first()
                        reviewer_id = orig_user_obj.UserId if orig_user_obj else None
                except Exception as e:
                    print(f"DEBUG: Error resolving reviewer: {str(e)}")
                    reviewer_name = original_policy.Reviewer
                    # Get the original reviewer's UserId
                    orig_user_obj = Users.objects.filter(UserName=original_policy.Reviewer).first()
                    reviewer_id = orig_user_obj.UserId if orig_user_obj else None
            
            if not reviewer_name:
                reviewer_name = original_policy.Reviewer  # fallback to existing username
                # Get the original reviewer's UserId
                orig_user_obj = Users.objects.filter(UserName=original_policy.Reviewer).first()
                reviewer_id = orig_user_obj.UserId if orig_user_obj else None
            
            # Security: Sanitize policy data before database storage (Django ORM provides SQL injection protection)
            new_policy = Policy.objects.create(
                FrameworkId=original_policy.FrameworkId,
                PolicyName=escape_html(policy_name),
                PolicyDescription=escape_html(policy_data.get('PolicyDescription', original_policy.PolicyDescription)),
                Status='Under Review',
                StartDate=policy_data.get('StartDate', original_policy.StartDate),
                EndDate=policy_data.get('EndDate', original_policy.EndDate),
                Department=escape_html(policy_data.get('Department', original_policy.Department)),
                CreatedByName=escape_html(policy_data.get('CreatedByName', original_policy.CreatedByName)),
                CreatedByDate=date.today(),
                Applicability=escape_html(policy_data.get('Applicability', original_policy.Applicability)),
                DocURL=policy_data.get('DocURL', original_policy.DocURL),  # Note: If used in shell commands, apply secure_url_for_shell()
                Scope=escape_html(policy_data.get('Scope', original_policy.Scope)),
                Objective=escape_html(policy_data.get('Objective', original_policy.Objective)),
                Identifier=escape_html(policy_data.get('Identifier', original_policy.Identifier)),
                PermanentTemporary=policy_data.get('PermanentTemporary', original_policy.PermanentTemporary),
                ActiveInactive='Inactive',  # New versions are inactive and go for approval
                Reviewer=escape_html(reviewer_name),  # Save UserName here
                CoverageRate=policy_data.get('CoverageRate', original_policy.CoverageRate),
                CurrentVersion=new_version,
                PolicyType=escape_html(policy_data.get('PolicyType', original_policy.PolicyType)),
                PolicyCategory=escape_html(policy_data.get('PolicyCategory', original_policy.PolicyCategory)),
                PolicySubCategory=escape_html(policy_data.get('PolicySubCategory', original_policy.PolicySubCategory)),
                Entities=policy_data.get('Entities', original_policy.Entities)
            )
            
            print(f"DEBUG: Created new policy with ID: {new_policy.PolicyId}")
            
            # Log successful policy version creation
            send_log(
                module="Policy",
                actionType="VERSION_CREATE_SUCCESS",
                description=f"Policy version {new_version} created successfully",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=new_policy.PolicyId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "original_policy_id": policy_id,
                    "new_policy_id": new_policy.PolicyId,
                    "version": new_version,
                    "reviewer": new_policy.Reviewer
                }
            )
            
            # Get original PolicyVersion to link new version
            original_policy_version = PolicyVersion.objects.filter(
                PolicyId=original_policy,
                Version=str(original_policy.CurrentVersion)
            ).first()
            
            if not original_policy_version:
                print(f"WARNING: No PolicyVersion found for PolicyId={original_policy.PolicyId} and Version={original_policy.CurrentVersion}")
                # Create a fallback version record for linking
                original_policy_version = PolicyVersion.objects.filter(
                    PolicyId=original_policy
                ).first()
            
            # Create new PolicyVersion linked to previous
            policy_version = PolicyVersion.objects.create(
                PolicyId=new_policy,
                Version=new_version,
                PolicyName=new_policy.PolicyName,
                CreatedBy=new_policy.CreatedByName,
                CreatedDate=new_policy.CreatedByDate,
                PreviousVersionId=original_policy_version.VersionId if original_policy_version else None
            )
            
            print(f"DEBUG: Created policy version entry with ID: {policy_version.VersionId}")
            
            # Handle subpolicy customizations and new subpolicies
            subpolicy_customizations = {}
            subpolicies_to_exclude = []
            
            if 'subpolicies' in policy_data:
                subpolicies_count = len(policy_data.get('subpolicies', []))
                print(f"DEBUG: Processing {subpolicies_count} existing subpolicies")
                
                # Log subpolicy processing start
                send_log(
                    module="Policy",
                    actionType="VERSION_PROCESS_SUBPOLICIES",
                    description=f"Processing {subpolicies_count} existing subpolicies for policy version {new_version}",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="Policy",
                    entityId=new_policy.PolicyId,
                    ipAddress=get_client_ip(request),
                    additionalInfo={"subpolicies_count": subpolicies_count}
                )
                for sp_data in policy_data.get('subpolicies', []):
                    if 'original_subpolicy_id' in sp_data:
                        sp_id = sp_data.get('original_subpolicy_id')
                        if sp_data.get('exclude', False):
                            subpolicies_to_exclude.append(sp_id)
                        else:
                            if 'Identifier' not in sp_data:
                                return Response({
                                    'error': 'Identifier is required for modified subpolicies',
                                    'subpolicy_id': sp_id
                                }, status=status.HTTP_400_BAD_REQUEST)
                            subpolicy_customizations[sp_id] = sp_data
            
            # Process original subpolicies with customizations
            original_subpolicies = SubPolicy.objects.filter(PolicyId=original_policy)
            for original_subpolicy in original_subpolicies:
                if original_subpolicy.SubPolicyId in subpolicies_to_exclude:
                        continue
                custom_data = subpolicy_customizations.get(original_subpolicy.SubPolicyId, {})
                
                # Security: Sanitize subpolicy data before database storage
                new_subpolicy_data = {
                    'PolicyId': new_policy,
                    'SubPolicyName': escape_html(custom_data.get('SubPolicyName', original_subpolicy.SubPolicyName)),
                    'CreatedByName': escape_html(custom_data.get('CreatedByName') or new_policy.CreatedByName),
                    'CreatedByDate': new_policy.CreatedByDate,
                    'Identifier': escape_html(custom_data.get('Identifier', original_subpolicy.Identifier)),
                    'Description': escape_html(custom_data.get('Description', original_subpolicy.Description)),
                    'Status': 'Under Review',
                    'PermanentTemporary': custom_data.get('PermanentTemporary', original_subpolicy.PermanentTemporary),
                    'Control': escape_html(custom_data.get('Control', original_subpolicy.Control))
                }
                
                SubPolicy.objects.create(**new_subpolicy_data)
            
            # Add new subpolicies if any
            if 'new_subpolicies' in policy_data:
                new_subpolicies_count = len(policy_data.get('new_subpolicies', []))
                print(f"DEBUG: Processing {new_subpolicies_count} new subpolicies")
                
                # Log new subpolicies processing start
                send_log(
                    module="Policy",
                    actionType="VERSION_PROCESS_NEW_SUBPOLICIES",
                    description=f"Processing {new_subpolicies_count} new subpolicies for policy version {new_version}",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="Policy",
                    entityId=new_policy.PolicyId,
                    ipAddress=get_client_ip(request),
                    additionalInfo={"new_subpolicies_count": new_subpolicies_count}
                )
                for new_subpolicy_data in policy_data.get('new_subpolicies', []):
                    # Security: Sanitize new subpolicy data before database storage
                    subpolicy = new_subpolicy_data.copy()
                    subpolicy['PolicyId'] = new_policy
                    if 'CreatedByName' not in subpolicy or not subpolicy['CreatedByName']:
                        subpolicy['CreatedByName'] = escape_html(new_policy.CreatedByName)
                    else:
                        subpolicy['CreatedByName'] = escape_html(subpolicy['CreatedByName'])
                    subpolicy['CreatedByDate'] = new_policy.CreatedByDate
                    subpolicy['Status'] = 'Under Review'
                    
                    # Escape other text fields
                    if 'SubPolicyName' in subpolicy:
                        subpolicy['SubPolicyName'] = escape_html(subpolicy['SubPolicyName'])
                    if 'Identifier' in subpolicy:
                        subpolicy['Identifier'] = escape_html(subpolicy['Identifier'])
                    if 'Description' in subpolicy:
                        subpolicy['Description'] = escape_html(subpolicy['Description'])
                    if 'Control' in subpolicy:
                        subpolicy['Control'] = escape_html(subpolicy['Control'])
                    
                    SubPolicy.objects.create(**subpolicy)
            
            # Handle any new policies if specified (from policy.py functionality)
            created_policies = []
            if 'new_policies' in policy_data:
                new_policies_count = len(policy_data.get('new_policies', []))
                
                # Log new policies processing start
                send_log(
                    module="Policy",
                    actionType="VERSION_PROCESS_NEW_POLICIES",
                    description=f"Processing {new_policies_count} new policies for policy version {new_version}",
                    userId=getattr(request.user, 'id', None),
                    userName=getattr(request.user, 'username', 'Anonymous'),
                    entityType="Policy",
                    entityId=new_policy.PolicyId,
                    ipAddress=get_client_ip(request),
                    additionalInfo={"new_policies_count": new_policies_count}
                )
                for new_policy_data in policy_data.get('new_policies', []):
                    # Security: Sanitize new policy data before database storage
                    subpolicies_data = new_policy_data.pop('subpolicies', [])
                    policy_data_new = new_policy_data.copy()
                    policy_data_new['FrameworkId'] = original_policy.FrameworkId
                    policy_data_new['CurrentVersion'] = new_version
                    policy_data_new['Status'] = 'Under Review'
                    policy_data_new['ActiveInactive'] = 'Inactive'
                    if 'CreatedByName' not in policy_data_new or not policy_data_new['CreatedByName']:
                        policy_data_new['CreatedByName'] = escape_html(original_policy.CreatedByName)
                    else:
                        policy_data_new['CreatedByName'] = escape_html(policy_data_new['CreatedByName'])
                    policy_data_new['CreatedByDate'] = date.today()
                    
                    # Escape other text fields in new policy data
                    text_fields = ['PolicyName', 'PolicyDescription', 'Department', 'Applicability', 
                                   'Scope', 'Objective', 'Identifier', 'Reviewer', 'PolicyType', 
                                   'PolicyCategory', 'PolicySubCategory']
                    for field in text_fields:
                        if field in policy_data_new and policy_data_new[field]:
                            policy_data_new[field] = escape_html(policy_data_new[field])
                    
                    created_policy = Policy.objects.create(**policy_data_new)
                    created_policies.append(created_policy)
                    
                    PolicyVersion.objects.create(
                        PolicyId=created_policy,
                        Version=new_version,
                        PolicyName=created_policy.PolicyName,
                        CreatedBy=created_policy.CreatedByName,
                        CreatedDate=created_policy.CreatedByDate,
                        PreviousVersionId=None
                    )
                    
                    for subpolicy_data in subpolicies_data:
                        # Security: Sanitize subpolicy data for new policies
                        subpolicy = subpolicy_data.copy()
                        subpolicy['PolicyId'] = created_policy
                        if 'CreatedByName' not in subpolicy or not subpolicy['CreatedByName']:
                            subpolicy['CreatedByName'] = escape_html(created_policy.CreatedByName)
                        else:
                            subpolicy['CreatedByName'] = escape_html(subpolicy['CreatedByName'])
                        subpolicy['CreatedByDate'] = created_policy.CreatedByDate
                        subpolicy['Status'] = 'Under Review'
                        
                        # Escape text fields in subpolicy data
                        subpolicy_text_fields = ['SubPolicyName', 'Identifier', 'Description', 'Control']
                        for field in subpolicy_text_fields:
                            if field in subpolicy and subpolicy[field]:
                                subpolicy[field] = escape_html(subpolicy[field])
                        
                        SubPolicy.objects.create(**subpolicy)
            
            # Create policy approval entry for the new version
            print(f"DEBUG: Calling create_policy_approval_for_version for new policy ID: {new_policy.PolicyId}")
            approval_created = create_policy_approval_for_version(new_policy.PolicyId, request)
            print(f"DEBUG: Policy approval creation result: {approval_created}")
            
            # Verify the approval was created
            policy_approval = PolicyApproval.objects.filter(PolicyId=new_policy).first()
            if policy_approval:
                print(f"DEBUG: Verified policy approval was created with ID: {policy_approval.ApprovalId}")
            else:
                print(f"WARNING: Could not verify policy approval creation")
            
            # Prepare response
            response_data = {
                'message': 'New policy version created successfully',
                'PolicyId': new_policy.PolicyId,
                'PolicyName': new_policy.PolicyName,
                'PreviousVersion': current_version,
                'NewVersion': new_version,
                'VersionType': version_type,
                'FrameworkId': new_policy.FrameworkId.FrameworkId if new_policy.FrameworkId else None,
                'Identifier': new_policy.Identifier,
                'Status': new_policy.Status
            }
            
            if created_policies:
                response_data['policies'] = [{
                    'PolicyId': p.PolicyId,
                    'PolicyName': p.PolicyName,
                    'Identifier': p.Identifier,
                    'Version': p.CurrentVersion
                } for p in created_policies]
            
            # Send notification if reviewer is assigned
            if reviewer_name and reviewer_id:
                try:
                    from ...routes.Global.notification_service import NotificationService
                    notification_service = NotificationService()
                    
                    # First get the reviewer's UserId from their username
                    reviewer = Users.objects.filter(UserName=reviewer_name).first()
                    if reviewer:
                        reviewer_id = reviewer.UserId
                        # Now get the email using the correct UserId
                        reviewer_email = notification_service.get_user_email(reviewer_id)
                        
                        if reviewer_email:
                            # Security: XSS Protection - Escape HTML content before building email template
                            notification_data = {
                                'notification_type': 'policyNewVersion',
                                'email': reviewer_email,
                                'email_type': 'gmail',
                                'template_data': [
                                    escape_html(reviewer_name),  # Escape reviewer name for HTML context
                                    escape_html(new_policy.PolicyName),  # Escape policy name for HTML context
                                    new_version,  # Version number is safe
                                    escape_html(new_policy.CreatedByName)  # Escape submitter name for HTML context
                                ]
                            }
                            notification_service.send_multi_channel_notification(notification_data)
                        else:
                            print(f"No email found for reviewer with ID: {reviewer_id}")
                    else:
                        print(f"No user found with username: {reviewer_name}")
                except Exception as e:
                    print(f"Failed to send notification: {str(e)}")
            
            # Log successful policy version completion
            send_log(
                module="Policy",
                actionType="VERSION_CREATE_COMPLETE",
                description=f"Policy version {new_version} created and configured successfully",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=new_policy.PolicyId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "policy_name": new_policy.PolicyName,
                    "new_version": new_version,
                    "previous_version": current_version,
                    "version_type": version_type,
                    "subpolicies_processed": subpolicies_count if 'subpolicies_count' in locals() else 0,
                    "new_subpolicies_added": new_subpolicies_count if 'new_subpolicies_count' in locals() else 0,
                    "new_policies_added": new_policies_count if 'new_policies_count' in locals() else 0,
                    "status": new_policy.Status
                }
            )
            
            # Note: Previous policy version will be set to inactive only when this new version is approved
            # This allows both versions to be active during the approval process
            
            return Response(response_data, status=status.HTTP_201_CREATED)
    
    except Policy.DoesNotExist:
        print(f"ERROR: Original policy with ID {policy_id} not found")
        
        # Log policy not found error
        send_log(
            module="Policy",
            actionType="VERSION_CREATE_FAILED",
            description=f"Original policy {policy_id} not found",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        
        return Response({"error": "Original policy not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"ERROR in create_policy_version: {str(e)}")
        traceback.print_exc()
        
        # Log general exception
        send_log(
            module="Policy",
            actionType="VERSION_CREATE_FAILED",
            description=f"Unexpected error creating policy version: {str(e)}",
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
        return Response({'error': 'Error creating new policy version', 'details': error_info}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_policy_approval_for_version(policy_id, request=None):
    """
    Helper function to create a policy approval entry for a new policy version
    """
    try:
        # Import security modules
        from django.utils.html import escape as escape_html
        
        # Get the policy
        policy = Policy.objects.get(PolicyId=policy_id)
        
        # Get the corresponding user version approval for this policy
        try:
            # First get the policy version to determine which user version to look for
            policy_version = PolicyVersion.objects.get(PolicyId=policy_id)
            version_number = policy_version.Version  # e.g. "1.2"
            
            print(f"DEBUG: Looking for approval with version {version_number}")
            
            # Find the corresponding user version approval
            latest_approval = PolicyApproval.objects.filter(
                PolicyId__PolicyName=policy.PolicyName,
                Version='u1'  # Always get the initial user version
            ).first()
            
            if latest_approval:
                # Use the same user ID and reviewer ID from the user version
                user_id = latest_approval.UserId
                reviewer_id = latest_approval.ReviewerId
                print(f"DEBUG: Found matching approval - Using user ID {user_id} and reviewer ID {reviewer_id}")
            else:
                print(f"DEBUG: No matching user version approval found for policy {policy.PolicyName}")
        except Exception as e:
            print(f"DEBUG: Error finding matching approval: {str(e)}")
        else:
            # If no previous approval exists, get IDs from session/policy
            user_id = None
            if request and hasattr(request, 'session'):
                user_id = request.session.get('user_id')
                print(f"DEBUG: Got user ID {user_id} from session")
            
            if not user_id:
                user_id = request.session.get('grc_user_id') if request and hasattr(request, 'session') else None
                print(f"DEBUG: Fallback - Got user ID {user_id} from grc_user_id")
            
            if not user_id:
                user_obj = Users.objects.filter(UserName=policy.CreatedByName).first()
                user_id = user_obj.UserId if user_obj else None
                print(f"DEBUG: Final fallback - Got user ID {user_id} from CreatedByName: {policy.CreatedByName}")
            
            # Get reviewer ID from Reviewer name
            reviewer_obj = Users.objects.filter(UserName=policy.Reviewer).first()
            reviewer_id = reviewer_obj.UserId if reviewer_obj else None
        
        print(f"DEBUG: Using user ID: {user_id} from logged in user or CreatedByName: {policy.CreatedByName}")
        print(f"DEBUG: Using reviewer ID: {reviewer_id} from Reviewer: {policy.Reviewer}")
        
        # Security: Escape policy name for safe logging (prevents log injection)
        safe_policy_name = escape_html(policy.PolicyName)
        print(f"DEBUG: Starting policy approval creation for policy ID: {policy_id}, Name: {safe_policy_name}")
        
        # Security: XSS Protection - Escape subpolicy text fields before adding to approval data
        subpolicies_data = []
        created_subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        
        for subpolicy in created_subpolicies:
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
        
        # Security: XSS Protection - Escape framework text fields
        framework_info = {}
        if policy.FrameworkId:
            framework = policy.FrameworkId
            framework_info = {
                "FrameworkId": framework.FrameworkId,
                "FrameworkName": escape_html(framework.FrameworkName),
                "Category": escape_html(framework.Category)
            }
        
        # Security: XSS Protection - Escape all text fields before storing in extracted_data
        extracted_data = {
            "PolicyId": policy.PolicyId,
            "PolicyName": escape_html(policy.PolicyName),
            "PolicyDescription": escape_html(policy.PolicyDescription),
            "StartDate": policy.StartDate.isoformat() if policy.StartDate else None,
            "EndDate": policy.EndDate.isoformat() if policy.EndDate else None,
            "Department": escape_html(policy.Department),
            "CreatedByName": escape_html(policy.CreatedByName),
            "CreatedByDate": policy.CreatedByDate.isoformat() if policy.CreatedByDate else None,
            "Applicability": escape_html(policy.Applicability),
            "DocURL": escape_html(policy.DocURL),
            "Scope": escape_html(policy.Scope),
            "Objective": escape_html(policy.Objective),
            "Identifier": escape_html(policy.Identifier),
            "Status": policy.Status,
            "PermanentTemporary": policy.PermanentTemporary,
            "ActiveInactive": policy.ActiveInactive,
            "type": "policy",
            "source": "versioning",
            "reviewer": escape_html(policy.Reviewer),
            "CoverageRate": policy.CoverageRate,
            "CurrentVersion": policy.CurrentVersion,
            "subpolicies": subpolicies_data,
            "totalSubpolicies": len(subpolicies_data),
            "framework": framework_info
        }
        
        # Get policy version info
        policy_version = PolicyVersion.objects.filter(PolicyId=policy).first()
        if policy_version:
            extracted_data["Version"] = policy_version.Version
            extracted_data["PreviousVersionId"] = policy_version.PreviousVersionId
        
        print(f"DEBUG: Prepared extracted data for policy approval")
        
        # Create the policy approval with direct SQL debug to verify it's working
        try:
            if not user_id or not reviewer_id:
                print(f"WARNING: Missing IDs for policy approval creation - user_id: {user_id}, reviewer_id: {reviewer_id}")
                
                # If we still don't have IDs, get them from the original policy
                if not user_id:
                    user_obj = Users.objects.filter(UserName=policy.CreatedByName).first()
                    user_id = user_obj.UserId if user_obj else None
                    print(f"DEBUG: Final attempt - Got user ID {user_id} from policy CreatedByName")
                
                if not reviewer_id:
                    reviewer_obj = Users.objects.filter(UserName=policy.Reviewer).first()
                    reviewer_id = reviewer_obj.UserId if reviewer_obj else None
                    print(f"DEBUG: Final attempt - Got reviewer ID {reviewer_id} from policy Reviewer")
            
            print(f"DEBUG: Creating PolicyApproval with user_id: {user_id}, reviewer_id: {reviewer_id}")
            
            # Determine the version type (u1 or r1) based on the policy version
            version_type = "r1" if hasattr(policy, 'reviewer') else "u1"
            
            approval = PolicyApproval.objects.create(
                PolicyId=policy,
                ExtractedData=extracted_data,
                UserId=user_id,
                ReviewerId=reviewer_id,
                Version=version_type,
                ApprovedNot=None,  # Not yet approved
                FrameworkId=policy.FrameworkId
            )
            print(f"DEBUG: Successfully created policy approval with ID: {approval.ApprovalId}")
            
            # Send notification to reviewer if available
            if reviewer_id:
                try:
                    reviewer_user = Users.objects.get(UserId=reviewer_id)
                    reviewer_email = reviewer_user.Email
                    
                    if reviewer_email:
                        from ...routes.Global.notification_service import NotificationService
                        notification_service = NotificationService()
                        notification_data = {
                            'notification_type': 'policyVersionSubmitted',
                            'email': reviewer_email,
                            'email_type': 'gmail',
                            'template_data': [
                                policy.PolicyName,
                                reviewer_user.UserName,
                                policy.CreatedByName,
                                str(policy.CurrentVersion)
                            ]
                        }
                        notification_result = notification_service.send_multi_channel_notification(notification_data)
                        print(f"DEBUG: Policy version approval notification sent: {notification_result}")
                    else:
                        print(f"DEBUG: No email found for reviewer ID: {reviewer_id}")
                except Users.DoesNotExist:
                    print(f"DEBUG: Reviewer user not found with ID: {reviewer_id}")
                except Exception as e:
                    print(f"DEBUG: Error sending policy version approval notification: {str(e)}")
            
            # Log successful policy approval creation
            send_log(
                module="Policy",
                actionType="VERSION_APPROVAL_CREATE_SUCCESS",
                description=f"Policy approval created successfully with ID {approval.ApprovalId}",
                userId=user_id,
                userName=policy.CreatedByName,
                entityType="Policy",
                entityId=policy_id,
                ipAddress=None,
                additionalInfo={"approval_id": approval.ApprovalId, "reviewer_id": reviewer_id}
            )
            
            # Verify the approval was created
            verification = PolicyApproval.objects.filter(PolicyId=policy).exists()
            print(f"DEBUG: Verification of policy approval creation: {verification}")
            
            return True
        except Exception as create_error:
            print(f"ERROR creating policy approval record: {str(create_error)}")
            
            # Log policy approval creation failure
            send_log(
                module="Policy",
                actionType="VERSION_APPROVAL_CREATE_FAILED",
                description=f"Failed to create policy approval: {str(create_error)}",
                userId=None,
                userName="System",
                entityType="Policy",
                entityId=policy_id,
                logLevel="ERROR",
                ipAddress=None,
                additionalInfo={"error": str(create_error)}
            )
            
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"ERROR in create_policy_approval_for_version: {str(e)}")
        
        # Log general exception in policy approval creation
        send_log(
            module="Policy",
            actionType="VERSION_APPROVAL_CREATE_FAILED",
            description=f"Unexpected error in policy approval creation: {str(e)}",
            userId=None,
            userName="System",
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=None,
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        traceback.print_exc()
        return False


@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing policy versions
def get_policy_versions(request, policy_id=None):
    """
    Get all versions of a policy by its Identifier
    """
    # Log policy versions retrieval attempt
    send_log(
        module="Policy",
        actionType="VIEW_POLICY_VERSIONS",
        description=f"Retrieving policy versions for policy {policy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request)
    )
    
    try:
        if policy_id:
            # Get the policy to find its identifier
            policy = Policy.objects.get(PolicyId=policy_id)
            identifier = policy.Identifier
            
            # Find all policies with this identifier
            policies = Policy.objects.filter(Identifier=identifier).order_by('-PolicyId')
            
            # Get the version information for each policy
            versions_data = []
            for pol in policies:
                version_info = PolicyVersion.objects.filter(PolicyId=pol).first()
                if version_info:
                    versions_data.append({
                        "PolicyId": pol.PolicyId,
                        "PolicyName": pol.PolicyName,
                        "Version": version_info.Version,
                        "CreatedBy": version_info.CreatedBy,
                        "CreatedDate": version_info.CreatedDate.isoformat() if version_info.CreatedDate else None,
                        "Status": pol.Status,
                        "ActiveInactive": pol.ActiveInactive
                    })
                else:
                    # Handle policies without version information
                    versions_data.append({
                        "PolicyId": pol.PolicyId,
                        "PolicyName": pol.PolicyName,
                        "Version": pol.CurrentVersion,
                        "CreatedBy": pol.CreatedByName,
                        "CreatedDate": pol.CreatedByDate.isoformat() if pol.CreatedByDate else None,
                        "Status": pol.Status,
                        "ActiveInactive": pol.ActiveInactive
                    })
            
            # Log successful policy versions retrieval
            send_log(
                module="Policy",
                actionType="VIEW_POLICY_VERSIONS_SUCCESS",
                description=f"Successfully retrieved {len(versions_data)} policy versions",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                ipAddress=get_client_ip(request),
                additionalInfo={"versions_count": len(versions_data)}
            )
            
            return Response(versions_data, status=status.HTTP_200_OK)
        else:
            # Log missing policy ID error
            send_log(
                module="Policy",
                actionType="VIEW_POLICY_VERSIONS_FAILED",
                description="Policy ID is required but not provided",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=None,
                logLevel="WARNING",
                ipAddress=get_client_ip(request)
            )
            return Response({"error": "Policy ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Policy.DoesNotExist:
        # Log policy not found error
        send_log(
            module="Policy",
            actionType="VIEW_POLICY_VERSIONS_FAILED",
            description=f"Policy {policy_id} not found",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="WARNING",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Log general exception
        send_log(
            module="Policy",
            actionType="VIEW_POLICY_VERSIONS_FAILED",
            description=f"Error retrieving policy versions: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing all policy versions
def get_all_policy_versions(request):
    """
    Get all policy versions in the system
    """
    # Log policy versions retrieval attempt
    send_log(
        module="Policy",
        actionType="VIEW_ALL_POLICY_VERSIONS",
        description="Retrieving all policy versions",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=None,
        ipAddress=get_client_ip(request)
    )
    
    try:
        print(f"DEBUG: Starting get_all_policy_versions")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request params: {request.GET}")
        
        # Get all policy versions
        policy_versions = PolicyVersion.objects.all().order_by('-CreatedDate')
        print(f"DEBUG: Found {policy_versions.count()} policy versions")
        
        versions_data = []
        for version in policy_versions:
            policy = version.PolicyId
            if policy:
                versions_data.append({
                    "VersionId": version.VersionId,
                    "PolicyId": policy.PolicyId,
                    "PolicyName": policy.PolicyName,
                    "Version": version.Version,
                    "PreviousVersionId": version.PreviousVersionId,
                    "CreatedBy": version.CreatedBy,
                    "CreatedDate": version.CreatedDate.isoformat() if version.CreatedDate else None,
                    "Status": policy.Status,
                    "ActiveInactive": policy.ActiveInactive
                })
        
        print(f"DEBUG: Returning {len(versions_data)} policy versions")
        
        # Log successful retrieval
        send_log(
            module="Policy",
            actionType="VIEW_ALL_POLICY_VERSIONS_SUCCESS",
            description=f"Successfully retrieved {len(versions_data)} policy versions",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=None,
            ipAddress=get_client_ip(request),
            additionalInfo={"versions_count": len(versions_data)}
        )
        
        return Response(versions_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"ERROR in get_all_policy_versions: {str(e)}")
        
        # Log error
        send_log(
            module="Policy",
            actionType="VIEW_ALL_POLICY_VERSIONS_FAILED",
            description=f"Error retrieving all policy versions: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=None,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e)}
        )
        
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing rejected policy versions
def get_rejected_policy_versions(request, user_id=None):
    """
    Get all rejected policy versions for a specific user that can be edited and resubmitted
    """
    # Log rejected policy versions retrieval attempt
    send_log(
        module="Policy",
        actionType="VIEW_REJECTED_POLICY_VERSIONS",
        description=f"Retrieving rejected policy versions for user {user_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=None,
        ipAddress=get_client_ip(request),
        additionalInfo={"target_user_id": user_id}
    )
    
    try:
        if not user_id:
            user_id = request.GET.get('user_id', None)
            
        if not user_id:
            # Log missing user ID error
            send_log(
                module="Policy",
                actionType="VIEW_REJECTED_POLICY_VERSIONS_FAILED",
                description="User ID is required but not provided",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=None,
                logLevel="WARNING",
                ipAddress=get_client_ip(request)
            )
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get all policy approvals where:
        # 1. The approval is rejected (ApprovedNot=False)
        # 2. The version starts with 'r' (reviewer version)
        # 3. If user_id is provided, filter by UserId
        query_filters = {
            'ApprovedNot': False,
            'Version__startswith': 'r'
        }
        
        if user_id:
            query_filters['UserId'] = user_id
            
        rejections = PolicyApproval.objects.filter(**query_filters).order_by('-ApprovalId')
        
        # Group by PolicyId to get only the latest rejection for each policy
        policy_rejections = {}
        for rejection in rejections:
            if not rejection.PolicyId:
                continue
                
            policy_id = rejection.PolicyId.PolicyId
            if policy_id not in policy_rejections:
                policy_rejections[policy_id] = rejection
        
        # Format response
        rejected_policies = []
        for rejection in policy_rejections.values():
            policy = rejection.PolicyId
            if not policy:
                continue
                
            # Get version info - handle cases where version info might not exist
            try:
                version_info = PolicyVersion.objects.filter(PolicyId=policy).first()
                version = version_info.Version if version_info else policy.CurrentVersion
            except (AttributeError, Exception) as e:
                print(f"Error getting version info: {str(e)}")
                version = "Unknown"
                
            # Handle potential missing dates
            try:
                created_date = policy.CreatedByDate.isoformat() if policy.CreatedByDate else None
            except (AttributeError, Exception):
                created_date = None
                
            # Safely extract rejection reason
            try:
                rejection_reason = rejection.ExtractedData.get('policy_approval', {}).get('remarks', 'No reason provided')
            except (AttributeError, TypeError, Exception):
                rejection_reason = 'No reason provided'
            
            rejection_data = {
                "ApprovalId": rejection.ApprovalId,
                "PolicyId": policy.PolicyId,
                "PolicyName": policy.PolicyName,
                "Version": version,
                "Status": policy.Status,
                "CreatedByName": policy.CreatedByName,
                "CreatedDate": created_date,
                "ExtractedData": rejection.ExtractedData or {},
                "RejectionReason": rejection_reason
            }
            
            rejected_policies.append(rejection_data)
        
        # Log successful retrieval
        send_log(
            module="Policy",
            actionType="VIEW_REJECTED_POLICY_VERSIONS_SUCCESS",
            description=f"Successfully retrieved {len(rejected_policies)} rejected policy versions",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=None,
            ipAddress=get_client_ip(request),
            additionalInfo={"rejected_policies_count": len(rejected_policies), "target_user_id": user_id}
        )
        
        return Response(rejected_policies, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"ERROR in get_rejected_policy_versions: {str(e)}")
        
        # Log error
        send_log(
            module="Policy",
            actionType="VIEW_REJECTED_POLICY_VERSIONS_FAILED",
            description=f"Error retrieving rejected policy versions: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=None,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e), "target_user_id": user_id}
        )
        
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([PolicyEditPermission])  # RBAC: Require PolicyEditPermission for activating/deactivating policies
def activate_deactivate_policy(request, policy_id):
    """
    Activate or deactivate a policy with date-based scheduling logic.
    When activating a policy, all previous versions with the same Identifier will be deactivated.
    """
    # Import security modules for safe logging
    from django.utils.html import escape as escape_html
    import shlex
    
    action = request.data.get('action')
    
    # Log policy activation/deactivation attempt
    send_log(
        module="Policy",
        actionType="TOGGLE_POLICY_STATUS",
        description=f"Attempting to {action} policy {policy_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="Policy",
        entityId=policy_id,
        ipAddress=get_client_ip(request),
        additionalInfo={"action": action}
    )
    
    try:
        policy = Policy.objects.get(PolicyId=policy_id)
        
        if action == 'activate':
            # Use transaction to ensure atomicity
            with transaction.atomic():
                # Set policy to Active or Scheduled based on StartDate
                today = date.today()
                print(f"DEBUG: Policy Version Activation {policy_id} - Today: {today}, StartDate: {policy.StartDate} (type: {type(policy.StartDate)})")
                
                if policy.StartDate and policy.StartDate > today:
                    policy.ActiveInactive = 'Scheduled'
                    print(f"Set policy version {policy_id} to Scheduled status (StartDate: {policy.StartDate} > today: {today})")
                else:
                    policy.ActiveInactive = 'Active'
                    print(f"Set policy version {policy_id} to Active status (StartDate: {policy.StartDate} <= today: {today} or None)")
                
                policy.save()
                
                # When activating a policy, deactivate all previous versions
                deactivated_count = deactivate_previous_policy_versions_on_approval(policy)
                # Security: Escape policy name for safe logging (prevents log injection)
                safe_policy_name = escape_html(policy.PolicyName)
                print(f"Policy {policy_id} ({safe_policy_name}) set to {policy.ActiveInactive}. Deactivated {deactivated_count} previous versions.")
            
            # Log successful activation
            send_log(
                module="Policy",
                actionType="TOGGLE_POLICY_STATUS_SUCCESS",
                description=f"Policy {policy_id} successfully activated to {policy.ActiveInactive}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "action": "activate",
                    "new_status": policy.ActiveInactive,
                    "deactivated_previous_versions": deactivated_count
                }
            )
            
            return Response({
                "message": f"Policy updated to {policy.ActiveInactive} successfully. {deactivated_count} previous versions deactivated.",
                "PolicyId": policy.PolicyId,
                "ActiveInactive": policy.ActiveInactive,
                "deactivated_previous_versions": deactivated_count
            }, status=status.HTTP_200_OK)
            
        elif action == 'deactivate':
            policy.ActiveInactive = 'Inactive'
            policy.save()
            
            # Log successful deactivation
            send_log(
                module="Policy",
                actionType="TOGGLE_POLICY_STATUS_SUCCESS",
                description=f"Policy {policy_id} successfully deactivated",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                ipAddress=get_client_ip(request),
                additionalInfo={"action": "deactivate", "new_status": "Inactive"}
            )
            
            return Response({
                "message": "Policy deactivated successfully",
                "PolicyId": policy.PolicyId,
                "ActiveInactive": policy.ActiveInactive
            }, status=status.HTTP_200_OK)
        else:
            # Log invalid action error
            send_log(
                module="Policy",
                actionType="TOGGLE_POLICY_STATUS_FAILED",
                description=f"Invalid action '{action}' for policy {policy_id}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="Policy",
                entityId=policy_id,
                logLevel="WARNING",
                ipAddress=get_client_ip(request),
                additionalInfo={"action": action}
            )
            return Response({"error": "Invalid action. Use 'activate' or 'deactivate'"}, status=status.HTTP_400_BAD_REQUEST)
        
    except Policy.DoesNotExist:
        # Log policy not found error
        send_log(
            module="Policy",
            actionType="TOGGLE_POLICY_STATUS_FAILED",
            description=f"Policy {policy_id} not found for {action}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="WARNING",
            ipAddress=get_client_ip(request),
            additionalInfo={"action": action}
        )
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Log general exception
        send_log(
            module="Policy",
            actionType="TOGGLE_POLICY_STATUS_FAILED",
            description=f"Error toggling policy status: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="Policy",
            entityId=policy_id,
            logLevel="ERROR",
            ipAddress=get_client_ip(request),
            additionalInfo={"error": str(e), "action": action}
        )
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([PolicyApprovePermission])  # RBAC: Require PolicyApprovePermission for approving policy versions
def approve_policy_version(request, policy_id):
    """
    Approve a policy version and automatically deactivate all previous versions.
    This endpoint is specifically designed for the Versioning.vue component.
    """
    try:
        # Get the policy
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Get the latest policy approval
        latest_approval = PolicyApproval.objects.filter(
            PolicyId=policy,
            ApprovedNot__isnull=True  # Get the pending approval
        ).order_by('-ApprovalId').first()
        
        if not latest_approval:
            return Response({
                'error': 'No pending approval found for this policy'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start database transaction
        with transaction.atomic():
            # Update policy status
            policy.Status = 'Approved'
            today = date.today()
            
            if policy.StartDate and policy.StartDate > today:
                policy.ActiveInactive = 'Scheduled'
            else:
                policy.ActiveInactive = 'Active'
            
            policy.save()
            
            # Create new reviewer version with same user/reviewer IDs
            new_approval = PolicyApproval.objects.create(
                PolicyId=policy,
                ExtractedData=latest_approval.ExtractedData,
                UserId=latest_approval.UserId,  # Keep the same user ID
                ReviewerId=latest_approval.ReviewerId,  # Keep the same reviewer ID
                Version=f"r{int(latest_approval.Version[1:]) if latest_approval.Version[1:].isdigit() else 1}",
                ApprovedNot=True,
                ApprovedDate=today,
                FrameworkId=policy.FrameworkId
            )
            
            # Deactivate previous versions
            deactivated_count = deactivate_previous_policy_versions(policy)
            
            # Update subpolicies
            subpolicies = SubPolicy.objects.filter(PolicyId=policy)
            for subpolicy in subpolicies:
                subpolicy.Status = 'Approved'
                if hasattr(subpolicy, 'ActiveInactive'):
                    subpolicy.ActiveInactive = policy.ActiveInactive
                subpolicy.save()
            
            return Response({
                'message': 'Policy version approved successfully',
                'policy_id': policy_id,
                'status': policy.Status,
                'active_inactive': policy.ActiveInactive,
                'deactivated_count': deactivated_count,
                'approval_id': new_approval.ApprovalId,
                'version': new_approval.Version
            })
            
    except Exception as e:
        print(f"Error approving policy version: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


def update_policy_status_based_on_subpolicies(policy_id):
    """
    Update policy status based on its subpolicies statuses
    """
    try:
        policy = Policy.objects.get(PolicyId=policy_id)
        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
        
        # Check if any subpolicy is rejected
        has_rejected = False
        for subpolicy in subpolicies:
            if subpolicy.Status == 'Rejected':
                has_rejected = True
                break
        
        # Update policy status if any subpolicy is rejected
        if has_rejected:
            policy.Status = 'Rejected'
            policy.save()
            print(f"DEBUG: Updated policy {policy_id} status to Rejected due to rejected subpolicy")
            return True
        
        return False
    except Exception as e:
        print(f"ERROR updating policy status based on subpolicies: {str(e)}")
        return False


def deactivate_previous_policy_versions_on_approval(current_policy):
    """
    Deactivate all previous versions of a policy when a new version is approved.
    This function is specifically for use in the policy versioning workflow.
    
    Args:
        current_policy: The newly approved policy object
        
    Returns:
        int: Number of previous versions deactivated
    """
    # Import security modules for safe logging
    from django.utils.html import escape as escape_html
    
    # Security: Escape policy data for safe logging (prevents log injection)
    safe_policy_name = escape_html(current_policy.PolicyName)
    safe_identifier = escape_html(current_policy.Identifier)
    print(f"Policy versioning: Deactivating previous versions for policy: PolicyId={current_policy.PolicyId}, Name={safe_policy_name}, Identifier={safe_identifier}")
    
    if not current_policy.Identifier:
        print("Warning: Policy has no Identifier, cannot find previous versions")
        return 0
    
    try:
        # Find all policies with the same Identifier, excluding the current one
        previous_policies = Policy.objects.filter(
            Identifier=current_policy.Identifier
        ).exclude(
            PolicyId=current_policy.PolicyId
        )
        
        print(f"Found {previous_policies.count()} previous versions to check for deactivation")
        
        deactivated_count = 0
        for prev_policy in previous_policies:
            if prev_policy.ActiveInactive == 'Active':
                # Security: Escape previous policy name for safe logging
                safe_prev_name = escape_html(prev_policy.PolicyName)
                print(f"Deactivating policy: PolicyId={prev_policy.PolicyId}, Name={safe_prev_name}, Version={prev_policy.CurrentVersion}")
                
                # Set to Inactive but keep the Status unchanged
                prev_policy.ActiveInactive = 'Inactive'
                prev_policy.save()
                deactivated_count += 1
                
                print(f"Successfully deactivated policy {prev_policy.PolicyId} ({safe_prev_name})")
                
                # Also deactivate all subpolicies of this previous version
                prev_subpolicies = SubPolicy.objects.filter(PolicyId=prev_policy)
                for prev_subpolicy in prev_subpolicies:
                    if hasattr(prev_subpolicy, 'ActiveInactive'):
                        prev_subpolicy.ActiveInactive = 'Inactive'
                        prev_subpolicy.save()
                        print(f"Deactivated subpolicy {prev_subpolicy.SubPolicyId} of previous policy {prev_policy.PolicyId}")
            else:
                print(f"Policy {prev_policy.PolicyId} is already inactive, skipping")
        
        print(f"Policy versioning: Successfully deactivated {deactivated_count} previous policy versions")
        return deactivated_count
        
    except Exception as e:
        print(f"Error deactivating previous policy versions in versioning: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def approve_policy_version_and_deactivate_previous(policy_id, approval_data):
    """
    Approve a policy version and automatically deactivate previous versions.
    This function can be called when a policy version is approved through the versioning workflow.
    
    Args:
        policy_id: The ID of the policy to approve
        approval_data: Data related to the approval
        
    Returns:
        dict: Result of the approval process
    """
    # Import security modules for safe logging
    from django.utils.html import escape as escape_html
    
    try:
        # Get the policy
        policy = get_object_or_404(Policy, PolicyId=policy_id)
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Update policy status to Approved and Active/Scheduled based on StartDate
            policy.Status = 'Approved'
            # Set policy to Active or Scheduled based on StartDate
            today = date.today()
            print(f"DEBUG: Policy Version Auto-Approval {policy_id} - Today: {today}, StartDate: {policy.StartDate} (type: {type(policy.StartDate)})")
            
            if policy.StartDate and policy.StartDate > today:
                policy.ActiveInactive = 'Scheduled'
                print(f"Set policy version {policy_id} to Approved status and Scheduled status (StartDate: {policy.StartDate} > today: {today})")
            else:
                policy.ActiveInactive = 'Active'
                print(f"Set policy version {policy_id} to Approved status and Active status (StartDate: {policy.StartDate} <= today: {today} or None)")
            
            policy.save()
            
            # Security: Escape policy name for safe logging (prevents log injection)
            safe_policy_name = escape_html(policy.PolicyName)
            print(f"Policy {policy_id} ({safe_policy_name}) approved and set to {policy.ActiveInactive}")
            
            # Deactivate all previous versions
            deactivated_count = deactivate_previous_policy_versions_on_approval(policy)
            
            # Update all subpolicies for this policy to Approved with same ActiveInactive as parent policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy)
            for subpolicy in subpolicies:
                subpolicy.Status = 'Approved'
                if hasattr(subpolicy, 'ActiveInactive'):
                    subpolicy.ActiveInactive = policy.ActiveInactive  # Match parent policy's ActiveInactive status
                subpolicy.save()
                print(f"Updated subpolicy {subpolicy.SubPolicyId} status to Approved and ActiveInactive to {policy.ActiveInactive}")
        
        return {
            'success': True,
            'message': f'Policy approved successfully. {deactivated_count} previous versions deactivated.',
            'deactivated_count': deactivated_count,
            'policy_id': policy_id
        }
        
    except Exception as e:
        print(f"Error approving policy version: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }