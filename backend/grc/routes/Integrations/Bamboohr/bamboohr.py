import os
import json
import requests
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
import logging

from grc.models import Users, ExternalApplication, ExternalApplicationConnection, ExternalApplicationSyncLog, OAuthState, Framework, Department, Entity
from django.utils import timezone

logger = logging.getLogger(__name__)

class BambooHRIntegration:
    def __init__(self, subdomain, access_token):
        # Clean and validate subdomain
        self.subdomain = subdomain.strip().lower()
        # Remove any invalid characters that might cause URL issues
        import re
        self.subdomain = re.sub(r'[^a-z0-9\-]', '', self.subdomain)
        
        if not self.subdomain:
            raise ValueError("Invalid subdomain provided")
            
        self.access_token = access_token
        self.api_base = f"https://{self.subdomain}.bamboohr.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        
        logger.info(f"BambooHR Integration initialized with subdomain: {self.subdomain}")
        logger.info(f"API Base URL: {self.api_base}")

    def get_employee_directory(self):
        """Fetch employee directory from BambooHR"""
        try:
            url = f"{self.api_base}/employees/directory"
            logger.info(f"Making request to: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            logger.info(f"Response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"API error response: {response.text}")
            
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
            logger.error(f"Request failed for URL {url}: {str(e)}")
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def get_current_user(self):
        """Get current user information"""
        try:
            # First try to get users metadata
            users_url = f"{self.api_base}/meta/users"
            users_response = requests.get(users_url, headers=self.headers, timeout=30)
            
            if users_response.status_code == 200:
                users_data = users_response.json()
                users = users_data.get("users", [])
                current_user = next((u for u in users if u.get("self")), None)
                
                if current_user:
                    employee_id = current_user["employeeId"]
                    
                    # Get detailed employee information
                    fields = [
                        "id", "displayName", "firstName", "lastName", "jobTitle", "department",
                        "division", "location", "workEmail", "mobilePhone", "workPhone", "hireDate",
                        "supervisor", "supervisorId", "status"
                    ]
                    
                    emp_url = f"{self.api_base}/employees/{employee_id}"
                    emp_response = requests.get(
                        emp_url,
                        params={"fields": ",".join(fields)},
                        headers=self.headers,
                        timeout=30
                    )
                    
                    if emp_response.status_code == 200:
                        profile = emp_response.json()
                        return {
                            'success': True,
                            'data': {
                                'user_meta': current_user,
                                'employee_profile': profile
                            }
                        }
            
            return {
                'success': False,
                'error': "Could not fetch current user information"
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def get_all_employees(self):
        """Get all employees with detailed information"""
        try:
            # Get basic employee directory first
            directory_result = self.get_employee_directory()
            if not directory_result['success']:
                return directory_result
            
            directory = directory_result['data']
            employees = directory.get('employees', [])
            
            # Process and enhance employee data
            processed_employees = []
            departments = {}
            total_employees = len(employees)
            active_employees = 0
            recent_hires = 0
            
            # Calculate date for recent hires (last 90 days)
            ninety_days_ago = datetime.now() - timedelta(days=90)
            
            for emp in employees:
                # Count active employees
                if emp.get('status', '').lower() != 'inactive':
                    active_employees += 1
                
                # Count recent hires
                hire_date_str = emp.get('hireDate')
                if hire_date_str:
                    try:
                        hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d')
                        if hire_date > ninety_days_ago:
                            recent_hires += 1
                    except ValueError:
                        pass
                
                # Process departments
                dept_name = emp.get('department', 'Unknown')
                if dept_name not in departments:
                    departments[dept_name] = {
                        'name': dept_name,
                        'employeeCount': 0,
                        'manager': None
                    }
                departments[dept_name]['employeeCount'] += 1
                
                # If this employee is a supervisor, they might be a department manager
                if emp.get('supervisor') is None and emp.get('jobTitle'):
                    title = emp.get('jobTitle', '').lower()
                    if any(word in title for word in ['manager', 'director', 'head', 'lead']):
                        departments[dept_name]['manager'] = emp.get('displayName') or f"{emp.get('firstName', '')} {emp.get('lastName', '')}"
                
                processed_employees.append(emp)
            
            # Convert departments dict to list
            departments_list = list(departments.values())
            
            return {
                'success': True,
                'data': {
                    'employees': processed_employees,
                    'departments': departments_list,
                    'totalEmployees': total_employees,
                    'activeEmployees': active_employees,
                    'recentHires': recent_hires,
                    'lastUpdated': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error processing employee data: {str(e)}"
            }

@csrf_exempt
@require_http_methods(["GET", "POST"])
def bamboohr_employees(request):
    """Handle BambooHR employee data requests"""
    try:
        if request.method == 'GET':
            # Get stored employee data
            user_id = request.GET.get('user_id', 1)
            
            try:
                user = Users.objects.get(UserId=user_id)
                bamboohr_app = ExternalApplication.objects.get(name='BambooHR')
                connection = ExternalApplicationConnection.objects.get(
                    application=bamboohr_app,
                    user=user,
                    connection_status='active'
                )
                
                if connection.projects_data:
                    return JsonResponse({
                        'success': True,
                        'data': connection.projects_data.get('employees', {}),
                        'current_user': connection.projects_data.get('current_user'),
                        'company_info': connection.projects_data.get('company_info', {}),
                        'last_updated': connection.updated_at.isoformat(),
                        'sync_status': connection.projects_data.get('sync_status', 'unknown'),
                        'total_employees': connection.projects_data.get('employees', {}).get('totalEmployees', 0)
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No stored employee data found'
                    })
                    
            except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': 'BambooHR connection not found'
                })
        
        elif request.method == 'POST':
            # Fetch fresh employee data from BambooHR
            data = json.loads(request.body)
            user_id = data.get('user_id', 1)
            access_token = data.get('access_token')
            action = data.get('action', 'fetch_employees')
            
            if not access_token:
                return JsonResponse({
                    'success': False,
                    'error': 'Access token is required'
                })
            
            # Get connection details from database
            try:
                user = Users.objects.get(UserId=user_id)
                bamboohr_app = ExternalApplication.objects.get(name='BambooHR')
                connection = ExternalApplicationConnection.objects.get(
                    application=bamboohr_app,
                    user=user,
                    connection_status='active'
                )
                
                # Get subdomain and API key from stored connection data
                projects_data = connection.projects_data or {}
                logger.info(f"Projects data keys: {list(projects_data.keys()) if isinstance(projects_data, dict) else 'Not a dict'}")
                logger.info(f"Full projects_data: {projects_data}")
                
                subdomain = projects_data.get('subdomain', 'demo')  # fallback for demo
                api_key = connection.connection_token or access_token
                
                logger.info(f"Retrieved subdomain from database: '{subdomain}'")
                
            except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                # For demo purposes, use mock data
                subdomain = 'demo'
                api_key = access_token
                logger.warning("Using demo subdomain as fallback")
            
            # Validate subdomain before creating integration
            if not subdomain or subdomain == 'demo':
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid subdomain - please reconnect to BambooHR'
                })
            
            # Initialize BambooHR integration
            try:
                bamboo_integration = BambooHRIntegration(subdomain, api_key)
            except ValueError as e:
                logger.error(f"Invalid subdomain '{subdomain}': {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid subdomain: {str(e)}'
                })
            
            if action == 'fetch_employees':
                # Fetch all employee data
                employees_result = bamboo_integration.get_all_employees()
                
                if employees_result['success']:
                    # Also get current user data
                    current_user_result = bamboo_integration.get_current_user()
                    current_user = current_user_result.get('data') if current_user_result['success'] else None
                    
                    data_structure = employees_result['data']
                    logger.info(f"Fetched employee data - Keys: {list(data_structure.keys())}")
                    logger.info(f"Total employees: {data_structure.get('totalEmployees', 0)}")
                    logger.info(f"Has employees array: {'employees' in data_structure}")
                    if 'employees' in data_structure:
                        logger.info(f"Number of employees in array: {len(data_structure.get('employees', []))}")
                    
                    return JsonResponse({
                        'success': True,
                        'data': data_structure,
                        'current_user': current_user,
                        'message': 'Employee data fetched successfully'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': employees_result['error']
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
        logger.error(f"BambooHR employees endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def bamboohr_stored_data(request):
    """Handle BambooHR stored data requests"""
    try:
        if request.method == 'GET':
            user_id = request.GET.get('user_id', 1)
            
            try:
                user = Users.objects.get(UserId=user_id)
                bamboohr_app = ExternalApplication.objects.get(name='BambooHR')
                connection = ExternalApplicationConnection.objects.get(
                    application=bamboohr_app,
                    user=user,
                    connection_status='active'
                )
                
                if connection.projects_data:
                    # Parse the employee data correctly from the JSON structure
                    employees_data = connection.projects_data.get('employees', {})
                    employees_list = employees_data.get('employees', []) if isinstance(employees_data, dict) else []
                    
                    # Count employees from the actual array
                    total_employees = len(employees_list) if isinstance(employees_list, list) else 0
                    
                    logger.info(f"Retrieved stored data - Total employees: {total_employees}")
                    logger.info(f"Employees data keys: {list(employees_data.keys()) if isinstance(employees_data, dict) else 'Not a dict'}")
                    logger.info(f"Projects data keys: {list(connection.projects_data.keys())}")
                    
                    return JsonResponse({
                        'success': True,
                        'data': {  # Wrap in 'data' key for frontend
                            'employees': employees_list,  # Return array of employees
                            'departments': employees_data.get('departments', []) if isinstance(employees_data, dict) else [],
                            'total_employees': total_employees,
                            'has_data': True
                        },
                        'has_data': True,
                        'projects_data': connection.projects_data,  # Return full projects_data
                        'added_users': connection.projects_data.get('added_users', []),  # Return list of added user IDs
                        'employee_data': employees_data,  # Keep original structure for compatibility
                        'current_user': connection.projects_data.get('current_user'),
                        'company_info': connection.projects_data.get('company_info', {}),
                        'connection_config': {
                            'subdomain': connection.projects_data.get('subdomain', ''),
                            'connected_at': connection.projects_data.get('connected_at', ''),
                            'last_sync': connection.projects_data.get('last_sync', ''),
                            'sync_status': connection.projects_data.get('sync_status', 'unknown')
                        },
                        'last_updated': connection.updated_at.isoformat(),
                        'total_employees': total_employees,
                        'departments_count': len(employees_data.get('departments', [])) if isinstance(employees_data, dict) else 0
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
                    'message': 'No BambooHR connection found'
                })
        
        elif request.method == 'POST':
            # Handle connection or data storage
            data = json.loads(request.body)
            user_id = data.get('user_id', 1)
            action = data.get('action', 'connect')
            
            if action == 'connect':
                subdomain = data.get('subdomain')
                api_key = data.get('api_key')
                
                if not subdomain or not api_key:
                    return JsonResponse({
                        'success': False,
                        'error': 'Subdomain and API key are required'
                    })
                
                # Test the connection
                bamboo_integration = BambooHRIntegration(subdomain, api_key)
                test_result = bamboo_integration.get_employee_directory()
                
                if test_result['success']:
                    # Save connection to database
                    try:
                        user = Users.objects.get(UserId=user_id)
                        bamboohr_app, created = ExternalApplication.objects.get_or_create(
                            name='BambooHR',
                            defaults={
                                'category': 'HR Management',
                                'type': 'Human Resources',
                                'description': 'BambooHR integration for employee data management',
                                'icon_class': 'fas fa-users',
                                'status': 'connected'
                            }
                        )
                        
                        connection, created = ExternalApplicationConnection.objects.update_or_create(
                            application=bamboohr_app,
                            user=user,
                            defaults={
                                'connection_token': api_key,
                                'connection_status': 'active',
                                'token_expires_at': datetime.now() + timedelta(days=365),
                                'projects_data': {
                                    'subdomain': subdomain,
                                    'company_info': {'name': subdomain}
                                }
                            }
                        )
                        
                        return JsonResponse({
                            'success': True,
                            'message': 'Connected to BambooHR successfully'
                        })
                        
                    except Users.DoesNotExist:
                        return JsonResponse({
                            'success': False,
                            'error': 'User not found'
                        })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f'Connection test failed: {test_result["error"]}'
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
        logger.error(f"BambooHR stored data endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def bamboohr_sync_data(request):
    """Sync and save BambooHR employee data to database"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id', 1)
        employee_data = data.get('employee_data', {})
        current_user = data.get('current_user')
        access_token = data.get('access_token', '')
        
        try:
            user = Users.objects.get(UserId=user_id)
            bamboohr_app = ExternalApplication.objects.get(name='BambooHR')
            
            # Update connection with employee data
            connection = ExternalApplicationConnection.objects.get(
                application=bamboohr_app,
                user=user
            )
            
            # Update projects_data with employee information
            projects_data = connection.projects_data or {}
            
            # IMPORTANT: Preserve existing keys (especially 'subdomain') when updating
            projects_data.update({
                'employees': employee_data,
                'last_sync': datetime.now().isoformat()
            })
            
            logger.info(f"Syncing data - Projects data keys after update: {list(projects_data.keys())}")
            logger.info(f"Syncing data - Subdomain preserved: {projects_data.get('subdomain', 'NOT FOUND')}")
            
            connection.projects_data = projects_data
            connection.last_used = datetime.now()
            connection.save()
            
            # Create sync log
            ExternalApplicationSyncLog.objects.create(
                application=bamboohr_app,
                user=user,
                sync_type='manual',
                sync_status='success',
                records_synced=employee_data.get('totalEmployees', 0),
                sync_started_at=datetime.now(),
                sync_completed_at=datetime.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Employee data synced successfully',
                'records_synced': employee_data.get('totalEmployees', 0)
            })
            
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist) as e:
            return JsonResponse({
                'success': False,
                'error': f'Database error: {str(e)}'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"BambooHR sync data endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET"])
def bamboohr_departments(request):
    """Get BambooHR departments data"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = Users.objects.get(UserId=user_id)
            bamboohr_app = ExternalApplication.objects.get(name='BambooHR')
            connection = ExternalApplicationConnection.objects.get(
                application=bamboohr_app,
                user=user,
                connection_status='active'
            )
            
            if connection.projects_data and 'employees' in connection.projects_data:
                employee_data = connection.projects_data['employees']
                departments = employee_data.get('departments', [])
                
                return JsonResponse({
                    'success': True,
                    'departments': departments,
                    'count': len(departments)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No department data found'
                })
                
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'BambooHR connection not found'
            })
    
    except Exception as e:
        logger.error(f"BambooHR departments endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET"])
def bamboohr_oauth(request):
    """Handle BambooHR OAuth initiation - redirects directly to BambooHR"""
    try:
        user_id = request.GET.get('user_id', 1)
        subdomain_raw = request.GET.get('subdomain', '').strip()
        
        logger.info(f"BambooHR OAuth - Received subdomain from request: '{subdomain_raw}'")
        
        # Clean function to remove quotes (same as Jira)
        def clean_value(value):
            """Remove quotes from anywhere in the string"""
            if not value:
                return ''
            original = str(value)
            value = str(value).strip()
            while (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1].strip()
            value = value.strip("'\"")
            if original != value:
                logger.info(f"Cleaned value: '{original}' -> '{value}'")
            return value
        
        # Get OAuth configuration from Django settings first
        client_id = getattr(settings, 'BAMBOOHR_CLIENT_ID', '')
        redirect_uri = getattr(settings, 'BAMBOOHR_REDIRECT_URI', 'http://127.0.0.1:8000/api/bamboohr/oauth-callback/')
        scopes = getattr(settings, 'BAMBOOHR_SCOPES', 'email openid employee company:info employee:contact employee:job employee:name employee:photo employee_directory')
        use_local_dev = getattr(settings, 'USE_LOCAL_DEVELOPMENT', True)
        
        # Clean all configuration values
        client_id = clean_value(client_id) if client_id else ''
        scopes = clean_value(scopes) if scopes else 'email openid employee company:info employee:contact employee:job employee:name employee:photo employee_directory'
        
        # Validate and clean subdomain BEFORE storing in database
        subdomain = subdomain_raw.strip().lower() if subdomain_raw else ''
        # Remove any invalid characters (only allow alphanumeric and hyphens)
        import re
        subdomain = re.sub(r'[^a-z0-9\-]', '', subdomain)
        
        logger.info(f"BambooHR OAuth - Cleaned subdomain: '{subdomain}' (from '{subdomain_raw}')")
        
        if not subdomain or subdomain in ['www', '']:
            logger.error(f"BambooHR OAuth - Invalid subdomain: '{subdomain}' (original: '{subdomain_raw}')")
            return JsonResponse({
                'success': False,
                'error': f'Invalid subdomain: "{subdomain_raw}". Please enter your company subdomain (e.g., "acme" for acme.bamboohr.com)'
            })
        
        # Generate state parameter for security
        import secrets
        state = secrets.token_urlsafe(24)
        
        # Store state in database (not session) to persist across OAuth redirect
        expires_at = timezone.now() + timedelta(minutes=10)  # State expires in 10 minutes
        oauth_state = OAuthState.objects.create(
            state=state,
            user_id=user_id,
            subdomain=subdomain,  # Store cleaned subdomain
            provider='bamboohr',
            expires_at=expires_at
        )
        
        logger.info(f"Stored OAuth state in database: {state[:10]}...")
        logger.info(f"State record ID: {oauth_state.id}, Subdomain: {subdomain}, User ID: {user_id}")
        
        # Force local redirect URI if in local development mode
        if use_local_dev:
            redirect_uri = 'http://127.0.0.1:8000/api/bamboohr/oauth-callback/'
        else:
            redirect_uri = clean_value(redirect_uri)
            if not redirect_uri:
                redirect_uri = 'https://grc-backend.vardaands.com/api/bamboohr/oauth-callback/'
        
        logger.info(f"BambooHR OAuth - USE_LOCAL_DEVELOPMENT: {use_local_dev}, Redirect URI: {redirect_uri}")
        logger.info(f"BambooHR OAuth - Client ID: {client_id[:10]}... (length: {len(client_id)})")
        logger.info(f"BambooHR OAuth - Subdomain: {subdomain}")
        
        if not client_id:
            return JsonResponse({
                'success': False,
                'error': 'BambooHR OAuth not configured - missing CLIENT_ID'
            })
        
        # Build BambooHR OAuth URL
        import urllib.parse as up
        # Ensure scopes is a string (space-separated)
        scope_string = scopes if isinstance(scopes, str) else ' '.join(scopes) if isinstance(scopes, list) else str(scopes)
        
        # Clean all parameters before building URL
        oauth_params = {
            'request': 'authorize',
            'response_type': 'code',
            'client_id': clean_value(client_id),
            'redirect_uri': clean_value(redirect_uri),
            'scope': clean_value(scope_string),
            'state': str(state).strip()
        }
        
        # Build the OAuth URL (subdomain already validated above)
        bamboohr_oauth_url = f"https://{subdomain}.bamboohr.com/authorize.php?{up.urlencode(oauth_params)}"
        
        # Log full URL for debugging
        logger.info(f"🔗 BambooHR OAuth URL being generated:")
        logger.info(f"   Subdomain: {subdomain}")
        logger.info(f"   Client ID: {client_id[:20]}... (length: {len(client_id)})")
        logger.info(f"   Redirect URI: {redirect_uri}")
        logger.info(f"   Scopes: {scope_string}")
        logger.info(f"   Full URL: {bamboohr_oauth_url[:300]}...")
        logger.info(f"   Note: If you see login page, you may need to log into BambooHR first")
        
        # Redirect directly to BambooHR
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(bamboohr_oauth_url)
        
    except Exception as e:
        logger.error(f"BambooHR OAuth initiation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'OAuth initiation failed: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def bamboohr_oauth_callback(request):
    """Handle BambooHR OAuth callback directly from BambooHR"""
    try:
        if request.method == 'GET':
            # Handle OAuth callback from BambooHR
            code = request.GET.get('code')
            state = request.GET.get('state')
            error = request.GET.get('error')
            error_description = request.GET.get('error_description', '')
            
            # Get stored state from database (not session)
            try:
                oauth_state = OAuthState.objects.get(state=state)
                
                # Check if expired
                if oauth_state.is_expired():
                    logger.error(f"OAuth state has expired: {state}")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/bamboohr?error=state_expired"
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect(error_url)
                
                # Get user info from stored state
                user_id = oauth_state.user_id
                subdomain = oauth_state.subdomain
                
                logger.info(f"Callback received - State from request: {state}")
                logger.info(f"State found in database - Subdomain: {subdomain}, User ID: {user_id}")
                
            except OAuthState.DoesNotExist:
                logger.error(f"OAuth state not found in database: {state}")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/bamboohr?error=state_not_found"
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(error_url)
            
            # Check if this is a local development environment
            # Use Django settings for consistency
            use_local_dev = getattr(settings, 'USE_LOCAL_DEVELOPMENT', True)
            is_local = use_local_dev or '127.0.0.1' in request.get_host() or 'localhost' in request.get_host()
            
            # Verify state parameter
            if state != oauth_state.state:
                logger.error(f"OAuth state mismatch - Expected: {oauth_state.state}, Got: {state}")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/bamboohr?error=state_mismatch"
                
                if is_local and '/oauth/callback' in request.path:
                    return JsonResponse({
                        'success': False,
                        'error': 'OAuth state mismatch',
                        'redirect_url': error_url
                    })
                else:
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect(error_url)
            
            # Handle OAuth errors
            if error:
                logger.error(f"OAuth error: {error} - {error_description}")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/bamboohr?error={error}"
                
                if is_local and '/oauth/callback' in request.path:
                    return JsonResponse({
                        'success': False,
                        'error': f"OAuth error: {error} - {error_description}",
                        'redirect_url': error_url
                    })
                else:
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect(error_url)
            
            if not code:
                logger.error("No authorization code received")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/bamboohr?error=no_code"
                
                if is_local and '/oauth/callback' in request.path:
                    return JsonResponse({
                        'success': False,
                        'error': 'No authorization code received',
                        'redirect_url': error_url
                    })
                else:
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect(error_url)
            
            if not subdomain:
                logger.error("No subdomain in session")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/bamboohr?error=session_expired"
                
                if is_local and '/oauth/callback' in request.path:
                    return JsonResponse({
                        'success': False,
                        'error': 'No subdomain in session',
                        'redirect_url': error_url
                    })
                else:
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect(error_url)
            
            # Exchange code for access token
            try:
                client_id = getattr(settings, 'BAMBOOHR_CLIENT_ID', '')
                client_secret = getattr(settings, 'BAMBOOHR_CLIENT_SECRET', '')
                redirect_uri = getattr(settings, 'BAMBOOHR_REDIRECT_URI', 'http://127.0.0.1:8000/api/bamboohr/oauth-callback/')
                use_local_dev = getattr(settings, 'USE_LOCAL_DEVELOPMENT', True)
                
                # Force local redirect URI if in local development mode
                if use_local_dev:
                    redirect_uri = 'http://127.0.0.1:8000/api/bamboohr/oauth-callback/'
                
                # Log the redirect URI being used
                logger.info(f"BambooHR OAuth Callback - USE_LOCAL_DEVELOPMENT: {use_local_dev}, Redirect URI: {redirect_uri}")
                
                if not client_id or not client_secret:
                    logger.error("BambooHR OAuth credentials not configured")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/bamboohr?error=oauth_not_configured"
                    
                    if is_local and '/oauth/callback' in request.path:
                        return JsonResponse({
                            'success': False,
                            'error': "BambooHR OAuth credentials not configured",
                            'redirect_url': error_url
                        })
                    else:
                        from django.http import HttpResponseRedirect
                        return HttpResponseRedirect(error_url)
                
                # Exchange code for token
                token_url = f"https://{subdomain}.bamboohr.com/token.php?request=token"
                token_data = {
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                    'client_id': client_id,
                    'client_secret': client_secret
                }
                
                token_headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
                
                logger.info(f"Exchanging code for token with {subdomain}.bamboohr.com")
                token_response = requests.post(token_url, data=token_data, headers=token_headers, timeout=30)
                
                if token_response.status_code != 200:
                    logger.error(f"Token exchange failed: {token_response.status_code} {token_response.text}")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/bamboohr?error=token_exchange_failed"
                    
                    if is_local and '/oauth/callback' in request.path:
                        return JsonResponse({
                            'success': False,
                            'error': f"Token exchange failed: {token_response.status_code} {token_response.text}",
                            'redirect_url': error_url
                        })
                    else:
                        from django.http import HttpResponseRedirect
                        return HttpResponseRedirect(error_url)
                
                token_json = token_response.json()
                access_token = token_json.get('access_token')
                
                if not access_token:
                    logger.error("No access token in response")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/bamboohr?error=no_access_token"
                    
                    if is_local and '/oauth/callback' in request.path:
                        return JsonResponse({
                            'success': False,
                            'error': "No access token in response",
                            'redirect_url': error_url
                        })
                    else:
                        from django.http import HttpResponseRedirect
                        return HttpResponseRedirect(error_url)
                
                logger.info(f"Access token received: {access_token[:20]}...")
                
                # Fetch employee data immediately after successful authentication
                logger.info(f"Fetching employee data from {subdomain}.bamboohr.com...")
                employee_data = {}
                current_user_data = {}
                company_info = {}
                
                try:
                    # Initialize BambooHR integration to fetch data
                    bamboo_integration = BambooHRIntegration(subdomain, access_token)
                    
                    # Get all employee data
                    employees_result = bamboo_integration.get_all_employees()
                    if employees_result['success']:
                        employee_data = employees_result['data']
                        logger.info(f"Successfully fetched employee data: {employee_data.get('totalEmployees', 0)} employees")
                    else:
                        logger.warning(f"Failed to fetch employee data: {employees_result['error']}")
                    
                    # Get current user data
                    current_user_result = bamboo_integration.get_current_user()
                    if current_user_result['success']:
                        current_user_data = current_user_result['data']
                        logger.info("Successfully fetched current user data")
                    else:
                        logger.warning(f"Failed to fetch current user data: {current_user_result['error']}")
                    
                    # Get company info
                    try:
                        api_base = f"https://{subdomain}.bamboohr.com/api/v1"
                        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
                        company_resp = requests.get(f"{api_base}/meta/company", headers=headers, timeout=30)
                        if company_resp.status_code == 200:
                            company_info = company_resp.json()
                            logger.info("Successfully fetched company info")
                        else:
                            logger.warning(f"Failed to fetch company info: {company_resp.status_code}")
                    except Exception as e:
                        logger.warning(f"Error fetching company info: {str(e)}")
                    
                except Exception as e:
                    logger.error(f"Error fetching BambooHR data: {str(e)}")
                    # Continue with connection even if data fetch fails
                
                # Save the access token and connection details with employee data
                try:
                    user = Users.objects.get(UserId=user_id)
                    bamboohr_app, created = ExternalApplication.objects.get_or_create(
                        name='BambooHR',
                        defaults={
                            'category': 'HR Management',
                            'type': 'Human Resources',
                            'description': 'BambooHR integration for employee data management',
                            'icon_class': 'fas fa-users',
                            'status': 'connected'
                        }
                    )
                    
                    # Prepare projects_data with employees and current user
                    projects_data = {
                        'subdomain': subdomain,
                        'connected_at': datetime.now().isoformat(),
                        'employees': employee_data or {},
                        'current_user': current_user_data or {},
                        'last_sync': datetime.now().isoformat(),
                        'sync_status': 'success' if employee_data else 'partial'
                    }
                    
                    logger.info(f"Saving connection - Projects data keys: {list(projects_data.keys())}")
                    logger.info(f"Saving connection - Subdomain: {projects_data.get('subdomain')}")
                    logger.info(f"Saving connection - Total employees: {employee_data.get('totalEmployees', 0) if employee_data else 0}")
                    
                    connection, created = ExternalApplicationConnection.objects.update_or_create(
                        application=bamboohr_app,
                        user=user,
                        defaults={
                            'connection_token': access_token,
                            'connection_status': 'active',
                            'token_expires_at': datetime.now() + timedelta(days=365),
                            'projects_data': projects_data,
                            'last_used': datetime.now()
                        }
                    )
                    
                    # Create sync log
                    ExternalApplicationSyncLog.objects.create(
                        application=bamboohr_app,
                        user=user,
                        sync_type='manual',
                        sync_status='success' if employee_data else 'partial',
                        records_synced=employee_data.get('totalEmployees', 0) if employee_data else 0,
                        sync_started_at=datetime.now(),
                        sync_completed_at=datetime.now()
                    )
                    
                    logger.info(f"Successfully saved BambooHR connection with employee data: {employee_data.get('totalEmployees', 0)} employees")
                    
                    # Clean up OAuth state from database after successful connection
                    try:
                        oauth_state.delete()
                        logger.info("OAuth state cleaned up from database")
                    except Exception as e:
                        logger.warning(f"Failed to clean up OAuth state: {e}")
                    
                    # Redirect back to frontend with success (without token to avoid URL length limit)
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    frontend_url = f"{frontend_base}/integration/bamboohr?success=true&user_id={user_id}&subdomain={subdomain}"
                    
                    logger.info(f"Redirecting to frontend: {frontend_url}")
                    
                    # For local testing, if the request is to /oauth/callback, return JSON instead of redirecting
                    if is_local and '/oauth/callback' in request.path:
                        return JsonResponse({
                            'success': True,
                            'message': 'OAuth authentication successful',
                            'user_id': user_id,
                            'subdomain': subdomain,
                            'redirect_url': frontend_url
                        })
                    else:
                        from django.http import HttpResponseRedirect
                        return HttpResponseRedirect(frontend_url)
                    
                except Users.DoesNotExist:
                    logger.error("User not found")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/bamboohr?error=user_not_found"
                    
                    if is_local and '/oauth/callback' in request.path:
                        return JsonResponse({
                            'success': False,
                            'error': "User not found",
                            'redirect_url': error_url
                        })
                    else:
                        from django.http import HttpResponseRedirect
                        return HttpResponseRedirect(error_url)
                    
            except requests.RequestException as e:
                logger.error(f"Request error during token exchange: {str(e)}")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/bamboohr?error=network_error"
                
                if is_local and '/oauth/callback' in request.path:
                    return JsonResponse({
                        'success': False,
                        'error': f"Request error during token exchange: {str(e)}",
                        'redirect_url': error_url
                    })
                else:
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect(error_url)
        
        elif request.method == 'POST':
            # Handle POST callback - don't overwrite, just verify connection exists
            # The GET handler above already saved everything during OAuth redirect
            data = json.loads(request.body)
            user_id = data.get('user_id', 1)
            
            try:
                # Check if connection already exists (from GET handler)
                user = Users.objects.get(UserId=user_id)
                bamboohr_app = ExternalApplication.objects.get(name='BambooHR')
                connection = ExternalApplicationConnection.objects.get(
                    application=bamboohr_app,
                    user=user,
                    connection_status='active'
                )
                
                logger.info("POST callback - Connection already exists from OAuth flow")
                logger.info(f"Connection subdomain: {connection.projects_data.get('subdomain', 'N/A')}")
                
                # Don't overwrite - just return success
                return JsonResponse({
                    'success': True,
                    'message': 'BambooHR connection already established',
                    'connection_id': connection.id
                })
                
            except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                # Connection doesn't exist - might be from Flask OAuth server
                logger.warning("POST callback - No connection found, creating new one")
                
                access_token = data.get('access_token')
                subdomain = data.get('subdomain', '')
                account_info = data.get('account_info', {})
                
                if not access_token:
                    return JsonResponse({
                        'success': False,
                        'error': 'No access token provided'
                    })
                
                try:
                    user = Users.objects.get(UserId=user_id)
                    bamboohr_app, created = ExternalApplication.objects.get_or_create(
                        name='BambooHR',
                        defaults={
                            'category': 'HR Management',
                            'type': 'Human Resources',
                            'description': 'BambooHR integration for employee data management',
                            'icon_class': 'fas fa-users',
                            'status': 'connected'
                        }
                    )
                    
                    connection, created = ExternalApplicationConnection.objects.update_or_create(
                        application=bamboohr_app,
                        user=user,
                        defaults={
                            'connection_token': access_token,
                            'connection_status': 'active',
                            'token_expires_at': datetime.now() + timedelta(days=365),
                            'projects_data': {
                                'access_token': access_token,
                                'subdomain': subdomain,
                                'connected_at': datetime.now().isoformat(),
                                'account_info': account_info
                            }
                        }
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'BambooHR connection established successfully',
                        'connection_id': connection.id
                    })
                    
                except Users.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'User not found'
                })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"BambooHR OAuth callback error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'OAuth callback failed: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def bamboohr_add_user(request):
    """Add BambooHR employee to Users database"""
    try:
        data = json.loads(request.body)
        employee = data.get('employee', {})
        framework_id = data.get('framework_id', 1)  # Default framework ID
        user_id = data.get('user_id')  # Get current user ID from request
        
        if not employee:
            return JsonResponse({
                'success': False,
                'error': 'No employee data provided'
            })
        
        # Extract employee data
        employee_id = employee.get('id')
        email = employee.get('workEmail') or employee.get('email')
        first_name = employee.get('firstName') or ''
        last_name = employee.get('lastName') or ''
        display_name = employee.get('displayName') or f"{first_name} {last_name}".strip()
        department_name = employee.get('department') or 'Unknown'
        job_title = employee.get('jobTitle') or ''
        
        # Use email as username, or fallback to display name
        username = email or display_name
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'No valid username could be generated from employee data'
            })
        
        try:
            # Check if user already exists
            existing_user = Users.objects.filter(Email=email).first()
            
            if existing_user:
                logger.info(f"User already exists: {email}")
                return JsonResponse({
                    'success': False,
                    'already_exists': True,
                    'message': 'User already exists in database',
                    'user_id': existing_user.UserId
                })
            
            # Get connection to update added_users list
            connection = None
            if user_id:
                try:
                    bamboohr_app = ExternalApplication.objects.get(name='BambooHR')
                    connection = ExternalApplicationConnection.objects.filter(
                        application=bamboohr_app,
                        user_id=user_id,
                        connection_status='active'
                    ).first()
                except Exception as e:
                    logger.warning(f"Could not find connection to update: {str(e)}")
            
            # Get framework
            try:
                framework = Framework.objects.get(FrameworkId=framework_id)
            except Framework.DoesNotExist:
                # Use first available framework
                framework = Framework.objects.first()
                if not framework:
                    return JsonResponse({
                        'success': False,
                        'error': 'No framework found in database'
                    })
            
            logger.info(f"Adding user: {email}, Department: {department_name}")
            
            # Handle DepartmentId - search/create department and get its ID
            department_id = None
            if department_name:
                try:
                    # Try to find existing department by name
                    department = Department.objects.filter(DepartmentName=department_name).first()
                    
                    if department:
                        department_id = department.DepartmentId
                        logger.info(f"Found existing department: {department_name} (ID: {department_id})")
                    else:
                        # Create new department
                        # Get EntityId - try to find entity for this framework, or use default
                        entity_id = 1  # Default value
                        try:
                            # Get entity for this framework
                            entity = Entity.objects.filter(FrameworkId=framework.FrameworkId).first()
                            if entity:
                                entity_id = entity.Id
                                logger.info(f"Found entity ID: {entity_id} for framework {framework.FrameworkId}")
                        except Exception as e:
                            logger.warning(f"Could not find entity for framework: {str(e)}")
                            entity_id = 1
                        
                        logger.info(f"Creating department '{department_name}' with EntityId={entity_id}")
                        
                        # Create new department
                        new_department = Department.objects.create(
                            EntityId=entity_id,
                            DepartmentName=department_name,
                            DepartmentHead=0,  # Default value
                            IsActive=True,
                            CreatedDate=timezone.now(),  # Use Django timezone
                            BusinessUnitId=1,  # Default business unit
                            FrameworkId=framework
                        )
                        department_id = new_department.DepartmentId
                        logger.info(f"Created new department: {department_name} (ID: {department_id})")
                except Exception as dept_error:
                    logger.warning(f"Could not handle department '{department_name}': {str(dept_error)}")
                    department_id = None
            
            # Create new user with DepartmentId
            # Set DepartmentId to '0' if no valid department was found
            dept_id_str = str(department_id) if department_id else '0'
            
            new_user = Users.objects.create(
                UserName=username,
                Password='',  # Empty password - should be set by user later
                Email=email,
                FirstName=first_name,
                LastName=last_name,
                IsActive='Y',
                DepartmentId=dept_id_str,  # Set department ID or default to '0'
                consent_accepted='1',
                FrameworkId=framework
            )
            
            if department_id:
                logger.info(f"Created user with DepartmentId={department_id} for {email}")
            else:
                logger.info(f"Created user with default DepartmentId='0' for {email}")
            
            logger.info(f"Successfully added user: {email} (ID: {new_user.UserId})")
            
            # Update projects_data to track added users
            if connection and employee_id:
                try:
                    # Get current projects_data
                    projects_data = connection.projects_data if connection.projects_data else {}
                    
                    # Initialize added_users list if it doesn't exist
                    if 'added_users' not in projects_data:
                        projects_data['added_users'] = []
                    
                    # Add employee ID if not already in list
                    if employee_id not in projects_data['added_users']:
                        projects_data['added_users'].append(str(employee_id))
                        
                        # Update connection
                        connection.projects_data = projects_data
                        connection.save()
                        
                        logger.info(f"Updated projects_data with added_user: {employee_id}")
                except Exception as e:
                    logger.warning(f"Could not update projects_data: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'message': 'User added successfully',
                'user_id': new_user.UserId,
                'employee_id': employee_id,
                'user_data': {
                    'email': email,
                    'name': display_name,
                    'department': department_name,
                    'job_title': job_title
                }
            })
            
        except Exception as e:
            logger.error(f"Error adding user to database: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to add user: {str(e)}'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"BambooHR add user endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET"])
def bamboohr_reports(request):
    """Generate BambooHR reports"""
    try:
        user_id = request.GET.get('user_id', 1)
        report_type = request.GET.get('type', 'summary')
        
        try:
            user = Users.objects.get(UserId=user_id)
            bamboohr_app = ExternalApplication.objects.get(name='BambooHR')
            connection = ExternalApplicationConnection.objects.get(
                application=bamboohr_app,
                user=user,
                connection_status='active'
            )
            
            if not connection.projects_data or 'employees' not in connection.projects_data:
                return JsonResponse({
                    'success': False,
                    'error': 'No employee data found'
                })
            
            employee_data = connection.projects_data['employees']
            
            if report_type == 'summary':
                report = {
                    'total_employees': employee_data.get('totalEmployees', 0),
                    'active_employees': employee_data.get('activeEmployees', 0),
                    'recent_hires': employee_data.get('recentHires', 0),
                    'departments_count': len(employee_data.get('departments', [])),
                    'last_updated': employee_data.get('lastUpdated')
                }
            elif report_type == 'departments':
                report = {
                    'departments': employee_data.get('departments', []),
                    'total_departments': len(employee_data.get('departments', []))
                }
            elif report_type == 'employees':
                report = {
                    'employees': employee_data.get('employees', []),
                    'total_employees': len(employee_data.get('employees', []))
                }
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid report type'
                })
            
            return JsonResponse({
                'success': True,
                'report_type': report_type,
                'data': report,
                'generated_at': datetime.now().isoformat()
            })
            
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'BambooHR connection not found'
            })
    
    except Exception as e:
        logger.error(f"BambooHR reports endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET"])
