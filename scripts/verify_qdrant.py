"""
Verify Qdrant collection has embeddings
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from qdrant_client import QdrantClient
from src.common import logger, config

def main():
    logger.info("Verifying Qdrant collection...")
    
    try:
        client = QdrantClient(url=config.qdrant_url)
        
        # Get collection info
        collection_info = client.get_collection(config.qdrant_collection_name)
        vectors_count = collection_info.vectors_count
        points_count = collection_info.points_count
        
        logger.success(f"✅ Collection '{config.qdrant_collection_name}' exists!")
        logger.info(f"   Vectors: {vectors_count}")
        logger.info(f"   Points: {points_count}")
        
        if points_count > 0:
            # Sample a few points
            scroll_result = client.scroll(
                collection_name=config.qdrant_collection_name,
                limit=3
            )
            
            logger.info(f"\nSample points:")
            for i, point in enumerate(scroll_result[0], 1):
                payload = point.payload
                logger.info(f"\n{i}. Document: {payload.get('doc_id', 'Unknown')}")
                logger.info(f"   Language: {payload.get('language', 'Unknown')}")
                logger.info(f"   Page: {payload.get('page_num', 'Unknown')}")
                logger.info(f"   Text: {payload.get('text', '')[:100]}...")
            
            logger.success(f"\n✅ System is ready for querying!")
            return 0
        else:
            logger.warning("⚠️  Collection exists but has no points yet")
            logger.info("   Processing may still be ongoing...")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

