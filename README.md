# PCC — PRIVACY CASE CLASSIFIER

**Original Author:** Alejandro Garay  
**Project Type:** End-to-End ML Inference Pipeline  
**Stack:** BigQuery • MiniLM • Scikit-learn • Pandas • Pydantic • Docker  
**Use Case:** Classification of customer support messages into privacy-related intent categories using precomputed sentence embeddings and a swappable inference module.  
**Status:** MVP-first, production-minded.

---

## Attribution

This project was originally created by Alejandro Garay as a privacy case classification system for GDPR/CCPA compliance. For contributions, please see [CONTRIBUTING.md](CONTRIBUTING.md).

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

```