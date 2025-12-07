"""
AI-Powered Risk Instance Document Ingestion (Complete)
- Reads PDF/DOCX/XLSX/TXT
- Extracts risk instance data using OpenAI (GPT models)
- Fills missing fields with focused prompts
- Returns normalized, DB-ready JSON for `risk_instance` table
"""

import os
import re
import json
import time
import tempfile
from datetime import date, datetime
from typing import Any, Optional

import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

# RBAC imports
from ...rbac.decorators import rbac_required

# --- Optional parsers (install as needed) ---
try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    import docx  # python-docx
except Exception:
    docx = None

try:
    import pandas as pd
except Exception:
    pd = None

# --- Your models ---
from grc.models import RiskInstance  # Import RiskInstance model


# =========================
# OPENAI CONFIG
# =========================
# OpenAI API Configuration - Use Django settings
from django.conf import settings
OPENAI_API_KEY = getattr(settings, 'OPENAI_API_KEY', None)
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')

if not OPENAI_API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY not found in Django settings!")
    print("   Please set OPENAI_API_KEY in your .env file.")
else:
    print(f"🌐 OpenAI Configuration for Risk Instance AI:")
    print(f"   API URL: {OPENAI_API_URL}")
    print(f"   Model: {OPENAI_MODEL}")
    print(f"   API Key: {'*' * (len(OPENAI_API_KEY) - 4) + OPENAI_API_KEY[-4:]}")

# RiskInstance DB fields (excluding auto-generated IDs: RiskInstanceId, UserId, ReportedBy, ReviewerId, IncidentId, ComplianceId, RiskId)
RISK_INSTANCE_DB_FIELDS = [
    "RiskTitle",
    "RiskDescription",
    "PossibleDamage",
    "RiskPriority",
    "Criticality",
    "Category",
    "Origin",
    "RiskLikelihood",
    "RiskImpact",
    "RiskExposureRating",
    "RiskMultiplierX",
    "RiskMultiplierY",
    "Appetite",
    "RiskResponseType",
    "RiskResponseDescription",
    "RiskMitigation",
    "RiskType",
    "RiskOwner",
    "BusinessImpact",
    "RiskStatus",
    "MitigationStatus",
    "ModifiedMitigations",
    "RiskFormDetails",
    "Reviewer",
]

# Canonical choices / constraints to stabilize LLM outputs
CRITICALITY_CHOICES = ["Low", "Medium", "High", "Critical"]
PRIORITY_CHOICES = ["Low", "Medium", "High", "Critical"]
CATEGORY_HINTS = [
    "Operational", "Financial", "Strategic", "Compliance", "Technical",
    "Reputational", "Information Security", "Process Risk", "Third-Party",
    "Regulatory", "Governance"
]
RISKTYPE_HINTS = ["Current", "Residual", "Inherent", "Emerging", "Accepted"]
ORIGIN_HINTS = ["Internal", "External", "Third-Party", "Regulatory", "Market", "Operational"]
APPETITE_HINTS = ["Low", "Medium", "High"]
RESPONSE_TYPE_HINTS = ["Avoid", "Mitigate", "Transfer", "Accept"]
RISK_STATUS_CHOICES = ["Not Assigned", "Assigned", "Approved", "Rejected"]
MITIGATION_STATUS_CHOICES = ["Pending", "Yet to Start", "Work In Progress", "Revision Required by Reviewer", "Revision Required by User", "Completed"]
DATE_FORMAT_HINT = "YYYY-MM-DD (ISO)"

# Field-specific micro-prompts (used when a single field is missing/invalid)
# NOTE: RiskTitle is NEVER inferred by AI - it must always come from the document
FIELD_PROMPTS = {
    "RiskDescription": "Write a precise, detailed description (2–4 sentences) of how/why the risk instance occurred, what happened, when it happened, and who was affected. Include specific details about the incident.",
    "PossibleDamage": "Describe concrete, specific damages that occurred or could occur (data loss volume, downtime duration, financial penalties, reputation impact). Be detailed and quantitative where possible (2–3 sentences).",
    "RiskPriority": f"Return one of: {PRIORITY_CHOICES}. Analyze the severity based on exposure, criticality, business impact, and urgency. Consider both likelihood and potential damage.",
    "Criticality": f"Return one of: {CRITICALITY_CHOICES}. Consider the severity of impact on business operations, compliance requirements, financial impact, and reputational damage.",
    "Category": f"Return one category from this list (best fit): {CATEGORY_HINTS}. Analyze the nature of the risk and choose the most appropriate category based on the root cause and impact area.",
    "Origin": f"Return one of: {ORIGIN_HINTS}. Identify where the risk originated from - was it internal processes, external threats, third-party vendors, regulatory changes, or market conditions?",
    "RiskLikelihood": "Return an integer 1–10 (1=rare/almost never, 5=possible/moderate, 10=almost certain/very frequent). Base this on historical data, environmental factors, and current controls.",
    "RiskImpact": "Return an integer 1–10 (1=negligible/minimal, 5=moderate/noticeable, 10=catastrophic/severe). Consider financial, operational, reputational, and compliance impacts.",
    "RiskExposureRating": "Return a float (0–100) representing overall risk exposure. Calculate as: (Likelihood × Impact × average of multipliers). Higher values indicate greater exposure.",
    "RiskMultiplierX": "Return a float in 0.1–2.0 reflecting organizational weighting factor X for likelihood adjustment based on industry, size, or environmental factors (default ~1.0 if unknown).",
    "RiskMultiplierY": "Return a float in 0.1–2.0 reflecting organizational weighting factor Y for impact adjustment based on risk tolerance and organizational resilience (default ~1.0 if unknown).",
    "Appetite": f"Return one of: {APPETITE_HINTS}. Determine the organization's tolerance level for this type of risk based on strategic objectives, regulatory requirements, and industry standards.",
    "RiskResponseType": f"Return one of: {RESPONSE_TYPE_HINTS}. Choose the most appropriate response: Avoid (eliminate risk), Mitigate (reduce likelihood/impact), Transfer (insurance/outsource), Accept (acknowledge and monitor).",
    "RiskResponseDescription": "Provide a detailed 2-3 sentence description of the chosen risk response strategy, explaining specific actions, rationale, timeline, and expected outcomes.",
    "RiskMitigation": "Return 3–5 specific, actionable mitigation steps as a JSON array of objects with 'step' (action title) and 'description' (detailed implementation) fields. Each step should be practical, measurable, and time-bound. Example: [{\"step\": \"Implement Multi-Factor Authentication\", \"description\": \"Deploy MFA across all user accounts within 30 days to prevent unauthorized access\"}]",
    "RiskType": f"Return one of: {RISKTYPE_HINTS}. Current=existing risk, Residual=risk after controls, Inherent=risk before controls, Emerging=newly identified, Accepted=acknowledged without action.",
    "RiskOwner": "Return the specific name, role, or department responsible for managing this risk instance (e.g., 'John Smith - IT Security Manager', 'Compliance Department', 'Chief Risk Officer'). Be specific.",
    "BusinessImpact": "Provide a detailed 2-4 sentence explanation of business impact using business terms: revenue loss, SLA breaches, customer churn, regulatory penalties, operational disruption, market share impact, brand reputation damage. Include quantitative estimates where possible.",
    "RiskStatus": f"Return one of: {RISK_STATUS_CHOICES}. Assess the current state: Not Assigned (new, unassigned), Assigned (owner designated), Approved (accepted by management), Rejected (dismissed as non-risk).",
    "MitigationStatus": f"Return one of: {MITIGATION_STATUS_CHOICES}. Determine progress: Pending (awaiting action), Yet to Start (planned but not begun), Work In Progress (actively being addressed), Revision Required by Reviewer (needs reviewer changes), Revision Required by User (needs user changes), Completed (fully implemented).",
    "ModifiedMitigations": "Return a JSON array documenting any changes made to original mitigation plans. Format: [{\"date\": \"YYYY-MM-DD\", \"changed_by\": \"Name/Role\", \"changes\": \"Description of modifications\", \"reason\": \"Why changes were needed\"}]. Return empty array [] if no modifications yet.",
    "RiskFormDetails": "Return a JSON object containing additional structured risk assessment details. Format: {\"assessment_method\": \"Qualitative/Quantitative/Mixed\", \"data_sources\": [\"source1\", \"source2\"], \"stakeholders_consulted\": [\"person1\", \"person2\"], \"assessment_date\": \"YYYY-MM-DD\", \"next_review_date\": \"YYYY-MM-DD\", \"additional_notes\": \"Any relevant notes\"}. Infer reasonable values based on context.",
    "Reviewer": "Return the name or role of the person who reviewed/approved this risk instance (e.g., 'Sarah Johnson', 'Senior Risk Analyst', 'Compliance Manager'). Default to 'Pending Review' if not yet reviewed.",
}

