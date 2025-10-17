# 🌍 Multilingual Agentic RAG System

A **production-ready** multilingual document Question-Answering system using Retrieval-Augmented Generation (RAG) with specialized agents for intelligent document processing and querying.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Passing](https://img.shields.io/badge/tests-5%2F5%20passing-brightgreen.svg)](tests/)

## 🎯 Key Features

- **🌐 Multilingual Support**: Process documents in English, Chinese, Hindi, Bengali, and Urdu
- **🤖 Agentic Architecture**: 11 specialized agents for end-to-end document intelligence
- **🔍 Hybrid Retrieval**: Combines semantic search (Gemini embeddings) + BM25 keyword matching
- **📊 Advanced Reranking**: Gemini Flash-based relevance scoring
- **💬 Chat Memory**: Multi-turn conversations with context retention
- **🧠 Query Decomposition**: Breaks complex queries into manageable sub-queries
- **⚡ Production-Ready**: Docker containerization, comprehensive logging, error handling
- **🎨 Modern UI**: Dark-mode NiceGUI interface with real-time streaming responses

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Document Processing Pipeline                │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   PDF    │────▶│   OCR    │────▶│ Chunking │────▶│Embedding │
│  Upload  │     │(Tesseract│     │(Lang-Aware)    │ (Gemini) │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                            │
                                                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Qdrant Vector Database                     │
│                  (106+ documents, 96+ indexed)                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Query   │────▶│ Retrieval│────▶│ Reranker │────▶│   LLM    │
│          │     │ (Hybrid) │     │ (Gemini) │     │ (Ollama) │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────┐
                                                   │   Answer +   │
                                                   │ Chat Memory  │
                                                   └──────────────┘
```

## 📦 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **LLM** | Ollama (Gemma3:4b) | Local inference, answer generation |
| **Fallback LLM** | Gemini Flash | Cloud backup for complex queries |
| **Embeddings** | Gemini text-embedding-004 | 768-dimensional multilingual vectors |
| **Vector DB** | Qdrant (Docker) | Efficient similarity search |
| **OCR** | Tesseract 5.0+ | Multilingual text extraction |
| **Frontend** | NiceGUI | Real-time web interface |
| **Storage** | SQLite | Chat history & job queue |
| **Containerization** | Docker Compose | Service orchestration |

## 🚀 Quick Start

### Prerequisites
- **Windows 10/11** or **Linux**
- **Python 3.11+**
- **Docker Desktop** (for Qdrant)
- **Ollama** (for local LLM)
- **Tesseract OCR** with language packs

### 1. Install Dependencies

#### Windows:
```powershell
# Install Python
winget install Python.Python.3.11

# Install Docker Desktop
winget install Docker.DockerDesktop

# Install Ollama
winget install Ollama.Ollama

# Install Tesseract
winget install UB-Mannheim.TesseractOCR
```

#### Linux:
```bash
# Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ollama
curl https://ollama.ai/install.sh | sh

# Tesseract
sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim \
                 tesseract-ocr-hin tesseract-ocr-ben tesseract-ocr-urd
```

### 2. Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/multilingual-rag.git
cd multilingual-rag

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API keys
nano .env  # or notepad .env on Windows
```

### 3. Configure API Keys

Edit `.env` and add your Google Gemini API keys:

```env
GEMINI_API_KEYS=your-key-1,your-key-2,your-key-3
```

Get API keys from: https://makersuite.google.com/app/apikey

### 4. Start Services

```bash
# Start Qdrant vector database
docker-compose --profile cpu up -d

# Pull Ollama model
ollama pull gemma3:4b

# Verify services
curl http://localhost:6333/healthz  # Qdrant
curl http://localhost:11434/api/tags  # Ollama
```

### 5. Process Documents

```bash
# Clean and reindex (first time)
python tests/clean_and_reindex.py

# Process sample document
python scripts/process_one_sample.py

# Process all documents
python -m src.main
```

### 6. Start Web UI

```bash
# Launch NiceGUI interface
python -m src.main

# Open browser to http://127.0.0.1:8080
```

## 📚 Example Queries

### Bengali (বাংলা):
```
গবেষণা নির্দেশিকায় কী কী বিষয় আছে?
(What topics are covered in the research guidelines?)
```

### Urdu (اردو):
```
عارضی ملازمین کی ملازمت کی مدت کب تک بڑھائی گئی ہے؟
(Until when has the employment period of adhoc employees been extended?)
```

### Chinese (中文):
```
这个文件是关于什么的？
(What is this document about?)
```

### English:
```
What types of administrative documents are available?
Compare research guidelines and employment procedures.
```

## 🧪 Testing

```bash
# Run quick tests (5 core features)
python tests/test_rag_quick.py

# Expected output:
# ✅ PASS - Query Decomposition
# ✅ PASS - Document Retrieval
# ✅ PASS - Reranking
# ✅ PASS - Single-Turn Chat
# ✅ PASS - Chat Memory
# Passed: 5/5 (100.0%)

# Run comprehensive tests with proof
python scripts/run_comprehensive_tests.py
# Generates docs/RAG_TEST_PROOF.json
```

## 📊 Performance Benchmarks

| Metric | Value | Details |
|--------|-------|---------|
| **Documents Indexed** | 106+ | Bengali (6), Urdu (7), Chinese (3) |
| **Vectors Indexed** | 96+ | 90%+ indexing rate |
| **Retrieval Speed** | < 1 sec | Hybrid search (semantic + BM25) |
| **Embedding Speed** | ~0.02 sec/chunk | Gemini API with batching |
| **Answer Generation** | 5-10 sec | Streaming with Ollama |
| **Test Pass Rate** | 100% | 5/5 tests passing |

## 🎯 Use Cases

### 1. Government Document Search
- Process multilingual policy documents
- Extract specific regulations, dates, amounts
- Compare procedures across departments

### 2. Research & Academia
- Analyze research guidelines in local languages
- Find funding limits and application procedures
- Cross-reference multiple guideline documents

### 3. Administrative Queries
- Employment extensions and notifications
- Budget allocation information
- Organizational hierarchies

### 4. Multilingual Knowledge Base
- Unified search across language barriers
- Semantic understanding of queries
- Context-aware answers with citations

## 📖 Documentation

- **[Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md)** - Architecture, components, API docs
- **[User Guide](docs/USER_GUIDE.md)** - Operating and maintaining the system
- **[Performance Report](docs/PERFORMANCE_EVALUATION.md)** - Benchmarks and test results
- **[Presentation](docs/INTERVIEW_PRESENTATION.md)** - Project overview for interviews
- **[Test Questions](docs/TEST_QUESTIONS.md)** - Comprehensive test scenarios
- **[Qdrant Fix Guide](docs/QDRANT_FIX_SUMMARY.md)** - Filesystem issue resolution

## 🔧 Configuration

Key configuration options in `.env`:

```env
# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=multilingual_docs

# Embeddings
EMBEDDING_MODEL=models/text-embedding-004
GEMINI_API_KEYS=key1,key2,key3

# LLMs
LLM_PRIMARY=ollama:gemma3:4b
LLM_FALLBACK=gemini-flash-latest
OLLAMA_HOST=http://localhost:11434

# Retrieval
ENABLE_BM25=true
DENSE_WEIGHT=0.6
KEYWORD_WEIGHT=0.4

# Reranking
ENABLE_RERANK=true
RERANK_TOP_K=30

# OCR
OCR_ENGINE=tesseract
OCR_LANGS=eng,chi_sim,hin,ben,urd
```

## 🐛 Troubleshooting

### Common Issues

**1. Qdrant OutputTooSmall Error**
- **Solution**: Ensure using Docker named volumes (not bind mounts)
- See: [Qdrant Fix Guide](docs/QDRANT_FIX_SUMMARY.md)

**2. Embedding API Errors**
- **Check**: API keys in `.env`
- **Verify**: Model name is `models/text-embedding-004`

**3. Ollama Connection Failed**
- **Start**: `ollama serve`
- **Pull model**: `ollama pull gemma3:4b`

**4. Tesseract Language Packs Missing**
- **Windows**: Install from UB-Mannheim installer
- **Linux**: `sudo apt install tesseract-ocr-[lang]`

**5. Upload Not Working**
- **Fixed**: NiceGUI event handler updated
- **Check**: PDF files only, max 50MB

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini**: For powerful multilingual embeddings
- **Ollama**: For easy local LLM deployment
- **Qdrant**: For efficient vector search
- **Tesseract**: For OCR capabilities
- **NiceGUI**: For beautiful Python UI

## 📧 Contact

- **GitHub**: [@yourusername](https://github.com/yourusername)
- **Email**: your.email@example.com
- **LinkedIn**: [Your Name](https://linkedin.com/in/yourprofile)

## 🌟 Star History

If you find this project useful, please consider giving it a star ⭐

---

**Built with ❤️ for multilingual document intelligence**
