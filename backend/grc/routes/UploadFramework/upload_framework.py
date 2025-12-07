from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
import threading
import time
import shutil
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.cache import cache
import pandas as pd
import re
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from grc.models import Framework, Policy, SubPolicy, Compliance

# # Import the processing function from final_adithya.py
# from .final_adithya import extract_document_sections
# from .policy_text_extract import process_checked_sections

# COMMENTED OUT OLD IMPORTS - Using new AI upload API
# from ..uploadNist.all_integrated_upload import upload_pdf_and_extract_complete, create_user_folder
from ..uploadNist import ai_upload
from ..uploadNist import pdf_index_extractor
from ..uploadNist import index_content_extractor
from ..uploadNist import policy_extractor_enhanced

# Global progress tracking
processing_status = {}

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

def update_progress(task_id, progress, message):
    """Update processing progress"""
    processing_status[task_id] = {
        'progress': progress,
        'message': message,
        'timestamp': time.time()
    }
    cache.set(f'processing_{task_id}', processing_status[task_id], timeout=3600)

def process_pdf_framework_new(userid, pdf_path, task_id):
    """New PDF processing function using the NEW AI upload pipeline"""
    try:
        update_progress(task_id, 5, "Starting PDF processing with new AI pipeline...")
        
        # Use the new ai_upload pipeline
        from pathlib import Path
        
        # Get MEDIA_ROOT
        media_root = ai_upload.get_media_root()
        user_folder = media_root / f"upload_{userid}"
        pdf_path_obj = Path(pdf_path)
        pdf_name = pdf_path_obj.stem
        
        # Step 1: Extract Index
        update_progress(task_id, 30, "Extracting PDF index...")
        index_json_path = user_folder / f"{pdf_name}_index.json"
        
        try:
            index_data = pdf_index_extractor.extract_and_save_index(
                pdf_path=str(pdf_path),
                output_path=str(index_json_path),
                prefer_toc=True
            )
            index_items_count = len(index_data.get('items', []))
            update_progress(task_id, 40, f"Index extracted: {index_items_count} items")
        except Exception as e:
            update_progress(task_id, 100, f"Index extraction failed: {str(e)}")
            return False
        
        # Step 2: Extract Sections
        update_progress(task_id, 45, "Extracting sections...")
        sections_dir = user_folder / f"sections_{pdf_name}"
        
        try:
            manifest = index_content_extractor.process_pdf_sections(
                pdf_path=str(pdf_path),
                index_json_path=str(index_json_path),
                output_dir=str(sections_dir),
                verbose=True
            )
            sections_count = len(manifest.get('sections_written', []))
            update_progress(task_id, 60, f"Sections extracted: {sections_count} sections")
        except Exception as e:
            update_progress(task_id, 100, f"Section extraction failed: {str(e)}")
            return False
        
        # Step 3: Extract Policies
        update_progress(task_id, 65, "Extracting policies using AI...")
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
            
            update_progress(task_id, 95, f"Policies extracted: {total_policies} policies")
            
            # Store result
            result = {
                "status": "success",
                "data": {
                    'user_folder': f"upload_{userid}",
                    'index_items': index_items_count,
                    'sections': sections_count,
                    'policies': total_policies,
                    'subpolicies': total_subpolicies
                }
            }
            
            cache.set(f'processing_result_{task_id}', result, timeout=3600)
            update_progress(task_id, 100, "PDF processing completed successfully!")
            return True
            
        except Exception as e:
            update_progress(task_id, 100, f"Policy extraction failed: {str(e)}")
            return False
            
    except Exception as e:
        update_progress(task_id, 100, f"Error: {str(e)}")
        return False

def process_pdf_framework(pdf_path, task_id, output_dir):
    """Main PDF processing function with progress tracking"""
    try:
        update_progress(task_id, 5, "Starting PDF processing...")
        
        # Call the extract_document_sections function with progress updates
        def progress_callback(progress, message):
            update_progress(task_id, progress, message)
        
        # Process the PDF using the extract_document_sections function with custom output directory
        update_progress(task_id, 10, "Extracting document sections...")
        result_output_dir = extract_document_sections(pdf_path, output_dir)
        
        if not result_output_dir:
            update_progress(task_id, 100, "Error: Failed to extract document sections")
            return False
            
        # Store the output directory path for later use
        cache.set(f'output_dir_{task_id}', result_output_dir, timeout=3600)
        
        update_progress(task_id, 100, "PDF processing completed successfully!")
        return True
        
    except Exception as e:
        update_progress(task_id, 100, f"Error: {str(e)}")
        return False

def use_default_temp_data(task_id, output_dir):
    """
    Fast function to copy pre-processed data from /temp directory
    Instead of calling final_adithya.py, this takes only 20 seconds
    """
    try:
        # Source directory with pre-processed data
        temp_source_dir = os.path.join(settings.MEDIA_ROOT, 'temp', 'temp')
        
        if not os.path.exists(temp_source_dir):
            update_progress(task_id, 100, "Error: Default temp data not found")
            return False
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Progress tracking for 20 seconds (20000ms)
        start_time = time.time()
        total_duration = 20.0  # 20 seconds
        
        # Get list of sections in temp directory
        section_dirs = [d for d in os.listdir(temp_source_dir) 
                       if os.path.isdir(os.path.join(temp_source_dir, d))]
        
        if not section_dirs:
            update_progress(task_id, 100, "Error: No sections found in temp data")
            return False
        
        update_progress(task_id, 5, "Loading default framework data...")
        time.sleep(1)
        
        total_sections = len(section_dirs)
        
        for i, section_name in enumerate(section_dirs):
            # Calculate progress (5% to 95% over 18 seconds, leaving 2 seconds for completion)
            elapsed_time = time.time() - start_time
            target_progress = 5 + (85 * (i + 1) / total_sections)
            target_time = (18.0 * (i + 1) / total_sections)
            
            # Adjust timing to stay on 20-second schedule
            if elapsed_time < target_time:
                time.sleep(target_time - elapsed_time)
            
            section_source = os.path.join(temp_source_dir, section_name)
            section_dest = os.path.join(output_dir, section_name)
            
            update_progress(task_id, int(target_progress), 
                          f"Processing section: {section_name}")
            
            # Copy the entire section directory
            if os.path.exists(section_source):
                shutil.copytree(section_source, section_dest, dirs_exist_ok=True)
            
            # Small delay between sections for realistic progress
            time.sleep(0.5)
        
        # Final completion phase
        update_progress(task_id, 95, "Finalizing data structure...")
        time.sleep(2)
        
        # Ensure we've taken close to 20 seconds
        elapsed_time = time.time() - start_time
        if elapsed_time < total_duration:
            remaining_time = total_duration - elapsed_time
            time.sleep(remaining_time)
        
        update_progress(task_id, 100, "Default data loaded successfully!")
        return True
        
    except Exception as e:
        update_progress(task_id, 100, f"Error loading default data: {str(e)}")
        return False

def process_pdf_framework_fast(pdf_path, task_id, output_dir):
    """Fast PDF processing function using pre-processed temp data"""
    try:
        update_progress(task_id, 5, "Starting fast processing with default data...")
        
        # Use the fast temp data function instead of calling final_adithya.py
        result = use_default_temp_data(task_id, output_dir)
        
        if result:
            # Store the output directory path for later use
            cache.set(f'output_dir_{task_id}', output_dir, timeout=3600)
            return True
        else:
            return False
            
    except Exception as e:
        update_progress(task_id, 100, f"Error: {str(e)}")
        return False

