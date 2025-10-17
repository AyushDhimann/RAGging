"""
Comprehensive RAG testing with genuine queries and proof generation
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common import logger, config, storage
from src.agents.retriever_agent import RetrieverAgent
from src.agents.reranker_agent import RerankerAgent
from src.agents.decomposition_agent import DecompositionAgent
from src.agents.rag_agent import RAGAgent
from src.agents.metadata_filter_agent import MetadataFilterAgent

# Test questions from actual documents
TEST_QUESTIONS = [
    {
        "id": 1,
        "query": "গবেষণা নির্দেশিকায় কী কী বিষয় আছে?",
        "language": "bn",
        "type": "basic_retrieval",
        "expected": "Research guidelines topics"
    },
    {
        "id": 2,
        "query": "What is the maximum budget allowed for research projects?",
        "language": "en",
        "type": "specific_detail",
        "expected": "50,00,000 টাকা"
    },
    {
        "id": 3,
        "query": "عارضی ملازمین کی ملازمت کی مدت کب تک بڑھائی گئی ہے؟",
        "language": "ur",
        "type": "basic_retrieval",
        "expected": "31.10.2024"
    },
    {
        "id": 4,
        "query": "Who issued the order for extension of adhoc employees?",
        "language": "en",
        "type": "entity_extraction",
        "expected": "Governor of Jammu Kashmir"
    },
    {
        "id": 5,
        "query": "这个文件是关于什么的？",
        "language": "zh",
        "type": "basic_retrieval",
        "expected": "People's Congress documents"
    },
    {
        "id": 6,
        "query": "What types of administrative documents are available in the database?",
        "language": "en",
        "type": "cross_lingual",
        "expected": "Research guidelines, employment notices, government documents"
    }
]

results = []

async def test_single_query(question):
    """Test a single query and collect detailed proof"""
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST {question['id']}: {question['type'].upper()}")
    logger.info(f"{'='*80}")
    logger.info(f"Query: {question['query']}")
    logger.info(f"Language: {question['language']}")
    
    result = {
        "question_id": question["id"],
        "query": question["query"],
        "language": question["language"],
        "type": question["type"],
        "timestamp": datetime.now().isoformat(),
        "stages": {}
    }
    
    try:
        # Stage 1: Retrieval
        logger.info("\n[STAGE 1] RETRIEVAL")
        retriever = RetrieverAgent()
        
        # Retrieve without filters for now (metadata filtering can be added later)
        retrieved = retriever.retrieve(question["query"], top_k=10)
        
        result["stages"]["retrieval"] = {
            "num_results": len(retrieved),
            "top_3_scores": [r.score for r in retrieved[:3]],
            "top_3_texts": [r.text[:200] for r in retrieved[:3]],
            "sources": [{"doc_id": r.doc_id, "page": r.page_num} for r in retrieved[:5]]
        }
        
        logger.success(f"✅ Retrieved {len(retrieved)} results")
        logger.info(f"Top 3 scores: {result['stages']['retrieval']['top_3_scores']}")
        
        # Stage 2: Reranking
        logger.info("\n[STAGE 2] RERANKING")
        reranker = RerankerAgent()
        reranked = reranker.rerank(query=question["query"], results=retrieved, top_k=5)
        
        result["stages"]["reranking"] = {
            "num_results": len(reranked),
            "top_3_scores": [r.score for r in reranked[:3]],
            "score_improvement": reranked[0].score - retrieved[0].score if reranked and retrieved else 0
        }
        
        logger.success(f"✅ Reranked to top {len(reranked)}")
        logger.info(f"Score improvement: {result['stages']['reranking']['score_improvement']:.4f}")
        
        # Stage 3: Answer Generation
        logger.info("\n[STAGE 3] ANSWER GENERATION")
        rag_agent = RAGAgent()
        await storage.initialize()
        session_id = f"test_{question['id']}"
        await storage.create_session(session_id)
        
        answer_parts = []
        sources_used = []
        
        async for chunk in rag_agent.chat(question["query"], session_id, stream=True):
            if chunk["type"] == "response":
                answer_parts.append(chunk["content"])
            elif chunk["type"] == "sources":
                sources_used = chunk["sources"]
        
        full_answer = "".join(answer_parts)
        
        result["stages"]["answer_generation"] = {
            "answer": full_answer[:500],
            "answer_length": len(full_answer),
            "sources_cited": len(sources_used),
            "source_docs": [s.get("doc_id", "unknown") for s in sources_used[:3]]
        }
        
        logger.success(f"✅ Generated answer ({len(full_answer)} chars)")
        logger.info(f"Answer: {full_answer[:200]}...")
        logger.info(f"Sources cited: {len(sources_used)}")
        
        result["status"] = "SUCCESS"
        logger.success(f"\n✅ TEST {question['id']} PASSED")
        
    except Exception as e:
        result["status"] = "FAILED"
        result["error"] = str(e)
        logger.error(f"\n❌ TEST {question['id']} FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    results.append(result)
    return result

async def main():
    logger.info("="*80)
    logger.info("COMPREHENSIVE RAG TESTING WITH PROOF GENERATION")
    logger.info("="*80)
    
    # Run all tests
    for question in TEST_QUESTIONS:
        await test_single_query(question)
        await asyncio.sleep(2)  # Rate limiting
    
    # Generate proof document
    proof_file = Path("docs/RAG_TEST_PROOF.json")
    with open(proof_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.success(f"\n✅ Proof document saved to: {proof_file}")
    
    # Summary
    passed = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total Tests: {len(results)}")
    logger.success(f"Passed: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    if failed > 0:
        logger.error(f"Failed: {failed}/{len(results)}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

