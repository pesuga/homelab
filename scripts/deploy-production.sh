#!/bin/bash

# Family AI Platform Production Deployment Script
# This script orchestrates the complete production deployment process

set -euo pipefail

# Configuration
VERSION=${1:-latest}
ENVIRONMENT=${2:-production}
COMPOSE_FILE="docker-compose.prod.yml"
NAMESPACE="familyai"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ⚠️ $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check kubectl if Kubernetes deployment
    if [ "$ENVIRONMENT" = "kubernetes" ] && ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi

    log_success "Prerequisites check completed"
}

# Prepare environment
prepare_environment() {
    log "Preparing deployment environment..."

    # Create necessary directories
    mkdir -p logs
    mkdir -p uploads
    mkdir -p ai-models
    mkdir -p monitoring/data

    # Set proper permissions
    chmod 755 logs uploads ai-models monitoring/data

    # Generate secrets if not exist
    if [ ! -f .env ]; then
        log "Creating .env file from template..."
        cp .env-example .env
        log_warning "Please edit .env file with your production values before proceeding!"
    fi

    # Generate JWT secret
    if ! grep -q "JWT_SECRET_KEY=" .env; then
        log "Generating JWT secret..."
        JWT_SECRET=$(openssl rand -hex 32)
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=\"$JWT_SECRET\"/" .env
    fi

    # Generate database password
    if ! grep -q "POSTGRES_PASSWORD=" .env; then
        log "Generating database password..."
        DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=\"$DB_PASSWORD\"/" .env
    fi

    log_success "Environment preparation completed"
}

# Build application image
build_image() {
    log "Building Family AI Platform Docker image..."

    docker build \
        --tag "familyai-platform:$VERSION" \
        --tag "familyai-platform:latest" \
        ./

    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"
    else
        log_error "Docker image build failed"
        exit 1
    fi
}

# Deploy with Docker Compose
deploy_docker_compose() {
    log "Deploying with Docker Compose..."

    # Pull latest images for external services
    log "Pulling external service images..."
    docker-compose -f "$COMPOSE_FILE" pull postgres redis qdrant ollama

    # Deploy all services
    log "Starting all services..."
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30

    # Check service health
    check_service_health

    log_success "Docker Compose deployment completed"
}

# Deploy with Kubernetes
deploy_kubernetes() {
    log "Deploying to Kubernetes cluster..."

    # Create namespace
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log "Creating Kubernetes namespace..."
        kubectl create namespace "$NAMESPACE"
    fi

    # Apply secrets
    log "Applying Kubernetes secrets..."
    kubectl apply -f production/kubernetes/deployments/familyai-platform.yaml

    # Wait for deployments
    log "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment -n "$NAMESPACE" -l app.kubernetes.io/component=api
    kubectl wait --for=condition=available --timeout=600s deployment -n "$NAMESPACE" -l app.kubernetes.io/component=database

    # Check service health
    check_service_health_k8s

    log_success "Kubernetes deployment completed"
}

# Check service health
check_service_health() {
    local max_retries=30
    local retry=0

    log "Checking service health..."

    while [ $retry -lt $max_retries ]; do
        if curl -f "http://localhost:8000/api/v1/health" &> /dev/null; then
            log_success "All services are healthy"
            return 0
        fi

        retry=$((retry + 1))
        log "Attempt $retry/$max_retries: Services not ready yet..."
        sleep 10
    done

    log_error "Service health check failed after $max_retries attempts"
    return 1
}

# Check Kubernetes service health
check_service_k8s() {
    local max_retries=30
    local retry=0

    log "Checking Kubernetes service health..."

    # Get API service URL
    API_URL=$(kubectl get service familyai-api -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)

    if [ -z "$API_URL" ]; then
        API_URL="localhost:8000"
    fi

    while [ $retry -lt $max_retries ]; do
        if curl -f "http://$API_URL/api/v1/health" &> /dev/null; then
            log_success "Kubernetes services are healthy"
            return 0
        fi

        retry=$((retry + 1))
        log "Attempt $retry/$max_retries: Kubernetes services not ready yet..."
        sleep 10
    done

    log_error "Kubernetes service health check failed after $max_retries attempts"
    return 1
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    if [ "$ENVIRONMENT" = "docker-compose" ]; then
        # Wait for database to be ready
        sleep 20

        # Run migrations
        docker-compose -f "$COMPOSE_FILE" exec -T familyai-api \
            python -m core.models.database init_db

        log_success "Database migrations completed"
    elif [ "$ENVIRONMENT" = "kubernetes" ]; then
        # Run migrations in Kubernetes pod
        kubectl exec -n "$NAMESPACE" deployment/familyai-api -- \
            python -m core.models.database init_db

        log_success "Database migrations completed"
    fi
}

