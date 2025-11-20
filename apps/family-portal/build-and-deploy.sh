#!/bin/bash

# Family Assistant Build and Deploy Script
# This script builds the Docker image and deploys to Kubernetes

set -euo pipefail

# Configuration
APP_NAME="family-assistant"
DOCKER_REGISTRY="100.81.76.55:30500"
DOCKER_IMAGE="${DOCKER_REGISTRY}/${APP_NAME}"
NAMESPACE="family-assistant"
DOMAIN="family-assistant.homelab.pesulabs.net"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_success "Kubernetes cluster connection verified"
}

# Function to check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Cannot connect to Docker daemon"
        exit 1
    fi

    log_success "Docker daemon connection verified"
}

# Function to build Docker image
build_image() {
    log_info "Building Docker image for ${APP_NAME}..."

    cd "$(dirname "$0")"

    # Create .dockerignore if it doesn't exist
    if [ ! -f .dockerignore ]; then
        cat > .dockerignore << EOF
node_modules
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache
.git
.gitignore
README.md
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
coverage
.nyc_output
.cache
.parcel-cache
.DS_Store
.vscode
.idea
*.swp
*.swo
*~
EOF
        log_info "Created .dockerignore file"
    fi

    # Build the image
    if docker build -t "${DOCKER_IMAGE}:latest" .; then
        log_success "Docker image built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi
}

# Function to push Docker image
push_image() {
    log_info "Pushing Docker image to registry..."

    if docker push "${DOCKER_IMAGE}:latest"; then
        log_success "Docker image pushed successfully"
    else
        log_error "Docker push failed"
        exit 1
    fi
}

# Function to deploy to Kubernetes
deploy_k8s() {
    log_info "Deploying to Kubernetes cluster..."

    # Get the directory where this script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    K8S_DIR="${SCRIPT_DIR}/../../infrastructure/kubernetes/family-app"

    if [ ! -d "$K8S_DIR" ]; then
        log_error "Kubernetes manifests directory not found: $K8S_DIR"
        exit 1
    fi

    cd "$K8S_DIR"

    # Create namespace
    log_info "Creating namespace ${NAMESPACE}..."
    kubectl apply -f namespace.yaml

    # Apply ConfigMap
    log_info "Applying ConfigMap..."
    kubectl apply -f configmap.yaml

    # Apply middlewares
    log_info "Applying Traefik middlewares..."
    kubectl apply -f middlewares.yaml

    # Apply Service
    log_info "Applying Service..."
    kubectl apply -f service.yaml

    # Apply Deployment
    log_info "Applying Deployment..."
    kubectl apply -f deployment.yaml

    # Apply Ingress
    log_info "Applying Ingress..."
    kubectl apply -f ingress.yaml

    log_success "Kubernetes deployment completed"
}

# Function to verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl rollout status deployment/${APP_NAME} -n ${NAMESPACE} --timeout=300s

    # Check pod status
    log_info "Checking pod status..."
    kubectl get pods -n ${NAMESPACE}

    # Check service status
    log_info "Checking service status..."
    kubectl get svc -n ${NAMESPACE}

    # Check ingress status
    log_info "Checking ingress status..."
    kubectl get ingress -n ${NAMESPACE}

    # Wait a bit for DNS to propagate
    log_info "Waiting for DNS to propagate..."
    sleep 10

    # Test the application
    log_info "Testing application availability..."
    if curl -f -s "https://${DOMAIN}/health" > /dev/null; then
        log_success "Application is accessible at https://${DOMAIN}"
    else
        log_warning "Application may still be starting. Please check https://${DOMAIN} in a few moments."
    fi
}

# Function to show deployment information
show_info() {
    log_success "Deployment completed successfully!"
    echo
    echo "🌐 Application URL: https://${DOMAIN}"
    echo "📊 Kubernetes namespace: ${NAMESPACE}"
    echo "🐳 Docker image: ${DOCKER_IMAGE}:latest"
    echo
    echo "Useful commands:"
    echo "  kubectl get pods -n ${NAMESPACE}        # Check pod status"
    echo "  kubectl logs -f deployment/${APP_NAME} -n ${NAMESPACE}  # View logs"
    echo "  kubectl get ingress -n ${NAMESPACE}     # Check ingress status"
    echo "  kubectl rollout status deployment/${APP_NAME} -n ${NAMESPACE}  # Check rollout status"
    echo
}

# Main execution
main() {
    log_info "Starting Family Assistant deployment process..."

    check_kubectl
    check_docker
    build_image
    push_image
    deploy_k8s
    verify_deployment
    show_info

    log_success "🎉 Family Assistant deployment completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    "build-only")
        check_docker
        build_image
        log_success "Build completed. Use 'push' to push to registry or 'deploy' to deploy to cluster."
        ;;
    "push-only")
        check_docker
        push_image
        log_success "Push completed. Use 'deploy' to deploy to cluster."
        ;;
    "deploy-only")
        check_kubectl
        deploy_k8s
        verify_deployment
        show_info
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  (no args)  Full build, push, and deploy process"
        echo "  build-only  Build Docker image only"
        echo "  push-only   Push Docker image to registry only"
        echo "  deploy-only Deploy to Kubernetes cluster only"
        echo "  help        Show this help message"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information."
        exit 1
        ;;
esac