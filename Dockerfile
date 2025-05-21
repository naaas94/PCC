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

# Entry point
ENTRYPOINT ["python", "scripts/run_local_pipeline.py"]