def bamboohr_debug(request):
    """Debug endpoint to test BambooHR connection"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = Users.objects.get(UserId=user_id)
            bamboohr_app = ExternalApplication.objects.get(name='BambooHR')
            connection = ExternalApplicationConnection.objects.get(
                application=bamboohr_app,
                user=user,
                connection_status='active'
            )
            
            projects_data = connection.projects_data or {}
            subdomain = projects_data.get('subdomain', '')
            access_token = connection.connection_token
            
            logger.info(f"Debug - Subdomain: {subdomain}")
            logger.info(f"Debug - Access token length: {len(access_token) if access_token else 0}")
            logger.info(f"Debug - Projects data keys: {list(projects_data.keys())}")
            
            # Test URL construction
            test_url = f"https://{subdomain}.bamboohr.com/api/v1/employees/directory"
            logger.info(f"Debug - Test URL: {test_url}")
            
            return JsonResponse({
                'success': True,
                'debug_info': {
                    'subdomain': subdomain,
                    'has_access_token': bool(access_token),
                    'access_token_length': len(access_token) if access_token else 0,
                    'test_url': test_url,
                    'projects_data_keys': list(projects_data.keys())
                }
            })
            
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist) as e:
            return JsonResponse({
                'success': False,
                'error': f'Connection not found: {str(e)}'
            })
    
    except Exception as e:
        logger.error(f"BambooHR debug endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Debug error: {str(e)}'
        })