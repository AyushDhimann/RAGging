"""
Process all documents in incoming directories - complete pipeline
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.common import logger
from src.main import DocumentProcessingPipeline

async def main():
    logger.info("=" * 80)
    logger.info("DOCUMENT PROCESSING PIPELINE")
    logger.info("=" * 80)
    
    pipeline = DocumentProcessingPipeline()
    await pipeline.initialize()
    
    logger.info("\n[1/2] Scanning for existing PDFs...")
    await pipeline.ingestion_agent.scan_existing_files()
    
    logger.info("\n[2/2] Processing document queue...")
    
    # Process all queued documents
    processed = 0
    while True:
        job = await pipeline.ingestion_agent.get_next_job()
        if not job:
            break
        
        doc_id = job.get("doc_id")
        logger.info(f"\nProcessing: {job.get('filename')} ({job.get('language')})")
        
        try:
            await pipeline.process_document(job)
            processed += 1
            logger.success(f"✓ Completed: {doc_id}")
        except Exception as e:
            logger.error(f"✗ Failed {doc_id}: {e}")
            await pipeline.ingestion_agent.mark_job_failed(doc_id, str(e))
    
    logger.success(f"\n✅ Processing complete! {processed} documents processed.")
    logger.info("Next: Run 'python tests/test_rag_quick.py' to test the system")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

