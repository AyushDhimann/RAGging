"""
LLM Cleanup Agent (mandatory)
Uses DeepSeek-R1 via Ollama to clean and normalize OCR text.
Falls back to Gemini Flash if Ollama fails.
"""

import re
from typing import Optional
import httpx
import google.generativeai as genai

from ..common import logger, config


class CleanupAgent:
    """
    LLM-based text cleanup agent.
    Normalizes OCR text, fixes spacing/diacritics, preserves page markers.
    """
    
    def __init__(self):
        self.ollama_host = config.ollama_host
        self.primary_model = self._parse_model_name(config.llm_primary)
        self.fallback_model = config.llm_fallback
        
        # Configure Gemini
        keys = config.get_gemini_keys()
        if keys:
            genai.configure(api_key=keys[0])
        
        self.cleanup_prompt_template = """You are a text cleanup assistant. Your task is to clean and normalize OCR-extracted text while preserving its structure and meaning.

Instructions:
1. Fix OCR errors (misrecognized characters, spacing issues)
2. Normalize whitespace and line breaks
3. Preserve page markers in format [PAGE N]
4. Fix diacritics and special characters for the given language
5. Do NOT translate or modify the actual content
6. Do NOT add or remove information
7. Return ONLY the cleaned text, no explanations

Language: {language}

Text to clean:
{text}

Cleaned text:"""
    
    def _parse_model_name(self, model_str: str) -> str:
        """Parse model string (e.g., 'ollama:deepseek-r1:1.5b' -> 'deepseek-r1:1.5b')."""
        if ":" in model_str:
            parts = model_str.split(":", 1)
            if len(parts) == 2:
                return parts[1]
        return model_str
    
    async def cleanup_with_ollama(self, text: str, language: str = "en") -> Optional[str]:
        """
        Clean text using Ollama (DeepSeek-R1).
        
        Args:
            text: Text to clean
            language: Source language
            
        Returns:
            Cleaned text or None if failed
        """
        try:
            prompt = self.cleanup_prompt_template.format(language=language, text=text)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.primary_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    cleaned_text = result.get("response", "").strip()
                    return cleaned_text
                else:
                    logger.warning(f"Ollama request failed with status {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Ollama cleanup failed: {e}")
            return None
    
    def cleanup_with_gemini(self, text: str, language: str = "en") -> Optional[str]:
        """
        Clean text using Gemini Flash (fallback).
        
        Args:
            text: Text to clean
            language: Source language
            
        Returns:
            Cleaned text or None if failed
        """
        try:
            model = genai.GenerativeModel(self.fallback_model)
            prompt = self.cleanup_prompt_template.format(language=language, text=text)
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_output_tokens": 4096,
                }
            )
            
            if response.text:
                return response.text.strip()
            else:
                logger.warning("Gemini returned empty response")
                return None
                
        except Exception as e:
            logger.error(f"Gemini cleanup failed: {e}")
            return None
    
    async def cleanup_text(self, text: str, language: str = "en") -> str:
        """
        Clean OCR text using LLM (Ollama primary, Gemini fallback).
        
        Args:
            text: Raw OCR text
            language: Source language
            
        Returns:
            Cleaned text (or original if all methods fail)
        """
        # Split into chunks if text is very large (> 3000 chars)
        if len(text) > 3000:
            return await self._cleanup_large_text(text, language)
        
        logger.info(f"Cleaning text ({len(text)} chars) with LLM...")
        
        # Try Ollama first
        cleaned = await self.cleanup_with_ollama(text, language)
        
        if cleaned:
            logger.success("Text cleaned with Ollama")
            return cleaned
        
        # Fallback to Gemini
        logger.info("Falling back to Gemini for cleanup...")
        cleaned = self.cleanup_with_gemini(text, language)
        
        if cleaned:
            logger.success("Text cleaned with Gemini")
            return cleaned
        
        # If both fail, apply basic cleanup
        logger.warning("LLM cleanup failed, applying basic cleanup")
        return self._basic_cleanup(text)
    
    async def _cleanup_large_text(self, text: str, language: str = "en") -> str:
        """Clean large text by splitting into chunks."""
        # Split by page markers
        page_pattern = r'\[PAGE \d+\]'
        pages = re.split(page_pattern, text)
        markers = re.findall(page_pattern, text)
        
        cleaned_pages = []
        
        for i, page_text in enumerate(pages):
            if not page_text.strip():
                continue
            
            # Clean each page
            cleaned = await self.cleanup_text(page_text.strip(), language)
            
            # Add marker back
            if i > 0 and i <= len(markers):
                cleaned_pages.append(markers[i-1])
            
            cleaned_pages.append(cleaned)
        
        return "\n\n".join(cleaned_pages)
    
    def _basic_cleanup(self, text: str) -> str:
        """Apply basic regex-based cleanup."""
        # Remove excessive whitespace
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Fix common OCR errors
        text = text.replace('|', 'I')
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        return text.strip()
    
    def save_cleaned_text(self, doc_id: str, cleaned_text: str):
        """Save cleaned text to file."""
        try:
            ocr_clean_dir = config.get_ocr_clean_dir()
            output_file = ocr_clean_dir / f"{doc_id}_clean.txt"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
            
            logger.info(f"Saved cleaned text to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving cleaned text: {e}")

