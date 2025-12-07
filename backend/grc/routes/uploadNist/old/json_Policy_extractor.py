


"""
NIST SP 800-53 Rev.5 (generic) extractor (PDF or JSON)
- Accepts a PDF or a JSON file.
- For PDFs: extracts lines with PyMuPDF (fallback to pdfminer) and dumps font-change TXT segments.
- For JSON: supports several shapes; specifically optimized for a single big "content" string like the sample you provided.
- Parses families, policy (*-1), sub-policies (other base controls), control statements, and enhancements.
- Returns a comprehensive JSON with all families and controls.

Requirements:
  pip install pymupdf pdfminer.six
"""

import os
import re
import json
from pathlib import Path

# ---------- Utility ----------
def dash_normalize(s: str) -> str:
    """Replace various unicode dash characters with ASCII hyphen."""
    return re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", s)

def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

# ---------- Regex / markers ----------
CONTROL_ID_ONLY_RE = re.compile(r"^([A-Z]{2})-(\d+)$")            # e.g., "AC-2"
CONTROL_HEADER_RE   = re.compile(r"^([A-Z]{2})-(\d+)\s+(.+)$")    # e.g., "AC-2 Account Management"
ENHANCEMENT_RE      = re.compile(r"^\((\d+)\)\s+(.+)$")           # e.g., "(1) Automated ..."
FAMILY_CHAPTER_RE   = re.compile(r"^\s*3\.\d+\s+([A-Z][A-Z\s/&-]+)\s*$")

SECTION_CONTROL      = "Control:"
SECTION_DISCUSSION   = "Discussion:"
SECTION_RELATED      = "Related Controls:"
SECTION_ENHANCEMENTS = "Control Enhancements:"
SECTION_REFERENCES   = "References:"

SECTION_LABELS = [SECTION_CONTROL, SECTION_DISCUSSION, SECTION_RELATED, SECTION_ENHANCEMENTS, SECTION_REFERENCES]

# ---------- Readers ----------
def read_lines_with_pymupdf(pdf_path: str):
    """Return a list of normalized lines for parsing (using PyMuPDF)."""
    import fitz
    doc = fitz.open(pdf_path)
    all_lines = []
    for pno in range(len(doc)):
        page = doc[pno]
        text = page.get_text("text").replace("\r\n", "\n").replace("\r", "\n")
        text = dash_normalize(text)
        lines = [normalize_ws(ln) for ln in text.split("\n")]
        all_lines.extend(lines)
    return _post_process_lines(all_lines)

def read_lines_fallback_pdfminer(pdf_path: str):
    """Fallback text extraction via pdfminer (no font detail)."""
    from pdfminer.high_level import extract_text
    text = extract_text(pdf_path).replace("\r\n", "\n").replace("\r", "\n")
    text = dash_normalize(text)
    lines = [normalize_ws(ln) for ln in text.split("\n")]
    return _post_process_lines(lines)

def _split_inline_section_markers(lines):
    """
    Some sources (like your JSON) have headers and section labels on the *same* line:
      'AC-1 POLICY AND PROCEDURES Control: a. ...'
    We split so labels start at BOL for the parser.

    Rules:
      - For 'Control:' keep remainder on the SAME line (parser consumes 'after' text).
      - For other labels (Discussion/Related/Enhancements/References), put label on its own line,
        and push the remainder to the next line (if any).
    """
    out = []
    for s in lines:
        if not s:
            continue
        split_done = False
        for lab in SECTION_LABELS:
            idx = s.find(lab)
            if idx > 0:  # embedded (not already at start)
                before = s[:idx].strip()
                after  = s[idx + len(lab):].strip()
                if before:
                    out.append(before)
                if lab == SECTION_CONTROL:
                    # keep remainder on same line so parser picks it up as 'after'
                    out.append(lab + ((" " + after) if after else ""))
                else:
                    # put label on its own line; remainder as next line
                    out.append(lab)
                    if after:
                        out.append(after)
                split_done = True
                break
        if not split_done:
            out.append(s)
    return out

def _post_process_lines(lines):
    """Common cleanup: drop blanks & [Page N] markers, split inline section labels, normalize again."""
    cleaned = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if re.match(r"^\[Page\s+\d+\]$", ln):
            continue
        cleaned.append(ln)
    cleaned = _split_inline_section_markers(cleaned)
    # one more light normalize pass after splitting
    return [normalize_ws(dash_normalize(x)) for x in cleaned if x]

