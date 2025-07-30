#!/usr/bin/env python3
# scripts/ingest_and_run_pipeline.py

import sys
import os
import argparse
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingestion.load_model_from_gcs import ingest_latest_model
from inference.classifier_interface import reload_model
from utils.logger import get_logger

logger = get_logger()


def main():
    parser = argparse.ArgumentParser(description="Ingest latest model and run pipeline")
    parser.add_argument("--force-latest", action="store_true",
                       help="Get the latest model regardless of date")
    parser.add_argument("--skip-ingestion", action="store_true",
                       help="Skip model ingestion and use existing model")
    parser.add_argument("--pipeline-script", default="scripts/run_pipeline.py",
                       help="Path to the pipeline script to run after ingestion")
    
    args = parser.parse_args()
    
    # Step 1: Ingest latest model (unless skipped)
    if not args.skip_ingestion:
        logger.info("Starting model ingestion...")
        success = ingest_latest_model(force_latest=args.force_latest)
        if not success:
            logger.error("Model ingestion failed. Exiting.")
            sys.exit(1)
        
        # Reload model in memory
        reload_model()
        logger.info("Model ingestion completed successfully")
    else:
        logger.info("Skipping model ingestion, using existing model")
    
    # Step 2: Run the pipeline
    logger.info("Starting pipeline execution...")
    
    # Import and run the pipeline
    try:
        # Import the pipeline script
        pipeline_module = __import__('scripts.run_pipeline', fromlist=['main'])
        
        # Run the pipeline
        pipeline_module.main()
        
    except ImportError:
        logger.error(f"Could not import pipeline script: {args.pipeline_script}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)
    
    logger.info("Pipeline execution completed successfully")


if __name__ == "__main__":
    main() 