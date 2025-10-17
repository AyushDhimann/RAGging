"""
Main Orchestrator
Coordinates document processing pipeline and starts the application.
"""

import asyncio
from pathlib import Path
from typing import Optional

from .common import logger, config, storage
from .agents.ingestion_agent import IngestionAgent
from .agents.pdf_type_detector import PDFTypeDetector
from .agents.ocr_agent import OCRAgent
from .agents.cleanup_agent import CleanupAgent
from .agents.chunking_agent import ChunkingAgent
from .agents.embedding_agent import EmbeddingAgent
from .frontend import start_app


class DocumentProcessingPipeline:
    """
    Main document processing pipeline orchestrator.
    Coordinates all agents to process documents end-to-end.
    """
    
    def __init__(self):
        self.ingestion_agent = IngestionAgent()
        self.pdf_detector = PDFTypeDetector()
        self.ocr_agent = OCRAgent()
        self.cleanup_agent = CleanupAgent()
        self.chunking_agent = ChunkingAgent()
        self.embedding_agent = EmbeddingAgent()
        
        self.processing = False
    
    async def initialize(self):
        """Initialize all components."""
        logger.info("Initializing document processing pipeline...")
        
        # Initialize storage
        await storage.initialize()
        
        # Initialize ingestion agent
        await self.ingestion_agent.initialize()
        
        # Ensure Qdrant collection exists
        self.embedding_agent.ensure_collection()
        
        logger.success("Pipeline initialized successfully")
    
    async def process_document(self, job: dict):
        """
        Process a single document through the entire pipeline.
        
        Args:
            job: Job dictionary from storage
        """
        doc_id = job['doc_id']
        file_path = Path(job['file_path'])
        language = job['language']
        
        try:
            logger.info(f"Processing document: {doc_id} (language: {language})")
            
            # Step 1: OCR
            logger.info("Step 1: OCR processing...")
            page_texts = self.ocr_agent.process_document(file_path, language)
            
            if not page_texts:
                raise Exception("OCR failed: no text extracted")
            
            # Combine pages
            raw_text = self.ocr_agent.get_combined_text(page_texts)
            
            # Step 2: LLM Cleanup (optional based on config)
            if config.enable_llm_cleanup:
                logger.info("Step 2: LLM cleanup...")
                cleaned_text = await self.cleanup_agent.cleanup_text(raw_text, language)
                
                # Save cleaned text
                self.cleanup_agent.save_cleaned_text(doc_id, cleaned_text)
            else:
                logger.info("Step 2: LLM cleanup DISABLED - using raw OCR text")
                cleaned_text = raw_text
            
            # Step 3: Chunking
            logger.info("Step 3: Chunking...")
            chunks = self.chunking_agent.chunk_document(
                text=cleaned_text,
                doc_id=doc_id,
                language=language,
                metadata={
                    "original_file": file_path.name,
                    "num_pages": len(page_texts)
                }
            )
            
            # Save chunks
            self.chunking_agent.save_chunks(chunks)
            
            # Step 4: Embedding & Storage
            logger.info("Step 4: Embedding and storage...")
            await self.embedding_agent.process_document(chunks)
            
            # Mark as completed
            await self.ingestion_agent.mark_job_completed(doc_id)
            
            logger.success(f"Successfully processed document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {e}")
            await self.ingestion_agent.mark_job_failed(doc_id, str(e))
    
    async def process_queue(self):
        """Process pending jobs from the queue."""
        while self.processing:
            # Get next job
            job = await self.ingestion_agent.get_next_job()
            
            if job:
                await self.process_document(job)
            else:
                # No jobs, wait a bit
                await asyncio.sleep(5)
    
    async def start_processing(self):
        """Start background document processing."""
        self.processing = True
        logger.info("Started background document processing")
        
        # Process existing queue
        asyncio.create_task(self.process_queue())
        
        # Scan for existing files
        await self.ingestion_agent.scan_existing_files()
    
    def stop_processing(self):
        """Stop background processing."""
        self.processing = False
        logger.info("Stopped background document processing")


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("Multilingual Agentic RAG System")
    logger.info("=" * 80)
    
    # Start web UI (NiceGUI handles async internally)
    logger.info("Starting web interface...")
    start_app()


if __name__ == "__main__":
    main()

