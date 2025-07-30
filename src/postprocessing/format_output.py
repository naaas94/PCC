# src/postprocessing/format_output.py

import pandas as pd
from utils.logger import get_logger
from utils.schema_validator import validate_schema

logger = get_logger()


def format_predictions(
    df: pd.DataFrame, 
    schema_path: str = "schemas/output_schema.json"
) -> pd.DataFrame:
    """
    Format prediction results for output to BigQuery.
    Validates against output schema.
    """
    # Convert numeric labels to string labels
    # 5/21 added this as a placeholder for mvp, will change it for label_encoder layer when subtypes are introduced
    label_map = {"0": "NOT_PC", "1": "PC"}
    df["predicted_label"] = df["predicted_label"].replace(label_map).astype("string")
    
    # Ensure confidence is float
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    
    # Add ingestion timestamp
    df["ingestion_time"] = pd.Timestamp.now()
    
    # Validate against output schema
    try:
        validate_schema(df, schema_path)
        logger.info("Output schema validation passed")
    except Exception as e:
        logger.error(f"Output schema validation failed: {e}")
        raise
    
    # Ensure all required columns exist
    required_columns = ["case_id", "predicted_label", "confidence", "ingestion_time"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Select only the columns we want to output
    output_df = df[required_columns].copy()
    
    logger.info(f"Formatted prediction output with {len(df)} rows. Ready for persistence.")
    return output_df