# Strict JSON schema block the LLM must follow
STRICT_SCHEMA_BLOCK = f"""
CRITICAL: Return ONLY a valid JSON array. No markdown, no code blocks, no explanations.
Start with [ and end with ]. Use proper JSON syntax with double quotes.

Example structure (return array of risk instances like this):
[
  {{
    "RiskTitle": "Specific risk instance title here",
    "RiskDescription": "Detailed description of the risk instance occurrence",
    "PossibleDamage": "Concrete description of damages",
    "RiskPriority": "Medium",
    "Criticality": "Medium",
    "Category": "Operational",
    "Origin": "Internal",
    "RiskLikelihood": 5,
    "RiskImpact": 6,
    "RiskExposureRating": 30.0,
    "RiskMultiplierX": 1.0,
    "RiskMultiplierY": 1.0,
    "Appetite": "Medium",
    "RiskResponseType": "Mitigate",
    "RiskResponseDescription": "Detailed response strategy description",
    "RiskMitigation": [{{"step": "Step 1", "description": "Detailed action description"}}],
    "RiskType": "Current",
    "RiskOwner": "Risk Manager Name/Role",
    "BusinessImpact": "Detailed business impact explanation",
    "RiskStatus": "Not Assigned",
    "MitigationStatus": "Pending",
    "ModifiedMitigations": [],
    "RiskFormDetails": {{"assessment_method": "Qualitative", "data_sources": ["Document"], "assessment_date": "{date.today().isoformat()}"}},
    "Reviewer": "Pending Review",
    "_meta": {{
      "per_field": {{
        "RiskTitle": {{"source": "EXTRACTED", "confidence": 0.9, "rationale": "Found explicitly in document"}},
        "Criticality": {{"source": "AI_GENERATED", "confidence": 0.7, "rationale": "Inferred from severity indicators"}},
        "RiskLikelihood": {{"source": "AI_GENERATED", "confidence": 0.6, "rationale": "Estimated based on frequency mentions"}}
      }}
    }}
  }}
]

Rules:
- Criticality must be: {CRITICALITY_CHOICES}
- RiskPriority must be: {PRIORITY_CHOICES}
- RiskLikelihood and RiskImpact must be integers 1-10
- RiskExposureRating must be float 0-100
- RiskMultiplierX and RiskMultiplierY must be floats 0.1-2.0
- RiskMitigation must be a JSON array of objects with "step" and "description"
- ModifiedMitigations must be a JSON array (empty [] if no modifications)
- RiskFormDetails must be a JSON object
- RiskStatus must be one of: {RISK_STATUS_CHOICES}
- MitigationStatus must be one of: {MITIGATION_STATUS_CHOICES}
- Appetite must be one of: {APPETITE_HINTS}
- RiskResponseType must be one of: {RESPONSE_TYPE_HINTS}
- Origin must be one of: {ORIGIN_HINTS}
- RiskType must be one of: {RISKTYPE_HINTS}
- NO trailing commas
- NO comments in JSON
- Return ONLY the JSON array, nothing else
- Include _meta.per_field for EVERY field showing source (EXTRACTED or AI_GENERATED), confidence (0.0-1.0), and rationale
"""

# =========================
# UTILITIES / VALIDATORS
# =========================
def _json_from_llm_text(text: str) -> Any:
    """Extract the first valid JSON array/object from the LLM response."""
    # Remove markdown code blocks if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Try to find JSON array or object
    m = re.search(r"(\[.*\]|\{.*\})", text, flags=re.S)
    block = m.group(1) if m else text.strip()
    
    # Clean up common JSON issues
    # Remove trailing commas before closing braces/brackets
    block = re.sub(r',(\s*[}\]])', r'\1', block)
    
    return json.loads(block)

