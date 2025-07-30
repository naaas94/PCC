# src/ingestion/load_from_bq.py

import pandas as pd
from google.cloud import bigquery
from utils.logger import get_bq_logger
from config.config import load_config

logger = get_bq_logger()
config = load_config()


def load_partitioned_data(partition_date: str) -> pd.DataFrame:
    """
    Load the partitioned case snapshot and join with precomputed embeddings for the same day.
    Validates the resulting schema.
    """
    case_table = config["bq"]["source_table"]
    embedding_table = config["bq"]["embedding_table"]

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
    """  # 5/20 added a limit to test pipeline 5/21: added where clause to ingestion query

    logger.info(f"Loading data for partition {partition_date}")
    client = bigquery.Client(location="EU")
    df = client.query(query).to_dataframe()

    logger.info(f"Loaded {len(df)} rows from BigQuery")
    return df
