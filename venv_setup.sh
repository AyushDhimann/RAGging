#!/bin/bash
# Linux/Mac venv setup script
# Run with: chmod +x venv_setup.sh && ./venv_setup.sh

set -e

echo "Setting up Python virtual environment (Linux/Mac)..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found! Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Found: $PYTHON_VERSION"

# Create venv
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing old venv..."
    rm -rf venv
fi

echo "Creating virtual environment..."
python3 -m venv venv

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create data directories
echo "Creating data directories..."
mkdir -p data/incoming/{en,zh,hi,bn,ur}
mkdir -p data/{processing,ocr_raw,ocr_clean,chunks,embeddings}
mkdir -p reports
mkdir -p qdrant_storage

# Copy .env.example to .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env and add your API keys!"
fi

echo ""
echo "Setup complete!"
echo "Next steps:"
echo "  1. Edit .env and add your Gemini API keys"
echo "  2. Install Tesseract OCR: sudo apt-get install tesseract-ocr"
echo "  3. Install language packs: sudo apt-get install tesseract-ocr-{eng,chi-sim,hin,ben,urd}"
echo "  4. Install Ollama and pull deepseek-r1:1.5b model"
echo "  5. Start Qdrant: docker-compose --profile cpu up -d"
echo "  6. Run the app: python src/main.py"

