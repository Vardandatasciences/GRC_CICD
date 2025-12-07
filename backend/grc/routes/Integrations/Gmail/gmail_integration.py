import os
import json
import logging
import base64
import mimetypes
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from grc.models import ExternalApplication, ExternalApplicationConnection, ExternalApplicationSyncLog, Users, IntegrationDataList

logger = logging.getLogger(__name__)

# Gmail OAuth Configuration
GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID', '485924947413-c0agg3va7u43ahf1cll50ekas5aba5a6.apps.googleusercontent.com')
GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET', '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')
GMAIL_REDIRECT_URI = os.getenv('GMAIL_REDIRECT_URI', 'http://localhost:8000/api/gmail/oauth-callback/')
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:8080')
GMAIL_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email'
]

# File-based OAuth state storage (simpler approach)
import tempfile
import pickle

OAUTH_STATES_FILE = os.path.join(tempfile.gettempdir(), 'gmail_oauth_states.pkl')

def store_oauth_state(state, user_id, flow_data):
    """Store OAuth state in temporary file"""
    try:
        # Load existing states
        states = {}
        if os.path.exists(OAUTH_STATES_FILE):
            try:
                with open(OAUTH_STATES_FILE, 'rb') as f:
                    states = pickle.load(f)
            except:
                states = {}
        
        # Add new state
        states[state] = {
            'user_id': user_id,
            'flow_data': flow_data,
            'created_at': timezone.now().isoformat()
        }
        
        # Save states
        with open(OAUTH_STATES_FILE, 'wb') as f:
            pickle.dump(states, f)
        
        logger.info(f"Stored OAuth state {state}")
        return True
    except Exception as e:
        logger.error(f"Error storing OAuth state: {str(e)}")
        return False

def get_oauth_state(state):
    """Retrieve OAuth state from temporary file"""
    try:
        logger.info(f"Looking for OAuth state: {state}")
        
        if not os.path.exists(OAUTH_STATES_FILE):
            logger.warning("OAuth states file not found")
            return None
        
        # Load states
        with open(OAUTH_STATES_FILE, 'rb') as f:
            states = pickle.load(f)
        
        logger.info(f"Found {len(states)} OAuth states")
        
        if state in states:
            stored_data = states[state]
            created_at = timezone.datetime.fromisoformat(stored_data['created_at'].replace('Z', '+00:00'))
            
            # Check if state is expired (10 minutes)
            if timezone.now() - created_at > timedelta(minutes=10):
                logger.warning(f"OAuth state {state} expired")
                del states[state]
                with open(OAUTH_STATES_FILE, 'wb') as f:
                    pickle.dump(states, f)
                return None
            
            logger.info(f"Found matching OAuth state: {state}")
            return stored_data
        
        logger.warning(f"No matching OAuth state found for: {state}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving OAuth state: {str(e)}")
        return None

def delete_oauth_state(state):
    """Delete OAuth state from temporary file"""
    try:
        if not os.path.exists(OAUTH_STATES_FILE):
            return False
        
        # Load states
        with open(OAUTH_STATES_FILE, 'rb') as f:
            states = pickle.load(f)
        
        # Remove state
        if state in states:
            del states[state]
            with open(OAUTH_STATES_FILE, 'wb') as f:
                pickle.dump(states, f)
            logger.info(f"Deleted OAuth state: {state}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error deleting OAuth state: {str(e)}")
        return False

def extract_attachments_from_message(service, message_id):
    """
    Extract attachments from a Gmail message
    """
    try:
        # Get the full message
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        attachments = []
        
        def process_part(part):
            """Recursively process message parts"""
            if 'parts' in part:
                for subpart in part['parts']:
                    process_part(subpart)
            
            # Check if this part has attachments
            if part.get('filename') and part.get('body', {}).get('attachmentId'):
                attachment_id = part['body']['attachmentId']
                filename = part['filename']
                mime_type = part.get('mimeType', 'application/octet-stream')
                size = part['body'].get('size', 0)
                
                # Get attachment data
                attachment_data = service.users().messages().attachments().get(
                    userId='me',
                    messageId=message_id,
                    id=attachment_id
                ).execute()
                
                # Decode attachment data
                file_data = base64.urlsafe_b64decode(attachment_data['data'])
                
                # Determine file extension
                file_extension = mimetypes.guess_extension(mime_type) or '.bin'
                
                attachment_info = {
                    'id': attachment_id,
                    'filename': filename,
                    'mime_type': mime_type,
                    'size': size,
                    'file_extension': file_extension,
                    'data': base64.b64encode(file_data).decode('utf-8'),  # Store as base64 for JSON
                    'is_image': mime_type.startswith('image/'),
                    'is_pdf': mime_type == 'application/pdf',
                    'is_document': mime_type in [
                        'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'application/vnd.ms-excel',
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'application/vnd.ms-powerpoint',
                        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    ]
                }
                
                attachments.append(attachment_info)
                logger.info(f"Extracted attachment: {filename} ({mime_type}, {size} bytes)")
        
        # Process the message payload
        payload = message.get('payload', {})
        process_part(payload)
        
        return attachments
        
    except Exception as e:
        logger.error(f"Error extracting attachments from message {message_id}: {str(e)}")
        return []

