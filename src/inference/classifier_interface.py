# src/inference/classifier_interface.py

import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from config.config import load_config
from typing import Optional, Dict

config = load_config()

# Load model artifacts from paths in config
CLASSIFIER_PATH = config["models"]["classifier_path"]
# ENCODER_PATH = config["models"]["label_encoder_path"] #5/20 took it out to test pl
MODEL_VERSION = config["models"].get("model_version", "v0.1")
EMBEDDING_MODEL = config["models"].get("embedding_model", "unknown")

classifier = joblib.load(CLASSIFIER_PATH)
# label_encoder = joblib.load(ENCODER_PATH) 5/20 took it out to test pl 


def predict(embedding: np.ndarray, metadata: Optional[Dict] = None) -> dict:
    """
    Predict the privacy case label given an embedding.
    Returns structured output with metadata and confidence.
    """
    # Ensure input is 2D
    embedding = np.array(embedding).reshape(1, -1)

    predicted_label = str(classifier.predict(embedding)[0])
    # predicted_label = label_encoder.inverse_transform([predicted_idx])[0] 5/20 same update
    confidence = classifier.predict_proba(embedding).max()

    return {
        "predicted_label": predicted_label, # 5/20 changed from predicted_idx to predicted_label also changed the funct, revert for prod
        "confidence": float(confidence),
        "model_version": MODEL_VERSION,
        "embedding_model": EMBEDDING_MODEL,
        "inference_timestamp": pd.Timestamp.utcnow(),
        "prediction_notes": "LogReg v0.1 placeholder",
        "subtype_label": pd.NA  # Not used in MVP - use pandas NA for nullable string
    }
