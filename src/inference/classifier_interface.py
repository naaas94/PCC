# src/inference/classifier_interface.py

import numpy as np
import pandas as pd
import joblib
import json
import os
from config.config import load_config
from typing import Optional, Dict
from utils.logger import get_logger

logger = get_logger()

# Global variables to cache model and metadata
# These are intentionally unused at module level - they're used within functions
_classifier = None  # noqa: F824
_metadata = None  # noqa: F824
_model_version = None  # noqa: F824
_embedding_model = None  # noqa: F824


def _load_model_artifacts():
    """Load model artifacts and cache them globally."""
    global _classifier, _metadata, _model_version, _embedding_model
    
    config = load_config()
    
    # Load model path from config
    classifier_path = config["models"]["classifier_path"]
    
    # Check if model file exists
    if not os.path.exists(classifier_path):
        raise FileNotFoundError(f"Model file not found: {classifier_path}")
    
    # Load the classifier
    try:
        _classifier = joblib.load(classifier_path)
        logger.info(f"Loaded classifier from {classifier_path}")
    except Exception as e:
        logger.error(f"Failed to load classifier from {classifier_path}: {e}")
        raise
    
    # Load metadata if available
    metadata_path = "src/models/metadata.json"
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                _metadata = json.load(f)
            logger.info("Loaded model metadata")
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            _metadata = {}
    else:
        logger.warning("No metadata file found")
        _metadata = {}
    
    # Get model version and embedding model from config or metadata
    _model_version = config["models"].get("model_version", "unknown")
    _embedding_model = config["models"].get("embedding_model", "unknown")
    
    # Override with metadata if available
    if _metadata:
        _model_version = _metadata.get("model_version", _model_version)
        _embedding_model = _metadata.get("embedding_model", _embedding_model)


def predict(embedding: np.ndarray, metadata: Optional[Dict] = None) -> dict:
    """
    Predict the privacy case label given an embedding.
    Returns structured output with metadata and confidence.
    """
    global _classifier, _metadata, _model_version, _embedding_model  # noqa: F824,E501
    
    # Load model if not already loaded
    if _classifier is None:
        _load_model_artifacts()
    
    # Ensure input is 2D
    embedding = np.array(embedding).reshape(1, -1)

    predicted_label = str(_classifier.predict(embedding)[0])
    confidence = _classifier.predict_proba(embedding).max()

    # Get additional info from metadata
    classifier_type = _metadata.get("classifier", "LogisticRegression") if _metadata else "LogisticRegression"
    trained_on = _metadata.get("trained_on", "") if _metadata else ""
    
    return {
        "predicted_label": predicted_label,
        "confidence": float(confidence),
        "model_version": _model_version,
        "embedding_model": _embedding_model,
        "inference_timestamp": pd.Timestamp.utcnow(),
        "prediction_notes": f"{classifier_type} model",
        "subtype_label": pd.NA,  # Not used in MVP - use pandas NA for nullable string
        "trained_on": trained_on
    }


def reload_model():
    """Force reload of the model artifacts."""
    global _classifier, _metadata, _model_version, _embedding_model  # noqa: F824,E501
    _classifier = None
    _metadata = None
    _model_version = None
    _embedding_model = None
    logger.info("Model cache cleared, will reload on next prediction")
