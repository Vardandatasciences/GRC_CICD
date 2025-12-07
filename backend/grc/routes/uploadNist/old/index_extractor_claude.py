
import re
import json
import argparse
from pathlib import Path
from typing import Union, Optional
 
# ---------------- Utilities ----------------
 
DASHES = r"[\u2010\u2011\u2012\u2013\u2014\u2212]"
 
def norm_dashes(s: str) -> str:
    return re.sub(DASHES, "-", s)
 
def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
 
ROMAN_RE = re.compile(
    r"^(?=[ivxlcdmIVXLCDM]+$)M{0,4}(CM|CD|D?C{0,3})"
    r"(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"
)
 
def roman_to_int(s: str) -> Optional[int]:
    s = s.upper()
    if not ROMAN_RE.match(s):
        return None
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total, prev = 0, 0
    for ch in reversed(s):
        v = vals[ch]
        if v < prev:
            total -= v
        else:
            total += v
            prev = v
    return total
 
def to_int_if_numeric(page_label: str) -> Optional[int]:
    if page_label.isdigit():
        return int(page_label)
    r = roman_to_int(page_label)
    return r
 
# ---------------- Extraction via PyMuPDF (preferred) ----------------
 
def load_pages_with_positions_pymupdf(pdf_path: str):
    """Return list of pages; each page is list of (text_line, x0_left)."""
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    pages = []
    for pno in range(len(doc)):
        page = doc[pno]
        d = page.get_text("dict")
        lines = []
        for block in d.get("blocks", []):
            for line in block.get("lines", []):
                parts = []
                x0s = []
                for span in line.get("spans", []):
                    parts.append(span.get("text", ""))
                    bbox = span.get("bbox", None)
                    if bbox:
                        x0s.append(bbox[0])
                text = norm_ws(norm_dashes("".join(parts)))
                if text and len(text.strip()) > 0:
                    x0 = min(x0s) if x0s else 0.0
                    lines.append((text, x0))
        pages.append(lines)
    return pages
 
def extract_outline_pymupdf(pdf_path: str):
    """Return outline items from the PDF's internal bookmarks, if any."""
    import fitz
    doc = fitz.open(pdf_path)
    toc = doc.get_toc(simple=True)  # list of [level, title, page]
    items = []
    for lvl, title, page in toc:
        title = norm_ws(norm_dashes(title))
        items.append({
            "level": int(lvl),
            "title": title,
            "page_label": str(page),  # bookmark page is 1-based pdf page index
            "page_number": page if isinstance(page, int) else None,
            "source_page": int(page) if isinstance(page, int) else None
        })
    return items
 
# ---------------- Fallback via pdfminer (text only) ----------------
 
def load_pages_text_pdfminer(pdf_path: str):
    """Fallback: return list of pages; each page is list of (text_line, None)."""
    from pdfminer.high_level import extract_text
    try:
        import fitz
        doc = fitz.open(pdf_path)
        pages = []
        for pno in range(len(doc)):
            txt = norm_ws(norm_dashes(doc[pno].get_text("text")))
            lines = [(ln, None) for ln in txt.split("\n") if ln.strip()]
            pages.append(lines)
        return pages
    except Exception:
        text = extract_text(pdf_path)
        text = norm_ws(norm_dashes(text))
        return [[(ln, None) for ln in text.split("\n") if ln.strip()]]
 
# ---------------- TOC detection & parsing ----------------
 
TOC_TITLE_PATTERNS = [
    re.compile(r"\btable of contents\b", re.IGNORECASE),
    re.compile(r"^\s*contents\s*$", re.IGNORECASE),
    re.compile(r"^\s*contents\b", re.IGNORECASE),
    re.compile(r"\bcontents\b", re.IGNORECASE),
    re.compile(r"\bindex\b", re.IGNORECASE),
]
 
