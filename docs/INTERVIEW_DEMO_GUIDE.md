# Interview Demo Guide - Multilingual RAG System

## System Overview

This is a **production-ready Multilingual Agentic RAG (Retrieval-Augmented Generation) System** that processes documents in multiple languages (English, Chinese, Hindi, Bengali, Urdu) and provides intelligent question-answering with full chat memory.

---

## Architecture & Data Flow

```
PDFs (multilingual) → Ingestion → OCR (Tesseract) → Chunking → Embeddings (Gemini) → Qdrant → Retrieval → Reranking → LLM Answer
```

### Detailed Flow:

1. **Document Ingestion** (`src/agents/ingestion_agent.py`)
   - Watches `data/incoming/<lang>/` directories
   - Detects new PDFs and queues them for processing
   - Moves files to `data/processing/` to avoid reprocessing
   
2. **PDF Type Detection** (`src/agents/pdf_type_detector.py`)
   - Analyzes each page to determine if it's scanned or digital
   - Scanned pages → Tesseract OCR
   - Digital pages → Direct text extraction (PyMuPDF)

3. **OCR Processing** (`src/agents/ocr_agent.py`)
   - Uses Tesseract with language-specific models (`eng`, `chi_sim`, `hin`, `ben`, `urd`)
   - Saves raw OCR text to `data/ocr_raw/`
   - **Feature Flag**: Optional LLM cleanup to fix OCR errors (disabled by default)

4. **Text Cleanup** (`src/agents/cleanup_agent.py`) - **OPTIONAL**
   - Uses DeepSeek-R1 or Gemini Flash to normalize OCR text
   - Fixes spacing, diacritics, and common OCR errors
   - Controlled by `ENABLE_LLM_CLEANUP` env variable (default: false)

5. **Chunking** (`src/agents/chunking_agent.py`)
   - Language-aware recursive splitting (handles CJK characters)
   - 450-550 tokens per chunk with 50-80 token overlap
   - Preserves document structure (paragraphs, sections)
   - Adds metadata: `doc_id`, `page_num`, `language`, `section`
   - Saves chunks to `data/chunks/<doc_id>_chunks.json`

6. **Embedding** (`src/agents/embedding_agent.py`)
   - Uses Google Gemini `models/text-embedding-004` (768-dimensional)
   - Batch processing with automatic key rotation for rate limiting
   - Stores vectors + payloads in Qdrant collection `multilingual_docs`

7. **Hybrid Retrieval** (`src/agents/retriever_agent.py`)
   - **Dense Search**: Semantic similarity (cosine) via Qdrant
   - **Keyword Search**: BM25 for exact term matching
   - **Fusion**: Weighted combination (60% dense, 40% keyword)
   - **Metadata Filtering**: Filter by language, document, page

8. **Reranking** (`src/agents/reranker_agent.py`)
   - Uses Gemini Flash to score relevance of top-K results
   - Improves precision by reordering based on actual content understanding

9. **Query Decomposition** (`src/agents/decomposition_agent.py`)
   - Breaks complex queries into simpler sub-queries
   - Example: "What are requirements and documents?" → ["What are requirements?", "What documents?"]
   - Retrieves for each sub-query and merges results

10. **RAG Generation** (`src/agents/rag_agent.py`)
    - Primary: Ollama DeepSeek-R1:1.5b (local, CPU-optimized)
    - Fallback: Gemini Flash (cloud)
    - Streaming responses for real-time UI
    - Chat memory integration (SQLite)

11. **Chat Memory** (`src/common/storage.py`)
    - SQLite database stores sessions and messages
    - Multi-turn conversations with context awareness
    - Session-based history tracking

---

## Key Interview Questions & Answers

### 1. **"How does your system handle multiple languages?"**

**Answer**: 
- Language-specific Tesseract models for OCR (`chi_sim`, `hin`, `ben`, `urd`)
- Language-aware chunking that respects CJK character boundaries
- Metadata stored in Qdrant allows filtering by language
- Gemini embeddings are inherently multilingual
- Directory structure separates incoming documents by language

**Proof in Code**:
- `.env`: `OCR_LANGS=eng,chi_sim,hin,ben,urd`
- `src/agents/ocr_agent.py:36-38`: Language mapping
- `src/agents/chunking_agent.py:32-40`: CJK-aware splitting
- `data/incoming/*/`: Language-specific directories

---

### 2. **"How do you ensure retrieval quality?"**

**Answer**: **Hybrid Retrieval with Reranking**
1. **Dense Search** (semantic): Captures meaning and context
2. **BM25** (keyword): Ensures exact terms aren't missed  
3. **Fusion**: Combines both methods (configurable weights)
4. **Gemini Reranking**: Final ranking based on actual relevance

**Proof in Code**:
- `src/agents/retriever_agent.py:93-156`: Hybrid retrieval implementation
- `.env`: `ENABLE_BM25=true`, `DENSE_WEIGHT=0.6`, `KEYWORD_WEIGHT=0.4`
- `src/agents/reranker_agent.py:25-70`: Reranking logic

