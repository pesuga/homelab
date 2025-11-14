#!/bin/bash
# Deployment script for secure Homelab Dashboard

set -e  # Exit on error

echo "🚀 Deploying Secure Homelab Dashboard"
echo "======================================="

# Configuration
NAMESPACE="homelab"
IMAGE_REGISTRY="100.81.76.55:30500"
IMAGE_NAME="homelab-dashboard"
IMAGE_TAG="secure-$(date +%Y%m%d-%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "app/app.py" ]; then
    echo -e "${RED}❌ Error: Must run from homelab-dashboard directory${NC}"
    exit 1
fi

# Step 1: Build Docker image
echo -e "\n${YELLOW}📦 Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .

# Step 2: Tag for registry
echo -e "\n${YELLOW}🏷️  Tagging image for registry...${NC}"
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
docker tag ${IMAGE_NAME}:latest ${IMAGE_REGISTRY}/${IMAGE_NAME}:latest

# Step 3: Push to registry
echo -e "\n${YELLOW}⬆️  Pushing to registry...${NC}"
docker push ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
docker push ${IMAGE_REGISTRY}/${IMAGE_NAME}:latest

# Step 4: Initialize database schema
echo -e "\n${YELLOW}🗄️  Initializing database schema...${NC}"
echo "Connecting to PostgreSQL to create schema..."

kubectl exec -n ${NAMESPACE} -it $(kubectl get pod -n ${NAMESPACE} -l app=postgres -o jsonpath="{.items[0].metadata.name}") -- \
    psql -U homelab -d homelab < database/schema.sql 2>/dev/null || \
    echo -e "${YELLOW}⚠️  Schema may already exist, continuing...${NC}"

# Step 5: Generate strong secret if needed
echo -e "\n${YELLOW}🔐 Checking secrets...${NC}"
if kubectl get secret dashboard-secrets -n ${NAMESPACE} >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Secret 'dashboard-secrets' already exists${NC}"
    read -p "Do you want to update the secret? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete secret dashboard-secrets -n ${NAMESPACE}
        kubectl apply -f k8s/deployment.yaml
        echo -e "${GREEN}✓ Secret updated${NC}"
    fi
else
    echo -e "${YELLOW}Creating new secret...${NC}"
    kubectl apply -f k8s/deployment.yaml
    echo -e "${GREEN}✓ Secret created${NC}"
fi

# Step 6: Deploy application
echo -e "\n${YELLOW}🚢 Deploying application...${NC}"
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Step 7: Wait for deployment
echo -e "\n${YELLOW}⏳ Waiting for deployment to be ready...${NC}"
kubectl rollout status deployment/homelab-dashboard -n ${NAMESPACE} --timeout=120s

# Step 8: Verify deployment
echo -e "\n${YELLOW}🔍 Verifying deployment...${NC}"
POD_NAME=$(kubectl get pod -n ${NAMESPACE} -l app=homelab-dashboard -o jsonpath="{.items[0].metadata.name}")
POD_STATUS=$(kubectl get pod ${POD_NAME} -n ${NAMESPACE} -o jsonpath="{.status.phase}")

if [ "$POD_STATUS" == "Running" ]; then
    echo -e "${GREEN}✅ Pod is running: ${POD_NAME}${NC}"

    # Check logs for initialization
    echo -e "\n${YELLOW}📋 Checking application logs...${NC}"
    kubectl logs ${POD_NAME} -n ${NAMESPACE} --tail=20

    # Test health endpoint
    echo -e "\n${YELLOW}🏥 Testing health endpoint...${NC}"
    if kubectl exec -n ${NAMESPACE} ${POD_NAME} -- wget -q -O- http://localhost:5000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
    fi
else
    echo -e "${RED}❌ Pod status: ${POD_STATUS}${NC}"
    kubectl describe pod ${POD_NAME} -n ${NAMESPACE}
    exit 1
fi

# Step 9: Display access information
echo -e "\n${GREEN}✨ Deployment Complete!${NC}"
echo "======================================="
echo -e "Dashboard URL: ${GREEN}https://dash.pesulabs.net${NC}"
echo -e "NodePort URL:  ${GREEN}http://100.81.76.55:30800${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT SECURITY NOTES:${NC}"
echo "1. Change the default password immediately after first login"
echo "2. The secret key has been generated and stored in K8s Secret"
echo "3. Review audit logs regularly: kubectl logs -n ${NAMESPACE} ${POD_NAME} | grep audit"
echo "4. Consider restricting Ingress access to Tailscale IPs only"
echo ""
echo -e "${YELLOW}📊 Monitoring:${NC}"
echo "• View logs:    kubectl logs -f -n ${NAMESPACE} ${POD_NAME}"
echo "• View events:  kubectl get events -n ${NAMESPACE} --sort-by='.lastTimestamp'"
echo "• Check status: kubectl get all -n ${NAMESPACE} -l app=homelab-dashboard"
echo ""
echo -e "${GREEN}🎉 Happy homelab-ing!${NC}"
