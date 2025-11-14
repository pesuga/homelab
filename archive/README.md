# Archive Directory

This directory contains deprecated and decommissioned services from the homelab infrastructure.

## Structure

- **deprecated/**: Services that were previously deployed but have been removed from production
- **prototypes/**: Early experimental versions and proof-of-concepts
- **old-configs/**: Historical configuration files for reference

## Deprecation Timeline

| Service | Archive Date | Reason for Deprecation | Replacement |
|---------|--------------|------------------------|-------------|
| Flowise | 2024-10-31 | Replaced by N8n workflows | N8n |
| Grafana | 2024-10-31 | Dashboard consolidation into homelab-dashboard | Homelab Dashboard |
| Monitorium | 2024-11-08 | Experimental monitoring tool, replaced by Prometheus+Loki | Prometheus/Loki |
| Terraform experiments | 2024-10-25 | Infrastructure managed via Kubernetes manifests | K8s manifests |

## Retention Policy

- **Keep for 6 months**: Configuration files and deployment manifests
- **Keep for 1 year**: Documentation and architectural decisions
- **Keep indefinitely**: Critical data backups and state snapshots

## Migration Notes

When removing services, ensure to:
1. Move all configurations to the appropriate archive subdirectory
2. Add entry to the deprecation timeline table above
3. Document reason for deprecation and any replacements
4. Update service dependencies and remove references in active configs