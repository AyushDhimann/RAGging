"""Common utilities and shared components."""

from .config import config, Config
from .logging import logger, console, info, warning, error, success, debug, ui_log_bridge
from .storage import storage, SQLiteStorage, JobStatus
from .utils import (
    compute_file_hash,
    generate_doc_id,
    detect_language_from_path,
    is_cjk_text,
    normalize_whitespace,
    clean_ocr_text,
    get_pdf_page_count,
    pdf_page_to_image,
    language_to_tesseract_code,
    format_page_marker,
)

__all__ = [
    "config",
    "Config",
    "logger",
    "console",
    "info",
    "warning",
    "error",
    "success",
    "debug",
    "ui_log_bridge",
    "storage",
    "SQLiteStorage",
    "JobStatus",
    "compute_file_hash",
    "generate_doc_id",
    "detect_language_from_path",
    "is_cjk_text",
    "normalize_whitespace",
    "clean_ocr_text",
    "get_pdf_page_count",
    "pdf_page_to_image",
    "language_to_tesseract_code",
    "format_page_marker",
]

