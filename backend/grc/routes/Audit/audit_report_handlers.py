from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
import json
from ...models import Audit, AuditReport
from ...routes.Global.notification_service import NotificationService
from ...routes.Global.logging_service import send_log
from datetime import datetime
from ...rbac.permissions import (
    AuditViewPermission, AuditAssignPermission
)
from ...rbac.decorators import (
    audit_view_reports_required,
    audit_assign_required
)
from .framework_filter_helper import get_active_framework_filter, apply_framework_filter_to_audits, get_framework_sql_filter

@api_view(['GET'])
@permission_classes([AuditViewPermission])
@audit_view_reports_required
def check_audit_reports(request):
    """
    Check for existing audit reports based on framework, policy, and subpolicy IDs
    """
    try:
        framework_id = request.GET.get('framework_id')
        policy_id = request.GET.get('policy_id')
        subpolicy_id = request.GET.get('subpolicy_id')
        user_id = request.session.get('user_id')

        if not framework_id:
            send_log(
                module="AuditReport",
                actionType="CHECK_AUDIT_REPORTS_ERROR",
                description="Framework ID is required but was not provided",
                userId=user_id,
                entityType="AuditReport",
                logLevel="ERROR"
            )
            return Response({'error': 'Framework ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Log the request
        send_log(
            module="AuditReport",
            actionType="CHECK_AUDIT_REPORTS",
            description=f"Checking audit reports for framework ID {framework_id}",
            userId=user_id,
            entityType="AuditReport",
            entityId=framework_id,
            additionalInfo={
                "policy_id": policy_id,
                "subpolicy_id": subpolicy_id
            }
        )

        # Build query based on provided parameters
        query = """
            SELECT 
                ar.ReportId,
                a.CompletionDate,
                auditor.UserName as AuditorName,
                reviewer.UserName as ReviewerName
            FROM 
                audit_report ar
                JOIN audit a ON ar.AuditId = a.AuditId
                JOIN users auditor ON a.auditor = auditor.UserId
                LEFT JOIN users reviewer ON a.reviewer = reviewer.UserId
            WHERE 
                ar.FrameworkId = %s
        """
        params = [framework_id]

        if policy_id:
            query += " AND ar.PolicyId = %s"
            params.append(policy_id)
        else:
            query += " AND ar.PolicyId IS NULL"

        if subpolicy_id:
            query += " AND ar.SubPolicyId = %s"
            params.append(subpolicy_id)
        else:
            query += " AND ar.SubPolicyId IS NULL"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            reports = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Format dates
            for report in reports:
                if report.get('CompletionDate'):
                    report['CompletionDate'] = report['CompletionDate'].strftime('%Y-%m-%d %H:%M:%S')

        # Log success
        send_log(
            module="AuditReport",
            actionType="CHECK_AUDIT_REPORTS_SUCCESS",
            description=f"Found {len(reports)} audit reports for framework ID {framework_id}",
            userId=user_id,
            entityType="AuditReport",
            entityId=framework_id,
            additionalInfo={
                "report_count": len(reports),
                "policy_id": policy_id,
                "subpolicy_id": subpolicy_id
            }
        )

        return Response({'reports': reports}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"ERROR in check_audit_reports: {str(e)}")
        user_id = request.session.get('user_id')
        send_log(
            module="AuditReport",
            actionType="CHECK_AUDIT_REPORTS_ERROR",
            description=f"Error checking audit reports: {str(e)}",
            userId=user_id,
            entityType="AuditReport",
            entityId=framework_id if 'framework_id' in locals() else None,
            logLevel="ERROR",
            additionalInfo={"error": str(e)}
        )
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def handle_selected_reports(audit, selected_reports):
    """
    Handle selected reports for an audit
    """
    try:
        if not selected_reports:
            return

        # Log the attempt
        send_log(
            module="AuditReport",
            actionType="HANDLE_SELECTED_REPORTS",
            description=f"Handling {len(selected_reports)} selected reports for audit ID {audit.AuditId}",
            userId=None,  # No user context in this function
            entityType="Audit",
            entityId=str(audit.AuditId),
            additionalInfo={"selected_report_count": len(selected_reports)}
        )

        reports_json = []
        for report_id in selected_reports:
            try:
                report = AuditReport.objects.get(ReportId=report_id)
                reports_json.append({
                    'report_id': report.ReportId,
                    'audit_id': report.AuditId.AuditId,
                    'report': report.Report
                })
            except AuditReport.DoesNotExist:
                send_log(
                    module="AuditReport",
                    actionType="REPORT_NOT_FOUND",
                    description=f"Report ID {report_id} not found",
                    entityType="AuditReport",
                    entityId=str(report_id),
                    logLevel="WARNING"
                )
                continue
        
        if reports_json:
            audit.Report = json.dumps(reports_json)
            audit.save()
            print(f"Successfully saved {len(reports_json)} reports to audit {audit.AuditId}")
            
            # Log success
            send_log(
                module="AuditReport",
                actionType="REPORTS_ATTACHED",
                description=f"Successfully attached {len(reports_json)} reports to audit {audit.AuditId}",
                entityType="Audit",
                entityId=str(audit.AuditId),
                additionalInfo={"report_count": len(reports_json)}
            )
            
            # Send notification about reports being attached
            try:
                notification_service = NotificationService()
                
                # Get auditor email
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT u.Email 
                        FROM users u 
                        JOIN audit a ON u.UserId = a.Auditor 
                        WHERE a.AuditId = %s
                    """, [audit.AuditId])
                    auditor_email = cursor.fetchone()[0]
                
                if auditor_email:
                    notification_data = {
                        'notification_type': 'auditReportsAttached',
                        'email': auditor_email,
                        'email_type': 'gmail',
                        'template_data': [
                            f"Auditor", 
                            f"Audit #{audit.AuditId}", 
                            f"{len(reports_json)}", 
                            datetime.now().strftime('%Y-%m-%d')
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
                    
                    # Log notification sent
                    send_log(
                        module="AuditReport",
                        actionType="NOTIFICATION_SENT",
                        description=f"Notification sent to auditor about attached reports for audit {audit.AuditId}",
                        entityType="Notification",
                        entityId=str(audit.AuditId),
                        additionalInfo={"email": auditor_email}
                    )
            except Exception as e:
                print(f"Failed to send notification: {str(e)}")
                send_log(
                    module="AuditReport",
                    actionType="NOTIFICATION_ERROR",
                    description=f"Failed to send notification: {str(e)}",
                    entityType="Notification",
                    entityId=str(audit.AuditId),
                    logLevel="ERROR",
                    additionalInfo={"error": str(e)}
                )
            
    except Exception as e:
        print(f"ERROR in handle_selected_reports: {str(e)}")
        send_log(
            module="AuditReport",
            actionType="HANDLE_SELECTED_REPORTS_ERROR",
            description=f"Error handling selected reports: {str(e)}",
            entityType="Audit",
            entityId=str(audit.AuditId) if 'audit' in locals() else None,
            logLevel="ERROR",
            additionalInfo={"error": str(e)}
        )
        # Don't raise the exception, just log it
        pass 

@api_view(['GET'])
@permission_classes([AuditViewPermission])
@audit_view_reports_required
def get_report_details(request):
    """
    Get details for specific report IDs
    """
    try:
        report_ids_str = request.GET.get('report_ids', '')
        user_id = request.session.get('user_id')
        
        if not report_ids_str:
            send_log(
                module="AuditReport",
                actionType="GET_REPORT_DETAILS_ERROR",
                description="No report IDs provided",
                userId=user_id,
                entityType="AuditReport",
                logLevel="ERROR"
            )
            return Response({'error': 'No report IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Split and clean the report IDs
        report_ids = [int(id.strip()) for id in report_ids_str.split(',') if id.strip()]
        
        if not report_ids:
            send_log(
                module="AuditReport",
                actionType="GET_REPORT_DETAILS_ERROR",
                description="No valid report IDs found",
                userId=user_id,
                entityType="AuditReport",
                logLevel="ERROR"
            )
            return Response({'error': 'No valid report IDs found'}, status=status.HTTP_400_BAD_REQUEST)

        # Log the request
        send_log(
            module="AuditReport",
            actionType="GET_REPORT_DETAILS",
            description=f"Getting details for {len(report_ids)} reports",
            userId=user_id,
            entityType="AuditReport",
            additionalInfo={"report_ids": report_ids}
        )

        # Build query to get report details with proper joins
        query = """
            SELECT 
                ar.ReportId as report_id,
                ar.Report as report,
                a.CompletionDate as report_date,
                auditor.UserName as auditor,
                reviewer.UserName as reviewer
            FROM audit_report ar
            JOIN audit a ON ar.AuditId = a.AuditId
            JOIN users auditor ON a.Auditor = auditor.UserId
            LEFT JOIN users reviewer ON a.Reviewer = reviewer.UserId
            WHERE ar.ReportId IN %s
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [tuple(report_ids)])
            columns = [col[0] for col in cursor.description]
            reports = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Format dates
            for report in reports:
                if report.get('report_date'):
                    report['report_date'] = report['report_date'].strftime('%Y-%m-%d')
            
            if not reports:
                send_log(
                    module="AuditReport",
                    actionType="GET_REPORT_DETAILS_NOT_FOUND",
                    description="No reports found for the provided IDs",
                    userId=user_id,
                    entityType="AuditReport",
                    logLevel="WARNING",
                    additionalInfo={"report_ids": report_ids}
                )
                return Response({'error': 'No reports found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Log success
            send_log(
                module="AuditReport",
                actionType="GET_REPORT_DETAILS_SUCCESS",
                description=f"Successfully retrieved {len(reports)} reports",
                userId=user_id,
                entityType="AuditReport",
                additionalInfo={"report_count": len(reports)}
            )
                
            return Response({'reports': reports})
            
    except Exception as e:
        print(f"Error in get_report_details: {str(e)}")
        user_id = request.session.get('user_id')
        send_log(
            module="AuditReport",
            actionType="GET_REPORT_DETAILS_ERROR",
            description=f"Error getting report details: {str(e)}",
            userId=user_id,
            entityType="AuditReport",
            logLevel="ERROR",
            additionalInfo={"error": str(e)}
        )
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 