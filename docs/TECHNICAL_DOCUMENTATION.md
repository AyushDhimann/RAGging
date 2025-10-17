# Technical Documentation
## Multilingual Agentic RAG System

**Version:** 1.0  
**Date:** October 2025  
**Pages:** 3

---

## 1. System Architecture & Components

### 1.1 High-Level Architecture

```
┌─────────────── INGESTION LAYER ───────────────┐
│  PDF Upload → Type Detection → OCR Agent      │
│  (NiceGUI UI)  (Scanned/Digital) (Tesseract)  │
└────────────────────┬───────────────────────────┘
                     ▼
┌─────────────── PROCESSING LAYER ──────────────┐
│  Chunking Agent → Embedding Agent → Qdrant    │
│  (Lang-Aware)     (Gemini API)     (Vector DB)│
└────────────────────┬───────────────────────────┘
                     ▼
┌─────────────── RETRIEVAL LAYER ───────────────┐
│  Query → Metadata Filter → Decomposition      │
│         → Hybrid Retrieval → Reranker         │
│  (BM25 + Semantic Search) (Gemini Flash)      │
└────────────────────┬───────────────────────────┘
                     ▼
┌─────────────── GENERATION LAYER ──────────────┐
│  RAG Agent → LLM (Ollama) → Streaming Response│
│  (Context + Memory) (gemma3:4b) (WebSocket)   │
└───────────────────────────────────────────────┘
```

### 1.2 Core Components

#### 1.2.1 Ingestion Agent
- **Function:** Watches `data/incoming/<lang>/` directories
- **Queue:** SQLite-based job queue
- **Process:** Moves files to `data/processing/` during ingestion
- **Languages:** en, zh, hi, bn, ur (auto-detected from folder structure)
- **Output:** Job records in SQLite with status tracking

#### 1.2.2 PDF Type Detector
- **Library:** PyMuPDF (`fitz`)
- **Detection:** Per-page analysis
- **Criteria:** Text extraction success rate
- **Types:** Digital (extractable text) vs Scanned (requires OCR)
- **Threshold:** < 50 chars/page → Scanned

#### 1.2.3 OCR Agent
- **Engine:** Tesseract 5.0+
- **Languages:** eng, chi_sim, hin, ben, urd
- **Mode:** `--oem 1 --psm 6` (LSTM + uniform text block)
- **Process:** 
  - Scanned pages: `pdf2image` → Tesseract → text
  - Digital pages: PyMuPDF text extraction
- **Output:** `data/ocr_raw/<doc_id>_raw.txt` with page markers

#### 1.2.4 Chunking Agent
- **Strategy:** Recursive Character Text Splitter
- **Chunk Size:** 450-550 tokens (language-aware)
- **Overlap:** 50-80 tokens (10-15%)
- **Metadata:** doc_id, page_num, language, chunk_index
- **Special Handling:** CJK characters counted differently
- **Output:** JSON in `data/chunks/`

#### 1.2.5 Embedding Agent
- **Model:** `models/text-embedding-004` (Gemini)
- **Dimension:** 768
- **Task Type:** `retrieval_document`
- **Batching:** 100 chunks per API call
- **Key Rotation:** Round-robin across multiple API keys
- **Rate Limiting:** 90 RPM per key
- **Retry:** Exponential backoff (3 attempts)
- **Storage:** Direct to Qdrant via batch upload

#### 1.2.6 Qdrant Vector Database
- **Version:** Latest (Docker)
- **Storage:** Named volumes (`qdrant_storage:`)
- **Collection:** `multilingual_docs`
- **Distance:** Cosine similarity
- **Indexing:** HNSW (Hierarchical Navigable Small World)
- **Threshold:** 50 vectors (optimized for small collections)
- **Payload:** Full metadata + text
- **Index Fields:** language, doc_id, page_num

#### 1.2.7 Retriever Agent (Hybrid)
- **Dense Search:**
  - Query → Gemini embedding → Qdrant cosine search
  - Top-K: 10 results
  - Min score: 0.0
- **Sparse Search (BM25):**
  - Query → Tokenize → BM25 scoring
  - Index: In-memory (built on first query)
  - Top-K: 10 results
