# Upload Data Structure Update

## Summary
Updated the backend code to work with the new folder structure for uploaded framework data. The system now properly loads and displays **Sections → Policies → Subpolicies** hierarchy from uploaded documents.

## Changes Made

### 1. Updated File Structure Support

#### Old Structure (No longer used):
```
MEDIA_ROOT/upload_1/
├── extracted_sections/
│   └── sections_index.json
└── policies/
```

#### New Structure (Now supported):
```
MEDIA_ROOT/upload_1/
├── sections_PCI_DSS_1/
│   ├── sections_index.json
│   └── sections/
│       ├── 001-Introduction_Protecting_Cardholder_Data/
│       ├── 002-Overview_of_PCI_Requirements/
│       └── ...
├── policies_PCI_DSS_1/
│   ├── all_policies.json
│   └── extraction_summary.json
├── PCI_DSS_1_index.json
└── PCI_DSS_1.pdf
```

### 2. Modified Files

#### A. `backend/grc/routes/uploadNist/uploaded_data_loader.py`
**Updated Functions:**

1. **`get_sections_folder(user_id)`**
   - Now dynamically searches for any folder starting with `sections_`
   - Falls back to multiple predefined paths
   - Properly handles `sections_PCI_DSS_1/sections/` structure

2. **`get_policies_folder(user_id)`**
   - Now dynamically searches for any folder starting with `policies_`
   - Falls back to predefined paths including `policies_PCI_DSS_1`

3. **`get_pdf_index_json(user_id)`**
   - Now searches for any file ending with `_index.json`
   - Supports `PCI_DSS_1_index.json` naming pattern

4. **`get_sections_index_json(user_id)` (NEW)**
   - New function to specifically load `sections_index.json` from sections folders
   - Searches in multiple possible locations

5. **`build_sections_from_index(index_data)`**
   - Updated to handle new `sections_written` format from `sections_index.json`
   - Filters for level 1 sections (top-level sections only)
   - Maintains backward compatibility with old format

6. **`build_sections_from_folders(sections_dir)`**
   - Enhanced to include full section metadata
   - Properly reads `content.json` for section titles and content
   - Adds `id`, `section_id`, and other required fields

7. **`_get_policies_for_section_internal(policies_data, section_folder)`**
   - Enhanced path matching logic for nested sections
   - Now returns complete policy structure with all fields:
     - policy_id, policy_title, policy_description, policy_text
     - scope, objective, policy_type, policy_category, policy_subcategory
   - Properly formats subpolicies with all details

8. **`build_complete_structure(user_id)`**
   - Now tries three methods in order:
     1. Load from `sections_index.json` (most reliable)
     2. Load from PDF index JSON
     3. Build from folder structure
   - Enhanced logging for debugging
   - Properly populates policies and counts for each section

9. **`get_uploaded_data_sections(request, user_id)`**
   - Now returns data in same format as `default_data_loader`
   - Includes comprehensive response with:
     - success status
     - task_id
     - framework_name (extracted from PDF filename)
     - sections with full hierarchy
     - total counts (sections, policies, subpolicies)
     - source identifier

#### B. `backend/grc/routes/UploadFramework/new_upload_framework.py`

1. **`get_sections_by_user(request, userid)`**
   - **COMPLETELY REWRITTEN** to use `uploaded_data_loader`
   - Now delegates to `get_uploaded_data_sections` function
   - Returns complete hierarchical structure with policies and subpolicies

2. **`get_sections_from_user_folder(userid)`**
   - Marked as DEPRECATED
   - Updated to search multiple possible locations for `sections_index.json`
   - Added fallback paths for backward compatibility

### 3. URL Configuration

The following URL endpoints are already configured and working:

```python
# Main endpoint for getting sections by user
path('get-sections-by-user/<str:userid>/', new_get_sections_by_user, name='get-sections-by-user')

# Direct access to uploaded data loader
path('ai-upload/uploaded-sections/<str:user_id>/', get_uploaded_data_sections, name='get-uploaded-data-sections')
```

### 4. API Response Format

#### GET `/api/get-sections-by-user/1/`

