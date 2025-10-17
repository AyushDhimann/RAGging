"""
OCR Agent (Tesseract-only)
Performs OCR on scanned PDF pages using Tesseract.
Digital pages are extracted directly via PyMuPDF.
"""

import fitz  # PyMuPDF
import pytesseract
from pathlib import Path
from typing import Dict, List, Optional
from pdf2image import convert_from_path
from PIL import Image

from ..common import (
    logger, config,
    language_to_tesseract_code,
    format_page_marker,
    pdf_page_to_image
)
from .pdf_type_detector import PDFTypeDetector, PageType


class OCRAgent:
    """OCR agent using Tesseract for scanned pages and PyMuPDF for digital pages."""
    
    def __init__(self):
        self.pdf_detector = PDFTypeDetector()
        self.tesseract_cmd = config.tesseract_cmd
        
        # Set Tesseract command path
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
    
    def extract_text_from_digital_page(self, pdf_path: Path, page_num: int) -> str:
        """
        Extract text from a digital PDF page using PyMuPDF.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            Extracted text
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            text = page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from digital page {page_num}: {e}")
            return ""
    
    def extract_text_from_scanned_page(
        self,
        pdf_path: Path,
        page_num: int,
        language: str = "en"
    ) -> str:
        """
        Extract text from a scanned PDF page using Tesseract OCR.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            language: Language code (en, zh, hi, bn, ur)
            
        Returns:
            OCR-extracted text
        """
        try:
            # Convert language code to Tesseract code
            tesseract_lang = language_to_tesseract_code(language)
            
            # Convert PDF page to image
            image = pdf_page_to_image(pdf_path, page_num, dpi=300)
            if image is None:
                logger.error(f"Failed to convert page {page_num} to image")
                return ""
            
            # Perform OCR
            custom_config = r'--oem 1 --psm 6'
            text = pytesseract.image_to_string(
                image,
                lang=tesseract_lang,
                config=custom_config
            )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error performing OCR on page {page_num}: {e}")
            return ""
    
    def process_document(
        self,
        pdf_path: Path,
        language: str = "en",
        save_raw: bool = True
    ) -> Dict[int, str]:
        """
        Process entire PDF document - OCR scanned pages, extract digital pages.
        
        Args:
            pdf_path: Path to PDF file
            language: Document language
            save_raw: Whether to save raw OCR output
            
        Returns:
            Dictionary mapping page numbers to extracted text
        """
        logger.info(f"Starting OCR processing for {pdf_path.name} (language: {language})")
        
        # Detect page types
        page_types = self.pdf_detector.detect_document_type(pdf_path)
        
        if not page_types:
            logger.error(f"Failed to detect page types for {pdf_path}")
            return {}
        
        # Extract text from all pages
        page_texts = {}
        
        for page_num, page_type in page_types.items():
            logger.debug(f"Processing page {page_num} (type: {page_type})")
            
            if page_type == PageType.DIGITAL:
                # Extract text directly
                text = self.extract_text_from_digital_page(pdf_path, page_num)
            else:
                # Perform OCR
                text = self.extract_text_from_scanned_page(pdf_path, page_num, language)
            
            # Add page marker
            page_texts[page_num] = format_page_marker(page_num) + text
        
        logger.success(f"OCR completed for {pdf_path.name}: {len(page_texts)} pages processed")
        
        # Save raw OCR output if requested
        if save_raw:
            self._save_raw_output(pdf_path, page_texts)
        
        return page_texts
    
    def _save_raw_output(self, pdf_path: Path, page_texts: Dict[int, str]):
        """Save raw OCR output to file."""
        try:
            ocr_raw_dir = config.get_ocr_raw_dir()
            output_file = ocr_raw_dir / f"{pdf_path.stem}_raw.txt"
            
            # Combine all pages
            full_text = "\n\n".join(page_texts[i] for i in sorted(page_texts.keys()))
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(full_text)
            
            logger.info(f"Saved raw OCR output to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving raw OCR output: {e}")
    
    def get_combined_text(self, page_texts: Dict[int, str]) -> str:
        """Combine page texts into single document."""
        return "\n\n".join(page_texts[i] for i in sorted(page_texts.keys()))

