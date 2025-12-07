from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from grc.models import FileOperations, Users
from datetime import datetime
import logging
import os
import tempfile
from grc.routes.Global.s3_fucntions import create_direct_mysql_client
from rest_framework.parsers import MultiPartParser, FormParser
import re

logger = logging.getLogger(__name__)

# Modules we never want to expose to the UI
EXCLUDED_MODULES = {'synthetic'}


def apply_module_exclusions(queryset):
    """
    Remove modules that should not surface in API responses.
    """
    for module_name in EXCLUDED_MODULES:
        queryset = queryset.exclude(module__iexact=module_name)
    return queryset


def get_user_display_name(user_id):
    """
    Get user display name from user_id
    Returns full name (FirstName LastName) or username as fallback
    """
    try:
        if not user_id:
            return 'Unknown User'
        
        # Try to get user by UserId (integer)
        try:
            user_id_int = int(user_id)
            user = Users.objects.get(UserId=user_id_int)
            if user.FirstName and user.LastName:
                return f"{user.FirstName} {user.LastName}"
            elif user.UserName:
                return user.UserName
            else:
                return f"User {user_id}"
        except (ValueError, Users.DoesNotExist):
            # If user_id is not an integer or user not found, try as username
            try:
                user = Users.objects.get(UserName=user_id)
                if user.FirstName and user.LastName:
                    return f"{user.FirstName} {user.LastName}"
                else:
                    return user.UserName
            except Users.DoesNotExist:
                return str(user_id)  # Return original user_id if not found
    except Exception as e:
        logger.warning(f"Error getting user name for {user_id}: {str(e)}")
        return str(user_id)


