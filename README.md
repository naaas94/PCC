# PCC — PRIVACY CASE CLASSIFIER

**Author:** Ale Garay  
**Project Type:** End-to-End ML Inference Pipeline  
**Stack:** BigQuery • MiniLM • Scikit-learn • Pandas • Pydantic • Docker  
**Use Case:** Classification of customer support messages into privacy-related intent categories using precomputed sentence embeddings and a swappable inference module.  
**Status:** MVP-first, production-minded.

---

## TL;DR

PCC is an MVP implementation of a larger text classification system designed to process inbound customer support messages and identify privacy-related intents under GDPR and CCPA regulations. The system uses precomputed sentence embeddings and a modular inference pipeline to classify messages as privacy cases (PC) or non-privacy cases (NOT_PC).

**Current Status:** MVP with synthetic data and dummy model. All Spotify-specific information and sensitive data have been redacted. The pipeline processes 100 synthetic cases with 95%+ confidence scores and validates against strict input/output schemas.

**How it works:** Daily customer support data is ingested from BigQuery, preprocessed using MiniLM embeddings, classified through a swappable inference module, and output with full metadata and confidence scores.

---

## TABLE OF CONTENTS

* [Project Purpose](#project-purpose)
* [Architecture Overview](#architecture-overview)
* [Project Structure](#project-structure)
* [Getting Started](#getting-started)
* [Configuration](#configuration)
* [Testing](#testing)
* [Status and Roadmap](#status-and-roadmap)
* [Design Principles](#design-principles)

---

## PROJECT PURPOSE

PCC (Privacy Case Classifier) is a modular, orchestrated machine learning pipeline engineered to process daily customer support case data, infer privacy-related intent labels, and output structured, versioned results.

The system is designed for:
* Clear module boundaries (decoupled and testable)
* Daily batch operation over BQ snapshots
* Reproducibility and traceability (model and embedding versions)
* Monitoring, retraining, and drift detection readiness

---

## ARCHITECTURE OVERVIEW

**Ingestion**
* Reads daily partitioned snapshot: redacted_snapshot_<yyyymmdd>
* Validates schema using input_schema.json

**Preprocessing**
* Uses precomputed MiniLM-v6 sentence embeddings
* Validates embedding shape and nullability

**Inference**
* Swappable model interface predict() with version control
* Dummy model (LogReg) with confidence simulation as placeholder
* Structured error handling to avoid pipeline interruption

**Postprocessing**
* Attaches metadata: model version, timestamp, notes
* Enforces output schema compliance

**Output**
* Final predictions written to BigQuery (consumption layer)
* Parallel logging to monitoring layer (audit, drift, diagnostics)

**Orchestration**
* Local CLI mode for development and debugging
* Dockerized for consistent environments

---

## PROJECT STRUCTURE

```
PCC/
├── src/
│   ├── config/          ← Configuration management
│   ├── models/          ← Model artifacts and metadata
│   ├── ingestion/       ← load_from_bq.py
│   ├── preprocessing/   ← embed_text.py
│   ├── inference/       ← classifier_interface.py, predict_intent.py
│   ├── postprocessing/  ← format_output.py
│   ├── monitoring/      ← log_inference_run.py
│   ├── output/          ← write_to_bq.py
│   └── utils/           ← logger.py, schema_validator.py
├── tests/               ← Test suite and fixtures
├── scripts/             ← run_pipeline.py, generate_sample_data.py
├── schemas/             ← JSON schema definitions
├── docs/                ← Technical documentation
│   ├── model_analysis.ipynb ← Model training and analysis
│   └── README.md        ← Documentation guide
├── .env.example         ← Environment variables template
├── requirements.txt     ← Production dependencies
├── requirements-dev.txt ← Development dependencies
├── README.md
├── CONTRIBUTING.md
├── Makefile
└── Dockerfile
```

---

## GETTING STARTED

### Installation

Clone the repository and install required packages:

```bash
git clone <repo>
cd PCC
pip install -r requirements.txt
```

### Environment Setup

Copy the example configuration and set up environment variables:

```bash
cp .env.example .env
cp src/config/config.yaml.example src/config/config.yaml
# Edit .env with your BigQuery credentials
```

### Running the Pipeline

Test the full pipeline locally with synthetic data:

```bash
python scripts/run_pipeline.py --sample
```

Run with BigQuery data (requires credentials):

```bash
python scripts/run_pipeline.py --partition 20250403 --mode dev
```

### Development Commands

```bash
# Run tests
make test

# Format code
make format

# Lint code
make lint

# Run pipeline
make run

# Clean artifacts
make clean
```

---

## CONFIGURATION

**File:** `src/config/config.yaml`

```yaml
bq:
  source_table: your_dataset.redacted_*
  output_table: your_dataset.pcc_predictions
models:
  classifier_path: src/models/pcc_v0.1.1.pkl
  embedding_model: all-MiniLM-L6-v2
runtime:
  mode: dev
  dry_run: true
  partition_date: 20250403
```

**Environment Variables:** See `.env.example` for required BigQuery credentials and configuration.

---

## TESTING

Run the test suite:

```bash
pytest tests/
```

Tests cover:
* Ingestion and schema validation
* Inference pipeline components
* Mock fixtures and synthetic data
* End-to-end pipeline execution

---

## STATUS AND ROADMAP

### Current Status (MVP)

**Completed:**
* Modular pipeline architecture (ingestion, preprocessing, inference, postprocessing, monitoring)
* Schema validation for input/output data
* Synthetic data generation and dummy model
* Basic CI/CD with GitHub Actions
* Docker containerization
* Comprehensive logging and error handling

**Known Limitations:**
* Dummy model lacks semantic complexity — real model integration pending
* Upstream embedding logic assumed to be stable
* Monitoring and alerting system under development
* BigQuery integration requires production credentials

### Sample Results

```
🚀 Running PCC Pipeline with Sample Data
==================================================
✅ Pipeline completed successfully!

📈 Results Summary:
Total cases processed: 100
Model version: v0.1
Embedding model: all-MiniLM-L6-v2

Sample predictions:
       case_id predicted_label  confidence
0  CASE_000000          NOT_PC    0.994793
1  CASE_000001              PC    0.981397
2  CASE_000002              PC    0.973360
```

### Model Performance

For detailed model analysis and training process, see [`docs/model_analysis.ipynb`](docs/model_analysis.ipynb).

**Key Performance Metrics:**
- **ROC-AUC: 0.998** - Excellent class separability
- **PR-AUC: 0.998** - Outstanding performance on imbalanced dataset
- **F1-Score: 0.97** - Balanced precision and recall
- **Accuracy: 97%** - High overall performance

---

## DESIGN PRINCIPLES

* Each component must be testable in isolation.
* Pipeline must fail loudly and visibly when assumptions break.
* Output tables must always be schema-compliant and versioned.
* Prediction functions must be swappable, with zero side effects.
* Monitoring is not an add-on. It is part of the system design.
* Treat Docker as runtime notebooks — identical outputs, different environments.

---

## CONTRIBUTING

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and contribution process.

## LICENSE

[LICENSE](https://github.com/naaas94/PCC/blob/main/LICENSE) 
