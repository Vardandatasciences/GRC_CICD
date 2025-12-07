"""
RiskAvaire Integration for Automatic Event Creation

This module handles automatic event creation based on RiskAvaire tool triggers.
It monitors risk, compliance, and audit conditions and creates appropriate events.
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging

from ...rbac.permissions import EventViewAllPermission, EventViewModulePermission
from ...rbac.utils import RBACUtils

from ...models import (
    Event, Framework, Policy, Compliance, Audit, Risk, Incident, 
    SubPolicy, Users, RiskInstance, RBAC
)

# Configure logging
logger = logging.getLogger(__name__)

def _should_show_event_for_user(user_id, linked_record_type):
    """
    Determine if an event should be shown to a user based on their role and the LinkedRecordType
    
    Args:
        user_id: User ID to check
        linked_record_type: The LinkedRecordType of the event
    
    Returns:
        bool: True if the event should be shown to the user, False otherwise
    """
    try:
        rbac_record = RBAC.objects.filter(user=user_id, is_active='Y').first()
        if not rbac_record:
            logger.warning(f"[RBAC FILTER] No RBAC record found for user {user_id}")
            return False
        
        # Admin roles can see all events
        admin_roles = [
            'GRC Administrator',
            'Audit Manager', 
            'Internal Auditor',
            'External Auditor',
            'Audit Reviewer'
        ]
        
        if rbac_record.role in admin_roles:
            logger.info(f"[RBAC FILTER] User {user_id} has admin role - showing all events")
            return True
        
        # If user has view_all_event permission, they can see all events
        if rbac_record.view_all_event:
            logger.info(f"[RBAC FILTER] User {user_id} has view_all_event permission - showing all events")
            return True
        
        # Role-based filtering for specific LinkedRecordTypes
        if linked_record_type == 'compliance':
            # Show compliance events to compliance-related roles
            compliance_roles = [
                'Compliance Manager',
                'Compliance Officer', 
                'Compliance Approver'
            ]
            if rbac_record.role in compliance_roles:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} can see compliance events")
                return True
            else:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} cannot see compliance events")
                return False
                
        elif linked_record_type == 'policy':
            # Show policy events to policy-related roles
            policy_roles = [
                'Policy Manager',
                'Policy Approver'
            ]
            if rbac_record.role in policy_roles:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} can see policy events")
                return True
            else:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} cannot see policy events")
                return False
                
        elif linked_record_type == 'audit':
            # Show audit events to audit-related roles
            audit_roles = [
                'Audit Manager',
                'Internal Auditor',
                'External Auditor',
                'Audit Reviewer'
            ]
            if rbac_record.role in audit_roles:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} can see audit events")
                return True
            else:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} cannot see audit events")
                return False
                
        elif linked_record_type == 'risk':
            # Show risk events to risk-related roles
            risk_roles = [
                'Risk Manager',
                'Risk Analyst',
                'Risk Reviewer'
            ]
            if rbac_record.role in risk_roles:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} can see risk events")
                return True
            else:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} cannot see risk events")
                return False
                
        elif linked_record_type == 'incident':
            # Show incident events to incident-related roles
            incident_roles = [
                'Incident Response Manager',
                'Incident Analyst'
            ]
            if rbac_record.role in incident_roles:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} can see incident events")
                return True
            else:
                logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} cannot see incident events")
                return False
        
        # For other LinkedRecordTypes or if user has view_module_event permission, 
        # let the existing module-based filtering handle it
        logger.info(f"[RBAC FILTER] User {user_id} with role {rbac_record.role} - using module-based filtering for LinkedRecordType: {linked_record_type}")
        return True
        
    except Exception as e:
        logger.error(f"[RBAC FILTER] Error checking event visibility for user {user_id}: {e}")
        return False

class RiskAvaireEventTrigger:
    """
    Handles automatic event creation based on RiskAvaire tool conditions
    """
    
    @staticmethod
    def create_risk_event(risk_instance, trigger_type="risk_detected"):
        """
        Create an event when a risk is detected or status changes
        """
        try:
            # Determine event details based on trigger type
            event_titles = {
                "risk_detected": f"Risk Detected: {risk_instance.RiskTitle}",
                "risk_escalated": f"Risk Escalated: {risk_instance.RiskTitle}",
                "mitigation_overdue": f"Risk Mitigation Overdue: {risk_instance.RiskTitle}",
                "risk_approved": f"Risk Approved: {risk_instance.RiskTitle}",
                "risk_rejected": f"Risk Rejected: {risk_instance.RiskTitle}"
            }
            
            event_descriptions = {
                "risk_detected": f"New risk identified: {risk_instance.RiskDescription}",
                "risk_escalated": f"Risk has been escalated due to high impact: {risk_instance.RiskDescription}",
                "mitigation_overdue": f"Risk mitigation is overdue. Due date: {risk_instance.MitigationDueDate}",
                "risk_approved": f"Risk has been approved for implementation",
                "risk_rejected": f"Risk has been rejected and requires review"
            }
            
            # Determine priority based on risk criticality
            priority_mapping = {
                'Critical': 'Critical',
                'High': 'High', 
                'Medium': 'Medium',
                'Low': 'Low'
            }
            
            priority = priority_mapping.get(risk_instance.Criticality, 'Medium')
            
            # Determine event status based on trigger
            status_mapping = {
                "risk_detected": "Pending Review",
                "risk_escalated": "Under Review", 
                "mitigation_overdue": "Pending Review",
                "risk_approved": "Approved",
                "risk_rejected": "Rejected"
            }
            
            event_status = status_mapping.get(trigger_type, "Pending Review")
            
            # Create the event
            event_data = {
                'EventTitle': event_titles.get(trigger_type, f"Risk Event: {risk_instance.RiskTitle}"),
                'Description': event_descriptions.get(trigger_type, f"Risk-related event: {risk_instance.RiskDescription}"),
                'LinkedRecordType': 'risk',
                'LinkedRecordId': risk_instance.RiskInstanceId,
                'LinkedRecordName': risk_instance.RiskTitle,
                'Category': 'Risk Management',
                'Priority': priority,
                'Status': event_status,
                'StartDate': timezone.now().date(),
                'EndDate': risk_instance.MitigationDueDate if risk_instance.MitigationDueDate else (timezone.now().date() + timedelta(days=30)),
                'RecurrenceType': 'Non-Recurring',
                'CreatedBy': Users.objects.filter(UserId=risk_instance.UserId).first() if risk_instance.UserId else None,
                'Owner': Users.objects.filter(UserId=risk_instance.UserId).first() if risk_instance.UserId else None,
                'Reviewer': Users.objects.filter(UserId=risk_instance.ReviewerId).first() if risk_instance.ReviewerId else None,
                'IsTemplate': False
            }
            
            event = Event.objects.create(**event_data)
            logger.info(f"Created risk event {event.EventId_Generated} for risk {risk_instance.RiskInstanceId}")
            
            # Send email notifications for event creation
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                
                # Get recipients: Owner, Reviewer, and risk creator
                recipients = []
                if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                    recipients.append(('owner', event.Owner.Email, event.Owner.UserName or event.Owner.Email.split('@')[0]))
                if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                    recipients.append(('reviewer', event.Reviewer.Email, event.Reviewer.UserName or event.Reviewer.Email.split('@')[0]))
                if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                    recipients.append(('creator', event.CreatedBy.Email, event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0]))
                
                # Send notifications to all recipients
                for role, email, name in recipients:
                    try:
                        notification_data = {
                            'notification_type': 'eventCreated',
                            'email': email,
                            'email_type': 'gmail',
                            'template_data': [
                                name,
                                event.EventTitle,
                                event.Description or 'No description provided',
                                event.CreatedBy.UserName if event.CreatedBy else 'System',
                                event.Category or 'General'
                            ]
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                        logger.info(f"Sent event creation notification to {role} ({email})")
                    except Exception as notify_error:
                        logger.error(f"Error sending notification to {email}: {str(notify_error)}")
            except Exception as e:
                logger.error(f"Error in event notification service: {str(e)}")
                # Don't fail event creation if notifications fail
            
            return event
            
        except Exception as e:
            logger.error(f"Error creating risk event: {str(e)}")
            return None
    
    @staticmethod
    def create_compliance_event(compliance, trigger_type="compliance_breach"):
        """
        Create an event when compliance issues are detected
        """
        try:
            event_titles = {
                "compliance_breach": f"Compliance Breach: {compliance.ComplianceTitle}",
                "compliance_overdue": f"Compliance Overdue: {compliance.ComplianceTitle}",
                "compliance_approved": f"Compliance Approved: {compliance.ComplianceTitle}",
                "compliance_rejected": f"Compliance Rejected: {compliance.ComplianceTitle}",
                "compliance_review_required": f"Compliance Review Required: {compliance.ComplianceTitle}"
            }
            
            event_descriptions = {
                "compliance_breach": f"Compliance breach detected: {compliance.ComplianceItemDescription}",
                "compliance_overdue": f"Compliance item is overdue for review",
                "compliance_approved": f"Compliance item has been approved",
                "compliance_rejected": f"Compliance item has been rejected and requires attention",
                "compliance_review_required": f"Compliance item requires periodic review"
            }
            
            # Determine priority based on compliance criticality
            priority_mapping = {
                'Critical': 'Critical',
                'High': 'High',
                'Medium': 'Medium', 
                'Low': 'Low'
            }
            
            priority = priority_mapping.get(compliance.Criticality, 'Medium')
            
            event_data = {
                'EventTitle': event_titles.get(trigger_type, f"Compliance Event: {compliance.ComplianceTitle}"),
                'Description': event_descriptions.get(trigger_type, f"Compliance-related event: {compliance.ComplianceItemDescription}"),
                'LinkedRecordType': 'compliance',
                'LinkedRecordId': compliance.ComplianceId,
                'LinkedRecordName': compliance.ComplianceTitle,
                'Category': 'Compliance Management',
                'Priority': priority,
                'Status': 'Pending Review',
                'StartDate': timezone.now().date(),
                'EndDate': timezone.now().date() + timedelta(days=30),
                'RecurrenceType': 'Non-Recurring',
                'IsTemplate': False
            }
            
            event = Event.objects.create(**event_data)
            logger.info(f"Created compliance event {event.EventId_Generated} for compliance {compliance.ComplianceId}")
            
            # Send email notifications for event creation
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                
                # Get recipients: Owner, Reviewer, and compliance creator
                recipients = []
                if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                    recipients.append(('owner', event.Owner.Email, event.Owner.UserName or event.Owner.Email.split('@')[0]))
                if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                    recipients.append(('reviewer', event.Reviewer.Email, event.Reviewer.UserName or event.Reviewer.Email.split('@')[0]))
                if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                    recipients.append(('creator', event.CreatedBy.Email, event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0]))
                
                # Send notifications to all recipients
                for role, email, name in recipients:
                    try:
                        notification_data = {
                            'notification_type': 'eventCreated',
                            'email': email,
                            'email_type': 'gmail',
                            'template_data': [
                                name,
                                event.EventTitle,
                                event.Description or 'No description provided',
                                event.CreatedBy.UserName if event.CreatedBy else 'System',
                                event.Category or 'General'
                            ]
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                        logger.info(f"Sent event creation notification to {role} ({email})")
                    except Exception as notify_error:
                        logger.error(f"Error sending notification to {email}: {str(notify_error)}")
            except Exception as e:
                logger.error(f"Error in event notification service: {str(e)}")
            
            return event
            
        except Exception as e:
            logger.error(f"Error creating compliance event: {str(e)}")
            return None
    
    @staticmethod
    def create_audit_event(audit, trigger_type="audit_finding"):
        """
        Create an event when audit findings are detected
        """
        try:
            event_titles = {
                "audit_finding": f"Audit Finding: {audit.AuditTitle}",
                "audit_overdue": f"Audit Overdue: {audit.AuditTitle}",
                "audit_approved": f"Audit Approved: {audit.AuditTitle}",
                "audit_rejected": f"Audit Rejected: {audit.AuditTitle}",
                "audit_scheduled": f"Audit Scheduled: {audit.AuditTitle}"
            }
            
            event_descriptions = {
                "audit_finding": f"Audit finding identified: {audit.AuditDescription}",
                "audit_overdue": f"Audit is overdue for completion",
                "audit_approved": f"Audit has been approved",
                "audit_rejected": f"Audit has been rejected and requires attention",
                "audit_scheduled": f"Audit has been scheduled for execution"
            }
            
            event_data = {
                'EventTitle': event_titles.get(trigger_type, f"Audit Event: {audit.AuditTitle}"),
                'Description': event_descriptions.get(trigger_type, f"Audit-related event: {audit.AuditDescription}"),
                'LinkedRecordType': 'audit',
                'LinkedRecordId': audit.AuditId,
                'LinkedRecordName': audit.AuditTitle,
                'Category': 'Audit Management',
                'Priority': 'High',  # Audit findings are typically high priority
                'Status': 'Pending Review',
                'StartDate': timezone.now().date(),
                'EndDate': timezone.now().date() + timedelta(days=14),  # Shorter timeline for audit events
                'RecurrenceType': 'Non-Recurring',
                'IsTemplate': False
            }
            
            event = Event.objects.create(**event_data)
            logger.info(f"Created audit event {event.EventId_Generated} for audit {audit.AuditId}")
            
            # Send email notifications for event creation
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                
                # Get recipients: Owner, Reviewer, and audit creator
                recipients = []
                if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                    recipients.append(('owner', event.Owner.Email, event.Owner.UserName or event.Owner.Email.split('@')[0]))
                if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                    recipients.append(('reviewer', event.Reviewer.Email, event.Reviewer.UserName or event.Reviewer.Email.split('@')[0]))
                if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                    recipients.append(('creator', event.CreatedBy.Email, event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0]))
                
                # Send notifications to all recipients
                for role, email, name in recipients:
                    try:
                        notification_data = {
                            'notification_type': 'eventCreated',
                            'email': email,
                            'email_type': 'gmail',
                            'template_data': [
                                name,
                                event.EventTitle,
                                event.Description or 'No description provided',
                                event.CreatedBy.UserName if event.CreatedBy else 'System',
                                event.Category or 'General'
                            ]
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                        logger.info(f"Sent event creation notification to {role} ({email})")
                    except Exception as notify_error:
                        logger.error(f"Error sending notification to {email}: {str(notify_error)}")
            except Exception as e:
                logger.error(f"Error in event notification service: {str(e)}")
            
            return event
            
        except Exception as e:
            logger.error(f"Error creating audit event: {str(e)}")
            return None
    
    @staticmethod
    def create_incident_event(incident, trigger_type="incident_detected"):
        """
        Create an event when incidents are detected
        """
        try:
            event_titles = {
                "incident_detected": f"Incident Detected: {incident.IncidentTitle}",
                "incident_escalated": f"Incident Escalated: {incident.IncidentTitle}",
                "incident_resolved": f"Incident Resolved: {incident.IncidentTitle}",
                "incident_overdue": f"Incident Response Overdue: {incident.IncidentTitle}"
            }
            
            event_descriptions = {
                "incident_detected": f"New incident reported: {incident.IncidentDescription}",
                "incident_escalated": f"Incident has been escalated due to severity",
                "incident_resolved": f"Incident has been resolved",
                "incident_overdue": f"Incident response is overdue"
            }
            
            # Determine priority based on incident severity
            priority_mapping = {
                'Critical': 'Critical',
                'High': 'High',
                'Medium': 'Medium',
                'Low': 'Low'
            }
            
            priority = priority_mapping.get(incident.Severity, 'Medium')
            
            event_data = {
                'EventTitle': event_titles.get(trigger_type, f"Incident Event: {incident.IncidentTitle}"),
                'Description': event_descriptions.get(trigger_type, f"Incident-related event: {incident.IncidentDescription}"),
                'LinkedRecordType': 'incident',
                'LinkedRecordId': incident.IncidentId,
                'LinkedRecordName': incident.IncidentTitle,
                'Category': 'Incident Management',
                'Priority': priority,
                'Status': 'Pending Review',
                'StartDate': timezone.now().date(),
                'EndDate': timezone.now().date() + timedelta(days=7),  # Shorter timeline for incidents
                'RecurrenceType': 'Non-Recurring',
                'IsTemplate': False
            }
            
            event = Event.objects.create(**event_data)
            logger.info(f"Created incident event {event.EventId_Generated} for incident {incident.IncidentId}")
            
            # Send email notifications for event creation
            try:
                from ...routes.Global.notification_service import NotificationService
                notification_service = NotificationService()
                
                # Get recipients: Owner, Reviewer, and incident creator
                recipients = []
                if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                    recipients.append(('owner', event.Owner.Email, event.Owner.UserName or event.Owner.Email.split('@')[0]))
                if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                    recipients.append(('reviewer', event.Reviewer.Email, event.Reviewer.UserName or event.Reviewer.Email.split('@')[0]))
                if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                    recipients.append(('creator', event.CreatedBy.Email, event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0]))
                
                # Send notifications to all recipients
                for role, email, name in recipients:
                    try:
                        notification_data = {
                            'notification_type': 'eventCreated',
                            'email': email,
                            'email_type': 'gmail',
                            'template_data': [
                                name,
                                event.EventTitle,
                                event.Description or 'No description provided',
                                event.CreatedBy.UserName if event.CreatedBy else 'System',
                                event.Category or 'General'
                            ]
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                        logger.info(f"Sent event creation notification to {role} ({email})")
                    except Exception as notify_error:
                        logger.error(f"Error sending notification to {email}: {str(notify_error)}")
            except Exception as e:
                logger.error(f"Error in event notification service: {str(e)}")
            
            return event
            
        except Exception as e:
            logger.error(f"Error creating incident event: {str(e)}")
            return None

    @staticmethod
    def create_policy_event(policy, trigger_type="policy_review_due"):
        """
        Create an event when a policy needs attention or status changes
        """
        try:
            # Determine event details based on trigger type
            event_titles = {
                "policy_review_due": f"Policy Review Due: {policy.PolicyName}",
                "policy_update_required": f"Policy Update Required: {policy.PolicyName}",
                "policy_approval_needed": f"Policy Approval Needed: {policy.PolicyName}",
                "policy_expiration_warning": f"Policy Expiration Warning: {policy.PolicyName}",
                "policy_approved": f"Policy Approved: {policy.PolicyName}",
                "policy_rejected": f"Policy Rejected: {policy.PolicyName}",
                "policy_published": f"Policy Published: {policy.PolicyName}",
                "policy_archived": f"Policy Archived: {policy.PolicyName}"
            }
            
            event_descriptions = {
                "policy_review_due": f"Policy review is due for: {policy.PolicyName}. Last reviewed: {policy.LastReviewedDate if hasattr(policy, 'LastReviewedDate') else 'Never'}",
                "policy_update_required": f"Policy requires updates: {policy.PolicyName}. Reason: Regulatory changes or business requirements",
                "policy_approval_needed": f"Policy requires approval: {policy.PolicyName}. Status: {policy.Status}",
                "policy_expiration_warning": f"Policy will expire soon: {policy.PolicyName}. Expiry date: {policy.ExpiryDate if hasattr(policy, 'ExpiryDate') else 'Not set'}",
                "policy_approved": f"Policy has been approved: {policy.PolicyName}",
                "policy_rejected": f"Policy has been rejected: {policy.PolicyName}. Requires revision",
                "policy_published": f"Policy has been published: {policy.PolicyName}",
                "policy_archived": f"Policy has been archived: {policy.PolicyName}"
            }
            
            # Determine priority based on policy criticality and trigger type
            priority_mapping = {
                "policy_review_due": "Medium",
                "policy_update_required": "High",
                "policy_approval_needed": "High",
                "policy_expiration_warning": "High",
                "policy_approved": "Low",
                "policy_rejected": "Medium",
                "policy_published": "Low",
                "policy_archived": "Low"
            }
            
            priority = priority_mapping.get(trigger_type, "Medium")
            
            # Determine event status based on trigger
            status_mapping = {
                "policy_review_due": "Pending Review",
                "policy_update_required": "Pending Review",
                "policy_approval_needed": "Under Review",
                "policy_expiration_warning": "Pending Review",
                "policy_approved": "Approved",
                "policy_rejected": "Rejected",
                "policy_published": "Completed",
                "policy_archived": "Completed"
            }
            
            event_status = status_mapping.get(trigger_type, "Pending Review")
            
            # Calculate end date based on trigger type
            if trigger_type in ["policy_review_due", "policy_update_required"]:
                end_date = timezone.now().date() + timedelta(days=30)  # 30 days for reviews/updates
            elif trigger_type == "policy_expiration_warning":
                end_date = timezone.now().date() + timedelta(days=7)   # 7 days for expiration warnings
            else:
                end_date = timezone.now().date() + timedelta(days=14)  # 14 days default
            
            # Create the event
            event_data = {
                'EventTitle': event_titles.get(trigger_type, f"Policy Event: {policy.PolicyName}"),
                'Description': event_descriptions.get(trigger_type, f"Policy-related event: {policy.PolicyName}"),
                'LinkedRecordType': 'policy',
                'LinkedRecordId': policy.PolicyId,
                'LinkedRecordName': policy.PolicyName,
                'Category': 'Policy Management',
                'Priority': priority,
                'Status': event_status,
                'StartDate': timezone.now().date(),
                'EndDate': end_date,
                'RecurrenceType': 'Non-Recurring',
                'CreatedBy': Users.objects.filter(UserId=policy.CreatedBy).first() if hasattr(policy, 'CreatedBy') and policy.CreatedBy else None,
                'Owner': Users.objects.filter(UserId=policy.OwnerId).first() if hasattr(policy, 'OwnerId') and policy.OwnerId else None,
                'Reviewer': Users.objects.filter(UserId=policy.ReviewerId).first() if hasattr(policy, 'ReviewerId') and policy.ReviewerId else None,
                'IsTemplate': False
            }
            
            # Create the event
            # Note: This is typically called from transaction.on_commit() in signal handlers
            # to prevent event creation errors from breaking the main transaction
            try:
                event = Event.objects.create(**event_data)
                logger.info(f"Created policy event {event.EventId_Generated} for policy {policy.PolicyId}")
                
                # Send email notifications for event creation
                try:
                    from ...routes.Global.notification_service import NotificationService
                    notification_service = NotificationService()
                    
                    # Get recipients: Owner, Reviewer, and policy creator
                    recipients = []
                    if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                        recipients.append(('owner', event.Owner.Email, event.Owner.UserName or event.Owner.Email.split('@')[0]))
                    if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                        recipients.append(('reviewer', event.Reviewer.Email, event.Reviewer.UserName or event.Reviewer.Email.split('@')[0]))
                    if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                        recipients.append(('creator', event.CreatedBy.Email, event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0]))
                    
                    # Send notifications to all recipients
                    for role, email, name in recipients:
                        try:
                            notification_data = {
                                'notification_type': 'eventCreated',
                                'email': email,
                                'email_type': 'gmail',
                                'template_data': [
                                    name,
                                    event.EventTitle,
                                    event.Description or 'No description provided',
                                    event.CreatedBy.UserName if event.CreatedBy else 'System',
                                    event.Category or 'General'
                                ]
                            }
                            notification_service.send_multi_channel_notification(notification_data)
                            logger.info(f"Sent event creation notification to {role} ({email})")
                        except Exception as notify_error:
                            logger.error(f"Error sending notification to {email}: {str(notify_error)}")
                except Exception as e:
                    logger.error(f"Error in event notification service: {str(e)}")
                
                return event
            except Exception as create_error:
                # Log error but don't raise - event creation failures shouldn't break policy creation
                logger.error(f"Error creating policy event for policy {policy.PolicyId}: {str(create_error)}")
                return None
            
        except Exception as e:
            logger.error(f"Error creating policy event: {str(e)}")
            return None


def handle_riskavaire_data(data, record_type):
    """
    Handle direct data from RiskAvaire tool and create/update records
    """
    try:
        if record_type == 'risk' and data.get('risk_details'):
            risk_details = data['risk_details']
            
            # Create or update risk instance
            risk_data = {
                'RiskTitle': risk_details.get('title', 'Risk from RiskAvaire'),
                'RiskDescription': risk_details.get('description', 'Risk detected by RiskAvaire tool'),
                'Criticality': risk_details.get('criticality', 'Medium'),
                'RiskStatus': risk_details.get('status', 'Not Assigned'),
                'MitigationStatus': risk_details.get('mitigation_status', 'Yet to Start'),
                'RiskLikelihood': risk_details.get('likelihood', 5),
                'RiskImpact': risk_details.get('impact', 5),
                'RiskExposureRating': risk_details.get('exposure_rating', 25),
                'Category': risk_details.get('category', 'General'),
                'RiskType': risk_details.get('risk_type', 'Current'),
                'CreatedAt': timezone.now().date()
            }
            
            # Set mitigation due date if provided
            if risk_details.get('mitigation_due_date'):
                try:
                    from datetime import datetime
                    risk_data['MitigationDueDate'] = datetime.strptime(
                        risk_details['mitigation_due_date'], '%Y-%m-%d'
                    ).date()
                except:
                    pass
            
            # Create the risk instance
            risk = RiskInstance.objects.create(**risk_data)
            logger.info(f"Created risk instance from RiskAvaire: {risk.RiskInstanceId}")
            return risk.RiskInstanceId
            
        elif record_type == 'compliance' and data.get('compliance_details'):
            compliance_details = data['compliance_details']
            
            # Create compliance record
            compliance_data = {
                'ComplianceTitle': compliance_details.get('title', 'Compliance from RiskAvaire'),
                'ComplianceItemDescription': compliance_details.get('description', 'Compliance item from RiskAvaire tool'),
                'ComplianceType': compliance_details.get('type', 'Regulatory'),
                'Criticality': compliance_details.get('criticality', 'Medium'),
                'Status': compliance_details.get('status', 'Under Review'),
                'ComplianceVersion': '1.0',
                'CreatedByDate': timezone.now().date(),
                'ActiveInactive': 'Active'
            }
            
            compliance = Compliance.objects.create(**compliance_data)
            logger.info(f"Created compliance record from RiskAvaire: {compliance.ComplianceId}")
            return compliance.ComplianceId
            
        elif record_type == 'incident' and data.get('incident_details'):
            incident_details = data['incident_details']
            
            # Create incident record
            incident_data = {
                'IncidentTitle': incident_details.get('title', 'Incident from RiskAvaire'),
                'IncidentDescription': incident_details.get('description', 'Incident detected by RiskAvaire tool'),
                'Severity': incident_details.get('severity', 'Medium'),
                'Status': incident_details.get('status', 'Open'),
                'IncidentDate': timezone.now().date(),
                'ReportedBy': incident_details.get('reported_by', 'RiskAvaire Tool')
            }
            
            incident = Incident.objects.create(**incident_data)
            logger.info(f"Created incident record from RiskAvaire: {incident.IncidentId}")
            return incident.IncidentId
            
    except Exception as e:
        logger.error(f"Error handling RiskAvaire data: {str(e)}")
        return None
    
    return None


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def riskavaire_webhook(request):
    """
    Webhook endpoint for RiskAvaire tool to send event triggers
    """
    try:
        data = request.data
        logger.info(f"RiskAvaire webhook received: {data}")
        
        # Validate required fields
        if not data.get('trigger_type'):
            return Response({
                'success': False,
                'message': 'trigger_type is required'
            }, status=400)
        
        trigger_type = data.get('trigger_type')
        record_type = data.get('record_type')  # risk, compliance, audit, incident
        record_id = data.get('record_id')
        
        # Handle direct data from RiskAvaire tool (when record_id is not available)
        if not record_id and data.get('risk_details'):
            # Create or update record from RiskAvaire data
            record_id = handle_riskavaire_data(data, record_type)
        
        created_events = []
        
        # Handle different record types
        if record_type == 'risk' and record_id:
            try:
                risk_instance = RiskInstance.objects.get(RiskInstanceId=record_id)
                event = RiskAvaireEventTrigger.create_risk_event(risk_instance, trigger_type)
                if event:
                    created_events.append({
                        'event_id': event.EventId,
                        'event_id_generated': event.EventId_Generated,
                        'event_title': event.EventTitle
                    })
            except RiskInstance.DoesNotExist:
                logger.warning(f"Risk instance {record_id} not found")
        
        elif record_type == 'compliance' and record_id:
            try:
                compliance = Compliance.objects.get(ComplianceId=record_id)
                event = RiskAvaireEventTrigger.create_compliance_event(compliance, trigger_type)
                if event:
                    created_events.append({
                        'event_id': event.EventId,
                        'event_id_generated': event.EventId_Generated,
                        'event_title': event.EventTitle
                    })
            except Compliance.DoesNotExist:
                logger.warning(f"Compliance {record_id} not found")
        
        elif record_type == 'audit' and record_id:
            try:
                audit = Audit.objects.get(AuditId=record_id)
                event = RiskAvaireEventTrigger.create_audit_event(audit, trigger_type)
                if event:
                    created_events.append({
                        'event_id': event.EventId,
                        'event_id_generated': event.EventId_Generated,
                        'event_title': event.EventTitle
                    })
            except Audit.DoesNotExist:
                logger.warning(f"Audit {record_id} not found")
        
        elif record_type == 'incident' and record_id:
            try:
                incident = Incident.objects.get(IncidentId=record_id)
                event = RiskAvaireEventTrigger.create_incident_event(incident, trigger_type)
                if event:
                    created_events.append({
                        'event_id': event.EventId,
                        'event_id_generated': event.EventId_Generated,
                        'event_title': event.EventTitle
                    })
            except Incident.DoesNotExist:
                logger.warning(f"Incident {record_id} not found")
        
        elif record_type == 'policy' and record_id:
            try:
                policy = Policy.objects.get(PolicyId=record_id)
                event = RiskAvaireEventTrigger.create_policy_event(policy, trigger_type)
                if event:
                    created_events.append({
                        'event_id': event.EventId,
                        'event_id_generated': event.EventId_Generated,
                        'event_title': event.EventTitle
                    })
            except Policy.DoesNotExist:
                logger.warning(f"Policy {record_id} not found")
        
        return Response({
            'success': True,
            'message': f'Processed {len(created_events)} events',
            'created_events': created_events
        })
        
    except Exception as e:
        logger.error(f"Error in RiskAvaire webhook: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error processing webhook: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def check_automated_triggers(request):
    """
    Check for conditions that should trigger automatic events
    This can be called periodically or manually
    """
    try:
        created_events = []
        current_date = timezone.now().date()
        
        # Check for overdue risk mitigations
        overdue_risks = RiskInstance.objects.filter(
            MitigationDueDate__lt=current_date,
            MitigationStatus__in=['Yet to Start', 'Work In Progress'],
            RiskStatus='Approved'
        )
        
        for risk in overdue_risks:
            # Check if event already exists for this overdue risk
            existing_event = Event.objects.filter(
                LinkedRecordType='risk',
                LinkedRecordId=risk.RiskInstanceId,
                EventTitle__icontains='Mitigation Overdue'
            ).first()
            
            if not existing_event:
                event = RiskAvaireEventTrigger.create_risk_event(risk, "mitigation_overdue")
                if event:
                    created_events.append({
                        'type': 'overdue_mitigation',
                        'event_id': event.EventId,
                        'event_title': event.EventTitle
                    })
        
        # Check for high-priority risks that need escalation
        high_priority_risks = RiskInstance.objects.filter(
            Criticality__in=['Critical', 'High'],
            RiskStatus='Not Assigned',
            CreatedAt__gte=current_date - timedelta(days=7)  # Only recent risks
        )
        
        for risk in high_priority_risks:
            existing_event = Event.objects.filter(
                LinkedRecordType='risk',
                LinkedRecordId=risk.RiskInstanceId,
                EventTitle__icontains='Escalated'
            ).first()
            
            if not existing_event:
                event = RiskAvaireEventTrigger.create_risk_event(risk, "risk_escalated")
                if event:
                    created_events.append({
                        'type': 'risk_escalation',
                        'event_id': event.EventId,
                        'event_title': event.EventTitle
                    })
        
        # Check for compliance items that need review
        compliance_review_needed = Compliance.objects.filter(
            Status='Under Review',
            CreatedByDate__lte=current_date - timedelta(days=90)  # 90 days old
        )
        
        for compliance in compliance_review_needed:
            existing_event = Event.objects.filter(
                LinkedRecordType='compliance',
                LinkedRecordId=compliance.ComplianceId,
                EventTitle__icontains='Review Required'
            ).first()
            
            if not existing_event:
                event = RiskAvaireEventTrigger.create_compliance_event(compliance, "compliance_review_required")
                if event:
                    created_events.append({
                        'type': 'compliance_review',
                        'event_id': event.EventId,
                        'event_title': event.EventTitle
                    })
        
        return Response({
            'success': True,
            'message': f'Checked automated triggers and created {len(created_events)} events',
            'created_events': created_events
        })
        
    except Exception as e:
        logger.error(f"Error checking automated triggers: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error checking triggers: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
def get_riskavaire_events(request):
    """
    Get events created by RiskAvaire integration with RBAC filtering
    """
    try:
        # Get user ID for RBAC filtering
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get user's accessible modules for filtering
        accessible_modules = RBACUtils.get_user_accessible_modules(user_id)
        logger.info(f"[RBAC RISKAVAIRE] User {user_id} accessible modules: {accessible_modules}")
        
        # Get events that are linked to risk, compliance, audit, incident, or policy records
        events = Event.objects.filter(
            LinkedRecordType__in=['risk', 'compliance', 'audit', 'incident', 'policy']
        ).order_by('-CreatedAt')
        
        events_data = []
        for event in events:
            # Determine framework and module based on linked record type
            framework = 'N/A'
            module = 'N/A'
            
            if event.LinkedRecordType == 'risk':
                module = 'Risk Management'
                framework = 'Risk Management Framework'
            elif event.LinkedRecordType == 'compliance':
                module = 'Compliance Management'
                framework = 'Compliance Framework'
            elif event.LinkedRecordType == 'audit':
                module = 'Audit Management'
                framework = 'Audit Framework'
            elif event.LinkedRecordType == 'incident':
                module = 'Incident Management'
                framework = 'Incident Management Framework'
            elif event.LinkedRecordType == 'policy':
                module = 'Policy Management'
                framework = 'Policy Management Framework'
            
            # Apply RBAC filtering - only include events from accessible modules
            if module not in accessible_modules:
                logger.info(f"[RBAC RISKAVAIRE] Filtering out event {event.EventId} - module '{module}' not accessible to user {user_id}")
                continue
            
            # Apply LinkedRecordType-based filtering for specific user roles
            if not _should_show_event_for_user(user_id, event.LinkedRecordType):
                logger.info(f"[RBAC RISKAVAIRE] Filtering out event {event.EventId} - LinkedRecordType '{event.LinkedRecordType}' not accessible to user {user_id}")
                continue
            
            events_data.append({
                'event_id': event.EventId,
                'event_id_generated': event.EventId_Generated,
                'event_title': event.EventTitle,
                'description': event.Description,
                'linked_record_type': event.LinkedRecordType,
                'linked_record_id': event.LinkedRecordId,
                'linked_record_name': event.LinkedRecordName,
                'category': event.Category,
                'priority': event.Priority,
                'status': event.Status,
                'start_date': event.StartDate,
                'end_date': event.EndDate,
                'created_at': event.CreatedAt,
                'owner': event.Owner.UserName if event.Owner else None,
                'reviewer': event.Reviewer.UserName if event.Reviewer else None,
                'framework': framework,
                'module': module
            })
        
        logger.info(f"[RBAC RISKAVAIRE] Returning {len(events_data)} events for user {user_id}")
        
        response_data = {
            'success': True,
            'events': events_data,
            'total_count': len(events_data)
        }
        
        logger.info(f"[RBAC RISKAVAIRE] Response data: {response_data}")
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting RiskAvaire events: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting events: {str(e)}'
        }, status=500)
