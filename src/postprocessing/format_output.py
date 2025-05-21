# src/postprocessing/format_output.py

import pandas as pd
from utils.schema_validator import validate_schema
from utils.logger import get_logger

logger = get_logger()


def format_predictions(df: pd.DataFrame, schema_path: str = "schemas/output_schema.json") -> pd.DataFrame:
    """
    Postprocess prediction DataFrame:
    - Validate schema and fail fast if broken
    - Ensure output column order and integrity
    - Log output status
    """
    label_map: Dict[int, str] = {0: "NOT_PC", 1: "PC"} #5/21 added this as a placeholder for mvp, will change it for label_encoder layer when subtypes are introduced
    df["predicted_label"] = df["predicted_label"].astype(int).map(label_map).astype("string")
    
    # Validate against output schema
    validate_schema(df, schema_path=schema_path)

    # Define explicit output column order
    columns = [
        "case_id",
        "predicted_label",
        "subtype_label",
        "confidence",
        "model_version",
        "embedding_model",
        "inference_timestamp",
        "prediction_notes"
    ]
    
    df = pd.DataFrame(df[columns])  # type: ignore
    
    logger.info(f"Formatted prediction output with {len(df)} rows. Ready for persistence.")
    return df
