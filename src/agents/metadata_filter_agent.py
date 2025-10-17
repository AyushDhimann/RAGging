"""
Metadata Filter Agent
Extracts filters from user queries for metadata-based filtering.
"""

import re
from typing import Dict, Any, Optional

from ..common import logger


class MetadataFilterAgent:
    """
    Extracts metadata filters from user queries.
    Supports language, page number, and document ID filters.
    """
    
    def __init__(self):
        self.supported_languages = ["en", "zh", "hi", "bn", "ur", "english", "chinese", "hindi", "bengali", "urdu"]
        self.language_map = {
            "english": "en",
            "chinese": "zh",
            "hindi": "hi",
            "bengali": "bn",
            "urdu": "ur",
        }
    
    def extract_language_filter(self, query: str) -> Optional[str]:
        """Extract language filter from query."""
        query_lower = query.lower()
        
        for lang in self.supported_languages:
            if lang in query_lower:
                # Map to language code
                lang_code = self.language_map.get(lang, lang)
                if len(lang_code) == 2:  # Valid code
                    logger.info(f"Detected language filter: {lang_code}")
                    return lang_code
        
        return None
    
    def extract_page_filter(self, query: str) -> Optional[int]:
        """Extract page number filter from query."""
        # Look for patterns like "page 5", "page 10", "on page 3"
        match = re.search(r'\bpage\s+(\d+)\b', query, re.IGNORECASE)
        if match:
            page_num = int(match.group(1))
            logger.info(f"Detected page filter: {page_num}")
            return page_num
        
        return None
    
    def extract_doc_id_filter(self, query: str) -> Optional[str]:
        """Extract document ID filter from query."""
        # Look for patterns like "in document X", "from doc X"
        match = re.search(r'\b(?:document|doc)\s+([a-zA-Z0-9_-]+)\b', query, re.IGNORECASE)
        if match:
            doc_id = match.group(1)
            logger.info(f"Detected document filter: {doc_id}")
            return doc_id
        
        return None
    
    def extract_filters(self, query: str) -> Dict[str, Any]:
        """
        Extract all metadata filters from query.
        
        Args:
            query: User query
            
        Returns:
            Dictionary of filters
        """
        filters = {}
        
        # Extract language
        language = self.extract_language_filter(query)
        if language:
            filters["language"] = language
        
        # Extract page number
        page_num = self.extract_page_filter(query)
        if page_num is not None:
            filters["page_num"] = page_num
        
        # Extract document ID
        doc_id = self.extract_doc_id_filter(query)
        if doc_id:
            filters["doc_id"] = doc_id
        
        if filters:
            logger.info(f"Extracted filters: {filters}")
        
        return filters
    
    def clean_query(self, query: str, filters: Dict[str, Any]) -> str:
        """
        Remove filter keywords from query.
        
        Args:
            query: Original query
            filters: Extracted filters
            
        Returns:
            Cleaned query
        """
        cleaned = query
        
        # Remove language mentions
        if "language" in filters:
            for lang in self.supported_languages:
                cleaned = re.sub(r'\b' + lang + r'\b', '', cleaned, flags=re.IGNORECASE)
        
        # Remove page mentions
        if "page_num" in filters:
            cleaned = re.sub(r'\bpage\s+\d+\b', '', cleaned, flags=re.IGNORECASE)
        
        # Remove document mentions
        if "doc_id" in filters:
            cleaned = re.sub(r'\b(?:document|doc)\s+[a-zA-Z0-9_-]+\b', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