@api_view(['GET'])
def get_documents(request):
    """
    Fetch documents from FileOperations table
    Optionally filter by module: policy, audit, incident, risk
    """
    try:
        # Get query parameters
        module_filter = request.GET.get('module', 'all')
        search_query = request.GET.get('search', '')
        file_type_filter = request.GET.get('file_type', 'all')
        
        # Base query - get all uploads (completed, pending, failed)
        # Exclude downloads, exports, and system-generated files
        queryset = FileOperations.objects.filter(
            operation_type='upload'
        ).exclude(
            user_id='export_user'  # Exclude system-generated exports
        )
        queryset = apply_module_exclusions(queryset)
        
        # Filter by module
        if module_filter and module_filter != 'all':
            queryset = queryset.filter(module__iexact=module_filter)
        
        # Search filter
        if search_query:
            queryset = queryset.filter(
                Q(file_name__icontains=search_query) |
                Q(original_name__icontains=search_query) |
                Q(user_id__icontains=search_query)
            )
        
        # File type filter
        if file_type_filter and file_type_filter != 'all':
            queryset = queryset.filter(file_type__iexact=file_type_filter)
        
        # Order by most recent first
        queryset = queryset.order_by('-created_at')
        
        # Build response
        documents = []
        for file_op in queryset:
            # Determine file type from file_type or content_type
            file_ext = file_op.file_type or ''
            if not file_ext and file_op.content_type:
                # Extract extension from content_type
                if 'pdf' in file_op.content_type.lower():
                    file_ext = 'pdf'
                elif 'word' in file_op.content_type.lower() or 'document' in file_op.content_type.lower():
                    file_ext = 'doc'
                elif 'excel' in file_op.content_type.lower() or 'spreadsheet' in file_op.content_type.lower():
                    file_ext = 'xlsx'
                elif 'csv' in file_op.content_type.lower():
                    file_ext = 'csv'
                else:
                    file_ext = 'file'
            
            # Format file size
            file_size_str = format_file_size(file_op.file_size)
            
            # Get display name - try to get originalName from metadata.upload_response first
            display_name = file_op.file_name or 'Unknown File'
            
            # Try to extract originalName from metadata.upload_response
            if file_op.metadata:
                try:
                    import json
                    metadata = json.loads(file_op.metadata) if isinstance(file_op.metadata, str) else file_op.metadata
                    if metadata and 'upload_response' in metadata:
                        upload_response = metadata['upload_response']
                        if upload_response and 'originalName' in upload_response:
                            display_name = upload_response['originalName']
                            # logger.info(f"Using originalName from upload_response: {display_name}")
                        else:
                            logger.info(f"No originalName in upload_response for file {file_op.id}")
                    else:
                        logger.info(f"No upload_response in metadata for file {file_op.id}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Error parsing metadata for file {file_op.id}: {str(e)}")
            
            # If no originalName found, use original_name as fallback
            if display_name == file_op.file_name:
                display_name = file_op.original_name or file_op.file_name or 'Unknown File'
                # logger.info(f"Using fallback name: {display_name}")
            
            # Get user display name
            user_display_name = get_user_display_name(file_op.user_id)
            
            documents.append({
                'id': file_op.id,
                'name': display_name,
                'fileType': file_ext.lower(),
                'fileSize': file_size_str,
                'uploadTime': file_op.created_at.isoformat() if file_op.created_at else None,
                'uploadedBy': user_display_name,
                'module': file_op.module or 'general',
                's3Url': file_op.s3_url or '',
                's3Key': file_op.s3_key or '',
                's3Bucket': file_op.s3_bucket or '',
                'description': f'{file_op.module or "General"} document uploaded on {file_op.created_at.strftime("%Y-%m-%d") if file_op.created_at else "unknown date"}',
                'status': file_op.status,
                'contentType': file_op.content_type or ''
            })
        
        return Response({
            'success': True,
            'count': len(documents),
            'documents': documents
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'documents': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_document_counts(request):
    """
    Get document counts by module
    """
    try:
        # Base query - all uploads (exclude downloads, exports, and system files)
        base_query = FileOperations.objects.filter(
            operation_type='upload'
        ).exclude(
            user_id='export_user'  # Exclude system-generated exports
        )
        base_query = apply_module_exclusions(base_query)
        
        counts = {
            'all': base_query.count(),
            'policy': base_query.filter(module__iexact='policy').count(),
            'audit': base_query.filter(module__iexact='audit').count(),
            'incident': base_query.filter(module__iexact='incident').count(),
            'risk': base_query.filter(module__iexact='risk').count(),
            'event': base_query.filter(module__iexact='event').count()
        }
        
        return Response({
            'success': True,
            'counts': counts
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching document counts: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'counts': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def format_file_size(size_in_bytes):
    """
    Format file size from bytes to human-readable format
    """
    if not size_in_bytes:
        return "Unknown size"
    
    size = float(size_in_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    
    return f"{size:.1f} PB"


def sanitize_filename_part(value: str) -> str:
    """
    Sanitize a string so it is safe to use as part of a filename.
    Converts to lowercase, replaces non-alphanumeric characters with underscores,
    and trims redundant underscores.
    """
    if not value:
        return 'na'
    
    value = value.strip().lower()
    value = re.sub(r'[^a-z0-9]+', '_', value)
    value = value.strip('_')
    return value or 'na'


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    Upload document with optional framework selection
    Naming convention: framework_module_datetime.filetype (if framework selected)
    Or: module_datetime.filetype (if no framework)
    """
    try:
        # Get form data
        uploaded_file = request.FILES.get('file')
        module = request.data.get('module')
        framework = request.data.get('framework', '')
        user_id = request.data.get('user_id', 'unknown-user')
        
        # Validation
        if not uploaded_file:
            return Response({
                'success': False,
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not module:
            return Response({
                'success': False,
                'error': 'Module is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get file extension
        original_filename = uploaded_file.name
        file_extension = os.path.splitext(original_filename)[1]  # includes the dot
        
        # Generate timestamp
        timestamp = datetime.now()
        date_part = timestamp.strftime('%Y%m%d')
        
        # Sanitize parts for filename
        base_prefix = 'document_handling'
        framework_part = sanitize_filename_part(framework) if framework else 'no_framework'
        module_part = sanitize_filename_part(module)
        original_base = os.path.splitext(original_filename)[0]
        original_part = sanitize_filename_part(original_base)
        extension_part = file_extension.lower()

        filename_parts = [
            base_prefix,
            date_part,
            framework_part,
            module_part,
            original_part
        ]
        custom_filename = f"{'_'.join(filename_parts)}{extension_part}"
        
        # logger.info(f"📤 Uploading document: {original_filename} -> {custom_filename}")
        # logger.info(f"   Module: {module}")
        # logger.info(f"   Framework: {framework or 'None'}")
        # logger.info(f"   User: {user_id}")
        
        # Save uploaded file temporarily
        temp_file_path = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                # Write uploaded file content to temp file
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # logger.info(f"📁 Temporary file created: {temp_file_path}")
            
            # Create S3 client
            s3_client = create_direct_mysql_client()
            
            # Upload to S3 with custom filename
            upload_result = s3_client.upload(
                file_path=temp_file_path,
                user_id=user_id,
                custom_file_name=custom_filename,
                module=module
            )
            
            if upload_result.get('success'):
                # logger.info(f"✅ Upload successful: {upload_result.get('file_info', {}).get('storedName')}")
                
                operation_id = upload_result.get('operation_id')

                # Update FileOperations record to reflect custom filename
                if operation_id:
                    try:
                        FileOperations.objects.filter(id=operation_id).update(
                            file_name=custom_filename,
                            original_name=custom_filename
                        )
                        # logger.info(f"📝 FileOperations record {operation_id} updated with custom filename")
                    except Exception as db_err:
                        logger.warning(f"⚠️ Failed to update FileOperations record {operation_id}: {db_err}")
                
                return Response({
                    'success': True,
                    'message': 'Document uploaded successfully',
                    'stored_name': upload_result.get('file_info', {}).get('storedName'),
                    'original_name': custom_filename,
                    'custom_name': custom_filename,
                    's3_url': upload_result.get('file_info', {}).get('url'),
                    's3_key': upload_result.get('file_info', {}).get('s3Key'),
                    'operation_id': operation_id,
                    'file_size': upload_result.get('file_info', {}).get('size'),
                    'module': module,
                    'framework': framework or None
                }, status=status.HTTP_200_OK)
            else:
                error_msg = upload_result.get('error', 'Unknown error during upload')
                logger.error(f"❌ Upload failed: {error_msg}")
                return Response({
                    'success': False,
                    'error': error_msg
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    # logger.info(f"🗑️  Temporary file deleted: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to delete temporary file: {str(e)}")
    
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)