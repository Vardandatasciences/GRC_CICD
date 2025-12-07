import os
import shutil
import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from werkzeug.utils import secure_filename
import logging
from django.http import FileResponse
from django.http import Http404
import glob

# Import the policy extractor
from .json_Policy_extractor import extract_policy_from_pdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CheckedSectionsManager:
    def __init__(self, base_media_path=None):
        self.base_media_path = base_media_path or settings.MEDIA_ROOT
    
    def create_checked_sections_folder(self, user_id, task_id=None):
        """
        Create the checked_sections folder inside the user's upload folder
        """
        try:
            # Determine the user folder path
            if task_id and task_id.startswith('default_'):
                # For default data, use user_id = 1
                user_folder = f"upload_1"
            else:
                user_folder = f"upload_{user_id}"
            
            # Create the checked_sections folder path
            checked_sections_path = os.path.join(
                self.base_media_path, 
                user_folder, 
                "checked_sections"
            )
            
            # Create the folder if it doesn't exist
            if not os.path.exists(checked_sections_path):
                os.makedirs(checked_sections_path, exist_ok=True)
                logger.info(f"Created checked_sections folder: {checked_sections_path}")
            
            return checked_sections_path
            
        except Exception as e:
            logger.error(f"Error creating checked_sections folder: {str(e)}")
            raise
    
    def copy_selected_sections(self, user_id, task_id, selected_sections):
        """
        Copy only selected subsections/controls to the checked_sections folder
        """
        try:
            # Create the checked_sections folder
            checked_sections_path = self.create_checked_sections_folder(user_id, task_id)
            
            # Determine the source folder path
            if task_id and task_id.startswith('default_'):
                # For default data, use the main_default folder
                source_base_path = os.path.join(self.base_media_path, "main_default")
                user_folder = "upload_1"
            else:
                # For normal uploads, use the user's upload folder
                source_base_path = os.path.join(self.base_media_path, f"upload_{user_id}")
                user_folder = f"upload_{user_id}"
            
            copied_sections = []
            failed_sections = []
            
            for section_data in selected_sections:
                try:
                    section_name = section_data.get('name')
                    subsections = section_data.get('subsections', [])
                    
                    if not section_name:
                        logger.warning("Section name is missing, skipping...")
                        continue
                    
                    if not subsections:
                        logger.warning(f"No subsections selected for section: {section_name}")
                        continue
                    
                    # Create section folder in checked_sections
                    section_folder_name = secure_filename(section_name)
                    section_checked_path = os.path.join(checked_sections_path, section_folder_name)
                    os.makedirs(section_checked_path, exist_ok=True)
                    
                    # Find the source section folder
                    source_section_path = self._find_source_section_folder(source_base_path, section_name)
                    
                    if not source_section_path:
                        logger.warning(f"Source section folder not found for: {section_name}")
                        failed_sections.append({
                            'section': section_name,
                            'reason': 'Source folder not found'
                        })
                        continue
                    
                    # Copy only the selected subsections/controls
                    copied_controls = self._copy_selected_controls(source_section_path, section_checked_path, subsections)
                    
                    if not copied_controls:
                        logger.warning(f"No controls were copied for section: {section_name}")
                        failed_sections.append({
                            'section': section_name,
                            'reason': 'No controls found or copied'
                        })
                        continue
                    
                    # Create a metadata file with selection information
                    metadata = {
                        'section_name': section_name,
                        'selected_subsections': subsections,
                        'copied_controls': copied_controls,
                        'copied_at': datetime.now().isoformat(),
                        'user_id': user_id,
                        'task_id': task_id,
                        'source_path': source_section_path,
                        'destination_path': section_checked_path
                    }
                    
                    metadata_file = os.path.join(section_checked_path, 'selection_metadata.json')
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    copied_sections.append({
                        'section_name': section_name,
                        'destination_path': section_checked_path,
                        'subsections_count': len(subsections),
                        'copied_controls_count': len(copied_controls)
                    })
                    
                    logger.info(f"Successfully copied {len(copied_controls)} controls for section: {section_name}")
                    
                except Exception as e:
                    logger.error(f"Error copying section {section_data.get('name', 'Unknown')}: {str(e)}")
                    failed_sections.append({
                        'section': section_data.get('name', 'Unknown'),
                        'reason': str(e)
                    })
            
            # Create a summary file
            summary = {
                'user_id': user_id,
                'task_id': task_id,
                'copied_at': datetime.now().isoformat(),
                'total_sections': len(selected_sections),
                'successful_copies': len(copied_sections),
                'failed_copies': len(failed_sections),
                'copied_sections': copied_sections,
                'failed_sections': failed_sections
            }
            
            summary_file = os.path.join(checked_sections_path, 'copy_summary.json')
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            return {
                'success': True,
                'checked_sections_path': checked_sections_path,
                'copied_sections': copied_sections,
                'failed_sections': failed_sections,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error in copy_selected_sections: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_section_folder(self, folder_path, section_name):
        """
        Check if a folder contains content for the given section
        """
        try:
            # Look for common files that indicate this is the right section
            section_files = ['section_content.txt', 'section_info.json', 'controls']
            
            for file_name in section_files:
                file_path = os.path.join(folder_path, file_name)
                if os.path.exists(file_path):
                    return True
            
            # Also check if the folder name matches the section name
            folder_name = os.path.basename(folder_path)
            if section_name.lower() in folder_name.lower():
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking section folder: {str(e)}")
            return False
    
    def _copy_selected_controls(self, source_section_path, destination_section_path, selected_subsections):
        """
        Copy only the selected subsections/controls from the source to the destination.
        """
        copied_controls = []
        try:
            # Look for the extracted_controls directory in the source section
            extracted_controls_path = os.path.join(source_section_path, "extracted_controls")
            
            if not os.path.exists(extracted_controls_path):
                logger.warning(f"Extracted controls directory not found: {extracted_controls_path}")
                return []
            
            # Copy each selected subsection/control
            for subsection in selected_subsections:
                control_id = subsection.get('control_id')
                if not control_id:
                    logger.warning(f"No control_id found for subsection: {subsection.get('name', 'Unknown')}")
                    continue
                
                # Look for the control folder in extracted_controls with exact matching
                control_folder_name = None
                for folder in os.listdir(extracted_controls_path):
                    # Use exact matching to avoid partial matches
                    # Look for folders that start with the control_id followed by underscore or dash
                    if folder.startswith(f"{control_id}_") or folder.startswith(f"{control_id}-"):
                        control_folder_name = folder
                        break
                    # Also check for exact control_id match
                    elif folder == control_id:
                        control_folder_name = folder
                        break
                
                if not control_folder_name:
                    logger.warning(f"Control folder not found for {control_id}")
                    continue
                
                source_control_path = os.path.join(extracted_controls_path, control_folder_name)
                destination_control_path = os.path.join(destination_section_path, control_folder_name)
                
                if os.path.exists(source_control_path):
                    # Copy the entire control folder
                    shutil.copytree(source_control_path, destination_control_path, dirs_exist_ok=True)
                    copied_controls.append({
                        'control_id': control_id,
                        'name': subsection.get('name', control_id),
                        'source_path': source_control_path,
                        'destination_path': destination_control_path
                    })
                    logger.info(f"Copied control: {control_id} ({control_folder_name})")
                else:
                    logger.warning(f"Source control path not found: {source_control_path}")
            
            return copied_controls
            
        except Exception as e:
            logger.error(f"Error copying selected controls: {str(e)}")
            return []
    
    def _find_source_section_folder(self, source_base_path, section_name):
        """
        Find the source section folder with improved matching logic
        """
        try:
            # First, try to find in extracted_sections/sections folder
            extracted_sections_path = os.path.join(source_base_path, "extracted_sections", "sections")
            
            if os.path.exists(extracted_sections_path):
                # Look for the section folder with multiple matching strategies
                for folder in os.listdir(extracted_sections_path):
                    folder_path = os.path.join(extracted_sections_path, folder)
                    if os.path.isdir(folder_path):
                        # Strategy 1: Exact folder name match (highest priority)
                        if folder.lower() == section_name.lower():
                            logger.info(f"Found exact folder match: {folder}")
                            return folder_path
                        
                        # Strategy 2: Convert section name to folder name format and match
                        # Convert "3.1 ACCESS CONTROL" to "3_1_ACCESS_CONTROL"
                        normalized_section_name = self._normalize_section_name(section_name)
                        if normalized_section_name in folder:
                            logger.info(f"Found normalized folder match: {folder}")
                            return folder_path
                        
                        # Strategy 3: Extract section number and match (highest priority for numbered sections)
                        # Extract "3.1" from "3.1 ACCESS CONTROL" and look for "015-3_1_ACCESS_CONTROL"
                        section_number = self._extract_section_number(section_name)
                        if section_number and section_number in folder:
                            logger.info(f"Found section number match: {folder}")
                            return folder_path
                        
                        # Strategy 3.5: Check if folder name contains the exact section number pattern
                        # Look for folders like "015-3_1_ACCESS_CONTROL" that contain "3_1"
                        if section_number:
                            normalized_number = section_number.replace('.', '_')
                            if normalized_number in folder:
                                logger.info(f"Found normalized section number match: {folder}")
                                return folder_path
                        
                        # Strategy 4: Folder name contains section name (lower priority)
                        if section_name.lower() in folder.lower():
                            logger.info(f"Found partial folder match: {folder}")
                            return folder_path
                        
                        # Strategy 5: Check if folder contains section content files (lowest priority)
                        # Only check content if the folder name has some relation to the section
                        if self._is_section_folder(folder_path, section_name) and self._folder_name_matches_section(folder, section_name):
                            logger.info(f"Found section folder by content and name: {folder}")
                            return folder_path
            
            # If not found in extracted_sections/sections, try extracted_sections folder
            extracted_sections_path = os.path.join(source_base_path, "extracted_sections")
            if os.path.exists(extracted_sections_path):
                for folder in os.listdir(extracted_sections_path):
                    folder_path = os.path.join(extracted_sections_path, folder)
                    if os.path.isdir(folder_path):
                        # Check if folder name matches section name
                        if section_name.lower() in folder.lower():
                            logger.info(f"Found direct folder match: {folder}")
                            return folder_path
            
            # If not found in extracted_sections, try direct folder matching
            for folder in os.listdir(source_base_path):
                folder_path = os.path.join(source_base_path, folder)
                if os.path.isdir(folder_path):
                    # Check if folder name matches section name
                    if section_name.lower() in folder.lower():
                        logger.info(f"Found direct folder match: {folder}")
                        return folder_path
            
            logger.warning(f"No source folder found for section: {section_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding source section folder: {str(e)}")
            return None
    
    def _extract_section_number(self, section_name):
        """
        Extract section number from section name
        Extract "3.1" from "3.1 ACCESS CONTROL"
        """
        try:
            import re
            # Look for pattern like "3.1", "3.2", etc.
            match = re.search(r'(\d+\.\d+)', section_name)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logger.error(f"Error extracting section number: {str(e)}")
            return None
    
    def _normalize_section_name(self, section_name):
        """
        Normalize section name to match folder naming convention
        Convert "3.1 ACCESS CONTROL" to "3_1_ACCESS_CONTROL"
        """
        try:
            # Remove any leading/trailing whitespace
            normalized = section_name.strip()
            
            # Replace dots with underscores
            normalized = normalized.replace('.', '_')
            
            # Replace spaces with underscores
            normalized = normalized.replace(' ', '_')
            
            # Convert to uppercase to match folder naming
            normalized = normalized.upper()
            
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing section name: {str(e)}")
            return section_name
    
    def _folder_name_matches_section(self, folder_name, section_name):
        """
        Check if folder name has any relation to the section name
        """
        try:
            # Convert both to lowercase for comparison
            folder_lower = folder_name.lower()
            section_lower = section_name.lower()
            
            # Check if folder contains section name
            if section_lower in folder_lower:
                return True
            
            # Check if folder contains section number
            section_number = self._extract_section_number(section_name)
            if section_number:
                normalized_number = section_number.replace('.', '_')
                if normalized_number in folder_lower:
                    return True
            
            # Check if folder contains normalized section name
            normalized_section = self._normalize_section_name(section_name)
            if normalized_section.lower() in folder_lower:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking folder name match: {str(e)}")
            return False
    
    def process_checked_sections_pdfs(self, user_id, task_id=None):
        """
        Step 4: Process PDFs in checked sections folder
        - Read the checked_sections folder
        - Navigate through multiple subfolders
        - Find PDF files in each subfolder
        - Extract content using json_Policy_extractor
        """
        try:
            # Get the checked sections folder path
            checked_sections_path = self.create_checked_sections_folder(user_id, task_id)
            
            if not os.path.exists(checked_sections_path):
                logger.warning(f"Checked sections folder does not exist: {checked_sections_path}")
                return {
                    'success': False,
                    'error': 'Checked sections folder does not exist'
                }
            
            processed_results = []
            failed_extractions = []
            
            # Walk through all subfolders in checked_sections
            for root, dirs, files in os.walk(checked_sections_path):
                # Look for PDF files in each subfolder
                pdf_files = [f for f in files if f.lower().endswith('.pdf')]
                
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(root, pdf_file)
                    relative_path = os.path.relpath(pdf_path, checked_sections_path)
                    
                    try:
                        logger.info(f"Processing PDF: {relative_path}")
                        
                        # Extract content using the policy extractor
                        extracted_content = extract_policy_from_pdf(pdf_path)
                        
                        # Create output filename for extracted content
                        base_name = os.path.splitext(pdf_file)[0]
                        output_file = os.path.join(root, f"{base_name}_extracted.json")
                        
                        # Save extracted content to JSON file
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(extracted_content, f, indent=2, ensure_ascii=False)
                        
                        # Process and restructure the JSON with sub-sections
                        restructured_content = self._restructure_control_text(extracted_content)
                        
                        # Save the restructured content
                        restructured_file = os.path.join(root, f"{base_name}_restructured.json")
                        with open(restructured_file, 'w', encoding='utf-8') as f:
                            json.dump(restructured_content, f, indent=2, ensure_ascii=False)
                        
                        processed_results.append({
                            'pdf_file': pdf_file,
                            'pdf_path': relative_path,
                            'output_file': os.path.relpath(output_file, checked_sections_path),
                            'restructured_file': os.path.relpath(restructured_file, checked_sections_path),
                            'families_count': len(extracted_content.get('families', [])),
                            'total_controls': sum(len(fam.get('controls', [])) for fam in extracted_content.get('families', [])),
                            'extraction_success': True,
                            'restructuring_success': True
                        })
                        
                        logger.info(f"Successfully extracted content from {pdf_file}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting content from {pdf_file}: {str(e)}")
                        failed_extractions.append({
                            'pdf_file': pdf_file,
                            'pdf_path': relative_path,
                            'error': str(e)
                        })
            
            # Create a summary of the processing
            summary = {
                'user_id': user_id,
                'task_id': task_id,
                'processed_at': datetime.now().isoformat(),
                'total_pdfs_found': len(processed_results) + len(failed_extractions),
                'successful_extractions': len(processed_results),
                'failed_extractions': len(failed_extractions),
                'processed_results': processed_results,
                'failed_extractions': failed_extractions
            }
            
            # Save processing summary
            summary_file = os.path.join(checked_sections_path, 'pdf_processing_summary.json')
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            return {
                'success': True,
                'summary': summary,
                'checked_sections_path': checked_sections_path
            }
            
        except Exception as e:
            logger.error(f"Error in process_checked_sections_pdfs: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_checked_sections_info(self, user_id, task_id=None):
        """
        Get information about the checked sections folder
        """
        try:
            checked_sections_path = self.create_checked_sections_folder(user_id, task_id)
            
            if not os.path.exists(checked_sections_path):
                return {
                    'exists': False,
                    'path': checked_sections_path,
                    'sections': []
                }
            
            sections = []
            for item in os.listdir(checked_sections_path):
                item_path = os.path.join(checked_sections_path, item)
                if os.path.isdir(item_path):
                    # Read metadata if available
                    metadata_file = os.path.join(item_path, 'selection_metadata.json')
                    metadata = None
                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                        except Exception as e:
                            logger.error(f"Error reading metadata for {item}: {str(e)}")
                    
                    sections.append({
                        'name': item,
                        'path': item_path,
                        'metadata': metadata,
                        'size': self._get_folder_size(item_path)
                    })
            
            return {
                'exists': True,
                'path': checked_sections_path,
                'sections': sections,
                'total_sections': len(sections)
            }
            
        except Exception as e:
            logger.error(f"Error getting checked sections info: {str(e)}")
            return {
                'exists': False,
                'error': str(e)
            }
    
    def get_extracted_policies_for_form(self, user_id, task_id=None):
        """
        Step 6: Read all restructured JSON files and extract form data
        Returns data for the policy form with id, title, sub_sections, related_controls
        """
        try:
            checked_sections_path = self.create_checked_sections_folder(user_id, task_id)
            
            if not os.path.exists(checked_sections_path):
                return {
                    'success': False,
                    'error': 'Checked sections folder does not exist'
                }
            
            policies_data = []
            
            # Walk through all subfolders in checked_sections
            for root, dirs, files in os.walk(checked_sections_path):
                # Look for restructured JSON files
                restructured_files = [f for f in files if f.endswith('_restructured.json')]
                
                for restructured_file in restructured_files:
                    file_path = os.path.join(root, restructured_file)
                    relative_path = os.path.relpath(file_path, checked_sections_path)
                    
                    try:
                        logger.info(f"Reading restructured file: {relative_path}")
                        
                        # Read the restructured JSON file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                        
                        # Extract policy information
                        policy_info = self._extract_policy_form_data(json_data, relative_path)
                        
                        if policy_info and policy_info.get('policy_name') and policy_info.get('sub_policies'):
                            policies_data.append(policy_info)
                            logger.info(f"Successfully extracted policy data from {restructured_file}")
                        else:
                            logger.warning(f"Invalid policy data extracted from {restructured_file}")
                        
                    except Exception as e:
                        logger.error(f"Error reading restructured file {restructured_file}: {str(e)}")
            
            # Ensure we have at least one policy
            if not policies_data:
                logger.warning("No valid policies found, creating default policy")
                policies_data = [{
                    'file_path': 'default',
                    'policy_name': 'Default Policy',
                    'sub_policies': [{
                        'id': 'default',
                        'title': 'Default Control',
                        'sub_sections': {
                            'main': {
                                'text': 'No policy data available. Please check your uploaded files.',
                                'order': 1
                            }
                        },
                        'related_controls': []
                    }]
                }]
            
            return {
                'success': True,
                'policies': policies_data,
                'total_policies': len(policies_data),
                'checked_sections_path': checked_sections_path
            }
            
        except Exception as e:
            logger.error(f"Error in get_extracted_policies_for_form: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_policy_form_data(self, json_data, file_path):
        """
        Extract form data from restructured JSON
        """
        try:
            policy_data = {
                'file_path': file_path,
                'policy_name': 'Unknown Policy',  # Default fallback
                'sub_policies': []
            }
            
            # Extract policy name from file path (folder name)
            path_parts = file_path.split(os.sep)
            if len(path_parts) >= 2:
                extracted_name = path_parts[0]  # Section folder name
                if extracted_name and extracted_name.strip():
                    policy_data['policy_name'] = extracted_name
                else:
                    # If folder name is empty, try to get from the file name
                    file_name = os.path.basename(file_path)
                    if file_name and file_name.endswith('_restructured.json'):
                        policy_data['policy_name'] = file_name.replace('_restructured.json', '')
                    else:
                        policy_data['policy_name'] = f"Policy_{len(path_parts)}"
            else:
                # If path is too short, use file name
                file_name = os.path.basename(file_path)
                if file_name and file_name.endswith('_restructured.json'):
                    policy_data['policy_name'] = file_name.replace('_restructured.json', '')
                else:
                    policy_data['policy_name'] = 'Unknown Policy'
            
            # Process each family and control
            for family in json_data.get('families', []):
                for control in family.get('controls', []):
                    # Ensure control has required fields
                    control_id = control.get('id', '')
                    control_title = control.get('title', '')
                    
                    # Skip controls without ID
                    if not control_id:
                        logger.warning(f"Skipping control without ID in {file_path}")
                        continue
                    
                    sub_policy = {
                        'id': control_id,
                        'title': control_title or control_id,  # Use ID as fallback for title
                        'sub_sections': {},
                        'related_controls': control.get('related_controls', [])
                    }
                    
                    # Extract sub_sections from control_text
                    control_text = control.get('control_text', {})
                    if isinstance(control_text, dict) and 'sub_sections' in control_text:
                        sub_policy['sub_sections'] = control_text['sub_sections']
                    elif isinstance(control_text, str):
                        # If control_text is still a string, create a single sub-section
                        sub_policy['sub_sections'] = {
                            'main': {
                                'text': control_text,
                                'order': 1
                            }
                        }
                    else:
                        # If control_text is missing or invalid, create empty sub-section
                        sub_policy['sub_sections'] = {
                            'main': {
                                'text': f"Control {control_id}",
                                'order': 1
                            }
                        }
                    
                    policy_data['sub_policies'].append(sub_policy)
            
            # Ensure we have at least one sub-policy
            if not policy_data['sub_policies']:
                logger.warning(f"No valid sub-policies found in {file_path}")
                # Create a default sub-policy
                policy_data['sub_policies'] = [{
                    'id': 'default',
                    'title': 'Default Control',
                    'sub_sections': {
                        'main': {
                            'text': 'No control data available',
                            'order': 1
                        }
                    },
                    'related_controls': []
                }]
            
            logger.info(f"Successfully extracted policy data: {policy_data['policy_name']} with {len(policy_data['sub_policies'])} sub-policies")
            return policy_data
            
        except Exception as e:
            logger.error(f"Error extracting policy form data from {file_path}: {str(e)}")
            # Return a minimal valid structure instead of None
            return {
                'file_path': file_path,
                'policy_name': 'Error Policy',
                'sub_policies': [{
                    'id': 'error',
                    'title': 'Error Control',
                    'sub_sections': {
                        'main': {
                            'text': f'Error processing file: {str(e)}',
                            'order': 1
                        }
                    },
                    'related_controls': []
                }]
            }
    
    def _restructure_control_text(self, extracted_content):
        """
        Restructure control text by breaking it down into sub-sections based on alphabetical points
        """
        try:
            restructured_content = extracted_content.copy()
            
            # Process each family
            for family in restructured_content.get('families', []):
                # Process each control in the family
                for control in family.get('controls', []):
                    control_text = control.get('control_text', '')
                    
                    if control_text:
                        # Break down the control text into sub-sections
                        sub_sections = self._parse_control_text_sections(control_text)
                        
                        # Replace the control_text with structured sub-sections
                        control['control_text'] = {
                            'original_text': control_text,
                            'sub_sections': sub_sections
                        }
            
            return restructured_content
            
        except Exception as e:
            logger.error(f"Error restructuring control text: {str(e)}")
            return extracted_content
    
    def _parse_control_text_sections(self, control_text):
        """
        Parse control text and break it down into sub-sections based on alphabetical points
        """
        try:
            import re
            
            sub_sections = {}
            
            # Split the text by alphabetical points (a., b., c., etc.)
            # First, find all the alphabetical section markers
            section_markers = re.findall(r'\b([a-z])\.\s*', control_text, re.IGNORECASE)
            
            if section_markers:
                # Split the text by these markers
                parts = re.split(r'\b[a-z]\.\s*', control_text, flags=re.IGNORECASE)
                
                # Remove the first empty part if it exists
                if parts and not parts[0].strip():
                    parts = parts[1:]
                
                # Create sub-sections for each part
                for i, (marker, part) in enumerate(zip(section_markers, parts)):
                    cleaned_text = part.strip()
                    if cleaned_text:
                        sub_sections[marker.upper()] = {
                            'text': cleaned_text,
                            'order': i + 1
                        }
            
            # If no alphabetical sections found, try numbered sections
            if not sub_sections:
                numbered_markers = re.findall(r'\b(\d+)\.\s*', control_text)
                
                if numbered_markers:
                    parts = re.split(r'\b\d+\.\s*', control_text)
                    
                    # Remove the first empty part if it exists
                    if parts and not parts[0].strip():
                        parts = parts[1:]
                    
                    for i, (marker, part) in enumerate(zip(numbered_markers, parts)):
                        cleaned_text = part.strip()
                        if cleaned_text:
                            sub_sections[f"section_{marker}"] = {
                                'text': cleaned_text,
                                'order': i + 1
                            }
            
            # If still no sections found, create a single section
            if not sub_sections:
                sub_sections['main'] = {
                    'text': control_text.strip(),
                    'order': 1
                }
            
            return sub_sections
            
        except Exception as e:
            logger.error(f"Error parsing control text sections: {str(e)}")
            return {
                'main': {
                    'text': control_text.strip(),
                    'order': 1
                }
            }
    
    def _get_folder_size(self, folder_path):
        """
        Calculate the size of a folder in bytes
        """
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            logger.error(f"Error calculating folder size: {str(e)}")
            return 0

# Create a global instance
checked_sections_manager = CheckedSectionsManager()

@csrf_exempt
@require_http_methods(["POST"])
def save_selected_sections(request):
    """
    Save selected sections to the checked_sections folder
    """
    try:
        data = json.loads(request.body)
        
        if not data:
            return JsonResponse({
                'success': False,
                'error': 'No data provided'
            }, status=400)
        
        user_id = data.get('user_id')
        task_id = data.get('task_id')
        selected_sections = data.get('selected_sections', [])
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User ID is required'
            }, status=400)
        
        if not selected_sections:
            return JsonResponse({
                'success': False,
                'error': 'No sections selected'
            }, status=400)
        
        logger.info(f"Saving selected sections for user {user_id}, task {task_id}")
        logger.info(f"Selected sections: {len(selected_sections)}")
        
        # Copy the selected sections
        result = checked_sections_manager.copy_selected_sections(
            user_id, 
            task_id, 
            selected_sections
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f"Successfully saved {len(result['copied_sections'])} sections",
                'data': result
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in save_selected_sections endpoint: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def process_checked_sections_pdfs_endpoint(request):
    """
    Step 4: Process PDFs in checked sections folder
    """
    try:
        data = json.loads(request.body)
        
        if not data:
            return JsonResponse({
                'success': False,
                'error': 'No data provided'
            }, status=400)
        
        user_id = data.get('user_id')
        task_id = data.get('task_id')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User ID is required'
            }, status=400)
        
        logger.info(f"Processing PDFs in checked sections for user {user_id}, task {task_id}")
        
        # Process the PDFs in checked sections
        result = checked_sections_manager.process_checked_sections_pdfs(user_id, task_id)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f"Successfully processed {result['summary']['successful_extractions']} PDFs",
                'data': result
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in process_checked_sections_pdfs_endpoint: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_checked_sections(request, user_id):
    """
    Get information about checked sections for a user
    """
    try:
        task_id = request.GET.get('task_id')
        
        logger.info(f"Getting checked sections for user {user_id}, task {task_id}")
        
        result = checked_sections_manager.get_checked_sections_info(user_id, task_id)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error in get_checked_sections endpoint: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_extracted_policies_form_data(request, user_id):
    """
    Step 6: Get extracted policies data for form population
    """
    try:
        task_id = request.GET.get('task_id')
        
        logger.info(f"Getting extracted policies form data for user {user_id}, task {task_id}")
        
        result = checked_sections_manager.get_extracted_policies_for_form(user_id, task_id)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f"Successfully loaded {result['total_policies']} policies",
                'data': result
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }, status=500)
        
    except Exception as e:
        logger.error(f"Error in get_extracted_policies_form_data endpoint: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_checked_sections(request, user_id):
    """
    Delete the checked_sections folder for a user
    """
    try:
        task_id = request.GET.get('task_id')
        
        logger.info(f"Deleting checked sections for user {user_id}, task {task_id}")
        
        checked_sections_path = checked_sections_manager.create_checked_sections_folder(user_id, task_id)
        
        if os.path.exists(checked_sections_path):
            shutil.rmtree(checked_sections_path)
            logger.info(f"Deleted checked_sections folder: {checked_sections_path}")
            
            return JsonResponse({
                'success': True,
                'message': 'Checked sections folder deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Checked sections folder does not exist'
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error in delete_checked_sections endpoint: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def serve_checked_section_pdf(request, user_id, section_folder, control_id):
    """
    Serve PDF files from both checked_sections folder and original upload structure
    """
    try:
        task_id = request.GET.get('task_id')
        
        logger.info(f"Serving PDF for user {user_id}, section {section_folder}, control {control_id}")
        
        # Get the checked sections folder path
        checked_sections_path = checked_sections_manager.create_checked_sections_folder(user_id, task_id)
        
        # Get the original upload path
        upload_base_path = os.path.join(settings.MEDIA_ROOT, f"upload_{user_id}")
        
        # Look for the PDF file in multiple locations
        pdf_path = None
        
        # Strategy 1: Look in checked_sections folder (after Step 3)
        checked_paths = [
            os.path.join(checked_sections_path, section_folder, control_id, f"{control_id}.pdf"),
            os.path.join(checked_sections_path, section_folder, f"{control_id}_*", f"{control_id}.pdf"),
            os.path.join(checked_sections_path, section_folder, f"{control_id}-*", f"{control_id}.pdf")
        ]
        
        for path_pattern in checked_paths:
            if '*' in path_pattern:
                matching_files = glob.glob(path_pattern)
                if matching_files:
                    pdf_path = matching_files[0]
                    break
            elif os.path.exists(path_pattern):
                pdf_path = path_pattern
                break
        
        # Strategy 2: Look in original upload structure (before Step 3)
        if not pdf_path:
            original_paths = [
                # Path: upload_1/extracted_sections/sections/015-3_1_ACCESS_CONTROL/extracted_controls/AC-5_SEPARATION_OF_DUTIES/AC-5_SEPARATION_OF_DUTIES.pdf
                os.path.join(upload_base_path, "extracted_sections", "sections", section_folder, "extracted_controls", control_id, f"{control_id}.pdf"),
                # Alternative: upload_1/extracted_sections/sections/015-3_1_ACCESS_CONTROL/extracted_controls/AC-5_SEPARATION_OF_DUTIES_*/AC-5_SEPARATION_OF_DUTIES.pdf
                os.path.join(upload_base_path, "extracted_sections", "sections", section_folder, "extracted_controls", f"{control_id}_*", f"{control_id}.pdf"),
                # Alternative: upload_1/extracted_sections/sections/015-3_1_ACCESS_CONTROL/extracted_controls/AC-5_SEPARATION_OF_DUTIES-*/AC-5_SEPARATION_OF_DUTIES.pdf
                os.path.join(upload_base_path, "extracted_sections", "sections", section_folder, "extracted_controls", f"{control_id}-*", f"{control_id}.pdf"),
                # Alternative: upload_1/extracted_sections/015-3_1_ACCESS_CONTROL/controls/AC-5_SEPARATION_OF_DUTIES.pdf
                os.path.join(upload_base_path, "extracted_sections", section_folder, "controls", f"{control_id}.pdf"),
                # Alternative: upload_1/015-3_1_ACCESS_CONTROL/AC-5_SEPARATION_OF_DUTIES.pdf
                os.path.join(upload_base_path, section_folder, f"{control_id}.pdf")
            ]
            
            for path_pattern in original_paths:
                if '*' in path_pattern:
                    matching_files = glob.glob(path_pattern)
                    if matching_files:
                        pdf_path = matching_files[0]
                        logger.info(f"Found PDF in original structure: {pdf_path}")
                        break
                elif os.path.exists(path_pattern):
                    pdf_path = path_pattern
                    logger.info(f"Found PDF in original structure: {pdf_path}")
                    break
        
        # Strategy 3: Look for any PDF file with the control_id in the filename
        if not pdf_path:
            # Search recursively in the upload directory for any PDF with the control_id
            search_pattern = os.path.join(upload_base_path, "**", f"*{control_id}*.pdf")
            matching_files = glob.glob(search_pattern, recursive=True)
            if matching_files:
                pdf_path = matching_files[0]
                logger.info(f"Found PDF using recursive search: {pdf_path}")
        
        if pdf_path and os.path.exists(pdf_path):
            logger.info(f"Serving PDF from: {pdf_path}")
            response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
            # Allow iframe embedding for PDF viewing
            response['X-Frame-Options'] = 'SAMEORIGIN'
            response['Content-Disposition'] = 'inline'
            return response
        else:
            logger.warning(f"PDF not found for control {control_id} in section {section_folder}")
            logger.warning(f"Searched in checked_sections: {checked_sections_path}")
            logger.warning(f"Searched in upload_base: {upload_base_path}")
            raise Http404(f"PDF not found for control {control_id}")
            
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error serving PDF for control {control_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
