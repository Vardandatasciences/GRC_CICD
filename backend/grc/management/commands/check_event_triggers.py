"""
Management command to check for automated event triggers
This can be run periodically via cron job or scheduled task
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from grc.signals.event_signals import check_overdue_items

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check for automated event triggers and create events for overdue items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating events',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No events will be created')
            )
        
        try:
            self.stdout.write('Checking for automated event triggers...')
            
            if not dry_run:
                created_events = check_overdue_items()
                
                if created_events:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created {len(created_events)} events:'
                        )
                    )
                    for event in created_events:
                        self.stdout.write(f'  - {event.EventId_Generated}: {event.EventTitle}')
                else:
                    self.stdout.write(
                        self.style.SUCCESS('No new events needed to be created')
                    )
            else:
                # In dry run mode, just show what would be checked
                from grc.models import RiskInstance, Compliance, Audit, Incident
                from django.db.models import Q
                
                current_date = timezone.now().date()
                
                # Count overdue risks
                overdue_risks = RiskInstance.objects.filter(
                    MitigationDueDate__lt=current_date,
                    MitigationStatus__in=['Yet to Start', 'Work In Progress'],
                    RiskStatus='Approved'
                ).count()
                
                # Count high priority risks
                high_priority_risks = RiskInstance.objects.filter(
                    Criticality__in=['Critical', 'High'],
                    RiskStatus='Not Assigned',
                    CreatedAt__gte=current_date - timedelta(days=3)
                ).count()
                
                # Count compliance items needing review
                compliance_review_needed = Compliance.objects.filter(
                    Status='Under Review',
                    CreatedByDate__lte=current_date - timedelta(days=90)
                ).count()
                
                self.stdout.write(f'Overdue risk mitigations: {overdue_risks}')
                self.stdout.write(f'High priority risks needing escalation: {high_priority_risks}')
                self.stdout.write(f'Compliance items needing review: {compliance_review_needed}')
                
                total_potential_events = overdue_risks + high_priority_risks + compliance_review_needed
                self.stdout.write(
                    self.style.SUCCESS(f'Total potential events to create: {total_potential_events}')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking event triggers: {str(e)}')
            )
            logger.error(f'Error in check_event_triggers command: {str(e)}')
            raise
