# Homelab Infrastructure (GitOps)

This repository contains the GitOps configuration for a MicroK8s-based Kubernetes homelab managed by FluxCD.

## Core Components

- FluxCD for GitOps management
- n8n workflow automation platform
- Private container registry
- Monitoring stack (Prometheus + Grafana)
- SealedSecrets for secret management

## Repository Structure

```
homelab/
├── clusters/              # Kubernetes cluster configurations
│   └── production/       # Production environment
│       ├── apps/        # Application deployments
│       └── infrastructure/ # Core infrastructure components
├── images/               # Custom container image definitions
└── docs/                # Additional documentation
```

## Getting Started

1. Install MicroK8s and enable required addons
2. Install Flux CLI and bootstrap the cluster
3. Configure sealed-secrets for credential management
4. Deploy core infrastructure components
5. Deploy applications

For detailed setup instructions, see [SETUP.md](./docs/SETUP.md)

## Monitoring

The cluster includes a comprehensive monitoring stack:
- Prometheus for metrics collection
- Grafana for visualization
- Alert management and notification

## Security

- SealedSecrets for encrypted secret management
- Private registry for container images
- RBAC policies and network policies
- Regular security scanning

## Contributing

Please follow our Git workflow:
1. Create feature branches from main
2. Use conventional commits
3. Submit PRs for review
4. Ensure CI passes before merging
