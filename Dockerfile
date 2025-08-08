# PCC — Privacy Case Classifier
# Production-ready Docker image for EKS deployment

# Multi-stage build for optimization
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Production stage
FROM python:3.10-slim

# Create non-root user for security
RUN groupadd -r pcc && useradd -r -g pcc pcc

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set workdir
WORKDIR /app

# Copy application code
COPY --chown=pcc:pcc . .

# Add src to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Create necessary directories
RUN mkdir -p /app/logs /app/models /app/config && \
    chown -R pcc:pcc /app

# Switch to non-root user
USER pcc

# Set default environment variables
ENV DRY_RUN=false \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command (can be overridden)
ENTRYPOINT ["python", "scripts/run_pipeline.py"]