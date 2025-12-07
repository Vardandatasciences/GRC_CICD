import os
import json
import requests
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
import logging
import urllib.parse as up

from grc.models import Users, ExternalApplication, ExternalApplicationConnection, ExternalApplicationSyncLog

logger = logging.getLogger(__name__)

class JiraIntegration:
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    def get_accessible_resources(self):
        """Get accessible Jira resources from Atlassian API"""
        try:
            url = "https://api.atlassian.com/oauth/token/accessible-resources"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}: {response.text}"
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def get_current_user(self, cloud_id):
        """Get current user information from Jira"""
        try:
            url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}: {response.text}"
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def get_projects(self, cloud_id):
        """Get all projects from Jira"""
        try:
            url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}: {response.text}"
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def get_project_details(self, cloud_id, project_id):
        """Get detailed project information"""
        try:
            # Get basic project info
            project_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{project_id}"
            project_response = requests.get(project_url, headers=self.headers, timeout=30)
            
            if project_response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Failed to fetch project: {project_response.status_code}"
                }
            
            project_data = project_response.json()
            
            # Get project components
            components_data = []
            try:
                components_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{project_id}/components"
                components_response = requests.get(components_url, headers=self.headers, timeout=30)
                if components_response.status_code == 200:
                    components_data = components_response.json()
            except Exception as e:
                logger.warning(f"Failed to fetch components: {str(e)}")
            
            # Get project versions
            versions_data = []
            try:
                versions_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{project_id}/versions"
                versions_response = requests.get(versions_url, headers=self.headers, timeout=30)
                if versions_response.status_code == 200:
                    versions_data = versions_response.json()
            except Exception as e:
                logger.warning(f"Failed to fetch versions: {str(e)}")
            
            # Get project issues (first 50)
            issues_data = {"issues": [], "total": 0}
            try:
                # Try with project ID first
                issues_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search?jql=project={project_id}&maxResults=50"
                issues_response = requests.get(issues_url, headers=self.headers, timeout=30)
                if issues_response.status_code == 200:
                    issues_data = issues_response.json()
                else:
                    # Try with project key
                    issues_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search?jql=project=\"{project_data.get('key', '')}\"&maxResults=50"
                    issues_response = requests.get(issues_url, headers=self.headers, timeout=30)
                    if issues_response.status_code == 200:
                        issues_data = issues_response.json()
            except Exception as e:
                logger.warning(f"Failed to fetch issues: {str(e)}")
            
            return {
                'success': True,
                'data': {
                    'project': project_data,
                    'components': components_data,
                    'versions': versions_data,
                    'issues': issues_data
                }
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

@csrf_exempt
@require_http_methods(["GET"])
def jira_oauth(request):
    """Handle Jira OAuth initiation - redirects directly to Atlassian"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        # Get OAuth configuration from Django settings
        client_id = getattr(settings, 'JIRA_CLIENT_ID', '')
        redirect_uri = getattr(settings, 'JIRA_REDIRECT_URI', 'http://127.0.0.1:8000/api/jira/oauth-callback/')
        scopes = getattr(settings, 'JIRA_SCOPES', 'read:jira-user read:jira-work')
        use_local_dev = getattr(settings, 'USE_LOCAL_DEVELOPMENT', True)
        
        # Force local redirect URI if in local development mode
        if use_local_dev:
            redirect_uri = 'http://127.0.0.1:8000/api/jira/oauth-callback/'
        else:
            # Ensure production redirect URI is clean (no quotes, no extra whitespace)
            redirect_uri = str(redirect_uri).strip().strip("'\"")
            # Fallback if somehow empty
            if not redirect_uri:
                redirect_uri = 'https://grc-backend.vardaands.com/api/jira/oauth-callback'
        
        # CRITICAL: Strip quotes from all parameters (they might be stored with quotes in env vars)
        def clean_value(value):
            """Remove quotes from anywhere in the string"""
            if not value:
                return ''
            original = str(value)
            value = str(value).strip()
            # Remove quotes from start and end multiple times to handle nested quotes
            while (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1].strip()
            # Also use strip to remove any remaining quotes
            value = value.strip("'\"")
            # Log if we removed quotes
            if original != value:
                logger.info(f"Cleaned value: '{original}' -> '{value}'")
            return value
        
        # Log raw values before cleaning
        logger.info(f"Raw values from settings:")
        logger.info(f"  Raw client_id: {repr(client_id)}")
        logger.info(f"  Raw scopes: {repr(scopes)}")
        logger.info(f"  Raw redirect_uri: {repr(redirect_uri)}")
        
        client_id = clean_value(client_id) if client_id else ''
        scopes = clean_value(scopes) if scopes else 'read:jira-user read:jira-work'
        redirect_uri = clean_value(redirect_uri)
        
        # Log cleaned values
        logger.info(f"Cleaned values:")
        logger.info(f"  Clean client_id: {repr(client_id)}")
        logger.info(f"  Clean scopes: {repr(scopes)}")
        logger.info(f"  Clean redirect_uri: {repr(redirect_uri)}")
        
        logger.info(f"Jira OAuth - USE_LOCAL_DEVELOPMENT: {use_local_dev}, Redirect URI: {redirect_uri}")
        
        # Validate all required parameters
        if not client_id:
            logger.error("Jira OAuth - CLIENT_ID is empty or missing")
            return JsonResponse({
                'success': False,
                'error': 'Jira OAuth not configured - missing CLIENT_ID'
            })
        
        if not redirect_uri:
            logger.error("Jira OAuth - REDIRECT_URI is empty or missing")
            return JsonResponse({
                'success': False,
                'error': 'Jira OAuth not configured - missing REDIRECT_URI'
            })
        
        if not scopes:
            logger.error("Jira OAuth - SCOPES is empty or missing")
            return JsonResponse({
                'success': False,
                'error': 'Jira OAuth not configured - missing SCOPES'
            })
        
        # Store user_id in session for callback
        request.session['jira_user_id'] = user_id
        
        # Generate state parameter for security
        import secrets
        state = secrets.token_urlsafe(24)
        request.session['jira_oauth_state'] = state
        
        # Build Atlassian OAuth URL with correct parameters
        # Ensure all values are clean (no quotes)
        oauth_params = {
            'client_id': clean_value(client_id),
            'scope': clean_value(scopes),
            'response_type': 'code',
            'redirect_uri': clean_value(redirect_uri),
            'state': str(state).strip(),
            'audience': 'api.atlassian.com'
        }
        
        # Validate no empty values
        for key, value in oauth_params.items():
            if not value:
                logger.error(f"Jira OAuth - Parameter '{key}' is empty!")
                return JsonResponse({
                    'success': False,
                    'error': f'OAuth parameter {key} is empty or invalid'
                })
        
        # Log the parameters being sent (without sensitive data)
        logger.info(f"Jira OAuth Parameters:")
        logger.info(f"  client_id: {oauth_params['client_id'][:20]}... (length: {len(oauth_params['client_id'])})")
        logger.info(f"  redirect_uri: {oauth_params['redirect_uri']}")
        logger.info(f"  scope: {oauth_params['scope']}")
        logger.info(f"  state: {oauth_params['state'][:20]}...")
        logger.info(f"  audience: {oauth_params['audience']}")
        
        atlassian_oauth_url = f"https://auth.atlassian.com/authorize?{up.urlencode(oauth_params)}"
        
        logger.info(f"Jira OAuth - Full URL (first 300 chars): {atlassian_oauth_url[:300]}")
        
        # Redirect directly to Atlassian
        return HttpResponseRedirect(atlassian_oauth_url)
        
    except Exception as e:
        logger.error(f"Jira OAuth initiation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'OAuth initiation failed: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def jira_oauth_callback(request):
    """Handle Jira OAuth callback directly from Atlassian"""
    try:
        if request.method == 'GET':
            # Handle OAuth callback from Atlassian
            code = request.GET.get('code')
            state = request.GET.get('state')
            error = request.GET.get('error')
            error_description = request.GET.get('error_description', '')
            
            # Get stored session data
            stored_state = request.session.get('jira_oauth_state')
            user_id = request.session.get('jira_user_id', 1)
            
            # Verify state parameter
            if state != stored_state:
                logger.error("OAuth state mismatch")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/jira?error=state_mismatch"
                return HttpResponseRedirect(error_url)
            
            # Handle OAuth errors
            if error:
                logger.error(f"OAuth error: {error} - {error_description}")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/jira?error={error}"
                return HttpResponseRedirect(error_url)
            
            if not code:
                logger.error("No authorization code received")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/jira?error=no_code"
                return HttpResponseRedirect(error_url)
            
            # Exchange code for access token
            try:
                client_id = getattr(settings, 'JIRA_CLIENT_ID', '')
                client_secret = getattr(settings, 'JIRA_CLIENT_SECRET', '')
                redirect_uri = getattr(settings, 'JIRA_REDIRECT_URI', 'http://127.0.0.1:8000/api/jira/oauth-callback/')
                use_local_dev = getattr(settings, 'USE_LOCAL_DEVELOPMENT', True)
                
                # Force local redirect URI if in local development mode
                if use_local_dev:
                    redirect_uri = 'http://127.0.0.1:8000/api/jira/oauth-callback/'
                else:
                    # Ensure production redirect URI is clean (no quotes, no extra whitespace)
                    redirect_uri = str(redirect_uri).strip().strip("'\"")
                
                logger.info(f"Jira OAuth Callback - USE_LOCAL_DEVELOPMENT: {use_local_dev}, Redirect URI: {redirect_uri}")
                
                if not client_id or not client_secret:
                    logger.error("Jira OAuth credentials not configured")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/jira?error=oauth_not_configured"
                    return HttpResponseRedirect(error_url)
                
                # Exchange code for token
                token_url = "https://auth.atlassian.com/oauth/token"
                token_data = {
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'audience': 'api.atlassian.com'
                }
                
                token_headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
                
                logger.info("Exchanging code for token with Atlassian")
                token_response = requests.post(token_url, data=token_data, headers=token_headers, timeout=30)
                
                if token_response.status_code != 200:
                    logger.error(f"Token exchange failed: {token_response.status_code} {token_response.text}")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/jira?error=token_exchange_failed"
                    return HttpResponseRedirect(error_url)
                
                token_json = token_response.json()
                access_token = token_json.get('access_token')
                
                if not access_token:
                    logger.error("No access token in response")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/jira?error=no_access_token"
                    return HttpResponseRedirect(error_url)
                
                logger.info(f"Access token received: {access_token[:20]}...")
                
                # Fetch accessible resources immediately after successful authentication
                logger.info("Fetching accessible Jira resources...")
                jira_integration = JiraIntegration(access_token)
                resources_result = jira_integration.get_accessible_resources()
                
                resources_data = []
                if resources_result['success']:
                    resources_data = resources_result['data']
                    logger.info(f"Successfully fetched {len(resources_data)} accessible resources")
                else:
                    logger.warning(f"Failed to fetch resources during OAuth: {resources_result['error']}")
                    # Don't fail the OAuth process if resources can't be fetched
                    # They can be fetched later when needed
                
                # Save the access token and connection details
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app, created = ExternalApplication.objects.get_or_create(
                        name='Jira',
                        defaults={
                            'category': 'Project Management',
                            'type': 'Issue Tracking',
                            'description': 'Jira integration for project and issue management',
                            'icon_class': 'fas fa-tasks',
                            'status': 'connected'
                        }
                    )
                    
                    # Update the application status to connected if it was created or already exists
                    if not created:
                        jira_app.status = 'connected'
                        jira_app.save()
                        logger.info("Updated existing Jira application status to 'connected'")
                    else:
                        logger.info("Created new Jira application with 'connected' status")
                    
                    # Prepare projects_data with resources information
                    projects_data = {
                        'access_token': access_token,
                        'connected_at': datetime.now().isoformat(),
                        'resources': resources_data,
                        'last_sync': datetime.now().isoformat(),
                        'sync_status': 'success' if resources_data else 'pending'
                    }
                    
                    connection, created = ExternalApplicationConnection.objects.update_or_create(
                        application=jira_app,
                        user=user,
                        defaults={
                            'connection_token': access_token,
                            'connection_status': 'active',
                            'token_expires_at': datetime.now() + timedelta(days=365),
                            'projects_data': projects_data,
                            'last_used': datetime.now()
                        }
                    )
                    
                    if created:
                        logger.info(f"Created new Jira connection for user {user_id}")
                    else:
                        logger.info(f"Updated existing Jira connection for user {user_id}")
                    
                    # Create sync log
                    ExternalApplicationSyncLog.objects.create(
                        application=jira_app,
                        user=user,
                        sync_type='manual',
                        sync_status='success' if resources_data else 'pending',
                        records_synced=len(resources_data),
                        sync_started_at=datetime.now(),
                        sync_completed_at=datetime.now()
                    )
                    
                    logger.info(f"Successfully saved Jira connection with {len(resources_data)} resources")
                    
                    # Store success flag in session temporarily (token is already saved in DB)
                    request.session['jira_oauth_success'] = True
                    request.session['jira_oauth_user_id'] = user_id
                    
                    # Clear OAuth state data
                    request.session.pop('jira_oauth_state', None)
                    request.session.pop('jira_user_id', None)
                    
                    # Redirect back to frontend without token (to avoid URL length limit)
                    # Frontend will load stored data from database
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    frontend_url = f"{frontend_base}/integration/jira?success=true&user_id={user_id}"
                    
                    logger.info(f"Redirecting to frontend: {frontend_url}")
                    return HttpResponseRedirect(frontend_url)
                    
                except Users.DoesNotExist:
                    logger.error("User not found")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/jira?error=user_not_found"
                    return HttpResponseRedirect(error_url)
                    
            except requests.RequestException as e:
                logger.error(f"Request error during token exchange: {str(e)}")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/jira?error=network_error"
                return HttpResponseRedirect(error_url)
        
        elif request.method == 'POST':
            # Handle POST callback data from frontend
            data = json.loads(request.body)
            access_token = data.get('access_token')
            user_id = data.get('user_id', 1)
            account_info = data.get('account_info', {})
            
            if access_token:
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app, created = ExternalApplication.objects.get_or_create(
                        name='Jira',
                        defaults={
                            'category': 'Project Management',
                            'type': 'Issue Tracking',
                            'description': 'Jira integration for project and issue management',
                            'icon_class': 'fas fa-tasks',
                            'status': 'connected'
                        }
                    )
                    
                    connection, created = ExternalApplicationConnection.objects.update_or_create(
                        application=jira_app,
                        user=user,
                        defaults={
                            'connection_token': access_token,
                            'connection_status': 'active',
                            'token_expires_at': datetime.now() + timedelta(days=365),
                            'projects_data': {
                                'access_token': access_token,
                                'connected_at': datetime.now().isoformat(),
                                'account_info': account_info
                            }
                        }
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Jira connection established successfully',
                        'connection_id': connection.id
                    })
                    
                except Users.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'User not found'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No access token provided'
                })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Jira OAuth callback error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'OAuth callback failed: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def jira_projects(request):
    """Handle Jira projects requests"""
    try:
        if request.method == 'GET':
            # Get stored projects data
            user_id = request.GET.get('user_id', 1)
            
            try:
                user = Users.objects.get(UserId=user_id)
                jira_app = ExternalApplication.objects.get(name='Jira')
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
                
                if connection.projects_data:
                    return JsonResponse({
                        'success': True,
                        'data': connection.projects_data.get('projects', []),
                        'resources': connection.projects_data.get('resources', []),
                        'last_updated': connection.updated_at.isoformat(),
                        'sync_status': connection.projects_data.get('sync_status', 'unknown')
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No stored projects data found'
                    })
                    
            except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': 'Jira connection not found'
                })
        
        elif request.method == 'POST':
            # Fetch fresh projects data from Jira
            data = json.loads(request.body)
            user_id = data.get('user_id', 1)
            access_token = data.get('access_token')
            cloud_id = data.get('cloud_id')
            action = data.get('action', 'fetch_projects')
            
            # If no access token provided, try to get it from stored connection
            if not access_token:
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app = ExternalApplication.objects.get(name='Jira')
                    connection = ExternalApplicationConnection.objects.get(
                        application=jira_app,
                        user=user,
                        connection_status='active'
                    )
                    access_token = connection.connection_token
                    logger.info("Using stored connection token for fetching projects")
                except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                    return JsonResponse({
                        'success': False,
                        'error': 'Access token is required and no stored connection found'
                    })
            
            if not access_token:
                return JsonResponse({
                    'success': False,
                    'error': 'Access token is required'
                })
            
            if not cloud_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Cloud ID is required'
                })
            
            # Initialize Jira integration
            jira_integration = JiraIntegration(access_token)
            
            if action == 'fetch_projects':
                # Fetch projects data
                projects_result = jira_integration.get_projects(cloud_id)
                
                if projects_result['success']:
                    return JsonResponse({
                        'success': True,
                        'data': projects_result['data'],
                        'message': 'Projects data fetched successfully'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': projects_result['error']
                    })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action'
                })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Jira projects endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def jira_project_details(request):
    """Handle Jira project details requests"""
    try:
        if request.method == 'GET':
            # Get stored project details from database
            user_id = request.GET.get('user_id', 1)
            project_id = request.GET.get('project_id')
            
            if not project_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Project ID is required'
                })
            
            try:
                user = Users.objects.get(UserId=user_id)
                jira_app = ExternalApplication.objects.get(name='Jira')
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
                
                # Check if project details are stored
                project_details = connection.projects_data.get('project_details', {})
                if project_id in project_details:
                    return JsonResponse({
                        'success': True,
                        'project_details': project_details[project_id],
                        'last_updated': connection.updated_at.isoformat()
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Project details not found'
                    })
                    
            except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': 'Jira connection not found'
                })
        
        elif request.method == 'POST':
            # Fetch fresh project details from Jira
            data = json.loads(request.body)
            user_id = data.get('user_id', 1)
            project_id = data.get('project_id')
            access_token = data.get('access_token')
            cloud_id = data.get('cloud_id')
            
            if not access_token or not project_id or not cloud_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Access token, project ID, and cloud ID are required'
                })
            
            # Initialize Jira integration
            jira_integration = JiraIntegration(access_token)
            
            # Fetch project details
            details_result = jira_integration.get_project_details(cloud_id, project_id)
            
            if details_result['success']:
                # Save project details to database
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app = ExternalApplication.objects.get(name='Jira')
                    connection = ExternalApplicationConnection.objects.get(
                        application=jira_app,
                        user=user
                    )
                    
                    # Update projects_data with project details
                    projects_data = connection.projects_data or {}
                    project_details = projects_data.get('project_details', {})
                    project_details[project_id] = {
                        'data': details_result['data'],
                        'fetched_at': datetime.now().isoformat()
                    }
                    projects_data['project_details'] = project_details
                    
                    connection.projects_data = projects_data
                    connection.last_used = datetime.now()
                    connection.save()
                    
                    return JsonResponse({
                        'success': True,
                        'data': details_result['data'],
                        'message': 'Project details fetched and saved successfully'
                    })
                    
                except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                    return JsonResponse({
                        'success': False,
                        'error': 'Database error'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': details_result['error']
                })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Jira project details endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET"])
def jira_resources(request):
    """Get Jira accessible resources"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = Users.objects.get(UserId=user_id)
            jira_app = ExternalApplication.objects.get(name='Jira')
            connection = ExternalApplicationConnection.objects.get(
                application=jira_app,
                user=user,
                connection_status='active'
            )
            
            logger.info(f"Jira resources request for user {user_id}, connection {connection.id}")
            logger.info(f"Connection projects_data: {connection.projects_data}")
            
            if connection.projects_data and 'resources' in connection.projects_data:
                resources = connection.projects_data['resources']
                logger.info(f"Found {len(resources)} resources in database")
                
                return JsonResponse({
                    'success': True,
                    'resources': resources,
                    'count': len(resources)
                })
            else:
                # If no resources in database, try to fetch them fresh
                logger.info("No resources in database, attempting to fetch fresh resources")
                
                if connection.connection_token:
                    jira_integration = JiraIntegration(connection.connection_token)
                    resources_result = jira_integration.get_accessible_resources()
                    
                    if resources_result['success']:
                        resources_data = resources_result['data']
                        logger.info(f"Successfully fetched {len(resources_data)} fresh resources")
                        
                        # Update the connection with fresh resources
                        projects_data = connection.projects_data or {}
                        projects_data['resources'] = resources_data
                        projects_data['last_sync'] = datetime.now().isoformat()
                        connection.projects_data = projects_data
                        connection.save()
                        
                        return JsonResponse({
                            'success': True,
                            'resources': resources_data,
                            'count': len(resources_data)
                        })
                    else:
                        logger.error(f"Failed to fetch fresh resources: {resources_result['error']}")
                        return JsonResponse({
                            'success': False,
                            'error': f'Failed to fetch resources: {resources_result["error"]}'
                        })
                else:
                    logger.error("No connection token available")
                    return JsonResponse({
                        'success': False,
                        'error': 'No connection token available'
                    })
                
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
            logger.error(f"Jira connection not found for user {user_id}")
            return JsonResponse({
                'success': False,
                'error': 'Jira connection not found'
            })
    
    except Exception as e:
        logger.error(f"Jira resources endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET"])
