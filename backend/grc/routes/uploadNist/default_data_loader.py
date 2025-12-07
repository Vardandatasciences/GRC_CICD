import os
import json
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from pathlib import Path

logger = logging.getLogger(__name__)

def get_temp_media_root():
    """Get the TEMP_MEDIA_ROOT path - defaults to backend/TEMP_MEDIA_ROOT"""
    temp_media_root = getattr(settings, 'TEMP_MEDIA_ROOT', None)
    if not temp_media_root:
        # Default to backend/TEMP_MEDIA_ROOT (same level as manage.py)
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from routes/uploadNist to backend
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir)))
        temp_media_root = os.path.join(backend_dir, 'TEMP_MEDIA_ROOT')
    return temp_media_root

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def load_default_data(request):
    """
    Load default data from TEMP_MEDIA_ROOT directory
    Returns complete hierarchical structure: sections → policies → subpolicies
    """
    try:
        temp_media_root = get_temp_media_root()
        logger.info(f"Loading default data from {temp_media_root}")
        
        # Define paths to important directories and files
        sections_dir = os.path.join(temp_media_root, 'sections_PCI_DSS_2')
        policies_dir = os.path.join(temp_media_root, 'policies_PCI_DSS_2')
        
        # Check if required directories exist
        if not os.path.exists(sections_dir):
            return JsonResponse({"success": False, "error": f"Sections directory not found: {sections_dir}"}, status=404)
        
        if not os.path.exists(policies_dir):
            return JsonResponse({"success": False, "error": f"Policies directory not found: {policies_dir}"}, status=404)
        
        # Load policies data first
        policies_file = os.path.join(policies_dir, 'all_policies.json')
        if not os.path.exists(policies_file):
            return JsonResponse({"success": False, "error": f"Policies file not found: {policies_file}"}, status=404)
            
        with open(policies_file, 'r', encoding='utf-8') as f:
            policies_data = json.load(f)
        
        # Build complete hierarchical structure with sections, policies, and subpolicies
        sections_data = build_complete_structure(sections_dir, policies_data)
        
        # Generate task ID for this default data session
        task_id = f"default_PCI_DSS_2_{request.user.id if hasattr(request, 'user') and hasattr(request.user, 'id') else '1'}"
        
        # Count total policies and subpolicies
        total_policies = 0
        total_subpolicies = 0
        for section in sections_data:
            total_policies += len(section.get('policies', []))
            for policy in section.get('policies', []):
                total_subpolicies += len(policy.get('subpolicies', []))
        
        # Return the combined data
        response_data = {
            "success": True,
            "task_id": task_id,
            "framework_name": "PCI DSS 2",
            "sections": sections_data,
            "total_sections": len(sections_data),
            "total_policies": total_policies,
            "total_subpolicies": total_subpolicies,
            "source": "TEMP_MEDIA_ROOT"
        }
        
        logger.info(f"Successfully loaded default data: {len(sections_data)} sections, {total_policies} policies, {total_subpolicies} subpolicies")
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.exception(f"Error loading default data: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

def build_complete_structure(sections_dir, policies_data):
    """
    Build complete hierarchical structure: sections → policies → subpolicies
    All in proper order with checkboxes at every level
    """
    sections = []
    sections_folder = os.path.join(sections_dir, 'sections')
    
    if not os.path.exists(sections_folder):
        logger.error(f"Sections folder not found: {sections_folder}")
        return sections
    
    try:
        # Get all section folders and sort them by numeric prefix (001, 002, 003, etc.)
        all_folders = [f for f in os.listdir(sections_folder) if os.path.isdir(os.path.join(sections_folder, f))]
        
        # Sort by extracting the numeric prefix from folder names
        def get_sort_key(folder_name):
            if '-' in folder_name:
                prefix = folder_name.split('-')[0]
                try:
                    return int(prefix)  # Convert to integer for proper numeric sorting
                except ValueError:
                    return 999  # Put non-numeric folders at the end
            return 999
        
        section_folders = sorted(all_folders, key=get_sort_key)
        logger.info(f"Section folders in order: {section_folders}")
        
        logger.info(f"Found {len(section_folders)} section folders")
        
        for idx, section_folder in enumerate(section_folders):
            section_path = os.path.join(sections_folder, section_folder)
            
            # Read content.json for section title and content
            content_file = os.path.join(section_path, 'content.json')
            section_title = section_folder.split('-', 1)[-1].replace('_', ' ') if '-' in section_folder else section_folder.replace('_', ' ')
            section_content = ''
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content_data = json.load(f)
                        section_title = content_data.get('name', section_title)
                        section_content = content_data.get('content', '')
                except Exception as e:
                    logger.warning(f"Error reading content.json for {section_folder}: {str(e)}")
            
            # Get all policies for this section from all_policies.json
            section_policies = _get_policies_for_section_internal(policies_data, section_folder)
            
            # Build the section object with complete hierarchy
            section_obj = {
                'id': idx,
                'section_id': f"section_{idx}",
                'title': section_title,
                'folder': section_folder,
                'content': section_content,
                'selected': False,
                'expanded': False,
                'policies': section_policies,
                'total_policies': len(section_policies),
                'total_subpolicies': sum(len(p.get('subpolicies', [])) for p in section_policies)
            }
            
            sections.append(section_obj)
            
        logger.info(f"Built {len(sections)} sections with complete hierarchy")
        
    except Exception as e:
        logger.exception(f"Error building complete structure: {str(e)}")
    
    return sections

def _get_policies_for_section_internal(policies_data, section_folder):
    """
    Internal helper: Get all policies for a specific section from all_policies.json
    Returns policies with their subpolicies in proper structure
    """
    section_policies = []
    
    try:
        for policy_entry in policies_data:
            section_info = policy_entry.get('section_info', {})
            folder_path = section_info.get('folder_path', '')
            
            # Normalize paths for comparison
            folder_path_normalized = folder_path.replace('\\', '/').strip('/')
            section_folder_normalized = section_folder.replace('\\', '/').strip('/')
            
            # Check if this policy belongs to the current section or its subsections
            if (folder_path_normalized == section_folder_normalized or 
                folder_path_normalized.startswith(section_folder_normalized + '/')):
                analysis = policy_entry.get('analysis', {})
                policies = analysis.get('policies', [])
                
                for policy_idx, policy in enumerate(policies):
                    # Format policy with all details
                    formatted_policy = {
                        'policy_id': policy.get('policy_id'),
                        'policy_title': policy.get('policy_title'),
                        'policy_description': policy.get('policy_description'),
                        'policy_text': policy.get('policy_text'),
                        'scope': policy.get('scope'),
                        'objective': policy.get('objective'),
                        'policy_type': policy.get('policy_type'),
                        'policy_category': policy.get('policy_category'),
                        'policy_subcategory': policy.get('policy_subcategory'),
                        'selected': False,
                        'expanded': False,
                        'subpolicies': []
                    }
                    
                    # Add all subpolicies
                    subpolicies = policy.get('subpolicies', [])
                    for subpolicy_idx, subpolicy in enumerate(subpolicies):
                        formatted_subpolicy = {
                            'subpolicy_id': subpolicy.get('subpolicy_id'),
                            'subpolicy_title': subpolicy.get('subpolicy_title'),
                            'subpolicy_description': subpolicy.get('subpolicy_description'),
                            'subpolicy_text': subpolicy.get('subpolicy_text'),
                            'control': subpolicy.get('control'),
                            'selected': False
                        }
                        formatted_policy['subpolicies'].append(formatted_subpolicy)
                    
                    section_policies.append(formatted_policy)
                    
    except Exception as e:
        logger.exception(f"Error getting policies for section {section_folder}: {str(e)}")
    
    return section_policies

def build_sections_from_index(sections_dir, sections_index):
    """Build section data from sections_index.json"""
    sections = []
    
    try:
        # Handle both list and string formats
        if isinstance(sections_index, str):
            # If it's a string, try to parse it as JSON
            try:
                sections_index = json.loads(sections_index)
            except:
                logger.warning("Could not parse sections_index as JSON, treating as folder list")
                return build_sections_from_folders(sections_dir)
        
        if not isinstance(sections_index, list):
            logger.warning("sections_index is not a list, using folder structure")
            return build_sections_from_folders(sections_dir)
        
        for idx, section in enumerate(sections_index):
            # Skip if section doesn't have required fields or is not a dict
            if not isinstance(section, dict) or not section.get('title') or not section.get('folder'):
                continue
                
            section_folder = section.get('folder')
            section_path = os.path.join(sections_dir, 'sections', section_folder)
            
            # Check if section folder exists
            if not os.path.exists(section_path):
                continue
                
            # Read content.json for section title and content
            content_file = os.path.join(section_path, 'content.json')
            section_title = section.get('title')
            section_content = section.get('content', '')
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r') as f:
                        content_data = json.load(f)
                        section_title = content_data.get('name', section_title)
                        section_content = content_data.get('content', section_content)
                except Exception as e:
                    logger.warning(f"Error reading content.json for {section_folder}: {str(e)}")
            
            # Get subsections based on PDFs in the section folder
            subsections = []
            try:
                for pdf_file in os.listdir(section_path):
                    if pdf_file.endswith('.pdf'):
                        control_id = pdf_file.replace('.pdf', '')
                        subsection_title = control_id.replace('_', ' ')
                        
                        subsections.append({
                            'title': subsection_title,
                            'control_id': control_id,
                            'selected': False,
                            'showPDF': False,
                            'path': os.path.join(section_path, pdf_file),
                            'relative_path': f"sections/{section_folder}/{pdf_file}"
                        })
            except Exception as e:
                logger.warning(f"Error processing subsections for {section_folder}: {str(e)}")
            
            # Add section with subsections
            sections.append({
                'id': idx,
                'title': section_title,
                'folder': section_folder,
                'selected': False,
                'expanded': False,  # Start collapsed
                'subsections': subsections,
                'content': section_content
            })
            
    except Exception as e:
        logger.exception(f"Error building sections from index: {str(e)}")
        
    return sections

def build_sections_from_folders(sections_dir):
    """Build section data from folder structure as fallback"""
    sections = []
    sections_folder = os.path.join(sections_dir, 'sections')
    
    if not os.path.exists(sections_folder):
        return sections
        
    try:
        for idx, section_folder in enumerate(os.listdir(sections_folder)):
            section_path = os.path.join(sections_folder, section_folder)
            
            if not os.path.isdir(section_path):
                continue
            
            # Read content.json for section title and content
            content_file = os.path.join(section_path, 'content.json')
            section_title = section_folder.split('-', 1)[-1].replace('_', ' ')
            section_content = ''
            
            if os.path.exists(content_file):
                try:
                    with open(content_file, 'r') as f:
                        content_data = json.load(f)
                        section_title = content_data.get('name', section_title)
                        section_content = content_data.get('content', '')
                except Exception as e:
                    logger.warning(f"Error reading content.json for {section_folder}: {str(e)}")
            
            if not section_title:
                section_title = f"Section {idx+1}"
                
            # Get subsections based on PDFs in the section folder
            subsections = []
            try:
                for pdf_file in os.listdir(section_path):
                    if pdf_file.endswith('.pdf'):
                        control_id = pdf_file.replace('.pdf', '')
                        subsection_title = control_id.replace('_', ' ')
                        
                        subsections.append({
                            'title': subsection_title,
                            'control_id': control_id,
                            'selected': False,
                            'showPDF': False,
                            'path': os.path.join(section_path, pdf_file),
                            'relative_path': f"sections/{section_folder}/{pdf_file}"
                        })
            except Exception as e:
                logger.warning(f"Error processing subsections for {section_folder}: {str(e)}")
            
            # Add section with subsections
            sections.append({
                'id': idx,
                'title': section_title,
                'folder': section_folder,
                'selected': False,
                'expanded': False,  # Start collapsed
                'subsections': subsections,
                'content': section_content
            })
            
    except Exception as e:
        logger.exception(f"Error building sections from folders: {str(e)}")
        
    return sections

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_default_data_sections(request, user_id=None):
    """API endpoint to get sections from default data for a specific user"""
    try:
        # Load default data
        response = load_default_data(request)
        if response.status_code != 200:
            return response
            
        # Parse JSON content
        data = json.loads(response.content)
        
        # Return just the sections part
        return JsonResponse({
            "success": True,
            "sections": data.get("sections", []),
            "task_id": data.get("task_id", "default_task"),
            "framework_name": data.get("framework_name", "PCI DSS 2"),
            "total_sections": data.get("total_sections", 0)
        })
        
    except Exception as e:
        logger.exception(f"Error getting default data sections: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_policies_for_section(request, section_folder):
    """API endpoint to get policies for a specific section"""
    try:
        temp_media_root = get_temp_media_root()
        policies_file = os.path.join(temp_media_root, 'policies_PCI_DSS_2', 'all_policies.json')
        
        if not os.path.exists(policies_file):
            return JsonResponse({"success": False, "error": "Policies file not found"}, status=404)
        
        with open(policies_file, 'r') as f:
            all_policies = json.load(f)
        
        # Filter policies for the specific section
        section_policies = []
        for policy_data in all_policies:
            section_info = policy_data.get('section_info', {})
            if section_info.get('folder_path') == section_folder:
                # Extract policy details without subpolicies initially
                analysis = policy_data.get('analysis', {})
                policies = analysis.get('policies', [])
                
                for policy in policies:
                    policy_details = {
                        'policy_id': policy.get('policy_id'),
                        'policy_title': policy.get('policy_title'),
                        'policy_description': policy.get('policy_description'),
                        'policy_text': policy.get('policy_text'),
                        'scope': policy.get('scope'),
                        'objective': policy.get('objective'),
                        'policy_type': policy.get('policy_type'),
                        'policy_category': policy.get('policy_category'),
                        'policy_subcategory': policy.get('policy_subcategory'),
                        'subpolicies_count': len(policy.get('subpolicies', [])),
                        'subpolicies': []  # Initially empty, will be loaded on demand
                    }
                    section_policies.append(policy_details)
        
        return JsonResponse({
            "success": True,
            "section_folder": section_folder,
            "policies": section_policies,
            "total_policies": len(section_policies)
        })
        
    except Exception as e:
        logger.exception(f"Error getting policies for section {section_folder}: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_subpolicies_for_policy(request, section_folder, policy_id):
    """API endpoint to get subpolicies for a specific policy"""
    try:
        temp_media_root = get_temp_media_root()
        policies_file = os.path.join(temp_media_root, 'policies_PCI_DSS_2', 'all_policies.json')
        
        if not os.path.exists(policies_file):
            return JsonResponse({"success": False, "error": "Policies file not found"}, status=404)
        
        with open(policies_file, 'r') as f:
            all_policies = json.load(f)
        
        # Find the specific policy and return its subpolicies
        for policy_data in all_policies:
            section_info = policy_data.get('section_info', {})
            if section_info.get('folder_path') == section_folder:
                analysis = policy_data.get('analysis', {})
                policies = analysis.get('policies', [])
                
                for policy in policies:
                    if policy.get('policy_id') == policy_id:
                        subpolicies = policy.get('subpolicies', [])
                        
                        # Format subpolicies for display
                        formatted_subpolicies = []
                        for subpolicy in subpolicies:
                            formatted_subpolicies.append({
                                'subpolicy_id': subpolicy.get('subpolicy_id'),
                                'subpolicy_title': subpolicy.get('subpolicy_title'),
                                'subpolicy_description': subpolicy.get('subpolicy_description'),
                                'subpolicy_text': subpolicy.get('subpolicy_text'),
                                'control': subpolicy.get('control')
                            })
                        
                        return JsonResponse({
                            "success": True,
                            "section_folder": section_folder,
                            "policy_id": policy_id,
                            "subpolicies": formatted_subpolicies,
                            "total_subpolicies": len(formatted_subpolicies)
                        })
        
        return JsonResponse({"success": False, "error": "Policy not found"}, status=404)
        
    except Exception as e:
        logger.exception(f"Error getting subpolicies for policy {policy_id}: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_default_pdf_content(request, section_folder, control_id):
    """API endpoint to get PDF content for a specific section and control"""
    try:
        from django.http import FileResponse
        
        temp_media_root = get_temp_media_root()
        pdf_path = os.path.join(temp_media_root, 'sections_PCI_DSS_2', 'sections', section_folder, f"{control_id}.pdf")
        
        logger.info(f"Attempting to serve PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return JsonResponse({"success": False, "error": f"PDF file not found: {pdf_path}"}, status=404)
        
        # Serve the PDF file
        try:
            pdf_file = open(pdf_path, 'rb')
            response = FileResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{control_id}.pdf"'
            logger.info(f"Successfully serving PDF: {pdf_path}")
            return response
        except Exception as e:
            logger.exception(f"Error opening PDF file: {str(e)}")
            return JsonResponse({"success": False, "error": f"Error opening PDF file: {str(e)}"}, status=500)
        
    except Exception as e:
        logger.exception(f"Error getting default PDF content: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
