from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from ...models import Framework, FrameworkApproval, Policy, SubPolicy, PolicyApproval, FrameworkVersion,Users
import json
from datetime import datetime
from django.db import connection
from ...routes.Global.notification_service import NotificationService  # Add this import
# Import logging modules
import logging
import traceback
from ...utils import send_log, get_client_ip

# Configure logging
logger = logging.getLogger(__name__)

# RBAC Permission imports - Add comprehensive RBAC permissions
from ...rbac.permissions import (
    PolicyFrameworkPermission, PolicyApprovalWorkflowPermission, PolicyViewPermission,
    PolicyApprovePermission, PolicyEditPermission, PolicyCreatePermission
)


def get_next_reviewer_version(framework):
    """
    Helper function to determine the next reviewer version for a framework
    """
    print(f"DEBUG: get_next_reviewer_version called for framework {framework.FrameworkId}")
    
    # Check if there's already a reviewer version for this framework
    latest_reviewer_version = FrameworkApproval.objects.filter(
        FrameworkId=framework,
        Version__startswith='r'
    ).order_by('-ApprovalId').first()
    
    if latest_reviewer_version:
        # Increment the existing reviewer version
        try:
            version_num = int(latest_reviewer_version.Version[1:])
            next_version = f'r{version_num + 1}'
            print(f"DEBUG: Incrementing reviewer version from {latest_reviewer_version.Version} to {next_version}")
            return next_version
        except ValueError:
            print(f"DEBUG: Invalid reviewer version format '{latest_reviewer_version.Version}', starting with r1")
            return 'r1'
    else:
        # First reviewer version
        print(f"DEBUG: No existing reviewer versions found, starting with r1")
        return 'r1'

def get_next_user_version(framework):
    """
    Helper function to determine the next user version for a framework
    """
    # Check if there's already a user version for this framework
    latest_user_version = FrameworkApproval.objects.filter(
        FrameworkId=framework,
        Version__startswith='u'
    ).order_by('-ApprovalId').first()
    
    if latest_user_version:
        # Increment the existing user version
        try:
            version_num = int(latest_user_version.Version[1:])
            next_version = f'u{version_num + 1}'
            print(f"DEBUG: Incrementing user version from {latest_user_version.Version} to {next_version}")
            return next_version
        except ValueError:
            print(f"DEBUG: Invalid user version format '{latest_user_version.Version}', starting with u1")
            return 'u1'
    else:
        # First user version
        print(f"DEBUG: No existing user versions found, starting with u1")
        return 'u1'

def fix_framework_versioning(framework_id=None):
    """
    Utility function to fix framework versioning issues
    Resets version numbers to follow the correct pattern: u1, r1, u2, r2, etc.
    """
    try:
        from django.db import transaction
        
        with transaction.atomic():
            if framework_id:
                frameworks = Framework.objects.filter(FrameworkId=framework_id)
            else:
                frameworks = Framework.objects.all()
            
            for framework in frameworks:
                print(f"DEBUG: Fixing versioning for framework {framework.FrameworkId}: {framework.FrameworkName}")
                
                # Get all approvals for this framework, ordered by creation time
                approvals = FrameworkApproval.objects.filter(
                    FrameworkId=framework
                ).order_by('ApprovalId')
                
                user_version_count = 0
                reviewer_version_count = 0
                
                for approval in approvals:
                    old_version = approval.Version
                    
                    # Determine if this should be a user or reviewer version based on the approval data
                    # User versions are typically created by the framework creator
                    # Reviewer versions are typically created by reviewers
                    
                    if approval.Version.startswith('u'):
                        user_version_count += 1
                        new_version = f'u{user_version_count}'
                    elif approval.Version.startswith('r'):
                        reviewer_version_count += 1
                        new_version = f'r{reviewer_version_count}'
                    else:
                        # If version doesn't start with u or r, determine based on context
                        # Check if this is a user or reviewer approval
                        if approval.UserId == approval.ReviewerId:
                            # This is likely a user version
                            user_version_count += 1
                            new_version = f'u{user_version_count}'
                        else:
                            # This is likely a reviewer version
                            reviewer_version_count += 1
                            new_version = f'r{reviewer_version_count}'
                    
                    if old_version != new_version:
                        print(f"DEBUG: Updating approval {approval.ApprovalId} version from {old_version} to {new_version}")
                        approval.Version = new_version
                        approval.save()
                    else:
                        print(f"DEBUG: Approval {approval.ApprovalId} version {old_version} is already correct")
                
                print(f"DEBUG: Completed fixing versioning for framework {framework.FrameworkId}")
        
        return True
    except Exception as e:
        print(f"DEBUG: Error fixing framework versioning: {str(e)}")
        return False

def get_next_policy_reviewer_version(policy):
    """
    Get the next reviewer version for a policy
    """
    # Get the latest reviewer version for this policy
    latest_reviewer_approval = PolicyApproval.objects.filter(
        PolicyId=policy,
        Version__startswith='r'
    ).order_by('-Version').first()
    
    if latest_reviewer_approval:
        # Parse the version and increment
        current_version = latest_reviewer_approval.Version
        if current_version.startswith('r'):
            version_num = int(current_version[1:]) + 1
            return f'r{version_num}'
    
    # If no previous reviewer version, start with r1
    return 'r1'

