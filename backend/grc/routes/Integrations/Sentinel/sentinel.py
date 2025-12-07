import os
import json
import base64
import zlib
import secrets
import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, quote

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.shortcuts import redirect
from django.db import transaction
from grc.models import IntegrationDataList, Users
import re

def parse_microsoft_date(date_string):
    """Parse Microsoft date format with flexible microseconds handling"""
    try:
        # Remove 'Z' and replace with '+00:00' if present
        if date_string.endswith('Z'):
            date_string = date_string[:-1] + '+00:00'
        
        # Handle microseconds - Microsoft sometimes returns 7 digits, Python supports max 6
        # Use regex to find and normalize microseconds
        pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d+)'
        match = re.match(pattern, date_string)
        
        if match:
            base_time = match.group(1)
            microseconds = match.group(2)
            
            # Truncate microseconds to 6 digits if longer
            if len(microseconds) > 6:
                microseconds = microseconds[:6]
            elif len(microseconds) < 6:
                microseconds = microseconds.ljust(6, '0')
            
            # Reconstruct the date string
            timezone_part = date_string[date_string.find('+'):] if '+' in date_string else date_string[date_string.find('-'):]
            if '+' not in timezone_part and '-' not in timezone_part:
                timezone_part = '+00:00'
            
            date_string = f"{base_time}.{microseconds}{timezone_part}"
        
        parsed_date = datetime.fromisoformat(date_string)
        # Return timezone-aware datetime for processing, will be converted to naive later
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        return parsed_date
    except Exception as e:
        print(f"Date parsing error for '{date_string}': {e}")
        # Fallback to current time if parsing fails
        return datetime.now()

# ==================== SERVICE CLASSES ====================

