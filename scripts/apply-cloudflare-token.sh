#!/bin/bash

# Script to apply Cloudflare API token for external-dns

# Check if token is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <cloudflare-api-token>"
  exit 1
fi

# Set the token
export CLOUDFLARE_API_TOKEN=$1

# Replace the token in the secret
envsubst < /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/cloudflare-secret.yaml | kubectl apply -f -

# Apply the rest of the resources
kubectl apply -f /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/namespace.yaml
kubectl apply -f /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/helmrepository.yaml
kubectl apply -f /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/release.yaml

echo "Done! Checking external-dns deployment..."
kubectl get pods -n external-dns