**Response:**
```json
{
  "success": true,
  "task_id": "upload_1",
  "framework_name": "PCI_DSS_1",
  "sections": [
    {
      "id": 0,
      "section_id": "section_0",
      "title": "Introduction: Protecting Cardholder Data with PCI Security Standards",
      "folder": "001-Introduction_Protecting_Cardholder_Data",
      "content": "",
      "selected": false,
      "expanded": false,
      "policies": [
        {
          "policy_id": "POLICY_001",
          "policy_title": "Data Protection Policy",
          "policy_description": "...",
          "policy_text": "...",
          "scope": "...",
          "objective": "...",
          "policy_type": "...",
          "policy_category": "...",
          "policy_subcategory": "...",
          "selected": false,
          "expanded": false,
          "subpolicies": [
            {
              "subpolicy_id": "SUB_001",
              "subpolicy_title": "Encryption Standards",
              "subpolicy_description": "...",
              "subpolicy_text": "...",
              "control": "...",
              "selected": false
            }
          ]
        }
      ],
      "total_policies": 5,
      "total_subpolicies": 12
    }
  ],
  "total_sections": 6,
  "total_policies": 25,
  "total_subpolicies": 78,
  "source": "upload_1"
}
```

### 5. Key Features

✅ **Dynamic Folder Detection**: Automatically finds folders starting with `sections_` and `policies_`
✅ **Multiple Fallback Paths**: Tries multiple locations for each required file
✅ **Hierarchical Structure**: Complete Sections → Policies → Subpolicies hierarchy
✅ **Backward Compatible**: Still works with old folder structures
✅ **Rich Metadata**: Includes all policy and subpolicy details
✅ **Proper Logging**: Comprehensive logging for debugging
✅ **Error Handling**: Graceful error handling with informative messages

### 6. Comparison with Default Data Loader

The uploaded data loader now works exactly like the default data loader:

| Feature | Default Data Loader | Uploaded Data Loader |
|---------|-------------------|---------------------|
| Data Source | `TEMP_MEDIA_ROOT/sections_PCI_DSS_2` | `MEDIA_ROOT/upload_1/sections_PCI_DSS_1` |
| Response Format | ✅ Hierarchical JSON | ✅ Hierarchical JSON |
| Sections | ✅ Full metadata | ✅ Full metadata |
| Policies | ✅ Complete details | ✅ Complete details |
| Subpolicies | ✅ All fields | ✅ All fields |
| Counts | ✅ Totals included | ✅ Totals included |
| Error Handling | ✅ Graceful | ✅ Graceful |

### 7. Testing

To test the changes:

```bash
# 1. Get sections for user 1 (uploaded data)
GET http://localhost:8000/api/get-sections-by-user/1/

# 2. Load default data
POST http://localhost:8000/api/load-default-data/

# 3. Get default sections
GET http://localhost:8000/api/ai-upload/default-sections/1/
```

### 8. Error Resolution

The error you were seeing:
```
Sections index file not found: D:\grc_dmeo\UI_GRC\backend\MEDIA_ROOT\upload_1\extracted_sections\sections_index.json
```

**Has been fixed by:**
1. Updating the search logic to look in multiple locations
2. Adding support for `sections_PCI_DSS_1/sections_index.json`
3. Implementing dynamic folder detection

### 9. Next Steps

The system is now ready to:
- ✅ Load data from uploaded documents
- ✅ Display sections with policies and subpolicies
- ✅ Handle different folder naming conventions
- ✅ Provide consistent API responses

### 10. Important Notes

⚠️ **Old Function Deprecated**: `get_sections_from_user_folder()` is now deprecated in favor of the new loader
⚠️ **Frontend Changes**: If your frontend expects a different format, update it to handle the new hierarchical structure
⚠️ **Caching**: Consider adding caching for large policy files to improve performance

## Questions or Issues?

If you encounter any issues:
1. Check the server logs for detailed error messages
2. Verify the folder structure matches the expected pattern
3. Ensure `all_policies.json` and `sections_index.json` exist
4. Check file permissions on the upload folders