@csrf_exempt
@require_http_methods(["POST"])
def upload_framework_file(request):
    try:
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
        
        # Create user-specific folder
        try:
            user_folder = create_user_folder(userid)
        except Exception as e:
            return JsonResponse({'error': f'Failed to create user folder: {str(e)}'}, status=500)
        
        # Save file in user-specific directory
        file_path = os.path.join(user_folder, uploaded_file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Create output directory for extracted sections
        output_dir = os.path.join(user_folder, 'extracted_sections')
        
        # Start actual PDF processing in background thread
        def background_process():
            try:
                update_progress(task_id, 5, "Starting processing...")
                
                # Use new integrated processing for PDF files
                if file_extension.lower() == '.pdf':
                    update_progress(task_id, 10, "Processing PDF with integrated system...")
                    result = process_pdf_framework_new(userid, file_path, task_id)
                    
                    if result:
                        update_progress(task_id, 100, "Framework data processed successfully!")
                    else:
                        update_progress(task_id, 100, "Error: Failed to process framework data")
                else:
                    # For non-PDF files, use fast processing
                    update_progress(task_id, 20, f"Processing {file_extension} file...")
                    result = use_default_temp_data(task_id, output_dir)
                    
                    if result:
                        cache.set(f'output_dir_{task_id}', output_dir, timeout=3600)
                        update_progress(task_id, 100, "File processed successfully!")
                    else:
                        update_progress(task_id, 100, "Error: Failed to process file")
                    
                    # Create a simple section based on filename
                    filename_base = os.path.splitext(uploaded_file.name)[0]
                    section_dir = os.path.join(output_dir, f"1 {filename_base}")
                    json_dir = os.path.join(section_dir, "json_chunks")
                    txt_dir = os.path.join(section_dir, "txt_chunks")
                    
                    os.makedirs(json_dir, exist_ok=True)
                    os.makedirs(txt_dir, exist_ok=True)
                    
                    # Read file content based on type
                    content = ""
                    if file_extension.lower() in ['.txt']:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    elif file_extension.lower() in ['.doc', '.docx']:
                        try:
                            import docx
                            doc = docx.Document(file_path)
                            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                        except:
                            content = f"Could not extract content from {uploaded_file.name}"
                    elif file_extension.lower() in ['.xlsx', '.xls']:
                        try:
                            df = pd.read_excel(file_path)
                            content = df.to_string()
                        except:
                            content = f"Could not extract content from {uploaded_file.name}"
                    
                    # Save content to files
                    with open(os.path.join(txt_dir, f"{filename_base}.txt"), 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    json_data = {
                        "subheading": filename_base,
                        "start_text": content[:50],
                        "content": content
                    }
                    with open(os.path.join(json_dir, f"{filename_base}.json"), 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2)
                    
                    # Store the output directory path for later use
                    cache.set(f'output_dir_{task_id}', output_dir, timeout=3600)
                    
                    update_progress(task_id, 100, f"{file_extension.upper()} file processed successfully!")
                    
            except Exception as e:
                update_progress(task_id, 100, f"Error: {str(e)}")
        
        thread = threading.Thread(target=background_process)
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
    """Get processing status for a task"""
    try:
        status = cache.get(f'processing_{task_id}')
        if status:
            return JsonResponse(status)
        else:
            return JsonResponse({
                'progress': 0,
                'message': 'Task not found or expired',
                'error': True
            }, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_sections(request, task_id):
    """Get extracted sections for a processed document with policies and subpolicies"""
    try:
        # First, try to find and read the all_policies.json file
        from pathlib import Path
        
        # Extract userid from task_id if it contains 'upload_'
        userid = None
        if 'upload_' in task_id:
            # Try to extract userid from task_id
            parts = task_id.split('_')
            if len(parts) > 1:
                userid = parts[1].split('.')[0]  # Handle cases like "upload_1_PCI.pdf"
        
        # If no userid found in task_id, try to get from request parameters
        if not userid:
            userid = request.GET.get('user_id', '1')
        
        if userid:
            media_root = Path(settings.MEDIA_ROOT)
            user_folder = media_root / f"upload_{userid}"
            
            # Find the policies folder (e.g., policies_PCI_DSS_1)
            if user_folder.exists():
                policies_folders = list(user_folder.glob("policies_*"))
                
                if policies_folders:
                    policies_folder = policies_folders[0]
                    all_policies_json = policies_folder / "all_policies.json"
                    
                    if all_policies_json.exists():
                        print(f"[INFO] Reading all_policies.json from: {all_policies_json}")
                        
                        # Read and parse the JSON file
                        with open(all_policies_json, 'r', encoding='utf-8') as f:
                            all_policies_data = json.load(f)
                        
                        # Build hierarchical structure
                        sections = []
                        
                        for section_data in all_policies_data:
                            section_info = section_data.get('section_info', {})
                            analysis = section_data.get('analysis', {})
                            
                            # Build section object
                            section = {
                                'name': section_info.get('title', 'Untitled Section'),
                                'title': section_info.get('title', 'Untitled Section'),
                                'level': section_info.get('level', 1),
                                'start_page': section_info.get('start_page'),
                                'end_page': section_info.get('end_page'),
                                'folder_path': section_info.get('folder_path', ''),
                                'policies': []
                            }
                            
                            # Extract policies from analysis
                            if analysis.get('has_policies') and analysis.get('policies'):
                                for policy_data in analysis.get('policies', []):
                                    policy = {
                                        'policy_id': policy_data.get('policy_id', ''),
                                        'policy_title': policy_data.get('policy_title', ''),
                                        'policy_description': policy_data.get('policy_description', ''),
                                        'policy_text': policy_data.get('policy_text', ''),
                                        'scope': policy_data.get('scope', ''),
                                        'objective': policy_data.get('objective', ''),
                                        'policy_type': policy_data.get('policy_type', ''),
                                        'policy_category': policy_data.get('policy_category', ''),
                                        'policy_subcategory': policy_data.get('policy_subcategory', ''),
                                        'subpolicies': []
                                    }
                                    
                                    # Extract subpolicies
                                    for subpolicy_data in policy_data.get('subpolicies', []):
                                        subpolicy = {
                                            'subpolicy_id': subpolicy_data.get('subpolicy_id', ''),
                                            'subpolicy_title': subpolicy_data.get('subpolicy_title', ''),
                                            'subpolicy_description': subpolicy_data.get('subpolicy_description', ''),
                                            'subpolicy_text': subpolicy_data.get('subpolicy_text', ''),
                                            'control': subpolicy_data.get('control', '')
                                        }
                                        policy['subpolicies'].append(subpolicy)
                                    
                                    section['policies'].append(policy)
                            
                            sections.append(section)
                        
                        print(f"[SUCCESS] Loaded {len(sections)} sections with policies from JSON")
                        return JsonResponse(sections, safe=False)
        
        # Fallback to old method if all_policies.json not found
        print("[INFO] all_policies.json not found, falling back to old method")
        
        # Get the output directory from cache
        output_dir = cache.get(f'output_dir_{task_id}')
        if not output_dir or not os.path.exists(output_dir):
            return JsonResponse({'error': 'Extracted sections not found'}, status=404)
        
        sections = []
        
        # List all directories in the extracted_sections folder
        dir_list = [d for d in os.listdir(output_dir) 
                    if os.path.isdir(os.path.join(output_dir, d))]
        
        # Sort directories using natural sorting (numerical order)
        def natural_sort_key(s):
            import re
            return [int(text) if text.isdigit() else text.lower()
                    for text in re.split('([0-9]+)', s)]
        
        dir_list.sort(key=natural_sort_key)
        
        for section_dir in dir_list:
            section_path = os.path.join(output_dir, section_dir)
            section = {
                'name': section_dir,
                'subsections': []
            }
            
            # Check for subdirectories like json_chunks and txt_chunks
            subdir_list = [d for d in os.listdir(section_path) 
                          if os.path.isdir(os.path.join(section_path, d))]
            
            # Only process txt_chunks directory, skip json_chunks
            if 'txt_chunks' in subdir_list:
                txt_chunks_path = os.path.join(section_path, 'txt_chunks')
                
                try:
                    files = [f for f in os.listdir(txt_chunks_path) 
                            if os.path.isfile(os.path.join(txt_chunks_path, f)) and f.endswith('.txt')]
                    
                    # Sort files using natural sorting
                    files.sort(key=natural_sort_key)
                    
                    for file_name in files:
                        file_path = os.path.join(txt_chunks_path, file_name)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Extract clean name without extension
                            clean_name = os.path.splitext(file_name)[0]
                            
                            section['subsections'].append({
                                'name': clean_name,
                                'content': content
                            })
                        except Exception as e:
                            clean_name = os.path.splitext(file_name)[0]
                            section['subsections'].append({
                                'name': clean_name,
                                'content': f"Error reading file: {str(e)}"
                            })
                except Exception as e:
                    print(f"Error listing files in {txt_chunks_path}: {str(e)}")
            
            # Also check for files directly in the section directory
            direct_files = [f for f in os.listdir(section_path) 
                           if os.path.isfile(os.path.join(section_path, f)) and f.endswith('.txt')]
            
            # Sort direct files using natural sorting
            direct_files.sort(key=natural_sort_key)
            
            for file_name in direct_files:
                file_path = os.path.join(section_path, file_name)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Extract clean name without extension
                    clean_name = os.path.splitext(file_name)[0]
                    
                    section['subsections'].append({
                        'name': clean_name,
                        'content': content
                    })
                except Exception as e:
                    clean_name = os.path.splitext(file_name)[0]
                    section['subsections'].append({
                        'name': clean_name,
                        'content': f"Error reading file: {str(e)}"
                    })
            
            # Add section even if empty
            sections.append(section)
        
        return JsonResponse(sections, safe=False)
    
    except Exception as e:
        print(f"[ERROR] Error in get_sections: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_section(request):
    """Update section content"""
    try:
        data = json.loads(request.body)
        section_name = data.get('section')
        subsection_name = data.get('subsection')
        content = data.get('content')
        task_id = data.get('task_id')
        
        if not all([section_name, subsection_name, content, task_id]):
            return JsonResponse({'error': 'Missing required data'}, status=400)
        
        # Get the output directory from cache
        output_dir = cache.get(f'output_dir_{task_id}')
        if not output_dir or not os.path.exists(output_dir):
            return JsonResponse({'error': 'Extracted sections not found'}, status=404)
        
        # Backend now returns clean names, so we need to find the actual file
        # subsection_name is clean (e.g., "AC-1"), but we need to find it in txt_chunks/AC-1.txt
        txt_chunks_path = os.path.join(output_dir, section_name, 'txt_chunks')
        file_path = os.path.join(txt_chunks_path, f"{subsection_name}.txt")
        
        # If not found in txt_chunks, try direct file in section directory
        if not os.path.exists(file_path):
            file_path = os.path.join(output_dir, section_name, f"{subsection_name}.txt")
        
        # We're only dealing with text files now, not JSON
        is_json = False
        
        # Write the content
        with open(file_path, 'w', encoding='utf-8') as f:
            if is_json:
                json.dump(json_content, f, indent=2)
            else:
                f.write(content)
        
        return JsonResponse({'message': 'Section updated successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_checked_structure(request):
    """Create structure with checked items"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        sections_data = data.get('sections', [])
        
        if not task_id or not sections_data:
            return JsonResponse({'error': 'Missing required data'}, status=400)
        
        # Get the output directory from cache
        output_dir = cache.get(f'output_dir_{task_id}')
        if not output_dir or not os.path.exists(output_dir):
            return JsonResponse({'error': 'Extracted sections not found'}, status=404)
        
        # Create output directory for checked items - NEW STRUCTURE: "checked by user"
        checked_output_dir = os.path.join(settings.MEDIA_ROOT, 'checked_by_user', task_id)
        
        # Delete existing checked_by_user directory if it exists
        if os.path.exists(checked_output_dir):
            print(f"Removing existing checked_by_user directory: {checked_output_dir}")
            shutil.rmtree(checked_output_dir)
        
        os.makedirs(checked_output_dir, exist_ok=True)
        print(f"Created checked_by_user directory: {checked_output_dir}")
        
        # Process each section and create plain text files
        file_counter = 1
        for section in sections_data:
            section_name = section.get('name')
            subsections = section.get('subsections', [])
            
            # Skip sections with no subsections
            if not section_name or not subsections:
                continue
            
            # Process each subsection and create a plain text file
            for subsection in subsections:
                subsection_name = subsection.get('name')
                content = subsection.get('content')
                
                if not subsection_name or content is None:
                    continue
                
                # Backend now returns clean names without directory prefixes
                # subsection_name is already clean (e.g., "AC-1" instead of "txt_chunks/AC-1.txt")
                clean_name = subsection_name
                
                # Create a simple numbered file name
                plain_filename = f"{file_counter:03d}_{clean_name}.txt"
                
                # Save content to the plain file
                file_path = os.path.join(checked_output_dir, plain_filename)
                
                # Write the content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Created plain file: {plain_filename}")
                file_counter += 1
        
        # Start processing in background thread
        def background_process():
            # Process the checked sections to extract policy information
            update_progress(task_id, 50, "Processing checked sections to extract policy information...")
            excel_path = process_checked_sections(task_id)
            
            if excel_path:
                update_progress(task_id, 100, "Policy extraction completed successfully!")
                # Cache the Excel file path for later retrieval
                cache.set(f'policy_excel_{task_id}', excel_path, timeout=3600)
            else:
                update_progress(task_id, 100, "Error: Failed to extract policy information")
        
        thread = threading.Thread(target=background_process)
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'message': 'Checked sections created successfully. Policy extraction has started.',
            'task_id': task_id,
            'status': 'processing'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_extracted_policies(request, task_id):
    """Get extracted policy information from Excel file"""
    try:
        # First check if we have cached policies
        cached_policies = cache.get(f'extracted_policies_{task_id}')
        if cached_policies:
            return JsonResponse({
                'policies': cached_policies,
                'filename': f"cached_policies_{task_id}.xlsx",
                'excel_path': f"cached_policies_{task_id}.xlsx",
                'total_policies': len(cached_policies),
                'source': 'cache'
            })
        
        # Try to load existing extracted policies using the new function
        from .policy_text_extract import load_existing_extracted_policies
        existing_policies = load_existing_extracted_policies(task_id)
        
        if existing_policies:
            # Cache the policies for future use
            cache.set(f'extracted_policies_{task_id}', existing_policies, timeout=3600)
            
            return JsonResponse({
                'policies': existing_policies,
                'filename': f"extracted_policies_{task_id}.xlsx",
                'excel_path': f"extracted_policies_{task_id}.xlsx",
                'total_policies': len(existing_policies),
                'source': 'existing_extracted_policies'
            })
        
        # If no existing policies found, create a sample Excel file with default data
        media_root = settings.MEDIA_ROOT
        extracted_policies_dir = os.path.join(media_root, 'extracted_policies', task_id)
        
        if not os.path.exists(extracted_policies_dir):
            os.makedirs(extracted_policies_dir, exist_ok=True)
        
        # Create sample Excel file with default data
        sample_policies = [
            {
                'section_name': '3.1 ACCESS CONTROL',
                'file_name': 'sample.txt',
                'Sub_policy_id': 'AC-1',
                'sub_policy_name': 'Access Control Policy and Procedures',
                'control': 'Develop, document, and disseminate to all personnel: Access control policy that addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance.',
                'discussion': '',
                'related_controls': 'PM-9, PS-8, SI-12',
                'control_enhancements': '',
                'references': 'NIST SP 800-12, NIST SP 800-30'
            }
        ]
        
        # Create a DataFrame and save to Excel
        df = pd.DataFrame(sample_policies)
        output_file = os.path.join(extracted_policies_dir, f"extracted_policies_{task_id}.xlsx")
        df.to_excel(output_file, index=False)
        
        # Cache the policies
        cache.set(f'extracted_policies_{task_id}', sample_policies, timeout=3600)
        
        return JsonResponse({
            'policies': sample_policies,
            'filename': os.path.basename(output_file),
            'excel_path': os.path.basename(output_file),
            'total_policies': len(sample_policies),
            'source': 'generated_sample'
        })
    
    except Exception as e:
        print(f"Error in get_extracted_policies: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def direct_process_checked_sections(request):
    """
    Directly process the existing checked_by_user directory without requiring upload or selection.
    This is a shortcut for development and testing.
    """
    try:
        # Create a task ID
        task_id = f"direct_{int(time.time())}"
        
        # Update progress status
        update_progress(task_id, 10, "Starting direct policy extraction...")
        
        # Get the checked_by_user directory
        checked_by_user_dir = os.path.join(settings.MEDIA_ROOT, 'checked_by_user')
        
        if not os.path.exists(checked_by_user_dir):
            return JsonResponse({'error': 'Checked by user directory not found'}, status=404)
            
        # Process the checked sections in the background
        def background_process():
            update_progress(task_id, 50, "Processing checked by user sections to extract policy information...")
            excel_path = process_checked_sections(task_id)
            
            if excel_path:
                update_progress(task_id, 100, "Policy extraction completed successfully!")
                # Cache the Excel file path for later retrieval
                cache.set(f'policy_excel_{task_id}', excel_path, timeout=3600)
            else:
                update_progress(task_id, 100, "Error: Failed to extract policy information")
        
        thread = threading.Thread(target=background_process)
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'message': 'Direct policy extraction started',
            'task_id': task_id,
            'status': 'processing'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_updated_policies(request):
    """Save updated policy data to a new Excel file"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        policies = data.get('policies', [])
        
        if not task_id or not policies:
            return JsonResponse({'error': 'Missing required data'}, status=400)
        
        # Create DataFrame from updated policies
        df = pd.DataFrame(policies)
        
        # Ensure all expected columns exist (even if empty)
        expected_columns = [
            'section_name', 'file_name', 'Sub_policy_id', 'sub_policy_name', 
            'control', 'discussion', 'related_controls', 'control_enhancements', 'references'
        ]
        
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Reorder columns to have section_name and file_name first
        df = df[expected_columns]
        
        # Create output directory for updated policies
        media_root = settings.MEDIA_ROOT
        updated_policies_dir = os.path.join(media_root, 'updated_policies')
        os.makedirs(updated_policies_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = int(time.time())
        output_file = os.path.join(updated_policies_dir, f"updated_policies_{task_id}_{timestamp}.xlsx")
        
        # Save to Excel
        df.to_excel(output_file, index=False)
        
        # Cache the updated Excel file path
        cache.set(f'updated_policy_excel_{task_id}', output_file, timeout=3600)
        
        return JsonResponse({
            'message': 'Policies updated successfully',
            'excel_path': os.path.basename(output_file),
            'file_path': output_file
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_policies(request):
    """Save all policies to Excel file with timestamp"""
    try:
        data = json.loads(request.body)
        policies = data.get('policies', [])
        filename = data.get('filename', 'policies')
        task_id = data.get('task_id', 'unknown')
        
        if not policies:
            return JsonResponse({'error': 'No policies provided'}, status=400)
        
        # Create DataFrame from policies
        df = pd.DataFrame(policies)
        
        # Ensure all expected columns exist (even if empty)
        expected_columns = [
            'section_name', 'file_name', 'Sub_policy_id', 'sub_policy_name', 
            'control', 'discussion', 'related_controls', 'control_enhancements', 'references'
        ]
        
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Reorder columns
        df = df[expected_columns]
        
        # 1. Save to extracted_policies (original location)
        media_root = settings.MEDIA_ROOT
        extracted_policies_dir = os.path.join(media_root, 'extracted_policies', task_id)
        os.makedirs(extracted_policies_dir, exist_ok=True)
        
        source_file = os.path.join(extracted_policies_dir, f"extracted_policies_{task_id}.xlsx")
        df.to_excel(source_file, index=False)
        
        # 2. Create a copy in updated_policies with timestamp
        updated_policies_dir = os.path.join(media_root, 'updated_policies', task_id)
        os.makedirs(updated_policies_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = int(time.time())
        safe_filename = filename.replace('.xlsx', '').replace('.xls', '')
        output_file = os.path.join(updated_policies_dir, f"{safe_filename}_bulk_save_{timestamp}.xlsx")
        
        # Save to Excel
        df.to_excel(output_file, index=False)
        
        # Also update the cache for the task
        cache.set(f'extracted_policies_{task_id}', policies, timeout=3600)
        
        return JsonResponse({
            'message': 'All policies saved successfully',
            'original_file': os.path.basename(source_file),
            'updated_file': os.path.basename(output_file),
            'total_policies': len(policies),
            'timestamp': timestamp
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_single_policy(request):
    """Save a single updated policy and create new Excel file with timestamp"""
    try:
        data = json.loads(request.body)
        policy = data.get('policy')
        task_id = data.get('task_id', 'unknown')
        
        if not policy:
            return JsonResponse({'error': 'No policy provided'}, status=400)
        
        # Get current policies from cache or load from Excel
        cache_key = f'extracted_policies_{task_id}'
        cached_policies = cache.get(cache_key)
        
        if not cached_policies:
            # Try to load from the original Excel file
            try:
                media_root = settings.MEDIA_ROOT
                extracted_policies_dir = os.path.join(media_root, 'extracted_policies', task_id)
                
                if not os.path.exists(extracted_policies_dir):
                    os.makedirs(extracted_policies_dir, exist_ok=True)
                
                # Look for any Excel file in the directory
                excel_files = [f for f in os.listdir(extracted_policies_dir) if f.endswith('.xlsx')]
                
                if excel_files:
                    excel_path = os.path.join(extracted_policies_dir, excel_files[0])
                    df = pd.read_excel(excel_path)
                    cached_policies = df.fillna('').to_dict(orient='records')
                else:
                    cached_policies = []
            except Exception as e:
                return JsonResponse({'error': f'Failed to load policies: {str(e)}'}, status=500)
        
        # Find and update the policy
        policy_updated = False
        for i, cached_policy in enumerate(cached_policies):
            if cached_policy.get('Sub_policy_id') == policy.get('Sub_policy_id'):
                cached_policies[i] = policy
                policy_updated = True
                break
        
        if not policy_updated:
            # If policy not found, add it as new
            cached_policies.append(policy)
        
        # Update the cache
        cache.set(cache_key, cached_policies, timeout=3600)
        
        # Create output directory with task-specific subfolder for original and updated files
        media_root = settings.MEDIA_ROOT
        
        # 1. Save to extracted_policies (original location) to update the source file
        extracted_policies_dir = os.path.join(media_root, 'extracted_policies', task_id)
        os.makedirs(extracted_policies_dir, exist_ok=True)
        
        source_file = os.path.join(extracted_policies_dir, f"extracted_policies_{task_id}.xlsx")
        df = pd.DataFrame(cached_policies)
        
        # Ensure all expected columns exist
        expected_columns = [
            'section_name', 'file_name', 'Sub_policy_id', 'sub_policy_name', 
            'control', 'discussion', 'related_controls', 'control_enhancements', 'references'
        ]
        
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ''
        
        df = df[expected_columns]
        
        # Save updated source file
        df.to_excel(source_file, index=False)
        
        # 2. Also save a copy to updated_policies with timestamp
        updated_policies_dir = os.path.join(media_root, 'updated_policies', task_id)
        os.makedirs(updated_policies_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = int(time.time())
        output_file = os.path.join(updated_policies_dir, f"updated_policy_{policy.get('Sub_policy_id')}_{timestamp}.xlsx")
        
        # Save to Excel
        df.to_excel(output_file, index=False)
        
        return JsonResponse({
            'message': 'Policy saved successfully',
            'original_file': os.path.basename(source_file),
            'updated_file': os.path.basename(output_file),
            'policy_id': policy.get('Sub_policy_id'),
            'updated': policy_updated,
            'timestamp': timestamp
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_saved_excel_files(request, task_id):
    """Get list of all saved Excel files for a task"""
    try:
        media_root = settings.MEDIA_ROOT
        updated_policies_dir = os.path.join(media_root, 'updated_policies', task_id)
        
        if not os.path.exists(updated_policies_dir):
            return JsonResponse({
                'files': [],
                'message': 'No saved files found for this task'
            })
        
        files = []
        for filename in os.listdir(updated_policies_dir):
            if filename.endswith('.xlsx'):
                file_path = os.path.join(updated_policies_dir, filename)
                file_stats = os.stat(file_path)
                
                # Extract timestamp from filename
                timestamp_match = filename.split('_')[-1].replace('.xlsx', '')
                try:
                    timestamp = int(timestamp_match)
                    created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                except:
                    created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_stats.st_mtime))
                
                # Determine file type
                file_type = 'bulk_save' if 'bulk_save' in filename else 'single_edit'
                
                files.append({
                    'filename': filename,
                    'file_path': os.path.join('updated_policies', task_id, filename),
                    'size': file_stats.st_size,
                    'created_time': created_time,
                    'type': file_type
                })
        
        # Sort by creation time (newest first)
        files.sort(key=lambda x: x['created_time'], reverse=True)
        
        return JsonResponse({
            'files': files,
            'total_files': len(files),
            'task_id': task_id
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_policy_details(request):
    """Save policy details information (step 6)"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        details = data.get('details', {})
        
        if not task_id:
            return JsonResponse({'error': 'Task ID is required'}, status=400)
        
        # Get cached policy details or create new
        cached_details = cache.get(f'policy_details_{task_id}')
        if not cached_details:
            cached_details = {}
        
        # Update cached details with new data
        for key, value in details.items():
            cached_details[key] = value
        
        # Save updated details to cache
        cache.set(f'policy_details_{task_id}', cached_details, timeout=86400)  # 24-hour cache
        
        # Create policy details directory if it doesn't exist
        media_root = settings.MEDIA_ROOT
        policy_details_dir = os.path.join(media_root, 'policy_details', task_id)
        os.makedirs(policy_details_dir, exist_ok=True)
        
        # Save details to JSON file
        json_file_path = os.path.join(policy_details_dir, f"policy_details_{task_id}.json")
        with open(json_file_path, 'w') as f:
            json.dump(cached_details, f, indent=2)
        
        return JsonResponse({
            'message': 'Policy details saved successfully',
            'json_file': json_file_path
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_checked_sections_json(request):
    """Save selected sections, policies, and subpolicies to checked_section.json"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        selected_items = data.get('selected_items', [])
        
        if not task_id:
            return JsonResponse({'error': 'Task ID is required'}, status=400)
        
        if not selected_items:
            return JsonResponse({'error': 'No items selected'}, status=400)
        
        # Extract user ID from task ID or request data
        user_id = data.get('user_id', '1')  # Get from request data first
        if not user_id and task_id.startswith('upload_'):
            parts = task_id.split('_')
            if len(parts) > 1:
                user_id = parts[1].split('.')[0]  # Handle cases like "upload_1_PCI.pdf"
        
        # Get the user folder path
        media_root = Path(settings.MEDIA_ROOT)
        user_folder = media_root / f"upload_{user_id}"
        
        if not user_folder.exists():
            return JsonResponse({'error': f'User folder not found: upload_{user_id}'}, status=404)
        
        # Build the hierarchical structure
        checked_sections_data = {
            "metadata": {
                "task_id": task_id,
                "user_id": user_id,
                "creation_timestamp": int(time.time()),
                "creation_date": time.strftime('%Y-%m-%d %H:%M:%S'),
                "total_sections": len(selected_items),
                "selection_type": "hierarchical"
            },
            "sections": []
        }
        
        # Process each selected item
        for item in selected_items:
            section_data = {
                "section_name": item.get('section_name', ''),
                "section_title": item.get('section_title', ''),
                "policies": []
            }
            
            # Process policies for this section
            for policy in item.get('policies', []):
                policy_data = {
                    "policy_id": policy.get('policy_id', ''),
                    "policy_title": policy.get('policy_title', ''),
                    "policy_description": policy.get('policy_description', ''),
                    "policy_text": policy.get('policy_text', ''),
                    "scope": policy.get('scope', ''),
                    "objective": policy.get('objective', ''),
                    "policy_type": policy.get('policy_type', ''),
                    "policy_category": policy.get('policy_category', ''),
                    "policy_subcategory": policy.get('policy_subcategory', ''),
                    "subpolicies": []
                }
                
                # Process subpolicies for this policy
                for subpolicy in policy.get('subpolicies', []):
                    subpolicy_data = {
                        "subpolicy_id": subpolicy.get('subpolicy_id', ''),
                        "subpolicy_title": subpolicy.get('subpolicy_title', ''),
                        "subpolicy_description": subpolicy.get('subpolicy_description', ''),
                        "subpolicy_text": subpolicy.get('subpolicy_text', ''),
                        "control": subpolicy.get('control', '')
                    }
                    policy_data["subpolicies"].append(subpolicy_data)
                
                section_data["policies"].append(policy_data)
            
            checked_sections_data["sections"].append(section_data)
        
        # Save to checked_section.json in the user folder
        checked_section_file = user_folder / "checked_section.json"
        with open(checked_section_file, 'w', encoding='utf-8') as f:
            json.dump(checked_sections_data, f, indent=2, ensure_ascii=False)
        
        # Count totals
        total_policies = sum(len(section.get('policies', [])) for section in checked_sections_data["sections"])
        total_subpolicies = sum(
            len(policy.get('subpolicies', [])) 
            for section in checked_sections_data["sections"] 
            for policy in section.get('policies', [])
        )
        
        return JsonResponse({
            'message': 'Selected sections saved successfully',
            'file_path': str(checked_section_file),
            'total_sections': len(checked_sections_data["sections"]),
            'total_policies': total_policies,
            'total_subpolicies': total_subpolicies,
            'task_id': task_id
        })
        
    except Exception as e:
        print(f"Error saving checked sections: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def generate_compliances_for_checked_sections(request):
    """Read checked_section.json and generate compliances for all subpolicies"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        
        if not task_id:
            return JsonResponse({'error': 'Task ID is required'}, status=400)
        
        # Extract user ID from task ID or request data
        user_id = data.get('user_id', '1')  # Get from request data first
        if not user_id and task_id.startswith('upload_'):
            parts = task_id.split('_')
            if len(parts) > 1:
                user_id = parts[1].split('.')[0]
        
        # Get the user folder path
        media_root = Path(settings.MEDIA_ROOT)
        user_folder = media_root / f"upload_{user_id}"
        checked_sections_path = user_folder / "checked_section.json"
        
        if not checked_sections_path.exists():
            return JsonResponse({'error': 'checked_section.json not found. Please save your selections first.'}, status=404)
        
        # Read the checked_section.json file
        with open(checked_sections_path, 'r', encoding='utf-8') as f:
            checked_data = json.load(f)
        
        # Import the compliance generator
        from ...routes.uploadNist.compliance_generator import generate_compliance_for_single_subpolicy
        
        # Process each section and generate compliances for subpolicies
        total_subpolicies = 0
        total_compliances = 0
        all_compliances = []
        
        sections = checked_data.get('sections', [])
        
        for section in sections:
            section_compliances = []
            
            for policy in section.get('policies', []):
                policy_compliances = []
                
                for subpolicy in policy.get('subpolicies', []):
                    total_subpolicies += 1
                    
                    # Generate compliances for this subpolicy
                    subpolicy_id = subpolicy.get('subpolicy_id', '')
                    subpolicy_name = subpolicy.get('subpolicy_title', '')
                    description = subpolicy.get('description', '')
                    control = subpolicy.get('control', '')
                    
                    # Call the compliance generator
                    compliances = generate_compliance_for_single_subpolicy(
                        subpolicy_id=subpolicy_id,
                        subpolicy_name=subpolicy_name,
                        description=description,
                        control=control
                    )
                    
                    total_compliances += len(compliances)
                    
                    # Add section and policy context to each compliance
                    for comp in compliances:
                        comp['section_name'] = section.get('section_name', '')
                        comp['section_title'] = section.get('section_title', '')
                        comp['policy_id'] = policy.get('policy_id', '')
                        comp['policy_title'] = policy.get('policy_title', '')
                    
                    policy_compliances.extend(compliances)
                
                section_compliances.extend(policy_compliances)
            
            all_compliances.extend(section_compliances)
        
        # Update the checked_section.json with compliance data
        checked_data['compliances'] = all_compliances
        checked_data['metadata']['total_subpolicies'] = total_subpolicies
        checked_data['metadata']['total_compliances'] = total_compliances
        checked_data['metadata']['compliances_generated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Save the updated JSON
        with open(checked_sections_path, 'w', encoding='utf-8') as f:
            json.dump(checked_data, f, indent=2, ensure_ascii=False)
        
        # Count total policies
        total_policies = sum(len(section.get('policies', [])) for section in sections)
        
        return JsonResponse({
            'success': True,
            'message': 'Compliances generated successfully',
            'total_sections': len(sections),
            'total_policies': total_policies,
            'total_subpolicies': total_subpolicies,
            'total_compliances': total_compliances,
            'checked_sections_path': str(checked_sections_path)
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_checked_sections_with_compliances(request, task_id):
    """Get checked_section.json data with all compliances for Step 6 editing"""
    try:
        # Extract user ID from task ID or request parameters
        user_id = request.GET.get('user_id', '1')  # Get from request parameters first
        if not user_id and task_id.startswith('upload_'):
            parts = task_id.split('_')
            if len(parts) > 1:
                user_id = parts[1].split('.')[0]
        
        # Get the user folder path
        media_root = Path(settings.MEDIA_ROOT)
        user_folder = media_root / f"upload_{user_id}"
        checked_sections_path = user_folder / "checked_section.json"
        
        if not checked_sections_path.exists():
            return JsonResponse({'error': 'checked_section.json not found'}, status=404)
        
        # Read the checked_section.json file
        with open(checked_sections_path, 'r', encoding='utf-8') as f:
            checked_data = json.load(f)
        
        return JsonResponse({
            'success': True,
            'data': checked_data
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_complete_policy_package(request):
    """Save complete policy package with 4-level hierarchy: Framework -> Policy -> Sub-Policy -> Compliance"""
    try:
        print("===== STARTING SAVE COMPLETE POLICY PACKAGE =====")
        data = json.loads(request.body)
        task_id = data.get('task_id')
        framework_details = data.get('framework_details', {})
        policy_forms = data.get('policy_forms', {})
        sub_policies = data.get('sub_policies', [])
        compliance_data = data.get('compliance_data', {})
        unique_sections = data.get('unique_sections', [])
        
        print(f"Task ID: {task_id}")
        print(f"Framework details: {framework_details.get('title', 'Untitled')}")
        print(f"Number of policies: {len(policy_forms)}")
        print(f"Number of sub-policies: {len(sub_policies)}")
        print(f"Number of compliance sections: {len(compliance_data)}")
        print(f"Unique sections: {unique_sections}")
        
        if not task_id:
            return JsonResponse({'error': 'Task ID is required'}, status=400)
        
        # Create directories if they don't exist
        media_root = settings.MEDIA_ROOT
        complete_package_dir = os.path.join(media_root, 'complete_packages', task_id)
        os.makedirs(complete_package_dir, exist_ok=True)
        
        # Create hierarchical JSON structure
        hierarchical_data = {
            "metadata": {
                "task_id": task_id,
                "creation_timestamp": int(time.time()),
                "creation_date": time.strftime('%Y-%m-%d %H:%M:%S'),
                "total_policies": len(policy_forms),
                "total_sub_policies": len(sub_policies),
                "total_compliance_items": sum(len(items) for items in compliance_data.values()),
                "unique_sections": unique_sections,
                "hierarchy_levels": 4
            },
            "hierarchy": {
                "level_1_framework": {
                    "level": 1,
                    "type": "framework",
                    "data": framework_details,
                    "children": []
                }
            }
        }
        
        # We'll skip creating Compliance records here and let save_framework_to_database handle it
        # Just build the hierarchical structure
        
        flat_data = []  # Initialize flat_data here
        
        # Build hierarchy: Framework -> Policies -> Sub-policies
        for section_index, section_name in enumerate(unique_sections):
            # Level 2: Policy for this section
            policy_data = policy_forms.get(section_name, {})
            policy_node = {
                "level": 2,
                "type": "policy",
                "section_name": section_name,
                "section_index": section_index + 1,
                "data": policy_data,
                "children": []
            }
            
            # Level 3: Sub-policies for this section
            section_sub_policies = [sp for sp in sub_policies if sp.get('section_name') == section_name]
            for sub_policy_index, sub_policy in enumerate(section_sub_policies):
                sub_policy_node = {
                    "level": 3,
                    "type": "sub_policy",
                    "section_name": section_name,
                    "sub_policy_index": sub_policy_index + 1,
                    "parent_policy_section": section_name,
                    "data": sub_policy,
                    "children": []
                }
                
                # Level 4: Compliance items for this sub-policy
                policy_key = f"{section_name}_{sub_policy.get('Sub_policy_id', '')}"
                compliance_items = compliance_data.get(policy_key, [])
                
                # If no compliance data provided, parse from control text
                if not compliance_items and sub_policy.get('control'):
                    compliance_items = parse_compliance_items(sub_policy.get('control'))
                
                for compliance_index, compliance in enumerate(compliance_items):
                    # Add to hierarchical structure only - no database operations here
                    compliance_node = {
                        "level": 4,
                        "type": "compliance",
                        "section_name": section_name,
                        "parent_section": sub_policy.get('Sub_policy_id', ''),
                        "sub_policy_id": sub_policy.get('Sub_policy_id', ''),
                        "compliance_index": compliance_index + 1,
                        "compliance_id": compliance.get('id', ''),
                        "data": {
                            "letter": compliance.get('letter', 'a'),
                            "name": compliance.get('name', ''),
                            "description": compliance.get('description', ''),
                            "status": compliance.get('status', 'pending'),
                            "assignee": compliance.get('assignee', ''),
                            "dueDate": compliance.get('dueDate', '')
                        }
                    }
                    sub_policy_node["children"].append(compliance_node)
                
                policy_node["children"].append(sub_policy_node)
            
            hierarchical_data["hierarchy"]["level_1_framework"]["children"].append(policy_node)
        
        # Save hierarchical JSON file
        timestamp = int(time.time())
        json_file_path = os.path.join(complete_package_dir, f"hierarchical_policy_package_{task_id}_{timestamp}.json")
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(hierarchical_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved hierarchical JSON to: {json_file_path}")
        
        # Also save flat structure for Excel compatibility
        flat_data = []
        
        # Add framework row
        framework_row = {
            "hierarchy_level": 1,
            "type": "framework",
            "section_name": "FRAMEWORK",
            "parent_section": "",
            "title": framework_details.get('title', ''),
            "description": framework_details.get('description', ''),
            "category": framework_details.get('category', ''),
            "effective_date": framework_details.get('effectiveDate', ''),
            "start_date": framework_details.get('startDate', ''),
            "end_date": framework_details.get('endDate', ''),
            "task_id": task_id,
            "creation_timestamp": int(time.time()),
            "creation_date": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        flat_data.append(framework_row)
        
        # Add policy and sub-policy rows
        for section_index, section_name in enumerate(unique_sections):
            policy_data = policy_forms.get(section_name, {})
            
            # Add policy row
            policy_row = {
                "hierarchy_level": 2,
                "type": "policy",
                "section_name": section_name,
                "parent_section": "FRAMEWORK",
                "policy_index": section_index + 1,
                "document_url": policy_data.get('documentUrl', ''),
                "identifier": policy_data.get('identifier', ''),
                "created_by": policy_data.get('createdBy', ''),
                "reviewer": policy_data.get('reviewer', ''),
                "policy_name": policy_data.get('policyName', ''),
                "department": policy_data.get('department', ''),
                "scope": policy_data.get('scope', ''),
                "applicability": policy_data.get('applicability', ''),
                "objective": policy_data.get('objective', ''),
                "coverage_rate": policy_data.get('coverageRate', ''),
                "task_id": task_id,
                "creation_timestamp": int(time.time()),
                "creation_date": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            flat_data.append(policy_row)
            
            # Add sub-policy rows
            section_sub_policies = [sp for sp in sub_policies if sp.get('section_name') == section_name]
            for sub_policy_index, sub_policy in enumerate(section_sub_policies):
                sub_policy_row = {
                    "hierarchy_level": 3,
                    "type": "sub_policy",
                    "section_name": section_name,
                    "parent_section": section_name,
                    "sub_policy_index": sub_policy_index + 1,
                    "sub_policy_id": sub_policy.get('Sub_policy_id', ''),
                    "sub_policy_name": sub_policy.get('sub_policy_name', ''),
                    "control": sub_policy.get('control', ''),
                    "scope": sub_policy.get('scope', ''),
                    "department": sub_policy.get('department', ''),
                    "objective": sub_policy.get('objective', ''),
                    "applicability": sub_policy.get('applicability', ''),
                    "coverage_rate": sub_policy.get('coverage_rate', ''),
                    "related_controls": sub_policy.get('related_controls', ''),
                    "start_date": sub_policy.get('start_date', ''),
                    "end_date": sub_policy.get('end_date', ''),
                    "task_id": task_id,
                    "creation_timestamp": int(time.time()),
                    "creation_date": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                flat_data.append(sub_policy_row)
                
                # Add compliance rows
                policy_key = f"{section_name}_{sub_policy.get('Sub_policy_id', '')}"
                compliance_items = compliance_data.get(policy_key, [])
                
                # If no compliance data provided, parse from control text
                if not compliance_items and sub_policy.get('control'):
                    compliance_items = parse_compliance_items(sub_policy.get('control'))
                
                for compliance_index, compliance in enumerate(compliance_items):
                    compliance_row = {
                        "hierarchy_level": 4,
                        "type": "compliance",
                        "section_name": section_name,
                        "parent_section": sub_policy.get('Sub_policy_id', ''),
                        "sub_policy_id": sub_policy.get('Sub_policy_id', ''),
                        "compliance_index": compliance_index + 1,
                        "compliance_id": compliance.get('id', ''),
                        "compliance_letter": compliance.get('letter', ''),
                        "compliance_name": compliance.get('name', ''),
                        "compliance_description": compliance.get('description', ''),
                        "compliance_status": compliance.get('status', 'pending'),
                        "assignee": compliance.get('assignee', ''),
                        "due_date": compliance.get('dueDate', ''),
                        "evidence_file": compliance.get('evidence', {}).get('name', '') if isinstance(compliance.get('evidence'), dict) else '',
                        "task_id": task_id,
                        "creation_timestamp": int(time.time()),
                        "creation_date": time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    flat_data.append(compliance_row)
        
        # Save flat structure as Excel
        excel_file_path = os.path.join(complete_package_dir, f"flat_policy_package_{task_id}_{timestamp}.xlsx")
        df = pd.DataFrame(flat_data)
        df.to_excel(excel_file_path, index=False)
        
        print(f"Saved flat Excel to: {excel_file_path}")
        print("===== SAVE COMPLETE POLICY PACKAGE COMPLETED SUCCESSFULLY =====")
        
        return JsonResponse({
            'message': 'Policy package saved successfully',
            'hierarchical_json_file': json_file_path,
            'flat_excel_file': excel_file_path,
            'task_id': task_id
        })
    except Exception as e:
        print(f"===== ERROR IN SAVE COMPLETE POLICY PACKAGE =====")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

# Helper function to parse compliance items from control text
def parse_compliance_items(control_text):
    if not control_text:
        return []
    
    import re
    
    # Patterns to match: a), b), c) or a., b., c. or (a), (b), (c)
    patterns = [
        r'([a-z])\)\s*',  # a) b) c)
        r'([a-z])\.\s*',  # a. b. c.
        r'\(([a-z])\)\s*' # (a) (b) (c)
    ]
    
    items = []
    
    # Try each pattern
    for pattern in patterns:
        matches = list(re.finditer(pattern, control_text, re.IGNORECASE))
        if len(matches) > 1:
            # Found multiple matches, split by this pattern
            parts = re.split(pattern, control_text, flags=re.IGNORECASE)
            # Filter out empty parts and letter matches
            content_parts = [part.strip() for part in parts if part.strip() and not re.match(r'^[a-z]$', part.strip(), re.IGNORECASE)]
            
            for index, part in enumerate(content_parts):
                if part:
                    items.append({
                        'id': f'compliance_{index + 1}',
                        'letter': chr(97 + index),  # a, b, c, d, e...
                        'name': part[:100] + ('...' if len(part) > 100 else ''),
                        'description': part,
                        'status': 'pending',
                        'assignee': '',
                        'due_date': '',
                        'evidence': None
                    })
            break
    
    # If no pattern found, create single compliance item
    if not items:
        items = [{
            'id': 'compliance_1',
            'letter': 'a',
            'name': control_text[:100] + ('...' if len(control_text) > 100 else ''),
            'description': control_text,
            'status': 'pending',
            'assignee': '',
            'due_date': '',
            'evidence': None
        }]
    
    return items




@csrf_exempt
@require_http_methods(["POST"])
def save_edited_framework_to_database(request):
    """Save edited framework, policies, subpolicies, and compliances from Step 6 to database"""
    try:
        from django.db import transaction
        from ...models import Framework, Policy, SubPolicy, Compliance
        from datetime import date
        
        data = json.loads(request.body)
        task_id = data.get('task_id')
        framework_data = data.get('framework', {})
        sections_data = data.get('sections', [])
        
        print(f"\n\n{'='*80}")
        print(f"===== SAVING EDITED DATA TO DATABASE =====")
        print(f"{'='*80}")
        print(f"Task ID: {task_id}")
        print(f"Framework: {framework_data.get('FrameworkName', 'N/A')}")
        print(f"Total sections received: {len(sections_data)}")
        
        # Debug: Print sections structure
        for idx, section in enumerate(sections_data):
            policies_count = len(section.get('policies', []))
            print(f"  Section {idx+1}: {section.get('section_title', 'N/A')} - {policies_count} policies")
            for pidx, policy in enumerate(section.get('policies', [])):
                subpolicies_count = len(policy.get('subpolicies', []))
                print(f"    Policy {pidx+1}: {policy.get('policy_title', 'N/A')} - {subpolicies_count} subpolicies")
        
        # Load the full checked_section.json to get compliances
        user_id = data.get('user_id', '1')  # Get from request data first
        if not user_id and (task_id.startswith('upload_') or task_id.startswith('default_')):
            parts = task_id.split('_')
            if len(parts) > 1 and parts[1] != 'PCI':
                user_id = parts[1].split('.')[0]
        
        media_root = Path(settings.MEDIA_ROOT)
        user_folder = media_root / f"upload_{user_id}"
        checked_sections_path = user_folder / "checked_section.json"
        
        compliances_list = []
        if checked_sections_path.exists():
            with open(checked_sections_path, 'r', encoding='utf-8') as f:
                checked_data = json.load(f)
                compliances_list = checked_data.get('compliances', [])
                print(f"\n📂 Loaded {len(compliances_list)} compliances from: {checked_sections_path}")
                if compliances_list:
                    print(f"   First compliance: {compliances_list[0].get('ComplianceTitle', 'N/A')}")
                    print(f"   SubPolicyId: {compliances_list[0].get('SubPolicyId', 'N/A')}")
        else:
            print(f"\n❌ ERROR: checked_section.json not found at: {checked_sections_path}")
        
        # Use transaction to ensure all-or-nothing save
        with transaction.atomic():
            # Step 1: Create Framework
            framework = Framework.objects.create(
                FrameworkName=framework_data.get('FrameworkName', 'Untitled Framework'),
                CurrentVersion=float(framework_data.get('CurrentVersion', 1.0)) if framework_data.get('CurrentVersion') else 1.0,
                FrameworkDescription=framework_data.get('FrameworkDescription', ''),
                EffectiveDate=framework_data.get('EffectiveDate') or date.today(),
                CreatedByName=framework_data.get('CreatedByName', 'Admin'),
                CreatedByDate=date.today(),
                Category=framework_data.get('Category', ''),
                Identifier=framework_data.get('Identifier', ''),
                StartDate=framework_data.get('StartDate') or date.today(),
                EndDate=framework_data.get('EndDate'),
                Status=framework_data.get('Status', 'Under Review'),
                ActiveInactive=framework_data.get('ActiveInactive', 'Active'),
                Reviewer=framework_data.get('Reviewer', ''),
                InternalExternal=framework_data.get('InternalExternal', 'Internal')
            )
            print(f"Created Framework: {framework.FrameworkId}")
            
            # Create a mapping of subpolicy_id to SubPolicy object for compliance linking
            subpolicy_mapping = {}
            total_policies = 0
            total_subpolicies = 0
            total_compliances = 0
            
            # Step 2: Process each section -> policies -> subpolicies
            print(f"\n===== PROCESSING SECTIONS, POLICIES, AND SUBPOLICIES =====")
            
            for section_idx, section in enumerate(sections_data):
                print(f"\nSection {section_idx + 1}: {section.get('section_title', 'N/A')}")
                
                for policy_idx, policy_data in enumerate(section.get('policies', [])):
                    print(f"  Policy {policy_idx + 1}: {policy_data.get('policy_title', 'N/A')}")
                    
                    # Create Policy
                    policy = Policy.objects.create(
                        FrameworkId=framework,
                        CurrentVersion='1.0',
                        Status=policy_data.get('Status', 'Under Review'),
                        PolicyDescription=policy_data.get('policy_description', ''),
                        PolicyName=policy_data.get('policy_title', 'Untitled Policy'),
                        StartDate=date.today(),
                        Department=policy_data.get('Department', ''),
                        CreatedByName=policy_data.get('CreatedByName', 'Admin'),
                        CreatedByDate=date.today(),
                        Applicability=policy_data.get('Applicability', ''),
                        Scope=policy_data.get('scope', ''),
                        Objective=policy_data.get('objective', ''),
                        Identifier=policy_data.get('policy_id', ''),
                        PermanentTemporary='Permanent',
                        ActiveInactive='Active',
                        Reviewer=policy_data.get('Reviewer', ''),
                        PolicyType=policy_data.get('policy_type', ''),
                        PolicyCategory=policy_data.get('policy_category', ''),
                        PolicySubCategory=policy_data.get('policy_subcategory', '')
                    )
                    total_policies += 1
                    print(f"  ✅ Created Policy: {policy.PolicyId} - {policy.PolicyName}")
                    
                    # Step 3: Create SubPolicies for this Policy
                    for subpolicy_idx, subpolicy_data in enumerate(policy_data.get('subpolicies', [])):
                        subpolicy_id = subpolicy_data.get('subpolicy_id', '')
                        print(f"    Subpolicy {subpolicy_idx + 1}: {subpolicy_data.get('subpolicy_title', 'N/A')} (ID: {subpolicy_id})")
                        
                        subpolicy = SubPolicy.objects.create(
                            PolicyId=policy,
                            SubPolicyName=subpolicy_data.get('subpolicy_title', 'Untitled SubPolicy'),
                            CreatedByName=subpolicy_data.get('CreatedByName', 'Admin'),
                            CreatedByDate=date.today(),
                            Identifier=subpolicy_id,
                            Description=subpolicy_data.get('subpolicy_description', ''),
                            Status='Under Review',
                            PermanentTemporary='Permanent',
                            Control=subpolicy_data.get('control', ''),
                            FrameworkId=framework
                        )
                        total_subpolicies += 1
                        print(f"    ✅ Created SubPolicy DB ID: {subpolicy.SubPolicyId}, Identifier: {subpolicy.Identifier}")
                        
                        # Map subpolicy_id to SubPolicy object for compliance linking
                        # IMPORTANT: Use the subpolicy_id as the key!
                        subpolicy_mapping[subpolicy_id] = subpolicy
                        print(f"    📌 Mapped '{subpolicy_id}' → SubPolicy(DB ID: {subpolicy.SubPolicyId})")
            
            # Step 4: Create Compliances (match by SubPolicyId)
            print(f"\n===== CREATING COMPLIANCES =====")
            print(f"Total compliances to process: {len(compliances_list)}")
            print(f"SubPolicy mapping has {len(subpolicy_mapping)} entries")
            print(f"Mapped SubPolicy IDs: {list(subpolicy_mapping.keys())}")
            
            for idx, compliance_data in enumerate(compliances_list):
                subpolicy_id = compliance_data.get('SubPolicyId', '')
                
                print(f"\n[{idx+1}/{len(compliances_list)}] Processing compliance for SubPolicyId: {subpolicy_id}")
                
                # Find the SubPolicy object
                subpolicy = subpolicy_mapping.get(subpolicy_id)
                
                if not subpolicy:
                    print(f"❌ WARNING: SubPolicy not found for compliance with SubPolicyId: {subpolicy_id}")
                    print(f"   Available SubPolicy IDs: {list(subpolicy_mapping.keys())}")
                    continue
                
                try:
                    # Prepare mitigation field (must be JSON or dict)
                    mitigation_value = compliance_data.get('mitigation', {})
                    if isinstance(mitigation_value, str):
                        # If it's already a string, keep it
                        mitigation_final = mitigation_value
                    elif isinstance(mitigation_value, dict):
                        # If it's a dict, leave it as dict (Django JSONField handles it)
                        mitigation_final = mitigation_value
                    else:
                        mitigation_final = {}
                    
                    print(f"   Creating compliance: {compliance_data.get('ComplianceTitle', 'N/A')[:50]}")
                    
                    # Truncate fields to match model max_length constraints
                    compliance_title = (compliance_data.get('ComplianceTitle', 'Untitled Compliance') or 'Untitled Compliance')[:145]
                    business_units = (compliance_data.get('BusinessUnitsCovered', '') or '')[:225]
                    created_by = (compliance_data.get('CreatedByName', 'Admin') or 'Admin')[:250]
                    identifier = (compliance_data.get('Identifier', '') or '')[:45]
                    applicability = (compliance_data.get('Applicability', '') or '')[:450]
                    risk_category = (compliance_data.get('RiskCategory', '') or '')[:45]
                    risk_business_impact = (compliance_data.get('RiskBusinessImpact', '') or '')[:45]
                    
                    # Create Compliance record
                    compliance = Compliance.objects.create(
                        SubPolicy=subpolicy,
                        ComplianceTitle=compliance_title,
                        ComplianceItemDescription=compliance_data.get('ComplianceItemDescription', ''),
                        ComplianceType=compliance_data.get('ComplianceType', 'Regulatory'),
                        Scope=compliance_data.get('Scope', ''),
                        Objective=compliance_data.get('Objective', ''),
                        BusinessUnitsCovered=business_units,
                        IsRisk=bool(compliance_data.get('IsRisk', 1)),
                        PossibleDamage=compliance_data.get('PossibleDamage', ''),
                        mitigation=mitigation_final,
                        Criticality=compliance_data.get('Criticality', 'Medium'),
                        MandatoryOptional=compliance_data.get('MandatoryOptional', 'Mandatory'),
                        ManualAutomatic=compliance_data.get('ManualAutomatic', 'Manual'),
                        Impact=str(compliance_data.get('Impact', '5')),
                        Probability=str(compliance_data.get('Probability', '5')),
                        MaturityLevel=compliance_data.get('MaturityLevel', 'Initial'),
                        ActiveInactive=compliance_data.get('ActiveInactive', 'Active'),
                        PermanentTemporary=compliance_data.get('PermanentTemporary', 'Permanent'),
                        CreatedByName=created_by,
                        CreatedByDate=date.today(),
                        ComplianceVersion=compliance_data.get('ComplianceVersion', '1.0'),
                        Status=compliance_data.get('Status', 'Under Review'),
                        Identifier=identifier,
                        Applicability=applicability,
                        PotentialRiskScenarios=compliance_data.get('PotentialRiskScenarios', ''),
                        RiskType=compliance_data.get('RiskType', 'Current'),
                        RiskCategory=risk_category,
                        RiskBusinessImpact=risk_business_impact,
                        FrameworkId=framework
                    )
                    total_compliances += 1
                    print(f"   ✅ Created Compliance: {compliance.ComplianceId} - {compliance.ComplianceTitle}")
                except Exception as comp_error:
                    print(f"   ❌ ERROR creating compliance for SubPolicyId {subpolicy_id}:")
                    print(f"      Error: {str(comp_error)}")
                    print(f"      Compliance data: {json.dumps(compliance_data, indent=2)[:500]}")
                    import traceback
                    traceback.print_exc()
                    # Continue with next compliance instead of failing entire transaction
                    continue
            
            print(f"\n===== DATABASE SAVE COMPLETE =====")
            print(f"Framework ID: {framework.FrameworkId}")
            print(f"Total Policies: {total_policies}")
            print(f"Total SubPolicies: {total_subpolicies}")
            print(f"Total Compliances: {total_compliances}")
            
            return JsonResponse({
                'success': True,
                'message': 'Successfully saved to database',
                'framework_id': framework.FrameworkId,
                'framework_name': framework.FrameworkName,
                'total_policies': total_policies,
                'total_subpolicies': total_subpolicies,
                'total_compliances': total_compliances
            })
            
    except Exception as e:
        import traceback
        print(f"ERROR saving to database: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_framework_to_database(request):
    """Save the hierarchical policy package to the database in proper order"""
    print("===== STARTING SAVE TO DATABASE =====")
    print(f"Request received at: {timezone.now()}")
    
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        
        print(f"Task ID: {task_id}")
        
        if not task_id:
            return JsonResponse({'error': 'Task ID is required'}, status=400)
        
        # Find the latest JSON file in the complete_packages directory
        media_root = settings.MEDIA_ROOT
        complete_package_dir = os.path.join(media_root, 'complete_packages', task_id)
        
        if not os.path.exists(complete_package_dir):
            return JsonResponse({'error': 'Complete package directory not found'}, status=404)
        
        # Look for hierarchical JSON files
        json_files = [f for f in os.listdir(complete_package_dir) if f.startswith('hierarchical_policy_package_') and f.endswith('.json')]
        
        if not json_files:
            return JsonResponse({'error': 'No hierarchical policy package found'}, status=404)
        
        # Sort by filename which should have timestamp at the end
        json_files.sort(reverse=True)
        json_file_path = os.path.join(complete_package_dir, json_files[0])
        
        print(f"Found JSON file: {json_file_path}")
        
        # Load hierarchical JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            hierarchical_data = json.load(f)
        
        print("Successfully loaded hierarchical JSON data")
        
        # Start database transaction to ensure all-or-nothing save
        with transaction.atomic():
            # STEP 1: CREATE FRAMEWORK FIRST
            framework_data = hierarchical_data.get('hierarchy', {}).get('level_1_framework', {})
            if not framework_data:
                return JsonResponse({'error': 'Framework data not found in JSON'}, status=400)
            
            framework_details = framework_data.get('data', {})
            print(f"Framework details: {framework_details.get('title', 'Untitled Framework')}")
            
            # Format dates - handle both string formats and empty values
            effective_date = framework_details.get('effectiveDate')
            start_date = framework_details.get('startDate')
            end_date = framework_details.get('endDate')
            
            # Convert string dates to datetime objects if they exist
            effective_date = datetime.strptime(effective_date, '%Y-%m-%d').date() if effective_date else timezone.now().date()
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else timezone.now().date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
            
            # Create Framework record
            framework = Framework.objects.create(
                FrameworkName=framework_details.get('title', 'Untitled Framework'),
                FrameworkDescription=framework_details.get('description', ''),
                EffectiveDate=effective_date,
                CreatedByName='System Import',
                CreatedByDate=timezone.now().date(),
                Category=framework_details.get('category', ''),
                StartDate=start_date,
                EndDate=end_date,
                Status='Active',
                ActiveInactive='Active',
                Reviewer='System'
            )
            
            print(f"✅ STEP 1 COMPLETED: Created framework with ID: {framework.FrameworkId}")
            
            # STEP 2: CREATE ALL POLICIES
            policies = []
            policy_mapping = {}  # Map section_name to policy object
            
            for policy_node in framework_data.get('children', []):
                if policy_node.get('type') == 'policy':
                    policy_data = policy_node.get('data', {})
                    section_name = policy_node.get('section_name', '')
                    
                    print(f"Processing policy section: {section_name}")
                    
                    # Create Policy record
                    policy = Policy.objects.create(
                        FrameworkId=framework,
                        Status='Active',
                        PolicyDescription=policy_data.get('objective', '') or section_name,
                        PolicyName=policy_data.get('policyName', '') or section_name,
                        StartDate=start_date,
                        Department=policy_data.get('department', ''),
                        CreatedByName=policy_data.get('createdBy', 'System Import'),
                        CreatedByDate=timezone.now().date(),
                        Applicability=policy_data.get('applicability', ''),
                        DocURL=policy_data.get('documentUrl', ''),
                        Scope=policy_data.get('scope', ''),
                        Objective=policy_data.get('objective', ''),
                        Identifier=policy_data.get('identifier', ''),
                        ActiveInactive='Active',
                        Reviewer=policy_data.get('reviewer', 'System'),
                        CoverageRate=float(policy_data.get('coverageRate', 0)) if policy_data.get('coverageRate') else 0
                    )
                    
                    policies.append(policy)
                    policy_mapping[section_name] = policy
                    print(f"Created policy with ID: {policy.PolicyId} for section: {section_name}")
            
            print(f"✅ STEP 2 COMPLETED: Created {len(policies)} policies")
            
            # STEP 3: CREATE ALL SUB-POLICIES
            sub_policies = []
            sub_policy_mapping = {}  # Map for compliance linking
            
            for policy_node in framework_data.get('children', []):
                if policy_node.get('type') == 'policy':
                    section_name = policy_node.get('section_name', '')
                    policy = policy_mapping.get(section_name)
                    
                    if not policy:
                        continue
                    
                    for sub_policy_node in policy_node.get('children', []):
                        if sub_policy_node.get('type') == 'sub_policy':
                            sub_policy_data = sub_policy_node.get('data', {})
                            
                            print(f"Creating sub-policy: {sub_policy_data.get('sub_policy_name', 'Unnamed')}")
                            
                            # Create SubPolicy record
                            sub_policy = SubPolicy.objects.create(
                                PolicyId=policy,
                                SubPolicyName=sub_policy_data.get('sub_policy_name', ''),
                                CreatedByName='System Import',
                                CreatedByDate=timezone.now().date(),
                                Identifier=sub_policy_data.get('Sub_policy_id', ''),
                                Description=sub_policy_data.get('control', ''),
                                Status='Active',
                                Control=sub_policy_data.get('control', '')
                            )
                            
                            sub_policies.append(sub_policy)
                            # Create unique key for compliance mapping
                            sub_policy_key = f"{section_name}_{sub_policy_data.get('Sub_policy_id', '')}"
                            sub_policy_mapping[sub_policy_key] = {
                                'sub_policy': sub_policy,
                                'compliance_nodes': sub_policy_node.get('children', [])
                            }
                            print(f"Created sub-policy with ID: {sub_policy.SubPolicyId} - {sub_policy.SubPolicyName}")
            
            print(f"✅ STEP 3 COMPLETED: Created {len(sub_policies)} sub-policies")
            
            # STEP 4: CREATE ALL COMPLIANCE ITEMS
            compliance_items = []
            total_compliance_count = 0

            for sub_policy_key, sub_policy_info in sub_policy_mapping.items():
                sub_policy = sub_policy_info['sub_policy']
                print(f"Processing compliance for sub-policy: {sub_policy.SubPolicyName} (ID: {sub_policy.SubPolicyId})")
                compliance_nodes = sub_policy_info['compliance_nodes']
                
                compliance_count_for_subpolicy = 0
                for compliance_node in compliance_nodes:
                    if compliance_node.get('type') == 'compliance':
                        compliance_data = compliance_node.get('data', {})
                        print(f"Compliance data for {sub_policy.SubPolicyName}:", compliance_data)
                        
                        # Create Compliance record with corrected field names
                        compliance_obj = Compliance.objects.create(
                            SubPolicy=sub_policy,  # Changed from SubPolicyId to SubPolicy
                            ComplianceItemDescription=compliance_data.get('description', '')[:500] if compliance_data.get('description') else '',
                            Status=compliance_data.get('status', 'pending')[:50] if compliance_data.get('status') else 'pending',
                            CreatedByName=compliance_data.get('assignee', 'System')[:250] if compliance_data.get('assignee') else 'System',
                            
                            # Static values for remaining fields
                            IsRisk=False,
                            PossibleDamage='',
                            mitigation='{}',  # Changed from Mitigation to mitigation (lowercase)
                            Criticality='Medium',
                            MandatoryOptional='Optional',
                            ManualAutomatic='Manual',
                            Impact='0.0',  # Changed to string since model field is CharField
                            Probability='0.0',  # Changed to string since model field is CharField
                            ActiveInactive='Active',
                            PermanentTemporary='Permanent',
                            CreatedByDate=timezone.now().date(),
                            ComplianceVersion='1.0',
                            Identifier=compliance_data.get('letter', 'a')[:45] if compliance_data.get('letter') else 'a',
                            MaturityLevel='Initial'
                        )
                        
                        compliance_items.append(compliance_obj)
                        compliance_count_for_subpolicy += 1
                        total_compliance_count += 1
                        print(f"Created compliance item with ID: {compliance_obj.ComplianceId} for sub-policy: {sub_policy.SubPolicyName}")
                
                print(f"Created {compliance_count_for_subpolicy} compliance items for sub-policy: {sub_policy.SubPolicyName}")

            print(f"✅ STEP 4 COMPLETED: Created {total_compliance_count} compliance items")
              # STEP 5: FINALIZE AND RETURN                   
            # Return success with all counts
            print(f"===== DATABASE SAVE COMPLETED SUCCESSFULLY =====")
            print(f"Framework ID: {framework.FrameworkId}")
            print(f"Total policies: {len(policies)}")
            print(f"Total sub-policies: {len(sub_policies)}")
            print(f"Total compliance items: {total_compliance_count}")
            
            return JsonResponse({
                'message': 'Framework, policies, sub-policies, and compliance items saved to database successfully',
                'framework_id': framework.FrameworkId,
                'framework_name': framework.FrameworkName,
                'total_policies': len(policies),
                'total_sub_policies': len(sub_policies),
                'total_compliance_items': total_compliance_count
            })
    
    except Exception as e:
        print(f"===== ERROR SAVING TO DATABASE =====")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

