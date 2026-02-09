# PCC — PRIVACY CASE CLASSIFIER

**Original Author:** Alejandro Garay  
**Project Type:** End-to-End ML Inference Pipeline  
**Stack:** BigQuery • MiniLM • Scikit-learn • Pandas • Pydantic • Docker • Google Cloud Storage  
**Use Case:** Classification of customer support messages into privacy-related intent categories using precomputed sentence embeddings and a swappable inference module with automatic model ingestion from GCS.  
**Status:** Production-ready with full BigQuery orchestration and dynamic model management.

> Live Looker Dashboard: [View real-time pipeline monitoring and inference results](https://lookerstudio.google.com/reporting/9cb78e63-f5a4-4c5b-95b2-3056171628a6/page/SuJRF) — data from the endpoints (EPs) is displayed and monitored here daily.

---

## Attribution

This project was originally created by Alejandro Garay as a privacy case classification system for GDPR/CCPA compliance. For contributions, please see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## TL;DR

PCC is a production-ready implementation of a text classification system designed to process inbound customer support messages and identify privacy-related intents under GDPR and CCPA regulations. The system uses precomputed sentence embeddings and a modular inference pipeline to classify messages as privacy cases (PC) or non-privacy cases (NOT_PC).

**Current Status:** Fully orchestrated system with BigQuery integration, monitoring, and production-ready error handling. The pipeline processes data with 95%+ confidence scores, validates against strict input/output schemas, and writes results to BigQuery tables with comprehensive monitoring. **LIVE:** Two production BigQuery tables running daily real-time inferences with synthetic data, plus a Looker dashboard for monitoring pipeline performance. **NEW:** Automatic model ingestion from GCS with dynamic model loading, version management, and seamless integration with the existing pipeline.

**How it works:** Daily customer support data is ingested from BigQuery, preprocessed using combined MiniLM and TF-IDF embeddings (584 dimensions), classified through a swappable inference module with automatic model updates from GCS, and output with full metadata and confidence scores to BigQuery tables with monitoring logs.

---

## TABLE OF CONTENTS

* [Project Purpose](#project-purpose)
* [Architecture Overview](#architecture-overview)
* [Project Structure](#project-structure)
* [Getting Started](#getting-started)
* [Configuration](#configuration)
* [Model Management](#model-management)
* [Testing](#testing)
* [Status and Roadmap](#status-and-roadmap)
* [Design Principles](#design-principles)

---

## PROJECT PURPOSE

PCC (Privacy Case Classifier) is a modular, orchestrated machine learning pipeline engineered to process daily customer support case data, infer privacy-related intent labels, and output structured, versioned results to BigQuery with comprehensive monitoring and dynamic model management.

The system is designed for:
* Clear module boundaries (decoupled and testable)
* Daily batch operation over BQ snapshots
* Reproducibility and traceability (model and embedding versions)
* Production monitoring, retraining, and drift detection
* Full BigQuery integration with error handling and retry logic
* Automatic model ingestion and version management from GCS

---

## ARCHITECTURE OVERVIEW

**Ingestion**
* Reads daily partitioned snapshot: redacted_snapshot_<yyyymmdd>
* Validates schema using input_schema.json
* Supports both BigQuery and synthetic data sources

**Preprocessing**
* Uses precomputed combined MiniLM and TF-IDF embeddings (584 dimensions)
* Validates embedding shape and nullability
* Handles data quality issues gracefully

**Inference**
* Swappable model interface predict() with version control
* Dynamic model loading with automatic GCS ingestion
* Model caching and reloading for performance
* Structured error handling to avoid pipeline interruption

**Postprocessing**
* Attaches metadata: model version, timestamp, notes
* Enforces output schema compliance
* Prepares data for BigQuery persistence

**Output**
* Final predictions written to BigQuery (consumption layer)
* Parallel logging to monitoring layer (audit, drift, diagnostics)
* Write verification and retry logic for reliability

**Orchestration**
* Local CLI mode for development and debugging
* Dockerized for consistent environments
* Production-ready error handling and monitoring

**Model Management**
* Automatic ingestion from GCS bucket `pcc-datasets/pcc-models`
* Dynamic model loading with version tracking
* Support for today's model priority or latest model fallback
* Seamless integration with existing pipeline
* Model caching and reloading capabilities

---

## PROJECT STRUCTURE

```
PCC/
├── src/
│   ├── config/          ← Configuration management
│   ├── models/          ← Model artifacts and metadata
│   ├── ingestion/       ← load_from_bq.py, load_model_from_gcs.py
│   ├── preprocessing/   ← embed_text.py
│   ├── inference/       ← classifier_interface.py, predict_intent.py
│   ├── postprocessing/  ← format_output.py
│   ├── monitoring/      ← log_inference_run.py
│   ├── output/          ← write_to_bq.py
│   └── utils/           ← logger.py, schema_validator.py
├── tests/               ← Test suite and fixtures
├── scripts/             ← run_pipeline.py, ingest_and_run_pipeline.py
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

### BigQuery Setup

Create the required BigQuery tables:

```bash
# Execute the table creation script in BigQuery
bq query --use_legacy_sql=false < scripts/create_bigquery_tables.sql
```

### Model Ingestion

The system automatically ingests models from GCS. You can ingest models manually or as part of pipeline execution:

```bash
# Ingest latest model from GCS
make ingest-model

# Ingest today's model (if available)
make ingest-today

# Ingest and run pipeline in one command
make ingest-and-run

# Run daily pipeline with automatic model ingestion
make daily-run
```

### Running the Pipeline

Test the full pipeline locally with synthetic data:

```bash
python scripts/run_pipeline.py --sample
```

Run with BigQuery data and model ingestion:

```bash
python scripts/run_pipeline.py --partition 20250101 --mode dev --force-latest
```

### Development Commands

```bash
# Run tests
make test

# Format code
make format

# Lint code
make lint

# Run pipeline with sample data
make run

# Run pipeline with model ingestion
make run-with-model

# Run with BigQuery data and model ingestion
make run-bq-with-model PARTITION=20250101
```

---

## CONFIGURATION

### Live BigQuery Tables

The system maintains two production BigQuery tables running daily real-time inferences with synthetic data:

- **Inference Output Table**: `ales-sandbox-465911.PCC_EPs.pcc_inference_output`
  - Stores daily inference results with 7-day retention
  - Partitioned by ingestion date
  - Contains case_id, predictions, confidence scores, and metadata
  - **Status**: Live daily pipeline with synthetic data

- **Monitoring Logs Table**: `ales-sandbox-465911.PCC_EPs.pcc_monitoring_logs`
  - Tracks pipeline execution metrics and run logs
  - Stores run_id, performance metrics, and error information
  - Partitioned by ingestion date with 7-day retention
  - **Status**: Live daily monitoring with comprehensive logging

### Looker Dashboard

A production Looker dashboard is available for monitoring daily pipeline runs and performance metrics:
- **Dashboard**: [PCC Pipeline Monitoring](https://lookerstudio.google.com/reporting/9cb78e63-f5a4-4c5b-95b2-3056171628a6/page/SuJRF)
- **Purpose**: Real-time visualization of pipeline performance, inference results, and monitoring metrics
- **Access**: Internal dashboard for pipeline oversight and performance tracking

*Note: BigQuery tables are not public to manage billing and quota usage carefully.*

### Environment Variables

- `DRY_RUN`: Set to `true` for dry runs, `false` (default) for production writes
- `BQ_SOURCE_TABLE`: Override source table in config
- `BQ_OUTPUT_TABLE`: Override output table in config
- `PARTITION_DATE`: Override partition date in config

### Runtime Modes

- **dev**: Development mode with detailed logging
- **prod**: Production mode with optimized performance
- **dry_run**: Prevents BigQuery writes for testing

---

## MODEL MANAGEMENT

### GCS Model Storage

Models are stored in Google Cloud Storage with the following structure:
```
pcc-datasets/pcc-models/
├── v20250101_143022/
│   ├── model.joblib
│   └── metadata.json
├── v20250102_091545/
│   ├── model.joblib
│   └── metadata.json
└── ...
```

### Model Ingestion Process

1. **Discovery**: System searches for model folders in GCS bucket
2. **Priority**: Today's model (if available) takes priority over latest model
3. **Download**: Model.joblib and metadata.json are downloaded to local storage
4. **Validation**: Model is validated by attempting to load it
5. **Configuration**: Config.yaml is updated with new model information
6. **Integration**: Model is seamlessly integrated with existing pipeline

### Model Versioning

- **Naming Convention**: `vYYYYMMDD_HHMMSS` format
- **Metadata Tracking**: Model version, embedding model, training date
- **Fallback Strategy**: Latest available model if today's model not found
- **Cache Management**: Model caching with reload capabilities

### Available Commands

```bash
# Model ingestion
make ingest-model          # Ingest latest model
make ingest-today          # Ingest today's model (if available)
make ingest-and-run        # Ingest model and run pipeline

# Pipeline execution with models
make run-with-model        # Run with sample data + model ingestion
make run-bq-with-model     # Run with BigQuery + model ingestion
make daily-run             # Daily pipeline with automatic model ingestion
```

---

## TESTING

The system includes comprehensive testing:

```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_config.py -v
pytest tests/test_pipeline_smoke.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

- Configuration management
- Schema validation
- Pipeline smoke tests
- BigQuery integration (mocked)
- Error handling scenarios
- Model ingestion and loading

---
