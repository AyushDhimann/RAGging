# User Guide
## Operating and Maintaining the Multilingual RAG System

**Version:** 1.0  
**Last Updated:** October 2025  
**Audience:** System Operators, Administrators

---

## Table of Contents
1. [Getting Started](#1-getting-started)
2. [Daily Operations](#2-daily-operations)
3. [System Maintenance](#3-system-maintenance)
4. [Troubleshooting](#4-troubleshooting)
5. [Best Practices](#5-best-practices)

---

## 1. Getting Started

### 1.1 System Requirements

#### Minimum Hardware:
- **CPU:** 4 cores (Intel i5/AMD Ryzen 5 or better)
- **RAM:** 16 GB
- **Storage:** 100 GB SSD
- **Network:** Stable internet (for Gemini API calls)

#### Recommended Hardware:
- **CPU:** 8 cores (Intel i7/AMD Ryzen 7)
- **RAM:** 32 GB
- **Storage:** 250 GB NVMe SSD
- **GPU:** Optional (for future local embeddings)

#### Software:
- **OS:** Windows 10/11 or Ubuntu 20.04+
- **Python:** 3.11+
- **Docker:** Latest Desktop version
- **Ollama:** Latest release
- **Tesseract:** 5.0+ with language packs

### 1.2 Initial Setup

#### Step 1: Install Dependencies
```powershell
# Windows (PowerShell as Administrator)
winget install Python.Python.3.11
winget install Docker.DockerDesktop
winget install Ollama.Ollama
winget install UB-Mannheim.TesseractOCR
```

#### Step 2: Clone & Configure
```bash
git clone <repository-url>
cd multilingual-rag
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux

pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Gemini API keys
```

#### Step 3: Start Services
```powershell
# Start Qdrant
docker-compose --profile cpu up -d

# Pull Ollama model
ollama pull gemma3:4b

# Verify services
curl http://localhost:6333/healthz  # Qdrant
curl http://localhost:11434/api/tags  # Ollama
```

#### Step 4: Initialize Database
```powershell
# Clean and create fresh database
python tests/clean_and_reindex.py

# Process sample document (optional)
python scripts/process_one_sample.py
```

---

## 2. Daily Operations

### 2.1 Starting the System

#### Option A: Web UI (Recommended for Users)
```powershell
# Ensure services are running
docker ps  # Check Qdrant
ollama list  # Check models

# Start web interface
python -m src.main

# Access: http://127.0.0.1:8080
```

#### Option B: CLI (For Batch Processing)
```powershell
# Process specific document
python -m src.cli process <pdf-path> --language bn

# Process directory
python -m src.cli batch data/incoming/ur/

# Query from command line
python -m src.cli query "What are the requirements?"
```

### 2.2 Using the Web UI

#### Upload Tab:
1. Select language from dropdown (en, zh, hi, bn, ur)
2. Click "Select PDF Files" or drag-and-drop
3. System automatically processes and indexes
4. Check "Processing Queue" for status

#### Chat Tab:
1. Type query in text input
2. Press "Send" or hit Enter
3. Response streams in real-time
4. Sources cited at bottom of answer
5. Use "Clear" to start new session

#### Documents Tab:
1. View indexed document list
2. Filter by language
3. See processing status
4. Delete documents if needed

#### Logs Tab:
1. Real-time system logs
2. Auto-refreshes every 2 seconds
3. Shows errors, warnings, info
4. Use for debugging

#### Config Tab:
1. View current settings
2. LLM, embedding, retrieval configs
3. Cannot edit (use .env file)

### 2.3 Common Tasks

#### Task 1: Upload New Documents
```
1. Navigate to "Upload" tab
2. Select language (e.g., "bn" for Bengali)
3. Click "Select PDF Files"
4. Choose one or more PDFs (max 50MB each)
5. Wait for "Uploaded X.pdf" notification
6. Check "Documents" tab for processing status
7. Document ready for queries when status = "completed"
```

#### Task 2: Query Documents
```
1. Navigate to "Chat" tab
2. Type query in any supported language
3. Examples:
   - "গবেষণা নির্দেশিকায় কী কী বিষয় আছে?" (Bengali)
   - "عارضی ملازمین کی ملازمت کی مدت کب تک بڑھائی گئی ہے؟" (Urdu)
   - "What administrative documents are available?"
4. Review answer and sources
5. Ask follow-up questions (memory enabled)
```

#### Task 3: Monitor System Health
```powershell
# Check Qdrant
Invoke-RestMethod -Uri 'http://localhost:6333/collections/multilingual_docs' | 
  Select-Object -ExpandProperty result | 
  Select-Object status, points_count, indexed_vectors_count

# Check Ollama
ollama ps  # Running models
ollama list  # Available models

# Check logs
Get-Content logs\app.log -Tail 50

# Or use web UI "Logs" tab
```

---

## 3. System Maintenance

### 3.1 Daily Maintenance

#### Checklist:
- [ ] **Verify Qdrant is running:** `docker ps`
- [ ] **Check disk space:** Minimum 10 GB free
- [ ] **Review error logs:** `logs/app.log`
- [ ] **Monitor API quota:** Gemini API usage
- [ ] **Backup database:** Copy `app.db` and Qdrant volume

#### Daily Backup Script:
```powershell
# backup.ps1
$date = Get-Date -Format "yyyyMMdd"
$backupDir = "backups\$date"

# Create backup directory
New-Item -ItemType Directory -Force -Path $backupDir

# Backup SQLite database
Copy-Item app.db "$backupDir\app.db"

# Backup Qdrant (export collection)
Invoke-RestMethod -Method Post -Uri 'http://localhost:6333/collections/multilingual_docs/snapshots' -OutFile "$backupDir\qdrant_snapshot.snapshot"

Write-Host "Backup completed: $backupDir"
```

### 3.2 Weekly Maintenance

#### Tasks:
1. **Update Dependencies:**
   ```powershell
   pip list --outdated
   pip install --upgrade <package-name>
   ```

2. **Clean Up Processed Files:**
   ```powershell
   # Delete old processed PDFs (>30 days)
   Get-ChildItem data\processed -Recurse -File | 
     Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
     Remove-Item
   ```

3. **Optimize Qdrant:**
   ```powershell
   # Trigger collection optimization
   Invoke-RestMethod -Method Post -Uri 'http://localhost:6333/collections/multilingual_docs/optimizer'
   ```

4. **Review API Usage:**
   - Check Gemini API quota: https://makersuite.google.com/app/quotas
   - Monitor API costs
   - Rotate API keys if needed

### 3.3 Monthly Maintenance

#### Tasks:
1. **Full System Backup:**
   - Export entire Qdrant collection
   - Backup all data directories
   - Save `.env` configuration (securely)

2. **Performance Analysis:**
   - Review query response times
   - Check retrieval accuracy (spot checks)
   - Analyze error rates

3. **Update System:**
   - Pull latest Docker images: `docker-compose pull`
   - Update Ollama models: `ollama pull gemma3:4b`
   - Update Tesseract language packs

4. **Database Maintenance:**
   - Vacuum SQLite: `python -c "import sqlite3; conn = sqlite3.connect('app.db'); conn.execute('VACUUM'); conn.close()"`
   - Reindex if needed: `python tests/clean_and_reindex.py` (only if issues)

---

## 4. Troubleshooting

### 4.1 Common Issues

#### Issue 1: Qdrant Not Starting
**Symptoms:** "Connection refused" error, web UI can't connect

**Diagnosis:**
```powershell
docker ps  # Check if qdrant_multilingual is running
docker logs qdrant_multilingual  # Check container logs
```

**Solutions:**
```powershell
# Restart Qdrant
docker-compose restart

# If still failing, recreate
docker-compose down
docker-compose --profile cpu up -d

# Check for port conflicts
netstat -ano | findstr :6333
```

#### Issue 2: Ollama Connection Failed
**Symptoms:** "Failed to connect to Ollama" error

**Diagnosis:**
```powershell
ollama ps  # Check running models
curl http://localhost:11434/api/tags  # Test API
```

**Solutions:**
```powershell
# Start Ollama service
ollama serve  # Run in separate terminal

# Or (Windows) check if service is running
Get-Service ollama

# Pull model if missing
ollama pull gemma3:4b
```

#### Issue 3: Upload Not Working
**Symptoms:** PDF upload fails, no error message

**Diagnosis:**
- Check PDF file size (max 50MB)
- Verify PDF is not corrupted
- Check logs: `logs/app.log`

**Solutions:**
- Reduce PDF file size (compress or split)
- Try different PDF
- Restart web UI

#### Issue 4: Low Retrieval Quality
**Symptoms:** Irrelevant results, low scores

**Diagnosis:**
```powershell
# Check collection status
Invoke-RestMethod -Uri 'http://localhost:6333/collections/multilingual_docs'

# Count indexed vectors
# indexed_vectors_count should be > 90% of points_count
```

**Solutions:**
```powershell
# Wait for indexing to complete (can take minutes)
# Check indexing_threshold setting

# If stuck, reindex
python scripts/recreate_collection.py
python scripts/process_one_sample.py  # Reprocess documents
```

#### Issue 5: Out of Memory
**Symptoms:** System crash, slow performance

**Diagnosis:**
```powershell
# Check memory usage
docker stats  # Qdrant memory
Get-Process python  # Python processes
```

**Solutions:**
- Increase Docker memory limit (Settings → Resources)
- Process fewer documents at once
- Reduce chunk size in config
- Add more RAM

### 4.2 Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `OutputTooSmall` | Qdrant filesystem issue | Use named volumes (check docker-compose.yml) |
| `API key not found` | Missing Gemini key | Add to `.env` file |
| `Model not found` | Ollama model missing | Run `ollama pull gemma3:4b` |
| `Collection not found` | Qdrant collection missing | Run `python tests/clean_and_reindex.py` |
| `OCR failed` | Tesseract error | Install language packs, check TESSERACT_CMD |

### 4.3 Logs & Debugging

#### Log Locations:
- **Application:** `logs/app.log`
- **Qdrant:** `docker logs qdrant_multilingual`
- **Ollama:** `ollama logs` (if running as service)

#### Enable Debug Mode:
```env
# In .env
LOG_LEVEL=DEBUG
```

Then restart: `python -m src.main`

---

## 5. Best Practices

### 5.1 Document Upload
- ✅ **Use correct language folder:** Ensures proper OCR settings
- ✅ **Filename conventions:** Use descriptive names (no special chars)
- ✅ **PDF quality:** High-resolution scans (300+ DPI) for better OCR
- ✅ **Batch processing:** Upload similar documents together
- ❌ **Don't upload:** Very large files (>50MB), corrupted PDFs, password-protected

### 5.2 Querying
- ✅ **Be specific:** "What is the research budget limit?" beats "Tell me about budget"
- ✅ **Use keywords:** Include important terms from documents
- ✅ **Natural language:** System understands conversational queries
- ✅ **Follow-up questions:** Chat memory allows context-aware queries
- ❌ **Don't ask:** Out-of-domain questions (weather, sports, etc.)

### 5.3 API Key Management
- ✅ **Use multiple keys:** For rate limit distribution
- ✅ **Monitor quota:** Check Gemini console regularly
- ✅ **Rotate keys:** Monthly or if compromised
- ✅ **Secure storage:** Never commit .env to git
- ❌ **Don't share:** Keys are sensitive credentials

### 5.4 Performance Optimization
- ✅ **Index regularly:** Ensure vectors are indexed (check Qdrant)
- ✅ **Clean old data:** Remove obsolete documents
- ✅ **Monitor resources:** Keep disk >10GB free, RAM >50% available
- ✅ **Use named volumes:** For Qdrant (POSIX compliance)
- ❌ **Don't restart unnecessarily:** Can interrupt processing

### 5.5 Security
- ✅ **Local deployment:** System runs locally, data doesn't leave premise (except API calls)
- ✅ **API encryption:** HTTPS for Gemini API calls
- ✅ **Access control:** Restrict web UI to localhost or use reverse proxy with auth
- ✅ **Backup encryption:** Encrypt backups if containing sensitive data
- ❌ **Don't expose:** Qdrant or Ollama ports to public internet

---

## 6. Quick Reference

### 6.1 Service URLs
- **Web UI:** http://127.0.0.1:8080
- **Qdrant:** http://localhost:6333
- **Qdrant Dashboard:** http://localhost:6333/dashboard
- **Ollama:** http://localhost:11434

### 6.2 Common Commands

```powershell
# Start system
docker-compose --profile cpu up -d
python -m src.main

# Stop system
docker-compose down

# View logs
Get-Content logs\app.log -Tail 50 -Wait

# Backup database
Copy-Item app.db backups\app_$(Get-Date -Format 'yyyyMMdd').db

# Check status
docker ps
ollama list
Invoke-RestMethod -Uri 'http://localhost:6333/healthz'

# Run tests
python tests\test_rag_quick.py

# Reindex (if needed)
python tests\clean_and_reindex.py
```

### 6.3 Support Contacts
- **Technical Issues:** [GitHub Issues](https://github.com/yourrepo/issues)
- **Documentation:** [README.md](../README.md)
- **Email:** support@yourorg.com

---

**End of User Guide**

