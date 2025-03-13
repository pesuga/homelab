# Home Lab GitOps Repository

This repository contains the GitOps configuration for my home Kubernetes lab running on K3s and managed using Flux CD with plain Kubernetes manifests.

## Architecture

- **Kubernetes**: K3s lightweight distribution
- **GitOps**: Flux CD
- **Manifests**: Plain Kubernetes YAML (no Helm charts)

## Structure

- `clusters/homelab/`: Kubernetes manifests organized by cluster
  - `infrastructure/`: Core infrastructure components
    - `networking/`: Ingress controllers and network policies
    - `monitoring/`: Prometheus, Grafana, and logging
    - `security/`: Security-related components
  - `apps/`: Application workloads
    - `n8n/`: n8n workflow automation platform
- `docs/`: Setup and maintenance documentation
  - `K3S_SETUP.md`: How to set up K3s
  - `FLUX_SETUP.md`: How to set up Flux
  - `SETUP.md`: Complete end-to-end setup guide

## Getting Started

1. Set up a K3s cluster (see `docs/K3S_SETUP.md`)
2. Bootstrap Flux (see `docs/FLUX_SETUP.md`)
3. Push changes to this repository - Flux will automatically apply them

## Commands

To check the status of your deployments:

```bash
# Using k alias for kubectl
k get pods -A

# Check Flux resources
flux get all -A
```

To manually trigger reconciliation:

```bash
flux reconcile source git flux-system
flux reconcile kustomization flux-system
```

## License

MIT License
