# Multilingual Agentic RAG (venv, Qdrant, NiceGUI, Gemini-001)

## Final Decisions (enforced)

- venv only; Windows-first; no WSL
- Embeddings strictly Google `gemini-embedding-001` (no local embeddings)
- OCR strictly Tesseract + language packs; LLM cleanup is mandatory
- Main LLM: Ollama `deepseek-r1:1.5b` (CPU-first); Fallback: `gemini-flash-latest`
- Hybrid retrieval: semantic (Gemini-001) + keyword (BM25) + Gemini rerank
- GPU: off by default everywhere; Windows may enable GPU; Linux defaults CPU unless env overrides
- NiceGUI dark-mode UI for uploads, chat, logs, flags, metrics
- Gemini key rotation with multiple keys in one env var
- Vector DB: Qdrant (Docker), on-disk storage, payload indexes, metadata filters

## Architecture & Pipeline (Agentic)

1. Ingestion Agent: watches `data/incoming/<lang>/` (en, zh, hi, bn, ur,...); queues jobs to SQLite; moves to `data/processing/`.
2. PDF Type Detector: per-page PyMuPDF sniff; classify page as scanned or digital.
3. OCR Agent (Tesseract-only): scanned pages via `pdf2image` → Tesseract (`--oem 1 --psm 6`, lang from folder, e.g., `eng`, `chi_sim`, `hin`, `ben`); digital pages via PyMuPDF.
4. LLM Cleanup Agent (mandatory): DeepSeek-R1 normalizes OCR text (spacing/diacritics), preserves page markers; fallback to Gemini Flash if Ollama fails.
5. Chunking Agent: language-aware recursive splitter (CJK-aware), 450–550 tokens, 50–80 overlap; keep structure; add metadata (doc_id, page, lang, section).
6. Embedding Agent: batch call `gemini-embedding-001` with key rotation; persist vectors + payloads to Qdrant.
7. Retriever Agent (Hybrid): dense cosine (Qdrant) + BM25 (`rank-bm25`); fuse (weighted sum or RRF); prefilter by metadata.
8. Reranker Agent: Gemini Flash scoring for top-K passages; CPU-only local rerank fallback (very small K) for offline.
9. Decomposer Agent: DeepSeek-R1 decomposes query into sub-queries; retrieve+merge results.
10. RAG Agent (Chat): chat memory (SQLite) + prompt assembly; generation via DeepSeek-R1 with streaming; fallback to Gemini.
11. Evaluation Agent: RAGAS retrieval metrics; latency; fluency via Gemini Flash; save `reports/` JSON + HTML.

## Files & Layout

```
project-root/
├── .env.example
├── docker-compose.yml                 # Qdrant + app (CPU profile); optional GPU profile flags only
├── Dockerfile                         # App image (CPU default)
├── venv_setup.ps1                     # Windows PowerShell venv bootstrap
├── venv_setup.sh                      # Linux/Mac venv bootstrap
├── src/
│   ├── main.py                        # Orchestrator
│   ├── api/server.py                  # (optional) REST hooks if needed
│   ├── frontend/nicegui_app.py        # Dark-mode UI: upload, docs, chat, logs, flags
│   ├── agents/
│   │   ├── ingestion_agent.py
│   │   ├── pdf_type_detector.py
│   │   ├── ocr_agent.py               # Tesseract only
│   │   ├── cleanup_agent.py           # LLM cleanup mandatory
│   │   ├── chunking_agent.py
│   │   ├── embedding_agent.py         # gemini-embedding-001 + key rotation
│   │   ├── retriever_agent.py         # dense + BM25 fusion
│   │   ├── reranker_agent.py          # Gemini rerank; CPU fallback
│   │   ├── decomposition_agent.py
│   │   ├── rag_agent.py
│   │   ├── metadata_filter_agent.py
│   │   └── evaluation_agent.py
│   ├── common/
│   │   ├── config.py                  # flags, API keys (rotation), paths, GPU toggles
│   │   ├── logging.py                 # rich logs + UI bridge
│   │   ├── storage.py                 # SQLite for jobs & chat memory
│   │   └── utils.py                   # pdf helpers, text utils
│   └── cli.py                         # batch ingestion & eval
├── data/{incoming/<lang>,processing,ocr_raw,ocr_clean,chunks,embeddings}
├── reports/
├── tests/{unit,integration}
├── requirements.txt
└── README.md
```

