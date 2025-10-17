# Start the Multilingual RAG Application

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Multilingual Agentic RAG System - Starting..." -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

# Check if Qdrant is running
Write-Host "`nChecking Qdrant..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:6333" -UseBasicParsing -ErrorAction Stop
    Write-Host "[OK] Qdrant is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Qdrant is not running!" -ForegroundColor Red
    Write-Host "Please start Qdrant first: docker-compose --profile cpu up -d" -ForegroundColor Yellow
    exit 1
}

# Check for Tesseract
Write-Host "`nChecking Tesseract OCR..." -ForegroundColor Yellow
$tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (Test-Path $tesseractPath) {
    Write-Host "[OK] Tesseract found" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Tesseract not found" -ForegroundColor Yellow
    Write-Host "  OCR will not work for scanned PDFs" -ForegroundColor Yellow
    Write-Host "  Digital PDFs will still work fine" -ForegroundColor Yellow
    Write-Host "  Install from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
}

# Count PDFs ready for processing
$pdfCount = (Get-ChildItem data\incoming\*\*.pdf -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "`nPDFs ready for processing: $pdfCount" -ForegroundColor Cyan

Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host "Starting Web UI..." -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "`nOnce started, open your browser to:" -ForegroundColor Yellow
Write-Host "  http://localhost:8080" -ForegroundColor Cyan -NoNewline
Write-Host "`n"
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "`n"

# Start the application
.venv\Scripts\python.exe -m src.main

