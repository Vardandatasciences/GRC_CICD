import os

from .framework_update_checker import run_framework_update_check

# ============================================================
# CONFIGURATION - UPDATE THESE VARIABLES
# ============================================================

# Perplexity API Key

# Framework to test
FRAMEWORK_NAME = "HITRUST CSF"
LAST_UPDATED_DATE = "2025-06-13"

# Download settings
DOWNLOAD_DIR = "downloads"

# ============================================================
# MAIN CODE
# ============================================================


def display_results(update_info: dict) -> None:
    """Display the update check results in a formatted way."""

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\n📋 Framework: {update_info.get('framework_name', 'N/A')}")

    if update_info.get("error"):
        print(f"\n❌ Error occurred: {update_info['error']}")
        return

    has_update = update_info.get("has_update", False)

    if has_update:
        print("\n✅ UPDATE AVAILABLE!")
        print(f"\n   Latest Version Date: {update_info.get('latest_update_date', 'N/A')}")

        if update_info.get("version"):
            print(f"   Version: {update_info.get('version')}")

        if update_info.get("document_url"):
            print(f"   Document URL: {update_info.get('document_url')}")

        if update_info.get("notes"):
            print(f"   Notes: {update_info.get('notes')}")
    else:
        print("\nℹ️  No updates found")
        print(f"   The framework is up to date as of {update_info.get('latest_update_date', 'the last check')}")

    if update_info.get("downloaded_path"):
        print(f"\n📁 Download saved at: {update_info['downloaded_path']}")

    print("\n" + "=" * 70 + "\n")


# ============================================================
# RUN THE TEST
# ============================================================

if __name__ == "__main__":
    # Validate API key
    if PERPLEXITY_API_KEY == "your_perplexity_api_key_here":
        print("\n" + "=" * 70)
        print("⚠️  WARNING: Please set your Perplexity API key!")
        print("=" * 70)
        print("\nUpdate the PERPLEXITY_API_KEY variable at the top of the script.")
        print("Get your API key from: https://www.perplexity.ai/settings/api\n")
        raise SystemExit(1)

    print(f"\n{'=' * 70}")
    print("Checking Framework Update")
    print("=" * 70)
    print(f"Framework: {FRAMEWORK_NAME}")
    print(f"Last Known Update: {LAST_UPDATED_DATE}")
    print("=" * 70 + "\n")

    # Check for framework update
    update_info = run_framework_update_check(
        framework_name=FRAMEWORK_NAME,
        last_updated_date=LAST_UPDATED_DATE,
        api_key=PERPLEXITY_API_KEY,
        download_dir=DOWNLOAD_DIR,
    )

    # Display results
    display_results(update_info)

    # Optionally keep downloaded file reference
    downloaded_path = update_info.get("downloaded_path")
    if downloaded_path and os.path.exists(downloaded_path):
        print(f"📁 Document saved to {downloaded_path}")

    # Print final summary
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)
    print(f"Framework: {FRAMEWORK_NAME}")
    print(f"Has Update: {'YES' if update_info.get('has_update') else 'NO'}")
    if update_info.get("document_url"):
        print(f"Document URL: {update_info.get('document_url')}")
    print("=" * 70 + "\n")
import json
import requests
from datetime import datetime

# ============================================================
# CONFIGURATION - UPDATE THESE VARIABLES
# ============================================================

# Perplexity API Key


# Framework to test
FRAMEWORK_NAME = "HITRUST CSF"
LAST_UPDATED_DATE = "2025-06-13"


# Download settings
DOWNLOAD_ENABLED = True
DOWNLOAD_DIR = "downloads"

# ============================================================
# MAIN CODE
# ============================================================

def create_system_prompt(framework_name: str, last_updated_date: str) -> str:
    """Create system prompt for Perplexity API"""
    return f"""You are a GRC (Governance, Risk, and Compliance) framework update tracker.

Your task is to check if the {framework_name} framework has been updated after {last_updated_date}.

CRITICAL: The has_update field should ONLY be true if the latest official update date is AFTER {last_updated_date}.
If the latest update is on or before {last_updated_date}, set has_update to false.

Instructions:
1. Search for the latest official version/update of {framework_name}
2. Find the exact release/publication date of the latest version
3. Compare the latest update date with {last_updated_date}
4. Set has_update to true ONLY if latest_update_date > {last_updated_date}
5. Respond ONLY in the following JSON format (no additional text):

{{
    "framework_name": "{framework_name}",
    "has_update": true or false,
    "latest_update_date": "YYYY-MM-DD",
    "document_url": "official document URL" or null,
    "version": "version number if available",
    "notes": "brief description of changes if updated"
}}

Requirements:
- has_update must be true ONLY if latest_update_date is AFTER {last_updated_date}
- If latest_update_date is same as or before {last_updated_date}, set has_update to false
- document_url must be a DIRECT download link to the PDF/ZIP file (ending in .pdf, .zip, etc.)
- DO NOT provide page URLs - find the actual downloadable document link
- Use only official sources (nist.gov, iso.org, hhs.gov, etc.)
- If no update found or dates are equal/before, set has_update to false and document_url to null

Example date comparison:
- If last_updated_date is 2025-09-13 and latest is 2025-08-27: has_update = false
- If last_updated_date is 2025-08-27 and latest is 2025-09-13: has_update = true"""


