# 🚀 Quick Start Guide - Multilingual Agentic RAG

## ✅ System Status: RUNNING

**🎉 Your application is now live and running!**

### Access the Web Interface

**URL:** http://localhost:8080

Open your browser and navigate to the URL above to access the dark-mode UI.

---

## 📊 Current System Status

| Component | Status | Details |
|-----------|--------|---------|
| **Web UI** | ✅ Running | Port 8080 |
| **Qdrant Vector DB** | ✅ Running | Port 6333 |
| **Tesseract OCR** | ✅ Installed | Version 5.5.0 |
| **Ollama LLM** | ✅ Running | deepseek-r1:1.5b model ready |
| **Gemini API** | ✅ Configured | 2 API keys for rotation |
| **PDFs Ready** | ✅ 16 files | In incoming directories |

---

## 🎯 Features Available

### 1. 📤 Upload Tab
- **Upload PDFs** in multiple languages
- **Select language** before upload (Bengali, Chinese, Hindi, Urdu, English)
- **Automatic processing** starts immediately
- **Scan existing files** button to process files already in folders

### 2. 💬 Chat Tab
- **Ask questions** about your uploaded documents
- **Real-time streaming** responses
- **Chat history** persisted in SQLite
- **Multi-document** synthesis
- **Source citations** with page numbers

### 3. 📚 Documents Tab
- **Browse** indexed documents
- **View metadata** (coming soon - currently in UI)

### 4. 📋 Logs Tab
- **Real-time logs** from all agents
- **Auto-refresh** every 2 seconds
- **Color-coded** by level (INFO, WARNING, ERROR, SUCCESS)

### 5. ⚙️ Config Tab
- **View system configuration**
- **Check API key status**
- **See enabled features**

---

## 📂 PDFs Ready for Processing

Your system has **16 PDFs** ready to be processed:

- **Bengali (bn)**: 6 documents
- **Urdu (ur)**: 7 documents
- **Chinese (zh)**: 3 documents

These files are in `data/incoming/<language>/` and will be automatically:
1. Detected by the ingestion agent
2. Classified (scanned vs digital pages)
3. OCR processed (Tesseract)
4. Cleaned (DeepSeek-R1/Gemini LLM)
5. Chunked (CJK-aware, 450-550 tokens)
6. Embedded (Gemini embedding-001)
7. Stored in Qdrant vector database

**Processing happens automatically in the background!**

---

## 🧪 Testing the System

### Test 1: Check Web UI
1. Open http://localhost:8080 in your browser
2. You should see the dark-mode interface with 5 tabs
3. Check the **Logs** tab to see background processing activity

### Test 2: Wait for Document Processing
The system is now processing your 16 PDFs. This may take time depending on:
- PDF size and complexity
- Whether pages are scanned (OCR required) or digital
- API rate limits

**Monitor progress in the Logs tab!**

### Test 3: Upload a New Document
1. Go to the **Upload** tab
2. Select a language (e.g., "en" for English)
3. Click "Select PDF Files" and upload a test PDF
4. Watch the **Logs** tab for processing updates

### Test 4: Chat with Documents
Once documents are processed:
1. Go to the **Chat** tab
2. Type a question like:
   - "What are the main topics in the Bengali documents?"
   - "Summarize the Urdu documents"
   - "What information is in the Chinese PDFs?"
3. Press Send or hit Enter
4. Watch the streaming response appear!

---

## 🔧 Advanced Features Active

### Hybrid Retrieval
- **Dense Search**: Gemini embeddings with cosine similarity
- **Sparse Search**: BM25 keyword matching
- **Fusion**: Weighted combination (60% dense, 40% keyword)

### Query Enhancement
- **Decomposition**: Complex queries split into sub-queries
- **Metadata Filters**: Automatic detection of language/page filters
- **Reranking**: Gemini Flash scores results for relevance

### LLM Intelligence
- **Primary**: Ollama deepseek-r1:1.5b (local, fast)
- **Fallback**: Gemini Flash (when Ollama unavailable)
- **Text Cleanup**: LLM normalizes OCR errors
- **Streaming**: Real-time response generation

---

## 📈 Monitoring

### Check Background Processing
Watch the Logs tab to see:
- Files being scanned
- OCR progress
- LLM cleanup operations
- Chunking and embedding
- Vector storage updates

### Check Qdrant Collections
```powershell
# In a new terminal
curl http://localhost:6333/collections
```

### Check Processing Queue
The system maintains a job queue in SQLite (`data/app.db`). Jobs move through states:
- **PENDING** → **PROCESSING** → **COMPLETED** or **FAILED**

---

## 💡 Tips for Best Results

### For Queries:
- Be specific about what you're looking for
- Mention language if relevant ("in the Bengali documents...")
- Ask for citations ("with page numbers")
- Try follow-up questions for deeper insight

### For Uploads:
- Select the correct language before upload
- One language per upload batch
- Supported: English, Chinese, Hindi, Bengali, Urdu
- Both scanned and digital PDFs work

### For Performance:
- First query may be slow (building BM25 index)
- Subsequent queries are faster
- Streaming provides faster perceived response
- Multiple API keys improve rate limits

---

## 🐛 Troubleshooting

### If Web UI doesn't load:
```powershell
# Check if app is running
curl http://localhost:8080

# Restart if needed
# Ctrl+C in the terminal running the app
.venv\Scripts\python.exe -m src.main
```

### If Qdrant connection fails:
```powershell
# Check Qdrant status
docker ps | findstr qdrant

# Restart if needed
docker-compose --profile cpu restart
```

### If OCR fails:
- Verify Tesseract is installed
- Check language packs are installed
- Digital PDFs will still work (no OCR needed)

### If Ollama fails:
- System automatically falls back to Gemini Flash
- No action needed, but local LLM won't be used

---

## 📝 Next Steps

1. **Monitor the Logs tab** to see your 16 PDFs being processed
2. **Wait for processing to complete** (progress shown in logs)
3. **Try your first chat query** once documents are indexed
4. **Upload additional documents** via the Upload tab
5. **Explore advanced features** like metadata filtering

---

## 🎓 Example Queries to Try

Once your documents are indexed:

```
"What are the main topics discussed in the Bengali documents?"

"Summarize the key points from the Urdu PDFs"

"Find information about [your topic] in the Chinese documents"

"List all documents and their main subjects"

"What is mentioned on page 5 of document X?"

"Compare the themes across all languages"
```

---

## 📞 Support

If you encounter issues:
1. Check the **Logs** tab for error messages
2. Verify all components are running (see status table above)
3. Check `logs/app.log` for detailed debugging info
4. Review `TEST_RESULTS.md` for verification steps

---

## 🎉 You're All Set!

Your multilingual agentic RAG system is fully operational and processing documents in the background. 

**Open http://localhost:8080 and start exploring!**

---

*Generated: Your system is running and ready to use!*
