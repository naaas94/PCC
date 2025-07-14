# BigQuery Schemas and Partitioning Configuration

## Overview

This document specifies the schemas for the two main BigQuery tables in the PCC (Privacy Case Classifier) system:

1. **Inference Output Table** - Stores prediction results
2. **Monitoring Log Table** - Stores pipeline execution logs

Both tables are configured with ingestion-time partitioning and 7-day retention for optimal performance and cost management.

## 1. Inference Output Table Schema

**Table Purpose**: Stores the final prediction results for each processed case.

**Schema**:
```json
{
    "case_id": "STRING",
    "predicted_label": "STRING", 
    "subtype_label": "STRING",
    "confidence": "FLOAT64",
    "model_version": "STRING",
    "embedding_model": "STRING",
    "inference_timestamp": "TIMESTAMP",
    "prediction_notes": "STRING",
    "ingestion_time": "TIMESTAMP"
}
```

**Field Descriptions**:
- `case_id`: Unique identifier for the customer support case
- `predicted_label`: Predicted classification (PC, NOT_PC)
- `subtype_label`: Subtype classification (nullable, for future use)
- `confidence`: Prediction confidence score (0.0 to 1.0)
- `model_version`: Version of the model used for inference
- `embedding_model`: Name of the embedding model used
- `inference_timestamp`: When the prediction was made
- `prediction_notes`: Additional notes about the prediction
- `ingestion_time`: When the record was written to BigQuery (for partitioning)

## 2. Monitoring Log Table Schema

**Table Purpose**: Stores pipeline execution metadata for monitoring, debugging, and performance analysis.

**Schema**:
```json
{
    "run_id": "STRING",
    "model_version": "STRING",
    "embedding_model": "STRING", 
    "partition_date": "DATE",
    "runtime_ts": "TIMESTAMP",
    "status": "STRING",
    "total_cases": "INT64",
    "passed_validation": "INT64",
    "dropped_cases": "INT64",
    "notes": "STRING",
    "ingestion_time": "TIMESTAMP",
    "processing_duration_seconds": "FLOAT64",
    "error_message": "STRING"
}
```

**Field Descriptions**:
- `run_id`: Unique identifier for each pipeline run
- `model_version`: Version of the model used
- `embedding_model`: Name of the embedding model used
- `partition_date`: Date partition being processed (YYYY-MM-DD)
- `runtime_ts`: When the pipeline run started
- `status`: Run status (success, failed, empty)
- `total_cases`: Total number of cases processed
- `passed_validation`: Number of cases that passed validation
- `dropped_cases`: Number of cases dropped during processing
- `notes`: Additional notes about the run
- `ingestion_time`: When the log record was written to BigQuery
- `processing_duration_seconds`: Total processing time in seconds
- `error_message`: Error details if the run failed (nullable)

## 3. BigQuery Table Configuration

### Partitioning Strategy

Both tables use **ingestion-time partitioning** with the following configuration:

```sql
-- Inference Output Table
CREATE TABLE `project.dataset.pcc_inference_output`
(
    case_id STRING,
    predicted_label STRING,
    subtype_label STRING,
    confidence FLOAT64,
    model_version STRING,
    embedding_model STRING,
    inference_timestamp TIMESTAMP,
    prediction_notes STRING,
    ingestion_time TIMESTAMP
)
PARTITION BY DATE(ingestion_time)
OPTIONS(
    partition_expiration_days = 7,
    require_partition_filter = true
);

-- Monitoring Log Table  
CREATE TABLE `project.dataset.pcc_monitoring_logs`
(
    run_id STRING,
    model_version STRING,
    embedding_model STRING,
    partition_date DATE,
    runtime_ts TIMESTAMP,
    status STRING,
    total_cases INT64,
    passed_validation INT64,
    dropped_cases INT64,
    notes STRING,
    ingestion_time TIMESTAMP,
    processing_duration_seconds FLOAT64,
    error_message STRING
)
PARTITION BY DATE(ingestion_time)
OPTIONS(
    partition_expiration_days = 7,
    require_partition_filter = true
);
```

### Key Configuration Options

1. **Partitioning**: `PARTITION BY DATE(ingestion_time)`
   - Partitions data by the date when records are ingested
   - Enables efficient querying by time ranges
   - Automatic partition management

2. **Retention**: `partition_expiration_days = 7`
   - Automatically deletes partitions older than 7 days
   - Reduces storage costs
   - Maintains only recent data for analysis

3. **Query Optimization**: `require_partition_filter = true`
   - Forces queries to include partition filters
   - Prevents expensive full-table scans
   - Improves query performance and cost control

### Recommended Query Patterns

```sql
-- Query recent inference results (last 3 days)
SELECT *
FROM `project.dataset.pcc_inference_output`
WHERE DATE(ingestion_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
  AND DATE(ingestion_time) <= CURRENT_DATE();

-- Query monitoring logs for specific date range
SELECT *
FROM `project.dataset.pcc_monitoring_logs`
WHERE DATE(ingestion_time) BETWEEN '2025-01-01' AND '2025-01-07'
ORDER BY runtime_ts DESC;

-- Performance analysis query
SELECT 
    DATE(ingestion_time) as processing_date,
    COUNT(*) as total_runs,
    AVG(processing_duration_seconds) as avg_duration,
    SUM(total_cases) as total_cases_processed
FROM `project.dataset.pcc_monitoring_logs`
WHERE DATE(ingestion_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY DATE(ingestion_time)
ORDER BY processing_date DESC;
```

## 4. Implementation Notes

### Data Ingestion

The system automatically adds `ingestion_time` to all records:

```python
# In postprocessing/format_output.py
df["ingestion_time"] = pd.Timestamp.utcnow()

# In monitoring/log_inference_run.py  
row["ingestion_time"] = runtime_ts
```

### Error Handling

- Failed pipeline runs are logged with `status = "failed"` and error details in `error_message`
- Partial failures are tracked with `dropped_cases` count
- All monitoring data is written even if the main pipeline fails

### Performance Considerations

- Batch writes are used for efficiency
- Partition filters are automatically applied in queries
- 7-day retention balances data availability with storage costs
- Indexes on frequently queried fields (case_id, model_version) may be added as needed

## 5. Monitoring and Alerting

### Key Metrics to Monitor

1. **Pipeline Success Rate**: Percentage of successful runs
2. **Processing Duration**: Average and p95 processing times
3. **Data Quality**: Cases dropped vs. processed
4. **Model Performance**: Confidence score distributions
5. **Storage Costs**: Daily data volume and retention compliance

### Recommended Alerts

- Pipeline failures (status = "failed")
- Processing duration > 30 minutes
- Drop rate > 10% of total cases
- Missing data for expected partitions
- Storage quota approaching limits

---

*This configuration ensures optimal performance, cost efficiency, and data governance for the PCC inference pipeline.* 
noteId: "98848f6060a511f0b8495786f5b7ce68"
tags: []

---

 