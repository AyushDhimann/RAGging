"""
Quick RAG System Test - Tests core features with correct APIs
"""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common import logger, config, storage
from src.agents.retriever_agent import RetrieverAgent
from src.agents.reranker_agent import RerankerAgent
from src.agents.decomposition_agent import DecompositionAgent
from src.agents.rag_agent import RAGAgent


async def test_query_decomposition():
    """Test query decomposition."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Query Decomposition")
    logger.info("=" * 80)
    
    decomposer = DecompositionAgent()
    query = "What are the admission requirements and what documents are needed?"
    logger.info(f"Query: '{query}'")
    
    sub_queries = await decomposer.decompose_query(query)
    logger.success(f"✅ Decomposed into {len(sub_queries)} sub-queries:")
    for i, sq in enumerate(sub_queries, 1):
        logger.info(f"  {i}. {sq}")
    
    return len(sub_queries) > 1


async def test_retrieval():
    """Test basic retrieval."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Document Retrieval")
    logger.info("=" * 80)
    
    retriever = RetrieverAgent()
    query = "educational guidelines"
    logger.info(f"Query: '{query}'")
    
    results = retriever.retrieve(query=query, top_k=5)
    
    if results and len(results) > 0:
        logger.success(f"✅ Retrieved {len(results)} results")
        logger.info(f"Top result score: {results[0].score:.4f}")
        logger.info(f"Top result: {results[0].text[:150]}...")
        return True
    else:
        logger.warning("⚠️  No results returned")
        return False


async def test_reranking():
    """Test reranking."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Reranking")
    logger.info("=" * 80)
    
    retriever = RetrieverAgent()
    reranker = RerankerAgent()
    
    query = "What are the requirements?"
    logger.info(f"Query: '{query}'")
    
    # Get initial results
    results = retriever.retrieve(query=query, top_k=10)
    
    if not results:
        logger.warning("⚠️  No retrieval results to rerank")
        return False
    
    logger.info(f"Initial: {len(results)} results, top score: {results[0].score:.4f}")
    
    # Rerank
    reranked = reranker.rerank(query=query, results=results, top_k=5)
    
    if reranked:
        logger.success(f"✅ Reranked to {len(reranked)} results")
        logger.info(f"Top reranked score: {reranked[0].score:.4f}")
        return True
    else:
        logger.warning("⚠️  Reranking failed")
        return False


async def test_chat_single_turn():
    """Test single-turn chat."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Single-Turn Chat")
    logger.info("=" * 80)
    
    await storage.initialize()
    rag_agent = RAGAgent()
    
    session_id = str(uuid.uuid4())
    await storage.create_session(session_id)
    
    query = "What documents are available?"
    logger.info(f"Query: '{query}'")
    
    # Collect streamed response
    response_text = ""
    context_chunks = []
    
    async for chunk in rag_agent.chat(session_id=session_id, query=query):
        if chunk.get("type") == "response":
            response_text += chunk.get("content", "")
        elif chunk.get("type") == "context":
            context_chunks = chunk.get("chunks", [])
    
    if response_text:
        logger.success("✅ Chat response generated")
        logger.info(f"Answer: {response_text[:200]}...")
        logger.info(f"Sources: {len(context_chunks)} documents")
        return True
    else:
        logger.warning("⚠️  No answer generated")
        return False


async def test_chat_memory():
    """Test multi-turn chat with memory."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Chat Memory (Multi-Turn)")
    logger.info("=" * 80)
    
    await storage.initialize()
    rag_agent = RAGAgent()
    
    session_id = str(uuid.uuid4())
    await storage.create_session(session_id)
    
    # Turn 1
    query1 = "What types of documents do we have?"
    logger.info(f"\nTurn 1: '{query1}'")
    
    response1_text = ""
    async for chunk in rag_agent.chat(session_id=session_id, query=query1):
        if chunk.get("type") == "response":
            response1_text += chunk.get("content", "")
    
    if not response1_text:
        logger.warning("⚠️  Turn 1 failed")
        return False
    
    logger.info(f"Turn 1 answer: {response1_text[:150]}...")
    
    # Turn 2 (should use memory)
    query2 = "Which language has the most?"
    logger.info(f"\nTurn 2: '{query2}' (requires memory)")
    
    response2_text = ""
    async for chunk in rag_agent.chat(session_id=session_id, query=query2):
        if chunk.get("type") == "response":
            response2_text += chunk.get("content", "")
    
    if not response2_text:
        logger.warning("⚠️  Turn 2 failed")
        return False
    
    logger.info(f"Turn 2 answer: {response2_text[:150]}...")
    
    # Check history
    messages = await storage.get_session_messages(session_id)
    logger.success(f"✅ Chat history has {len(messages)} messages (2 turns)")
    return len(messages) >= 4  # 2 user + 2 assistant messages


async def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("RAG SYSTEM QUICK TEST SUITE")
    logger.info("=" * 80)
    
    results = {
        "Query Decomposition": False,
        "Document Retrieval": False,
        "Reranking": False,
        "Single-Turn Chat": False,
        "Chat Memory": False
    }
    
    try:
        # Run tests
        results["Query Decomposition"] = await test_query_decomposition()
        results["Document Retrieval"] = await test_retrieval()
        results["Reranking"] = await test_reranking()
        results["Single-Turn Chat"] = await test_chat_single_turn()
        results["Chat Memory"] = await test_chat_memory()
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\nPassed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed >= 3:
        logger.success("\n✅ SUCCESS: Core RAG features are working!")
        return 0
    else:
        logger.error("\n❌ FAILED: Some core features need attention")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