def clean_and_validate_json_data(data):
    """
    Clean and validate JSON data before saving to database
    """
    try:
        # Convert to JSON string and back to ensure it's valid
        json_string = json.dumps(data, indent=2, ensure_ascii=False)
        validated_data = json.loads(json_string)
        
        # Ensure all string values are properly encoded
        def clean_strings(obj):
            if isinstance(obj, dict):
                return {k: clean_strings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_strings(item) for item in obj]
            elif isinstance(obj, str):
                # Ensure string is properly encoded and doesn't contain control characters
                return obj.encode('utf-8').decode('utf-8')
            else:
                return obj
        
        cleaned_data = clean_strings(validated_data)
        return json.dumps(cleaned_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error cleaning JSON data: {str(e)}")
        # Return a minimal valid JSON structure if cleaning fails
        return json.dumps({
            "error": "Failed to process data",
            "timestamp": timezone.now().isoformat()
        }, indent=2)

def determine_file_type(mime_type):
    """
    Determine file type category from MIME type
    """
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type == 'application/pdf':
        return 'pdf'
    elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        return 'document'
    elif mime_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        return 'spreadsheet'
    elif mime_type in ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']:
        return 'presentation'
    elif mime_type.startswith('text/'):
        return 'text'
    elif mime_type.startswith('application/'):
        return 'application'
    else:
        return 'unknown'

def parse_email_field(email_field):
    """
    Parse email field to extract name, email, and domain
    """
    import re
    
    # Handle empty or default values
    if not email_field or email_field in ['Unknown Sender', 'Unknown Recipient', '']:
        return {
            'email': 'unknown@example.com',
            'name': 'Unknown',
            'domain': 'example.com'
        }
    
    # Pattern to match various email formats:
    # 1. "Name" <email@domain.com>
    # 2. Name <email@domain.com>
    # 3. email@domain.com
    # 4. "Name" email@domain.com
    email_pattern = r'(?:"?([^"<>]+)"?\s*)?<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?'
    
    match = re.search(email_pattern, email_field)
    if match:
        name_part = match.group(1).strip() if match.group(1) else ''
        email = match.group(2).strip()
        domain = email.split('@')[1] if '@' in email else ''
        
        # Clean up name (remove quotes and extra whitespace)
        name = name_part.strip('"').strip()
        
        # If name is empty or just whitespace, use email prefix
        if not name:
            name = email.split('@')[0]
        
        return {
            'email': email,
            'name': name,
            'domain': domain
        }
    
    # Fallback for malformed email - try to extract just the email part
    email_only_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    email_match = re.search(email_only_pattern, email_field)
    
    if email_match:
        email = email_match.group(1)
        domain = email.split('@')[1]
        return {
            'email': email,
            'name': email.split('@')[0],
            'domain': domain
        }
    
    # Final fallback
    return {
        'email': email_field,
        'name': email_field,
        'domain': 'unknown'
    }

def save_message_data_to_db(user_id, messages_with_attachments):
    """
    Save Gmail message data with attachments to database in structured format
    """
    try:
        user = Users.objects.get(UserId=user_id)
        gmail_app = ExternalApplication.objects.get(name='Gmail')
        connection = ExternalApplicationConnection.objects.filter(
            application=gmail_app,
            user=user,
            connection_status='active'
        ).first()
        
        if not connection:
            return {'success': False, 'error': 'Gmail connection not found'}
        
        # Structure the messages data properly
        structured_messages = []
        total_attachments = 0
        
        for idx, message in enumerate(messages_with_attachments):
            # Parse sender and receiver details
            from_field = message.get('from', 'Unknown Sender')
            to_field = message.get('to', 'Unknown Recipient')
            cc_field = message.get('cc', '')
            bcc_field = message.get('bcc', '')
            
            # Extract email and name from fields
            sender_details = parse_email_field(from_field)
            receiver_details = parse_email_field(to_field)
            cc_details = parse_email_field(cc_field) if cc_field else None
            bcc_details = parse_email_field(bcc_field) if bcc_field else None
            
            # Log parsed details for debugging
            logger.info(f"Message {idx + 1} - Sender: {sender_details}, Receiver: {receiver_details}")
            
            # Create structured message entry with comprehensive details
            structured_message = {
                'id': f'gmail_msg_{idx + 1}',  # Internal ID for database
                'message_id': message.get('id', f'msg_{idx}'),  # Gmail's internal message ID
                'gmail_message_id': message.get('id'),  # Original Gmail ID
                'subject': message.get('subject', 'No Subject'),
                'message_content': message.get('snippet', ''),
                'date': message.get('date', ''),
                'timestamp': timezone.now().isoformat(),
                
                # Sender details
                'sender': {
                    'email': sender_details['email'],
                    'name': sender_details['name'],
                    'full_address': from_field,
                    'domain': sender_details['domain']
                },
                
                # Receiver details
                'receiver': {
                    'email': receiver_details['email'],
                    'name': receiver_details['name'],
                    'full_address': to_field,
                    'domain': receiver_details['domain']
                },
                
                # CC and BCC details (if present)
                'cc': {
                    'email': cc_details['email'] if cc_details else '',
                    'name': cc_details['name'] if cc_details else '',
                    'full_address': cc_field,
                    'domain': cc_details['domain'] if cc_details else ''
                } if cc_details else None,
                
                'bcc': {
                    'email': bcc_details['email'] if bcc_details else '',
                    'name': bcc_details['name'] if bcc_details else '',
                    'full_address': bcc_field,
                    'domain': bcc_details['domain'] if bcc_details else ''
                } if bcc_details else None,
                
                # Attachment information
                'has_attachments': message.get('has_attachments', False),
                'attachment_count': message.get('attachment_count', 0),
                'attachments': [],
                
                # Metadata
                'extracted_at': timezone.now().isoformat(),
                'message_index': idx + 1,
                'status': 'unread',  # Default status
                'priority': 'normal'  # Default priority
            }
            
            # Process attachments if they exist
            if message.get('attachments'):
                for att_idx, attachment in enumerate(message['attachments']):
                    structured_attachment = {
                        'id': f'attachment_{idx + 1}_{att_idx + 1}',  # Internal attachment ID
                        'attachment_id': attachment.get('id', f'att_{idx}_{att_idx}'),
                        'gmail_attachment_id': attachment.get('id'),  # Original Gmail attachment ID
                        'filename': attachment.get('filename', 'unknown_file'),
                        'mime_type': attachment.get('mime_type', 'application/octet-stream'),
                        'size': attachment.get('size', 0),
                        'file_extension': attachment.get('file_extension', '.bin'),
                        'file_type': determine_file_type(attachment.get('mime_type', '')),
                        'is_image': attachment.get('is_image', False),
                        'is_pdf': attachment.get('is_pdf', False),
                        'is_document': attachment.get('is_document', False),
                        'data': attachment.get('data', ''),  # Base64 encoded data
                        'attachment_index': att_idx + 1,
                        'upload_date': timezone.now().isoformat(),
                        'status': 'available'
                    }
                    structured_message['attachments'].append(structured_attachment)
                    total_attachments += 1
            
            structured_messages.append(structured_message)
        
        # Create comprehensive data structure
        gmail_data_structure = {
            'gmail_messages': {
                'metadata': {
                    'extracted_at': timezone.now().isoformat(),
                    'total_messages': len(structured_messages),
                    'total_attachments': total_attachments,
                    'user_id': user_id,
                    'extraction_method': 'gmail_api_v1',
                    'message_limit': 10,
                    'include_attachments': True
                },
                'messages': structured_messages
            },
            'last_updated': timezone.now().isoformat(),
            'version': '1.0'
        }
        
        # Get current data and merge properly
        # Since projects_data is a JSONField, it returns a dict directly
        current_data = connection.projects_data or {}
        if isinstance(current_data, str):
            # Handle case where it might be stored as string
            try:
                current_data = json.loads(current_data)
            except (json.JSONDecodeError, TypeError):
                current_data = {}
        
        # Update with new Gmail data structure
        current_data.update(gmail_data_structure)
        
        # Save to database - JSONField handles serialization automatically
        # No need to use json.dumps() as Django JSONField stores it properly
        connection.projects_data = current_data
        connection.last_used = timezone.now()
        connection.save()
        
        logger.info(f"Saved {len(structured_messages)} structured Gmail messages with {total_attachments} attachments to database")
        logger.info("=== GMAIL DATA STRUCTURE JSON ===")
        logger.info(json.dumps(gmail_data_structure, indent=2))
        
        # Print to console as well
        print("\n" + "="*80)
        print("GMAIL DATA SAVED TO DATABASE")
        print("="*80)
        print(json.dumps(current_data, indent=2))
        print("="*80 + "\n")
        
        # Also log the final formatted JSON that was saved to database
        formatted_preview = json.dumps(current_data, indent=2)
        print("\n" + "="*80)
        print("FINAL JSON SAVED TO DATABASE (projects_data column)")
        print("="*80)
        print(formatted_preview[:1000] + "..." if len(formatted_preview) > 1000 else formatted_preview)
        print("="*80 + "\n")
        
        logger.info("=== FINAL DATABASE JSON (first 500 chars) ===")
        logger.info(formatted_preview[:500] + "..." if len(formatted_preview) > 500 else formatted_preview)
        
        return {
            'success': True, 
            'messages_saved': len(structured_messages),
            'attachments_saved': total_attachments,
            'data_structure': gmail_data_structure
        }
        
    except Exception as e:
        logger.error(f"Error saving structured message data to database: {str(e)}")
        return {'success': False, 'error': str(e)}

@csrf_exempt
@require_http_methods(["GET"])
def gmail_oauth_initiate(request):
    """
    Initiate Gmail OAuth flow
    """
    try:
        # Get user ID from request
        user_id = request.GET.get('user_id', 1)
        
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GMAIL_CLIENT_ID,
                    "client_secret": GMAIL_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GMAIL_REDIRECT_URI]
                }
            },
            scopes=GMAIL_SCOPES
        )
        flow.redirect_uri = GMAIL_REDIRECT_URI
        
        # Generate authorization URL with unique state
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=timezone.now().isoformat() + '_' + str(user_id)  # Unique state
        )
        
        # Store OAuth state in database (serialize flow for storage)
        flow_data = {
            'user_id': user_id,
            'created_at': timezone.now().isoformat(),
            'client_config': {
                'client_id': GMAIL_CLIENT_ID,
                'client_secret': GMAIL_CLIENT_SECRET,
                'redirect_uri': GMAIL_REDIRECT_URI,
                'scopes': GMAIL_SCOPES
            }
        }
        
        store_oauth_state(state, user_id, flow_data)
        
        return JsonResponse({
            'success': True,
            'auth_url': auth_url,
            'state': state
        })
        
    except Exception as e:
        logger.error(f"Gmail OAuth initiation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def gmail_oauth_callback(request):
    """
    Handle Gmail OAuth callback and create connection
    """
    try:
        # Handle both GET (from Google redirect) and POST (from frontend) requests
        if request.method == 'GET':
            # Extract parameters from URL query string
            state = request.GET.get('state')
            auth_code = request.GET.get('code')
            error = request.GET.get('error')
            
            if error:
                return JsonResponse({
                    'success': False,
                    'error': f'OAuth Error: {error}'
                }, status=400)
        else:
            # POST request from frontend
            data = json.loads(request.body)
            state = data.get('state')
            auth_code = data.get('auth_code')
        
        logger.info(f"OAuth callback received - Code: {auth_code[:10] if auth_code else 'None'}..., State: {state}")
        
        if not state or not auth_code:
            logger.error("Missing state or auth_code in callback")
            return JsonResponse({
                'success': False,
                'error': 'State and auth_code are required'
            }, status=400)
        
        # Retrieve stored OAuth state from database
        stored_state = get_oauth_state(state)
        if not stored_state:
            logger.error(f"Invalid or expired OAuth state: {state}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired OAuth state'
            }, status=400)
        
        user_id = stored_state['flow_data']['user_id']
        client_config = stored_state['flow_data']['client_config']
        logger.info(f"OAuth state verified for user: {user_id}")
        
        # Recreate the flow from stored configuration
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_config['client_id'],
                    "client_secret": client_config['client_secret'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [client_config['redirect_uri']]
                }
            },
            scopes=client_config['scopes']
        )
        flow.redirect_uri = client_config['redirect_uri']
        
        # Exchange authorization code for tokens
        try:
            # Fetch token with the authorization code
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            logger.info(f"Successfully exchanged authorization code for tokens")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Token exchange failed: {error_msg}")
            
            # Clean up the OAuth state since the code failed
            delete_oauth_state(state)
            
            # Handle common OAuth errors
            if "invalid_grant" in error_msg or "invalid_request" in error_msg:
                return JsonResponse({
                    'success': False,
                    'error': 'Authorization code expired or already used. Please try connecting again.',
                    'error_type': 'expired_code'
                })
            elif "invalid_client" in error_msg:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid client credentials. Please check configuration.',
                    'error_type': 'invalid_client'
                })
            elif "access_denied" in error_msg:
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied. Please grant all required permissions.',
                    'error_type': 'access_denied'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'OAuth token exchange failed: {error_msg}',
                    'error_type': 'token_exchange_failed'
                })
        
        # Get user info from Google
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # Save Gmail connection to database
        result = save_gmail_connection(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expires_at=credentials.expiry,
            user_info=user_info
        )
        
        # Clean up stored OAuth state from database
        delete_oauth_state(state)
        
        if result['success']:
            if request.method == 'GET':
                # For GET requests (Google redirect), return HTML page that redirects to frontend
                from django.http import HttpResponse
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Gmail OAuth Success</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                        .success {{ color: green; }}
                        .loading {{ color: blue; }}
                    </style>
                </head>
                <body>
                    <h2 class="success">✅ Gmail Connected Successfully!</h2>
                    <p class="loading">Redirecting to your GRC dashboard...</p>
                    <script>
                          setTimeout(function() {{
                              window.location.href = '{FRONTEND_BASE_URL}/integrations/gmail?oauth_success=true&user_id={user_id}';
                          }}, 2000);
                    </script>
                </body>
                </html>
                """
                return HttpResponse(html_content)
            else:
                # For POST requests (from frontend), return JSON
                return JsonResponse({
                    'success': True,
                    'message': 'Gmail connected successfully',
                    'connection_id': result.get('connection_id'),
                    'user_info': user_info
                })
        else:
            if request.method == 'GET':
                # For GET requests, return HTML page with error
                from django.http import HttpResponse
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Gmail OAuth Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                        .error {{ color: red; }}
                        .loading {{ color: blue; }}
                    </style>
                </head>
                <body>
                    <h2 class="error">❌ Gmail Connection Failed</h2>
                    <p>Error: {result["error"]}</p>
                    <p class="loading">Redirecting back to integrations...</p>
                    <script>
                        setTimeout(function() {{
                            window.location.href = 'http://localhost:8080/integrations/external?oauth_error={result["error"]}';
                        }}, 3000);
                    </script>
                </body>
                </html>
                """
                return HttpResponse(html_content)
            else:
                # For POST requests, return JSON error
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Gmail OAuth callback error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def save_gmail_connection(user_id, access_token, refresh_token, token_expires_at, user_info):
    """
    Save Gmail connection to database
    """
    try:
        # Get or create Gmail external application
        gmail_app, created = ExternalApplication.objects.get_or_create(
            name='Gmail',
            defaults={
                'description': 'Google Gmail Integration',
                'category': 'Communication',
                'type': 'OAuth',
                'version': '1.0',
                'is_active': True,
                'status': 'available'
            }
        )
        
        # Get user
        try:
            user = Users.objects.get(UserId=user_id)
        except Users.DoesNotExist:
            return {'success': False, 'error': 'User not found'}
        
        with transaction.atomic():
            # Create or update connection
            connection, created = ExternalApplicationConnection.objects.get_or_create(
                application=gmail_app,
                user=user,
                defaults={
                    'connection_token': access_token,
                    'refresh_token': refresh_token,
                    'token_expires_at': token_expires_at,
                    'connection_status': 'active',
                    'last_used': timezone.now(),
                    'projects_data': {
                        'user_info': user_info,
                        'connected_at': timezone.now().isoformat()
                    }
                }
            )
            
            if not created:
                # Update existing connection
                connection.connection_token = access_token
                connection.refresh_token = refresh_token
                connection.token_expires_at = token_expires_at
                connection.connection_status = 'active'
                connection.last_used = timezone.now()
                connection.projects_data = {
                    'user_info': user_info,
                    'connected_at': timezone.now().isoformat()
                }
                connection.save()
            
            # Update application status
            gmail_app.status = 'connected'
            gmail_app.last_sync = timezone.now()
            gmail_app.save()
            
            # Log the connection
            ExternalApplicationSyncLog.objects.create(
                application=gmail_app,
                user=user,
                sync_type='manual',
                sync_status='success',
                records_synced=1,
                sync_started_at=timezone.now(),
                sync_completed_at=timezone.now(),
                error_message=f'Gmail OAuth connection established for {user_info.get("email", "unknown")}'
            )
        
        return {
            'success': True,
            'connection_id': connection.id,
            'created': created
        }
        
    except Exception as e:
        logger.error(f"Error saving Gmail connection: {str(e)}")
        return {'success': False, 'error': str(e)}

