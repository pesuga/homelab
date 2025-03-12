# Home Lab GitOps Repository

This repository contains the GitOps configuration for my home Kubernetes lab, managed using Flux CD.

## Structure

- `clusters/homelab/`: Kubernetes manifests organized by cluster
  - `infrastructure/`: Core infrastructure components
    - `sources/`: Helm and Git repositories
    - `networking/`: Ingress controllers and network policies
    - `monitoring/`: Prometheus, Grafana, and logging
    - `security/`: SealedSecrets and other security tools
  - `apps/`: Application workloads
- `charts/`: Custom Helm charts

## Bootstrap

The cluster is bootstrapped using Flux CD. See documentation in `docs/` for details.

## License

This project is personal and not licensed for distribution.
