#!/bin/bash

# Script to set up Cloudflare API token for Flux

# Check if token is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <cloudflare-api-token>"
  exit 1
fi

# Replace token in kustomization files
CF_TOKEN=$1

# Update the kustomization files with the actual token
sed -i '' "s/REPLACE_WITH_YOUR_ACTUAL_TOKEN/$CF_TOKEN/g" /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/kustomization.yaml
sed -i '' "s/REPLACE_WITH_YOUR_ACTUAL_TOKEN/$CF_TOKEN/g" /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/cert-manager/kustomization.yaml

echo "Updated kustomization files with Cloudflare API token."
echo "IMPORTANT: Do NOT commit these files to git with the actual token!"
echo "After testing, please revert the changes to avoid committing sensitive information."
echo "You can now commit and push your other changes, and Flux will reconcile them."
