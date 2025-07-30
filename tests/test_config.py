"""
Tests for configuration module
"""

import pytest
import os
import tempfile
import yaml
from unittest.mock import patch

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.config import load_config

def test_load_config_default():
    """Test loading config with default mode"""
    config = load_config()
    assert config["runtime"]["mode"] == "dev"

def test_load_config_test_mode():
    """Test loading config with test mode - uses test config file"""
    config = load_config("test")
    # Now that config.test.yaml exists, it should load test mode
    assert config["runtime"]["mode"] == "test"

def test_config_structure():
    """Test config has required structure"""
    config = load_config()
    
    # Check required sections
    assert "bq" in config
    assert "models" in config
    assert "runtime" in config
    
    # Check BigQuery config
    assert "source_table" in config["bq"]
    assert "output_table" in config["bq"]
    
    # Check models config
    assert "classifier_path" in config["models"]
    assert "embedding_model" in config["models"]
    
    # Check runtime config
    assert "mode" in config["runtime"]
    assert "dry_run" in config["runtime"]
    assert "partition_date" in config["runtime"]

@patch.dict(os.environ, {
    'BQ_SOURCE_TABLE': 'test-project.test-dataset.source',
    'BQ_OUTPUT_TABLE': 'test-project.test-dataset.output',
    'MODEL_VERSION': 'v1.0',
    'EMBEDDING_MODEL': 'test-model',
    'DRY_RUN': 'false',
    'PARTITION_DATE': '20250102'
})
def test_environment_variables():
    """Test environment variable overrides"""
    config = load_config()
    
    assert config["bq"]["source_table"] == 'test-project.test-dataset.source'
    assert config["bq"]["output_table"] == 'test-project.test-dataset.output'
    assert config["models"]["model_version"] == 'v1.0'
    assert config["models"]["embedding_model"] == 'test-model'
    assert config["runtime"]["dry_run"] == False
    assert config["runtime"]["partition_date"] == '20250102'

def test_config_file_not_found():
    """Test handling of missing config file - should fall back to base config"""
    # This test now verifies that the function handles missing files gracefully
    # by falling back to the base config.yaml
    config = load_config("nonexistent_mode")
    
    # Should still load successfully using the fallback
    assert config is not None
    assert "bq" in config
    assert "models" in config
    assert "runtime" in config 