@api_view(['POST'])
@permission_classes([PolicyApprovalWorkflowPermission])  # RBAC: Require PolicyApprovalWorkflowPermission for creating framework approvals
def create_framework_approval(request, framework_id):
    """
    Create a framework approval entry when a new framework is created
    """
    # Log framework approval creation attempt
    logger.info(f"Framework approval creation attempt for framework ID: {framework_id}")
    send_log(
        module="Framework",
        actionType="CREATE_APPROVAL",
        description=f"Framework approval creation attempt for framework ID: {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="FrameworkApproval",
        ipAddress=get_client_ip(request)
    )
    
    # Import security modules
    from django.utils.html import escape as escape_html
    import shlex
    
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
    
    try:
        # Get the framework
        framework = Framework.objects.get(FrameworkId=framework_id)
        logger.info(f"Found framework: {framework.FrameworkName} (ID: {framework_id})")
        
        # Security: Escape framework name for safe logging (prevents log injection)
        safe_framework_name = escape_html(framework.FrameworkName)
        print(f"DEBUG: Creating framework approval for: {safe_framework_name} (ID: {framework_id})")
        
        # Extract data for the approval
        # UserId should be the framework creator, not from request data
        user_id = framework.CreatedBy if framework.CreatedBy else request.session.get('user_id')
        if not user_id:
            return Response(
                {"error": "User authentication required. Please log in and try again."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        reviewer_id = framework.Reviewer if framework.Reviewer else request.data.get('ReviewerId')
        if not reviewer_id:
            return Response(
                {"error": "Reviewer assignment required. Please select a reviewer and try again."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Security: XSS Protection - Escape policy and subpolicy text fields before adding to approval data
        policies_data = []
        created_policies = Policy.objects.filter(FrameworkId=framework)
        
        for policy in created_policies:
            policy_dict = {
                "PolicyId": policy.PolicyId,
                "PolicyName": escape_html(policy.PolicyName),
                "PolicyDescription": escape_html(policy.PolicyDescription),
                "Status": policy.Status,
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
                "PermanentTemporary": policy.PermanentTemporary,
                "ActiveInactive": policy.ActiveInactive,
                "Reviewer": escape_html(policy.Reviewer),
                "CoverageRate": policy.CoverageRate,
                "CurrentVersion": policy.CurrentVersion,
                "subpolicies": []
            }
            
            # Security: XSS Protection - Escape subpolicy text fields
            subpolicies = SubPolicy.objects.filter(PolicyId=policy)
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
                policy_dict["subpolicies"].append(subpolicy_dict)
            
            policies_data.append(policy_dict)
        
        # Security: XSS Protection - Escape all framework text fields before storing in extracted_data
        extracted_data = {
            "FrameworkName": escape_html(framework.FrameworkName),
            "FrameworkDescription": escape_html(framework.FrameworkDescription),
            "Category": escape_html(framework.Category),
            "EffectiveDate": framework.EffectiveDate.isoformat() if framework.EffectiveDate else None,
            "StartDate": framework.StartDate.isoformat() if framework.StartDate else None,
            "EndDate": framework.EndDate.isoformat() if framework.EndDate else None,
            "CreatedByName": escape_html(framework.CreatedByName),
            "CreatedByDate": framework.CreatedByDate.isoformat() if framework.CreatedByDate else None,
            "Identifier": escape_html(framework.Identifier),
            "Status": framework.Status,
            "ActiveInactive": framework.ActiveInactive,
            "InternalExternal": framework.InternalExternal,
            "type": "framework",
            "docURL": escape_html(framework.DocURL),
            "reviewer": escape_html(framework.Reviewer),
            "source": "manual_approval",
            "policies": policies_data,
            "totalPolicies": len(policies_data),
            "totalSubpolicies": sum(len(p["subpolicies"]) for p in policies_data)
        }
        
        # Create the framework approval
        framework_approval = FrameworkApproval.objects.create(
            FrameworkId=framework,
            ExtractedData=extracted_data,
            UserId=user_id,
            ReviewerId=reviewer_id,
            Version="u1",  # Default initial version
            ApprovedNot=None  # Not yet approved
        )
        
        logger.info(f"Framework approval created successfully with ID: {framework_approval.ApprovalId}")
        send_log(
            module="Framework",
            actionType="CREATE_APPROVAL_SUCCESS",
            description=f"Framework approval created successfully for framework '{framework.FrameworkName}'",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            entityId=framework_approval.ApprovalId,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_id": framework_id,
                "framework_name": framework.FrameworkName,
                "approval_id": framework_approval.ApprovalId,
                "version": framework_approval.Version
            }
        )
        
        return Response({
            "message": "Framework approval created successfully",
            "ApprovalId": framework_approval.ApprovalId,
            "Version": framework_approval.Version
        }, status=status.HTTP_201_CREATED)
        
    except Framework.DoesNotExist:
        logger.error(f"Framework not found with ID: {framework_id}")
        send_log(
            module="Framework",
            actionType="CREATE_APPROVAL_FAILED",
            description=f"Framework approval creation failed - framework not found (ID: {framework_id})",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error creating framework approval for framework {framework_id}: {str(e)}")
        logger.error(traceback.format_exc())
        send_log(
            module="Framework",
            actionType="CREATE_APPROVAL_FAILED",
            description=f"Framework approval creation failed with error: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing framework approvals by user
def get_framework_approvals_by_user(request, user_id):
    """
    Get framework approvals where the user is the creator (UserId)
    Automatically applies framework filter from session if no explicit filter provided
    """
    from ...routes.Policy.framework_filter_helper import get_active_framework_filter
    
    logger.info(f"Framework approvals by user retrieval attempt for user ID: {user_id}")
    send_log(
        module="Framework",
        actionType="VIEW_APPROVALS_BY_USER",
        description=f"Framework approvals by user retrieval attempt for user ID: {user_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="FrameworkApproval",
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Check for explicit framework filter in query params
        framework_id = request.GET.get('framework_id', None)
        
        # If no explicit filter, check session-based framework filter
        if not framework_id:
            framework_id = get_active_framework_filter(request)
        
        # Get framework approvals where user is the creator
        approvals = FrameworkApproval.objects.filter(UserId=user_id)
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering framework approvals by framework_id: {framework_id}")
            approvals = approvals.filter(FrameworkId=framework_id)
            print(f"✅ Framework filter applied. Found {approvals.count()} framework approvals.")
        
        # Get only the latest approval for each framework
        from django.db.models import Max
        latest_approval_ids = approvals.values('FrameworkId').annotate(
            latest_approval=Max('ApprovalId')
        ).values_list('latest_approval', flat=True)
        
        # Filter to only include the latest approvals
        approvals = approvals.filter(ApprovalId__in=latest_approval_ids)
        print(f"DEBUG: Found {approvals.count()} latest approvals for user {user_id}")
        
        approvals_data = []
        for approval in approvals:
            # Get framework details for the approval
            framework_name = None
            framework_category = None
            framework_status = None
            created_by_name = None
            created_by_date = None
            reviewer_name = None
            
            if approval.FrameworkId:
                framework_name = approval.FrameworkId.FrameworkName
                framework_category = approval.FrameworkId.Category
                framework_status = approval.FrameworkId.Status
                created_by_name = approval.FrameworkId.CreatedByName
                created_by_date = approval.FrameworkId.CreatedByDate
                
                # Get reviewer name from Users table
                if approval.ReviewerId:
                    try:
                        reviewer_user = Users.objects.filter(UserId=approval.ReviewerId).first()
                        if reviewer_user:
                            reviewer_name = reviewer_user.UserName
                    except Exception as e:
                        logger.warning(f"Error looking up reviewer name: {e}")
            
            approval_data = {
                "ApprovalId": approval.ApprovalId,
                "FrameworkId": approval.FrameworkId.FrameworkId if approval.FrameworkId else None,
                "FrameworkName": framework_name,
                "Category": framework_category,
                "FrameworkStatus": framework_status,
                "CreatedByName": created_by_name,
                "CreatedByDate": created_by_date.isoformat() if created_by_date else None,
                "ExtractedData": approval.ExtractedData,
                "UserId": approval.UserId,
                "ReviewerId": approval.ReviewerId,
                "ReviewerName": reviewer_name,
                "Version": approval.Version,
                "ApprovedNot": approval.ApprovedNot,
                "ApprovedDate": approval.ApprovedDate.isoformat() if approval.ApprovedDate else None
            }
            approvals_data.append(approval_data)
        
        logger.info(f"Successfully retrieved {len(approvals_data)} framework approvals for user {user_id}")
        return Response(approvals_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving framework approvals by user: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing framework approvals by reviewer
def get_framework_approvals_by_reviewer(request, user_id):
    """
    Get framework approvals where the user is the reviewer (ReviewerId)
    Automatically applies framework filter from session if no explicit filter provided
    """
    from ...routes.Policy.framework_filter_helper import get_active_framework_filter
    
    logger.info(f"Framework approvals by reviewer retrieval attempt for user ID: {user_id}")
    send_log(
        module="Framework",
        actionType="VIEW_APPROVALS_BY_REVIEWER",
        description=f"Framework approvals by reviewer retrieval attempt for user ID: {user_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="FrameworkApproval",
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Check for explicit framework filter in query params
        framework_id = request.GET.get('framework_id', None)
        
        # If no explicit filter, check session-based framework filter
        if not framework_id:
            framework_id = get_active_framework_filter(request)
        
        # Get framework approvals where user is the reviewer
        approvals = FrameworkApproval.objects.filter(ReviewerId=user_id)
        
        # Apply framework filter if provided
        if framework_id:
            print(f"🔍 DEBUG: Filtering framework approvals by framework_id: {framework_id}")
            approvals = approvals.filter(FrameworkId=framework_id)
            print(f"✅ Framework filter applied. Found {approvals.count()} framework approvals.")
        
        # Get only the latest approval for each framework
        from django.db.models import Max
        latest_approval_ids = approvals.values('FrameworkId').annotate(
            latest_approval=Max('ApprovalId')
        ).values_list('latest_approval', flat=True)
        
        # Filter to only include the latest approvals
        approvals = approvals.filter(ApprovalId__in=latest_approval_ids)
        print(f"DEBUG: Found {approvals.count()} latest approvals for reviewer {user_id}")
        
        approvals_data = []
        for approval in approvals:
            # Get framework details for the approval
            framework_name = None
            framework_category = None
            framework_status = None
            created_by_name = None
            created_by_date = None
            reviewer_name = None
            
            if approval.FrameworkId:
                framework_name = approval.FrameworkId.FrameworkName
                framework_category = approval.FrameworkId.Category
                framework_status = approval.FrameworkId.Status
                created_by_name = approval.FrameworkId.CreatedByName
                created_by_date = approval.FrameworkId.CreatedByDate
                
                # Get reviewer name from Users table
                if approval.ReviewerId:
                    try:
                        reviewer_user = Users.objects.filter(UserId=approval.ReviewerId).first()
                        if reviewer_user:
                            reviewer_name = reviewer_user.UserName
                    except Exception as e:
                        logger.warning(f"Error looking up reviewer name: {e}")
            
            approval_data = {
                "ApprovalId": approval.ApprovalId,
                "FrameworkId": approval.FrameworkId.FrameworkId if approval.FrameworkId else None,
                "FrameworkName": framework_name,
                "Category": framework_category,
                "FrameworkStatus": framework_status,
                "CreatedByName": created_by_name,
                "CreatedByDate": created_by_date.isoformat() if created_by_date else None,
                "ExtractedData": approval.ExtractedData,
                "UserId": approval.UserId,
                "ReviewerId": approval.ReviewerId,
                "ReviewerName": reviewer_name,
                "Version": approval.Version,
                "ApprovedNot": approval.ApprovedNot,
                "ApprovedDate": approval.ApprovedDate.isoformat() if approval.ApprovedDate else None
            }
            approvals_data.append(approval_data)
        
        logger.info(f"Successfully retrieved {len(approvals_data)} framework approvals for reviewer {user_id}")
        return Response(approvals_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving framework approvals by reviewer: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing framework approvals
def get_framework_approvals(request, framework_id=None):
    """
    Get all framework approvals or approvals for a specific framework
    Supports filtering by user_id to get approvals where user is creator OR reviewer
    """
    # Log framework approvals retrieval attempt
    logger.info(f"Framework approvals retrieval attempt for framework ID: {framework_id}")
    send_log(
        module="Framework",
        actionType="VIEW_APPROVALS",
        description=f"Framework approvals retrieval attempt for framework ID: {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="FrameworkApproval",
        ipAddress=get_client_ip(request)
    )
    
    # Import security modules for safe logging
    from django.utils.html import escape as escape_html
    import shlex
    
    try:
        # Get user_id filter parameter if provided
        filter_user_id = request.GET.get('user_id')
        
        if framework_id:
            # Security: Log framework ID safely
            logger.info(f"Getting approvals for framework ID: {framework_id}")
            print(f"DEBUG: Getting approvals for framework ID: {framework_id}")
            approvals = FrameworkApproval.objects.filter(FrameworkId=framework_id)
        else:
            logger.info("Getting all framework approvals")
            print("DEBUG: Getting all framework approvals")
            approvals = FrameworkApproval.objects.all()
            
            # NEW: Apply user filtering if user_id parameter is provided
            if filter_user_id:
                # Filter by approvals where user is creator (UserId) OR reviewer (ReviewerId)
                approvals = approvals.filter(
                    Q(UserId=filter_user_id) | Q(ReviewerId=filter_user_id)
                )
                logger.info(f"Filtering approvals for user {filter_user_id} (creator OR reviewer)")
                print(f"DEBUG: Filtering approvals for user {filter_user_id} - found {approvals.count()} records")
        
        # Get only the latest approval for each framework
        # Group by FrameworkId and get the latest ApprovalId for each
        from django.db.models import Max
        latest_approval_ids = approvals.values('FrameworkId').annotate(
            latest_approval=Max('ApprovalId')
        ).values_list('latest_approval', flat=True)
        
        # Filter to only include the latest approvals
        approvals = approvals.filter(ApprovalId__in=latest_approval_ids)
        print(f"DEBUG: After filtering to latest approvals per framework: {approvals.count()} records")
        logger.info(f"Showing {approvals.count()} latest approvals (one per framework)")
            
        approvals_data = []
        for approval in approvals:
            print(f"DEBUG: Processing approval {approval.ApprovalId} for framework {approval.FrameworkId.FrameworkId if approval.FrameworkId else 'None'}")
            print(f"       UserId: {approval.UserId}, ReviewerId: {approval.ReviewerId}, ApprovedNot: {approval.ApprovedNot}")
            
            # Get framework details for the approval
            framework_name = None
            framework_category = None
            framework_status = None
            created_by_name = None
            created_by_date = None
            reviewer_name = None
            
            if approval.FrameworkId:
                framework_name = approval.FrameworkId.FrameworkName
                framework_category = approval.FrameworkId.Category
                framework_status = approval.FrameworkId.Status
                created_by_name = approval.FrameworkId.CreatedByName
                created_by_date = approval.FrameworkId.CreatedByDate
                
                # Get reviewer name from Users table
                if approval.ReviewerId:
                    try:
                        reviewer_user = Users.objects.filter(UserId=approval.ReviewerId).first()
                        if reviewer_user:
                            reviewer_name = reviewer_user.UserName
                    except Exception as e:
                        logger.warning(f"Error looking up reviewer name: {e}")
            
            approval_data = {
                "ApprovalId": approval.ApprovalId,
                "FrameworkId": approval.FrameworkId.FrameworkId if approval.FrameworkId else None,
                "FrameworkName": framework_name,
                "Category": framework_category,
                "FrameworkStatus": framework_status,
                "CreatedByName": created_by_name,
                "CreatedByDate": created_by_date.isoformat() if created_by_date else None,
                "ExtractedData": approval.ExtractedData,
                "UserId": approval.UserId,
                "ReviewerId": approval.ReviewerId,
                "ReviewerName": reviewer_name,
                "Version": approval.Version,
                "ApprovedNot": approval.ApprovedNot,
                "ApprovedDate": approval.ApprovedDate.isoformat() if approval.ApprovedDate else None
            }
            
            # If this is an approved framework, also include its policies
            if approval.ApprovedNot is True:
                policies = Policy.objects.filter(FrameworkId=approval.FrameworkId)
                policies_data = []
                
                for policy in policies:
                    # Security: XSS Protection - Escape policy name in response data
                    policy_data = {
                        "PolicyId": policy.PolicyId,
                        "PolicyName": escape_html(policy.PolicyName),
                        "Status": policy.Status
                    }
                    policies_data.append(policy_data)
                
                approval_data["policies"] = policies_data
            
            approvals_data.append(approval_data)
        
        logger.info(f"Successfully retrieved {len(approvals_data)} framework approvals")
        send_log(
            module="Framework",
            actionType="VIEW_APPROVALS_SUCCESS",
            description=f"Successfully retrieved {len(approvals_data)} framework approvals",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_id": framework_id,
                "approvals_count": len(approvals_data)
            }
        )
            
        return Response(approvals_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving framework approvals: {str(e)}")
        logger.error(traceback.format_exc())
        send_log(
            module="Framework",
            actionType="VIEW_APPROVALS_FAILED",
            description=f"Framework approvals retrieval failed with error: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([PolicyApprovalWorkflowPermission])# RBAC: Require PolicyApprovalWorkflowPermission for updating framework approvals
def update_framework_approval(request, approval_id):
    """
    Update a framework approval status
    """
    try:
        approval = FrameworkApproval.objects.get(ApprovalId=approval_id)
        
        # Update approval status
        approved = request.data.get('ApprovedNot')
        if approved is not None:
            approval.ApprovedNot = approved
            
            # If approved, set approval date
            if approved:
                approval.ApprovedDate = timezone.now().date()
                
                # Also update the framework status
                if approval.FrameworkId:
                    framework = approval.FrameworkId
                    framework.Status = 'Approved'
                    
                    # Check if the framework is inactive, and update Status accordingly
                    if framework.ActiveInactive == 'Inactive':
                        framework.Status = 'Inactive'
                        
                        # Also update the ExtractedData
                        request_extracted_data = request.data.get('ExtractedData')
                        if request_extracted_data:
                            # If extracted_data was provided in the request
                            if 'ActiveInactive' in request_extracted_data and request_extracted_data['ActiveInactive'] == 'Inactive':
                                request_extracted_data['Status'] = 'Inactive'
                        elif 'ActiveInactive' in approval.ExtractedData and approval.ExtractedData['ActiveInactive'] == 'Inactive':
                            # If using existing ExtractedData
                            approval.ExtractedData['Status'] = 'Inactive'
                    
                    framework.save()
            elif approved is False:
                # If rejected, update framework status
                if approval.FrameworkId:
                    framework = approval.FrameworkId
                    framework.Status = 'Rejected'
                    framework.save()
        
        # Update extracted data if provided
        extracted_data = request.data.get('ExtractedData')
        if extracted_data:
            approval.ExtractedData = extracted_data
            
        approval.save()
        
        return Response({
            "message": "Framework approval updated successfully",
            "ApprovalId": approval.ApprovalId,
            "ApprovedNot": approval.ApprovedNot,
            "ApprovedDate": approval.ApprovedDate.isoformat() if approval.ApprovedDate else None
        }, status=status.HTTP_200_OK)
        
    except FrameworkApproval.DoesNotExist:
        return Response({"error": "Framework approval not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([PolicyApprovalWorkflowPermission]) # RBAC: Require PolicyApprovalWorkflowPermission for submitting framework reviews
def submit_framework_review(request, framework_id):
    """
    Submit a review for a framework
    """
    logger.info(f"Framework review submission attempt for framework ID: {framework_id}")
    send_log(
        module="Framework",
        actionType="SUBMIT_REVIEW",
        description=f"Framework review submission attempt for framework ID: {framework_id}",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="FrameworkApproval",
        ipAddress=get_client_ip(request)
    )
    
    try:
        print(f"submit_framework_review called for framework_id: {framework_id}")
        print(f"Request data: {request.data}")
        logger.debug(f"Request data received: {request.data}")
        
        framework = Framework.objects.get(FrameworkId=framework_id)
        logger.info(f"Found framework: {framework.FrameworkName}, current status: {framework.Status}")
        print(f"Found framework: {framework.FrameworkName}, current status: {framework.Status}")
        
        # Get current version info
        current_version = request.data.get('currentVersion', 'u1')
        user_id = request.data.get('UserId') or getattr(request.user, 'id', None)
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        reviewer_id = request.data.get('ReviewerId', 2)
        approved = request.data.get('ApprovedNot')
        extracted_data = request.data.get('ExtractedData')
        remarks = request.data.get('remarks', '')
        
        print(f"Processing: version={current_version}, approved={approved}, type={type(approved)}")
        
        # Validate required data
        if extracted_data is None:
            return Response({"error": "ExtractedData is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert boolean/null to proper values
        if approved == 'true' or approved is True:
            approved = True
        elif approved == 'false' or approved is False:
            approved = False
        else:
            approved = None
            
        print(f"Normalized approved value: {approved}, type={type(approved)}")
        
        # Create or update the framework approval
        with transaction.atomic():
            # Always create a new reviewer version when submitting a review
            new_version = get_next_reviewer_version(framework)
            
            print(f"DEBUG: Creating new reviewer version: {new_version} for framework {framework.FrameworkId}")
            print(f"DEBUG: Framework status: {framework.Status}, Approved value: {approved}")
            
            # Create a new approval record with the reviewer version
            new_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=user_id,
                ReviewerId=reviewer_id,
                Version=new_version,
                ApprovedNot=approved
            )
            
            # Set approval date if approved
            if approved:
                new_approval.ApprovedDate = timezone.now().date()
                new_approval.save()
                
                logger.info(f"Framework {framework_id} approved by reviewer")
                # Update framework status
                framework.Status = 'Approved'
                # Set framework to Active or Scheduled based on StartDate
                from datetime import date
                today = date.today()
                print(f"DEBUG: Today's date: {today}")
                print(f"DEBUG: Framework StartDate: {framework.StartDate} (type: {type(framework.StartDate)})")
                
                if framework.StartDate and framework.StartDate > today:
                    framework.ActiveInactive = 'Scheduled'
                    print(f"DEBUG: Framework {framework_id} set to 'Scheduled' because StartDate {framework.StartDate} > today {today}")
                else:
                    framework.ActiveInactive = 'Active'
                    print(f"DEBUG: Framework {framework_id} set to 'Active' because StartDate {framework.StartDate} <= today {today} or StartDate is None")
                
                # Ensure CurrentVersion is preserved during approval
                # We do this by not touching the CurrentVersion field
                # or by setting it explicitly from the framework version record
                current_framework_version = FrameworkVersion.objects.filter(
                    FrameworkId=framework
                ).first()
                if current_framework_version:
                    print(f"Setting CurrentVersion to {current_framework_version.Version} for framework {framework_id}")
                    framework.CurrentVersion = current_framework_version.Version
                    
                    # Update all policies to have the same CurrentVersion
                    policies = Policy.objects.filter(FrameworkId=framework)
                    for policy in policies:
                        policy.CurrentVersion = str(float(current_framework_version.Version))
                        print(f"Setting CurrentVersion to {policy.CurrentVersion} for policy {policy.PolicyId}")
                        policy.save()
                
                # Update extracted data to reflect the active/scheduled status
                if extracted_data:
                    extracted_data['ActiveInactive'] = framework.ActiveInactive
                    extracted_data['Status'] = 'Approved'
                
                # Send notification to submitter about framework approval
                try:
                    notification_service = NotificationService()
                    submitter = Users.objects.get(UserId=user_id)
                    reviewer = Users.objects.get(UserId=reviewer_id)
                    approval_date = timezone.now().date().isoformat()
                    notification_data = {
                        'notification_type': 'frameworkFinalApproved',
                        'email': submitter.Email,
                        'email_type': 'gmail',
                        'template_data': [
                            submitter.UserName,
                            framework.FrameworkName,
                            reviewer.UserName,
                            approval_date
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
                except Exception as notify_ex:
                    print(f"DEBUG: Error sending framework approval notification: {notify_ex}")
                
                # IMPORTANT: Deactivate previous versions of this framework
                print("\n--- STARTING PREVIOUS VERSION DEACTIVATION ---")
                
                previous_frameworks_deactivated = []
                
                # Method 1: Use the FrameworkVersion.PreviousVersionId relationship
                print("DEBUG: Method 1 - Using PreviousVersionId relationship")
                try:
                    # Get the version record for the current framework
                    current_framework_version = FrameworkVersion.objects.filter(
                        FrameworkId=framework
                    ).first()
                    
                    if current_framework_version:
                        print(f"DEBUG: Current framework {framework_id} has version record: ID={current_framework_version.VersionId}, Version={current_framework_version.Version}, PreviousVersionId={current_framework_version.PreviousVersionId}")
                        
                        # First, try using PreviousVersionId
                        if current_framework_version.PreviousVersionId:
                            try:
                                # Get the previous version record
                                previous_version = FrameworkVersion.objects.get(
                                    VersionId=current_framework_version.PreviousVersionId
                                )
                                
                                if previous_version and previous_version.FrameworkId:
                                    previous_framework_id = previous_version.FrameworkId.FrameworkId
                                    print(f"DEBUG: Previous version points to framework ID: {previous_framework_id}")
                                    
                                    previous_framework = previous_version.FrameworkId
                                    
                                    print(f"DEBUG: Previous framework {previous_framework_id} status before update: {previous_framework.ActiveInactive}")
                                    previous_framework.ActiveInactive = 'Inactive'
                                    # Make sure Status remains 'Approved' if it was already approved
                                    if previous_framework.Status == 'Approved':
                                        # Don't change the Status, leave it as 'Approved'
                                        print(f"DEBUG: Keeping Status 'Approved' for framework {previous_framework_id}")
                                    previous_framework.save()
                                    
                                    # Verify the update
                                    previous_framework.refresh_from_db()
                                    print(f"DEBUG: Previous framework {previous_framework_id} status after update: {previous_framework.ActiveInactive}, Status: {previous_framework.Status}")
                                    
                                    # Set all policies of the previous framework to inactive
                                    previous_policies = Policy.objects.filter(FrameworkId=previous_framework)
                                    for prev_policy in previous_policies:
                                        prev_policy.ActiveInactive = 'Inactive'
                                        # Don't change Status if it's already Approved
                                        if prev_policy.Status == 'Approved':
                                            print(f"DEBUG: Keeping Status 'Approved' for policy {prev_policy.PolicyId}")
                                        # Don't change CurrentVersion value
                                        print(f"DEBUG: Preserving CurrentVersion {prev_policy.CurrentVersion} for policy {prev_policy.PolicyId}")
                                        prev_policy.save()
                                    
                                    print(f"DEBUG: Using PreviousVersionId: Deactivated framework {previous_framework_id} and its {previous_policies.count()} policies")
                                    previous_frameworks_deactivated.append(int(previous_framework_id))
                            except FrameworkVersion.DoesNotExist:
                                print(f"DEBUG: Previous version record with ID {current_framework_version.PreviousVersionId} not found")
                    else:
                        print(f"DEBUG: No FrameworkVersion record found for framework {framework_id}")
                except Exception as e:
                    print(f"DEBUG: Error in Method 1: {str(e)}")
                
                # Method 2: Fallback method - direct check and update for frameworks with same identifier
                print("\nDEBUG: Method 2 - Fallback direct check for frameworks with same identifier")
                try:
                    # Get the identifier of the current framework
                    current_identifier = framework.Identifier
                    print(f"DEBUG: Current framework identifier: {current_identifier}")
                    
                    # Find all frameworks with this identifier except the current one
                    other_frameworks = Framework.objects.filter(
                        Identifier=current_identifier
                    ).exclude(FrameworkId=framework_id)
                    
                    print(f"DEBUG: Found {other_frameworks.count()} other frameworks with the same identifier")
                    
                    for other_framework in other_frameworks:
                        # Skip if already deactivated
                        if int(other_framework.FrameworkId) in previous_frameworks_deactivated:
                            print(f"DEBUG: Framework {other_framework.FrameworkId} already processed, skipping")
                            continue
                        
                        print(f"DEBUG: Framework {other_framework.FrameworkId} status before update: {other_framework.ActiveInactive}")
                        
                        # Set to inactive
                        other_framework.ActiveInactive = 'Inactive'
                        # Make sure Status remains 'Approved' if it was already approved
                        if other_framework.Status == 'Approved':
                            # Don't change the Status, leave it as 'Approved'
                            print(f"DEBUG: Keeping Status 'Approved' for framework {other_framework.FrameworkId}")
                        other_framework.save()
                        
                        # Verify the update
                        other_framework.refresh_from_db()
                        print(f"DEBUG: Framework {other_framework.FrameworkId} status after update: {other_framework.ActiveInactive}, Status: {other_framework.Status}")
                        
                        # Set all policies to inactive
                        other_policies = Policy.objects.filter(FrameworkId=other_framework)
                        for other_policy in other_policies:
                            other_policy.ActiveInactive = 'Inactive'
                            # Don't change Status if it's already Approved
                            if other_policy.Status == 'Approved':
                                print(f"DEBUG: Keeping Status 'Approved' for policy {other_policy.PolicyId}")
                            # Don't change CurrentVersion value
                            print(f"DEBUG: Preserving CurrentVersion {other_policy.CurrentVersion} for policy {other_policy.PolicyId}")
                            other_policy.save()
                        
                        print(f"DEBUG: By direct check: Deactivated framework {other_framework.FrameworkId} and its {other_policies.count()} policies")
                        previous_frameworks_deactivated.append(int(other_framework.FrameworkId))
                except Exception as e:
                    print(f"DEBUG: Error in Method 2: {str(e)}")
                
                # Log summary of what was deactivated
                print(f"\nDEBUG: Deactivated frameworks: {previous_frameworks_deactivated}")
                
                # Approve all policies and subpolicies associated with this framework
                policies = Policy.objects.filter(FrameworkId=framework)
                print(f"Approving {policies.count()} policies for framework {framework_id}")
                
                # Update all policies in the database
                for policy in policies:
                    policy.Status = 'Approved'
                    # Set policy to Active or Scheduled based on StartDate
                    from datetime import date
                    today = date.today()
                    print(f"DEBUG: Policy {policy.PolicyId} - Today: {today}, StartDate: {policy.StartDate} (type: {type(policy.StartDate)})")
                    
                    if policy.StartDate and policy.StartDate > today:
                        policy.ActiveInactive = 'Scheduled'
                        print(f"Set policy {policy.PolicyId} to Approved status and Scheduled status (StartDate: {policy.StartDate} > today: {today})")
                    else:
                        policy.ActiveInactive = 'Active'
                        print(f"Set policy {policy.PolicyId} to Approved status and Active status (StartDate: {policy.StartDate} <= today: {today} or None)")
                    
                    # 🔁 Patch to pull updated values from ExtractedData
                    for pol_data in extracted_data.get('policies', []):
                        if str(pol_data.get('PolicyId')) == str(policy.PolicyId):
                            policy.PolicyType = pol_data.get('PolicyType', '')
                            policy.PolicyCategory = pol_data.get('PolicyCategory', '')
                            policy.PolicySubCategory = pol_data.get('PolicySubCategory', '')
                            break

                    policy.save()
                    
                    # Update all subpolicies for this policy
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    for subpolicy in subpolicies:
                        subpolicy.Status = 'Approved'
                        subpolicy.save()
                        print(f"Set subpolicy {subpolicy.SubPolicyId} to Approved status")
                
                # Also update the status in the extracted data
                if 'policies' in extracted_data:
                    for policy_data in extracted_data['policies']:
                        policy_data['Status'] = 'Approved'
                        # Find the corresponding policy to get its updated ActiveInactive status
                        for policy in policies:
                            if str(policy.PolicyId) == str(policy_data.get('PolicyId')):
                                policy_data['ActiveInactive'] = policy.ActiveInactive
                                break
                        if 'subpolicies' in policy_data:
                            for subpolicy_data in policy_data['subpolicies']:
                                subpolicy_data['Status'] = 'Approved'
                    
                    # Update the extracted data in the approval record
                    new_approval.ExtractedData = extracted_data
                    new_approval.save()
                
                framework.save()
            elif approved is False:
                logger.info(f"Framework {framework_id} rejected by reviewer")
                print(f"DEBUG: Framework {framework_id} rejected by reviewer with remarks: {remarks}")
                
                # Set rejection date for framework approval
                new_approval.ApprovedDate = timezone.now().date()
                new_approval.save()
                
                # Update framework status if rejected
                framework.Status = 'Rejected'
                framework.save()
                print(f"DEBUG: Updated framework {framework_id} status to 'Rejected'")
                
                # Update the extracted data to include rejection information
                if extracted_data:
                    extracted_data['Status'] = 'Rejected'
                    if 'framework_approval' not in extracted_data:
                        extracted_data['framework_approval'] = {}
                    extracted_data['framework_approval']['approved'] = False
                    extracted_data['framework_approval']['remarks'] = remarks or 'Framework was rejected'
                    print(f"DEBUG: Updated extracted_data with rejection information")
                
                # Also reject all policies in this framework
                # Get all policies for this framework
                policies = Policy.objects.filter(FrameworkId=framework)
                logger.info(f"Rejecting {policies.count()} policies associated with framework {framework_id}")
                print(f"DEBUG: Rejecting {policies.count()} policies associated with framework {framework_id}")
                
                for policy in policies:
                    # Update policy status to rejected
                    policy.Status = 'Rejected'
                    policy.save()
                    print(f"DEBUG: Updated policy {policy.PolicyId} status to 'Rejected'")
                    
                    # Create rejection entry in policy approval
                    policy_extracted_data = {
                        "PolicyName": policy.PolicyName,
                        "PolicyDescription": policy.PolicyDescription,
                        "Status": "Rejected",
                        "Scope": policy.Scope,
                        "Objective": policy.Objective,
                        "type": "policy",
                        "framework_rejection": True,
                        "rejection_reason": remarks or f'Framework was rejected',
                        "remarks": remarks
                    }
                    
                    # Get all subpolicies for this policy
                    subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                    
                    # Create subpolicies data
                    subpolicies_data = []
                    for subpolicy in subpolicies:
                        # Update subpolicy status to rejected
                        subpolicy.Status = 'Rejected'
                        subpolicy.save()
                        print(f"DEBUG: Updated subpolicy {subpolicy.SubPolicyId} status to 'Rejected'")
                        
                        subpolicy_data = {
                            "SubPolicyId": subpolicy.SubPolicyId,
                            "SubPolicyName": subpolicy.SubPolicyName,
                            "Identifier": subpolicy.Identifier,
                            "Description": subpolicy.Description,
                            "Status": "Rejected",
                            "approval": {
                                "approved": False,
                                "remarks": remarks or f'Subpolicy "{subpolicy.SubPolicyName}" was rejected'
                            }
                        }
                        subpolicies_data.append(subpolicy_data)
                    
                    # Add subpolicies to policy data
                    policy_extracted_data["subpolicies"] = subpolicies_data
                    
                    # Create policy approval record
                    policy_approval = PolicyApproval.objects.create(
                        PolicyId=policy,
                        ExtractedData=policy_extracted_data,
                        UserId=user_id,
                        ReviewerId=reviewer_id,
                        Version=get_next_policy_reviewer_version(policy),
                        ApprovedNot=False  # Rejected
                    )
                    print(f"DEBUG: Created policy approval record {policy_approval.ApprovalId} for policy {policy.PolicyId}")
                
                # Update the framework approval record with rejection data
                new_approval.ExtractedData = extracted_data
                new_approval.save()
                print(f"DEBUG: Updated framework approval record {new_approval.ApprovalId} with rejection data")
                
                # Send notification to submitter about framework rejection
                try:
                    notification_service = NotificationService()
                    submitter = Users.objects.get(UserId=user_id)
                    reviewer = Users.objects.get(UserId=reviewer_id)
                    notification_data = {
                        'notification_type': 'frameworkRejected',
                        'email': submitter.Email,
                        'email_type': 'gmail',
                        'template_data': [
                            submitter.UserName,
                            framework.FrameworkName,
                            reviewer.UserName,
                            remarks or 'Framework was rejected'
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
                except Exception as notify_ex:
                    print(f"DEBUG: Error sending framework rejection notification: {notify_ex}")
            
            logger.info(f"Framework review submitted successfully for framework {framework_id}, approval status: {approved}")
            send_log(
                module="Framework",
                actionType="SUBMIT_REVIEW_SUCCESS",
                description=f"Framework review submitted successfully for framework '{framework.FrameworkName}', approval status: {approved}",
                userId=getattr(request.user, 'id', None),
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="FrameworkApproval",
                entityId=new_approval.ApprovalId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "framework_id": framework_id,
                    "framework_name": framework.FrameworkName,
                    "approved": approved,
                    "approval_id": new_approval.ApprovalId,
                    "version": new_approval.Version
                }
            )
            
            # Verify the database changes were saved
            framework.refresh_from_db()
            new_approval.refresh_from_db()
            print(f"DEBUG: Final framework status: {framework.Status}")
            print(f"DEBUG: Final approval status: {new_approval.ApprovedNot}")
            print(f"DEBUG: Final approval ID: {new_approval.ApprovalId}")
            
            return Response({
                "message": "Framework review submitted successfully",
                "ApprovalId": new_approval.ApprovalId,
                "Version": new_approval.Version,
                "ApprovedNot": new_approval.ApprovedNot,
                "ApprovedDate": new_approval.ApprovedDate.isoformat() if new_approval.ApprovedDate else None
            }, status=status.HTTP_200_OK)
            
    except Framework.DoesNotExist:
        logger.error(f"Framework not found with ID: {framework_id}")
        send_log(
            module="Framework",
            actionType="SUBMIT_REVIEW_FAILED",
            description=f"Framework review submission failed - framework not found (ID: {framework_id})",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error submitting framework review for framework {framework_id}: {str(e)}")
        logger.error(traceback.format_exc())
        send_log(
            module="Framework",
            actionType="SUBMIT_REVIEW_FAILED",
            description=f"Framework review submission failed with error: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for getting latest framework approval
def get_latest_framework_approval(request, framework_id):
    """
    Get the latest approval for a framework
    """
    try:
        # Get the latest approval by created date
        latest_approval = FrameworkApproval.objects.filter(
            FrameworkId=framework_id
        ).order_by('-ApprovalId').first()
        
        if not latest_approval:
            return Response({"message": "No approvals found for this framework"}, status=status.HTTP_404_NOT_FOUND)
        
        approval_data = {
            "ApprovalId": latest_approval.ApprovalId,
            "FrameworkId": latest_approval.FrameworkId.FrameworkId if latest_approval.FrameworkId else None,
            "ExtractedData": latest_approval.ExtractedData,
            "UserId": latest_approval.UserId,
            "ReviewerId": latest_approval.ReviewerId,
            "Version": latest_approval.Version,
            "ApprovedNot": latest_approval.ApprovedNot,
            "ApprovedDate": latest_approval.ApprovedDate.isoformat() if latest_approval.ApprovedDate else None
        }
        
        return Response(approval_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([PolicyApprovalWorkflowPermission]) # RBAC: Require PolicyApprovalWorkflowPermission for approving/rejecting subpolicies in framework
def approve_reject_subpolicy_in_framework(request, framework_id, policy_id, subpolicy_id):
    """
    Approve or reject a specific subpolicy within a framework approval process
    """
    print(f"DEBUG: ===== SUBPOLICY REJECTION START =====")
    print(f"DEBUG: framework_id: {framework_id}")
    print(f"DEBUG: policy_id: {policy_id}")
    print(f"DEBUG: subpolicy_id: {subpolicy_id}")
    print(f"DEBUG: request.data: {request.data}")
    print(f"DEBUG: approved: {request.data.get('approved')}")
    print(f"DEBUG: submit_review: {request.data.get('submit_review')}")
    print(f"DEBUG: rejection_reason: {request.data.get('rejection_reason')}")
    
    try:
        # First check if all database records exist and belong to the correct framework
        try:
            framework = Framework.objects.get(FrameworkId=framework_id)
            policy = Policy.objects.get(PolicyId=policy_id, FrameworkId=framework)
            subpolicy = SubPolicy.objects.get(SubPolicyId=subpolicy_id, PolicyId=policy)
            
            # Additional validation: Ensure the policy actually belongs to this framework
            if policy.FrameworkId.FrameworkId != framework_id:
                return Response({
                    "error": f"Policy {policy_id} does not belong to framework {framework_id}. Policy belongs to framework {policy.FrameworkId.FrameworkId}."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Additional validation: Ensure the subpolicy belongs to this policy
            if subpolicy.PolicyId.PolicyId != policy_id:
                return Response({
                    "error": f"Subpolicy {subpolicy_id} does not belong to policy {policy_id}. Subpolicy belongs to policy {subpolicy.PolicyId.PolicyId}."
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Framework.DoesNotExist:
            return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
        except Policy.DoesNotExist:
            # Check if policy exists but belongs to a different framework
            try:
                policy = Policy.objects.get(PolicyId=policy_id)
                return Response({
                    "error": f"Policy {policy_id} not found in framework {framework_id}. Policy belongs to framework {policy.FrameworkId.FrameworkId}."
                }, status=status.HTTP_404_NOT_FOUND)
            except Policy.DoesNotExist:
                return Response({"error": f"Policy {policy_id} not found in any framework"}, status=status.HTTP_404_NOT_FOUND)
        except SubPolicy.DoesNotExist:
            # Check if subpolicy exists but belongs to a different policy
            try:
                subpolicy = SubPolicy.objects.get(SubPolicyId=subpolicy_id)
                return Response({
                    "error": f"Subpolicy {subpolicy_id} not found in policy {policy_id}. Subpolicy belongs to policy {subpolicy.PolicyId.PolicyId}."
                }, status=status.HTTP_404_NOT_FOUND)
            except SubPolicy.DoesNotExist:
                return Response({"error": f"Subpolicy {subpolicy_id} not found in any policy"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the latest framework approval
        latest_approval = FrameworkApproval.objects.filter(
            FrameworkId=framework
        ).order_by('-ApprovalId').first()
        
        if not latest_approval:
            return Response({"error": "No framework approval found"}, status=status.HTTP_404_NOT_FOUND)
        
        approved = request.data.get('approved', None)  # True for approve, False for reject
        rejection_reason = request.data.get('rejection_reason', '')
        submit_review = request.data.get('submit_review', False)  # New flag to submit review immediately
        
        print(f"DEBUG: Parsed parameters - approved: {approved} (type: {type(approved)})")
        print(f"DEBUG: Parsed parameters - submit_review: {submit_review} (type: {type(submit_review)})")
        print(f"DEBUG: Parsed parameters - rejection_reason: {rejection_reason}")
        
        if approved is None:
            return Response({"error": "Approval status not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a copy of the extracted data for the new version
        extracted_data = latest_approval.ExtractedData.copy() if latest_approval.ExtractedData else {}
        
        print(f"DEBUG: Extracted data keys: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'Not a dict'}")
        print(f"DEBUG: Extracted data type: {type(extracted_data)}")
        print(f"DEBUG: Extracted data content: {extracted_data}")
        
        # Find and update the subpolicy status in JSON
        policies = extracted_data.get('policies', [])
        print(f"DEBUG: Found {len(policies)} policies in extracted data")
        for i, policy in enumerate(policies):
            print(f"DEBUG: Policy {i}: ID={policy.get('PolicyId')}, Name={policy.get('PolicyName')}")
            subpolicies = policy.get('subpolicies', [])
            print(f"DEBUG:   - Has {len(subpolicies)} subpolicies")
            for j, subpolicy in enumerate(subpolicies):
                print(f"DEBUG:   - Subpolicy {j}: ID={subpolicy.get('SubPolicyId')}, Name={subpolicy.get('SubPolicyName')}")
        
        # Also log the actual subpolicies in the database for this framework
        db_subpolicies = SubPolicy.objects.filter(PolicyId__FrameworkId=framework_id)
        print(f"DEBUG: Database subpolicies for framework {framework_id}: {list(db_subpolicies.values_list('SubPolicyId', 'SubPolicyName'))}")
        
        # Check if the requested subpolicy exists in the database for this framework
        db_subpolicy = SubPolicy.objects.filter(
            SubPolicyId=subpolicy_id,
            PolicyId__FrameworkId=framework_id
        ).first()
        
        if not db_subpolicy:
            print(f"DEBUG: Subpolicy {subpolicy_id} not found in database for framework {framework_id}")
            # Try to find which framework this subpolicy actually belongs to
            actual_subpolicy = SubPolicy.objects.filter(SubPolicyId=subpolicy_id).first()
            if actual_subpolicy:
                actual_framework_id = actual_subpolicy.PolicyId.FrameworkId.FrameworkId
                return Response({
                    "error": f"Subpolicy {subpolicy_id} not found in framework {framework_id}. Subpolicy belongs to framework {actual_framework_id}."
                }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    "error": f"Subpolicy {subpolicy_id} not found in any framework"
                }, status=status.HTTP_404_NOT_FOUND)
        
        print(f"DEBUG: Found subpolicy {subpolicy_id} in database for framework {framework_id}")
        
        # Find the corresponding subpolicy in ExtractedData by matching names
        # This handles the case where IDs don't match between database and ExtractedData
        matching_subpolicy_data = None
        matching_policy_data = None
        
        for policy_data in policies:
            subpolicies = policy_data.get('subpolicies', [])
            for subpolicy_data in subpolicies:
                # Try to match by name first, then by ID
                if (subpolicy_data.get('SubPolicyName') == db_subpolicy.SubPolicyName or 
                    str(subpolicy_data.get('SubPolicyId')) == str(subpolicy_id)):
                    matching_subpolicy_data = subpolicy_data
                    matching_policy_data = policy_data
                    print(f"DEBUG: Found matching subpolicy in ExtractedData: {subpolicy_data.get('SubPolicyName')}")
                    break
            if matching_subpolicy_data:
                break
        
        if not matching_subpolicy_data:
            print(f"DEBUG: Could not find matching subpolicy in ExtractedData for database subpolicy {db_subpolicy.SubPolicyName}")
            # Create a new subpolicy entry in ExtractedData
            matching_subpolicy_data = {
                'SubPolicyId': db_subpolicy.SubPolicyId,
                'SubPolicyName': db_subpolicy.SubPolicyName,
                'Status': 'Under Review',
                'Control': db_subpolicy.Control,
                'Description': db_subpolicy.Description,
                'Identifier': db_subpolicy.Identifier,
                'CreatedByName': db_subpolicy.CreatedByName,
                'CreatedByDate': db_subpolicy.CreatedByDate.isoformat() if db_subpolicy.CreatedByDate else None,
                'PermanentTemporary': db_subpolicy.PermanentTemporary
            }
            
            # Find the policy in ExtractedData that corresponds to the database policy
            db_policy = db_subpolicy.PolicyId
            for policy_data in policies:
                if (policy_data.get('PolicyName') == db_policy.PolicyName or 
                    str(policy_data.get('PolicyId')) == str(db_policy.PolicyId)):
                    matching_policy_data = policy_data
                    if 'subpolicies' not in matching_policy_data:
                        matching_policy_data['subpolicies'] = []
                    matching_policy_data['subpolicies'].append(matching_subpolicy_data)
                    # print(f"DEBUG: Added subpolicy to existing policy in ExtractedData: {db_policy.PolicyName}")
                    break
            else:
                # Create a new policy entry in ExtractedData
                matching_policy_data = {
                    'PolicyId': db_policy.PolicyId,
                    'PolicyName': db_policy.PolicyName,
                    'PolicyDescription': db_policy.PolicyDescription,
                    'Status': 'Under Review',
                    'StartDate': db_policy.StartDate.isoformat() if db_policy.StartDate else None,
                    'EndDate': db_policy.EndDate.isoformat() if db_policy.EndDate else None,
                    'Department': db_policy.Department,
                    'CreatedByName': db_policy.CreatedByName,
                    'CreatedByDate': db_policy.CreatedByDate.isoformat() if db_policy.CreatedByDate else None,
                    'Applicability': db_policy.Applicability,
                    'DocURL': db_policy.DocURL,
                    'Scope': db_policy.Scope,
                    'Objective': db_policy.Objective,
                    'Identifier': db_policy.Identifier,
                    'PermanentTemporary': db_policy.PermanentTemporary,
                    'ActiveInactive': db_policy.ActiveInactive,
                    'Reviewer': db_policy.Reviewer,
                    'CoverageRate': db_policy.CoverageRate,
                    'CurrentVersion': db_policy.CurrentVersion,
                    'PolicyType': db_policy.PolicyType,
                    'PolicyCategory': db_policy.PolicyCategory,
                    'PolicySubCategory': db_policy.PolicySubCategory,
                    'subpolicies': [matching_subpolicy_data]
                }
                policies.append(matching_policy_data)
                print(f"DEBUG: Added new policy to ExtractedData: {db_policy.PolicyName}")
        
        with transaction.atomic():
            # Process the approval/rejection using the database objects and ExtractedData
            print(f"DEBUG: Processing approval/rejection for subpolicy {db_subpolicy.SubPolicyName}")
            try:
                submitter = Users.objects.get(UserId=latest_approval.UserId)
                reviewer = Users.objects.get(UserId=latest_approval.ReviewerId)
                notification_service = NotificationService()
                
                if approved:
                    db_subpolicy.Status = 'Approved'
                    db_subpolicy.save()
                    matching_subpolicy_data['Status'] = 'Approved'
                    
                    # Check if all subpolicies for this policy are approved
                    all_subpolicies = SubPolicy.objects.filter(PolicyId=db_subpolicy.PolicyId)
                    all_approved = all(sp.Status == 'Approved' for sp in all_subpolicies)
                    
                    # If all subpolicies are approved, we can mark the policy as ready for approval
                    if all_approved:
                        db_subpolicy.PolicyId.Status = 'Ready for Approval'
                        db_subpolicy.PolicyId.save()
                        matching_policy_data['Status'] = 'Ready for Approval'
                    
                    # Send notification to submitter about approval
                    if submitter and reviewer:
                        notification_data = {
                            'notification_type': 'policyApproved',
                            'email': submitter.Email,
                            'email_type': 'gmail',
                            'template_data': [
                                submitter.UserName,
                                db_subpolicy.PolicyId.PolicyName,
                                reviewer.UserName,
                                framework.FrameworkName
                            ]
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                else:
                    db_subpolicy.Status = 'Rejected'
                    db_subpolicy.save()
                    matching_subpolicy_data['Status'] = 'Rejected'
                    
                    print(f"DEBUG: Subpolicy {db_subpolicy.SubPolicyName} rejected, processing rejection logic")
                    
                    # Also update the policy status in database
                    db_subpolicy.PolicyId.Status = 'Rejected'
                    db_subpolicy.PolicyId.save()
                    matching_policy_data['Status'] = 'Rejected'
                    
                    # Add rejection details to framework ExtractedData
                    extracted_data['framework_approval'] = {
                        'approved': False,
                        'remarks': rejection_reason or f'Subpolicy "{matching_subpolicy_data.get("SubPolicyName", "")}" was rejected',
                        'rejected_by': 'Reviewer',
                        'rejection_level': 'subpolicy',
                        'rejected_item': f'Subpolicy: {matching_subpolicy_data.get("SubPolicyName", "")}'
                    }
                    
                    # Send notification to submitter about rejection
                    if submitter and reviewer:
                        notification_data = {
                            'notification_type': 'policyRejected',
                            'email': submitter.Email,
                            'email_type': 'gmail',
                            'template_data': [
                                submitter.UserName,
                                db_subpolicy.PolicyId.PolicyName,
                                reviewer.UserName,
                                framework.FrameworkName,
                                rejection_reason or f'Subpolicy "{matching_subpolicy_data.get("SubPolicyName", "")}" was rejected'
                            ]
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                    
                    # If submit_review flag is true, submit the final review directly
                    print(f"DEBUG: Checking submit_review flag: {submit_review}")
                    if submit_review:
                        print(f"DEBUG: submit_review is True, creating new reviewer version")
                        # Always create a new reviewer version when submit_review is true
                        # Don't check for existing rejection - always create new version
                        new_version = get_next_reviewer_version(framework)
                        print(f"DEBUG: Creating new reviewer version {new_version} for framework {framework.FrameworkId} due to subpolicy rejection")
                        
                        framework_approval = FrameworkApproval.objects.create(
                            FrameworkId=framework,
                            ExtractedData=extracted_data,
                            UserId=latest_approval.UserId,
                            ReviewerId=latest_approval.ReviewerId,
                            ApprovedNot=False,  # Rejected
                            Version=new_version,  # Use the helper function
                            ApprovedDate=timezone.now().date()  # Set rejection date
                        )
                        
                        print(f"DEBUG: Created framework approval with ID: {framework_approval.ApprovalId}, Version: {framework_approval.Version}")
                        
                        # Update framework status to rejected
                        framework.Status = 'Rejected'
                        framework.save()
                        
                        return Response({
                            "message": "Subpolicy rejected and review submitted successfully",
                            "subpolicy_status": "Rejected",
                            "framework_status": "Rejected",
                            "ApprovalId": framework_approval.ApprovalId,
                            "Version": framework_approval.Version
                        }, status=status.HTTP_200_OK)
                    else:
                        print(f"DEBUG: submit_review is False, not creating new reviewer version")
                
                db_subpolicy.save()
                
            except Users.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # If approved, just update the current approval
            # Only update if we haven't already created a new approval record (when submit_review=True)
            if not submit_review:
                latest_approval.ExtractedData = extracted_data
                latest_approval.save()
            
            final_response = {
                "message": f"Subpolicy {'approved' if approved else 'rejected'} successfully",
                "subpolicy_status": "Approved" if approved else "Rejected"
            }
            print(f"DEBUG: Final response: {final_response}")
            return Response(final_response, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([PolicyApprovalWorkflowPermission])  # RBAC: Require PolicyApprovalWorkflowPermission for approving/rejecting policies in framework
def approve_reject_policy_in_framework(request, framework_id, policy_id):
    """
    Approve or reject a specific policy within a framework approval process
    """
    print(f"DEBUG: ===== POLICY REJECTION START =====")
    print(f"DEBUG: framework_id: {framework_id}")
    print(f"DEBUG: policy_id: {policy_id}")
    print(f"DEBUG: request.data: {request.data}")
    print(f"DEBUG: approved: {request.data.get('approved')}")
    print(f"DEBUG: submit_review: {request.data.get('submit_review')}")
    print(f"DEBUG: rejection_reason: {request.data.get('rejection_reason')}")
    
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Validate that the policy belongs to this framework
        try:
            policy = Policy.objects.get(PolicyId=policy_id, FrameworkId=framework)
        except Policy.DoesNotExist:
            # Check if policy exists but belongs to a different framework
            try:
                policy = Policy.objects.get(PolicyId=policy_id)
                return Response({
                    "error": f"Policy {policy_id} not found in framework {framework_id}. Policy belongs to framework {policy.FrameworkId.FrameworkId}."
                }, status=status.HTTP_404_NOT_FOUND)
            except Policy.DoesNotExist:
                return Response({"error": f"Policy {policy_id} not found in any framework"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the latest framework approval
        latest_approval = FrameworkApproval.objects.filter(
            FrameworkId=framework
        ).order_by('-ApprovalId').first()
        
        if not latest_approval:
            return Response({"error": "No framework approval found"}, status=status.HTTP_404_NOT_FOUND)
        
        approved = request.data.get('approved', None)  # True for approve, False for reject
        rejection_reason = request.data.get('rejection_reason', '')
        submit_review = request.data.get('submit_review', False)  # New flag to submit review immediately
        
        print(f"DEBUG: Parsed parameters - approved: {approved} (type: {type(approved)})")
        print(f"DEBUG: Parsed parameters - submit_review: {submit_review} (type: {type(submit_review)})")
        print(f"DEBUG: Parsed parameters - rejection_reason: {rejection_reason}")
        
        if approved is None:
            return Response({"error": "Approval status not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a copy of the extracted data for the new version
        extracted_data = latest_approval.ExtractedData.copy()
        
        # Find and update the policy status in JSON
        policies = extracted_data.get('policies', [])
        policy_found = False
        
        with transaction.atomic():
            for policy in policies:
                if str(policy.get('PolicyId')) == str(policy_id):
                    policy_found = True
                    
                    # Prepare notification service and user info
                    notification_service = NotificationService()
                    try:
                        db_policy = Policy.objects.get(PolicyId=policy_id)
                        submitter = Users.objects.get(UserId=latest_approval.UserId)
                        reviewer = Users.objects.get(UserId=latest_approval.ReviewerId)
                    except Exception as user_ex:
                        print(f"Notification user lookup error: {user_ex}")
                        submitter = None
                        reviewer = None
                    now_str = timezone.now().strftime('%Y-%m-%d %H:%M')
                    
                    if approved:
                        # Check if all subpolicies are approved first
                        subpolicies = policy.get('subpolicies', [])
                        if subpolicies:
                            all_subpolicies_approved = all(sp.get('Status') == 'Approved' for sp in subpolicies)
                            if not all_subpolicies_approved:
                                return Response({
                                    "error": "All subpolicies must be approved before approving the policy"
                                }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Update the actual Policy record in database
                        try:
                            db_policy.Status = 'Approved'
                            db_policy.save()
                            policy['Status'] = 'Approved'
                            
                            # Check if all policies are approved to update framework status
                            all_policies_approved = all(p.get('Status') == 'Approved' for p in policies)
                            if all_policies_approved:
                                extracted_data['Status'] = 'Ready for Final Approval'
                            
                            # Send notification to submitter about approval
                            if submitter and reviewer:
                                notification_data = {
                                    'notification_type': 'policyApproved',
                                    'email': submitter.Email,
                                    'email_type': 'gmail',
                                    'template_data': [
                                        submitter.UserName,
                                        db_policy.PolicyName,
                                        reviewer.UserName,
                                        now_str
                                    ]
                                }
                                notification_service.send_multi_channel_notification(notification_data)
                        except Policy.DoesNotExist:
                            return Response({"error": "Policy not found in database"}, status=status.HTTP_404_NOT_FOUND)
                        
                    else:
                        # Update the actual Policy record in database
                        try:
                            db_policy.Status = 'Rejected'
                            db_policy.save()
                            policy['Status'] = 'Rejected'
                            
                            # Reject all subpolicies in this policy
                            subpolicies_in_db = SubPolicy.objects.filter(PolicyId=policy_id)
                            for sp_db in subpolicies_in_db:
                                sp_db.Status = 'Rejected'
                                sp_db.save()
                            
                            subpolicies = policy.get('subpolicies', [])
                            for subpolicy in subpolicies:
                                subpolicy['Status'] = 'Rejected'
                            
                            # Reject entire framework
                            framework.Status = 'Rejected'
                            framework.save()
                            extracted_data['Status'] = 'Rejected'
                            
                            # Add rejection details
                            extracted_data['framework_approval'] = {
                                'approved': False,
                                'remarks': rejection_reason or f'Policy "{policy.get("PolicyName", "")}" was rejected',
                                'rejected_by': 'Reviewer',
                                'rejection_level': 'policy',
                                'rejected_item': f'Policy: {policy.get("PolicyName", "")}'
                            }
                            
                            # Send notification to submitter about rejection
                            if submitter and reviewer:
                                notification_data = {
                                    'notification_type': 'policyRejected',
                                    'email': submitter.Email,
                                    'email_type': 'gmail',
                                    'template_data': [
                                        submitter.UserName,
                                        db_policy.PolicyName,
                                        reviewer.UserName,
                                        rejection_reason or f'Policy "{policy.get("PolicyName", "")}" was rejected'
                                    ]
                                }
                                notification_service.send_multi_channel_notification(notification_data)
                            
                            # If submit_review flag is true, submit the final review directly
                            if submit_review:
                                # Always create a new reviewer version when submit_review is true
                                # Don't check for existing rejection - always create new version
                                new_version = get_next_reviewer_version(framework)
                                print(f"DEBUG: Creating new reviewer version {new_version} for framework {framework.FrameworkId} due to policy rejection")
                                
                                framework_approval = FrameworkApproval.objects.create(
                                    FrameworkId=framework,
                                    ExtractedData=extracted_data,
                                    UserId=latest_approval.UserId,
                                    ReviewerId=latest_approval.ReviewerId,
                                    ApprovedNot=False,  # Rejected
                                    Version=new_version,  # Use the helper function
                                    ApprovedDate=timezone.now().date()  # Set rejection date
                                )
                                
                                print(f"DEBUG: Created framework approval with ID: {framework_approval.ApprovalId}, Version: {framework_approval.Version}")
                                
                                # Update framework status to rejected
                                framework.Status = 'Rejected'
                                framework.save()
                                
                                return Response({
                                    "message": "Policy rejected and review submitted successfully",
                                    "policy_status": "Rejected",
                                    "framework_status": "Rejected",
                                    "ApprovalId": framework_approval.ApprovalId,
                                    "Version": framework_approval.Version
                                }, status=status.HTTP_200_OK)
                            else:
                                # Create new reviewer version without final submission
                                return create_reviewer_version(framework, extracted_data, latest_approval, False, rejection_reason)
                        
                        except Policy.DoesNotExist:
                            return Response({"error": "Policy not found in database"}, status=status.HTTP_404_NOT_FOUND)
                    
                    break
            
            if not policy_found:
                return Response({"error": "Policy not found in framework"}, status=status.HTTP_404_NOT_FOUND)
            
            # If approved, just update the current approval
            # Only update if we haven't already created a new approval record (when submit_review=True)
            if not submit_review:
                latest_approval.ExtractedData = extracted_data
                latest_approval.save()
            
            final_response = {
                "message": f"Policy {'approved' if approved else 'rejected'} successfully",
                "policy_status": "Approved" if approved else "Rejected"
            }
            print(f"DEBUG: Final response: {final_response}")
            return Response(final_response, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([PolicyApprovalWorkflowPermission])  # RBAC: Require PolicyApprovalWorkflowPermission for final framework approval
def approve_entire_framework_final(request, framework_id):
    """
    Final approval of entire framework after all policies are approved
    """
    try:
        print(f"\n\n==== DEBUG: Starting approve_entire_framework_final for framework ID: {framework_id} ====")
        framework = Framework.objects.get(FrameworkId=framework_id)
        print(f"DEBUG: Found framework: {framework.FrameworkName} (ID: {framework.FrameworkId}), Status: {framework.Status}, ActiveInactive: {framework.ActiveInactive}")
        
        # Get the latest framework approval
        latest_approval = FrameworkApproval.objects.filter(
            FrameworkId=framework
        ).order_by('-ApprovalId').first()
        
        if not latest_approval:
            return Response({"error": "No framework approval found"}, status=status.HTTP_404_NOT_FOUND)
        
        extracted_data = latest_approval.ExtractedData.copy()
        policies = extracted_data.get('policies', [])
        
        # Verify all policies are approved
        if not all(p.get('Status') == 'Approved' for p in policies):
            return Response({
                "error": "All policies must be approved before final framework approval"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Update framework status in database
            framework.Status = 'Approved'
            # Set framework to Active or Scheduled based on StartDate
            from datetime import date
            today = date.today()
            print(f"DEBUG: Today's date: {today}")
            print(f"DEBUG: Framework StartDate: {framework.StartDate} (type: {type(framework.StartDate)})")
            
            if framework.StartDate and framework.StartDate > today:
                framework.ActiveInactive = 'Scheduled'
                print(f"DEBUG: Framework {framework_id} set to 'Scheduled' because StartDate {framework.StartDate} > today {today}")
            else:
                framework.ActiveInactive = 'Active'
                print(f"DEBUG: Framework {framework_id} set to 'Active' because StartDate {framework.StartDate} <= today {today} or StartDate is None")
            
            # Ensure CurrentVersion is set correctly from the FrameworkVersion record
            current_framework_version = FrameworkVersion.objects.filter(
                FrameworkId=framework
            ).first()
            if current_framework_version:
                print(f"DEBUG: Setting CurrentVersion to {current_framework_version.Version} for framework {framework_id}")
                framework.CurrentVersion = current_framework_version.Version
                
                # Update all policies to have the same CurrentVersion
                policies_db = Policy.objects.filter(FrameworkId=framework)
                for policy in policies_db:
                    policy.CurrentVersion = str(float(current_framework_version.Version))
                    # Set policy status to Approved and ActiveInactive based on StartDate
                    policy.Status = 'Approved'
                    from datetime import date
                    today = date.today()
                    print(f"DEBUG: Policy {policy.PolicyId} - Today: {today}, StartDate: {policy.StartDate} (type: {type(policy.StartDate)})")
                    
                    if policy.StartDate and policy.StartDate > today:
                        policy.ActiveInactive = 'Scheduled'
                        print(f"DEBUG: Setting policy {policy.PolicyId} to Status='Approved', ActiveInactive='Scheduled' (StartDate: {policy.StartDate} > today: {today})")
                    else:
                        policy.ActiveInactive = 'Active'
                        print(f"DEBUG: Setting policy {policy.PolicyId} to Status='Approved', ActiveInactive='Active' (StartDate: {policy.StartDate} <= today: {today} or None)")
                    policy.save()
            
            framework.save()
            print(f"DEBUG: Updated framework {framework_id} status to 'Approved'")
            
            # Update all policies in the JSON data as well
            for policy_data in policies:
                policy_data['Status'] = 'Approved'
                # Find the corresponding policy to get its updated ActiveInactive status
                for policy in policies_db:
                    if str(policy.PolicyId) == str(policy_data.get('PolicyId')):
                        policy_data['ActiveInactive'] = policy.ActiveInactive
                        break
            
            # Also update all related SubPolicies to be Approved
            for policy in policies_db:
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                for subpolicy in subpolicies:
                    subpolicy.Status = 'Approved'
                    subpolicy.save()
                    print(f"DEBUG: Set subpolicy {subpolicy.SubPolicyId} to Status='Approved'")
            
            # Now deactivate any previous frameworks with the same identifier
            previous_frameworks_deactivated = []
            
            # Method 1: Check if there's a previous version record for this framework
            try:
                latest_version = FrameworkVersion.objects.filter(
                    FrameworkId=framework
                ).order_by('-Version').first()
                
                if latest_version and latest_version.PreviousVersionId:
                    previous_framework_id = latest_version.PreviousVersionId
                    print(f"DEBUG: Found previous framework version: {previous_framework_id}")
                    
                    try:
                        previous_version = FrameworkVersion.objects.get(FrameworkId=previous_framework_id)
                        previous_framework = previous_version.FrameworkId
                        
                        print(f"DEBUG: Previous framework {previous_framework_id} status before update: {previous_framework.ActiveInactive}")
                        previous_framework.ActiveInactive = 'Inactive'
                        # Make sure Status remains 'Approved' if it was already approved
                        if previous_framework.Status == 'Approved':
                            # Don't change the Status, leave it as 'Approved'
                            print(f"DEBUG: Keeping Status 'Approved' for framework {previous_framework_id}")
                        previous_framework.save()
                        
                        # Verify the update
                        previous_framework.refresh_from_db()
                        print(f"DEBUG: Previous framework {previous_framework_id} status after update: {previous_framework.ActiveInactive}, Status: {previous_framework.Status}")
                        
                        # Set all policies of the previous framework to inactive
                        previous_policies = Policy.objects.filter(FrameworkId=previous_framework)
                        for previous_policy in previous_policies:
                            previous_policy.ActiveInactive = 'Inactive'
                            # Don't change Status if it's already Approved
                            if previous_policy.Status == 'Approved':
                                print(f"DEBUG: Keeping Status 'Approved' for policy {previous_policy.PolicyId}")
                            # Don't change CurrentVersion value
                            print(f"DEBUG: Preserving CurrentVersion {previous_policy.CurrentVersion} for policy {previous_policy.PolicyId}")
                            previous_policy.save()
                        
                        previous_frameworks_deactivated.append(int(previous_framework_id))
                        print(f"DEBUG: Deactivated previous framework {previous_framework_id} and its {previous_policies.count()} policies")
                    except Exception as e:
                        print(f"DEBUG: Error in Method 1: {str(e)}")
            except Exception as e:
                print(f"DEBUG: Error in Method 1 (outer): {str(e)}")
            
            # Method 2: Use the identifier field to find other frameworks
            try:
                # Get the identifier of the current framework
                current_identifier = framework.Identifier
                print(f"DEBUG: Current framework identifier: {current_identifier}")
                
                # Find all frameworks with this identifier except the current one
                other_frameworks = Framework.objects.filter(
                    Identifier=current_identifier
                ).exclude(FrameworkId=framework_id)
                
                print(f"DEBUG: Found {other_frameworks.count()} other frameworks with the same identifier")
                
                for other_framework in other_frameworks:
                    # Skip if already deactivated
                    if int(other_framework.FrameworkId) in previous_frameworks_deactivated:
                        print(f"DEBUG: Framework {other_framework.FrameworkId} already processed, skipping")
                        continue
                    
                    print(f"DEBUG: Framework {other_framework.FrameworkId} status before update: {other_framework.ActiveInactive}")
                    
                    # Set to inactive
                    other_framework.ActiveInactive = 'Inactive'
                    # Make sure Status remains 'Approved' if it was already approved
                    if other_framework.Status == 'Approved':
                        # Don't change the Status, leave it as 'Approved'
                        print(f"DEBUG: Keeping Status 'Approved' for framework {other_framework.FrameworkId}")
                    other_framework.save()
                    
                    # Verify the update
                    other_framework.refresh_from_db()
                    print(f"DEBUG: Framework {other_framework.FrameworkId} status after update: {other_framework.ActiveInactive}, Status: {other_framework.Status}")
                    
                    # Set all policies to inactive
                    other_policies = Policy.objects.filter(FrameworkId=other_framework)
                    for other_policy in other_policies:
                        other_policy.ActiveInactive = 'Inactive'
                        # Don't change Status if it's already Approved
                        if other_policy.Status == 'Approved':
                            print(f"DEBUG: Keeping Status 'Approved' for policy {other_policy.PolicyId}")
                        # Don't change CurrentVersion value
                        print(f"DEBUG: Preserving CurrentVersion {other_policy.CurrentVersion} for policy {other_policy.PolicyId}")
                        other_policy.save()
                    
                    print(f"DEBUG: By direct check: Deactivated framework {other_framework.FrameworkId} and its {other_policies.count()} policies")
                    previous_frameworks_deactivated.append(int(other_framework.FrameworkId))
            except Exception as e:
                print(f"DEBUG: Error in Method 2: {str(e)}")
            
            # Log summary of what was deactivated
            print(f"\nDEBUG: Deactivated frameworks: {previous_frameworks_deactivated}")
            
            # Approve all policies and subpolicies associated with this framework
            policies = Policy.objects.filter(FrameworkId=framework)
            print(f"Approving {policies.count()} policies for framework {framework_id}")
            
            # Update all policies in the database
            for policy in policies:
                policy.Status = 'Approved'
                # Set policy to Active or Scheduled based on StartDate
                today = timezone.now().date()
                if policy.StartDate and policy.StartDate > today:
                    policy.ActiveInactive = 'Scheduled'
                    print(f"Set policy {policy.PolicyId} to Approved status and Scheduled status (StartDate: {policy.StartDate})")
                else:
                    policy.ActiveInactive = 'Active'
                    print(f"Set policy {policy.PolicyId} to Approved status and Active status (StartDate: {policy.StartDate})")
                policy.save()
                
                # Update all subpolicies for this policy
                subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                for subpolicy in subpolicies:
                    subpolicy.Status = 'Approved'
                    subpolicy.save()
                    print(f"Set subpolicy {subpolicy.SubPolicyId} to Approved status")
            
            # Also update the status in the extracted data
            if 'policies' in extracted_data:
                for policy_data in extracted_data['policies']:
                    policy_data['Status'] = 'Approved'
                    # Find the corresponding policy to get its updated ActiveInactive status
                    for policy in policies:
                        if str(policy.PolicyId) == str(policy_data.get('PolicyId')):
                            policy_data['ActiveInactive'] = policy.ActiveInactive
                            break
                    if 'subpolicies' in policy_data:
                        for subpolicy_data in policy_data['subpolicies']:
                            subpolicy_data['Status'] = 'Approved'
                
                # Update the extracted data in the approval record
                latest_approval.ExtractedData = extracted_data
                latest_approval.save()
            
            # Send notification to submitter about final framework approval
            try:
                notification_service = NotificationService()
                submitter = Users.objects.get(UserId=latest_approval.UserId)
                reviewer = Users.objects.get(UserId=latest_approval.ReviewerId)
                approval_date = timezone.now().date().isoformat()
                notification_data = {
                    'notification_type': 'frameworkFinalApproved',
                    'email': submitter.Email,
                    'email_type': 'gmail',
                    'template_data': [
                        submitter.UserName,
                        framework.FrameworkName,
                        reviewer.UserName,
                        approval_date
                    ]
                }
                notification_service.send_multi_channel_notification(notification_data)
            except Exception as notify_ex:
                print(f"DEBUG: Error sending framework final approval notification: {notify_ex}")
            
            extracted_data['framework_approval'] = {
                'approved': True,
                'remarks': 'Framework approved successfully',
                'approved_by': 'Reviewer',
                'approval_date': timezone.now().date().isoformat()
            }
            
            print("\n==== DEBUG: Completed framework approval process ====\n")
            
            # Create new reviewer version for final approval
            return create_reviewer_version(framework, extracted_data, latest_approval, True, 'Framework approved successfully')
        
    except Framework.DoesNotExist:
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"DEBUG: Unhandled exception in approve_entire_framework_final: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def create_reviewer_version(framework, extracted_data, latest_approval, approved, remarks):
    """
    Helper function to create a new reviewer version of framework approval
    """
    try:
        with transaction.atomic():
            # Determine the next reviewer version using the helper function
            new_version = get_next_reviewer_version(framework)
            
            print(f"DEBUG: Creating reviewer version {new_version} for framework {framework.FrameworkId}")
            
            # Create a new approval record with the reviewer version
            new_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=latest_approval.UserId,
                ReviewerId=latest_approval.ReviewerId,
                Version=new_version,
                ApprovedNot=approved
            )
            
            # Set approval/rejection date
            if approved:
                # Set the approval date to current date
                new_approval.ApprovedDate = timezone.now().date()
                
                # Update framework status
                if framework.ActiveInactive == 'Inactive':
                    framework.Status = 'Inactive'
                else:
                    framework.Status = 'Approved'
                
                # Ensure all policies and subpolicies are approved in the extracted data
                if 'policies' in extracted_data:
                    for policy_data in extracted_data['policies']:
                        policy_data['Status'] = 'Approved'
                        if 'subpolicies' in policy_data:
                            for subpolicy_data in policy_data['subpolicies']:
                                subpolicy_data['Status'] = 'Approved'
                
                # Update the extracted data in the approval record
                new_approval.ExtractedData = extracted_data
                
                framework.save()
            else:
                # Set rejection date for framework approval
                new_approval.ApprovedDate = timezone.now().date()
                
                # Update framework status to rejected
                framework.Status = 'Rejected'
                framework.save()
            
            # Save the approval record with the date
            new_approval.save()
            
            return Response({
                "message": f"Framework {'approved' if approved else 'rejected'} successfully",
                "ApprovalId": new_approval.ApprovalId,
                "Version": new_approval.Version,
                "ApprovedNot": new_approval.ApprovedNot,
                "framework_status": "Approved" if approved else "Rejected",
                "ApprovedDate": new_approval.ApprovedDate.isoformat() if new_approval.ApprovedDate else None
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({"error": f"Error creating reviewer version: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing rejected frameworks
def get_rejected_frameworks_for_user(request, framework_id=None, user_id=None):
    """
    Get all rejected frameworks for a specific user that can be edited and resubmitted
    Note: framework_id parameter is ignored - it's only in URL for consistency
    """
    try:
        if not user_id:
            user_id = request.GET.get('user_id', 1)  # Default user
            
        # NEW: Check if current user is GRC Administrator
        is_grc_admin = False
        current_user_id = getattr(request.user, 'id', None)
        
        if current_user_id:
            try:
                rbac_record = RBAC.objects.filter(user_id=current_user_id, is_active='Y').first()
                if rbac_record and rbac_record.is_grc_administrator():
                    is_grc_admin = True
                    logger.info(f"User {current_user_id} confirmed as GRC Administrator for rejected frameworks")
            except Exception as rbac_error:
                logger.warning(f"Error checking GRC Administrator status: {rbac_error}")
        
        # Get all frameworks with rejected status
        rejected_frameworks_query = Framework.objects.filter(Status='Rejected')
        print(f"DEBUG: Found {rejected_frameworks_query.count()} frameworks with 'Rejected' status")
        logger.info(f"Found {rejected_frameworks_query.count()} frameworks with 'Rejected' status")
        
        # NEW: Apply user filtering 
        if user_id:
            # Filter by specific user - match against CreatedByName field
            try:
                target_user = Users.objects.filter(UserId=user_id).first()
                if target_user:
                    # Filter by both user ID (as string) and user name
                    rejected_frameworks_query = rejected_frameworks_query.filter(
                        Q(CreatedByName=str(user_id)) | 
                        Q(CreatedByName=target_user.UserName)
                    )
                    logger.info(f"Filtering rejected frameworks for user {user_id} ({target_user.UserName})")
                    print(f"DEBUG: After user filtering: {rejected_frameworks_query.count()} frameworks")
                else:
                    # If user not found, just filter by user ID as string
                    rejected_frameworks_query = rejected_frameworks_query.filter(CreatedByName=str(user_id))
                    logger.info(f"Filtering rejected frameworks for user ID {user_id}")
                    print(f"DEBUG: After user ID filtering: {rejected_frameworks_query.count()} frameworks")
            except Exception as user_lookup_error:
                logger.warning(f"Error looking up user {user_id}: {user_lookup_error}")
                # Fallback to filtering by user ID as string
                rejected_frameworks_query = rejected_frameworks_query.filter(CreatedByName=str(user_id))
                print(f"DEBUG: After fallback filtering: {rejected_frameworks_query.count()} frameworks")
        
        rejected_frameworks = rejected_frameworks_query
        
        # Find the latest approval for each rejected framework
        rejected_framework_data = []
        
        for framework in rejected_frameworks:
            print(f"DEBUG: Processing rejected framework {framework.FrameworkId}: {framework.FrameworkName}")
            
            # Get the latest approval for this framework
            latest_approval = FrameworkApproval.objects.filter(
                FrameworkId=framework.FrameworkId,
                ApprovedNot=False  # Must be rejected
            ).order_by('-ApprovalId').first()
            
            print(f"DEBUG: Found approval record for framework {framework.FrameworkId}: {latest_approval.ApprovalId if latest_approval else 'None'}")
            
            if latest_approval:
                # Get reviewer name from Users table if ReviewerId is available
                reviewer_name = None
                if latest_approval.ReviewerId:
                    try:
                        reviewer_user = Users.objects.filter(UserId=latest_approval.ReviewerId).first()
                        if reviewer_user:
                            reviewer_name = reviewer_user.UserName
                    except Exception as e:
                        logger.warning(f"Error looking up reviewer name for ReviewerId {latest_approval.ReviewerId}: {e}")
                
                framework_data = {
                    "ApprovalId": latest_approval.ApprovalId,
                    "FrameworkId": framework.FrameworkId,
                    "ReviewerId": latest_approval.ReviewerId,  # Include ReviewerId
                    "ExtractedData": latest_approval.ExtractedData,
                    "Version": latest_approval.Version,
                    "ApprovedNot": latest_approval.ApprovedNot,
                    "rejection_reason": safe_get_extracted_data(latest_approval, 'framework_approval', {}).get('remarks', 'No reason provided'),
                    "created_at": framework.CreatedByDate.isoformat() if framework.CreatedByDate else None,
                    "Reviewer": reviewer_name,  # Include reviewer name
                    "CreatedBy": latest_approval.UserId  # Include creator user ID
                }
                rejected_framework_data.append(framework_data)
                print(f"DEBUG: Added framework {framework.FrameworkId} to rejected list")
            else:
                print(f"DEBUG: No approval record found for framework {framework.FrameworkId}")
                logger.warning(f"No approval record found for rejected framework {framework.FrameworkId}")
        
        print(f"DEBUG: Returning {len(rejected_framework_data)} rejected frameworks for user {user_id}")
        logger.info(f"Returning {len(rejected_framework_data)} rejected frameworks for user {user_id}")
        return Response(rejected_framework_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([PolicyEditPermission])  # RBAC: Require PolicyEditPermission for requesting framework status changes
def request_framework_status_change(request, framework_id):
    """
    Request approval for changing a framework's status from Active to Inactive
    Creates a framework approval entry that needs to be approved by a reviewer
    """
    logger.info(f"Framework status change request for framework ID: {framework_id}")
    
    # Get user ID from session or request data
    user_id = request.session.get('user_id') or request.data.get('UserId') or getattr(request.user, 'id', None)
    print('UserId--------------------------------------------------------------------:', user_id)
    
    if not user_id:
        logger.error("User ID not found in session or request")
        return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    send_log(
        module="Framework",
        actionType="REQUEST_STATUS_CHANGE",
        description=f"Framework status change request for framework ID: {framework_id}",
        userId=user_id,
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="FrameworkApproval",
        ipAddress=get_client_ip(request)
    )
    
    try:
        print(f"DEBUG: request_framework_status_change called for framework_id: {framework_id}")
        print(f"DEBUG: Request data: {request.data}")
        logger.debug(f"Request data received: {request.data}")
        
        # Get the framework
        framework = Framework.objects.get(FrameworkId=framework_id)
        logger.info(f"Found framework: {framework.FrameworkName}, Status: {framework.Status}, ActiveInactive: {framework.ActiveInactive}")
        print(f"DEBUG: Found framework: {framework.FrameworkName}, Status: {framework.Status}, ActiveInactive: {framework.ActiveInactive}")
        
        # Check if framework is active
        if framework.ActiveInactive != 'Active':
            return Response({"error": "Only Active frameworks can be submitted for status change approval"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Extract reviewer ID from request
        reviewer_id = request.data.get('ReviewerId')
        if not reviewer_id:
            return Response({"error": "Reviewer ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        print(f"DEBUG: UserId: {user_id}, ReviewerId: {reviewer_id}")
        
        reviewer_email = None
        if reviewer_id:
            try:
                reviewer_user = Users.objects.get(UserId=reviewer_id)
                reviewer_email = reviewer_user.Email
                print(f"DEBUG: Found reviewer: {reviewer_user.UserName} ({reviewer_email})")
            except Users.DoesNotExist:
                print(f"DEBUG: Reviewer with ID {reviewer_id} not found")
        
        reason = request.data.get('reason', 'No reason provided')
        print(f"DEBUG: Reason: {reason}")
        
        # Collect policies and subpolicies data for approval JSON
        policies_data = []
        created_policies = Policy.objects.filter(FrameworkId=framework)
        
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
            "EffectiveDate": framework.EffectiveDate.isoformat() if framework.EffectiveDate else None,
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
            "source": "status_change_request",
            "request_type": "status_change",
            "requested_status": "Inactive",
            "current_status": "Active",
            "reason_for_change": reason,
            "requested_date": timezone.now().date().isoformat(),
            "policies": policies_data,
            "totalPolicies": len(policies_data),
            "totalSubpolicies": sum(len(p["subpolicies"]) for p in policies_data),
            "cascade_to_policies": request.data.get('cascadeToApproved', True)
        }
        
        with transaction.atomic():
            # Update framework status to Under Review
            framework.Status = 'Under Review'
            framework.save()
            
            # Determine the next user version using the helper function
            new_version = get_next_user_version(framework)
            
            # Create the framework approval
            framework_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=user_id,
                ReviewerId=reviewer_id,
                Version=new_version,
                ApprovedNot=None  # Not yet approved
            )
            print(f"DEBUG: Created FrameworkApproval with ID: {framework_approval.ApprovalId}, Version: {new_version}, ReviewerId: {reviewer_id}")
            
            # Send notification to reviewer if email is available
            if 'reviewer_email' not in locals():
                reviewer_email = None
                if reviewer_id:
                    try:
                        reviewer_user = Users.objects.get(UserId=reviewer_id)
                        reviewer_email = reviewer_user.Email
                        print(f"DEBUG: Sending notification to reviewer: {reviewer_user.UserName} ({reviewer_email})")
                    except Users.DoesNotExist:
                        print(f"DEBUG: Could not find reviewer with ID {reviewer_id} for notification")
            
            if reviewer_email:
                print(f"DEBUG: Attempting to send notification to {reviewer_email}")
                notification_service = NotificationService()
                notification_data = {
                    'notification_type': 'frameworkInactiveRequested',
                    'email': reviewer_email,
                    'email_type': 'gmail',
                    'template_data': [
                        framework.FrameworkName,
                        reviewer_user.UserName if 'reviewer_user' in locals() else 'Unknown',
                        framework.CreatedByName,
                        reason
                    ]
                }
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"DEBUG: Framework inactivation notification result: {notification_result}")
            else:
                print("DEBUG: No reviewer email found, skipping notification")
        
        logger.info(f"Framework status change request submitted successfully for framework {framework_id}")
        send_log(
            module="Framework",
            actionType="REQUEST_STATUS_CHANGE_SUCCESS",
            description=f"Framework status change request submitted successfully for framework '{framework.FrameworkName}'",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            entityId=framework_approval.ApprovalId,
            ipAddress=get_client_ip(request),
            additionalInfo={
                "framework_id": framework_id,
                "framework_name": framework.FrameworkName,
                "approval_id": framework_approval.ApprovalId,
                "reviewer_id": reviewer_id,
                "reason": reason
            }
        )
        
        return Response({
            "message": "Framework status change request submitted successfully. Awaiting approval.",
            "ApprovalId": framework_approval.ApprovalId,
            "Version": framework_approval.Version,
            "Status": "Under Review",
            "ReviewerId": reviewer_id,
            "ReviewerEmail": reviewer_email if reviewer_email else None
        }, status=status.HTTP_201_CREATED)
        
    except Framework.DoesNotExist:
        logger.error(f"Framework not found with ID: {framework_id}")
        send_log(
            module="Framework",
            actionType="REQUEST_STATUS_CHANGE_FAILED",
            description=f"Framework status change request failed - framework not found (ID: {framework_id})",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": "Framework not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error requesting framework status change for framework {framework_id}: {str(e)}")
        logger.error(traceback.format_exc())
        send_log(
            module="Framework",
            actionType="REQUEST_STATUS_CHANGE_FAILED",
            description=f"Framework status change request failed with error: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST', 'GET'])
@permission_classes([])  # Temporarily remove permission class for debugging
@authentication_classes([])  # Temporarily remove authentication for debugging
def approve_framework_status_change(request, approval_id):
    print(f"DEBUG: ===== FUNCTION ENTRY POINT =====")
    print(f"DEBUG: Function called with approval_id: {approval_id}")
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request path: {request.path}")
    print(f"DEBUG: Request user: {request.user}")
    print(f"DEBUG: Request headers: {dict(request.headers)}")
    print(f"DEBUG: Request data: {request.data}")
    print(f"DEBUG: ===== END FUNCTION ENTRY POINT =====")
    
    # Simple test for GET requests
    if request.method == 'GET':
        return Response({
            "message": "Function is working!",
            "approval_id": approval_id,
            "method": request.method,
            "user": str(request.user) if request.user else "No user"
        })
    """
    Approve or reject a framework status change request
    """
    print(f"DEBUG: ===== APPROVE FRAMEWORK STATUS CHANGE FUNCTION CALLED =====")
    print(f"DEBUG: approval_id: {approval_id}")
    print(f"DEBUG: request.method: {request.method}")
    print(f"DEBUG: request.path: {request.path}")
    print(f"DEBUG: request.user: {request.user}")
    print(f"DEBUG: request.headers: {dict(request.headers)}")
    logger.info(f"Framework status change approval attempt for approval ID: {approval_id}")
    
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
                logger.info(f"DEBUG: approve_framework_status_change - Extracted user_id from JWT: {user_id}")
        except Exception as e:
            logger.error(f"DEBUG: approve_framework_status_change - Error extracting user_id from JWT: {e}")
    
    # Fallback to RBAC utils if JWT extraction failed
    if not user_id:
        user_id_from_rbac = RBACUtils.get_user_id_from_request(request)
        user_id_from_userid = getattr(request.user, 'UserId', None)
        user_id_from_id = getattr(request.user, 'id', None)
        
        # Use the first available user ID
        user_id = user_id_from_userid or user_id_from_id or user_id_from_rbac
    
    if not user_id:
        logger.error(f"DEBUG: approve_framework_status_change - No user ID found from any source")
        return Response({"error": "User not authenticated. Please login again."}, status=status.HTTP_401_UNAUTHORIZED)
    
    send_log(
        module="Framework",
        actionType="APPROVE_STATUS_CHANGE",
        description=f"Framework status change approval attempt for approval ID: {approval_id}",
        userId=user_id,
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="FrameworkApproval",
        ipAddress=get_client_ip(request)
    )
    
    try:
        approval = FrameworkApproval.objects.get(ApprovalId=approval_id)
        framework = approval.FrameworkId
        logger.info(f"Found framework: {framework.FrameworkName} for status change approval")
        logger.info(f"DEBUG: approve_framework_status_change - approval object: {approval}")
        logger.info(f"DEBUG: approve_framework_status_change - approval.ReviewerId: {approval.ReviewerId}")
        logger.info(f"DEBUG: approve_framework_status_change - approval.UserId: {approval.UserId}")
        logger.info(f"DEBUG: approve_framework_status_change - approval.ExtractedData: {approval.ExtractedData}")
        
        # Check if this is a status change request
        if not is_status_change_request(approval):
            logger.warning(f"Approval {approval_id} is not a status change request")
            return Response({"error": "This is not a status change request"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the current user is the assigned reviewer
        logger.info(f"DEBUG: approve_framework_status_change - approval.ReviewerId: {approval.ReviewerId}")
        logger.info(f"DEBUG: approve_framework_status_change - user_id: {user_id}")
        logger.info(f"DEBUG: approve_framework_status_change - ReviewerId type: {type(approval.ReviewerId)}")
        logger.info(f"DEBUG: approve_framework_status_change - user_id type: {type(user_id)}")
        logger.info(f"DEBUG: approve_framework_status_change - approval.ReviewerId == user_id: {approval.ReviewerId == user_id}")
        logger.info(f"DEBUG: approve_framework_status_change - str(approval.ReviewerId) == str(user_id): {str(approval.ReviewerId) == str(user_id)}")
        
        # Convert both to integers for comparison, handling None values
        try:
            reviewer_id_int = int(approval.ReviewerId) if approval.ReviewerId is not None else None
            user_id_int = int(user_id) if user_id is not None else None
            
            logger.info(f"DEBUG: approve_framework_status_change - reviewer_id_int: {reviewer_id_int}")
            logger.info(f"DEBUG: approve_framework_status_change - user_id_int: {user_id_int}")
            
            # Also try string comparison as fallback
            reviewer_id_str = str(approval.ReviewerId) if approval.ReviewerId is not None else None
            user_id_str = str(user_id) if user_id is not None else None
            
            logger.info(f"DEBUG: approve_framework_status_change - reviewer_id_str: {reviewer_id_str}")
            logger.info(f"DEBUG: approve_framework_status_change - user_id_str: {user_id_str}")
            
            # Check both integer and string comparisons
            int_match = reviewer_id_int == user_id_int
            str_match = reviewer_id_str == user_id_str
            
            logger.info(f"DEBUG: approve_framework_status_change - int_match: {int_match}")
            logger.info(f"DEBUG: approve_framework_status_change - str_match: {str_match}")
            
            if not int_match and not str_match:
                logger.warning(f"DEBUG: approve_framework_status_change - Access denied: reviewer_id ({approval.ReviewerId}) != user_id ({user_id})")
                return Response({
                    "error": "You are not the assigned reviewer for this request. Only the assigned reviewer can approve or reject status change requests."
                }, status=status.HTTP_403_FORBIDDEN)
                
        except (ValueError, TypeError) as e:
            logger.error(f"DEBUG: approve_framework_status_change - Error converting IDs: {e}")
            # If conversion fails, try direct comparison
            if str(approval.ReviewerId) != str(user_id):
                logger.warning(f"DEBUG: approve_framework_status_change - Access denied after conversion error: reviewer_id ({approval.ReviewerId}) != user_id ({user_id})")
                return Response({
                    "error": "You are not the assigned reviewer for this request. Only the assigned reviewer can approve or reject status change requests."
                }, status=status.HTTP_403_FORBIDDEN)
            
        # Get approval decision
        approved = request.data.get('approved', False)
        remarks = request.data.get('remarks', '')
        logger.info(f"Processing status change approval: approved={approved}, remarks={remarks}")
        
        with transaction.atomic():
            # Create a copy of the extracted data
            extracted_data = approval.ExtractedData.copy()
            
            if approved:
                logger.info(f"Approving status change for framework {framework.FrameworkId} to Inactive")
                # Change framework status to Inactive
                framework.ActiveInactive = 'Inactive'
                framework.Status = 'Approved'  # Also set Status field to Inactive
                framework.save()
                
                # Update extracted data
                extracted_data['ActiveInactive'] = 'Inactive'
                extracted_data['Status'] = 'Approved'
                extracted_data['status_change_approval'] = {
                    'approved': True,
                    'remarks': remarks or 'Status change approved',
                    'approved_by': user_id,  # Use the provided user_id
                    'approval_date': timezone.now().date().isoformat()
                }
                
                # Check if we should cascade to policies
                cascade_to_policies = extracted_data.get('cascade_to_policies', True)
                if cascade_to_policies:
                    # Get all policies for this framework (not just approved ones)
                    policies = Policy.objects.filter(
                        FrameworkId=framework
                    )
                    
                    # Update their status to Inactive
                    for policy in policies:
                        policy.ActiveInactive = 'Inactive'
                        policy.Status = 'Approved'  # Also set Status field to Inactive
                        policy.save()
                        
                        # Also update all subpolicies for this policy to Inactive
                        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                        for subpolicy in subpolicies:
                            subpolicy.Status = 'Inactive'
                            subpolicy.save()
                        
                        # Update in extracted data
                        for policy_data in extracted_data.get('policies', []):
                            if policy_data.get('PolicyId') == policy.PolicyId:
                                policy_data['ActiveInactive'] = 'Inactive'
                                policy_data['Status'] = 'Approved'  # Also update Status in JSON
                                
                                # Update subpolicies in extracted data
                                for subpolicy_data in policy_data.get('subpolicies', []):
                                    subpolicy_data['Status'] = 'Approved'
                else:
                    logger.info(f"Rejecting status change for framework {framework.FrameworkId}")
                    # Reject status change request, revert framework status
                    framework.Status = 'Approved'  # Reset from "Under Review"
                    framework.save()
                    
                    # Update extracted data
                    extracted_data['status_change_approval'] = {
                        'approved': False,
                        'remarks': remarks or 'Status change rejected',
                        'rejected_by': 'Reviewer',
                        'rejection_date': timezone.now().date().isoformat()
                    }
                
            # Determine the next reviewer version using the helper function
            new_version = get_next_reviewer_version(framework)
                
            # Create a new approval record with the reviewer version
            new_approval = FrameworkApproval.objects.create(
                FrameworkId=framework,
                ExtractedData=extracted_data,
                UserId=approval.UserId,
                ReviewerId=approval.ReviewerId,
                Version=new_version,
                ApprovedNot=approved
            )
            
            # Set approval/rejection date
            new_approval.ApprovedDate = timezone.now().date()
            new_approval.save()
            
            # Send notification to submitter about approval or rejection
            submitter_email = None
            submitter_name = framework.CreatedByName
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
                notification_service = NotificationService()
                if approved:
                    notification_data = {
                        'notification_type': 'frameworkInactivationApproved',
                        'email': submitter_email,
                        'email_type': 'gmail',
                        'template_data': [
                            submitter_name,
                            framework.FrameworkName,
                            reviewer_name,
                            remarks or 'Status change approved'
                        ]
                    }
                else:
                    notification_data = {
                        'notification_type': 'frameworkInactivationRejected',
                        'email': submitter_email,
                        'email_type': 'gmail',
                        'template_data': [
                            framework.FrameworkName,
                            submitter_name,
                            reviewer_name,
                            remarks or 'Status change rejected'
                        ]
                    }
                notification_result = notification_service.send_multi_channel_notification(notification_data)
                print(f"Framework inactivation approval notification result: {notification_result}")
                
            logger.info(f"Framework status change {'approved' if approved else 'rejected'} successfully for approval {approval_id}")
            send_log(
                module="Framework",
                actionType="APPROVE_STATUS_CHANGE_SUCCESS",
                description=f"Framework status change {'approved' if approved else 'rejected'} successfully for framework '{framework.FrameworkName}'",
                userId=user_id,
                userName=getattr(request.user, 'username', 'Anonymous'),
                entityType="FrameworkApproval",
                entityId=new_approval.ApprovalId,
                ipAddress=get_client_ip(request),
                additionalInfo={
                    "framework_id": framework.FrameworkId,
                    "framework_name": framework.FrameworkName,
                    "approved": approved,
                    "approval_id": new_approval.ApprovalId,
                    "remarks": remarks
                }
            )
            
            return Response({
                "message": f"Framework status change request {'approved' if approved else 'rejected'}",
                "ApprovalId": new_approval.ApprovalId,
                "Version": new_approval.Version,
                "ApprovedNot": approved,
                "framework_status": framework.Status,
                "framework_active_inactive": framework.ActiveInactive
            }, status=status.HTTP_200_OK)
            
    except FrameworkApproval.DoesNotExist:
        logger.error(f"Framework approval not found with ID: {approval_id}")
        send_log(
            module="Framework",
            actionType="APPROVE_STATUS_CHANGE_FAILED",
            description=f"Framework status change approval failed - approval not found (ID: {approval_id})",
            userId=user_id,
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": "Framework approval not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error approving framework status change for approval {approval_id}: {str(e)}")
        logger.error(traceback.format_exc())
        send_log(
            module="Framework",
            actionType="APPROVE_STATUS_CHANGE_FAILED",
            description=f"Framework status change approval failed with error: {str(e)}",
            userId=user_id,
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def safe_get_extracted_data(approval, key, default=None):
    """Safely get data from ExtractedData with null check and legacy format support"""
    if not approval.ExtractedData:
        return default
    
    # Try the requested key first
    value = approval.ExtractedData.get(key, default)
    if value is not None:
        return value
    
    # Legacy format mapping for old data
    legacy_mapping = {
        'request_type': 'type',  # Old format uses 'type' instead of 'request_type'
        'reason_for_change': 'reason',  # Old format might use 'reason'
        'requested_date': 'date',  # Old format might use 'date'
        'cascade_to_policies': 'cascade',  # Old format might use 'cascade'
    }
    
    if key in legacy_mapping:
        legacy_key = legacy_mapping[key]
        return approval.ExtractedData.get(legacy_key, default)
    
    return default

def is_status_change_request(approval):
    """Check if approval is a status change request - supports both old and new formats"""
    if not approval.ExtractedData:
        return False
    
    # New format: request_type = 'status_change'
    if approval.ExtractedData.get('request_type') == 'status_change':
        return True
    
    # Old format: type = 'framework' (legacy support)
    if approval.ExtractedData.get('type') == 'framework':
        return True
    
    return False

@api_view(['GET'])
@permission_classes([PolicyViewPermission])  # RBAC: Require PolicyViewPermission for viewing status change requests
def get_status_change_requests(request):
    """
    Get all framework status change requests
    Include both pending and processed (approved/rejected) requests
    Group related approvals by framework name to ensure consistent status display
    """
    logger.info("Retrieving all framework status change requests")
    send_log(
        module="Framework",
        actionType="VIEW_STATUS_CHANGE_REQUESTS",
        description="Retrieving all framework status change requests",
        userId=getattr(request.user, 'id', None),
        userName=getattr(request.user, 'username', 'Anonymous'),
        entityType="FrameworkApproval",
        ipAddress=get_client_ip(request)
    )
    
    try:
        # Find all framework approvals with request_type=status_change
        status_change_requests = []
        framework_status_map = {}  # To track the latest status for each framework
        logger.debug("Starting framework status change requests retrieval")
        
        # Get all approvals, not just those with ApprovedNot=None
        approvals = FrameworkApproval.objects.filter().order_by('-ApprovalId')
        
        # First pass: Get the latest status for each framework
        for approval in approvals:
            # Check if the extracted data contains request_type=status_change
            if is_status_change_request(approval):
                try:
                    framework = approval.FrameworkId
                    framework_name = framework.FrameworkName
                    
                    # Only track the status if we haven't seen this framework before
                    # or if this is a newer approval (with a higher ApprovalId)
                    if framework_name not in framework_status_map:
                        framework_status_map[framework_name] = {
                            'status': approval.ApprovedNot,
                            'approvalId': approval.ApprovalId
                        }
                except Exception as e:
                    logger.warning(f"Skipping approval {approval.ApprovalId} - Framework not found: {str(e)}")
                    continue
        
        # Second pass: Create the request data with consistent status
        for approval in approvals:
            # Check if the extracted data contains request_type=status_change
            if is_status_change_request(approval):
                try:
                    framework = approval.FrameworkId
                    framework_name = framework.FrameworkName
                except Exception as e:
                    logger.warning(f"Skipping approval {approval.ApprovalId} - Framework not found: {str(e)}")
                    continue
                
                # Get the policies and subpolicies that would be affected if approved
                affected_policies = []
                total_subpolicies = 0
                if safe_get_extracted_data(approval, 'cascade_to_policies', True):
                    policies = Policy.objects.filter(
                        FrameworkId=framework
                    )
                    
                    for policy in policies:
                        # Count subpolicies for this policy
                        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                        subpolicy_count = subpolicies.count()
                        total_subpolicies += subpolicy_count
                        
                        affected_policies.append({
                            'PolicyId': policy.PolicyId,
                            'PolicyName': policy.PolicyName,
                            'Department': policy.Department,
                            'Status': policy.Status,
                            'ActiveInactive': policy.ActiveInactive,
                            'Identifier': policy.Identifier,
                            'Description': policy.PolicyDescription[:100] + '...' if policy.PolicyDescription and len(policy.PolicyDescription) > 100 else policy.PolicyDescription,
                            'SubpolicyCount': subpolicy_count
                        })
                
                # Use the latest status for this framework from our map
                latest_status = framework_status_map.get(framework_name, {'status': None})['status']
                
                # Determine status based on the latest status for this framework
                approval_status = "Pending Approval"
                if latest_status is True:
                    approval_status = "Approved"
                elif latest_status is False:
                    approval_status = "Rejected"
                
                # Include any approval remarks
                approval_remarks = ""
                if safe_get_extracted_data(approval, 'status_change_approval'):
                    approval_remarks = safe_get_extracted_data(approval, 'status_change_approval', {}).get('remarks', '')
                
                request_data = {
                    'ApprovalId': approval.ApprovalId,
                    'FrameworkId': framework.FrameworkId,
                    'FrameworkName': framework.FrameworkName,
                    'Category': framework.Category,
                    'RequestType': 'Change Status to Inactive',
                    'RequestDate': safe_get_extracted_data(approval, 'requested_date'),
                    'Reason': safe_get_extracted_data(approval, 'reason_for_change', 'No reason provided'),
                    'UserId': approval.UserId,
                    'ReviewerId': approval.ReviewerId,
                    'Version': approval.Version,
                    'Status': approval_status,
                    'ApprovedNot': latest_status,  # Use the latest status for consistency
                    'ApprovedDate': approval.ApprovedDate.isoformat() if approval.ApprovedDate else None,
                    'CascadeToApproved': safe_get_extracted_data(approval, 'cascade_to_policies', True),
                    'PolicyCount': len(affected_policies),
                    'SubpolicyCount': total_subpolicies,
                    'AffectedPolicies': affected_policies,
                    'Remarks': approval_remarks,
                    'IsLatestApproval': approval.ApprovalId == framework_status_map.get(framework_name, {'approvalId': None})['approvalId']
                }
                
                status_change_requests.append(request_data)
        
        logger.info(f"Successfully retrieved {len(status_change_requests)} framework status change requests")
        send_log(
            module="Framework",
            actionType="VIEW_STATUS_CHANGE_REQUESTS_SUCCESS",
            description=f"Successfully retrieved {len(status_change_requests)} framework status change requests",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            ipAddress=get_client_ip(request),
            additionalInfo={
                "requests_count": len(status_change_requests)
            }
        )
        
        return Response(status_change_requests, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving framework status change requests: {str(e)}")
        logger.error(traceback.format_exc())
        send_log(
            module="Framework",
            actionType="VIEW_STATUS_CHANGE_REQUESTS_FAILED",
            description=f"Framework status change requests retrieval failed with error: {str(e)}",
            userId=getattr(request.user, 'id', None),
            userName=getattr(request.user, 'username', 'Anonymous'),
            entityType="FrameworkApproval",
            logLevel="ERROR",
            ipAddress=get_client_ip(request)
        )
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([PolicyEditPermission])
def update_existing_activeinactive_by_date(request):
    """
    Update existing approved frameworks and policies ActiveInactive status based on StartDate
    This is a utility function to fix existing data
    """
    try:
        from datetime import date
        today = date.today()
        print(f"DEBUG: Today's date for update: {today}")
        
        updated_frameworks = 0
        updated_policies = 0
        
        # Update approved frameworks
        approved_frameworks = Framework.objects.filter(Status='Approved')
        print(f"DEBUG: Found {approved_frameworks.count()} approved frameworks to check")
        
        for framework in approved_frameworks:
            old_status = framework.ActiveInactive
            print(f"DEBUG: Framework {framework.FrameworkId} - StartDate: {framework.StartDate}, Current ActiveInactive: {old_status}")
            
            if framework.StartDate and framework.StartDate > today:
                framework.ActiveInactive = 'Scheduled'
                framework.save()
                updated_frameworks += 1
                print(f"DEBUG: Updated Framework {framework.FrameworkId} from '{old_status}' to 'Scheduled' (StartDate: {framework.StartDate} > today: {today})")
            elif framework.StartDate and framework.StartDate <= today and old_status not in ['Active', 'Inactive']:
                framework.ActiveInactive = 'Active'
                framework.save()
                updated_frameworks += 1
                print(f"DEBUG: Updated Framework {framework.FrameworkId} from '{old_status}' to 'Active' (StartDate: {framework.StartDate} <= today: {today})")
        
        # Update approved policies
        approved_policies = Policy.objects.filter(Status='Approved')
        print(f"DEBUG: Found {approved_policies.count()} approved policies to check")
        
        for policy in approved_policies:
            old_status = policy.ActiveInactive
            print(f"DEBUG: Policy {policy.PolicyId} - StartDate: {policy.StartDate}, Current ActiveInactive: {old_status}")
            
            if policy.StartDate and policy.StartDate > today:
                policy.ActiveInactive = 'Scheduled'
                policy.save()
                updated_policies += 1
                print(f"DEBUG: Updated Policy {policy.PolicyId} from '{old_status}' to 'Scheduled' (StartDate: {policy.StartDate} > today: {today})")
            elif policy.StartDate and policy.StartDate <= today and old_status not in ['Active', 'Inactive']:
                policy.ActiveInactive = 'Active'
                policy.save()
                updated_policies += 1
                print(f"DEBUG: Updated Policy {policy.PolicyId} from '{old_status}' to 'Active' (StartDate: {policy.StartDate} <= today: {today})")
        
        return Response({
            "message": "Successfully updated ActiveInactive status based on StartDate",
            "updated_frameworks": updated_frameworks,
            "updated_policies": updated_policies,
            "today_date": today.isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"ERROR in update_existing_activeinactive_by_date: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_users_for_reviewer_selection(request):
    """
    Get all users that can be selected as reviewers for framework status change requests
    """
    try:
        print("DEBUG: Fetching users for reviewer selection...")
        users = Users.objects.all().values('UserId', 'UserName', 'Email')
        users_list = list(users)
        print(f"DEBUG: Found {len(users_list)} users: {users_list}")
        
        # If no users found, create test users automatically
        if len(users_list) == 0:
            print("DEBUG: No users found, creating test users...")
            from datetime import datetime
            
            test_users = [
                {
                    'UserName': 'John Reviewer',
                    'Email': 'john.reviewer@company.com',
                    'Password': 'password123'
                },
                {
                    'UserName': 'Jane Approver', 
                    'Email': 'jane.approver@company.com',
                    'Password': 'password123'
                },
                {
                    'UserName': 'Bob Manager',
                    'Email': 'bob.manager@company.com', 
                    'Password': 'password123'
                }
            ]
            
            for user_data in test_users:
                user = Users.objects.create(
                    UserName=user_data['UserName'],
                    Email=user_data['Email'],
                    Password=user_data['Password'],
                    CreatedAt=datetime.now(),
                    UpdatedAt=datetime.now()
                )
                users_list.append({
                    'UserId': user.UserId,
                    'UserName': user.UserName,
                    'Email': user.Email
                })
            
            print(f"DEBUG: Created {len(test_users)} test users. Total users now: {len(users_list)}")
        
        return Response(users_list, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"ERROR: Failed to fetch users: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_status_change_requests_by_user(request, user_id=None):
    """
    Get framework status change requests filtered by user (creator/owner)
    """
    try:
        print(f"DEBUG: get_status_change_requests_by_user called with user_id: {user_id}")
        
        # If user_id is provided, filter by that user
        if user_id:
            approvals = FrameworkApproval.objects.filter(
                UserId=user_id
            ).order_by('-ApprovalId')
            print(f"DEBUG: Found {approvals.count()} approvals for user {user_id}")
        else:
            # Get all approvals if no user specified
            approvals = FrameworkApproval.objects.all().order_by('-ApprovalId')
            print(f"DEBUG: Found {approvals.count()} total approvals")
        
        status_change_requests = []
        framework_status_map = {}
        
        # First pass: Get the latest status for each framework
        for approval in approvals:
            if is_status_change_request(approval):
                try:
                    framework = approval.FrameworkId
                    framework_name = framework.FrameworkName
                    
                    if framework_name not in framework_status_map:
                        framework_status_map[framework_name] = {
                            'status': approval.ApprovedNot,
                            'approvalId': approval.ApprovalId
                        }
                except Exception as e:
                    logger.warning(f"Skipping approval {approval.ApprovalId} - Framework not found: {str(e)}")
                    continue
        
        # Second pass: Create the request data with consistent status
        for approval in approvals:
            if is_status_change_request(approval):
                try:
                    framework = approval.FrameworkId
                    framework_name = framework.FrameworkName
                except Exception as e:
                    logger.warning(f"Skipping approval {approval.ApprovalId} - Framework not found: {str(e)}")
                    continue
                
                # Get the policies that would be affected if approved
                affected_policies = []
                total_subpolicies = 0
                if safe_get_extracted_data(approval, 'cascade_to_policies', True):
                    policies = Policy.objects.filter(FrameworkId=framework)
                    
                    for policy in policies:
                        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                        subpolicy_count = subpolicies.count()
                        total_subpolicies += subpolicy_count
                        
                        affected_policies.append({
                            'PolicyId': policy.PolicyId,
                            'PolicyName': policy.PolicyName,
                            'Department': policy.Department,
                            'Status': policy.Status,
                            'ActiveInactive': policy.ActiveInactive,
                            'SubpolicyCount': subpolicy_count
                        })
                
                latest_status = framework_status_map.get(framework_name, {'status': None})['status']
                
                approval_status = "Pending Approval"
                if latest_status is True:
                    approval_status = "Approved"
                elif latest_status is False:
                    approval_status = "Rejected"
                
                approval_remarks = ""
                if safe_get_extracted_data(approval, 'status_change_approval'):
                    approval_remarks = safe_get_extracted_data(approval, 'status_change_approval', {}).get('remarks', '')
                
                # Get reviewer information
                reviewer_info = None
                if approval.ReviewerId:
                    try:
                        reviewer_user = Users.objects.get(UserId=approval.ReviewerId)
                        reviewer_info = {
                            'UserId': reviewer_user.UserId,
                            'UserName': reviewer_user.UserName,
                            'Email': reviewer_user.Email
                        }
                    except Users.DoesNotExist:
                        pass
                
                request_data = {
                    'ApprovalId': approval.ApprovalId,
                    'FrameworkId': framework.FrameworkId,
                    'FrameworkName': framework.FrameworkName,
                    'Category': framework.Category,
                    'RequestType': 'Change Status to Inactive',
                    'RequestDate': safe_get_extracted_data(approval, 'requested_date'),
                    'Reason': safe_get_extracted_data(approval, 'reason_for_change', 'No reason provided'),
                    'UserId': approval.UserId,
                    'ReviewerId': approval.ReviewerId,
                    'ReviewerInfo': reviewer_info,
                    'Status': approval_status,
                    'ApprovedNot': approval.ApprovedNot,
                    'ApprovedDate': approval.ApprovedDate.isoformat() if approval.ApprovedDate else None,
                    'CascadeToApproved': safe_get_extracted_data(approval, 'cascade_to_policies', True),
                    'PolicyCount': len(affected_policies),
                    'AffectedPolicies': affected_policies,
                    'Remarks': approval_remarks,
                    'Type': 'Framework'  # Add type field to distinguish from policies
                }
                
                status_change_requests.append(request_data)
        
        print(f"DEBUG: Returning {len(status_change_requests)} framework status change requests for user {user_id}")
        logger.info(f"Found {len(status_change_requests)} framework status change requests for user {user_id}")
        
        # Debug: Print all approvals in database
        all_approvals = FrameworkApproval.objects.filter(
            Q(ExtractedData__request_type='status_change') | Q(ExtractedData__type='framework')
        ).values('ApprovalId', 'UserId', 'ReviewerId', 'FrameworkId__FrameworkName')
        print(f"DEBUG: All status change approvals in database: {list(all_approvals)}")
        
        return Response(status_change_requests, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"DEBUG: ERROR in get_status_change_requests_by_user: {str(e)}")
        logger.error(f"ERROR in get_status_change_requests_by_user: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_status_change_requests_by_reviewer(request, reviewer_id=None):
    """
    Get framework status change requests filtered by reviewer
    """
    try:
        print(f"DEBUG: get_status_change_requests_by_reviewer called with reviewer_id: {reviewer_id}")
        
        # If reviewer_id is provided, filter by that reviewer
        if reviewer_id:
            approvals = FrameworkApproval.objects.filter(
                ReviewerId=reviewer_id
            ).order_by('-ApprovalId')
            print(f"DEBUG: Found {approvals.count()} framework approvals for reviewer {reviewer_id}")
        else:
            # Get all approvals if no reviewer specified
            approvals = FrameworkApproval.objects.all().order_by('-ApprovalId')
            print(f"DEBUG: Found {approvals.count()} total framework approvals")
        
        status_change_requests = []
        framework_status_map = {}
        
        # First pass: Get the latest status for each framework
        for approval in approvals:
            if is_status_change_request(approval):
                try:
                    framework = approval.FrameworkId
                    framework_name = framework.FrameworkName
                    
                    if framework_name not in framework_status_map:
                        framework_status_map[framework_name] = {
                            'status': approval.ApprovedNot,
                            'approvalId': approval.ApprovalId
                        }
                except Exception as e:
                    logger.warning(f"Skipping approval {approval.ApprovalId} - Framework not found: {str(e)}")
                    continue
        
        # Second pass: Create the request data with consistent status
        for approval in approvals:
            if is_status_change_request(approval):
                try:
                    framework = approval.FrameworkId
                    framework_name = framework.FrameworkName
                except Exception as e:
                    logger.warning(f"Skipping approval {approval.ApprovalId} - Framework not found: {str(e)}")
                    continue
                
                # Get the policies that would be affected if approved
                affected_policies = []
                total_subpolicies = 0
                if safe_get_extracted_data(approval, 'cascade_to_policies', True):
                    policies = Policy.objects.filter(FrameworkId=framework)
                    
                    for policy in policies:
                        subpolicies = SubPolicy.objects.filter(PolicyId=policy)
                        subpolicy_count = subpolicies.count()
                        total_subpolicies += subpolicy_count
                        
                        affected_policies.append({
                            'PolicyId': policy.PolicyId,
                            'PolicyName': policy.PolicyName,
                            'Department': policy.Department,
                            'Status': policy.Status,
                            'ActiveInactive': policy.ActiveInactive,
                            'SubpolicyCount': subpolicy_count
                        })
                
                latest_status = framework_status_map.get(framework_name, {'status': None})['status']
                
                approval_status = "Pending Approval"
                if latest_status is True:
                    approval_status = "Approved"
                elif latest_status is False:
                    approval_status = "Rejected"
                
                approval_remarks = ""
                if safe_get_extracted_data(approval, 'status_change_approval'):
                    approval_remarks = safe_get_extracted_data(approval, 'status_change_approval', {}).get('remarks', '')
                
                # Get reviewer information
                reviewer_info = None
                if approval.ReviewerId:
                    try:
                        reviewer_user = Users.objects.get(UserId=approval.ReviewerId)
                        reviewer_info = {
                            'UserId': reviewer_user.UserId,
                            'UserName': reviewer_user.UserName,
                            'Email': reviewer_user.Email
                        }
                    except Users.DoesNotExist:
                        pass
                
                request_data = {
                    'ApprovalId': approval.ApprovalId,
                    'FrameworkId': framework.FrameworkId,
                    'FrameworkName': framework.FrameworkName,
                    'Category': framework.Category,
                    'RequestType': 'Change Status to Inactive',
                    'RequestDate': safe_get_extracted_data(approval, 'requested_date'),
                    'Reason': safe_get_extracted_data(approval, 'reason_for_change', 'No reason provided'),
                    'UserId': approval.UserId,
                    'ReviewerId': approval.ReviewerId,
                    'ReviewerInfo': reviewer_info,
                    'Version': approval.Version,
                    'Status': approval_status,
                    'ApprovedNot': latest_status,
                    'ApprovedDate': approval.ApprovedDate.isoformat() if approval.ApprovedDate else None,
                    'CascadeToApproved': safe_get_extracted_data(approval, 'cascade_to_policies', True),
                    'PolicyCount': len(affected_policies),
                    'SubpolicyCount': total_subpolicies,
                    'AffectedPolicies': affected_policies,
                    'Remarks': approval_remarks,
                    'IsLatestApproval': approval.ApprovalId == framework_status_map.get(framework_name, {'approvalId': None})['approvalId']
                }
                
                status_change_requests.append(request_data)
        
        print(f"DEBUG: Returning {len(status_change_requests)} framework status change requests for reviewer {reviewer_id}")
        
        # Debug: Print all approvals in database
        all_approvals = FrameworkApproval.objects.filter(
            Q(ExtractedData__request_type='status_change') | Q(ExtractedData__type='framework')
        ).values('ApprovalId', 'UserId', 'ReviewerId', 'FrameworkId__FrameworkName')
        print(f"DEBUG: All status change approvals in database: {list(all_approvals)}")
        
        return Response(status_change_requests, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"DEBUG: ERROR in get_status_change_requests_by_reviewer: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([PolicyCreatePermission])
def create_test_users(request):
    """
    Create test users for testing reviewer selection functionality
    This is a temporary endpoint for testing purposes
    """
    try:
        from datetime import datetime
        
        # Check if users already exist
        existing_users = Users.objects.count()
        if existing_users > 0:
            return Response({"message": f"Users already exist in database ({existing_users} users found)"}, status=status.HTTP_200_OK)
        
        # Create test users
        test_users = [
            {
                'UserName': 'John Reviewer',
                'Email': 'john.reviewer@company.com',
                'Password': 'password123'
            },
            {
                'UserName': 'Jane Approver', 
                'Email': 'jane.approver@company.com',
                'Password': 'password123'
            },
            {
                'UserName': 'Bob Manager',
                'Email': 'bob.manager@company.com', 
                'Password': 'password123'
            }
        ]
        
        created_users = []
        for user_data in test_users:
            user = Users.objects.create(
                UserName=user_data['UserName'],
                Email=user_data['Email'],
                Password=user_data['Password'],
                CreatedAt=datetime.now(),
                UpdatedAt=datetime.now()
            )
            created_users.append({
                'UserId': user.UserId,
                'UserName': user.UserName,
                'Email': user.Email
            })
        
        return Response({
            "message": f"Created {len(created_users)} test users successfully",
            "users": created_users
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"ERROR: Failed to create test users: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([PolicyEditPermission])
def fix_framework_versions(request):
    """
    API endpoint to fix framework versioning issues
    """
    try:
        framework_id = request.data.get('framework_id')
        
        print(f"DEBUG: Fixing framework versions for framework_id: {framework_id}")
        
        success = fix_framework_versioning(framework_id)
        
        if success:
            return Response({
                "message": "Framework versioning fixed successfully",
                "framework_id": framework_id
            }, status=200)
        else:
            return Response({
                "error": "Failed to fix framework versioning"
            }, status=500)
            
    except Exception as e:
        print(f"DEBUG: Error in fix_framework_versions API: {str(e)}")
        return Response({
            "error": f"Error fixing framework versions: {str(e)}"
        }, status=500)

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
def get_frameworks(request):
    """
    Get all frameworks with optional filtering
    """
    try:
        # Get query parameters
        user_id = request.GET.get('user_id')
        include_all_status = request.GET.get('include_all_status', 'false').lower() == 'true'
        
        # Base query
        frameworks = Framework.objects.all()
        
        # Apply user filter if provided
        if user_id:
            frameworks = frameworks.filter(
                Q(CreatedBy=user_id) |  # Frameworks created by user
                Q(Reviewer=user_id)     # Frameworks assigned to user for review
            )
        
        # If include_all_status is false, only return frameworks that need review
        if not include_all_status:
            frameworks = frameworks.filter(Status='Under Review')
        
        # Convert frameworks to list of dictionaries
        frameworks_list = []
        for framework in frameworks:
            framework_dict = {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName,
                'FrameworkDescription': framework.FrameworkDescription,
                'Category': framework.Category,
                'Status': framework.Status,
                'CreatedBy': framework.CreatedBy,
                'CreatedByName': framework.CreatedByName,
                'CreatedByDate': framework.CreatedByDate,
                'StartDate': framework.StartDate,
                'EndDate': framework.EndDate,
                'Identifier': framework.Identifier,
                'DocURL': framework.DocURL,
                'Reviewer': framework.Reviewer,
                'ReviewerId': framework.ReviewerId,
                'InternalExternal': framework.InternalExternal,
                'CurrentVersion': framework.CurrentVersion,
                'UserId': framework.CreatedBy  # Include UserId for consistency
            }
            frameworks_list.append(framework_dict)
        
        return Response(frameworks_list)
    except Exception as e:
        logger.error(f"Error in get_frameworks: {str(e)}")
        return Response(
            {"error": "Failed to fetch frameworks"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow all users to see approved frameworks on homepage
def get_approved_active_frameworks(request):
    """
    Get all approved and active frameworks for display on homepage
    """
    try:
        # Query for frameworks that are both Approved and Active
        frameworks = Framework.objects.filter(
            Status='Approved',
            ActiveInactive='Active'
        ).order_by('FrameworkName')
        
        # Convert frameworks to list of dictionaries
        frameworks_list = []
        for framework in frameworks:
            framework_dict = {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName,
                'FrameworkDescription': framework.FrameworkDescription,
                'Category': framework.Category,
                'CurrentVersion': framework.CurrentVersion,
                'EffectiveDate': framework.EffectiveDate.isoformat() if framework.EffectiveDate else None,
                'Identifier': framework.Identifier,
                'InternalExternal': framework.InternalExternal
            }
            frameworks_list.append(framework_dict)
        
        return Response({
            'success': True,
            'data': frameworks_list,
            'count': len(frameworks_list)
        })
    except Exception as e:
        logger.error(f"Error in get_approved_active_frameworks: {str(e)}")
        return Response(
            {
                "success": False,
                "error": "Failed to fetch approved frameworks"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow all users to set framework in session
def set_selected_framework(request):
    """
    Store selected framework ID for user
    - If frameworkId is provided: Filter by that framework
    - If frameworkId is None: Show all frameworks (no filter)
    """
    try:
        from ...framework_context import set_framework_context, clear_framework_context
        
        framework_id = request.data.get('frameworkId')
        user_id = request.data.get('userId')
        
        print(f"🔍 DEBUG: set_selected_framework called")
        print(f"📊 DEBUG: frameworkId = {framework_id}")
        print(f"👤 DEBUG: userId = {user_id}")
        print(f"📝 DEBUG: request.data = {request.data}")
        
        # User ID is required
        if not user_id:
            print("❌ DEBUG: No userId provided")
            return Response(
                {
                    "success": False,
                    "error": "User ID is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If framework_id is None, it means "All" is selected - clear the filter
        if framework_id is None:
            print("ℹ️ DEBUG: frameworkId is None - clearing filter (All selected)")
            
            # Clear from framework context (this will also clear session)
            clear_framework_context(str(user_id), request)
            print(f"✅ DEBUG: Framework filter cleared for user {user_id}")
            
            return Response({
                'success': True,
                'message': 'All frameworks selected (filter cleared)',
                'frameworkId': None,
                'userId': user_id,
                'sessionKeys': list(request.session.keys())
            })
        
        # If framework_id is provided, store it
        print(f"ℹ️ DEBUG: frameworkId provided - setting filter to {framework_id}")
        
        # Store in framework context (this will also clear old session data)
        set_framework_context(str(user_id), str(framework_id), request)
        print(f"✅ DEBUG: Framework {framework_id} stored in framework context for user {user_id}")
        
        return Response({
            'success': True,
            'message': f'Framework {framework_id} selected successfully',
            'frameworkId': framework_id,
            'userId': user_id,
            'sessionKeys': list(request.session.keys())
        })
        
    except Exception as e:
        print(f"❌ DEBUG: Error in set_selected_framework: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.error(f"Error in set_selected_framework: {str(e)}")
        return Response(
            {
                "success": False,
                "error": "Failed to set selected framework"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow all users to get selected framework
def get_selected_framework(request):
    """
    Get currently selected framework ID for user
    """
    try:
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
        
        # If not in request.user, try from query parameters
        if not user_id and request.GET.get('userId'):
            user_id = request.GET.get('userId')
            print(f"✅ DEBUG: Found user_id in query parameters: {user_id}")
        
        # If still no user_id, try JWT token
        if not user_id:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                from ...authentication import verify_jwt_token
                token = auth_header.split(' ')[1]
                try:
                    payload = verify_jwt_token(token)
                    if payload and 'user_id' in payload:
                        user_id = payload['user_id']
                        print(f"✅ DEBUG: Found user_id in JWT token: {user_id}")
                except Exception as jwt_error:
                    print(f"⚠️ DEBUG: JWT extraction failed: {str(jwt_error)}")
        
        print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        print(f"🔍 DEBUG: get_selected_framework called")
        
        # Try to get framework_id from various sources
        framework_id = None
        session_framework_id = None  # Initialize to avoid reference error
        
        # Try from framework context FIRST (more reliable and up-to-date)
        if user_id:
            framework_id = get_framework_context(str(user_id))
            if framework_id:
                print(f"✅ DEBUG: Found framework_id in framework context: {framework_id}")
        
        # Fall back to session if not in framework context (for backward compatibility)
        if not framework_id:
            session_framework_id = request.session.get('selected_framework_id') or request.session.get('grc_framework_selected')
            if session_framework_id:
                framework_id = session_framework_id
                print(f"⚠️ DEBUG: Found framework_id in session (fallback): {framework_id}")
        
        # If still no framework_id, try query parameters
        if not framework_id and request.GET.get('frameworkId'):
            framework_id = request.GET.get('frameworkId')
            print(f"✅ DEBUG: Found framework_id in query parameters: {framework_id}")
        
        print(f"📊 DEBUG: Final frameworkId = {framework_id}")
        print(f"👤 DEBUG: Final userId = {user_id}")
        print(f"🔍 DEBUG: Session keys = {list(request.session.keys()) if hasattr(request, 'session') else 'No session'}")
        
        # Get framework name if framework_id exists
        framework_name = None
        if framework_id:
            try:
                from ...models import Framework
                framework = Framework.objects.filter(FrameworkId=framework_id).first()
                if framework:
                    framework_name = framework.FrameworkName
                    print(f"✅ DEBUG: Found framework name: {framework_name}")
                else:
                    print(f"⚠️ DEBUG: No framework found with ID {framework_id}")
            except Exception as fw_error:
                print(f"⚠️ DEBUG: Error fetching framework name: {str(fw_error)}")
        
        return Response({
            'success': True,
            'frameworkId': framework_id,
            'frameworkName': framework_name,
            'userId': user_id,
            'hasFramework': framework_id is not None,
            'source': 'framework_context' if not session_framework_id and framework_id else 'session'
        })
        
    except Exception as e:
        print(f"❌ DEBUG: Error in get_selected_framework: {str(e)}")
        logger.error(f"Error in get_selected_framework: {str(e)}")
        return Response(
            {
                "success": False,
                "error": "Failed to get selected framework"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Test endpoint for debugging session issues
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def test_session_debug(request):
    """Test endpoint to debug session issues"""
    try:
        if request.method == 'POST':
            # Set test data in session
            test_framework_id = request.data.get('test_framework_id', 999)
            test_user_id = request.data.get('test_user_id', 888)
            
            request.session['selected_framework_id'] = test_framework_id
            request.session['user_id'] = test_user_id
            request.session['test_timestamp'] = timezone.now().isoformat()
            request.session.save()
            
            print(f"🧪 DEBUG: Test session data set")
            print(f"📊 DEBUG: Framework ID: {test_framework_id}")
            print(f"👤 DEBUG: User ID: {test_user_id}")
            print(f"🔑 DEBUG: Session key: {request.session.session_key}")
            
            return Response({
                'success': True,
                'message': 'Test session data set',
                'session_key': request.session.session_key,
                'framework_id': test_framework_id,
                'user_id': test_user_id
            })
        
        else:  # GET request
            # Get test data from session
            framework_id = request.session.get('selected_framework_id')
            user_id = request.session.get('user_id')
            timestamp = request.session.get('test_timestamp')
            
            print(f"🧪 DEBUG: Test session data retrieved")
            print(f"📊 DEBUG: Framework ID: {framework_id}")
            print(f"👤 DEBUG: User ID: {user_id}")
            print(f"⏰ DEBUG: Timestamp: {timestamp}")
            print(f"🔑 DEBUG: Session key: {request.session.session_key}")
            print(f"🔍 DEBUG: All session keys: {list(request.session.keys())}")
            
            return Response({
                'success': True,
                'framework_id': framework_id,
                'user_id': user_id,
                'timestamp': timestamp,
                'session_key': request.session.session_key,
                'session_keys': list(request.session.keys()),
                'has_session': hasattr(request, 'session')
            })
            
    except Exception as e:
        print(f"❌ DEBUG: Error in test_session_debug: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# Test endpoint for debugging user ID extraction
@api_view(['GET'])
@permission_classes([])
def test_user_id_extraction(request):
    """Test endpoint to debug user ID extraction"""
    from grc.rbac.utils import RBACUtils
    
    # Test different methods of getting user ID
    user_id_from_rbac = RBACUtils.get_user_id_from_request(request)
    user_id_from_request = getattr(request.user, 'UserId', None) if request.user else None
    user_id_from_session = request.session.get('user_id') if hasattr(request, 'session') else None
    
    return Response({
        'user_id_from_rbac': user_id_from_rbac,
        'user_id_from_request': user_id_from_request,
        'user_id_from_session': user_id_from_session,
        'request_user': str(request.user),
        'request_user_type': str(type(request.user)),
        'session_exists': hasattr(request, 'session'),
        'session_keys': list(request.session.keys()) if hasattr(request, 'session') else []
    })

# Test endpoint for framework approval routing
@api_view(['GET'])
@permission_classes([])
def test_framework_approval_routing(request, approval_id):
    """Test endpoint to check if framework approval routing is working"""
    print(f"DEBUG: ===== TEST FRAMEWORK APPROVAL ROUTING FUNCTION CALLED for approval {approval_id} =====")
    return Response({
        'message': 'Framework approval routing test successful',
        'approval_id': approval_id,
        'user': str(request.user),
        'user_id': getattr(request.user, 'UserId', None),
        'request_method': request.method,
        'request_path': request.path
    })

# Test endpoint for POST framework approval routing
@api_view(['POST'])
@permission_classes([])
def test_framework_approval_post_routing(request, approval_id):
    """Test endpoint to check if POST framework approval routing is working"""
    print(f"DEBUG: ===== TEST FRAMEWORK APPROVAL POST ROUTING FUNCTION CALLED for approval {approval_id} =====")
    return Response({
        'message': 'Framework approval POST routing test successful',
        'approval_id': approval_id,
        'user': str(request.user),
        'user_id': getattr(request.user, 'UserId', None),
        'request_method': request.method,
        'request_path': request.path,
        'request_data': request.data
    })