@csrf_exempt
@require_http_methods(["GET"])
def get_gmail_connection_status(request):
    """
    Get Gmail connection status for user
    """
    try:
        # Try to get user_id from JWT token first, then from query param
        user_id = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            logger.info(f"Using authenticated user ID: {user_id}")
        else:
            # Fallback to query parameter
            user_id = request.GET.get('user_id', 1)
            logger.info(f"Using query parameter user ID: {user_id}")
        
        try:
            user = Users.objects.get(UserId=user_id)
            gmail_app = ExternalApplication.objects.get(name='Gmail')
            connection = ExternalApplicationConnection.objects.filter(
                application=gmail_app,
                user=user,
                connection_status='active'
            ).first()
            
            if connection:
                # Check if token is still valid
                if connection.token_expires_at and connection.token_expires_at <= timezone.now():
                    # Try to refresh token
                    refreshed = refresh_gmail_token(connection)
                    if not refreshed:
                        connection.connection_status = 'expired'
                        connection.save()
                        return JsonResponse({
                            'success': True,
                            'connected': False,
                            'status': 'expired',
                            'message': 'Gmail connection expired'
                        })
                
                # Check if there's stored data
                projects_data = connection.projects_data or {}
                if isinstance(projects_data, str):
                    try:
                        projects_data = json.loads(projects_data)
                    except (json.JSONDecodeError, TypeError):
                        projects_data = {}
                
                has_stored_data = 'gmail_messages' in projects_data
                messages_count = 0
                attachments_count = 0
                stored_data = None
                user_info = projects_data.get('user_info', {})
                
                if has_stored_data:
                    gmail_data = projects_data.get('gmail_messages', {})
                    messages_count = gmail_data.get('metadata', {}).get('total_messages', 0)
                    attachments_count = gmail_data.get('metadata', {}).get('total_attachments', 0)
                    stored_data = {
                        'metadata': gmail_data.get('metadata', {}),
                        'messages': gmail_data.get('messages', [])
                    }
                
                return JsonResponse({
                    'success': True,
                    'connected': True,
                    'status': 'active',
                    'connection_id': connection.id,
                    'last_used': connection.last_used,
                    'user_info': user_info,
                    'has_stored_data': has_stored_data,
                    'messages_count': messages_count,
                    'attachments_count': attachments_count,
                    'stored_data': stored_data
                })
            else:
                return JsonResponse({
                    'success': True,
                    'connected': False,
                    'status': 'not_connected',
                    'message': 'Gmail not connected'
                })
                
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist):
            return JsonResponse({
                'success': True,
                'connected': False,
                'status': 'not_connected',
                'message': 'Gmail application not found'
            })
            
    except Exception as e:
        logger.error(f"Error checking Gmail connection status: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def refresh_gmail_token(connection):
    """
    Refresh Gmail access token
    """
    try:
        if not connection.refresh_token:
            return False
        
        credentials = Credentials(
            token=connection.connection_token,
            refresh_token=connection.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=GMAIL_CLIENT_ID,
            client_secret=GMAIL_CLIENT_SECRET
        )
        
        # Refresh the token
        credentials.refresh(Request())
        
        # Update connection with new token
        connection.connection_token = credentials.token
        connection.token_expires_at = credentials.expiry
        connection.last_used = timezone.now()
        connection.save()
        
        return True
        
    except Exception as e:
        logger.error(f"Error refreshing Gmail token: {str(e)}")
        return False

@csrf_exempt
@require_http_methods(["GET"])
def test_gmail_headers(request):
    """
    Test endpoint to debug Gmail headers
    """
    try:
        user_id = request.GET.get('user_id', 1)
        
        # Get user's Gmail connection
        try:
            user = Users.objects.get(UserId=user_id)
            gmail_app = ExternalApplication.objects.get(name='Gmail')
            connection = ExternalApplicationConnection.objects.filter(
                application=gmail_app,
                user=user,
                connection_status='active'
            ).first()
            
            if not connection:
                return JsonResponse({
                    'success': False,
                    'error': 'Gmail not connected'
                }, status=401)
            
            # Check and refresh token if needed
            if connection.token_expires_at and connection.token_expires_at <= timezone.now():
                if not refresh_gmail_token(connection):
                    return JsonResponse({
                        'success': False,
                        'error': 'Gmail connection expired'
                    }, status=401)
            
            # Build Gmail service
            credentials = Credentials(
                token=connection.connection_token,
                refresh_token=connection.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=GMAIL_CLIENT_ID,
                client_secret=GMAIL_CLIENT_SECRET
            )
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Get just one message for testing
            results = service.users().messages().list(
                userId='me',
                maxResults=1,
                q='in:inbox'
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                return JsonResponse({
                    'success': False,
                    'error': 'No messages found'
                })
            
            # Get the first message with full headers
            msg = service.users().messages().get(
                userId='me',
                id=messages[0]['id'],
                format='full'  # Get full message, not just metadata
            ).execute()
            
            # Extract all headers
            headers = msg['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            return JsonResponse({
                'success': True,
                'message_id': messages[0]['id'],
                'all_headers': header_dict,
                'from': header_dict.get('From', 'NOT_FOUND'),
                'to': header_dict.get('To', 'NOT_FOUND'),
                'cc': header_dict.get('Cc', 'NOT_FOUND'),
                'bcc': header_dict.get('Bcc', 'NOT_FOUND'),
                'subject': header_dict.get('Subject', 'NOT_FOUND')
            })
            
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'User or Gmail application not found'
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error testing Gmail headers: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_gmail_messages(request):
    """
    Get Gmail messages with attachments for authenticated user
    """
    try:
        # Try to get user_id from JWT token first, then from query param
        user_id = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            logger.info(f"Using authenticated user ID: {user_id}")
        else:
            # Fallback to query parameter
            user_id = request.GET.get('user_id', 1)
            logger.info(f"Using query parameter user ID: {user_id}")
            
        include_attachments = request.GET.get('include_attachments', 'true').lower() == 'true'
        
        # Get user's Gmail connection
        try:
            user = Users.objects.get(UserId=user_id)
            gmail_app = ExternalApplication.objects.get(name='Gmail')
            connection = ExternalApplicationConnection.objects.filter(
                application=gmail_app,
                user=user,
                connection_status='active'
            ).first()
            
            if not connection:
                return JsonResponse({
                    'success': False,
                    'error': 'Gmail not connected'
                }, status=401)
            
            # Check and refresh token if needed
            if connection.token_expires_at and connection.token_expires_at <= timezone.now():
                if not refresh_gmail_token(connection):
                    return JsonResponse({
                        'success': False,
                        'error': 'Gmail connection expired'
                    }, status=401)
            
            # Build Gmail service
            credentials = Credentials(
                token=connection.connection_token,
                refresh_token=connection.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=GMAIL_CLIENT_ID,
                client_secret=GMAIL_CLIENT_SECRET
            )
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Get messages
            results = service.users().messages().list(
                userId='me',
                maxResults=10,
                q='in:inbox'
            ).execute()
            
            messages = results.get('messages', [])
            message_details = []
            
            for message in messages:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'  # Use 'full' instead of 'metadata' to get all headers
                ).execute()
                
                headers = msg['payload'].get('headers', [])
                
                # Create a dictionary for easier header lookup
                header_dict = {h['name']: h['value'] for h in headers}
                
                # Extract headers with better fallback handling
                subject = header_dict.get('Subject', 'No Subject')
                sender = header_dict.get('From', 'Unknown Sender')
                recipient = header_dict.get('To', 'Unknown Recipient')
                cc = header_dict.get('Cc', '')
                bcc = header_dict.get('Bcc', '')
                date = header_dict.get('Date', '')
                
                # Log extracted values for debugging
                logger.info(f"Message {message['id']} - From: {sender}, To: {recipient}, CC: {cc}, BCC: {bcc}")
                
                message_info = {
                    'id': message['id'],
                    'subject': subject,
                    'from': sender,
                    'to': recipient,
                    'cc': cc,
                    'bcc': bcc,
                    'date': date,
                    'snippet': msg.get('snippet', ''),
                    'attachments': []
                }
                
                # Extract attachments if requested
                if include_attachments:
                    attachments = extract_attachments_from_message(service, message['id'])
                    message_info['attachments'] = attachments
                    message_info['has_attachments'] = len(attachments) > 0
                    message_info['attachment_count'] = len(attachments)
                else:
                    message_info['has_attachments'] = False
                    message_info['attachment_count'] = 0
                
                message_details.append(message_info)
            
            # Always save message data to database (with or without attachments)
            save_result = save_message_data_to_db(user_id, message_details)
            if not save_result['success']:
                logger.warning(f"Failed to save message data: {save_result['error']}")
                # Continue with the response even if saving failed
            else:
                logger.info(f"Successfully saved {save_result['messages_saved']} messages with {save_result['attachments_saved']} attachments to database")
            
            # Update last used
            connection.last_used = timezone.now()
            connection.save()
            
            return JsonResponse({
                'success': True,
                'messages': message_details,
                'total_messages': len(message_details),
                'total_attachments': sum(msg.get('attachment_count', 0) for msg in message_details),
                'auto_saved': save_result.get('success', False),
                'save_message': 'Messages automatically saved to database' if save_result.get('success', False) else 'Failed to save messages to database'
            })
            
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'User or Gmail application not found'
            }, status=404)
            
    except HttpError as e:
        logger.error(f"Gmail API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Gmail API error: {str(e)}'
        }, status=500)
    except Exception as e:
        logger.error(f"Error fetching Gmail messages: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_calendar_events(request):
    """
    Get Google Calendar events for authenticated user
    """
    try:
        # Try to get user_id from JWT token first, then from query param
        user_id = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            logger.info(f"Calendar: Using authenticated user ID: {user_id}")
        else:
            # Fallback to query parameter
            user_id = request.GET.get('user_id', 1)
            logger.info(f"Calendar: Using query parameter user ID: {user_id}")
        
        # Get user's Gmail connection (same credentials work for Calendar)
        try:
            user = Users.objects.get(UserId=user_id)
            gmail_app = ExternalApplication.objects.get(name='Gmail')
            connection = ExternalApplicationConnection.objects.filter(
                application=gmail_app,
                user=user,
                connection_status='active'
            ).first()
            
            if not connection:
                logger.error(f"No active Gmail connection found for user {user_id}")
                return JsonResponse({
                    'success': False,
                    'error': 'Gmail not connected. Please connect your Gmail account first.'
                }, status=401)
            
            logger.info(f"Found Gmail connection for user {user_id}")
            
            # Check and refresh token if needed
            if connection.token_expires_at and connection.token_expires_at <= timezone.now():
                logger.info(f"Token expired for user {user_id}, attempting refresh")
                if not refresh_gmail_token(connection):
                    logger.error(f"Failed to refresh token for user {user_id}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Gmail connection expired and could not be refreshed. Please reconnect.'
                    }, status=401)
                logger.info(f"Token refreshed successfully for user {user_id}")
            
            # Build Calendar service
            credentials = Credentials(
                token=connection.connection_token,
                refresh_token=connection.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=GMAIL_CLIENT_ID,
                client_secret=GMAIL_CLIENT_SECRET,
                scopes=GMAIL_SCOPES
            )
            
            logger.info("Building Google Calendar service")
            service = build('calendar', 'v3', credentials=credentials)
            
            # Get events - fetch from past 7 days to future 30 days
            time_min = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
            time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
            
            logger.info(f"Fetching calendar events from {time_min} to {time_max}")
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} calendar events")
            
            event_details = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                event_detail = {
                    'id': event['id'],
                    'title': event.get('summary', 'No Title'),
                    'start': start,
                    'end': end,
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'status': event.get('status', ''),
                    'htmlLink': event.get('htmlLink', ''),
                    'created': event.get('created', ''),
                    'updated': event.get('updated', ''),
                    'creator': event.get('creator', {}),
                    'organizer': event.get('organizer', {}),
                    'attendees': event.get('attendees', [])
                }
                
                event_details.append(event_detail)
                logger.info(f"Event: {event_detail['title']} at {start}")
            
            # Update last used
            connection.last_used = timezone.now()
            connection.save()
            
            logger.info(f"Successfully fetched {len(event_details)} calendar events for user {user_id}")
            
            return JsonResponse({
                'success': True,
                'events': event_details,
                'total_events': len(event_details),
                'message': f'Successfully fetched {len(event_details)} calendar events'
            })
            
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist) as e:
            logger.error(f"User or Gmail application not found: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'User or Gmail application not found'
            }, status=404)
            
    except HttpError as e:
        error_details = str(e)
        logger.error(f"Calendar API error: {error_details}")
        
        # Check if it's a scope/permission error
        if 'insufficient permissions' in error_details.lower() or 'access_denied' in error_details.lower():
            return JsonResponse({
                'success': False,
                'error': 'Insufficient permissions to access Google Calendar. Please reconnect your Gmail account and grant calendar permissions.',
                'error_type': 'permission_denied'
            }, status=403)
        else:
            return JsonResponse({
                'success': False,
                'error': f'Calendar API error: {error_details}',
                'error_type': 'api_error'
            }, status=500)
    except Exception as e:
        logger.error(f"Error fetching calendar events: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch calendar events: {str(e)}',
            'error_type': 'general_error'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def download_attachment(request):
    """
    Download a specific attachment from Gmail
    """
    try:
        # Try to get user_id from JWT token first, then from query param
        user_id = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            logger.info(f"Using authenticated user ID: {user_id}")
        else:
            # Fallback to query parameter
            user_id = request.GET.get('user_id', 1)
            logger.info(f"Using query parameter user ID: {user_id}")
            
        message_id = request.GET.get('message_id')
        attachment_id = request.GET.get('attachment_id')
        
        if not message_id or not attachment_id:
            return JsonResponse({
                'success': False,
                'error': 'message_id and attachment_id are required'
            }, status=400)
        
        # Get user's Gmail connection
        try:
            user = Users.objects.get(UserId=user_id)
            gmail_app = ExternalApplication.objects.get(name='Gmail')
            connection = ExternalApplicationConnection.objects.filter(
                application=gmail_app,
                user=user,
                connection_status='active'
            ).first()
            
            if not connection:
                return JsonResponse({
                    'success': False,
                    'error': 'Gmail not connected'
                }, status=401)
            
            # Check and refresh token if needed
            if connection.token_expires_at and connection.token_expires_at <= timezone.now():
                if not refresh_gmail_token(connection):
                    return JsonResponse({
                        'success': False,
                        'error': 'Gmail connection expired'
                    }, status=401)
            
            # Build Gmail service
            credentials = Credentials(
                token=connection.connection_token,
                refresh_token=connection.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=GMAIL_CLIENT_ID,
                client_secret=GMAIL_CLIENT_SECRET
            )
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Get attachment data
            attachment_data = service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            # Decode attachment data
            file_data = base64.urlsafe_b64decode(attachment_data['data'])
            
            # Get message to find attachment filename
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            filename = 'attachment'
            mime_type = 'application/octet-stream'
            
            def find_attachment_info(part):
                if part.get('body', {}).get('attachmentId') == attachment_id:
                    return part.get('filename', 'attachment'), part.get('mimeType', 'application/octet-stream')
                
                if 'parts' in part:
                    for subpart in part['parts']:
                        result = find_attachment_info(subpart)
                        if result[0] != 'attachment':
                            return result
                
                return 'attachment', 'application/octet-stream'
            
            filename, mime_type = find_attachment_info(message.get('payload', {}))
            
            # Return attachment data
            return JsonResponse({
                'success': True,
                'filename': filename,
                'mime_type': mime_type,
                'size': len(file_data),
                'data': base64.b64encode(file_data).decode('utf-8')
            })
            
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'User or Gmail application not found'
            }, status=404)
            
    except HttpError as e:
        logger.error(f"Gmail API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Gmail API error: {str(e)}'
        }, status=500)
    except Exception as e:
        logger.error(f"Error downloading attachment: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_stored_gmail_data_formatted(request):
    """
    Get stored Gmail data in a formatted, readable JSON structure
    """
    try:
        # Try to get user_id from JWT token first, then from query param
        user_id = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            logger.info(f"Using authenticated user ID: {user_id}")
        else:
            # Fallback to query parameter
            user_id = request.GET.get('user_id', 1)
            logger.info(f"Using query parameter user ID: {user_id}")
        
        try:
            user = Users.objects.get(UserId=user_id)
            gmail_app = ExternalApplication.objects.get(name='Gmail')
            connection = ExternalApplicationConnection.objects.filter(
                application=gmail_app,
                user=user,
                connection_status='active'
            ).first()
            
            if not connection:
                return JsonResponse({
                    'success': False,
                    'error': 'Gmail not connected'
                }, status=401)
            
            # Get stored data
            projects_data = connection.projects_data or '{}'
            
            # Try to parse the JSON data
            try:
                parsed_data = json.loads(projects_data)
            except json.JSONDecodeError as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid JSON data in database: {str(e)}',
                    'raw_data': projects_data[:500] + "..." if len(projects_data) > 500 else projects_data
                }, status=500)
            
            if 'gmail_messages' not in parsed_data:
                return JsonResponse({
                    'success': False,
                    'error': 'No stored Gmail data found'
                }, status=404)
            
            gmail_data = parsed_data.get('gmail_messages', {})
            
            # Create a formatted response
            response_data = {
                'success': True,
                'data': {
                    'metadata': gmail_data.get('metadata', {}),
                    'messages': gmail_data.get('messages', [])
                },
                'raw_json_size': len(projects_data),
                'parsed_successfully': True
            }
            
            logger.info("=== FORMATTED STORED GMAIL DATA RETRIEVED ===")
            logger.info(json.dumps(response_data, indent=2))
            
            return JsonResponse(response_data)
            
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'User or Gmail application not found'
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error retrieving formatted stored Gmail data: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_stored_gmail_data(request):
    """
    Get stored Gmail data in structured format
    """
    try:
        # Try to get user_id from JWT token first, then from query param
        user_id = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            logger.info(f"Using authenticated user ID: {user_id}")
        else:
            # Fallback to query parameter
            user_id = request.GET.get('user_id', 1)
            logger.info(f"Using query parameter user ID: {user_id}")
        
        try:
            user = Users.objects.get(UserId=user_id)
            gmail_app = ExternalApplication.objects.get(name='Gmail')
            connection = ExternalApplicationConnection.objects.filter(
                application=gmail_app,
                user=user,
                connection_status='active'
            ).first()
            
            if not connection:
                return JsonResponse({
                    'success': False,
                    'error': 'Gmail not connected'
                }, status=401)
            
            # Get stored data - JSONField returns dict directly
            projects_data = connection.projects_data or {}
            if isinstance(projects_data, str):
                # Handle legacy string format
                try:
                    projects_data = json.loads(projects_data)
                except (json.JSONDecodeError, TypeError):
                    projects_data = {}
            
            if 'gmail_messages' not in projects_data:
                return JsonResponse({
                    'success': False,
                    'error': 'No stored Gmail data found'
                }, status=404)
            
            gmail_data = projects_data.get('gmail_messages', {})
            
            response_data = {
                'success': True,
                'data': {
                    'metadata': gmail_data.get('metadata', {}),
                    'messages': gmail_data.get('messages', [])
                }
            }
            
            logger.info("=== STORED GMAIL DATA RETRIEVED ===")
            logger.info(json.dumps(response_data, indent=2))
            print("\n" + "="*80)
            print("STORED GMAIL DATA RETRIEVED")
            print("="*80)
            print(json.dumps(response_data, indent=2))
            print("="*80 + "\n")
            
            return JsonResponse(response_data)
            
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'User or Gmail application not found'
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error retrieving stored Gmail data: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_gmail_data_to_db(request):
    """
    Manually save Gmail data to database
    """
    try:
        data = json.loads(request.body)
        
        # Try to get user_id from JWT token first, then from request body
        user_id = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            logger.info(f"Using authenticated user ID: {user_id}")
        else:
            # Fallback to request body
            user_id = data.get('user_id', 1)
            logger.info(f"Using request body user ID: {user_id}")
        
        # Get messages data from request
        messages_data = data.get('messages', [])
        
        if not messages_data:
            return JsonResponse({
                'success': False,
                'error': 'No messages data provided'
            }, status=400)
        
        # Save to database
        save_result = save_message_data_to_db(user_id, messages_data)
        
        if save_result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Gmail data saved to database successfully',
                'messages_saved': save_result['messages_saved'],
                'attachments_saved': save_result['attachments_saved']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': save_result['error']
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error saving Gmail data to database: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def disconnect_gmail(request):
    """
    Disconnect Gmail integration
    """
    try:
        data = json.loads(request.body)
        
        # Try to get user_id from JWT token first, then from request body
        user_id = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            logger.info(f"Using authenticated user ID: {user_id}")
        else:
            # Fallback to request body
            user_id = data.get('user_id', 1)
            logger.info(f"Using request body user ID: {user_id}")
        
        try:
            user = Users.objects.get(UserId=user_id)
            gmail_app = ExternalApplication.objects.get(name='Gmail')
            connection = ExternalApplicationConnection.objects.filter(
                application=gmail_app,
                user=user
            ).first()
            
            if connection:
                connection.connection_status = 'revoked'
                connection.save()
                
                # Log the disconnection
                ExternalApplicationSyncLog.objects.create(
                    application=gmail_app,
                    user=user,
                    sync_type='manual',
                    sync_status='success',
                    records_synced=0,
                    sync_started_at=timezone.now(),
                    sync_completed_at=timezone.now(),
                    error_message='Gmail connection disconnected'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Gmail disconnected successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Gmail connection not found'
                }, status=404)
                
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'User or Gmail application not found'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_gmail_message_to_integration_list(request):
    """
    Save individual Gmail message data to integration_data_list table
    This endpoint is called when the plus button is clicked on a message
    """
    try:
        data = json.loads(request.body)
        
        # Try to get user_id from JWT token first, then from request body
        user_id = None
        username = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            username = request.user.UserName
            logger.info(f"Using authenticated user ID: {user_id}")
        else:
            # Fallback to request body
            user_id = data.get('user_id', 1)
            logger.info(f"Using request body user ID: {user_id}")
            
            # Get username from user_id
            try:
                user = Users.objects.get(UserId=user_id)
                username = user.UserName
            except Users.DoesNotExist:
                username = 'unknown_user'
        
        # Get message data from request
        message_data = data.get('message_data')
        
        if not message_data:
            return JsonResponse({
                'success': False,
                'error': 'No message data provided'
            }, status=400)
        
        # Extract key fields from message data
        subject = message_data.get('subject', 'No Subject')
        message_date = message_data.get('date')
        message_id = message_data.get('id', '')
        
        # Parse message date
        if message_date:
            try:
                # Try to parse different date formats
                from dateutil import parser
                parsed_date = parser.parse(message_date)
                # Remove timezone info if present to avoid MySQL timezone issues
                if parsed_date.tzinfo is not None:
                    parsed_date = parsed_date.replace(tzinfo=None)
            except:
                # Use naive datetime (without timezone)
                parsed_date = datetime.now()
        else:
            # Use naive datetime (without timezone)
            parsed_date = datetime.now()
        
        # Prepare metadata
        metadata = {
            'message_id': message_id,
            'user_id': user_id,
            'source_type': 'gmail',
            'saved_at': datetime.now().isoformat(),
            'sender': message_data.get('sender_details', {}),
            'receiver': message_data.get('receiver_details', {}),
            'has_attachments': message_data.get('has_attachments', False),
            'attachment_count': message_data.get('attachment_count', 0)
        }
        
        # Create the integration data list entry
        integration_entry = IntegrationDataList.objects.create(
            heading=subject,
            source='Gmail',
            username=username,
            time=parsed_date,
            data=message_data,  # Store complete message data as JSON
            metadata=metadata
        )
        
        logger.info(f"Saved Gmail message '{subject}' to integration_data_list (ID: {integration_entry.id})")
        
        return JsonResponse({
            'success': True,
            'message': 'Gmail message saved to integration list successfully',
            'integration_id': integration_entry.id,
            'heading': subject
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error saving Gmail message to integration list: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_calendar_event_to_integration_list(request):
    """
    Save individual Google Calendar event data to integration_data_list table
    This endpoint is called when the plus button is clicked on a calendar event
    """
    try:
        data = json.loads(request.body)
        
        # Try to get user_id from JWT token first, then from request body
        user_id = None
        username = None
        
        # Check if user is authenticated via JWT
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = request.user.UserId
            username = request.user.UserName
            logger.info(f"Using authenticated user ID: {user_id}")
        else:
            # Fallback to request body
            user_id = data.get('user_id', 1)
            logger.info(f"Using request body user ID: {user_id}")
            
            # Get username from user_id
            try:
                user = Users.objects.get(UserId=user_id)
                username = user.UserName
            except Users.DoesNotExist:
                username = 'unknown_user'
        
        # Get event data from request
        event_data = data.get('event_data')
        
        if not event_data:
            return JsonResponse({
                'success': False,
                'error': 'No event data provided'
            }, status=400)
        
        # Extract key fields from event data
        event_title = event_data.get('title', 'No Title')
        event_start = event_data.get('start')
        event_id = event_data.get('id', '')
        
        # Parse event start date
        if event_start:
            try:
                # Try to parse different date formats
                from dateutil import parser
                parsed_date = parser.parse(event_start)
                # Remove timezone info if present to avoid MySQL timezone issues
                if parsed_date.tzinfo is not None:
                    parsed_date = parsed_date.replace(tzinfo=None)
            except:
                # Use naive datetime (without timezone)
                parsed_date = datetime.now()
        else:
            # Use naive datetime (without timezone)
            parsed_date = datetime.now()
        
        # Prepare metadata
        metadata = {
            'event_id': event_id,
            'user_id': user_id,
            'source_type': 'google_calendar',
            'saved_at': datetime.now().isoformat(),
            'location': event_data.get('location', ''),
            'status': event_data.get('status', ''),
            'has_attendees': len(event_data.get('attendees', [])) > 0,
            'attendees_count': len(event_data.get('attendees', [])),
            'organizer': event_data.get('organizer', {}),
            'html_link': event_data.get('htmlLink', '')
        }
        
        # Create the integration data list entry
        integration_entry = IntegrationDataList.objects.create(
            heading=event_title,
            source='Google Calendar',
            username=username,
            time=parsed_date,
            data=event_data,  # Store complete event data as JSON
            metadata=metadata
        )
        
        logger.info(f"Saved calendar event '{event_title}' to integration_data_list (ID: {integration_entry.id})")
        
        return JsonResponse({
            'success': True,
            'message': 'Calendar event saved to integration list successfully',
            'integration_id': integration_entry.id,
            'heading': event_title
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error saving calendar event to integration list: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