def call_openai_json(prompt: str, retries: int = 3, timeout: int = 120) -> Any:
    """Call OpenAI API expecting JSON response."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    
    # OpenAI API format
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    # Models that support json_object response_format:
    # gpt-4-turbo-preview, gpt-4-0125-preview, gpt-3.5-turbo-1106, gpt-4-turbo, gpt-4o
    # Note: gpt-4o-mini does NOT support json_object format
    # Clean model name - strip quotes and whitespace
    model_clean = str(OPENAI_MODEL).strip().strip('"').strip("'")
    model_lower = model_clean.lower()
    
    print(f"🔍 Model check - Original: '{OPENAI_MODEL}', Cleaned: '{model_clean}', Lower: '{model_lower}'")
    
    # Explicitly exclude gpt-4o-mini first (it contains "gpt-4o" but doesn't support json_object)
    if "gpt-4o-mini" in model_lower:
        supports_json_format = False
        print(f"🔍 Model '{model_clean}' is gpt-4o-mini - NOT adding response_format")
    else:
        # Check if model exactly matches or starts with a supported model
        models_with_json_support = [
            "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-3.5-turbo-1106", 
            "gpt-4-turbo", "gpt-4o"
        ]
        supports_json_format = any(
            model_lower == model.lower() or model_lower.startswith(model.lower() + "-")
            for model in models_with_json_support
        )
        print(f"🔍 Model '{model_clean}' supports_json_format check result: {supports_json_format}")
    
    payload = {
        "model": model_clean,  # Use cleaned model name
        "messages": [
            {"role": "system", "content": "You are a GRC (Governance, Risk, and Compliance) analyst expert. Always return valid JSON responses as requested."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    
    # Only add response_format for models that support it
    if supports_json_format:
        payload["response_format"] = {"type": "json_object"}
        print(f"✅ Adding response_format: json_object (model '{model_clean}' supports it)")
    else:
        print(f"⚠️  NOT adding response_format (model '{model_clean}' does not support json_object)")
    
    print(f"🤖 Calling OpenAI API at {OPENAI_API_URL}")
    print(f"🤖 Model: {model_clean}")
    print(f"🤖 Prompt length: {len(prompt)} chars")
    print(f"🔍 Payload keys: {list(payload.keys())}")
    if 'response_format' in payload:
        print(f"🔍 response_format value: {payload['response_format']}")
    else:
        print(f"🔍 response_format: NOT in payload")
    
    for attempt in range(retries):
        print(f"🤖 Attempt {attempt + 1}/{retries}...")
        resp = None
        try:
            resp = requests.post(OPENAI_API_URL, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            print(f"✅ OpenAI API responded with status {resp.status_code}")
            
            # OpenAI response format
            response_data = resp.json()
            raw = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"📝 Response length: {len(raw)} chars")
            print(f"📝 First 200 chars: {raw[:200]}...")
            
            result = _json_from_llm_text(raw)
            print(f"✅ Successfully parsed JSON from OpenAI response")
            return result
            
        except json.JSONDecodeError as je:
            print(f"❌ JSON parsing error on attempt {attempt + 1}: {je}")
            if attempt < retries - 1:
                print(f"⏳ Retrying in 1 second...")
                time.sleep(1)
                continue
            print(f"❌ All retries exhausted. Raw response: {raw[:500] if 'raw' in locals() else 'N/A'}...")
            raise RuntimeError(f"Failed to parse JSON from OpenAI response after {retries} attempts")
            
        except requests.exceptions.HTTPError as he:
            print(f"❌ HTTP error on attempt {attempt + 1}: {he}")
            
            # Ensure resp is available
            if resp is None:
                print(f"⚠️  Response object is None - error occurred before response was received")
                raise RuntimeError(f"OpenAI API HTTP error: {he}")
            
            print(f"🔍 Status Code: {resp.status_code}")
            
            # Log the actual error response from OpenAI - be more robust
            try:
                # Try to get response text first
                response_text = resp.text if hasattr(resp, 'text') else 'N/A'
                print(f"🔍 Raw response text (first 1000 chars): {response_text[:1000]}")
                
                # Try to parse as JSON
                try:
                    error_response = resp.json()
                    error_message = error_response.get('error', {})
                    if isinstance(error_message, dict):
                        error_detail = error_message.get('message', 'Unknown error')
                        error_type = error_message.get('type', 'Unknown type')
                        error_code = error_message.get('code', 'Unknown code')
                        print(f"🔍 OpenAI Error Details:")
                        print(f"   Type: {error_type}")
                        print(f"   Code: {error_code}")
                        print(f"   Message: {error_detail}")
                        print(f"   Full error object: {error_message}")
                    else:
                        print(f"🔍 OpenAI Error Response (non-dict): {error_response}")
                except (ValueError, AttributeError, json.JSONDecodeError) as json_err:
                    print(f"⚠️  Response is not valid JSON: {json_err}")
                    print(f"   Response text: {response_text[:500]}")
            except Exception as e:
                print(f"⚠️  Could not parse error response: {e}")
                print(f"   Exception type: {type(e).__name__}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
            
            if resp.status_code == 401:
                raise RuntimeError("OpenAI API authentication failed. Please check your OPENAI_API_KEY.")
            elif resp.status_code == 429:
                print(f"⚠️  Rate limit exceeded. Waiting 5 seconds...")
                if attempt < retries - 1:
                    time.sleep(5)
                    continue
            elif resp.status_code >= 500:
                print(f"⚠️  OpenAI server error. Retrying...")
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
            elif resp.status_code == 400:
                # For 400 errors, log the payload to help debug
                print(f"🔍 Debugging 400 error - Payload being sent:")
                print(f"   Model: {payload.get('model')}")
                print(f"   Has response_format: {'response_format' in payload}")
                if 'response_format' in payload:
                    print(f"   response_format value: {payload.get('response_format')}")
                print(f"   Messages count: {len(payload.get('messages', []))}")
                print(f"   Temperature: {payload.get('temperature')}")
            
            raise RuntimeError(f"OpenAI API HTTP error: {he}")
            
        except requests.exceptions.ConnectionError as ce:
            print(f"❌ Connection error on attempt {attempt + 1}: {ce}")
            if attempt < retries - 1:
                print(f"⏳ Retrying in 2 seconds...")
                time.sleep(2)
                continue
            raise RuntimeError(f"Failed to connect to OpenAI API: {ce}")
            
        except requests.exceptions.Timeout as te:
            print(f"❌ Timeout error on attempt {attempt + 1}: {te}")
            if attempt < retries - 1:
                print(f"⏳ Retrying in 2 seconds...")
                time.sleep(2)
                continue
            raise RuntimeError(f"OpenAI API request timed out: {te}")
            
        except Exception as e:
            print(f"❌ Unexpected error on attempt {attempt + 1}: {type(e).__name__}: {e}")
            if attempt < retries - 1:
                print(f"⏳ Retrying in 1 second...")
                time.sleep(1)
                continue
            raise RuntimeError(f"Unexpected error calling OpenAI API: {e}")
    
    raise RuntimeError(f"Failed to get response from OpenAI API after {retries} attempts")

def clamp_int(v, lo, hi) -> Optional[int]:
    if v is None: return None
    try:
        return max(lo, min(hi, int(v)))
    except Exception:
        # try to find a number in string
        m = re.search(r"\b(\d{1,2})\b", str(v))
        if m:
            return max(lo, min(hi, int(m.group(1))))
        return None

def as_float_or_none(v) -> Optional[float]:
    if v is None: return None
    try:
        return float(v)
    except Exception:
        try:
            # extract first float from string
            m = re.search(r"[-+]?\d*\.?\d+", str(v))
            return float(m.group(0)) if m else None
        except Exception:
            return None

def as_date_or_none(s: str) -> Optional[str]:
    if not s: return None
    s = str(s).strip()
    return s if re.match(r"^\d{4}-\d{2}-\d{2}$", s) else None

def compute_exposure(lk, im) -> Optional[float]:
    if lk is None or im is None: return None
    try:
        return round(float(lk) * float(im), 2)
    except Exception:
        return None

def normalize_choice(val: str, choices: list[str]) -> Optional[str]:
    if not val: return None
    v = str(val).strip()
    for c in choices:
        if v.lower() == c.lower():
            return c
    for c in choices:
        if v.lower().startswith(c.lower()[0:3]):
            return c
    return None


# =========================
# FILE EXTRACTORS
# =========================
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF (pdfplumber preferred; PyPDF2 fallback)."""
    try:
        if pdfplumber:
            parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    if t.strip():
                        parts.append(t)
            return "\n".join(parts)
        elif PyPDF2:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for p in reader.pages:
                    text += (p.extract_text() or "") + "\n"
                return text
        return ""
    except Exception as e:
        print(f"[PDF] Extraction error: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    try:
        if not docx:
            raise RuntimeError("python-docx not installed")
        d = docx.Document(file_path)
        parts = []
        for p in d.paragraphs:
            if p.text.strip():
                parts.append(p.text)
        for t in d.tables:
            for row in t.rows:
                cells = [c.text.strip() for c in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
    except Exception as e:
        print(f"[DOCX] Extraction error: {e}")
        return ""

def extract_text_from_excel(file_path: str) -> str:
    try:
        if not pd:
            raise RuntimeError("pandas/openpyxl not installed")
        df_sheets = pd.read_excel(file_path, sheet_name=None)
        out = []
        for name, df in df_sheets.items():
            out.append(f"=== Sheet: {name} ===")
            out.append(df.to_string(index=False))
        return "\n".join(out)
    except Exception as e:
        print(f"[XLSX] Extraction error: {e}")
        return ""

def extract_text_from_file(file_path: str, file_extension: str) -> str:
    ext = file_extension.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    if ext in [".xlsx", ".xls"]:
        return extract_text_from_excel(file_path)
    if ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
    return ""


# =========================
# DOCUMENT PARSING & DETECTION
# =========================
def detect_and_parse_risk_instance_blocks(text: str) -> list[dict]:
    """
    Step 1: Detect how many risk instances are in the document by finding 'Risk X:' patterns.
    Step 2: For each risk instance, extract whatever fields are explicitly present.
    Returns a list of partially-filled risk instance dictionaries with only extracted fields.
    """
    print(f"🔍 Detecting risk instance blocks in document...")
    
    # Find all risk blocks using pattern "Risk X: Title" or "Risk Instance X: Title"
    risk_pattern = r'Risk(?:\s+Instance)?\s+(\d+):\s*([^\n]+)'
    risk_matches = list(re.finditer(risk_pattern, text, re.IGNORECASE))
    
    if not risk_matches:
        print(f"⚠️  No risk instances found with 'Risk X:' or 'Risk Instance X:' pattern")
        return []
    
    print(f"✅ Found {len(risk_matches)} risk instance(s) in document")
    
    risk_instances = []
    for i, match in enumerate(risk_matches):
        risk_num = match.group(1)
        risk_title = match.group(2).strip()
        
        # Extract the text block for this risk instance (from this match to next risk or end of document)
        start_pos = match.end()
        if i + 1 < len(risk_matches):
            end_pos = risk_matches[i + 1].start()
        else:
            end_pos = len(text)
        
        risk_block = text[start_pos:end_pos]
        
        print(f"  📋 Risk Instance {risk_num}: {risk_title[:60]}...")
        
        # Extract fields that are explicitly present in the block
        risk_data = {
            "RiskTitle": risk_title,  # Always extracted from document
            "_extracted_fields": ["RiskTitle"],  # Track what was extracted
            "_risk_block": risk_block  # Keep for AI context
        }
        
        # Field mapping: document field name -> DB field name
        field_mappings = {
            r'(?:Risk\s+)?Description:\s*([^\n]+(?:\n(?!(?:Risk|Possible Damage|Risk Priority|Criticality|Category|Origin|Status|Mitigation|Risk Type|Risk Owner|Business Impact|Risk Status|Mitigation Status|Reviewer|—))[^\n]+)*)': 'RiskDescription',
            r'Possible Damage:\s*([^\n]+(?:\n(?!(?:Risk|Description|Risk Priority|Criticality|Category|Origin|Status|Mitigation|Risk Type|Risk Owner|Business Impact|Risk Status|Mitigation Status|Reviewer|—))[^\n]+)*)': 'PossibleDamage',
            r'Risk Priority:\s*([^\n]+)': 'RiskPriority',
            r'Criticality:\s*([^\n]+)': 'Criticality',
            r'Category:\s*([^\n]+)': 'Category',
            r'Origin:\s*([^\n]+)': 'Origin',
            r'Risk Likelihood:\s*([^\n]+)': 'RiskLikelihood',
            r'Risk Impact:\s*([^\n]+)': 'RiskImpact',
            r'(?:Risk\s+)?Exposure(?:\s+Rating)?:\s*([^\n]+)': 'RiskExposureRating',
            r'Multiplier\s*X:\s*([^\n]+)': 'RiskMultiplierX',
            r'Multiplier\s*Y:\s*([^\n]+)': 'RiskMultiplierY',
            r'Appetite:\s*([^\n]+)': 'Appetite',
            r'Risk Response Type:\s*([^\n]+)': 'RiskResponseType',
            r'Risk Response(?:\s+Description)?:\s*([^\n]+(?:\n(?!(?:Risk|Description|Possible Damage|Risk Priority|Criticality|Category|—))[^\n]+)*)': 'RiskResponseDescription',
            r'Mitigation:\s*([^\n]+(?:\n(?!(?:Risk|Description|Possible Damage|Risk Priority|Criticality|Category|Origin|Risk Type|Risk Owner|Business Impact|Risk Status|Mitigation Status|Reviewer|—))[^\n]+)*)': 'RiskMitigation',
            r'Risk Type:\s*([^\n]+)': 'RiskType',
            r'Risk Owner:\s*([^\n]+)': 'RiskOwner',
            r'Business Impact:\s*([^\n]+(?:\n(?!(?:Risk|Description|Possible Damage|Risk Priority|Criticality|Category|Origin|Mitigation|Risk Type|Risk Owner|Risk Status|Mitigation Status|Reviewer|—))[^\n]+)*)': 'BusinessImpact',
            r'Risk Status:\s*([^\n]+)': 'RiskStatus',
            r'Mitigation Status:\s*([^\n]+)': 'MitigationStatus',
            r'Modified Mitigations:\s*([^\n]+(?:\n(?!(?:Risk|Description|Possible Damage|—))[^\n]+)*)': 'ModifiedMitigations',
            r'Risk Form Details:\s*([^\n]+(?:\n(?!(?:Risk|Description|Possible Damage|—))[^\n]+)*)': 'RiskFormDetails',
            r'Reviewer:\s*([^\n]+)': 'Reviewer',
        }
        
        # Extract each field if present
        for pattern, field_name in field_mappings.items():
            match = re.search(pattern, risk_block, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:  # Only add if not empty
                    risk_data[field_name] = value
                    risk_data["_extracted_fields"].append(field_name)
                    print(f"    ✓ {field_name}: {value[:50]}...")
        
        risk_instances.append(risk_data)
    
    return risk_instances


# =========================
# AI EXTRACTION CORE
# =========================
def infer_single_field(field_name: str, current_record: dict, document_context: str) -> tuple[Any, dict]:
    """
    Focused prompt for ONE field using AI.
    Returns: (value, metadata_dict)
    """
    print(f"🤖 AI PREDICTING FIELD: {field_name}")
    
    guidance = FIELD_PROMPTS.get(field_name, "Return a concise, professional value.")
    mini = f"""
You are a GRC analyst. Infer ONLY the field "{field_name}" for this risk instance.
Return JSON: {{"value": <scalar or string or array>, "confidence": 0.0-1.0, "rationale": "brief explanation"}}

Context (document):
\"\"\"{document_context[:3000]}\"\"\"

Current risk instance (partial):
{json.dumps({k: current_record.get(k) for k in RISK_INSTANCE_DB_FIELDS if current_record.get(k)}, indent=2)}

Rules:
- {guidance}
- If you cannot infer, return {{"value": null, "confidence": 0.0, "rationale": "Not enough information"}}.
- Always include a brief rationale explaining your decision.
- No extra text outside the JSON.
"""
    try:
        print(f"   📤 Sending prompt to OpenAI for {field_name}...")
        out = call_openai_json(mini)
        v = out.get("value") if isinstance(out, dict) else None
        confidence = out.get("confidence", 0.7) if isinstance(out, dict) else 0.7
        rationale = out.get("rationale", "AI predicted based on document context") if isinstance(out, dict) else "AI predicted based on document context"
        print(f"   ✅ AI PREDICTED {field_name}: '{v}' (confidence: {confidence:.2f})")
    except Exception as e:
        print(f"   ❌ AI FAILED to predict {field_name}: {str(e)}")
        v = None
        confidence = 0.0
        rationale = f"AI prediction failed: {str(e)}"

    # Create metadata for this field
    metadata = {
        "source": "AI_GENERATED",
        "confidence": confidence,
        "rationale": rationale
    }

    # normalize after inference
    if field_name in ("RiskLikelihood", "RiskImpact"):
        v = clamp_int(v, 1, 10) or 5
    elif field_name == "RiskExposureRating":
        lk = clamp_int(current_record.get("RiskLikelihood"), 1, 10)
        im = clamp_int(current_record.get("RiskImpact"), 1, 10)
        computed = compute_exposure(lk, im)
        v = computed if computed is not None else 0.0
    elif field_name in ("RiskMultiplierX", "RiskMultiplierY"):
        vf = as_float_or_none(v)
        v = vf if vf is not None else 1.0
    elif field_name in ("CreatedAt", "MitigationDueDate"):
        v = as_date_or_none(v) or date.today().isoformat()
    elif field_name == "Criticality":
        v = normalize_choice(v, CRITICALITY_CHOICES) or "Medium"
    elif field_name == "RiskPriority":
        v = normalize_choice(v, PRIORITY_CHOICES) or "Medium"
    elif field_name == "RiskType":
        v = normalize_choice(v, RISKTYPE_HINTS) or "Current"
    elif field_name == "Origin":
        v = normalize_choice(v, ORIGIN_HINTS) or "Internal"
    elif field_name == "Appetite":
        v = normalize_choice(v, APPETITE_HINTS) or "Medium"
    elif field_name == "RiskResponseType":
        v = normalize_choice(v, RESPONSE_TYPE_HINTS) or "Mitigate"
    elif field_name == "RiskStatus":
        v = normalize_choice(v, RISK_STATUS_CHOICES) or "Not Assigned"
    elif field_name == "MitigationStatus":
        v = normalize_choice(v, MITIGATION_STATUS_CHOICES) or "Pending"
    elif field_name == "RiskMitigation":
        # Should be a JSON array of mitigation steps
        if isinstance(v, list):
            pass
        elif isinstance(v, str):
            try:
                v = json.loads(v)
            except:
                v = [{"step": "Mitigation Step 1", "description": v}]
        else:
            v = [{"step": "Mitigation Step 1", "description": "To be defined"}]
    elif field_name == "ModifiedMitigations":
        # Should be a JSON array documenting modifications
        if isinstance(v, list):
            pass
        elif isinstance(v, str):
            try:
                v = json.loads(v)
            except:
                v = []
        else:
            v = []
    elif field_name == "RiskFormDetails":
        # Should be a JSON object with assessment details
        if isinstance(v, dict):
            pass
        elif isinstance(v, str):
            try:
                v = json.loads(v)
            except:
                v = {
                    "assessment_method": "Qualitative",
                    "data_sources": ["Document"],
                    "assessment_date": date.today().isoformat()
                }
        else:
            v = {
                "assessment_method": "Qualitative",
                "data_sources": ["Document"],
                "assessment_date": date.today().isoformat()
            }
    elif field_name == "Reviewer":
        v = str(v).strip() if v else "Pending Review"
    elif isinstance(v, str):
        v = v.strip() or None
    
    return v, metadata


def fallback_risk_instance_extraction(text: str) -> list[dict]:
    """
    Minimal pattern-based fallback when AI fails completely.
    Produces at least one record using generic defaults.
    """
    risk_instances = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    risk_keywords = ["risk", "threat", "vulnerability", "hazard", "danger", "exposure", "incident"]
    current = None
    count = 0

    for i, ln in enumerate(lines):
        if any(k in ln.lower() for k in risk_keywords):
            if current:
                risk_instances.append(current)
            count += 1
            current = {
                "RiskTitle": f"Risk Instance {count}: {ln[:100]}",
                "RiskDescription": ln,
                "PossibleDamage": "Potential damages vary (reputation, compliance, downtime).",
                "RiskPriority": "Medium",
                "Criticality": "Medium",
                "Category": "Operational",
                "Origin": "Internal",
                "RiskLikelihood": 5,
                "RiskImpact": 5,
                "RiskExposureRating": 25.0,
                "RiskMultiplierX": 1.0,
                "RiskMultiplierY": 1.0,
                "Appetite": "Medium",
                "RiskResponseType": "Mitigate",
                "RiskResponseDescription": "Response strategy to be defined after assessment.",
                "RiskMitigation": [{"step": "Step 1", "description": "Mitigation steps to be defined"}],
                "RiskType": "Current",
                "RiskOwner": "Risk Manager",
                "BusinessImpact": "Potential business impact in operations/compliance.",
                "RiskStatus": "Not Assigned",
                "MitigationStatus": "Pending",
                "ModifiedMitigations": [],
                "RiskFormDetails": {
                    "assessment_method": "Qualitative",
                    "data_sources": ["Document"],
                    "assessment_date": date.today().isoformat()
                },
                "Reviewer": "Pending Review",
            }

    if current:
        risk_instances.append(current)

    if not risk_instances:
        risk_instances.append({
            "RiskTitle": "Document Risk Instance Analysis",
            "RiskDescription": f"Automated risk instance derived from document (length={len(text)} chars).",
            "PossibleDamage": "Data loss, downtime, penalties, reputation.",
            "RiskPriority": "Medium",
            "Criticality": "Medium",
            "Category": "Operational",
            "Origin": "Internal",
            "RiskLikelihood": 5,
            "RiskImpact": 5,
            "RiskExposureRating": 25.0,
            "RiskMultiplierX": 1.0,
            "RiskMultiplierY": 1.0,
            "Appetite": "Medium",
            "RiskResponseType": "Mitigate",
            "RiskResponseDescription": "Response strategy to be defined after assessment.",
            "RiskMitigation": [{"step": "Step 1", "description": "Review & implement standard mitigations for identified weaknesses."}],
            "RiskType": "Current",
            "RiskOwner": "Risk Manager",
            "BusinessImpact": "Potential business impact in operations/compliance.",
            "RiskStatus": "Not Assigned",
            "MitigationStatus": "Pending",
            "ModifiedMitigations": [],
            "RiskFormDetails": {
                "assessment_method": "Qualitative",
                "data_sources": ["Document"],
                "assessment_date": date.today().isoformat()
            },
            "Reviewer": "Pending Review",
        })

    return risk_instances


def parse_risk_instances_from_text(text: str) -> list[dict]:
    """
    NEW APPROACH:
    1. First detect how many risk instances are in the document by finding 'Risk X:' patterns
    2. Extract whatever fields are explicitly present in each risk instance block
    3. Use AI to fill ONLY the missing fields (not to create risk titles)
    """
    print(f"📊 parse_risk_instances_from_text() called with {len(text)} chars of text")
    
    # Step 1: Detect and parse risk instance blocks from document
    detected_risk_instances = detect_and_parse_risk_instance_blocks(text)
    
    if not detected_risk_instances:
        print(f"⚠️  No structured risk instances found. Falling back to old AI extraction...")
        # Fallback to old behavior if no "Risk X:" pattern found
        return fallback_risk_instance_extraction(text)
    
    print(f"✅ Detected {len(detected_risk_instances)} risk instance(s), now processing each...")
    
    # Step 2: For each detected risk instance, normalize extracted fields and fill missing ones
    completed_risk_instances = []
    for idx, risk_data in enumerate(detected_risk_instances, 1):
        print(f"\n🔧 Processing Risk Instance {idx}: {risk_data.get('RiskTitle', 'Unknown')[:50]}...")
        
        # Start with empty item for all DB fields
        item = {k: None for k in RISK_INSTANCE_DB_FIELDS}
        
        # Copy extracted fields
        for field in RISK_INSTANCE_DB_FIELDS:
            if field in risk_data and risk_data[field]:
                item[field] = risk_data[field]
        
        # Get the risk block for AI context
        risk_block = risk_data.get("_risk_block", "")
        extracted_fields = risk_data.get("_extracted_fields", [])
        
        print(f"  📝 Extracted fields: {', '.join(extracted_fields)}")
        
        # Initialize metadata structure
        if "_meta" not in item:
            item["_meta"] = {}
        if "per_field" not in item["_meta"]:
            item["_meta"]["per_field"] = {}
        
        # Mark extracted fields in metadata
        for field in extracted_fields:
            if field in item and item[field]:
                item["_meta"]["per_field"][field] = {
                    "source": "EXTRACTED",
                    "confidence": 0.95,
                    "rationale": "Found explicitly in document"
                }
        
        # Normalize extracted fields
        if item.get("RiskLikelihood"):
            item["RiskLikelihood"] = clamp_int(item["RiskLikelihood"], 1, 10)
        if item.get("RiskImpact"):
            item["RiskImpact"] = clamp_int(item["RiskImpact"], 1, 10)
        if item.get("RiskExposureRating"):
            item["RiskExposureRating"] = as_float_or_none(item["RiskExposureRating"])
        if item.get("Criticality"):
            item["Criticality"] = normalize_choice(item["Criticality"], CRITICALITY_CHOICES)
        if item.get("RiskPriority"):
            item["RiskPriority"] = normalize_choice(item["RiskPriority"], PRIORITY_CHOICES)
        if item.get("RiskType"):
            item["RiskType"] = normalize_choice(item["RiskType"], RISKTYPE_HINTS)
        if item.get("Origin"):
            item["Origin"] = normalize_choice(item["Origin"], ORIGIN_HINTS)
        if item.get("Appetite"):
            item["Appetite"] = normalize_choice(item["Appetite"], APPETITE_HINTS)
        if item.get("RiskResponseType"):
            item["RiskResponseType"] = normalize_choice(item["RiskResponseType"], RESPONSE_TYPE_HINTS)
        if item.get("RiskStatus"):
            item["RiskStatus"] = normalize_choice(item["RiskStatus"], RISK_STATUS_CHOICES)
        if item.get("MitigationStatus"):
            item["MitigationStatus"] = normalize_choice(item["MitigationStatus"], MITIGATION_STATUS_CHOICES)
        if item.get("RiskMultiplierX"):
            item["RiskMultiplierX"] = as_float_or_none(item["RiskMultiplierX"])
        if item.get("RiskMultiplierY"):
            item["RiskMultiplierY"] = as_float_or_none(item["RiskMultiplierY"])
        
        # Handle JSON fields
        if item.get("RiskMitigation"):
            mitigation = item["RiskMitigation"]
            if isinstance(mitigation, str):
                try:
                    item["RiskMitigation"] = json.loads(mitigation)
                except:
                    item["RiskMitigation"] = [{"step": "Step 1", "description": mitigation}]
            elif not isinstance(mitigation, list):
                item["RiskMitigation"] = None
        
        if item.get("ModifiedMitigations"):
            mod_mits = item["ModifiedMitigations"]
            if isinstance(mod_mits, str):
                try:
                    item["ModifiedMitigations"] = json.loads(mod_mits)
                except:
                    item["ModifiedMitigations"] = []
            elif not isinstance(mod_mits, list):
                item["ModifiedMitigations"] = None
        
        if item.get("RiskFormDetails"):
            form_details = item["RiskFormDetails"]
            if isinstance(form_details, str):
                try:
                    item["RiskFormDetails"] = json.loads(form_details)
                except:
                    item["RiskFormDetails"] = None
            elif not isinstance(form_details, dict):
                item["RiskFormDetails"] = None
        
        # Step 3: Use AI to fill ONLY missing fields (NEVER RiskTitle - must be in document)
        missing_fields = [f for f in RISK_INSTANCE_DB_FIELDS if item.get(f) in (None, "", []) and f != "RiskTitle"]
        if missing_fields:
            print(f"  🤖 Missing fields: {', '.join(missing_fields)}")
            print(f"  🤖 Using AI to infer missing fields...")
            
            for field in missing_fields:
                print(f"    🔍 Inferring {field}...")
                value, metadata = infer_single_field(field, item, risk_block or text[:3000])
                item[field] = value
                # Store AI generation metadata
                item["_meta"]["per_field"][field] = metadata
                print(f"    🏷️  Marked {field} as AI_GENERATED in metadata")
        else:
            print(f"  ✅ All fields extracted from document!")
        
        # Final normalization and defaults
        item["RiskLikelihood"] = item["RiskLikelihood"] or 5
        item["RiskImpact"] = item["RiskImpact"] or 5
        
        # Compute exposure if not present
        if not item.get("RiskExposureRating"):
            item["RiskExposureRating"] = compute_exposure(item["RiskLikelihood"], item["RiskImpact"]) or 25.0
        
        item["RiskExposureRating"] = float(max(0.0, min(100.0, item["RiskExposureRating"])))
        item["RiskMultiplierX"] = item["RiskMultiplierX"] or 1.0
        item["RiskMultiplierY"] = item["RiskMultiplierY"] or 1.0
        item["Criticality"] = item["Criticality"] or "Medium"
        item["RiskPriority"] = item["RiskPriority"] or "Medium"
        item["RiskType"] = item["RiskType"] or "Current"
        item["Origin"] = item["Origin"] or "Internal"
        item["Appetite"] = item["Appetite"] or "Medium"
        item["RiskResponseType"] = item["RiskResponseType"] or "Mitigate"
        item["RiskStatus"] = item["RiskStatus"] or "Not Assigned"
        item["MitigationStatus"] = item["MitigationStatus"] or "Pending"
        item["Reviewer"] = item["Reviewer"] or "Pending Review"
        
        # RiskTitle must ALWAYS come from document - never generate it
        if not item.get("RiskTitle"):
            raise ValueError(f"RiskTitle is missing for risk instance {idx}. All risk titles must be present in the document as 'Risk X: Title'.")
        
        # Ensure JSON fields have proper defaults
        if not isinstance(item.get("RiskMitigation"), list):
            item["RiskMitigation"] = [{"step": "Step 1", "description": "To be defined"}]
        if not isinstance(item.get("ModifiedMitigations"), list):
            item["ModifiedMitigations"] = []
        if not isinstance(item.get("RiskFormDetails"), dict):
            item["RiskFormDetails"] = {
                "assessment_method": "Qualitative",
                "data_sources": ["Document"],
                "assessment_date": date.today().isoformat()
            }
        
        # Debug: Print metadata summary
        ai_fields = [field for field, info in item["_meta"]["per_field"].items() 
                    if info.get("source") == "AI_GENERATED"]
        extracted = [field for field, info in item["_meta"]["per_field"].items() 
                    if info.get("source") == "EXTRACTED"]
        
        print(f"  📊 Metadata Summary:")
        print(f"     🤖 AI Generated: {len(ai_fields)} fields - {ai_fields}")
        print(f"     📄 Extracted: {len(extracted)} fields - {extracted}")
        
        completed_risk_instances.append(item)
        print(f"  ✅ Risk Instance {idx} completed!")
    
    return completed_risk_instances


# =========================
# DJANGO API ENDPOINTS
# =========================
@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
@csrf_exempt
@rbac_required(required_permission='create_risk')
def upload_and_process_risk_instance_document(request):
    """
    Upload a document and process it to extract COMPLETE risk instance data
    (fills missing fields via Ollama).
    Saves the uploaded document to MEDIA_ROOT/ai_uploads/risk_instance/
    """

    print(f"📤 Upload request for risk instance document")
    print(f"📤 Request data: {request.POST}")
    print(f"📤 Request files: {request.FILES}")
    print(f"📤 User ID: {request.POST.get('user_id', 'unknown')}")

    # CORS preflight support
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Max-Age'] = '86400'
        return response

    try:
        if 'file' not in request.FILES:
            resp = JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)
            resp['Access-Control-Allow-Origin'] = '*'
            return resp

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        ext = os.path.splitext(file_name)[1].lower()

        allowed = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt']
        if ext not in allowed:
            resp = JsonResponse({'status': 'error', 'message': f'Invalid file type. Allowed: {", ".join(allowed)}'}, status=400)
            resp['Access-Control-Allow-Origin'] = '*'
            return resp

        # Create the ai_uploads/risk_instance directory if it doesn't exist
        from django.conf import settings
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'ai_uploads', 'risk_instance')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file with timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{file_name}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Write the uploaded file to disk
        with open(file_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        print(f"✅ File saved to: {file_path}")

        try:
            # Step 1: Extract text from the saved file
            print(f"🔍 STEP 1: Starting text extraction from {ext} file...")
            text = extract_text_from_file(file_path, ext)
            
            if not text or len(text.strip()) < 50:
                print(f"❌ ERROR: Could not extract meaningful text. Length: {len(text) if text else 0}")
                resp = JsonResponse({'status': 'error', 'message': 'Could not extract meaningful text from document'}, status=400)
                resp['Access-Control-Allow-Origin'] = '*'
                return resp

            print(f"✅ STEP 1 COMPLETE: Extracted {len(text)} characters from document")
            print(f"📄 First 200 chars: {text[:200]}...")
            
            # Step 2: Check OpenAI API key
            print(f"🔍 STEP 2: Checking OpenAI API configuration...")
            if not OPENAI_API_KEY:
                print(f"❌ ERROR: OPENAI_API_KEY is not set")
                resp = JsonResponse({
                    'status': 'error', 
                    'message': 'OPENAI_API_KEY environment variable is not set. Please configure your OpenAI API key.'
                }, status=503)
                resp['Access-Control-Allow-Origin'] = '*'
                return resp
            
            print(f"✅ STEP 2 COMPLETE: OpenAI API key is configured")
            
            # Step 3: Process with AI
            print(f"🤖 STEP 3: Calling OpenAI model '{OPENAI_MODEL}' to extract risk instances...")
            risk_instances = parse_risk_instances_from_text(text)
            
            print(f"✅ STEP 3 COMPLETE: AI extracted {len(risk_instances)} risk instance(s) from document")
            for idx, ri in enumerate(risk_instances, 1):
                print(f"  Risk Instance {idx}: {ri.get('RiskTitle', 'Untitled')[:50]}...")

            resp = JsonResponse({
                'status': 'success',
                'message': f'Successfully extracted {len(risk_instances)} risk instance(s)',
                'document_name': file_name,
                'saved_path': safe_filename,
                'extracted_text_length': len(text),
                'risk_instances': risk_instances
            })
            resp['Access-Control-Allow-Origin'] = '*'
            return resp
        except Exception as process_error:
            # Clean up the file if processing fails
            if os.path.exists(file_path):
                os.unlink(file_path)
            raise process_error

    except Exception as e:
        import traceback
        traceback.print_exc()
        resp = JsonResponse({'status': 'error', 'message': f'Error processing document: {str(e)}'}, status=500)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
@csrf_exempt
@rbac_required(required_permission='create_risk')
def save_extracted_risk_instances(request):
    """
    Save extracted/reviewed risk instances to the database.
    (Does not set RiskId, IncidentId, ComplianceId here - these are foreign keys.)
    """
    try:
        data = json.loads(request.body or "{}")
        risk_instances_data = data.get('risk_instances', [])
        if not risk_instances_data:
            return JsonResponse({'status': 'error', 'message': 'No risk instances provided'}, status=400)

        saved = []
        errors = []

        for idx, r in enumerate(risk_instances_data):
            try:
                # Parse RiskMitigation if it's a string
                risk_mitigation = r.get('RiskMitigation')
                if isinstance(risk_mitigation, str):
                    try:
                        risk_mitigation = json.loads(risk_mitigation)
                    except:
                        risk_mitigation = [{"step": "Step 1", "description": risk_mitigation}]
                elif not isinstance(risk_mitigation, list):
                    risk_mitigation = [{"step": "Step 1", "description": "To be defined"}]
                
                # Parse ModifiedMitigations if it's a string
                modified_mitigations = r.get('ModifiedMitigations', [])
                if isinstance(modified_mitigations, str):
                    try:
                        modified_mitigations = json.loads(modified_mitigations)
                    except:
                        modified_mitigations = []
                elif not isinstance(modified_mitigations, list):
                    modified_mitigations = []
                
                # Parse RiskFormDetails if it's a string
                risk_form_details = r.get('RiskFormDetails')
                if isinstance(risk_form_details, str):
                    try:
                        risk_form_details = json.loads(risk_form_details)
                    except:
                        risk_form_details = {
                            "assessment_method": "Qualitative",
                            "data_sources": ["Document"],
                            "assessment_date": date.today().isoformat()
                        }
                elif not isinstance(risk_form_details, dict):
                    risk_form_details = {
                        "assessment_method": "Qualitative",
                        "data_sources": ["Document"],
                        "assessment_date": date.today().isoformat()
                    }
                
                kwargs = {
                    # not setting: RiskInstanceId (auto), RiskId, IncidentId, ComplianceId, UserId, ReviewerId, ReportedBy
                    'RiskTitle': r.get('RiskTitle', f'Risk Instance {idx+1}'),
                    'RiskDescription': r.get('RiskDescription', ''),
                    'PossibleDamage': r.get('PossibleDamage', ''),
                    'RiskPriority': r.get('RiskPriority', 'Medium'),
                    'Criticality': r.get('Criticality', 'Medium'),
                    'Category': r.get('Category', ''),
                    'Origin': r.get('Origin', 'Internal'),
                    'RiskLikelihood': int(r.get('RiskLikelihood') or 5),
                    'RiskImpact': int(r.get('RiskImpact') or 5),
                    'RiskExposureRating': float(r.get('RiskExposureRating') or 25.0),
                    'RiskMultiplierX': float(r.get('RiskMultiplierX') or 1.0),
                    'RiskMultiplierY': float(r.get('RiskMultiplierY') or 1.0),
                    'Appetite': r.get('Appetite', 'Medium'),
                    'RiskResponseType': r.get('RiskResponseType', 'Mitigate'),
                    'RiskResponseDescription': r.get('RiskResponseDescription', ''),
                    'RiskMitigation': risk_mitigation,
                    'RiskType': r.get('RiskType', 'Current'),
                    'RiskOwner': r.get('RiskOwner', ''),
                    'BusinessImpact': r.get('BusinessImpact', ''),
                    'RiskStatus': r.get('RiskStatus', 'Not Assigned'),
                    'MitigationStatus': r.get('MitigationStatus', 'Pending'),
                    'ModifiedMitigations': modified_mitigations,
                    'RiskFormDetails': risk_form_details,
                    'Reviewer': r.get('Reviewer', 'Pending Review'),
                }
                risk_instance = RiskInstance.objects.create(**kwargs)
                saved.append({'risk_instance_id': getattr(risk_instance, "RiskInstanceId", None), 'risk_title': risk_instance.RiskTitle})
            except Exception as ex:
                errors.append({'risk_instance_index': idx, 'title': r.get('RiskTitle'), 'error': str(ex)})

        resp = {
            'status': 'success',
            'message': f'Saved {len(saved)} risk instance(s)' + (f' with {len(errors)} error(s)' if errors else ''),
            'saved': saved
        }
        if errors:
            resp['errors'] = errors
        return JsonResponse(resp)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'Error saving risk instances: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@rbac_required(required_permission='view_all_risk')
def test_openai_connection_risk_instance(request):
    """Quick check that OpenAI API responds."""
    try:
        if not OPENAI_API_KEY:
            return JsonResponse({
                'status': 'error',
                'message': 'OPENAI_API_KEY is not set',
                'model': OPENAI_MODEL,
                'api_url': OPENAI_API_URL
            }, status=500)
        
        out = call_openai_json('Return JSON: {"ok": true}')
        return JsonResponse({
            'status': 'success', 
            'openai_reply': out, 
            'model': OPENAI_MODEL, 
            'api_url': OPENAI_API_URL
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'OpenAI error: {e}', 
            'model': OPENAI_MODEL, 
            'api_url': OPENAI_API_URL
        }, status=500)

