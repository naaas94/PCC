# Model Ingestion from GCS

This document describes the model ingestion system that automatically fetches the latest trained models from Google Cloud Storage and integrates them into the PCC pipeline.

## Overview

The model ingestion system:
- Monitors the GCS bucket `pcc-datasets/pcc-models` for new model artifacts
- Follows the naming convention `vYYYYMMDD_timestamp` for model folders
- Downloads `model.joblib` and `metadata.json` files
- Updates the pipeline configuration automatically
- Integrates seamlessly with the existing inference pipeline

## GCS Structure

```
pcc-datasets/
└── pcc-models/
    ├── v20250729_092110/
    │   ├── model.joblib
    │   └── metadata.json
    ├── v20250729_092253/
    │   ├── model.joblib
    │   └── metadata.json
    └── ...
```

## Usage

### Command Line Interface

```bash
# Ingest the latest model (regardless of date)
python src/ingestion/load_model_from_gcs.py --force-latest

# Ingest today's model (if available)
python src/ingestion/load_model_from_gcs.py

# Ingest and run pipeline in one command
python scripts/ingest_and_run_pipeline.py

# Ingest and run pipeline (today's model only)
python scripts/ingest_and_run_pipeline.py
```

### Makefile Targets

```bash
# Ingest latest model
make ingest-model

# Ingest today's model
make ingest-today

# Ingest and run pipeline
make ingest-and-run

# Ingest today's model and run pipeline
make ingest-and-run-today
```

## Configuration

The model ingestion system updates the following configuration:

### config.yaml
```yaml
models:
  classifier_path: src/models/model.joblib  # Updated automatically
  model_version: v20250729_092110          # Updated from folder name
  embedding_model: all-MiniLM-L6-v2        # From metadata.json
  trained_on: "2025-07-29T09:21:10"       # From metadata.json
  classifier_type: "LogisticRegression"    # From metadata.json
```

### Local Files
- `src/models/model.joblib` - The trained model file
- `src/models/metadata.json` - Model metadata and configuration

## Model Selection Logic

1. **Today's Model Priority**: By default, the system looks for a model folder with today's date (`vYYYYMMDD_*`)
2. **Fallback to Latest**: If no today's model is found, it fetches the latest available model
3. **Force Latest**: Use `--force-latest` flag to always get the latest model regardless of date

## Integration with Pipeline

The model ingestion is integrated into the pipeline in two ways:

### 1. Dynamic Model Loading
The `classifier_interface.py` module now:
- Loads models dynamically from the updated path
- Caches model artifacts in memory
- Provides a `reload_model()` function for manual refresh
- Handles metadata from the ingested model

### 2. Combined Execution
The `ingest_and_run_pipeline.py` script:
- Ingests the latest model
- Reloads the model in memory
- Executes the full pipeline with the new model

## Error Handling

The system handles various error scenarios:

- **No model folders found**: Logs warning and exits gracefully
- **Invalid model file**: Validates model can be loaded before copying
- **Missing metadata**: Continues with default values
- **GCS access issues**: Provides clear error messages

## Monitoring

Model ingestion events are logged with:
- Model folder name and version
- Download success/failure status
- Configuration update status
- Model validation results

## Development Workflow

1. **Local Development**: Use `make ingest-model` to get latest model
2. **Testing**: Use `make ingest-and-run` for end-to-end testing
3. **Production**: Automate with cron jobs or CI/CD pipelines

## Security Considerations

- Requires appropriate GCS permissions
- Validates model files before loading
- Uses temporary directories for downloads
- Cleans up temporary files automatically

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure GCS bucket access
2. **Model Load Failure**: Check model file integrity
3. **Config Update Failure**: Verify write permissions to config.yaml

### Debug Commands

```bash
# Check available models in GCS
gsutil ls gs://pcc-datasets/pcc-models/

# Validate local model
python -c "import joblib; joblib.load('src/models/model.joblib')"

# Check configuration
python -c "from src.config.config import load_config; print(load_config()['models'])"
``` 
noteId: "bd9db4506ccd11f0b65ae144d7921359"
tags: []

---

 