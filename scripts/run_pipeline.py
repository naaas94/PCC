#!/usr/bin/env python3
"""
PCC Pipeline Runner
Executes the complete Privacy Case Classifier pipeline with configurable data sources.
"""

import argparse
import pandas as pd
import json
import os
import sys
from datetime import datetime
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.config import load_config
from utils.logger import get_logger
from utils.schema_validator import validate_schema

def setup_gcp_credentials():
    """Setup GCP credentials from AWS Secrets Manager"""
    import os
    import json
    
    gcp_json = os.environ.get('GCP_SA_JSON')
    print(f"GCP_SA_JSON exists: {gcp_json is not None}")
    if gcp_json:
        print(f"First 50 chars: {gcp_json[:50]}...")
        try:
            # Parse the JSON string from Secrets Manager
            credentials_data = json.loads(gcp_json)
            
            # Write to the file that GOOGLE_APPLICATION_CREDENTIALS points to
            creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/tmp/gcp-sa.json')
            with open(creds_path, 'w') as f:
                json.dump(credentials_data, f)
            
            print(f"✓ GCP credentials written to {creds_path}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse GCP credentials JSON: {e}")
            return False
    else:
        print("❌ GCP_SA_JSON environment variable not found")
        return False

def check_and_ingest_model(force_latest: bool = False, skip_ingestion: bool = False):
    """
    Check for new models and ingest if available.
    
    Args:
        force_latest: If True, get the latest model regardless of date
        skip_ingestion: If True, skip model ingestion entirely
    
    Returns:
        bool: True if model ingestion was successful or skipped, False otherwise
    """
    if skip_ingestion:
        logger = get_logger()
        logger.info("Model ingestion skipped by user request")
        return True
    
    try:
        from ingestion.load_model_from_gcs import ingest_latest_model
        from inference.classifier_interface import reload_model
        
        logger = get_logger()
        logger.info("Checking for new models in GCS...")
        
        # Ingest the latest model
        success = ingest_latest_model(force_latest=force_latest)
        
        if success:
            # Reload the model in memory
            reload_model()
            logger.info("Model ingestion completed successfully")
            return True
        else:
            logger.warning("Model ingestion failed, continuing with existing model")
            return False
            
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error during model ingestion: {e}")
        logger.warning("Continuing with existing model")
        return False