class SentinelOAuthService:
    """OAuth service for Microsoft Sentinel authentication"""
    
    def __init__(self):
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID', '1d9fdf2e-ebc8-47e0-8e7d-4c4c41b6a616')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID', 'aa7c8c45-41a3-4453-bc9a-3adfe8ff5fb6')
        # Use MICROSOFT_REDIRECT_URI to match settings.py, with fallback options
        # Priority: MICROSOFT_REDIRECT_URI env var > REDIRECT_URI env var > settings.REDIRECT_URI > default
        
        def clean_redirect_uri(uri):
            """Remove quotes and whitespace from redirect URI"""
            if not uri:
                return None
            uri = str(uri).strip()
            # Remove quotes from start and end if present
            while (uri.startswith('"') and uri.endswith('"')) or (uri.startswith("'") and uri.endswith("'")):
                uri = uri[1:-1].strip()
            return uri.strip('"\'')
        
        redirect_uri_from_env = clean_redirect_uri(os.getenv('MICROSOFT_REDIRECT_URI') or os.getenv('REDIRECT_URI'))
        redirect_uri_from_settings = clean_redirect_uri(getattr(settings, 'REDIRECT_URI', None))
        
        # Determine default based on environment
        use_local = os.getenv('USE_LOCAL_DEVELOPMENT', 'false').lower() == 'true'
        default_redirect_uri = (
            'http://localhost:8000/auth/sentinel/callback' if use_local
            else 'https://grc-backend.vardaands.com/auth/sentinel/callback'
        )
        
        # Use first available value, ensuring it's cleaned
        self.redirect_uri = redirect_uri_from_env or redirect_uri_from_settings or default_redirect_uri
        
        # Validate redirect_uri is not empty and is a valid absolute URI
        if not self.redirect_uri:
            raise ValueError(
                "Redirect URI must be configured. Set MICROSOFT_REDIRECT_URI or REDIRECT_URI environment variable."
            )
        if not (self.redirect_uri.startswith('http://') or self.redirect_uri.startswith('https://')):
            raise ValueError(
                f"Redirect URI must be a valid absolute URI (starting with http:// or https://). "
                f"Got: {repr(self.redirect_uri)}"
            )
        self.scope = 'https://graph.microsoft.com/.default'
    
    def get_authorization_url(self, state):
        """Generate OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': state,
            'response_mode': 'query',
            'prompt': 'login'
        }
        base_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize'
        return f'{base_url}?{urlencode(params)}'
    
    def exchange_code_for_token(self, auth_code):
        """Exchange authorization code for access token"""
        token_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'scope': self.scope
        }
        
        response = requests.post(token_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        if not response.ok:
            error_data = response.json()
            raise Exception(f"Token exchange failed: {error_data.get('error_description', error_data.get('error'))}")
        
        return response.json()
    
    def refresh_access_token(self, refresh_token):
        """Refresh the access token"""
        token_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'scope': self.scope
        }
        
        response = requests.post(token_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        if not response.ok:
            error_data = response.json()
            raise Exception(f"Token refresh failed: {error_data.get('error_description', error_data.get('error'))}")
        
        return response.json()
    
    @staticmethod
    def generate_random_state():
        """Generate random state for CSRF protection"""
        return secrets.token_hex(32)
    
    @staticmethod
    def verify_state(state, session_state):
        """Verify OAuth state parameter"""
        return state == session_state


class SentinelAuthService:
    """Authentication service for Microsoft Sentinel"""
    
    def __init__(self):
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID', '1d9fdf2e-ebc8-47e0-8e7d-4c4c41b6a616')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID', 'aa7c8c45-41a3-4453-bc9a-3adfe8ff5fb6')
        self.scope = 'https://graph.microsoft.com/.default'
    
    def authenticate_with_credentials(self, email, password):
        """Authenticate using Resource Owner Password Credential flow"""
        try:
            print('🔐 Authenticating with Microsoft using Resource Owner Password Credential flow')
            token_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': self.scope,
                'username': email,
                'password': password,
                'grant_type': 'password'
            }
            
            response = requests.post(token_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
            response.raise_for_status()
            
            token_data = response.json()
            user_info = self.get_user_info(token_data['access_token'])
            
            return {
                'success': True,
                'accessToken': token_data['access_token'],
                'refreshToken': token_data.get('refresh_token'),
                'expiresIn': token_data['expires_in'],
                'tokenExpiry': datetime.now().timestamp() * 1000 + (token_data['expires_in'] * 1000),
                'userInfo': user_info
            }
        except Exception as error:
            print(f'❌ Authentication failed: {error}')
            error_message = 'Authentication failed'
            if hasattr(error, 'response') and error.response:
                try:
                    error_data = error.response.json()
                    error_message = error_data.get('error_description', error_data.get('error', error_message))
                except:
                    pass
            return {'success': False, 'error': error_message}
    
    def get_user_info(self, access_token):
        """Get user information from Microsoft Graph"""
        try:
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'id': data.get('id'),
                'displayName': data.get('displayName'),
                'userPrincipalName': data.get('userPrincipalName'),
                'mail': data.get('mail')
            }
        except:
            return {
                'id': 'unknown',
                'displayName': 'User',
                'userPrincipalName': 'user@domain.com',
                'mail': 'user@domain.com'
            }
    
    def test_defender_connection(self, access_token):
        """Test connection to Microsoft Defender"""
        try:
            test_url = 'https://graph.microsoft.com/v1.0/security/incidents?$top=1'
            response = requests.get(
                test_url,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
            )
            response.raise_for_status()
            data = response.json()
            return {'success': True, 'incidentCount': len(data.get('value', []))}
        except Exception as error:
            error_msg = str(error)
            if hasattr(error, 'response') and error.response:
                try:
                    error_data = error.response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                except:
                    pass
            return {'success': False, 'error': error_msg}
    
    def refresh_token(self, refresh_token):
        """Refresh access token"""
        try:
            token_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
                'scope': self.scope
            }
            
            response = requests.post(token_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
            response.raise_for_status()
            token_data = response.json()
            
            return {
                'success': True,
                'accessToken': token_data['access_token'],
                'refreshToken': token_data.get('refresh_token', refresh_token),
                'expiresIn': token_data['expires_in'],
                'tokenExpiry': datetime.now().timestamp() * 1000 + (token_data['expires_in'] * 1000)
            }
        except Exception as error:
            error_msg = str(error)
            if hasattr(error, 'response') and error.response:
                try:
                    error_data = error.response.json()
                    error_msg = error_data.get('error_description', error_msg)
                except:
                    pass
            return {'success': False, 'error': error_msg}


class QueryDecompressor:
    """Decompress and parse KQL queries from alerts"""
    
    @staticmethod
    def decompress_query(compressed_query):
        """Decompress base64 encoded compressed query"""
        try:
            import re
            base64_match = re.search(r"'([A-Za-z0-9+/=]+)'", compressed_query)
            if not base64_match:
                raise Exception('No base64 data found in query')
            
            base64_data = base64_match.group(1)
            buffer = base64.b64decode(base64_data)
            
            # Try different decompression methods
            try:
                decompressed = zlib.decompress(buffer)
            except:
                try:
                    decompressed = zlib.decompress(buffer, 16 + zlib.MAX_WBITS)  # gzip
                except:
                    decompressed = zlib.decompress(buffer, -zlib.MAX_WBITS)  # raw deflate
            
            decompressed_string = decompressed.decode('utf-8')
            return QueryDecompressor.parse_kql_result(decompressed_string)
        except Exception as error:
            print(f'❌ Error decompressing query: {error}')
            return None
    
    @staticmethod
    def parse_kql_result(kql_result):
        """Parse KQL result to extract user and action information"""
        try:
            import re
            
            json_data = None
            try:
                json_data = json.loads(kql_result)
            except:
                pass
            
            # Extract emails
            email_regex = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            emails = re.findall(email_regex, kql_result)
            
            # Extract users
            user_patterns = [
                r'(?:user|account|email|mailbox|upn|username)[:\s=]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"',
                r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
            ]
            
            all_user_matches = []
            for pattern in user_patterns:
                matches = re.findall(pattern, kql_result, re.IGNORECASE)
                all_user_matches.extend(matches)
            
            unique_users = list(set(all_user_matches))
            
            # Extract actions
            action_patterns = [
                r'(?:action|operation|activity|command|ActionsPerformed)[:\s=]+"([^"]+)"',
                r'ActionsPerformed[:\s]*\["([^"]+)"\]',
                r'"([^"]*(?:add|remove|create|delete|modify|change|update)[^"]*)"'
            ]
            
            all_action_matches = []
            for pattern in action_patterns:
                matches = re.findall(pattern, kql_result, re.IGNORECASE)
                all_action_matches.extend(matches)
            
            generic_actions = ['action', 'operation', 'activity', 'command', 'performed', 'detected', 'sensitive', 'operations']
            unique_actions = [a for a in set(all_action_matches) if a and a.lower() not in generic_actions]
            
            result = {
                'rawData': kql_result,
                'jsonData': json_data,
                'emails': emails or [],
                'users': unique_users or [],
                'actions': unique_actions or [],
                'hasData': False
            }
            
            if json_data:
                if json_data.get('User'):
                    result['primaryUser'] = json_data['User']
                    result['hasData'] = True
                if json_data.get('ActionsPerformed') and isinstance(json_data['ActionsPerformed'], list):
                    result['primaryAction'] = json_data['ActionsPerformed'][0]
                if json_data.get('AlertDescription'):
                    result['alertDescription'] = json_data['AlertDescription']
            
            if not result['hasData'] and (result['emails'] or result['users']):
                result['hasData'] = True
                result['primaryUser'] = result['users'][0] if result['users'] else result['emails'][0] if result['emails'] else None
            
            if not result.get('primaryAction') and result['actions']:
                result['primaryAction'] = result['actions'][0]
            
            return result
        except Exception as error:
            return {'rawData': kql_result, 'hasData': False}
    
    @staticmethod
    def extract_enriched_user_data(alert):
        """Extract enriched user data from alert"""
        try:
            if not alert.get('additionalData') or not alert['additionalData'].get('Query'):
                return None
            
            decompressed = QueryDecompressor.decompress_query(alert['additionalData']['Query'])
            
            if decompressed and decompressed.get('hasData'):
                return {
                    'user': decompressed.get('primaryUser'),
                    'action': decompressed.get('primaryAction'),
                    'alertDescription': decompressed.get('alertDescription'),
                    'allEmails': decompressed.get('emails'),
                    'allActions': decompressed.get('actions'),
                    'source': 'decompressed_query'
                }
            
            return None
        except:
            return None


class DefenderAPIService:
    """Service for interacting with Microsoft Defender API"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://graph.microsoft.com/v1.0/security'
    
    def get_incidents(self, filters=None):
        """Get incidents from Microsoft Defender"""
        try:
            filters = filters or {}
            
            # Get time range from filters, default to 30 days (1 month)
            days = int(filters.get('days', 30))
            
            days_ago = datetime.now() - timedelta(days=days)
            days_ago_iso = days_ago.isoformat() + 'Z'
            
            print(f"[SENTINEL] Fetching incidents from last {days} days")
            
            url = f'{self.base_url}/incidents?$top=50'  # Microsoft Defender API limit is 50
            odata_filters = [f'createdDateTime ge {days_ago_iso}']
            
            if odata_filters:
                url += f'&$filter={quote(" and ".join(odata_filters))}'
            
            response = requests.get(
                url,
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if not response.ok:
                error_details = ''
                try:
                    error_data = response.json()
                    error_details = error_data.get('error', {}).get('message', json.dumps(error_data))
                except:
                    error_details = response.text
                raise Exception(f'Defender API Error: {response.status_code} - {error_details}')
            
            data = response.json()
            all_incidents = data.get('value', [])
            print(f"[SENTINEL] Initial fetch: {len(all_incidents)} incidents")
            
            # Handle pagination - increased from 3 to 10 pages to fetch more incidents
            next_link = data.get('@odata.nextLink')
            page_count = 1
            
            while next_link and page_count < 10:
                print(f"[SENTINEL] Fetching page {page_count + 1}...")
                next_response = requests.get(
                    next_link,
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if next_response.ok:
                    next_data = next_response.json()
                    page_incidents = next_data.get('value', [])
                    all_incidents.extend(page_incidents)
                    print(f"[SENTINEL] Page {page_count + 1}: {len(page_incidents)} incidents (Total: {len(all_incidents)})")
                    next_link = next_data.get('@odata.nextLink')
                    page_count += 1
                else:
                    print(f"[SENTINEL] Pagination failed: {next_response.status_code}")
                    break
            
            print(f"[SENTINEL] Total incidents fetched: {len(all_incidents)}")
            
            incidents = self.transform_incidents(all_incidents)
            grouped_incidents = self.group_incidents_by_id(incidents)
            
            # Filter by date - use the same days as the API call
            date_threshold = datetime.now(timezone.utc) - timedelta(days=days)
            filtered_incidents = [
                incident for incident in grouped_incidents
                if parse_microsoft_date(incident['createdTime']) >= date_threshold
            ]
            print(f"[SENTINEL] Incidents after date filter ({days} days): {len(filtered_incidents)}")
            
            # Apply status filter
            if not filters.get('includeAll') and not filters.get('status'):
                filtered_incidents = [
                    incident for incident in filtered_incidents
                    if incident['status'] in ['New', 'Active']
                ]
                print(f"[SENTINEL] Incidents after status filter (Active only): {len(filtered_incidents)}")
            elif filters.get('status') and filters['status'] != 'All':
                filtered_incidents = [
                    incident for incident in filtered_incidents
                    if incident['status'] == filters['status']
                ]
                print(f"[SENTINEL] Incidents after status filter ({filters['status']}): {len(filtered_incidents)}")
            
            # Apply severity filter
            if filters.get('severity'):
                filtered_incidents = [
                    incident for incident in filtered_incidents
                    if incident['severity'].lower() == filters['severity'].lower()
                ]
                print(f"[SENTINEL] Incidents after severity filter ({filters['severity']}): {len(filtered_incidents)}")
            
            print(f"[SENTINEL] Final filtered incidents: {len(filtered_incidents)}")
            return filtered_incidents
        except Exception as error:
            print(f'❌ Error fetching incidents: {error}')
            raise error
    
    def get_incident(self, incident_id):
        """Get a single incident by ID"""
        url = f'{self.base_url}/incidents/{incident_id}'
        response = requests.get(
            url,
            headers={
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if not response.ok:
            raise Exception(f'Failed to fetch incident: {response.status_code}')
        
        incident = response.json()
        return self.transform_incident(incident)
    
    def get_incident_alerts(self, incident_id):
        """Get alerts for a specific incident"""
        try:
            print(f'[SENTINEL] Fetching alerts for incident ID: {incident_id}')
            incident_url = f'{self.base_url}/incidents/{incident_id}'
            incident_response = requests.get(
                incident_url,
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if not incident_response.ok:
                print(f'[SENTINEL] Failed to fetch incident: {incident_response.status_code}')
                raise Exception('Failed to fetch incident')
            
            incident = incident_response.json()
            print(f'[SENTINEL] Incident fetched successfully')
            
            # Try to fetch alerts with different filter attempts
            alerts = []
            filter_attempts = [
                f"incidentId eq '{incident_id}'",
                f"incidentId eq {incident_id}"
            ]
            
            for filter_str in filter_attempts:
                list_url = f'https://graph.microsoft.com/v1.0/security/alerts_v2?$filter={quote(filter_str)}&$top=100'
                print(f'[SENTINEL] Trying filter: {filter_str}')
                
                try:
                    list_response = requests.get(
                        list_url,
                        headers={
                            'Authorization': f'Bearer {self.access_token}',
                            'Content-Type': 'application/json'
                        }
                    )
                    
                    if list_response.ok:
                        list_data = list_response.json()
                        alerts = list_data.get('value', [])
                        print(f'[SENTINEL] Found {len(alerts)} alerts with filter')
                        if alerts:
                            break
                except Exception as e:
                    print(f'[SENTINEL] Filter attempt failed: {e}')
                    continue
            
            # If no alerts found, try fetching all recent alerts and filter
            if not alerts:
                print('[SENTINEL] No alerts found with filters, fetching all recent alerts...')
                all_alerts_url = 'https://graph.microsoft.com/v1.0/security/alerts_v2?$top=200&$orderby=createdDateTime desc'
                all_alerts_response = requests.get(
                    all_alerts_url,
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if all_alerts_response.ok:
                    all_alerts_data = all_alerts_response.json()
                    all_alerts = all_alerts_data.get('value', [])
                    print(f'[SENTINEL] Fetched {len(all_alerts)} total alerts')
                    alerts = [
                        alert for alert in all_alerts
                        if str(alert.get('incidentId')) == str(incident_id)
                    ]
                    print(f'[SENTINEL] Filtered to {len(alerts)} alerts for incident {incident_id}')
            
            if alerts:
                transformed = self.transform_alerts_to_detailed_format(alerts, incident)
                print(f'[SENTINEL] Transformed {len(transformed)} alerts')
                if transformed:
                    print(f'[SENTINEL] Sample alert: {transformed[0]}')
                return transformed
            
            print('[SENTINEL] No alerts found for this incident')
            return []
        except Exception as error:
            print(f'❌ Error in get_incident_alerts: {error}')
            import traceback
            traceback.print_exc()
            raise error
    
    def transform_alerts_to_detailed_format(self, alerts, incident):
        """Transform alerts to detailed format"""
        transformed_alerts = []
        
        for index, alert in enumerate(alerts):
            time_generated = (alert.get('createdDateTime') or 
                            alert.get('firstActivityDateTime') or 
                            incident.get('createdDateTime') or 
                            datetime.now().isoformat())
            
            # Try to extract enriched data
            enriched_data = None
            try:
                enriched_data = QueryDecompressor.extract_enriched_user_data(alert)
            except:
                pass
            
            user = enriched_data.get('user') if enriched_data else None
            
            # Extract user from various sources
            if not user and alert.get('userStates') and isinstance(alert['userStates'], list):
                for user_state in alert['userStates']:
                    if user_state.get('userPrincipalName') or user_state.get('accountName'):
                        user = user_state.get('userPrincipalName') or user_state.get('accountName')
                        break
            
            if not user and alert.get('entities'):
                for entity in alert['entities']:
                    odata_type = entity.get('@odata.type', '')
                    if 'user' in odata_type.lower() or 'mailbox' in odata_type.lower():
                        user = (entity.get('userPrincipalName') or 
                               entity.get('mailboxPrimaryAddress') or 
                               entity.get('accountName'))
                        break
            
            if not user and alert.get('evidence'):
                for evidence in alert['evidence']:
                    odata_type = evidence.get('@odata.type', '')
                    if 'user' in odata_type.lower() or 'mailbox' in odata_type.lower():
                        if evidence.get('userAccount'):
                            user = (evidence['userAccount'].get('userPrincipalName') or 
                                   evidence['userAccount'].get('accountName'))
                            break
            
            # Extract user from description
            if not user:
                import re
                text = f"{alert.get('title', '')} {alert.get('description', '')}"
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
                if email_match:
                    user = email_match.group(1)
            
            # Extract actions
            actions_performed = None
            if enriched_data and enriched_data.get('action'):
                actions_performed = [enriched_data['action']]
            else:
                actions_performed = self.extract_actions_from_alert(alert, incident)
            
            if actions_performed:
                generic_actions = ['Suspicious activity detected', 'SuspiciousActivity', 'Unknown']
                if actions_performed[0] in generic_actions:
                    actions_performed = None
            
            suspicious_activity_count = self.extract_suspicious_activity_count(alert)
            
            alert_description = (enriched_data.get('alertDescription') if enriched_data else None) or \
                               alert.get('description') or \
                               alert.get('title') or \
                               'No description available'
            
            transformed = {
                'id': alert.get('id', f'alert-{index}'),
                'timeGenerated': time_generated,
                'actionsPerformed': actions_performed,
                'alertDescription': alert_description,
                'suspiciousActivityCount': suspicious_activity_count,
                'user': user,
                'severity': self.map_severity(alert.get('severity') or incident.get('severity') or 'Informational'),
                'status': self.map_status(alert.get('status') or incident.get('status') or 'Active'),
                'category': alert.get('category', 'Unknown'),
                'title': alert.get('title') or incident.get('displayName') or 'Untitled Alert',
                'detectionSource': alert.get('detectionSource', 'Microsoft Defender'),
                'productName': alert.get('productName', 'Microsoft Defender'),
                'fullAlertData': alert
            }
            
            transformed_alerts.append(transformed)
        
        return transformed_alerts
    
    def extract_actions_from_alert(self, alert, incident):
        """Extract actions from alert description"""
        actions = []
        text = f"{alert.get('title', '')} {alert.get('description', '')}".lower()
        
        action_patterns = [
            {'pattern': r'add(?:ed|ing)?\s+(?:member|user)\s+to\s+(?:group|role)', 'action': 'Add member to group'},
            {'pattern': r'add(?:ed|ing)?\s+(?:user|member)', 'action': 'Add user'},
            {'pattern': r'remov(?:ed|ing)?\s+(?:member|user)', 'action': 'Remove user'},
            {'pattern': r'creat(?:ed|ing)?\s+(?:user|account)', 'action': 'Create user'},
            {'pattern': r'delet(?:ed|ing)?\s+(?:user|account)', 'action': 'Delete user'},
            {'pattern': r'modif(?:ied|ying)?\s+(?:user|account)', 'action': 'Modify user'},
            {'pattern': r'reset.*password', 'action': 'Reset password'},
            {'pattern': r'login|sign[- ]?in', 'action': 'Sign in'}
        ]
        
        import re
        for item in action_patterns:
            if re.search(item['pattern'], text, re.IGNORECASE) and item['action'] not in actions:
                actions.append(item['action'])
        
        if not actions:
            actions.append('Suspicious activity detected')
        
        return actions
    
    def extract_suspicious_activity_count(self, alert):
        """Extract suspicious activity count from alert"""
        import re
        text = f"{alert.get('description', '')} {alert.get('title', '')}"
        
        count_patterns = [
            r'(\d+)\s+(?:suspicious|sensitive|unusual)\s+(?:operations?|activities?)',
            r'performed\s+(\d+)'
        ]
        
        for pattern in count_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        if alert.get('evidence'):
            return len(alert['evidence'])
        if alert.get('entities'):
            return len(alert['entities'])
        
        return 1
    
    def group_incidents_by_id(self, incidents):
        """Group incidents by incident ID - match backend.js logic exactly"""
        incident_groups = {}
        
        for incident in incidents:
            incident_id = incident.get('incidentId') or incident.get('id')
            
            if incident_id not in incident_groups:
                incident_groups[incident_id] = {
                    **incident,
                    'alerts': [incident],
                    'alertsCount': 1,
                    'activeAlerts': 1 if incident.get('status') in ['New', 'Active'] else 0,
                    'activeAlertsRatio': '1/1'
                }
            else:
                existing = incident_groups[incident_id]
                existing['alerts'].append(incident)
                existing['alertsCount'] += 1
                if incident.get('status') in ['New', 'Active']:
                    existing['activeAlerts'] += 1
                existing['activeAlertsRatio'] = f"{existing['activeAlerts']}/{existing['alertsCount']}"
        
        return list(incident_groups.values())
    
    def transform_incidents(self, incidents):
        """Transform multiple incidents"""
        return [self.transform_incident(incident) for incident in incidents]
    
    def transform_incident(self, incident):
        """Transform a single incident"""
        title = incident.get('title') or incident.get('displayName') or 'Untitled Incident'
        description = incident.get('description', 'No description available')
        severity = incident.get('severity', 'Informational')
        status = incident.get('status', 'Unknown')
        created_time = incident.get('createdDateTime', datetime.now().isoformat())
        
        # Parse Microsoft date format properly
        if incident.get('createdDateTime'):
            try:
                parsed_date = parse_microsoft_date(incident['createdDateTime'])
                created_time = parsed_date.isoformat()
            except Exception as e:
                print(f"Error parsing createdDateTime: {e}")
                created_time = datetime.now().isoformat()
        
        # Calculate alerts count - match backend.js logic exactly
        total_alerts = len(incident.get('alerts', []))
        active_alerts = len([a for a in incident.get('alerts', []) if a.get('status') in ['new', 'active']])
        active_alerts_ratio = f'{active_alerts}/{total_alerts}' if total_alerts > 0 else '0/0'
        
        # Generate incident ID - match backend.js logic
        incident_id = incident.get('id', f'incident-{int(datetime.now().timestamp() * 1000)}')
        
        return {
            'id': incident_id,
            'incidentId': incident_id,
            'title': title,
            'severity': self.map_severity(severity),
            'status': self.map_status(status),
            'createdTime': created_time,
            'createdDateTime': created_time,  # Add this for frontend compatibility
            'description': description,
            'incidentNumber': incident.get('id', 'N/A'),
            'alertsCount': total_alerts,
            'activeAlerts': active_alerts,
            'activeAlertsRatio': active_alerts_ratio,
            'owner': incident.get('assignedTo', 'Unassigned'),
            'assignedTo': incident.get('assignedTo', 'Unassigned'),  # Add this for frontend compatibility
            'classification': incident.get('classification', 'Unclassified'),
            'lastActivityTime': incident.get('lastUpdateDateTime', created_time),
            'lastUpdateTime': incident.get('lastUpdateDateTime', created_time),
            'lastUpdateDateTime': incident.get('lastUpdateDateTime', created_time),  # Add this for frontend compatibility
            'source': 'microsoft-defender',
            'displayName': title,  # Add this for frontend compatibility
            'alerts': incident.get('alerts', [])  # Include alerts array
        }
    
    @staticmethod
    def map_severity(severity):
        """Map severity to standard format - match backend.js exactly"""
        if isinstance(severity, str):
            severity_map = {
                'high': 'High',
                'medium': 'Medium',
                'low': 'Low',
                'informational': 'Informational',
                'critical': 'Critical'
            }
            return severity_map.get(severity.lower(), 'Informational')
        return 'Informational'
    
    @staticmethod
    def map_status(status):
        """Map status to standard format - match backend.js exactly"""
        if isinstance(status, str):
            status_map = {
                'new': 'New',
                'active': 'Active',
                'resolved': 'Closed',
                'closed': 'Closed'
            }
            return status_map.get(status.lower(), 'Unknown')
        return 'Unknown'
    
    def test_connection(self):
        """Test connection to Microsoft Defender API"""
        try:
            url = f'{self.base_url}/incidents?$top=1'
            response = requests.get(
                url,
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if not response.ok:
                raise Exception('Connection test failed')
            
            data = response.json()
            return {'success': True, 'incidentCount': len(data.get('value', []))}
        except Exception as error:
            return {'success': False, 'error': str(error)}


# ==================== HELPER FUNCTIONS ====================

def get_user_access_token(request):
    """Get and refresh user access token if needed"""
    try:
        access_token = request.session.get('sentinelAccessToken')
        token_expiry = request.session.get('sentinelTokenExpiry')
        
        if access_token and token_expiry:
            now = datetime.now().timestamp() * 1000
            expires_in = token_expiry - now
            
            # If token expires in more than 5 minutes, return it
            if expires_in > 300000:
                return access_token
            
            # Refresh token
            refresh_token = request.session.get('sentinelRefreshToken')
            if refresh_token:
                auth_method = request.session.get('authMethod')
                if auth_method == 'credentials':
                    return refresh_credential_token(request)
                else:
                    return refresh_access_token(request)
        
        raise Exception('No valid access token available')
    except Exception as error:
        print(f'Error getting user access token: {error}')
        raise error


def refresh_access_token(request):
    """Refresh OAuth access token"""
    try:
        oauth_service = SentinelOAuthService()
        refresh_token = request.session.get('sentinelRefreshToken')
        token_response = oauth_service.refresh_access_token(refresh_token)
        
        request.session['sentinelAccessToken'] = token_response['access_token']
        request.session['sentinelRefreshToken'] = token_response.get('refresh_token', refresh_token)
        request.session['sentinelTokenExpiry'] = datetime.now().timestamp() * 1000 + (token_response['expires_in'] * 1000)
        
        return token_response['access_token']
    except Exception as error:
        raise error


def refresh_credential_token(request):
    """Refresh credentials-based access token"""
    try:
        auth_service = SentinelAuthService()
        refresh_token = request.session.get('sentinelRefreshToken')
        token_response = auth_service.refresh_token(refresh_token)
        
        if token_response['success']:
            request.session['sentinelAccessToken'] = token_response['accessToken']
            request.session['sentinelRefreshToken'] = token_response['refreshToken']
            request.session['sentinelTokenExpiry'] = token_response['tokenExpiry']
            return token_response['accessToken']
        else:
            raise Exception(token_response['error'])
    except Exception as error:
        raise error


# ==================== DATABASE OPERATIONS ====================

def save_incident_to_database(incident_data, user_id=None, username=None):
    """
    Save Sentinel incident to IntegrationDataList table
    
    Args:
        incident_data (dict): Incident data from Microsoft Sentinel
        user_id (int, optional): User ID who is saving the incident
        username (str, optional): Username who is saving the incident
    
    Returns:
        dict: Success status and saved record details
    """
    try:
        with transaction.atomic():
            # Extract incident information
            incident_title = incident_data.get('title') or incident_data.get('displayName', 'Untitled Incident')
            incident_time = incident_data.get('createdDateTime') or incident_data.get('createdTime')
            
            # Parse incident time
            if incident_time:
                try:
                    incident_datetime = parse_microsoft_date(incident_time)
                    print(f"[SENTINEL] Parsed datetime: {incident_datetime}, timezone: {incident_datetime.tzinfo}")
                    # Convert timezone-aware datetime to naive datetime for MySQL compatibility
                    if incident_datetime.tzinfo is not None:
                        incident_datetime = incident_datetime.replace(tzinfo=None)
                        print(f"[SENTINEL] Converted to naive datetime: {incident_datetime}")
                except Exception as e:
                    print(f"[SENTINEL] Date parsing failed: {e}")
                    incident_datetime = datetime.now()
            else:
                incident_datetime = datetime.now()
            
            print(f"[SENTINEL] Final datetime for DB: {incident_datetime}, timezone: {incident_datetime.tzinfo}")
            
            # Get username if user_id provided
            if user_id and not username:
                try:
                    user = Users.objects.get(UserId=user_id)
                    username = user.UserName
                except Users.DoesNotExist:
                    username = 'Unknown User'
            elif not username:
                username = 'System'
            
            # Prepare metadata
            metadata = {
                'severity': incident_data.get('severity', 'Unknown'),
                'status': incident_data.get('status', 'Unknown'),
                'incident_number': incident_data.get('incidentNumber') or incident_data.get('id'),
                'alerts_count': incident_data.get('alertsCount', 0),
                'active_alerts': incident_data.get('activeAlerts', 0),
                'source': 'Microsoft Sentinel',
                'saved_at': datetime.now().isoformat()
            }
            
            # Create IntegrationDataList entry
            integration_record = IntegrationDataList.objects.create(
                heading=incident_title,
                source='Microsoft Sentinel',
                username=username,
                time=incident_datetime,
                data=incident_data,
                metadata=metadata
            )
            
            print(f"[SENTINEL] Saved incident {incident_title} to database with ID {integration_record.id}")
            
            return {
                'success': True,
                'message': f'Incident "{incident_title}" saved successfully',
                'record_id': integration_record.id,
                'heading': incident_title
            }
            
    except Exception as error:
        print(f'[SENTINEL] Error saving incident to database: {error}')
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }


# ==================== VIEWS / ROUTES ====================

def sentinel_home(request):
    """Home page for Sentinel integration"""
    return JsonResponse({'message': 'Sentinel Platform', 'status': 'ok'})


def sentinel_integrations(request):
    """Integrations page"""
    is_sentinel_connected = request.session.get('isSentinelConnected', False)
    user_info = request.session.get('userInfo')
    
    return JsonResponse({
        'isSentinelConnected': is_sentinel_connected,
        'userInfo': user_info,
        'query': dict(request.GET)
    })


@csrf_exempt
def sentinel_oauth_start(request):
    """Initiate OAuth flow"""
    try:
        print("[SENTINEL] ===== OAuth Start Request Received =====")
        print(f"[SENTINEL] Request method: {request.method}")
        print(f"[SENTINEL] Request path: {request.path}")
        
        # Ensure session exists before storing state
        if not request.session.session_key:
            request.session.create()
            print("[SENTINEL] Created new session")
        
        print(f"[SENTINEL] Session key: {request.session.session_key}")
        
        oauth_service = SentinelOAuthService()
        state = oauth_service.generate_random_state()
        request.session['oauthState'] = state
        request.session.modified = True  # Ensure session is saved
        request.session.save()  # Explicitly save the session
        
        print(f"[SENTINEL] Generated state: {state}")
        print(f"[SENTINEL] State saved to session: {request.session.get('oauthState')}")
        
        auth_url = oauth_service.get_authorization_url(state)
        print(f"[SENTINEL] Auth URL: {auth_url[:80]}...")
        print(f"[SENTINEL] Client ID: {oauth_service.client_id}")
        print(f"[SENTINEL] Tenant ID: {oauth_service.tenant_id}")
        print(f"[SENTINEL] Redirect URI: {oauth_service.redirect_uri}")
        print("[SENTINEL] ===== Redirecting to Microsoft =====")
        
        return redirect(auth_url)
    except Exception as error:
        print(f"[SENTINEL] ===== ERROR in OAuth Start =====")
        print(f"[SENTINEL] Error: {error}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error initiating authentication: {str(error)}'}, status=500)


@csrf_exempt
def sentinel_oauth_callback(request):
    """Handle OAuth callback"""
    print("[SENTINEL] ===== OAuth Callback Received =====")
    print(f"[SENTINEL] Request method: {request.method}")
    print(f"[SENTINEL] Request path: {request.path}")
    print(f"[SENTINEL] Session key exists: {request.session.session_key is not None}")
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    print(f"[SENTINEL] Code present: {code is not None}")
    print(f"[SENTINEL] State from request: {state[:20] if state else 'NONE'}...")
    print(f"[SENTINEL] State from session: {request.session.get('oauthState', 'NONE')[:20] if request.session.get('oauthState') else 'NONE'}...")
    print(f"[SENTINEL] Session ID: {request.session.session_key}")
    
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')
    
    if error:
        print(f"[SENTINEL] OAuth error received: {error}")
        return redirect(f'{frontend_url}/integration/sentinel?error={error}')
    
    session_state = request.session.get('oauthState')
    
    # Check if state verification should be enforced
    skip_state_verification = os.getenv('SKIP_OAUTH_STATE_VERIFICATION', 'false').lower() == 'true'
    
    if not session_state:
        print("[SENTINEL] ERROR: No state found in session!")
        print(f"[SENTINEL] Available session keys: {list(request.session.keys())}")
        if not skip_state_verification:
            return redirect(f'{frontend_url}/integration/sentinel?error=Session%20expired%20or%20invalid')
        else:
            print("[SENTINEL] WARNING: Skipping state verification (development mode)")
    
    oauth_service = SentinelOAuthService()
    if session_state and not oauth_service.verify_state(state, session_state):
        print(f"[SENTINEL] ERROR: State mismatch!")
        print(f"[SENTINEL] Expected: {session_state}")
        print(f"[SENTINEL] Received: {state}")
        if not skip_state_verification:
            return redirect(f'{frontend_url}/integration/sentinel?error=Invalid%20state%20parameter')
        else:
            print("[SENTINEL] WARNING: State mismatch ignored (development mode)")
    
    if not code:
        print("[SENTINEL] ERROR: No authorization code received!")
        return redirect(f'{frontend_url}/integration/sentinel?error=Authorization%20code%20not%20found')
    
    try:
        print(f"[SENTINEL] Callback received with code: {code[:20]}...")
        print(f"[SENTINEL] State verification successful!")
        
        token_response = oauth_service.exchange_code_for_token(code)
        print("[SENTINEL] Token exchange successful!")
        
        request.session['sentinelAccessToken'] = token_response['access_token']
        request.session['sentinelRefreshToken'] = token_response.get('refresh_token')
        request.session['sentinelTokenExpiry'] = datetime.now().timestamp() * 1000 + (token_response['expires_in'] * 1000)
        request.session['isSentinelConnected'] = True
        request.session['authMethod'] = 'oauth'
        request.session['lastConnected'] = datetime.now().isoformat()
        request.session.modified = True  # Force session save
        
        print(f"[SENTINEL] Session data saved. Connected: {request.session.get('isSentinelConnected')}")
        
        # Parse ID token if available
        if token_response.get('id_token'):
            try:
                import jwt
                payload = jwt.decode(token_response['id_token'], options={"verify_signature": False})
                request.session['userInfo'] = {
                    'displayName': payload.get('name') or payload.get('preferred_username'),
                    'userPrincipalName': payload.get('preferred_username') or payload.get('email'),
                    'id': payload.get('oid') or payload.get('sub')
                }
            except Exception as e:
                print(f"Warning: Could not parse ID token: {e}")
                # Get user info from Graph API as fallback
                try:
                    auth_service = SentinelAuthService()
                    user_info = auth_service.get_user_info(token_response['access_token'])
                    request.session['userInfo'] = user_info
                except:
                    pass
        
        # Redirect to frontend Vue app
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')
        return redirect(f'{frontend_url}/integration/sentinel?connected=sentinel')
    except Exception as error:
        print(f"OAuth Error: {error}")
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')
        return redirect(f'{frontend_url}/integration/sentinel?error=Authentication%20failed')


@csrf_exempt
def sentinel_disconnect(request):
    """Disconnect from Sentinel"""
    request.session['isSentinelConnected'] = False
    request.session.pop('sentinelAccessToken', None)
    request.session.pop('sentinelRefreshToken', None)
    request.session.pop('sentinelTokenExpiry', None)
    request.session.pop('userInfo', None)
    
    # If it's an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'message': 'Disconnected from Microsoft Sentinel'
        })
    
    # Redirect to frontend
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')
    return redirect(f'{frontend_url}/integration/sentinel?disconnected=sentinel')


@csrf_exempt
@require_http_methods(["GET"])
def sentinel_check_status(request):
    """Check Sentinel connection status"""
    try:
        is_connected = request.session.get('isSentinelConnected', False)
        user_info = request.session.get('userInfo')
        
        print(f"[SENTINEL] Status check - Connected: {is_connected}, User: {user_info}")
        
        return JsonResponse({
            'connected': is_connected,
            'userInfo': user_info
        })
    except Exception as error:
        print(f"[SENTINEL] Status check error: {error}")
        return JsonResponse({'error': str(error)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_sentinel_alerts(request):
    """Get alerts/incidents from Microsoft Defender"""
    try:
        if not request.session.get('isSentinelConnected'):
            return JsonResponse({'error': 'Not connected to Microsoft Defender'}, status=401)
        
        access_token = get_user_access_token(request)
        defender_api = DefenderAPIService(access_token)
        
        filters = {}
        if request.GET.get('days'):
            filters['days'] = request.GET.get('days')
        if request.GET.get('severity'):
            filters['severity'] = request.GET.get('severity')
        if request.GET.get('status'):
            filters['status'] = request.GET.get('status')
        if request.GET.get('includeAll') == 'true':
            filters['includeAll'] = True
        
        incidents = defender_api.get_incidents(filters)
        
        # Debug logging
        print(f"[SENTINEL] Returning {len(incidents)} incidents")
        if incidents:
            print(f"[SENTINEL] Sample incident keys: {list(incidents[0].keys())}")
            print(f"[SENTINEL] Sample incident: {incidents[0]}")
        
        return JsonResponse({
            'success': True,
            'alerts': incidents,
            'incidents': incidents,  # Add this for frontend compatibility
            'totalCount': len(incidents),
            'lastUpdated': datetime.now().isoformat(),
            'source': 'microsoft-defender'
        })
    except Exception as error:
        return JsonResponse({
            'error': 'Failed to fetch incidents',
            'details': str(error)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_sentinel_stats(request):
    """Get statistics for Sentinel incidents"""
    try:
        if not request.session.get('isSentinelConnected'):
            return JsonResponse({'error': 'Not connected to Microsoft Defender'}, status=401)
        
        access_token = get_user_access_token(request)
        defender_api = DefenderAPIService(access_token)
        
        active_incidents = defender_api.get_incidents()
        all_incidents = defender_api.get_incidents({'includeAll': True})
        
        stats = {
            'total': len(active_incidents),
            'critical': len([a for a in active_incidents if a['severity'] == 'Critical']),
            'high': len([a for a in active_incidents if a['severity'] == 'High']),
            'medium': len([a for a in active_incidents if a['severity'] == 'Medium']),
            'low': len([a for a in active_incidents if a['severity'] == 'Low']),
            'bySeverity': {
                'critical': len([a for a in active_incidents if a['severity'] == 'Critical']),
                'high': len([a for a in active_incidents if a['severity'] == 'High']),
                'medium': len([a for a in active_incidents if a['severity'] == 'Medium']),
                'low': len([a for a in active_incidents if a['severity'] == 'Low'])
            }
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'lastUpdated': datetime.now().isoformat(),
            'source': 'microsoft-defender'
        })
    except Exception as error:
        return JsonResponse({
            'error': 'Failed to fetch statistics',
            'details': str(error)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_sentinel_incident(request, incident_id):
    """Get a specific incident with alerts"""
    try:
        if not request.session.get('isSentinelConnected'):
            return JsonResponse({'error': 'Not connected to Microsoft Defender'}, status=401)
        
        access_token = get_user_access_token(request)
        defender_api = DefenderAPIService(access_token)
        
        incident = defender_api.get_incident(incident_id)
        alerts = defender_api.get_incident_alerts(incident_id)
        
        return JsonResponse({
            'success': True,
            'incident': incident,
            'alerts': alerts,
            'source': 'microsoft-defender'
        })
    except Exception as error:
        return JsonResponse({
            'error': 'Failed to fetch incident details',
            'details': str(error)
        }, status=500)


# Global storage for webhook-received incidents
RECEIVED_INCIDENTS = []


@csrf_exempt
@require_http_methods(["POST"])
def receive_incident_webhook(request):
    """Receive incidents from Logic App webhook"""
    try:
        data = json.loads(request.body)
        
        # Handle Azure Logic App format
        if data.get('properties') and data['properties'].get('incidentNumber'):
            incident_data = {
                'incidentId': data['properties']['incidentNumber'],
                'title': data['properties'].get('title', 'Untitled Incident'),
                'severity': data['properties'].get('severity', 'Informational'),
                'description': data['properties'].get('description', 'No description available'),
                'createdTime': data['properties'].get('createdTimeUtc', datetime.now().isoformat()),
                'status': data['properties'].get('status', 'New'),
                'source': 'logic-app-webhook',
                'receivedAt': datetime.now().isoformat()
            }
        else:
            incident_data = {
                'incidentId': data.get('incidentId', f'webhook-{int(datetime.now().timestamp())}'),
                'title': data.get('title', 'Unknown Incident'),
                'severity': data.get('severity', 'Informational'),
                'description': data.get('description', 'No description available'),
                'createdTime': data.get('createdTime', datetime.now().isoformat()),
                'status': data.get('status', 'New'),
                'source': 'logic-app-custom',
                'receivedAt': datetime.now().isoformat()
            }
        
        RECEIVED_INCIDENTS.append(incident_data)
        
        return JsonResponse({
            'success': True,
            'message': 'Incident received',
            'incidentId': incident_data['incidentId']
        })
    except Exception as error:
        return JsonResponse({
            'success': False,
            'error': str(error)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_received_incidents(request):
    """Get incidents received via webhook"""
    return JsonResponse({
        'success': True,
        'totalCount': len(RECEIVED_INCIDENTS),
        'incidents': RECEIVED_INCIDENTS
    })


@csrf_exempt
@require_http_methods(["POST"])
def save_sentinel_incident(request):
    """Save a Sentinel incident to IntegrationDataList table"""
    try:
        print("[SENTINEL] ===== Save Incident Request Received =====")
        print(f"[SENTINEL] Request method: {request.method}")
        print(f"[SENTINEL] Request path: {request.path}")
        print(f"[SENTINEL] Content-Type: {request.content_type}")
        print(f"[SENTINEL] Session key: {request.session.session_key}")
        
        # Check if user is authenticated
        is_connected = request.session.get('isSentinelConnected', False)
        print(f"[SENTINEL] Is Sentinel connected: {is_connected}")
        
        if not is_connected:
            print("[SENTINEL] ERROR: Not connected to Microsoft Sentinel")
            return JsonResponse({
                'success': False,
                'error': 'Not connected to Microsoft Sentinel'
            }, status=401)
        
        # Parse request body
        try:
            data = json.loads(request.body)
            print(f"[SENTINEL] Request data keys: {list(data.keys())}")
        except json.JSONDecodeError as e:
            print(f"[SENTINEL] JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        incident_data = data.get('incident')
        user_id = data.get('user_id')
        
        print(f"[SENTINEL] User ID: {user_id}")
        print(f"[SENTINEL] Incident data present: {incident_data is not None}")
        
        if not incident_data:
            print("[SENTINEL] ERROR: No incident data provided")
            return JsonResponse({
                'success': False,
                'error': 'No incident data provided'
            }, status=400)
        
        # Get username from session or user_id
        username = None
        if user_id:
            try:
                user = Users.objects.get(UserId=user_id)
                username = user.UserName
                print(f"[SENTINEL] Found user: {username}")
            except Users.DoesNotExist:
                username = 'Unknown User'
                print(f"[SENTINEL] User not found, using: {username}")
        else:
            # Try to get from session
            user_info = request.session.get('userInfo')
            if user_info:
                username = user_info.get('displayName') or user_info.get('userPrincipalName')
                print(f"[SENTINEL] Username from session: {username}")
        
        # Save incident to database
        print("[SENTINEL] Calling save_incident_to_database...")
        result = save_incident_to_database(incident_data, user_id, username)
        print(f"[SENTINEL] Save result: {result}")
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=500)
            
    except Exception as error:
        print(f'[SENTINEL] ===== ERROR in save_sentinel_incident =====')
        print(f'[SENTINEL] Error: {error}')
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(error)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_saved_incidents(request):
    """Get all saved Sentinel incidents from IntegrationDataList"""
    try:
        user_id = request.GET.get('user_id')
        
        # Filter by source = 'Microsoft Sentinel'
        queryset = IntegrationDataList.objects.filter(source='Microsoft Sentinel')
        
        # Optionally filter by username if user_id provided
        if user_id:
            try:
                user = Users.objects.get(UserId=user_id)
                queryset = queryset.filter(username=user.UserName)
            except Users.DoesNotExist:
                pass
        
        # Order by time descending
        incidents = queryset.order_by('-time')
        
        # Serialize incidents
        incidents_list = []
        for incident in incidents:
            incidents_list.append({
                'id': incident.id,
                'heading': incident.heading,
                'source': incident.source,
                'username': incident.username,
                'time': incident.time.isoformat(),
                'data': incident.data,
                'metadata': incident.metadata,
                'created_at': incident.created_at.isoformat(),
                'updated_at': incident.updated_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'incidents': incidents_list,
            'count': len(incidents_list)
        })
        
    except Exception as error:
        print(f'[SENTINEL] Error in get_saved_incidents: {error}')
        return JsonResponse({
            'success': False,
            'error': str(error)
        }, status=500)

