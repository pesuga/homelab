#!/bin/bash
# Verify deployment status
# Usage: ./scripts/verify-deployment.sh <deployment-name> [namespace]

DEPLOYMENT=$1
NAMESPACE=${2:-homelab}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$DEPLOYMENT" ]; then
    echo -e "${RED}Error: Deployment name required${NC}"
    echo "Usage: $0 <deployment-name> [namespace]"
    exit 1
fi

echo -e "${YELLOW}=== Deployment Verification ===${NC}"
echo "Deployment: $DEPLOYMENT"
echo "Namespace: $NAMESPACE"
echo ""

# Check if deployment exists
if ! kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE} &> /dev/null; then
    echo -e "${RED}Deployment ${DEPLOYMENT} not found in namespace ${NAMESPACE}${NC}"
    exit 1
fi

# Deployment Status
echo -e "${YELLOW}=== Deployment Status ===${NC}"
kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE}

# Pod Status
echo -e "\n${YELLOW}=== Pod Status ===${NC}"
kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT} 2>/dev/null || \
    kubectl get pods -n ${NAMESPACE} | grep ${DEPLOYMENT}

# Service Status
echo -e "\n${YELLOW}=== Service Status ===${NC}"
kubectl get svc -n ${NAMESPACE} ${DEPLOYMENT} 2>/dev/null || echo "No service found"

# Resource Usage
echo -e "\n${YELLOW}=== Resource Usage ===${NC}"
kubectl top pods -n ${NAMESPACE} -l app=${DEPLOYMENT} 2>/dev/null || echo "Metrics not available"

# Recent Events
echo -e "\n${YELLOW}=== Recent Events ===${NC}"
kubectl get events -n ${NAMESPACE} \
    --field-selector involvedObject.name=${DEPLOYMENT} \
    --sort-by='.lastTimestamp' | tail -10

# Container Logs
echo -e "\n${YELLOW}=== Container Logs (last 20 lines) ===${NC}"
kubectl logs -n ${NAMESPACE} deployment/${DEPLOYMENT} --tail=20 2>/dev/null || \
    echo "Unable to fetch logs (deployment may not be ready)"

# Health Check
echo -e "\n${YELLOW}=== Health Check ===${NC}"
READY_PODS=$(kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT} -o json | \
    jq -r '.items[] | select(.status.conditions[] | select(.type=="Ready" and .status=="True")) | .metadata.name' | wc -l)
TOTAL_PODS=$(kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT} --no-headers | wc -l)

if [ "$READY_PODS" -eq "$TOTAL_PODS" ] && [ "$TOTAL_PODS" -gt 0 ]; then
    echo -e "${GREEN}✓ All pods ready ($READY_PODS/$TOTAL_PODS)${NC}"
else
    echo -e "${RED}✗ Some pods not ready ($READY_PODS/$TOTAL_PODS)${NC}"
fi

echo -e "\n${GREEN}Verification complete${NC}"