def load_sample_data():
    """Load synthetic sample data for demonstration"""
    try:
        with open('tests/fixtures/sample_data.json', 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except FileNotFoundError:
        print("❌ Sample data not found. Run 'python scripts/generate_sample_data.py' first.")
        sys.exit(1)

def run_pipeline_with_sample_data(force_latest: bool = False, skip_ingestion: bool = False):
    """Execute pipeline with synthetic data"""
    logger = get_logger()
    
    print("🚀 Running PCC Pipeline with Sample Data")
    print("=" * 50)
    
    # Check and ingest new model
    print("🔍 Checking for new models...")
    model_ingestion_success = check_and_ingest_model(force_latest=force_latest, skip_ingestion=skip_ingestion)
    if model_ingestion_success:
        print("   ✓ Model ingestion completed")
    else:
        print("   ⚠️  Model ingestion failed, continuing with existing model")
    
    # Load configuration
    config = load_config("dev")
    logger.info("Configuration loaded")
    
    # Load sample data
    print("📊 Loading sample data...")
    df_raw = load_sample_data()
    if 'timestamp' in df_raw.columns:
        df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'], errors='raise')
    print(f"   ✓ Loaded {len(df_raw)} sample cases")
    
    # Validate input schema
    print("🔍 Validating input schema...")
    validate_schema(df_raw, schema_path="schemas/input_schema.json")
    print("   ✓ Input schema validated")
    
    # Preprocessing
    print("⚙️  Preprocessing embeddings...")
    from preprocessing.embed_text import validate_embeddings, truncate_embeddings_to_model_dimensions
    
    # For sample data, use 584 dimensions (model expects 584)
    # For BigQuery data, use 588 dimensions and then truncate
    df_valid = validate_embeddings(df_raw, expected_dim=584)
    print(f"   ✓ Validated {len(df_valid)} embeddings")
    
    # Only truncate if we have embeddings with more than 584 dimensions
    if len(df_valid) > 0:
        sample_embedding = df_valid.iloc[0]['embedding_vector']
        if len(sample_embedding) > 584:
            print("🔧 Fixing feature mismatch...")
            df_valid = truncate_embeddings_to_model_dimensions(df_valid, target_dim=584)
            print(f"   ✓ Truncated embeddings to 584 dimensions")
        else:
            print("   ✓ Embeddings already match model dimensions")
    else:
        print("   ⚠️  No valid embeddings found")
    
    # Inference
    print("🤖 Running inference...")
    from inference.classifier_interface import predict
    
    predictions = []
    for _, row in df_valid.iterrows():
        embedding = np.array(row['embedding_vector'])
        pred = predict(embedding)
        predictions.append({
            'case_id': row['case_id'],
            **pred
        })
    
    df_preds = pd.DataFrame(predictions)
    print(f"   ✓ Generated {len(df_preds)} predictions")
    
    # Postprocessing
    print("📝 Formatting output...")
    from postprocessing.format_output import format_predictions
    df_formatted = format_predictions(df_preds, schema_path="schemas/output_schema.json")
    print("   ✓ Output formatted")
    
    # Validate output schema
    print("🔍 Validating output schema...")
    validate_schema(df_formatted, schema_path="schemas/output_schema.json")
    print("   ✓ Output schema validated")
    
    # Output to BigQuery (if not dry run)
    if config["runtime"].get("dry_run", False):
        print("💡 Dry run mode - skipping BigQuery write")
        display_results(df_formatted, config)
    else:
        print("📤 Writing to BigQuery...")
        from output.write_to_bq import write_to_bigquery, verify_bigquery_write
        success = write_to_bigquery(df_formatted)
        if success:
            print("   ✓ Successfully wrote to BigQuery")
            # Verify the write operation
            verify_success = verify_bigquery_write(df_formatted)
            if verify_success:
                print("   ✓ BigQuery write verified")
            else:
                print("   ⚠️  BigQuery write verification failed")
        else:
            print("   ❌ Failed to write to BigQuery")
        
        display_results(df_formatted, config)
    
    # Log pipeline run to monitoring
    import time
    partition_date = config["runtime"]["partition_date"]
    partition_date = str(partition_date)
    if len(partition_date) == 8 and partition_date.isdigit():
        partition_date = f"{partition_date[:4]}-{partition_date[4:6]}-{partition_date[6:]}"
    log_pipeline_run(config, partition_date, len(df_raw), len(df_valid), len(df_formatted), time.time())
    
    return df_formatted

def run_pipeline_with_bigquery(partition_date: str, mode: str = "dev", force_latest: bool = False, skip_ingestion: bool = False):
    """Execute pipeline with BigQuery data"""
    import time
    
    logger = get_logger()
    config = load_config(mode)
    start_time = time.time()

    logger.info("Starting PCC pipeline with BigQuery data")
    logger.info(f"Partition date: {partition_date}")

    # Check and ingest new model
    logger.info("Checking for new models...")
    model_ingestion_success = check_and_ingest_model(force_latest=force_latest, skip_ingestion=skip_ingestion)
    if model_ingestion_success:
        logger.info("Model ingestion completed successfully")
    else:
        logger.warning("Model ingestion failed, continuing with existing model")

    # Ingestion
    from ingestion.load_from_bq import load_partitioned_data
    df_raw = load_partitioned_data(partition_date)
    validate_schema(df_raw, schema_path="schemas/input_schema.json")
    logger.info(f"Loaded {len(df_raw)} rows from BigQuery snapshot")

    # Preprocessing
    from preprocessing.embed_text import validate_embeddings, truncate_embeddings_to_model_dimensions
    df_valid = validate_embeddings(df_raw)
    logger.info(f"Validated {len(df_valid)} embeddings")
    
    # Fix feature mismatch by truncating to model dimensions
    df_valid = truncate_embeddings_to_model_dimensions(df_valid, target_dim=584)
    logger.info(f"Truncated embeddings to 584 dimensions")

    # Inference
    from inference.predict_intent import predict_batch
    df_preds = predict_batch(df_valid, chunk_size=2000)
    logger.info(f"Predicted {len(df_preds)} cases")

    # Postprocessing
    from postprocessing.format_output import format_predictions
    df_formatted = format_predictions(df_preds, schema_path="schemas/output_schema.json")
    validate_schema(df_formatted, schema_path="schemas/output_schema.json")
    logger.info("Output schema validated")

    # Output
    if config["runtime"].get("dry_run", False):
        display_results(df_formatted, config)
    else:
        from output.write_to_bq import write_to_bigquery, verify_bigquery_write
        success = write_to_bigquery(df_formatted)
        if success:
            logger.info("Predictions written to BigQuery successfully")
            # Verify the write operation
            verify_success = verify_bigquery_write(df_formatted)
            if not verify_success:
                logger.warning("BigQuery write verification failed")
        else:
            logger.error("Failed to write predictions to BigQuery")
            status = "failed"
    
    # Monitoring
    log_pipeline_run(config, partition_date, len(df_raw), len(df_valid), len(df_formatted), start_time)
    
    return df_formatted

def display_results(df: pd.DataFrame, config: dict):
    """Display pipeline results summary"""
    print("\n📈 Results Summary:")
    print("=" * 50)
    print(f"Total cases processed: {len(df)}")
    print(f"Model version: {df['model_version'].iloc[0]}")
    print(f"Embedding model: {df['embedding_model'].iloc[0]}")
    
    # Prediction distribution
    label_counts = df['predicted_label'].value_counts()
    print(f"\nPrediction distribution:")
    for label, count in label_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {label}: {count} ({percentage:.1f}%)")
    
    # Confidence statistics
    avg_confidence = df['confidence'].mean()
    print(f"\nAverage confidence: {avg_confidence:.3f}")
    
    # Sample predictions
    print(f"\nSample predictions:")
    print(df[['case_id', 'predicted_label', 'confidence']].head())
    
    print("\n✅ Pipeline completed successfully!")
    
    if config["runtime"].get("dry_run", False):
        print("💡 This was a dry run. Set DRY_RUN=true to prevent writing to BigQuery.")

def log_pipeline_run(config: dict, partition_date: str, total_cases: int, 
                    passed_validation: int, output_cases: int, start_time=None, status="success"):
    """Log pipeline execution to monitoring system"""
    try:
        from monitoring.log_inference_run import log_inference_run, verify_monitoring_log
        import time
        
        if status == "success" and output_cases > 0:
            run_status = "success"
        elif output_cases == 0:
            run_status = "empty"
        else:
            run_status = status
            
        processing_duration = time.time() - start_time if start_time else 0.0
        
        success = log_inference_run(
            partition_date=partition_date,
            model_version=config["models"].get("model_version", "unknown"),
            embedding_model=config["models"].get("embedding_model", "unknown"),
            total_cases=total_cases,
            passed_validation=passed_validation,
            dropped_cases=total_cases - passed_validation,
            status=run_status,
            notes=f"Pipeline run with status: {run_status}",
            processing_duration_seconds=processing_duration
        )
        
        if success:
            logger = get_logger()
            logger.info("Pipeline run logged to monitoring system successfully")
        else:
            logger = get_logger()
            logger.warning("Failed to log pipeline run to monitoring system")
            
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Failed to log pipeline run: {e}")

def main():
    # Add this debug code at the very beginning
    import os
    print("=== STARTUP DEBUG ===")
    print(f"GCP_SA_JSON exists: {os.environ.get('GCP_SA_JSON') is not None}")
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")
    
    if os.environ.get('GCP_SA_JSON'):
        print(f"GCP_SA_JSON length: {len(os.environ.get('GCP_SA_JSON'))}")
        print(f"First 100 chars: {os.environ.get('GCP_SA_JSON')[:100]}")
    
    # Call setup function
    if not setup_gcp_credentials():
        print("Failed to setup GCP credentials")
        sys.exit(1)
    
    # Check if file was created
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/tmp/gcp-sa.json')
    if os.path.exists(creds_path):
        print(f"✓ Credentials file exists at {creds_path}")
        with open(creds_path, 'r') as f:
            content = f.read()
            print(f"File size: {len(content)} characters")
    else:
        print(f"❌ Credentials file NOT found at {creds_path}")
    
    parser = argparse.ArgumentParser(description="Run PCC Pipeline")
    parser.add_argument("--mode", default="dev", choices=["dev", "prod"], 
                       help="Runtime mode")
    parser.add_argument("--partition", help="Partition date in YYYYMMDD format (for BigQuery)")
    parser.add_argument("--sample", action="store_true", 
                       help="Use sample data instead of BigQuery")
    parser.add_argument("--force-latest", action="store_true",
                       help="Get the latest model regardless of date")
    parser.add_argument("--skip-ingestion", action="store_true",
                       help="Skip model ingestion and use existing model")
    
    args = parser.parse_args()
    
    try:
        if args.sample or not args.partition:
            run_pipeline_with_sample_data(force_latest=args.force_latest, skip_ingestion=args.skip_ingestion)
        else:
            run_pipeline_with_bigquery(args.partition, args.mode, force_latest=args.force_latest, skip_ingestion=args.skip_ingestion)
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 