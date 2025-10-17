"""
Application Startup Script
Handles prerequisites and starts the multilingual RAG system.
"""
import asyncio
import sys
import time
import subprocess
from pathlib import Path

def check_qdrant():
    """Check if Qdrant is accessible."""
    import httpx
    try:
        response = httpx.get("http://localhost:6333", timeout=2.0)
        return response.status_code == 200
    except:
        return False

def copy_pdfs_to_incoming():
    """Copy PDFs from pdfs/ to data/incoming/ directories."""
    import shutil
    
    pdf_dir = Path("pdfs")
    if not pdf_dir.exists():
        print("No pdfs/ directory found")
        return
    
    lang_map = {
        "bn": "bn",  # Bengali
        "ur": "ur",  # Urdu
        "zh": "zh",  # Chinese
    }
    
    copied = 0
    for lang_folder, lang_code in lang_map.items():
        source_dir = pdf_dir / lang_folder
        if source_dir.exists():
            dest_dir = Path(f"data/incoming/{lang_code}")
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            for pdf_file in source_dir.glob("*.pdf"):
                dest_file = dest_dir / pdf_file.name
                if not dest_file.exists():
                    shutil.copy2(pdf_file, dest_file)
                    print(f"  Copied: {pdf_file.name} -> data/incoming/{lang_code}/")
                    copied += 1
                else:
                    print(f"  Skipped (exists): {pdf_file.name}")
    
    print(f"\nTotal PDFs copied: {copied}")
    return copied

async def main():
    """Main startup routine."""
    print("=" * 70)
    print("  Multilingual Agentic RAG System - Startup")
    print("=" * 70)
    
    # Check Qdrant
    print("\n[1/5] Checking Qdrant...")
    if check_qdrant():
        print("  [OK] Qdrant is running on http://localhost:6333")
    else:
        print("  [WARNING] Qdrant is not running!")
        print("\n  Please start Qdrant first:")
        print("  1. Start Docker Desktop")
        print("  2. Run: docker-compose --profile cpu up -d")
        print("\n  OR download and run Qdrant locally:")
        print("  https://qdrant.tech/documentation/quick-start/")
        
        response = input("\n  Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("\nExiting...")
            sys.exit(1)
    
    # Copy PDFs
    print("\n[2/5] Copying PDFs to incoming directories...")
    copied = copy_pdfs_to_incoming()
    
    # Initialize storage
    print("\n[3/5] Initializing storage...")
    from src.common import storage
    await storage.initialize()
    print("  [OK] Storage initialized")
    
    # Initialize pipeline
    print("\n[4/5] Initializing document processing pipeline...")
    from src.main import DocumentProcessingPipeline
    pipeline = DocumentProcessingPipeline()
    await pipeline.initialize()
    print("  [OK] Pipeline ready")
    
    # Start background processing
    if copied > 0:
        print("\n[5/5] Starting background document processing...")
        await pipeline.start_processing()
        print(f"  [OK] Processing {copied} documents in background...")
        
        # Give it a few seconds to start processing
        await asyncio.sleep(2)
    else:
        print("\n[5/5] No new documents to process")
    
    # Start web UI
    print("\n" + "=" * 70)
    print("  Starting Web Interface...")
    print("=" * 70)
    print("\n  URL: http://localhost:8080")
    print("\n  Features:")
    print("  - Upload Tab: Upload new PDF documents")
    print("  - Chat Tab: Query your documents")
    print("  - Logs Tab: Monitor system activity")
    print("  - Config Tab: View system configuration")
    print("\n" + "=" * 70)
    
    # Start NiceGUI
    from src.frontend import start_app
    start_app()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

