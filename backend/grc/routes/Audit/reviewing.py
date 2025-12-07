# from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.views.decorators.csrf import csrf_exempt
import json
import boto3
import os
import tempfile
from botocore.exceptions import ClientError
from django.conf import settings
from dotenv import load_dotenv
from ...models import Audit
from .checklist_utils import update_lastchecklistitem_verified
from .report_views import generate_report_file
from ...routes.Global.logging_service import send_log
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
import datetime
from typing import Dict, Any, Optional
from ...rbac.permissions import (
    AuditReviewPermission, AuditConductPermission, AuditViewPermission
)
from ...rbac.decorators import (
    audit_review_required,
    audit_conduct_required,
    audit_view_reports_required
)
from .framework_filter_helper import get_active_framework_filter, apply_framework_filter_to_audits, get_framework_sql_filter

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

# Load environment variables
load_dotenv()


def upload_to_s3(file_path: str, bucket_name: str, s3_file_name: str) -> Optional[str]:
    """
    Upload a file to S3 and return the URL
    """
    try:
        # Get AWS credentials from environment variables
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        aws_bucket = "orcashoimages"

        if not all([aws_access_key, aws_secret_key, aws_bucket]):
            print("ERROR: Missing required AWS credentials in .env file")
            return None

        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Upload file
        s3_client.upload_file(file_path, aws_bucket, module='Audit', s3_file_name=s3_file_name)
        
        # Generate URL
        url = f"https://{aws_bucket}.s3.{aws_region}.amazonaws.com/{s3_file_name}"
        print(f"+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++URL: {url}")
        return url
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return None

def save_report_to_db(audit_id: int, report_url: str, version: str = None) -> bool:
    """
    Save report URL to audit_report table
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_report (
                    AuditId, Report, PolicyId, SubPolicyId, FrameworkId
                ) SELECT 
                    %s, %s, PolicyId, SubPolicyId, FrameworkId 
                FROM audit 
                WHERE AuditId = %s
            """, [audit_id, report_url, audit_id])
            return True
    except Exception as e:
        print(f"Error saving report to DB: {str(e)}")
        return False

def save_review_version(
    audit_id: int,
    version_data: Dict[str, Any],
    user_id: int,
    is_rejected: bool = False,
    save_only: bool = False,
    update_audit_status: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Save a new review version of an audit.
    This creates a new version with 'R' prefix in the version number.
    """
    try:
        # Get the latest version number
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT version_number 
                FROM audit_version 
                WHERE audit_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """, [audit_id])
            result = cursor.fetchone()
            latest_version = result[0] if result else None

        # Generate next version number with 'R' prefix
        if latest_version:
            version_num = int(latest_version.lstrip('R')) + 1
            next_version = f"R{version_num}"
        else:
            next_version = "R1"

        # Create new version
        print(datetime.datetime.now(),"------------------------------------------------------------------------------")
        with connection.cursor() as cursor:
            # Get FrameworkId from the audit
            cursor.execute("SELECT FrameworkId FROM audit WHERE AuditId = %s", [audit_id])
            framework_row = cursor.fetchone()
            framework_id = framework_row[0] if framework_row else None
            
            cursor.execute("""
                INSERT INTO audit_version (
                    AuditId, Version, ExtractedInfo, 
                    UserId, Date, ActiveInactive, ApprovedRejected, FrameworkId
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                audit_id,
                next_version,
                version_data,
                user_id,
                datetime.datetime.now(),
                'R',  # R for Review version
                'rejected' if is_rejected else None,
                framework_id
            ])
            print(timezone.now(),"------------------------------------------------------------------------------")
        # Update audit status if all compliances are reviewed
        compliances = version_data.get('compliances', {})
        all_reviewed = all(
            comp.get('review_status') in ['accept', 'reject']
            for comp in compliances.values()
        )

        if all_reviewed and not save_only:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM audit WHERE id = %s", [audit_id])
                audit = cursor.fetchone()
                
                if audit:
                    # Check if all compliances are accepted
                    all_accepted = all(
                        comp.get('review_status') == 'accept'
                        for comp in compliances.values()
                    )
                    
                    new_status = 'Work In Progress' if is_rejected or not all_accepted else 'completed'
                    new_review_status = 'rejected' if is_rejected else 'accepted'
                    
                    cursor.execute("""
                        UPDATE audit 
                        SET status = %s, review_status = %s,
                            last_modified = %s, modified_by = %s
                        WHERE id = %s
                    """, [
                        new_status,
                        new_review_status,
                        timezone.now(),
                        user_id,
                        audit_id
                    ])

        if not save_only and update_audit_status:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE audit 
                    SET review_status = %s, status = %s,
                        last_modified = %s, modified_by = %s
                    WHERE id = %s
                """, [
                    update_audit_status['review_status'],
                    update_audit_status['status'],
                    timezone.now(),
                    user_id,
                    audit_id
                ])

        return {'version': next_version}
    except Exception as e:
        print(f"ERROR in save_review_version: {str(e)}")
        raise e

