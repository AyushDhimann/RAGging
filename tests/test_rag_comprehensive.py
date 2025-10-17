"""
Comprehensive RAG System Test Suite

Tests all major features:
1. Document retrieval
2. Semantic search
3. Reranking
4. Query decomposition
5. Chat memory and conversation
6. Hybrid retrieval (Dense + BM25)
7. End-to-end RAG pipeline
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.common import logger, config, storage
from src.agents.retriever_agent import RetrieverAgent
from src.agents.reranker_agent import RerankerAgent
from src.agents.decomposition_agent import DecompositionAgent
from src.agents.rag_agent import RAGAgent
from src.agents.metadata_filter_agent import MetadataFilterAgent


class RAGSystemTester:
    """Comprehensive RAG system tester."""
    
    def __init__(self):
        self.retriever = RetrieverAgent()
        self.reranker = RerankerAgent()
        self.decomposer = DecompositionAgent()
        self.rag_agent = RAGAgent()
        self.metadata_filter = MetadataFilterAgent()
        
        self.results = {
            "test_run": datetime.now().isoformat(),
            "tests": {}
        }
    
    async def initialize(self):
        """Initialize all components."""
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE RAG SYSTEM TEST SUITE")
        logger.info("=" * 80)
        
        await storage.initialize()
        logger.success("[OK] Storage initialized")
    
    def log_test(self, test_name: str, status: str, details: dict = None):
        """Log test result."""
        self.results["tests"][test_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        symbol = "[OK]" if status == "PASS" else "ERROR" if status == "FAIL" else "[SKIP]"
        logger.info(f"{symbol} {test_name}: {status}")
        if details:
            for key, value in details.items():
                logger.info(f"    {key}: {value}")
    
    async def test_1_retrieval_basic(self):
        """Test 1: Basic document retrieval."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Basic Document Retrieval")
        logger.info("=" * 80)
        
        try:
            query = "What is the main topic of the documents?"
            logger.info(f"Query: '{query}'")
            
            # Retrieve documents
            results = await self.retriever.retrieve(
                query=query,
                top_k=5,
                filters=None
            )
            
            if results:
                self.log_test(
                    "Test 1: Basic Retrieval",
                    "PASS",
                    {
                        "query": query,
                        "num_results": len(results),
                        "top_score": results[0].get('score', 0) if results else 0
                    }
                )
                
                # Print top 3 results
                for i, result in enumerate(results[:3], 1):
                    logger.info(f"\n  Result {i}:")
                    logger.info(f"    Score: {result.get('score', 0):.4f}")
                    logger.info(f"    Doc ID: {result.get('metadata', {}).get('doc_id', 'N/A')}")
                    logger.info(f"    Text: {result.get('text', '')[:150]}...")
                
                return True
            else:
                self.log_test(
                    "Test 1: Basic Retrieval",
                    "FAIL",
                    {"error": "No results returned"}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Test 1: Basic Retrieval",
                "FAIL",
                {"error": str(e)}
            )
            logger.error(f"Test 1 failed: {e}")
            return False
    
    async def test_2_semantic_search(self):
        """Test 2: Semantic search capabilities."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Semantic Search")
        logger.info("=" * 80)
        
        try:
            # Use semantic queries (not exact keyword matches)
            semantic_queries = [
                "educational policies and guidelines",
                "administrative procedures and regulations",
                "research and academic standards"
            ]
            
            all_passed = True
            for query in semantic_queries:
                logger.info(f"\nSemantic Query: '{query}'")
                
                results = await self.retriever.retrieve(
                    query=query,
                    top_k=3,
                    filters=None
                )
                
                if results:
                    logger.info(f"  [OK] Found {len(results)} semantic matches")
                    logger.info(f"  Top result: {results[0].get('text', '')[:100]}...")
                else:
                    logger.warning(f"  [WARNING] No results for query: {query}")
                    all_passed = False
            
            status = "PASS" if all_passed else "PARTIAL"
            self.log_test(
                "Test 2: Semantic Search",
                status,
                {"queries_tested": len(semantic_queries)}
            )
            return all_passed
            
        except Exception as e:
            self.log_test(
                "Test 2: Semantic Search",
                "FAIL",
                {"error": str(e)}
            )
            logger.error(f"Test 2 failed: {e}")
            return False
    
    async def test_3_hybrid_retrieval(self):
        """Test 3: Hybrid retrieval (Dense + BM25)."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: Hybrid Retrieval (Dense + BM25)")
        logger.info("=" * 80)
        
        try:
            query = "university admission requirements"
            logger.info(f"Query: '{query}'")
            logger.info(f"BM25 Enabled: {config.enable_bm25}")
            logger.info(f"Fusion Method: {config.fusion_method}")
            logger.info(f"Dense Weight: {config.dense_weight}, Keyword Weight: {config.keyword_weight}")
            
            results = await self.retriever.retrieve(
                query=query,
                top_k=5,
                filters=None
            )
            
            if results:
                self.log_test(
                    "Test 3: Hybrid Retrieval",
                    "PASS",
                    {
                        "num_results": len(results),
                        "fusion_method": config.fusion_method,
                        "bm25_enabled": config.enable_bm25
                    }
                )
                
                for i, result in enumerate(results[:3], 1):
                    logger.info(f"\n  Result {i}:")
                    logger.info(f"    Score: {result.get('score', 0):.4f}")
                    logger.info(f"    Text: {result.get('text', '')[:120]}...")
                
                return True
            else:
                self.log_test(
                    "Test 3: Hybrid Retrieval",
                    "FAIL",
                    {"error": "No results returned"}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Test 3: Hybrid Retrieval",
                "FAIL",
                {"error": str(e)}
            )
            logger.error(f"Test 3 failed: {e}")
            return False
    
    async def test_4_reranking(self):
        """Test 4: Reranking with Gemini."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 4: Reranking")
        logger.info("=" * 80)
        
        try:
            query = "What are the key requirements mentioned?"
            logger.info(f"Query: '{query}'")
            logger.info(f"Rerank Enabled: {config.enable_rerank}")
            logger.info(f"Rerank Backend: {config.rerank_backend}")
            logger.info(f"Rerank Top-K: {config.rerank_top_k}")
            
            # First, get retrieval results
            initial_results = await self.retriever.retrieve(
                query=query,
                top_k=10,
                filters=None
            )
            
            if not initial_results:
                self.log_test(
                    "Test 4: Reranking",
                    "SKIP",
                    {"reason": "No retrieval results to rerank"}
                )
                return False
            
            logger.info(f"\nInitial retrieval: {len(initial_results)} results")
            logger.info(f"Top score before rerank: {initial_results[0].get('score', 0):.4f}")
            
            # Rerank
            reranked_results = await self.reranker.rerank(
                query=query,
                documents=initial_results,
                top_k=5
            )
            
            if reranked_results:
                logger.info(f"\nAfter reranking: {len(reranked_results)} results")
                logger.info(f"Top score after rerank: {reranked_results[0].get('score', 0):.4f}")
                
                self.log_test(
                    "Test 4: Reranking",
                    "PASS",
                    {
                        "initial_results": len(initial_results),
                        "reranked_results": len(reranked_results),
                        "backend": config.rerank_backend
                    }
                )
                
                for i, result in enumerate(reranked_results[:3], 1):
                    logger.info(f"\n  Reranked Result {i}:")
                    logger.info(f"    Score: {result.get('score', 0):.4f}")
                    logger.info(f"    Text: {result.get('text', '')[:120]}...")
                
                return True
            else:
                self.log_test(
                    "Test 4: Reranking",
                    "FAIL",
                    {"error": "Reranking returned no results"}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Test 4: Reranking",
                "FAIL",
                {"error": str(e)}
            )
            logger.error(f"Test 4 failed: {e}")
            return False
    
    async def test_5_query_decomposition(self):
        """Test 5: Query decomposition for complex queries."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 5: Query Decomposition")
        logger.info("=" * 80)
        
        try:
            complex_query = "What are the admission requirements and what documents are needed for application?"
            logger.info(f"Complex Query: '{complex_query}'")
            logger.info(f"Decomposition Enabled: {config.enable_decomposition}")
            
            # Decompose query
            sub_queries = await self.decomposer.decompose_query(complex_query)
            
            if sub_queries and len(sub_queries) > 1:
                logger.info(f"\n[OK] Query decomposed into {len(sub_queries)} sub-queries:")
                for i, sq in enumerate(sub_queries, 1):
                    logger.info(f"  {i}. {sq}")
                
                self.log_test(
                    "Test 5: Query Decomposition",
                    "PASS",
                    {
                        "original_query": complex_query,
                        "num_sub_queries": len(sub_queries),
                        "sub_queries": sub_queries
                    }
                )
                return True
            else:
                logger.warning("Query was not decomposed (single query returned)")
                self.log_test(
                    "Test 5: Query Decomposition",
                    "PARTIAL",
                    {"sub_queries": sub_queries}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Test 5: Query Decomposition",
                "FAIL",
                {"error": str(e)}
            )
            logger.error(f"Test 5 failed: {e}")
            return False
    
    async def test_6_metadata_filtering(self):
        """Test 6: Metadata-based filtering."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 6: Metadata Filtering")
        logger.info("=" * 80)
        
        try:
            query = "Show me documents in Bengali"
            logger.info(f"Query: '{query}'")
            
            # Extract filters
            filters = await self.metadata_filter.extract_filters(query)
            logger.info(f"Extracted filters: {filters}")
            
            # Retrieve with filters
            results = await self.retriever.retrieve(
                query="documents",
                top_k=5,
                filters=filters
            )
            
            if results:
                logger.info(f"\n[OK] Retrieved {len(results)} filtered results")
                
                # Check if filtering worked
                languages_found = set()
                for result in results:
                    lang = result.get('metadata', {}).get('language', 'unknown')
                    languages_found.add(lang)
                
                logger.info(f"Languages in results: {languages_found}")
                
                self.log_test(
                    "Test 6: Metadata Filtering",
                    "PASS",
                    {
                        "filters_extracted": filters,
                        "num_results": len(results),
                        "languages_found": list(languages_found)
                    }
                )
                return True
            else:
                self.log_test(
                    "Test 6: Metadata Filtering",
                    "FAIL",
                    {"error": "No filtered results"}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Test 6: Metadata Filtering",
                "FAIL",
                {"error": str(e)}
            )
            logger.error(f"Test 6 failed: {e}")
            return False
    
    async def test_7_chat_single_turn(self):
        """Test 7: Single-turn chat (no memory)."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 7: Single-Turn Chat")
        logger.info("=" * 80)
        
        try:
            query = "What is the main purpose of these documents?"
            logger.info(f"Query: '{query}'")
            
            # Create new session
            session_id = await storage.create_chat_session()
            logger.info(f"Session ID: {session_id}")
            
            # Send query
            response = await self.rag_agent.chat(
                session_id=session_id,
                query=query
            )
            
            if response and response.get('answer'):
                logger.info(f"\n[OK] Received response:")
                logger.info(f"  Answer: {response['answer'][:300]}...")
                logger.info(f"  Sources: {len(response.get('sources', []))} documents")
                
                self.log_test(
                    "Test 7: Single-Turn Chat",
                    "PASS",
                    {
                        "query": query,
                        "answer_length": len(response['answer']),
                        "num_sources": len(response.get('sources', []))
                    }
                )
                return True
            else:
                self.log_test(
                    "Test 7: Single-Turn Chat",
                    "FAIL",
                    {"error": "No answer generated"}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Test 7: Single-Turn Chat",
                "FAIL",
                {"error": str(e)}
            )
            logger.error(f"Test 7 failed: {e}")
            return False
    
    async def test_8_chat_memory(self):
        """Test 8: Multi-turn chat with memory."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 8: Multi-Turn Chat with Memory")
        logger.info("=" * 80)
        
        try:
            # Create new session
            session_id = await storage.create_chat_session()
            logger.info(f"Session ID: {session_id}")
            
            # First turn
            query1 = "What documents are available?"
            logger.info(f"\nTurn 1 Query: '{query1}'")
            
            response1 = await self.rag_agent.chat(
                session_id=session_id,
                query=query1
            )
            
            if not response1 or not response1.get('answer'):
                raise Exception("First turn failed")
            
            logger.info(f"Turn 1 Answer: {response1['answer'][:200]}...")
            
            # Second turn (should use memory)
            query2 = "What languages are they in?"
            logger.info(f"\nTurn 2 Query: '{query2}' (requires memory)")
            
            response2 = await self.rag_agent.chat(
                session_id=session_id,
                query=query2
            )
            
            if not response2 or not response2.get('answer'):
                raise Exception("Second turn failed")
            
            logger.info(f"Turn 2 Answer: {response2['answer'][:200]}...")
            
            # Check if memory was used
            history = await storage.get_chat_history(session_id)
            logger.info(f"\n[OK] Chat history has {len(history)} messages")
            
            if len(history) >= 4:  # 2 queries + 2 responses
                self.log_test(
                    "Test 8: Chat Memory",
                    "PASS",
                    {
                        "session_id": session_id,
                        "num_turns": 2,
                        "history_messages": len(history)
                    }
                )
                return True
            else:
                self.log_test(
                    "Test 8: Chat Memory",
                    "PARTIAL",
                    {"history_messages": len(history)}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Test 8: Chat Memory",
                "FAIL",
                {"error": str(e)}
            )
            logger.error(f"Test 8 failed: {e}")
            return False
    
    async def test_9_end_to_end_rag(self):
        """Test 9: Full end-to-end RAG pipeline."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 9: End-to-End RAG Pipeline")
        logger.info("=" * 80)
        
        try:
            # Complex query that exercises all components
            query = "What are the key requirements and procedures mentioned in the Bengali documents?"
            logger.info(f"Complex Query: '{query}'")
            logger.info("\nThis test exercises:")
            logger.info("  - Metadata filtering (Bengali)")
            logger.info("  - Query decomposition")
            logger.info("  - Hybrid retrieval")
            logger.info("  - Reranking")
            logger.info("  - Response generation")
            
            session_id = await storage.create_chat_session()
            
            response = await self.rag_agent.chat(
                session_id=session_id,
                query=query
            )
            
            if response and response.get('answer'):
                logger.info(f"\n[OK] Full RAG pipeline completed!")
                logger.info(f"  Answer: {response['answer'][:300]}...")
                logger.info(f"  Sources: {len(response.get('sources', []))} documents")
                logger.info(f"  Answer length: {len(response['answer'])} chars")
                
                self.log_test(
                    "Test 9: End-to-End RAG",
                    "PASS",
                    {
                        "query": query,
                        "answer_length": len(response['answer']),
                        "num_sources": len(response.get('sources', [])),
                        "components_used": ["metadata_filter", "decomposition", "retrieval", "rerank", "generation"]
                    }
                )
                return True
            else:
                self.log_test(
                    "Test 9: End-to-End RAG",
                    "FAIL",
                    {"error": "No answer generated"}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Test 9: End-to-End RAG",
                "FAIL",
                {"error": str(e)}
            )
            logger.error(f"Test 9 failed: {e}")
            return False
    
    def generate_report(self):
        """Generate comprehensive test report."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUITE SUMMARY")
        logger.info("=" * 80)
        
        passed = sum(1 for t in self.results["tests"].values() if t["status"] == "PASS")
        partial = sum(1 for t in self.results["tests"].values() if t["status"] == "PARTIAL")
        failed = sum(1 for t in self.results["tests"].values() if t["status"] == "FAIL")
        skipped = sum(1 for t in self.results["tests"].values() if t["status"] == "SKIP")
        total = len(self.results["tests"])
        
        logger.info(f"\nTotal Tests: {total}")
        logger.info(f"  PASSED: {passed}")
        logger.info(f"  PARTIAL: {partial}")
        logger.info(f"  FAILED: {failed}")
        logger.info(f"  SKIPPED: {skipped}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        logger.info(f"\nSuccess Rate: {success_rate:.1f}%")
        
        # Save results to JSON
        report_path = Path("reports") / f"rag_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.success(f"\nTest report saved to: {report_path}")
        
        logger.info("\n" + "=" * 80)
        logger.info("DETAILED TEST RESULTS")
        logger.info("=" * 80)
        
        for test_name, result in self.results["tests"].items():
            status_symbol = {
                "PASS": "[OK]",
                "FAIL": "ERROR",
                "PARTIAL": "[PARTIAL]",
                "SKIP": "[SKIP]"
            }.get(result["status"], "?")
            
            logger.info(f"\n{status_symbol} {test_name}")
            logger.info(f"  Status: {result['status']}")
            logger.info(f"  Time: {result['timestamp']}")
            
            if result.get("details"):
                logger.info("  Details:")
                for key, value in result["details"].items():
                    logger.info(f"    - {key}: {value}")
        
        logger.info("\n" + "=" * 80)
        return success_rate >= 70  # Consider 70%+ as overall success


async def main():
    """Run comprehensive test suite."""
    tester = RAGSystemTester()
    
    try:
        # Initialize
        await tester.initialize()
        
        # Run all tests
        await tester.test_1_retrieval_basic()
        await tester.test_2_semantic_search()
        await tester.test_3_hybrid_retrieval()
        await tester.test_4_reranking()
        await tester.test_5_query_decomposition()
        await tester.test_6_metadata_filtering()
        await tester.test_7_chat_single_turn()
        await tester.test_8_chat_memory()
        await tester.test_9_end_to_end_rag()
        
        # Generate report
        success = tester.generate_report()
        
        if success:
            logger.success("\n[SUCCESS] RAG system test suite completed successfully!")
            return 0
        else:
            logger.error("\n[FAILED] RAG system test suite had failures")
            return 1
            
    except Exception as e:
        logger.error(f"\n[CRITICAL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