def read_lines_from_json(json_path: str):
    """
    Accepts JSON and returns a flat list of normalized lines.

    Supported shapes:
      A) {"content": "<BIG STRING>"}    <-- optimized for your sample
      B) ["line1", "line2", ...]
      C) {"lines": ["..."]}
      D) {"pages": [{"lines": ["..."]}, {"lines": ["..."]}]}
      E) {"blocks": [{"text": "..."}, ...]}  # split on newlines

    Fallback: recursively flatten *string* fields.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Preferred: single big "content" string (your sample)
    if isinstance(data, dict) and isinstance(data.get("content"), str):
        raw = data["content"].replace("\r\n", "\n").replace("\r", "\n")
        raw = dash_normalize(raw)
        lines = [normalize_ws(ln) for ln in raw.split("\n")]
        return _post_process_lines(lines)

    lines = []

    def add_lines(seq):
        for x in seq:
            if not isinstance(x, str):
                x = str(x)
            x = normalize_ws(dash_normalize(x))
            if x:
                lines.append(x)

    if isinstance(data, list):
        # Case B
        add_lines(data)

    elif isinstance(data, dict):
        if "lines" in data and isinstance(data["lines"], list):
            # Case C
            add_lines(data["lines"])

        elif "pages" in data and isinstance(data["pages"], list):
            # Case D
            for pg in data["pages"]:
                add_lines(pg.get("lines", []))

        elif "blocks" in data and isinstance(data["blocks"], list):
            # Case E
            blob = "\n".join([b.get("text", "") for b in data["blocks"]])
            add_lines(blob.split("\n"))

        else:
            # Fallback: flatten string fields, but prefer 'content' if present
            def walk(obj):
                if isinstance(obj, str):
                    add_lines(obj.split("\n"))
                elif isinstance(obj, list):
                    for v in obj:
                        walk(v)
                elif isinstance(obj, dict):
                    for k, v in obj.items():
                        # Skip obviously non-content scalars to reduce noise
                        if k.lower() in {"name", "chapter_title", "parent_title"} and isinstance(v, str):
                            add_lines([v])  # small, but can be useful
                        else:
                            walk(v)
            walk(data)

    else:
        raise ValueError("Unsupported JSON shape for text extraction")

    return _post_process_lines(lines)

# ---------- Catalog building ----------
def ensure_family(catalog, fam_code, fam_title=None):
    if fam_code not in catalog:
        catalog[fam_code] = {"family_title": fam_title or "", "policy": None, "sub_policies": {}}
    else:
        if fam_title and not catalog[fam_code]["family_title"]:
            catalog[fam_code]["family_title"] = fam_title

def store_control_text(catalog, family_code, control_id, control_title, control_text_buffer):
    """Attach the collected Control: statement to policy or sub-policy entry."""
    if not (family_code and control_id):
        return
    txt = normalize_ws(" ".join(control_text_buffer))
    fam = catalog[family_code]
    base_num = int(control_id.split("-")[1])
    if base_num == 1:
        fam["policy"] = {
            "id": control_id, 
            "title": control_title, 
            "control_text": txt, 
            "enhancements": [],
            "references": [],
            "related_controls": []
        }
    else:
        sp = fam["sub_policies"].setdefault(control_id, {
            "id": control_id, 
            "title": control_title, 
            "control_text": "", 
            "enhancements": [],
            "references": [],
            "related_controls": []
        })
        sp["control_text"] = txt

def add_enhancement(catalog, family_code, control_id, control_title, number_str, enh_title):
    if not (family_code and control_id):
        return
    enh_id = f"{control_id}({number_str})"
    entry = {"id": enh_id, "title": normalize_ws(enh_title)}
    fam = catalog[family_code]
    base_num = int(control_id.split("-")[1])
    if base_num == 1:
        if fam["policy"] is None:
            fam["policy"] = {
                "id": control_id, 
                "title": control_title, 
                "control_text": "", 
                "enhancements": [],
                "references": [],
                "related_controls": []
            }
        fam["policy"]["enhancements"].append(entry)
    else:
        sp = fam["sub_policies"].setdefault(control_id, {
            "id": control_id, 
            "title": control_title, 
            "control_text": "", 
            "enhancements": [],
            "references": [],
            "related_controls": []
        })
        sp["enhancements"].append(entry)
        
def add_references(catalog, family_code, control_id, references_text):
    """Add references to a control."""
    if not (family_code and control_id and references_text):
        return
    
    # Process the references text into a list
    refs = [ref.strip() for ref in references_text.split(';') if ref.strip()]
    
    fam = catalog[family_code]
    base_num = int(control_id.split("-")[1])
    if base_num == 1:
        if fam["policy"] is None:
            return
        fam["policy"]["references"] = refs
    else:
        if control_id not in fam["sub_policies"]:
            return
        fam["sub_policies"][control_id]["references"] = refs

def add_related_controls(catalog, family_code, control_id, related_controls_text):
    """Add related controls to a control."""
    if not (family_code and control_id and related_controls_text):
        return
    
    # Extract control IDs using regex
    control_ids = []
    # Match patterns like AC-1, AC-2(1), etc.
    for match in re.finditer(r'([A-Z]{2}-\d+(?:\(\d+\))?)', related_controls_text):
        control_ids.append(match.group(1))
    
    fam = catalog[family_code]
    base_num = int(control_id.split("-")[1])
    if base_num == 1:
        if fam["policy"] is None:
            return
        fam["policy"]["related_controls"] = control_ids
    else:
        if control_id not in fam["sub_policies"]:
            return
        fam["sub_policies"][control_id]["related_controls"] = control_ids

def parse_controls(all_lines):
    """
    Generic parser for NIST SP 800-53r5 Chapter Three controls.
    Returns a catalog dict keyed by family code (e.g., AC).
    """
    catalog = {}

    current_family_code = None
    current_control_id   = None
    current_control_title= None
    collecting_control_text = False
    collecting_enhancements = False
    collecting_references = False
    collecting_related_controls = False
    control_text_buffer = []
    references_buffer = []
    related_controls_buffer = []
    pending_family_title = None

    i = 0
    N = len(all_lines)
    while i < N:
        line = all_lines[i].strip()
        if not line:
            i += 1
            continue

        # Family heading like "3.1   ACCESS CONTROL"
        m_fam = FAMILY_CHAPTER_RE.match(line)
        if m_fam:
            pending_family_title = m_fam.group(1).title().strip()
            i += 1
            continue

        m_ctrl_full   = CONTROL_HEADER_RE.match(line)
        m_ctrl_idonly = CONTROL_ID_ONLY_RE.match(line)

        if m_ctrl_full or m_ctrl_idonly:
            # finalize prior control's data if collecting
            if collecting_control_text:
                store_control_text(catalog, current_family_code, current_control_id, current_control_title, control_text_buffer)
            if collecting_references and references_buffer:
                add_references(catalog, current_family_code, current_control_id, " ".join(references_buffer))
            if collecting_related_controls and related_controls_buffer:
                add_related_controls(catalog, current_family_code, current_control_id, " ".join(related_controls_buffer))
                
            collecting_control_text = False
            collecting_enhancements = False
            collecting_references = False
            collecting_related_controls = False
            control_text_buffer = []
            references_buffer = []
            related_controls_buffer = []

            if m_ctrl_full:
                fam_code, num, title = m_ctrl_full.group(1), m_ctrl_full.group(2), m_ctrl_full.group(3).strip()
            else:
                fam_code, num = m_ctrl_idonly.group(1), m_ctrl_idonly.group(2)
                # title is typically the next non-empty line (and not a section label)
                title = ""
                j = i + 1
                while j < N and not title:
                    candidate = all_lines[j].strip()
                    if candidate and not any(candidate.startswith(s) for s in [SECTION_CONTROL, SECTION_DISCUSSION, SECTION_RELATED, SECTION_ENHANCEMENTS, SECTION_REFERENCES]):
                        title = candidate
                        break
                    j += 1

            current_family_code = fam_code
            ensure_family(catalog, current_family_code, pending_family_title)
            pending_family_title = None

            current_control_id    = f"{fam_code}-{num}"
            current_control_title = title
            i += 1
            continue

        # Section markers
        if line.startswith(SECTION_CONTROL):
            collecting_control_text = True
            collecting_enhancements = False
            collecting_references = False
            collecting_related_controls = False
            after = line[len(SECTION_CONTROL):].strip()
            if after:
                control_text_buffer.append(after)
            i += 1
            continue

        if line.startswith(SECTION_DISCUSSION):
            if collecting_control_text:
                store_control_text(catalog, current_family_code, current_control_id, current_control_title, control_text_buffer)
                control_text_buffer = []
                collecting_control_text = False
            collecting_enhancements = False
            collecting_references = False
            collecting_related_controls = False
            i += 1
            continue
            
        if line.startswith(SECTION_REFERENCES):
            if collecting_control_text:
                store_control_text(catalog, current_family_code, current_control_id, current_control_title, control_text_buffer)
                control_text_buffer = []
                collecting_control_text = False
            if collecting_related_controls and related_controls_buffer:
                add_related_controls(catalog, current_family_code, current_control_id, " ".join(related_controls_buffer))
                related_controls_buffer = []
            collecting_enhancements = False
            collecting_references = True
            collecting_related_controls = False
            i += 1
            continue
            
        if line.startswith(SECTION_RELATED):
            if collecting_control_text:
                store_control_text(catalog, current_family_code, current_control_id, current_control_title, control_text_buffer)
                control_text_buffer = []
                collecting_control_text = False
            collecting_enhancements = False
            collecting_references = False
            collecting_related_controls = True
            i += 1
            continue

        if line.startswith(SECTION_ENHANCEMENTS):
            if collecting_control_text:
                store_control_text(catalog, current_family_code, current_control_id, current_control_title, control_text_buffer)
                control_text_buffer = []
                collecting_control_text = False
            if collecting_references and references_buffer:
                add_references(catalog, current_family_code, current_control_id, " ".join(references_buffer))
                references_buffer = []
            if collecting_related_controls and related_controls_buffer:
                add_related_controls(catalog, current_family_code, current_control_id, " ".join(related_controls_buffer))
                related_controls_buffer = []
            collecting_enhancements = True
            collecting_references = False
            collecting_related_controls = False
            i += 1
            continue

        if collecting_enhancements:
            m_enh = ENHANCEMENT_RE.match(line)
            if m_enh:
                add_enhancement(catalog, current_family_code, current_control_id, current_control_title, m_enh.group(1), m_enh.group(2))
                i += 1
                continue
            if line.lower().startswith("none"):
                collecting_enhancements = False
                i += 1
                continue

        if collecting_control_text:
            control_text_buffer.append(" " + line)
        elif collecting_references:
            references_buffer.append(" " + line)
        elif collecting_related_controls:
            related_controls_buffer.append(" " + line)

        i += 1

    # final flush
    if collecting_control_text:
        store_control_text(catalog, current_family_code, current_control_id, current_control_title, control_text_buffer)
    if collecting_references and references_buffer:
        add_references(catalog, current_family_code, current_control_id, " ".join(references_buffer))
    if collecting_related_controls and related_controls_buffer:
        add_related_controls(catalog, current_family_code, current_control_id, " ".join(related_controls_buffer))

    return catalog

def create_final_merged_json(catalog: dict):
    """
    Create a comprehensive JSON file containing all families and their controls.
    Returns the JSON as a dictionary.
    """
    final_json = {
        "families": []
    }
    
    for family_code, family_data in sorted(catalog.items()):
        family_entry = {
            "family_code": family_code,
            "family_title": family_data.get("family_title", ""),
            "controls": []
        }
        
        # Add the main policy first (if it exists)
        policy = family_data.get("policy")
        if policy:
            family_entry["controls"].append({
                "id": policy["id"],
                "title": policy["title"],
                "control_text": policy.get("control_text", ""),
                "enhancements": policy.get("enhancements", []),
                "references": policy.get("references", []),
                "related_controls": policy.get("related_controls", [])
            })
        
        # Add all sub-policies
        for control_id, control_data in sorted(family_data["sub_policies"].items()):
            family_entry["controls"].append({
                "id": control_data["id"],
                "title": control_data["title"],
                "control_text": control_data.get("control_text", ""),
                "enhancements": control_data.get("enhancements", []),
                "references": control_data.get("references", []),
                "related_controls": control_data.get("related_controls", [])
            })
        
        final_json["families"].append(family_entry)
    
    return final_json

def extract_policy_from_pdf(pdf_path: str):
    """
    Main function that takes a PDF path as input and returns the final JSON result.
    
    Args:
        pdf_path (str): Path to the PDF file to process
        
    Returns:
        dict: Comprehensive JSON containing all families and their controls
    """
    # Validate input
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError("Input file must be a PDF")
    
    # Extract lines from PDF
    try:
        all_lines = read_lines_with_pymupdf(pdf_path)
    except Exception as e:
        print(f"PyMuPDF failed, trying pdfminer fallback: {e}")
        all_lines = read_lines_fallback_pdfminer(pdf_path)
    
    # Parse controls
    catalog = parse_controls(all_lines)
    
    # Create final merged JSON
    final_json = create_final_merged_json(catalog)
    
    return final_json

# ------- Example usage -------
if __name__ == "__main__":
    # Example usage
    pdf_path = "NIST.SP.800-53r5_3.15-3.16.pdf"
    try:
        result = extract_policy_from_pdf(pdf_path)
        print("Extraction completed successfully!")
        print(f"Found {len(result['families'])} families")
        print("Family codes:", [fam['family_code'] for fam in result['families']])
        
        # Optionally save to file
        with open("extracted_policies.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("Results saved to extracted_policies.json")
        
    except Exception as e:
        print(f"Error: {e}")
