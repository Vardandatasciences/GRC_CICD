import json
import os
import re
from datetime import datetime
from typing import Optional

import requests


def create_system_prompt(framework_name: str, last_updated_date: str) -> str:
    """Create system prompt for Perplexity API."""
    return f"""You are a GRC (Governance, Risk, and Compliance) framework update tracker and PDF finder.

Your PRIMARY TASK is to:
1. Check if {framework_name} has been updated after {last_updated_date}
2. THOROUGHLY search for and find the DIRECT PDF download link for the LATEST AMENDMENT document
3. Return the PDF URL if available, even if it requires authentication (we'll handle that separately)

CRITICAL: The has_update field should ONLY be true if the latest official update date is AFTER {last_updated_date}.
If the latest update is on or before {last_updated_date}, set has_update to false.

SEARCH STRATEGY - Search THOROUGHLY for PDFs:
1. Search the official framework website/documentation portal
2. Search for "download PDF", "PDF download", "get PDF", "view PDF", "PDF file"
3. Search for amendment-specific terms: "amendment PDF", "update PDF", "change document PDF", "revision PDF", "supplement PDF"
4. Search official repositories: NIST publications, ISO standards library, PCI DSS document library, etc.
5. Check document libraries, publication pages, download sections
6. Look for direct file links ending in .pdf
7. Search for version numbers, update numbers, amendment numbers combined with PDF
8. Check release notes, changelogs, update announcements for PDF links
9. Search for "Summary of Changes PDF", "What's New PDF", "Update Document PDF"
10. Look in official document archives and version history pages

IMPORTANT: You are looking for AMENDMENT documents, NOT the full framework document.
- Amendments are typically smaller PDFs (usually 10-100 pages) that describe changes/updates
- Full framework documents are large (hundreds of pages) - DO NOT use these
- Search for terms like: "amendment", "update", "change document", "revision", "supplement", "summary of changes"
- Look for documents titled: "Amendment to...", "Update to...", "Changes to...", "Revision...", "Summary of Changes..."

PDF URL REQUIREMENTS:
- document_url MUST be a DIRECT download link to a PDF file (must end with .pdf)
- document_url MUST be for the AMENDMENT document, NOT the full framework document
- Search for URLs like: https://example.com/amendment-2025.pdf, https://example.com/downloads/update.pdf
- Look for URLs containing: /pdf/, /download/, /files/, /documents/, /publications/
- Accept URLs even if they might require authentication (we'll handle that)
- If you find ANY PDF URL that could be the amendment, include it
- Search multiple sources: official websites, document libraries, publication portals
- Check both current and archive sections of websites

Instructions:
1. THOROUGHLY search for the latest official AMENDMENT/UPDATE document of {framework_name} (NOT the full framework)
2. Search multiple sources: official website, document library, publication portal, standards organization website
3. Find the exact release/publication date of the latest amendment
4. Compare the latest update date with {last_updated_date}
5. Set has_update to true ONLY if latest_update_date > {last_updated_date}
6. MOST IMPORTANT: Search extensively and find the DIRECT PDF download link for the LATEST AMENDMENT document
7. If you find ANY PDF URL that could be the amendment document, include it in document_url
8. Search for PDFs in: official websites, document libraries, download sections, publication pages, archives
9. CRITICAL: You MUST respond with ONLY valid JSON. Do NOT include any explanatory text, markdown, or code blocks. Return ONLY the JSON object starting with {{ and ending with }}.

{{
    "framework_name": "{framework_name}",
    "has_update": true or false,
    "latest_update_date": "YYYY-MM-DD",
    "document_url": "DIRECT PDF download URL for AMENDMENT" or null,
    "version": "version number if available",
    "notes": "brief description of changes if updated"
}}

CRITICAL REQUIREMENTS FOR document_url - SEARCH THOROUGHLY:
- document_url MUST be a DIRECT download link to an AMENDMENT PDF file (must end with .pdf)
- document_url MUST be for the AMENDMENT document, NOT the full framework document
- Amendment documents are typically smaller PDFs (10-100 pages)
- DO NOT use full framework documents (which are large, 200+ pages)

SEARCH THOROUGHLY FOR PDFs:
- Search official framework websites, document libraries, publication portals
- Search for: "amendment PDF", "update PDF", "change document PDF", "revision PDF", "summary of changes PDF"
- Search for: "download PDF", "PDF download", "get PDF", "view PDF", "PDF file"
- Look for URLs containing words like: amendment, update, changes, revision, supplement, summary, changelog
- Check these URL patterns: /pdf/, /download/, /files/, /documents/, /publications/, /amendments/, /updates/
- Search in: official websites, standards organizations, document repositories, download sections
- Check both current pages AND archive/history pages
- Look for version numbers, update numbers, amendment numbers in URLs
- Search for "Summary of Changes", "What's New", "Update Document", "Amendment Document"

PDF URL VALIDATION:
- document_url MUST be the actual PDF file URL, NOT a webpage or HTML page
- Look for URLs like: https://example.com/amendment-2025.pdf or https://example.com/updates/changes.pdf
- Accept URLs like: https://example.com/downloads/amendment.pdf, https://example.com/files/update-2025.pdf
- DO NOT provide page URLs like https://example.com/pages/document (these are HTML pages)
- DO NOT provide URLs that redirect to pages - find the actual PDF file URL
- If you find ANY PDF URL that could be the amendment, include it (even if authentication might be required)
- Use official sources: nist.gov, iso.org, hhs.gov, pcisecuritystandards.org, etc.
- Search multiple pages: homepage, downloads, publications, documents, updates, amendments sections
- If you cannot find a direct AMENDMENT PDF download link after thorough searching, set document_url to null

Other Requirements:
- has_update must be true ONLY if latest_update_date is AFTER {last_updated_date}
- If latest_update_date is same as or before {last_updated_date}, set has_update to false
- If no update found or dates are equal/before, set has_update to false and document_url to null
- If update found but no AMENDMENT PDF download link available, set document_url to null

Example date comparison:
- If last_updated_date is 2025-09-13 and latest is 2025-08-27: has_update = false
- If last_updated_date is 2025-08-27 and latest is 2025-09-13: has_update = true

Example of GOOD document_url (AMENDMENT documents):
- https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/upd1/final/sp800-53r5-upd1.pdf (amendment)
- https://example.com/downloads/framework-amendment-2025.pdf (amendment)
- https://example.com/updates/changes-to-framework.pdf (amendment)

Example of BAD document_url (DO NOT USE):
- https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final/sp800-53r5.pdf (full framework, too large)
- https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final (this is a webpage, not a PDF)
- https://example.com/pages/document (this is an HTML page)
- Any URL to the complete/full framework document (these are too large)"""


