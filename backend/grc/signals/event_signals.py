"""
Signal handlers for automatic event creation based on model changes
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import logging

from ..models import RiskInstance, Compliance, Audit, Incident, Event, Users, Policy, PolicyApproval

logger = logging.getLogger(__name__)

@receiver(post_save, sender=RiskInstance)
def handle_risk_instance_changes(sender, instance, created, **kwargs):
    """
    Automatically create events when risk instances are created or updated
    """
    try:
        from ..routes.EventHandling.riskavaire_integration import RiskAvaireEventTrigger
        
        if created:
            # New risk instance created
            event = RiskAvaireEventTrigger.create_risk_event(instance, "risk_detected")
            if event:
                logger.info(f"Auto-created event for new risk instance {instance.RiskInstanceId}")
        
        else:
            # Risk instance updated - check for status changes
            if hasattr(instance, '_state') and hasattr(instance._state, 'db'):
                # Get the previous state from the database
                try:
                    old_instance = RiskInstance.objects.get(RiskInstanceId=instance.RiskInstanceId)
                    
                    # Check if risk status changed to approved
                    if (old_instance.RiskStatus != instance.RiskStatus and 
                        instance.RiskStatus == 'Approved'):
                        event = RiskAvaireEventTrigger.create_risk_event(instance, "risk_approved")
                        if event:
                            logger.info(f"Auto-created event for approved risk {instance.RiskInstanceId}")
                    
                    # Check if risk status changed to rejected
                    elif (old_instance.RiskStatus != instance.RiskStatus and 
                          instance.RiskStatus == 'Rejected'):
                        event = RiskAvaireEventTrigger.create_risk_event(instance, "risk_rejected")
                        if event:
                            logger.info(f"Auto-created event for rejected risk {instance.RiskInstanceId}")
                    
                    # Check if mitigation status changed to completed
                    elif (old_instance.MitigationStatus != instance.MitigationStatus and 
                          instance.MitigationStatus == 'Completed'):
                        # Create a completion event
                        event_data = {
                            'EventTitle': f"Risk Mitigation Completed: {instance.RiskTitle}",
                            'Description': f"Risk mitigation has been completed for: {instance.RiskDescription}",
                            'LinkedRecordType': 'risk',
                            'LinkedRecordId': instance.RiskInstanceId,
                            'LinkedRecordName': instance.RiskTitle,
                            'Category': 'Risk Management',
                            'Priority': 'Medium',
                            'Status': 'Completed',
                            'StartDate': timezone.now().date(),
                            'EndDate': timezone.now().date(),
                            'RecurrenceType': 'Non-Recurring',
                            'CreatedBy': Users.objects.filter(UserId=instance.UserId).first() if instance.UserId else None,
                            'Owner': Users.objects.filter(UserId=instance.UserId).first() if instance.UserId else None,
                            'Reviewer': Users.objects.filter(UserId=instance.ReviewerId).first() if instance.ReviewerId else None,
                            'IsTemplate': False
                        }
                        event = Event.objects.create(**event_data)
                        logger.info(f"Auto-created completion event for risk {instance.RiskInstanceId}")
                
                except RiskInstance.DoesNotExist:
                    pass  # Instance was deleted or doesn't exist
                    
    except Exception as e:
        logger.error(f"Error in risk instance signal handler: {str(e)}")


@receiver(post_save, sender=Compliance)
def handle_compliance_changes(sender, instance, created, **kwargs):
    """
    Automatically create events when compliance records are created or updated
    """
    try:
        from ..routes.EventHandling.riskavaire_integration import RiskAvaireEventTrigger
        
        if created:
            # New compliance record created
            event = RiskAvaireEventTrigger.create_compliance_event(instance, "compliance_review_required")
            if event:
                logger.info(f"Auto-created event for new compliance {instance.ComplianceId}")
        
        else:
            # Compliance record updated - check for status changes
            try:
                old_instance = Compliance.objects.get(ComplianceId=instance.ComplianceId)
                
                # Check if status changed to approved
                if (old_instance.Status != instance.Status and 
                    instance.Status == 'Approved'):
                    event = RiskAvaireEventTrigger.create_compliance_event(instance, "compliance_approved")
                    if event:
                        logger.info(f"Auto-created event for approved compliance {instance.ComplianceId}")
                
                # Check if status changed to rejected
                elif (old_instance.Status != instance.Status and 
                      instance.Status == 'Rejected'):
                    event = RiskAvaireEventTrigger.create_compliance_event(instance, "compliance_rejected")
                    if event:
                        logger.info(f"Auto-created event for rejected compliance {instance.ComplianceId}")
                        
            except Compliance.DoesNotExist:
                pass
                
    except Exception as e:
        logger.error(f"Error in compliance signal handler: {str(e)}")


@receiver(post_save, sender=Audit)
def handle_audit_changes(sender, instance, created, **kwargs):
    """
    Automatically create events when audit records are created or updated
    """
    try:
        from ..routes.EventHandling.riskavaire_integration import RiskAvaireEventTrigger
        
        if created:
            # New audit record created
            event = RiskAvaireEventTrigger.create_audit_event(instance, "audit_scheduled")
            if event:
                logger.info(f"Auto-created event for new audit {instance.AuditId}")
        
        else:
            # Audit record updated - check for status changes
            try:
                old_instance = Audit.objects.get(AuditId=instance.AuditId)
                
                # Check if status changed to approved
                if (old_instance.Status != instance.Status and 
                    instance.Status == 'Approved'):
                    event = RiskAvaireEventTrigger.create_audit_event(instance, "audit_approved")
                    if event:
                        logger.info(f"Auto-created event for approved audit {instance.AuditId}")
                
                # Check if status changed to rejected
                elif (old_instance.Status != instance.Status and 
                      instance.Status == 'Rejected'):
                    event = RiskAvaireEventTrigger.create_audit_event(instance, "audit_rejected")
                    if event:
                        logger.info(f"Auto-created event for rejected audit {instance.AuditId}")
                        
            except Audit.DoesNotExist:
                pass
                
    except Exception as e:
        logger.error(f"Error in audit signal handler: {str(e)}")


@receiver(post_save, sender=Incident)
def handle_incident_changes(sender, instance, created, **kwargs):
    """
    Automatically create events when incident records are created or updated
    """
    try:
        from ..routes.EventHandling.riskavaire_integration import RiskAvaireEventTrigger
        
        if created:
            # New incident record created
            event = RiskAvaireEventTrigger.create_incident_event(instance, "incident_detected")
            if event:
                logger.info(f"Auto-created event for new incident {instance.IncidentId}")
        
        else:
            # Incident record updated - check for status changes
            try:
                old_instance = Incident.objects.get(IncidentId=instance.IncidentId)
                
                # Check if status changed to resolved
                if (old_instance.Status != instance.Status and 
                    instance.Status == 'Resolved'):
                    event = RiskAvaireEventTrigger.create_incident_event(instance, "incident_resolved")
                    if event:
                        logger.info(f"Auto-created event for resolved incident {instance.IncidentId}")
                
                # Check if severity changed to high/critical (escalation)
                elif (old_instance.Severity != instance.Severity and 
                      instance.Severity in ['High', 'Critical']):
                    event = RiskAvaireEventTrigger.create_incident_event(instance, "incident_escalated")
                    if event:
                        logger.info(f"Auto-created event for escalated incident {instance.IncidentId}")
                        
            except Incident.DoesNotExist:
                pass
                
    except Exception as e:
        logger.error(f"Error in incident signal handler: {str(e)}")


@receiver(post_save, sender=Policy)
def handle_policy_changes(sender, instance, created, **kwargs):
    """
    Automatically create events when policy records are created or updated
    Uses transaction.on_commit to defer event creation until after transaction commits
    This prevents event creation errors from breaking the main transaction
    """
    try:
        from django.db import transaction
        from ..routes.EventHandling.riskavaire_integration import RiskAvaireEventTrigger
        
        if created:
            # New policy created - defer event creation until after transaction commits
            # Capture policy ID to avoid closure issues
            policy_id = instance.PolicyId
            policy_name = instance.PolicyName
            
            def create_event_after_commit():
                try:
                    # Reload policy to ensure we have the latest data
                    from ..models import Policy
                    try:
                        policy = Policy.objects.get(PolicyId=policy_id)
                        event = RiskAvaireEventTrigger.create_policy_event(policy, "policy_approval_needed")
                        if event:
                            logger.info(f"Auto-created event for new policy {policy_id}")
                    except Policy.DoesNotExist:
                        logger.warning(f"Policy {policy_id} not found when creating event after commit")
                except Exception as e:
                    logger.error(f"Error creating event after commit for policy {policy_id}: {str(e)}")
            
            transaction.on_commit(create_event_after_commit)
        
        else:
            # Policy updated - check for status changes
            try:
                old_instance = Policy.objects.get(PolicyId=instance.PolicyId)
                trigger_type = None
                
                # Check if status changed to approved
                if (old_instance.Status != instance.Status and 
                    instance.Status == 'Approved'):
                    trigger_type = "policy_approved"
                
                # Check if status changed to rejected
                elif (old_instance.Status != instance.Status and 
                      instance.Status == 'Rejected'):
                    trigger_type = "policy_rejected"
                
                # Check if status changed to published
                elif (old_instance.Status != instance.Status and 
                      instance.Status == 'Published'):
                    trigger_type = "policy_published"
                
                # Check if status changed to archived
                elif (old_instance.Status != instance.Status and 
                      instance.Status == 'Archived'):
                    trigger_type = "policy_archived"
                
                # Defer event creation until after transaction commits
                if trigger_type:
                    def create_event_after_commit():
                        try:
                            event = RiskAvaireEventTrigger.create_policy_event(instance, trigger_type)
                            if event:
                                logger.info(f"Auto-created event for {trigger_type} policy {instance.PolicyId}")
                        except Exception as e:
                            logger.error(f"Error creating event after commit for policy {instance.PolicyId}: {str(e)}")
                    
                    transaction.on_commit(create_event_after_commit)
                        
            except Policy.DoesNotExist:
                pass
                
    except Exception as e:
        logger.error(f"Error in policy signal handler: {str(e)}")


@receiver(post_save, sender=PolicyApproval)
def handle_policy_approval_changes(sender, instance, created, **kwargs):
    """
    Automatically create events when policy approval records are created or updated
    Uses transaction.on_commit to defer event creation until after transaction commits
    This prevents event creation errors from breaking the main transaction
    """
    try:
        from django.db import transaction
        from ..routes.EventHandling.riskavaire_integration import RiskAvaireEventTrigger
        
        if created:
            # New policy approval created - defer event creation until after transaction commits
            if instance.PolicyId:
                policy_id = instance.PolicyId.PolicyId if hasattr(instance.PolicyId, 'PolicyId') else instance.PolicyId
                approval_id = instance.ApprovalId
                
                def create_event_after_commit():
                    try:
                        # Reload policy to ensure we have the latest data
                        from ..models import Policy
                        try:
                            policy = Policy.objects.get(PolicyId=policy_id)
                            event = RiskAvaireEventTrigger.create_policy_event(policy, "policy_approval_needed")
                            if event:
                                logger.info(f"Auto-created event for new policy approval {approval_id}")
                        except Policy.DoesNotExist:
                            logger.warning(f"Policy {policy_id} not found when creating event after commit")
                    except Exception as e:
                        logger.error(f"Error creating event after commit for policy approval {approval_id}: {str(e)}")
                
                transaction.on_commit(create_event_after_commit)
        
        else:
            # Policy approval updated - check for approval status changes
            if instance.PolicyId and instance.ApprovedNot is not None:
                try:
                    old_instance = PolicyApproval.objects.get(ApprovalId=instance.ApprovalId)
                    trigger_type = None
                    
                    # Check if approval status changed from None to True (approved)
                    if (old_instance.ApprovedNot is None and instance.ApprovedNot is True):
                        trigger_type = "policy_approved"
                    
                    # Check if approval status changed from None to False (rejected)
                    elif (old_instance.ApprovedNot is None and instance.ApprovedNot is False):
                        trigger_type = "policy_rejected"
                    
                    # Defer event creation until after transaction commits
                    if trigger_type:
                        policy_id = instance.PolicyId.PolicyId if hasattr(instance.PolicyId, 'PolicyId') else instance.PolicyId
                        approval_id = instance.ApprovalId
                        
                        def create_event_after_commit():
                            try:
                                # Reload policy to ensure we have the latest data
                                from ..models import Policy
                                try:
                                    policy = Policy.objects.get(PolicyId=policy_id)
                                    event = RiskAvaireEventTrigger.create_policy_event(policy, trigger_type)
                                    if event:
                                        logger.info(f"Auto-created event for {trigger_type} policy {policy_id}")
                                except Policy.DoesNotExist:
                                    logger.warning(f"Policy {policy_id} not found when creating event after commit")
                            except Exception as e:
                                logger.error(f"Error creating event after commit for policy approval {approval_id}: {str(e)}")
                        
                        transaction.on_commit(create_event_after_commit)
                            
                except PolicyApproval.DoesNotExist:
                    pass
                
    except Exception as e:
        logger.error(f"Error in policy approval signal handler: {str(e)}")


# Periodic check for overdue items
def check_overdue_items():
    """
    Function to check for overdue items and create events
    This can be called by a scheduled task or cron job
    """
    try:
        from ..routes.EventHandling.riskavaire_integration import RiskAvaireEventTrigger
        
        current_date = timezone.now().date()
        created_events = []
        
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
                EventTitle__icontains='Mitigation Overdue',
                CreatedAt__gte=current_date - timedelta(days=1)  # Only check recent events
            ).first()
            
            if not existing_event:
                event = RiskAvaireEventTrigger.create_risk_event(risk, "mitigation_overdue")
                if event:
                    created_events.append(event)
                    logger.info(f"Created overdue mitigation event for risk {risk.RiskInstanceId}")
        
        # Check for high-priority risks that need escalation
        high_priority_risks = RiskInstance.objects.filter(
            Criticality__in=['Critical', 'High'],
            RiskStatus='Not Assigned',
            CreatedAt__gte=current_date - timedelta(days=3)  # Only recent risks
        )
        
        for risk in high_priority_risks:
            existing_event = Event.objects.filter(
                LinkedRecordType='risk',
                LinkedRecordId=risk.RiskInstanceId,
                EventTitle__icontains='Escalated',
                CreatedAt__gte=current_date - timedelta(days=1)
            ).first()
            
            if not existing_event:
                event = RiskAvaireEventTrigger.create_risk_event(risk, "risk_escalated")
                if event:
                    created_events.append(event)
                    logger.info(f"Created escalation event for risk {risk.RiskInstanceId}")
        
        logger.info(f"Periodic check completed. Created {len(created_events)} events.")
        return created_events
        
    except Exception as e:
        logger.error(f"Error in periodic overdue check: {str(e)}")
        return []
