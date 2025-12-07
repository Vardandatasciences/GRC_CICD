from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os
import shutil
import time
import threading
from pathlib import Path

# Import the processing modules
# COMMENTED OUT OLD IMPORT - Using new AI upload API
# from ..uploadNist.all_integrated_upload import upload_pdf_and_extract_complete
from ..uploadNist import ai_upload
from ..uploadNist import pdf_index_extractor
from ..uploadNist import index_content_extractor
from ..uploadNist import policy_extractor_enhanced

# Global progress tracking
processing_status = {}

def update_progress(task_id, progress, message):
    """Update processing progress"""
    processing_status[task_id] = {
        'progress': progress,
        'message': message,
        'timestamp': time.time()
    }

def create_user_folder(userid):
    """
    Creates a folder with the name 'upload_userid' where userid is the provided user ID.
    If folder exists, tries to delete it and creates a new one.
    Handles OneDrive sync issues with retry logic.
    
    Args:
        userid (str): The user ID to create the folder for
        
    Returns:
        str: The path of the created folder
        
    Raises:
        OSError: If there's an error creating the folder after retries
    """
    # Create folder name with the user ID
    folder_name = f"upload_{userid}"
    
    # Create the folder path in MEDIA_ROOT
    folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # Delete folder if it exists (with retry logic for OneDrive sync issues)
            if os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    print(f"Deleted existing folder: {folder_path}")
                    # Small delay after deletion to let OneDrive sync
                    time.sleep(0.5)
                except (OSError, PermissionError) as delete_error:
                    if attempt < max_retries - 1:
                        print(f"Warning: Could not delete folder (attempt {attempt + 1}/{max_retries}): {delete_error}")
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        # If we can't delete, try to use existing folder or clear contents
                        print(f"Warning: Could not delete folder after {max_retries} attempts. Trying to clear contents instead...")
                        try:
                            # Clear folder contents instead of deleting
                            for item in os.listdir(folder_path):
                                item_path = os.path.join(folder_path, item)
                                if os.path.isdir(item_path):
                                    shutil.rmtree(item_path, ignore_errors=True)
                                else:
                                    try:
                                        os.remove(item_path)
                                    except (OSError, PermissionError):
                                        pass
                            print(f"Cleared contents of existing folder: {folder_path}")
                        except Exception as clear_error:
                            print(f"Warning: Could not clear folder contents: {clear_error}")
                            # Continue anyway - will try to create/use existing folder
            
            # Create the new folder (or ensure it exists)
            os.makedirs(folder_path, exist_ok=True)
            print(f"Created/verified folder: {folder_path}")
            
            return folder_path
            
        except (OSError, PermissionError) as e:
            if attempt < max_retries - 1:
                print(f"Error creating folder '{folder_name}' (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Error creating folder '{folder_name}' after {max_retries} attempts: {e}")
                raise OSError(f"Failed to create folder '{folder_name}' after {max_retries} attempts. "
                            f"This may be due to OneDrive sync locking the folder. "
                            f"Original error: {e}")
    
    # Should not reach here, but just in case
    raise OSError(f"Failed to create folder '{folder_name}'")

def save_uploaded_file(uploaded_file, user_folder):
    """
    Save the uploaded file to the user's folder.
    
    Args:
        uploaded_file: The uploaded file object
        user_folder (str): Path to the user's folder
        
    Returns:
        str: Path to the saved file
    """
    try:
        # Create the full file path
        file_path = os.path.join(user_folder, uploaded_file.name)
        
        # Save the file
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        print(f"File saved successfully to: {file_path}")
        return file_path
        
    except Exception as e:
        print(f"Error saving file: {e}")
        raise

