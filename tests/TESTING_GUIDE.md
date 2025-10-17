# RAG System Testing Guide

## Overview

This guide covers comprehensive testing of all RAG system features.

---

## ✅ Fixed Issues

### 1. **Gemini Embedding Model Name Error** ✅ FIXED
**Error**: `Model names should start with 'models/' or 'tunedModels/', got: {name}`

**Fix Applied**:
- Updated `.env`: `EMBEDDING_MODEL=models/text-embedding-004`
- Updated `.env.example`: Same change
- This ensures compatibility with Gemini's API requirements

### 2. **LLM Cleanup Feature Flag** ✅ ADDED
**Change**: Added `ENABLE_LLM_CLEANUP` feature flag

**Default**: `false` (disabled by default)

**Files Modified**:
- `.env`: Added `ENABLE_LLM_CLEANUP=false`
- `.env.example`: Added `ENABLE_LLM_CLEANUP=false`
- `src/common/config.py`: Added `enable_llm_cleanup` field
- `src/main.py`: Added conditional logic to skip LLM cleanup when disabled

**Why**: LLM cleanup is time-consuming and expensive. Users can enable it only when needed.

---

## 🧪 Test Suite

### Running Comprehensive Tests

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Run comprehensive test suite
python test_rag_comprehensive.py
```

### Test Coverage

The comprehensive test suite (`test_rag_comprehensive.py`) includes:

#### **Test 1: Basic Document Retrieval**
- Tests basic retrieval functionality
- Verifies vector search is working
- Checks if documents are returned with scores

#### **Test 2: Semantic Search**
- Tests semantic understanding (not just keyword matching)
- Queries:
  - "educational policies and guidelines"
  - "administrative procedures and regulations"
  - "research and academic standards"

#### **Test 3: Hybrid Retrieval (Dense + BM25)**
- Tests combination of semantic + keyword search
- Verifies fusion method is working
- Checks dense/keyword weight configuration

#### **Test 4: Reranking**
- Tests Gemini-based reranking
- Compares scores before/after reranking
- Verifies top results are more relevant after reranking

#### **Test 5: Query Decomposition**
- Tests complex query breakdown
- Example: "What are the admission requirements and what documents are needed for application?"
- Should split into multiple sub-queries

#### **Test 6: Metadata Filtering**
- Tests filtering by language, document type, etc.
- Example: "Show me documents in Bengali"
- Verifies filter extraction and application

#### **Test 7: Single-Turn Chat**
- Tests basic chat without memory
- Verifies answer generation
- Checks source citations

#### **Test 8: Multi-Turn Chat with Memory**
- Tests conversation continuity
- Turn 1: "What documents are available?"
- Turn 2: "What languages are they in?" (should reference previous context)
- Verifies chat history persistence

#### **Test 9: End-to-End RAG Pipeline**
- Tests all components together
- Complex query exercising:
  - Metadata filtering
  - Query decomposition
  - Hybrid retrieval
  - Reranking
  - Response generation

---

## 📊 Test Results

### Expected Output

```
================================================================================
COMPREHENSIVE RAG SYSTEM TEST SUITE
================================================================================
[OK] Storage initialized

================================================================================
TEST 1: Basic Document Retrieval
================================================================================
Query: 'What is the main topic of the documents?'
[OK] Test 1: Basic Retrieval: PASS
    query: What is the main topic of the documents?
    num_results: 5
    top_score: 0.8234

  Result 1:
    Score: 0.8234
    Doc ID: bn_15092024_142_98b5f5b2
    Text: ...

[... more tests ...]

================================================================================
TEST SUITE SUMMARY
================================================================================

Total Tests: 9
  PASSED: 8
  PARTIAL: 1
  FAILED: 0
  SKIPPED: 0

Success Rate: 88.9%
```

### Test Report

After running, a detailed JSON report is saved to:
```
reports/rag_test_report_YYYYMMDD_HHMMSS.json
```

This includes:
- Test run timestamp
- Individual test results
- Pass/fail status
- Detailed metrics for each test
- Error messages (if any)

---

## 🔍 Manual Testing via Chat UI

### 1. Start the Application

```powershell
# Activate venv
.venv\Scripts\activate

# Start Qdrant (if not running)
docker-compose --profile cpu up -d

# Start Ollama service (if not running)
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden

# Start the application
python -m src.main
```

### 2. Open Web Interface

Navigate to: **http://localhost:8080**

### 3. Test Queries

Try these queries in the **Chat** tab:

#### **Basic Retrieval Test**
```
What documents are available in the system?
```

#### **Semantic Search Test**
```
Tell me about educational guidelines and policies
```

#### **Language Filtering Test**
```
Show me content from Bengali documents
```

#### **Complex Query (Decomposition Test)**
```
What are the admission requirements and what is the application process?
```

#### **Memory Test (Multi-Turn)**
```
Turn 1: What types of documents do we have?
Turn 2: Which language has the most documents?
Turn 3: Can you summarize them?
```

#### **Citation Test**
```
What are the key requirements mentioned? Please cite specific documents.
```

---

## 📈 Verifying Features

### ✅ Hybrid Retrieval

**Check**: Logs should show BM25 + Dense fusion

```
INFO - Using hybrid retrieval: Dense (0.6) + BM25 (0.4)
INFO - Retrieved 10 results from dense search
INFO - Retrieved 10 results from BM25 search
INFO - Fused to 10 final results
```

### ✅ Reranking

**Check**: Logs should show reranking process

```
INFO - Reranking 10 results with Gemini
INFO - Reranked to top 5 results
```

### ✅ Query Decomposition

**Check**: Complex queries are split

```
INFO - Decomposing query: "What are the admission requirements and what documents are needed?"
INFO - Sub-queries: ["What are the admission requirements?", "What documents are needed for application?"]
```

### ✅ Chat Memory

**Check**: Follow-up questions reference previous context

```
INFO - Retrieved 2 previous messages from history
INFO - Context window includes previous question
```

### ✅ LLM Cleanup (When Enabled)

**Check**: If `ENABLE_LLM_CLEANUP=true`

```
INFO - Step 2: LLM cleanup...
INFO - Cleaning text with Ollama
```

**Check**: If `ENABLE_LLM_CLEANUP=false` (default)

```
INFO - Step 2: LLM cleanup DISABLED - using raw OCR text
```

---

## 🐛 Troubleshooting

### No Results from Retrieval

**Check**:
1. Are documents indexed? Look at Qdrant collection count
2. Is Gemini API working? Check API keys
3. Are embeddings being generated? Check logs

```powershell
# Check Qdrant collection
curl http://localhost:6333/collections/multilingual_docs
```

### Chat Not Working

**Check**:
1. Is Ollama running? `ollama list`
2. Is deepseek-r1:1.5b available? Should show in list
3. Check Gemini fallback is configured

### Slow Performance

**Check**:
1. **Disable LLM Cleanup** (if enabled): Set `ENABLE_LLM_CLEANUP=false`
2. Reduce top_k values: Lower `RERANK_TOP_K`
3. Disable decomposition for simple queries: Set `ENABLE_DECOMPOSITION=false` temporarily

---

## 📝 Performance Benchmarks

### Expected Timings (Approximate)

| Operation | Time (CPU) | Time (GPU) |
|-----------|-----------|-----------|
| **Retrieval** | 200-500ms | 100-200ms |
| **Reranking (Gemini)** | 1-2s | 1-2s (API call) |
| **LLM Generation** | 3-5s (Ollama) | 1-2s (with GPU) |
| **Query Decomposition** | 2-3s (Ollama) | 1-2s (with GPU) |
| **End-to-End Chat** | 5-10s | 3-5s |

### With LLM Cleanup Enabled

| Operation | Time (CPU) |
|-----------|-----------|
| **OCR + Cleanup per page** | 5-10s |
| **Full document (10 pages)** | 50-100s |

**Recommendation**: Keep `ENABLE_LLM_CLEANUP=false` for faster processing unless text quality is critical.

---

## 🎯 Success Criteria

### Minimum Requirements

- ✅ **Retrieval**: Returns relevant results
- ✅ **Search**: Semantic understanding (not just keywords)
- ✅ **Reranking**: Improves result relevance
- ✅ **Chat**: Generates coherent answers
- ✅ **Memory**: Maintains conversation context
- ✅ **Sources**: Provides document citations

### Advanced Requirements

- ✅ **Hybrid Search**: Dense + BM25 fusion
- ✅ **Decomposition**: Handles complex queries
- ✅ **Filtering**: Language/metadata filters work
- ✅ **Multilingual**: Works across Bengali, Urdu, Chinese, etc.
- ✅ **Accuracy**: Answers are factually grounded in documents

---

## 🚀 Next Steps

### After Testing

1. **Review test report** in `reports/` directory
2. **Check logs** in `logs/app.log` for any warnings
3. **Verify document count** in Qdrant matches uploaded PDFs
4. **Test edge cases** with unusual queries
5. **Stress test** with many concurrent queries

### For Production

1. **Enable evaluation**: Set `ENABLE_EVAL=true`
2. **Monitor metrics**: RAGAS scores, latency, throughput
3. **Tune parameters**: Adjust chunk size, top_k, weights
4. **Scale Qdrant**: Consider cluster deployment for large datasets

---

## 📚 Additional Resources

- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Ollama Models**: `ollama list`
- **Logs**: `logs/app.log`
- **Test Reports**: `reports/`
- **Documentation**: `README.md`, `QUICK_START.md`

---

**Last Updated**: Based on current implementation with LLM cleanup feature flag and comprehensive testing suite.

