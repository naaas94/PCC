# PCC — PRIVACY CASE CLASSIFIER
# Development automation

.PHONY: help install test format lint check clean run setup

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

# Pipeline execution
run:
	@echo "Running pipeline with sample data..."
	python scripts/run_pipeline.py --sample

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