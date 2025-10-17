# Windows PowerShell venv setup script
# Run with: .\venv_setup.ps1

Write-Host "Setting up Python virtual environment (Windows)..." -ForegroundColor Green

# Check Python version
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found! Please install Python 3.10+ first." -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Cyan

# Create venv
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Removing old venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

Write-Host "Creating virtual environment..." -ForegroundColor Green
python -m venv venv

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

# Create data directories
Write-Host "Creating data directories..." -ForegroundColor Green
$dirs = @(
    "data\incoming\en",
    "data\incoming\zh",
    "data\incoming\hi",
    "data\incoming\bn",
    "data\incoming\ur",
    "data\processing",
    "data\ocr_raw",
    "data\ocr_clean",
    "data\chunks",
    "data\embeddings",
    "reports",
    "qdrant_storage"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Copy .env.example to .env if not exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Green
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env and add your API keys!" -ForegroundColor Yellow
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env and add your Gemini API keys" -ForegroundColor White
Write-Host "  2. Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor White
Write-Host "  3. Download language packs: eng, chi_sim, hin, ben, urd" -ForegroundColor White
Write-Host "  4. Install Ollama and pull deepseek-r1:1.5b model" -ForegroundColor White
Write-Host "  5. Start Qdrant: docker-compose --profile cpu up -d" -ForegroundColor White
Write-Host "  6. Run the app: python src/main.py" -ForegroundColor White

