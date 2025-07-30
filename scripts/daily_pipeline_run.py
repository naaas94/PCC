#!/usr/bin/env python3
"""
Daily Pipeline Run Script
Executes the complete PCC pipeline with automatic model ingestion.
This script is designed for daily automated runs.
"""

import sys
import os
import argparse
from datetime import datetime, date
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.logger import get_logger

def setup_logging():
    """Setup logging for the daily run"""
    logger = get_logger()
    
    # Also log to file
    file_handler = logging.FileHandler('daily_pipeline.log')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def run_daily_pipeline(partition_date: str = None, mode: str = "prod", force_latest: bool = True, use_sample: bool = False):
    """
    Run the daily pipeline with model ingestion.
    
    Args:
        partition_date: Partition date in YYYYMMDD format (for BigQuery)
        mode: Runtime mode (dev/prod)
        force_latest: Whether to force ingestion of latest model
        use_sample: Whether to use sample data instead of BigQuery
    """
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("STARTING DAILY PCC PIPELINE RUN")
    logger.info("=" * 60)
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mode: {mode}")
    logger.info(f"Force Latest Model: {force_latest}")
    logger.info(f"Use Sample Data: {use_sample}")
    
    if partition_date and not use_sample:
        logger.info(f"Partition Date: {partition_date}")
    elif use_sample:
        logger.info("Using sample data")
    else:
        # Use today's date if not specified
        partition_date = date.today().strftime("%Y%m%d")
        logger.info(f"Using today's partition: {partition_date}")
    
    try:
        # Step 1: Model Ingestion
        logger.info("Step 1: Checking for new models...")
        from ingestion.load_model_from_gcs import ingest_latest_model
        from inference.classifier_interface import reload_model
        
        ingestion_success = ingest_latest_model(force_latest=force_latest)
        
        if ingestion_success:
            # Reload model in memory
            reload_model()
            logger.info("Model ingestion completed successfully")
        else:
            logger.warning("Model ingestion failed, continuing with existing model")
        
        # Step 2: Run Pipeline
        logger.info("Step 2: Running inference pipeline...")
        
        # Import the pipeline functions directly
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        
        # Import the functions from the run_pipeline module
        from scripts.run_pipeline import run_pipeline_with_bigquery, run_pipeline_with_sample_data
        
        if use_sample:
            # Run with sample data
            df_result = run_pipeline_with_sample_data(
                force_latest=force_latest,
                skip_ingestion=True  # Already ingested above
            )
        elif partition_date:
            # Run with BigQuery data
            df_result = run_pipeline_with_bigquery(
                partition_date=partition_date,
                mode=mode,
                force_latest=force_latest,
                skip_ingestion=True  # Already ingested above
            )
        else:
            # Run with sample data as fallback
            df_result = run_pipeline_with_sample_data(
                force_latest=force_latest,
                skip_ingestion=True  # Already ingested above
            )
        
        # Step 3: Log Results
        logger.info("Step 3: Logging results...")
        if df_result is not None and len(df_result) > 0:
            logger.info("Pipeline completed successfully")
            logger.info(f"   Processed {len(df_result)} cases")
            logger.info(f"   Model version: {df_result['model_version'].iloc[0] if 'model_version' in df_result.columns else 'unknown'}")
            
            # Log prediction distribution
            if 'predicted_label' in df_result.columns:
                label_counts = df_result['predicted_label'].value_counts()
                logger.info("   Prediction distribution:")
                for label, count in label_counts.items():
                    percentage = (count / len(df_result)) * 100
                    logger.info(f"     {label}: {count} ({percentage:.1f}%)")
        else:
            logger.warning("Pipeline completed but no results generated")
        
        logger.info("=" * 60)
        logger.info("DAILY PIPELINE RUN COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Daily pipeline run failed: {str(e)}")
        logger.error("=" * 60)
        logger.error("DAILY PIPELINE RUN FAILED")
        logger.error("=" * 60)
        raise

def main():
    parser = argparse.ArgumentParser(description="Run daily PCC pipeline with model ingestion")
    parser.add_argument("--partition", help="Partition date in YYYYMMDD format (for BigQuery)")
    parser.add_argument("--mode", default="prod", choices=["dev", "prod"], 
                       help="Runtime mode")
    parser.add_argument("--force-latest", action="store_true", default=True,
                       help="Force ingestion of latest model (default: True)")
    parser.add_argument("--no-force-latest", action="store_true",
                       help="Don't force latest model ingestion")
    parser.add_argument("--sample", action="store_true", default=False,
                       help="Run pipeline with sample data instead of BigQuery")
    
    args = parser.parse_args()
    
    # Handle force_latest logic
    force_latest = args.force_latest and not args.no_force_latest
    
    try:
        success = run_daily_pipeline(
            partition_date=args.partition,
            mode=args.mode,
            force_latest=force_latest,
            use_sample=args.sample
        )
        
        if success:
            print("Daily pipeline run completed successfully")
            sys.exit(0)
        else:
            print("Daily pipeline run failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error in daily pipeline run: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 