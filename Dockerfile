# Dockerfile for Multilingual Agentic RAG
# CPU-first, optional GPU support

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-chi-sim \
    tesseract-ocr-hin \
    tesseract-ocr-ben \
    tesseract-ocr-urd \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY .env.example .env

# Create data directories
RUN mkdir -p data/incoming/{en,zh,hi,bn,ur} \
    data/{processing,ocr_raw,ocr_clean,chunks,embeddings} \
    reports \
    logs

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TESSERACT_CMD=/usr/bin/tesseract

# Run application
CMD ["python", "-m", "src.main"]

