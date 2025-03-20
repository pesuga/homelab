# Homelab Documentation Index

This document serves as a central index for all documentation in the homelab repository.

## Setup Guides

- [Setup Guide](setup.md) - Complete end-to-end setup guide
- [K3s Setup](k3s_setup.md) - How to set up K3s
- [Flux Setup](flux_setup.md) - How to set up Flux

## Infrastructure Documentation

- [Subdomain Routing](subdomain_routing.md) - Configuration for subdomain-based routing
- [Monitoring Setup](monitoring_setup.md) - Information about the monitoring stack
- [Router Security](router_security.md) - Network security measures
- [Tailscale Secure Access](tailscale_secure_access.md) - Secure remote access with Tailscale

## Database Services
- [PostgreSQL Setup](postgresql_setup.md) - PostgreSQL database configuration and management

## Application Documentation

- [Vector Database Setup](vectordb_setup.md) - Qdrant vector database setup and usage

## Project Management

- [Project Management](project_management.md) - Task tracking and project management

## Scripts

The `scripts/` directory contains helper scripts:

- `add-manual-dns-records.sh` - Add manual DNS records to Cloudflare
- `apply-cloudflare-token.sh` - Apply Cloudflare API token to Kubernetes
- `install-external-dns.sh` - Direct installation of External-DNS
- `organize-docs.sh` - Script to organize documentation files
- `remove-cloudflare-dns-records.sh` - Remove DNS records from Cloudflare
- `setup-cloudflare-token.sh` - Set up Cloudflare API token for Flux
- `setup-local-dns.sh` - Set up local DNS resolution
- `test-subdomain-access.sh` - Test access to application subdomains

## How to Use This Documentation

1. Start with the [Setup Guide](setup.md) for a complete overview
2. Refer to specific documentation for details on individual components
3. Use the [Project Management](project_management.md) document to track tasks and issues

## Contributing to Documentation

When adding or updating documentation:

1. Follow the established naming convention (lowercase with underscores)
2. Update this index file to include new documentation
3. Use markdown formatting for consistency
4. Include examples and troubleshooting sections where appropriate
