#!/bin/bash
# Quick deployment script for development iterations

set -e

TARGET=${1:-full}
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$(dirname "$0")/.."

case $TARGET in
  frontend)
    echo -e "${GREEN}📦 Building frontend...${NC}"
    cd frontend
    npm run build
    cd ..

    TAG="dev-$TIMESTAMP"
    echo -e "${GREEN}🐳 Building Docker image: frontend:$TAG${NC}"
    docker build -t 100.81.76.55:30500/family-assistant-frontend:$TAG -f frontend/Dockerfile frontend/

    echo -e "${GREEN}⬆️  Pushing to registry...${NC}"
    docker push 100.81.76.55:30500/family-assistant-frontend:$TAG

    echo -e "${GREEN}🚀 Deploying to Kubernetes...${NC}"
    kubectl set image deployment/family-assistant-frontend -n homelab \
      frontend=100.81.76.55:30500/family-assistant-frontend:$TAG

    echo -e "${GREEN}⏳ Waiting for rollout...${NC}"
    kubectl rollout status deployment/family-assistant-frontend -n homelab --timeout=120s

    echo -e "${GREEN}✅ Frontend deployed successfully!${NC}"
    echo -e "   Image: family-assistant-frontend:$TAG"
    echo -e "   URL: https://family.homelab.pesulabs.net"
    ;;

  backend)
    echo -e "${GREEN}📦 Building backend...${NC}"

    TAG="dev-$TIMESTAMP"
    echo -e "${GREEN}🐳 Building Docker image: backend:$TAG${NC}"
    docker build -t 100.81.76.55:30500/family-assistant:$TAG .

    echo -e "${GREEN}⬆️  Pushing to registry...${NC}"
    docker push 100.81.76.55:30500/family-assistant:$TAG

    echo -e "${GREEN}🚀 Deploying to Kubernetes...${NC}"
    kubectl set image deployment/family-assistant -n homelab \
      family-assistant=100.81.76.55:30500/family-assistant:$TAG

    echo -e "${GREEN}⏳ Waiting for rollout...${NC}"
    kubectl rollout status deployment/family-assistant -n homelab --timeout=120s

    echo -e "${GREEN}✅ Backend deployed successfully!${NC}"
    echo -e "   Image: family-assistant:$TAG"
    echo -e "   API: https://family-api.homelab.pesulabs.net"
    ;;

  full)
    echo -e "${YELLOW}🔄 Deploying both frontend and backend...${NC}"
    $0 backend
    $0 frontend
    ;;

  *)
    echo -e "${RED}❌ Invalid target: $TARGET${NC}"
    echo "Usage: $0 [frontend|backend|full]"
    exit 1
    ;;
esac