- **Fusion:**
  - Method: Weighted sum (configurable)
  - Dense weight: 0.6
  - Keyword weight: 0.4
  - Alternative: Reciprocal Rank Fusion (RRF)

#### 1.2.8 Reranker Agent
- **Primary:** Gemini Flash (`gemini-flash-latest`)
- **Method:** Pairwise relevance scoring
- **Input:** Top-30 retrieved results
- **Output:** Top-5 reranked results
- **Fallback:** CPU-based local reranker (optional)
- **Prompt:** "Score relevance of passage to query (0-1 scale)"

#### 1.2.9 Query Decomposition Agent
- **LLM:** Ollama (gemma3:4b)
- **Trigger:** Complex queries (>= 2 clauses, AND/OR operators)
- **Strategy:** Break into independent sub-queries
- **Retrieval:** Parallel retrieval for each sub-query
- **Fusion:** Deduplicate + merge by score
- **Max Sub-Queries:** 5

#### 1.2.10 RAG Agent (Orchestrator)
- **Pipeline:**
  1. Metadata filtering (language, date, type)
  2. Query decomposition (if complex)
  3. Retrieval (hybrid)
  4. Reranking (Gemini)
  5. Context assembly (top-K chunks + metadata)
  6. Prompt construction (system + context + history + query)
  7. LLM generation (Ollama streaming)
- **Memory:** SQLite session storage
- **Streaming:** Server-Sent Events (SSE) via async generator

#### 1.2.11 Metadata Filter Agent
- **Language Detection:** Keywords + Unicode ranges
- **Filters:** language, date_range, doc_type
- **Extraction:** LLM-based entity recognition (optional)

---

## 2. Data Flow & Processing Pipeline

### 2.1 Document Ingestion Flow

```
1. PDF Upload (NiceGUI UI or file drop)
   ↓
2. Save to data/incoming/<lang>/
   ↓
3. Ingestion Agent scans directory
   ↓
4. Create job in SQLite (status: pending)
   ↓
5. Move to data/processing/<doc_id>.pdf
   ↓
6. PDF Type Detector analyzes pages
   ↓
7. OCR Agent processes:
   - Scanned pages: pdf2image → Tesseract
   - Digital pages: PyMuPDF extraction
   ↓
8. Save raw text: data/ocr_raw/<doc_id>_raw.txt
   ↓
9. Chunking Agent splits text:
   - Recursive splitter (450-550 tokens)
   - Add metadata (page, language, doc_id)
   ↓
10. Save chunks: data/chunks/<doc_id>.json
    ↓
11. Embedding Agent:
    - Batch API calls to Gemini
    - Generate 768-dim vectors
    ↓
12. Upload to Qdrant:
    - Batch insert (100 chunks/batch)
    - Create payload with metadata
    ↓
13. Update job status: completed
    ↓
14. Move to data/processed/<doc_id>.pdf
```

**Performance:** ~2 minutes for 10-page PDF (with OCR)

### 2.2 Query Processing Flow

```
1. User query (NiceGUI chat or API)
   ↓
2. Metadata Filter Agent extracts filters
   ↓
3. Query Decomposition (if complex)
   ↓
4. For each sub-query:
   a. Dense search (Gemini embedding → Qdrant)
   b. Sparse search (BM25 index)
   c. Fusion (weighted sum)
   ↓
5. Deduplicate and merge results
   ↓
6. Reranker Agent (Gemini Flash)
   ↓
7. Top-K selection (default: 5)
   ↓
8. Context assembly:
   - Chunk text + metadata
   - Page numbers + source docs
   ↓
9. Prompt construction:
   - System prompt (instructions)
   - Context (retrieved chunks)
   - Chat history (last N messages)
   - Current query
   ↓
10. LLM generation (Ollama streaming)
    ↓
11. Parse citations and sources
    ↓
12. Stream response to UI (SSE)
    ↓
13. Save to chat history (SQLite)
```

**Performance:** 5-10 seconds end-to-end

---

## 3. Configuration & Deployment

### 3.1 Environment Variables

