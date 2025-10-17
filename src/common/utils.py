"""
Utility functions for PDF processing, text manipulation, and more.
"""

import hashlib
import re
from typing import List, Tuple, Optional
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def generate_doc_id(file_path: Path, language: str) -> str:
    """Generate a unique document ID from file path and language."""
    file_hash = compute_file_hash(file_path)
    return f"{language}_{file_path.stem}_{file_hash[:8]}"


def detect_language_from_path(file_path: Path) -> Optional[str]:
    """Detect language from file path (based on parent directory)."""
    # Assuming structure: data/incoming/<lang>/file.pdf
    parent = file_path.parent.name
    if parent in ["en", "zh", "hi", "bn", "ur"]:
        return parent
    return None


def is_cjk_char(char: str) -> bool:
    """Check if a character is CJK (Chinese, Japanese, Korean)."""
    if not char:
        return False
    code = ord(char)
    # CJK Unified Ideographs and extensions
    return (
        (0x4E00 <= code <= 0x9FFF) or  # CJK Unified Ideographs
        (0x3400 <= code <= 0x4DBF) or  # CJK Extension A
        (0x20000 <= code <= 0x2A6DF) or  # CJK Extension B
        (0x2A700 <= code <= 0x2B73F) or  # CJK Extension C
        (0x2B740 <= code <= 0x2B81F) or  # CJK Extension D
        (0x2B820 <= code <= 0x2CEAF) or  # CJK Extension E
        (0x3000 <= code <= 0x303F) or  # CJK Symbols and Punctuation
        (0xFF00 <= code <= 0xFFEF)  # Halfwidth and Fullwidth Forms
    )


def count_cjk_chars(text: str) -> int:
    """Count CJK characters in text."""
    return sum(1 for char in text if is_cjk_char(char))


def is_cjk_text(text: str, threshold: float = 0.3) -> bool:
    """Check if text is predominantly CJK."""
    if not text:
        return False
    cjk_count = count_cjk_chars(text)
    total_chars = len(text.strip())
    if total_chars == 0:
        return False
    return (cjk_count / total_chars) >= threshold


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text."""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\n+', '\n\n', text)
    return text.strip()


def clean_ocr_text(text: str) -> str:
    """Basic OCR text cleaning."""
    # Remove excessive whitespace
    text = normalize_whitespace(text)
    # Remove common OCR artifacts
    text = re.sub(r'[|\\]', '', text)
    # Fix common OCR errors (example)
    text = text.replace('|', 'I')
    return text


def extract_page_metadata(pdf_path: Path, page_num: int) -> dict:
    """Extract metadata from a PDF page."""
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        metadata = {
            "page_num": page_num,
            "width": page.rect.width,
            "height": page.rect.height,
            "rotation": page.rotation,
        }
        doc.close()
        return metadata
    except Exception as e:
        return {"error": str(e)}


def pdf_page_to_image(pdf_path: Path, page_num: int, dpi: int = 300) -> Optional[Image.Image]:
    """Convert a PDF page to an image."""
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        # Render page to pixmap
        mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 is default DPI
        pix = page.get_pixmap(matrix=mat)
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        doc.close()
        return img
    except Exception as e:
        print(f"Error converting PDF page to image: {e}")
        return None


def get_pdf_page_count(pdf_path: Path) -> int:
    """Get the number of pages in a PDF."""
    try:
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0


def split_into_sentences(text: str, language: str = "en") -> List[str]:
    """Split text into sentences (basic implementation)."""
    if language == "zh":
        # Chinese sentence endings
        sentences = re.split(r'[。！？；]', text)
    else:
        # English and other languages
        sentences = re.split(r'[.!?]+', text)
    
    return [s.strip() for s in sentences if s.strip()]


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_page_marker(page_num: int) -> str:
    """Format page marker for text."""
    return f"\n\n[PAGE {page_num}]\n\n"


def extract_page_number_from_marker(text: str) -> Optional[int]:
    """Extract page number from page marker."""
    match = re.search(r'\[PAGE (\d+)\]', text)
    if match:
        return int(match.group(1))
    return None


def language_to_tesseract_code(lang: str) -> str:
    """Convert language code to Tesseract language code."""
    mapping = {
        "en": "eng",
        "zh": "chi_sim",
        "hi": "hin",
        "bn": "ben",
        "ur": "urd",
    }
    return mapping.get(lang, "eng")


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

