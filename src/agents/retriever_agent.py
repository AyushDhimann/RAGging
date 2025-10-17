"""
Retriever Agent
Hybrid retrieval combining dense (Qdrant) and sparse (BM25) search.
Supports metadata filtering and result fusion.
"""

from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from ..common import logger, config


class RetrievalResult:
    """Represents a retrieval result."""
    
    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        text: str,
        score: float,
        language: str = None,
        page_num: int = None,
        metadata: Dict[str, Any] = None
    ):
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.text = text
        self.score = score
        self.language = language
        self.page_num = page_num
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "text": self.text,
            "score": self.score,
            "language": self.language,
            "page_num": self.page_num,
            "metadata": self.metadata
        }


class RetrieverAgent:
    """
    Hybrid retriever combining dense semantic search (Qdrant) and sparse keyword search (BM25).
    """
    
    def __init__(self):
        self.enable_bm25 = config.enable_bm25
        self.fusion_method = config.fusion_method
        self.dense_weight = config.dense_weight
        self.keyword_weight = config.keyword_weight
        self.enable_metadata_filter = config.enable_metadata_filter
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key,
        )
        self.collection_name = config.qdrant_collection_name
        
        # Gemini for query embedding
        self.embedding_model = config.embedding_model
        keys = config.get_gemini_keys()
        if keys:
            genai.configure(api_key=keys[0])
        
        # BM25 index (lazy loaded)
        self.bm25_index = None
        self.bm25_documents = []
    
    def _build_bm25_index(self):
        """Build BM25 index from all documents in Qdrant."""
        logger.info("Building BM25 index from Qdrant collection...")
        
        try:
            # Scroll through all documents
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10000  # Adjust based on collection size
            )
            
            points = scroll_result[0]
            
            # Extract texts and build corpus
            self.bm25_documents = []
            for point in points:
                self.bm25_documents.append({
                    "chunk_id": point.payload.get("chunk_id"),
                    "doc_id": point.payload.get("doc_id"),
                    "text": point.payload.get("text", ""),
                    "language": point.payload.get("language"),
                    "page_num": point.payload.get("page_num"),
                    "metadata": {k: v for k, v in point.payload.items() 
                                if k not in ["chunk_id", "doc_id", "text", "language", "page_num"]}
                })
            
            # Tokenize corpus
            tokenized_corpus = [doc["text"].lower().split() for doc in self.bm25_documents]
            
            # Build BM25 index
            self.bm25_index = BM25Okapi(tokenized_corpus)
            
            logger.success(f"Built BM25 index with {len(self.bm25_documents)} documents")
            
        except Exception as e:
            logger.error(f"Error building BM25 index: {e}")
            self.bm25_index = None
    
    def embed_query(self, query: str) -> Optional[List[float]]:
        """Embed query using Gemini."""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            return None
    
    def dense_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Perform dense semantic search using Qdrant.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            metadata_filter: Optional metadata filters
            
        Returns:
            List of RetrievalResult objects
        """
        try:
            # Build filter if needed
            qdrant_filter = None
            if metadata_filter and self.enable_metadata_filter:
                conditions = []
                for key, value in metadata_filter.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            # Search
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k
            )
            
            # Convert to RetrievalResult
            results = []
            for hit in search_result:
                result = RetrievalResult(
                    chunk_id=hit.payload.get("chunk_id"),
                    doc_id=hit.payload.get("doc_id"),
                    text=hit.payload.get("text"),
                    score=hit.score,
                    language=hit.payload.get("language"),
                    page_num=hit.payload.get("page_num"),
                    metadata={k: v for k, v in hit.payload.items() 
                             if k not in ["chunk_id", "doc_id", "text", "language", "page_num"]}
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in dense search: {e}")
            return []
    
    def sparse_search(
        self,
        query: str,
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Perform sparse keyword search using BM25.
        
        Args:
            query: Query text
            top_k: Number of results to return
            metadata_filter: Optional metadata filters
            
        Returns:
            List of RetrievalResult objects
        """
        # Build index if not exists
        if self.bm25_index is None:
            self._build_bm25_index()
        
        if self.bm25_index is None or not self.bm25_documents:
            logger.warning("BM25 index not available")
            return []
        
        try:
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            scores = self.bm25_index.get_scores(tokenized_query)
            
            # Get top-k indices
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            
            # Build results
            results = []
            for idx in top_indices:
                doc = self.bm25_documents[idx]
                
                # Apply metadata filter if specified
                if metadata_filter and self.enable_metadata_filter:
                    if not all(doc.get(k) == v for k, v in metadata_filter.items()):
                        continue
                
                result = RetrievalResult(
                    chunk_id=doc["chunk_id"],
                    doc_id=doc["doc_id"],
                    text=doc["text"],
                    score=float(scores[idx]),
                    language=doc.get("language"),
                    page_num=doc.get("page_num"),
                    metadata=doc.get("metadata", {})
                )
                results.append(result)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in sparse search: {e}")
            return []
    
    def fuse_results(
        self,
        dense_results: List[RetrievalResult],
        sparse_results: List[RetrievalResult],
        method: str = "weighted"
    ) -> List[RetrievalResult]:
        """
        Fuse dense and sparse results.
        
        Args:
            dense_results: Results from dense search
            sparse_results: Results from sparse search
            method: Fusion method ('weighted' or 'rrf')
            
        Returns:
            Fused and sorted results
        """
        if method == "weighted":
            # Weighted fusion
            result_map = {}
            
            # Add dense results
            for result in dense_results:
                result_map[result.chunk_id] = RetrievalResult(
                    chunk_id=result.chunk_id,
                    doc_id=result.doc_id,
                    text=result.text,
                    score=result.score * self.dense_weight,
                    language=result.language,
                    page_num=result.page_num,
                    metadata=result.metadata
                )
            
            # Add sparse results
            for result in sparse_results:
                if result.chunk_id in result_map:
                    # Combine scores
                    result_map[result.chunk_id].score += result.score * self.keyword_weight
                else:
                    result_map[result.chunk_id] = RetrievalResult(
                        chunk_id=result.chunk_id,
                        doc_id=result.doc_id,
                        text=result.text,
                        score=result.score * self.keyword_weight,
                        language=result.language,
                        page_num=result.page_num,
                        metadata=result.metadata
                    )
            
            # Sort by score
            fused_results = sorted(result_map.values(), key=lambda x: x.score, reverse=True)
            
        else:  # RRF (Reciprocal Rank Fusion)
            k = 60  # RRF constant
            result_map = {}
            
            # Process dense results
            for rank, result in enumerate(dense_results):
                score = 1.0 / (k + rank + 1)
                result_map[result.chunk_id] = RetrievalResult(
                    chunk_id=result.chunk_id,
                    doc_id=result.doc_id,
                    text=result.text,
                    score=score,
                    language=result.language,
                    page_num=result.page_num,
                    metadata=result.metadata
                )
            
            # Process sparse results
            for rank, result in enumerate(sparse_results):
                score = 1.0 / (k + rank + 1)
                if result.chunk_id in result_map:
                    result_map[result.chunk_id].score += score
                else:
                    result_map[result.chunk_id] = RetrievalResult(
                        chunk_id=result.chunk_id,
                        doc_id=result.doc_id,
                        text=result.text,
                        score=score,
                        language=result.language,
                        page_num=result.page_num,
                        metadata=result.metadata
                    )
            
            fused_results = sorted(result_map.values(), key=lambda x: x.score, reverse=True)
        
        return fused_results
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks using hybrid search.
        
        Args:
            query: Query text
            top_k: Number of results to return
            metadata_filter: Optional metadata filters (e.g., {"language": "en"})
            
        Returns:
            List of RetrievalResult objects
        """
        logger.info(f"Retrieving documents for query: '{query[:50]}...'")
        
        # Embed query for dense search
        query_vector = self.embed_query(query)
        
        if query_vector is None:
            logger.error("Failed to embed query")
            return []
        
        # Dense search
        dense_results = self.dense_search(query_vector, top_k=top_k * 2, metadata_filter=metadata_filter)
        logger.info(f"Dense search returned {len(dense_results)} results")
        
        # Sparse search (if enabled)
        if self.enable_bm25:
            sparse_results = self.sparse_search(query, top_k=top_k * 2, metadata_filter=metadata_filter)
            logger.info(f"Sparse search returned {len(sparse_results)} results")
            
            # Fuse results
            results = self.fuse_results(dense_results, sparse_results, method=self.fusion_method)
            logger.info(f"Fused {len(results)} results")
        else:
            results = dense_results
        
        # Return top-k
        return results[:top_k]

