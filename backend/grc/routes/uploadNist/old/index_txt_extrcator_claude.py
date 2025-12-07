import json
import re
from pathlib import Path
from collections import Counter
 
# ---------- Normalization helpers ----------
DASHES = r"[\u2010\u2011\u2012\u2013\u2014\u2212]"
 
def norm_dashes(s: str) -> str:
    return re.sub(DASHES, "-", s)
 
def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
 
def slug(s: str, maxlen: int = 40) -> str:
    """Create a filesystem-safe slug from a string, with shorter max length to avoid path issues."""
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_+", "_", s).strip("_")
    if len(s) > maxlen:
        s = s[:maxlen].rstrip("_")
    return s or "section"
 
# ---------- PDF helpers ----------
def load_doc(pdf_path: str):
    import fitz  # PyMuPDF
    return fitz.open(pdf_path)

# ---------- Extract printed page numbers from PDF ----------
def extract_printed_page_numbers(doc):
    """Extract printed page numbers from PDF footers/headers to create a mapping."""
    import fitz  # PyMuPDF
    printed_to_pdf_mapping = {}
    
    for pdf_page_num in range(len(doc)):
        page = doc[pdf_page_num]
        
        # Get text from the entire page
        text = page.get_text("text")
        
        # Look for page numbers in various formats
        # Common patterns: "Page X", "X", "Page X of Y", etc.
        page_number_patterns = [
            r'page\s+(\d+)',  # "Page 123"
            r'^\s*(\d+)\s*$',  # Standalone number
            r'(\d+)\s+of\s+\d+',  # "123 of 456"
            r'(\d+)\s*$',  # Number at end of line
        ]
        
        for pattern in page_number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    printed_num = int(match)
                    if 1 <= printed_num <= 1000:  # Reasonable page number range
                        printed_to_pdf_mapping[printed_num] = pdf_page_num
                        break
                except ValueError:
                    continue
        
        # Also check for page numbers in footer areas (bottom 20% of page)
        footer_rect = fitz.Rect(page.rect.x0, page.rect.y0 * 0.8 + page.rect.y1 * 0.2, page.rect.x1, page.rect.y1)
        footer_text = page.get_text("text", clip=footer_rect)
        for pattern in page_number_patterns:
            matches = re.findall(pattern, footer_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    printed_num = int(match)
                    if 1 <= printed_num <= 1000:
                        printed_to_pdf_mapping[printed_num] = pdf_page_num
                        break
                except ValueError:
                    continue
    
    return printed_to_pdf_mapping

# ---------- Detect printed page number offset ----------
def detect_page_offset(items, doc):
    """Detect the offset between printed page numbers and PDF page numbers."""
    printed_to_pdf_mapping = extract_printed_page_numbers(doc)
    
    if not printed_to_pdf_mapping:
        print("[WARN] No printed page numbers found in PDF")
        return 0
    
    # Find the most common offset by comparing printed page numbers from index
    # with the detected printed page numbers in the PDF
    offsets = []
    
    for item in items:
        printed_page = item.get("page_number")
        if not isinstance(printed_page, int) or printed_page < 1:
            continue
            
        # Look for this printed page number in our mapping
        if printed_page in printed_to_pdf_mapping:
            pdf_page = printed_to_pdf_mapping[printed_page]
            offset = pdf_page - (printed_page - 1)  # printed_page is 1-indexed, pdf_page is 0-indexed
            offsets.append(offset)
    
    if offsets:
        # Use the most common offset
        most_common_offset = Counter(offsets).most_common(1)[0][0]
        print(f"[INFO] Detected printed→PDF page offset: {most_common_offset}")
        print(f"[INFO] Found {len(printed_to_pdf_mapping)} printed page numbers in PDF")
        return most_common_offset
    else:
        print("[WARN] Could not detect offset from printed page numbers")
        return 0

# ---------- Assign start pages (with offset) ----------
def assign_start_pages(items, doc):
    offset = detect_page_offset(items, doc)
    starts = {}
    
    for it in items:
        printed_page = it.get("page_number")
        if isinstance(printed_page, int) and printed_page >= 1:
            # Convert printed page (1-indexed) to PDF page (0-indexed)
            pdf_page = (printed_page - 1) + offset
            pdf_page = max(0, min(pdf_page, len(doc) - 1))
            starts[it["title"]] = pdf_page
        else:
            starts[it["title"]] = None
    
    return [
        {
            "title": it["title"],
            "start": starts.get(it["title"]),
            "printed_page": it.get("page_number"),
            "source_page": it.get("source_page"),
            "level": it.get("level", 1)
        }
        for it in items
    ]
 
# ---------- Hierarchy ----------
def build_hierarchy(items):
    hierarchy = []
    stack = []
    for item in items:
        level = item.get("level", 1)
        while stack and stack[-1]["level"] >= level:
            stack.pop()
        node = {
            "title": item["title"],
            "level": level,
            "page_number": item.get("page_number"),
            "page_label": item.get("page_label"),
            "source_page": item.get("source_page"),
            "children": []
        }
        if stack:
            stack[-1]["children"].append(node)
        else:
            hierarchy.append(node)
        stack.append(node)
    return hierarchy
 
def flatten_hierarchy_with_paths(hierarchy, parent_path="", parent_counter=1):
    flat_list = []
    for idx, item in enumerate(hierarchy, start=parent_counter):
        folder = f"{idx:03d}-{slug(item['title'])}"
        current_path = f"{parent_path}/{folder}" if parent_path else folder
        flat_item = {
            "title": item["title"],
            "level": item["level"],
            "page_number": item.get("page_number"),
            "page_label": item.get("page_label"),
            "source_page": item.get("source_page"),
            "folder_path": current_path,
            "children": item["children"]
        }
        flat_list.append(flat_item)
        if item["children"]:
            flat_list.extend(flatten_hierarchy_with_paths(item["children"], current_path, 1))
    return flat_list
 
# ---------- Compute ranges based on printed page numbers ----------
def compute_ranges_by_printed_pages(flat_items, doc_page_count):
    """Compute page ranges based on printed page numbers instead of PDF page numbers."""
    items = [it for it in flat_items if it.get("start") is not None]
    items.sort(key=lambda x: x["start"])
    
    for i, item in enumerate(items):
        printed_start = item.get("printed_page")
        if not printed_start:
            continue
            
        # Find the next item at the same or higher level
        printed_end = doc_page_count - 1  # Default to end of document
        
        for next_item in items[i+1:]:
            next_level = next_item.get("level", 1)
            current_level = item.get("level", 1)
            
            # If next item is at same or higher level, it marks the end of current section
            if next_level <= current_level:
                next_printed = next_item.get("printed_page")
                if next_printed and next_printed > printed_start:
                    printed_end = next_printed - 1
                    break
        
        # Convert printed page range to PDF page range
        offset = item["start"] - (printed_start - 1)  # Calculate offset from this item
        
        pdf_start = item["start"]
        pdf_end = (printed_end - 1) + offset  # Convert printed end to PDF page
        
        # Ensure PDF page numbers are within bounds
        pdf_end = max(pdf_start, min(pdf_end, doc_page_count - 1))
        
        item["printed_start"] = printed_start
        item["printed_end"] = printed_end
        item["end"] = pdf_end
    
    return items
 
# ---------- Extract section text with intra-page cropping ----------
def extract_section_text(doc, start_page, end_page, heading_title, next_heading_title=None):
    start_norm = norm_ws(norm_dashes(heading_title)).lower()
    end_norm = norm_ws(norm_dashes(next_heading_title)).lower() if next_heading_title else None
    parts = []
    for pno in range(start_page, end_page + 1):
        txt = doc[pno].get_text("text")
        txt_norm = norm_ws(norm_dashes(txt))
        # Trim start page
        if pno == start_page:
            idx = txt_norm.lower().find(start_norm)
            if idx != -1:
                txt_norm = txt_norm[idx:]
        # Trim end page
        if pno == end_page and end_norm:
            idx_end = txt_norm.lower().find(end_norm)
            if idx_end != -1:
                txt_norm = txt_norm[:idx_end]
        parts.append(txt_norm)
    return "\n\n".join(parts).strip()
 
# ---------- Extract PDF pages ----------
def extract_pdf_pages(doc, start_page, end_page, output_path):
    """
    Extract specific pages from a PDF and save as a new PDF file.
    """
    try:
        import fitz  # PyMuPDF
        # Create a new PDF document
        new_doc = fitz.open()
       
        # Copy pages from the original document
        for page_num in range(start_page, end_page + 1):
            if page_num < len(doc):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
       
        # Save the new PDF
        new_doc.save(str(output_path))
        new_doc.close()
       
        print(f"[INFO] Saved PDF section: {output_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to extract PDF pages {start_page}-{end_page}: {e}")
        return False
 
# ---------- Save sections ----------
def save_sections_hierarchical(doc, sections_with_paths, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, sec in enumerate(sections_with_paths):
        if sec.get("start") is None:
            continue
        next_title = sections_with_paths[i+1]["title"] if i+1 < len(sections_with_paths) else None
        extracted = extract_section_text(doc, sec["start"], sec["end"], sec["title"], next_title)
        # Add bold title at top (Markdown format)
        content = f"**{sec['title']}**\n\n" + extracted
        folder_path = out_dir / sec["folder_path"]
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Could not create directory {folder_path}: {e}")
            print(f"[ERROR] Path length: {len(str(folder_path))}")
            # Try with a shorter path
            short_folder = f"{i+1:03d}-section_{i+1}"
            folder_path = out_dir / short_folder
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Using shorter path: {folder_path}")
            sec["folder_path"] = short_folder
       
        # Save JSON content
        rec = {
            "name": sec["title"],
            "level": sec.get("level", 1),
            "printed_start": sec.get("printed_start"),
            "printed_end": sec.get("printed_end"),
            "pdf_start": int(sec["start"]),
            "pdf_end": int(sec["end"]),
            "printed_page": sec.get("printed_page"),
            "content": content
        }
        with open(folder_path / "content.json", "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
 
        # Extract and save PDF pages
        pdf_filename = f"{slug(sec['title'])}.pdf"
        pdf_path = folder_path / pdf_filename
        extract_pdf_pages(doc, sec["start"], sec["end"], pdf_path)
       
        manifest.append({
            "folder": sec["folder_path"],
            "title": sec["title"],
            "level": sec.get("level", 1),
            "printed_start": rec["printed_start"],
            "printed_end": rec["printed_end"],
            "pdf_start": rec["pdf_start"],
            "pdf_end": rec["pdf_end"],
            "printed_page": rec.get("printed_page"),
            "has_children": bool(sec.get("children")),
            "pdf_file": pdf_filename
        })
    return manifest
 
# ---------- Main ----------
# Configuration - Set your folder path here
INPUT_FOLDER = "upload_12345"  # Change this to your folder path

def main(folder_path):
    """
    Extract sections from PDF using index JSON.
    
    Args:
        folder_path (str): Path to folder containing PDF and JSON index files
    """
    print("=== PDF Section Extractor (printed page number based) ===")
    
    # Convert to Path object and resolve
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists():
        raise SystemExit(f"Folder does not exist: {folder}")
    
    # Find PDF and JSON files in the folder
    pdf_files = list(folder.glob("*.pdf"))
    json_files = list(folder.glob("*_index.json"))
    
    if not pdf_files:
        raise SystemExit(f"No PDF files found in {folder}")
    if not json_files:
        raise SystemExit(f"No index JSON files found in {folder}")
    
    # Use the first PDF and JSON file found
    pdf_path = str(pdf_files[0])
    idx_path = str(json_files[0])
    
    print(f"Using PDF: {pdf_path}")
    print(f"Using index: {idx_path}")
    
    # Create output directory as "extracted_sections" inside the input folder
    out_dir = folder / "extracted_sections"
    print(f"Output directory: {out_dir}")

    with open(idx_path, "r", encoding="utf-8") as f:
        index_obj = json.load(f)
    items = index_obj.get("items", [])
    if not items:
        raise SystemExit("No items in the index JSON.")

    norm_items = []
    for it in items:
        title = norm_ws(norm_dashes(it.get("title", "")))
        if not title:
            continue
        norm_items.append({
            "title": title,
            "level": it.get("level", 1),
            "page_number": it.get("page_number"),
            "page_label": it.get("page_label"),
            "source_page": it.get("source_page"),
        })

    hierarchy = build_hierarchy(norm_items)
    flat_with_paths = flatten_hierarchy_with_paths(hierarchy)
    doc = load_doc(pdf_path)

    starts = assign_start_pages(norm_items, doc)
    title_to_start = {s["title"]: s["start"] for s in starts}

    sections_with_paths = []
    for item in flat_with_paths:
        start_page = title_to_start.get(item["title"])
        if start_page is not None:
            item["start"] = start_page
            item["printed_page"] = next((it.get("page_number") for it in norm_items if it["title"] == item["title"]), None)
            sections_with_paths.append(item)

    resolved_sections = compute_ranges_by_printed_pages(sections_with_paths, len(doc))
    unresolved_sections = [s for s in flat_with_paths if s.get("start") is None]

    sections_dir = out_dir / "sections"
    manifest = save_sections_hierarchical(doc, resolved_sections, sections_dir)

    manifest_obj = {
        "source_pdf": str(Path(pdf_path).resolve()),
        "index_json": str(Path(idx_path).resolve()),
        "structure_type": "hierarchical",
        "sections_written": manifest,
        "unresolved_titles": [u["title"] for u in unresolved_sections]
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "sections_index.json", "w", encoding="utf-8") as f:
        json.dump(manifest_obj, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Sections written: {len(manifest)}")
    if unresolved_sections:
        print("Unresolved titles:")
        for u in unresolved_sections:
            print(f" - {u['title']}")
    print(f"Output folder: {out_dir.resolve()}")
    
    return out_dir

# Legacy function for backward compatibility
def process_pdf_with_index(pdf_path, index_json_path, output_dir=None):
    """
    Legacy function that takes separate PDF and JSON paths.
    
    Args:
        pdf_path (str): Path to PDF file
        index_json_path (str): Path to index JSON file
        output_dir (str, optional): Output directory. If None, creates 'extracted_sections' in PDF's directory
    """
    if output_dir is None:
        output_dir = str(Path(pdf_path).parent / "extracted_sections")
    
    # Create a temporary folder structure and copy files
    import shutil
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_pdf = Path(temp_dir) / Path(pdf_path).name
        temp_json = Path(temp_dir) / Path(index_json_path).name
        
        shutil.copy2(pdf_path, temp_pdf)
        shutil.copy2(index_json_path, temp_json)
        
        # Process using the new main function
        result_dir = main(temp_dir)
        
        # Copy results to desired output location
        if Path(output_dir).exists():
            shutil.rmtree(output_dir)
        shutil.copytree(result_dir, output_dir)
        
        return output_dir

if __name__ == "__main__":
    # Load folder path directly from variable
    main(INPUT_FOLDER)