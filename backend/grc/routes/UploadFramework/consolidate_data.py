"""
Consolidate framework data into a single, simple JSON file
This makes it easy to load and debug the data structure
"""
import json
import os
from pathlib import Path
from django.conf import settings


def create_consolidated_json(userid):
    """
    Read all_policies.json and create a simple, consolidated JSON file
    in the upload_1 folder for easy loading
    
    Args:
        userid: User ID
        
    Returns:
        dict: Consolidated data structure
    """
    media_root = Path(settings.MEDIA_ROOT)
    user_folder = media_root / f"upload_{userid}"
    
    if not user_folder.exists():
        raise FileNotFoundError(f"User folder not found: {user_folder}")
    
    # Find policies folder
    policies_folders = list(user_folder.glob("policies_*"))
    if not policies_folders:
        raise FileNotFoundError(f"No policies folder found in {user_folder}")
    
    policies_folder = policies_folders[0]
    all_policies_json = policies_folder / "all_policies.json"
    
    if not all_policies_json.exists():
        raise FileNotFoundError(f"all_policies.json not found in {policies_folder}")
    
    print(f"[INFO] Reading all_policies.json from: {all_policies_json}")
    
    # Read the all_policies.json file
    with open(all_policies_json, 'r', encoding='utf-8') as f:
        all_policies_data = json.load(f)
    
    # Build consolidated structure
    consolidated_data = {
        "framework_info": None,
        "sections": [],
        "summary": {
            "total_sections": 0,
            "total_policies": 0,
            "total_subpolicies": 0
        }
    }
    
    total_policies = 0
    total_subpolicies = 0
    
    for section_data in all_policies_data:
        section_info = section_data.get('section_info', {})
        analysis = section_data.get('analysis', {})
        
        # Extract framework info from first section
        if not consolidated_data["framework_info"] and analysis.get('framework_info'):
            consolidated_data["framework_info"] = analysis.get('framework_info', {})
        
        # Build section object
        section = {
            "section_id": f"section_{len(consolidated_data['sections'])}",
            "title": section_info.get('title', 'Untitled Section'),
            "level": section_info.get('level', 1),
            "start_page": section_info.get('start_page'),
            "end_page": section_info.get('end_page'),
            "folder_path": section_info.get('folder_path', ''),
            "policies": []
        }
        
        # Extract policies from analysis
        if analysis.get('has_policies') and analysis.get('policies'):
            for policy_data in analysis.get('policies', []):
                policy = {
                    "policy_id": policy_data.get('policy_id', ''),
                    "policy_title": policy_data.get('policy_title', ''),
                    "policy_description": policy_data.get('policy_description', ''),
                    "policy_text": policy_data.get('policy_text', ''),
                    "scope": policy_data.get('scope', ''),
                    "objective": policy_data.get('objective', ''),
                    "policy_type": policy_data.get('policy_type', ''),
                    "policy_category": policy_data.get('policy_category', ''),
                    "policy_subcategory": policy_data.get('policy_subcategory', ''),
                    "subpolicies": []
                }
                
                # Extract subpolicies
                for subpolicy_data in policy_data.get('subpolicies', []):
                    subpolicy = {
                        "subpolicy_id": subpolicy_data.get('subpolicy_id', ''),
                        "subpolicy_title": subpolicy_data.get('subpolicy_title', ''),
                        "subpolicy_description": subpolicy_data.get('subpolicy_description', ''),
                        "subpolicy_text": subpolicy_data.get('subpolicy_text', ''),
                        "control": subpolicy_data.get('control', '')
                    }
                    policy['subpolicies'].append(subpolicy)
                    total_subpolicies += 1
                
                section['policies'].append(policy)
                total_policies += 1
        
        consolidated_data['sections'].append(section)
    
    # Update summary
    consolidated_data['summary'] = {
        "total_sections": len(consolidated_data['sections']),
        "total_policies": total_policies,
        "total_subpolicies": total_subpolicies
    }
    
    # Save consolidated JSON to upload_1 folder
    output_file = user_folder / "framework_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] Saved consolidated data to: {output_file}")
    print(f"[INFO] Summary: {consolidated_data['summary']}")
    
    return consolidated_data


def load_consolidated_json(userid):
    """
    Load the consolidated JSON file from upload folder
    
    Args:
        userid: User ID
        
    Returns:
        dict: Consolidated data structure or None if not found
    """
    media_root = Path(settings.MEDIA_ROOT)
    user_folder = media_root / f"upload_{userid}"
    
    if not user_folder.exists():
        print(f"[ERROR] User folder not found: {user_folder}")
        return None
    
    # Check if consolidated JSON exists
    consolidated_file = user_folder / "framework_data.json"
    
    if not consolidated_file.exists():
        print(f"[INFO] Consolidated JSON not found, creating it...")
        try:
            return create_consolidated_json(userid)
        except Exception as e:
            print(f"[ERROR] Failed to create consolidated JSON: {e}")
            return None
    
    print(f"[INFO] Loading consolidated data from: {consolidated_file}")
    
    # Read the consolidated JSON file
    with open(consolidated_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"[SUCCESS] Loaded consolidated data: {data.get('summary', {})}")
    
    return data


def regenerate_consolidated_json_for_all_users():
    """
    Regenerate consolidated JSON for all users in MEDIA_ROOT
    Useful for updating existing data
    """
    media_root = Path(settings.MEDIA_ROOT)
    
    # Find all upload_* folders
    upload_folders = list(media_root.glob("upload_*"))
    
    results = []
    for user_folder in upload_folders:
        # Extract userid from folder name
        folder_name = user_folder.name
        userid = folder_name.replace('upload_', '')
        
        try:
            print(f"\n[INFO] Processing user: {userid}")
            data = create_consolidated_json(userid)
            results.append({
                "userid": userid,
                "status": "success",
                "summary": data.get('summary', {})
            })
        except Exception as e:
            print(f"[ERROR] Failed for user {userid}: {e}")
            results.append({
                "userid": userid,
                "status": "error",
                "error": str(e)
            })
    
    return results

