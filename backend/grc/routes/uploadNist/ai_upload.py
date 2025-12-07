#!/usr/bin/env python3
"""
AI Upload - Unified PDF Processing Pipeline

This script orchestrates the complete PDF processing pipeline:
1. Extract index/TOC from PDF
2. Create separate sections and PDFs for each index item
3. Extract policies from sections
4. Generate subpolicies, compliances, and risks

Usage:
    python ai_upload.py --pdf path/to/document.pdf --username john_doe
    
    Or import and use:
    from ai_upload import process_pdf_complete
    results = process_pdf_complete("document.pdf", "john_doe")
"""

import os
import sys
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

# Import all required modules - use relative imports for same package
from . import pdf_index_extractor
from . import index_content_extractor
from . import policy_extractor_enhanced
from . import compliance_generator

def get_media_root():
    """
    Get the MEDIA_ROOT path from Django settings or use default.
    
    Returns:
        Path: Path object for MEDIA_ROOT
    """
    try:
        from django.conf import settings
        if hasattr(settings, 'MEDIA_ROOT'):
            media_root = Path(settings.MEDIA_ROOT)
            print(f"DEBUG: Using MEDIA_ROOT from settings: {media_root}")
            return media_root
    except Exception as e:
        print(f"DEBUG: Error getting MEDIA_ROOT from settings: {str(e)}")
    
    # Fallback to backend/MEDIA_ROOT if Django settings not available
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parent.parent.parent.parent
    media_root = backend_dir / "MEDIA_ROOT"
    print(f"DEBUG: Using default MEDIA_ROOT: {media_root}")
    return media_root


def create_user_folder(username: str, base_dir: str = None) -> Path:
    """
    Create or recreate the upload_{username} folder in MEDIA_ROOT.
    If folder exists, delete it and create a new one.
    
    Args:
        username: Username/UserID for folder creation
        base_dir: Base directory where to create the folder (defaults to MEDIA_ROOT)
        
    Returns:
        Path: Path object for the created folder
    """
    # Use MEDIA_ROOT if base_dir not specified
    if base_dir is None:
        base_dir = get_media_root()
        print(f"[DEBUG] Using default base_dir from MEDIA_ROOT: {base_dir}")
    else:
        print(f"[DEBUG] Using provided base_dir: {base_dir}")
    
    folder_name = f"upload_{username}"
    folder_path = Path(base_dir) / folder_name
    print(f"[DEBUG] User folder path: {folder_path}")
    
    # Delete folder if it exists
    if folder_path.exists():
        print(f"[INFO] Folder '{folder_name}' exists. Deleting...")
        try:
            shutil.rmtree(folder_path)
            print(f"[INFO] Deleted existing folder")
        except Exception as e:
            print(f"[ERROR] Failed to delete folder: {str(e)}")
    
    # Create new folder
    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Created folder: {folder_path.resolve()}")
    except Exception as e:
        print(f"[ERROR] Failed to create folder: {str(e)}")
    
    return folder_path


