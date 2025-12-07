from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from ...models import Audit, AuditVersion
from django.db import connection
import json,datetime
from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.parsers import MultiPartParser, FormParser
from .framework_filter_helper import get_active_framework_filter, apply_framework_filter_to_audits, get_framework_sql_filter

# Custom authentication class for CSRF exempt sessions
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

# from datetime import datetime, date
from ...routes.Global.validation import (
    validate_int, validate_audit_version_data, validate_new_compliance_data, 
    ValidationError
)
from django.utils.decorators import method_decorator
from ...routes.Global.logging_service import send_log
from ...routes.Global.s3_fucntions import create_direct_mysql_client
import os
import tempfile
from ...rbac.permissions import (
    AuditConductPermission, AuditReviewPermission, AuditAssignPermission
)
from ...rbac.decorators import (
    audit_conduct_required,
    audit_review_required,
    audit_assign_required
)

# Custom JSON encoder to handle date objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def get_audit_task_details(request, audit_id):
    """
    Get detailed information about a specific audit for the task view.
    Load the latest version data from audit_version table if available.
    """
    try:
        # Validate audit_id parameter
        try:
            validated_audit_id = validate_int(audit_id, min_value=1, field_name="Audit ID")
        except ValidationError as e:
            return JsonResponse({
                'error': f'Invalid audit ID: {str(e)}'
            }, status=400)
        
        print(f"Fetching audit details for audit_id: {validated_audit_id}")
        
        # Use raw SQL to get audit details with related data
        with connection.cursor() as cursor:
            # First get the audit details including evidence
            cursor.execute("""
                SELECT 
                    a.AuditId,
                    a.Title,
                    a.Scope,
                    a.Objective,
                    a.BusinessUnit,
                    a.Evidence,
                    f.FrameworkName,
                    p.PolicyName,
                    sp.SubPolicyName,
                    a.Comments
                FROM 
                    audit a
                LEFT JOIN
                    frameworks f ON a.FrameworkId = f.FrameworkId
                LEFT JOIN
                    policies p ON a.PolicyId = p.PolicyId
                LEFT JOIN
                    subpolicies sp ON a.SubPolicyId = sp.SubPolicyId
                WHERE 
                    a.AuditId = %s
            """, [validated_audit_id])
            
            audit_row = cursor.fetchone()
            if not audit_row:
                return JsonResponse({
                    'error': f'Audit with ID {validated_audit_id} not found'
                }, status=404)
                
            # Store audit details for later use
            audit_id_val = audit_row[0]
            audit_title = audit_row[1] or 'Not Specified'
            audit_scope = audit_row[2] or 'Not Specified'
            audit_objective = audit_row[3] or 'Not Specified'
            audit_business_unit = audit_row[4] or 'Not Specified'
            audit_evidence = audit_row[5] or ''
            framework_name = audit_row[6] or 'Not Specified'
            policy_name = audit_row[7] or 'Not Specified'
            subpolicy_name = audit_row[8] or 'Not Specified'
            audit_comments = audit_row[9] or ''
            
            print(f"Found audit: {audit_title} with ID {audit_id_val}")

            # Check for the latest version in audit_version table
            cursor.execute("""
                SELECT Version, ExtractedInfo, Date 
                FROM audit_version 
                WHERE AuditId = %s 
                ORDER BY Date DESC, Version DESC 
                LIMIT 1
            """, [validated_audit_id])
            
            version_row = cursor.fetchone()
            
            # Try to load from version first, fall back to audit_findings if any issues
            if version_row:
                # Load data from the latest version
                print(f"Loading data from version: {version_row[0]} dated: {version_row[2]}")
                
                try:
                    # Parse the JSON data - handle both string and already parsed data
                    extracted_info = version_row[1]
                    print(f"Raw extracted_info type: {type(extracted_info)}")
                    
                    if isinstance(extracted_info, str):
                        version_data = json.loads(extracted_info)
                    elif isinstance(extracted_info, dict):
                        version_data = extracted_info
                    else:
                        print(f"Unexpected data type for ExtractedInfo: {type(extracted_info)}")
                        raise TypeError(f"ExtractedInfo is neither string nor dict: {type(extracted_info)}")
                    
                    print(f"Version data type: {type(version_data)}")
                    
                    if not isinstance(version_data, dict):
                        print(f"Version data is not a dictionary: {type(version_data)}")
                        raise TypeError("Version data is not a dictionary")
                    
                    print(f"Version data keys: {list(version_data.keys())}")
                    
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    print(f"Error parsing version data: {str(e)}")
                    print(f"Raw version data (first 200 chars): {str(version_row[1])[:200]}")
                    # Fall back to loading from audit_findings
                    print("Falling back to audit_findings table due to version data error")
                    version_row = None
                    version_data = None
                
                if version_data and isinstance(version_data, dict):
                    # Extract compliance data from version
                    compliances = []
                    
                    # Get all compliance IDs from both version data and audit_findings
                    compliance_ids = set()
                    
                    # Add compliance IDs from version data
                    for key in version_data.keys():
                        if key.isdigit():
                            compliance_ids.add(int(key))
                    
                    # Add compliance IDs from audit_findings table to ensure we get newly added compliances
                    cursor.execute("""
                        SELECT DISTINCT ComplianceId FROM audit_findings WHERE AuditId = %s
                    """, [validated_audit_id])
                    
                    for finding_row in cursor.fetchall():
                        compliance_ids.add(finding_row[0])
                    
                    print(f"Found {len(compliance_ids)} total compliance IDs to process")
                    
                    # Process each compliance ID
                    for compliance_id in compliance_ids:
                        compliance_id_str = str(compliance_id)
                        
                        # Get compliance data from version if available
                        compliance_data = version_data.get(compliance_id_str, {})
                        
                        # Get risks for this compliance from the risk table
                        cursor.execute("""
                            SELECT r.RiskId, r.RiskTitle, r.Category, r.RiskType, r.RiskMitigation
                            FROM risk r
                            WHERE r.ComplianceId = %s
                        """, [compliance_id])
                        
                        risks = []
                        for risk_row in cursor.fetchall():
                            risks.append({
                                'id': risk_row[0],
                                'title': risk_row[1],
                                'category': risk_row[2],
                                'type': risk_row[3],
                                'mitigation': risk_row[4] or ''
                            })
                        
                        # Get compliance description from compliance table
                        cursor.execute("""
                            SELECT ComplianceItemDescription 
                            FROM compliance 
                            WHERE ComplianceId = %s
                        """, [compliance_id])
                        
                        desc_row = cursor.fetchone()
                        description = desc_row[0] if desc_row else compliance_data.get('description', '')
                        
                        # If this is a newly added compliance not in version data, get its details from audit_findings
                        if not compliance_data and desc_row:
                            cursor.execute("""
                                SELECT 
                                    `Check`, Evidence, Comments, HowToVerify, Impact, 
                                    Recommendation, DetailsOfFinding, MajorMinor
                                FROM audit_findings 
                                WHERE AuditId = %s AND ComplianceId = %s
                            """, [validated_audit_id, compliance_id])
                            
                            finding_row = cursor.fetchone()
                            if finding_row:
                                compliance_data = {
                                    'status': finding_row[0] or '0',
                                    'evidence': finding_row[1] or '',
                                    'comments': finding_row[2] or '',
                                    'how_to_verify': finding_row[3] or '',
                                    'impact': finding_row[4] or '',
                                    'recommendation': finding_row[5] or '',
                                    'details_of_finding': finding_row[6] or '',
                                    'major_minor': finding_row[7] or '0',
                                    'criticality': 'Major' if finding_row[7] == '1' else 'Minor'
                                }
                        
                        # Skip if we couldn't find any data for this compliance
                        if not description:
                            print(f"Skipping compliance ID {compliance_id} - no description found")
                            continue
                        
                        # Convert criticality to major_minor numeric format
                        criticality = compliance_data.get('criticality', '').strip().lower() if compliance_data.get('criticality') else ''
                        major_minor_value = ''
                        if criticality == 'major':
                            major_minor_value = '1'  # Major: 1
                        elif criticality == 'minor':
                            major_minor_value = '0'  # Minor: 0
                        elif criticality == 'not applicable':
                            major_minor_value = '2'
                            
                        compliances.append({
                            'id': compliance_id,
                            'description': description,
                            'status': compliance_data.get('compliance_status', '0'),
                            'evidence': compliance_data.get('evidence', ''),
                            'comments': compliance_data.get('comments', ''),
                            'how_to_verify': compliance_data.get('how_to_verify', ''),
                            'impact': compliance_data.get('impact', ''),
                            'recommendation': compliance_data.get('recommendation', ''),
                            'details_of_finding': compliance_data.get('details_of_finding', ''),
                            'major_minor': major_minor_value,
                            'severity_rating': compliance_data.get('severity_rating', ''),
                            'why_to_verify': compliance_data.get('why_to_verify', ''),
                            'what_to_verify': compliance_data.get('what_to_verify', ''),
                            'underlying_cause': compliance_data.get('underlying_cause', ''),
                            'suggested_action_plan': compliance_data.get('suggested_action_plan', ''),
                            'responsible_for_plan': compliance_data.get('responsible_for_plan', ''),
                            'mitigation_date': compliance_data.get('mitigation_date', ''),
                            're_audit': compliance_data.get('re_audit', False),
                            're_audit_date': compliance_data.get('re_audit_date', ''),
                            'risks': risks,
                            'selected_risks': compliance_data.get('selected_risks', []),
                            'selected_mitigations': compliance_data.get('selected_mitigations', []),
                            'review_status': compliance_data.get('review_status', 'in_review'),
                            'review_comments': compliance_data.get('review_comments', ''),
                            'accept_reject': compliance_data.get('accept_reject', '0')
                        })
                    
                    # Get metadata for audit evidence
                    metadata = version_data.get('__metadata__', {})
                    audit_evidence = metadata.get('audit_evidence', audit_evidence)
                    
                    # Get comments, prioritizing the correct sources
                    # For audit comments, check version_data['overall_comments'] first, 
                    # then metadata['overall_comments']
                    overall_audit_comments = ''
                    if 'overall_comments' in version_data:
                        overall_audit_comments = version_data.get('overall_comments', '')
                    elif 'overall_comments' in metadata:
                        overall_audit_comments = metadata.get('overall_comments', '')
                    
                    # For review comments, use version_data['overall_review_comments']
                    overall_review_comments = version_data.get('overall_review_comments', '')
                    
                    # Return data from version
                    print(f"Returning data from version {version_row[0]} with {len(compliances)} compliance items")
                    send_log(module="Auditing", actionType="GET_AUDIT_TASK_DETAILS", description="Fetched audit task details", userId=request.session.get('user_id'), entityType="Audit", entityId=audit_id)
                    return JsonResponse({
                        'title': metadata.get('audit_title', audit_title),
                        'scope': metadata.get('audit_scope', audit_scope),
                        'objective': metadata.get('audit_objective', audit_objective),
                        'business_unit': metadata.get('business_unit', audit_business_unit),
                        'evidence_urls': audit_evidence,
                        'framework_name': framework_name,
                        'policy_name': policy_name,
                        'subpolicy_name': subpolicy_name,
                        'compliances': compliances,
                        'current_version': version_row[0],
                        'version_date': version_row[2].isoformat() if version_row[2] else None,
                        'loaded_from_version': True,
                        'overall_audit_comments': overall_audit_comments,
                        'overall_review_comments': overall_review_comments
                    })
                else:
                    # If version data is invalid, fall back to audit_findings
                    print("Version data is invalid, falling back to audit_findings table")
                    version_row = None
            
            # If no version found or version data is invalid, load from audit_findings table
            if not version_row:
                print("No valid version found, loading from audit_findings table")

            # Get compliance items and associated risks for this audit
            cursor.execute("""
                SELECT 
                    af.ComplianceId,
                    c.ComplianceItemDescription,
                    af.`Check`,
                    af.Evidence,
                    af.Comments,
                    af.HowToVerify,
                    af.Impact,
                    af.Recommendation,
                    af.DetailsOfFinding,
                    af.MajorMinor,
                    af.SeverityRating,
                    af.WhyToVerify,
                    af.WhatToVerify,
                    af.UnderlyingCause,
                    af.SuggestedActionPlan,
                    af.ResponsibleForPlan,
                    af.MitigationDate,
                    af.ReAudit,
                    af.ReAuditDate,
                    r.RiskId,
                    r.RiskTitle,
                    r.Category,
                    r.RiskType,
                    r.RiskMitigation,
                    af.ReviewStatus,
                    af.ReviewComments,
                    af.ReviewRejected
                FROM 
                    audit_findings af
                JOIN
                    compliance c ON af.ComplianceId = c.ComplianceId
                LEFT JOIN
                    risk r ON c.ComplianceId = r.ComplianceId
                WHERE 
                    af.AuditId = %s
                ORDER BY
                    af.ComplianceId, r.RiskId
            """, [validated_audit_id])
            
            compliances = {}
            for comp_row in cursor.fetchall():
                compliance_id = comp_row[0]
                
                if compliance_id not in compliances:
                    # Map ReviewStatus and ReviewRejected to review_status
                    review_status = 'in_review'
                    if comp_row[24]:  # ReviewStatus
                        if comp_row[24] == 'Accept':
                            review_status = 'accept'
                        elif comp_row[24] == 'Reject':
                            review_status = 'reject'
                    
                    # Map ReviewRejected to accept_reject
                    accept_reject = '0'  # Default to in_review
                    if comp_row[26] is not None:  # ReviewRejected
                        if comp_row[26] == 0:
                            accept_reject = '1'  # Accepted
                        elif comp_row[26] == 1:
                            accept_reject = '2'  # Rejected

                    compliances[compliance_id] = {
                        'id': compliance_id,
                        'description': comp_row[1],
                        'status': comp_row[2],
                        'evidence': comp_row[3] or '',
                        'comments': comp_row[4] or '',
                        'how_to_verify': comp_row[5] or '',
                        'impact': comp_row[6] or '',
                        'recommendation': comp_row[7] or '',
                        'details_of_finding': comp_row[8] or '',
                        'major_minor': comp_row[9] or '',
                        'severity_rating': comp_row[10] or '',
                        'why_to_verify': comp_row[11] or '',
                        'what_to_verify': comp_row[12] or '',
                        'underlying_cause': comp_row[13] or '',
                        'suggested_action_plan': comp_row[14] or '',
                        'responsible_for_plan': comp_row[15] or '',
                        'mitigation_date': comp_row[16].isoformat() if comp_row[16] else '',
                        're_audit': bool(comp_row[17]) if comp_row[17] is not None else False,
                        're_audit_date': comp_row[18].isoformat() if comp_row[18] else '',
                        'risks': [],
                        'review_status': review_status,
                        'review_comments': comp_row[25] or '',  # ReviewComments
                        'accept_reject': accept_reject
                    }
                
                # Add risk if it exists
                if comp_row[19]:  # If RiskId exists
                    compliances[compliance_id]['risks'].append({
                        'id': comp_row[19],
                        'title': comp_row[20],
                        'category': comp_row[21],
                        'type': comp_row[22],
                        'mitigation': comp_row[23] or ''
                    })
            
            # Create initial A1 version if no version exists
            if not version_row:
                print("Creating initial A1 version from audit_findings data")
                
                # Prepare the initial version data
                initial_version_data = {}
                
                # Process compliance data
                for compliance_id, compliance_data in compliances.items():
                    initial_version_data[str(compliance_id)] = {
                        'description': compliance_data['description'],
                        'compliance_status': compliance_data['status'],
                        'evidence': compliance_data['evidence'],
                        'comments': compliance_data['comments'],
                        'how_to_verify': compliance_data['how_to_verify'],
                        'impact': compliance_data['impact'],
                        'recommendation': compliance_data['recommendation'],
                        'details_of_finding': compliance_data['details_of_finding'],
                        'criticality': 'Major' if compliance_data['major_minor'] == '1' else 'Minor' if compliance_data['major_minor'] == '0' else 'Not Applicable' if compliance_data['major_minor'] == '2' else '',
                        'severity_rating': compliance_data['severity_rating'],
                        'why_to_verify': compliance_data['why_to_verify'],
                        'what_to_verify': compliance_data['what_to_verify'],
                        'underlying_cause': compliance_data['underlying_cause'],
                        'suggested_action_plan': compliance_data['suggested_action_plan'],
                        'responsible_for_plan': compliance_data['responsible_for_plan'],
                        'mitigation_date': compliance_data['mitigation_date'],
                        're_audit': compliance_data['re_audit'],
                        're_audit_date': compliance_data['re_audit_date'],
                        'selected_risks': [],
                        'selected_mitigations': [],
                        'review_status': compliance_data['review_status'],
                        'review_comments': compliance_data['review_comments'],
                        'accept_reject': compliance_data['accept_reject']
                    }
                
                # Add metadata
                initial_version_data['__metadata__'] = {
                    'user_id': 1050,  # Default auditor ID
                    'created_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'version_type': 'Auditor',
                    'overall_status': 'Pending',
                    'ApprovedRejected': 'Pending',
                    'audit_evidence': audit_evidence,
                    'audit_title': audit_title,
                    'audit_scope': audit_scope,
                    'audit_objective': audit_objective,
                    'business_unit': audit_business_unit,
                    'overall_comments': audit_comments  # Store audit comments in metadata
                }
                
                # Add overall audit comments
                initial_version_data['overall_comments'] = audit_comments
                
                # Initialize overall review comments as empty
                initial_version_data['overall_review_comments'] = ''
                
                # Get FrameworkId from the audit
                cursor.execute("SELECT FrameworkId FROM audit WHERE AuditId = %s", [validated_audit_id])
                framework_row = cursor.fetchone()
                framework_id = framework_row[0] if framework_row else None
                
                # Insert the initial A1 version
                cursor.execute("""
                    INSERT INTO audit_version (AuditId, Version, ExtractedInfo, UserId, Date, ActiveInactive, FrameworkId)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    validated_audit_id,
                    'A1',
                    json.dumps(initial_version_data, cls=DateTimeEncoder),
                    1050,  # Default auditor ID
                    datetime.datetime.now(),
                    'A',
                    framework_id
                ])
                
                print(f"Created initial A1 version for audit {validated_audit_id}")
            
            # Return the combined data
            print(f"Returning data from audit_findings table with {len(compliances)} compliance items")
            send_log(module="Auditing", actionType="GET_AUDIT_TASK_DETAILS", description="Fetched audit task details", userId=request.session.get('user_id'), entityType="Audit", entityId=audit_id)
            return JsonResponse({
                'title': audit_title,
                'scope': audit_scope,
                'objective': audit_objective,
                'business_unit': audit_business_unit,
                'evidence_urls': audit_evidence,
                'framework_name': framework_name,
                'policy_name': policy_name,
                'subpolicy_name': subpolicy_name,
                'compliances': list(compliances.values()),
                'loaded_from_version': False,
                'current_version': 'A1' if not version_row else None,
                'version_date': datetime.datetime.now().isoformat() if not version_row else None,
                'overall_audit_comments': audit_comments,  # Comments from audit table
                'overall_review_comments': ''  # No review comments yet
            })
            
    except Exception as e:
        print(f"Error in get_audit_task_details: {str(e)}")
        send_log(module="Auditing", actionType="GET_AUDIT_TASK_DETAILS", description="Error fetching audit task details", userId=request.session.get('user_id'), entityType="Audit", entityId=audit_id, error=str(e))
        return JsonResponse({
            'error': str(e)
        }, status=500)

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def save_audit_version(request, audit_id):
    """
    Save audit form data as a version in audit_version table.
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
            return JsonResponse({
                'error': f'Invalid audit ID: {str(e)}'
            }, status=400)
        
        # Parse and validate request body
        try:
            raw_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON in request body'
            }, status=400)
        
        # Validate the audit version data
        try:
            validated_data = validate_audit_version_data(raw_data)
        except ValidationError as e:
            return JsonResponse({
                'error': f'Validation error: {str(e)}'
            }, status=400)
        
        # Get user ID from session or use validated user ID
        user_id = request.session.get('user_id', validated_data['user_id'])
        
        print(f"Saving audit version for audit_id: {validated_audit_id}")
        
        # Check for existing versions to preserve metadata
        with connection.cursor() as cursor:
            # First check for latest R version to get review data
            cursor.execute("""
                SELECT Version, ExtractedInfo FROM audit_version 
                WHERE AuditId = %s AND Version LIKE 'R%%' 
                ORDER BY CAST(SUBSTRING(Version, 2) AS UNSIGNED) DESC 
                LIMIT 1
            """, [validated_audit_id])
            
            r_version_result = cursor.fetchone()
            latest_review_data = {}
            latest_review_comments = None
            if r_version_result:
                try:
                    # Extract review data from latest R version
                    r_version_data = json.loads(r_version_result[1]) if isinstance(r_version_result[1], str) else r_version_result[1]
                    # Store review status and comments for each compliance
                    for compliance_id, compliance_data in r_version_data.items():
                        if compliance_id != '__metadata__':
                            latest_review_data[compliance_id] = {
                                'review_status': compliance_data.get('review_status', 'Pending'),
                                'review_comments': compliance_data.get('review_comments', ''),
                                'accept_reject': compliance_data.get('accept_reject', '0')
                            }
                    
                    # Preserve overall review comments if present
                    if 'overall_review_comments' in r_version_data:
                        latest_review_comments = r_version_data.get('overall_review_comments')
                except Exception as e:
                    print(f"Warning: Could not extract review data from R version: {str(e)}")

            # Get the current highest version number for this audit with 'A' prefix
            cursor.execute("""
                SELECT Version, ExtractedInfo FROM audit_version 
                WHERE AuditId = %s AND Version LIKE 'A%%' 
                ORDER BY CAST(SUBSTRING(Version, 2) AS UNSIGNED) DESC 
                LIMIT 1
            """, [validated_audit_id])
            
            result = cursor.fetchone()
            existing_metadata = {}
            if result:
                try:
                    # Extract metadata from existing version
                    existing_data = json.loads(result[1]) if isinstance(result[1], str) else result[1]
                    if '__metadata__' in existing_data:
                        existing_metadata = existing_data['__metadata__']
                    # Preserve overall comments if not provided in new data
                    if 'overall_comments' in existing_data and not validated_data.get('overall_comments'):
                        validated_data['overall_comments'] = existing_data.get('overall_comments', '')
                except Exception as e:
                    print(f"Warning: Could not extract metadata from existing version: {str(e)}")
                
                # Extract number from version (e.g., 'A3' -> 3)
                current_version_num = int(result[0][1:])
                new_version_num = current_version_num + 1
            else:
                new_version_num = 1
            
            new_version = f"A{new_version_num}"
            
            # Prepare the JSON data structure
            version_data = {}
            
            # Process compliance data
            compliances_data = validated_data.get('compliances', {})
            for compliance_id, compliance_data in compliances_data.items():
                version_data[str(compliance_id)] = {
                    'description': compliance_data.get('description', ''),
                    'compliance_status': compliance_data.get('status', ''),
                    'evidence': compliance_data.get('evidence', ''),
                    'comments': compliance_data.get('comments', ''),
                    'how_to_verify': compliance_data.get('how_to_verify', ''),
                    'impact': compliance_data.get('impact', ''),
                    'recommendation': compliance_data.get('recommendation', ''),
                    'details_of_finding': compliance_data.get('details_of_finding', ''),
                    'criticality': 'Major' if compliance_data.get('major_minor') == '1' else 'Minor' if compliance_data.get('major_minor') == '0' else 'Not Applicable' if compliance_data.get('major_minor') == '2' else '',
                    'severity_rating': compliance_data.get('severity_rating', ''),
                    'why_to_verify': compliance_data.get('why_to_verify', ''),
                    'what_to_verify': compliance_data.get('what_to_verify', ''),
                    'underlying_cause': compliance_data.get('underlying_cause', ''),
                    'suggested_action_plan': compliance_data.get('suggested_action_plan', ''),
                    'responsible_for_plan': compliance_data.get('responsible_for_plan', ''),
                    'mitigation_date': compliance_data.get('mitigation_date', ''),
                    're_audit': compliance_data.get('re_audit', False),
                    're_audit_date': compliance_data.get('re_audit_date', ''),
                    'selected_risks': compliance_data.get('selected_risks', []),
                    'selected_mitigations': compliance_data.get('selected_mitigations', [])
                }
                
                # Add review data from latest R version if available
                if str(compliance_id) in latest_review_data:
                    review_data = latest_review_data[str(compliance_id)]
                    version_data[str(compliance_id)].update({
                        'review_status': review_data['review_status'],
                        'review_comments': review_data['review_comments'],
                        'accept_reject': review_data['accept_reject']
                    })
                else:
                    # Default values if no review data exists
                    version_data[str(compliance_id)].update({
                        'review_status': 'Pending',
                        'review_comments': '',
                        'accept_reject': '0'
                    })
            
            # Add metadata including audit evidence
            audit_evidence_urls = validated_data.get('audit_evidence_urls', '')
            print(f"Saving audit evidence URLs: {audit_evidence_urls}")
            
            # Check if we need to append to existing evidence URLs
            existing_audit_evidence = existing_metadata.get('audit_evidence', '')
            if existing_audit_evidence and audit_evidence_urls:
                # Combine existing and new evidence URLs, avoiding duplicates
                existing_urls = existing_audit_evidence.split(',')
                new_urls = audit_evidence_urls.split(',')
                combined_urls = existing_urls
                for url in new_urls:
                    if url and url not in combined_urls:
                        combined_urls.append(url)
                combined_evidence = ','.join(combined_urls)
            else:
                combined_evidence = audit_evidence_urls or existing_audit_evidence
            
            # Merge existing metadata with new metadata
            metadata = {
                'user_id': user_id,
                'created_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version_type': 'Auditor',
                'overall_status': 'Pending',
                'ApprovedRejected': 'Pending',
                'audit_evidence': combined_evidence,
                'audit_title': validated_data.get('audit_title', ''),
                'audit_scope': validated_data.get('audit_scope', ''),
                'audit_objective': validated_data.get('audit_objective', ''),
                'business_unit': validated_data.get('business_unit', '')
            }
            
            # Preserve values from existing metadata if not provided in new data
            for key, value in existing_metadata.items():
                if key not in metadata or not metadata[key]:
                    metadata[key] = value
            
            # Make sure we don't accidentally store review comments in metadata
            # overall_comments in metadata should only contain audit comments
            if 'overall_comments' in existing_metadata:
                metadata['overall_comments'] = existing_metadata['overall_comments']
            
            version_data['__metadata__'] = metadata
            
            # Add overall audit comments to the version data
            # This is stored outside of metadata as well for easier access
            version_data['overall_comments'] = validated_data.get('overall_comments', '')
            print(f"Saving overall audit comments: {validated_data.get('overall_comments', '')}")
            
            # Preserve overall review comments if they exist from previous R version
            if latest_review_comments is not None:
                version_data['overall_review_comments'] = latest_review_comments
                print(f"Preserving existing overall review comments: {latest_review_comments}")
            
            # Update the audit table's Comments field with the overall audit comments
            cursor.execute("""
                UPDATE audit
                SET Comments = %s
                WHERE AuditId = %s
            """, [validated_data.get('overall_comments', ''), validated_audit_id])
            
            # Get FrameworkId from the audit
            cursor.execute("SELECT FrameworkId FROM audit WHERE AuditId = %s", [validated_audit_id])
            framework_row = cursor.fetchone()
            framework_id = framework_row[0] if framework_row else None
            
            # Insert the new version - use custom DateTimeEncoder to handle date objects
            cursor.execute("""
                INSERT INTO audit_version (AuditId, Version, ExtractedInfo, UserId, Date, ActiveInactive, FrameworkId)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [
                validated_audit_id,
                new_version,
                json.dumps(version_data, cls=DateTimeEncoder),  # Use custom JSON encoder
                user_id,
                datetime.datetime.now(),
                'A',
                framework_id
            ])
            
            print(f"Successfully saved audit version {new_version} for audit {validated_audit_id}")
            
            response = JsonResponse({
                'success': True,
                'message': f'Audit version {new_version} saved successfully',
                'version': new_version,
                'data': version_data
            }, encoder=DateTimeEncoder)  # Use custom encoder for the response too
            
            # Add CORS headers
            response["Access-Control-Allow-Origin"] = "http://localhost:8080"
            response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response["Access-Control-Allow-Credentials"] = "true"
            
            return response
            
    except Exception as e:
        print(f"Error in save_audit_version: {str(e)}")
        response = JsonResponse({
            'error': str(e)
        }, status=500)
        
        # Add CORS headers
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
        
        return response

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def send_audit_for_review(request, audit_id):
    """
    Update audit status to "Under Review" when auditor sends it for review.
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
            return JsonResponse({
                'error': f'Invalid audit ID: {str(e)}'
            }, status=400)
        
        # Parse and validate request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON in request body'
            }, status=400)
        
        # Validate version parameter if provided
        version = data.get('version', '')
        if version:
            # Basic version format validation
            if not isinstance(version, str) or len(version) > 10:
                return JsonResponse({
                    'error': 'Invalid version format'
                }, status=400)
        
        print(f"Sending audit {validated_audit_id} for review with version {version}")
        
        with connection.cursor() as cursor:
            # Update the audit status to "Under Review"
            cursor.execute("""
                UPDATE audit 
                SET Status = 'Under review'
                WHERE AuditId = %s
            """, [validated_audit_id])
            
            # Check if the update was successful
            if cursor.rowcount == 0:
                return JsonResponse({
                    'error': f'Audit with ID {validated_audit_id} not found'
                }, status=404)
            
            print(f"Successfully updated audit {validated_audit_id} status to 'Under Review'")
            
            response = JsonResponse({
                'success': True,
                'message': f'Audit {validated_audit_id} sent for review successfully',
                'audit_id': validated_audit_id,
                'version': version,
                'new_status': 'Under review'
            })
            
            # Add CORS headers
            response["Access-Control-Allow-Origin"] = "http://localhost:8080"
            response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response["Access-Control-Allow-Credentials"] = "true"
            
            return response
            
    except Exception as e:
        print(f"Error in send_audit_for_review: {str(e)}")
        response = JsonResponse({
            'error': str(e)
        }, status=500)
        
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
def update_audit_findings(request):
    """
    This endpoint is now deprecated - all updates should go through versioning system.
    """
    return JsonResponse({
        'error': 'Direct audit findings updates are not allowed. Please use the versioning system.',
        'success': False
    }, status=400)

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission])
@audit_conduct_required
def upload_evidence_to_s3(request):
    """
    Upload evidence files to S3 using the RenderS3Client.
    Handles both compliance evidence and audit evidence uploads.
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
        print(f"Request method: {request.method}")
        print(f"Content type: {request.content_type}")
        print(f"Request META: {dict(request.META)}")
        print(f"Request FILES keys: {list(request.FILES.keys())}")
        print(f"Request POST keys: {list(request.POST.keys())}")
        
        # Check if file is present
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file provided'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Get additional parameters
        user_id = request.POST.get('userId', 'default-user')
        document_type = request.POST.get('documentType', 'evidence')
        audit_id = request.POST.get('audit_id', '')
        compliance_id = request.POST.get('compliance_id', '')
        file_name = request.POST.get('fileName', uploaded_file.name)
        
        print(f"Uploading file: {file_name} for user: {user_id}, type: {document_type}")
        print(f"File size: {uploaded_file.size} bytes")
        print(f"File content type: {uploaded_file.content_type}")
        
        # Validate file size (max 50MB)
        max_file_size = 50 * 1024 * 1024  # 50MB in bytes
        if uploaded_file.size > max_file_size:
            return JsonResponse({
                'success': False,
                'error': f'File size exceeds maximum limit of 50MB. Current size: {uploaded_file.size / (1024*1024):.2f}MB'
            }, status=400)
        
        # Validate file type (basic validation)
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar']
        file_extension = os.path.splitext(file_name)[1].lower()
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': f'File type {file_extension} is not allowed. Allowed types: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # Create temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # Write uploaded file to temporary file
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # Create S3 client
            s3_client = create_direct_mysql_client()
            
            # Test connection first
            connection_test = s3_client.test_connection()
            if not connection_test.get('overall_success', False):
                return JsonResponse({
                    'success': False,
                    'error': 'S3 service is currently unavailable. Please try again later.',
                    'details': connection_test
                }, status=503)
            
            # Generate unique file name to avoid conflicts
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_file_name = f"{document_type}_{audit_id}_{compliance_id}_{timestamp}_{file_name}"
            
            # Upload to S3
            print(f"Uploading to S3 with filename: {unique_file_name}")
            upload_result = s3_client.upload(
                file_path=temp_file_path,
                user_id=user_id,
                custom_file_name=unique_file_name,
                module='Audit'
            )
            
            if upload_result.get('success'):
                file_info = upload_result.get('file_info', {})
                
                # Prepare response data
                response_data = {
                    'success': True,
                    'file': {
                        'name': file_name,  # Original file name for display
                        'storedName': file_info.get('storedName', unique_file_name),
                        'url': file_info.get('url', ''),
                        's3Key': file_info.get('s3Key', ''),
                        'size': uploaded_file.size,
                        'contentType': uploaded_file.content_type,
                        'uploadedAt': datetime.datetime.now().isoformat(),
                        'documentType': document_type,
                        'auditId': audit_id,
                        'complianceId': compliance_id
                    },
                    'operation_id': upload_result.get('operation_id'),
                    'message': f'File uploaded successfully to S3'
                }
                
                print(f"S3 upload successful: {file_info.get('storedName', unique_file_name)}")
                
                response = JsonResponse(response_data)
                response["Access-Control-Allow-Origin"] = "http://localhost:8080"
                response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
                response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                response["Access-Control-Allow-Credentials"] = "true"
                
                return response
            else:
                return JsonResponse({
                    'success': False,
                    'error': upload_result.get('error', 'S3 upload failed'),
                    'details': upload_result
                }, status=500)
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        print(f"Error in upload_evidence_to_s3: {str(e)}")
        import traceback
        traceback.print_exc()
        response = JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)
        
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
        
        return response