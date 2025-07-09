# src/inference/predict_intent.py

import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import datetime
from inference.classifier_interface import predict
from utils.logger import get_logger

logger = get_logger()


def predict_batch(df: pd.DataFrame, chunk_size: int = 2000) -> pd.DataFrame:
    """
    Apply classifier predict() function to all rows in df.
    Process in chunks to reduce risk of large-batch failure.
    Returns a new DataFrame with prediction results.
    """
    results = []
    failed = 0

    for start in tqdm(range(0, len(df), chunk_size), desc="Predicting", unit="chunk"):
        end = start + chunk_size
        chunk = df.iloc[start:end]

        for _, row in chunk.iterrows():
            try:
                prediction = predict(row["embedding_vector"], metadata={"case_id": row["case_id"]})
                result = {
                    "case_id": row["case_id"],
                    **prediction
                }
                results.append(result)
            except Exception as e:
                logger.error(f"Prediction failed for case_id {row['case_id']}: {e}")
                failed += 1

    logger.info(f"Prediction complete: {len(results)} successful, {failed} failed.")
    return pd.DataFrame(results)
