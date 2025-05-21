#### actual file without the temp debug for training stuff that was happening 


# src/preprocessing/embed_text.py

import pandas as pd
import numpy as np
from utils.logger import get_logger
from config.config import load_config  # not in use for now? 

logger = get_logger()


def validate_embeddings(df: pd.DataFrame, expected_dim: int = 384) -> pd.DataFrame:
    """
    Validate that each row has a proper embedding vector:
    - List or ndarray of floats
    - Expected dimensionality
    - No NaNs or malformed vectors
    """
    valid_rows = []
    dropped = 0

    for idx, row in df.iterrows():
        vec = row.get("embedding_vector")
        if not isinstance(vec, (list, np.ndarray)):
            dropped += 1
            continue
        vec = np.asarray(vec)
        if vec.shape != (expected_dim,):
            dropped += 1
            continue
        if np.isnan(vec).any():
            dropped += 1
            continue
        valid_rows.append(row)

    logger.info(f"Embedding validation complete: {len(valid_rows)} valid, {dropped} dropped")
    return pd.DataFrame(valid_rows)


def check_embedding_model_version(config: dict, actual_model: str):
    """
    Optional: Validate that the embedding model used matches expected version from config.
    """
    expected_model = config["models"]["embedding_model"]
    if expected_model != actual_model:
        logger.warning(f"Embedding model mismatch: expected '{expected_model}', got '{actual_model}'")