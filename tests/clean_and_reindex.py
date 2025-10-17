"""
Clean and reindex all documents - complete reset
"""
import asyncio
import shutil
from pathlib import Path
from qdrant_client import QdrantClient

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common import logger, config

async def main():
    logger.info("=" * 80)
    logger.info("CLEANING AND REINDEXING")
    logger.info("=" * 80)
    
    # 1. Clean data directories
    logger.info("\n[1/4] Cleaning data directories...")
    data_path = Path("data")
    dirs_to_clean = ["processing", "ocr_raw", "ocr_clean", "chunks", "embeddings"]
    
    for dir_name in dirs_to_clean:
        dir_path = data_path / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            logger.info(f"  ✓ Removed {dir_name}/")
        dir_path.mkdir(exist_ok=True)
        logger.info(f"  ✓ Created fresh {dir_name}/")
    
    # 2. Clean Qdrant collection
    logger.info("\n[2/4] Cleaning Qdrant collection...")
    try:
        client = QdrantClient(url=config.qdrant_url)
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if config.qdrant_collection_name in collection_names:
            client.delete_collection(config.qdrant_collection_name)
            logger.info(f"  ✓ Deleted collection '{config.qdrant_collection_name}'")
        else:
            logger.info(f"  ℹ Collection '{config.qdrant_collection_name}' doesn't exist")
        
        logger.success("Qdrant cleaned successfully")
    except Exception as e:
        logger.error(f"  ✗ Qdrant cleanup failed: {e}")
        logger.warning("  → Make sure Qdrant is running (docker-compose up -d)")
        return 1
    
    # 3. Clean SQLite database
    logger.info("\n[3/4] Cleaning SQLite database...")
    db_path = data_path / "app.db"
    if db_path.exists():
        db_path.unlink()
        logger.info("  ✓ Removed app.db")
    logger.info("  ✓ Database will be recreated on next run")
    
    # 4. Verify PDFs are in incoming
    logger.info("\n[4/4] Verifying incoming PDFs...")
    incoming_path = data_path / "incoming"
    total_pdfs = 0
    for lang_dir in incoming_path.iterdir():
        if lang_dir.is_dir():
            pdfs = list(lang_dir.glob("*.pdf"))
            if pdfs:
                logger.info(f"  ✓ {lang_dir.name}: {len(pdfs)} PDFs")
                total_pdfs += len(pdfs)
    
    logger.info(f"\n  Total: {total_pdfs} PDFs ready for processing")
    
    logger.success("\n✅ Cleanup complete! Ready for fresh ingestion.")
    logger.info("\nNext steps:")
    logger.info("  1. Run: python -m src.main")
    logger.info("  2. Wait for ingestion to complete")
    logger.info("  3. Run: python test_rag_quick.py")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

