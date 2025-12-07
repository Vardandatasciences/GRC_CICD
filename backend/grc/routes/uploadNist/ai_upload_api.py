"""
AI Upload API - Django REST API for Framework Upload and Processing

This module provides REST API endpoints for:
1. Uploading PDF files
2. Processing PDFs through the complete pipeline
3. Tracking processing status
4. Retrieving results

Flow:
1. Upload PDF -> Creates upload_{userid} folder in MEDIA_ROOT
2. Extract PDF Index -> Saves index JSON
3. Extract Content -> Creates section PDFs and text
4. Extract Policies -> Generates policies with AI
5. (Optional) Generate Compliance -> Creates compliance and risk records
"""

import os
import sys
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Import the processing modules
from . import ai_upload
from . import pdf_index_extractor
from . import index_content_extractor
from . import policy_extractor_enhanced
from . import compliance_generator


# Global dictionary to store processing status
PROCESSING_STATUS = {}


def get_media_root():
    """Get the MEDIA_ROOT path from Django settings."""
    return Path(settings.MEDIA_ROOT)


def update_status(task_id: str, status: str, progress: int, message: str, data: dict = None):
    """
    Update processing status for a task.
    
    Args:
        task_id: Unique task identifier
        status: Status string (uploading, processing, completed, error)
        progress: Progress percentage (0-100)
        message: Status message
        data: Additional data dictionary
    """
    PROCESSING_STATUS[task_id] = {
        'task_id': task_id,
        'status': status,
        'progress': progress,
        'message': message,
        'data': data or {},
        'updated_at': datetime.now().isoformat()
    }