# Load initial data
load_initial_data() {
    log "Loading initial data..."

    # This could load default family templates, sample memories, etc.
    # For now, we'll just create a placeholder
    echo "Initial data loading placeholder" > logs/initial-data.log

    log_success "Initial data loading completed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring and observability..."

    # Create monitoring directories
    mkdir -p monitoring/{prometheus,grafana,alerts}

    # This could configure Prometheus, Grafana dashboards, alerting rules
    log_warning "Monitoring setup is basic - consider full observability stack"

    log_success "Monitoring setup completed"
}

# Run health checks
run_health_checks() {
    log "Running comprehensive health checks..."

    # API health
    if curl -f "http://localhost:8000/api/v1/health" &> /dev/null; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi

    # Service health
    services=("postgres:5432" "redis:6379" "qdrant:6333")

    for service in "${services[@]}"; do
        if nc -z localhost ${service#*:} &> /dev/null; then
            log_success "Service $service is responding"
        else
            log_warning "Service $service may not be available"
        fi
    done

    log_success "Health checks completed"
}

# Display deployment information
display_deployment_info() {
    log "Deployment Information:"
    echo "  📊 Version: $VERSION"
    echo "  🌍 Environment: $ENVIRONMENT"
    echo "  📋 Compose File: $COMPOSE_FILE"
    echo "  🔗 API URL: http://localhost:8000"
    echo ""
    echo "🚀 Access Points:"
    echo "  • API: http://localhost:8000"
    echo "  • API Docs: http://localhost:8000/docs"
    echo "  • Health Check: http://localhost:8000/api/v1/health"
    echo ""
    echo "📋 Useful Commands:"
    echo "  • View logs: docker-compose logs -f familyai-api"
    echo "  • Scale API: docker-compose up -d --scale familyai-api=3"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart services: docker-compose restart"
    echo ""
    echo "📖 Monitoring:"
    echo "  • Logs directory: ./logs/"
    echo "  • Uploads directory: ./uploads/"
    echo "  • AI Models: ./ai-models/"
}

# Main deployment function
main() {
    local start_time=$(date +%s)

    log "Starting Family AI Platform Production Deployment"
    log "Version: $VERSION, Environment: $ENVIRONMENT"

    # Run deployment steps
    check_prerequisites
    prepare_environment
    build_image

    case "$ENVIRONMENT" in
        "docker-compose"|"prod")
            deploy_docker_compose
            ;;
        "kubernetes"|"k8s")
            deploy_kubernetes
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT. Use 'docker-compose' or 'kubernetes'"
            exit 1
            ;;
    esac

    run_migrations
    load_initial_data
    setup_monitoring
    run_health_checks

    # Calculate deployment time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    log_success "Deployment completed in ${minutes}m ${seconds}s!"
    display_deployment_info

    # Post-deployment recommendations
    log ""
    log "📝 Post-Deployment Recommendations:"
    echo "   1. Configure domain name and SSL certificates"
    echo "   2. Set up external monitoring (Prometheus/Grafana)"
    echo "  echo "  3. Configure backup strategies"
    echo "  4. Review security settings"
    echo "  5. Set up log rotation"
    echo ""
    log "🎯 Next Steps:"
    echo "   • Create your first family using the API or web interface"
    echo "  • Configure voice settings and test Whisper integration"
    echo "  • Set up Matrix Element for secure family communication"
    echo "  • Explore the dashboard features and analytics"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "build")
        build_image
        ;;
    "health")
        run_health_checks
        ;;
    "migrate")
        run_migrations
        ;;
    "clean")
        log "Cleaning up deployment..."
        docker-compose -f "$COMPOSE_FILE" down -v
        log_success "Cleanup completed"
        ;;
    "logs")
        log "Showing logs..."
        docker-compose -f "$COMPOSE_FILE" logs -f familyai-api
        ;;
    "status")
        run_health_checks
        display_deployment_info
        ;;
    "help"|"-h"|"--help")
        echo "Family AI Platform Production Deployment Script"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  deploy     Deploy the platform (default)"
        echo "  build      Build Docker image only"
        echo "  health     Run health checks"
        echo "  migrate    Run database migrations"
        echo "  clean      Clean up deployment"
        echo "  logs       Show application logs"
        echo "  status     Show deployment status"
        echo "  help       Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 deploy                          # Deploy with default settings"
        echo "  $0 deploy 1.0.0                    # Deploy specific version"
        echo "  $0 build                            # Build only"
        echo "  $0 deploy kubernetes                  # Deploy to Kubernetes"
        echo ""
        exit 0
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac