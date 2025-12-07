"""
AI Audit API Endpoints
Clean, single implementation for AI audit document upload and processing
"""

import logging
import json
import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn

from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.files.storage import default_storage
from django.conf import settings

from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
from rest_framework.response import Response
from ...rbac.permissions import AuditConductPermission, AuditReviewPermission
from ...rbac.decorators import audit_conduct_required
from ...authentication import verify_jwt_token

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

logger = logging.getLogger(__name__)


def call_ai_api(prompt, audit_id=None, document_id=None, model_type='compliance'):
    """
    AI API call using OpenAI for all processing.
    
    Args:
        prompt: The prompt to send to the AI
        audit_id: Audit ID for deterministic seeds
        document_id: Document ID for deterministic seeds
        model_type: Type of model call ('compliance', 'analysis', 'recommendations')
    
    Returns:
        str: AI response text
    """
    return _call_openai_api(prompt, audit_id, document_id, model_type)


def _call_openai_api(prompt, audit_id=None, document_id=None, model_type='compliance'):
    """Call OpenAI API for AI processing"""
    from django.conf import settings
    import requests
    import json
    
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key or api_key == 'your-openai-api-key-here':
        raise Exception("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
    
    # Clean model name - strip quotes and whitespace to avoid "invalid model ID" errors
    model_raw = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
    model = str(model_raw).strip().strip('"').strip("'")
    temperature = getattr(settings, 'OPENAI_TEMPERATURE', 0.1)
    max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS', 4000)
    timeout = getattr(settings, 'OPENAI_TIMEOUT', 60)
    
    logger.info(f"🔍 Model check - Original: '{model_raw}', Cleaned: '{model}'")
    
    # Generate deterministic seed for OpenAI (using user parameter)
    seed = generate_deterministic_seed(document_id or 0, audit_id or 0) if document_id and audit_id else 42
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': model,  # Use cleaned model name
        'messages': [
            {'role': 'system', 'content': 'You are an expert GRC (Governance, Risk & Compliance) auditor with deep expertise in regulatory frameworks, compliance standards, and audit methodologies. You excel at conducting comprehensive compliance assessments, identifying gaps, evaluating risks, and providing actionable recommendations. Always provide accurate, detailed, and consistent analysis in valid JSON format. Focus on evidence-based assessments and practical compliance solutions.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': temperature,
        'max_tokens': max_tokens,
        'user': f"audit_{audit_id}_{document_id}" if audit_id and document_id else "audit_user"
    }
    
    # Add seed for consistency (OpenAI supports this parameter)
    if hasattr(settings, 'OPENAI_SEED') and settings.OPENAI_SEED:
        payload['seed'] = seed
    
    logger.info(f"🤖 Calling OpenAI API with model: {model}, temperature: {temperature}")
    logger.info(f"🔍 Payload keys: {list(payload.keys())}")
    logger.info(f"🔍 Model in payload: '{payload['model']}'")
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            # Enhanced error logging
            error_msg = 'Unknown error'
            try:
                error_data = response.json() if response.content else {}
                error_obj = error_data.get('error', {})
                if isinstance(error_obj, dict):
                    error_msg = error_obj.get('message', 'Unknown error')
                    error_type = error_obj.get('type', 'Unknown type')
                    error_code = error_obj.get('code', 'Unknown code')
                    logger.error(f"🔍 OpenAI Error Details:")
                    logger.error(f"   Status Code: {response.status_code}")
                    logger.error(f"   Type: {error_type}")
                    logger.error(f"   Code: {error_code}")
                    logger.error(f"   Message: {error_msg}")
                    logger.error(f"   Full error: {error_obj}")
                    logger.error(f"   Model sent: '{model}'")
                    logger.error(f"   Payload: {json.dumps(payload, indent=2)}")
                else:
                    error_msg = str(error_obj) if error_obj else 'Unknown error'
                    logger.error(f"🔍 OpenAI Error Response: {error_data}")
            except Exception as parse_err:
                logger.error(f"⚠️  Could not parse error response: {parse_err}")
                logger.error(f"   Raw response text: {response.text[:500] if hasattr(response, 'text') else 'N/A'}")
                error_msg = f"HTTP {response.status_code} error - could not parse response"
            
            raise Exception(f"OpenAI API error {response.status_code}: {error_msg}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        logger.info(f"✅ OpenAI API response received: {len(content)} characters")
        return content
        
    except requests.exceptions.Timeout:
        raise Exception(f"OpenAI API timeout after {timeout} seconds")
    except requests.exceptions.RequestException as e:
        raise Exception(f"OpenAI API request failed: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("Invalid JSON response from OpenAI API")




def generate_deterministic_seed(document_id, audit_id, requirement_hash=None):
    """
    Generate a deterministic seed based on document and audit IDs for consistent results.
    
    Args:
        document_id: The document ID
        audit_id: The audit ID  
        requirement_hash: Optional hash of requirement content
        
    Returns:
        int: Deterministic seed value
    """
    import hashlib
    
    # Create a deterministic seed based on document and audit IDs
    seed_string = f"{document_id}_{audit_id}"
    if requirement_hash:
        seed_string += f"_{requirement_hash}"
    
    # Generate a hash and convert to integer seed
    hash_obj = hashlib.md5(seed_string.encode())
    seed_int = int(hash_obj.hexdigest()[:8], 16)
    
    return seed_int


def cleanup_ai_audit_temp_files(document_id, doc_id=None):
    """
    Clean up temporary files created during AI audit processing.
    
    Args:
        document_id: The document ID from the API request
        doc_id: The internal document ID from database (optional)
    """
    try:
        import tempfile
        import glob
        temp_dir = tempfile.gettempdir()
        
        # Look for temporary files created during AI audit processing
        temp_file_patterns = []
        
        if document_id:
            temp_file_patterns.extend([
                f"ai_audit_{document_id}_*",
                f"*ai_audit_{document_id}*",
                f"*compliance_check_{document_id}*",
                f"*temp_audit_{document_id}*"
            ])
            
        if doc_id and doc_id != document_id:
            temp_file_patterns.extend([
                f"ai_audit_{doc_id}_*",
                f"*ai_audit_{doc_id}*"
            ])
        
        cleaned_files = []
        for pattern in temp_file_patterns:
            temp_files = glob.glob(os.path.join(temp_dir, pattern))
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        cleaned_files.append(temp_file)
                        logger.info(f"🗑️ Cleaned up temporary file: {temp_file}")
                except Exception as temp_e:
                    logger.warning(f"⚠️ Could not delete temporary file {temp_file}: {temp_e}")
        
        return cleaned_files
        
    except Exception as e:
        logger.warning(f"⚠️ Error during temporary file cleanup: {e}")
        return []

@method_decorator(csrf_exempt, name='dispatch')
class AIAuditDocumentUploadView(View):
    """AI Audit Document Upload API - Single clean implementation"""
    
    def post(self, request, audit_id):
        """Upload document for AI audit processing"""
        try:
            print("=" * 80)
            print("AI AUDIT UPLOAD ENDPOINT CALLED - NEW CODE VERSION")
            print(f"Upload request for audit {audit_id}")
            print("=" * 80)
            logger.info("🚀🚀🚀 AI AUDIT UPLOAD ENDPOINT CALLED - NEW CODE VERSION 🚀🚀🚀")
            logger.info(f"📤 Upload request for audit {audit_id}")
            logger.info(f"📤 Upload audit_id type: {type(audit_id)}")
            logger.info(f"📤 Upload audit_id value: '{audit_id}'")
            
            # Check authentication using JWT (like other endpoints)
            from ...rbac.utils import RBACUtils
            user_id = RBACUtils.get_user_id_from_request(request)
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required'
                }, status=401)
            
            logger.info(f"📤 Authenticated user ID: {user_id}")
            
            # CRITICAL: Validate that the audit exists in the correct table (audit)
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT AuditId, AuditType FROM audit WHERE AuditId = %s", [audit_id])
                    audit_row = cursor.fetchone()
                    
                if audit_row:
                    audit_type = audit_row[1] if len(audit_row) > 1 else 'Unknown'
                    logger.info(f"✅ Found audit {audit_id} in audit table with type: {audit_type}")
                else:
                    logger.error(f"❌ Audit {audit_id} not found in audit table")
                    return JsonResponse({
                        'success': False,
                        'error': f'Audit {audit_id} not found. Please ensure the audit exists before uploading documents.'
                    }, status=404)
            except Exception as e:
                logger.error(f"❌ Error validating audit {audit_id}: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error validating audit: {e}'
                }, status=500)
            
            # Get optional mapping fields
            policy_id = request.POST.get('policy_id') or None
            subpolicy_id = request.POST.get('subpolicy_id') or None

            # Check if this is a metadata-only request (for already uploaded files)
            already_uploaded = request.POST.get('already_uploaded') == 'true'
            
            # Initialize variables that might be used later
            s3_key = None
            stored_name = None
            aws_file_link = None
            
            if already_uploaded:
                # Handle metadata-only document creation for already uploaded files
                file_name = request.POST.get('file_name')
                file_size = int(request.POST.get('file_size', 0))
                aws_file_link = request.POST.get('aws_file_link')
                s3_key = request.POST.get('s3_key')
                stored_name = request.POST.get('stored_name')
                file_id = request.POST.get('file_id')
                upload_type = request.POST.get('upload_type', 'evidence')
                
                logger.info(f"📤 S3 file metadata: s3_key={s3_key}, stored_name={stored_name}, aws_file_link={aws_file_link}")
                
                if not file_name:
                    return JsonResponse({
                        'success': False,
                        'error': 'File name is required for metadata-only upload'
                    }, status=400)
                
                # Use the stored_name or file_id as the document path for already uploaded files
                document_path = stored_name or f"uploaded/{file_id}" if file_id else f"uploaded/{file_name}"
                
                logger.info(f"📤 Creating metadata record for already uploaded file: {file_name}")
            else:
                # Get uploaded file for new uploads
                if 'file' not in request.FILES:
                    return JsonResponse({
                        'success': False,
                        'error': 'No file provided'
                    }, status=400)
                
                file = request.FILES['file']
                logger.info(f"📤 Uploading file: {file.name} ({file.size} bytes)")
                
                # Generate unique file ID and path
                file_id = str(uuid.uuid4())
                file_extension = os.path.splitext(file.name)[1].lower()
                unique_filename = f"{file_id}{file_extension}"
                
                # Save file to MEDIA_ROOT
                file_path = os.path.join('ai_audit_documents', unique_filename)
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Save file
                with open(full_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                logger.info(f"📤 File saved to: {full_path}")
                
                # Set variables for database insertion
                file_name = file.name
                file_size = file.size
                document_path = file_path
                upload_type = 'evidence'
            
            
            # Get user ID - handle case where user might not exist in database
            user_id = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                try:
                    # Verify user exists in database
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT UserId FROM grc_users WHERE UserId = %s", [request.user.id])
                        db_user = cursor.fetchone()
                        if db_user:
                            user_id = request.user.id
                        else:
                            logger.warning(f"User {request.user.id} not found in grc_users table")
                except Exception as e:
                    logger.warning(f"Error checking user in database: {e}")
            
            # If no valid user found, use NULL (database now allows this)
            if user_id is None:
                logger.info("No valid user found, using NULL for UploadedBy")
            
            # Store ONLY in ai_audit_data table (it has everything we need)
            try:
                with connection.cursor() as cursor:
                    # First insert with a temporary document_id (will be updated after)
                    # Determine mime type and external source
                    if already_uploaded:
                        mime_type = 'application/octet-stream'  # Default for already uploaded files
                        external_source = 'evidence_attachment'
                    else:
                        mime_type = file.content_type
                        external_source = 'manual'
                    
                    # Get FrameworkId from the audit record
                    try:
                        logger.info(f"🔍 Querying FrameworkId for audit {audit_id}")
                        cursor.execute("SELECT FrameworkId FROM audit WHERE AuditId = %s", [int(audit_id) if str(audit_id).isdigit() else audit_id])
                        framework_result = cursor.fetchone()
                        logger.info(f"🔍 FrameworkId query result: {framework_result}")
                        
                        if framework_result and framework_result[0] is not None:
                            framework_id = framework_result[0]
                            logger.info(f"✅ Found FrameworkId {framework_id} for audit {audit_id}")
                        else:
                            logger.error(f"❌ No FrameworkId found for audit {audit_id}. Audit record may not exist or FrameworkId is NULL.")
                            return JsonResponse({
                                'success': False,
                                'error': f'Audit {audit_id} not found or has no FrameworkId assigned. Please ensure the audit exists and has a framework assigned.'
                            }, status=400)
                    except Exception as framework_err:
                        logger.error(f"❌ Error querying FrameworkId for audit {audit_id}: {framework_err}")
                        return JsonResponse({
                            'success': False,
                            'error': f'Database error while retrieving audit framework: {framework_err}'
                        }, status=500)
                    
                    # external_id column is VARCHAR(100). Store a compact identifier
                    # Prefer S3 key; otherwise stored_name or file_id; as a last resort, derive key from URL
                    compact_external_id = None
                    if s3_key:
                        compact_external_id = s3_key
                    elif stored_name:
                        compact_external_id = stored_name
                    elif file_id:
                        compact_external_id = str(file_id)
                    elif aws_file_link and 'amazonaws.com/' in aws_file_link:
                        compact_external_id = aws_file_link.split('amazonaws.com/')[-1].split('?')[0]
                    
                    # Ensure it fits the varchar(100)
                    if compact_external_id and len(compact_external_id) > 100:
                        compact_external_id = compact_external_id[-100:]
                    
                    try:
                        print("=" * 80)
                        print("ABOUT TO INSERT INTO ai_audit_data")
                        print(f"audit_id: {audit_id}")
                        print(f"framework_id: {framework_id}")
                        print("=" * 80)
                        logger.info(f"🔍 About to insert into ai_audit_data with values:")
                        logger.info(f"  - audit_id: {audit_id}")
                        logger.info(f"  - file_name: {file_name}")
                        logger.info(f"  - document_path: {document_path}")
                        logger.info(f"  - upload_type: {upload_type}")
                        logger.info(f"  - file_size: {file_size}")
                        logger.info(f"  - mime_type: {mime_type}")
                        logger.info(f"  - user_id: {user_id}")
                        logger.info(f"  - policy_id: {policy_id}")
                        logger.info(f"  - subpolicy_id: {subpolicy_id}")
                        logger.info(f"  - external_source: {external_source}")
                        logger.info(f"  - compact_external_id: {compact_external_id}")
                        logger.info(f"  - framework_id: {framework_id}")
                        
                        cursor.execute("""
                            INSERT INTO ai_audit_data 
                            (audit_id, document_id, document_name, document_path, document_type, 
                             file_size, mime_type, uploaded_by, ai_processing_status, uploaded_date,
                             policy_id, subpolicy_id, upload_status, external_source, external_id,
                             FrameworkId, created_at, updated_at)
                            VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'pending', NOW(),
                                   %s, %s, 'uploaded', %s, %s, %s, NOW(), NOW())
                        """, [
                            int(audit_id) if str(audit_id).isdigit() else audit_id,
                            file_name,
                            document_path,
                            upload_type[:50],  # Truncate to fit varchar(50)
                            file_size,
                            mime_type,
                            user_id,
                            policy_id,  # Add policy_id
                            subpolicy_id,  # Add subpolicy_id
                            external_source,
                            compact_external_id,  # Compact identifier fits column limit
                            framework_id  # Add FrameworkId
                        ])
                        logger.info("✅ Insert into ai_audit_data successful")
                    except Exception as insert_err:
                        logger.error(f"❌ Insert error: {insert_err}")
                        logger.error(f"❌ Insert error type: {type(insert_err)}")
                        import traceback
                        logger.error(f"❌ Insert error traceback: {traceback.format_exc()}")
                        
                        # Handle missing FrameworkId column
                        if 'Unknown column' in str(insert_err) and 'FrameworkId' in str(insert_err):
                            logger.warning("ai_audit_data lacks FrameworkId column; inserting without it")
                            cursor.execute("""
                                INSERT INTO ai_audit_data 
                                (audit_id, document_id, document_name, document_path, document_type, 
                                 file_size, mime_type, uploaded_by, ai_processing_status, uploaded_date,
                                 policy_id, subpolicy_id, upload_status, external_source, external_id,
                                 created_at, updated_at)
                                VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'pending', NOW(),
                                       %s, %s, 'uploaded', %s, %s, NOW(), NOW())
                            """, [
                                int(audit_id) if str(audit_id).isdigit() else audit_id,
                                file_name,
                                document_path,
                                upload_type[:50],
                                file_size,
                                mime_type,
                                user_id,
                                policy_id,
                                subpolicy_id,
                                external_source,
                                compact_external_id
                            ])
                        else:
                            # Re-raise the exception with more context
                            raise Exception(f"Database insert failed: {insert_err}") from insert_err
                    
                    # Get the auto-generated ID (this will be the primary key 'id')
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    result = cursor.fetchone()
                    record_id = result[0] if result else None
                    document_id = record_id  # Use the auto-generated ID as document_id
                    
                    # Update the document_id column with the same value
                    cursor.execute("""
                        UPDATE ai_audit_data 
                        SET document_id = %s 
                        WHERE id = %s
                    """, [record_id, record_id])
                    
                    logger.info(f"📤 Stored in ai_audit_data table with ID: {record_id}")
            except Exception as e:
                logger.error(f"❌ Could not store in ai_audit_data table: {e}")
                raise

            # All document data is now stored in ai_audit_data table with policy mapping
            
            return JsonResponse({
                'success': True,
                'document_id': document_id,
                'file_name': file_name,
                'file_size': file_size,
                'file_type': mime_type,
                'policy_id': policy_id,
                'subpolicy_id': subpolicy_id,
                'message': 'File uploaded successfully'
            })
            
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    

@method_decorator(csrf_exempt, name='dispatch')
class AIAuditDocumentsView(View):
    """Get uploaded documents for an audit"""
    
    def get(self, request, audit_id):
        """Get all documents for an audit"""
        try:
            logger.info(f"📋 Getting documents for audit {audit_id}")
            
            # Check authentication using JWT
            from ...rbac.utils import RBACUtils
            user_id = RBACUtils.get_user_id_from_request(request)
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required'
                }, status=401)
            
            with connection.cursor() as cursor:
                # Debug the audit_id parameter
                converted_audit_id = int(audit_id) if str(audit_id).isdigit() else audit_id
                logger.info(f"📋 Querying documents for audit_id: {audit_id} (type: {type(audit_id)})")
                logger.info(f"📋 Converted audit_id: {converted_audit_id} (type: {type(converted_audit_id)})")
                
                cursor.execute("""
                    SELECT document_id, document_name, document_type, file_size, 
                        created_at, upload_status, ai_processing_status, 
                        external_source, external_id, mime_type, document_path,
                        compliance_status, confidence_score, compliance_analyses,
                        processing_completed_at, policy_id, subpolicy_id
                    FROM ai_audit_data 
                    WHERE audit_id = %s 
                    ORDER BY created_at DESC
                """, [converted_audit_id])
                
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                logger.info(f"📋 Raw SQL result rows: {len(rows)}")

                # Also load the audit's policy/subpolicy names to show mapping
                policy_name = None
                subpolicy_name = None
                try:
                    cursor.execute(
                        """
                        SELECT p.PolicyName, sp.SubPolicyName
                        FROM audit a
                        LEFT JOIN policies p ON a.PolicyId = p.PolicyId
                        LEFT JOIN subpolicies sp ON a.SubPolicyId = sp.SubPolicyId
                        WHERE a.AuditId = %s
                        """,
                        [converted_audit_id]
                    )
                    row = cursor.fetchone()
                    if row:
                        policy_name, subpolicy_name = row[0], row[1]
                except Exception as e:
                    logger.warning(f"ℹ️ Could not fetch policy/subpolicy names for audit {audit_id}: {e}")
                
            documents = []
            for row in rows:
                doc_dict = dict(zip(columns, row))
                
                # Parse compliance analyses if available
                compliance_analyses = None
                if doc_dict.get('compliance_analyses'):
                    try:
                        import json
                        compliance_analyses = json.loads(doc_dict['compliance_analyses'])
                    except (json.JSONDecodeError, TypeError):
                        compliance_analyses = None
                
                documents.append({
                        'document_id': doc_dict.get('document_id'),
                        'document_name': doc_dict.get('document_name'),
                        'file_name': doc_dict.get('document_name'),  # Frontend compatibility
                        'file_type': doc_dict.get('document_type'),
                        'file_size': doc_dict.get('file_size'),
                        'uploaded_date': doc_dict.get('created_at').isoformat() if doc_dict.get('created_at') else None,
                        'upload_status': doc_dict.get('upload_status'),
                        'processing_status': doc_dict.get('ai_processing_status'),
                        'ai_processing_status': doc_dict.get('ai_processing_status'),  # Frontend compatibility
                        'external_source': doc_dict.get('external_source'),
                        'external_id': doc_dict.get('external_id'),
                        'mime_type': doc_dict.get('mime_type'),
                        'document_path': doc_dict.get('document_path'),
                        'compliance_status': doc_dict.get('compliance_status'),
                        'confidence_score': doc_dict.get('confidence_score'),
                        'compliance_analyses': compliance_analyses,
                        'processing_completed_at': doc_dict.get('processing_completed_at').isoformat() if doc_dict.get('processing_completed_at') else None,
                        'policy_id': doc_dict.get('policy_id'),
                        'subpolicy_id': doc_dict.get('subpolicy_id'),
                        # Frontend looks for these labels to display mapping
                        'policy_name': policy_name,
                        'subpolicy_name': subpolicy_name,
                        'mapped_policy': policy_name,  # Frontend compatibility
                        'mapped_subpolicy': subpolicy_name,  # Frontend compatibility
                        'processing_results': compliance_analyses,  # Use compliance analyses as processing results
                        'compliance_mapping': compliance_analyses,  # Use compliance analyses as mapping
                        'extracted_text': None  # Not implemented in this table yet
                    })
            
            logger.info(f"✅ Returning {len(documents)} documents for audit {audit_id}")
            
            return JsonResponse({
                'success': True,
                'audit_id': audit_id,
                'documents': documents,
                'total_documents': len(documents)
            })
            
        except Exception as e:
            logger.error(f"❌ Error getting documents: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# =====================
# Mapping Update API
# =====================
@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def map_audit_document_api(request, audit_id, document_id):
    """Update the policy/sub-policy mapping for a specific uploaded document."""
    try:
        policy_id = request.data.get('policy_id')
        subpolicy_id = request.data.get('subpolicy_id')

        if not policy_id and not subpolicy_id:
            return Response({
                'success': False,
                'error': 'Provide at least policy_id or subpolicy_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            # Verify the document belongs to this audit
            cursor.execute(
                """
                SELECT document_id FROM audit_document 
                WHERE document_id = %s AND audit_id = %s
                """,
                [int(document_id), int(audit_id) if str(audit_id).isdigit() else audit_id]
            )
            if not cursor.fetchone():
                return Response({
                    'success': False,
                    'error': 'Document not found for this audit'
                }, status=status.HTTP_404_NOT_FOUND)

            # Optional: validate subpolicy belongs to policy if both are provided
            if policy_id and subpolicy_id:
                try:
                    cursor.execute(
                        """
                        SELECT 1 FROM subpolicies WHERE SubPolicyId = %s AND PolicyId = %s
                        """,
                        [int(subpolicy_id), int(policy_id)]
                    )
                    if cursor.fetchone() is None:
                        return Response({
                            'success': False,
                            'error': 'Sub-policy does not belong to the provided policy'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except Exception:
                    # If schema differs, skip strict validation
                    pass

            # Update mapping columns when available
            updated = 0
            try:
                cursor.execute(
                    """
                    UPDATE audit_document
                    SET policy_id = COALESCE(%s, policy_id),
                        subpolicy_id = COALESCE(%s, subpolicy_id)
                    WHERE document_id = %s
                    """,
                    [policy_id, subpolicy_id, int(document_id)]
                )
                updated = cursor.rowcount
            except Exception as e:
                logger.warning(f"ℹ️ Mapping columns may not exist on audit_document: {e}")
                return Response({
                    'success': False,
                    'error': 'Mapping columns not available on audit_document table'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Fetch human-readable names
            policy_name = None
            subpolicy_name = None
            try:
                if policy_id:
                    cursor.execute("SELECT PolicyName FROM policies WHERE PolicyId = %s", [int(policy_id)])
                    row = cursor.fetchone()
                    if row:
                        policy_name = row[0]
                if subpolicy_id:
                    cursor.execute("SELECT SubPolicyName FROM subpolicies WHERE SubPolicyId = %s", [int(subpolicy_id)])
                    row = cursor.fetchone()
                    if row:
                        subpolicy_name = row[0]
            except Exception:
                pass

        return Response({
            'success': True,
            'document_id': int(document_id),
            'audit_id': audit_id,
            'policy_id': policy_id,
            'subpolicy_id': subpolicy_id,
            'policy_name': policy_name,
            'subpolicy_name': subpolicy_name,
            'updated': updated
        })
    except Exception as e:
        logger.error(f"❌ Error updating mapping: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class AIAuditStatusView(View):
    """Get AI audit processing status"""
    
    def get(self, request, audit_id):
        """Get processing status for an audit"""
        try:
            logger.info(f"📊 Getting AI audit status for audit {audit_id}")
            
            # Check authentication using JWT
            from ...rbac.utils import RBACUtils
            user_id = RBACUtils.get_user_id_from_request(request)
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required'
                }, status=401)
            
            with connection.cursor() as cursor:
                # Get status counts from new audit_document table
                cursor.execute("""
                    SELECT ai_processing_status, COUNT(*) as count
                    FROM audit_document 
                    WHERE audit_id = %s 
                    GROUP BY ai_processing_status
                """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
                
                status_rows = cursor.fetchall()
            
            status_counts = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0
            }
            
            for status_name, count in status_rows:
                if status_name in status_counts:
                    status_counts[status_name] = count
            
            # Calculate progress
            total_documents = sum(status_counts.values())
            completed_documents = status_counts['completed']
            progress_percentage = (completed_documents / total_documents * 100) if total_documents > 0 else 0
            
            return JsonResponse({
                'success': True,
                'audit_id': audit_id,
                'processing_status': {
                    'total_documents': total_documents,
                    'pending': status_counts['pending'],
                    'processing': status_counts['processing'],
                    'completed': status_counts['completed'],
                    'failed': status_counts['failed'],
                    'progress_percentage': round(progress_percentage, 2)
                },
                'is_complete': status_counts['pending'] == 0 and status_counts['processing'] == 0
            })
            
        except Exception as e:
            logger.error(f"❌ Error getting AI status: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def start_ai_audit_processing_api(request, audit_id):
    """Start AI processing for all pending documents with real AI/ML analysis"""
    try:
        logger.info(f"🚀 Starting AI processing for audit {audit_id}")
        
        # Check authentication using JWT
        from ...rbac.utils import RBACUtils
        user_id = RBACUtils.get_user_id_from_request(request)
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"🚀 Processing request from user: {user_id}")
        
        # Get pending documents from new audit_document table
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT document_id, document_name, document_path, document_type, file_size, mime_type
                FROM audit_document 
                WHERE audit_id = %s AND ai_processing_status = 'pending'
            """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
            
            documents = cursor.fetchall()
        
        if not documents:
            return Response({
                'success': False,
                'error': 'No pending documents to process'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"🚀 Found {len(documents)} documents to process")
        
        # Update status to processing in new table
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE audit_document 
                SET ai_processing_status = 'processing' 
                WHERE audit_id = %s AND ai_processing_status = 'pending'
            """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
            
            updated_count = cursor.rowcount
        
        logger.info(f"🚀 Updated {updated_count} documents to processing status")
        
        # Start AI processing for each document
        processing_results = []
        for doc in documents:
            doc_id, doc_name, file_path, doc_type, file_size, mime_type = doc
            try:
                logger.info(f"🤖 Processing document: {doc_name}")
                
                # Use MIME type instead of DocumentType for better accuracy
                actual_doc_type = mime_type if mime_type else doc_type
                logger.info(f"🔍 Using document type: {actual_doc_type}")
                
                # Process the document with AI/ML
                result = process_document_with_ai(doc_id, doc_name, file_path, actual_doc_type, audit_id)
                processing_results.append(result)
                
                # Update document status to completed (store minimal fields available)
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE audit_document 
                        SET ai_processing_status = 'completed'
                        WHERE document_id = %s
                    """, [doc_id])
                
                logger.info(f"✅ Document {doc_name} processed successfully")
                
            except Exception as e:
                logger.error(f"❌ Error processing document {doc_name}: {e}")
                logger.error(f"❌ Error type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                
                # Mark document as failed (minimal update)
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE audit_document 
                        SET ai_processing_status = 'failed'
                        WHERE document_id = %s
                    """, [doc_id])
        
        return Response({
            'success': True,
            'message': f'AI processing completed for {len(processing_results)} documents',
            'audit_id': audit_id,
            'documents_processed': len(processing_results),
            'processing_results': processing_results
        })
        
    except Exception as e:
        logger.error(f"❌ Error starting AI processing: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def process_document_with_ai(doc_id, doc_name, file_path, doc_type, audit_id):
    """Process document with real AI/ML to extract metadata and determine compliance"""
    try:
        logger.info(f"🤖 Starting AI processing for document: {doc_name}")
        
        # Get full file path - handle both relative and absolute paths
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        logger.info(f"🔍 Checking file path: {full_path}")
        if not os.path.exists(full_path):
            logger.error(f"❌ File not found: {full_path}")
            raise Exception(f"File not found: {full_path}")
        
        logger.info(f"✅ File found, size: {os.path.getsize(full_path)} bytes")
        
        # Extract text from document
        full_text = extract_text_from_document(full_path, doc_type)
        
        if not full_text or len(full_text.strip()) < 50:
            raise Exception(f"Document {doc_name} has insufficient text for AI analysis")
        
        # Use structured compliance checking
        from .structured_compliance_checker import check_document_structured_compliance
        
        # Check compliance against specific policies/subpolicies
        compliance_result = check_document_structured_compliance(audit_id, doc_id, full_text, doc_name)
        
        if not compliance_result['success']:
            raise Exception(f"Compliance checking failed: {compliance_result['error']}")
        
        # Extract AI analysis and compliance matrix
        ai_analysis = compliance_result['ai_analysis']
        compliance_matrix = compliance_result['compliance_matrix']
        compliance_summary = compliance_result['summary']
        
        # Generate AI-powered recommendations
        ai_recommendations = generate_ai_recommendations(full_text, ai_analysis)
        
        # Extract metadata using AI
        metadata = extract_ai_metadata(full_path, doc_type, full_text, ai_analysis)
        
        result = {
            'document_id': doc_id,
            'document_name': doc_name,
            'processing_results': {
                'text_length': len(full_text),
                'metadata': metadata,
                'processing_timestamp': datetime.now().isoformat(),
                'ai_analysis': ai_analysis,
                'data_quality_score': ai_analysis.get('data_quality_score', 0.0)
            },
            'compliance_mapping': ai_analysis.get('compliance_analysis', {}),
            'compliance_matrix': compliance_matrix,  # Detailed compliance matrix
            'compliance_summary': compliance_summary,  # Overall compliance summary
            'extracted_text': full_text[:1000] + '...' if len(full_text) > 1000 else full_text,
            'ai_recommendations': ai_recommendations,
            'compliance_status': compliance_summary.get('overall_status', 'unknown'),
            'risk_level': ai_analysis.get('risk_level', 'medium'),
            'confidence_score': ai_analysis.get('confidence_score', 0.0)
        }
        
        logger.info(f"✅ AI processing completed for {doc_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ AI processing failed for {doc_name}: {e}")
        raise


def extract_text_from_document(file_path, doc_type):
    """Extract text from various document types using AI/ML"""
    try:
        if doc_type == 'application/pdf':
            return extract_text_from_pdf(file_path)
        elif doc_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return extract_text_from_word(file_path)
        elif doc_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
            return extract_text_from_excel(file_path)
        elif doc_type == 'text/plain':
            return extract_text_from_txt(file_path)
        else:
            return f"Document type {doc_type} not supported for text extraction"
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return f"Error extracting text: {str(e)}"


def extract_text_from_pdf(file_path):
    """Extract text from PDF using PyPDF2"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return f"PDF extraction failed: {str(e)}"


def extract_text_from_word(file_path):
    """Extract text from Word document using python-docx"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Word extraction error: {e}")
        return f"Word extraction failed: {str(e)}"


def extract_text_from_excel(file_path):
    """Extract text from Excel document using openpyxl"""
    try:
        import openpyxl
        workbook = openpyxl.load_workbook(file_path)
        text = ""
        inferred = { 'sheets': [] }
        for sheet_name in workbook.sheetnames[:3]:
            sheet = workbook[sheet_name]
            rows_iter = list(sheet.iter_rows(values_only=True))
            headers = []
            sample = []
            if rows_iter:
                headers = [str(h).strip() if h is not None else '' for h in (rows_iter[0] or [])]
                for r in rows_iter[1:11]:
                    sample.append({ headers[i] if i < len(headers) else f'col_{i+1}': (r[i] if i < len(r) else None) for i in range(max(len(headers), len(r or []))) })
            inferred['sheets'].append({ 'name': sheet_name, 'headers': headers, 'sample_rows': sample })
            # Also flatten into text for generic analysis
            if headers:
                text += ' | '.join(headers) + '\n'
            for r in rows_iter[1:101]:
                line = ' | '.join([str(v) for v in (r or []) if v is not None])
                if line:
                    text += line + '\n'
        # Attach inferred schema JSON at the end (truncated in prompt if needed)
        text += f"\n__INFERRED_SCHEMA_START__\n{json.dumps(inferred, ensure_ascii=False)}\n__INFERRED_SCHEMA_END__\n"
        return text
    except Exception as e:
        logger.error(f"Excel extraction error: {e}")
        return f"Excel extraction failed: {str(e)}"


def extract_text_from_txt(file_path):
    """Extract text from plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"TXT extraction error: {e}")
        return f"TXT extraction failed: {str(e)}"


# =============================
# Compliance Checking Endpoints
# =============================

def _get_policy_requirements(policy_id: int, subpolicy_id: int = None):
    """Fetch compliance requirements for a policy from DB."""
    try:
        with connection.cursor() as cursor:
            # If subpolicy_id is provided, only fetch requirements for that specific subpolicy
            if subpolicy_id:
                cursor.execute(
                    """
                    SELECT c.ComplianceId, c.ComplianceTitle, c.ComplianceItemDescription,
                           c.ComplianceType, c.Criticality, c.MandatoryOptional,
                           sp.SubPolicyId, sp.SubPolicyName
                    FROM compliance c
                    JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                    WHERE sp.SubPolicyId = %s
                    """,
                    [int(subpolicy_id)]
                )
            else:
                cursor.execute(
                """
                SELECT c.ComplianceId, c.ComplianceTitle, c.ComplianceItemDescription,
                       c.ComplianceType, c.Criticality, c.MandatoryOptional,
                       sp.SubPolicyId, sp.SubPolicyName
                FROM compliance c
                JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                WHERE sp.PolicyId = %s
                """,
                [int(policy_id)]
            )
            rows = cursor.fetchall()
            reqs = []
            used_titles = set()  # Track used titles to prevent duplicates
            used_descriptions = set()  # Track used descriptions to prevent duplicates
            
            for r in rows:
                # Create a unique title by combining title with compliance ID or description
                base_title = r[1] or 'Compliance Requirement'
                description = r[2] or ''
                
                # Use the full description as the title if it's available and meaningful
                if description and len(description) > 10 and description != base_title:
                    # Use full description as the main title
                    unique_title = description
                else:
                    unique_title = f"{base_title} (ID: {r[0]})"
                
                # Check for duplicates based on description (most reliable)
                if description and description in used_descriptions:
                    logger.info(f"🔄 Skipping duplicate compliance {r[0]}: '{description[:50]}...'")
                    continue
                
                # Mark this description as used
                if description:
                    used_descriptions.add(description)
                
                # Ensure title is unique by adding ID if duplicate
                counter = 1
                original_title = unique_title
                while unique_title in used_titles:
                    unique_title = f"{original_title} (ID: {r[0]})"
                    counter += 1
                
                used_titles.add(unique_title)
                logger.info(f"🔍 Requirement {r[0]}: '{base_title}' -> '{unique_title}'")
                
                reqs.append({
                    'compliance_id': r[0],
                    'title': unique_title,
                    'description': description,
                    'type': r[3] or 'General',
                    'risk': r[4] or 'Medium',
                    'mandatory': (r[5] or '').lower() == 'mandatory',
                    'subpolicy_id': r[6],
                    'subpolicy_name': r[7]
                })
            return reqs
    except Exception as e:
        logger.error(f"❌ Error loading requirements for policy {policy_id}: {e}")
        return []


def _ai_score_requirements_with_openai(document_text: str, requirements: list, schema: dict = None, audit_id=None, document_id=None):
    """Call OpenAI in batches to score requirements against text."""
    import requests, json, re
    
    results = []
    logger.info(f"🔍 Processing {len(requirements)} requirements sequentially with 600s timeout each")
    
    # Process requirements sequentially
    for i, req in enumerate(requirements):
        global_idx = i + 1
        logger.info(f"🔍 Processing requirement {global_idx}: {req.get('title', 'Requirement')}")
        batch_results = _process_single_requirement_batch(document_text, [req], global_idx, audit_id, document_id)
        results.extend(batch_results)
        logger.info(f"✅ Completed requirement {global_idx}")
    
    return results

def _process_single_requirement_batch(document_text: str, batch: list, global_idx: int, audit_id=None, document_id=None):
    """Process a single requirement batch"""
    import json, re
    
    req = batch[0]  # Single requirement
    logger.info("🤖 Using unified AI API for compliance checking")
    logger.info(f"⏱️ Processing requirement {global_idx} with 600s timeout (10 minutes)...")
    
    # Create advanced prompt for single requirement
    prompt = f"""You are an expert GRC compliance auditor with deep knowledge of regulatory frameworks. Perform a comprehensive compliance analysis.

DOCUMENT CONTENT: {document_text[:800]}

COMPLIANCE REQUIREMENT:
{global_idx}. {req.get('title','Requirement')}
Description: {req.get('description', 'No description provided')}

ADVANCED ANALYSIS TASK:
1. **Relevance Assessment**: How relevant is this requirement to the document content?
2. **Evidence Detection**: Find ALL specific evidence that demonstrates compliance
3. **Gap Analysis**: Identify ALL missing elements that would be needed for full compliance
4. **Compliance Scoring**: Determine compliance level based on evidence quality and completeness
5. **Risk Assessment**: Evaluate the risk level of any compliance gaps

COMPLIANCE LEVELS:
- **COMPLIANT**: Strong evidence exists, all key elements present, low risk
- **PARTIALLY_COMPLIANT**: Some evidence exists, but gaps or weaknesses identified, medium risk
- **NON_COMPLIANT**: Little to no evidence, major gaps present, high risk

REQUIRED JSON OUTPUT FORMAT:
{{
  "analysis": [{{
    "index": {global_idx},
    "compliance_id": {req.get('compliance_id', global_idx)},
    "relevance": 0.0-1.0,
    "compliance_status": "COMPLIANT|PARTIALLY_COMPLIANT|NON_COMPLIANT",
    "compliance_score": 0.0-1.0,
    "risk_level": "LOW|MEDIUM|HIGH",
    "confidence": 0.0-1.0,
    "evidence": [
      "Specific text snippet or procedure found",
      "Another compliance element present"
    ],
    "missing": [
      "Specific requirement not found",
      "Another gap identified"
    ],
    "strengths": [
      "What the document does well for this requirement"
    ],
    "weaknesses": [
      "Areas that need improvement"
    ],
    "recommendations": [
      "Specific actionable recommendations"
    ]
  }}]
}}

ANALYSIS CRITERIA:
- Look for specific policies, procedures, controls, metrics, or documentation
- Consider both explicit statements and implied compliance through practices
- Evaluate the completeness and quality of evidence
- Assess whether controls are properly implemented and documented
- Consider regulatory context and industry best practices

CRITICAL: Return ONLY the JSON structure above. No explanations or additional text.

JSON:"""
    
    # Use unified AI API call
    data = call_ai_api(prompt, audit_id, document_id, 'compliance')
    
    logger.info(f"🤖 TinyLlama response length: {len(data)} characters")
    
    # Parse JSON response - Enhanced with markdown code block handling
    try:
        # Remove markdown code blocks if present
        cleaned_data = data.strip()
        if cleaned_data.startswith('```json'):
            cleaned_data = cleaned_data[7:]  # Remove ```json
        if cleaned_data.startswith('```'):
            cleaned_data = cleaned_data[3:]   # Remove ```
        if cleaned_data.endswith('```'):
            cleaned_data = cleaned_data[:-3]  # Remove trailing ```
        
        parsed = json.loads(cleaned_data.strip())
    except Exception as e:
        raise Exception(f"Failed to parse JSON response: {e}. Response: {data[:200]}...")
    if 'analysis' in parsed and isinstance(parsed['analysis'], list):
        # Enhanced compliance analysis processing
        for a in parsed['analysis']:
            a['requirement_title'] = req.get('title') or a.get('requirement_title') or f"Requirement {global_idx}"
            
            # Handle enhanced response format with predefined compliance_status
            if 'compliance_status' in a:
                # Use the AI-determined compliance status directly
                compliance_status = a.get('compliance_status', '').upper()
                if compliance_status == 'COMPLIANT':
                    a['status'] = 'compliant'
                    a['compliance_score'] = a.get('compliance_score', 0.9)
                elif compliance_status == 'PARTIALLY_COMPLIANT':
                    a['status'] = 'partially_compliant'
                    a['compliance_score'] = a.get('compliance_score', 0.6)
                elif compliance_status == 'NON_COMPLIANT':
                    a['status'] = 'non_compliant'
                    a['compliance_score'] = a.get('compliance_score', 0.2)
                else:
                    # Default to non-compliant if status is unclear
                    a['compliance_score'] = 0.2
                    a['status'] = 'non_compliant'
            else:
                # Default to non-compliant if no enhanced fields
                a['compliance_score'] = 0.2
                a['status'] = 'non_compliant'
            
            # Calculate compliance percentage
            a['compliance_percent'] = int(round(a['compliance_score'] * 100))
        return parsed['analysis']
    else:
        raise Exception(f"Unexpected response format: {data}")
        logger.info("🤖 Using OpenAI for compliance checking")
        logger.info(f"⏱️ Processing {len(batch)} requirement with 60s timeout...")
        req_lines = []
        for j, req in enumerate(batch):
            global_idx = i + j + 1  # Global index across all batches
            desc = (req.get('description') or '').strip()
            req_lines.append(f"{global_idx}. {req.get('title','Requirement')}")
        
        # Advanced multi-requirement compliance analysis prompt
        prompt = f"""You are an expert GRC compliance auditor conducting a comprehensive multi-requirement audit. Perform detailed compliance analysis for each requirement.

DOCUMENT CONTENT: {document_text[:1000]}

COMPLIANCE REQUIREMENTS TO ANALYZE:
{chr(10).join(req_lines)}

ADVANCED MULTI-REQUIREMENT ANALYSIS TASK:
For EACH requirement (1 through {len(batch)}), perform:

1. **Comprehensive Evidence Detection**: Find ALL specific evidence demonstrating compliance
2. **Gap Analysis**: Identify ALL missing elements needed for full compliance  
3. **Compliance Assessment**: Determine exact compliance level (COMPLIANT/PARTIALLY_COMPLIANT/NON_COMPLIANT)
4. **Risk Evaluation**: Assess risk level of compliance gaps
5. **Quality Assessment**: Evaluate evidence quality and completeness

COMPLIANCE LEVEL DEFINITIONS:
- **COMPLIANT**: Strong evidence, all key elements present, well-documented, low risk
- **PARTIALLY_COMPLIANT**: Some evidence exists, but gaps/weaknesses identified, medium risk  
- **NON_COMPLIANT**: Little/no evidence, major gaps, high risk

REQUIRED JSON OUTPUT FORMAT:
{{
  "analysis": [
    {{
      "index": 1,
      "compliance_id": {requirements[i+0]['compliance_id']},
      "relevance": 0.0-1.0,
      "compliance_status": "COMPLIANT|PARTIALLY_COMPLIANT|NON_COMPLIANT",
      "compliance_score": 0.0-1.0,
      "risk_level": "LOW|MEDIUM|HIGH", 
      "confidence": 0.0-1.0,
      "evidence": ["Specific evidence found in document"],
      "missing": ["Specific gaps identified"],
      "strengths": ["What document does well"],
      "weaknesses": ["Areas needing improvement"],
      "recommendations": ["Specific actionable steps"]
    }}
  ]
}}

ANALYSIS STANDARDS:
- Look for policies, procedures, controls, metrics, documentation, training records
- Consider both explicit statements and implied compliance through practices
- Evaluate evidence completeness, accuracy, and implementation quality
- Assess regulatory context and industry standards
- Identify root causes of any compliance gaps

CRITICAL REQUIREMENTS:
- Analyze ALL {len(batch)} requirements listed above
- Return EXACTLY {len(batch)} analysis objects
- Use double quotes, square brackets, curly braces for JSON
- No explanations or additional text outside JSON
- Each requirement gets ONE object in the analysis array

JSON:"""
        
        try:
            # Use unified AI API call
            data = call_ai_api(prompt, audit_id, document_id, 'compliance')
            
            logger.info(f"🤖 TinyLlama response length: {len(data)} characters")
            logger.info(f"🤖 TinyLlama response preview: {data[:300]}...")
            logger.info(f"🤖 Full TinyLlama response: {data}")
            
            # Enhanced JSON parsing to handle markdown code blocks and malformed responses
            try:
                # Remove markdown code blocks if present
                cleaned_data = data.strip()
                if cleaned_data.startswith('```json'):
                    cleaned_data = cleaned_data[7:]  # Remove ```json
                if cleaned_data.startswith('```'):
                    cleaned_data = cleaned_data[3:]   # Remove ```
                if cleaned_data.endswith('```'):
                    cleaned_data = cleaned_data[:-3]  # Remove trailing ```
                
                parsed = json.loads(cleaned_data.strip())
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Raw response: {data}")
                raise Exception(f"Failed to parse JSON response: {e}. Response: {data[:200]}...")
            
            # Enforce de-duplication by requirement title and index (across batches)
            for a in parsed.get('analysis', []):
                # Validate that analysis item is a dictionary
                if not isinstance(a, dict):
                    logger.error(f"❌ Analysis item is not a dict: {type(a)} - {a}")
                    raise Exception(f"OpenAI returned invalid analysis item: {a}")
                
                # Add the requirement title to the analysis result
                # Model returns index relative to the current batch (1..len(batch)).
                # Convert to GLOBAL requirement index using the batch offset 'i'.
                global_index = i + int(a.get('index', 1))
                req_index = global_index - 1  # 0-based
                if req_index < len(requirements):
                    a['requirement_title'] = requirements[req_index].get('title', f'Requirement {global_index}')
                    a['requirement_description'] = requirements[req_index].get('description', '')
                    a['compliance_id'] = requirements[req_index].get('compliance_id')
                else:
                    a['requirement_title'] = f'Requirement {global_index}'
                    a['requirement_description'] = ''
                # Overwrite index with the global index so downstream consumers are consistent
                a['index'] = global_index
                # Skip duplicates by title or by index across all batches
                title_key = a['requirement_title'].strip().lower()
                if global_index in seen_indexes_global or title_key in seen_titles_global:
                    logger.info(f"🔄 Skipping duplicate analysis for global index {global_index} / title '{a['requirement_title']}'")
                    continue
                seen_indexes_global.add(global_index)
                seen_titles_global.add(title_key)
                results.append(a)
            
            logger.info(f"✅ Processed batch {i//BATCH + 1} successfully")
            
        except Exception as e:
            logger.error(f"❌ OpenAI batch {i//BATCH + 1} failed: {e}")
            raise Exception(f"OpenAI processing failed: {e}")

    logger.info(f"✅ OpenAI compliance check completed for {len(requirements)} requirements")
    return results


def _determine_status(requirements: list, analyses: list):
    """Overall status per user's rule:
    - If any requirement has compliance score > 0.5 → overall 'compliant'
    - Else if any requirement has evidence (score > 0 because we set 0 without evidence) → 'partially_compliant'
    - Else → 'non_compliant'
    Return also the average score for display.
    """
    scores = []
    has_any_evidence = False
    has_any_gt_50 = False
    for a in analyses or []:
        evidence_items = a.get('evidence') or []
        score = float(a.get('compliance_score', 0.0))
        scores.append(score)
        if isinstance(evidence_items, list) and len(evidence_items) > 0:
            has_any_evidence = True
        if score > 0.5:
            has_any_gt_50 = True

    avg = (sum(scores)/len(scores)) if scores else 0.0
    if has_any_gt_50:
        return 'compliant', avg
    if has_any_evidence:
        return 'partially_compliant', avg
    return 'non_compliant', avg


def _compute_basic_signals(inferred_schema: dict) -> dict:
    """Infer simple, deterministic signals from inferred Excel schema/sample rows.
    Signals are generic and resilient to header variations.
    """
    try:
        if not inferred_schema or 'sheets' not in inferred_schema:
            return {'core_fields_ok': False, 'fields': {}, 'coverage': {}}

        # Synonym map
        synonyms = {
            'user_id': ['employee id', 'employee_id', 'user id', 'user_id', 'userid', 'username'],
            'time_in': ['login time', 'time in', 'signin', 'sign_in', 'time_in', 'access time'],
            'time_out': ['logoff time', 'logout time', 'time out', 'signout', 'sign_out', 'time_out'],
            'action': ['action', 'event', 'activity', 'operation'],
            'mfa': ['mfa', 'two factor', '2fa', 'multifactor', 'otp']
        }

        def normalize(h):
            return (h or '').strip().lower()

        found_fields = {}
        coverage = {}

        for sheet in inferred_schema.get('sheets', [])[:1]:  # first sheet is usually primary
            headers = [normalize(h) for h in (sheet.get('headers') or [])]
            sample = sheet.get('sample_rows') or []
            # Map headers by synonym
            for key, syns in synonyms.items():
                idx = next((i for i, h in enumerate(headers) if any(s in h for s in syns)), None)
                if idx is not None:
                    found_fields[key] = headers[idx]
                    if sample:
                        non_empty = 0
                        total = len(sample)
                        for r in sample:
                            val = r.get(headers[idx])
                            if val not in (None, ''):
                                non_empty += 1
                        coverage[key] = round(non_empty / max(total, 1), 2)
                else:
                    coverage[key] = 0.0

        core_fields = ['user_id', 'time_in']
        core_ok = all(found_fields.get(f) for f in core_fields)
        return {'core_fields_ok': core_ok, 'fields': found_fields, 'coverage': coverage}
    except Exception:
        return {'core_fields_ok': False, 'fields': {}, 'coverage': {}}


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def check_document_compliance(request, audit_id, document_id):
    """Run compliance check for a single mapped document using OpenAI."""
    try:
        # Check authentication using JWT (like other endpoints)
        from ...rbac.utils import RBACUtils
        user_id = RBACUtils.get_user_id_from_request(request)
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"🔍 Compliance check request from user: {user_id}")
        
        # Lookup document path, mime, and policy mapping from ai_audit_data table
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT d.document_path, COALESCE(d.mime_type, d.document_type) AS doc_type,
                       COALESCE(d.policy_id, a.PolicyId) AS policy_id,
                       COALESCE(d.subpolicy_id, a.SubPolicyId) AS subpolicy_id,
                       d.external_source, d.external_id
                FROM ai_audit_data d
                JOIN audit a ON a.AuditId = d.audit_id
                WHERE d.document_id = %s AND d.audit_id = %s
                """,
                [int(document_id), int(audit_id) if str(audit_id).isdigit() else audit_id]
            )
            row = cursor.fetchone()
            if not row:
                return Response({'success': False, 'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
            doc_path, doc_type, policy_id, subpolicy_id, external_source, external_id = row

        # Handle file path - check if it's S3 or local
        if external_source in ['s3', 'evidence_attachment'] and external_id:
            # Handle S3 file
            try:
                import json
                s3_metadata = None
                s3_key = None
                # external_id might be JSON, a raw S3 key, or a full S3 URL
                if isinstance(external_id, str):
                    raw_value = external_id.strip()
                    try:
                        s3_metadata = json.loads(raw_value)
                    except Exception:
                        # Not JSON; handle as key or URL
                        if 'amazonaws.com/' in raw_value:
                            s3_key = raw_value.split('amazonaws.com/')[-1].split('?')[0]
                        else:
                            s3_key = raw_value
                else:
                    s3_metadata = external_id

                if not s3_key and s3_metadata:
                    s3_key = s3_metadata.get('s3_key')
                    if not s3_key and s3_metadata.get('aws_file_link'):
                        aws_link = s3_metadata.get('aws_file_link')
                        if 'amazonaws.com/' in aws_link:
                            s3_key = aws_link.split('amazonaws.com/')[-1].split('?')[0]
                
                if not s3_key:
                    return Response({'success': False, 'error': 'S3 key not found in metadata'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Download file from S3 to temporary location
                from ..Global.s3_fucntions import create_direct_mysql_client
                import tempfile
                
                s3_client = create_direct_mysql_client()
                # Extract filename from s3_key or use a default
                file_name = s3_key.split('/')[-1] if '/' in s3_key else s3_key
                if not file_name or '.' not in file_name:
                    file_name = f"document_{document_id}.pdf"  # Default filename
                
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, f"ai_audit_{document_id}_{file_name}")
                
                download_result = s3_client.download(s3_key, file_name, temp_dir, str(user_id))
                if not download_result.get('success'):
                    return Response({'success': False, 'error': f'Failed to download from S3: {download_result.get("error", "Unknown error")}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                temp_file_path = download_result.get('file_path', temp_file_path)
                if not temp_file_path or not os.path.exists(temp_file_path):
                    return Response({'success': False, 'error': 'Failed to download file from S3'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                full_path = temp_file_path
                temp_file_created = True
                logger.info(f"🔍 Downloaded S3 file to: {full_path}")
                
            except Exception as e:
                logger.error(f"❌ Error handling S3 file: {e}")
                return Response({'success': False, 'error': f'S3 file handling error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Handle local file
            full_path = doc_path if os.path.isabs(doc_path) else os.path.join(settings.MEDIA_ROOT, doc_path)
            if not os.path.exists(full_path):
                return Response({'success': False, 'error': 'File not found on server'}, status=status.HTTP_404_NOT_FOUND)
            temp_file_created = False

        # Extract text content (and inferred schema if Excel)
        text = extract_text_from_document(full_path, doc_type or 'text/plain')
        inferred_schema = None
        try:
            if '__INFERRED_SCHEMA_START__' in text:
                import re, json as _json
                m = re.search(r'__INFERRED_SCHEMA_START__\n([\s\S]*?)\n__INFERRED_SCHEMA_END__', text)
                if m:
                    inferred_schema = _json.loads(m.group(1))
                    # Remove schema marker from text before sending to model
                    text = text.replace(m.group(0), '')
        except Exception:
            inferred_schema = None

        # Load requirements
        requirements = _get_policy_requirements(policy_id, subpolicy_id)
        if not requirements:
            return Response({'success': False, 'error': 'No requirements for policy'}, status=status.HTTP_400_BAD_REQUEST)
        # Cap to first 10 requirements with better timeouts
        requirements = requirements[:10]

        # Deterministic signals from schema/sample
        signals = _compute_basic_signals(inferred_schema)

        # AI scoring
        analyses = _ai_score_requirements_with_openai(text, requirements, schema=inferred_schema, audit_id=audit_id, document_id=document_id)
        logger.info(f"🔍 Analyses type: {type(analyses)}, length: {len(analyses) if analyses else 0}")
        if analyses:
            logger.info(f"🔍 First analysis item type: {type(analyses[0])}, content: {analyses[0]}")
        status_label, confidence = _determine_status(requirements, analyses)

        # Blend signals: if core fields missing, keep status but reduce confidence
        if not signals.get('core_fields_ok'):
            confidence = max(0.0, confidence - 0.2)

        # Persist results to the new ai_audit_data table
        try:
            import json
            with connection.cursor() as cursor:
                # First, ensure the document exists in ai_audit_data table
                # Get FrameworkId from the audit record
                try:
                    logger.info(f"🔍 Querying FrameworkId for audit {audit_id} in compliance check")
                    cursor.execute("SELECT FrameworkId FROM audit WHERE AuditId = %s", [int(audit_id) if str(audit_id).isdigit() else audit_id])
                    framework_result = cursor.fetchone()
                    logger.info(f"🔍 FrameworkId query result: {framework_result}")
                    
                    if framework_result and framework_result[0] is not None:
                        framework_id = framework_result[0]
                        logger.info(f"✅ Found FrameworkId {framework_id} for audit {audit_id}")
                    else:
                        logger.error(f"❌ No FrameworkId found for audit {audit_id}. Audit record may not exist or FrameworkId is NULL.")
                        return JsonResponse({
                            'success': False,
                            'error': f'Audit {audit_id} not found or has no FrameworkId assigned. Please ensure the audit exists and has a framework assigned.'
                        }, status=400)
                except Exception as framework_err:
                    logger.error(f"❌ Error querying FrameworkId for audit {audit_id}: {framework_err}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Database error while retrieving audit framework: {framework_err}'
                    }, status=500)
                
                cursor.execute(
                    """
                    INSERT INTO ai_audit_data 
                    (audit_id, document_id, document_name, document_path, document_type, 
                     file_size, mime_type, uploaded_by, ai_processing_status, 
                     compliance_status, confidence_score, compliance_analyses, processing_completed_at, FrameworkId)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'completed', %s, %s, %s, NOW(), %s)
                    ON DUPLICATE KEY UPDATE
                    ai_processing_status = 'completed',
                    compliance_status = VALUES(compliance_status),
                    confidence_score = VALUES(confidence_score),
                    compliance_analyses = VALUES(compliance_analyses),
                    processing_completed_at = NOW(),
                    FrameworkId = VALUES(FrameworkId)
                    """,
                        [
                            int(audit_id), int(document_id), 'Document', doc_path, doc_type[:50],  # Truncate to fit varchar(50)
                            1024000, doc_type, 1, status_label, float(confidence),
                            json.dumps({
                                'compliance_status': status_label,
                                'confidence_score': float(confidence),
                                'compliance_analyses': analyses,
                                'processed_at': datetime.now().isoformat()
                            }),
                            framework_id  # Add FrameworkId
                        ]
                )
                logger.info(f"✅ Persisted compliance results for doc {document_id} in ai_audit_data table")
        except Exception as e:
            logger.warning(f"ℹ️ Could not persist compliance results for doc {document_id}: {e}")

        return Response({
            'success': True,
            'document_id': int(document_id),
            'audit_id': audit_id,
            'policy_id': policy_id,
            'status': status_label,
            'confidence': round(confidence, 2),
            'analyses': analyses,
            'signals': signals
        })
    except Exception as e:
        logger.error(f"❌ Error checking document compliance: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        # Clean up temporary file if it was created from S3
        if 'temp_file_created' in locals() and temp_file_created and 'full_path' in locals():
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logger.info(f"🗑️ Cleaned up temporary file: {full_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clean up temporary file {full_path}: {e}")
                
        # Additional cleanup for any other temporary files that might have been created
        cleaned_temp_files = cleanup_ai_audit_temp_files(document_id)
        if cleaned_temp_files:
            logger.info(f"🗑️ Additional cleanup - removed {len(cleaned_temp_files)} temporary files")


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def check_all_documents_compliance(request, audit_id):
    """Run compliance check for all mapped documents in an audit using OpenAI."""
    try:
        # Check authentication using JWT (like other endpoints)
        from ...rbac.utils import RBACUtils
        user_id = RBACUtils.get_user_id_from_request(request)
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"🔍 Bulk compliance check request from user: {user_id}")
        
        # Get all documents
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT d.document_id
                FROM audit_document d
                WHERE d.audit_id = %s
                """,
                [int(audit_id) if str(audit_id).isdigit() else audit_id]
            )
            doc_ids = [r[0] for r in cursor.fetchall()]

        results = []
        for doc_id in doc_ids:
            r = check_document_compliance(request._request, audit_id, doc_id)  # reuse logic
            # If called internally, r may be a DRF Response already
            res_data = r.data if hasattr(r, 'data') else r
            if isinstance(res_data, dict) and res_data.get('success'):
                results.append(res_data)

        # Aggregate simple rollup
        summary = { 'compliant': 0, 'partially_compliant': 0, 'non_compliant': 0 }
        for r in results:
            s = r.get('status')
            if s in summary:
                summary[s] += 1

        # Best-effort: persist an audit-level summary if needed (skip for now)

        return Response({
            'success': True,
            'audit_id': audit_id,
            'summary': summary,
            'results': results
        })
    except Exception as e:
        logger.error(f"❌ Error checking all documents: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditConductPermission, AuditReviewPermission])
@audit_conduct_required
def delete_audit_document_api(request, audit_id, document_id):
    """Delete an audit document"""
    try:
        logger.info(f"🗑️ Deleting document {document_id} from audit {audit_id}")
        
        # Check authentication using JWT
        from ...rbac.utils import RBACUtils
        user_id = RBACUtils.get_user_id_from_request(request)
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"🗑️ Delete request from user: {user_id}")
        
        # Check if document exists and belongs to the audit (correct table/columns)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, document_name, document_path 
                FROM ai_audit_data 
                WHERE document_id = %s AND audit_id = %s
                """,
                [int(document_id), int(audit_id) if str(audit_id).isdigit() else audit_id]
            )
            row = cursor.fetchone()
        
        if not row:
            return Response({
                'success': False,
                'error': 'Document not found or does not belong to this audit'
            }, status=status.HTTP_404_NOT_FOUND)
        
        doc_id, doc_name, doc_path = row
        
        # Delete the physical file (if present)
        try:
            if doc_path:
                full_path = doc_path if os.path.isabs(doc_path) else os.path.join(settings.MEDIA_ROOT, doc_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logger.info(f"🗑️ Deleted file: {full_path}")
                else:
                    logger.warning(f"🗑️ File not found on disk: {full_path}")
        except Exception as e:
            logger.warning(f"🗑️ Could not delete file {doc_path}: {e}")
        
        # Clean up any temporary files that might have been created during AI processing
        cleaned_temp_files = cleanup_ai_audit_temp_files(document_id, doc_id)
        if cleaned_temp_files:
            logger.info(f"🗑️ Cleaned up {len(cleaned_temp_files)} temporary files for document {document_id}")
        
        # Delete the database record
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM ai_audit_data 
                WHERE document_id = %s AND audit_id = %s
                """,
                [int(document_id), int(audit_id) if str(audit_id).isdigit() else audit_id]
            )
            deleted_count = cursor.rowcount
        
        if deleted_count == 0:
            return Response({
                'success': False,
                'error': 'Document could not be deleted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"✅ Document {doc_name} deleted successfully")
        
        return Response({
            'success': True,
            'message': f'Document {doc_name} deleted successfully',
            'document_id': document_id,
            'audit_id': audit_id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error deleting document: {e}")
        return Response({
            'success': False,
            'error': f'Failed to delete document: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    """Extract metadata using AI insights"""
    try:
        import os
        file_stats = os.stat(file_path)
        
        return {
            'file_size': file_stats.st_size,
            'file_type': doc_type,
            'created_time': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
            'modified_time': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            'file_extension': os.path.splitext(file_path)[1],
            'ai_document_type': ai_analysis.get('document_type', 'unknown'),
            'ai_audit_scope': ai_analysis.get('audit_scope', 'unknown'),
            'data_quality_score': ai_analysis.get('data_quality_score', 0.0),
            'confidence_score': ai_analysis.get('confidence_score', 0.0),
            'key_findings_count': len(ai_analysis.get('key_findings', [])),
            'missing_elements_count': len(ai_analysis.get('missing_elements', []))
        }
    except Exception as e:
        logger.error(f"Error extracting AI metadata: {e}")
        return {}


# AI processing functions using OpenAI


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def download_audit_report(request, audit_id):
    """Generate a comprehensive AI audit report and return it as a download."""
    try:
        logger.info(f"📊 Generating comprehensive AI audit report for audit {audit_id}")
        
        # Check authentication using JWT
        from ...rbac.utils import RBACUtils
        user_id = RBACUtils.get_user_id_from_request(request)
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get audit information
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT a.AuditId, a.AuditType, a.Status, a.AssignedDate, a.DueDate, a.CompletionDate,
                       p.PolicyName, sp.SubPolicyName, f.FrameworkName,
                       u1.UserName as AuditorName,
                       u2.UserName as AssigneeName,
                       u3.UserName as ReviewerName
                FROM audit a
                LEFT JOIN policies p ON a.PolicyId = p.PolicyId
                LEFT JOIN subpolicies sp ON a.SubPolicyId = sp.SubPolicyId
                LEFT JOIN frameworks f ON a.FrameworkId = f.FrameworkId
                LEFT JOIN users u1 ON a.Auditor = u1.UserId
                LEFT JOIN users u2 ON a.Assignee = u2.UserId
                LEFT JOIN users u3 ON a.Reviewer = u3.UserId
                WHERE a.AuditId = %s
            """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
            
            audit_row = cursor.fetchone()
            
            # Check if this is actually an AI audit by looking for AI audit data
            cursor.execute("""
                SELECT COUNT(*) FROM ai_audit_data WHERE audit_id = %s
            """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
            
            ai_data_count = cursor.fetchone()[0]
            is_actual_ai_audit = ai_data_count > 0
            
        if not audit_row:
            return Response({
                'success': False,
                'error': f'Audit {audit_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all AI audit documents and their processing results
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT document_id, document_name, document_type, file_size, mime_type,
                       ai_processing_status, compliance_status, confidence_score,
                       compliance_analyses, processing_completed_at, uploaded_date,
                       policy_id, subpolicy_id, external_source, external_id
                FROM ai_audit_data 
                WHERE audit_id = %s 
                ORDER BY uploaded_date DESC
            """, [int(audit_id) if str(audit_id).isdigit() else audit_id])
            
            documents = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
        
        # Process documents data
        processed_documents = []
        total_documents = len(documents)
        completed_documents = 0
        failed_documents = 0
        compliance_summary = {'compliant': 0, 'partially_compliant': 0, 'non_compliant': 0, 'unknown': 0}
        
        # Determine actual audit status based on AI processing results
        actual_audit_status = audit_row[2]  # Default to original status
        actual_completion_date = audit_row[5]  # Default to original completion date
        
        for doc_row in documents:
            doc_dict = dict(zip(columns, doc_row))
            
            # Parse compliance analyses if available
            compliance_analyses = None
            if doc_dict.get('compliance_analyses'):
                try:
                    try:
                        compliance_analyses = json.loads(doc_dict['compliance_analyses'])
                    except Exception as e:
                        logger.error(f"Failed to parse compliance analyses JSON: {e}")
                        compliance_analyses = None
                except:
                    compliance_analyses = None
            
            # Count compliance status
            status = doc_dict.get('compliance_status', 'unknown')
            if status in compliance_summary:
                compliance_summary[status] += 1
            
            # Count processing status
            processing_status = doc_dict.get('ai_processing_status', 'pending')
            if processing_status == 'completed':
                completed_documents += 1
            elif processing_status == 'failed':
                failed_documents += 1
            
            processed_documents.append({
                'document_id': doc_dict.get('document_id'),
                'document_name': doc_dict.get('document_name'),
                'document_type': doc_dict.get('document_type'),
                'file_size': doc_dict.get('file_size'),
                'mime_type': doc_dict.get('mime_type'),
                'ai_processing_status': processing_status,
                'compliance_status': status,
                'confidence_score': doc_dict.get('confidence_score'),
                'compliance_analyses': compliance_analyses,
                'processing_completed_at': doc_dict.get('processing_completed_at'),
                'uploaded_date': doc_dict.get('uploaded_date'),
                'policy_id': doc_dict.get('policy_id'),
                'subpolicy_id': doc_dict.get('subpolicy_id'),
                'external_source': doc_dict.get('external_source'),
                'external_id': doc_dict.get('external_id')
            })
        
        # Calculate actual audit status based on AI processing results
        if is_actual_ai_audit and total_documents > 0:
            completion_percentage = (completed_documents / total_documents) * 100
            
            if completion_percentage == 100:
                actual_audit_status = 'Completed'
                # Set completion date to the latest processing completion date
                latest_completion = None
                for doc in processed_documents:
                    if doc.get('processing_completed_at'):
                        if latest_completion is None or doc['processing_completed_at'] > latest_completion:
                            latest_completion = doc['processing_completed_at']
                if latest_completion:
                    actual_completion_date = latest_completion
            elif completion_percentage > 0:
                actual_audit_status = 'Work In Progress'
        
        # Generate comprehensive report data
        report_data = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'generated_by_user_id': user_id,
                'report_type': 'AI Audit Comprehensive Report',
                'audit_id': audit_id
            },
            'audit_information': {
                'audit_id': audit_row[0],
                'audit_type': 'AI Audit' if (audit_row[1] == 'A' or is_actual_ai_audit) else ('Internal' if audit_row[1] == 'I' else ('External' if audit_row[1] == 'E' else ('Self-Audit' if audit_row[1] == 'S' else audit_row[1]))),
                'status': actual_audit_status,
                'assigned_date': audit_row[3].isoformat() if audit_row[3] else None,
                'due_date': audit_row[4].isoformat() if audit_row[4] else None,
                'completion_date': actual_completion_date.isoformat() if actual_completion_date else None,
                'policy_name': audit_row[6],
                'subpolicy_name': audit_row[7],
                'framework_name': audit_row[8],
                'auditor_name': 'AI System (Automated)' if (audit_row[1] == 'A' or is_actual_ai_audit) else (audit_row[9] or 'Not Assigned'),
                'assignee_name': audit_row[10] or 'Not Assigned',
                'reviewer_name': audit_row[11] or 'Not Assigned',
                'is_ai_audit_detected': is_actual_ai_audit,
                'ai_data_records': ai_data_count,
                'audit_assignment_issue': '⚠️ WARNING: This audit was created as Internal but has AI processing data. It should be treated as an AI Audit.' if (audit_row[1] == 'I' and is_actual_ai_audit) else None
            },
            'processing_summary': {
                'total_documents': total_documents,
                'completed_documents': completed_documents,
                'failed_documents': failed_documents,
                'pending_documents': total_documents - completed_documents - failed_documents,
                'completion_percentage': round((completed_documents / total_documents * 100) if total_documents > 0 else 0, 2)
            },
            'compliance_summary': compliance_summary,
            'ai_processing_details': {
                'processing_method': 'OpenAI AI/ML Analysis',
                'analysis_engine': 'gpt-4o-mini',
                'compliance_checking': 'Structured Compliance Analysis',
                'text_extraction': 'Multi-format Document Processing',
                'metadata_extraction': 'AI-powered Document Analysis'
            },
            'documents_processed': processed_documents,
            'key_findings': {
                'overall_compliance_rate': round((compliance_summary['compliant'] / total_documents * 100) if total_documents > 0 else 0, 2),
                'average_confidence_score': round(sum(doc['confidence_score'] or 0 for doc in processed_documents) / total_documents if total_documents > 0 else 0, 2),
                'documents_requiring_attention': compliance_summary['non_compliant'] + compliance_summary['partially_compliant'],
                'processing_success_rate': round((completed_documents / total_documents * 100) if total_documents > 0 else 0, 2),
                'audit_assignment_status': 'Complete' if (audit_row[1] == 'A' and audit_row[11]) or (audit_row[1] != 'A' and audit_row[9] and audit_row[10] and audit_row[11]) else 'Incomplete - Missing Reviewer Assignment'
            },
            'recommendations': _generate_audit_recommendations(compliance_summary, processed_documents, audit_row),
            'technical_details': {
                'ai_model_used': 'llama3.2:3b',
                'processing_timestamp': datetime.now().isoformat(),
                'report_format': 'JSON',
                'data_sources': ['ai_audit_data', 'audit', 'policies', 'subpolicies', 'frameworks', 'grc_users']
            }
        }
        
        # Generate formatted Word document
        doc_content = _generate_word_document(report_data)
        
        # Create response with Word document
        response = HttpResponse(
            doc_content,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={
                'Content-Disposition': f'attachment; filename="AI_Audit_Report_{audit_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx"'
            }
        )
        
        logger.info(f"✅ Generated comprehensive AI audit report for audit {audit_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error generating AI audit report: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _format_datetime(dt_value):
    """Safely format datetime values that could be datetime objects or strings"""
    if not dt_value:
        return 'N/A'
    
    if isinstance(dt_value, datetime):
        return dt_value.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(dt_value, str):
        # If it's already a string, try to parse and reformat
        try:
            # Handle ISO format strings
            if 'T' in dt_value:
                parsed_dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                return parsed_dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # If it's already in a good format, return as is
                return dt_value
        except (ValueError, TypeError):
            return str(dt_value)
    else:
        return str(dt_value)

def _generate_html_report(report_data):
    """Generate a formatted HTML report from the audit data"""
    
    # Extract key data for easier access
    metadata = report_data['report_metadata']
    audit_info = report_data['audit_information']
    processing = report_data['processing_summary']
    compliance = report_data['compliance_summary']
    documents = report_data['documents_processed']
    findings = report_data['key_findings']
    recommendations = report_data['recommendations']
    technical = report_data['technical_details']
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Audit Report - Audit {audit_info['audit_id']}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #2c3e50;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #2c3e50;
                margin: 0;
                font-size: 2.5em;
            }}
            .header p {{
                color: #7f8c8d;
                margin: 10px 0 0 0;
                font-size: 1.1em;
            }}
            .section {{
                margin-bottom: 30px;
                padding: 20px;
                border-left: 4px solid #3498db;
                background-color: #f8f9fa;
            }}
            .section h2 {{
                color: #2c3e50;
                margin-top: 0;
                font-size: 1.8em;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 10px;
            }}
            .section h3 {{
                color: #34495e;
                margin-top: 25px;
                font-size: 1.4em;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .info-card {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #e1e8ed;
            }}
            .info-card h4 {{
                color: #2c3e50;
                margin: 0 0 10px 0;
                font-size: 1.1em;
            }}
            .info-card p {{
                margin: 5px 0;
                color: #555;
            }}
            .status-badge {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.9em;
            }}
            .status-compliant {{ background-color: #d4edda; color: #155724; }}
            .status-non-compliant {{ background-color: #f8d7da; color: #721c24; }}
            .status-pending {{ background-color: #fff3cd; color: #856404; }}
            .status-ai {{ background-color: #d1ecf1; color: #0c5460; }}
            .document-item {{
                background: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }}
            .document-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }}
            .document-name {{
                font-weight: bold;
                color: #2c3e50;
            }}
            .confidence-score {{
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 15px;
                background-color: #ecf0f1;
            }}
            .recommendations {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 10px 0;
            }}
            .recommendations ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .recommendations li {{
                margin: 8px 0;
                color: #856404;
            }}
            .warning {{
                background: #f8d7da;
                border-left: 4px solid #dc3545;
                padding: 15px;
                margin: 10px 0;
                color: #721c24;
            }}
            .summary-stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px;
                border: 1px solid #e1e8ed;
            }}
            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                color: #2c3e50;
            }}
            .stat-label {{
                color: #7f8c8d;
                margin-top: 5px;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Audit Comprehensive Report</h1>
                <p>Generated on {_format_datetime(metadata['generated_at']).replace(' ', ' at ')} | Audit ID: {audit_info['audit_id']}</p>
            </div>
            
            {f'<div class="warning"><strong>⚠️ Warning:</strong> {audit_info["audit_assignment_issue"]}</div>' if audit_info.get('audit_assignment_issue') else ''}
            
            <div class="section">
                <h2>📋 Audit Information</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h4>Audit Details</h4>
                        <p><strong>Type:</strong> <span class="status-badge status-ai">{audit_info['audit_type']}</span></p>
                        <p><strong>Status:</strong> {audit_info['status']}</p>
                        <p><strong>Framework:</strong> {audit_info['framework_name']}</p>
                        <p><strong>Policy:</strong> {audit_info['policy_name']}</p>
                    </div>
                    <div class="info-card">
                        <h4>Assignment</h4>
                        <p><strong>Auditor:</strong> {audit_info['auditor_name']}</p>
                        <p><strong>Assignee:</strong> {audit_info['assignee_name']}</p>
                        <p><strong>Reviewer:</strong> {audit_info['reviewer_name']}</p>
                    </div>
                    <div class="info-card">
                        <h4>Timeline</h4>
                        <p><strong>Assigned:</strong> {_format_datetime(audit_info['assigned_date'])}</p>
                        <p><strong>Due Date:</strong> {audit_info['due_date']}</p>
                        <p><strong>Completed:</strong> {_format_datetime(audit_info['completion_date']) if audit_info['completion_date'] else 'Not completed'}</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📊 Processing Summary</h2>
                <div class="summary-stats">
                    <div class="stat-card">
                        <div class="stat-number">{processing['total_documents']}</div>
                        <div class="stat-label">Total Documents</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{processing['completed_documents']}</div>
                        <div class="stat-label">Completed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{processing['pending_documents']}</div>
                        <div class="stat-label">Pending</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{processing['completion_percentage']}%</div>
                        <div class="stat-label">Completion Rate</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>✅ Compliance Summary</h2>
                <div class="summary-stats">
                    <div class="stat-card">
                        <div class="stat-number" style="color: #28a745;">{compliance['compliant']}</div>
                        <div class="stat-label">Compliant</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #ffc107;">{compliance['partially_compliant']}</div>
                        <div class="stat-label">Partially Compliant</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #dc3545;">{compliance['non_compliant']}</div>
                        <div class="stat-label">Non-Compliant</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #6c757d;">{compliance['unknown']}</div>
                        <div class="stat-label">Unknown</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📄 Documents Processed</h2>
                {''.join([f'''
                <div class="document-item">
                    <div class="document-header">
                        <div class="document-name">{doc['document_name']}</div>
                    </div>
                    <p><strong>Type:</strong> {doc['document_type']} | <strong>Size:</strong> {doc['file_size']:,} bytes</p>
                    <p><strong>Processing:</strong> {doc['ai_processing_status']}</p>
                    <p><strong>Uploaded:</strong> {_format_datetime(doc['uploaded_date'])}</p>
                </div>
                ''' for doc in documents])}
            </div>
            
            <div class="section">
                <h2>🔍 Key Findings</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h4>Compliance Rate</h4>
                        <p><strong>{findings['overall_compliance_rate']}%</strong> overall compliance</p>
                    </div>
                    <div class="info-card">
                        <h4>Confidence Score</h4>
                        <p><strong>{findings['average_confidence_score']}</strong> average confidence</p>
                    </div>
                    <div class="info-card">
                        <h4>Attention Required</h4>
                        <p><strong>{findings['documents_requiring_attention']}</strong> documents need attention</p>
                    </div>
                    <div class="info-card">
                        <h4>Processing Success</h4>
                        <p><strong>{findings['processing_success_rate']}%</strong> success rate</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>💡 Recommendations</h2>
                <div class="recommendations">
                    <ul>
                        {''.join([f'<li>{rec}</li>' for rec in recommendations])}
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2>🔧 Technical Details</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h4>AI Processing</h4>
                        <p><strong>Method:</strong> OpenAI AI/ML Analysis</p>
                        <p><strong>Model:</strong> {technical['ai_model_used']}</p>
                        <p><strong>Generated:</strong> {_format_datetime(technical['processing_timestamp'])}</p>
                    </div>
                    <div class="info-card">
                        <h4>Data Sources</h4>
                        <p>{', '.join(technical['data_sources'])}</p>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>This report was generated automatically by the AI Audit System</p>
                <p>Report ID: {metadata['audit_id']} | Generated by User: {metadata['generated_by_user_id']}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content


def _make_heading_bold(heading):
    """Helper function to make a heading bold"""
    for run in heading.runs:
        run.bold = True
    return heading


def _add_bold_label_paragraph(doc, text):
    """Helper function to add a paragraph with bold label"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.bold = True
    return para


def _generate_word_document(report_data):
    """Generate a proper Word document (.docx) from the audit data"""
    
    # Extract key data for easier access
    metadata = report_data['report_metadata']
    audit_info = report_data['audit_information']
    processing = report_data['processing_summary']
    compliance = report_data['compliance_summary']
    documents = report_data['documents_processed']
    findings = report_data['key_findings']
    recommendations = report_data['recommendations']
    technical = report_data['technical_details']
    
    # Create a new Word document
    doc = Document()
    
    # Set document margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
    
    # Add title
    title = doc.add_heading('🤖 AI Audit Comprehensive Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _make_heading_bold(title)
    
    # Add subtitle
    subtitle = doc.add_paragraph(f'Generated on: {_format_datetime(metadata["generated_at"]).replace(" ", " at ")}')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle.runs[0]
    subtitle_run.font.size = Inches(0.15)
    
    audit_id_para = doc.add_paragraph(f'Audit ID: {audit_info["audit_id"]}')
    audit_id_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    audit_id_run = audit_id_para.runs[0]
    audit_id_run.font.size = Inches(0.15)
    
    doc.add_paragraph()  # Add space
    
    # Add warning if exists
    if audit_info.get('audit_assignment_issue'):
        warning = doc.add_paragraph(f'⚠️ WARNING: {audit_info["audit_assignment_issue"]}')
        warning_run = warning.runs[0]
        warning_run.font.color.rgb = None  # Red color
        warning_run.bold = True
        doc.add_paragraph()
    
    # Audit Information Section
    audit_info_heading = doc.add_heading('📋 Audit Information', level=1)
    _make_heading_bold(audit_info_heading)
    
    # Audit Details
    audit_details_heading = doc.add_heading('Audit Details', level=2)
    _make_heading_bold(audit_details_heading)
    doc.add_paragraph(f'• Type: {audit_info["audit_type"]}')
    doc.add_paragraph(f'• Status: {audit_info["status"]}')
    doc.add_paragraph(f'• Framework: {audit_info["framework_name"]}')
    doc.add_paragraph(f'• Policy: {audit_info["policy_name"]}')
    
    # Assignment
    assignment_heading = doc.add_heading('Assignment', level=2)
    _make_heading_bold(assignment_heading)
    doc.add_paragraph(f'• Auditor: {audit_info["auditor_name"]}')
    doc.add_paragraph(f'• Assignee: {audit_info["assignee_name"]}')
    doc.add_paragraph(f'• Reviewer: {audit_info["reviewer_name"]}')
    
    # Timeline
    timeline_heading = doc.add_heading('Timeline', level=2)
    _make_heading_bold(timeline_heading)
    doc.add_paragraph(f'• Assigned: {_format_datetime(audit_info["assigned_date"])}')
    doc.add_paragraph(f'• Due Date: {audit_info["due_date"]}')
    doc.add_paragraph(f'• Completed: {_format_datetime(audit_info["completion_date"]) if audit_info["completion_date"] else "Not completed"}')
    
    # Processing Summary Section
    processing_heading = doc.add_heading('📊 Processing Summary', level=1)
    _make_heading_bold(processing_heading)
    doc.add_paragraph(f'• Total Documents: {processing["total_documents"]}')
    doc.add_paragraph(f'• Completed: {processing["completed_documents"]}')
    doc.add_paragraph(f'• Pending: {processing["pending_documents"]}')
    doc.add_paragraph(f'• Completion Rate: {processing["completion_percentage"]}%')
    
    # Compliance Summary Section
    compliance_heading = doc.add_heading('✅ Compliance Summary', level=1)
    _make_heading_bold(compliance_heading)
    doc.add_paragraph(f'• Compliant: {compliance["compliant"]}')
    doc.add_paragraph(f'• Partially Compliant: {compliance["partially_compliant"]}')
    doc.add_paragraph(f'• Non-Compliant: {compliance["non_compliant"]}')
    doc.add_paragraph(f'• Unknown: {compliance["unknown"]}')
    
    # Documents Processed Section
    documents_heading = doc.add_heading('📄 Documents Processed', level=1)
    _make_heading_bold(documents_heading)
    for doc_item in documents:
        doc_name_heading = doc.add_heading(doc_item['document_name'], level=2)
        _make_heading_bold(doc_name_heading)
        doc.add_paragraph(f'• Type: {doc_item["document_type"]} | Size: {doc_item["file_size"]:,} bytes')
        doc.add_paragraph(f'• Processing: {doc_item["ai_processing_status"]}')
        doc.add_paragraph(f'• Uploaded: {_format_datetime(doc_item["uploaded_date"])}')
        
        # Add detailed compliance analysis if available
        compliance_analyses = doc_item.get('compliance_analyses')
        if compliance_analyses:
            # Handle nested structure - analyses might be in compliance_analyses.compliance_analyses
            if isinstance(compliance_analyses, dict) and 'compliance_analyses' in compliance_analyses:
                analyses_list = compliance_analyses['compliance_analyses']
            elif isinstance(compliance_analyses, list):
                analyses_list = compliance_analyses
            else:
                analyses_list = []
            
            if analyses_list and len(analyses_list) > 0:
                doc.add_paragraph()
                detailed_analysis_heading = doc.add_heading('Compliance Analysis Results', level=3)
                _make_heading_bold(detailed_analysis_heading)
                
                # Add summary info if available
                if isinstance(compliance_analyses, dict):
                    if compliance_analyses.get('processed_at'):
                        proc_para = doc.add_paragraph()
                        proc_run = proc_para.add_run('Processed At: ')
                        proc_run.bold = True
                        proc_para.add_run(_format_datetime(compliance_analyses["processed_at"]))
                    if compliance_analyses.get('confidence_score'):
                        conf_para = doc.add_paragraph()
                        conf_run = conf_para.add_run('Overall Confidence: ')
                        conf_run.bold = True
                        conf_para.add_run(str(compliance_analyses["confidence_score"]))
                    if compliance_analyses.get('compliance_status'):
                        status_para = doc.add_paragraph()
                        status_run = status_para.add_run('Overall Status: ')
                        status_run.bold = True
                        status_para.add_run(compliance_analyses["compliance_status"])
                    doc.add_paragraph()
                
                for i, analysis in enumerate(analyses_list[:10], 1):  # Limit to first 10 analyses
                    if isinstance(analysis, dict):
                        # Use compliance name as heading instead of "Analysis X:"
                        compliance_name = analysis.get('requirement_title', f'Compliance Requirement {i}')
                        compliance_heading = doc.add_heading(compliance_name, level=3)
                        _make_heading_bold(compliance_heading)
                        
                        # Add requirement description
                        if analysis.get('requirement_description'):
                            desc_para = doc.add_paragraph()
                            desc_run = desc_para.add_run('Description: ')
                            desc_run.bold = True
                            desc_para.add_run(analysis["requirement_description"])
                        
                        # Add compliance score (formerly relevance score)
                        if analysis.get('relevance'):
                            score_para = doc.add_paragraph()
                            score_run = score_para.add_run('Compliance Score: ')
                            score_run.bold = True
                            score_para.add_run(str(analysis["relevance"]))
                        
                        # Add evidence found
                        if analysis.get('evidence'):
                            evidence = analysis['evidence']
                            evid_para = doc.add_paragraph()
                            evid_run = evid_para.add_run('Evidence Found: ')
                            evid_run.bold = True
                            if isinstance(evidence, list):
                                evid_para.add_run(", ".join(evidence[:5]))  # Limit to first 5
                            else:
                                evid_para.add_run(str(evidence))
                        
                        # Add gap (formerly missing elements)
                        if analysis.get('missing'):
                            missing_elements = analysis['missing']
                            gap_para = doc.add_paragraph()
                            gap_run = gap_para.add_run('Gap: ')
                            gap_run.bold = True
                            if isinstance(missing_elements, list):
                                gap_para.add_run(", ".join(missing_elements[:5]))  # Limit to first 5
                            else:
                                gap_para.add_run(str(missing_elements))
                        
                        # Add recommendations for this compliance
                        recommendations_para = doc.add_paragraph()
                        rec_run = recommendations_para.add_run('Recommendations: ')
                        rec_run.bold = True
                        
                        # Generate recommendations based on compliance score and gaps
                        compliance_score = float(analysis.get('relevance', 0))
                        missing_elements = analysis.get('missing', [])
                        
                        recommendations = []
                        if compliance_score < 0.4:
                            recommendations.append("CRITICAL: Immediate action required - document does not adequately address this requirement")
                        elif compliance_score < 0.6:
                            recommendations.append("HIGH PRIORITY: Significant improvements needed to meet compliance standards")
                        elif compliance_score < 0.8:
                            recommendations.append("MEDIUM PRIORITY: Minor improvements recommended for better compliance")
                        else:
                            recommendations.append("LOW PRIORITY: Document adequately addresses this requirement")
                        
                        if missing_elements:
                            if isinstance(missing_elements, list):
                                recommendations.append(f"Address missing elements: {', '.join(missing_elements[:3])}")
                            else:
                                recommendations.append(f"Address missing elements: {missing_elements}")
                        
                        if not recommendations:
                            recommendations.append("Review and enhance document content to improve compliance coverage")
                        
                        recommendations_para.add_run("; ".join(recommendations))
                        
                        doc.add_paragraph()  # Add space between analyses
                
                if len(analyses_list) > 10:
                    doc.add_paragraph(f'... and {len(analyses_list) - 10} more analyses available')
            else:
                doc.add_paragraph('• Detailed Analysis: No detailed analysis available')
        else:
            doc.add_paragraph('• Detailed Analysis: No detailed analysis available')
        
        doc.add_paragraph()
    
    # Key Findings Section
    findings_heading = doc.add_heading('🔍 Key Findings', level=1)
    _make_heading_bold(findings_heading)
    doc.add_paragraph(f'• Overall Compliance Rate: {findings["overall_compliance_rate"]}%')
    doc.add_paragraph(f'• Average Confidence Score: {findings["average_confidence_score"]}')
    doc.add_paragraph(f'• Documents Requiring Attention: {findings["documents_requiring_attention"]}')
    doc.add_paragraph(f'• Processing Success Rate: {findings["processing_success_rate"]}%')
    
    # Recommendations Section
    recommendations_heading = doc.add_heading('💡 Recommendations', level=1)
    _make_heading_bold(recommendations_heading)
    for rec in recommendations:
        doc.add_paragraph(f'• {rec}')
    
    # Technical Details Section
    technical_heading = doc.add_heading('🔧 Technical Details', level=1)
    _make_heading_bold(technical_heading)
    doc.add_paragraph(f'• Method: OpenAI AI/ML Analysis')
    doc.add_paragraph(f'• Model: {technical["ai_model_used"]}')
    doc.add_paragraph(f'• Generated: {_format_datetime(technical["processing_timestamp"])}')
    doc.add_paragraph(f'• Data Sources: {", ".join(technical["data_sources"])}')
    
    # Footer
    doc.add_paragraph()
    footer = doc.add_paragraph('This report was generated automatically by the AI Audit System')
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.runs[0]
    footer_run.font.size = Inches(0.12)
    
    footer2 = doc.add_paragraph(f'Report ID: {metadata["audit_id"]} | Generated by User: {metadata["generated_by_user_id"]}')
    footer2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer2_run = footer2.runs[0]
    footer2_run.font.size = Inches(0.12)
    
    # Save document to bytes
    import io
    doc_buffer = io.BytesIO()
    doc.save(doc_buffer)
    doc_buffer.seek(0)
    
    return doc_buffer.getvalue()


def _generate_audit_recommendations(compliance_summary, documents, audit_row=None):
    """Generate recommendations based on audit results"""
    recommendations = []
    
    total_docs = sum(compliance_summary.values())
    if total_docs == 0:
        return ["No documents processed for analysis"]
    
    # Audit assignment recommendations
    if audit_row:
        is_ai_audit = audit_row[1] == 'A'
        if is_ai_audit:
            # For AI audits, only reviewer is required
            if not audit_row[11]:
                recommendations.append("ADMINISTRATIVE: AI audit assignment is incomplete. Please assign a reviewer through the Assign Audit page.")
        else:
            # For regular audits, auditor, assignee, and reviewer are required
            if not audit_row[9] or not audit_row[10] or not audit_row[11]:
                recommendations.append("ADMINISTRATIVE: Regular audit assignment is incomplete. Please assign auditor, assignee, and reviewer through the Assign Audit page.")
    
    # Compliance-based recommendations
    non_compliant_rate = compliance_summary['non_compliant'] / total_docs
    if non_compliant_rate > 0.3:
        recommendations.append("HIGH PRIORITY: Significant number of non-compliant documents detected. Immediate remediation required.")
    
    partially_compliant_rate = compliance_summary['partially_compliant'] / total_docs
    if partially_compliant_rate > 0.4:
        recommendations.append("MEDIUM PRIORITY: Many documents show partial compliance. Review and strengthen controls.")
    
    # Processing-based recommendations
    failed_docs = sum(1 for doc in documents if doc['ai_processing_status'] == 'failed')
    if failed_docs > 0:
        recommendations.append(f"TECHNICAL: {failed_docs} document(s) failed AI processing. Review document formats and retry processing.")
    
    # Confidence-based recommendations
    low_confidence_docs = sum(1 for doc in documents if (doc['confidence_score'] or 0) < 0.6)
    if low_confidence_docs > 0:
        recommendations.append(f"QUALITY: {low_confidence_docs} document(s) have low confidence scores. Consider manual review or document improvement.")
    
    # General recommendations
    if compliance_summary['compliant'] / total_docs > 0.8:
        recommendations.append("POSITIVE: High compliance rate achieved. Continue monitoring and maintain current controls.")
    else:
        recommendations.append("IMPROVEMENT NEEDED: Overall compliance rate below 80%. Implement additional controls and training.")
    
    return recommendations


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def test_structured_compliance_api(request, audit_id):
    """Test the structured compliance checking with a sample document"""
    try:
        from .structured_compliance_checker import check_document_structured_compliance
        
        # Sample audit document for testing
        sample_document = """
        AUDIT REPORT - DATA SECURITY COMPLIANCE
        
        Executive Summary:
        This audit was conducted to assess our data security controls and ensure compliance 
        with our Data Protection Policy and Access Control Standards.
        
        Key Findings:
        1. Data Encryption: All sensitive data is encrypted using AES-256 encryption
        2. Access Controls: User access is properly managed with role-based permissions
        3. Audit Logging: Comprehensive audit logs are maintained for all data access
        4. Data Retention: Data retention policies are properly implemented
        
        Technical Details:
        - Database encryption: AES-256 enabled
        - Access control: Multi-factor authentication implemented
        - Audit trail: All access attempts logged with timestamps
        - Data classification: Sensitive data properly labeled
        
        Compliance Status:
        - Data Protection Policy: COMPLIANT
        - Access Control Standards: COMPLIANT
        - Audit Requirements: COMPLIANT
        """
        
        # Test structured compliance checking
        result = check_document_structured_compliance(
            audit_id=audit_id,
            document_id="test_doc_001",
            document_text=sample_document,
            document_name="Sample Audit Report"
        )
        
        return Response({
            'success': True,
            'message': 'Structured compliance checking test completed',
            'audit_id': audit_id,
            'test_result': result
        })
        
    except Exception as e:
        logger.error(f"❌ Error testing structured compliance: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
