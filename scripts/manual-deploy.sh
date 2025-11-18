#!/bin/bash
# Manual GitOps deployment script
# Usage: ./scripts/manual-deploy.sh <service-name> [namespace]

set -e

SERVICE=$1
NAMESPACE=${2:-homelab}
MANIFEST_DIR="infrastructure/kubernetes/${SERVICE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ -z "$SERVICE" ]; then
    echo -e "${RED}Error: Service name required${NC}"
    echo "Usage: $0 <service-name> [namespace]"
    exit 1
fi

if [ ! -d "$MANIFEST_DIR" ]; then
    echo -e "${RED}Error: $MANIFEST_DIR does not exist${NC}"
    exit 1
fi

echo -e "${YELLOW}=== Manual GitOps Deployment ===${NC}"
echo "Service: $SERVICE"
echo "Namespace: $NAMESPACE"
echo "Manifest Directory: $MANIFEST_DIR"
echo ""

# Check if kustomization.yaml exists
if [ -f "${MANIFEST_DIR}/kustomization.yaml" ]; then
    echo -e "${GREEN}Using Kustomize...${NC}"
    APPLY_CMD="kubectl apply -k ${MANIFEST_DIR}"
else
    echo -e "${GREEN}Using direct apply...${NC}"
    APPLY_CMD="kubectl apply -f ${MANIFEST_DIR}/"
fi

# Show what will be applied
echo -e "\n${YELLOW}Preview of changes:${NC}"
kubectl diff -f ${MANIFEST_DIR}/ || true

# Ask for confirmation
echo -e "\n${YELLOW}Proceed with deployment? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 0
fi

# Apply manifests
echo -e "\n${GREEN}Deploying ${SERVICE}...${NC}"
eval $APPLY_CMD

# Wait for rollout if deployment exists
if kubectl get deployment ${SERVICE} -n ${NAMESPACE} &> /dev/null; then
    echo -e "\n${YELLOW}Waiting for rollout...${NC}"
    kubectl rollout status deployment/${SERVICE} -n ${NAMESPACE} --timeout=300s
else
    echo -e "\n${YELLOW}No deployment found (might be StatefulSet, DaemonSet, or other resource)${NC}"
fi

# Show final status
echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "\n${YELLOW}Pod Status:${NC}"
kubectl get pods -n ${NAMESPACE} -l app=${SERVICE} 2>/dev/null || \
    kubectl get pods -n ${NAMESPACE} | grep ${SERVICE}

echo -e "\n${YELLOW}Service Status:${NC}"
kubectl get svc -n ${NAMESPACE} ${SERVICE} 2>/dev/null || echo "No service found"

echo -e "\n${GREEN}Deployment successful!${NC}"
