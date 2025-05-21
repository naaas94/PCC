PCC — PRIVACY CASE CLASSIFIER
Author: Ale Garay
Project Type: End-to-End ML Inference Pipeline
Stack: BigQuery • MiniLM • Scikit-learn • Flyte • Docker • Pandas • Pydantic
Use Case: Classification of customer support messages into privacy-related intent categories using precomputed sentence embeddings and a swappable inference module. Status: MVP-first, production-minded.
________________


TABLE OF CONTENTS
* Project Purpose
* Architecture Overview
* Project Structure
* Getting Started
* Schema Definitions
* Tests
* Configuration
* Status and Roadmap
* Design Principles
________________


PROJECT PURPOSE
PCC (Privacy Case Classifier) is a modular, orchestrated machine learning pipeline engineered to process daily customer support case data, infer privacy-related intent labels, and output structured, versioned results.
The system is designed for:
* Clear module boundaries (decoupled and testable)
* Daily batch operation over BQ snapshots (Flyte DAG)
* Reproducibility and traceability (model and embedding versions)
* Monitoring, retraining, and drift detection readiness
________________


ARCHITECTURE OVERVIEW
Ingestion
* Reads daily partitioned snapshot: redacted_snapshot_<yyyymmdd>
* Validates schema using input_schema.json
Preprocessing
* Uses precomputed MiniLM-v6 sentence embeddings
* Validates embedding shape and nullability
Inference
* Swappable model interface predict() with version control
* Dummy model (LogReg) with confidence simulation as placeholder
* Structured error handling to avoid pipeline interruption
Postprocessing
* Attaches metadata: model version, timestamp, notes
* Enforces output schema compliance
Output
* Final predictions written to BigQuery (consumption layer)
* Parallel logging to monitoring layer or lakehouse (audit, drift, diagnostics)
Orchestration
* Orchestrated with Flyte for daily execution
* Local CLI mode for development and debugging
* Dockerized for consistent environments
________________


PROJECT STRUCTURE
pcc_pipeline/
├── src/
│   ├── ingestion/        ← load_from_bq.py
│   ├── preprocessing/    ← embed_text.py
│   ├── inference/        ← classifier_interface.py, predict_intent.py
│   ├── postprocessing/   ← format_output.py
│   ├── monitoring/       ← log_to_lake.py
│   ├── output/           ← write_to_bq.py
│   └── utils/            ← logger.py, schema_validator.py
├── flyte/                ← flyte_tasks.py, flyte_workflow.py
├── models/               ← classifier.pkl, metadata.json
├── schemas/              ← input_schema.json, output_schema.json
├── tests/                ← test_*.py, fixtures/
├── scripts/              ← run_local_pipeline.py, run_training.py
├── config/               ← config.yaml
├── Dockerfile
├── requirements.txt
└── README.md
________________


GETTING STARTED
Installation
Clone the repository and install required packages:
git clone <repo>
cd pcc_pipeline
pip install -r requirements.txt
Running the Local Pipeline
Test the full pipeline locally using a specific snapshot date:
python scripts/run_local_pipeline.py \
  --mode dev \
  --partition 20250403
Training a Model (Optional)
python scripts/run_training.py \
  --input data/training_data.csv \
  --output models/pcc_v0.1.1.pkl
________________


SCHEMA DEFINITIONS
Input Schema: schemas/input_schema.json
{
  "case_id": "string",
  "embedding_vector": "list[float]",
  "ingestion_ts": "timestamp"
}
Output Schema: schemas/output_schema.json
{
  "case_id": "string",
  "predicted_label": "string",
  "subtype_label": "string|null",
  "confidence": "float",
  "model_version": "string",
  "embedding_model": "string",
  "inference_timestamp": "timestamp",
  "prediction_notes": "string|null"
}
________________


TESTS
To run the test suite:
pytest tests/
Tests cover ingestion, inference, schema validation, and mock fixtures.
________________


CONFIGURATION
File: config/config.yaml
bq:
  source_table: your_dataset.v2_case_history_snapshot_*
  output_table: your_dataset.pcc_predictions
models:
  classifier_path: models/pcc_v0.1.1.pkl
  label_encoder_path: models/label_encoder.pkl # not used in mvp
  embedding_model: MiniLM-L6-v2
runtime:
  mode: dev
  dry_run: false
  partition_date: 20250403
________________


STATUS AND ROADMAP
Known Limitations:
* Dummy model lacks semantic complexity — real model integration pending
* Upstream embedding logic assumed to be stable
* Monitoring and alerting system under development
________________


DESIGN PRINCIPLES
* Each component must be testable in isolation.
* Pipeline must fail loudly and visibly when assumptions break.
* Output tables must always be schema-compliant and versioned.
* Prediction functions must be swappable, with zero side effects.
* Monitoring is not an add-on. It is part of the system design.
* Treat Flyte and Docker as runtime notebooks — identical outputs, different environments.