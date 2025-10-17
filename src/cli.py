"""
CLI Tool
Command-line interface for batch ingestion, testing, and evaluation.
"""

import asyncio
import argparse
from pathlib import Path
import time

from .common import logger, config, storage
from .main import DocumentProcessingPipeline
from .agents.rag_agent import RAGAgent
from .agents.evaluation_agent import EvaluationAgent


async def ingest_documents(directory: Path, language: str):
    """
    Ingest all PDF documents from a directory.
    
    Args:
        directory: Directory containing PDF files
        language: Language code for documents
    """
    logger.info(f"Ingesting documents from {directory} (language: {language})")
    
    pipeline = DocumentProcessingPipeline()
    await pipeline.initialize()
    
    # Find all PDFs
    pdf_files = list(directory.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Copy to incoming directory
    incoming_dir = config.get_incoming_dir(language)
    for pdf_file in pdf_files:
        dest = incoming_dir / pdf_file.name
        if not dest.exists():
            import shutil
            shutil.copy2(pdf_file, dest)
            logger.info(f"Copied {pdf_file.name} to incoming directory")
    
    # Scan and process
    await pipeline.ingestion_agent.scan_existing_files()
    
    # Start processing
    await pipeline.start_processing()
    
    # Wait for queue to empty
    while True:
        jobs = await storage.get_pending_jobs(limit=1)
        if not jobs:
            break
        logger.info("Waiting for processing to complete...")
        await asyncio.sleep(5)
    
    logger.success("Document ingestion complete!")


async def test_query(query: str, top_k: int = 5):
    """
    Test a single query against the RAG system.
    
    Args:
        query: Query text
        top_k: Number of results to retrieve
    """
    logger.info(f"Testing query: '{query}'")
    
    await storage.initialize()
    
    rag_agent = RAGAgent()
    
    # Get response
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80 + "\n")
    
    async for chunk in rag_agent.chat(query, stream=True):
        if chunk["type"] == "status":
            print(f"[STATUS] {chunk['message']}")
        elif chunk["type"] == "context":
            print(f"[CONTEXT] Retrieved {len(chunk['chunks'])} chunks")
            for i, c in enumerate(chunk['chunks'][:3], 1):
                print(f"  {i}. {c['doc_id']} (page {c['page_num']})")
        elif chunk["type"] == "response":
            print(chunk["content"], end="", flush=True)
        elif chunk["type"] == "error":
            print(f"\n[ERROR] {chunk['message']}")
    
    print("\n" + "=" * 80)


async def run_evaluation(queries_file: Path):
    """
    Run evaluation on a set of test queries.
    
    Args:
        queries_file: File containing test queries (one per line)
    """
    logger.info(f"Running evaluation with queries from {queries_file}")
    
    await storage.initialize()
    
    # Load queries
    with open(queries_file, 'r', encoding='utf-8') as f:
        queries = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Loaded {len(queries)} test queries")
    
    rag_agent = RAGAgent()
    eval_agent = EvaluationAgent()
    
    evaluations = []
    
    for i, query in enumerate(queries, 1):
        logger.info(f"Evaluating query {i}/{len(queries)}: '{query[:50]}...'")
        
        start_time = time.time()
        
        # Get response
        context = []
        response_parts = []
        
        async for chunk in rag_agent.chat(query, stream=True):
            if chunk["type"] == "context":
                context = [
                    type('RetrievalResult', (), c)()
                    for c in chunk['chunks']
                ]
            elif chunk["type"] == "response":
                response_parts.append(chunk["content"])
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        response = "".join(response_parts)
        
        # Evaluate
        if config.enable_eval:
            evaluation = eval_agent.evaluate_query(query, context, response, latency_ms)
            evaluations.append(evaluation)
    
    # Save report
    if evaluations:
        eval_agent.save_evaluation_report(evaluations)
        logger.success("Evaluation complete! Report saved to reports/")


def main():
    """CLI main entry point."""
    parser = argparse.ArgumentParser(
        description="Multilingual Agentic RAG - CLI Tool"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest PDF documents")
    ingest_parser.add_argument("directory", type=Path, help="Directory containing PDFs")
    ingest_parser.add_argument("--language", "-l", default="en", help="Language code")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Test a query")
    query_parser.add_argument("query", type=str, help="Query text")
    query_parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    
    # Evaluate command
    eval_parser = subparsers.add_parser("eval", help="Run evaluation")
    eval_parser.add_argument("queries_file", type=Path, help="File with test queries")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        asyncio.run(ingest_documents(args.directory, args.language))
    elif args.command == "query":
        asyncio.run(test_query(args.query, args.top_k))
    elif args.command == "eval":
        asyncio.run(run_evaluation(args.queries_file))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

