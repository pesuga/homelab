#!/bin/bash
set -euo pipefail

# LobeChat Stack Deployment Script
# Deploys: Whisper STT + mem0 Middleware + LobeChat UI

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== LobeChat + mem0 + Whisper Deployment ===${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found${NC}"
    exit 1
fi

# Check K3s cluster
if ! kubectl get nodes &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to K3s cluster${NC}"
    exit 1
fi

# Check mem0
if ! kubectl get pods -n homelab -l app=mem0 | grep -q Running; then
    echo -e "${YELLOW}Warning: mem0 not running${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Step 1: Build middleware Docker image
echo -e "${BLUE}Step 1: Building mem0 middleware Docker image...${NC}"

cd services/lobechat-mem0-middleware

if docker build -t lobechat-mem0-middleware:latest .; then
    echo -e "${GREEN}✓ Middleware image built${NC}"
else
    echo -e "${RED}✗ Middleware build failed${NC}"
    exit 1
fi

cd ../..
echo ""

# Step 2: Deploy Whisper STT
echo -e "${BLUE}Step 2: Deploying Whisper STT...${NC}"

kubectl apply -f infrastructure/kubernetes/services/whisper/whisper.yaml

echo "Waiting for Whisper pod to be ready (this may take 2-3 minutes for model download)..."
if kubectl wait --for=condition=ready pod -l app=whisper -n homelab --timeout=300s; then
    echo -e "${GREEN}✓ Whisper deployed and ready${NC}"
else
    echo -e "${YELLOW}⚠ Whisper deployment taking longer than expected${NC}"
    echo "Check status: kubectl get pods -n homelab -l app=whisper"
fi

echo ""

# Step 3: Deploy mem0 Middleware
echo -e "${BLUE}Step 3: Deploying mem0 Middleware...${NC}"

kubectl apply -f infrastructure/kubernetes/services/lobechat/mem0-middleware.yaml

echo "Waiting for middleware pods to be ready..."
if kubectl wait --for=condition=ready pod -l app=lobechat-mem0-middleware -n homelab --timeout=120s; then
    echo -e "${GREEN}✓ mem0 Middleware deployed and ready${NC}"
else
    echo -e "${RED}✗ Middleware deployment failed${NC}"
    kubectl get pods -n homelab -l app=lobechat-mem0-middleware
    exit 1
fi

echo ""

# Step 4: Deploy LobeChat
echo -e "${BLUE}Step 4: Deploying LobeChat...${NC}"

kubectl apply -f infrastructure/kubernetes/services/lobechat/lobechat.yaml

echo "Waiting for LobeChat pod to be ready..."
if kubectl wait --for=condition=ready pod -l app=lobechat -n homelab --timeout=180s; then
    echo -e "${GREEN}✓ LobeChat deployed and ready${NC}"
else
    echo -e "${RED}✗ LobeChat deployment failed${NC}"
    kubectl get pods -n homelab -l app=lobechat
    exit 1
fi

echo ""

# Verification
echo -e "${BLUE}=== Deployment Summary ===${NC}"

# Get service endpoints
LOBECHAT_PORT=$(kubectl get svc lobechat-nodeport -n homelab -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")
WHISPER_PORT=$(kubectl get svc whisper-nodeport -n homelab -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")

echo ""
echo -e "${GREEN}✓ All services deployed!${NC}"
echo ""
echo "Service Status:"
kubectl get pods -n homelab -l 'app in (whisper,lobechat-mem0-middleware,lobechat)' -o wide

echo ""
echo "Access Points:"
echo -e "  LobeChat UI:  ${GREEN}http://100.81.76.55:${LOBECHAT_PORT}${NC}"
echo -e "  Whisper STT:  ${GREEN}http://100.81.76.55:${WHISPER_PORT}${NC}"
echo -e "  mem0 API:     ${GREEN}http://mem0.homelab.svc.cluster.local:8080${NC} (internal)"

echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Access LobeChat: http://100.81.76.55:${LOBECHAT_PORT}"
echo "2. Select model: gpt-oss:20b"
echo "3. Test Spanish conversation with voice input"
echo "4. Verify memory persistence across sessions"

echo ""
echo -e "${YELLOW}Monitoring:${NC}"
echo "  View logs: kubectl logs -n homelab -l app=<service> -f"
echo "  Check resources: kubectl top pods -n homelab"
echo "  Grafana: http://100.81.76.55:30300"

echo ""
echo -e "${GREEN}Deployment complete! 🎉${NC}"
