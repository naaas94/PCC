# PCC EKS Deployment Guide

## Overview

This guide covers deploying the PCC (Privacy Case Classifier) ML pipeline to Amazon EKS with full BigQuery integration, model management, and monitoring capabilities.

## System Architecture

### Pipeline Components
- **Data Ingestion**: BigQuery partitioned tables or synthetic data
- **Model Management**: Dynamic GCS model ingestion with version control
- **Preprocessing**: Embedding validation (584-dimension combined MiniLM + TF-IDF)
- **Inference**: Swappable classifier interface
- **Postprocessing**: Output formatting and schema validation
- **Output**: BigQuery writes with monitoring
- **Monitoring**: Comprehensive logging and metrics

### Trigger Logic
- **Daily CronJob**: Automated daily runs at 2 AM UTC
- **Manual Jobs**: On-demand runs for specific partitions
- **Deployment**: Long-running deployment for testing
- **Sample Mode**: Testing with synthetic data

## Prerequisites

### AWS Setup
1. **EKS Cluster**: Running EKS cluster with appropriate node groups
2. **IAM Roles**: Service account with BigQuery and GCS permissions
3. **ECR Repository**: For storing Docker images
4. **VPC Configuration**: Proper networking for external API access

### GCP Setup
1. **Service Account**: With BigQuery and GCS permissions
2. **BigQuery Tables**: Created and configured
3. **GCS Bucket**: For model storage (`pcc-datasets/pcc-models`)

### Local Setup
1. **kubectl**: Configured for your EKS cluster
2. **Docker**: For building and pushing images
3. **AWS CLI**: Configured with appropriate permissions

## Deployment Steps

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t pcc-pipeline:latest .

# Tag for ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com
docker tag pcc-pipeline:latest YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/pcc-pipeline:latest

# Push to ECR
docker push YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/pcc-pipeline:latest
```

### 2. Configure Secrets

```bash
# Create base64 encoded service account
cat gcp_service_account.json | base64 -w 0

# Update k8s/secret.yaml with the encoded content
# Replace the placeholder in gcp-service-account.json with your actual service account
```

### 3. Update Configuration

Edit `k8s/configmap.yaml`:
- Update BigQuery table names
- Set appropriate model versions
- Configure runtime parameters

### 4. Deploy to EKS

```bash
# Create namespace and service account
kubectl apply -f k8s/namespace.yaml

# Create ConfigMap and Secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy the CronJob for daily runs
kubectl apply -f k8s/cronjob.yaml

# Optional: Deploy manual job for testing
kubectl apply -f k8s/job.yaml
```

### 5. Verify Deployment

```bash
# Check namespace
kubectl get namespace pcc-system

# Check CronJob
kubectl get cronjob -n pcc-system

# Check recent jobs
kubectl get jobs -n pcc-system

# Check pod logs
kubectl logs -n pcc-system -l app=pcc-pipeline --tail=100
```

## Configuration Management

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DRY_RUN` | Enable/disable BigQuery writes | `false` | No |
| `PYTHONPATH` | Python path for imports | `/app/src` | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP service account path | `/app/config/gcp-service-account.json` | Yes |
| `PARTITION_DATE` | BigQuery partition date | `20250101` | No |
| `TZ` | Timezone for scheduling | `UTC` | No |

### Resource Requirements

#### CronJob (Daily Runs)
- **Memory**: 1Gi request, 4Gi limit
- **CPU**: 500m request, 2000m limit
- **Timeout**: 1 hour
- **Schedule**: Daily at 2 AM UTC

#### Manual Jobs
- **Memory**: 1Gi request, 4Gi limit
- **CPU**: 500m request, 2000m limit
- **Timeout**: 1 hour
- **Backoff**: 3 retries

### Volume Mounts

- **Config**: ConfigMap mounted as config.yaml
- **Secrets**: GCP service account JSON
- **Logs**: EmptyDir for temporary logs
- **Models**: EmptyDir for model caching

## Monitoring and Logging

### Kubernetes Logs

```bash
# View CronJob logs
kubectl logs -n pcc-system -l type=cronjob --tail=100

# View manual job logs
kubectl logs -n pcc-system -l type=manual-run --tail=100

# Follow logs in real-time
kubectl logs -n pcc-system -f -l app=pcc-pipeline
```

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
# Check CronJob status
kubectl get cronjob pcc-daily-pipeline -n pcc-system

# Check recent job executions
kubectl get jobs -n pcc-system

# Check pod status
kubectl get pods -n pcc-system -l app=pcc-pipeline
```

## Operations

### Manual Pipeline Runs

```bash
# Create a job for specific partition
kubectl create job --from=cronjob/pcc-daily-pipeline pcc-manual-run-$(date +%Y%m%d) -n pcc-system

