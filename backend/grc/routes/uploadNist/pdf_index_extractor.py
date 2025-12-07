"""
PDF Table of Contents / Index Extractor

This module extracts the Table of Contents (TOC) or Index from PDF documents.
It can be used as a standalone CLI tool or imported into other Python code.

Usage as a module:
    # Simple extraction - returns dict
    from extractor import extract_index
    data = extract_index("document.pdf")
    print(f"Found {len(data['items'])} TOC items")
    
    # Extract and save to JSON
    from extractor import extract_and_save_index
    data = extract_and_save_index("document.pdf", "output.json")
    
    # Access the extracted items
    for item in data['items']:
        indent = "  " * (item['level'] - 1)
        print(f"{indent}{item['title']} - Page {item['page_number']}")

Usage as CLI:
    python extractor.py -i document.pdf -o output.json
    python extractor.py -i document.pdf  # auto-generates output filename
"""

import re
import json
import argparse
from pathlib import Path

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

def roman_to_int(s: str) -> int | None:
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

def to_int_if_numeric(page_label: str) -> int | None:
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
    Extracts the Table of Contents (TOC) or Index from a PDF document.
    
    This function first attempts to parse the TOC as printed in the document.
    If that fails, it falls back to extracting the PDF's internal bookmarks/outline.
    
    Args:
        pdf_path (str): Path to the PDF file to extract from
        prefer_toc (bool): If True, always try TOC text parsing first (default: True)
    
    Returns:
        dict: A dictionary containing:
            - 'source_pdf': Absolute path to the source PDF
            - 'extraction_method': Method used ('toc_text_with_positions', 'toc_text_fallback', 'outline', or 'none_found')
            - 'items': List of TOC items, each containing:
                - 'level': Hierarchy level (1, 2, 3, etc.)
                - 'title': Section/chapter title
                - 'page_label': Page number as string
                - 'page_number': Page number as integer (if numeric)
                - 'source_page': Page where this TOC entry was found
    
    Example:
        >>> data = extract_index("document.pdf")
        >>> print(f"Found {len(data['items'])} items")
        >>> for item in data['items']:
        >>>     print(f"{item['title']} - Page {item['page_number']}")
    """
    print(f"[DEBUG] pdf_index_extractor.extract_index called")
    print(f"[DEBUG] PDF path: {pdf_path}")
    print(f"[DEBUG] Prefer TOC: {prefer_toc}")
    
    pages = None
    used_fitz = True
    try:
        print(f"[DEBUG] Attempting to load pages with PyMuPDF...")
        pages = load_pages_with_positions_pymupdf(pdf_path)
        print(f"[DEBUG] Successfully loaded pages with PyMuPDF")
    except Exception as e:
        used_fitz = False
        print(f"[DEBUG] PyMuPDF loading failed: {str(e)}")
        print(f"[DEBUG] Falling back to PDFMiner...")
        try:
            pages = load_pages_text_pdfminer(pdf_path)
            print(f"[DEBUG] Successfully loaded pages with PDFMiner")
        except Exception as e:
            print(f"[ERROR] PDFMiner loading also failed: {str(e)}")
            import traceback
            print(f"[DEBUG] Exception traceback: {traceback.format_exc()}")
            raise

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

def save_index_to_json(index_data: dict, output_path: str):
    """
    Save extracted index data to a JSON file.
    
    Args:
        index_data (dict): The index data returned by extract_index()
        output_path (str): Path where JSON file should be saved
    
    Returns:
        str: The absolute path where the file was saved
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    return str(out_file.resolve())

def extract_and_save_index(pdf_path: str, output_path: str = None, prefer_toc: bool = True):
    """
    Convenience function that extracts index and saves to JSON in one call.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_path (str, optional): Output JSON path. If None, uses <pdf_name>_index.json
        prefer_toc (bool): Whether to prefer TOC text parsing (default: True)
    
    Returns:
        dict: The extracted index data (same as extract_index())
    """
    print(f"[DEBUG] pdf_index_extractor.extract_and_save_index called")
    print(f"[DEBUG] PDF path: {pdf_path}")
    print(f"[DEBUG] Output path: {output_path}")
    print(f"[DEBUG] Prefer TOC: {prefer_toc}")
    
    try:
        print(f"[DEBUG] Calling extract_index function...")
        data = extract_index(pdf_path, prefer_toc=prefer_toc)
        print(f"[DEBUG] extract_index completed successfully")
        
        if output_path is None:
            output_path = str(Path(pdf_path).with_suffix("")) + "_index.json"
            print(f"[DEBUG] No output path provided, using default: {output_path}")
        
        print(f"[DEBUG] Saving index data to JSON file: {output_path}")
        save_index_to_json(data, output_path)
        print(f"[DEBUG] Index data saved successfully")
        
        print(f"[DEBUG] Items extracted: {len(data.get('items', []))}")
        print(f"[DEBUG] Extraction method: {data.get('extraction_method', 'unknown')}")
        
        return data
    except Exception as e:
        print(f"[ERROR] Error in extract_and_save_index: {str(e)}")
        import traceback
        print(f"[DEBUG] Exception traceback: {traceback.format_exc()}")
        raise

# ---------------- CLI ----------------

def main():
    """CLI entry point for extracting PDF index/TOC."""
    ap = argparse.ArgumentParser(description="Extract Table of Contents / Index (heading + page) from a PDF to JSON.")
    ap.add_argument("-i", "--input", required=True, help="Path to PDF file")
    ap.add_argument("-o", "--output", default=None, help="Path to output JSON (default: <pdfname>_index.json)")
    ap.add_argument("--prefer-outline", action="store_true", help="Prefer PDF outline/bookmarks over text TOC")
    args = ap.parse_args()

    pdf_path = args.input
    prefer_toc = not args.prefer_outline
    
    data = extract_and_save_index(pdf_path, args.output, prefer_toc=prefer_toc)
    
    output_file = args.output or str(Path(pdf_path).with_suffix("")) + "_index.json"
    print(f"Saved index JSON -> {output_file}")
    print(f"Items extracted: {len(data.get('items', []))}")
    print(f"Extraction method: {data.get('extraction_method', 'unknown')}")

if __name__ == "__main__":
    main()
