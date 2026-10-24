# Production Dockerfile for DocuMind AI
FROM python:3.11-slim

# Optimize Python execution environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    APP_ENV=production \
    CHROMA_PERSIST_DIRECTORY=/app/data/chroma \
    UPLOAD_DIR=/app/data/uploads

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache embedding model weights for rapid cold starts and offline execution
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code, evaluation suite, and compiled React UI
COPY app /app/app
COPY evals /app/evals
COPY frontend/dist /app/frontend/dist

# Create non-privileged user and persistent data directories
RUN useradd -u 10001 -m -s /bin/bash appuser && \
    mkdir -p /app/data/chroma /app/data/uploads && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Bind to dynamically assigned PORT from hosting environment
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
