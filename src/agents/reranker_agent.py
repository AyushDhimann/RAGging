"""
Reranker Agent
Reranks retrieval results using Gemini Flash.
Optional CPU-based fallback for offline scenarios.
"""

from typing import List, Dict, Any
import google.generativeai as genai

from ..common import logger, config
from .retriever_agent import RetrievalResult


class RerankerAgent:
    """
    Reranks retrieval results using LLM scoring.
    Primary: Gemini Flash
    Fallback: Simple CPU-based scoring
    """
    
    def __init__(self):
        self.enable_rerank = config.enable_rerank
        self.rerank_backend = config.rerank_backend
        self.rerank_top_k = config.rerank_top_k
        self.rerank_model = config.eval_model  # Use same model as eval
        
        # Configure Gemini
        keys = config.get_gemini_keys()
        if keys:
            genai.configure(api_key=keys[0])
    
    def rerank_with_gemini(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = None
    ) -> List[RetrievalResult]:
        """
        Rerank results using Gemini Flash.
        
        Args:
            query: Original query
            results: List of retrieval results
            top_k: Number of top results to return
            
        Returns:
            Reranked list of results
        """
        top_k = top_k or self.rerank_top_k
        
        if not results:
            return []
        
        logger.info(f"Reranking {len(results)} results with Gemini...")
        
        try:
            # Create prompt for reranking
            prompt = self._build_reranking_prompt(query, results)
            
            model = genai.GenerativeModel(self.rerank_model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "max_output_tokens": 1024,
                }
            )
            
            if not response.text:
                logger.warning("Gemini reranking returned empty response")
                return results[:top_k]
            
            # Parse response to get reranked indices
            reranked_results = self._parse_reranking_response(response.text, results)
            
            logger.success(f"Reranked to {len(reranked_results)} results")
            return reranked_results[:top_k]
            
        except Exception as e:
            logger.error(f"Gemini reranking failed: {e}")
            return results[:top_k]
    
    def _build_reranking_prompt(self, query: str, results: List[RetrievalResult]) -> str:
        """Build prompt for reranking."""
        passages = []
        for i, result in enumerate(results):
            passages.append(f"[{i}] {result.text[:300]}...")
        
        prompt = f"""You are a reranking assistant. Given a query and a list of passages, rank the passages by their relevance to the query.

Query: {query}

Passages:
{chr(10).join(passages)}

Instructions:
1. Analyze each passage's relevance to the query
2. Return ONLY the passage indices in order of relevance (most relevant first)
3. Format: space-separated indices, e.g., "2 0 4 1 3"

Reranked indices:"""
        
        return prompt
    
    def _parse_reranking_response(
        self,
        response: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Parse reranking response and reorder results."""
        try:
            # Extract indices from response
            indices_str = response.strip().split('\n')[0].strip()
            indices = [int(i) for i in indices_str.split() if i.isdigit()]
            
            # Reorder results
            reranked = []
            for idx in indices:
                if 0 <= idx < len(results):
                    reranked.append(results[idx])
            
            # Add any missing results at the end
            for i, result in enumerate(results):
                if i not in indices:
                    reranked.append(result)
            
            return reranked
            
        except Exception as e:
            logger.warning(f"Error parsing reranking response: {e}")
            return results
    
    def rerank_with_cpu(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = None
    ) -> List[RetrievalResult]:
        """
        Simple CPU-based reranking using keyword overlap.
        
        Args:
            query: Original query
            results: List of retrieval results
            top_k: Number of top results to return
            
        Returns:
            Reranked list of results
        """
        top_k = top_k or self.rerank_top_k
        
        if not results:
            return []
        
        logger.info(f"Reranking {len(results)} results with CPU (keyword overlap)...")
        
        # Tokenize query
        query_tokens = set(query.lower().split())
        
        # Score by keyword overlap
        scored_results = []
        for result in results:
            text_tokens = set(result.text.lower().split())
            overlap = len(query_tokens & text_tokens)
            
            # Combine original score with overlap score
            new_score = result.score + (overlap * 0.1)
            
            result.score = new_score
            scored_results.append(result)
        
        # Sort by new score
        reranked = sorted(scored_results, key=lambda x: x.score, reverse=True)
        
        return reranked[:top_k]
    
    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = None
    ) -> List[RetrievalResult]:
        """
        Rerank retrieval results.
        
        Args:
            query: Original query
            results: List of retrieval results
            top_k: Number of top results to return
            
        Returns:
            Reranked list of results
        """
        if not self.enable_rerank:
            return results[:top_k or len(results)]
        
        if self.rerank_backend == "gemini":
            return self.rerank_with_gemini(query, results, top_k)
        else:
            return self.rerank_with_cpu(query, results, top_k)

