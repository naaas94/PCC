# src/output/write_to_bq.py

from google.cloud import bigquery
import pandas as pd
from utils.logger import get_logger
from config.config import load_config

logger = get_logger()
config = load_config()


def write_to_bigquery(df: pd.DataFrame):
    """
    Write final predictions to BigQuery output table.
    Uses schema from config.yaml and respects dry_run mode.
    """
    table_id = config["bq"]["output_table"]
    dry_run = config["runtime"].get("dry_run", True)

    if dry_run:
        logger.info(f"[DRY RUN] Would write {len(df)} rows to {table_id}")
        return

    client = bigquery.Client()

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=False
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for the job to complete

    logger.info(f"Wrote {len(df)} rows to BigQuery table: {table_id}")
