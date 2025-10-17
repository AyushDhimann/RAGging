"""
Complete processing and testing workflow
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common import logger
from src.main import DocumentProcessingPipeline

async def main():
    logger.info("=" * 80)
    logger.info("PROCESSING AND TESTING WORKFLOW")
    logger.info("=" * 80)
    
    # Initialize pipeline
    pipeline = DocumentProcessingPipeline()
    await pipeline.initialize()
    
    # Step 1: Scan for existing documents
    logger.info("\n[STEP 1/3] Scanning for existing PDFs...")
    await pipeline.ingestion_agent.scan_existing_files()
    
    # Step 2: Process all queued documents
    logger.info("\n[STEP 2/3] Processing documents...")
    processed = 0
    max_docs = 16  # Total PDFs we know exist
    
    while processed < max_docs:
        job = await pipeline.ingestion_agent.get_next_job()
        if not job:
            logger.warning(f"No more jobs found after {processed} documents")
            break
        
        doc_id = job.get("doc_id")
        filename = job.get("filename", "unknown")
        logger.info(f"\n--- Processing {processed+1}/{max_docs}: {filename} ---")
        
        try:
            result = await pipeline.process_document(job)
            if result and result.get("status") == "success":
                processed += 1
                chunks = result.get("chunks", 0)
                logger.success(f"✅ {filename}: {chunks} chunks embedded")
            else:
                logger.error(f"❌ {filename}: Processing failed")
        except Exception as e:
            logger.error(f"❌ {filename}: Error - {e}")
            processed += 1  # Count it anyway to avoid infinite loop
    
    logger.success(f"\n✅ Document processing complete! Processed {processed} documents")
    
    # Step 3: Verify Qdrant
    logger.info("\n[STEP 3/3] Verifying Qdrant collection...")
    from qdrant_client import QdrantClient
    
    try:
        client = QdrantClient(url="http://localhost:6333")
        collection_info = client.get_collection("multilingual_docs")
        points_count = collection_info.points_count
        
        logger.success(f"✅ Qdrant collection has {points_count} points")
        
        if points_count > 0:
            # Sample query
            logger.info("\n[SAMPLE QUERY TEST]")
            from src.agents.retriever_agent import RetrieverAgent
            
            retriever = RetrieverAgent()
            query = "What documents are available?"
            logger.info(f"Query: '{query}'")
            
            results = retriever.retrieve(query=query, top_k=3)
            
            if results:
                logger.success(f"✅ Retrieved {len(results)} results")
                for i, result in enumerate(results[:3], 1):
                    logger.info(f"\n  Result {i}:")
                    logger.info(f"    Score: {result.score:.4f}")
                    logger.info(f"    Doc: {result.doc_id}")
                    logger.info(f"    Language: {result.language}")
                    logger.info(f"    Text: {result.text[:100]}...")
            else:
                logger.warning("⚠️  No results returned")
        
    except Exception as e:
        logger.error(f"❌ Qdrant verification failed: {e}")
    
    logger.info("\n" + "=" * 80)
    logger.success("WORKFLOW COMPLETE!")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("  1. Run: python tests/test_rag_quick.py")
    logger.info("  2. Start web UI: python -m src.main")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\nProcess interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

