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

## Current Status

- **Tailscale DNS Limitation**: Tailscale DNS setup does not support subdomains. Applications should be configured with path-based routing (like `/home-assistant`) rather than dedicated subdomains.

- **External-DNS Issues**: Currently experiencing issues with the External-DNS HelmRelease. See `docs/SUBDOMAIN_ROUTING_FIX_PLAN.md` for details and workarounds.

- **Certificates**: Certificate issuance is working correctly with Let's Encrypt and DNS-01 validation through Cloudflare.

## Scripts

The `scripts/` directory contains helper scripts:

- `install-external-dns.sh`: Direct installation of External-DNS using Helm (bypassing Flux)
- `add-manual-dns-records.sh`: Add manual DNS records to Cloudflare
- `test-subdomain-access.sh`: Test access to application subdomains
- `setup-cloudflare-token.sh`: Set up Cloudflare API token for Flux

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

## Applications

Application configurations are organized in their respective directories under `clusters/homelab/apps/`.

## License

MIT License