TOC_LINE_RES = [
    # GRI specific format: "GRI 1: Foundation 2021" followed by page number (right-aligned)
    re.compile(r"^(?P<title>GRI\s+\d+[A-Za-z]?\s*:\s*[^0-9]+?\s+\d{4})\s+(?P<page>\d+)$"),
    # General format with dots: "Title .......... 123"
    re.compile(r"^(?P<title>.+?)\s?\.{2,}\s*(?P<page>[ivxlcdmIVXLCDM]+|\d+)$"),
    # Format with lots of spaces (right-aligned page numbers): "Title           123"
    re.compile(r"^(?P<title>.+?)\s{5,}(?P<page>\d+)$"),
    # Standard format: "Title   123"
    re.compile(r"^(?P<title>.+?)\s{3,}(?P<page>[ivxlcdmIVXLCDM]+|\d+)$"),
    # Loose format: "Title 123" (minimal spacing, last resort)
    re.compile(r"^(?P<title>.+?)\s+(?P<page>[ivxlcdmIVXLCDM]+|\d+)$"),
]
 
def find_toc_start_pages(pages):
    """Return candidate page indices where a TOC title appears."""
    hits = []
    max_scan = min(len(pages), 30)
    for pno in range(max_scan):
        text = " ".join([t for (t, _x) in pages[pno]])
        for pat in TOC_TITLE_PATTERNS:
            if pat.search(text):
                hits.append(pno)
                break
        gri_count = len(re.findall(r'GRI\s+\d+[A-Za-z]?\s*:', text, re.IGNORECASE))
        if gri_count >= 3:
            if pno not in hits:
                hits.append(pno)
    return hits
 
def infer_levels_from_indents(items):
    """Given [(title, page_label, x0, source_page)], assign levels based on distinct x0 buckets."""
    xs = [x for (_t, _p, x, _sp) in items if x is not None]
    if not xs:
        return [1] * len(items)
    x_counts = {}
    for x in xs:
        x_counts[x] = x_counts.get(x, 0) + 1
    main_x = max(x_counts.keys(), key=lambda k: x_counts[k])
    if x_counts[main_x] >= len(items) * 0.7:
        return [1] * len(items)
    tol = 4.0
    buckets = []
    for x in sorted(xs):
        placed = False
        for b in buckets:
            if abs(b - x) <= tol:
                placed = True
                break
        if not placed:
            buckets.append(x)
    buckets = sorted(buckets)
    levels = []
    for (_t, _p, x, _sp) in items:
        if x is None:
            levels.append(1)
        else:
            idx = min(range(len(buckets)), key=lambda i: abs(buckets[i]-x))
            levels.append(idx + 1)
    return levels
 
def parse_toc_from_pages(pages, start_pno):
    """
    Parse TOC lines starting at 'start_pno' and continue forward
    until TOC pattern disappears for a while.
    Returns list of dicts with title, page_label, page_number, level, source_page.
    """
    results_raw = []  # (title, page_label, x0, source_page)
    pno = start_pno
    misses = 0
    MAX_MISSES = 3
    MAX_PAGES = min(len(pages), start_pno + 15)
   
    while pno < MAX_PAGES:
        page_lines = pages[pno]
        found_on_page = 0
        page_text = " ".join([t for (t, _x) in page_lines])
        long_text_blocks = [t for (t, _x) in page_lines if len(t) > 100]
        if len(long_text_blocks) > 3 and pno > start_pno + 2:
            break
        if any(indicator in page_text.lower() for indicator in [
            'requirement', 'guidance', 'disclosure', 'reporting', 'organization should',
            'this standard', 'the organization is required'
        ]) and pno > start_pno + 2:
            break
 
        for i, (text, x0) in enumerate(page_lines):
            if re.match(r'^GRI\s+\d+[A-Za-z]?\s*:', text, re.IGNORECASE):
                if i + 1 < len(page_lines):
                    next_text, next_x0 = page_lines[i + 1]
                    if next_text.strip().isdigit():
                        page_label = next_text.strip()
                        try:
                            page_num = int(page_label)
                            if (page_num <= 2000 and page_num >= 3 and
                                x0 is not None and 50 <= x0 <= 100 and
                                next_x0 is not None and next_x0 > 400):
                                title = norm_ws(text)
                                results_raw.append((title, page_label, x0, pno + 1))
                                found_on_page += 1
                        except:
                            pass
                continue
 
            for pat in TOC_LINE_RES:
                m = pat.match(text)
                if not m:
                    continue
                title = norm_ws(m.group("title"))
                page_label = m.group("page")
                if len(title) < 3 or not re.search(r"[A-Za-z]", title):
                    continue
                try:
                    page_num = int(page_label) if page_label.isdigit() else roman_to_int(page_label)
                    if page_num and page_num > 2000:
                        continue
                except:
                    pass
                results_raw.append((title, page_label, x0, pno + 1))
                found_on_page += 1
                break
       
        if found_on_page == 0:
            misses += 1
        else:
            misses = 0
        if misses >= MAX_MISSES and len(results_raw) > 5:
            break
        pno += 1
 
    # Assign hierarchy levels based on x positions
    levels = infer_levels_from_indents(results_raw)
    items = []
    for (title, page_label, x0, src_page), lvl in zip(results_raw, levels):
        items.append({
            "level": int(lvl),
            "title": title,
            "page_label": page_label,
            "page_number": to_int_if_numeric(page_label),
            "source_page": int(src_page)
        })
    return items
 
