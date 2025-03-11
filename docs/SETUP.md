# Homelab Setup Guide

## Prerequisites

1. MicroK8s Installation
```bash
sudo snap install microk8s --classic
microk8s enable dns ingress storage metrics-server registry
```

2. Install Flux CLI
```bash
brew install fluxcd/tap/flux
```

## Initial Setup

1. Bootstrap FluxCD:
```bash
flux bootstrap github \
  --owner=$GITHUB_USER \
  --repository=homelab \
  --branch=main \
  --path=clusters/homelab \
  --personal
```

2. Install SealedSecrets Controller:
```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.19.0/controller.yaml
```

3. Configure Registry Access:

Option 1 - GitHub Container Registry:
```bash
kubectl create secret docker-registry regcred \
  --namespace=n8n \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USER \
  --docker-password=$GITHUB_TOKEN

# Copy the secret to postgres namespace
kubectl get secret regcred --namespace=n8n -o yaml | \
  sed 's/namespace: n8n/namespace: postgres/' | \
  kubectl apply -f -
```

Option 2 - MicroK8s Local Registry:
```bash
# Registry is available at localhost:32000
# No credentials needed
```

4. Create Required Secrets:
```bash
# Create PostgreSQL secret
kubectl create secret generic postgres-secret \
  --namespace=postgres \
  --from-literal=password=$(openssl rand -base64 20)

# Save the password for n8n configuration
POSTGRES_PASSWORD=$(kubectl get secret postgres-secret -n postgres \
  -o jsonpath="{.data.password}" | base64 --decode)
```

## Application Deployment

1. Deploy PostgreSQL Database:
```bash
# Create namespace and deploy PostgreSQL
kubectl apply -k clusters/homelab/apps/postgres

# Verify deployment
kubectl -n postgres get pods
kubectl -n postgres get pvc
```

2. Deploy n8n:
```bash
# Create namespace and deploy n8n
kubectl apply -k clusters/homelab/apps/n8n

# Verify deployment
kubectl -n n8n get pods
kubectl -n n8n get ingress
```

3. Deploy Monitoring Stack:
```bash
# Deploy Prometheus and Grafana
kubectl apply -k clusters/homelab/infrastructure/monitoring

# Verify deployments
kubectl -n monitoring get pods
```

## Access Services

Services will be available at:
- n8n: http://n8n.local
- Grafana: http://grafana.local
- Prometheus: http://prometheus.local

Add these to your `/etc/hosts` file:
```bash
echo "127.0.0.1 n8n.local grafana.local prometheus.local" | sudo tee -a /etc/hosts
```

## Troubleshooting

1. Check Flux status:
```bash
flux get all
flux get helmreleases -A
```

2. View reconciliation logs:
```bash
flux logs --all-namespaces
```

3. Check application status:
```bash
# PostgreSQL
kubectl -n postgres describe pod -l app=postgres
kubectl -n postgres logs -l app=postgres

# n8n
kubectl -n n8n describe pod -l app=n8n
kubectl -n n8n logs -l app=n8n
```

## Security Best Practices

1. Rotate secrets periodically:
   - PostgreSQL password
   - Registry credentials
   - SealedSecrets key

2. Enable network policies:
```bash
microk8s enable network-policy
```

3. Regular maintenance:
   - Keep MicroK8s updated: `sudo snap refresh microk8s`
   - Update Flux: `brew upgrade fluxcd/tap/flux`
   - Run security scans: `kubectl exec -n security trivy-operator -- trivy image <image>`
