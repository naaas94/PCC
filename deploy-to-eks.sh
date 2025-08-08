#!/bin/bash

# PCC EKS Deployment Script
# This script automates the deployment of the PCC pipeline to EKS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="pcc-system"
IMAGE_NAME="pcc-pipeline"
AWS_REGION=${AWS_REGION:-"us-west-2"}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-""}

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check if connected to EKS cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Not connected to Kubernetes cluster"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        log_error "AWS_ACCOUNT_ID environment variable is required"
        exit 1
    fi
    
    ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    ECR_REPOSITORY="${ECR_REGISTRY}/${IMAGE_NAME}"
    
    # Build image
    log_info "Building Docker image..."
    docker build -t ${IMAGE_NAME}:latest .
    
    # Login to ECR
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
    
    # Tag image
    log_info "Tagging image..."
    docker tag ${IMAGE_NAME}:latest ${ECR_REPOSITORY}:latest
    
    # Push image
    log_info "Pushing image to ECR..."
    docker push ${ECR_REPOSITORY}:latest
    
    log_info "Image pushed successfully: ${ECR_REPOSITORY}:latest"
}

update_k8s_manifests() {
    log_info "Updating Kubernetes manifests..."
    
    # Update image in deployment files
    sed -i.bak "s|image: ${IMAGE_NAME}:latest|image: ${ECR_REPOSITORY}:latest|g" k8s/deployment.yaml
    sed -i.bak "s|image: ${IMAGE_NAME}:latest|image: ${ECR_REPOSITORY}:latest|g" k8s/cronjob.yaml
    sed -i.bak "s|image: ${IMAGE_NAME}:latest|image: ${ECR_REPOSITORY}:latest|g" k8s/job.yaml
    
    # Update service account ARN if provided
    if [ ! -z "$AWS_ACCOUNT_ID" ]; then
        sed -i.bak "s|YOUR_AWS_ACCOUNT_ID|${AWS_ACCOUNT_ID}|g" k8s/namespace.yaml
    fi
    
    log_info "Kubernetes manifests updated"
}

deploy_to_eks() {
    log_info "Deploying to EKS..."
    
    # Create namespace and service account
    log_info "Creating namespace and service account..."
    kubectl apply -f k8s/namespace.yaml
    
    # Create ConfigMap and Secret
    log_info "Creating ConfigMap and Secret..."
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secret.yaml
    
    # Deploy CronJob
    log_info "Deploying CronJob..."
    kubectl apply -f k8s/cronjob.yaml
    
    # Optional: Deploy manual job for testing
    if [ "$1" = "--with-manual-job" ]; then
        log_info "Deploying manual job..."
        kubectl apply -f k8s/job.yaml
    fi
    
    log_info "Deployment completed successfully"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check namespace
    if kubectl get namespace ${NAMESPACE} &> /dev/null; then
        log_info "Namespace ${NAMESPACE} created successfully"
    else
        log_error "Failed to create namespace ${NAMESPACE}"
        exit 1
    fi
    
    # Check CronJob
    if kubectl get cronjob -n ${NAMESPACE} &> /dev/null; then
        log_info "CronJob deployed successfully"
    else
        log_error "Failed to deploy CronJob"
        exit 1
    fi
    
    # Check ConfigMap and Secret
    if kubectl get configmap -n ${NAMESPACE} &> /dev/null; then
        log_info "ConfigMap created successfully"
    else
        log_error "Failed to create ConfigMap"
        exit 1
    fi
    
    if kubectl get secret -n ${NAMESPACE} &> /dev/null; then
        log_info "Secret created successfully"
    else
        log_error "Failed to create Secret"
        exit 1
    fi
    
    log_info "Deployment verification completed"
}

show_status() {
    log_info "Current deployment status:"
    echo ""
    kubectl get all -n ${NAMESPACE}
    echo ""
    kubectl get cronjob -n ${NAMESPACE}
    echo ""
    kubectl get jobs -n ${NAMESPACE}
}

cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f k8s/*.bak
}

# Main execution
main() {
    log_info "Starting PCC EKS deployment..."
    
    # Parse arguments
    WITH_MANUAL_JOB=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --with-manual-job)
                WITH_MANUAL_JOB=true
                shift
                ;;
            --help)
                echo "Usage: $0 [--with-manual-job]"
                echo "  --with-manual-job  Also deploy manual job for testing"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute deployment steps
    check_prerequisites
    build_and_push_image
    update_k8s_manifests
    
    if [ "$WITH_MANUAL_JOB" = true ]; then
        deploy_to_eks --with-manual-job
    else
        deploy_to_eks
    fi
    
    verify_deployment
    show_status
    cleanup
    
    log_info "PCC EKS deployment completed successfully!"
    log_info "Next steps:"
    log_info "1. Monitor the CronJob: kubectl get cronjob -n ${NAMESPACE}"
    log_info "2. Check logs: kubectl logs -n ${NAMESPACE} -l app=pcc-pipeline"
    log_info "3. Verify BigQuery writes: Check the monitoring tables"
}

# Run main function
main "$@"
