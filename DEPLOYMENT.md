# PCC Deployment Guide

## Overview
This guide covers deployment of the fully orchestrated PCC (Privacy Case Classifier) system with BigQuery integration and monitoring.

## Prerequisites

### BigQuery Setup
1. **Project Access**: Ensure access to BigQuery project `ales-sandbox-465911`
2. **Service Account**: Configure service account with BigQuery permissions
3. **Tables**: Create required BigQuery tables using the provided SQL script

### Environment Requirements
- Python 3.10+
- Docker (for containerized deployment)
- BigQuery CLI tools (for table management)

## Deployment Options

### Option 1: Local Development Deployment

#### 1. Environment Setup
```bash
# Clone repository
git clone <repo-url>
cd PCC

# Setup environment
make setup
make install
```

#### 2. Configuration
```bash
# Copy configuration files
cp src/config/config.yaml.example src/config/config.yaml

# Edit configuration
# Update BigQuery table names and project details
# Set dry_run=false for production writes
```

#### 3. BigQuery Tables
```bash
# Create BigQuery tables
make bq-setup

# Or manually execute:
bq query --use_legacy_sql=false < scripts/create_bigquery_tables.sql
```

#### 4. Test Deployment
```bash
# Run with sample data
make run

# Check logs
make logs

# Verify BigQuery writes
make monitor
```

### Option 2: Docker Deployment

#### 1. Build Image
```bash
# Build Docker image
docker build -t pcc-pipeline .

# Verify image
docker images | grep pcc-pipeline
```

#### 2. Run Container
```bash
# Run with sample data
docker run --rm \
  -v $(pwd)/logs:/app/logs \
  -e DRY_RUN=false \
  pcc-pipeline --sample

# Run with BigQuery data
docker run --rm \
  -v $(pwd)/logs:/app/logs \
  -e DRY_RUN=false \
  -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json \
  -v /path/to/service-account.json:/app/service-account.json \
  pcc-pipeline --partition 20250101 --mode dev
```

### Option 3: Production Deployment

#### 1. Environment Configuration
```bash
# Production environment variables
export DRY_RUN=false
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export BQ_PROJECT_ID=ales-sandbox-465911
export BQ_DATASET=PCC_EPs
```

#### 2. BigQuery Permissions
Ensure service account has the following BigQuery permissions:
- `bigquery.jobs.create`
- `bigquery.tables.getData`
- `bigquery.tables.updateData`
- `bigquery.tables.insertData`

#### 3. Production Run
```bash
# Setup production environment
make prod-setup

# Run production pipeline
make run-bq PARTITION=20250101

# Monitor execution
make monitor
```

## Configuration Management

### Environment Variables
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DRY_RUN` | Enable/disable BigQuery writes | `false` | No |
| `BQ_SOURCE_TABLE` | Override source table | Config file | No |
| `BQ_OUTPUT_TABLE` | Override output table | Config file | No |
| `PARTITION_DATE` | Override partition date | Config file | No |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account path | None | Yes |

### Configuration Files
- `src/config/config.yaml`: Main configuration
- `src/config/config.yaml.example`: Template configuration
- `.env`: Environment variables (optional)

## Monitoring and Logging

### Log Files
- `pcc_pipeline.log`: General pipeline logs
- `pcc_bigquery.log`: BigQuery operation logs

### BigQuery Monitoring
```sql
-- Check recent pipeline runs
SELECT * FROM `ales-sandbox-465911.PCC_EPs.pcc_monitoring_logs`
ORDER BY runtime_ts DESC LIMIT 10;

-- Check inference results
SELECT * FROM `ales-sandbox-465911.PCC_EPs.pcc_inference_output`
ORDER BY ingestion_time DESC LIMIT 10;
```

### Health Checks
```bash
# Check pipeline status
make logs

# Check BigQuery connectivity
python -c "from google.cloud import bigquery; client = bigquery.Client(); print('Connected')"

# Check configuration
python -c "from src.config.config import load_config; print(load_config())"
```

## Troubleshooting

### Common Issues

#### 1. BigQuery Permission Errors
```
Error: 403 POST https://bigquery.googleapis.com/upload/bigquery/v2/projects/ales-sandbox-465911/jobs?uploadType=multipart: Access Denied
```
**Solution**: Verify service account permissions and credentials

#### 2. Schema Validation Errors
```
Error: Schema validation failed
```
**Solution**: Check input data format and schema definitions

#### 3. Monitoring Log Errors
```
Error: Invalid date format
```
**Solution**: Ensure partition_date is in YYYY-MM-DD format

### Debug Commands
```bash
# Check BigQuery tables
bq ls ales-sandbox-465911:PCC_EPs

# Check service account
gcloud auth list

# Test BigQuery connection
bq query "SELECT 1"

# Check logs
tail -f pcc_pipeline.log
tail -f pcc_bigquery.log
```

## Performance Optimization

### Current Performance
- **Processing Speed**: ~0.003 seconds for 100 cases
- **BigQuery Write**: Sub-second for 100-row batches
- **Memory Usage**: Minimal (synthetic data)

### Scaling Considerations
1. **Batch Size**: Increase chunk_size for larger datasets
2. **Parallel Processing**: Implement multiprocessing for inference
3. **BigQuery Optimization**: Use streaming inserts for real-time data
4. **Resource Allocation**: Adjust memory and CPU limits

## Security Considerations

### Data Protection
- All sensitive data redacted in synthetic samples
- BigQuery tables with 7-day retention
- Service account with minimal required permissions

### Access Control
- BigQuery table-level permissions
- Service account authentication
- Environment variable protection

## Backup and Recovery

### Data Backup
- BigQuery tables with automatic backups
- Configuration files in version control
- Log files for audit trail

### Recovery Procedures
1. **Pipeline Failure**: Check logs and restart
2. **BigQuery Issues**: Verify permissions and connectivity
3. **Configuration Issues**: Restore from version control

## Maintenance

### Regular Tasks
- Monitor log files for errors
- Check BigQuery table performance
- Update dependencies as needed
- Review and rotate service account keys

### Updates
- Pull latest code changes
- Update configuration if needed
- Test with sample data before production
- Monitor for any breaking changes

## Support

### Documentation
- `README.md`: System overview and usage
- `SYSTEM_STATUS.md`: Current system status
- `WET_RUN_SETUP.md`: BigQuery integration details

### Logs and Monitoring
- Pipeline logs: `pcc_pipeline.log`
- BigQuery logs: `pcc_bigquery.log`
- Monitoring table: `pcc_monitoring_logs`

### Contact
For issues and questions, refer to the project documentation and logs. 
noteId: "10d5cec060b511f095184d3dd951ecc0"
tags: []

---

 