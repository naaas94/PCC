# src/preprocessing/embed_text.py

import pandas as pd
from utils.logger import get_logger

logger = get_logger()


def truncate_embeddings_to_model_dimensions(
    df: pd.DataFrame, 
    target_dim: int = 584,  # Model expects 584 features
    debug: bool = False
) -> pd.DataFrame:
    """
    Truncate embeddings to match the model's expected dimensions.
    This is a quick fix for the feature mismatch issue.
    """
    import numpy as np
    
    logger.info(f"Truncating embeddings from {len(df)} rows to {target_dim} dimensions")
    
    truncated_rows = []
    for idx, row in df.iterrows():
        vec = row.get("embedding_vector")
        if not isinstance(vec, (list, np.ndarray)):
            if debug:
                logger.warning(f"Row {idx}: Invalid embedding type {type(vec)}")
            continue
            
        vec = np.asarray(vec)
        if len(vec) >= target_dim:
            # Truncate to target dimension
            truncated_vec = vec[:target_dim]
            row_copy = row.copy()
            row_copy['embedding_vector'] = truncated_vec
            truncated_rows.append(row_copy)
        else:
            if debug:
                logger.warning(f"Row {idx}: Embedding too short ({len(vec)} < {target_dim})")
    
    logger.info(f"Truncated {len(truncated_rows)} embeddings to {target_dim} dimensions")
    return pd.DataFrame(truncated_rows)


def validate_embeddings(
    df: pd.DataFrame, 
    expected_dim: int = 588,  # Combined MiniLM + TF-IDF embeddings (updated to match current BigQuery output)
    debug: bool = False
) -> pd.DataFrame:
    import numpy as np
    valid_rows = []
    dropped = 0

    for idx, row in df.iterrows():
        vec = row.get("embedding_vector")
        if debug:
            print(
                f"[{idx}] Type: {type(row.get('embedding_vector'))} → "
                f"Value: {str(row.get('embedding_vector'))[:100]}"
            )
        if not isinstance(vec, (list, np.ndarray)):
            if debug:
                print(f"[{idx}] Dropped: not list or ndarray → {type(vec)}")
            dropped += 1
            continue
        vec = np.asarray(vec)
        if vec.shape != (expected_dim,):
            if debug:
                print(f"[{idx}] Dropped: bad shape {vec.shape}")
            dropped += 1
            continue
        if np.isnan(vec).any():
            if debug:
                print(f"[{idx}] Dropped: contains NaNs")
            dropped += 1
            continue
        valid_rows.append(row)

    logger.info(
        f"Embedding validation complete: {len(valid_rows)} valid, {dropped} dropped"
    )
    return pd.DataFrame(valid_rows)


def check_embedding_model_version(config: dict, actual_model: str):
    """
    Optional: Validate that the embedding model used matches expected version from config.
    """
    expected_model = config["models"]["embedding_model"]
    if expected_model != actual_model:
        logger.warning(
            f"Embedding model mismatch: expected '{expected_model}', got '{actual_model}'"
        )