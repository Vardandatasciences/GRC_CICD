import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from django.conf import settings
from django.http import HttpRequest, JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_media_root() -> Path:
    """Get the media root path from Django settings or use a default."""
    try:
        from django.conf import settings
        if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT and settings.MEDIA_ROOT != '.':
            media_root = Path(settings.MEDIA_ROOT)
            logger.info(f"✓ Using MEDIA_ROOT from settings: {media_root}")
            return media_root.resolve()
    except (ImportError, AttributeError) as e:
        logger.warning(f"Error getting MEDIA_ROOT from settings: {str(e)}")
    
    # Default fallback: backend/MEDIA_ROOT
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    media_root = base_dir / "MEDIA_ROOT"
    logger.info(f"✓ Using default MEDIA_ROOT: {media_root}")
    
    if not media_root.exists():
        logger.error(f"✗ MEDIA_ROOT does not exist: {media_root}")
        # List what's in the base directory
        try:
            items = [item.name for item in base_dir.iterdir() if item.name.startswith('MEDIA')]
            logger.info(f"Available MEDIA folders in {base_dir}: {items}")
        except:
            pass
    
    return media_root.resolve()

def get_upload_folder(user_id: str) -> Path:
    """Get the upload folder path for a specific user."""
    media_root = get_media_root()
    upload_folder = media_root / f"upload_{user_id}"
    
    if not upload_folder.exists():
        logger.warning(f"Upload folder for user {user_id} does not exist: {upload_folder}")
        return None
    
    logger.info(f"Found upload folder for user {user_id}: {upload_folder}")
    return upload_folder

def get_sections_folder(user_id: str) -> Optional[Path]:
    """Get the sections folder path for a specific user."""
    upload_folder = get_upload_folder(user_id)
    if not upload_folder:
        return None
    
    sections_folder = None
    
    # DYNAMIC: Find ANY folder starting with "sections_"
    try:
        for item in upload_folder.iterdir():
            if item.is_dir() and item.name.startswith('sections_'):
                # Check if there's a "sections" subfolder inside
                sections_subfolder = item / "sections"
                if sections_subfolder.exists() and sections_subfolder.is_dir():
                    sections_folder = sections_subfolder
                    logger.info(f"✓ Found sections subfolder: {sections_folder}")
                    break
                else:
                    # Use the main folder if no subfolder
                    sections_folder = item
                    logger.info(f"✓ Found sections folder: {sections_folder}")
                    break
    except Exception as e:
        logger.error(f"Error searching for sections folder: {str(e)}")
    
    if not sections_folder:
        logger.error(f"✗ No sections folder found in {upload_folder}")
        # List what's actually there
        try:
            items = [item.name for item in upload_folder.iterdir()]
            logger.error(f"Available items: {items}")
        except:
            pass
        return None
    
    return sections_folder

def get_policies_folder(user_id: str) -> Optional[Path]:
    """Get the policies folder path for a specific user."""
    upload_folder = get_upload_folder(user_id)
    if not upload_folder:
        return None
    
    policies_folder = None
    
    # DYNAMIC: Find ANY folder starting with "policies_"
    try:
        for item in upload_folder.iterdir():
            if item.is_dir() and item.name.startswith('policies_'):
                policies_folder = item
                logger.info(f"✓ Found policies folder: {policies_folder}")
                break
    except Exception as e:
        logger.error(f"Error searching for policies folder: {str(e)}")
    
    if not policies_folder:
        logger.error(f"✗ No policies folder found in {upload_folder}")
        return None
    
    return policies_folder

def get_all_policies_json(user_id: str) -> Optional[Dict]:
    """Get the all_policies.json content for a specific user."""
    policies_folder = get_policies_folder(user_id)
    if not policies_folder:
        return None
    
    policies_json_path = policies_folder / "all_policies.json"
    
    if not policies_json_path.exists():
        logger.warning(f"all_policies.json not found in {policies_folder}")
        return None
    
    try:
        with open(policies_json_path, 'r', encoding='utf-8') as f:
            policies_data = json.load(f)
            logger.info(f"Successfully loaded all_policies.json for user {user_id}")
            return policies_data
    except Exception as e:
        logger.error(f"Error loading all_policies.json: {str(e)}")
        return None

