#!/bin/bash

# Script to directly install external-dns using Helm
# This bypasses Flux and the OCI issues we're experiencing

# Check if CLOUDFLARE_API_TOKEN is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <cloudflare-api-token>"
  exit 1
fi

CLOUDFLARE_API_TOKEN=$1

# Create namespace if it doesn't exist
kubectl create namespace external-dns --dry-run=client -o yaml | kubectl apply -f -

# Add Bitnami repo and update
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install external-dns using Helm with corrected values
helm upgrade --install external-dns bitnami/external-dns \
  --namespace external-dns \
  --set provider=cloudflare \
  --set cloudflare.apiToken="${CLOUDFLARE_API_TOKEN}" \
  --set cloudflare.proxied=false \
  --set policy=sync \
  --set sources="{ingress}" \
  --set domainFilters="{pesulabs.net}" \
  --set txtOwnerId=homelab \
  --set interval=2m \
  --set logLevel=debug

# Check status
echo "Waiting for external-dns pod to be ready..."
sleep 10
kubectl get pods -n external-dns

echo "Installation complete. Check pods with: kubectl get pods -n external-dns"
echo "Check logs with: kubectl logs -n external-dns -l app.kubernetes.io/name=external-dns"
