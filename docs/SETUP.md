# Homelab Setup Guide

## Prerequisites

1. MicroK8s Installation
```bash
sudo snap install microk8s --classic
microk8s enable dns ingress storage metrics-server
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
  --path=clusters/production \
  --personal
```

2. Install SealedSecrets Controller:
```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.19.0/controller.yaml
```

3. Configure Private Registry:
```bash
kubectl create secret docker-registry regcred \
  --docker-server=<registry-server> \
  --docker-username=$REGISTRY_USER \
  --docker-password=$REGISTRY_PASS
```

## Application Deployment

1. Deploy Core Infrastructure:
```bash
kubectl apply -k clusters/production/infrastructure
```

2. Deploy n8n:
```bash
kubectl apply -k clusters/production/apps/n8n
```

## Monitoring Access

- Grafana: http://grafana.local
- Prometheus: http://prometheus.local
- n8n: http://n8n.local

## Troubleshooting

1. Check Flux status:
```bash
flux get all
```

2. View reconciliation logs:
```bash
flux logs --all-namespaces
```

3. Debug n8n deployment:
```bash
kubectl -n n8n describe pod -l app=n8n
```

## Security Best Practices

1. Rotate SealedSecrets key periodically
2. Enable network policies
3. Regular security scans with Trivy
4. Keep Flux and components updated