def get_latest_version(audit_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the latest version of an audit, regardless of whether it's a review or audit version.
    """
    try:
        with connection.cursor() as cursor:
            # Updated query to sort by datetime (created_at) and get the most recent
            cursor.execute("""
                SELECT Version, ExtractedInfo, Date, UserId, ApprovedRejected
                FROM audit_version 
                WHERE AuditId = %s
                ORDER BY Date DESC, Version DESC
                LIMIT 1
            """, [audit_id])
            result = cursor.fetchone()
            if result:
                return {
                    'version_number': result[0],
                    'version_data': result[1] if isinstance(result[1], dict) else json.loads(result[1]) if result[1] else {},
                    'date': result[2],
                    'user_id': result[3],
                    'approved_rejected': result[4]
                }
            return None
    except Exception as e:
        print(f"ERROR in get_latest_version: {str(e)}")
        return None

def extract_risks_and_mitigations_from_json(json_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract selected risks and mitigations from JSON data structure.
    Returns a dictionary with compliance_id as key and extracted data as value.
    """
    extracted_data = {}
    
    for key, value in json_data.items():
        # Skip metadata and overall comments
        if key in ['__metadata__', 'overall_comments']:
            continue
            
        if isinstance(value, dict):
            compliance_id = key
            selected_risks = value.get('selected_risks', [])
            selected_mitigations = value.get('selected_mitigations', [])
            
            print(f"DEBUG: Extracting from compliance {compliance_id}:")
            print(f"  - Found {len(selected_risks)} selected risks")
            print(f"  - Found {len(selected_mitigations)} selected mitigations")
            
            # Print detailed risk information
            for i, risk in enumerate(selected_risks):
                print(f"    Risk {i+1}: ID={risk.get('id')}, Title='{risk.get('title')}', Category='{risk.get('category')}'")
            
            # Print detailed mitigation information
            for i, mitigation in enumerate(selected_mitigations):
                print(f"    Mitigation {i+1}: Risk ID={mitigation.get('risk_id')}, Mitigation='{mitigation.get('mitigation')}'")
            
            extracted_data[compliance_id] = {
                'selected_risks': selected_risks,
                'selected_mitigations': selected_mitigations,
                'compliance_status': value.get('compliance_status', '0'),
                'review_status': value.get('review_status', ''),
                'review_comments': value.get('review_comments', ''),
                'evidence': value.get('evidence', ''),
                'criticality': value.get('criticality', ''),
                'severity_rating': value.get('severity_rating', ''),
                'impact': value.get('impact', ''),
                'comments': value.get('comments', ''),
                'how_to_verify': value.get('how_to_verify', ''),
                'details_of_finding': value.get('details_of_finding', ''),
                'underlying_cause': value.get('underlying_cause', ''),
                'why_to_verify': value.get('why_to_verify', ''),
                'what_to_verify': value.get('what_to_verify', ''),
                'suggested_action_plan': value.get('suggested_action_plan', ''),
                'responsible_for_plan': value.get('responsible_for_plan', ''),
                'mitigation_date': value.get('mitigation_date', ''),
                're_audit': value.get('re_audit', False),
                're_audit_date': value.get('re_audit_date', ''),
                'recommendation': value.get('recommendation', '')
            }
    
    return extracted_data

def create_incidents_for_findings(audit_id: int) -> None:
    """
    Create incidents for non-compliant and partially compliant audit findings
    """
    try:
        with connection.cursor() as cursor:
            # Get relevant audit findings and compliance details
            cursor.execute("""
                SELECT 
                    af.ComplianceId,
                    af.Check,
                    af.Comments,
                    af.UserId,
                    c.ComplianceTitle,
                    c.ComplianceItemDescription,
                    c.PossibleDamage,
                    c.Mitigation
                FROM audit_findings af
                JOIN compliance c ON af.ComplianceId = c.ComplianceId
                WHERE af.AuditId = %s 
                AND (
                    (af.Check = '0') OR  -- Not Compliant
                    (af.Check = '1')     -- Partially Compliant
                )
            """, [audit_id])
            
            findings = cursor.fetchall()
            
            current_datetime = timezone.now()
            current_date = current_datetime.date()
            current_time = current_datetime.time()
            
            # Create incidents for each finding
            for finding in findings:
                compliance_id = finding[0]
                check_status = finding[1]
                comments = finding[2]
                user_id = finding[3]
                compliance_title = finding[4]
                compliance_desc = finding[5]
                possible_damage = finding[6]
                mitigation = finding[7]
                
                # Check if incident already exists for this finding
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM incidents 
                    WHERE AuditId = %s AND ComplianceId = %s
                """, [audit_id, compliance_id])
                
                if cursor.fetchone()[0] > 0:
                    print(f"Incident already exists for AuditId {audit_id} and ComplianceId {compliance_id}")
                    continue
                
                # Create new incident
                cursor.execute("""
                    INSERT INTO incidents (
                        IncidentTitle,
                        Description,
                        PossibleDamage,
                        Mitigation,
                        AuditId,
                        ComplianceId,
                        Date,
                        Time,
                        UserId,
                        Origin,
                        Comments,
                        Status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, [
                    f"Non-Compliance of {compliance_title}",
                    compliance_desc,
                    possible_damage,
                    mitigation,
                    audit_id,
                    compliance_id,
                    current_date,
                    current_time,
                    user_id,
                    "Audit Finding",
                    comments,
                    "Open"
                ])
                
                print(f"Created incident for ComplianceId {compliance_id} in AuditId {audit_id}")
                
    except Exception as e:
        print(f"Error creating incidents: {str(e)}")
        import traceback
        traceback.print_exc()
@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditReviewPermission])
@audit_review_required
def update_audit_review_status(request, audit_id):
    """
    Update the review status of an audit and handle rejection/acceptance flows.
    """
    print("--------------reviewing.py update_review_status---------------------------------------")
    try:
        print(f"DEBUG: update_review_status called for audit_id: {audit_id}")
        print(f"DEBUG: Request data: {request.data}")
        
        # Get review status from either 'review_status' or 'status' field
        new_status_str = request.data.get('review_status') or request.data.get('status')
        print(f"DEBUG: Received status: {new_status_str}")
        
        if not new_status_str:
            return Response({'error': 'review_status field is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize compliance reviews
        compliance_reviews = request.data.get('compliance_reviews', [])
        print(f"DEBUG: Received compliance reviews: {compliance_reviews}")
        
        # Check if any compliance has a 'Reject' status
        has_rejected = False
        all_accepted = True
        for review in compliance_reviews:
            review_status = review.get('review_status', '').strip().lower()
            if review_status == 'reject':
                has_rejected = True
                all_accepted = False
                break
            elif review_status != 'accept':
                all_accepted = False
        
        print(f"DEBUG: Review status check - has_rejected: {has_rejected}, all_accepted: {all_accepted}")
        
        # Convert status to proper case format and handle variations
        new_status_str = new_status_str.strip()
        
        # Map common variations to standard values
        status_mapping = {
            'accept': 'Accept',
            'Accept': 'Accept',
            'Accepted': 'Accept',
            'reject': 'Reject',
            'Reject': 'Reject',
            'Rejected': 'Reject',
            'in review': 'In Review',
            'In Review': 'In Review',
            'In_review': 'In Review',
            'yet to start': 'Yet to Start',
            'Yet to Start': 'Yet to Start',
            'Yet_to_start': 'Yet to Start'
        }
        
        new_status_str = status_mapping.get(new_status_str, new_status_str)
        print(f"DEBUG: Mapped status to: {new_status_str}")
        
        valid_statuses = ['Yet to Start', 'In Review', 'Accept', 'Reject']
        if new_status_str not in valid_statuses:
            error_msg = f'Invalid status "{new_status_str}". Must be one of: {", ".join(valid_statuses)}'
            print(f"DEBUG: Validation error - {error_msg}")
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # Map string status to integer for database
        status_map = {
            'Yet to Start': 0,
            'In Review': 1,
            'Accept': 2,
            'Reject': 3
        }
        new_status_int = status_map.get(new_status_str)
        print(f"DEBUG: Mapped status to integer: {new_status_int}")
        
        # Find and update the audit
        try:
            audit = Audit.objects.get(AuditId=audit_id)
            print(f"DEBUG: Found audit with ID {audit_id}, current status: {audit.Status}, review status: {audit.ReviewStatus}")
        except Audit.DoesNotExist:
            return Response({'error': 'Audit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if audit is in the correct state for review
        if audit.Status != 'Under review':
            error_msg = f'Cannot update review status when audit is not under review. Current status: {audit.Status}'
            print(f"DEBUG: State error - {error_msg}")
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        # Store the old status before updating
        old_status_int = audit.ReviewStatus
        status_reverse_map = {0: 'Yet to Start', 1: 'In Review', 2: 'Accept', 3: 'Reject'}
        old_status_str = status_reverse_map.get(old_status_int, 'Unknown') if old_status_int is not None else 'None'
        print(f"DEBUG: Changing review status from '{old_status_str}' ({old_status_int}) to '{new_status_str}' ({new_status_int})")
        
        # Update the review status with integer value
        audit.ReviewStatus = new_status_int
        
        # Add review comments if provided
        review_comments = request.data.get('review_comments')
        if review_comments is not None:
            audit.ReviewComments = review_comments
            print(f"DEBUG: Setting review comments: {review_comments}")
        
        # Set review date
        current_time = timezone.now()
        audit.ReviewDate = current_time
        
        # Set ReviewStartDate when status changes to 'In Review'
        if new_status_str == 'In Review' and old_status_str != 'In Review':
            audit.ReviewStartDate = current_time
            print(f"DEBUG: Setting ReviewStartDate to {current_time}")
        
        # Save the audit object with the updated review status
        audit.save()
        print(f"DEBUG: Audit review status updated in database to {new_status_str}")
        
        # Get user ID from session or request
        user_id = request.session.get('user_id')
        if not user_id and hasattr(audit, 'reviewer_id'):
            user_id = audit.reviewer_id
        
        # If the review is rejected, update the audit status back to "Work In Progress"
        if new_status_str == 'Reject' or has_rejected:
            print(f"DEBUG: Audit {audit_id} rejected, changing status back to 'Work In Progress'")
            audit.Status = 'Work In Progress'
            audit.ReviewStatus = 0  # Set review status to 0
            audit.save()
            
            # Update audit findings with rejection status
            with connection.cursor() as cursor:
                if compliance_reviews:
                    for review in compliance_reviews:
                        cursor.execute("""
                            UPDATE audit_findings
                            SET ReviewStatus = %s,
                                ReviewComments = %s,
                                ReviewRejected = 1,
                                ReviewDate = %s
                            WHERE AuditId = %s AND ComplianceId = %s
                        """, [
                            review.get('review_status'),
                            review.get('review_comments', ''),
                            current_time,
                            audit_id,
                            review.get('compliance_id')
                        ])
                else:
                    # If no compliance reviews, update all findings for this audit
                    cursor.execute("""
                        UPDATE audit_findings
                        SET ReviewStatus = 'Reject',
                            ReviewComments = %s,
                            ReviewRejected = 1,
                            ReviewDate = %s
                        WHERE AuditId = %s
                    """, [
                        review_comments or 'Audit rejected',
                        current_time,
                        audit_id
                    ])
                    
                # Update version data to indicate rejection
                cursor.execute("""
                    SELECT Version, ExtractedInfo 
                    FROM audit_version 
                    WHERE AuditId = %s AND Version LIKE 'R%%'
                    ORDER BY Version DESC
                    LIMIT 1
                """, [audit_id])
                
                version_row = cursor.fetchone()
                if version_row:
                    latest_version = version_row[0]
                    version_data = json.loads(version_row[1]) if isinstance(version_row[1], str) else version_row[1]
                    
                    # Update metadata
                    metadata = version_data.get('__metadata__', {})
                    metadata['overall_status'] = 'Reject'
                    metadata['ApprovedRejected'] = 'Rejected'
                    
                    # Make sure metadata's overall_comments is preserved as audit comments
                    # Do NOT update metadata's overall_comments with review comments
                    
                    version_data['__metadata__'] = metadata
                    
                    # Store review comments separately from audit comments
                    if review_comments:
                        version_data['overall_review_comments'] = review_comments
                        # Do NOT modify overall_comments - it should contain audit comments only
                    
                    cursor.execute("""
                        UPDATE audit_version
                        SET ExtractedInfo = %s,
                            ApprovedRejected = %s
                        WHERE AuditId = %s AND Version = %s
                    """, [json.dumps(version_data), 'Rejected', audit_id, latest_version])
            
            # Send rejection notification
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                
                with connection.cursor() as cursor:
                    # Get audit and user details
                    cursor.execute("""
                        SELECT a.Title, a.Auditor, a.Assignee, u1.Email as auditor_email, 
                               u1.UserName as auditor_name, u2.Email as assignee_email,
                               u2.UserName as assignee_name
                        FROM audit a
                        LEFT JOIN users u1 ON a.Auditor = u1.UserId
                        LEFT JOIN users u2 ON a.Assignee = u2.UserId
                        WHERE a.AuditId = %s
                    """, [audit_id])
                    
                    audit_data = cursor.fetchone()
                    if audit_data:
                        audit_title = audit_data[0] or f"Audit #{audit_id}"
                        auditor_email = audit_data[3]
                        auditor_name = audit_data[4]
                        assignee_email = audit_data[5]
                        assignee_name = audit_data[6]
                        
                        reviewer_name = "System"
                        if user_id:
                            cursor.execute("SELECT UserName FROM users WHERE UserId = %s", [user_id])
                            reviewer_row = cursor.fetchone()
                            if reviewer_row:
                                reviewer_name = reviewer_row[0] or f"User {user_id}"
                        
                        # Send notification to auditor
                        if auditor_email:
                            notification_service.send_multi_channel_notification({
                                'notification_type': 'auditReviewed',
                                'email': auditor_email,
                                'email_type': 'gmail',
                                'template_data': [
                                    auditor_name,
                                    audit_title,
                                    'Rejected',
                                    reviewer_name,
                                    review_comments or 'Audit requires revisions. Please review and update.'
                                ]
                            })
                        
                        # Send notification to assignee if different from auditor
                        if assignee_email and assignee_email != auditor_email:
                            notification_service.send_multi_channel_notification({
                                'notification_type': 'auditReviewed',
                                'email': assignee_email,
                                'email_type': 'gmail',
                                'template_data': [
                                    assignee_name,
                                    audit_title,
                                    'Rejected',
                                    reviewer_name,
                                    review_comments or 'Audit requires revisions. Please review and update.'
                                ]
                            })
            except Exception as e:
                print(f"ERROR: Failed to send rejection notifications: {str(e)}")
            
            send_log(module="Reviewing", actionType="UPDATE_REVIEW_STATUS", description="Updated review status", userId=request.session.get('user_id'), entityType="Audit", entityId=audit_id)
            
            return Response({
                'message': 'Audit rejected and returned for revision',
                'status': audit.Status,
                'review_status': new_status_str
            }, status=status.HTTP_200_OK)
            
        # Handle acceptance flow
        elif new_status_str == 'Accept' and all_accepted:
            print(f"DEBUG: Audit {audit_id} accepted, updating status to Completed")
            audit.Status = 'Completed'
            
            # Update audit metadata
            # Check for audit_evidence in the request data
            audit_evidence = request.data.get('audit_evidence', '')
            if audit_evidence:
                print(f"DEBUG: Setting audit Evidence from request audit_evidence: {audit_evidence}")
                audit.Evidence = audit_evidence
            else:
                # Fall back to 'evidence' field if audit_evidence is not provided
                audit.Evidence = request.data.get('evidence', '')
            
            audit.ReviewerComments = review_comments
            audit.Comments = request.data.get('overall_comments', '')
            audit.save()
            
            # First update audit findings with acceptance status and all compliance data
            with connection.cursor() as cursor:
                # Check if we have JSON data in the request
                json_data = request.data.get('json_data')
                if json_data:
                    print("DEBUG: Processing JSON data directly")
                    extracted_data = extract_risks_and_mitigations_from_json(json_data)
                    
                    for compliance_id, data in extracted_data.items():
                        selected_risks = data['selected_risks']
                        selected_mitigations = data['selected_mitigations']
                        
                        # Format the data for MySQL JSON columns
                        predictive_risks = json.dumps([{
                            'id': risk.get('id'),
                            'type': risk.get('type'),
                            'title': risk.get('title'),
                            'category': risk.get('category'),
                            'mitigation': risk.get('mitigation')
                        } for risk in selected_risks]) if selected_risks else 'null'
                        
                        corrective_actions = json.dumps([{
                            'risk_id': action.get('risk_id'),
                            'mitigation': action.get('mitigation')
                        } for action in selected_mitigations]) if selected_mitigations else 'null'
                        
                        print(f"DEBUG: Saving for compliance {compliance_id}:")
                        print(f"  - predictive_risks: {predictive_risks}")
                        print(f"  - corrective_actions: {corrective_actions}")
                        
                        # Print detailed risk information for JSON processing
                        print(f"DEBUG: JSON Processing - Compliance {compliance_id} - Selected Risks:")
                        print(f"  - Found {len(selected_risks)} selected risks")
                        for i, risk in enumerate(selected_risks):
                            print(f"    Risk {i+1}: ID={risk.get('id')}, Title='{risk.get('title')}', Category='{risk.get('category')}'")
                        
                        print(f"DEBUG: JSON Processing - Compliance {compliance_id} - Selected Mitigations:")
                        print(f"  - Found {len(selected_mitigations)} selected mitigations")
                        for i, mitigation in enumerate(selected_mitigations):
                            print(f"    Mitigation {i+1}: Risk ID={mitigation.get('risk_id')}, Mitigation='{mitigation.get('mitigation')}'")
                        
                        # Convert criticality text to numeric format
                        criticality_value = ''
                        criticality_text = data.get('criticality', '').strip().lower() if data.get('criticality') else ''
                        if criticality_text == 'major':
                            criticality_value = '1'
                        elif criticality_text == 'minor':
                            criticality_value = '0'
                        elif criticality_text == 'not applicable':
                            criticality_value = '2'
                        else:
                            criticality_value = '0'  # Default to Minor
                        
                        cursor.execute("""
                            UPDATE audit_findings
                            SET ReviewStatus = %s,
                                ReviewComments = %s,
                                ReviewRejected = 0,
                                ReviewDate = %s,
                                CheckedDate = %s,
                                Evidence = %s,
                                HowToVerify = %s,
                                Impact = %s,
                                DetailsOfFinding = %s,
                                Comments = %s,
                                MajorMinor = %s,
                                SeverityRating = %s,
                                PredictiveRisks = %s,
                                CorrectiveActions = %s,
                                UnderlyingCause = %s,
                                WhyToVerify = %s,
                                WhatToVerify = %s,
                                SuggestedActionPlan = %s,
                                MitigationDate = %s,
                                ResponsibleForPlan = %s,
                                ReAudit = %s,
                                ReAuditDate = %s,
                                Recommendation = %s,
                                `Check` = %s
                            WHERE AuditId = %s AND ComplianceId = %s
                        """, [
                            data.get('review_status', 'Accept'),
                            data.get('review_comments', ''),
                            current_time,
                            current_time,
                            data.get('evidence', ''),
                            data.get('how_to_verify', ''),
                            data.get('impact', ''),
                            data.get('details_of_finding', ''),
                            data.get('comments', ''),
                            criticality_value,
                            data.get('severity_rating', 0),
                            predictive_risks,
                            corrective_actions,
                            data.get('underlying_cause', ''),
                            data.get('why_to_verify', ''),
                            data.get('what_to_verify', ''),
                            data.get('suggested_action_plan', ''),
                            data.get('mitigation_date'),
                            data.get('responsible_for_plan', ''),
                            data.get('re_audit', 0),
                            data.get('re_audit_date'),
                            data.get('recommendation', ''),
                            data.get('compliance_status', '0'),
                            audit_id,
                            compliance_id
                        ])
                        print(f"DEBUG: Updated audit_finding for compliance_id {compliance_id}")
                
                elif compliance_reviews:
                    for review in compliance_reviews:
                        compliance_id = review.get('compliance_id')
                        print(f"DEBUG11111111111111111111111111111111: Compliance ID {compliance_id}")
                        if not compliance_id:
                            continue

                        # Get the selected risks and mitigations from the review data
                        selected_risks = review.get('predictive_risks', [])
                        selected_mitigations = review.get('corrective_actions', [])
                        
                        # Enhanced debugging for selected risks and mitigations
                        print(f"DEBUG: Compliance ID {compliance_id} - Selected Risks:")
                        print(f"  - Found {len(selected_risks)} selected risks")
                        for i, risk in enumerate(selected_risks):
                            print(f"    Risk {i+1}: ID={risk.get('id')}, Title='{risk.get('title')}', Category='{risk.get('category')}'")
                        
                        print(f"DEBUG: Compliance ID {compliance_id} - Selected Mitigations:")
                        print(f"  - Found {len(selected_mitigations)} selected mitigations")
                        for i, mitigation in enumerate(selected_mitigations):
                            print(f"    Mitigation {i+1}: Risk ID={mitigation.get('risk_id')}, Mitigation='{mitigation.get('mitigation')}'")
                        
                        # Format the data for MySQL JSON columns
                        predictive_risks = json.dumps([{
                            'id': risk.get('id'),
                            'type': risk.get('type'),
                            'title': risk.get('title'),
                            'category': risk.get('category'),
                            'mitigation': risk.get('mitigation')
                        } for risk in selected_risks]) if selected_risks else 'null'
                        
                        corrective_actions = json.dumps([{
                            'risk_id': action.get('risk_id'),
                            'mitigation': action.get('mitigation')
                        } for action in selected_mitigations]) if selected_mitigations else 'null'
                        
                        print(f"DEBUG: Saving predictive_risks: {predictive_risks}")
                        print(f"DEBUG: Saving corrective_actions: {corrective_actions}")
                        
                        # Map compliance status to Check value
                        check_value = review.get('compliance_status', '0') # Default to Not Started or Not Compliant
                        
                        print(f"DEBUG: Using check_value '{check_value}' from compliance_status")
                        
                        # Convert criticality text to numeric format (Major: 1, Minor: 0)
                        criticality_value = ''
                        criticality_text = review.get('criticality', '').strip().lower() if review.get('criticality') else ''
                        if criticality_text == 'major':
                            criticality_value = '1'  # Major: 1
                        elif criticality_text == 'minor':
                            criticality_value = '0'  # Minor: 0
                        elif criticality_text == 'not applicable':
                            criticality_value = '2'
                        else:
                            # If no valid criticality is provided, check if there's a major_minor field directly
                            major_minor = review.get('major_minor')
                            if major_minor in ['0', '1', '2']:
                                criticality_value = major_minor
                            else:
                                # Default to Minor if nothing valid is provided
                                criticality_value = '0'
                        
                        print(f"DEBUG: Setting MajorMinor to '{criticality_value}' for compliance_id {compliance_id}")
                        
                        cursor.execute("""
                            UPDATE audit_findings
                            SET ReviewStatus = 'Accept',
                                ReviewComments = %s,
                                ReviewRejected = 0,
                                ReviewDate = %s,
                                CheckedDate = %s,  -- Update CheckedDate with current timestamp
                                Evidence = %s,
                                HowToVerify = %s,
                                Impact = %s,
                                DetailsOfFinding = %s,
                                Comments = %s,
                                MajorMinor = %s,
                                SeverityRating = %s,
                                PredictiveRisks = %s,
                                CorrectiveActions = %s,
                                UnderlyingCause = %s,
                                WhyToVerify = %s,
                                WhatToVerify = %s,
                                SuggestedActionPlan = %s,
                                MitigationDate = %s,
                                ResponsibleForPlan = %s,
                                ReAudit = %s,
                                ReAuditDate = %s,
                                Recommendation = %s,
                                `Check` = %s
                            WHERE AuditId = %s AND ComplianceId = %s
                        """, [
                            review.get('review_comments', ''),
                            current_time,
                            current_time,  # CheckedDate gets current timestamp
                            review.get('evidence', ''),
                            review.get('how_to_verify', ''),
                            review.get('impact', ''),
                            review.get('details_of_finding', ''),
                            review.get('comments', ''),
                            criticality_value,  # Use converted numeric value from JSON
                            review.get('severity_rating', 0),
                            predictive_risks,
                            corrective_actions,
                            review.get('underlying_cause', ''),
                            review.get('why_to_verify', ''),
                            review.get('what_to_verify', ''),
                            review.get('suggested_action_plan', ''),
                            review.get('mitigation_date'),
                            review.get('responsible_for_plan', ''),
                            review.get('re_audit', 0),
                            review.get('re_audit_date'),
                            review.get('recommendation', ''),
                            check_value,
                            audit_id,
                            compliance_id
                        ])
                        print(f"DEBUG: Updated audit_finding for compliance_id {compliance_id} with check_value {check_value}")
                
                # Update version data to indicate acceptance
                cursor.execute("""
                    SELECT Version, ExtractedInfo 
                    FROM audit_version 
                    WHERE AuditId = %s AND Version LIKE 'R%%'
                    ORDER BY Version DESC
                    LIMIT 1
                """, [audit_id])
                
                version_row = cursor.fetchone()
                if version_row:
                    latest_version = version_row[0]
                    version_data = json.loads(version_row[1]) if isinstance(version_row[1], str) else version_row[1]
                    
                    # Get audit details for metadata
                    cursor.execute("""
                        SELECT Title, Scope, Objective, BusinessUnit, Auditor, Reviewer, Evidence, Comments
                        FROM audit
                        WHERE AuditId = %s
                    """, [audit_id])
                    audit_details = cursor.fetchone()
                    
                    # Extract audit_evidence from version data if it exists
                    audit_evidence = version_data.get('__metadata__', {}).get('audit_evidence', '')
                    
                    # If audit_evidence exists in metadata, update the Evidence column in audit table
                    if audit_evidence:
                        # First check if there's existing evidence to append to
                        cursor.execute("""
                            SELECT Evidence FROM audit
                            WHERE AuditId = %s
                        """, [audit_id])
                        
                        evidence_row = cursor.fetchone()
                        existing_evidence = evidence_row[0] if evidence_row and evidence_row[0] else ''
                        
                        # Combine existing and new evidence URLs, avoiding duplicates
                        if existing_evidence:
                            existing_urls = existing_evidence.split(',')
                            new_urls = audit_evidence.split(',')
                            combined_urls = existing_urls
                            for url in new_urls:
                                if url and url not in combined_urls:
                                    combined_urls.append(url)
                            combined_evidence = ','.join(combined_urls)
                        else:
                            combined_evidence = audit_evidence
                            
                        print(f"DEBUG: Updating audit Evidence with metadata audit_evidence: {combined_evidence}")
                        cursor.execute("""
                            UPDATE audit
                            SET Evidence = %s
                            WHERE AuditId = %s
                        """, [combined_evidence, audit_id])
                    
                    # Update metadata
                    metadata = {
                        'user_id': audit_details[4] if audit_details else None,  # Auditor as user_id
                        'audit_scope': audit_details[1] if audit_details else '',
                        'audit_title': audit_details[0] if audit_details else '',
                        'review_date': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'reviewer_id': audit_details[5] if audit_details else None,
                        'created_date': version_data.get('__metadata__', {}).get('created_date', current_time.strftime('%Y-%m-%d %H:%M:%S')),
                        'version_type': 'Auditor',
                        'business_unit': audit_details[3] if audit_details else '',
                        'audit_evidence': audit_evidence or audit_details[6] or '',  # Preserve audit_evidence from metadata
                        'overall_status': 'Accept',
                        'audit_objective': audit_details[2] if audit_details else '',
                        'ApprovedRejected': 'Approved',
                        'overall_comments': audit_details[7] if audit_details else ''  # Keep audit comments in metadata
                    }
                    
                    # Preserve existing metadata fields if they exist
                    existing_metadata = version_data.get('__metadata__', {})
                    for key, value in existing_metadata.items():
                        if key not in metadata or not metadata[key]:
                            metadata[key] = value
                    
                    # Special handling for audit_evidence to ensure it's preserved
                    if 'audit_evidence' in existing_metadata and existing_metadata['audit_evidence']:
                        metadata['audit_evidence'] = existing_metadata['audit_evidence']
                        
                        # First check if there's existing evidence to append to
                        cursor.execute("""
                            SELECT Evidence FROM audit
                            WHERE AuditId = %s
                        """, [audit_id])
                        
                        evidence_row = cursor.fetchone()
                        existing_evidence = evidence_row[0] if evidence_row and evidence_row[0] else ''
                        
                        # Combine existing and new evidence URLs, avoiding duplicates
                        if existing_evidence and existing_evidence != metadata['audit_evidence']:
                            existing_urls = existing_evidence.split(',')
                            new_urls = metadata['audit_evidence'].split(',')
                            combined_urls = existing_urls
                            for url in new_urls:
                                if url and url not in combined_urls:
                                    combined_urls.append(url)
                            combined_evidence = ','.join(combined_urls)
                        else:
                            combined_evidence = metadata['audit_evidence']
                        
                        # Also update the audit table with this evidence
                        print(f"DEBUG: Updating audit Evidence from preserved metadata: {combined_evidence}")
                        cursor.execute("""
                            UPDATE audit
                            SET Evidence = %s
                            WHERE AuditId = %s
                        """, [combined_evidence, audit_id])
                    
                    version_data['__metadata__'] = metadata
                    
                    # Store review comments separately from audit comments
                    version_data['overall_review_comments'] = review_comments or ''
                    
                    # Do NOT modify overall_comments - it should contain audit comments only
                    
                    cursor.execute("""
                        UPDATE audit_version
                        SET ExtractedInfo = %s,
                            ApprovedRejected = %s
                        WHERE AuditId = %s AND Version = %s
                    """, [json.dumps(version_data), 'Approved', audit_id, latest_version])
            
            # Now generate report and upload to S3 after all database updates are complete
            try:
                # Create temporary directory for report generation
                temp_dir = tempfile.mkdtemp()
                report_file_name = f"audit_report_{audit_id}.docx"
                report_file_path = os.path.join(temp_dir, report_file_name)
                
                print(f"DEBUG: Generating report for audit {audit_id} after database updates")
                
                # Generate report - this will fetch the latest data from audit and audit_findings tables
                generated_file = generate_report_file(audit_id, report_file_path)
                
                if generated_file:
                    # Upload to S3
                    s3_file_name = f"audit_reports/{audit_id}/{report_file_name}"
                    aws_bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
                    if not aws_bucket:
                        print("ERROR: AWS_STORAGE_BUCKET_NAME not found in .env file")
                        raise ValueError("AWS_STORAGE_BUCKET_NAME not configured")
                        
                    report_url = upload_to_s3(
                        generated_file,
                        aws_bucket,
                        s3_file_name
                    )
                    
                    if report_url:
                        # Save to audit_report table
                        save_report_to_db(audit_id, report_url)
                        print(f"DEBUG: Successfully generated and uploaded report for audit {audit_id}")
                    else:
                        print(f"WARNING: Failed to upload report to S3 for audit {audit_id}")
                else:
                    print(f"WARNING: Failed to generate report for audit {audit_id}")
                
                # Cleanup temporary files
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
                    
            except Exception as e:
                print(f"ERROR: Failed to handle report generation and upload: {str(e)}")
                import traceback
                traceback.print_exc()
            
# This section was moved above to update the database before generating the report
            
            # Update lastchecklistitemverified table
            try:
                print(f"+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++DEBUG: Updating lastchecklistitemverified table for audit {audit_id}")
                print(f"DEBUG: ==========================================")
                print(f"DEBUG: About to call update_lastchecklistitem_verified for audit_id: {audit_id}")
                print(f"DEBUG: ==========================================")
                
                update_result = update_lastchecklistitem_verified(audit_id)
                
                print(f"DEBUG: ==========================================")
                print(f"DEBUG: update_lastchecklistitem_verified returned: {update_result}")
                print(f"DEBUG: ==========================================")
                
                if not update_result:
                    print(f"WARNING: Failed to update lastchecklistitemverified table for audit {audit_id}")
                else:
                    print(f"DEBUG: SUCCESS: lastchecklistitemverified table updated successfully for audit {audit_id}")
                
                # Create incidents for non-compliant and partially compliant findings
                print(f"DEBUG: Creating incidents for non-compliant findings in audit {audit_id}")
                create_incidents_for_findings(audit_id)
                
            except Exception as e:
                print(f"ERROR: Exception while updating lastchecklistitemverified table: {str(e)}")
                print(f"DEBUG: ==========================================")
                print(f"DEBUG: ERROR in update_lastchecklistitem_verified call:")
                print(f"DEBUG: Error type: {type(e).__name__}")
                print(f"DEBUG: Error message: {str(e)}")
                import traceback
                print(f"DEBUG: Full traceback:")
                traceback.print_exc()
                print(f"DEBUG: ==========================================")
            
            # Send acceptance notification
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                
                with connection.cursor() as cursor:
                    # Get audit and user details
                    cursor.execute("""
                        SELECT a.Title, a.Auditor, a.Assignee, u1.Email as auditor_email, 
                               u1.UserName as auditor_name, u2.Email as assignee_email,
                               u2.UserName as assignee_name
                        FROM audit a
                        LEFT JOIN users u1 ON a.Auditor = u1.UserId
                        LEFT JOIN users u2 ON a.Assignee = u2.UserId
                        WHERE a.AuditId = %s
                    """, [audit_id])
                    
                    audit_data = cursor.fetchone()
                    if audit_data:
                        audit_title = audit_data[0] or f"Audit #{audit_id}"
                        auditor_email = audit_data[3]
                        auditor_name = audit_data[4]
                        assignee_email = audit_data[5]
                        assignee_name = audit_data[6]
                        
                        reviewer_name = "System"
                        if user_id:
                            cursor.execute("SELECT UserName FROM users WHERE UserId = %s", [user_id])
                            reviewer_row = cursor.fetchone()
                            if reviewer_row:
                                reviewer_name = reviewer_row[0] or f"User {user_id}"
                        
                        # Send notification to auditor
                        if auditor_email:
                            notification_service.send_multi_channel_notification({
                                'notification_type': 'auditReviewed',
                                'email': auditor_email,
                                'email_type': 'gmail',
                                'template_data': [
                                    auditor_name,
                                    audit_title,
                                    'Approved',
                                    reviewer_name,
                                    review_comments or 'Audit has been approved.'
                                ]
                            })
                        
                        # Send notification to assignee if different from auditor
                        if assignee_email and assignee_email != auditor_email:
                            notification_service.send_multi_channel_notification({
                                'notification_type': 'auditReviewed',
                                'email': assignee_email,
                                'email_type': 'gmail',
                                'template_data': [
                                    assignee_name,
                                    audit_title,
                                    'Approved',
                                    reviewer_name,
                                    review_comments or 'Audit has been approved.'
                                ]
                            })
            except Exception as e:
                print(f"ERROR: Failed to send acceptance notifications: {str(e)}")
            
            send_log(module="Reviewing", actionType="UPDATE_REVIEW_STATUS", description="Updated review status", userId=request.session.get('user_id'), entityType="Audit", entityId=audit_id)
            
            return Response({
                'message': 'Audit review completed and accepted',
                'status': audit.Status,
                'review_status': new_status_str
            }, status=status.HTTP_200_OK)
            
        # Return the updated status information
        return Response({
            'success': True,
            'audit_id': audit_id,
            'review_status': new_status_str,
            'review_status_int': new_status_int,
            'audit_status': audit.Status,
            'review_comments': review_comments,
            'has_rejected': has_rejected,
            'all_accepted': all_accepted
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"ERROR in update_review_status: {str(e)}")
        import traceback
        traceback.print_exc()
        send_log(module="Reviewing", actionType="UPDATE_REVIEW_STATUS", description="Error in update_review_status", userId=request.session.get('user_id'), entityType="Audit", entityId=audit_id)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
def test_json_extraction(request):
    """
    Test endpoint to extract risks and mitigations from JSON data
    """
    try:
        json_data = request.data.get('json_data')
        if not json_data:
            return Response({'error': 'json_data is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        print("DEBUG: Testing JSON extraction with data:")
        print(json.dumps(json_data, indent=2))
        
        extracted_data = extract_risks_and_mitigations_from_json(json_data)
        
        result = {
            'extracted_data': extracted_data,
            'summary': {
                'total_compliances': len(extracted_data),
                'total_risks': sum(len(data['selected_risks']) for data in extracted_data.values()),
                'total_mitigations': sum(len(data['selected_mitigations']) for data in extracted_data.values())
            }
        }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"ERROR in test_json_extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditReviewPermission])
@audit_review_required
def load_latest_review_data(request, audit_id):
    """
    Load the latest version data for review, sorted by datetime
    """
    try:
        # Get the latest version data
        latest_version = get_latest_version(audit_id)
        
        if not latest_version:
            return Response({
                'error': 'No version data found for this audit'
            }, status=status.HTTP_404_NOT_FOUND)
        
        version_data = latest_version['version_data']
        
        # Extract compliance data and review information
        compliances = []
        for compliance_id, compliance_data in version_data.items():
            if compliance_id == '__metadata__':
                continue
                
            compliance_info = {
                'id': compliance_id,
                'description': compliance_data.get('description', ''),
                'status': compliance_data.get('status', '0'),
                'compliance_status': compliance_data.get('compliance_status', 'Not Compliant'),
                'comments': compliance_data.get('comments', ''),
                'evidence': compliance_data.get('evidence', ''),
                'review_status': compliance_data.get('review_status', 'in_review'),
                'review_comments': compliance_data.get('review_comments', ''),
                'how_to_verify': compliance_data.get('how_to_verify', ''),
                'impact': compliance_data.get('impact', ''),
                'details_of_finding': compliance_data.get('details_of_finding', ''),
                'major_minor': compliance_data.get('major_minor', ''),
                'severity_rating': compliance_data.get('severity_rating', ''),
                'selected_risks': compliance_data.get('selected_risks', []),
                'selected_mitigations': compliance_data.get('selected_mitigations', []),
                'underlying_cause': compliance_data.get('underlying_cause', ''),
                'why_to_verify': compliance_data.get('why_to_verify', ''),
                'what_to_verify': compliance_data.get('what_to_verify', ''),
                'suggested_action_plan': compliance_data.get('suggested_action_plan', ''),
                'responsible_for_plan': compliance_data.get('responsible_for_plan', ''),
                'mitigation_date': compliance_data.get('mitigation_date', ''),
                're_audit': compliance_data.get('re_audit', False),
                're_audit_date': compliance_data.get('re_audit_date', '')
            }
            compliances.append(compliance_info)
        
        # Get metadata
        metadata = version_data.get('__metadata__', {})
        
        return Response({
            'version_number': latest_version['version_number'],
            'version_date': latest_version['date'],
            'compliances': compliances,
            'overall_audit_comments': metadata.get('overall_comments', ''),
            'overall_review_comments': version_data.get('overall_review_comments', ''),
            'audit_evidence': metadata.get('audit_evidence', ''),
            'loaded_from_version': True,
            'current_version': latest_version['version_number']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"ERROR in load_latest_review_data: {str(e)}")
        import traceback
        traceback.print_exc()
        send_log(module="Reviewing", actionType="LOAD_LATEST_REVIEW_DATA", description="Error in load_latest_review_data", userId=request.session.get('user_id'), entityType="Audit", entityId=audit_id)
        return Response({
            'error': f'Error loading latest review data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)