"""
Document ingestion only - no web UI
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.common import logger
from src.main import DocumentProcessingPipeline

async def main():
    logger.info("=" * 80)
    logger.info("DOCUMENT INGESTION (NO WEB UI)")
    logger.info("=" * 80)
    
    pipeline = DocumentProcessingPipeline()
    await pipeline.initialize()
    
    logger.info("\nScanning for existing documents...")
    await pipeline.ingestion_agent.scan_existing_files()
    
    logger.info("\nStarting document processing...")
    await pipeline.process_queue()
    
    logger.success("\n✅ Document ingestion complete!")
    logger.info("Next: Run 'python tests/test_rag_quick.py' to test the system")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        sys.exit(0)

