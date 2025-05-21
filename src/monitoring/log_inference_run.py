# src/monitoring/log_inference_run.py
### 5/21: added inference_log_schema.json and the funct

import uuid
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
from utils.logger import get_logger
from utils.schema_validator import validate_schema 

logger = get_logger()

def log_inference_run(
    partition_date: str,
    model_version: str,
    embedding_model: str,
    total_cases: int,
    passed_validation: int,
    dropped_cases: int,
    status: str = "success",
    notes: str = "MVP run log",
    table: str = "redacted"
):
    """
    Logs a single inference run to BigQuery monitoring table.
    """
    client = bigquery.Client(location="EU")
    run_id = str(uuid.uuid4())
    runtime_ts = datetime.utcnow().isoformat()

    row = {
        "run_id": run_id,
        "model_version": model_version,
        "embedding_model": embedding_model,
        "partition_date": partition_date,
        "runtime_ts": runtime_ts,
        "status": status,
        "total_cases": total_cases,
        "passed_validation": passed_validation,
        "dropped_cases": dropped_cases,
        "notes": notes
    }
    df_row = pd.DataFrame([row])
    df_row["runtime_ts"] = pd.to_datetime(df_row["runtime_ts"])
    validate_schema(df_row, schema_path="schemas/inference_log_schema.json")

    logger.debug(f"Logging inference run: {row}")
    errors = client.insert_rows_json(table, [row])
    if errors:
        logger.error(f"Failed to log inference run: {errors}")
    else:
        logger.info("Inference run logged successfully.")