```env
# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=multilingual_docs

# Embeddings
EMBEDDING_MODEL=models/text-embedding-004
GEMINI_API_KEYS=key1,key2,key3  # Comma-separated

# LLMs
LLM_PRIMARY=ollama:gemma3:4b
LLM_FALLBACK=gemini-flash-latest
OLLAMA_HOST=http://localhost:11434

# Retrieval
ENABLE_BM25=true
FUSION_METHOD=weighted  # or 'rrf'
DENSE_WEIGHT=0.6
KEYWORD_WEIGHT=0.4

# Reranking
ENABLE_RERANK=true
RERANK_BACKEND=gemini  # or 'local_cpu'
RERANK_TOP_K=30

# Query Decomposition
ENABLE_DECOMPOSITION=true

# OCR
OCR_ENGINE=tesseract
OCR_LANGS=eng,chi_sim,hin,ben,urd
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# System
ENABLE_GPU=false  # CPU-first by default
```

### 3.2 Docker Deployment

```yaml
# docker-compose.yml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage  # Named volume (critical!)
    ulimits:
      nofile: {soft: 10000, hard: 10000}

volumes:
  qdrant_storage:  # Docker-managed, POSIX-compliant
```

**Why Named Volumes:** Qdrant requires POSIX-compliant block-level storage. Bind mounts (`./qdrant_storage`) can cause `OutputTooSmall` errors on non-POSIX filesystems.

### 3.3 API Endpoints

#### NiceGUI Web UI:
- **URL:** `http://127.0.0.1:8080`
- **Tabs:** Upload, Chat, Documents, Logs, Config

#### Qdrant REST API:
- **Health:** `GET http://localhost:6333/healthz`
- **Collections:** `GET http://localhost:6333/collections`
- **Search:** `POST http://localhost:6333/collections/{name}/points/search`

#### Ollama API:
- **Models:** `GET http://localhost:11434/api/tags`
- **Generate:** `POST http://localhost:11434/api/generate`

### 3.4 Database Schema

#### SQLite Tables:

**1. ingestion_jobs**
```sql
CREATE TABLE ingestion_jobs (
    job_id TEXT PRIMARY KEY,
    doc_id TEXT,
    file_path TEXT,
    language TEXT,
    status TEXT,  -- pending, processing, completed, failed
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);
```

**2. chat_sessions**
```sql
CREATE TABLE chat_sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    last_activity TIMESTAMP
);
```

**3. chat_messages**
```sql
CREATE TABLE chat_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,  -- user, assistant
    content TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);
```

### 3.5 Performance Tuning

#### Qdrant:
- **HNSW Parameters:**
  - `m`: 16 (connections per node)
  - `ef_construct`: 100 (index build quality)
- **Indexing Threshold:** 50 (start indexing after 50 vectors)
- **On-Disk Storage:** Enabled (memory-efficient)

#### BM25:
- **k1:** 1.5 (term frequency saturation)
- **b:** 0.75 (length normalization)
- **Tokenization:** Language-aware (whitespace + punctuation)

#### Ollama:
- **Context Window:** 8192 tokens
- **Temperature:** 0.7
- **Top-P:** 0.9
- **Streaming:** Enabled

---

## 4. Troubleshooting & Known Issues

### 4.1 Resolved Issues

#### Issue: Qdrant OutputTooSmall Error
- **Symptom:** Panic during vector search
- **Cause:** Bind mount to non-POSIX filesystem (FUSE)
- **Fix:** Use Docker named volumes
- **Status:** ✅ Fixed

#### Issue: NiceGUI Upload Error
- **Symptom:** `UploadEventArguments has no 'files' attribute`
- **Cause:** Incorrect event attribute access
- **Fix:** Use `e.content` and `e.name` instead of `e.files`
- **Status:** ✅ Fixed

### 4.2 Limitations

1. **OCR Quality:** Bengali/Urdu OCR may have accuracy issues with complex scripts
2. **Context Length:** Max 8192 tokens for Ollama (long docs may be truncated)
3. **Embedding Speed:** ~0.02 sec/chunk (limited by Gemini API rate)
4. **Reranking Latency:** Adds 2-3 seconds per query (Gemini API call)

### 4.3 Monitoring

- **Logs:** `logs/app.log` (Rich console + file logging)
- **Metrics:** Query latency, retrieval scores, embedding time
- **Qdrant:** Built-in metrics at `http://localhost:6333/metrics`

---

**End of Technical Documentation**

