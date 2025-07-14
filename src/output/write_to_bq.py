# src/output/write_to_bq.py

from google.cloud import bigquery
import pandas as pd
from utils.logger import get_bq_logger
from utils.schema_validator import validate_schema
from config.config import load_config
import time
from typing import Optional

logger = get_bq_logger()
config = load_config()


def write_to_bigquery(df: pd.DataFrame, max_retries: int = 3) -> bool:
    """
    Write final predictions to BigQuery output table.
    Uses schema from config.yaml and respects dry_run mode.
    
    Args:
        df: DataFrame to write to BigQuery
        max_retries: Maximum number of retry attempts
        
    Returns:
        bool: True if successful, False otherwise
    """
    table_id = config["bq"]["output_table"]
    dry_run = config["runtime"].get("dry_run", False)  # Default to False for wet runs

    if dry_run:
        logger.info(f"[DRY RUN] Would write {len(df)} rows to {table_id}")
        logger.info(f"[DRY RUN] Sample data preview:")
        logger.info(df.head().to_string())
        return True

    # Validate schema before writing
    try:
        validate_schema(df, schema_path="schemas/output_schema.json")
        logger.info("Output schema validated successfully")
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False

    client = bigquery.Client()

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=False,
        ignore_unknown_values=False,
        max_bad_records=0  # Fail on any bad records
    )

    for attempt in range(max_retries):
        try:
            logger.info(f"Writing {len(df)} rows to BigQuery table: {table_id} (attempt {attempt + 1})")
            
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for the job to complete
            
            # Verify the write operation
            table = client.get_table(table_id)
            logger.info(f"Successfully wrote {len(df)} rows to BigQuery table: {table_id}")
            logger.info(f"Table now contains {table.num_rows} total rows")
            return True
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed. Data not written to BigQuery.")
                return False
    
    return False


def verify_bigquery_write(df: pd.DataFrame, table_id: Optional[str] = None) -> bool:
    """
    Verify that data was written to BigQuery by checking recent records.
    
    Args:
        df: Original DataFrame that was written
        table_id: BigQuery table ID (uses config if not provided)
        
    Returns:
        bool: True if verification successful
    """
    if table_id is None:
        table_id = config["bq"]["output_table"]
    
    dry_run = config["runtime"].get("dry_run", False)
    if dry_run:
        logger.info("[DRY RUN] Skipping BigQuery verification")
        return True
    
    try:
        client = bigquery.Client()
        
        # Query recent records to verify write
        query = f"""
        SELECT COUNT(*) as recent_count
        FROM `{table_id}`
        WHERE ingestion_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        """
        
        result = client.query(query).result()
        recent_count = next(result).recent_count
        
        logger.info(f"Found {recent_count} records written in the last hour")
        
        # Basic verification - we should have at least some recent records
        if recent_count > 0:
            logger.info("BigQuery write verification successful")
            return True
        else:
            logger.warning("No recent records found in BigQuery table")
            return False
            
    except Exception as e:
        logger.error(f"BigQuery verification failed: {e}")
        return False
