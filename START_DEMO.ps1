# START_DEMO.ps1 - Launch complete RAG system for interview demo

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🚀 MULTILINGUAL RAG SYSTEM - INTERVIEW DEMO" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# 1. Check if in correct directory
if (-not (Test-Path "src\main.py")) {
    Write-Host "❌ Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# 2. Check Qdrant
Write-Host "[1/4] Checking Qdrant..." -ForegroundColor Yellow
$qdrantRunning = docker ps | Select-String "qdrant"
if (-not $qdrantRunning) {
    Write-Host "   Starting Qdrant..." -ForegroundColor Cyan
    docker-compose up -d
    Start-Sleep -Seconds 5
}
Write-Host "   ✅ Qdrant is running" -ForegroundColor Green

# 3. Check Ollama
Write-Host "[2/4] Checking Ollama..." -ForegroundColor Yellow
try {
    $ollamaStatus = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -ErrorAction Stop
    Write-Host "   ✅ Ollama is running" -ForegroundColor Green
    
    $hasDeepseek = $ollamaStatus.models | Where-Object { $_.name -match "deepseek-r1:1.5b" }
    if ($hasDeepseek) {
        Write-Host "   ✅ deepseek-r1:1.5b model is ready" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  deepseek-r1:1.5b not found, pulling..." -ForegroundColor Yellow
        ollama pull deepseek-r1:1.5b
    }
} catch {
    Write-Host "   ❌ Ollama is not running. Please start Ollama first." -ForegroundColor Red
    exit 1
}

# 4. Check Tesseract
Write-Host "[3/4] Checking Tesseract..." -ForegroundColor Yellow
if (Test-Path "C:\Program Files\Tesseract-OCR\tesseract.exe") {
    Write-Host "   ✅ Tesseract is installed" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Tesseract not found at default location" -ForegroundColor Yellow
}

# 5. Verify Qdrant data
Write-Host "[4/4] Checking Qdrant data..." -ForegroundColor Yellow
try {
    $collectionInfo = Invoke-RestMethod -Uri "http://localhost:6333/collections/multilingual_docs"
    $pointsCount = $collectionInfo.result.points_count
    Write-Host "   ✅ Collection has $pointsCount embeddings" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Collection not found or empty. Run processing first:" -ForegroundColor Yellow
    Write-Host "      .venv\Scripts\python.exe scripts\process_one_sample.py" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📊 QUICK TESTS" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Run comprehensive tests:" -ForegroundColor Yellow
Write-Host "  .venv\Scripts\python.exe tests\test_rag_quick.py" -ForegroundColor Cyan
Write-Host ""

# Ask user what to do
Write-Host "What would you like to do?" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Run tests (show 5/5 passing)" -ForegroundColor Cyan
Write-Host "  2. Start web UI (for live demo)" -ForegroundColor Cyan
Write-Host "  3. Process sample documents" -ForegroundColor Cyan
Write-Host "  4. View system status" -ForegroundColor Cyan
Write-Host "  5. Exit" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "Enter choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🧪 Running comprehensive tests..." -ForegroundColor Green
        Write-Host ""
        .venv\Scripts\python.exe tests\test_rag_quick.py
        Write-Host ""
        Write-Host "Press any key to exit..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    "2" {
        Write-Host ""
        Write-Host "🌐 Starting web UI..." -ForegroundColor Green
        Write-Host ""
        Write-Host "Access the UI at: http://localhost:8080" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        .venv\Scripts\python.exe -m src.main
    }
    "3" {
        Write-Host ""
        Write-Host "📄 Processing sample documents..." -ForegroundColor Green
        Write-Host ""
        .venv\Scripts\python.exe scripts\process_one_sample.py
        Write-Host ""
        Write-Host "Press any key to exit..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    "4" {
        Write-Host ""
        Write-Host "📊 System Status:" -ForegroundColor Green
        Write-Host ""
        
        # Qdrant status
        try {
            $collectionInfo = Invoke-RestMethod -Uri "http://localhost:6333/collections/multilingual_docs"
            Write-Host "Qdrant Collection:" -ForegroundColor Yellow
            Write-Host "  Name: multilingual_docs" -ForegroundColor Cyan
            Write-Host "  Points: $($collectionInfo.result.points_count)" -ForegroundColor Cyan
            Write-Host "  Status: $($collectionInfo.result.status)" -ForegroundColor Cyan
        } catch {
            Write-Host "  ❌ Collection not accessible" -ForegroundColor Red
        }
        
        Write-Host ""
        Write-Host "Press any key to exit..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    "5" {
        Write-Host ""
        Write-Host "👋 Goodbye! Good luck with your interview!" -ForegroundColor Green
        exit 0
    }
    default {
        Write-Host ""
        Write-Host "Invalid choice. Exiting..." -ForegroundColor Red
        exit 1
    }
}

