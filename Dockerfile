# PCC — Privacy Case Classifier
# Production-ready Docker image for fully orchestrated system

# Base image
FROM python:3.10-slim

# Avoid .pyc files and enable live logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# Install system dependencies (compiler for packages like numpy, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Add src to PYTHONPATH so `from config.config import load_config` works
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Create log directory
RUN mkdir -p /app/logs

# Set default environment variables
ENV DRY_RUN=false
ENV PYTHONPATH=/app/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Entry point for production pipeline
ENTRYPOINT ["python", "scripts/run_pipeline.py"]