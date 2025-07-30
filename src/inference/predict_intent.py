# src/inference/predict_intent.py

import pandas as pd
from tqdm import tqdm
from utils.logger import get_logger
from .classifier_interface import predict

logger = get_logger()


def predict_batch(df: pd.DataFrame, chunk_size: int = 100) -> pd.DataFrame:
    """
    Predict intent for a batch of cases using the loaded model.
    
    Args:
        df: DataFrame with embedding vectors
        chunk_size: Number of cases to process in each chunk
        
    Returns:
        DataFrame with predictions added
    """
    results = []
    failed = 0

    for start in tqdm(range(0, len(df), chunk_size), desc="Predicting", unit="chunk"):
        chunk = df.iloc[start:start + chunk_size]
        
        for _, row in chunk.iterrows():
            try:
                prediction = predict(
                    row["embedding_vector"], 
                    metadata={"case_id": row["case_id"]}
                )
                results.append({
                    "case_id": row["case_id"],
                    "predicted_label": prediction["predicted_label"],
                    "confidence": prediction["confidence"],
                    "timestamp": row.get("timestamp", pd.Timestamp.now())
                })
            except Exception as e:
                logger.error(f"Prediction failed for case_id {row['case_id']}: {e}")
                failed += 1

    logger.info(f"Prediction complete: {len(results)} successful, {failed} failed.")
    return pd.DataFrame(results)