def convert_policies_to_excel(policies_json_path: str, output_excel_path: str) -> bool:
    """
    Convert policies JSON to Excel format for compliance generator.
    
    Args:
        policies_json_path: Path to all_policies.json
        output_excel_path: Path where to save the Excel file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(policies_json_path, 'r', encoding='utf-8') as f:
            all_policies = json.load(f)
        
        # Extract subpolicies into a flat structure
        subpolicies_data = []
        subpolicy_id_counter = 1
        
        for section in all_policies:
            policies = section.get('analysis', {}).get('policies', [])
            
            for policy in policies:
                for subpolicy in policy.get('subpolicies', []):
                    subpolicy_record = {
                        'SubPolicyId': subpolicy_id_counter,
                        'SubPolicyName': subpolicy.get('subpolicy_title', ''),
                        'Description': subpolicy.get('subpolicy_description', ''),
                        'Control': subpolicy.get('control', ''),
                        'PolicyId': policy.get('policy_id', ''),
                        'PolicyTitle': policy.get('policy_title', ''),
                        'PolicyType': policy.get('policy_type', ''),
                        'PolicyCategory': policy.get('policy_category', ''),
                        'SectionTitle': section.get('section_info', {}).get('title', '')
                    }
                    subpolicies_data.append(subpolicy_record)
                    subpolicy_id_counter += 1
        
        if not subpolicies_data:
            print("[WARN] No subpolicies found in the policies JSON")
            return False
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame(subpolicies_data)
        df.to_excel(output_excel_path, index=False)
        print(f"[SUCCESS] Converted {len(subpolicies_data)} subpolicies to Excel: {output_excel_path}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to convert policies to Excel: {e}")
        return False


def process_pdf_complete(pdf_path: str, username: str, base_dir: str = None, verbose: bool = True):
    """
    Complete PDF processing pipeline from PDF to compliance and risk records.
    
    Args:
        pdf_path: Path to the input PDF file
        username: Username/UserID for folder organization
        base_dir: Base directory for processing (default: MEDIA_ROOT)
        verbose: Whether to print detailed progress messages
        
    Returns:
        dict: Results dictionary containing:
            - success: bool indicating if the entire pipeline succeeded
            - user_folder: path to the created user folder
            - index_json: path to extracted index JSON
            - sections_dir: path to extracted sections
            - policies_dir: path to extracted policies
            - subpolicies_excel: path to subpolicies Excel file
            - compliance_file: path to compliance Excel file
            - risk_file: path to risk Excel file
            - summary: processing summary with statistics
            - errors: list of any errors encountered
    """
    print(f"[DEBUG] Starting process_pdf_complete for user: {username}")
    print(f"[DEBUG] PDF path: {pdf_path}")
    print(f"[DEBUG] Base directory: {base_dir}")
    print(f"[DEBUG] Verbose mode: {verbose}")
    
    results = {
        'success': False,
        'user_folder': None,
        'index_json': None,
        'sections_dir': None,
        'policies_dir': None,
        'subpolicies_excel': None,
        'compliance_file': None,
        'risk_file': None,
        'summary': {},
        'errors': []
    }
    
    start_time = datetime.now()
    print(f"[DEBUG] Start time: {start_time.isoformat()}")
    
    try:
        # Use MEDIA_ROOT if base_dir not specified
        if base_dir is None:
            base_dir = get_media_root()
        
        # Validate PDF exists
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        pdf_name = pdf_path.stem
        
        if verbose:
            print("=" * 80)
            print("PDF PROCESSING PIPELINE")
            print("=" * 80)
            print(f"PDF: {pdf_path.name}")
            print(f"Username: {username}")
            print(f"Base Directory (MEDIA_ROOT): {base_dir}")
            print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
        
        # Step 1: Create user folder in MEDIA_ROOT
        if verbose:
            print("\n[STEP 1/5] Creating user folder in MEDIA_ROOT...")
        
        user_folder = create_user_folder(username, base_dir)
        results['user_folder'] = str(user_folder)
        
        # Step 2: Extract index from PDF
        if verbose:
            print("\n[STEP 2/5] Extracting index/TOC from PDF...")
        
        index_json_path = user_folder / f"{pdf_name}_index.json"
        print(f"[DEBUG] Index JSON path: {index_json_path}")
        
        try:
            print(f"[DEBUG] Calling pdf_index_extractor.extract_and_save_index...")
            print(f"[DEBUG] PDF path: {str(pdf_path)}")
            print(f"[DEBUG] Output path: {str(index_json_path)}")
            
            index_data = pdf_index_extractor.extract_and_save_index(
                pdf_path=str(pdf_path),
                output_path=str(index_json_path),
                prefer_toc=True
            )
            results['index_json'] = str(index_json_path)
            
            print(f"[DEBUG] Index extraction completed. Items found: {len(index_data.get('items', []))}")
            
            if verbose:
                print(f"[SUCCESS] Extracted {len(index_data.get('items', []))} index items")
                print(f"[SUCCESS] Index saved to: {index_json_path.name}")
        except Exception as e:
            error_msg = f"Failed to extract index: {e}"
            results['errors'].append(error_msg)
            print(f"[ERROR] {error_msg}")
            import traceback
            print(f"[DEBUG] Exception traceback: {traceback.format_exc()}")
            return results
        
        # Step 3: Extract sections and create individual PDFs
        if verbose:
            print("\n[STEP 3/5] Extracting sections and creating PDFs...")
        
        sections_output_dir = user_folder / f"sections_{pdf_name}"
        try:
            manifest = index_content_extractor.process_pdf_sections(
                pdf_path=str(pdf_path),
                index_json_path=str(index_json_path),
                output_dir=str(sections_output_dir),
                verbose=verbose
            )
            results['sections_dir'] = str(sections_output_dir)
            
            if verbose:
                sections_count = len(manifest.get('sections_written', []))
                print(f"[SUCCESS] Extracted {sections_count} sections")
                print(f"[SUCCESS] Sections saved to: {sections_output_dir.name}/")
        except Exception as e:
            error_msg = f"Failed to extract sections: {e}"
            results['errors'].append(error_msg)
            print(f"[ERROR] {error_msg}")
            return results
        
        # Step 4: Extract policies from sections
        if verbose:
            print("\n[STEP 4/5] Extracting policies from sections using AI...")
        
        policies_output_dir = user_folder / f"policies_{pdf_name}"
        try:
            policy_results = policy_extractor_enhanced.extract_policies(
                sections_dir=str(sections_output_dir),
                output_dir=str(policies_output_dir),
                verbose=verbose
            )
            results['policies_dir'] = str(policies_output_dir)
            
            if policy_results.get('success'):
                total_policies = policy_results['summary']['extraction_summary']['total_policies']
                total_subpolicies = policy_results['summary']['extraction_summary']['total_subpolicies']
                
                if verbose:
                    print(f"[SUCCESS] Extracted {total_policies} policies")
                    print(f"[SUCCESS] Extracted {total_subpolicies} subpolicies")
                    print(f"[SUCCESS] Policies saved to: {policies_output_dir.name}/")
            else:
                error_msg = policy_results.get('error', 'Policy extraction failed')
                results['errors'].append(error_msg)
                print(f"[ERROR] {error_msg}")
                return results
                
        except Exception as e:
            error_msg = f"Failed to extract policies: {e}"
            results['errors'].append(error_msg)
            print(f"[ERROR] {error_msg}")
            return results
        
        # Step 4.5: Convert policies JSON to Excel for compliance generator
        if verbose:
            print("\n[STEP 4.5/5] Converting policies to Excel format...")
        
        policies_json_path = policies_output_dir / "all_policies.json"
        subpolicies_excel_path = user_folder / f"{pdf_name}_subpolicies.xlsx"
        
        try:
            conversion_success = convert_policies_to_excel(
                policies_json_path=str(policies_json_path),
                output_excel_path=str(subpolicies_excel_path)
            )
            
            if conversion_success:
                results['subpolicies_excel'] = str(subpolicies_excel_path)
            else:
                error_msg = "No subpolicies to convert"
                results['errors'].append(error_msg)
                print(f"[WARN] {error_msg}")
                # Continue anyway, this is not a critical failure
                
        except Exception as e:
            error_msg = f"Failed to convert policies to Excel: {e}"
            results['errors'].append(error_msg)
            print(f"[ERROR] {error_msg}")
            # Continue anyway
        
        # Step 5: Generate compliance and risk records
        if verbose:
            print("\n[STEP 5/5] Generating compliance and risk records using AI...")
        
        compliance_output_dir = user_folder / f"compliance_risk_{pdf_name}"
        
        if results.get('subpolicies_excel'):
            try:
                compliance_results = compliance_generator.generate_compliance_and_risk(
                    excel_file_path=str(subpolicies_excel_path),
                    output_prefix=f"{pdf_name}",
                    output_dir=str(compliance_output_dir),
                    save_to_file=True
                )
                
                compliance_data, risk_data, compliance_file, risk_file = compliance_results
                
                if compliance_file:
                    results['compliance_file'] = compliance_file
                    if verbose:
                        print(f"[SUCCESS] Generated {len(compliance_data)} compliance records")
                        print(f"[SUCCESS] Compliance saved to: {Path(compliance_file).name}")
                
                if risk_file:
                    results['risk_file'] = risk_file
                    if verbose:
                        print(f"[SUCCESS] Generated {len(risk_data)} risk records")
                        print(f"[SUCCESS] Risks saved to: {Path(risk_file).name}")
                        
            except Exception as e:
                error_msg = f"Failed to generate compliance and risk records: {e}"
                results['errors'].append(error_msg)
                print(f"[ERROR] {error_msg}")
        else:
            if verbose:
                print("[SKIP] No subpolicies Excel file available, skipping compliance generation")
        
        # Create final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        results['summary'] = {
            'pdf_name': pdf_name,
            'username': username,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'index_items': len(index_data.get('items', [])) if index_data else 0,
            'sections_extracted': len(manifest.get('sections_written', [])) if manifest else 0,
            'policies_extracted': total_policies if 'total_policies' in locals() else 0,
            'subpolicies_extracted': total_subpolicies if 'total_subpolicies' in locals() else 0,
            'compliance_records': len(compliance_data) if 'compliance_data' in locals() and compliance_data else 0,
            'risk_records': len(risk_data) if 'risk_data' in locals() and risk_data else 0
        }
        
        # Save summary to JSON
        summary_file = user_folder / "processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        if verbose:
            print("\n" + "=" * 80)
            print("PROCESSING COMPLETE")
            print("=" * 80)
            print(f"Total duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
            print(f"\nResults saved in: {user_folder}")
            print(f"\nSummary:")
            print(f"  - Index items: {results['summary']['index_items']}")
            print(f"  - Sections: {results['summary']['sections_extracted']}")
            print(f"  - Policies: {results['summary']['policies_extracted']}")
            print(f"  - Subpolicies: {results['summary']['subpolicies_extracted']}")
            print(f"  - Compliance records: {results['summary']['compliance_records']}")
            print(f"  - Risk records: {results['summary']['risk_records']}")
            
            if results['errors']:
                print(f"\nWarnings/Errors: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"  - {error}")
            
            print(f"\nProcessing summary saved to: {summary_file.name}")
            print("=" * 80)
        
        results['success'] = True
        
    except Exception as e:
        error_msg = f"Unexpected error in pipeline: {e}"
        results['errors'].append(error_msg)
        print(f"[ERROR] {error_msg}")
        
        # Save error summary
        if results.get('user_folder'):
            error_file = Path(results['user_folder']) / "error_log.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Error log saved to: {error_file}")
    
    return results


def main():
    """Command-line interface for the PDF processing pipeline."""
    parser = argparse.ArgumentParser(
        description="Complete PDF Processing Pipeline - Extract index, sections, policies, compliance, and risks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ai_upload.py --pdf PCI_DSS.pdf --username john_doe
  python ai_upload.py --pdf document.pdf --username alice --base-dir ./output --quiet
        """
    )
    
    parser.add_argument(
        '--pdf',
        required=True,
        help='Path to the PDF file to process'
    )
    
    parser.add_argument(
        '--username',
        required=True,
        help='Username for folder organization (creates upload_{username} folder)'
    )
    
    parser.add_argument(
        '--base-dir',
        default='.',
        help='Base directory for processing (default: current directory)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress detailed progress messages'
    )
    
    args = parser.parse_args()
    
    # Run the complete pipeline
    results = process_pdf_complete(
        pdf_path=args.pdf,
        username=args.username,
        base_dir=args.base_dir,
        verbose=not args.quiet
    )
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