def jira_users(request):
    """Get all users for JIRA project assignment"""
    try:
        # Import the JiraBackendManager
        from .jira_backend import JiraBackendManager
        jira_backend = JiraBackendManager()
        
        result = jira_backend.get_all_users()
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error getting JIRA users: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def jira_assign_project(request):
    """Assign a JIRA project to selected users"""
    try:
        # Import the JiraBackendManager
        from .jira_backend import JiraBackendManager
        jira_backend = JiraBackendManager()
        
        data = json.loads(request.body)
        assigned_by_user_id = data.get('assigned_by_user_id')
        project_data = data.get('project_data')
        selected_users = data.get('selected_users')
        
        result = jira_backend.assign_project_to_users(
            assigned_by_user_id, project_data, selected_users
        )
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error assigning JIRA project: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def jira_stored_data(request):
    """Get stored Jira data"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = Users.objects.get(UserId=user_id)
            jira_app = ExternalApplication.objects.get(name='Jira')
            connection = ExternalApplicationConnection.objects.get(
                application=jira_app,
                user=user,
                connection_status='active'
            )
            
            if connection.projects_data:
                projects = connection.projects_data.get('projects', [])
                return JsonResponse({
                    'success': True,
                    'has_data': True,
                    'data': {  # Wrap in 'data' key for frontend
                        'projects': projects,
                        'resources': connection.projects_data.get('resources', []),
                        'project_details': connection.projects_data.get('project_details', {}),
                        'projects_count': len(projects)
                    },
                    'projects_data': connection.projects_data,  # Keep full data for compatibility
                    'resources': connection.projects_data.get('resources', []),
                    'projects': projects,
                    'project_details': connection.projects_data.get('project_details', {}),
                    'last_updated': connection.updated_at.isoformat(),
                    'sync_status': connection.projects_data.get('sync_status', 'unknown')
                })
            else:
                return JsonResponse({
                    'success': True,
                    'has_data': False,
                    'message': 'No stored data found'
                })
                
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
            return JsonResponse({
                'success': True,
                'has_data': False,
                'message': 'No Jira connection found'
            })
    
    except Exception as e:
        logger.error(f"Jira stored data endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })
