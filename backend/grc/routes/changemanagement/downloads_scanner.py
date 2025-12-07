"""
Downloads Folder Scanner

This module automatically scans the downloads folder for PDF files and processes them.
It matches PDFs to frameworks and triggers the complete amendment processing pipeline.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from django.conf import settings
from grc.models import Framework

logger = logging.getLogger(__name__)


class DownloadsScanner:
    """Scans downloads folder and processes PDFs automatically."""
    
    def __init__(self, downloads_dir: str = None):
        """
        Initialize the downloads scanner.
        
        Args:
            downloads_dir: Path to downloads folder (default: settings.BASE_DIR/downloads)
        """
        if downloads_dir is None:
            downloads_dir = os.path.join(settings.BASE_DIR, 'downloads')
        
        self.downloads_dir = downloads_dir
        self.processed_file = os.path.join(downloads_dir, '.processed_files.json')
        self.processed_files = self._load_processed_files()
        
    def _load_processed_files(self) -> Dict[str, Any]:
        """Load list of already processed files."""
        if os.path.exists(self.processed_file):
            try:
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load processed files list: {str(e)}")
                return {}
        return {}
    
    def _save_processed_files(self):
        """Save list of processed files."""
        try:
            os.makedirs(os.path.dirname(self.processed_file), exist_ok=True)
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save processed files list: {str(e)}")
    
    def _is_processed(self, file_path: str) -> bool:
        """Check if a file has already been processed."""
        file_key = os.path.basename(file_path)
        file_stat = os.stat(file_path)
        file_size = file_stat.st_size
        file_mtime = file_stat.st_mtime
        
        if file_key in self.processed_files:
            processed_info = self.processed_files[file_key]
            # Check if file has been modified since last processing
            if (processed_info.get('size') == file_size and 
                processed_info.get('mtime') == file_mtime):
                return True
        
        return False
    
    def mark_as_processed(self, file_path: str, framework_id: int, result: Dict[str, Any]):
        """Mark a file as processed."""
        file_key = os.path.basename(file_path)
        try:
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            file_mtime = file_stat.st_mtime
        except FileNotFoundError:
            # If file doesn't exist (e.g. temp file), just use current time/0 size
            # This prevents crashing if cleanup happened
            file_size = 0
            file_mtime = datetime.now().timestamp()
        
        self.processed_files[file_key] = {
            'file_path': file_path,
            'framework_id': framework_id,
            'processed_date': datetime.now().isoformat(),
            'size': file_size,
            'mtime': file_mtime,
            'result': result
        }
        self._save_processed_files()
    
    def _match_framework_from_filename(self, filename: str) -> Optional[Framework]:
        """
        Try to match a framework from the PDF filename.
        
        Args:
            filename: Name of the PDF file
            
        Returns:
            Framework object if matched, None otherwise
        """
        filename_lower = filename.lower()
        
        # Get all frameworks
        frameworks = Framework.objects.all()
        
        # Try exact name matching first
        for framework in frameworks:
            framework_name_lower = framework.FrameworkName.lower()
            
            # Check if framework name appears in filename
            if framework_name_lower in filename_lower:
                logger.info(f"Matched '{filename}' to framework: {framework.FrameworkName}")
                return framework
            
            # Check common abbreviations
            if self._check_abbreviation_match(framework_name_lower, filename_lower):
                logger.info(f"Matched '{filename}' to framework (by abbreviation): {framework.FrameworkName}")
                return framework
        
        # Try pattern matching for common frameworks
        framework_patterns = {
            r'nist.*800.*53': ['NIST', '800-53', 'SP 800-53'],
            r'nist.*csf': ['NIST', 'CSF', 'Cybersecurity Framework'],
            r'pci.*dss': ['PCI', 'DSS', 'Payment Card Industry'],
            r'iso.*27001': ['ISO', '27001'],
            r'iso.*27002': ['ISO', '27002'],
            r'hipaa': ['HIPAA', 'Health Insurance Portability'],
            r'tcfd': ['TCFD', 'Task Force on Climate'],
            r'gri': ['GRI', 'Global Reporting Initiative'],
        }
        
        for pattern, keywords in framework_patterns.items():
            if re.search(pattern, filename_lower):
                # Try to find framework matching these keywords
                for framework in frameworks:
                    framework_name_lower = framework.FrameworkName.lower()
                    if all(keyword.lower() in framework_name_lower for keyword in keywords):
                        logger.info(f"Matched '{filename}' to framework (by pattern): {framework.FrameworkName}")
                        return framework
        
        logger.warning(f"Could not match '{filename}' to any framework")
        return None
    
    def _check_abbreviation_match(self, framework_name: str, filename: str) -> bool:
        """Check if framework matches by common abbreviations."""
        # Extract potential abbreviations from framework name
        words = framework_name.split()
        if len(words) >= 2:
            # Try first letters of words
            abbreviation = ''.join([w[0] for w in words if len(w) > 0])
            if len(abbreviation) >= 3 and abbreviation.lower() in filename:
                return True
        
        return False
    
    def scan_and_process(self, process_all: bool = False) -> Dict[str, Any]:
        """
        Scan downloads folder and process any unprocessed PDFs.
        
        Args:
            process_all: If True, process all PDFs even if already processed
            
        Returns:
            Dictionary with processing results
        """
        if not os.path.exists(self.downloads_dir):
            logger.warning(f"Downloads directory does not exist: {self.downloads_dir}")
            return {
                'success': False,
                'error': f'Downloads directory not found: {self.downloads_dir}',
                'processed': [],
                'skipped': [],
                'failed': []
            }
        
        # Find all PDF files
        pdf_files = []
        for file in os.listdir(self.downloads_dir):
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(self.downloads_dir, file)
                if os.path.isfile(file_path):
                    pdf_files.append(file_path)
        
        if not pdf_files:
            logger.info("No PDF files found in downloads folder")
            return {
                'success': True,
                'message': 'No PDF files found in downloads folder',
                'processed': [],
                'skipped': [],
                'failed': []
            }
        
        logger.info(f"Found {len(pdf_files)} PDF file(s) in downloads folder")
        
        results = {
            'success': True,
            'processed': [],
            'skipped': [],
            'failed': []
        }
        
        # Process each PDF
        for pdf_path in pdf_files:
            try:
                # Check if already processed
                if not process_all and self._is_processed(pdf_path):
                    logger.info(f"Skipping already processed file: {os.path.basename(pdf_path)}")
                    results['skipped'].append({
                        'file': os.path.basename(pdf_path),
                        'reason': 'Already processed'
                    })
                    continue
                
                # Try to match framework
                framework = self._match_framework_from_filename(os.path.basename(pdf_path))
                
                if not framework:
                    logger.warning(f"Could not match framework for: {os.path.basename(pdf_path)}")
                    results['failed'].append({
                        'file': os.path.basename(pdf_path),
                        'reason': 'Could not match to framework'
                    })
                    continue
                
                # Process the PDF
                logger.info(f"Processing PDF: {os.path.basename(pdf_path)} for framework: {framework.FrameworkName}")
                
                result = self._process_pdf(pdf_path, framework)
                
                if result.get('success'):
                    # Mark as processed
                    self.mark_as_processed(pdf_path, framework.FrameworkId, result)
                    results['processed'].append({
                        'file': os.path.basename(pdf_path),
                        'framework': framework.FrameworkName,
                        'framework_id': framework.FrameworkId,
                        'result': result
                    })
                    logger.info(f"Successfully processed: {os.path.basename(pdf_path)}")
                else:
                    results['failed'].append({
                        'file': os.path.basename(pdf_path),
                        'framework': framework.FrameworkName,
                        'reason': result.get('error', 'Processing failed')
                    })
                    logger.error(f"Failed to process: {os.path.basename(pdf_path)} - {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error processing {os.path.basename(pdf_path)}: {str(e)}")
                results['failed'].append({
                    'file': os.path.basename(pdf_path),
                    'reason': str(e)
                })
        
        # Summary
        total = len(results['processed']) + len(results['skipped']) + len(results['failed'])
        results['summary'] = {
            'total_files': len(pdf_files),
            'processed': len(results['processed']),
            'skipped': len(results['skipped']),
            'failed': len(results['failed'])
        }
        
        logger.info(f"Scan complete: {len(results['processed'])} processed, {len(results['skipped'])} skipped, {len(results['failed'])} failed")
        
        return results
    
    def _process_pdf(self, pdf_path: str, framework: Framework) -> Dict[str, Any]:
        """
        Process a single PDF file for a framework.
        
        Args:
            pdf_path: Path to the PDF file
            framework: Framework object
            
        Returns:
            Processing result dictionary
        """
        try:
            from .amendment_processor import process_downloaded_amendment
            
            # Determine amendment date
            amendment_date = None
            if framework.latestAmmendmentDate:
                if isinstance(framework.latestAmmendmentDate, str):
                    amendment_date = framework.latestAmmendmentDate
                else:
                    amendment_date = framework.latestAmmendmentDate.strftime("%Y-%m-%d")
            elif framework.latestComparisionCheckDate:
                if isinstance(framework.latestComparisionCheckDate, str):
                    amendment_date = framework.latestComparisionCheckDate
                else:
                    amendment_date = framework.latestComparisionCheckDate.strftime("%Y-%m-%d")
            else:
                amendment_date = datetime.now().strftime("%Y-%m-%d")
            
            # Process the amendment
            result = process_downloaded_amendment(
                pdf_path=pdf_path,
                framework_name=framework.FrameworkName,
                framework_id=framework.FrameworkId,
                amendment_date=amendment_date
            )
            
            if result.get('success'):
                # Store in database
                self._store_amendment_in_database(framework, result, pdf_path, amendment_date)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    def _store_amendment_in_database(self, framework: Framework, result: Dict[str, Any], 
                                     pdf_path: str, amendment_date: str):
        """Store processed amendment data in Framework.Amendment field."""
        try:
            amendment_data = result.get('data', {})
            
            # Create new amendment entry (replace existing content)
            new_amendment = {
                'amendment_id': 1,
                'amendment_name': f"{framework.FrameworkName} Amendment - {amendment_date}",
                'amendment_date': amendment_date,
                'document_path': pdf_path,
                'processed_date': datetime.now().isoformat(),
                'extraction_summary': amendment_data.get('extraction_summary', {}),
                'sections': amendment_data.get('sections', []),
                'framework_info': amendment_data.get('amendment_metadata', {}).get('framework_info', {}),
                'ai_analysis': amendment_data.get('ai_analysis', {})
            }
            
            framework.Amendment = [new_amendment]
            
            # Update latest amendment date
            try:
                latest_date = datetime.strptime(amendment_date, "%Y-%m-%d").date()
                framework.latestAmmendmentDate = latest_date
            except ValueError:
                pass
            
            framework.latestComparisionCheckDate = datetime.now().date()
            framework.save(update_fields=['Amendment', 'latestAmmendmentDate', 'latestComparisionCheckDate'])
            
            logger.info(f"Stored amendment data in database for framework {framework.FrameworkId}")
            
        except Exception as e:
            logger.error(f"Error storing amendment in database: {str(e)}")
            raise


def scan_downloads_folder(process_all: bool = False) -> Dict[str, Any]:
    """
    Convenience function to scan and process downloads folder.
    
    Args:
        process_all: If True, process all PDFs even if already processed
        
    Returns:
        Processing results dictionary
    """
    scanner = DownloadsScanner()
    return scanner.scan_and_process(process_all=process_all)

