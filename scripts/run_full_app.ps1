# Full Application Startup Script with Verification

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "  Multilingual Agentic RAG System - Full Application Startup" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan

# Verification checks
$allGood = $true

# 1. Check Qdrant
Write-Host "`n[1/4] Checking Qdrant Vector Database..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:6333" -UseBasicParsing -ErrorAction Stop
    Write-Host "      [OK] Qdrant is running on port 6333" -ForegroundColor Green
} catch {
    Write-Host "      [ERROR] Qdrant is not running!" -ForegroundColor Red
    Write-Host "      Run: docker-compose --profile cpu up -d" -ForegroundColor Yellow
    $allGood = $false
}

# 2. Check Tesseract
Write-Host "`n[2/4] Checking Tesseract OCR..." -ForegroundColor Yellow
$tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (Test-Path $tesseractPath) {
    $version = & $tesseractPath --version 2>&1 | Select-Object -First 1
    Write-Host "      [OK] Tesseract found: $version" -ForegroundColor Green
} else {
    Write-Host "      [ERROR] Tesseract not found at expected location" -ForegroundColor Red
    $allGood = $false
}

# 3. Check Ollama
Write-Host "`n[3/4] Checking Ollama LLM..." -ForegroundColor Yellow
try {
    $ollamaList = ollama list 2>&1
    if ($ollamaList -match "deepseek-r1:1.5b") {
        Write-Host "      [OK] Ollama is running with deepseek-r1:1.5b model" -ForegroundColor Green
    } else {
        Write-Host "      [WARNING] deepseek-r1:1.5b model not found" -ForegroundColor Yellow
        Write-Host "      System will use Gemini Flash fallback" -ForegroundColor Yellow
    }
} catch {
    Write-Host "      [WARNING] Ollama not running - will use Gemini fallback" -ForegroundColor Yellow
}

# 4. Check PDFs
Write-Host "`n[4/4] Checking PDFs ready for processing..." -ForegroundColor Yellow
$pdfCount = (Get-ChildItem data\incoming\*\*.pdf -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "      [OK] Found $pdfCount PDFs ready for ingestion" -ForegroundColor Green

# Summary
Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan

if ($allGood) {
    Write-Host "  ALL SYSTEMS READY!" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Cyan
    
    Write-Host "`n  Starting Web UI on: " -NoNewline -ForegroundColor Yellow
    Write-Host "http://localhost:8080" -ForegroundColor Cyan
    Write-Host "`n  Features available:" -ForegroundColor Yellow
    Write-Host "    - Upload & process multilingual PDFs" -ForegroundColor White
    Write-Host "    - Chat with your documents" -ForegroundColor White
    Write-Host "    - Real-time processing logs" -ForegroundColor White
    Write-Host "    - Hybrid retrieval (Dense + BM25)" -ForegroundColor White
    Write-Host "    - Query decomposition & reranking" -ForegroundColor White
    
    Write-Host "`n  Press Ctrl+C to stop the server`n" -ForegroundColor Gray
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "`n"
    
    # Start the application
    .venv\Scripts\python.exe -m src.main
} else {
    Write-Host "  SETUP INCOMPLETE - Please fix errors above" -ForegroundColor Red
    Write-Host "=" * 80 -ForegroundColor Cyan
    exit 1
}

