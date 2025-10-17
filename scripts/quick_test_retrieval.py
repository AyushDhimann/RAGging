"""
Quick test of retrieval functionality
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common import logger
from src.agents.retriever_agent import RetrieverAgent

def main():
    logger.info("Testing retrieval...")
    
    retriever = RetrieverAgent()
    
    # Test query
    query = "document information"
    logger.info(f"Query: '{query}'")
    
    results = retriever.retrieve(query, top_k=3)
    
    logger.info(f"Retrieved {len(results)} results")
    
    if results:
        logger.success("SUCCESS! Retrieval is working!")
        for i, result in enumerate(results):
            logger.info(f"\n{i+1}. Score: {result.score:.4f}")
            logger.info(f"   Text: {result.text[:200]}...")
        return 0
    else:
        logger.error("FAILED! No results retrieved")
        return 1

if __name__ == "__main__":
    exit(main())