**Live Demo**:
```python
# tests/test_rag_quick.py - test_retrieval()
retriever.retrieve(query="educational guidelines", top_k=5)
# Shows both dense and BM25 results, fused and ranked
```

---

### 3. **"How do you handle complex queries?"**

**Answer**: **Query Decomposition**
- Complex queries are broken into simpler sub-queries
- Each sub-query is independently retrieved
- Results are deduplicated and merged

**Example**:
- Input: "What are the admission requirements and what documents are needed?"
- Decomposed: 
  1. "What are the admission requirements?"
  2. "What documents are needed for admission?"

**Proof in Code**:
- `src/agents/decomposition_agent.py:24-60`: Decomposition logic
- `src/agents/rag_agent.py:76-96`: Used in RAG pipeline

**Live Demo**:
```python
# tests/test_rag_quick.py - test_query_decomposition()
decomposer.decompose_query("What are requirements and documents?")
```

---

### 4. **"How do you manage API rate limits?"**

**Answer**: **API Key Rotation**
- Multiple Gemini API keys in `.env` (comma-separated)
- Round-robin rotation with backoff on errors
- Automatic retry with exponential backoff

**Proof in Code**:
- `.env`: `GEMINI_API_KEYS=key1,key2,key3`
- `src/common/config.py:51-62`: Key parsing and rotation
- `src/agents/embedding_agent.py:40-45`: Key rotator initialization

---

### 5. **"How do you ensure accuracy of OCR?"**

**Answer**: **Two-stage approach with feature flag**
1. **Tesseract OCR** with language-specific models
2. **Optional LLM Cleanup** (DeepSeek/Gemini) to fix errors
   - Disabled by default (`ENABLE_LLM_CLEANUP=false`)
   - Can be enabled for higher accuracy at cost of processing time

**Proof in Code**:
- `src/agents/ocr_agent.py:40-75`: Tesseract OCR
- `src/agents/cleanup_agent.py:24-60`: LLM cleanup
- `src/main.py:72-81`: Conditional cleanup based on feature flag

---

### 6. **"How do you demonstrate chat memory?"**

**Answer**: **Multi-turn conversations with SQLite persistence**
- Each chat session has a unique ID
- Messages stored with role (user/assistant) and timestamps
- RAG agent retrieves last N messages for context

**Live Demo**:
```python
# tests/test_rag_quick.py - test_chat_memory()
# Turn 1: "What types of documents do we have?"
# Turn 2: "Which language has the most?" (uses memory from Turn 1)
```

**Proof in Code**:
- `src/common/storage.py:48-94`: Session and message management
- `src/agents/rag_agent.py:296-300`: History retrieval
- `data/app.db`: SQLite database with `chat_sessions` and `chat_messages` tables

---

### 7. **"How do you filter documents?"**

**Answer**: **Metadata Filtering**
- Every chunk has metadata: `doc_id`, `page_num`, `language`, `filename`
- Queries can include filters: "in Bengali documents", "from page 5"
- `MetadataFilterAgent` extracts filters from natural language

**Proof in Code**:
- `src/agents/metadata_filter_agent.py`: Filter extraction
- `src/agents/retriever_agent.py:91-95`: Applied during retrieval
- Qdrant payloads include all metadata

---

### 8. **"How do you evaluate system performance?"**

**Answer**: **RAGAS Metrics + Custom Metrics**
- **Context Precision**: How relevant are retrieved chunks?
- **Context Recall**: Did we retrieve all relevant chunks?
- **Faithfulness**: Is answer grounded in context?
- **Answer Relevance**: Does answer match the question?
- **Latency Tracking**: End-to-end response time

**Proof in Code**:
- `src/agents/evaluation_agent.py`: RAGAS integration
- `reports/`: Evaluation results in JSON + HTML
- `.env`: `ENABLE_EVAL=true`, `EVAL_MODEL=gemini-flash-latest`

---

## Demonstrating The Full Pipeline

### Step 1: Show Clean State
```bash
# Show that Qdrant is empty
curl http://localhost:6333/collections/multilingual_docs | jq '.result.vectors_count'
# Expected: 0
```

### Step 2: Ingest Documents
```bash
python process_documents.py
```

**Watch the flow**:
- PDFs detected in `data/incoming/<lang>/`
- OCR processing (Tesseract)
- Chunks created in `data/chunks/`
- Embeddings generated (Gemini API calls)
- Vectors stored in Qdrant

### Step 3: Verify in Qdrant
```bash
curl http://localhost:6333/collections/multilingual_docs | jq '.result.vectors_count'
# Expected: > 0 (number of chunks)
```

### Step 4: Test Retrieval
```bash
python tests/test_rag_quick.py
```