def process_document_background(userid, file_path, task_id):
    """
    Background processing function using NEW AI upload pipeline.
    
    Args:
        userid (str): The user ID
        file_path (str): Path to the uploaded file
        task_id (str): Task ID for progress tracking
    """
    try:
        update_progress(task_id, 10, "Starting document processing...")
        
        # Get MEDIA_ROOT
        media_root = ai_upload.get_media_root()
        user_folder = media_root / f"upload_{userid}"
        pdf_path = Path(file_path)
        pdf_name = pdf_path.stem
        
        # Step 1: Extract Index
        update_progress(task_id, 30, "Extracting PDF index...")
        print(f"[STEP 1] Extracting index from {file_path}...")
        
        index_json_path = user_folder / f"{pdf_name}_index.json"
        try:
            index_data = pdf_index_extractor.extract_and_save_index(
                pdf_path=str(file_path),
                output_path=str(index_json_path),
                prefer_toc=True
            )
            index_items_count = len(index_data.get('items', []))
            print(f"[SUCCESS] Extracted {index_items_count} index items")
            update_progress(task_id, 40, f"Index extracted: {index_items_count} items")
        except Exception as e:
            update_progress(task_id, 100, f"Index extraction failed: {str(e)}")
            return
        
        # Step 2: Extract Sections
        update_progress(task_id, 45, "Extracting sections and creating PDFs...")
        print(f"[STEP 2] Extracting sections...")
        
        sections_dir = user_folder / f"sections_{pdf_name}"
        try:
            manifest = index_content_extractor.process_pdf_sections(
                pdf_path=str(file_path),
                index_json_path=str(index_json_path),
                output_dir=str(sections_dir),
                verbose=True
            )
            sections_count = len(manifest.get('sections_written', []))
            print(f"[SUCCESS] Extracted {sections_count} sections")
            update_progress(task_id, 60, f"Sections extracted: {sections_count} sections")
        except Exception as e:
            update_progress(task_id, 100, f"Section extraction failed: {str(e)}")
            return
        
        # Step 3: Extract Policies
        update_progress(task_id, 65, "Extracting policies using AI...")
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
            update_progress(task_id, 95, f"Policies extracted: {total_policies} policies")
            
            # Store final result
            processing_status[task_id]["result"] = {
                "status": "success",
                "data": {
                    'user_folder': f"upload_{userid}",
                    'index_items': index_items_count,
                    'sections': sections_count,
                    'policies': total_policies,
                    'subpolicies': total_subpolicies
                }
            }
            
            update_progress(task_id, 100, "Document processing completed successfully!")
            
        except Exception as e:
            update_progress(task_id, 100, f"Policy extraction failed: {str(e)}")
            return
            
    except Exception as e:
        update_progress(task_id, 100, f"Error during processing: {str(e)}")

