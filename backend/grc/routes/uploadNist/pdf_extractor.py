"""
PDF Section Extractor Wrapper

This module provides a simple interface to extract sections from PDF files
using the existing index_content_extractor module.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_sections_from_pdf(
    pdf_path: str,
    output_dir: str = None,
    index_json_path: str = None,
    force_full_extraction: bool = False,
) -> Optional[str]:
    """
    Extract sections from a PDF file.
    
    This function wraps the existing PDF extraction logic to provide a simple interface
    for extracting sections from framework amendment PDFs.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted sections (optional, auto-generated if not provided)
        index_json_path: Path to index JSON file (optional, will be extracted if not provided)
        
    Returns:
        Path to the sections directory or None if failed
    """
    try:
        from .index_content_extractor import process_pdf_sections
        from .pdf_index_extractor import extract_and_save_index
        
        # Create output directory if not provided
        if output_dir is None:
            pdf_name = Path(pdf_path).stem
            output_dir = os.path.join(os.path.dirname(pdf_path), f"sections_{pdf_name}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        if force_full_extraction:
            logger.info(f"Force full-document extraction for {pdf_path}")
            return _extract_full_pdf_as_single_section(pdf_path, output_dir)

        # Extract index if not provided
        if index_json_path is None or not os.path.exists(index_json_path):
            logger.info(f"Extracting index from PDF: {pdf_path}")
            index_json_path = os.path.join(output_dir, "index.json")
            
            try:
                index_data = extract_and_save_index(pdf_path, index_json_path)
                if not index_data or not index_data.get('items'):
                    logger.warning("No index items found in PDF, will extract all pages")
                    # If no index, create a simple single-section structure
                    return _extract_full_pdf_as_single_section(pdf_path, output_dir)
            except Exception as e:
                logger.warning(f"Could not extract index: {str(e)}, will extract all pages")
                return _extract_full_pdf_as_single_section(pdf_path, output_dir)
        
        # Extract sections using the index
        logger.info(f"Extracting sections from PDF using index: {index_json_path}")
        process_pdf_sections(
            pdf_path=pdf_path,
            index_json_path=index_json_path,
            output_dir=output_dir,
            verbose=True
        )
        
        # Verify sections were created
        sections_dir = os.path.join(output_dir, "sections")
        if os.path.exists(sections_dir):
            logger.info(f"Successfully extracted sections to: {sections_dir}")
            return output_dir
        else:
            logger.error("Sections directory was not created")
            return None
            
    except ImportError as e:
        logger.error(f"Required module not found: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error extracting sections from PDF: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def _extract_full_pdf_as_single_section(pdf_path: str, output_dir: str) -> Optional[str]:
    """
    Extract the entire PDF as per-page sections when no index is available.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted content
        
    Returns:
        Path to the sections directory or None if failed
    """
    doc = None
    try:
        import fitz  # PyMuPDF
        
        logger.info("Extracting entire PDF as sequential per-page sections")
        
        # Open PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        logger.info(f"PDF has {total_pages} pages, extracting all content page-by-page...")
        
        # Create sections directory structure
        sections_dir = os.path.join(output_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)
        
        aggregated_text = []
        
        for page_num in range(total_pages):
            try:
                page = doc[page_num]
                page_text = page.get_text("text")
                
                # Create a folder for each page so policy extractor treats them as sections
                page_folder = os.path.join(sections_dir, f"page_{page_num + 1:04d}")
                os.makedirs(page_folder, exist_ok=True)
                
                page_data = {
                    "name": f"Page {page_num + 1}",
                    "level": 1,
                    "start_page": page_num + 1,
                    "end_page": page_num + 1,
                    "total_pages": 1,
                    "content": page_text,
                    "extraction_method": "per_page_fallback"
                }
                
                with open(os.path.join(page_folder, "content.json"), 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, ensure_ascii=False, indent=2)
                
                aggregated_text.append(f"\n\n--- Page {page_num + 1} ---\n\n{page_text}")
                
                if (page_num + 1) % 10 == 0:
                    logger.info(f"Extracted {page_num + 1}/{total_pages} pages...")
            except Exception as e:
                logger.warning(f"Error extracting page {page_num + 1}: {str(e)}")
                continue
        
        # Also save full document aggregation for completeness
        full_doc_folder = os.path.join(sections_dir, "full_document")
        os.makedirs(full_doc_folder, exist_ok=True)
        
        full_content_data = {
            "name": Path(pdf_path).stem,
            "level": 1,
            "start_page": 1,
            "end_page": total_pages,
            "total_pages": total_pages,
            "content": ''.join(aggregated_text),
            "extraction_method": "full_document_sequential"
        }
        
        with open(os.path.join(full_doc_folder, "content.json"), 'w', encoding='utf-8') as f:
            json.dump(full_content_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved per-page sections to: {sections_dir}")
        logger.info(f"Total characters extracted: {len(''.join(aggregated_text))}")
        
        return output_dir
        
    except ImportError:
        logger.error("PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF")
        return None
    except Exception as e:
        logger.error(f"Error extracting full PDF: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    finally:
        # Ensure document is closed
        if doc is not None:
            try:
                doc.close()
            except:
                pass

