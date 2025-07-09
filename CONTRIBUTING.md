# CONTRIBUTING TO PCC

Development guidelines for the Privacy Case Classifier project.

---

## SETUP

### Prerequisites
* Python 3.10+
* Git
* Docker (optional)

### Local Environment
```bash
git clone <repository-url>
cd PCC
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
cp src/config/config.yaml.example src/config/config.yaml
```

---

## DEVELOPMENT WORKFLOW

### Code Quality
* Follow PEP 8 style guidelines
* Use type hints for function parameters
* Keep functions focused and testable
* Document complex logic with clear comments

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Test pipeline
python scripts/run_pipeline.py --sample
```

### Code Quality Checks
```bash
# Format code
black src/ tests/ scripts/

# Lint code
flake8 src/ tests/ scripts/

# Run all checks
make check
```

---

## CONTRIBUTION PROCESS

### 1. Development
* Create feature branches from `main`
* Use descriptive branch names: `feature/component-name`
* Make atomic commits with clear messages
* Test changes thoroughly before submission

### 2. Pull Request
* Create PR with clear title and description
* Reference related issues
* Include test results
* Request review from maintainers

### 3. Review
* Code review required for all changes
* Address feedback and suggestions
* Ensure CI/CD pipeline passes
* Update documentation as needed

---

## ARCHITECTURE GUIDELINES

### Component Design
* Each component must be testable in isolation
* Maintain clear module boundaries
* Use dependency injection for external services
* Implement proper error handling and logging

### Pipeline Components
**Ingestion:** Validate input data against schemas
**Preprocessing:** Validate embedding vectors and shapes
**Inference:** Implement swappable model interface
**Postprocessing:** Enforce output schema compliance
**Output:** Write to configured destinations
**Monitoring:** Log pipeline execution and statistics

### Configuration Management
* Use environment variables for sensitive data
* Validate configuration at startup
* Provide clear error messages for missing configuration

---

## TESTING STRATEGY

### Test Types
**Unit Tests:** Test individual functions and classes
**Integration Tests:** Test component interactions
**End-to-End Tests:** Test complete pipeline execution

### Test Data
* Use synthetic data for reproducible tests
* Include edge cases and error scenarios
* Maintain test data schemas

---

## SECURITY GUIDELINES

* Never commit sensitive data or credentials
* Use environment variables for secrets
* Validate input data to prevent injection attacks
* Follow secure coding practices

---

## SUPPORT

For questions or issues:
* Check existing documentation
* Review open and closed issues
* Contact maintainers for urgent issues
* Provide detailed information when reporting problems

 