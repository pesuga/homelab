#!/bin/bash

# Script to apply external-dns and cert-manager resources

# Check if token is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <cloudflare-api-token>"
  exit 1
fi

# Replace token in files
CF_TOKEN=$1

# Create temporary copies with the actual token
cat /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/cloudflare-secret.yaml | sed "s/REPLACE_WITH_YOUR_ACTUAL_TOKEN/$CF_TOKEN/g" > /tmp/external-dns-secret.yaml
cat /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/cert-manager/cloudflare-secret.yaml | sed "s/REPLACE_WITH_YOUR_ACTUAL_TOKEN/$CF_TOKEN/g" > /tmp/cert-manager-secret.yaml

# Apply secrets with the real token
kubectl apply -f /tmp/external-dns-secret.yaml
kubectl apply -f /tmp/cert-manager-secret.yaml

# Clean up temporary files
rm /tmp/external-dns-secret.yaml /tmp/cert-manager-secret.yaml

# Apply the rest of the resources
kubectl apply -f /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/namespace.yaml
kubectl apply -f /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/helmrepository.yaml
kubectl apply -f /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/release.yaml
kubectl apply -f /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/cert-manager/clusterissuer.yaml

echo "Done! Checking external-dns deployment..."
kubectl get pods -n external-dns
echo "Checking cert-manager resources..."
kubectl get clusterissuer
