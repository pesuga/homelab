#!/bin/bash
# Grafana Secret Creation Script
# Purpose: Create Grafana admin credentials secret without storing password in Git
# Usage: ./scripts/secrets/create-grafana-secret.sh

set -euo pipefail

echo "=== Grafana Secret Creation ==="
echo

# Check if secret already exists
if kubectl get secret grafana-secret -n homelab &>/dev/null; then
    echo "⚠️  Secret 'grafana-secret' already exists in namespace 'homelab'"
    echo
    read -p "Do you want to recreate it (will rotate password)? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Existing secret unchanged."
        exit 0
    fi
fi

# Generate strong password
echo "🔐 Generating secure password..."
ADMIN_PASSWORD=$(openssl rand -base64 24)

# Create secret
echo "📝 Creating Kubernetes secret..."
kubectl create secret generic grafana-secret \
  --namespace=homelab \
  --from-literal=admin-password="$ADMIN_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify creation
if kubectl get secret grafana-secret -n homelab &>/dev/null; then
    echo "✅ Secret 'grafana-secret' created successfully"
    echo
    echo "🔑 Grafana admin credentials:"
    echo "   Username: admin"
    echo "   Password: $ADMIN_PASSWORD"
    echo
    echo "⚠️  IMPORTANT: Save this password securely!"
    echo "   - Store in password manager"
    echo "   - Do NOT commit to Git"
    echo
    echo "🌐 Access Grafana:"
    echo "   http://100.81.76.55:30300"
    echo
    echo "🔄 Restart Grafana to apply new credentials:"
    echo "   kubectl rollout restart deployment/grafana -n homelab"
else
    echo "❌ Failed to create secret"
    exit 1
fi