def check_framework_update(framework_name: str, last_updated_date: str, api_key: str) -> dict:
    """Check if framework has been updated using Perplexity API"""
    
    print(f"\n{'='*70}")
    print(f"Checking Framework Update")
    print(f"{'='*70}")
    print(f"Framework: {framework_name}")
    print(f"Last Known Update: {last_updated_date}")
    print(f"{'='*70}\n")
    
    system_prompt = create_system_prompt(framework_name, last_updated_date)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simplified payload - Perplexity doesn't support system messages in the same way
    payload = {
        "model": "sonar-pro",  # Updated to correct Perplexity model name
        "messages": [
            {
                "role": "user",
                "content": f"{system_prompt}\n\nCheck if {framework_name} has been updated after {last_updated_date}. Provide the official document download link if updated."
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }
    
    try:
        print("🔍 Querying Perplexity API...")
        print(f"API Key (first 10 chars): {api_key[:10]}...")
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Print detailed error info if request fails
        if response.status_code != 200:
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        print("✓ API Response received\n")
        print("Raw Response:")
        print("-" * 70)
        print(content)
        print("-" * 70 + "\n")
        
        # Parse JSON response
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        update_info = json.loads(content)
        
        # Validate date logic - ensure latest_update_date is actually after last_updated_date
        if update_info.get('has_update') and update_info.get('latest_update_date'):
            try:
                from datetime import datetime
                latest_date = datetime.strptime(update_info['latest_update_date'], "%Y-%m-%d")
                last_known_date = datetime.strptime(last_updated_date, "%Y-%m-%d")
                
                # If latest date is not after last known date, set has_update to False
                if latest_date <= last_known_date:
                    print(f"⚠️  Date validation: Latest date ({update_info['latest_update_date']}) is not after last known date ({last_updated_date})")
                    print(f"⚠️  Correcting has_update to False\n")
                    update_info['has_update'] = False
            except ValueError as e:
                print(f"⚠️  Could not parse dates for validation: {e}")
        
        return update_info
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Error Details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Response Text: {e.response.text}")
        return {
            "framework_name": framework_name,
            "has_update": False,
            "latest_update_date": None,
            "document_url": None,
            "error": str(e)
        }
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {str(e)}")
        print(f"Response content: {content}")
        return {
            "framework_name": framework_name,
            "has_update": False,
            "latest_update_date": None,
            "document_url": None,
            "error": f"JSON parse error: {str(e)}"
        }
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return {
            "framework_name": framework_name,
            "has_update": False,
            "latest_update_date": None,
            "document_url": None,
            "error": str(e)
        }


def find_actual_pdf_url(page_url: str, framework_name: str, api_key: str) -> str:
    """Use Perplexity to find the actual PDF download link from a page"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "user",
                "content": f"""Find the direct PDF download link for {framework_name} from this page: {page_url}

Requirements:
1. Find the ACTUAL downloadable PDF file link (must end with .pdf)
2. Do NOT return the main page URL
3. Look for links like "Download PDF", "View PDF", or direct .pdf links
4. Return ONLY the direct PDF URL, nothing else
5. If multiple PDFs exist, return the main framework document

Respond with ONLY the PDF URL or "NOT_FOUND" if no direct PDF link exists."""
            }
        ],
        "temperature": 0.1,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        pdf_url = result['choices'][0]['message']['content'].strip()
        
        # Clean up the response
        if pdf_url and pdf_url != "NOT_FOUND" and ".pdf" in pdf_url.lower():
            # Remove any markdown or extra text
            if "http" in pdf_url:
                # Extract just the URL
                import re
                urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+\.pdf', pdf_url)
                if urls:
                    return urls[0]
        
        return None
        
    except Exception as e:
        print(f"⚠️ Could not find direct PDF link: {str(e)}")
        return None


def download_document(framework_name: str, document_url: str, download_dir: str = "downloads", api_key: str = None) -> str:
    """Download framework document"""
    
    import os
    
    if not document_url:
        print("⚠️ No document URL provided")
        return None
    
    # Create download directory
    os.makedirs(download_dir, exist_ok=True)
    
    try:
        print(f"\n📥 Preparing to download...")
        print(f"URL: {document_url}")
        
        # First, check if the URL is a direct PDF link
        if not document_url.lower().endswith('.pdf'):
            print(f"⚠️ URL does not end with .pdf, attempting to find direct PDF link...")
            
            if api_key:
                direct_pdf_url = find_actual_pdf_url(document_url, framework_name, api_key)
                if direct_pdf_url:
                    print(f"✓ Found direct PDF link: {direct_pdf_url}")
                    document_url = direct_pdf_url
                else:
                    print(f"⚠️ Could not find direct PDF link. Saving page URL instead.")
                    # Save the URL to a text file instead
                    safe_name = framework_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{safe_name}_{timestamp}_URL.txt"
                    filepath = os.path.join(download_dir, filename)
                    
                    with open(filepath, 'w') as f:
                        f.write(f"Framework: {framework_name}\n")
                        f.write(f"URL: {document_url}\n")
                        f.write(f"Note: This is a page URL, not a direct PDF link.\n")
                        f.write(f"Please visit the URL to download the document manually.\n")
                    
                    print(f"📁 URL saved to: {filepath}")
                    return filepath
        
        # Try to download the file
        print(f"📥 Downloading from: {document_url}")
        response = requests.get(document_url, stream=True, timeout=60, allow_redirects=True)
        response.raise_for_status()
        
        # Check if we actually got a PDF
        content_type = response.headers.get('content-type', '').lower()
        
        # Determine file extension
        if 'pdf' in content_type or document_url.lower().endswith('.pdf'):
            ext = '.pdf'
        elif 'zip' in content_type:
            ext = '.zip'
        elif 'excel' in content_type or 'spreadsheet' in content_type:
            ext = '.xlsx'
        elif 'word' in content_type or 'document' in content_type:
            ext = '.docx'
        elif 'html' in content_type:
            print(f"⚠️ Warning: Got HTML instead of document (content-type: {content_type})")
            ext = '.html'
        else:
            ext = '.pdf'  # default
        
        # If we got HTML, save the URL instead
        if ext == '.html':
            safe_name = framework_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_{timestamp}_URL.txt"
            filepath = os.path.join(download_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(f"Framework: {framework_name}\n")
                f.write(f"URL: {document_url}\n")
                f.write(f"Content-Type: {content_type}\n")
                f.write(f"Note: This URL returned HTML instead of a document.\n")
                f.write(f"Please visit the URL to download the document manually.\n")
            
            print(f"⚠️ Downloaded HTML page instead of document")
            print(f"📁 URL reference saved to: {filepath}")
            return filepath
        
        # Create filename
        safe_name = framework_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}{ext}"
        filepath = os.path.join(download_dir, filename)
        
        # Download file
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    progress = (downloaded / total_size) * 100
                    print(f"\rProgress: {progress:.1f}%", end='', flush=True)
        
        print(f"\n✅ Successfully downloaded!")
        print(f"📁 File saved to: {filepath}")
        print(f"📊 File size: {downloaded / 1024:.2f} KB")
        print(f"📄 Content type: {content_type}")
        
        return filepath
        
    except Exception as e:
        print(f"\n❌ Download Error: {str(e)}")
        return None


def display_results(update_info: dict):
    """Display the update check results in a formatted way"""
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    print(f"\n📋 Framework: {update_info.get('framework_name', 'N/A')}")
    
    if update_info.get('error'):
        print(f"\n❌ Error occurred: {update_info['error']}")
        return
    
    has_update = update_info.get('has_update', False)
    
    if has_update:
        print(f"\n✅ UPDATE AVAILABLE!")
        print(f"\n   Latest Version Date: {update_info.get('latest_update_date', 'N/A')}")
        
        if update_info.get('version'):
            print(f"   Version: {update_info.get('version')}")
        
        if update_info.get('document_url'):
            print(f"   Document URL: {update_info.get('document_url')}")
        
        if update_info.get('notes'):
            print(f"   Notes: {update_info.get('notes')}")
    else:
        print(f"\nℹ️  No updates found")
        print(f"   The framework is up to date as of {update_info.get('latest_update_date', 'the last check')}")
    
    print("\n" + "="*70 + "\n")


# ============================================================
# RUN THE TEST
# ============================================================

if __name__ == "__main__":
    
    # Validate API key
    if PERPLEXITY_API_KEY == "your_perplexity_api_key_here":
        print("\n" + "="*70)
        print("⚠️  WARNING: Please set your Perplexity API key!")
        print("="*70)
        print("\nUpdate the PERPLEXITY_API_KEY variable at the top of the script.")
        print("Get your API key from: https://www.perplexity.ai/settings/api\n")
        exit(1)
    
    # Check for framework update
    update_info = check_framework_update(
        framework_name=FRAMEWORK_NAME,
        last_updated_date=LAST_UPDATED_DATE,
        api_key=PERPLEXITY_API_KEY
    )
    
    # Display results
    display_results(update_info)
    
    # Download document if update found and download is enabled
    if update_info.get('has_update') and DOWNLOAD_ENABLED and update_info.get('document_url'):
        download_document(
            framework_name=FRAMEWORK_NAME,
            document_url=update_info['document_url'],
            download_dir=DOWNLOAD_DIR,
            api_key=PERPLEXITY_API_KEY
        )
    
    # Print final summary
    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)
    print(f"Framework: {FRAMEWORK_NAME}")
    print(f"Has Update: {'YES' if update_info.get('has_update') else 'NO'}")
    if update_info.get('document_url'):
        print(f"Document URL: {update_info.get('document_url')}")
    print("="*70 + "\n")