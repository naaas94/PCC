# src/ingestion/load_from_bq.py

from google.cloud import bigquery
import pandas as pd
import os
from datetime import datetime
from utils.schema_validator import validate_schema
from utils.logger import get_logger

logger = get_logger()


def load_snapshot_partition(partition_date: str, config: dict) -> pd.DataFrame:
    """
    Load the partitioned case snapshot and join with precomputed embeddings for the same day.
    Validates the resulting schema.
    """
    client = bigquery.Client(location="EU")

    # Build dynamic table names based on config + partition date
    case_table = config["bq"]["source_table"].replace("*", partition_date)
    embedding_table = f"cs-analytics-dev.vector_embeddings.snapshot_semantic_search_embeddings_{partition_date}"

    query = f"""
        SELECT 
            c.core.case_number AS case_id,
            e.embeddings_allminilm AS embedding_vector,
            c.core.request_time AS timestamp
        FROM `{case_table}` AS c
        JOIN `{embedding_table}` AS e
        ON c.core.case_number = e.case_number
        WHERE DATE(c.core.request_time) = "{partition_date[:4]}-{partition_date[4:6]}-{partition_date[6:]}"

        LIMIT 6000
    """ #5/20 added a limit to test pipeline 5/21: added where clause to ingestion query 

    logger.info(f"Running query for partition {partition_date}...")
    df = client.query(query).result().to_dataframe()
    logger.info(f"Retrieved {len(df)} rows from BigQuery.")

    # Validate input schema
    validate_schema(df, schema_path="schemas/input_schema.json")

    return df
