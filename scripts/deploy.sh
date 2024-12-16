#!/bin/bash
set -e

# Configuration
AWS_REGION="us-west-2"
APP_NAME="applio"
ENVIRONMENT="production"

# Check required environment variables
required_vars=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "GOOGLE_CLOUD_CREDENTIALS"
    "GCS_BUCKET_NAME"
    "TF_VAR_models_bucket"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Initialize Google Cloud credentials
echo "$GOOGLE_CLOUD_CREDENTIALS" > /tmp/google-credentials.json
export GOOGLE_APPLICATION_CREDENTIALS="/tmp/google-credentials.json"

# Get ECR repository URL
echo "Getting ECR repository URL..."
ECR_REGISTRY=$(aws ecr describe-repositories --repository-names ${APP_NAME}-tts-api --region ${AWS_REGION} --query 'repositories[0].repositoryUri' --output text || \
    aws ecr create-repository --repository-name ${APP_NAME}-tts-api --region ${AWS_REGION} --query 'repository.repositoryUri' --output text)

# Build and push Docker image
echo "Building Docker image..."
docker build -t ${APP_NAME}:latest .

echo "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

echo "Tagging and pushing image..."
docker tag ${APP_NAME}:latest ${ECR_REGISTRY}:latest
docker push ${ECR_REGISTRY}:latest

# Apply Terraform configuration
echo "Initializing Terraform..."
cd terraform
terraform init

echo "Applying Terraform configuration..."
terraform apply -auto-approve \
    -var="aws_region=${AWS_REGION}" \
    -var="environment=${ENVIRONMENT}" \
    -var="app_name=${APP_NAME}"

# Get the ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

echo "Deployment complete!"
echo "Application is accessible at: http://${ALB_DNS}"
echo "API endpoint: http://${ALB_DNS}/api/v1/tts"

# Cleanup
rm -f /tmp/google-credentials.json
