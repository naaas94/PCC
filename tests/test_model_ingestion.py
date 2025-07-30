# tests/test_model_ingestion.py

import pytest
import tempfile
import os
import shutil
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import date

# Add src to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingestion.load_model_from_gcs import (
    get_latest_model_folder,
    check_today_model_exists,
    download_model_from_gcs,
    update_config_with_model_info
)


class TestModelIngestion:
    
    @pytest.fixture
    def temp_models_dir(self):
        """Create a temporary models directory for testing."""
        temp_dir = tempfile.mkdtemp()
        models_dir = os.path.join(temp_dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        yield models_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_storage_client(self):
        """Mock Google Cloud Storage client."""
        with patch('ingestion.load_model_from_gcs.storage.Client') as mock_client:
            # Mock bucket and blob operations
            mock_bucket = Mock()
            mock_client.return_value.bucket.return_value = mock_bucket
            
            # Mock blob listing
            mock_blobs = [
                Mock(name="pcc-models/v20250729_092110/", endswith=lambda x: x == '/'),
                Mock(name="pcc-models/v20250729_092253/", endswith=lambda x: x == '/'),
                Mock(name="pcc-models/v20250728_120000/", endswith=lambda x: x == '/'),
            ]
            mock_bucket.list_blobs.return_value = mock_blobs
            
            # Mock blob existence and download
            mock_model_blob = Mock()
            mock_model_blob.exists.return_value = True
            mock_model_blob.download_to_filename = Mock()
            
            mock_metadata_blob = Mock()
            mock_metadata_blob.exists.return_value = True
            mock_metadata_blob.download_to_filename = Mock()
            
            mock_bucket.blob.side_effect = lambda name: mock_model_blob if 'model.joblib' in name else mock_metadata_blob
            
            yield mock_client
    
    def test_get_latest_model_folder(self, mock_storage_client):
        """Test getting the latest model folder."""
        latest_folder = get_latest_model_folder()
        assert latest_folder == "v20250729_092253"  # Should be the latest by name
    
    def test_check_today_model_exists(self, mock_storage_client):
        """Test checking for today's model."""
        today = date.today().strftime("%Y%m%d")
        
        # Mock today's folder
        mock_bucket = mock_storage_client.return_value.bucket.return_value
        mock_blobs = [
            Mock(name=f"pcc-models/v{today}_120000/", endswith=lambda x: x == '/'),
        ]
        mock_bucket.list_blobs.return_value = mock_blobs
        
        today_folder = check_today_model_exists()
        assert today_folder == f"v{today}_120000"
    
    def test_check_today_model_not_exists(self, mock_storage_client):
        """Test when today's model doesn't exist."""
        # Mock no today's folders
        mock_bucket = mock_storage_client.return_value.bucket.return_value
        mock_blobs = [
            Mock(name="pcc-models/v20250728_120000/", endswith=lambda x: x == '/'),
        ]
        mock_bucket.list_blobs.return_value = mock_blobs
        
        today_folder = check_today_model_exists()
        assert today_folder is None
    
    @patch('joblib.load')
    def test_download_model_from_gcs(self, mock_joblib_load, mock_storage_client, temp_models_dir):
        """Test downloading model from GCS."""
        # Mock successful model load
        mock_joblib_load.return_value = Mock()
        
        success, model_path = download_model_from_gcs(
            "v20250729_092110",
            local_models_dir=temp_models_dir
        )
        
        assert success is True
        assert model_path == os.path.join(temp_models_dir, "model.joblib")
    
    def test_update_config_with_model_info(self, temp_models_dir):
        """Test updating config with model information."""
        # Create test metadata
        metadata = {
            "model_version": "v20250729_092110",
            "embedding_model": "all-MiniLM-L6-v2",
            "classifier": "LogisticRegression",
            "trained_on": "2025-07-29T09:21:10"
        }
        
        metadata_path = os.path.join(temp_models_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Create test config file
        config_path = os.path.join(temp_models_dir, "config.yaml")
        test_config = {
            'models': {
                'classifier_path': 'old/path.pkl',
                'embedding_model': 'old-model'
            }
        }
        
        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(test_config, f)
        
        success = update_config_with_model_info("v20250729_092110", config_path)
        assert success is True
        
        # Verify config was updated
        with open(config_path, 'r') as f:
            import yaml
            updated_config = yaml.safe_load(f)
        
        assert updated_config['models']['classifier_path'] == 'src/models/model.joblib'
        assert updated_config['models']['model_version'] == 'v20250729_092110'
        assert updated_config['models']['embedding_model'] == 'all-MiniLM-L6-v2'
    
    def test_download_model_missing_files(self, mock_storage_client, temp_models_dir):
        """Test downloading when model files are missing."""
        # Mock missing files
        mock_bucket = mock_storage_client.return_value.bucket.return_value
        mock_model_blob = Mock()
        mock_model_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_model_blob
        
        success, model_path = download_model_from_gcs(
            "v20250729_092110",
            local_models_dir=temp_models_dir
        )
        
        assert success is False
        assert model_path == "" 