@csrf_exempt
@require_http_methods(["POST"])
def upload_framework_file(request):
    """
    Main upload endpoint that handles file upload and starts processing.
    
    Expected request:
    - file: The uploaded file
    - userid: The user ID (optional, defaults to 'default')
    """
    try:
        # Check if file is provided
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Get user ID from request, default to 'default' if not provided
        userid = request.POST.get('userid', 'default')
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # Generate task ID for progress tracking
        task_id = f"upload_{int(time.time())}_{uploaded_file.name}"
        
        # Step 1: Create user folder (delete if exists, create new)
        try:
            user_folder = create_user_folder(userid)
        except Exception as e:
            return JsonResponse({'error': f'Failed to create user folder: {str(e)}'}, status=500)
        
        # Step 2: Save uploaded file to user folder
        try:
            file_path = save_uploaded_file(uploaded_file, user_folder)
        except Exception as e:
            return JsonResponse({'error': f'Failed to save uploaded file: {str(e)}'}, status=500)
        
        # Step 3: Start background processing
        update_progress(task_id, 5, "File uploaded successfully. Starting processing...")
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_document_background,
            args=(userid, file_path, task_id)
        )
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'message': 'File uploaded successfully. Processing started.',
            'filename': uploaded_file.name,
            'file_path': file_path,
            'file_size': uploaded_file.size,
            'task_id': task_id,
            'processing': True,
            'file_type': file_extension,
            'user_folder': user_folder
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_processing_status(request, task_id):
    """
    Get processing status for a task.
    
    Args:
        request: Django request object
        task_id (str): Task ID to get status for
    """
    try:
        if task_id in processing_status:
            status_data = processing_status[task_id]
            return JsonResponse({
                'task_id': task_id,
                'progress': status_data.get('progress', 0),
                'message': status_data.get('message', ''),
                'timestamp': status_data.get('timestamp', 0),
                'result': status_data.get('result', None)
            })
        else:
            return JsonResponse({
                'error': 'Task not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_sections(request, task_id):
    """
    Get extracted sections for a task.
    
    Args:
        request: Django request object
        task_id (str): Task ID to get sections for
    """
    try:
        if task_id not in processing_status:
            return JsonResponse({'error': 'Task not found'}, status=404)
        
        status_data = processing_status[task_id]
        result = status_data.get('result')
        
        if not result or result.get('status') != 'success':
            return JsonResponse({'error': 'Processing not completed or failed'}, status=400)
        
        # Extract sections from the result
        sections = []
        
        # If we have extracted sections directory
        if 'extracted_sections_dir' in result:
            sections_dir = result['extracted_sections_dir']
            if os.path.exists(sections_dir):
                # Read sections from the directory structure
                sections = read_sections_from_directory(sections_dir)
        
        return JsonResponse({
            'task_id': task_id,
            'sections': sections
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_sections_by_user(request, userid):
    """
    Get extracted sections with policies and subpolicies for a specific user.
    NOW READS FROM: upload_1/framework_data.json (consolidated JSON file)
    
    Args:
        request: Django request object
        userid (str): User ID to get sections for
    """
    try:
        print(f"[INFO] Getting sections for user: {userid}")
        
        # Import the consolidate_data module
        from .consolidate_data import load_consolidated_json
        
        # Load consolidated JSON (will create if doesn't exist)
        data = load_consolidated_json(userid)
        
        if not data:
            # Fallback: Check if we have basic files and return minimal data
            print(f"[WARNING] No consolidated data found, checking for basic files...")
            user_folder = os.path.join(settings.MEDIA_ROOT, f"upload_{userid}")
            
            if os.path.exists(user_folder):
                # Check if we have at least the PDF and index file
                pdf_files = [f for f in os.listdir(user_folder) if f.endswith('.pdf')]
                json_files = [f for f in os.listdir(user_folder) if f.endswith('.json')]
                
                if pdf_files and json_files:
                    print(f"[INFO] Found basic files, returning minimal response")
                    return JsonResponse({
                        'success': True,
                        'task_id': f"upload_{userid}",
                        'framework_name': 'Uploaded Framework',
                        'framework_info': {'framework_name': 'Uploaded Framework'},
                        'sections': [],
                        'total_sections': 0,
                        'total_policies': 0,
                        'total_subpolicies': 0,
                        'source': f'Basic files in upload_{userid}',
                        'message': 'Upload completed but policy extraction may be in progress'
                    })
            
            return JsonResponse({
                'success': False,
                'error': f'Could not load data for user {userid}'
            }, status=404)
        
        # Extract data from consolidated structure
        sections = data.get('sections', [])
        framework_info = data.get('framework_info', {})
        summary = data.get('summary', {})
        
        # Get framework name
        framework_name = framework_info.get('framework_name', 'Uploaded Framework')
        
        print(f"[SUCCESS] Loaded from framework_data.json: {summary}")
        
        return JsonResponse({
            'success': True,
            'task_id': f"upload_{userid}",
            'framework_name': framework_name,
            'framework_info': framework_info,
            'sections': sections,
            'total_sections': summary.get('total_sections', len(sections)),
            'total_policies': summary.get('total_policies', 0),
            'total_subpolicies': summary.get('total_subpolicies', 0),
            'source': f'framework_data.json in upload_{userid}'
        })
        
    except Exception as e:
        print(f"[ERROR] Error in get_sections_by_user: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e), 'success': False}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def save_checked_sections_json(request):
    """Save selected sections, policies, and subpolicies to checked_section.json"""
    try:
        # Handle GET requests for testing
        if request.method == 'GET':
            print(f"[DEBUG] GET request to save_checked_sections_json endpoint")
            return JsonResponse({
                'message': 'save-checked-sections-json endpoint is working',
                'method': 'GET',
                'status': 'success'
            })
        
        print(f"[DEBUG] POST request to save_checked_sections_json endpoint")
        data = json.loads(request.body)
        selected_items = data.get('selected_items', [])
        
        if not selected_items:
            return JsonResponse({'error': 'No items selected'}, status=400)
        
        # Extract user ID from request or use default
        user_id = data.get('user_id', '1')
        
        # Save to user-specific folder
        user_folder = os.path.join(settings.MEDIA_ROOT, f"upload_{user_id}")
        os.makedirs(user_folder, exist_ok=True)
        
        # Simple structure - just save the selected items
        checked_sections_data = {
            "metadata": {
                "creation_timestamp": int(time.time()),
                "creation_date": time.strftime('%Y-%m-%d %H:%M:%S'),
                "total_sections": len(selected_items)
            },
            "sections": selected_items
        }
        
        # Save to checked_section.json in the user folder
        checked_section_file = os.path.join(user_folder, "checked_section.json")
        with open(checked_section_file, 'w', encoding='utf-8') as f:
            json.dump(checked_sections_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] Saved checked sections to: {checked_section_file}")
        
        return JsonResponse({
            'message': 'Selected sections saved successfully',
            'file_path': checked_section_file,
            'total_sections': len(selected_items),
            'status': 'success'
        })
        
    except Exception as e:
        print(f"[ERROR] Error in save_checked_sections_json: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def generate_compliances_for_checked_sections(request):
    """Generate AI-powered compliance records and save them inside checked_section.json file"""
    try:
        print(f"[DEBUG] POST request to generate_compliances_for_checked_sections endpoint")
        
        data = json.loads(request.body)
        
        # Import the AI compliance generator
        from ..uploadNist.compliance_generator import generate_compliance_for_single_subpolicy
        
        # Extract user ID from request or use default
        user_id = data.get('user_id', '1')
        
        # Read from user-specific folder
        user_folder = os.path.join(settings.MEDIA_ROOT, f"upload_{user_id}")
        checked_section_file = os.path.join(user_folder, "checked_section.json")
        
        if not os.path.exists(checked_section_file):
            return JsonResponse({'error': 'checked_section.json file not found'}, status=404)
        
        # Read the checked sections data
        with open(checked_section_file, 'r', encoding='utf-8') as f:
            checked_data = json.load(f)
        
        sections = checked_data.get('sections', [])
        if not sections:
            return JsonResponse({'error': 'No sections found in checked_section.json'}, status=400)
        
        print(f"[INFO] Found {len(sections)} sections to process")
        
        # Debug: Print the actual data structure
        print(f"[DEBUG] Data structure verification:")
        for i, section in enumerate(sections):
            policies = section.get('policies', [])
            print(f"[DEBUG] Section {i+1}: '{section.get('section_title', 'No title')}' has {len(policies)} policies")
            for j, policy in enumerate(policies):
                subpolicies = policy.get('subpolicies', [])
                print(f"[DEBUG]   Policy {j+1}: '{policy.get('policy_title', 'No title')}' has {len(subpolicies)} subpolicies")
        
        # Generate AI-powered compliance records and add them to each subpolicy
        compliance_records = []
        total_processed = 0
        total_sections = len(sections)
        total_policies = 0
        
        print(f"[DEBUG] Starting compliance generation with {total_sections} sections")
        
        # Process each section
        for section in sections:
            section_name = section.get('section_name', '')
            section_title = section.get('section_title', '')
            policies = section.get('policies', [])
            total_policies += len(policies)
            
            print(f"[DEBUG] Section '{section_title}' has {len(policies)} policies")
            print(f"[INFO] Processing section: {section_title}")
            
            # Process each policy
            for policy in policies:
                policy_title = policy.get('policy_title', '')
                subpolicies = policy.get('subpolicies', [])
                
                print(f"[DEBUG] Policy '{policy_title}' has {len(subpolicies)} subpolicies")
                print(f"[INFO] Processing policy: {policy_title}")
                
                # Process each subpolicy
                for subpolicy in subpolicies:
                    subpolicy_id = subpolicy.get('subpolicy_id', '')
                    subpolicy_title = subpolicy.get('subpolicy_title', '')
                    subpolicy_description = subpolicy.get('subpolicy_description', '')
                    control = subpolicy.get('control', '')
                    
                    if not subpolicy_title:
                        continue
                    
                    print(f"[AI] Generating compliance for subpolicy: {subpolicy_title}")
                    
                    try:
                        # Use AI to generate compliance records
                        ai_compliances = generate_compliance_for_single_subpolicy(
                            subpolicy_id=subpolicy_id,
                            subpolicy_name=subpolicy_title,
                            description=subpolicy_description,
                            control=control
                        )
                        
                        # Process AI-generated compliance records
                        for ai_compliance in ai_compliances:
                            # Create enhanced compliance record with AI data
                            compliance_record = {
                                'SubPolicyId': subpolicy_id,
                                'SubPolicyTitle': subpolicy_title,
                                'SectionName': section_name,
                                'SectionTitle': section_title,
                                'PolicyTitle': policy_title,
                                'Status': 'Generated',
                                'CreatedAt': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'ComplianceType': ai_compliance.get('ComplianceType', 'Automated'),
                                'Description': ai_compliance.get('ComplianceItemDescription', f'AI-generated compliance for {subpolicy_title}'),
                                'Evidence': [],
                                'Notes': f'AI-generated from {section_title} - {policy_title}',
                                # Add AI-generated fields
                                'Identifier': ai_compliance.get('Identifier', ''),
                                'ComplianceTitle': ai_compliance.get('ComplianceTitle', ''),
                                'Scope': ai_compliance.get('Scope', ''),
                                'Objective': ai_compliance.get('Objective', ''),
                                'BusinessUnitsCovered': ai_compliance.get('BusinessUnitsCovered', ''),
                                'Criticality': ai_compliance.get('Criticality', 'Medium'),
                                'MandatoryOptional': ai_compliance.get('MandatoryOptional', 'Mandatory'),
                                'ManualAutomatic': ai_compliance.get('ManualAutomatic', 'Manual'),
                                'Impact': ai_compliance.get('Impact', 5.0),
                                'Probability': ai_compliance.get('Probability', 5.0),
                                'MaturityLevel': ai_compliance.get('MaturityLevel', 'Developing'),
                                'Applicability': ai_compliance.get('Applicability', 'Global'),
                                'PotentialRiskScenarios': ai_compliance.get('PotentialRiskScenarios', ''),
                                'RiskType': ai_compliance.get('RiskType', 'Current'),
                                'RiskCategory': ai_compliance.get('RiskCategory', 'Operational'),
                                'RiskBusinessImpact': ai_compliance.get('RiskBusinessImpact', ''),
                                'risk_details': ai_compliance.get('risk_details', {})
                            }
                            
                            # Add compliance record to the subpolicy
                            if 'compliances' not in subpolicy:
                                subpolicy['compliances'] = []
                            subpolicy['compliances'].append(compliance_record)
                            
                            compliance_records.append(compliance_record)
                            total_processed += 1
                        
                        print(f"[SUCCESS] Generated {len(ai_compliances)} AI compliance records for: {subpolicy_title}")
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to generate AI compliance for {subpolicy_title}: {e}")
                        # Fallback to simple compliance record
                        compliance_record = {
                            'SubPolicyId': subpolicy_id,
                            'SubPolicyTitle': subpolicy_title,
                            'SectionName': section_name,
                            'SectionTitle': section_title,
                            'PolicyTitle': policy_title,
                            'Status': 'Generated',
                            'CreatedAt': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'ComplianceType': 'Automated',
                            'Description': f'Fallback compliance for {subpolicy_title}',
                            'Evidence': [],
                            'Notes': f'Fallback from {section_title} - {policy_title}'
                        }
                        
                        if 'compliances' not in subpolicy:
                            subpolicy['compliances'] = []
                        subpolicy['compliances'].append(compliance_record)
                        
                        compliance_records.append(compliance_record)
                        total_processed += 1
        
        if not compliance_records:
            return JsonResponse({'error': 'No compliance records were generated'}, status=400)
        
        # Update metadata
        if 'metadata' not in checked_data:
            checked_data['metadata'] = {}
        
        checked_data['metadata']['compliance_generation_timestamp'] = int(time.time())
        checked_data['metadata']['compliance_generation_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        checked_data['metadata']['total_compliances'] = len(compliance_records)
        checked_data['metadata']['ai_generated'] = True
        
        # Save updated checked_section.json with AI compliance data
        with open(checked_section_file, 'w', encoding='utf-8') as f:
            json.dump(checked_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] Generated {len(compliance_records)} AI-powered compliance records")
        print(f"[SUCCESS] Updated checked_section.json with AI compliance data")
        print(f"[DEBUG] Final counts - Sections: {total_sections}, Policies: {total_policies}, Subpolicies: {total_processed}, Compliances: {len(compliance_records)}")
        
        return JsonResponse({
            'success': True,
            'message': 'AI-powered compliance records generated and saved to checked_section.json',
            'file_path': checked_section_file,
            'total_compliance_records': len(compliance_records),
            'total_subpolicies': total_processed,
            'total_compliances': len(compliance_records),
            'total_sections': total_sections,
            'total_policies': total_policies,
            'ai_generated': True,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"[ERROR] Error in generate_compliances_for_checked_sections: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_checked_sections_with_compliance(request):
    """
    Retrieves the checked sections data, including compliances, from checked_section.json.
    This endpoint is used by the frontend to load data for the "Edit Policy Details" section.
    """
    try:
        print(f"[DEBUG] GET request to get_checked_sections_with_compliance endpoint")

        # Extract user ID from request parameters or use default
        user_id = request.GET.get('user_id', '1')
        
        # Read from user-specific folder
        user_folder = os.path.join(settings.MEDIA_ROOT, f"upload_{user_id}")
        checked_section_file = os.path.join(user_folder, "checked_section.json")
        framework_data_file = os.path.join(user_folder, "framework_data.json")

        if not os.path.exists(checked_section_file):
            print(f"[ERROR] checked_section.json file not found at {checked_section_file}")
            return JsonResponse({'error': 'checked_section.json file not found'}, status=404)

        # Read the checked sections data
        with open(checked_section_file, 'r', encoding='utf-8') as f:
            checked_data = json.load(f)
        
        # Read framework data to get framework_info
        framework_info = None
        if os.path.exists(framework_data_file):
            try:
                with open(framework_data_file, 'r', encoding='utf-8') as f:
                    framework_data = json.load(f)
                    framework_info = framework_data.get('framework_info', {})
                    print(f"[DEBUG] Loaded framework_info from framework_data.json")
            except Exception as e:
                print(f"[WARNING] Could not read framework_data.json: {e}")
        
        # Merge framework_info into checked_data if available
        if framework_info:
            if 'metadata' not in checked_data:
                checked_data['metadata'] = {}
            checked_data['metadata']['framework_info'] = framework_info
            checked_data['metadata']['task_id'] = f"upload_1"
            print(f"[DEBUG] Added framework_info to metadata")
        
        print(f"[SUCCESS] Successfully loaded checked_section.json")
        print(f"[DEBUG] Data structure: {len(checked_data.get('sections', []))} sections")
        
        # Return the complete data structure in the format expected by frontend
        return JsonResponse({
            'success': True,
            'data': checked_data,
            'message': 'Successfully loaded checked sections data'
        }, status=200)

    except FileNotFoundError:
        print(f"[ERROR] File not found: {checked_section_file}")
        return JsonResponse({'error': 'checked_section.json file not found'}, status=404)
    except json.JSONDecodeError:
        print(f"[ERROR] Error decoding JSON from {checked_section_file}")
        return JsonResponse({'error': 'Error decoding JSON from checked_section.json'}, status=500)
    except Exception as e:
        print(f"[ERROR] Error in get_checked_sections_with_compliance: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def test_endpoint(request):
    """Test endpoint to verify URL mapping is working"""
    return JsonResponse({
        'message': 'Test endpoint is working',
        'method': request.method,
        'status': 'success'
    })

@csrf_exempt
@require_http_methods(["POST"])
def generate_consolidated_json(request):
    """
    Manually generate consolidated framework_data.json file for a user
    This creates a clean, simple JSON file in upload_1/ folder
    """
    try:
        data = json.loads(request.body)
        userid = data.get('userid', '1')
        
        print(f"[INFO] Generating consolidated JSON for user: {userid}")
        
        # Import the consolidate_data module
        from .consolidate_data import create_consolidated_json
        
        # Create the consolidated JSON
        consolidated_data = create_consolidated_json(userid)
        
        return JsonResponse({
            'success': True,
            'message': f'Consolidated JSON created successfully for user {userid}',
            'file_path': f'MEDIA_ROOT/upload_{userid}/framework_data.json',
            'summary': consolidated_data.get('summary', {}),
            'framework_name': consolidated_data.get('framework_info', {}).get('framework_name', 'Unknown')
        })
        
    except Exception as e:
        print(f"[ERROR] Error generating consolidated JSON: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e), 'success': False}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_user_folders(request):
    """
    List all available user folders.
    
    Args:
        request: Django request object
    """
    try:
        user_folders = find_user_folders()
        
        return JsonResponse({
            'user_folders': user_folders,
            'total_users': len(user_folders)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def read_sections_from_directory(sections_dir):
    """
    Read sections from the extracted sections directory.
    
    Args:
        sections_dir (str): Path to the sections directory
        
    Returns:
        list: List of sections with their subsections
    """
    sections = []
    
    try:
        # Look for sections_index.json file
        index_file = os.path.join(sections_dir, 'sections_index.json')
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                
            # Extract sections from the index
            for section_info in index_data.get('sections_written', []):
                section = {
                    'id': len(sections),
                    'title': section_info.get('title', ''),
                    'selected': False,
                    'expanded': False,
                    'subsections': []
                }
                
                # Add subsections if they exist
                section_folder = os.path.join(sections_dir, 'sections', section_info.get('folder', ''))
                if os.path.exists(section_folder):
                    # Read content.json for section details
                    content_file = os.path.join(section_folder, 'content.json')
                    if os.path.exists(content_file):
                        with open(content_file, 'r', encoding='utf-8') as f:
                            content_data = json.load(f)
                            section['content'] = content_data.get('content', '')
                
                sections.append(section)
        
        return sections
        
    except Exception as e:
        print(f"Error reading sections from directory: {e}")
        return []

def get_sections_from_user_folder(userid):
    """
    Get sections from a user's folder by searching for the sections_index.json file.
    DEPRECATED: This function is now replaced by the uploaded_data_loader.
    Use get_sections_by_user endpoint instead for complete hierarchical data.
    
    Args:
        userid (str): The user ID to search for
        
    Returns:
        list: List of sections with their titles and metadata
    """
    try:
        # Create the user folder path
        user_folder = os.path.join(settings.MEDIA_ROOT, f"upload_{userid}")
        
        if not os.path.exists(user_folder):
            print(f"User folder not found: {user_folder}")
            return []
        
        # Look for sections_index.json - try multiple possible locations
        sections_index_path = None
        possible_paths = [
            os.path.join(user_folder, 'extracted_sections', 'sections_index.json'),
            os.path.join(user_folder, 'sections_PCI_DSS_1', 'sections_index.json'),
            os.path.join(user_folder, 'sections_PCI_DSS', 'sections_index.json'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                sections_index_path = path
                print(f"Found sections index at: {sections_index_path}")
                break
        
        if not sections_index_path:
            print(f"Sections index file not found in any of the expected locations")
            return []
        
        # Read the sections index file
        with open(sections_index_path, 'r', encoding='utf-8') as f:
            sections_data = json.load(f)
        
        # Extract sections from the sections_written array
        sections = []
        for section_info in sections_data.get('sections_written', []):
            section = {
                'id': len(sections),
                'title': section_info.get('title', ''),
                'folder': section_info.get('folder', ''),
                'level': section_info.get('level', 1),
                'selected': False,
                'expanded': False,
                'subsections': []
            }
            
            # Check if there's a content.json file in the section folder
            section_folder = os.path.join(user_folder, 'extracted_sections', 'sections', section_info.get('folder', ''))
            content_file = os.path.join(section_folder, 'content.json')
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content_data = json.load(f)
                        section['content'] = content_data.get('content', '')
                except Exception as e:
                    print(f"Error reading content file {content_file}: {e}")
                    section['content'] = ''
            else:
                section['content'] = ''
            
            # Check for extracted controls in the section folder
            extracted_controls_folder = os.path.join(section_folder, 'extracted_controls')
            if os.path.exists(extracted_controls_folder):
                try:
                    # Read control headings from control_headings.json
                    control_headings_file = os.path.join(extracted_controls_folder, 'control_headings.json')
                    if os.path.exists(control_headings_file):
                        with open(control_headings_file, 'r', encoding='utf-8') as f:
                            control_data = json.load(f)
                            
                        # Extract control names from the JSON structure
                        controls = control_data.get('controls', [])
                        for control in controls:
                            control_name = control.get('name', '')
                            if control_name:
                                subsection = {
                                    'id': len(section['subsections']),
                                    'title': control_name,
                                    'selected': False,
                                    'content': control.get('description', ''),
                                    'control_id': control.get('id', ''),
                                    'type': 'control'
                                }
                                section['subsections'].append(subsection)
                    
                    # Also check for subdirectories in extracted_controls
                    for item in os.listdir(extracted_controls_folder):
                        item_path = os.path.join(extracted_controls_folder, item)
                        if os.path.isdir(item_path):
                            # This is a control subfolder
                            subsection = {
                                'id': len(section['subsections']),
                                'title': item.replace('_', ' '),
                                'selected': False,
                                'content': f'Control folder: {item}',
                                'control_id': item,
                                'type': 'control_folder'
                            }
                            section['subsections'].append(subsection)
                            
                except Exception as e:
                    print(f"Error reading extracted controls from {extracted_controls_folder}: {e}")
            
            sections.append(section)
        
        print(f"Found {len(sections)} sections in user folder: {user_folder}")
        return sections
        
    except Exception as e:
        print(f"Error getting sections from user folder: {e}")
        return []

def find_user_folders():
    """
    Find all user folders in MEDIA_ROOT.
    
    Returns:
        list: List of user IDs that have folders
    """
    try:
        user_folders = []
        media_root = settings.MEDIA_ROOT
        
        if not os.path.exists(media_root):
            return user_folders
        
        # Look for folders that start with 'upload_'
        for item in os.listdir(media_root):
            item_path = os.path.join(media_root, item)
            if os.path.isdir(item_path) and item.startswith('upload_'):
                userid = item.replace('upload_', '')
                user_folders.append(userid)
        
        return user_folders
        
    except Exception as e:
        print(f"Error finding user folders: {e}")
        return []

@csrf_exempt
@require_http_methods(["POST"])
def load_default_data(request):
    """
    Load default framework data from main_default folder.
    
    Args:
        request: Django request object
    """
    try:
        # Path to the main_default folder
        main_default_folder = os.path.join(settings.MEDIA_ROOT, 'main_default')
        
        if not os.path.exists(main_default_folder):
            return JsonResponse({'error': 'Default data folder not found'}, status=404)
        
        # Check for extracted_sections folder
        extracted_sections_folder = os.path.join(main_default_folder, 'extracted_sections')
        if not os.path.exists(extracted_sections_folder):
            return JsonResponse({'error': 'Default extracted sections not found'}, status=404)
        
        # Read sections from the main_default folder
        sections = get_sections_from_main_default()
        
        if not sections:
            return JsonResponse({'error': 'No sections found in default data'}, status=404)
        
        # Generate a default task ID
        default_task_id = f"default_{int(time.time())}"
        
        return JsonResponse({
            'message': 'Default framework data loaded successfully',
            'task_id': default_task_id,
            'processing': False,
            'sections': sections,
            'total_sections': len(sections),
            'source': 'main_default'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_sections_from_main_default():
    """
    Get sections from the main_default folder.
    
    Returns:
        list: List of sections with their titles and metadata
    """
    try:
        # Path to the main_default folder
        main_default_folder = os.path.join(settings.MEDIA_ROOT, 'main_default')
        
        if not os.path.exists(main_default_folder):
            print(f"Main default folder not found: {main_default_folder}")
            return []
        
        # Look for sections_index.json in the extracted_sections folder
        sections_index_path = os.path.join(main_default_folder, 'extracted_sections', 'sections_index.json')
        
        if not os.path.exists(sections_index_path):
            print(f"Sections index file not found: {sections_index_path}")
            return []
        
        # Read the sections index file
        with open(sections_index_path, 'r', encoding='utf-8') as f:
            sections_data = json.load(f)
        
        # Extract sections from the sections_written array
        sections = []
        for section_info in sections_data.get('sections_written', []):
            section = {
                'id': len(sections),
                'title': section_info.get('title', ''),
                'folder': section_info.get('folder', ''),
                'level': section_info.get('level', 1),
                'selected': False,
                'expanded': False,
                'subsections': []
            }
            
            # Check if there's a content.json file in the section folder
            section_folder = os.path.join(main_default_folder, 'extracted_sections', 'sections', section_info.get('folder', ''))
            content_file = os.path.join(section_folder, 'content.json')
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content_data = json.load(f)
                        section['content'] = content_data.get('content', '')
                except Exception as e:
                    print(f"Error reading content file {content_file}: {e}")
                    section['content'] = ''
            else:
                section['content'] = ''
            
            # Check for extracted controls in the section folder
            extracted_controls_folder = os.path.join(section_folder, 'extracted_controls')
            if os.path.exists(extracted_controls_folder):
                try:
                    # Read control headings from control_headings.json
                    control_headings_file = os.path.join(extracted_controls_folder, 'control_headings.json')
                    if os.path.exists(control_headings_file):
                        with open(control_headings_file, 'r', encoding='utf-8') as f:
                            control_data = json.load(f)
                            
                        # Extract control names from the JSON structure
                        controls = control_data.get('controls', [])
                        for control in controls:
                            control_name = control.get('name', '')
                            if control_name:
                                subsection = {
                                    'id': len(section['subsections']),
                                    'title': control_name,
                                    'selected': False,
                                    'content': control.get('description', ''),
                                    'control_id': control.get('id', ''),
                                    'type': 'control'
                                }
                                section['subsections'].append(subsection)
                    
                    # Also check for subdirectories in extracted_controls
                    for item in os.listdir(extracted_controls_folder):
                        item_path = os.path.join(extracted_controls_folder, item)
                        if os.path.isdir(item_path):
                            # This is a control subfolder
                            subsection = {
                                'id': len(section['subsections']),
                                'title': item.replace('_', ' '),
                                'selected': False,
                                'content': f'Control folder: {item}',
                                'control_id': item,
                                'type': 'control_folder'
                            }
                            section['subsections'].append(subsection)
                            
                except Exception as e:
                    print(f"Error reading extracted controls from {extracted_controls_folder}: {e}")
            
            sections.append(section)
        
        print(f"Found {len(sections)} sections in main_default folder: {main_default_folder}")
        return sections
        
    except Exception as e:
        print(f"Error getting sections from main_default folder: {e}")
        return []
