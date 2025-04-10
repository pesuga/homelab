# Accessing Homelab Services Using Standard Ports

## Configuration

We've configured the ingress controller to bind directly to the node's standard HTTP (80) and HTTPS (443) ports using the hostPort feature. This provides a simpler and more intuitive way to access your services.

## Host File Configuration

Add these entries to your `/etc/hosts` file:
```
192.168.86.141 grafana.homelab.local prometheus.homelab.local loki.homelab.local postgres.homelab.local qdrant.homelab.local
```

## Service Access

You can now access your services using standard URLs without specifying NodePorts:

| Service    | URL                                 |
|------------|-------------------------------------|
| Grafana    | https://grafana.homelab.local       |
| Prometheus | https://prometheus.homelab.local    |
| Loki       | https://loki.homelab.local          |
| PostgreSQL | https://postgres.homelab.local      |
| Qdrant     | https://qdrant.homelab.local        |

## Certificate Trust (One-time setup)

Import the generated CA certificate to trust the TLS connections:
```
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /tmp/homelab-certs/homelab-ca.crt
```

## Implementation Details

This setup uses a Kubernetes hostPort configuration to bind the ingress controller directly to ports 80 and 443 on the node. The advantages are:

1. More intuitive URLs without port numbers
2. Standard port access simplifies integration with other tools
3. Better compatibility with various clients that expect standard ports

The configuration is maintained through Flux GitOps and will persist across restarts.

## Fallback Access

The NodePort service is still available as a fallback method if needed:
- HTTP: http://192.168.86.141:32737
- HTTPS: https://192.168.86.141:32720