# Run with specific partition
kubectl patch job pcc-manual-run -n pcc-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"pcc-manual-pipeline","env":[{"name":"PARTITION_DATE","value":"20250115"}]}]}}}}'
```

### Scaling and Performance

```bash
# Scale CronJob (if needed)
kubectl scale cronjob pcc-daily-pipeline --replicas=2 -n pcc-system

# Check resource usage
kubectl top pods -n pcc-system
```

### Troubleshooting

#### Common Issues

1. **Service Account Permissions**
   ```bash
   # Check service account
   kubectl describe secret pcc-secrets -n pcc-system
   
   # Verify GCP credentials
   kubectl exec -n pcc-system -it <pod-name> -- python -c "from google.cloud import bigquery; print('Connected')"
   ```

2. **BigQuery Connection Issues**
   ```bash
   # Check network connectivity
   kubectl exec -n pcc-system -it <pod-name> -- curl -I https://bigquery.googleapis.com
   
   # Verify service account JSON
   kubectl exec -n pcc-system -it <pod-name> -- cat /app/config/gcp-service-account.json
   ```

3. **Model Ingestion Failures**
   ```bash
   # Check GCS connectivity
   kubectl exec -n pcc-system -it <pod-name> -- python -c "from google.cloud import storage; print('GCS Connected')"
   
   # Verify model bucket access
   kubectl exec -n pcc-system -it <pod-name> -- python -c "from google.cloud import storage; client = storage.Client(); bucket = client.bucket('pcc-datasets'); print(list(bucket.list_blobs(prefix='pcc-models/')))"
   ```

#### Debug Commands

```bash
# Get detailed pod information
kubectl describe pod -n pcc-system -l app=pcc-pipeline

# Check events
kubectl get events -n pcc-system --sort-by='.lastTimestamp'

# Exec into running pod
kubectl exec -n pcc-system -it <pod-name> -- /bin/bash

# Check configuration
kubectl exec -n pcc-system -it <pod-name> -- cat /app/src/config/config.yaml
```

## Security Considerations

### IAM Roles and Permissions

1. **EKS Service Account**: Minimal required permissions
2. **GCP Service Account**: BigQuery and GCS access only
3. **Network Security**: VPC configuration for external API access
4. **Secret Management**: Kubernetes secrets for sensitive data

### Data Protection

- All sensitive data redacted in synthetic samples
- BigQuery tables with 7-day retention
- Service account with minimal required permissions
- Network isolation through VPC

## Backup and Recovery

### Data Backup
- BigQuery tables with automatic backups
- Configuration in version control
- Kubernetes manifests in version control

### Recovery Procedures

1. **Pipeline Failure**: Check logs and restart
2. **BigQuery Issues**: Verify permissions and connectivity
3. **Configuration Issues**: Restore from version control
4. **Model Issues**: Check GCS connectivity and model availability

## Maintenance

### Regular Tasks

- Monitor job execution logs
- Check BigQuery table performance
- Update dependencies as needed
- Review and rotate service account keys
- Monitor resource usage and scaling needs

### Updates

- Pull latest code changes
- Update Docker image
- Test with sample data before production
- Monitor for any breaking changes

## Integration with Existing Systems

### CI/CD Pipeline

```yaml
# Example GitHub Actions workflow
name: Deploy PCC Pipeline
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build and push Docker image
      run: |
        docker build -t pcc-pipeline .
        docker push $ECR_REGISTRY/pcc-pipeline:${{ github.sha }}
    - name: Deploy to EKS
      run: |
        kubectl set image cronjob/pcc-daily-pipeline pcc-daily-pipeline=$ECR_REGISTRY/pcc-pipeline:${{ github.sha }} -n pcc-system
```

### Monitoring Integration

- **Prometheus**: Custom metrics for pipeline execution
- **Grafana**: Dashboard for pipeline monitoring
- **AlertManager**: Alerts for job failures
- **CloudWatch**: AWS-native monitoring integration

## Support and Documentation

### Key Files
- `k8s/`: Kubernetes manifests
- `Dockerfile`: Container configuration
- `docker-compose.yml`: Local development
- `scripts/`: Pipeline execution scripts
- `src/config/`: Configuration management

### Logs and Monitoring
- Kubernetes logs: `kubectl logs -n pcc-system`
- BigQuery monitoring: `pcc_monitoring_logs` table
- Pipeline logs: Container stdout/stderr

### Contact
For issues and questions, refer to the project documentation and logs.
noteId: "87b32510744711f08a8a63d7d22aff21"
tags: []

---

