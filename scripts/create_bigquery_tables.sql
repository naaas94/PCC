-- BigQuery Table Creation Scripts for PCC System
-- Execute these scripts in BigQuery to create the inference and monitoring tables

-- 1. Inference Output Table
CREATE TABLE IF NOT EXISTS `ales-sandbox-465911.PCC_EPs.pcc_inference_output`
(
    case_id STRING NOT NULL,
    predicted_label STRING NOT NULL,
    subtype_label STRING,
    confidence FLOAT64 NOT NULL,
    model_version STRING NOT NULL,
    embedding_model STRING NOT NULL,
    inference_timestamp TIMESTAMP NOT NULL,
    prediction_notes STRING,
    ingestion_time TIMESTAMP NOT NULL
)
PARTITION BY DATE(ingestion_time)
OPTIONS(
    partition_expiration_days = 7,
    require_partition_filter = true,
    description = "PCC inference results with 7-day retention"
);

-- 2. Monitoring Log Table
CREATE TABLE IF NOT EXISTS `ales-sandbox-465911.PCC_EPs.pcc_monitoring_logs`
(
    run_id STRING NOT NULL,
    model_version STRING NOT NULL,
    embedding_model STRING NOT NULL,
    partition_date DATE NOT NULL,
    runtime_ts TIMESTAMP NOT NULL,
    status STRING NOT NULL,
    total_cases INT64 NOT NULL,
    passed_validation INT64 NOT NULL,
    dropped_cases INT64 NOT NULL,
    notes STRING,
    ingestion_time TIMESTAMP NOT NULL,
    processing_duration_seconds FLOAT64 NOT NULL,
    error_message STRING
)
PARTITION BY DATE(ingestion_time)
OPTIONS(
    partition_expiration_days = 7,
    require_partition_filter = true,
    description = "PCC pipeline monitoring logs with 7-day retention"
);

-- 3. Create indexes for better query performance (optional)
-- Note: BigQuery automatically creates indexes, but you can optimize specific query patterns

-- Index on case_id for inference table (if frequently queried by case)
-- CREATE INDEX IF NOT EXISTS idx_inference_case_id 
-- ON `ales-sandbox-465911.PCC_EPs.pcc_inference_output`(case_id);

-- Index on run_id for monitoring table
-- CREATE INDEX IF NOT EXISTS idx_monitoring_run_id 
-- ON `ales-sandbox-465911.PCC_EPs.pcc_monitoring_logs`(run_id);

-- 4. Grant permissions (adjust as needed for your environment)
-- GRANT `roles/bigquery.dataEditor` ON TABLE `ales-sandbox-465911.PCC_EPs.pcc_inference_output` TO "user:your-service-account@ales-sandbox-465911.iam.gserviceaccount.com";
-- GRANT `roles/bigquery.dataEditor` ON TABLE `ales-sandbox-465911.PCC_EPs.pcc_monitoring_logs` TO "user:your-service-account@ales-sandbox-465911.iam.gserviceaccount.com";

-- 5. Example queries to verify table creation
-- SELECT COUNT(*) as total_partitions 
-- FROM `ales-sandbox-465911.PCC_EPs.__TABLES__` 
-- WHERE table_id = 'pcc_inference_output';

-- SELECT COUNT(*) as total_partitions 
-- FROM `ales-sandbox-465911.PCC_EPs.__TABLES__` 
-- WHERE table_id = 'pcc_monitoring_logs'; 