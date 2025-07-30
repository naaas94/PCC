# src/ingestion/load_model_from_gcs.py

import os
import shutil
import tempfile
from datetime import datetime, date
from google.cloud import storage
from google.cloud.exceptions import NotFound
import joblib
import json
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger()


def get_latest_model_folder(bucket_name: str = "pcc-datasets", 
                           folder_prefix: str = "pcc-models") -> Optional[str]:
    """
    Find the latest model folder in GCS based on the vYYYYMMDD_timestamp naming convention.
    Returns the folder name if found, None otherwise.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # List all folders in pcc-models
    blobs = bucket.list_blobs(prefix=f"{folder_prefix}/")
    
    # Filter for folders with vYYYYMMDD_timestamp pattern
    model_folders = []
    for blob in blobs:
        if blob.name.endswith('/') and '/v' in blob.name:
            # Extract folder name from path
            folder_name = blob.name.rstrip('/').split('/')[-1]
            if folder_name.startswith('v') and '_' in folder_name:
                model_folders.append(folder_name)
    
    if not model_folders:
        logger.warning("No model folders found in GCS")
        return None
    
    # Sort by folder name (which includes timestamp)
    model_folders.sort(reverse=True)
    latest_folder = model_folders[0]
    
    logger.info(f"Found {len(model_folders)} model folders. Latest: {latest_folder}")
    return latest_folder


def check_today_model_exists(bucket_name: str = "pcc-datasets", 
                           folder_prefix: str = "pcc-models") -> Optional[str]:
    """
    Check if there's a model folder for today's date.
    Returns the folder name if found, None otherwise.
    """
    today = date.today()
    today_str = today.strftime("%Y%m%d")
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Look for folders starting with today's date
    blobs = bucket.list_blobs(prefix=f"{folder_prefix}/v{today_str}")
    
    today_folders = []
    for blob in blobs:
        if blob.name.endswith('/'):
            folder_name = blob.name.rstrip('/').split('/')[-1]
            if folder_name.startswith(f'v{today_str}'):
                today_folders.append(folder_name)
    
    if today_folders:
        # Sort to get the latest one for today
        today_folders.sort(reverse=True)
        latest_today = today_folders[0]
        logger.info(f"Found today's model folder: {latest_today}")
        return latest_today
    
    logger.info(f"No model folder found for today ({today_str})")
    return None


def download_model_from_gcs(folder_name: str, 
                          bucket_name: str = "pcc-datasets",
                          folder_prefix: str = "pcc-models",
                          local_models_dir: str = "src/models") -> Tuple[bool, str]:
    """
    Download model.joblib and metadata.json from the specified GCS folder.
    Returns (success, model_path).
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Ensure local models directory exists
    os.makedirs(local_models_dir, exist_ok=True)
    
    # Download model.joblib
    model_blob_name = f"{folder_prefix}/{folder_name}/model.joblib"
    model_blob = bucket.blob(model_blob_name)
    
    if not model_blob.exists():
        logger.error(f"Model file not found: {model_blob_name}")
        return False, ""
    
    # Download metadata.json
    metadata_blob_name = f"{folder_prefix}/{folder_name}/metadata.json"
    metadata_blob = bucket.blob(metadata_blob_name)
    
    if not metadata_blob.exists():
        logger.error(f"Metadata file not found: {metadata_blob_name}")
        return False, ""
    
    # Create temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download model.joblib
        model_temp_path = os.path.join(temp_dir, "model.joblib")
        model_blob.download_to_filename(model_temp_path)
        
        # Download metadata.json
        metadata_temp_path = os.path.join(temp_dir, "metadata.json")
        metadata_blob.download_to_filename(metadata_temp_path)
        
        # Validate the model can be loaded
        try:
            model = joblib.load(model_temp_path)
            logger.info(f"Successfully loaded model from {folder_name}")
        except Exception as e:
            logger.error(f"Failed to load model from {folder_name}: {e}")
            return False, ""
        
        # Copy files to local models directory
        model_path = os.path.join(local_models_dir, "model.joblib")
        metadata_path = os.path.join(local_models_dir, "metadata.json")
        
        shutil.copy2(model_temp_path, model_path)
        shutil.copy2(metadata_temp_path, metadata_path)
        
        logger.info(f"Model and metadata downloaded to {local_models_dir}")
        return True, model_path


def update_config_with_model_info(folder_name: str, 
                                config_path: str = "src/config/config.yaml") -> bool:
    """
    Update the config.yaml file with the new model information.
    """
    try:
        import yaml
        
        # Load current config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update model path to use the new model.joblib
        config['models']['classifier_path'] = 'src/models/model.joblib'
        
        # Add model version from folder name
        config['models']['model_version'] = folder_name
        
        # Load metadata to get additional info
        metadata_path = "src/models/metadata.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Update config with metadata info
            config['models']['embedding_model'] = metadata.get('embedding_model', 'all-MiniLM-L6-v2')
            config['models']['trained_on'] = metadata.get('trained_on', '')
            config['models']['classifier_type'] = metadata.get('classifier', 'LogisticRegression')
        
        # Write updated config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Updated config with model info from {folder_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return False


def ingest_latest_model(force_latest: bool = False) -> bool:
    """
    Main function to ingest the latest model from GCS.
    
    Args:
        force_latest: If True, get the latest model regardless of date.
                     If False, only get today's model if it exists.
    
    Returns:
        True if successful, False otherwise.
    """
    logger.info("Starting model ingestion from GCS")
    
    if force_latest:
        # Get the latest model regardless of date
        folder_name = get_latest_model_folder()
    else:
        # First check for today's model
        folder_name = check_today_model_exists()
        if not folder_name:
            logger.info("No model for today found, getting latest available model")
            folder_name = get_latest_model_folder()
    
    if not folder_name:
        logger.error("No model folders found in GCS")
        return False
    
    # Download the model
    success, model_path = download_model_from_gcs(folder_name)
    if not success:
        return False
    
    # Update configuration
    config_success = update_config_with_model_info(folder_name)
    if not config_success:
        return False
    
    logger.info(f"Successfully ingested model from {folder_name}")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest latest model from GCS")
    parser.add_argument("--force-latest", action="store_true", 
                       help="Get the latest model regardless of date")
    
    args = parser.parse_args()
    
    success = ingest_latest_model(force_latest=args.force_latest)
    exit(0 if success else 1) 