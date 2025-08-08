# PCC EKS Deployment Script (PowerShell)
# This script automates the deployment of the PCC pipeline to EKS

param(
    [switch]$WithManualJob,
    [switch]$Help
)

# Configuration
$NAMESPACE = "pcc-system"
$IMAGE_NAME = "pcc-pipeline"
$AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-west-2" }
$AWS_ACCOUNT_ID = $env:AWS_ACCOUNT_ID

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check kubectl
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-Error "kubectl is not installed"
        exit 1
    }
    
    # Check docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "docker is not installed"
        exit 1
    }
    
    # Check AWS CLI
    if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
        Write-Error "AWS CLI is not installed"
        exit 1
    }
    
    # Check if connected to EKS cluster
    try {
        kubectl cluster-info | Out-Null
    }
    catch {
        Write-Error "Not connected to Kubernetes cluster"
        exit 1
    }
    
    Write-Info "Prerequisites check passed"
}

function Build-AndPush-Image {
    Write-Info "Building and pushing Docker image..."
    
    if (-not $AWS_ACCOUNT_ID) {
        Write-Error "AWS_ACCOUNT_ID environment variable is required"
        exit 1
    }
    
    $ECR_REGISTRY = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    $ECR_REPOSITORY = "$ECR_REGISTRY/$IMAGE_NAME"
    
    # Build image
    Write-Info "Building Docker image..."
    docker build -t ${IMAGE_NAME}:latest .
    
    # Login to ECR
    Write-Info "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
    
    # Tag image
    Write-Info "Tagging image..."
    docker tag ${IMAGE_NAME}:latest $ECR_REPOSITORY`:latest
    
    # Push image
    Write-Info "Pushing image to ECR..."
    docker push $ECR_REPOSITORY`:latest
    
    Write-Info "Image pushed successfully: $ECR_REPOSITORY`:latest"
    
    return $ECR_REPOSITORY
}

function Update-K8sManifests {
    param([string]$ECR_REPOSITORY)
    
    Write-Info "Updating Kubernetes manifests..."
    
    # Update image in deployment files
    (Get-Content k8s/deployment.yaml) -replace "image: ${IMAGE_NAME}:latest", "image: $ECR_REPOSITORY`:latest" | Set-Content k8s/deployment.yaml
    (Get-Content k8s/cronjob.yaml) -replace "image: ${IMAGE_NAME}:latest", "image: $ECR_REPOSITORY`:latest" | Set-Content k8s/cronjob.yaml
    (Get-Content k8s/job.yaml) -replace "image: ${IMAGE_NAME}:latest", "image: $ECR_REPOSITORY`:latest" | Set-Content k8s/job.yaml
    
    # Update service account ARN if provided
    if ($AWS_ACCOUNT_ID) {
        (Get-Content k8s/namespace.yaml) -replace "YOUR_AWS_ACCOUNT_ID", $AWS_ACCOUNT_ID | Set-Content k8s/namespace.yaml
    }
    
    Write-Info "Kubernetes manifests updated"
}

function Deploy-ToEKS {
    param([switch]$WithManualJob)
    
    Write-Info "Deploying to EKS..."
    
    # Create namespace and service account
    Write-Info "Creating namespace and service account..."
    kubectl apply -f k8s/namespace.yaml
    
    # Create ConfigMap and Secret
    Write-Info "Creating ConfigMap and Secret..."
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secret.yaml
    
    # Deploy CronJob
    Write-Info "Deploying CronJob..."
    kubectl apply -f k8s/cronjob.yaml
    
    # Optional: Deploy manual job for testing
    if ($WithManualJob) {
        Write-Info "Deploying manual job..."
        kubectl apply -f k8s/job.yaml
    }
    
    Write-Info "Deployment completed successfully"
}

function Test-Deployment {
    Write-Info "Verifying deployment..."
    
    # Check namespace
    try {
        kubectl get namespace $NAMESPACE | Out-Null
        Write-Info "Namespace $NAMESPACE created successfully"
    }
    catch {
        Write-Error "Failed to create namespace $NAMESPACE"
        exit 1
    }
    
    # Check CronJob
    try {
        kubectl get cronjob -n $NAMESPACE | Out-Null
        Write-Info "CronJob deployed successfully"
    }
    catch {
        Write-Error "Failed to deploy CronJob"
        exit 1
    }
    
    # Check ConfigMap and Secret
    try {
        kubectl get configmap -n $NAMESPACE | Out-Null
        Write-Info "ConfigMap created successfully"
    }
    catch {
        Write-Error "Failed to create ConfigMap"
        exit 1
    }
    
    try {
        kubectl get secret -n $NAMESPACE | Out-Null
        Write-Info "Secret created successfully"
    }
    catch {
        Write-Error "Failed to create Secret"
        exit 1
    }
    
    Write-Info "Deployment verification completed"
}

function Show-Status {
    Write-Info "Current deployment status:"
    Write-Host ""
    kubectl get all -n $NAMESPACE
    Write-Host ""
    kubectl get cronjob -n $NAMESPACE
    Write-Host ""
    kubectl get jobs -n $NAMESPACE
}

# Main execution
function Main {
    if ($Help) {
        Write-Host "Usage: .\deploy-to-eks.ps1 [-WithManualJob] [-Help]"
        Write-Host "  -WithManualJob  Also deploy manual job for testing"
        Write-Host "  -Help           Show this help message"
        exit 0
    }
    
    Write-Info "Starting PCC EKS deployment..."
    
    # Execute deployment steps
    Test-Prerequisites
    $ECR_REPOSITORY = Build-AndPush-Image
    Update-K8sManifests -ECR_REPOSITORY $ECR_REPOSITORY
    
    if ($WithManualJob) {
        Deploy-ToEKS -WithManualJob
    }
    else {
        Deploy-ToEKS
    }
    
    Test-Deployment
    Show-Status
    
    Write-Info "PCC EKS deployment completed successfully!"
    Write-Info "Next steps:"
    Write-Info "1. Monitor the CronJob: kubectl get cronjob -n $NAMESPACE"
    Write-Info "2. Check logs: kubectl logs -n $NAMESPACE -l app=pcc-pipeline"
    Write-Info "3. Verify BigQuery writes: Check the monitoring tables"
}

# Run main function
Main