def _clean_response_content(content: str) -> str:
    """Remove markdown fences and return raw JSON string."""
    import re
    
    # First, try to extract JSON from markdown code blocks
    if "```json" in content:
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
    if "```" in content:
        json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
    
    # Try to find JSON object in the text (handles cases where JSON is embedded in text)
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
    if json_match:
        return json_match.group(0).strip()
    
    # If no JSON found, return the content as-is (will fail gracefully)
    return content.strip()


def query_perplexity_api(framework_name: str, last_updated_date: str, api_key: str) -> dict:
    """Call Perplexity API and return parsed JSON response."""
    if not api_key:
        raise ValueError("Perplexity API key is required")

    system_prompt = create_system_prompt(framework_name, last_updated_date)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are a JSON-only API. You MUST respond with ONLY valid JSON. No explanations, no markdown, no code blocks. Just the JSON object."
            },
            {
                "role": "user",
                "content": (
                    f"{system_prompt}\n\n"
                    f"TASK: Check if {framework_name} has been updated after {last_updated_date} and find the DIRECT PDF download link.\n\n"
                    f"SEARCH INSTRUCTIONS - Be THOROUGHLY:\n"
                    f"1. Search the official {framework_name} website/documentation portal\n"
                    f"2. Search for 'download PDF', 'PDF download', 'amendment PDF', 'update PDF', 'change document PDF'\n"
                    f"3. Check document libraries, publication pages, download sections, archives\n"
                    f"4. Look for direct file links ending in .pdf\n"
                    f"5. Search for 'Summary of Changes PDF', 'What's New PDF', 'Update Document PDF'\n"
                    f"6. Check release notes, changelogs, update announcements for PDF links\n"
                    f"7. Search multiple sources: official websites, standards organizations, document repositories\n"
                    f"8. Look in both current pages AND archive/history pages\n"
                    f"9. Search for version numbers, update numbers, amendment numbers combined with PDF\n\n"
                    f"IMPORTANT:\n"
                    f"- Find the DIRECT PDF download link for the LATEST AMENDMENT document (NOT the full framework)\n"
                    f"- Amendment documents are typically small PDFs (10-100 pages) that describe changes\n"
                    f"- DO NOT use the full framework document (which is large, 200+ pages)\n"
                    f"- The document_url MUST be a direct PDF file URL (ending in .pdf), NOT a webpage\n"
                    f"- If you find ANY PDF URL that could be the amendment, include it\n"
                    f"- Search THOROUGHLY - check multiple pages, sections, and sources\n\n"
                    f"REMEMBER: Respond with ONLY the JSON object, nothing else."
                ),
            }
        ],
        "temperature": 0.1,
        "max_tokens": 800,
    }

    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json=payload,
        timeout=45,
    )
    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # Log raw response for debugging
    import logging
    import re
    logger = logging.getLogger(__name__)
    logger.info(f"Perplexity API raw response for {framework_name}: {content[:500]}...")
    
    # Try to parse JSON from the response
    cleaned_content = _clean_response_content(content)
    parsed = None
    
    try:
        parsed = json.loads(cleaned_content)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON directly: {str(e)}")
        # Try multiple JSON extraction strategies
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested JSON
            r'\{.*?"has_update".*?\}',  # JSON with has_update field
            r'\{.*?"document_url".*?\}',  # JSON with document_url field
            r'\{[^}]*"framework_name"[^}]*"has_update"[^}]*"latest_update_date"[^}]*"document_url"[^}]*\}',  # Complete JSON structure
        ]
        
        for pattern in json_patterns:
            json_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    # Try to fix common JSON issues
                    json_str = json_str.replace("'", '"')  # Replace single quotes
                    json_str = re.sub(r'(\w+):', r'"\1":', json_str)  # Add quotes to keys
                    parsed = json.loads(json_str)
                    logger.info("Successfully extracted JSON from text response using pattern matching")
                    break
                except (json.JSONDecodeError, AttributeError):
                    continue
        
        if not parsed:
            logger.warning("All JSON extraction attempts failed")
        
        # If still no JSON, create a default response based on text content
        if parsed is None:
            logger.warning("Could not parse JSON from Perplexity response. Analyzing text content for updates...")
            
            # More comprehensive update detection
            content_lower = content.lower()
            
            # Strong indicators of an update
            strong_update_indicators = [
                'has been updated', 'was updated', 'latest update', 'recent update',
                'new version', 'new amendment', 'latest amendment', 'recent amendment',
                'updated on', 'published on', 'released on', 'issued on',
                'version', 'amendment', 'update', 'revision', 'supplement'
            ]
            
            # Check for update mentions
            has_update_mention = any(indicator in content_lower for indicator in strong_update_indicators)
            
            # Try to extract URL from text (multiple patterns)
            document_url = None
            url_patterns = [
                r'https?://[^\s<>"{}|\\^`\[\]]+\.pdf',  # Standard PDF URL
                r'https?://[^\s<>"{}|\\^`\[\]]+\.pdf[^\s<>"{}|\\^`\[\]]*',  # PDF URL with query params
                r'https?://[^\s<>"{}|\\^`\[\]]+download[^\s<>"{}|\\^`\[\]]*\.pdf',  # Download PDF
                r'https?://[^\s<>"{}|\\^`\[\]]+pdf[^\s<>"{}|\\^`\[\]]*',  # Contains pdf
            ]
            
            for pattern in url_patterns:
                url_match = re.search(pattern, content, re.IGNORECASE)
                if url_match:
                    document_url = url_match.group(0).strip()
                    # Clean up URL (remove trailing punctuation)
                    document_url = re.sub(r'[.,;:!?)\]]+$', '', document_url)
                    break
            
            # Try to extract date from text (multiple formats)
            latest_date = None
            date_patterns = [
                r'\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b',  # YYYY-MM-DD or YYYY/MM/DD
                r'\b(\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b',  # MM-DD-YYYY or DD-MM-YYYY
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}\b',  # Month DD, YYYY
                r'\b(20\d{2})\b',  # Just year
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, content, re.IGNORECASE)
                if date_match:
                    date_str = date_match.group(0)
                    # Try to normalize to YYYY-MM-DD format
                    try:
                        if '/' in date_str:
                            parts = date_str.split('/')
                            if len(parts) == 3:
                                if len(parts[0]) == 4:  # YYYY/MM/DD
                                    latest_date = date_str.replace('/', '-')
                                else:  # MM/DD/YYYY
                                    latest_date = f"{parts[2]}-{parts[0]}-{parts[1]}"
                        elif '-' in date_str:
                            latest_date = date_str
                        else:
                            # Try parsing month name
                            # Try manual parsing for common formats
                            if any(month in date_str for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']):
                                # Month name format - try to extract
                                month_map = {
                                    'january': '01', 'february': '02', 'march': '03', 'april': '04',
                                    'may': '05', 'june': '06', 'july': '07', 'august': '08',
                                    'september': '09', 'october': '10', 'november': '11', 'december': '12'
                                }
                                for month_name, month_num in month_map.items():
                                    if month_name in date_str.lower():
                                        # Extract year and day
                                        year_match = re.search(r'20\d{2}', date_str)
                                        day_match = re.search(r'\b(\d{1,2})\b', date_str)
                                        if year_match and day_match:
                                            latest_date = f"{year_match.group(0)}-{month_num}-{day_match.group(1).zfill(2)}"
                                            break
                    except:
                        # If parsing fails, use as-is if it looks like a date
                        if re.match(r'\d{4}', date_str):
                            latest_date = date_str
                    if latest_date:
                        break
            
            # Determine if there's an update
            # PRIORITY: If we found a PDF URL, assume there's an update (most reliable indicator)
            has_update = False
            
            if document_url:
                # If we found a PDF URL, it's very likely an update exists
                has_update = True
                logger.info(f"Found PDF URL ({document_url}), assuming update exists")
                
                # If we also have a date, verify it's after last_updated_date
                if latest_date:
                    try:
                        # Normalize date format
                        if '/' in latest_date:
                            latest_date = latest_date.replace('/', '-')
                        # Handle different date formats
                        date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y"]
                        latest_date_obj = None
                        for fmt in date_formats:
                            try:
                                latest_date_obj = datetime.strptime(latest_date, fmt).date()
                                break
                            except ValueError:
                                continue
                        
                        if latest_date_obj:
                            last_known_obj = datetime.strptime(last_updated_date, "%Y-%m-%d").date()
                            if latest_date_obj <= last_known_obj:
                                logger.warning(f"Date comparison: latest={latest_date_obj} <= last_known={last_known_obj}, but PDF URL found - keeping has_update=True")
                            else:
                                logger.info(f"Date comparison confirms update: latest={latest_date_obj} > last_known={last_known_obj}")
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Could not parse date for comparison: {e}, but PDF URL found - keeping has_update=True")
            elif latest_date:
                # No PDF URL but we have a date - compare dates
                try:
                    # Normalize date format
                    if '/' in latest_date:
                        latest_date = latest_date.replace('/', '-')
                    date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y"]
                    latest_date_obj = None
                    for fmt in date_formats:
                        try:
                            latest_date_obj = datetime.strptime(latest_date, fmt).date()
                            break
                        except ValueError:
                            continue
                    
                    if latest_date_obj:
                        last_known_obj = datetime.strptime(last_updated_date, "%Y-%m-%d").date()
                        has_update = latest_date_obj > last_known_obj
                        logger.info(f"Date comparison: latest={latest_date_obj}, last_known={last_known_obj}, has_update={has_update}")
                    else:
                        # Date parsing failed, use heuristics
                        has_update = has_update_mention
                except (ValueError, AttributeError):
                    # If date parsing fails, use heuristics
                    has_update = has_update_mention
            else:
                # No PDF URL and no date - use heuristics
                has_update = has_update_mention
                logger.info(f"No PDF URL or date found, using heuristics: has_update={has_update}")
            
            parsed = {
                'has_update': has_update,
                'latest_update_date': latest_date or last_updated_date,
                'document_url': document_url,
                'version': None,
                'notes': content[:300] if len(content) > 300 else content
            }
            logger.info(f"Created default response from text analysis: has_update={parsed.get('has_update')}, latest_date={parsed.get('latest_update_date')}, document_url={parsed.get('document_url')}")
    
    if parsed:
        logger.info(f"Parsed update info: has_update={parsed.get('has_update')}, latest_update_date={parsed.get('latest_update_date')}, document_url={parsed.get('document_url')}")
    else:
        # Final fallback - return no update
        logger.error("Could not parse Perplexity response. Returning no update.")
        parsed = {
            'has_update': False,
            'latest_update_date': last_updated_date,
            'document_url': None,
            'version': None,
            'notes': 'Failed to parse API response'
        }

    # Validate date ordering per business rules
    # BUT: If we have a PDF URL, don't override has_update based on date alone
    # (PDF URL is a strong indicator of an update)
    if parsed.get("has_update") and parsed.get("latest_update_date"):
        try:
            latest_date_str = parsed["latest_update_date"]
            # Try multiple date formats
            date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y"]
            latest_date = None
            for fmt in date_formats:
                try:
                    latest_date = datetime.strptime(latest_date_str, fmt).date()
                    break
                except ValueError:
                    continue
            
            if latest_date:
                last_known = datetime.strptime(last_updated_date, "%Y-%m-%d").date()
                # Only override if date is clearly before AND we don't have a PDF URL
                # (PDF URL is a strong signal that an update exists)
                if latest_date <= last_known and not parsed.get("document_url"):
                    logger.warning(f"Date validation: latest={latest_date} <= last_known={last_known}, no PDF URL - setting has_update=False")
                    parsed["has_update"] = False
                elif latest_date <= last_known and parsed.get("document_url"):
                    logger.info(f"Date validation: latest={latest_date} <= last_known={last_known}, but PDF URL exists - keeping has_update=True")
        except (ValueError, AttributeError) as e:
            # If date parsing fails but we have a PDF URL, keep has_update as True
            if not parsed.get("document_url"):
                logger.warning(f"Date validation failed: {e}, no PDF URL - setting has_update=False")
                parsed["has_update"] = False
            else:
                logger.info(f"Date validation failed: {e}, but PDF URL exists - keeping has_update=True")
    
    # Validate document_url - must be a PDF URL
    doc_url = parsed.get("document_url")
    if doc_url:
        # Check if it's a valid PDF URL
        if not doc_url.lower().endswith('.pdf'):
            logger.warning(f"document_url from Perplexity is not a PDF URL: {doc_url}. Will attempt to find PDF link.")
            # Keep the URL so we can try to find the PDF from it
        else:
            logger.info(f"document_url appears to be a valid PDF URL: {doc_url}")

    return parsed


def find_actual_pdf_url(page_url: str, framework_name: str, api_key: str) -> Optional[str]:
    """Use Perplexity to find the actual PDF download link from a page for the latest amendment"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "user",
                "content": f"""Find the DIRECT PDF download link for the LATEST AMENDMENT of {framework_name} from this page: {page_url}

CRITICAL REQUIREMENTS:
1. Find the ACTUAL downloadable AMENDMENT PDF file link (MUST end with .pdf)
2. You are looking for AMENDMENT documents (small PDFs, 10-100 pages), NOT the full framework document
3. Amendment documents are typically titled: "Amendment to...", "Update to...", "Changes to...", "Revision..."
4. The URL must be a direct link to a PDF file, NOT a webpage or HTML page
5. Look specifically for the LATEST AMENDMENT PDF download link (small document, not full framework)
6. Search for links containing words like: "amendment", "update", "changes", "revision", "supplement"
7. Search for links like "Download Amendment PDF", "View Update PDF", "PDF Download", or direct .pdf file URLs
8. The URL should look like: https://example.com/amendment.pdf or https://example.com/downloads/update-2025.pdf
9. Do NOT return page URLs like https://example.com/pages/document (these are HTML pages)
10. Do NOT return URLs to full framework documents (these are too large, 200+ pages)
11. If multiple PDFs exist, return the PDF for the LATEST AMENDMENT only (smallest/shortest document)
12. Return ONLY the direct PDF URL, nothing else

Examples of GOOD AMENDMENT PDF URLs:
- https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/upd1/final/sp800-53r5-upd1.pdf (amendment)
- https://example.com/downloads/framework-amendment-2025.pdf (amendment)
- https://example.com/updates/changes-to-framework.pdf (amendment)

Examples of BAD URLs (DO NOT USE):
- https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final/sp800-53r5.pdf (full framework, too large)
- https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final (this is a webpage)
- https://example.com/pages/document (this is an HTML page)
- Any URL to the complete/full framework document (these are too large)

Respond with ONLY the PDF URL or "NOT_FOUND" if no direct AMENDMENT PDF download link exists."""
            }
        ],
        "temperature": 0.1,
        "max_tokens": 300
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
                urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+\.pdf', pdf_url)
                if urls:
                    return urls[0]
        
        return None
        
    except Exception as e:
        return None


def download_document(
    framework_name: str,
    document_url: str,
    download_dir: str,
    api_key: Optional[str] = None,
    store_in_media: bool = True,
) -> Optional[str]:
    """Download framework document - uses robust logic from framework_testing.py"""
    import logging
    logger = logging.getLogger(__name__)
    
    if not document_url:
        logger.warning("No document_url provided for download")
        return None
    
    # If store_in_media is True, use MEDIA_ROOT/change_management/
    if store_in_media:
        from django.conf import settings
        download_dir = os.path.join(settings.MEDIA_ROOT, 'change_management')
        logger.info(f"Storing document in MEDIA_ROOT/change_management/: {download_dir}")
    
    # Create download directory
    os.makedirs(download_dir, exist_ok=True)
    logger.info(f"Download directory: {download_dir}")
    
    def _attempt_download(url: str, headers: dict = None):
        """Attempt to download with proper headers and error handling"""
        logger.info(f"Downloading from: {url}")
        
        # Default headers to mimic a browser request
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # Merge with any provided headers
        if headers:
            default_headers.update(headers)
        
        # Create a session to maintain cookies
        session = requests.Session()
        session.headers.update(default_headers)
        
        try:
            resp = session.get(url, stream=True, timeout=60, allow_redirects=True)
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(f"403 Forbidden - URL may require authentication or have access restrictions: {url}")
                # Try with different headers
                logger.info("Retrying with alternative headers...")
                alt_headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': '/'.join(url.split('/')[:3]) + '/',  # Base URL as referer
                }
                try:
                    resp = session.get(url, stream=True, timeout=60, allow_redirects=True, headers=alt_headers)
                    resp.raise_for_status()
                    return resp
                except:
                    raise e
            else:
                raise
        finally:
            session.close()
    
    try:
        url_to_fetch = document_url
        logger.info(f"Attempting to download from URL: {document_url}")
        
        # Validate URL - must be a direct PDF link
        if not document_url.lower().endswith('.pdf'):
            logger.info("URL does not end with .pdf, attempting to find direct PDF link for latest amendment...")
            if api_key:
                # Try to find the actual PDF download link
                direct_pdf_url = find_actual_pdf_url(document_url, framework_name, api_key)
                if direct_pdf_url and direct_pdf_url.lower().endswith('.pdf') and direct_pdf_url != "NOT_FOUND":
                    logger.info(f"Found direct PDF URL: {direct_pdf_url}")
                    url_to_fetch = direct_pdf_url
                else:
                    logger.warning("Could not find direct PDF download link for the latest amendment. PDF document is not available.")
                    return None
            else:
                logger.warning("No API key provided to search for PDF URL. PDF document is not available for download.")
                return None
        else:
            # URL ends with .pdf, but verify it's actually a PDF URL (not a redirect)
            logger.info("URL appears to be a PDF link, proceeding with download...")
        
        # Try to download the file, with fallback if the direct link fails
        response = None
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries and response is None:
            try:
                response = _attempt_download(url_to_fetch)
                break  # Success, exit retry loop
            except requests.exceptions.HTTPError as http_err:
                status_code = http_err.response.status_code if hasattr(http_err, 'response') else None
                logger.error(f"HTTP error downloading {url_to_fetch}: {http_err} (Status: {status_code})")
                
                # If 403 Forbidden, try to find alternate URL
                if status_code == 403 and api_key and retry_count < max_retries - 1:
                    logger.info(f"403 Forbidden - Attempting to locate alternate PDF URL via Perplexity (attempt {retry_count + 1}/{max_retries})...")
                    alternate_url = find_actual_pdf_url(document_url, framework_name, api_key)
                    if alternate_url and alternate_url.lower().endswith('.pdf') and alternate_url != url_to_fetch:
                        logger.info(f"Alternate PDF URL found: {alternate_url}")
                        url_to_fetch = alternate_url
                        retry_count += 1
                        continue  # Retry with new URL
                    else:
                        logger.warning("No alternate PDF URL found via Perplexity")
                        if retry_count < max_retries - 1:
                            retry_count += 1
                            import time
                            time.sleep(2)  # Wait before retry
                            continue
                
                # If we've exhausted retries or it's not a 403, raise the error
                if retry_count >= max_retries - 1:
                    logger.error(f"Failed to download after {max_retries} attempts. Last error: {http_err}")
                    raise
                retry_count += 1
                
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Request error downloading {url_to_fetch}: {req_err}")
                if retry_count >= max_retries - 1:
                    raise
                retry_count += 1
                import time
                time.sleep(2 ** retry_count)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error during download attempt: {str(e)}")
                if retry_count >= max_retries - 1:
                    raise
                retry_count += 1
                import time
                time.sleep(2)
        
        # Check if we actually got a PDF
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"Response content-type: {content_type}")
        
        # Create temporary filename for download
        safe_name = framework_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filepath = os.path.join(download_dir, f"{safe_name}_{timestamp}.tmp")
        
        # Download file first to check if it's actually a PDF
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        logger.info(f"Downloading {total_size} bytes to temporary file: {temp_filepath}")
        
        with open(temp_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        logger.info(f"Downloaded {downloaded} bytes to temporary file")
        
        # Verify it's actually a PDF by checking magic number
        try:
            with open(temp_filepath, 'rb') as f:
                first_bytes = f.read(4)
                if first_bytes != b'%PDF':
                    # Not a PDF file, delete it and return None
                    os.remove(temp_filepath)
                    logger.warning(f"Downloaded file is not a PDF (magic number: {first_bytes}). PDF document is not available.")
                    return None
        except Exception as e:
            # If we can't read the file, delete it and return None
            try:
                os.remove(temp_filepath)
            except:
                pass
            logger.warning(f"Could not verify PDF file: {str(e)}. PDF document is not available.")
            return None
        
        # Check file size - amendments are typically smaller (1-15 MB), full frameworks are large (20+ MB)
        file_size_mb = downloaded / (1024 * 1024)
        MAX_AMENDMENT_SIZE_MB = 15  # Amendments are typically 1-15 MB
        
        if file_size_mb > MAX_AMENDMENT_SIZE_MB:
            # File is too large, likely the full framework document, not an amendment
            os.remove(temp_filepath)
            logger.warning(f"Downloaded PDF is too large ({file_size_mb:.2f} MB). This appears to be the full framework document, not an amendment. Amendments are typically 1-15 MB. PDF document is not available.")
            return None
        
        logger.info(f"PDF file size: {file_size_mb:.2f} MB (acceptable for amendment document)")
        
        # It's a valid PDF and size is appropriate for an amendment, rename to .pdf extension
        filename = f"{safe_name}_{timestamp}.pdf"
        filepath = os.path.join(download_dir, filename)
        os.rename(temp_filepath, filepath)
        
        logger.info(f"Successfully downloaded amendment PDF: {filepath} ({downloaded} bytes, {file_size_mb:.2f} MB)")
        
        # Upload to S3 after successful download
        try:
            from grc.routes.Global.s3_fucntions import create_direct_mysql_client
            from django.conf import settings
            
            logger.info("Uploading document to S3...")
            s3_client = create_direct_mysql_client()
            
            # Get user_id from settings or use default
            user_id = getattr(settings, 'DEFAULT_USER_ID', 'system')
            
            # Upload to S3 with changemanagement module
            upload_result = s3_client.upload(
                file_path=filepath,
                user_id=user_id,
                custom_file_name=filename,
                module='changemanagement'
            )
            
            if upload_result.get('success'):
                s3_url = upload_result['file_info']['url']
                logger.info(f"Successfully uploaded to S3: {s3_url}")
                # Return both local path and S3 URL as a dict
                return {
                    'local_path': filepath,
                    's3_url': s3_url,
                    's3_key': upload_result['file_info'].get('s3Key', ''),
                    'stored_name': upload_result['file_info'].get('storedName', filename)
                }
            else:
                logger.warning(f"Failed to upload to S3: {upload_result.get('error')}")
                # Return just local path if S3 upload fails
                return filepath
                
        except Exception as s3_error:
            logger.error(f"Error uploading to S3: {str(s3_error)}")
            import traceback
            logger.error(traceback.format_exc())
            # Return local path even if S3 upload fails
            return filepath
        
    except requests.exceptions.HTTPError as http_err:
        status_code = http_err.response.status_code if hasattr(http_err, 'response') else None
        if status_code == 403:
            logger.error(f"403 Forbidden - Document requires authentication or has access restrictions: {document_url}")
            logger.info("This PDF may require:")
            logger.info("  1. User authentication/login")
            logger.info("  2. Subscription or membership")
            logger.info("  3. Manual download from the website")
            logger.info(f"Please visit the URL manually: {document_url}")
        else:
            logger.error(f"HTTP error downloading document: {http_err} (Status: {status_code})")
        import traceback
        logger.error(traceback.format_exc())
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error downloading document: {str(e)}")
        logger.info(f"Please try downloading manually from: {document_url}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading document: {str(e)}")
        logger.info(f"Please try downloading manually from: {document_url}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def run_framework_update_check(
    framework_name: str,
    last_updated_date: str,
    api_key: str,
    download_dir: Optional[str] = None,
    framework_id: Optional[int] = None,
    process_amendment: bool = False,
    store_in_media: bool = True,
) -> dict:
    """
    Run the Perplexity check for a framework.

    Args:
        framework_name: Name of the framework
        last_updated_date: Last known update date (YYYY-MM-DD)
        api_key: Perplexity API key
        download_dir: Directory to save downloaded documents (ignored if store_in_media=True)
        framework_id: Framework ID for processing (optional)
        process_amendment: Whether to process the downloaded amendment (default: False)
        store_in_media: Whether to store in MEDIA_ROOT/change_management/ (default: True)

    Returns:
        dict with keys: has_update, latest_update_date, document_url, version,
        notes, downloaded_path (optional), processing_result (optional)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    download_folder = download_dir or "downloads"
    update_info = query_perplexity_api(framework_name, last_updated_date, api_key)

    downloaded_path = None
    downloaded_info = None  # Will contain S3 info if available
    processing_result = None
    
    # Log the update check results
    logger.info(f"Update check results for {framework_name}: has_update={update_info.get('has_update')}, document_url={update_info.get('document_url')}")
    
    if update_info.get("has_update") and update_info.get("document_url"):
        logger.info(f"Attempting to download document from: {update_info['document_url']}")
        try:
            download_result = download_document(
                framework_name,
                update_info["document_url"],
                download_folder,
                api_key=api_key,
                store_in_media=store_in_media,
            )
            
            if download_result:
                # Handle both dict (with S3 info) and string (local path only) returns
                if isinstance(download_result, dict):
                    downloaded_path = download_result.get('local_path')
                    downloaded_info = download_result
                    logger.info(f"Successfully downloaded and uploaded to S3: {downloaded_info.get('s3_url')}")
                else:
                    downloaded_path = download_result
                    logger.info(f"Successfully downloaded amendment document for {framework_name} to {downloaded_path}")
                
                # Only process the downloaded amendment if explicitly requested
                # Note: By default, we now wait for manual trigger via "Start Analysis" button
                if process_amendment and framework_id and downloaded_path and downloaded_path.lower().endswith('.pdf'):
                    try:
                        from .amendment_processor import process_downloaded_amendment
                        
                        logger.info(f"Starting amendment processing for {framework_name}")
                        
                        # Use the download directory as the output directory for processing
                        output_dir = download_dir if download_dir else os.path.dirname(downloaded_path)
                        
                        processing_result = process_downloaded_amendment(
                            pdf_path=downloaded_path,
                            framework_name=framework_name,
                            framework_id=framework_id,
                            amendment_date=update_info.get('latest_update_date', last_updated_date),
                            output_dir=output_dir
                        )
                        
                        if processing_result.get('success'):
                            logger.info(f"Successfully processed amendment: {processing_result.get('output_file')}")
                        else:
                            logger.error(f"Amendment processing failed: {processing_result.get('error')}")
                            
                    except Exception as e:
                        logger.error(f"Error processing amendment: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
                        processing_result = {
                            'success': False,
                            'error': str(e)
                        }
            else:
                logger.warning(f"Download failed or returned None for {framework_name}. document_url was: {update_info.get('document_url')}")
                        
        except Exception as e:
            logger.error(f"Error downloading document for {framework_name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            downloaded_path = None
    else:
        if not update_info.get("has_update"):
            logger.info(f"No update found for {framework_name} (has_update=False)")
        elif not update_info.get("document_url"):
            logger.warning(f"Update found for {framework_name} but no document_url provided")

    result = {
        **update_info,
        "downloaded_path": downloaded_path,
    }
    
    # Add S3 information if available
    if downloaded_info and isinstance(downloaded_info, dict):
        result["s3_url"] = downloaded_info.get('s3_url')
        result["s3_key"] = downloaded_info.get('s3_key')
        result["s3_stored_name"] = downloaded_info.get('stored_name')
    
    if processing_result:
        result["processing_result"] = processing_result
    
    return result

