# Homelab Infrastructure

K3s cluster on Asuna — managed via FluxCD.

## Services
- **Traefik** — Ingress / reverse proxy
- **Cert-Manager** — TLS certificates (Let's Encrypt)
- **n8n** — Workflow automation
- **Redis** — Cache

## Structure
```
clusters/          — Flux bootstrap
infrastructure/    — K8s manifests
  kubernetes/
    apps/          — Application deployments
    core/          — Traefik, ingress
    cert-manager/  — TLS
    certificates/  — Let's Encrypt issuers
```
