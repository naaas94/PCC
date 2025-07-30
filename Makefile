# PCC — PRIVACY CASE CLASSIFIER
# Development automation for fully orchestrated system

.PHONY: help install test format lint check clean run setup bq-setup logs monitor ingest-model ingest-and-run

# Default target
help:
	@echo "PCC — Privacy Case Classifier"
	@echo "=============================="
	@echo ""
	@echo "Available targets:"
	@echo "  setup     - Initial project setup"
	@echo "  install   - Install dependencies"
	@echo "  test      - Run test suite"
	@echo "  format    - Format code with black and isort"
	@echo "  lint      - Lint code with flake8"
	@echo "  check     - Run format and lint checks"
	@echo "  run       - Run pipeline with sample data"
	@echo "  ingest-model - Ingest latest model from GCS"
	@echo "  ingest-and-run - Ingest model and run pipeline"
	@echo "  bq-setup  - Setup BigQuery tables"
	@echo "  logs      - View recent logs"
	@echo "  monitor   - Check BigQuery monitoring data"
	@echo "  clean     - Remove generated files and caches"

# Development setup
setup:
	@echo "Setting up PCC development environment..."
	cp .env.example .env
	cp src/config/config.yaml.example src/config/config.yaml
	@echo "✓ Environment files created"
	@echo "✓ Edit .env and src/config/config.yaml with your settings"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "✓ Dependencies installed"

# BigQuery setup
bq-setup:
	@echo "Setting up BigQuery tables..."
	@echo "Execute the following command in BigQuery:"
	@echo "bq query --use_legacy_sql=false < scripts/create_bigquery_tables.sql"
	@echo "✓ BigQuery tables will be created"

# Testing
test:
	@echo "Running test suite..."
	pytest tests/ -v --tb=short
	@echo "✓ Tests completed"

# Code quality
format:
	@echo "Formatting code..."
	black src/ tests/ scripts/
	isort src/ tests/ scripts/
	@echo "✓ Code formatted"

lint:
	@echo "Linting code..."
	flake8 src/ tests/ scripts/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "✓ Linting completed"

check: format lint
	@echo "✓ All quality checks passed"

# Model ingestion
ingest-model:
	@echo "Ingesting latest model from GCS..."
	python src/ingestion/load_model_from_gcs.py --force-latest
	@echo "✓ Model ingestion completed"

ingest-today:
	@echo "Ingesting today's model from GCS (if available)..."
	python src/ingestion/load_model_from_gcs.py
	@echo "✓ Model ingestion completed"

# Pipeline execution
run:
	@echo "Running pipeline with sample data..."
	python scripts/run_pipeline.py --sample

run-bq:
	@echo "Running pipeline with BigQuery data..."
	@echo "Usage: make run-bq PARTITION=20250101"
	python scripts/run_pipeline.py --partition $(PARTITION) --mode dev

ingest-and-run:
	@echo "Ingesting latest model and running pipeline..."
	python scripts/ingest_and_run_pipeline.py

ingest-and-run-today:
	@echo "Ingesting today's model and running pipeline..."
	python scripts/ingest_and_run_pipeline.py

# Logging and monitoring
logs:
	@echo "Recent pipeline logs:"
	@tail -20 pcc_pipeline.log
	@echo ""
	@echo "Recent BigQuery logs:"
	@tail -20 pcc_bigquery.log

monitor:
	@echo "Checking BigQuery monitoring data..."
	@echo "Query the monitoring table:"
	@echo "SELECT * FROM \`ales-sandbox-465911.PCC_EPs.pcc_monitoring_logs\`"
	@echo "ORDER BY runtime_ts DESC LIMIT 10;"

# Cleanup
clean:
	@echo "Cleaning generated files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	@echo "✓ Cleanup completed"

# Development workflow
dev-setup: setup install
	@echo "✓ Development environment ready"

dev-test: check test
	@echo "✓ Development checks completed"

# Production workflow
prod-setup: setup install bq-setup
	@echo "✓ Production environment ready"

prod-run: check test run
	@echo "✓ Production pipeline completed" 