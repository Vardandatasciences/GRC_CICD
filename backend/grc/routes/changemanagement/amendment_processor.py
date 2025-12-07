"""
Amendment Processor Module

This module orchestrates the complete processing pipeline for downloaded framework amendments:
1. Extract sections from PDF
2. Generate policies and subpolicies using policy_extractor_enhanced.py
3. Generate compliance records using compliance_generator.py
4. Store results in JSON format

Usage:
    from .amendment_processor import process_downloaded_amendment
    
    result = process_downloaded_amendment(
        pdf_path="path/to/amendment.pdf",
        framework_name="NIST SP 800-53",
        framework_id=123
    )
"""

import json
import os
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AmendmentProcessor:
    """Orchestrates the complete amendment processing pipeline."""
    
    def __init__(self, base_dir: str = None, work_dir: str = None):
        """
        Initialize the amendment processor.
        
        Args:
            base_dir: Base directory for processing (default: backend directory)
            work_dir: Specific working directory for all outputs (overrides base_dir/temp_processing)
        """
        from django.conf import settings
        self.base_dir = base_dir or settings.BASE_DIR
        
        if work_dir:
            self.temp_dir = work_dir
        else:
            self.temp_dir = os.path.join(self.base_dir, 'temp_processing')
            
        os.makedirs(self.temp_dir, exist_ok=True)

    def prepare_temp_dir(self):
        """Clear any previous temp_processing data before a new run."""
        import shutil
        import time
        
        # If we are using a specific work_dir that contains other files (like the PDF),
        # we shouldn't just wipe the whole directory blindly.
        # However, per requirement "clear all files and folder before starting",
        # the caller (framework_comparison) already clears the directory.
        # So we might just ensure it exists.
        
        try:
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Unable to ensure temp directory exists: {str(e)}")

    def extract_sections_from_pdf(self, pdf_path: str, framework_name: str) -> Optional[str]:
        """
        Extract sections from PDF using existing PDF extraction logic.
        
        Args:
            pdf_path: Path to the PDF file
            framework_name: Name of the framework
            
        Returns:
            Path to the sections directory or None if failed
        """
        try:
            # Import PDF extraction module
            from ..uploadNist.pdf_extractor import extract_sections_from_pdf as pdf_extract_sections
            import shutil
            import time
            
            # Create output directory for sections
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = framework_name.replace(' ', '_').replace('/', '_')
            sections_dir = os.path.join(self.temp_dir, f"sections_{safe_name}_{timestamp}")
            
            logger.info(f"Extracting sections from PDF: {pdf_path}")
            
            # Extract sections
            result = pdf_extract_sections(
                pdf_path=pdf_path,
                output_dir=sections_dir
            )
            
            # Check if we need fallback (no index items found)
            fallback_required = False
            
            if result and os.path.exists(sections_dir):
                logger.info(f"Initial extraction completed. Verifying content...")

                index_path = os.path.join(sections_dir, "index.json")
                if not os.path.exists(index_path):
                    logger.warning("index.json not found; triggering fallback extraction without index")
                    fallback_required = True
                else:
                    try:
                        with open(index_path, 'r', encoding='utf-8') as f:
                            index_data = json.load(f)
                        if not index_data or not index_data.get('items'):
                            logger.warning("index.json is empty or has 0 items; triggering fallback extraction")
                            fallback_required = True
                    except Exception as exc:
                        logger.warning(f"Unable to read index.json ({exc}); triggering fallback extraction")
                        fallback_required = True

                # Also check if any actual content sections were created
                sections_content_dir = os.path.join(sections_dir, "sections")
                if not fallback_required:
                    has_content = False
                    if os.path.exists(sections_content_dir):
                        for root, dirs, files in os.walk(sections_content_dir):
                            if "content.json" in files:
                                has_content = True
                                break
                    
                    if not has_content:
                        logger.warning("No section content found after indexed extraction; triggering fallback")
                        fallback_required = True

                if fallback_required:
                    logger.info("Executing fallback: Full PDF page-by-page extraction")
                    
                    # Try to clean up previous attempt, but use a new directory if cleanup fails
                    try:
                        shutil.rmtree(sections_dir, ignore_errors=True)
                    except:
                        pass
                        
                    # Use a fresh directory suffix for fallback to avoid permission issues
                    sections_dir = f"{sections_dir}_fallback"
                    os.makedirs(sections_dir, exist_ok=True)
                    
                    fallback_result = pdf_extract_sections(
                        pdf_path=pdf_path,
                        output_dir=sections_dir,
                        force_full_extraction=True
                    )
                    
                    if not fallback_result:
                        logger.error("Fallback extraction failed")
                        return None
                    
                    logger.info(f"Fallback extraction successful to: {sections_dir}")
                    return sections_dir

                return sections_dir
            else:
                logger.error("Failed to extract sections from PDF (initial attempt returned None)")
                return None

                
        except ImportError:
            logger.error("PDF extraction module not found. Please ensure pdf_extractor.py exists.")
            return None
        except Exception as e:
            logger.error(f"Error extracting sections from PDF: {str(e)}")
            return None
    
    def extract_policies_and_subpolicies(self, sections_dir: str, api_key: str = None) -> Optional[Dict[str, Any]]:
        """
        Extract policies and subpolicies using policy_extractor_enhanced.py.
        
        Args:
            sections_dir: Path to the sections directory
            api_key: OpenAI API key (optional)
            
        Returns:
            Dictionary containing extracted policies or None if failed
        """
        try:
            from ..uploadNist.policy_extractor_enhanced import extract_policies
            from django.conf import settings
            
            # Get API key from settings if not provided
            if not api_key:
                api_key = getattr(settings, 'OPENAI_API_KEY', None)
            
            if not api_key:
                logger.error("OpenAI API key not found in settings")
                return None
            
            # Create output directory for policies
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            policies_dir = os.path.join(self.temp_dir, f"policies_{timestamp}")
            
            logger.info(f"Extracting policies from sections: {sections_dir}")
            logger.info(f"Using OpenAI API key: {'*' * (len(api_key) - 4) + api_key[-4:]}")
            
            # Extract policies
            result = extract_policies(
                sections_dir=sections_dir,
                output_dir=policies_dir,
                api_key=api_key,
                verbose=True
            )
            
            if result and result.get('success'):
                logger.info(f"Successfully extracted {result.get('summary', {}).get('extraction_summary', {}).get('total_policies', 0)} policies")
                return result
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                logger.error(f"Failed to extract policies: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting policies: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_compliance_records(self, policies_data: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
        """
        Generate compliance records for all subpolicies using compliance_generator.py.
        
        Args:
            policies_data: Dictionary containing extracted policies
            api_key: OpenAI API key (optional)
            
        Returns:
            Dictionary containing compliance records
        """
        try:
            from ..uploadNist.compliance_generator import generate_compliance_for_single_subpolicy
            from django.conf import settings
            
            # Get API key from settings if not provided
            if not api_key:
                api_key = getattr(settings, 'OPENAI_API_KEY', None)
            
            logger.info("Generating compliance records for subpolicies")
            
            compliance_results = []
            total_subpolicies = 0
            processed_subpolicies = 0
            
            # Iterate through all policies and subpolicies
            for section in policies_data.get('all_policies', []):
                for policy in section.get('analysis', {}).get('policies', []):
                    policy_id = policy.get('policy_id', '')
                    policy_title = policy.get('policy_title', '')
                    
                    for subpolicy in policy.get('subpolicies', []):
                        total_subpolicies += 1
                        subpolicy_id = subpolicy.get('subpolicy_id', '')
                        subpolicy_title = subpolicy.get('subpolicy_title', '')
                        subpolicy_description = subpolicy.get('subpolicy_description', '')
                        control = subpolicy.get('control', '')
                        
                        try:
                            # Generate compliance records for this subpolicy
                            compliances = generate_compliance_for_single_subpolicy(
                                subpolicy_id=subpolicy_id,
                                subpolicy_name=subpolicy_title,
                                description=subpolicy_description,
                                control=control,
                                api_key=api_key
                            )
                            
                            if compliances:
                                # Add policy context to compliance records
                                for compliance in compliances:
                                    compliance['PolicyId'] = policy_id
                                    compliance['PolicyTitle'] = policy_title
                                    compliance_results.append(compliance)
                                
                                processed_subpolicies += 1
                                logger.info(f"Generated {len(compliances)} compliance records for subpolicy: {subpolicy_title}")
                            
                        except Exception as e:
                            logger.error(f"Error generating compliance for subpolicy {subpolicy_id}: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
            
            logger.info(f"Generated compliance records for {processed_subpolicies}/{total_subpolicies} subpolicies")
            
            return {
                'success': True,
                'total_subpolicies': total_subpolicies,
                'processed_subpolicies': processed_subpolicies,
                'total_compliance_records': len(compliance_results),
                'compliance_records': compliance_results
            }
            
        except Exception as e:
            logger.error(f"Error generating compliance records: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'compliance_records': []
            }
    
    def combine_results(
        self,
        policies_data: Dict[str, Any],
        compliance_data: Dict[str, Any],
        framework_name: str,
        framework_id: int,
        amendment_date: str
    ) -> Dict[str, Any]:
        """
        Combine all extracted data into a single structured JSON.
        
        Args:
            policies_data: Extracted policies data
            compliance_data: Generated compliance data
            framework_name: Name of the framework
            framework_id: ID of the framework
            amendment_date: Date of the amendment
            
        Returns:
            Combined data structure
        """
        try:
            # Create compliance lookup by subpolicy_id
            compliance_by_subpolicy = {}
            for compliance in compliance_data.get('compliance_records', []):
                subpolicy_id = compliance.get('SubPolicyId', '')
                if subpolicy_id not in compliance_by_subpolicy:
                    compliance_by_subpolicy[subpolicy_id] = []
                compliance_by_subpolicy[subpolicy_id].append(compliance)
            
            # Enhance policies with compliance data
            enhanced_policies = []
            for section in policies_data.get('all_policies', []):
                section_info = section.get('section_info', {})
                policies = section.get('analysis', {}).get('policies', [])
                
                enhanced_section_policies = []
                for policy in policies:
                    enhanced_subpolicies = []
                    
                    for subpolicy in policy.get('subpolicies', []):
                        subpolicy_id = subpolicy.get('subpolicy_id', '')
                        
                        # Add compliance records to subpolicy
                        subpolicy_with_compliance = {
                            **subpolicy,
                            'compliance_records': compliance_by_subpolicy.get(subpolicy_id, [])
                        }
                        enhanced_subpolicies.append(subpolicy_with_compliance)
                    
                    enhanced_policy = {
                        **policy,
                        'subpolicies': enhanced_subpolicies
                    }
                    enhanced_section_policies.append(enhanced_policy)
                
                enhanced_policies.append({
                    'section_info': section_info,
                    'policies': enhanced_section_policies
                })
            
            # Create final combined structure
            combined_data = {
                'amendment_metadata': {
                    'framework_id': framework_id,
                    'framework_name': framework_name,
                    'amendment_date': amendment_date,
                    'processing_date': datetime.now().isoformat(),
                    'framework_info': policies_data.get('all_policies', [{}])[0].get('analysis', {}).get('framework_info', {})
                },
                'extraction_summary': {
                    'total_sections': len(enhanced_policies),
                    'total_policies': policies_data.get('summary', {}).get('extraction_summary', {}).get('total_policies', 0),
                    'total_subpolicies': policies_data.get('summary', {}).get('extraction_summary', {}).get('total_subpolicies', 0),
                    'total_compliance_records': compliance_data.get('total_compliance_records', 0),
                    'policy_type_distribution': policies_data.get('summary', {}).get('extraction_summary', {}).get('policy_type_distribution', {})
                },
                'sections': enhanced_policies
            }
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error combining results: {str(e)}")
            return {
                'error': str(e),
                'amendment_metadata': {
                    'framework_id': framework_id,
                    'framework_name': framework_name,
                    'amendment_date': amendment_date,
                    'processing_date': datetime.now().isoformat()
                }
            }
    
    def save_results(self, combined_data: Dict[str, Any], output_path: str) -> bool:
        """
        Save combined results to JSON file.
        
        Args:
            combined_data: Combined data structure
            output_path: Path to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully saved results to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary processing files."""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary processing files")
        except Exception as e:
            logger.warning(f"Could not clean up temporary files: {str(e)}")


def process_downloaded_amendment(
    pdf_path: str,
    framework_name: str,
    framework_id: int,
    amendment_date: str,
    output_dir: str = None
) -> Dict[str, Any]:
    """
    Main function to process a downloaded amendment PDF.
    
    This function orchestrates the complete pipeline:
    1. Extract sections from PDF
    2. Extract policies and subpolicies
    3. Generate compliance records
    4. Combine and save results
    
    Args:
        pdf_path: Path to the downloaded PDF file
        framework_name: Name of the framework
        framework_id: ID of the framework in the database
        amendment_date: Date of the amendment (YYYY-MM-DD)
        output_dir: Directory to save output files (optional)
        
    Returns:
        Dictionary containing:
            - success: bool
            - data: Combined JSON data
            - output_file: Path to saved JSON file
            - error: Error message if failed
    """
    # If output_dir is provided, use it as the working directory for everything
    processor = AmendmentProcessor(work_dir=output_dir)
    
    try:
        logger.info(f"Starting amendment processing for {framework_name}")
        logger.info(f"PDF path: {pdf_path}")
        
        # No need to wipe the directory here if it's the shared download folder 
        # and was already cleaned by the caller. Just ensure it exists.
        processor.prepare_temp_dir()
        
        # Step 1: Extract sections from PDF
        logger.info("Step 1/4: Extracting sections from PDF...")
        sections_dir = processor.extract_sections_from_pdf(pdf_path, framework_name)
        if not sections_dir:
            return {
                'success': False,
                'error': 'Failed to extract sections from PDF'
            }
        
        # Step 2: Extract policies and subpolicies
        logger.info("Step 2/4: Extracting policies and subpolicies...")
        from django.conf import settings
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        policies_data = processor.extract_policies_and_subpolicies(sections_dir, api_key=api_key)
        if not policies_data:
            return {
                'success': False,
                'error': 'Failed to extract policies and subpolicies'
            }
        
        # Step 3: Generate compliance records
        logger.info("Step 3/4: Generating compliance records...")
        compliance_data = processor.generate_compliance_records(policies_data, api_key=api_key)
        
        # Step 4: Combine and save results
        logger.info("Step 4/4: Combining and saving results...")
        combined_data = processor.combine_results(
            policies_data=policies_data,
            compliance_data=compliance_data,
            framework_name=framework_name,
            framework_id=framework_id,
            amendment_date=amendment_date
        )
        
        # Save to file
        if output_dir is None:
            from django.conf import settings
            output_dir = os.path.join(settings.BASE_DIR, 'amendments_processed')
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = framework_name.replace(' ', '_').replace('/', '_')
        output_file = os.path.join(output_dir, f"{safe_name}_amendment_{amendment_date}_{timestamp}.json")
        
        if processor.save_results(combined_data, output_file):
            logger.info(f"Amendment processing completed successfully")
            
            # Do NOT cleanup temp files if they are in the user's output directory 
            # and the user wants to keep them
            # processor.cleanup_temp_files()
            
            return {
                'success': True,
                'data': combined_data,
                'output_file': output_file,
                'summary': combined_data.get('extraction_summary', {})
            }
        else:
            return {
                'success': False,
                'error': 'Failed to save results'
            }
        
    except Exception as e:
        logger.error(f"Error processing amendment: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'success': False,
            'error': str(e)
        }

