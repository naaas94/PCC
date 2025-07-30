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
            
            # Create proper Mock objects with name attributes
            def create_mock_blob(name):
                mock_blob = Mock()
                mock_blob.name = name
                mock_blob.endswith = lambda suffix: name.endswith(suffix)
                return mock_blob
            
            # Mock blob listing
            mock_blobs = [
                create_mock_blob("pcc-models/v20250729_092110/"),
                create_mock_blob("pcc-models/v20250729_092253/"),
                create_mock_blob("pcc-models/v20250728_120000/"),
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
        
        # Create proper Mock objects with name attributes
        def create_mock_blob(name):
            mock_blob = Mock()
            mock_blob.name = name
            mock_blob.endswith = lambda suffix: name.endswith(suffix)
            return mock_blob
        
        mock_blobs = [
            create_mock_blob(f"pcc-models/v{today}_120000/"),
        ]
        mock_bucket.list_blobs.return_value = mock_blobs
        
        today_folder = check_today_model_exists()
        assert today_folder == f"v{today}_120000"
    
    def test_check_today_model_not_exists(self, mock_storage_client):
        """Test when today's model doesn't exist."""
        # Mock no today's folders
        mock_bucket = mock_storage_client.return_value.bucket.return_value
        
        # Create proper Mock objects with name attributes
        def create_mock_blob(name):
            mock_blob = Mock()
            mock_blob.name = name
            mock_blob.endswith = lambda suffix: name.endswith(suffix)
            return mock_blob
        
        mock_blobs = [
            create_mock_blob("pcc-models/v20250728_120000/"),
        ]
        mock_bucket.list_blobs.return_value = mock_blobs
        
        today_folder = check_today_model_exists()
        assert today_folder is None
    
    @patch('joblib.load')
    @patch('tempfile.TemporaryDirectory')
    @patch('shutil.copy2')
    def test_download_model_from_gcs(self, mock_copy2, mock_temp_dir, mock_joblib_load, mock_storage_client, temp_models_dir):
        """Test downloading model from GCS."""
        # Mock successful model load
        mock_joblib_load.return_value = Mock()
        
        # Mock temporary directory
        mock_temp_dir.return_value.__enter__.return_value = temp_models_dir
        mock_temp_dir.return_value.__exit__.return_value = None
        
        # Mock file copy operations
        mock_copy2.return_value = None
        
        success, model_path = download_model_from_gcs(
            "v20250729_092110",
            local_models_dir=temp_models_dir
        )
        
        assert success is True
        assert model_path == os.path.join(temp_models_dir, "model.joblib")
    
    def test_update_config_with_model_info(self, temp_models_dir):
        """Test updating config with model information."""
        # Create test metadata in the expected location
        expected_metadata_path = "src/models/metadata.json"
        os.makedirs(os.path.dirname(expected_metadata_path), exist_ok=True)
        
        metadata = {
            "model_version": "v20250729_092110",
            "embedding_model": "all-MiniLM-L6-v2",
            "classifier": "LogisticRegression",
            "trained_on": "2025-07-29T09:21:10"
        }
        
        with open(expected_metadata_path, 'w') as f:
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
        
        # Clean up the metadata file we created
        if os.path.exists(expected_metadata_path):
            os.remove(expected_metadata_path)
    
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


def test_model_ingestion_integration():
    """
    Integration test function for model ingestion pipeline.
    This function can be run directly to test the complete model ingestion workflow.
    
    Usage:
        python -m pytest tests/test_model_ingestion.py::test_model_ingestion_integration -v
        or
        python tests/test_model_ingestion.py
    """
    import tempfile
    import os
    import shutil
    import json
    import yaml
    from unittest.mock import Mock, patch, MagicMock
    from datetime import date
    
    print("Starting model ingestion integration test...")
    
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    models_dir = os.path.join(temp_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    try:
        # Mock Google Cloud Storage
        with patch('ingestion.load_model_from_gcs.storage.Client') as mock_client:
            # Setup mock storage
            mock_bucket = Mock()
            mock_client.return_value.bucket.return_value = mock_bucket
            
            # Mock available model folders with proper string attributes
            today = date.today().strftime("%Y%m%d")
            
            # Create proper Mock objects with name attributes
            def create_mock_blob(name):
                mock_blob = Mock()
                mock_blob.name = name
                mock_blob.endswith = lambda suffix: name.endswith(suffix)
                return mock_blob
            
            # Use a future date that will always be the latest
            future_date = "20251231_235959"  # Future date that will always be latest
            mock_blobs = [
                create_mock_blob(f"pcc-models/v{future_date}/"),
                create_mock_blob(f"pcc-models/v{today}_120000/"),
                create_mock_blob("pcc-models/v20250729_092253/"),
                create_mock_blob("pcc-models/v20250728_120000/"),
            ]
            mock_bucket.list_blobs.return_value = mock_blobs
            
            # Mock blob operations
            mock_model_blob = Mock()
            mock_model_blob.exists.return_value = True
            mock_model_blob.download_to_filename = Mock()
            
            mock_metadata_blob = Mock()
            mock_metadata_blob.exists.return_value = True
            mock_metadata_blob.download_to_filename = Mock()
            
            mock_bucket.blob.side_effect = lambda name: mock_model_blob if 'model.joblib' in name else mock_metadata_blob
            
            # Mock joblib load and file operations
            with patch('joblib.load') as mock_joblib_load, \
                 patch('tempfile.TemporaryDirectory') as mock_temp_dir, \
                 patch('shutil.copy2') as mock_copy2:
                
                # Mock temporary directory
                mock_temp_dir.return_value.__enter__.return_value = temp_dir
                mock_temp_dir.return_value.__exit__.return_value = None
                
                # Mock file copy operations
                mock_copy2.return_value = None
                
                mock_joblib_load.return_value = Mock()
                
                # Test 1: Get latest model folder
                print("Testing get_latest_model_folder...")
                latest_folder = get_latest_model_folder()
                assert latest_folder == f"v{future_date}"
                print(f"✓ Latest model folder: {latest_folder}")
                
                # Test 2: Check today's model
                print("Testing check_today_model_exists...")
                today_folder = check_today_model_exists()
                assert today_folder == f"v{today}_120000"
                print(f"✓ Today's model folder: {today_folder}")
                
                # Test 3: Download model
                print("Testing download_model_from_gcs...")
                try:
                    success, model_path = download_model_from_gcs(
                        f"v{future_date}",
                        local_models_dir=models_dir
                    )
                    assert success is True
                    assert model_path == os.path.join(models_dir, "model.joblib")
                    print(f"✓ Model downloaded successfully to: {model_path}")
                except Exception as e:
                    print(f"❌ Download model failed: {str(e)}")
                    raise
                
                # Test 4: Update config
                print("Testing update_config_with_model_info...")
                
                # Create test metadata in the expected location
                expected_metadata_path = "src/models/metadata.json"
                os.makedirs(os.path.dirname(expected_metadata_path), exist_ok=True)
                
                metadata = {
                    "model_version": f"v{future_date}",
                    "embedding_model": "all-MiniLM-L6-v2",
                    "classifier": "LogisticRegression",
                    "trained_on": "2025-12-31T23:59:59"
                }
                
                with open(expected_metadata_path, 'w') as f:
                    json.dump(metadata, f)
                
                # Create test config
                config_path = os.path.join(models_dir, "config.yaml")
                test_config = {
                    'models': {
                        'classifier_path': 'old/path.pkl',
                        'embedding_model': 'old-model'
                    }
                }
                
                with open(config_path, 'w') as f:
                    yaml.dump(test_config, f)
                
                success = update_config_with_model_info(f"v{future_date}", config_path)
                assert success is True
                
                # Verify config was updated
                with open(config_path, 'r') as f:
                    updated_config = yaml.safe_load(f)
                
                assert updated_config['models']['classifier_path'] == 'src/models/model.joblib'
                assert updated_config['models']['model_version'] == f"v{future_date}"
                assert updated_config['models']['embedding_model'] == 'all-MiniLM-L6-v2'
                print("✓ Config updated successfully")
                
                # Clean up the metadata file we created
                if os.path.exists(expected_metadata_path):
                    os.remove(expected_metadata_path)
                
                print("\n🎉 All model ingestion tests passed successfully!")
                
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        raise
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print("✓ Temporary files cleaned up")


if __name__ == "__main__":
    # Run the integration test when script is executed directly
    test_model_ingestion_integration() 