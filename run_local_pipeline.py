import argparse
import pandas as pd
from datetime import datetime

from src.ingestion.load_from_bq import load_snapshot_partition
from src.preprocessing.embed_text import validate_embeddings
from src.inference.predict_intent import predict_batch
from src.postprocessing.format_output import format_predictions
from src.output.write_to_bq import write_to_bigquery
from utils.logger import get_logger
from utils.schema_validator import validate_schema
from config.config import load_config
from src.monitoring.log_inference_run import log_inference_run



def run_pipeline(partition_date: str, mode: str = "dev"):
    logger = get_logger()
    config = load_config(mode)

    logger.info("Starting PCC local pipeline")
    logger.info(f"Partition date: {partition_date}")

    # Convert partition date to proper date object for monitoring
    partition_dt = datetime.strptime(partition_date, "%Y%m%d").date()

    # Ingestion
    df_raw = load_snapshot_partition(partition_date, config)
    validate_schema(df_raw, schema_path="schemas/input_schema.json")
    logger.info(f"Loaded {len(df_raw)} rows from BigQuery snapshot")

    # Preprocessing (just embedding validation — embeddings are precomputed)
    df_valid = validate_embeddings(df_raw, debug=True)
    logger.info(f"Validated {len(df_valid)} embeddings")

    # Inference
    df_preds = predict_batch(df_valid, chunk_size=2000)
    logger.info(f"Predicted {len(df_preds)} cases")

    # Postprocessing
    df_formatted = format_predictions(df_preds, schema_path="schemas/output_schema.json")
    validate_schema(df_formatted, schema_path="schemas/output_schema.json")
    logger.info("Output schema validated")

    # Output
    if config["runtime"].get("dry_run"):
        print(df_formatted.head())
    else:
        write_to_bigquery(df_formatted) # 5/20 changed funct to actual name and took out config arg
        logger.info("Predictions written to output table")
    #Monitoring (5/20)
    status = "unknown"
    partition_dt=partition_dt.isoformat()
    try:
        if config["runtime"].get("dry_run"):
            print(df_formatted.head())
        else:
            write_to_bigquery(df_formatted)
            logger.info("Predictions written to output table")
        status = "success" if len(df_formatted) > 0 else "empty"
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        status = "error"
    finally:
        log_inference_run(
            model_version=config["models"].get("model_version", "unknown"),
            embedding_model=config["models"].get("embedding_model", "unknown"),
            partition_date=partition_dt,  # ya corregido como date obj
            status=status,
            total_cases=len(df_raw),
            passed_validation=len(df_valid),
            dropped_cases=len(df_raw) - len(df_valid),
            notes=f"Pipeline run with status: {status}"
        )
    logger.info("Pipeline finished successfully")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PCC local pipeline")
    parser.add_argument("--partition", required=True, help="Partition date in YYYYMMDD format")
    parser.add_argument("--mode", default="dev", help="Runtime mode (dev, prod, dry_run)")
    args = parser.parse_args()

    run_pipeline(args.partition, args.mode)
