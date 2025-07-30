# src/monitoring/log_inference_run.py
# 5/21: added inference_log_schema.json and the funct

import uuid
import pandas as pd
from google.cloud import bigquery
from utils.logger import get_bq_logger
from utils.schema_validator import validate_schema
from config.config import load_config
import time
from typing import Optional

logger = get_bq_logger()
config = load_config()


def _prepare_log_row(
    partition_date: str,
    model_version: str,
    embedding_model: str,
    total_cases: int,
    passed_validation: int,
    dropped_cases: int,
    status: str,
    notes: str,
    processing_duration_seconds: float,
    error_message: str | None,
    run_id: str,
    runtime_ts: pd.Timestamp
) -> dict:
    """Prepare the log row data structure."""
    return {
        "run_id": run_id,
        "model_version": model_version,
        "embedding_model": embedding_model,
        "partition_date": partition_date,
        "runtime_ts": runtime_ts,
        "status": status,
        "total_cases": total_cases,
        "passed_validation": passed_validation,
        "dropped_cases": dropped_cases,
        "notes": notes,
        "ingestion_time": runtime_ts,
        "processing_duration_seconds": processing_duration_seconds,
        "error_message": error_message
    }


def _validate_and_prepare_data(row: dict, df_row: pd.DataFrame) -> bool:
    """Validate schema and prepare data for BigQuery."""
    try:
        validate_schema(
            df_row,
            schema_path="schemas/inference_log_schema.json"
        )
        logger.debug("Monitoring log schema validated successfully")
    except Exception as e:
        logger.error(f"Monitoring log schema validation failed: {e}")
        return False

    # Convert all pd.Timestamp to RFC3339 string for BigQuery JSON API
    for k, v in row.items():
        if isinstance(v, pd.Timestamp):
            row[k] = v.isoformat()

    return True


def _insert_with_retry(
    client: bigquery.Client,
    table: str,
    row: dict,
    max_retries: int
) -> bool:
    """Insert row to BigQuery with retry logic."""
    for attempt in range(max_retries):
        try:
            errors = client.insert_rows_json(table, [row])
            if errors:
                logger.error(
                    f"Failed to log inference run (attempt {attempt + 1}): {errors}"
                )
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return False
            else:
                logger.info(f"Inference run logged successfully to {table}")
                return True

        except Exception as e:
            logger.error(
                f"Exception logging inference run (attempt {attempt + 1}): {e}"
            )
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return False

    return False


def log_inference_run(
    partition_date: str,
    model_version: str,
    embedding_model: str,
    total_cases: int,
    passed_validation: int,
    dropped_cases: int,
    status: str = "success",
    notes: str = "MVP run log",
    processing_duration_seconds: float = 0.0,
    error_message: str | None = None,
    table: Optional[str] = None,
    max_retries: int = 3
) -> bool:
    """
    Logs a single inference run to BigQuery monitoring table.

    Args:
        partition_date: Date partition being processed
        model_version: Version of the model used
        embedding_model: Embedding model used
        total_cases: Total number of cases processed
        passed_validation: Number of cases that passed validation
        dropped_cases: Number of cases dropped during processing
        status: Status of the run (success, failed, partial)
        notes: Additional notes about the run
        processing_duration_seconds: Time taken to process
        error_message: Error message if any
        table: BigQuery table name (uses config if not provided)
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if logging successful, False otherwise
    """
    if table is None:
        # Use config table or default
        table = config.get("bq", {}).get(
            "monitoring_table",
            "ales-sandbox-465911.PCC_EPs.pcc_monitoring_logs"
        )

    # Ensure table is not None for BigQuery operations
    if table is None:
        logger.error("No monitoring table configured")
        return False

    dry_run = config["runtime"].get("dry_run", False)
    if dry_run:
        logger.info(f"[DRY RUN] Would log inference run to {table}")
        logger.info(
            f"[DRY RUN] Run details: {partition_date}, {model_version}, {status}"
        )
        return True

    client = bigquery.Client(location="EU")
    run_id = str(uuid.uuid4())
    runtime_ts = pd.Timestamp.utcnow()

    row = _prepare_log_row(
        partition_date, model_version, embedding_model, total_cases,
        passed_validation, dropped_cases, status, notes,
        processing_duration_seconds, error_message, run_id, runtime_ts
    )

    df_row = pd.DataFrame([row])

    # Validate schema and prepare data
    if not _validate_and_prepare_data(row, df_row):
        return False

    logger.debug(f"Logging inference run: {row}")

    # Insert with retry logic
    success = _insert_with_retry(client, table, row, max_retries)
    if success:
        logger.info(f"Run ID: {run_id}, Status: {status}, Cases: {total_cases}")

    return success


def verify_monitoring_log(run_id: str, table: Optional[str] = None) -> bool:
    """
    Verify that a monitoring log entry was written to BigQuery.

    Args:
        run_id: The run ID to verify
        table: BigQuery table name (uses config if not provided)

    Returns:
        bool: True if verification successful
    """
    if table is None:
        table = config.get("bq", {}).get(
            "monitoring_table",
            "ales-sandbox-465911.PCC_EPs.pcc_monitoring_logs"
        )

    # Ensure table is not None for BigQuery operations
    if table is None:
        logger.error("No monitoring table configured")
        return False

    dry_run = config["runtime"].get("dry_run", False)
    if dry_run:
        logger.info("[DRY RUN] Skipping monitoring log verification")
        return True

    try:
        client = bigquery.Client(location="EU")

        query = f"""
        SELECT COUNT(*) as log_count
        FROM `{table}`
        WHERE run_id = '{run_id}'
        """

        result = client.query(query).result()
        log_count = next(result).log_count

        if log_count > 0:
            logger.info(
                f"Monitoring log verification successful for run_id: {run_id}"
            )
            return True
        else:
            logger.warning(f"No monitoring log found for run_id: {run_id}")
            return False

    except Exception as e:
        logger.error(f"Monitoring log verification failed: {e}")
        return False
