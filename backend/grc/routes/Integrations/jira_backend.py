"""
Jira Backend Integration
Handles saving Jira account and project information to the database
"""
import json
import logging
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from ...models import (
    ExternalApplication, 
    ExternalApplicationConnection, 
    ExternalApplicationSyncLog, 
    Users,
    UsersProjectList
)

logger = logging.getLogger(__name__)


class JiraBackendManager:
    """
    Manages Jira integration backend operations
    """
    
    def __init__(self):
        self.jira_app_name = 'Jira'
    
    def get_or_create_jira_application(self):
        """
        Get or create the Jira external application record
        """
        try:
            jira_app, created = ExternalApplication.objects.get_or_create(
                name=self.jira_app_name,
                defaults={
                    'category': 'Project Management',
                    'type': 'Issue Tracking',
                    'description': 'Atlassian Jira - Issue and project tracking tool',
                    'icon_class': 'fab fa-jira',
                    'version': 'v1.0.0',
                    'status': 'disconnected',
                    'is_active': True,
                    'features': [
                        'Project Management',
                        'Issue Tracking',
                        'Workflow Management',
                        'Reporting',
                        'Integration APIs'
                    ],
                    'api_endpoint': 'https://api.atlassian.com/ex/jira/',
                    'oauth_url': 'https://auth.atlassian.com/authorize'
                }
            )
            
            if created:
                logger.info(f"Created new Jira application record: {jira_app.id}")
            else:
                logger.info(f"Found existing Jira application record: {jira_app.id}")
                
            return {
                'success': True,
                'application': jira_app
            }
            
        except Exception as e:
            logger.error(f"Error getting/creating Jira application: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_jira_connection(self, user_id, access_token, refresh_token=None, token_expires_at=None, jira_account_info=None):
        """
        Save Jira connection information for a user
        
        Args:
            user_id (int): User ID
            access_token (str): Jira access token
            refresh_token (str): Jira refresh token (optional)
            token_expires_at (datetime): Token expiration time (optional)
            jira_account_info (dict): Jira account information (optional)
        """
        try:
            with transaction.atomic():
                # Get or create Jira application
                app_result = self.get_or_create_jira_application()
                if not app_result['success']:
                    return app_result
                jira_app = app_result['application']
                
                # Get user
                try:
                    user = Users.objects.get(UserId=user_id)
                except Users.DoesNotExist:
                    logger.error(f"User with ID {user_id} not found")
                    return {
                        'success': False,
                        'error': f'User with ID {user_id} not found'
                    }
                
                # Create or update connection
                connection, created = ExternalApplicationConnection.objects.update_or_create(
                    application=jira_app,
                    user=user,
                    defaults={
                        'connection_token': access_token,
                        'refresh_token': refresh_token,
                        'token_expires_at': token_expires_at,
                        'connection_status': 'active',
                        'last_used': timezone.now()
                    }
                )
                
                # Update application status to connected
                jira_app.status = 'connected'
                jira_app.last_sync = timezone.now()
                
                # Store Jira account info in configuration if provided
                if jira_account_info:
                    jira_app.configuration = {
                        'account_info': jira_account_info,
                        'connected_at': timezone.now().isoformat(),
                        'last_updated': timezone.now().isoformat()
                    }
                
                jira_app.save()
                
                # Log the connection
                ExternalApplicationSyncLog.objects.create(
                    application=jira_app,
                    user=user,
                    sync_type='manual',
                    sync_status='success',
                    records_synced=1,
                    sync_started_at=timezone.now(),
                    sync_completed_at=timezone.now()
                )
                
                logger.info(f"Successfully saved Jira connection for user {user_id}")
                
                return {
                    'success': True,
                    'message': 'Jira connection saved successfully',
                    'connection_id': connection.id,
                    'created': created
                }
                
        except Exception as e:
            logger.error(f"Error saving Jira connection: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_jira_projects(self, user_id, projects_data, project_details_data=None):
        """
        Save Jira projects information for a user
        
        Args:
            user_id (int): User ID
            projects_data (list): List of Jira projects data
            project_details_data (dict): Optional project details data to save
        """
        try:
            with transaction.atomic():
                # Get Jira application
                app_result = self.get_or_create_jira_application()
                if not app_result['success']:
                    return app_result
                jira_app = app_result['application']
                
                # Get user
                try:
                    user = Users.objects.get(UserId=user_id)
                except Users.DoesNotExist:
                    logger.error(f"User with ID {user_id} not found")
                    return {
                        'success': False,
                        'error': f'User with ID {user_id} not found'
                    }
                
                # Get or create connection
                connection, created = ExternalApplicationConnection.objects.get_or_create(
                    application=jira_app,
                    user=user,
                    defaults={
                        'connection_status': 'active',
                        'last_used': timezone.now()
                    }
                )
                
                # Update connection with projects data
                if not connection.connection_token:
                    connection.connection_token = f'jira_projects_sync_{user_id}_{int(timezone.now().timestamp())}'
                
                # Prepare projects data structure
                projects_data_structure = {
                    'projects': projects_data,
                    'last_updated': timezone.now().isoformat(),
                    'projects_count': len(projects_data)
                }
                
                # Add project details if provided
                if project_details_data:
                    projects_data_structure['project_details'] = project_details_data
                    logger.info(f"Also saving {len(project_details_data)} project details")
                
                # Store projects data in the connection's projects_data field
                connection.projects_data = projects_data_structure
                connection.last_used = timezone.now()
                connection.save()
                
                # Store projects data in application configuration
                current_config = jira_app.configuration or {}
                current_config.update({
                    'projects_data': projects_data,
                    'projects_count': len(projects_data),
                    'projects_synced_at': timezone.now().isoformat(),
                    'last_updated': timezone.now().isoformat()
                })
                
                # Add project details to config if provided
                if project_details_data:
                    current_config['project_details'] = project_details_data
                
                jira_app.configuration = current_config
                jira_app.last_sync = timezone.now()
                jira_app.save()
                
                # Log the sync
                ExternalApplicationSyncLog.objects.create(
                    application=jira_app,
                    user=user,
                    sync_type='manual',
                    sync_status='success',
                    records_synced=len(projects_data),
                    sync_started_at=timezone.now(),
                    sync_completed_at=timezone.now()
                )
                
                logger.info(f"Successfully saved {len(projects_data)} Jira projects for user {user_id}")
                
                return {
                    'success': True,
                    'message': f'Saved {len(projects_data)} Jira projects',
                    'projects_count': len(projects_data)
                }
                
        except Exception as e:
            logger.error(f"Error saving Jira projects: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_jira_project_details(self, user_id, project_id, project_details):
        """
        Save detailed Jira project information
        
        Args:
            user_id (int): User ID
            project_id (str): Jira project ID
            project_details (dict): Detailed project information
        """
        try:
            with transaction.atomic():
                # Get Jira application
                app_result = self.get_or_create_jira_application()
                if not app_result['success']:
                    return app_result
                jira_app = app_result['application']
                
                # Get user
                try:
                    user = Users.objects.get(UserId=user_id)
                except Users.DoesNotExist:
                    logger.error(f"User with ID {user_id} not found")
                    return {
                        'success': False,
                        'error': f'User with ID {user_id} not found'
                    }
                
                # Get or create connection
                connection, created = ExternalApplicationConnection.objects.get_or_create(
                    application=jira_app,
                    user=user,
                    defaults={
                        'connection_status': 'active',
                        'last_used': timezone.now()
                    }
                )
                
                # Update projects_data in connection
                current_projects_data = connection.projects_data or {}
                
                # Initialize project_details if not exists
                if 'project_details' not in current_projects_data:
                    current_projects_data['project_details'] = {}
                
                # Store the specific project details
                current_projects_data['project_details'][project_id] = {
                    'data': project_details,
                    'synced_at': timezone.now().isoformat()
                }
                
                current_projects_data['last_updated'] = timezone.now().isoformat()
                connection.projects_data = current_projects_data
                connection.last_used = timezone.now()
                connection.save()
                
                # Store project details in application configuration (for backward compatibility)
                current_config = jira_app.configuration or {}
                
                # Initialize project_details if not exists
                if 'project_details' not in current_config:
                    current_config['project_details'] = {}
                
                # Store the specific project details
                current_config['project_details'][project_id] = {
                    'data': project_details,
                    'synced_at': timezone.now().isoformat()
                }
                
                current_config['last_updated'] = timezone.now().isoformat()
                
                jira_app.configuration = current_config
                jira_app.last_sync = timezone.now()
                jira_app.save()
                
                # Log the sync
                ExternalApplicationSyncLog.objects.create(
                    application=jira_app,
                    user=user,
                    sync_type='manual',
                    sync_status='success',
                    records_synced=1,
                    sync_started_at=timezone.now(),
                    sync_completed_at=timezone.now()
                )
                
                logger.info(f"Successfully saved Jira project details for project {project_id}, user {user_id}")
                
                return {
                    'success': True,
                    'message': f'Saved project details for {project_id}',
                    'project_id': project_id
                }
                
        except Exception as e:
            logger.error(f"Error saving Jira project details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def disconnect_jira(self, user_id):
        """
        Disconnect Jira for a user
        
        Args:
            user_id (int): User ID
        """
        try:
            with transaction.atomic():
                # Get Jira application
                try:
                    jira_app = ExternalApplication.objects.get(name=self.jira_app_name)
                except ExternalApplication.DoesNotExist:
                    logger.warning(f"Jira application not found")
                    return {
                        'success': False,
                        'error': 'Jira application not found'
                    }
                
                # Get user
                try:
                    user = Users.objects.get(UserId=user_id)
                except Users.DoesNotExist:
                    logger.error(f"User with ID {user_id} not found")
                    return {
                        'success': False,
                        'error': f'User with ID {user_id} not found'
                    }
                
                # Get connection
                try:
                    connection = ExternalApplicationConnection.objects.get(
                        application=jira_app,
                        user=user,
                        connection_status='active'
                    )
                except ExternalApplicationConnection.DoesNotExist:
                    logger.warning(f"No active Jira connection found for user {user_id}")
                    return {
                        'success': False,
                        'error': 'No active Jira connection found'
                    }
                
                # Update connection status to revoked
                connection.connection_status = 'revoked'
                connection.save()
                
                # Check if there are any other active connections
                active_connections = ExternalApplicationConnection.objects.filter(
                    application=jira_app,
                    connection_status='active'
                ).count()
                
                # If no active connections, update application status
                if active_connections == 0:
                    jira_app.status = 'disconnected'
                    jira_app.save()
                
                # Log the disconnection
                ExternalApplicationSyncLog.objects.create(
                    application=jira_app,
                    user=user,
                    sync_type='manual',
                    sync_status='success',
                    records_synced=0,
                    sync_started_at=timezone.now(),
                    sync_completed_at=timezone.now(),
                    error_message='User disconnected'
                )
                
                logger.info(f"Successfully disconnected Jira for user {user_id}")
                
                return {
                    'success': True,
                    'message': 'Jira disconnected successfully'
                }
                
        except Exception as e:
            logger.error(f"Error disconnecting Jira: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_jira_connection_status(self, user_id):
        """
        Get Jira connection status for a user
        
        Args:
            user_id (int): User ID
        """
        try:
            # Get Jira application
            try:
                jira_app = ExternalApplication.objects.get(name=self.jira_app_name)
            except ExternalApplication.DoesNotExist:
                return {
                    'success': False,
                    'connected': False,
                    'error': 'Jira application not found'
                }
            
            # Get user
            try:
                user = Users.objects.get(UserId=user_id)
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'connected': False,
                    'error': f'User with ID {user_id} not found'
                }
            
            # Check for active connection
            try:
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
                
                return {
                    'success': True,
                    'connected': True,
                    'connection_id': connection.id,
                    'last_used': connection.last_used,
                    'token_expires_at': connection.token_expires_at,
                    'is_token_expired': connection.is_token_expired()
                }
                
            except ExternalApplicationConnection.DoesNotExist:
                return {
                    'success': True,
                    'connected': False,
                    'message': 'No active Jira connection found'
                }
                
        except Exception as e:
            logger.error(f"Error getting Jira connection status: {str(e)}")
            return {
                'success': False,
                'connected': False,
                'error': str(e)
            }
    
    def get_jira_data(self, user_id):
        """
        Get all Jira data for a user (projects, configuration, etc.)
        
        Args:
            user_id (int): User ID
        """
        try:
            # Get Jira application
            try:
                jira_app = ExternalApplication.objects.get(name=self.jira_app_name)
            except ExternalApplication.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Jira application not found'
                }
            
            # Get user
            try:
                user = Users.objects.get(UserId=user_id)
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found'
                }
            
            # Get connection
            try:
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
            except ExternalApplicationConnection.DoesNotExist:
                return {
                    'success': False,
                    'error': 'No active Jira connection found'
                }
            
            # Get configuration data
            config = jira_app.configuration or {}
            
            return {
                'success': True,
                'application': {
                    'id': jira_app.id,
                    'name': jira_app.name,
                    'status': jira_app.status,
                    'last_sync': jira_app.last_sync,
                    'configuration': config
                },
                'connection': {
                    'id': connection.id,
                    'status': connection.connection_status,
                    'last_used': connection.last_used,
                    'token_expires_at': connection.token_expires_at
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting Jira data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_stored_projects_data(self, user_id):
        """
        Retrieves stored projects data from the database for a user.
        """
        try:
            app_result = self.get_or_create_jira_application()
            if not app_result['success']:
                return app_result
            jira_app = app_result['application']

            try:
                user = Users.objects.get(UserId=user_id)
            except Users.DoesNotExist:
                return {'success': False, 'error': f"User with ID {user_id} not found"}

            try:
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
                
                projects_data = connection.projects_data or {}
                
                return {
                    'success': True,
                    'projects_data': projects_data,
                    'has_data': bool(projects_data.get('projects') or projects_data.get('project_details')),
                    'last_updated': projects_data.get('last_updated'),
                    'projects_count': projects_data.get('projects_count', 0)
                }
            except ExternalApplicationConnection.DoesNotExist:
                return {
                    'success': True,
                    'projects_data': {},
                    'has_data': False,
                    'last_updated': None,
                    'projects_count': 0
                }
        except Exception as e:
            logger.error(f"Error getting stored projects data for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_jira_project_details(self, user_id, project_id):
        """
        Get detailed project information from stored data
        
        Args:
            user_id (int): User ID
            project_id (str): Jira project ID
        """
        try:
            app_result = self.get_or_create_jira_application()
            if not app_result['success']:
                return app_result
            jira_app = app_result['application']

            try:
                user = Users.objects.get(UserId=user_id)
            except Users.DoesNotExist:
                return {'success': False, 'error': f"User with ID {user_id} not found"}

            try:
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
                
                projects_data = connection.projects_data or {}
                project_details = projects_data.get('project_details', {})
                
                # Look for the specific project details
                if project_id in project_details:
                    return {
                        'success': True,
                        'project_details': project_details[project_id],
                        'project_id': project_id
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Project details not found for project ID: {project_id}'
                    }
                    
            except ExternalApplicationConnection.DoesNotExist:
                return {
                    'success': False,
                    'error': 'No active Jira connection found for user'
                }
        except Exception as e:
            logger.error(f"Error getting project details for user {user_id}, project {project_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_all_users(self):
        """
        Get all active users from the database
        
        Returns:
            dict: List of users with their details
        """
        try:
            users = Users.objects.filter(IsActive='Y').order_by('UserName')
            users_list = []
            
            for user in users:
                users_list.append({
                    'id': user.UserId,
                    'username': user.UserName,
                    'email': user.Email,
                    'first_name': user.FirstName,
                    'last_name': user.LastName,
                    'full_name': user.get_full_name(),
                    'department_id': user.DepartmentId
                })
            
            return {
                'success': True,
                'users': users_list,
                'count': len(users_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def assign_project_to_users(self, assigned_by_user_id, project_data, selected_users):
        """
        Assign a Jira project to selected users
        
        Args:
            assigned_by_user_id (int): User ID who is assigning the project
            project_data (dict): Project data from Jira
            selected_users (list): List of user IDs to assign to the project
            
        Returns:
            dict: Success status and details
        """
        try:
            with transaction.atomic():
                # Get the user who is assigning
                try:
                    assigned_by_user = Users.objects.get(UserId=assigned_by_user_id)
                except Users.DoesNotExist:
                    return {
                        'success': False,
                        'error': f'User with ID {assigned_by_user_id} not found'
                    }
                
                # Validate selected users
                if not selected_users:
                    return {
                        'success': False,
                        'error': 'No users selected for assignment'
                    }
                
                # Check if all selected users exist
                existing_users = Users.objects.filter(UserId__in=selected_users, IsActive='Y')
                if len(existing_users) != len(selected_users):
                    return {
                        'success': False,
                        'error': 'One or more selected users do not exist or are inactive'
                    }
                
                # Extract project information
                project_id = str(project_data.get('id', ''))
                project_name = project_data.get('name', '')
                project_key = project_data.get('key', '')
                
                if not project_id or not project_name:
                    return {
                        'success': False,
                        'error': 'Invalid project data provided'
                    }
                
                # Determine list type
                list_type = 'single' if len(selected_users) == 1 else 'multiple'
                
                # Create or update the project assignment
                project_assignment, created = UsersProjectList.objects.get_or_create(
                    project_id=project_id,
                    assigned_by=assigned_by_user,
                    defaults={
                        'project_name': project_name,
                        'project_key': project_key,
                        'project_details': project_data,
                        'users_list': selected_users,
                        'list_type': list_type,
                        'is_active': True
                    }
                )
                
                if not created:
                    # Update existing assignment
                    project_assignment.project_name = project_name
                    project_assignment.project_key = project_key
                    project_assignment.project_details = project_data
                    project_assignment.users_list = selected_users
                    project_assignment.list_type = list_type
                    project_assignment.is_active = True
                    project_assignment.save()
                
                # Get assigned users details for response
                assigned_users_details = []
                for user in existing_users:
                    assigned_users_details.append({
                        'id': user.UserId,
                        'username': user.UserName,
                        'email': user.Email,
                        'full_name': user.get_full_name()
                    })
                
                logger.info(f"Successfully assigned project {project_name} to {len(selected_users)} users")
                
                return {
                    'success': True,
                    'message': f'Project {project_name} assigned to {len(selected_users)} user(s)',
                    'project_assignment_id': project_assignment.id,
                    'project_name': project_name,
                    'project_key': project_key,
                    'assigned_users': assigned_users_details,
                    'list_type': list_type,
                    'created': created
                }
                
        except Exception as e:
            logger.error(f"Error assigning project to users: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_project_assignments(self, user_id=None, project_id=None):
        """
        Get project assignments
        
        Args:
            user_id (int, optional): Filter by user ID
            project_id (str, optional): Filter by project ID
            
        Returns:
            dict: List of project assignments
        """
        try:
            queryset = UsersProjectList.objects.filter(is_active=True)
            
            if user_id:
                queryset = queryset.filter(assigned_by__UserId=user_id)
            
            if project_id:
                queryset = queryset.filter(project_id=project_id)
            
            assignments = []
            for assignment in queryset.order_by('-created_at'):
                assigned_users = assignment.get_assigned_users()
                assigned_users_details = []
                
                for user in assigned_users:
                    assigned_users_details.append({
                        'id': user.UserId,
                        'username': user.UserName,
                        'email': user.Email,
                        'full_name': user.get_full_name()
                    })
                
                assignments.append({
                    'id': assignment.id,
                    'project_id': assignment.project_id,
                    'project_name': assignment.project_name,
                    'project_key': assignment.project_key,
                    'assigned_users': assigned_users_details,
                    'assigned_users_count': assignment.get_assigned_users_count(),
                    'list_type': assignment.list_type,
                    'assigned_by': {
                        'id': assignment.assigned_by.UserId,
                        'username': assignment.assigned_by.UserName,
                        'full_name': assignment.assigned_by.get_full_name()
                    },
                    'created_at': assignment.created_at.isoformat(),
                    'updated_at': assignment.updated_at.isoformat()
                })
            
            return {
                'success': True,
                'assignments': assignments,
                'count': len(assignments)
            }
            
        except Exception as e:
            logger.error(f"Error getting project assignments: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
jira_backend = JiraBackendManager()
