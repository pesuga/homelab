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

- **Subdomain Routing**: All services are now configured with subdomain-based routing (e.g., `immich.app.pesulabs.net`).

- **Local Network Access Only**: All services are now configured to be accessible only from the local network or via Tailscale for remote access. Public DNS records have been removed.

- **Certificates**: Certificate issuance is working correctly with self-signed certificates.

- **Services Status**:
  - **Immich**: Working - Web interface accessible
  - **Plex**: Working - Returns 401 (authentication required)
  - **Grafana**: Working - Returns 302 redirect to login page
  - **Prometheus**: Working - Returns 405 for HEAD requests (expected)
  - **Home Assistant**: Working - Returns 405 for HEAD requests (expected)
  - **N8N**: Working - Returns 200 OK
  - **OwnCloud**: Working - Returns 302 redirect to login page
  - **Glance**: Working - Returns 200 OK
  - **Qdrant**: Vector database for similarity search and vector embeddings

## Scripts

The `scripts/` directory contains helper scripts:

- `install-external-dns.sh`: Direct installation of External-DNS using Helm (bypassing Flux)
- `add-manual-dns-records.sh`: Add manual DNS records to Cloudflare
- `remove-cloudflare-dns-records.sh`: Remove DNS records from Cloudflare to restrict access to local network
- `setup-local-dns.sh`: Set up local DNS resolution for homelab services
- `test-subdomain-access.sh`: Test access to application subdomains
- `setup-cloudflare-token.sh`: Set up Cloudflare API token for Flux

## Getting Started

1. Set up a K3s cluster (see `docs/K3S_SETUP.md`)
2. Bootstrap Flux (see `docs/FLUX_SETUP.md`)
3. Push changes to this repository - Flux will automatically apply them

## Secure Remote Access

For secure remote access to homelab services:

1. Set up Tailscale on your devices and homelab server (see `docs/tailscale_secure_access.md`)
2. Configure your router for local-only access (see `docs/router_security.md`)
3. Use the `scripts/setup-local-dns.sh` script to set up local DNS resolution
4. Remove public DNS records using `scripts/remove-cloudflare-dns-records.sh` if needed

This setup ensures your services are only accessible from your local network or through Tailscale's secure VPN.

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

### Available Services

- **Immich** (`immich.app.pesulabs.net`): Photo and video backup and management
- **Plex** (`plex.app.pesulabs.net`): Media server for movies, TV shows, music, and more
- **Grafana** (`grafana.app.pesulabs.net`): Monitoring dashboard for system metrics
- **Prometheus** (`prometheus.app.pesulabs.net`): Time-series database for metrics collection
- **Home Assistant** (`home-assistant.app.pesulabs.net`): Home automation platform
- **N8N** (`n8n.app.pesulabs.net`): Workflow automation tool
- **OwnCloud** (`owncloud.app.pesulabs.net`): File storage and sharing
- **Glance** (`glance.app.pesulabs.net`): Dashboard for quick access to all services

All services are configured with subdomain-based routing and are accessible only from the local network or via Tailscale for remote access.

## License

MIT License
