"""
Decomposition Agent
Decomposes complex queries into sub-queries using DeepSeek-R1.
Helps retrieve more comprehensive context.
"""

from typing import List, Optional
import httpx
import google.generativeai as genai
import re

from ..common import logger, config


class DecompositionAgent:
    """
    Query decomposition agent using LLM.
    Breaks complex queries into simpler sub-queries.
    """
    
    def __init__(self):
        self.enable_decomposition = config.enable_decomposition
        self.ollama_host = config.ollama_host
        self.primary_model = self._parse_model_name(config.llm_primary)
        self.fallback_model = config.llm_fallback
        
        # Configure Gemini
        keys = config.get_gemini_keys()
        if keys:
            genai.configure(api_key=keys[0])
        
        self.decomposition_prompt_template = """You are a query decomposition assistant. Break down the following complex query into 2-4 simpler sub-queries that together would help answer the original query.

Original Query: {query}

Instructions:
1. Identify the key aspects of the original query
2. Create 2-4 focused sub-queries
3. Each sub-query should be self-contained and specific
4. Return ONLY the sub-queries, one per line
5. Do NOT include numbering or explanations

Sub-queries:"""
    
    def _parse_model_name(self, model_str: str) -> str:
        """Parse model string."""
        if ":" in model_str:
            parts = model_str.split(":", 1)
            if len(parts) == 2:
                return parts[1]
        return model_str
    
    async def decompose_with_ollama(self, query: str) -> Optional[List[str]]:
        """
        Decompose query using Ollama (DeepSeek-R1).
        
        Args:
            query: Original query
            
        Returns:
            List of sub-queries or None if failed
        """
        try:
            prompt = self.decomposition_prompt_template.format(query=query)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.primary_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "").strip()
                    
                    # Parse sub-queries
                    sub_queries = self._parse_sub_queries(response_text)
                    return sub_queries
                else:
                    logger.warning(f"Ollama request failed with status {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Ollama decomposition failed: {e}")
            return None
    
    def decompose_with_gemini(self, query: str) -> Optional[List[str]]:
        """
        Decompose query using Gemini Flash (fallback).
        
        Args:
            query: Original query
            
        Returns:
            List of sub-queries or None if failed
        """
        try:
            model = genai.GenerativeModel(self.fallback_model)
            prompt = self.decomposition_prompt_template.format(query=query)
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_output_tokens": 512,
                }
            )
            
            if response.text:
                sub_queries = self._parse_sub_queries(response.text)
                return sub_queries
            else:
                logger.warning("Gemini decomposition returned empty response")
                return None
                
        except Exception as e:
            logger.error(f"Gemini decomposition failed: {e}")
            return None
    
    def _parse_sub_queries(self, response_text: str) -> List[str]:
        """Parse sub-queries from LLM response."""
        # Split by newlines
        lines = response_text.strip().split('\n')
        
        # Clean up lines
        sub_queries = []
        for line in lines:
            line = line.strip()
            
            # Remove numbering (1., 2., etc.)
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            
            # Remove bullet points
            line = re.sub(r'^[-\*•]\s*', '', line)
            
            # Remove quotes
            line = line.strip('"\'')
            
            if line and len(line) > 10:  # Ignore very short lines
                sub_queries.append(line)
        
        return sub_queries[:4]  # Max 4 sub-queries
    
    async def decompose_query(self, query: str) -> List[str]:
        """
        Decompose a complex query into sub-queries.
        
        Args:
            query: Original query
            
        Returns:
            List of sub-queries (includes original query)
        """
        if not self.enable_decomposition:
            return [query]
        
        # For simple queries, don't decompose
        if len(query.split()) < 8:
            logger.info("Query is simple, skipping decomposition")
            return [query]
        
        logger.info(f"Decomposing query: '{query}'")
        
        # Try Ollama first
        sub_queries = await self.decompose_with_ollama(query)
        
        if sub_queries:
            logger.success(f"Decomposed into {len(sub_queries)} sub-queries with Ollama")
        else:
            # Fallback to Gemini
            logger.info("Falling back to Gemini for decomposition...")
            sub_queries = self.decompose_with_gemini(query)
            
            if sub_queries:
                logger.success(f"Decomposed into {len(sub_queries)} sub-queries with Gemini")
        
        # If decomposition failed, return original query
        if not sub_queries:
            logger.warning("Decomposition failed, using original query")
            return [query]
        
        # Always include original query
        all_queries = [query] + sub_queries
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in all_queries:
            q_lower = q.lower()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)
        
        return unique_queries

