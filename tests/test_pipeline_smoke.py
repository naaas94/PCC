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
        'prediction_notes': ['Test prediction'] * len(sample_data)
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

@patch('google.cloud.bigquery.Client')
def test_pipeline_end_to_end(mock_bq_client, sample_data):
    """Test complete pipeline flow"""
    # Mock BigQuery client
    mock_client = Mock()
    mock_result = Mock()
    mock_result.to_dataframe.return_value = sample_data.head(5)
    mock_client.query.return_value.result.return_value = mock_result
    mock_bq_client.return_value = mock_client
    
    # Import pipeline components
    from ingestion.load_from_bq import load_snapshot_partition
    from preprocessing.embed_text import validate_embeddings
    from inference.predict_intent import predict_batch
    from postprocessing.format_output import format_predictions
    
    # Test ingestion
    config = load_config("test")
    df_raw = load_snapshot_partition("20250101", config)
    assert len(df_raw) > 0
    assert "case_id" in df_raw.columns
    assert "embedding_vector" in df_raw.columns
    
    # Test preprocessing
    df_valid = validate_embeddings(df_raw, debug=True)
    assert len(df_valid) > 0
    
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
        predict(None)
    
    # Test with empty data
    empty_df = pd.DataFrame()
    with pytest.raises(ValueError):
        validate_schema(empty_df, schema_path="schemas/input_schema.json") 