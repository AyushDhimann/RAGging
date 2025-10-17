"""
Process one sample PDF for quick testing
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common import logger
from src.main import DocumentProcessingPipeline

async def main():
    logger.info("=" * 80)
    logger.info("PROCESSING ONE SAMPLE PDF (Quick Test)")
    logger.info("=" * 80)
    
    # Initialize pipeline
    pipeline = DocumentProcessingPipeline()
    await pipeline.initialize()
    
    # Scan for PDFs
    logger.info("\n[1/3] Scanning for PDFs...")
    await pipeline.ingestion_agent.scan_existing_files()
    
    # Process just ONE document
    logger.info("\n[2/3] Processing first document...")
    job = await pipeline.ingestion_agent.get_next_job()
    
    if not job:
        logger.error("No jobs found!")
        return 1
    
    doc_id = job.get("doc_id")
    logger.info(f"\nProcessing: {job.get('filename')}")
    logger.info(f"Language: {job.get('language')}")
    
    try:
        await pipeline.process_document(job)
        logger.success(f"✅ Successfully processed: {job.get('filename')}")
        
        # Verify in Qdrant
        logger.info("\n[3/3] Verifying in Qdrant...")
        from qdrant_client import QdrantClient
        from src.common import config
        
        client = QdrantClient(url=config.qdrant_url)
        collection_info = client.get_collection(config.qdrant_collection_name)
        
        logger.success(f"✅ Qdrant has {collection_info.points_count} points!")
        logger.info(f"   Ready for testing!")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        sys.exit(0)

