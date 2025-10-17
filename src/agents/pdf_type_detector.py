"""
PDF Type Detector Agent
Detects whether PDF pages are scanned (image-based) or digital (text-based).
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict
from enum import Enum

from ..common import logger


class PageType(str, Enum):
    """PDF page type."""
    DIGITAL = "digital"
    SCANNED = "scanned"
    MIXED = "mixed"


class PDFTypeDetector:
    """Detect whether PDF pages are scanned or digital."""
    
    def __init__(self, text_threshold: int = 50):
        """
        Initialize PDF type detector.
        
        Args:
            text_threshold: Minimum number of characters to consider page as digital
        """
        self.text_threshold = text_threshold
    
    def detect_page_type(self, pdf_path: Path, page_num: int) -> PageType:
        """
        Detect the type of a single PDF page.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            PageType enum (DIGITAL, SCANNED, or MIXED)
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            
            # Extract text
            text = page.get_text()
            text_length = len(text.strip())
            
            # Check for images
            image_list = page.get_images(full=True)
            has_images = len(image_list) > 0
            
            doc.close()
            
            # Determine page type
            if text_length >= self.text_threshold:
                if has_images and text_length < 200:
                    return PageType.MIXED
                return PageType.DIGITAL
            else:
                return PageType.SCANNED
                
        except Exception as e:
            logger.error(f"Error detecting page type for {pdf_path} page {page_num}: {e}")
            # Default to scanned if error
            return PageType.SCANNED
    
    def detect_document_type(self, pdf_path: Path) -> Dict[int, PageType]:
        """
        Detect types for all pages in a PDF document.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary mapping page numbers to PageType
        """
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            
            page_types = {}
            for page_num in range(page_count):
                page_types[page_num] = self.detect_page_type(pdf_path, page_num)
            
            logger.info(f"Detected page types for {pdf_path.name}: "
                       f"{sum(1 for t in page_types.values() if t == PageType.DIGITAL)} digital, "
                       f"{sum(1 for t in page_types.values() if t == PageType.SCANNED)} scanned, "
                       f"{sum(1 for t in page_types.values() if t == PageType.MIXED)} mixed")
            
            return page_types
            
        except Exception as e:
            logger.error(f"Error detecting document type for {pdf_path}: {e}")
            return {}
    
    def get_scanned_pages(self, pdf_path: Path) -> List[int]:
        """
        Get list of scanned page numbers.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of page numbers that are scanned
        """
        page_types = self.detect_document_type(pdf_path)
        return [
            page_num for page_num, page_type in page_types.items()
            if page_type in [PageType.SCANNED, PageType.MIXED]
        ]
    
    def get_digital_pages(self, pdf_path: Path) -> List[int]:
        """
        Get list of digital page numbers.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of page numbers that are digital
        """
        page_types = self.detect_document_type(pdf_path)
        return [
            page_num for page_num, page_type in page_types.items()
            if page_type == PageType.DIGITAL
        ]

