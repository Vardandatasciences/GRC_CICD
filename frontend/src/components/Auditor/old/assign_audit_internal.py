from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from ...models import Framework, Policy, SubPolicy, Users, Audit, AuditFinding, Compliance
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .audit_views import create_audit_version, get_audit_findings_json

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

import json
import datetime
from ...routes.Global.validation import validate_audit_data, ValidationError, validate_int, validate_new_compliance_data
from ...routes.Global.logging_service import send_log
from ...rbac.permissions import (
    AuditViewPermission, AuditConductPermission, AuditReviewPermission,
    AuditAssignPermission, AuditAnalyticsPermission, AuditViewAllPermission
)
from ...rbac.decorators import (
    audit_assign_required,
    audit_conduct_required,
    audit_view_reports_required,
    audit_view_all_required
)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AuditAssignPermission])
@audit_assign_required
def get_frameworks(request):
    """Return all frameworks (FrameworkId, FrameworkName)"""
    try:
        frameworks = Framework.objects.all().values('FrameworkId', 'FrameworkName')
        # Log the action
        user_id = request.session.get('user_id')
        send_log(
            module="Audit",
            actionType="GET_FRAMEWORKS",
            description="Retrieved all frameworks",
            userId=user_id,
            entityType="Framework"
        )
        return Response(list(frameworks), status=status.HTTP_200_OK)
    except Exception as e:
        send_log(
            module="Audit",
            actionType="GET_FRAMEWORKS_ERROR",
            description=f"Error retrieving frameworks: {str(e)}",
            userId=request.session.get('user_id'),
            entityType="Framework",
            logLevel="ERROR"
        )
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AuditAssignPermission])
@audit_assign_required
def get_policies(request):
    """Return all policies for a given framework (PolicyId, PolicyName, FrameworkId)"""
    try:
        framework_id = request.GET.get('framework_id')
        if not framework_id:
            return Response({'error': 'framework_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        policies = Policy.objects.filter(FrameworkId=framework_id).values('PolicyId', 'PolicyName', 'FrameworkId')
        # Log the action
        user_id = request.session.get('user_id')
        send_log(
            module="Audit",
            actionType="GET_POLICIES",
            description=f"Retrieved policies for framework ID {framework_id}",
            userId=user_id,
            entityType="Policy",
            entityId=framework_id
        )
        return Response(list(policies), status=status.HTTP_200_OK)
    except Exception as e:
        send_log(
            module="Audit",
            actionType="GET_POLICIES_ERROR",
            description=f"Error retrieving policies: {str(e)}",
            userId=request.session.get('user_id'),
            entityType="Policy",
            entityId=framework_id if 'framework_id' in locals() else None,
            logLevel="ERROR"
        )
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([AuditAssignPermission])
@audit_assign_required
def get_subpolicies(request):
    """Return all subpolicies for a given policy (SubPolicyId, SubPolicyName, PolicyId)"""
    try:
        policy_id = request.GET.get('policy_id')
        if not policy_id:
            return Response({'error': 'policy_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        subpolicies = SubPolicy.objects.filter(PolicyId=policy_id).values('SubPolicyId', 'SubPolicyName', 'PolicyId')
        # Log the action
        user_id = request.session.get('user_id')
        send_log(
            module="Audit",
            actionType="GET_SUBPOLICIES",
            description=f"Retrieved subpolicies for policy ID {policy_id}",
            userId=user_id,
            entityType="SubPolicy",
            entityId=policy_id
        )
        return Response(list(subpolicies), status=status.HTTP_200_OK)
    except Exception as e:
        send_log(
            module="Audit",
            actionType="GET_SUBPOLICIES_ERROR",
            description=f"Error retrieving subpolicies: {str(e)}",
            userId=request.session.get('user_id'),
            entityType="SubPolicy",
            entityId=policy_id if 'policy_id' in locals() else None,
            logLevel="ERROR"
        )
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditAssignPermission])
@audit_assign_required
def get_users_audit(request):
    """Return all users (UserId, UserName)"""
    try:
        users = Users.objects.all().values('UserId', 'UserName')
        
        # Log the action
        user_id = request.session.get('user_id')
        send_log(
            module="Audit",
            actionType="GET_USERS",
            description="Retrieved all users",
            userId=user_id,
            entityType="User"
        )
        
        return Response(list(users), status=status.HTTP_200_OK)
    except Exception as e:
        send_log(
            module="Audit",
            actionType="GET_USERS_ERROR",
            description=f"Error retrieving users: {str(e)}",
            userId=request.session.get('user_id'),
            entityType="User",
            logLevel="ERROR"
        )
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditAssignPermission])
@audit_assign_required
def create_audit(request):
    """
    Create new Audit instances for each team member based on the form submission.
    """
    try:
        data = request.data
        print(f"Received audit creation request with data: {data}")
        
        # Log audit creation attempt
        user_id = request.session.get('user_id')
        send_log(
            module="Audit",
            actionType="CREATE_AUDIT_ATTEMPT",
            description="Attempting to create new audit(s)",
            userId=user_id,
            entityType="Audit",
            additionalInfo={"title": data.get('title'), "framework_id": data.get('framework_id')}
        )
        
        try:
            # Validate all input data
            # validated_data = validate_audit_data(data)
            validated_data = data
        except ValidationError as e:
            send_log(
                module="Audit",
                actionType="CREATE_AUDIT_VALIDATION_ERROR",
                description=f"Validation error: {str(e)}",
                userId=user_id,
                entityType="Audit",
                logLevel="ERROR",
                additionalInfo={"validation_error": str(e)}
            )
            return Response({
                'error': 'Validation error',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        created_audits = []
        findings_created = 0
        
        # Create separate audit for each team member
        for member_id in validated_data['team_members']:
            print(f"Creating audit for team member {member_id}")
            # Ensure AuditType is always a valid single character (I/E/S)
            audit_type = validated_data.get('audit_type')
            if not audit_type or audit_type not in ['I', 'E', 'S']:
                audit_type = 'I'  # Default to Internal if missing or invalid
            audit_fields = {
                'Title': validated_data['title'],
                'Scope': validated_data['scope'],
                'Objective': validated_data['objective'],
                'BusinessUnit': validated_data.get('business_unit', ''),
                'Role': validated_data['role'],
                'Responsibility': validated_data['responsibility'],
                'Assignee_id': member_id,
                'Auditor_id': member_id,
                'Reviewer_id': validated_data['reviewer'],
                'FrameworkId_id': validated_data['framework_id'],
                'PolicyId_id': validated_data['policy_id'],
                'SubPolicyId_id': validated_data['subpolicy_id'],
                'DueDate': validated_data['due_date'],
                'Frequency': validated_data['frequency'],
                'Status': 'Yet to Start',
                'AuditType': audit_type,
                'AssignedDate': timezone.now(),
                'ReviewStatus': None,
                'ReviewerComments': None,
                'Evidence': '',
                'Comments': '',
                'Reports': data.get('reports', ''),
                'ReviewStartDate': None,
                'ReviewDate': None,
                'CompletionDate': None,
            }

            print(f"Audit fields for member {member_id}: {audit_fields}")

            audit = None
            try:
                # Create the audit instance for this team member
                audit = Audit.objects.create(**audit_fields)
                print(f"Created audit {audit.AuditId} for member {member_id}")
                created_audits.append(audit)
                
                # Log successful audit creation
                send_log(
                    module="Audit",
                    actionType="CREATE_AUDIT_SUCCESS",
                    description=f"Created audit {audit.AuditId} for member {member_id}",
                    userId=user_id,
                    userName=None,  # Could get username if needed
                    entityType="Audit",
                    entityId=str(audit.AuditId),
                    additionalInfo={
                        "audit_id": audit.AuditId,
                        "assignee_id": member_id,
                        "framework_id": validated_data['framework_id'],
                        "policy_id": validated_data['policy_id'],
                        "subpolicy_id": validated_data['subpolicy_id']
                    }
                )

                # Get compliances based on selection level
                findings_created += 1
                
                if audit_fields['FrameworkId_id']:
                    with connection.cursor() as cursor:
                        # First verify the framework exists
                        cursor.execute("""
                            SELECT FrameworkId, FrameworkName 
                            FROM frameworks 
                            WHERE FrameworkId = %s
                        """, [audit_fields['FrameworkId_id']])
                        framework = cursor.fetchone()
                        
                        if not framework:
                            print(f"Framework {audit_fields['FrameworkId_id']} not found")
                            return Response({
                                'error': f'Framework with ID {audit_fields["FrameworkId_id"]} not found'
                            }, status=status.HTTP_404_NOT_FOUND)
                        
                        print(f"Found framework: {framework}")
                        
                        # Get compliances based on selection level
                        if audit_fields['PolicyId_id'] and audit_fields['SubPolicyId_id']:
                            print(f"Getting compliances for subpolicy {audit_fields['SubPolicyId_id']}")
                            cursor.execute("""
                                SELECT c.* 
                                FROM compliance c
                                WHERE c.SubPolicyId = %s
                                AND c.PermanentTemporary = 'Permanent'
                                AND c.Status = 'Approved'
                                AND c.ActiveInactive = 'Active'
                            """, [audit_fields['SubPolicyId_id']])
                            
                        elif audit_fields['PolicyId_id']:
                            print(f"Getting compliances for policy {audit_fields['PolicyId_id']}")
                            cursor.execute("""
                                SELECT c.* 
                                FROM compliance c
                                INNER JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                                WHERE sp.PolicyId = %s
                                AND c.PermanentTemporary = 'Permanent'
                                AND c.Status = 'Approved'
                                AND c.ActiveInactive = 'Active'
                            """, [audit_fields['PolicyId_id']])
                            
                        else:
                            print(f"Getting compliances for framework {audit_fields['FrameworkId_id']}")
                            cursor.execute("""
                                SELECT c.* 
                                FROM compliance c
                                INNER JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                                INNER JOIN policies p ON sp.PolicyId = p.PolicyId
                                WHERE p.FrameworkId = %s
                                AND c.PermanentTemporary = 'Permanent'
                                AND c.Status = 'Approved'
                                AND c.ActiveInactive = 'Active'
                            """, [audit_fields['FrameworkId_id']])
                        
                        compliances = cursor.fetchall()
                        print(f"Found {len(compliances)} compliances")
                        
                        # Create audit findings for found compliances
                        if compliances:
                            for compliance in compliances:
                                compliance_id = compliance[0]  # Assuming ComplianceId is the first column
                                print(f"Creating finding for compliance {compliance_id}")
                                
                                cursor.execute("""
                                    INSERT INTO audit_findings (
                                        `AuditId`, `ComplianceId`, `UserId`, `Evidence`, 
                                        `Check`, `Comments`, `MajorMinor`, `AssignedDate`, `ReviewRejected`
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, [
                                    audit.AuditId, compliance_id, audit.Auditor_id,
                                    '', '0', '', None, audit.AssignedDate, 0  # Added default value 0 for ReviewRejected
                                ])
                                findings_created += 1
                                print(f"Created finding {findings_created} for compliance {compliance_id}")
                        else:
                            print(f"No compliances found for audit {audit.AuditId}")
            
            except Exception as e:
                send_log(
                    module="Audit",
                    actionType="CREATE_AUDIT_ERROR",
                    description=f"Error creating audit for member {member_id}: {str(e)}",
                    userId=user_id,
                    entityType="Audit",
                    logLevel="ERROR",
                    additionalInfo={"member_id": member_id, "error": str(e)}
                )
                # If we hit an error creating findings, we should clean up the audit
                if audit is not None:
                    try:
                        audit.delete()
                        print(f"Cleaned up audit {audit.AuditId} due to error")
                    except Exception as cleanup_error:
                        print(f"Error cleaning up audit: {str(cleanup_error)}")
                raise

        if not created_audits:
            send_log(
                module="Audit",
                actionType="CREATE_AUDIT_FAILED",
                description="No audits were created successfully",
                userId=user_id,
                entityType="Audit",
                logLevel="ERROR"
            )
            return Response({
                'error': 'No audits were created successfully'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print(f"Successfully created {len(created_audits)} audits with {findings_created} findings each")
        
        # Log final success
        send_log(
            module="Audit",
            actionType="CREATE_AUDIT_COMPLETE",
            description=f"Successfully created {len(created_audits)} audits with {findings_created} findings each",
            userId=user_id,
            entityType="Audit",
            additionalInfo={
                "audit_ids": [audit.AuditId for audit in created_audits],
                "findings_created": findings_created
            }
        )
        
        return Response({
            'message': 'Audits created successfully',
            'audits_created': len(created_audits),
            'audit_ids': [audit.AuditId for audit in created_audits],
            'findings_created_per_audit': findings_created,
        }, status=status.HTTP_201_CREATED)
        
    except (ValueError, TypeError) as e:
        print(f"Data format error: {str(e)}")
        send_log(
            module="Audit",
            actionType="CREATE_AUDIT_FORMAT_ERROR",
            description=f"Data format error: {str(e)}",
            userId=request.session.get('user_id'),
            entityType="Audit",
            logLevel="ERROR"
        )
        return Response({
            'error': f'Invalid data format: {str(e)}. Please check all fields are in the correct format.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        send_log(
            module="Audit",
            actionType="CREATE_AUDIT_UNEXPECTED_ERROR",
            description=f"Unexpected error: {str(e)}",
            userId=request.session.get('user_id'),
            entityType="Audit",
            logLevel="ERROR",
            additionalInfo={"traceback": traceback.format_exc()}
        )
        return Response({
            'error': f'Error creating audit: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def get_audit_compliances(request, audit_id):
    """
    Get all compliance details for a specific audit through audit findings
    """
    try:
        # Log the request
        user_id = request.session.get('user_id')
        send_log(
            module="Audit",
            actionType="GET_AUDIT_COMPLIANCES",
            description=f"Retrieving compliance details for audit ID {audit_id}",
            userId=user_id,
            entityType="Audit",
            entityId=str(audit_id)
        )
        
        # Get all audit findings for the given audit ID with related compliance info
        audit_findings = AuditFinding.objects.filter(
            AuditId=audit_id
        ).select_related(
            'ComplianceId',
            'ComplianceId__SubPolicyId',
            'ComplianceId__SubPolicyId__PolicyId',
            'ComplianceId__SubPolicyId__PolicyId__FrameworkId'
        )

        compliance_data = []
        for finding in audit_findings:
            compliance = finding.ComplianceId
            compliance_data.append({
                'finding_id': finding.AuditFindingId,
                'compliance_id': compliance.ComplianceId,
                'compliance_name': compliance.ComplianceName,
                'compliance_description': compliance.ComplianceDescription,
                'subpolicy_name': compliance.SubPolicyId.SubPolicyName if compliance.SubPolicyId else None,
                'policy_name': compliance.SubPolicyId.PolicyId.PolicyName if compliance.SubPolicyId and compliance.SubPolicyId.PolicyId else None,
                'framework_name': compliance.SubPolicyId.PolicyId.FrameworkId.FrameworkName if compliance.SubPolicyId and compliance.SubPolicyId.PolicyId and compliance.SubPolicyId.PolicyId.FrameworkId else None,
                'evidence': finding.Evidence,
                'check': finding.Check,
                'comments': finding.Comments,
                'major_minor': finding.MajorMinor
            })

        # Log success
        send_log(
            module="Audit",
            actionType="GET_AUDIT_COMPLIANCES_SUCCESS",
            description=f"Retrieved {len(compliance_data)} compliances for audit ID {audit_id}",
            userId=user_id,
            entityType="Audit",
            entityId=str(audit_id)
        )

        return Response({
            'audit_id': audit_id,
            'compliances': compliance_data
        }, status=status.HTTP_200_OK)

    except Audit.DoesNotExist:
        send_log(
            module="Audit",
            actionType="GET_AUDIT_COMPLIANCES_NOT_FOUND",
            description=f"Audit with ID {audit_id} not found",
            userId=user_id if 'user_id' in locals() else None,
            entityType="Audit",
            entityId=str(audit_id),
            logLevel="ERROR"
        )
        return Response({
            'error': f'Audit with ID {audit_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        send_log(
            module="Audit",
            actionType="GET_AUDIT_COMPLIANCES_ERROR",
            description=f"Error fetching compliance data: {str(e)}",
            userId=user_id if 'user_id' in locals() else None,
            entityType="Audit",
            entityId=str(audit_id),
            logLevel="ERROR"
        )
        return Response({
            'error': f'Error fetching compliance data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditAssignPermission])
@audit_assign_required
def add_compliance_to_audit(request, audit_id):
    """
    Add a new compliance item to an audit and create the corresponding audit finding.
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
        return response
    
    try:
        # Validate audit_id parameter
        try:
            validated_audit_id = validate_int(audit_id, min_value=1, field_name="Audit ID")
        except ValidationError as e:
            return Response({
                'error': f'Invalid audit ID: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse and validate request data
        try:
            if hasattr(request, 'data'):
                raw_data = request.data
            else:
                raw_data = json.loads(request.body)
        except (json.JSONDecodeError, AttributeError) as e:
            return Response({
                'error': 'Invalid JSON in request body'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate the new compliance data using centralized validation
        try:
            validated_data = validate_new_compliance_data(raw_data)
        except ValidationError as e:
            return Response({
                'error': f'Validation error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the audit to extract SubPolicyId
        try:
            audit = Audit.objects.get(AuditId=validated_audit_id)
        except Audit.DoesNotExist:
            return Response({
                'error': f'Audit with ID {validated_audit_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create new compliance record based on actual database schema using validated data
        compliance_data = {
            'PreviousComplianceVersionId': None,
            'Identifier': validated_data['identifier'],
            'ComplianceTitle': validated_data['complianceTitle'],
            'ComplianceItemDescription': validated_data['complianceItemDescription'],
            'ComplianceType': validated_data['complianceType'],
            'Scope': validated_data['scope'],
            'Objective': validated_data['objective'],
            'BusinessUnitsCovered': '',  # Default value
            'IsRisk': validated_data['isRisk'],
            'PossibleDamage': validated_data['possibleDamage'],
            'mitigation': validated_data['mitigation'],
            'Criticality': validated_data['criticality'],
            'MandatoryOptional': 'Optional',  # Default value
            'ManualAutomatic': 'Manual',      # Default value
            'Impact': validated_data['impact'],
            'Probability': validated_data['probability'],
            'MaturityLevel': 'Medium',        # Default value
            'ActiveInactive': 'Active',       # Default value
            'PermanentTemporary': 'Temporary',
            'CreatedByName': '1050',  # Default user ID
            'CreatedByDate': timezone.now(),
            'ComplianceVersion': '1.0',       # Default version
            'Status': 'Active',               # Default value
            'Applicability': 'Applicable'     # Default value
        }
        
        # Handle SubPolicyId - it's a required field in the Compliance model
        if audit.SubPolicyId_id is not None:
            compliance_data['SubPolicyId_id'] = audit.SubPolicyId_id
        elif audit.PolicyId_id is not None:
            # If audit has PolicyId but no SubPolicyId, get the first SubPolicy for that Policy
            try:
                sub_policy = SubPolicy.objects.filter(PolicyId_id=audit.PolicyId_id).first()
                if sub_policy:
                    compliance_data['SubPolicyId_id'] = sub_policy.SubPolicyId
                else:
                    # If no SubPolicy found for this Policy, get the first SubPolicy in the system
                    sub_policy = SubPolicy.objects.first()
                    if sub_policy:
                        compliance_data['SubPolicyId_id'] = sub_policy.SubPolicyId
                    else:
                        return Response({
                            'error': 'No SubPolicy found in the system. Cannot create compliance without a SubPolicy.'
                        }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"Error finding SubPolicy: {str(e)}")
                return Response({
                    'error': f'Error finding SubPolicy: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # If audit has no PolicyId or SubPolicyId, get the first SubPolicy in the system
            try:
                sub_policy = SubPolicy.objects.first()
                if sub_policy:
                    compliance_data['SubPolicyId_id'] = sub_policy.SubPolicyId
                else:
                    return Response({
                        'error': 'No SubPolicy found in the system. Cannot create compliance without a SubPolicy.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"Error finding SubPolicy: {str(e)}")
                return Response({
                    'error': f'Error finding SubPolicy: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Print debug info
        print(f"Creating compliance with data: {compliance_data}")
        
        new_compliance = Compliance.objects.create(**compliance_data)
        
        # Get the AssignedDate from the audit
        assigned_date = audit.AssignedDate
        
        # If audit has no AssignedDate, get it from existing audit findings or use current time
        if not assigned_date:
            existing_findings = AuditFinding.objects.filter(AuditId=audit_id).order_by('AssignedDate')
            if existing_findings.exists():
                assigned_date = existing_findings.first().AssignedDate
            else:
                # If still no date, use current time
                assigned_date = timezone.now()
                # Update the audit with this date to maintain consistency
                audit.AssignedDate = assigned_date
                audit.save()
        
        # Create audit finding for this compliance
        audit_finding = AuditFinding.objects.create(
            AuditId=audit,
            ComplianceId=new_compliance,
            UserId_id=audit.Auditor_id,
            Evidence='',
            Check='0',  # Default to "Not Compliant"
            Comments='',
            MajorMinor=None,
            AssignedDate=assigned_date,  # Use the AssignedDate from the audit
            ReviewRejected=0  # Default value for ReviewRejected
        )
        
        # Create a new audit version to include the new compliance
        user_id = request.session.get('user_id', audit.Auditor_id)
        new_version = None
        
        try:
            # First, check if there's an existing version and get its data
            existing_version_data = None
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT Version, ExtractedInfo FROM audit_version 
                    WHERE AuditId = %s AND Version LIKE 'A%' 
                    ORDER BY Version DESC, Date DESC 
                    LIMIT 1
                """, [validated_audit_id])
                
                version_row = cursor.fetchone()
                if version_row:
                    try:
                        print(f"Found version {version_row[0]} for audit {audit_id}")
                        print(f"ExtractedInfo type: {type(version_row[1])}")
                        
                        # Handle different data types that might be returned
                        if isinstance(version_row[1], dict):
                            existing_version_data = version_row[1]
                            print("ExtractedInfo is already a dictionary")
                        elif isinstance(version_row[1], str):
                            existing_version_data = json.loads(version_row[1])
                            print(f"Parsed ExtractedInfo from string, got {type(existing_version_data)}")
                        else:
                            print(f"WARNING: ExtractedInfo has unexpected type: {type(version_row[1])}")
                            # Try to convert to string and parse as JSON as a last resort
                            existing_version_data = json.loads(str(version_row[1]))
                            
                        if existing_version_data:
                            print(f"Found existing version data with {len(existing_version_data)} items")
                            print(f"Version data keys: {list(existing_version_data.keys())[:10]} (showing first 10)")
                    except Exception as e:
                        print(f"Error parsing existing version data: {str(e)}")
                        print(f"Raw version data (first 200 chars): {str(version_row[1])[:200]}")
                        existing_version_data = None
            
            # If we have existing version data, add the new compliance to it
            if existing_version_data and isinstance(existing_version_data, dict):
                print("Adding new compliance to existing version data")
                
                # Add the new compliance to the existing version data
                compliance_id = str(new_compliance.ComplianceId)
                print(f"Adding compliance ID {compliance_id} to version data")
                
                existing_version_data[compliance_id] = {
                    'description': new_compliance.ComplianceItemDescription,
                    'status': '0',  # Default to "Not Compliant"
                    'compliance_status': 'Not Compliant',
                    'comments': '',
                    'evidence': '',
                    'how_to_verify': '',
                    'impact': new_compliance.Impact or '',
                    'recommendation': '',
                    'details_of_finding': '',
                    'major_minor': '0',  # Default to "Minor"
                    'criticality': 'Minor',
                    'review_status': 'In Review',
                    'review_comments': '',
                    'reviewer_comments': '',
                    'accept_reject': '0',  # 0=In Review, 1=Accept, 2=Reject
                    'severity_rating': '',
                    'why_to_verify': '',
                    'what_to_verify': '',
                    'underlying_cause': '',
                    'suggested_action_plan': '',
                    'responsible_for_plan': '',
                    'mitigation_date': '',
                    're_audit': False,
                    're_audit_date': '',
                    'selected_risks': [],
                    'selected_mitigations': []
                }
                
                # Make sure __metadata__ exists
                if '__metadata__' not in existing_version_data:
                    existing_version_data['__metadata__'] = {
                        'user_id': user_id,
                        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'version_type': 'Auditor',
                        'overall_status': 'Pending',
                        'ApprovedRejected': 'Pending',
                        'audit_evidence': '',
                        'audit_title': audit.Title or '',
                        'audit_scope': audit.Scope or '',
                        'audit_objective': audit.Objective or '',
                        'business_unit': audit.BusinessUnit or ''
                    }
                
                # Create a new version with the updated data
                from .views import get_next_version_number
                next_version = get_next_version_number(audit_id, "A")
                
                print(f"Creating new version {next_version} with updated data")
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO audit_version (AuditId, Version, ExtractedInfo, UserId, Date) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, [
                        audit_id,
                        next_version,
                        json.dumps(existing_version_data),
                        user_id,
                        datetime.datetime.now()
                    ])
                
                print(f"Created new audit version {next_version} with merged data")
                new_version = next_version
            else:
                # If no existing version or error parsing it, create a new version from scratch
                print("No existing version found or error parsing it, creating new version from scratch")
                new_version = create_audit_version(audit_id, user_id)
                print(f"Created new audit version {new_version} after adding compliance")
                
        except Exception as e:
            print(f"Warning: Failed to create audit version: {str(e)}")
            import traceback
            traceback.print_exc()
            # Don't fail the overall operation if version creation fails
        
        # Return success response with compliance details
        from django.http import JsonResponse
        response = JsonResponse({
            'success': True,
            'message': 'Compliance added successfully',
            'compliance': {
                'id': new_compliance.ComplianceId,
                'identifier': new_compliance.Identifier,
                'complianceTitle': new_compliance.ComplianceTitle,
                'complianceItemDescription': new_compliance.ComplianceItemDescription,
                'complianceType': new_compliance.ComplianceType,
                'scope': new_compliance.Scope,
                'objective': new_compliance.Objective,
                'isRisk': new_compliance.IsRisk,
                'possibleDamage': new_compliance.PossibleDamage,
                'mitigation': new_compliance.mitigation,
                'criticality': new_compliance.Criticality,
                'mandatoryOptional': new_compliance.MandatoryOptional,
                'manualAutomatic': new_compliance.ManualAutomatic,
                'impact': new_compliance.Impact,
                'probability': new_compliance.Probability,
                'activeInactive': new_compliance.ActiveInactive,
                'permanentTemporary': new_compliance.PermanentTemporary,
                'createdByName': new_compliance.CreatedByName,
                'createdByDate': new_compliance.CreatedByDate,
                'complianceVersion': new_compliance.ComplianceVersion,
                'status': new_compliance.Status,
                'applicability': new_compliance.Applicability
            },
            'audit_finding_id': audit_finding.AuditFindingsId,
            'version_updated': True,
            'current_version': new_version,
            'version_date': datetime.now().isoformat(),
            'refresh_required': True  # Signal to frontend that a full refresh is needed
        }, status=status.HTTP_201_CREATED)
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
        
        return response
        
    except Exception as e:
        import traceback
        from django.http import JsonResponse
        
        error_traceback = traceback.format_exc()
        print(f"Error adding compliance: {str(e)}")
        print(f"Traceback: {error_traceback}")
        
        response = JsonResponse({
            'error': f'Error adding compliance: {str(e)}',
            'traceback': error_traceback
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
        
        return response

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def bulk_update_findings(request):
    """
    Bulk update audit findings
    """
    try:
        data = request.data
        audit_id = data.get('audit_id')
        findings = data.get('findings', [])
        user_id = request.session.get('user_id')

        if not audit_id or not findings:
            send_log(
                module="Audit",
                actionType="BULK_UPDATE_FINDINGS_VALIDATION_ERROR",
                description="Missing required parameters: audit_id or findings",
                userId=user_id,
                entityType="AuditFinding",
                logLevel="ERROR"
            )
            return Response({
                'error': 'audit_id and findings are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Log the bulk update attempt
        send_log(
            module="Audit",
            actionType="BULK_UPDATE_FINDINGS_ATTEMPT",
            description=f"Attempting to update {len(findings)} findings for audit ID {audit_id}",
            userId=user_id,
            entityType="AuditFinding",
            entityId=str(audit_id),
            additionalInfo={"finding_count": len(findings)}
        )

        # Get the audit
        try:
            audit = Audit.objects.get(AuditId=audit_id)
        except Audit.DoesNotExist:
            send_log(
                module="Audit",
                actionType="BULK_UPDATE_FINDINGS_AUDIT_NOT_FOUND",
                description=f"Audit with ID {audit_id} not found",
                userId=user_id,
                entityType="Audit",
                entityId=str(audit_id),
                logLevel="ERROR"
            )
            return Response({
                'error': f'Audit with ID {audit_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Update each finding
        updated_findings = []
        for finding_data in findings:
            finding_id = finding_data.get('finding_id')
            try:
                finding = AuditFinding.objects.get(AuditFindingId=finding_id)
                
                # Update fields
                finding.Check = finding_data.get('check', finding.Check)
                finding.Evidence = finding_data.get('evidence', finding.Evidence)
                finding.Comments = finding_data.get('comments', finding.Comments)
                finding.MajorMinor = finding_data.get('major_minor', finding.MajorMinor)
                
                finding.save()
                updated_findings.append(finding_id)
                
                # Log individual finding update
                send_log(
                    module="Audit",
                    actionType="UPDATE_FINDING",
                    description=f"Updated finding ID {finding_id} for audit ID {audit_id}",
                    userId=user_id,
                    entityType="AuditFinding",
                    entityId=str(finding_id),
                    additionalInfo={
                        "audit_id": audit_id,
                        "check": finding.Check,
                        "major_minor": finding.MajorMinor
                    }
                )
            except AuditFinding.DoesNotExist:
                send_log(
                    module="Audit",
                    actionType="UPDATE_FINDING_NOT_FOUND",
                    description=f"Finding with ID {finding_id} not found",
                    userId=user_id,
                    entityType="AuditFinding",
                    entityId=str(finding_id),
                    logLevel="ERROR"
                )
                return Response({
                    'error': f'Finding with ID {finding_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)

        # Update audit status if needed
        total_findings = AuditFinding.objects.filter(AuditId=audit_id).count()
        completed_findings = AuditFinding.objects.filter(
            AuditId=audit_id,
            Check__in=['0', '1']  # Count both compliant and non-compliant as completed
        ).count()

        # Calculate completion percentage
        completion_percentage = (completed_findings / total_findings * 100) if total_findings > 0 else 0

        # Update audit status based on completion
        old_status = audit.Status
        if completion_percentage == 100:
            audit.Status = 'Completed'
        elif completion_percentage > 0:
            audit.Status = 'Work In Progress'
        audit.save()
        
        # Log status change if it occurred
        if old_status != audit.Status:
            send_log(
                module="Audit",
                actionType="AUDIT_STATUS_CHANGE",
                description=f"Audit status changed from '{old_status}' to '{audit.Status}'",
                userId=user_id,
                entityType="Audit",
                entityId=str(audit_id),
                additionalInfo={
                    "old_status": old_status,
                    "new_status": audit.Status,
                    "completion_percentage": completion_percentage
                }
            )

        # Log overall success
        send_log(
            module="Audit",
            actionType="BULK_UPDATE_FINDINGS_SUCCESS",
            description=f"Successfully updated {len(updated_findings)} findings for audit ID {audit_id}",
            userId=user_id,
            entityType="AuditFinding",
            entityId=str(audit_id),
            additionalInfo={
                "updated_findings_count": len(updated_findings),
                "completion_percentage": completion_percentage
            }
        )

        return Response({
            'message': 'Findings updated successfully',
            'updated_findings': updated_findings,
            'completion_percentage': completion_percentage,
            'audit_status': audit.Status
        }, status=status.HTTP_200_OK)

    except Exception as e:
        user_id = request.session.get('user_id')
        send_log(
            module="Audit",
            actionType="BULK_UPDATE_FINDINGS_ERROR",
            description=f"Error updating findings: {str(e)}",
            userId=user_id,
            entityType="AuditFinding",
            entityId=str(audit_id) if 'audit_id' in locals() else None,
            logLevel="ERROR",
            additionalInfo={"error": str(e)}
        )
        return Response({
            'error': f'Error updating findings: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditAssignPermission])
@audit_assign_required
def get_compliance_count(request):
    """
    Get the count of permanent compliances for a policy or subpolicy
    """
    try:
        policy_id = request.GET.get('policy_id')
        subpolicy_id = request.GET.get('subpolicy_id')

        if not policy_id:
            return Response({
                'error': 'policy_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            # First, verify the policy exists
            cursor.execute("""
                SELECT PolicyId, PolicyName 
                FROM policies 
                WHERE PolicyId = %s
            """, [policy_id])
            policy = cursor.fetchone()
            
            if not policy:
                return Response({
                    'error': f'Policy with ID {policy_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # If subpolicy_id is provided, get compliances for that specific subpolicy
            if subpolicy_id:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM compliance c
                    WHERE c.SubPolicyId = %s
                    AND c.PermanentTemporary = 'Permanent'
                    AND c.Status = 'Approved'
                    AND c.ActiveInactive = 'Active'
                """, [subpolicy_id])
                
                count = cursor.fetchone()[0]
                
                # Get sample compliances for the specific subpolicy
                cursor.execute("""
                    SELECT c.ComplianceId, c.ComplianceTitle, c.SubPolicyId, c.PermanentTemporary,
                           sp.SubPolicyName, p.PolicyName
                    FROM compliance c
                    JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                    JOIN policies p ON sp.PolicyId = p.PolicyId
                    WHERE c.SubPolicyId = %s
                    AND c.PermanentTemporary = 'Permanent'
                    AND c.Status = 'Approved'
                    AND c.ActiveInactive = 'Active'
                    LIMIT 5
                """, [subpolicy_id])
                
            else:
                # Get all subpolicies for the policy
                cursor.execute("""
                    SELECT sp.SubPolicyId, sp.SubPolicyName
                    FROM subpolicies sp
                    WHERE sp.PolicyId = %s
                """, [policy_id])
                
                subpolicies = cursor.fetchall()
                
                if not subpolicies:
                    return Response({
                        'count': 0,
                        'message': 'No subpolicies found for the given policy',
                        'debug_info': {
                            'policy_id': policy_id,
                            'policy_name': policy[1],
                            'subpolicy_id': subpolicy_id
                        }
                    }, status=status.HTTP_200_OK)
                
                # Get compliance count for all subpolicies
                subpolicy_ids = [sp[0] for sp in subpolicies]
                placeholders = ','.join(['%s'] * len(subpolicy_ids))
                
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM compliance c
                    WHERE c.SubPolicyId IN ({placeholders})
                    AND c.PermanentTemporary = 'Permanent'
                    AND c.Status = 'Approved'
                    AND c.ActiveInactive = 'Active'
                """, subpolicy_ids)
                
                count = cursor.fetchone()[0]
                
                # Get sample compliances
                cursor.execute(f"""
                    SELECT c.ComplianceId, c.ComplianceTitle, c.SubPolicyId, c.PermanentTemporary,
                           sp.SubPolicyName, p.PolicyName
                    FROM compliance c
                    JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                    JOIN policies p ON sp.PolicyId = p.PolicyId
                    WHERE c.SubPolicyId IN ({placeholders})
                    AND c.PermanentTemporary = 'Permanent'
                    AND c.Status = 'Approved'
                    AND c.ActiveInactive = 'Active'
                    LIMIT 5
                """, subpolicy_ids)
            
            sample_compliances = cursor.fetchall()
            print(f"Sample compliances: {sample_compliances}")

            # Prepare detailed response
            response_data = {
                'count': count,
                'message': f'Found {count} approved and active permanent compliance items',
                'debug_info': {
                    'policy_id': policy_id,
                    'policy_name': policy[1],
                    'subpolicy_id': subpolicy_id,
                    'filters_applied': {
                        'permanent_temporary': 'Permanent',
                        'status': 'Approved',
                        'active_inactive': 'Active'
                    },
                    'sample_compliances': [
                        {
                            'id': c[0],
                            'title': c[1],
                            'subpolicy_id': c[2],
                            'permanent_temporary': c[3],
                            'subpolicy_name': c[4],
                            'policy_name': c[5]
                        } for c in sample_compliances
                    ] if sample_compliances else []
                }
            }

            # Add additional debug info for troubleshooting
            if count == 0:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM compliance
                    WHERE PermanentTemporary = 'Permanent'
                    AND Status = 'Approved'
                    AND ActiveInactive = 'Active'
                """)
                total_permanent = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM compliance
                    WHERE PermanentTemporary = 'Permanent'
                    AND Status = 'Approved'
                """)
                total_approved = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM compliance
                    WHERE PermanentTemporary = 'Permanent'
                    AND Status = 'Approved'
                    AND ActiveInactive = 'Active'
                """)
                total_active = cursor.fetchone()[0]
                
                response_data['debug_info']['total_permanent_compliances'] = total_permanent
                response_data['debug_info']['total_approved_compliances'] = total_approved
                response_data['debug_info']['total_active_compliances'] = total_active

            return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        print(f"Error in get_compliance_count: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditViewPermission])
@audit_view_reports_required
def get_report_details(request):
    """Get detailed information about specific reports"""
    try:
        report_ids = request.GET.get('report_ids', '').split(',')
        if not report_ids or not report_ids[0]:
            return Response({
                'error': 'report_ids parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            # Get report details including auditor name
            placeholders = ','.join(['%s'] * len(report_ids))
            cursor.execute(f"""
                SELECT r.ReportId, r.Report, r.CompletionDate, u.UserName as auditor_name
                FROM reports r
                LEFT JOIN users u ON r.AuditorId = u.UserId
                WHERE r.ReportId IN ({placeholders})
            """, report_ids)
            
            columns = [col[0] for col in cursor.description]
            reports = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

            return Response({
                'reports': [{
                    'report_id': report['ReportId'],
                    'report': report['Report'],
                    'completion_date': report['CompletionDate'].isoformat() if report['CompletionDate'] else None,
                    'auditor_name': report['auditor_name']
                } for report in reports]
            }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error fetching report details: {str(e)}")
        return Response({
            'error': f'Error fetching report details: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)