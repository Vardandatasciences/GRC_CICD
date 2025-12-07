from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, datetime, timedelta
from grc.models import Framework, Policy, Users
from ...routes.Global.notification_service import NotificationService
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('framework_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Continuously monitors frameworks and policies and updates their status based on StartDate'

    def handle(self, *args, **options):
        logger.info('Starting framework and policy monitoring service...')
        self.stdout.write('Starting framework and policy monitoring service...')
        
        last_check_time = None
        
        try:
            while True:
                start_time = time.time()
                current_date = date.today()
                current_time = datetime.now()
                
                # Log timing information
                if last_check_time:
                    time_since_last_check = (current_time - last_check_time).total_seconds()
                    logger.info(f'Time since last check: {time_since_last_check:.2f} seconds')
                
                logger.info(f'Starting check at: {current_time.strftime("%Y-%m-%d %H:%M:%S")}')
                logger.info(f'Current date for comparison: {current_date}')
                
                # 1. Monitor and update frameworks based on StartDate
                frameworks = Framework.objects.filter(
                    ActiveInactive='Scheduled',
                    Status='Approved',
                    StartDate__lte=current_date
                )
                
                # Update the status of matching frameworks and their policies
                updated_frameworks = 0
                updated_policies_from_framework = 0
                
                for framework in frameworks:
                    # Update framework status
                    framework.ActiveInactive = 'Active'
                    framework.save()
                    updated_frameworks += 1
                    logger.info(f'Updated framework {framework.FrameworkId} ({framework.FrameworkName}) to Active status')
                    
                    # Find and update approved policies for this framework
                    policies = Policy.objects.filter(
                        FrameworkId=framework,
                        Status='Approved',
                        ActiveInactive='Scheduled'
                    )
                    
                    for policy in policies:
                        policy.ActiveInactive = 'Active'
                        policy.save()
                        updated_policies_from_framework += 1
                        logger.info(f'Updated policy {policy.PolicyId} ({policy.PolicyName}) to Active status (from framework activation)')
                
                # 2. Monitor and update policies based on StartDate, but only if their framework is Approved and Active
                policies = Policy.objects.filter(
                    ActiveInactive='Scheduled',
                    Status='Approved',
                    FrameworkId__Status='Approved',
                    FrameworkId__ActiveInactive='Active'
                )
                
                logger.info(f'Found {policies.count()} scheduled, approved policies with approved/active frameworks')
                for p in policies:
                    logger.info(f'Policy {p.PolicyId}: {p.PolicyName}, StartDate={p.StartDate}, FrameworkId={p.FrameworkId_id}, ActiveInactive={p.ActiveInactive}, Status={p.Status}')
                
                updated_policies_from_date = 0
                for policy in policies:
                    # Log policy details for debugging
                    logger.info(f'Checking policy {policy.PolicyId} ({policy.PolicyName}):')
                    logger.info(f'  StartDate: {policy.StartDate}')
                    logger.info(f'  Current date: {current_date}')
                    
                    # Calculate and log the date difference
                    if policy.StartDate:
                        days_difference = (current_date - policy.StartDate).days
                        if days_difference > 0:
                            logger.info(f'  StartDate was {days_difference} days ago')
                        elif days_difference < 0:
                            logger.info(f'  StartDate is {abs(days_difference)} days in the future')
                        else:
                            logger.info('  StartDate is today')
                    
                    logger.info(f'  Parent Framework: {policy.FrameworkId.FrameworkName} (Status: {policy.FrameworkId.Status}, ActiveInactive: {policy.FrameworkId.ActiveInactive})')
                    
                    # Check if StartDate is in the past or today
                    if policy.StartDate and policy.StartDate <= current_date:
                        policy.ActiveInactive = 'Active'
                        policy.save()
                        updated_policies_from_date += 1
                        logger.info(f'Updated policy {policy.PolicyId} ({policy.PolicyName}) to Active status (from StartDate)')
                    else:
                        logger.info(f'Policy {policy.PolicyId} not updated - StartDate not reached')
                
                # 3. Monitor and expire frameworks based on EndDate
                expired_frameworks = Framework.objects.filter(
                    ActiveInactive='Active',
                    Status='Approved',
                    EndDate__isnull=False,
                    EndDate__lte=current_date
                )
                expired_frameworks_count = 0
                expired_policies_from_framework = 0
                for framework in expired_frameworks:
                    framework.ActiveInactive = 'Expired'
                    framework.save()
                    expired_frameworks_count += 1
                    logger.info(f'Expired framework {framework.FrameworkId} ({framework.FrameworkName}) due to EndDate {framework.EndDate}')
                    # Expire all its policies that are Approved and Active
                    fw_policies = Policy.objects.filter(
                        FrameworkId=framework,
                        Status='Approved',
                        ActiveInactive='Active'
                    )
                    for policy in fw_policies:
                        policy.ActiveInactive = 'Expired'
                        policy.save()
                        expired_policies_from_framework += 1
                        logger.info(f'Expired policy {policy.PolicyId} ({policy.PolicyName}) due to parent framework expiration')

                # 4. Monitor and expire policies based on EndDate
                expired_policies = Policy.objects.filter(
                    ActiveInactive='Active',
                    Status='Approved',
                    EndDate__isnull=False,
                    EndDate__lte=current_date
                )
                expired_policies_count = 0
                for policy in expired_policies:
                    policy.ActiveInactive = 'Expired'
                    policy.save()
                    expired_policies_count += 1
                    logger.info(f'Expired policy {policy.PolicyId} ({policy.PolicyName}) due to EndDate {policy.EndDate}')
                
                # Log summary of updates
                total_updates = (
                    updated_frameworks + updated_policies_from_framework + updated_policies_from_date +
                    expired_frameworks_count + expired_policies_from_framework + expired_policies_count
                )
                if total_updates > 0:
                    message = (
                        f'Updated {updated_frameworks} frameworks, '
                        f'{updated_policies_from_framework} policies from framework activation, '
                        f'and {updated_policies_from_date} policies from StartDate. '
                        f'Expired {expired_frameworks_count} frameworks, '
                        f'{expired_policies_from_framework} policies from framework expiration, '
                        f'and {expired_policies_count} policies from EndDate.'
                    )
                    logger.info(message)
                    self.stdout.write(message)
                else:
                    logger.info('No frameworks or policies needed updating or expiring')
                
                # Calculate time to sleep to maintain 1-minute intervals
                elapsed_time = time.time() - start_time
                sleep_time = max(0, 60 - elapsed_time)
                
                # Log timing information
                next_check_time = current_time + timedelta(seconds=sleep_time)
                logger.info(f'Check completed in {elapsed_time:.2f} seconds')
                logger.info(f'Next check scheduled at: {next_check_time.strftime("%Y-%m-%d %H:%M:%S")}')
                logger.info(f'Sleeping for {sleep_time:.2f} seconds')
                
                # Update last check time
                last_check_time = current_time
                
                # Sleep until next check
                time.sleep(sleep_time)
                
                notification_service = NotificationService()
                # Get all users' emails
                all_users = Users.objects.all()
                all_emails = [user.Email for user in all_users if user.Email]

                # Notify for frameworks activating in 3 days (i.e., 3 days before StartDate)
                frameworks_activating = Framework.objects.filter(
                    ActiveInactive='Scheduled',
                    Status='Approved',
                    StartDate=current_date + timedelta(days=3)
                )
                logger.info(f'Frameworks activating in 3 days: {frameworks_activating.count()}')
                logger.info(f'All user emails for notification: {all_emails}')
                for framework in frameworks_activating:
                    for email in all_emails:
                        result = notification_service.send_email(
                            to=email,
                            email_type='gmail',
                            notification_type='frameworkActivate',
                            template_data=[framework.FrameworkName, framework.StartDate.strftime('%Y-%m-%d')]
                        )
                        logger.info(f'Sent framework activation notification for {framework.FrameworkName} to {email}, result: {result}')

                # Notify for frameworks expiring in 3 days
                frameworks_expiring = Framework.objects.filter(
                    ActiveInactive='Active',
                    Status='Approved',
                    EndDate=current_date + timedelta(days=3)
                )
                logger.info(f'Frameworks expiring in 3 days: {frameworks_expiring.count()}')
                for framework in frameworks_expiring:
                    for email in all_emails:
                        result = notification_service.send_email(
                            to=email,
                            email_type='gmail',
                            notification_type='frameworkExpiring',
                            template_data=[framework.FrameworkName, framework.EndDate.strftime('%Y-%m-%d')]
                        )
                        logger.info(f'Sent framework expiring notification for {framework.FrameworkName} to {email}, result: {result}')

                # Notify for policies activating in 3 days
                policies_activating = Policy.objects.filter(
                    ActiveInactive='Scheduled',
                    Status='Approved',
                    StartDate=current_date + timedelta(days=3),
                    FrameworkId__Status='Approved',
                    FrameworkId__ActiveInactive='Active'
                )
                logger.info(f'Policies activating in 3 days: {policies_activating.count()}')
                for policy in policies_activating:
                    for email in all_emails:
                        result = notification_service.send_email(
                            to=email,
                            email_type='gmail',
                            notification_type='policyActivate',
                            template_data=[policy.PolicyName, policy.StartDate.strftime('%Y-%m-%d')]
                        )
                        logger.info(f'Sent policy activation notification for {policy.PolicyName} to {email}, result: {result}')

                # Notify for policies expiring in 3 days
                policies_expiring = Policy.objects.filter(
                    ActiveInactive='Active',
                    Status='Approved',
                    EndDate=current_date + timedelta(days=3),
                    FrameworkId__Status='Approved',
                    FrameworkId__ActiveInactive='Active'
                )
                logger.info(f'Policies expiring in 3 days: {policies_expiring.count()}')
                for policy in policies_expiring:
                    for email in all_emails:
                        result = notification_service.send_email(
                            to=email,
                            email_type='gmail',
                            notification_type='policyExpiring',
                            template_data=[policy.PolicyName, policy.EndDate.strftime('%Y-%m-%d')]
                        )
                        logger.info(f'Sent policy expiring notification for {policy.PolicyName} to {email}, result: {result}')
                
        except KeyboardInterrupt:
            logger.info('Framework and policy monitoring service stopped by user.')
            self.stdout.write('Framework and policy monitoring service stopped.')
        except Exception as e:
            logger.error(f'Error in monitoring: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 