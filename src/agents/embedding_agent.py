"""
Embedding Agent
Uses Google Gemini embedding-001 with API key rotation.
Embeds chunks and stores them in Qdrant vector database.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from itertools import cycle
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from ..common import logger, config
from .chunking_agent import Chunk


class GeminiKeyRotator:
    """Rotates Gemini API keys with backoff on rate limits."""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.key_cycle = cycle(api_keys)
        self.current_key = next(self.key_cycle) if api_keys else None
        self.rate_limit_rpm = config.rate_limit_rpm
        self.last_request_time = 0
        self.min_interval = 60.0 / self.rate_limit_rpm if self.rate_limit_rpm > 0 else 0
    
    def get_current_key(self) -> str:
        """Get current API key."""
        return self.current_key
    
    def rotate_key(self):
        """Rotate to next API key."""
        if len(self.api_keys) > 1:
            self.current_key = next(self.key_cycle)
            logger.info(f"Rotated to next API key")
    
    async def wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        if self.min_interval > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                await asyncio.sleep(wait_time)
        self.last_request_time = time.time()


class EmbeddingAgent:
    """
    Embedding agent using Gemini embedding-001 with key rotation.
    """
    
    def __init__(self):
        self.embedding_model = config.embedding_model
        self.api_keys = config.get_gemini_keys()
        
        if not self.api_keys:
            logger.warning("No Gemini API keys configured!")
            self.key_rotator = None
        else:
            self.key_rotator = GeminiKeyRotator(self.api_keys)
            genai.configure(api_key=self.key_rotator.get_current_key())
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key,
        )
        self.collection_name = config.qdrant_collection_name
        self.vector_size = 768  # Gemini embedding-001 dimension
    
    def ensure_collection(self):
        """Ensure Qdrant collection exists."""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                
                # Create payload indexes for filtering
                self.qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="doc_id",
                    field_schema="keyword"
                )
                self.qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="language",
                    field_schema="keyword"
                )
                self.qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="page_num",
                    field_schema="integer"
                )
                
                logger.success(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    async def embed_text(self, text: str, retry_count: int = 3) -> Optional[List[float]]:
        """
        Embed a single text using Gemini.
        
        Args:
            text: Text to embed
            retry_count: Number of retries on failure
            
        Returns:
            Embedding vector or None if failed
        """
        if not self.key_rotator:
            logger.error("No API keys available for embedding")
            return None
        
        for attempt in range(retry_count):
            try:
                # Wait for rate limit
                await self.key_rotator.wait_for_rate_limit()
                
                # Configure with current key
                genai.configure(api_key=self.key_rotator.get_current_key())
                
                # Generate embedding
                result = genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="retrieval_document"
                )
                
                return result['embedding']
                
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
                
                # Rotate key on rate limit or error
                if attempt < retry_count - 1:
                    self.key_rotator.rotate_key()
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to embed text after {retry_count} attempts")
                    return None
        
        return None
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[Optional[List[float]]]:
        """
        Embed multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            # Embed each text in batch
            batch_embeddings = await asyncio.gather(
                *[self.embed_text(text) for text in batch]
            )
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def embed_chunks(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """
        Embed chunks and prepare for Qdrant upload.
        
        Args:
            chunks: List of Chunk objects
            
        Returns:
            List of dictionaries with chunk data and embeddings
        """
        logger.info(f"Embedding {len(chunks)} chunks...")
        
        # Extract texts
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings
        embeddings = await self.embed_batch(texts)
        
        # Combine with chunk data
        embedded_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            if embedding is not None:
                embedded_chunks.append({
                    "chunk": chunk,
                    "embedding": embedding
                })
            else:
                logger.warning(f"Skipping chunk {chunk.chunk_id} due to embedding failure")
        
        logger.success(f"Successfully embedded {len(embedded_chunks)}/{len(chunks)} chunks")
        
        return embedded_chunks
    
    async def store_chunks_in_qdrant(self, embedded_chunks: List[Dict[str, Any]]):
        """
        Store embedded chunks in Qdrant.
        
        Args:
            embedded_chunks: List of chunks with embeddings
        """
        if not embedded_chunks:
            logger.warning("No chunks to store")
            return
        
        logger.info(f"Storing {len(embedded_chunks)} chunks in Qdrant...")
        
        # Ensure collection exists
        self.ensure_collection()
        
        # Create points
        points = []
        for i, item in enumerate(embedded_chunks):
            chunk = item["chunk"]
            embedding = item["embedding"]
            
            point = PointStruct(
                id=hash(chunk.chunk_id) % (2**63),  # Convert to int ID
                vector=embedding,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "text": chunk.text,
                    "language": chunk.language,
                    "page_num": chunk.page_num,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    **chunk.metadata
                }
            )
            points.append(point)
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
        
        logger.success(f"Stored {len(points)} chunks in Qdrant collection '{self.collection_name}'")
    
    async def process_document(self, chunks: List[Chunk]):
        """
        Process document chunks: embed and store in Qdrant.
        
        Args:
            chunks: List of Chunk objects
        """
        # Embed chunks
        embedded_chunks = await self.embed_chunks(chunks)
        
        # Store in Qdrant
        await self.store_chunks_in_qdrant(embedded_chunks)

