import os
import shutil
import json
import re
from pathlib import Path
from .index_extractor_claude import extract_index_to_folder
from .index_txt_extrcator_claude import main as extract_text_sections
from .sub_policy_extraction import process_all_pdfs_in_sections
from .json_Policy_extractor import extract_policy_from_pdf
from django.conf import settings

def create_user_folder(userid):
    """
    Creates a folder with the name 'upload_userid' where userid is the provided user ID.
    
    Args:
        userid (str): The user ID to create the folder for
        
    Returns:
        str: The path of the created folder
        
    Raises:
        OSError: If there's an error creating the folder
    """
    # Create folder name with the user ID
    folder_name = f"upload_{userid}"
    
    # Create the folder path in MEDIA_ROOT
    folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)
    
    try:
        # Delete folder if it exists
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"Deleted existing folder: {folder_path}")
        
        # Create the new folder
        os.makedirs(folder_path)
        print(f"Created new folder: {folder_path}")
        
        return folder_path
        
    except OSError as e:
        print(f"Error creating folder '{folder_name}': {e}")
        raise

def upload_pdf_and_extract_index(userid, pdf_path):
    """
    Uploads a PDF to the user's folder and extracts the index using index_extractor_claude.py
    
    Args:
        userid (str): The user ID to create/use the folder for
        pdf_path (str): Path to the PDF file to upload (already saved in user folder)
        
    Returns:
        dict: Dictionary containing folder path, uploaded PDF path, and extracted index path
    """
    try:
        # Step 1: Get the user folder (file is already saved here)
        user_folder = os.path.join(settings.MEDIA_ROOT, f"upload_{userid}")
        
        if not os.path.exists(user_folder):
            error_msg = f"User folder not found: {user_folder}"
            print(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
        
        # Step 2: Check if PDF file exists in the user folder
        pdf_filename = os.path.basename(pdf_path)
        uploaded_pdf_path = os.path.join(user_folder, pdf_filename)
        
        if not os.path.exists(uploaded_pdf_path):
            error_msg = f"PDF file not found in user folder: {uploaded_pdf_path}"
            print(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
        
        print(f"PDF found in user folder: {uploaded_pdf_path}")
        
        # Step 3: Extract index using the function from index_extractor_claude.py
        extracted_index_path = extract_index_to_folder(uploaded_pdf_path, user_folder)
        
        return {
            "user_folder": user_folder,
            "uploaded_pdf_path": uploaded_pdf_path,
            "extracted_index_path": extracted_index_path,
            "status": "success"
        }
        
    except Exception as e:
        error_msg = f"Error processing PDF: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }

def upload_pdf_and_extract_all(userid, pdf_path):
    """
    Complete workflow: Uploads a PDF to the user's folder, extracts index, checks for appendix, and extracts text sections.
    
    Args:
        userid (str): The user ID to create/use the folder for
        pdf_path (str): Path to the PDF file to upload
        
    Returns:
        dict: Dictionary containing all processing results
    """
    try:
        # Step 1: Upload PDF and extract index
        index_result = upload_pdf_and_extract_index(userid, pdf_path)
        
        if index_result["status"] != "success":
            return index_result
        
        user_folder = index_result["user_folder"]
        
        # Step 2: Check for appendix and extract policies if NOT found
        print(f"\n=== Starting Appendix Check and Policy Extraction ===")
        appendix_result = check_for_appendix_and_extract(user_folder, index_result["extracted_index_path"])
        
        if appendix_result["status"] == "error":
            return {
                "user_folder": user_folder,
                "uploaded_pdf_path": index_result["uploaded_pdf_path"],
                "extracted_index_path": index_result["extracted_index_path"],
                "status": "partial_success",
                "error": appendix_result["error"],
                "message": "Index extraction successful, but appendix check failed"
            }
        
        # If NO appendix was found and policy extraction was completed, return early
        if not appendix_result.get("appendix_found", True):
            return {
                "user_folder": user_folder,
                "uploaded_pdf_path": index_result["uploaded_pdf_path"],
                "extracted_index_path": index_result["extracted_index_path"],
                "policy_extraction": appendix_result,
                "status": "success",
                "message": "No appendix detected and policy extraction completed - skipping normal text section extraction"
            }
        
        # Step 3: Extract text sections using index_txt_extrcator_claude.py (only if appendix found)
        print(f"\n=== Starting Text Section Extraction ===")
        try:
            extracted_sections_dir = extract_text_sections(user_folder)
            print(f"Text sections extracted successfully to: {extracted_sections_dir}")
            
            return {
                "user_folder": user_folder,
                "uploaded_pdf_path": index_result["uploaded_pdf_path"],
                "extracted_index_path": index_result["extracted_index_path"],
                "extracted_sections_dir": str(extracted_sections_dir),
                "appendix_check": appendix_result,
                "status": "success",
                "message": "Complete processing successful"
            }
            
        except Exception as section_error:
            error_msg = f"Error extracting text sections: {str(section_error)}"
            print(error_msg)
            return {
                "user_folder": user_folder,
                "uploaded_pdf_path": index_result["uploaded_pdf_path"],
                "extracted_index_path": index_result["extracted_index_path"],
                "appendix_check": appendix_result,
                "status": "partial_success",
                "error": error_msg,
                "message": "Index and appendix check successful, but text section extraction failed"
            }
        
    except Exception as e:
        error_msg = f"Error in complete processing: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }

def upload_pdf_and_extract_complete(userid, pdf_path):
    """
    Complete workflow: Upload PDF, extract index, check for appendix, and either:
    - If appendix found: Extract policies using json_Policy_extractor
    - If no appendix: Extract text sections and sub-policies
    
    Args:
        userid (str): The user ID to create/use the folder for
        pdf_path (str): Path to the PDF file to upload
        
    Returns:
        dict: Dictionary containing all processing results
    """
    try:
        # Step 1-3: Upload PDF, extract index, and check for appendix
        sections_result = upload_pdf_and_extract_all(userid, pdf_path)
        
        if sections_result["status"] not in ["success", "partial_success"]:
            return sections_result
        
        user_folder = sections_result["user_folder"]
        
        # Check if NO appendix was found and policy extraction was completed
        if sections_result.get("policy_extraction"):
            # No appendix found and policy extraction completed - no need for sub-policy extraction
            return {
                "user_folder": user_folder,
                "uploaded_pdf_path": sections_result["uploaded_pdf_path"],
                "extracted_index_path": sections_result["extracted_index_path"],
                "policy_extraction": sections_result["policy_extraction"],
                "status": "success",
                "message": "No appendix detected and policy extraction completed - workflow complete"
            }
        
        # Step 4: Extract sub-policies using sub_policy_extraction.py (only if no appendix found)
        print(f"\n=== Starting Sub-Policy Extraction ===")
        try:
            # Temporarily change the working directory to the user folder
            # so that sub_policy_extraction can find the correct path
            original_cwd = os.getcwd()
            os.chdir(user_folder)
            
            # Call the sub-policy extraction function
            process_all_pdfs_in_sections()
            
            # Change back to original directory
            os.chdir(original_cwd)
            
            print(f"Sub-policy extraction completed successfully")
            
            return {
                "user_folder": user_folder,
                "uploaded_pdf_path": sections_result["uploaded_pdf_path"],
                "extracted_index_path": sections_result["extracted_index_path"],
                "extracted_sections_dir": sections_result.get("extracted_sections_dir", ""),
                "appendix_check": sections_result.get("appendix_check", {}),
                "sub_policy_extraction": "completed",
                "status": "success",
                "message": "Complete workflow successful (no appendix found)"
            }
            
        except Exception as sub_policy_error:
            error_msg = f"Error extracting sub-policies: {str(sub_policy_error)}"
            print(error_msg)
            
            # Change back to original directory if there was an error
            try:
                os.chdir(original_cwd)
            except:
                pass
            
            return {
                "user_folder": user_folder,
                "uploaded_pdf_path": sections_result["uploaded_pdf_path"],
                "extracted_index_path": sections_result["extracted_index_path"],
                "extracted_sections_dir": sections_result.get("extracted_sections_dir", ""),
                "appendix_check": sections_result.get("appendix_check", {}),
                "status": "partial_success",
                "error": error_msg,
                "message": "Steps 1-3 successful, but sub-policy extraction failed"
            }
        
    except Exception as e:
        error_msg = f"Error in complete workflow processing: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }

def check_for_appendix_and_extract(user_folder, index_json_path):
    """
    Check if the index JSON contains any appendix-type words in titles.
    If NOT found, call json_Policy_extractor.py to process the PDF.
    
    Args:
        user_folder (str): Path to the user's folder
        index_json_path (str): Path to the index JSON file
        
    Returns:
        dict: Dictionary containing the result of the check and extraction
    """
    try:
        # Read the index JSON file
        with open(index_json_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        # Check for appendix-type words in titles
        appendix_keywords = ['appendix', 'APPENDIX', 'Appendix']
        appendix_found = False
        appendix_titles = []
        
        if 'items' in index_data:
            for item in index_data['items']:
                if 'title' in item:
                    title = item['title']
                    for keyword in appendix_keywords:
                        if keyword in title:
                            appendix_found = True
                            appendix_titles.append(title)
                            break
        
        if appendix_found:
            print(f"\n=== Appendix Found - Continuing Normal Process ===")
            print(f"Found appendix titles: {appendix_titles}")
            
            return {
                "status": "success",
                "appendix_found": True,
                "appendix_titles": appendix_titles,
                "message": "Appendix detected, continuing with normal text section extraction"
            }
        else:
            print(f"\n=== No Appendix Found - Starting Policy Extraction ===")
            
            # Find the original PDF file in the user folder
            pdf_files = [f for f in os.listdir(user_folder) if f.lower().endswith('.pdf')]
            if not pdf_files:
                return {
                    "status": "error",
                    "error": "No PDF file found in user folder for policy extraction"
                }
            
            # Use the first PDF file found
            pdf_path = os.path.join(user_folder, pdf_files[0])
            print(f"Processing PDF for policy extraction: {pdf_path}")
            
            # Call the json_Policy_extractor function
            try:
                extracted_policies = extract_policy_from_pdf(pdf_path)
                
                # Save the extracted policies to the user folder
                output_path = os.path.join(user_folder, "policy_extracted.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(extracted_policies, f, indent=2, ensure_ascii=False)
                
                print(f"Policy extraction completed successfully!")
                print(f"Output saved to: {output_path}")
                
                return {
                    "status": "success",
                    "appendix_found": False,
                    "extracted_policies_path": output_path,
                    "message": "No appendix detected, policy extraction completed"
                }
                
            except Exception as extract_error:
                error_msg = f"Error during policy extraction: {str(extract_error)}"
                print(error_msg)
                return {
                    "status": "error",
                    "appendix_found": False,
                    "error": error_msg
                }
            
    except Exception as e:
        error_msg = f"Error checking for appendix: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }

# # Example usage
# if __name__ == "__main__":
#     # Example: Complete workflow processing for user "12345"
#     user_id = "12345"
#     pdf_file_path = "NIST.SP.800-53r5_3.2.pdf"  # Replace with your PDF path
    
#     # Complete workflow: Upload PDF, extract index, check for appendix, and process accordingly
#     result = upload_pdf_and_extract_complete(user_id, pdf_file_path)
    
#     if result["status"] == "success":
#         print(f"\n=== Complete Workflow Processing Results ===")
#         print(f"User folder: {result['user_folder']}")
#         print(f"Uploaded PDF: {result['uploaded_pdf_path']}")
#         print(f"Extracted index: {result['extracted_index_path']}")
        
#         # Check if policy extraction was processed (no appendix found)
#         if "policy_extraction" in result:
#             print(f"No appendix detected and policy extraction completed!")
#             print(f"Extracted policies: {result['policy_extraction'].get('extracted_policies_path', '')}")
#         else:
#             # Normal processing path (appendix found)
#             print(f"Appendix detected - continuing with normal process")
#             print(f"Extracted sections: {result.get('extracted_sections_dir', '')}")
#             print(f"Sub-policy extraction: {result.get('sub_policy_extraction', '')}")
#             if "appendix_check" in result:
#                 print(f"Appendix check: {result['appendix_check'].get('message', '')}")
        
#         print(f"Status: {result['message']}")
#     elif result["status"] == "partial_success":
#         print(f"\n=== Partial Processing Results ===")
#         print(f"User folder: {result['user_folder']}")
#         print(f"Uploaded PDF: {result['uploaded_pdf_path']}")
#         print(f"Extracted index: {result['extracted_index_path']}")
#         if "extracted_sections_dir" in result:
#             print(f"Extracted sections: {result['extracted_sections_dir']}")
#         if "appendix_check" in result:
#             print(f"Appendix check: {result['appendix_check'].get('message', '')}")
#         print(f"Status: {result['message']}")
#         print(f"Error: {result['error']}")
#     else:
        print(f"Error: {result['error']}")
