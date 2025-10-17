"""
Simple retrieval test without using qdrant-client get_collection
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common import logger
from src.agents.retriever_agent import RetrieverAgent

def main():
    logger.info("Testing retrieval (simple)...")
    
    retriever = RetrieverAgent()
    
    # Test query
    query = "What is this document about?"
    logger.info(f"Query: '{query}'")
    
    try:
        results = retriever.retrieve(query, top_k=5)
        
        if results:
            logger.success(f"✅ SUCCESS! Retrieved {len(results)} results")
            for i, result in enumerate(results[:3]):
                logger.info(f"\n{i+1}. Score: {result.score:.4f}")
                logger.info(f"   Text: {result.text[:200]}...")
            return 0
        else:
            logger.error("❌ FAILED! No results retrieved")
            return 1
    except Exception as e:
        logger.error(f"❌ FAILED! Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

