# src/ingestion/load_model_from_gcs.py

import os
import sys
import joblib
import yaml
from google.cloud import storage
from typing import Optional, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import get_logger
from config.config import load_config

logger = get_logger()
config = load_config()


def get_latest_model_folder(
    bucket_name: str = "pcc-datasets",
    folder_prefix: str = "pcc-models"
) -> Optional[str]:
    """
    Find the latest model folder in GCS based on the vYYYYMMDD_timestamp naming convention.
    Returns the folder name if found, None otherwise.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # List all blobs with the prefix
    blobs = bucket.list_blobs(prefix=folder_prefix)
    
    # Extract folder names and sort by date
    model_folders = []
    for blob in blobs:
        if blob.name.endswith('/'):
            folder_name = blob.name.rstrip('/')
            if folder_name.startswith(folder_prefix):
                model_folders.append(folder_name)
    
    if not model_folders:
        logger.warning("No model folders found in GCS")
        return None
    
    # Sort by folder name (assuming vYYYYMMDD_timestamp format)
    model_folders.sort(reverse=True)
    latest_folder = model_folders[0]
    
    # Extract just the folder name from the full path
    folder_name = os.path.basename(latest_folder)
    
    logger.info(f"Found {len(model_folders)} model folders. Latest: {folder_name}")
    return folder_name


def check_today_model_exists(
    bucket_name: str = "pcc-datasets",
    folder_prefix: str = "pcc-models"
) -> Optional[str]:
    """
    Check if a model for today's date exists in GCS.
    Returns the folder name if found, None otherwise.
    """
    from datetime import date
    
    today = date.today()
    today_date_str = today.strftime('%Y%m%d')
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # List all blobs with the prefix and find today's folders
    blobs = bucket.list_blobs(prefix=folder_prefix)
    today_folders = []
    
    for blob in blobs:
        if blob.name.endswith('/'):
            folder_name = blob.name.rstrip('/')
            if folder_name.startswith(folder_prefix):
                # Check if this folder contains today's date
                if f"v{today_date_str}" in folder_name:
                    today_folders.append(folder_name)
    
    if today_folders:
        # Sort by folder name to get the latest one
        today_folders.sort(reverse=True)
        latest_today_folder = today_folders[0]
        # Extract just the folder name from the full path
        folder_name = os.path.basename(latest_today_folder)
        logger.info(f"Found model for today: {folder_name}")
        return folder_name
    else:
        logger.info(f"No model found for today: {today_date_str}")
        return None


def download_model_from_gcs(
    folder_name: str,
    bucket_name: str = "pcc-datasets",
    folder_prefix: str = "pcc-models",
    local_models_dir: str = "src/models"
) -> Tuple[bool, str]:
    """
    Download model files from GCS to local directory.
    Returns (success, local_path).
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Create local directory if it doesn't exist
    os.makedirs(local_models_dir, exist_ok=True)
    
    # Download all files in the folder
    blobs = bucket.list_blobs(prefix=folder_name)
    downloaded_files = []
    
    for blob in blobs:
        if not blob.name.endswith('/'):  # Skip folder markers
            local_path = os.path.join(local_models_dir, os.path.basename(blob.name))
            blob.download_to_filename(local_path)
            downloaded_files.append(local_path)
            logger.info(f"Downloaded: {blob.name} -> {local_path}")
    
    if not downloaded_files:
        logger.error("No files downloaded from GCS")
        return False, ""
    
    # Verify model can be loaded
    model_temp_path = os.path.join(local_models_dir, "model.joblib")
    if os.path.exists(model_temp_path):
        try:
            # Test load the model
            joblib.load(model_temp_path)
            logger.info("Model loaded successfully for verification")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False, ""
    
    logger.info(f"Successfully downloaded {len(downloaded_files)} files")
    return True, local_models_dir


def update_config_with_model_info(
    folder_name: str,
    config_path: str = "src/config/config.yaml"
) -> bool:
    """
    Update config.yaml with model metadata from the downloaded model.
    """
    try:
        # Load current config
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        # Load model metadata
        metadata_path = "src/models/metadata.json"
        if os.path.exists(metadata_path):
            import json
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            # Update config with model info
            config['models']['model_version'] = metadata.get('model_version', 'unknown')
            config['models']['embedding_model'] = metadata.get(
                'embedding_model', 'all-MiniLM-L6-v2'
            )
            config['models']['classifier_type'] = metadata.get(
                'classifier', 'LogisticRegression'
            )
            
            # Write updated config
            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            
            logger.info("Config updated with model metadata")
            return True
        else:
            logger.warning("No metadata.yaml found, config not updated")
            return False
            
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
    try:
        logger.info("Starting model ingestion from GCS")
        
        if not force_latest:
            # Try to get today's model first
            today_folder = check_today_model_exists()
            if today_folder:
                success, local_path = download_model_from_gcs(today_folder)
                if success:
                    update_config_with_model_info(today_folder)
                    logger.info(f"Successfully ingested today's model: {today_folder}")
                    return True
        
        # Get the latest model
        latest_folder = get_latest_model_folder()
        if not latest_folder:
            logger.error("No model folders found in GCS")
            return False
        
        if not force_latest:
            logger.info("No model for today found, getting latest available model")
        
        success, local_path = download_model_from_gcs(latest_folder)
        if success:
            update_config_with_model_info(latest_folder)
            logger.info(f"Successfully ingested latest model: {latest_folder}")
            return True
        else:
            logger.error("Failed to download model from GCS")
            return False
            
    except Exception as e:
        logger.error(f"Error during model ingestion: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest latest model from GCS")
    parser.add_argument(
        "--force-latest", 
        action="store_true",
        help="Get the latest model regardless of date"
    )
    
    args = parser.parse_args()
    success = ingest_latest_model(force_latest=args.force_latest)
    exit(0 if success else 1) 