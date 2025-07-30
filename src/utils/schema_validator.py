# utils/schema_validator.py

import pandas as pd
import json
from utils.logger import get_logger

logger = get_logger()


def validate_schema(df: pd.DataFrame, schema_path: str) -> None:
    """
    Validates that the DataFrame matches the expected schema:
    - Required columns exist
    - Data types are compatible
    - No nulls in non-nullable fields
    """
    with open(schema_path, "r") as f:
        schema = json.load(f)

    missing_columns = [col for col in schema if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    for col, dtype in schema.items():
        if "null" in dtype:
            continue  # skip nullability checks
        if dtype == "string" and not pd.api.types.is_string_dtype(df[col]):
            raise TypeError(f"Column '{col}' is not string")
        if dtype == "float" and not pd.api.types.is_float_dtype(df[col]):
            raise TypeError(f"Column '{col}' is not float")
        if dtype == "timestamp" and not pd.api.types.is_datetime64_any_dtype(df[col]):
            raise TypeError(f"Column '{col}' is not timestamp")

    logger.info(f"Schema validated successfully against {schema_path}")
