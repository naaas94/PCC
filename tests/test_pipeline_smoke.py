"""
Smoke test for PCC Pipeline end-to-end functionality
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.config import load_config
from utils.schema_validator import validate_schema
from inference.classifier_interface import predict

def test_config_loading():
    """Test configuration loading"""
    config = load_config("test")
    assert "bq" in config
    assert "models" in config
    assert "runtime" in config
    assert config["runtime"]["mode"] == "test"

def test_schema_validation(sample_data):
    """Test schema validation with sample data"""
    # Test input schema
    validate_schema(sample_data, schema_path="schemas/input_schema.json")
    
    # Test output schema
    output_data = pd.DataFrame({
        'case_id': sample_data['case_id'],
        'predicted_label': ['NOT_PC'] * len(sample_data),
        'subtype_label': [None] * len(sample_data),
        'confidence': [0.8] * len(sample_data),
        'model_version': ['v0.1'] * len(sample_data),
        'embedding_model': ['all-MiniLM-L6-v2'] * len(sample_data),
        'inference_timestamp': pd.Timestamp.now(),
        'prediction_notes': ['Test prediction'] * len(sample_data),
        'ingestion_time': pd.Timestamp.now()
    })
    validate_schema(output_data, schema_path="schemas/output_schema.json")

def test_inference_interface(sample_embeddings):
    """Test inference interface"""
    # Test single prediction
    embedding = sample_embeddings[0]
    result = predict(embedding)
    
    assert "predicted_label" in result
    assert "confidence" in result
    assert "model_version" in result
    assert "embedding_model" in result
    assert "inference_timestamp" in result
    assert "prediction_notes" in result
    assert "subtype_label" in result
    
    assert isinstance(result["predicted_label"], str)
    assert isinstance(result["confidence"], float)
    assert 0 <= result["confidence"] <= 1

def test_pipeline_end_to_end(sample_data):
    """Test complete pipeline flow with sample data"""
    # Import pipeline components
    from preprocessing.embed_text import validate_embeddings
    from inference.predict_intent import predict_batch
    from postprocessing.format_output import format_predictions
    
    # Test preprocessing
    # Sample data has 584 dimensions, not 588 like BigQuery data
    df_valid = validate_embeddings(sample_data, expected_dim=584, debug=True)
    assert len(df_valid) > 0
    assert "case_id" in df_valid.columns
    assert "embedding_vector" in df_valid.columns
    
    # Test inference
    df_preds = predict_batch(df_valid, chunk_size=1000)
    assert len(df_preds) > 0
    assert "predicted_label" in df_preds.columns
    
    # Test postprocessing
    df_formatted = format_predictions(df_preds, schema_path="schemas/output_schema.json")
    assert len(df_formatted) > 0
    
    # Validate final output
    validate_schema(df_formatted, schema_path="schemas/output_schema.json")

def test_error_handling():
    """Test error handling"""
    # Test with invalid embedding
    with pytest.raises(Exception):
        predict(np.array([]))  # Empty array instead of None
    
    # Test with empty data
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError):
        validate_schema(empty_df, schema_path="schemas/input_schema.json") 