"""
Streamline Backend Integration
Handles user-specific project assignments and streamlined project views
"""
import json
import logging
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ...models import (
    Users,
    UsersProjectList,
    IntegrationDataList
)
from ...authentication import get_user_from_jwt

logger = logging.getLogger(__name__)


class StreamlineManager:
    """
    Manager class for handling streamlined project views
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_user_assigned_projects(self, user_id):
        """
        Get all projects assigned to a specific user
        
        Args:
            user_id (int): User ID to get projects for
            
        Returns:
            dict: List of projects assigned to the user
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Find all project assignments where the user is in the users_list
            project_assignments = UsersProjectList.objects.filter(
                is_active=True,
                users_list__contains=[user_id]  # Check if user_id is in the JSON array
            ).order_by('-created_at')
            
            projects = []
            for assignment in project_assignments:
                # Get assigned users details
                assigned_users = assignment.get_assigned_users()
                assigned_users_details = []
                
                for assigned_user in assigned_users:
                    assigned_users_details.append({
                        'id': assigned_user.UserId,
                        'username': assigned_user.UserName,
                        'email': assigned_user.Email,
                        'full_name': assigned_user.get_full_name()
                    })
                
                # Check if current user is assigned to this project
                is_user_assigned = assignment.is_user_assigned(user_id)
                
                if is_user_assigned:
                    projects.append({
                        'id': assignment.id,
                        'project_id': assignment.project_id,
                        'project_name': assignment.project_name,
                        'project_key': assignment.project_key,
                        'project_details': assignment.project_details,
                        'assigned_users': assigned_users_details,
                        'assigned_users_count': assignment.get_assigned_users_count(),
                        'list_type': assignment.list_type,
                        'assigned_by': {
                            'id': assignment.assigned_by.UserId,
                            'username': assignment.assigned_by.UserName,
                            'full_name': assignment.assigned_by.get_full_name()
                        },
                        'created_at': assignment.created_at.isoformat(),
                        'updated_at': assignment.updated_at.isoformat(),
                        'is_current_user_assigned': True
                    })
            
            self.logger.info(f"Found {len(projects)} projects assigned to user {user_id}")
            
            return {
                'success': True,
                'projects': projects,
                'count': len(projects),
                'user_info': {
                    'id': user.UserId,
                    'username': user.UserName,
                    'email': user.Email,
                    'full_name': user.get_full_name()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user assigned projects: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_project_details_for_user(self, user_id, project_id):
        """
        Get detailed project information for a specific user and project
        
        Args:
            user_id (int): User ID
            project_id (str): Project ID
            
        Returns:
            dict: Detailed project information
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Find the project assignment
            try:
                assignment = UsersProjectList.objects.get(
                    project_id=project_id,
                    is_active=True,
                    users_list__contains=[user_id]
                )
            except UsersProjectList.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Project {project_id} not found or user not assigned to it'
                }
            
            # Get assigned users details
            assigned_users = assignment.get_assigned_users()
            assigned_users_details = []
            
            for assigned_user in assigned_users:
                assigned_users_details.append({
                    'id': assigned_user.UserId,
                    'username': assigned_user.UserName,
                    'email': assigned_user.Email,
                    'full_name': assigned_user.get_full_name()
                })
            
            project_details = {
                'id': assignment.id,
                'project_id': assignment.project_id,
                'project_name': assignment.project_name,
                'project_key': assignment.project_key,
                'project_details': assignment.project_details,
                'assigned_users': assigned_users_details,
                'assigned_users_count': assignment.get_assigned_users_count(),
                'list_type': assignment.list_type,
                'assigned_by': {
                    'id': assignment.assigned_by.UserId,
                    'username': assignment.assigned_by.UserName,
                    'full_name': assignment.assigned_by.get_full_name()
                },
                'created_at': assignment.created_at.isoformat(),
                'updated_at': assignment.updated_at.isoformat(),
                'is_current_user_assigned': True
            }
            
            self.logger.info(f"Retrieved project details for user {user_id}, project {project_id}")
            
            return {
                'success': True,
                'project': project_details
            }
            
        except Exception as e:
            self.logger.error(f"Error getting project details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_project_statistics(self, user_id):
        """
        Get statistics about user's project assignments
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: Project statistics for the user
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Get all project assignments for the user
            project_assignments = UsersProjectList.objects.filter(
                is_active=True,
                users_list__contains=[user_id]
            )
            
            # Calculate statistics
            total_projects = project_assignments.count()
            single_user_projects = project_assignments.filter(list_type='single').count()
            multiple_user_projects = project_assignments.filter(list_type='multiple').count()
            
            # Get recent projects (last 30 days)
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recent_projects = project_assignments.filter(created_at__gte=thirty_days_ago).count()
            
            # Get projects by platform (assuming all are Jira for now)
            jira_projects = project_assignments.count()  # All current projects are from Jira
            
            statistics = {
                'total_projects': total_projects,
                'single_user_projects': single_user_projects,
                'multiple_user_projects': multiple_user_projects,
                'recent_projects': recent_projects,
                'platforms': {
                    'jira': jira_projects
                },
                'user_info': {
                    'id': user.UserId,
                    'username': user.UserName,
                    'email': user.Email,
                    'full_name': user.get_full_name()
                }
            }
            
            self.logger.info(f"Retrieved statistics for user {user_id}: {total_projects} total projects")
            
            return {
                'success': True,
                'statistics': statistics
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user project statistics: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_task_action(self, user_id, task_data, action_type, project_data=None, platform='jira'):
        """
        Save task action performed by user to IntegrationDataList
        
        Args:
            user_id (int): User ID who performed the action
            task_data (dict): Task information
            action_type (str): Type of action performed
            project_data (dict): Optional project information
            platform (str): Platform source (jira, gmail, sentinel, bamboohr, etc.)
            
        Returns:
            dict: Result of the save operation
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Validate and normalize platform
            valid_platforms = ['jira', 'gmail', 'sentinel', 'bamboohr', 'streamline']
            platform_lower = platform.lower() if platform else 'jira'
            
            if platform_lower not in valid_platforms:
                self.logger.warning(f"Unknown platform '{platform}', using as-is")
            
            # Prepare heading for the action
            task_name = task_data.get('summary') or task_data.get('title') or 'Untitled Task'
            task_id = task_data.get('id') or task_data.get('task_id')
            
            # Check for duplicate action (same user, task, action_type within last 5 minutes)
            five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
            
            duplicate_check = IntegrationDataList.objects.filter(
                source=platform_lower,
                username=user.UserName,
                metadata__task_id=str(task_id),
                data__action_type=action_type,
                created_at__gte=five_minutes_ago
            ).first()
            
            if duplicate_check:
                self.logger.info(
                    f"Duplicate action detected for user {user_id}: "
                    f"Task '{task_name}', Action '{action_type}' already recorded at {duplicate_check.created_at}"
                )
                return {
                    'success': True,
                    'already_added': True,
                    'message': 'This action was already recorded recently',
                    'record_id': duplicate_check.id,
                    'action_type': action_type,
                    'task_name': task_name,
                    'platform': platform_lower,
                    'previous_timestamp': duplicate_check.created_at.isoformat(),
                    'timestamp': timezone.now().isoformat()
                }
            
            heading = f"{platform_lower.upper()} - {action_type} - {task_name}"
            
            # Prepare full data payload
            data_payload = {
                'task': task_data,
                'action_type': action_type,
                'platform': platform_lower,
                'user': {
                    'id': user.UserId,
                    'username': user.UserName,
                    'email': user.Email,
                    'full_name': user.get_full_name()
                }
            }
            
            # Add project data if provided
            if project_data:
                data_payload['project'] = project_data
            
            # Prepare metadata
            metadata = {
                'task_id': str(task_id) if task_id else None,
                'task_status': task_data.get('status'),
                'task_priority': task_data.get('priority', {}).get('name') if isinstance(task_data.get('priority'), dict) else task_data.get('priority'),
                'action_timestamp': timezone.now().isoformat(),
                'platform': platform_lower,
                'project_key': project_data.get('project_key') if project_data else None
            }
            
            # Create IntegrationDataList entry with platform as source
            integration_record = IntegrationDataList.objects.create(
                heading=heading,
                source=platform_lower,  # Store platform name in source
                username=user.UserName,
                time=timezone.now(),
                data=data_payload,
                metadata=metadata
            )
            
            self.logger.info(
                f"Saved task action for user {user_id} on platform '{platform_lower}': "
                f"Task '{task_name}', Action '{action_type}', Record ID: {integration_record.id}"
            )
            
            return {
                'success': True,
                'already_added': False,
                'message': 'Task action saved successfully',
                'record_id': integration_record.id,
                'action_type': action_type,
                'task_name': task_name,
                'platform': platform_lower,
                'timestamp': integration_record.created_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error saving task action: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_task_actions(self, user_id, limit=50, platform=None):
        """
        Get task actions performed by a specific user
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of records to return
            platform (str): Optional filter by platform (jira, gmail, sentinel, bamboohr)
            
        Returns:
            dict: List of task actions
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Build query - filter by user
            query_filter = {
                'username': user.UserName
            }
            
            # Add platform filter if specified
            if platform:
                platform_lower = platform.lower()
                query_filter['source'] = platform_lower
            else:
                # Get all platform sources (not 'streamline_task_action' anymore)
                valid_platforms = ['jira', 'gmail', 'sentinel', 'bamboohr', 'streamline']
                # Filter by any of the valid platforms
                pass  # Will use username filter only
            
            # Query IntegrationDataList for user's task actions
            actions = IntegrationDataList.objects.filter(
                **query_filter
            ).order_by('-created_at')[:limit]
            
            actions_list = []
            for action in actions:
                actions_list.append({
                    'id': action.id,
                    'heading': action.heading,
                    'source': action.source,
                    'platform': action.metadata.get('platform') if action.metadata else action.source,
                    'action_type': action.data.get('action_type') if action.data else None,
                    'task': action.data.get('task') if action.data else None,
                    'project': action.data.get('project') if action.data else None,
                    'metadata': action.metadata,
                    'timestamp': action.created_at.isoformat(),
                    'time': action.time.isoformat()
                })
            
            self.logger.info(f"Retrieved {len(actions_list)} task actions for user {user_id}" + 
                           (f" on platform '{platform}'" if platform else ""))
            
            return {
                'success': True,
                'actions': actions_list,
                'count': len(actions_list),
                'platform_filter': platform if platform else 'all',
                'user_info': {
                    'id': user.UserId,
                    'username': user.UserName,
                    'full_name': user.get_full_name()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user task actions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
streamline_manager = StreamlineManager()


# API Views
@csrf_exempt
@require_http_methods(["GET"])
def get_user_projects(request):
    """
    Get all projects assigned to the current user
    """
    try:
        # Get user_id from query parameter or from authenticated user
        user_id = request.GET.get('user_id')
        
        # If no user_id in query, try to get from authenticated user
        if not user_id:
            # Try to get user from JWT token
            user = get_user_from_jwt(request)
            if user:
                user_id = user.UserId
                logger.info(f"Using authenticated user ID from JWT: {user_id}")
            elif hasattr(request, 'user') and request.user:
                user_id = request.user.UserId
                logger.info(f"Using authenticated user ID from request: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id parameter is required or user must be authenticated'}, status=400)
        
        result = streamline_manager.get_user_assigned_projects(user_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in get_user_projects: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_project_details(request):
    """
    Get detailed project information for a specific project
    """
    try:
        # Get user_id from query parameter or from authenticated user
        user_id = request.GET.get('user_id')
        project_id = request.GET.get('project_id')
        
        # If no user_id in query, try to get from authenticated user
        if not user_id and hasattr(request, 'user') and request.user:
            user_id = request.user.UserId
            logger.info(f"Using authenticated user ID: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id parameter is required or user must be authenticated'}, status=400)
        
        if not project_id:
            return JsonResponse({'error': 'project_id parameter is required'}, status=400)
        
        result = streamline_manager.get_project_details_for_user(user_id, project_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in get_project_details: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_user_statistics(request):
    """
    Get project statistics for the current user
    """
    try:
        # Get user_id from query parameter or from authenticated user
        user_id = request.GET.get('user_id')
        
        # If no user_id in query, try to get from authenticated user
        if not user_id:
            # Try to get user from JWT token
            user = get_user_from_jwt(request)
            if user:
                user_id = user.UserId
                logger.info(f"Using authenticated user ID from JWT: {user_id}")
            elif hasattr(request, 'user') and request.user:
                user_id = request.user.UserId
                logger.info(f"Using authenticated user ID from request: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id parameter is required or user must be authenticated'}, status=400)
        
        result = streamline_manager.get_user_project_statistics(user_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in get_user_statistics: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_task_action(request):
    """
    Save a task action performed by a user
    
    Expected JSON payload:
    {
        "user_id": 1,
        "task": {
            "id": 123,
            "summary": "Task name",
            "status": "In Progress",
            "assignee": {...},
            "priority": {...}
        },
        "action_type": "Task Viewed|Task Started|Task Completed|etc",
        "project": {
            "project_id": "10001",
            "project_name": "Project Name",
            "project_key": "PROJ"
        },
        "platform": "jira|gmail|sentinel|bamboohr"
    }
    """
    try:
        # Parse JSON body
        try:
            body = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        
        # Get user_id from payload or from authenticated user
        user_id = body.get('user_id')
        
        # If no user_id in payload, try to get from authenticated user
        if not user_id:
            # Try to get user from JWT token
            user = get_user_from_jwt(request)
            if user:
                user_id = user.UserId
                logger.info(f"Using authenticated user ID from JWT: {user_id}")
            elif hasattr(request, 'user') and request.user:
                user_id = request.user.UserId
                logger.info(f"Using authenticated user ID from request: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id is required or user must be authenticated'}, status=400)
        
        # Get task data
        task_data = body.get('task')
        if not task_data:
            return JsonResponse({'error': 'task data is required'}, status=400)
        
        # Get action type (default to "Task Action")
        action_type = body.get('action_type', 'Task Action')
        
        # Get project data (optional)
        project_data = body.get('project')
        
        # Get platform (default to 'jira')
        platform = body.get('platform', 'jira')
        
        # Save the task action
        result = streamline_manager.save_task_action(
            user_id=user_id,
            task_data=task_data,
            action_type=action_type,
            project_data=project_data,
            platform=platform
        )
        
        if result['success']:
            # Return 200 for duplicate, 201 for new record
            status_code = 200 if result.get('already_added') else 201
            return JsonResponse(result, status=status_code)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in save_task_action: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_user_task_actions(request):
    """
    Get all task actions performed by a user
    Query parameters:
    - user_id: User ID (optional if authenticated)
    - limit: Maximum number of records (default: 50)
    - platform: Filter by platform (jira, gmail, sentinel, bamboohr) - optional
    """
    try:
        # Get user_id from query parameter or from authenticated user
        user_id = request.GET.get('user_id')
        
        # If no user_id in query, try to get from authenticated user
        if not user_id:
            # Try to get user from JWT token
            user = get_user_from_jwt(request)
            if user:
                user_id = user.UserId
                logger.info(f"Using authenticated user ID from JWT: {user_id}")
            elif hasattr(request, 'user') and request.user:
                user_id = request.user.UserId
                logger.info(f"Using authenticated user ID from request: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id parameter is required or user must be authenticated'}, status=400)
        
        # Get limit parameter (default to 50)
        limit = int(request.GET.get('limit', 50))
        
        # Get platform parameter (optional)
        platform = request.GET.get('platform')
        
        result = streamline_manager.get_user_task_actions(user_id, limit, platform)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in get_user_task_actions: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