**What it tests**:
1. ✅ Query Decomposition
2. ✅ Document Retrieval (hybrid + BM25)
3. ✅ Reranking
4. ✅ Single-turn Chat
5. ✅ Multi-turn Chat with Memory

### Step 5: Show Chat Interface
```bash
python -m src.main
# Visit http://localhost:8080
```

**Live Demo in UI**:
- Upload a new PDF
- Ask questions
- Show chat history
- Switch languages mid-conversation

---

## File Organization

```
project/
├── data/
│   ├── incoming/<lang>/   # Drop PDFs here
│   ├── processing/        # Currently being processed
│   ├── ocr_raw/           # Raw OCR text
│   ├── ocr_clean/         # LLM-cleaned text (if enabled)
│   ├── chunks/            # Chunked documents (JSON)
│   ├── embeddings/        # Embedding metadata
│   └── app.db             # SQLite (chat memory)
│
├── src/
│   ├── agents/            # 11 specialized agents
│   ├── common/            # Config, logging, storage, utils
│   ├── frontend/          # NiceGUI web interface
│   ├── main.py            # Main orchestrator
│   └── cli.py             # CLI for batch operations
│
├── tests/
│   ├── test_rag_quick.py         # Quick integration test
│   ├── test_rag_comprehensive.py # Full test suite
│   ├── clean_and_reindex.py      # Reset everything
│   └── TEST_RESULTS.md           # Test results log
│
├── logs/                  # Application logs
├── reports/               # Evaluation reports
├── .env                   # Environment configuration
├── requirements.txt       # Python dependencies
└── docker-compose.yml     # Qdrant service
```

---

## Environment Variables (`.env`)

### Critical Settings:
```env
# Gemini API (for embeddings & fallback LLM)
GEMINI_API_KEYS=key1,key2,key3         # Comma-separated for rotation
EMBEDDING_MODEL=models/text-embedding-004

# LLMs
LLM_PRIMARY=ollama:deepseek-r1:1.5b    # Local, CPU-optimized
LLM_FALLBACK=gemini-flash-latest       # Cloud fallback

# OCR
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
OCR_LANGS=eng,chi_sim,hin,ben,urd
ENABLE_LLM_CLEANUP=false               # Feature flag

# Retrieval
ENABLE_BM25=true
DENSE_WEIGHT=0.6
KEYWORD_WEIGHT=0.4
ENABLE_RERANK=true

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=multilingual_docs
```

---

## Troubleshooting & FAQs

### Q: "Embeddings failing?"
**A**: Check Gemini API keys are valid and have quota:
```bash
python -c "from src.common.config import config; print(config.get_gemini_keys())"
```

### Q: "No retrieval results?"
**A**: Verify Qdrant has data:
```bash
curl http://localhost:6333/collections/multilingual_docs/points/scroll | jq
```

### Q: "OCR not working?"
**A**: Verify Tesseract installation:
```bash
tesseract --version
tesseract --list-langs  # Should show: eng, chi_sim, hin, ben, urd
```

### Q: "Chat memory not working?"
**A**: Check SQLite database:
```bash
sqlite3 data/app.db ".tables"  # Should show: chat_sessions, chat_messages, job_queue
```

---

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| **PDF Processing** | ~30-60s per page (OCR + chunking + embedding) |
| **Retrieval Latency** | ~200-500ms (hybrid + rerank) |
| **Chat Response** | ~2-5s (streaming, first token <1s) |
| **Memory Footprint** | ~2-4GB RAM (Ollama model) |
| **Embedding Batch** | ~100 chunks/minute (Gemini API) |

---

## What Makes This Production-Ready?

1. ✅ **Error Handling**: Retries, fallbacks, graceful degradation
2. ✅ **Logging**: Rich structured logs for debugging
3. ✅ **Configuration**: Environment-based, no hard-coded values
4. ✅ **Scalability**: Batch processing, async I/O, queue-based
5. ✅ **Monitoring**: Evaluation metrics, latency tracking
6. ✅ **Modularity**: 11 independent agents, easy to swap
7. ✅ **Testing**: Comprehensive test suite
8. ✅ **Documentation**: In-code docs + guides
9. ✅ **Feature Flags**: Toggle expensive features (LLM cleanup, eval)
10. ✅ **Multi-tenancy Ready**: Session-based isolation

---

## Next Steps for Production Deployment

1. **Containerization**: Docker multi-stage build
2. **Orchestration**: Kubernetes/Docker Swarm
3. **Scaling**: Horizontal scaling of workers
4. **Monitoring**: Prometheus + Grafana
5. **CI/CD**: Automated testing and deployment
6. **Security**: API key management (Vault), HTTPS
7. **Caching**: Redis for frequently accessed data
8. **Load Balancing**: NGINX for web tier
9. **Database**: PostgreSQL for metadata (vs SQLite)
10. **Object Storage**: S3 for PDFs and chunks

---

**Created**: October 2025  
**Last Updated**: October 16, 2025  
**Status**: ✅ Production-Ready

