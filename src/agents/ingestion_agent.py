"""
Ingestion Agent
Watches incoming directories, queues jobs to SQLite, and moves files to processing.
"""

import asyncio
import shutil
from pathlib import Path
from typing import List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from ..common import (
    logger, config, storage, JobStatus,
    generate_doc_id, detect_language_from_path
)


class PDFFileHandler(FileSystemEventHandler):
    """Handler for new PDF files in incoming directories."""
    
    def __init__(self, ingestion_agent: 'IngestionAgent'):
        self.ingestion_agent = ingestion_agent
    
    def on_created(self, event):
        """Handle file creation event."""
        if isinstance(event, FileCreatedEvent) and event.src_path.lower().endswith('.pdf'):
            # Schedule async processing
            asyncio.create_task(self.ingestion_agent.process_new_file(Path(event.src_path)))


class IngestionAgent:
    """
    Ingestion agent that watches incoming directories and queues PDF files.
    """
    
    def __init__(self):
        self.observers: List[Observer] = []
        self.watched_languages = ["en", "zh", "hi", "bn", "ur"]
    
    async def initialize(self):
        """Initialize the ingestion agent."""
        logger.info("Initializing Ingestion Agent...")
        
        # Ensure all incoming directories exist
        for lang in self.watched_languages:
            incoming_dir = config.get_incoming_dir(lang)
            incoming_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Watching directory: {incoming_dir}")
    
    async def process_new_file(self, file_path: Path):
        """
        Process a newly detected PDF file.
        
        Args:
            file_path: Path to the PDF file
        """
        try:
            # Wait a bit to ensure file is fully written
            await asyncio.sleep(1)
            
            if not file_path.exists():
                logger.warning(f"File no longer exists: {file_path}")
                return
            
            # Detect language from path
            language = detect_language_from_path(file_path)
            if not language:
                logger.warning(f"Could not detect language for {file_path}, skipping")
                return
            
            # Generate document ID
            doc_id = generate_doc_id(file_path, language)
            
            # Check if already processed
            existing_job = await storage.get_job(doc_id)
            if existing_job:
                logger.info(f"Document {doc_id} already in queue, skipping")
                return
            
            # Move to processing directory
            processing_dir = config.get_processing_dir()
            dest_path = processing_dir / f"{doc_id}.pdf"
            
            shutil.copy2(file_path, dest_path)
            logger.info(f"Copied {file_path.name} to processing directory")
            
            # Add job to queue
            await storage.add_job(
                doc_id=doc_id,
                file_path=str(dest_path),
                language=language,
                metadata={
                    "original_filename": file_path.name,
                    "original_path": str(file_path)
                }
            )
            
            logger.success(f"Queued job for {file_path.name} (doc_id: {doc_id})")
            
            # Optionally remove original file (or move to archive)
            # file_path.unlink()
            
        except Exception as e:
            logger.error(f"Error processing new file {file_path}: {e}")
    
    async def scan_existing_files(self):
        """Scan existing files in incoming directories and queue them."""
        logger.info("Scanning for existing PDF files...")
        
        for lang in self.watched_languages:
            incoming_dir = config.get_incoming_dir(lang)
            pdf_files = list(incoming_dir.glob("*.pdf"))
            
            logger.info(f"Found {len(pdf_files)} PDF files in {incoming_dir}")
            
            for pdf_file in pdf_files:
                await self.process_new_file(pdf_file)
    
    def start_watching(self):
        """Start watching incoming directories for new files."""
        logger.info("Starting file system watchers...")
        
        for lang in self.watched_languages:
            incoming_dir = config.get_incoming_dir(lang)
            
            observer = Observer()
            event_handler = PDFFileHandler(self)
            observer.schedule(event_handler, str(incoming_dir), recursive=False)
            observer.start()
            
            self.observers.append(observer)
            logger.info(f"Started watching: {incoming_dir}")
    
    def stop_watching(self):
        """Stop all file system watchers."""
        logger.info("Stopping file system watchers...")
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers.clear()
    
    async def get_next_job(self) -> Optional[dict]:
        """Get the next pending job from the queue."""
        jobs = await storage.get_pending_jobs(limit=1)
        if jobs:
            job = jobs[0]
            # Mark as processing
            await storage.update_job_status(job['doc_id'], JobStatus.PROCESSING)
            return job
        return None
    
    async def mark_job_completed(self, doc_id: str):
        """Mark a job as completed."""
        await storage.update_job_status(doc_id, JobStatus.COMPLETED)
        logger.success(f"Job {doc_id} marked as completed")
    
    async def mark_job_failed(self, doc_id: str, error_message: str):
        """Mark a job as failed."""
        await storage.update_job_status(doc_id, JobStatus.FAILED, error_message)
        logger.error(f"Job {doc_id} marked as failed: {error_message}")

