"""
Pytest configuration and fixtures for PCC Pipeline tests
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import json
import os

@pytest.fixture
def sample_data():
    """Load sample data for testing"""
    with open('tests/fixtures/sample_data.json', 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    # Convert timestamp to pandas datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client"""
    mock_client = Mock()
    mock_result = Mock()
    mock_result.to_dataframe.return_value = pd.DataFrame({
        'case_id': ['CASE_000001', 'CASE_000002'],
        'embedding_vector': [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        'timestamp': pd.to_datetime(['2025-01-01', '2025-01-02'])
    })
    mock_client.query.return_value.result.return_value = mock_result
    return mock_client

@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        "bq": {
            "source_table": "test-project.test-dataset.source_table",
            "output_table": "test-project.test-dataset.output_table"
        },
        "models": {
            "classifier_path": "src/models/pcc_v0.1.1.pkl",
            "embedding_model": "all-MiniLM-L6-v2",
            "model_version": "v0.1"
        },
        "runtime": {
            "mode": "test",
            "dry_run": True,
            "partition_date": "20250101"
        }
    }

@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing"""
    return np.random.randn(10, 584) 