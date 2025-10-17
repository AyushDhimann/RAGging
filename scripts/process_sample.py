"""
Process sample documents for quick testing (3 PDFs only)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common import logger
from src.main import DocumentProcessingPipeline

async def main():
    logger.info("=" * 80)
    logger.info("SAMPLE DOCUMENT PROCESSING (3 PDFs)")
    logger.info("=" * 80)
    
    # Initialize pipeline
    pipeline = DocumentProcessingPipeline()
    await pipeline.initialize()
    
    # Step 1: Scan for existing documents
    logger.info("\n[STEP 1/3] Scanning for PDFs...")
    await pipeline.ingestion_agent.scan_existing_files()
    
    # Step 2: Process first 3 documents only (one from each language)
    logger.info("\n[STEP 2/3] Processing sample documents...")
    max_docs = 3
    processed = 0
    
    while processed < max_docs:
        job = await pipeline.ingestion_agent.get_next_job()
        if not job:
            break
        
        doc_id = job.get("doc_id")
        filename = job.get("filename", "unknown")
        language = job.get("language", "unknown")
        
        logger.info(f"\n--- Processing {processed+1}/{max_docs}: {filename} ({language}) ---")
        
        try:
            result = await pipeline.process_document(job)
            if result and result.get("status") == "success":
                chunks = result.get("chunks", 0)
                logger.success(f"✅ {filename}: {chunks} chunks embedded")
                processed += 1
            else:
                logger.error(f"❌ {filename}: Processing failed")
                processed += 1
        except Exception as e:
            logger.error(f"❌ {filename}: Error - {e}")
            import traceback
            traceback.print_exc()
            processed += 1
    
    logger.success(f"\n✅ Sample processing complete! Processed {processed} documents")
    
    # Step 3: Verify and test retrieval
    logger.info("\n[STEP 3/3] Testing retrieval...")
    from qdrant_client import QdrantClient
    from src.agents.retriever_agent import RetrieverAgent
    
    try:
        client = QdrantClient(url="http://localhost:6333")
        collection_info = client.get_collection("multilingual_docs")
        points_count = collection_info.points_count
        
        logger.success(f"✅ Qdrant has {points_count} points")
        
        if points_count > 0:
            retriever = RetrieverAgent()
            
            # Test queries
            queries = [
                "What documents are available?",
                "政府文件",  # Government documents in Chinese
                "তথ্য",  # Information in Bengali
            ]
            
            for query in queries:
                logger.info(f"\nQuery: '{query}'")
                results = retriever.retrieve(query=query, top_k=2)
                
                if results:
                    logger.success(f"  → Retrieved {len(results)} results")
                    for i, result in enumerate(results, 1):
                        logger.info(f"    #{i}: score={result.score:.3f}, lang={result.language}, doc={result.doc_id[:30]}")
                else:
                    logger.warning(f"  → No results")
    
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n" + "=" * 80)
    logger.success("SAMPLE TEST COMPLETE!")
    logger.info("=" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

