"""
Chunking Agent
Language-aware recursive text splitter with CJK support.
Chunks text into 450-550 tokens with 50-80 token overlap.
"""

import re
import json
from typing import List, Dict, Any
from pathlib import Path
import tiktoken

from ..common import logger, config, is_cjk_text


class Chunk:
    """Represents a text chunk with metadata."""
    
    def __init__(
        self,
        text: str,
        chunk_id: str,
        doc_id: str,
        language: str,
        page_num: int,
        start_char: int,
        end_char: int,
        metadata: Dict[str, Any] = None
    ):
        self.text = text
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.language = language
        self.page_num = page_num
        self.start_char = start_char
        self.end_char = end_char
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "text": self.text,
            "language": self.language,
            "page_num": self.page_num,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata,
        }


class ChunkingAgent:
    """
    Language-aware chunking agent with CJK support.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        encoding_name: str = "cl100k_base"
    ):
        self.chunk_size = chunk_size or config.chunk_size
        self.chunk_overlap = chunk_overlap or config.chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def split_by_sentences(self, text: str, language: str = "en") -> List[str]:
        """Split text into sentences based on language."""
        if language == "zh":
            # Chinese sentence endings
            sentences = re.split(r'([。！？；])', text)
            # Recombine with punctuation
            result = []
            for i in range(0, len(sentences) - 1, 2):
                if i + 1 < len(sentences):
                    result.append(sentences[i] + sentences[i + 1])
                else:
                    result.append(sentences[i])
            return [s for s in result if s.strip()]
        else:
            # English and other languages
            sentences = re.split(r'([.!?]+\s+)', text)
            result = []
            for i in range(0, len(sentences) - 1, 2):
                if i + 1 < len(sentences):
                    result.append(sentences[i] + sentences[i + 1])
                else:
                    result.append(sentences[i])
            return [s for s in result if s.strip()]
    
    def chunk_text_recursive(
        self,
        text: str,
        language: str = "en",
        max_tokens: int = None,
        overlap_tokens: int = None
    ) -> List[str]:
        """
        Recursively chunk text into smaller pieces.
        
        Args:
            text: Text to chunk
            language: Language code
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Token overlap between chunks
            
        Returns:
            List of text chunks
        """
        max_tokens = max_tokens or self.chunk_size
        overlap_tokens = overlap_tokens or self.chunk_overlap
        
        # Check if text is already small enough
        token_count = self.count_tokens(text)
        if token_count <= max_tokens:
            return [text]
        
        # Try splitting by paragraphs first
        if language in ["zh", "ja", "ko"] or is_cjk_text(text):
            # CJK languages - split by newlines and punctuation
            paragraphs = re.split(r'\n\n+', text)
        else:
            # Other languages - split by double newlines
            paragraphs = re.split(r'\n\n+', text)
        
        if len(paragraphs) > 1:
            # Recursively chunk paragraphs
            chunks = []
            current_chunk = ""
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # Check if adding this paragraph exceeds max_tokens
                test_chunk = current_chunk + "\n\n" + para if current_chunk else para
                
                if self.count_tokens(test_chunk) <= max_tokens:
                    current_chunk = test_chunk
                else:
                    # Save current chunk if not empty
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    # Start new chunk with overlap
                    if chunks and overlap_tokens > 0:
                        # Get last N tokens from previous chunk for overlap
                        prev_tokens = self.encoding.encode(chunks[-1])
                        overlap_text = self.encoding.decode(prev_tokens[-overlap_tokens:])
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para
            
            # Add final chunk
            if current_chunk:
                chunks.append(current_chunk)
            
            return chunks
        
        # If no paragraphs, split by sentences
        sentences = self.split_by_sentences(text, language)
        
        if len(sentences) > 1:
            chunks = []
            current_chunk = ""
            
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                
                test_chunk = current_chunk + " " + sent if current_chunk else sent
                
                if self.count_tokens(test_chunk) <= max_tokens:
                    current_chunk = test_chunk
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    # Overlap
                    if chunks and overlap_tokens > 0:
                        prev_tokens = self.encoding.encode(chunks[-1])
                        overlap_text = self.encoding.decode(prev_tokens[-overlap_tokens:])
                        current_chunk = overlap_text + " " + sent
                    else:
                        current_chunk = sent
            
            if current_chunk:
                chunks.append(current_chunk)
            
            return chunks
        
        # Last resort: split by tokens
        tokens = self.encoding.encode(text)
        chunks = []
        
        i = 0
        while i < len(tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            i += max_tokens - overlap_tokens
        
        return chunks
    
    def extract_page_number(self, text: str) -> int:
        """Extract page number from text with page marker."""
        match = re.search(r'\[PAGE (\d+)\]', text)
        if match:
            return int(match.group(1))
        return 0
    
    def chunk_document(
        self,
        text: str,
        doc_id: str,
        language: str = "en",
        metadata: Dict[str, Any] = None
    ) -> List[Chunk]:
        """
        Chunk entire document into Chunk objects.
        
        Args:
            text: Full document text
            doc_id: Document ID
            language: Language code
            metadata: Additional metadata
            
        Returns:
            List of Chunk objects
        """
        logger.info(f"Chunking document {doc_id} ({self.count_tokens(text)} tokens)")
        
        # Split into text chunks
        text_chunks = self.chunk_text_recursive(text, language)
        
        # Create Chunk objects
        chunks = []
        char_offset = 0
        
        for i, chunk_text in enumerate(text_chunks):
            # Extract page number from chunk
            page_num = self.extract_page_number(chunk_text)
            
            # Create chunk ID
            chunk_id = f"{doc_id}_chunk_{i:04d}"
            
            chunk = Chunk(
                text=chunk_text,
                chunk_id=chunk_id,
                doc_id=doc_id,
                language=language,
                page_num=page_num,
                start_char=char_offset,
                end_char=char_offset + len(chunk_text),
                metadata={
                    **(metadata or {}),
                    "chunk_index": i,
                    "total_chunks": len(text_chunks),
                    "token_count": self.count_tokens(chunk_text),
                }
            )
            
            chunks.append(chunk)
            char_offset += len(chunk_text)
        
        logger.success(f"Created {len(chunks)} chunks for document {doc_id}")
        
        return chunks
    
    def save_chunks(self, chunks: List[Chunk]):
        """Save chunks to disk."""
        try:
            chunks_dir = config.get_chunks_dir()
            
            # Group chunks by document
            doc_chunks = {}
            for chunk in chunks:
                if chunk.doc_id not in doc_chunks:
                    doc_chunks[chunk.doc_id] = []
                doc_chunks[chunk.doc_id].append(chunk.to_dict())
            
            # Save each document's chunks
            for doc_id, chunk_list in doc_chunks.items():
                output_file = chunks_dir / f"{doc_id}_chunks.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(chunk_list, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved {len(chunk_list)} chunks to {output_file}")
                
        except Exception as e:
            logger.error(f"Error saving chunks: {e}")