@csrf_exempt
@require_http_methods(["POST"])
def upload_framework_pdf(request):
    """
    Step 1: Upload PDF file and create user folder.
    
    Request:
        - file: PDF file (multipart/form-data)
        - userid: User ID for folder creation
        
    Response:
        {
            "success": true,
            "task_id": "upload_1234567890_user123",
            "message": "File uploaded successfully",
            "user_folder": "upload_123",
            "file_path": "upload_123/document.pdf",
            "file_size": 1234567,
            "file_name": "document.pdf"
        }
    """
    try:
        # Validate request
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file provided'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        userid = request.POST.get('userid', 'default')
        
        # Validate file type
        if not uploaded_file.name.lower().endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'Only PDF files are supported'
            }, status=400)
        
        # Generate task ID
        timestamp = int(time.time())
        task_id = f"upload_{timestamp}_{userid}"
        
        # Update status
        update_status(task_id, 'uploading', 5, 'Creating user folder...')
        
        # Step 1: Create/recreate user folder in MEDIA_ROOT
        media_root = get_media_root()
        folder_name = f"upload_{userid}"
        user_folder_path = media_root / folder_name
        
        # Delete folder if it exists
        if user_folder_path.exists():
            import shutil
            shutil.rmtree(user_folder_path)
            print(f"[INFO] Deleted existing folder: {user_folder_path}")
        
        # Create new folder
        user_folder_path.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Created folder: {user_folder_path}")
        
        # Update status
        update_status(task_id, 'uploading', 15, 'Saving uploaded file...')
        
        # Step 2: Save uploaded file
        file_path = user_folder_path / uploaded_file.name
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        file_size = file_path.stat().st_size
        
        # Update status
        update_status(task_id, 'uploaded', 20, 'File uploaded successfully', {
            'file_name': uploaded_file.name,
            'file_path': str(file_path),
            'file_size': file_size,
            'user_folder': folder_name
        })
        
        print(f"[SUCCESS] File uploaded: {file_path} ({file_size} bytes)")
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'message': 'File uploaded successfully',
            'user_folder': folder_name,
            'file_path': str(file_path.relative_to(media_root)),
            'file_size': file_size,
            'file_name': uploaded_file.name
        })
        
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_pdf_processing(request):
    """
    Step 2-4: Start PDF processing pipeline (index extraction, content extraction, policy extraction).
    
    Request Body (JSON):
        {
            "task_id": "upload_1234567890_user123",
            "userid": "123",
            "file_name": "document.pdf",
            "include_compliance": false  // Optional: Generate compliance records
        }
        
    Response:
        {
            "success": true,
            "task_id": "upload_1234567890_user123",
            "message": "Processing started",
            "status": "processing"
        }
    """
    try:
        # Parse request body
        body = json.loads(request.body)
        task_id = body.get('task_id')
        userid = body.get('userid', 'default')
        file_name = body.get('file_name')
        include_compliance = body.get('include_compliance', False)
        
        if not task_id or not file_name:
            return JsonResponse({
                'success': False,
                'error': 'task_id and file_name are required'
            }, status=400)
        
        # Get paths
        media_root = get_media_root()
        user_folder = media_root / f"upload_{userid}"
        pdf_path = user_folder / file_name
        
        # Validate PDF exists
        if not pdf_path.exists():
            return JsonResponse({
                'success': False,
                'error': f'PDF file not found: {pdf_path}'
            }, status=404)
        
        # Update status
        update_status(task_id, 'processing', 25, 'Starting PDF processing...')
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_pdf_background,
            args=(task_id, userid, str(pdf_path), include_compliance)
        )
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'message': 'Processing started',
            'status': 'processing'
        })
        
    except Exception as e:
        print(f"[ERROR] Failed to start processing: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def process_pdf_background(task_id: str, userid: str, pdf_path: str, include_compliance: bool = False):
    """
    Background task to process PDF through the complete pipeline.
    
    Args:
        task_id: Task identifier
        userid: User ID
        pdf_path: Full path to PDF file
        include_compliance: Whether to generate compliance records
    """
    try:
        media_root = get_media_root()
        user_folder = media_root / f"upload_{userid}"
        pdf_path_obj = Path(pdf_path)
        pdf_name = pdf_path_obj.stem
        
        # Step 1: Extract Index
        update_status(task_id, 'processing', 30, 'Extracting PDF index...')
        print(f"[STEP 1] Extracting index from {pdf_path}...")
        
        index_json_path = user_folder / f"{pdf_name}_index.json"
        try:
            index_data = pdf_index_extractor.extract_and_save_index(
                pdf_path=pdf_path,
                output_path=str(index_json_path),
                prefer_toc=True
            )
            index_items_count = len(index_data.get('items', []))
            print(f"[SUCCESS] Extracted {index_items_count} index items")
            
            update_status(task_id, 'processing', 40, f'Index extracted: {index_items_count} items', {
                'index_json': str(index_json_path.relative_to(media_root)),
                'index_items_count': index_items_count
            })
        except Exception as e:
            raise Exception(f"Index extraction failed: {e}")
        
        # Step 2: Extract Sections
        update_status(task_id, 'processing', 45, 'Extracting sections and creating PDFs...')
        print(f"[STEP 2] Extracting sections...")
        
        sections_dir = user_folder / f"sections_{pdf_name}"
        try:
            manifest = index_content_extractor.process_pdf_sections(
                pdf_path=pdf_path,
                index_json_path=str(index_json_path),
                output_dir=str(sections_dir),
                verbose=True
            )
            sections_count = len(manifest.get('sections_written', []))
            print(f"[SUCCESS] Extracted {sections_count} sections")
            
            update_status(task_id, 'processing', 60, f'Sections extracted: {sections_count} sections', {
                'sections_dir': str(sections_dir.relative_to(media_root)),
                'sections_count': sections_count
            })
        except Exception as e:
            raise Exception(f"Section extraction failed: {e}")
        
        # Step 3: Extract Policies
        update_status(task_id, 'processing', 65, 'Extracting policies using AI...')
        print(f"[STEP 3] Extracting policies...")
        
        policies_dir = user_folder / f"policies_{pdf_name}"
        try:
            policy_results = policy_extractor_enhanced.extract_policies(
                sections_dir=str(sections_dir),
                output_dir=str(policies_dir),
                verbose=True
            )
            
            if not policy_results.get('success'):
                raise Exception(policy_results.get('error', 'Policy extraction failed'))
            
            total_policies = policy_results['summary']['extraction_summary']['total_policies']
            total_subpolicies = policy_results['summary']['extraction_summary']['total_subpolicies']
            
            print(f"[SUCCESS] Extracted {total_policies} policies, {total_subpolicies} subpolicies")
            
            update_status(task_id, 'processing', 85, f'Policies extracted: {total_policies} policies', {
                'policies_dir': str(policies_dir.relative_to(media_root)),
                'total_policies': total_policies,
                'total_subpolicies': total_subpolicies
            })
        except Exception as e:
            raise Exception(f"Policy extraction failed: {e}")
        
        # Step 4 (Optional): Generate Compliance
        compliance_data = None
        risk_data = None
        
        if include_compliance:
            update_status(task_id, 'processing', 90, 'Generating compliance records...')
            print(f"[STEP 4] Generating compliance records...")
            
            try:
                # Convert policies to Excel
                policies_json_path = policies_dir / "all_policies.json"
                subpolicies_excel_path = user_folder / f"{pdf_name}_subpolicies.xlsx"
                
                conversion_success = ai_upload.convert_policies_to_excel(
                    policies_json_path=str(policies_json_path),
                    output_excel_path=str(subpolicies_excel_path)
                )
                
                if conversion_success:
                    # Generate compliance and risk
                    compliance_output_dir = user_folder / f"compliance_risk_{pdf_name}"
                    
                    compliance_results = compliance_generator.generate_compliance_and_risk(
                        excel_file_path=str(subpolicies_excel_path),
                        output_prefix=f"{pdf_name}",
                        output_dir=str(compliance_output_dir),
                        save_to_file=True
                    )
                    
                    compliance_data, risk_data, compliance_file, risk_file = compliance_results
                    
                    print(f"[SUCCESS] Generated {len(compliance_data)} compliance, {len(risk_data)} risk records")
            except Exception as e:
                print(f"[WARN] Compliance generation failed: {e}")
        
        # Final status
        duration = time.time()
        
        final_data = {
            'user_folder': f"upload_{userid}",
            'pdf_name': pdf_name,
            'index_json': str(index_json_path.relative_to(media_root)),
            'sections_dir': str(sections_dir.relative_to(media_root)),
            'policies_dir': str(policies_dir.relative_to(media_root)),
            'stats': {
                'index_items': index_items_count,
                'sections': sections_count,
                'policies': total_policies,
                'subpolicies': total_subpolicies,
                'compliance_records': len(compliance_data) if compliance_data else 0,
                'risk_records': len(risk_data) if risk_data else 0
            }
        }
        
        update_status(task_id, 'completed', 100, 'Processing completed successfully', final_data)
        print(f"[SUCCESS] Processing completed for task {task_id}")
        
    except Exception as e:
        error_message = f"Processing failed: {str(e)}"
        print(f"[ERROR] {error_message}")
        update_status(task_id, 'error', -1, error_message)


@csrf_exempt
@require_http_methods(["GET"])
def get_processing_status(request, task_id):
    """
    Get the current processing status of a task.
    
    Response:
        {
            "success": true,
            "task_id": "upload_1234567890_user123",
            "status": "processing",
            "progress": 65,
            "message": "Extracting policies...",
            "data": {...},
            "updated_at": "2025-01-10T12:34:56"
        }
    """
    try:
        if task_id not in PROCESSING_STATUS:
            return JsonResponse({
                'success': False,
                'error': 'Task not found'
            }, status=404)
        
        status_data = PROCESSING_STATUS[task_id]
        return JsonResponse({
            'success': True,
            **status_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_extracted_data(request, userid):
    """
    Get extracted data for a user (policies, sections, etc.).
    
    Response:
        {
            "success": true,
            "user_folder": "upload_123",
            "files": {
                "index_json": "path/to/index.json",
                "sections_dir": "path/to/sections/",
                "policies_dir": "path/to/policies/",
                "policies_json": "path/to/all_policies.json"
            },
            "stats": {...}
        }
    """
    try:
        media_root = get_media_root()
        user_folder = media_root / f"upload_{userid}"
        
        if not user_folder.exists():
            return JsonResponse({
                'success': False,
                'error': f'User folder not found: upload_{userid}'
            }, status=404)
        
        # Find files
        files = {}
        stats = {}
        
        # Find index JSON
        index_files = list(user_folder.glob('*_index.json'))
        if index_files:
            files['index_json'] = str(index_files[0].relative_to(media_root))
            with open(index_files[0], 'r') as f:
                index_data = json.load(f)
                stats['index_items'] = len(index_data.get('items', []))
        
        # Find sections directory
        sections_dirs = list(user_folder.glob('sections_*'))
        if sections_dirs:
            files['sections_dir'] = str(sections_dirs[0].relative_to(media_root))
            # Count PDFs in sections
            pdf_count = len(list(sections_dirs[0].glob('**/*.pdf')))
            stats['sections'] = pdf_count
        
        # Find policies directory
        policies_dirs = list(user_folder.glob('policies_*'))
        if policies_dirs:
            files['policies_dir'] = str(policies_dirs[0].relative_to(media_root))
            
            # Find all_policies.json
            policies_json = policies_dirs[0] / 'all_policies.json'
            if policies_json.exists():
                files['policies_json'] = str(policies_json.relative_to(media_root))
                with open(policies_json, 'r') as f:
                    policies_data = json.load(f)
                    # Count policies and subpolicies
                    total_policies = 0
                    total_subpolicies = 0
                    for section in policies_data:
                        policies = section.get('analysis', {}).get('policies', [])
                        total_policies += len(policies)
                        for policy in policies:
                            total_subpolicies += len(policy.get('subpolicies', []))
                    stats['policies'] = total_policies
                    stats['subpolicies'] = total_subpolicies
        
        return JsonResponse({
            'success': True,
            'user_folder': f"upload_{userid}",
            'files': files,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def list_user_folders(request):
    """
    List all user folders in MEDIA_ROOT.
    
    Response:
        {
            "success": true,
            "folders": [
                {
                    "folder_name": "upload_123",
                    "userid": "123",
                    "created_at": "2025-01-10T12:34:56",
                    "has_pdf": true,
                    "has_index": true,
                    "has_sections": true,
                    "has_policies": true
                }
            ]
        }
    """
    try:
        media_root = get_media_root()
        folders = []
        
        for folder_path in media_root.glob('upload_*'):
            if folder_path.is_dir():
                folder_name = folder_path.name
                userid = folder_name.replace('upload_', '')
                
                # Get creation time
                created_at = datetime.fromtimestamp(folder_path.stat().st_ctime).isoformat()
                
                # Check what files exist
                has_pdf = len(list(folder_path.glob('*.pdf'))) > 0
                has_index = len(list(folder_path.glob('*_index.json'))) > 0
                has_sections = len(list(folder_path.glob('sections_*'))) > 0
                has_policies = len(list(folder_path.glob('policies_*'))) > 0
                
                folders.append({
                    'folder_name': folder_name,
                    'userid': userid,
                    'created_at': created_at,
                    'has_pdf': has_pdf,
                    'has_index': has_index,
                    'has_sections': has_sections,
                    'has_policies': has_policies
                })
        
        # Sort by creation time (newest first)
        folders.sort(key=lambda x: x['created_at'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'folders': folders,
            'count': len(folders)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