def get_sections_index_json(user_id: str) -> Optional[Dict]:
    """Get the sections_index.json content for a specific user."""
    upload_folder = get_upload_folder(user_id)
    if not upload_folder:
        return None
    
    sections_index_path = None
    
    # DYNAMIC: Find sections_index.json in ANY folder starting with "sections_"
    try:
        for item in upload_folder.iterdir():
            if item.is_dir() and item.name.startswith('sections_'):
                potential_index = item / "sections_index.json"
                if potential_index.exists():
                    sections_index_path = potential_index
                    logger.info(f"✓ Found sections_index.json: {sections_index_path}")
                    break
    except Exception as e:
        logger.error(f"Error searching for sections_index.json: {str(e)}")
    
    if not sections_index_path:
        logger.warning(f"No sections_index.json file found in {upload_folder}")
        return None
    
    try:
        with open(sections_index_path, 'r', encoding='utf-8') as f:
            sections_index_data = json.load(f)
            logger.info(f"✓ Successfully loaded sections_index.json for user {user_id}")
            return sections_index_data
    except Exception as e:
        logger.error(f"Error loading sections_index.json: {str(e)}")
        return None

def get_pdf_index_json(user_id: str) -> Optional[Dict]:
    """Get the PDF index JSON content for a specific user."""
    upload_folder = get_upload_folder(user_id)
    if not upload_folder:
        return None
    
    index_json_path = None
    
    # DYNAMIC: Find ANY file ending with "_index.json"
    try:
        for item in upload_folder.iterdir():
            if item.is_file() and item.name.endswith('_index.json'):
                index_json_path = item
                logger.info(f"✓ Found index JSON file: {index_json_path}")
                break
    except Exception as e:
        logger.error(f"Error searching for index JSON: {str(e)}")
    
    if not index_json_path:
        logger.warning(f"No index JSON file found in {upload_folder}")
        return None
    
    try:
        with open(index_json_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            logger.info(f"✓ Successfully loaded index JSON for user {user_id}")
            return index_data
    except Exception as e:
        logger.error(f"Error loading index JSON: {str(e)}")
        return None

def get_sort_key(folder_name):
    """Extract numeric prefix for sorting folders in natural order."""
    if '-' in folder_name:
        prefix = folder_name.split('-')[0]
        try:
            return int(prefix)  # Convert to integer for proper numeric sorting
        except ValueError:
            return 999  # Put non-numeric folders at the end
    return 999

def build_sections_from_folders(sections_dir: Path) -> List[Dict]:
    """Build section information from folder structure."""
    logger.info(f"Building sections from folders in {sections_dir}")
    
    if not sections_dir or not sections_dir.exists():
        logger.warning(f"Sections directory does not exist: {sections_dir}")
        return []
    
    sections = []
    
    try:
        # Get all directories in the sections folder
        all_folders = [f.name for f in sections_dir.iterdir() if f.is_dir()]
        section_folders = sorted(all_folders, key=get_sort_key)
        
        logger.info(f"Found {len(section_folders)} section folders")
        
        for idx, folder_name in enumerate(section_folders):
            folder_path = sections_dir / folder_name
            
            # Get section title from folder name
            section_title = folder_name.split('-', 1)[-1].replace('_', ' ') if '-' in folder_name else folder_name.replace('_', ' ')
            
            # Try to get content.json for better title
            content_json_path = folder_path / "content.json"
            if content_json_path.exists():
                try:
                    with open(content_json_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_data = json.load(f)
                        if isinstance(content_data, dict):
                            section_title = content_data.get('name', content_data.get('title', section_title))
                except Exception as e:
                    logger.warning(f"Error reading content.json for {folder_name}: {str(e)}")
            
            section = {
                'id': idx,
                'section_id': f"section_{idx}",
                'title': section_title,
                'folder': folder_name,
                'content': '',
                'selected': False,
                'expanded': False,
                'policies': [],  # Will be populated later
                'total_policies': 0,
                'total_subpolicies': 0
            }
            
            sections.append(section)
            logger.debug(f"Added section: {section_title}")
    
    except Exception as e:
        logger.error(f"Error building sections from folders: {str(e)}")
    
    logger.info(f"✓ Built {len(sections)} sections from folders")
    return sections

def build_sections_from_index(index_data: Dict) -> List[Dict]:
    """Build section information from sections_index.json with sections_written format."""
    logger.info("Building sections from index JSON data")
    
    if not index_data:
        logger.warning("No index data provided")
        return []
    
    sections = []
    
    try:
        # Check for 'sections_written' key (new format from sections_index.json)
        if 'sections_written' in index_data:
            sections_list = index_data['sections_written']
            
            if not isinstance(sections_list, list):
                logger.warning(f"sections_written is not a list: {type(sections_list)}")
                return []
            
            logger.info(f"Found {len(sections_list)} sections in sections_written")
            
            # Build sections, filtering for level 1 only (top-level sections)
            idx = 0
            for section_entry in sections_list:
                if not isinstance(section_entry, dict):
                    continue
                
                # Only include level 1 sections as main sections
                if section_entry.get('level', 1) != 1:
                    logger.debug(f"Skipping level {section_entry.get('level')} section: {section_entry.get('title')}")
                    continue
                
                section_title = section_entry.get('title', 'Unnamed Section')
                section_folder = section_entry.get('folder', '')
                
                if not section_folder:
                    logger.warning(f"Section has no folder: {section_title}")
                    continue
                
                section_data = {
                    'id': idx,
                    'section_id': f"section_{idx}",
                    'title': section_title,
                    'folder': section_folder,
                    'content': '',
                    'selected': False,
                    'expanded': False,
                    'policies': [],  # Will be populated later
                    'total_policies': 0,
                    'total_subpolicies': 0
                }
                
                sections.append(section_data)
                idx += 1
                logger.debug(f"Added section: {section_title} (folder: {section_folder})")
        else:
            logger.warning("Index data does not contain 'sections_written' key")
            return []
    
    except Exception as e:
        logger.exception(f"Error building sections from index: {str(e)}")
    
    logger.info(f"✓ Built {len(sections)} sections from index")
    return sections

def _get_policies_for_section_internal(policies_data: List[Dict], section_folder: str) -> List[Dict]:
    """Get policies for a specific section from policies data."""
    logger.info(f"[MATCH] Looking for policies in section: '{section_folder}'")
    
    if not policies_data or not isinstance(policies_data, list):
        logger.warning("No policies data provided or invalid format")
        return []
    
    policies = []
    
    try:
        # Normalize section folder for comparison
        section_folder_normalized = section_folder.replace('\\', '/').strip('/').lower()
        
        # Find policies for this section
        for policy_entry in policies_data:
            if not isinstance(policy_entry, dict):
                continue
                
            section_info = policy_entry.get('section_info', {})
            if not isinstance(section_info, dict):
                continue
                
            entry_folder = section_info.get('folder_path', '')
            entry_folder_normalized = entry_folder.replace('\\', '/').strip('/').lower()
            
            # Match: exact match OR entry is a child of section
            is_match = (
                entry_folder_normalized == section_folder_normalized or
                entry_folder_normalized.startswith(section_folder_normalized + '/')
            )
            
            if is_match:
                logger.info(f"[MATCH] ✓ Found match: '{entry_folder}' matches '{section_folder}'")
                
                analysis = policy_entry.get('analysis', {})
                if not isinstance(analysis, dict):
                    continue
                    
                entry_policies = analysis.get('policies', [])
                if not isinstance(entry_policies, list):
                    continue
                
                # Add each policy with ALL details
                for policy in entry_policies:
                    if not isinstance(policy, dict):
                        continue
                        
                    policy_id = policy.get('policy_id', '')
                    policy_title = policy.get('policy_title', 'Unnamed Policy')
                    policy_description = policy.get('policy_description', '')
                    policy_text = policy.get('policy_text', '')
                    scope = policy.get('scope', '')
                    objective = policy.get('objective', '')
                    policy_type = policy.get('policy_type', '')
                    policy_category = policy.get('policy_category', '')
                    policy_subcategory = policy.get('policy_subcategory', '')
                    
                    # Get subpolicies with all their details
                    subpolicies_raw = policy.get('subpolicies', [])
                    if not isinstance(subpolicies_raw, list):
                        subpolicies_raw = []
                    
                    # Format subpolicies properly
                    subpolicies = []
                    for subpolicy in subpolicies_raw:
                        if isinstance(subpolicy, dict):
                            formatted_subpolicy = {
                                'subpolicy_id': subpolicy.get('subpolicy_id', ''),
                                'subpolicy_title': subpolicy.get('subpolicy_title', ''),
                                'subpolicy_description': subpolicy.get('subpolicy_description', ''),
                                'subpolicy_text': subpolicy.get('subpolicy_text', ''),
                                'control': subpolicy.get('control', ''),
                                'selected': False
                            }
                            subpolicies.append(formatted_subpolicy)
                    
                    policy_data = {
                        'policy_id': policy_id,
                        'policy_title': policy_title,
                        'policy_description': policy_description,
                        'policy_text': policy_text,
                        'scope': scope,
                        'objective': objective,
                        'policy_type': policy_type,
                        'policy_category': policy_category,
                        'policy_subcategory': policy_subcategory,
                        'selected': False,
                        'expanded': False,
                        'subpolicies': subpolicies
                    }
                    
                    policies.append(policy_data)
                    logger.info(f"[MATCH] ✓ Added policy: '{policy_title}' with {len(subpolicies)} subpolicies")
    
    except Exception as e:
        logger.error(f"Error getting policies for section {section_folder}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    logger.info(f"[MATCH] ✓ FINAL: Found {len(policies)} total policies for section '{section_folder}'")
    return policies

def build_complete_structure(user_id: str) -> List[Dict]:
    """Build complete structure of sections and policies for a user."""
    logger.info(f"=" * 80)
    logger.info(f"[BUILD] Building complete structure for user {user_id}")
    logger.info(f"=" * 80)
    
    # Get sections folder and policies data
    sections_folder = get_sections_folder(user_id)
    policies_data = get_all_policies_json(user_id)
    
    # Try to get sections_index.json first (most reliable), then PDF index
    sections_index_data = get_sections_index_json(user_id)
    pdf_index_data = get_pdf_index_json(user_id)
    
    # Try to build sections from sections_index.json first
    sections = []
    if sections_index_data:
        logger.info("[BUILD] Building sections from sections_index.json")
        sections = build_sections_from_index(sections_index_data)
    
    # Fall back to PDF index if no sections from sections_index
    if not sections and pdf_index_data:
        logger.info("[BUILD] Building sections from PDF index")
        sections = build_sections_from_index(pdf_index_data)
    
    # If still no sections, try building from folders
    if not sections and sections_folder:
        logger.info("[BUILD] Building sections from folder structure")
        sections = build_sections_from_folders(sections_folder)
    
    if not sections:
        logger.error("[BUILD] ✗ No sections found!")
        return []
    
    logger.info(f"[BUILD] ✓ Built {len(sections)} sections")
    
    # If we have policies data, populate the policies for each section
    if policies_data:
        logger.info(f"[BUILD] Populating policies from {len(policies_data)} policy entries")
        
        for idx, section in enumerate(sections):
            section_folder = section.get('folder', '')
            section_title = section.get('title', '')
            
            logger.info(f"[BUILD] Section {idx+1}/{len(sections)}: '{section_title}' (folder: {section_folder})")
            
            section_policies = _get_policies_for_section_internal(policies_data, section_folder)
            section['policies'] = section_policies
            
            # Count total policies and subpolicies
            total_policies = len(section_policies)
            total_subpolicies = sum(len(policy.get('subpolicies', [])) for policy in section_policies)
            
            section['total_policies'] = total_policies
            section['total_subpolicies'] = total_subpolicies
            
            logger.info(f"[BUILD] ✓ '{section_title}': {total_policies} policies, {total_subpolicies} subpolicies")
    else:
        logger.error("[BUILD] ✗ No policies data available!")
    
    logger.info(f"=" * 80)
    logger.info(f"[BUILD] ✓ Complete structure built with {len(sections)} sections")
    logger.info(f"=" * 80)
    return sections

def get_pdf_path_for_section(user_id: str, section_folder: str, control_id: str = None) -> Optional[Path]:
    """Get the PDF path for a specific section."""
    sections_folder = get_sections_folder(user_id)
    if not sections_folder:
        return None
    
    # Try to find the section folder
    section_path = sections_folder / section_folder
    if not section_path.exists():
        logger.warning(f"Section folder does not exist: {section_path}")
        return None
    
    # If control_id is provided, look for a specific PDF
    if control_id:
        pdf_path = section_path / f"{control_id}.pdf"
        if pdf_path.exists():
            logger.info(f"Found PDF for control {control_id}: {pdf_path}")
            return pdf_path
    
    # Otherwise, look for any PDF in the section folder
    for file_path in section_path.iterdir():
        if file_path.suffix.lower() == '.pdf':
            logger.info(f"Found PDF in section folder: {file_path}")
            return file_path
    
    logger.warning(f"No PDF found in section folder: {section_path}")
    return None

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_uploaded_data_sections(request, user_id):
    """API endpoint to get sections from uploaded data for a specific user."""
    logger.info(f"API: Getting uploaded data sections for user {user_id}")
    
    try:
        sections = build_complete_structure(user_id)
        
        if not sections:
            return JsonResponse({
                'success': False,
                'error': f'No data found for user {user_id}'
            }, status=404)
        
        # Count total policies and subpolicies
        total_policies = 0
        total_subpolicies = 0
        for section in sections:
            total_policies += len(section.get('policies', []))
            for policy in section.get('policies', []):
                total_subpolicies += len(policy.get('subpolicies', []))
        
        # Get framework name from upload folder (try to extract from PDF name)
        upload_folder = get_upload_folder(user_id)
        framework_name = "Uploaded Framework"
        if upload_folder:
            # Try to find PDF file name
            for item in upload_folder.iterdir():
                if item.is_file() and item.suffix.lower() == '.pdf':
                    framework_name = item.stem  # Get filename without extension
                    break
        
        logger.info(f"API: ✓ Returning {len(sections)} sections, {total_policies} policies, {total_subpolicies} subpolicies")
        
        return JsonResponse({
            'success': True,
            'task_id': f"upload_{user_id}",
            'framework_name': framework_name,
            'sections': sections,
            'total_sections': len(sections),
            'total_policies': total_policies,
            'total_subpolicies': total_subpolicies,
            'source': f'upload_{user_id}'
        })
    except Exception as e:
        logger.exception(f"Error getting uploaded data sections: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_uploaded_pdf_content(request, user_id, section_folder, control_id=None):
    """API endpoint to get PDF content for a specific section."""
    logger.info(f"Getting PDF content for user {user_id}, section {section_folder}, control {control_id}")
    
    try:
        pdf_path = get_pdf_path_for_section(user_id, section_folder, control_id)
        if not pdf_path:
            return JsonResponse({'error': 'PDF not found'}, status=404)
        
        return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
    except Exception as e:
        logger.error(f"Error getting PDF content: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_uploaded_policies_for_section(request, user_id, section_folder):
    """API endpoint to get policies for a specific section."""
    logger.info(f"Getting policies for user {user_id}, section {section_folder}")
    
    try:
        policies_data = get_all_policies_json(user_id)
        if not policies_data:
            return JsonResponse({'error': 'Policies data not found'}, status=404)
        
        policies = _get_policies_for_section_internal(policies_data, section_folder)
        return JsonResponse({'policies': policies})
    except Exception as e:
        logger.error(f"Error getting policies for section: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_uploaded_subpolicies_for_policy(request, user_id, section_folder, policy_id):
    """API endpoint to get subpolicies for a specific policy."""
    logger.info(f"Getting subpolicies for user {user_id}, section {section_folder}, policy {policy_id}")
    
    try:
        policies_data = get_all_policies_json(user_id)
        if not policies_data:
            return JsonResponse({'error': 'Policies data not found'}, status=404)
        
        policies = _get_policies_for_section_internal(policies_data, section_folder)
        
        # Find the specific policy
        policy = next((p for p in policies if p.get('policy_id') == policy_id), None)
        if not policy:
            return JsonResponse({'error': 'Policy not found'}, status=404)
        
        subpolicies = policy.get('subpolicies', [])
        return JsonResponse({'subpolicies': subpolicies})
    except Exception as e:
        logger.error(f"Error getting subpolicies for policy: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def list_uploaded_folders(request):
    """API endpoint to list all user upload folders."""
    logger.info("Listing all user upload folders")
    
    try:
        media_root = get_media_root()
        upload_folders = []
        
        for item in media_root.iterdir():
            if item.is_dir() and item.name.startswith('upload_'):
                user_id = item.name.replace('upload_', '')
                upload_folders.append({
                    'user_id': user_id,
                    'folder_name': item.name,
                    'created_at': item.stat().st_ctime
                })
        
        # Sort by creation time, newest first
        upload_folders.sort(key=lambda x: x['created_at'], reverse=True)
        
        return JsonResponse({'folders': upload_folders})
    except Exception as e:
        logger.error(f"Error listing upload folders: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