# if __name__ == "__main__":
#     # ============================================================================
#     # DIRECT EXECUTION MODE - Set your paths here and run directly
#     # ============================================================================
    
#     # SET YOUR OPENAI API KEY HERE (if .env file is not working):
#     OPENAI_API_KEY = "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"
    
#     # SET YOUR PATHS HERE:
#     PDF_PATH = "PCI_DSS_2.pdf"              # Path to your PDF file
#     USERNAME = "john_doe"                  # Your username (for folder naming)
#     BASE_DIR = "."                         # Base directory (. = current directory)
#     VERBOSE = True                         # True = show progress, False = quiet mode
    
#     # ============================================================================
#     # Choose execution mode:
#     # - If you want to use command-line arguments: comment out the direct mode below
#     # - If you want to use direct paths: keep the direct mode uncommented
#     # ============================================================================
    
#     # Set API key in environment if provided directly
#     if OPENAI_API_KEY:
#         os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
#         print("[INFO] Using API key set directly in script")
    
#     # Check if command-line arguments are provided
#     if len(sys.argv) > 1:
#         # Use command-line parsing mode
#         main()
#     else:
#         # Use direct execution mode with variables set above
#         print("=" * 80)
#         print("RUNNING IN DIRECT MODE")
#         print("=" * 80)
#         print(f"PDF Path: {PDF_PATH}")
#         print(f"Username: {USERNAME}")
#         print(f"Base Directory: {BASE_DIR}")
#         print(f"API Key: {'Set' if os.environ.get('OPENAI_API_KEY') else 'NOT SET - WILL FAIL!'}")
#         print("=" * 80)
#         print("\nStarting pipeline...\n")
        
#         # Run the pipeline with the paths set above
#         results = process_pdf_complete(
#             pdf_path=PDF_PATH,
#             username=USERNAME,
#             base_dir=BASE_DIR,
#             verbose=VERBOSE
#         )
        
#         # Exit with appropriate code
#         sys.exit(0 if results['success'] else 1)

