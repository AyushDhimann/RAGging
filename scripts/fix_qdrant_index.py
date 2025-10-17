"""
Fix Qdrant indexing threshold to build HNSW index
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from src.common import logger, config

def main():
    logger.info("Fixing Qdrant indexing configuration...")
    
    client = QdrantClient(url=config.qdrant_url)
    
    # Get current collection info
    collection_info = client.get_collection(config.qdrant_collection_name)
    logger.info(f"Current points: {collection_info.points_count}")
    logger.info(f"Current indexed vectors: {collection_info.indexed_vectors_count}")
    
    if collection_info.indexed_vectors_count == 0:
        logger.warning("⚠️  Vectors are NOT indexed! Updating optimizer config...")
        
        # Update optimizer config to force indexing
        client.update_collection(
            collection_name=config.qdrant_collection_name,
            optimizer_config={
                "indexing_threshold": 100,  # Much lower threshold
                "max_optimization_threads": 0  # Use default
            }
        )
        
        logger.success("✅ Updated optimizer config - indexing_threshold set to 100")
        logger.info("Qdrant will now build the HNSW index automatically")
        logger.info("Wait a few seconds for the index to build...")
        
        import time
        time.sleep(5)
        
        # Check again
        collection_info = client.get_collection(config.qdrant_collection_name)
        logger.info(f"After update - Indexed vectors: {collection_info.indexed_vectors_count}")
        
        if collection_info.indexed_vectors_count > 0:
            logger.success(f"✅ SUCCESS! {collection_info.indexed_vectors_count} vectors now indexed")
        else:
            logger.warning("⏳ Index is building, give it a few more seconds...")
    else:
        logger.success(f"✅ Vectors already indexed: {collection_info.indexed_vectors_count}")
    
    return 0

if __name__ == "__main__":
    exit(main())