# ---------------- Main extraction ----------------
 
def extract_index(pdf_path: str, prefer_toc: bool = True):
    """
    Extracts the TOC as printed in the document, not from bookmarks,
    unless TOC cannot be parsed.
    prefer_toc: if True, always try TOC text parsing first.
    """
    pages = None
    used_fitz = True
    try:
        pages = load_pages_with_positions_pymupdf(pdf_path)
    except Exception:
        used_fitz = False
        pages = load_pages_text_pdfminer(pdf_path)
 
    cand_pages = find_toc_start_pages(pages)
    if not cand_pages:
        cand_pages = [0]
    if len(cand_pages) > 1:
        best_page = cand_pages[0]  # Initialize with first candidate instead of the list
        max_gri_count = 0
        for pno in cand_pages:
            text = " ".join([t for (t, _x) in pages[pno]])
            gri_count = len(re.findall(r'GRI\s+\d+[A-Za-z]?\s*:', text, re.IGNORECASE))
            if gri_count > max_gri_count:
                max_gri_count = gri_count
                best_page = pno
        start_pno = best_page
    else:
        start_pno = cand_pages[-1] if cand_pages else 0
 
    # Prefer TOC extraction
    toc_items = parse_toc_from_pages(pages, start_pno)
    if toc_items:
        return {
            "source_pdf": str(Path(pdf_path).resolve()),
            "extraction_method": "toc_text_with_positions" if used_fitz else "toc_text_fallback",
            "items": toc_items
        }
 
    # Fallback if no TOC was found
    try:
        outline_items = extract_outline_pymupdf(pdf_path)
        if outline_items:
            return {
                "source_pdf": str(Path(pdf_path).resolve()),
                "extraction_method": "outline",
                "items": outline_items
            }
    except Exception:
        pass
 
    return {
        "source_pdf": str(Path(pdf_path).resolve()),
        "extraction_method": "none_found",
        "items": []
    }
 
# ---------------- New Function for PDF and Folder Input ----------------
 
def extract_index_to_folder(pdf_path: str, folder_path: str):
    """
    Extract index from PDF and save JSON to specified folder.
    
    Args:
        pdf_path (str): Path to the PDF file
        folder_path (str): Path to the folder where JSON will be saved
    
    Returns:
        str: Path to the created JSON file
    """
    # Extract the index data
    data = extract_index(pdf_path)
    
    # Create output filename based on PDF name
    pdf_name = Path(pdf_path).stem
    json_filename = f"{pdf_name}_index.json"
    
    # Create full output path
    output_path = Path(folder_path) / json_filename
    
    # Save the JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved index JSON -> {output_path}")
    print(f"Items extracted: {len(data.get('items', []))}")
    
    return str(output_path)

# # Example usage with direct paths
# if __name__ == "__main__":
#     # Direct usage with PDF path and upload folder
#     pdf_file = "uploads/pdf/NIST.SP.800-53r5.pdf"  # Replace with your PDF path
#     upload_folder = "uploads_12345"  # Replace with your upload folder path
    
#     # Extract index and save to upload folder
#     result_path = extract_index_to_folder(pdf_file, upload_folder)
#     print(f"Index extraction completed: {result_path}")