## .env keys & flags (Windows/Linux)

- Core: `VECTOR_DB=qdrant`, `QDRANT_URL=http://localhost:6333`, `QDRANT_API_KEY` (optional)
- Embeddings: `EMBEDDING_MODEL=gemini-embedding-001`, `GEMINI_API_KEYS=key1,key2,key3` (comma-separated)
- LLMs: `LLM_PRIMARY=ollama:deepseek-r1:1.5b`, `LLM_FALLBACK=gemini-1.5-flash-latest`, `OLLAMA_HOST=http://localhost:11434`
- Retrieval: `ENABLE_BM25=true`, `FUSION_METHOD=weighted`, `DENSE_WEIGHT=0.6`, `KEYWORD_WEIGHT=0.4`
- Rerank: `ENABLE_RERANK=true`, `RERANK_BACKEND=gemini|local_cpu`, `RERANK_TOP_K=30`
- Decomposition: `ENABLE_DECOMPOSITION=true`
- Filters: `ENABLE_METADATA_FILTER=true`
- Eval: `ENABLE_EVAL=true`, `EVAL_MODEL=gemini-1.5-flash-latest`
- OCR: `OCR_ENGINE=tesseract`, `OCR_LANGS=eng,chi_sim,hin,ben`, `TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe`
- System: `ENABLE_GPU=false`, `USE_DOCKER_GPU=false`, `GPU_PLATFORM=windows|linux`
- Rate limiting: `KEY_ROTATION_STRATEGY=round_robin_backoff`, `RATE_LIMIT_RPM=90`

Setup notes:

- Windows GPU: set `ENABLE_GPU=true`, `GPU_PLATFORM=windows`. Linux stays CPU unless you set `ENABLE_GPU=true` and your container/host has CUDA; we won’t use WSL.

## DigitalOcean sizing (CPU-only online)

- Small dev: 4 vCPU / 16 GB RAM, 200–300 GB SSD
- Staging: 8 vCPU / 32 GB RAM, 1 TB SSD (Volume)
- Larger: 16 vCPU / 64 GB RAM, 2–4 TB SSD; move to Qdrant cluster on Azure when needed

## Demonstrability

- Meets assignment: multilingual PDFs, Tesseract OCR, LLM cleanup, hybrid retrieval+semantic, Gemini rerank, metadata filters, chat memory, query decomposition, NiceGUI frontend, Gemini-based eval.

## Risks & Mitigations

- Gemini rate limits → key rotation + retry/backoff
- VRAM 4GB → default to CPU; Gemini rerank avoids local GPU
- Large PDFs → page batching; ingestion queue backpressure

## Implementation Todos

- setup-venv: Create venv scripts and lock dependencies
- docker-qdrant: Docker Compose for Qdrant + volumes (CPU profile)
- config-keys: Env flags, GPU toggles, Gemini key rotation
- pdf-detect: Digital vs scanned page detection
- ocr-tesseract: Tesseract-only OCR agent (language-aware)
- llm-cleanup: Mandatory cleanup agent via Ollama; Gemini fallback
- chunking: Language-aware chunker (CJK-aware)
- embeddings-gemini: Gemini-001 embeddings + Qdrant ingestion
- retriever-hybrid: Dense+BM25 fusion with metadata filters
- rerank-gemini: Gemini Flash reranker; CPU fallback
- decompose-agent: Query decomposition with DeepSeek-R1
- rag-chat: RAG agent with memory and prompts
- nicegui-ui: Dark UI: upload, docs view, chat, logs, flags
- evaluation: RAGAS + Gemini fluency + latency metrics
- docs-setup: README + Windows/Linux setup (GPU flags, DO notes)