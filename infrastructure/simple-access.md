# Simple Homelab Access Guide

## Access Methods

We have two reliable methods to access services:

### Option 1: NodePort Access (Direct)

We've configured fixed NodePorts that will remain consistent:
- HTTP: Port 32737
- HTTPS: Port 32720

Add these entries to your `/etc/hosts` file:
```
192.168.86.141 grafana.homelab.local prometheus.homelab.local loki.homelab.local postgres.homelab.local qdrant.homelab.local
```

Access services via URLs like: https://grafana.homelab.local:32720

### Option 2: Kubectl Port-Forward (Recommended)

This method provides the cleanest approach with standard ports:

```bash
# Run this in a terminal to enable access on standard ports
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 8443:443 --address 0.0.0.0
```

Then add to your `/etc/hosts` file:
```
127.0.0.1 grafana.homelab.local prometheus.homelab.local loki.homelab.local postgres.homelab.local qdrant.homelab.local
```

Access services via URLs like: https://grafana.homelab.local:8443

### Option 3: Tailscale (Remote Access)

For remote access, our Tailscale subnet router approach provides secure access:

1. Fix Tailscale auth key issue
2. Access services using internal cluster IPs through Tailscale network

## Quick Access Script

Create this script to start port forwarding in the background:

```bash
#!/bin/bash
# Save as ~/start-homelab-proxy.sh and make executable with: chmod +x ~/start-homelab-proxy.sh

kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 8443:443 --address 0.0.0.0 &
echo "Access your homelab services at:"
echo "- Grafana:    https://grafana.homelab.local:8443"
echo "- Prometheus: https://prometheus.homelab.local:8443"
echo "- Loki:       https://loki.homelab.local:8443"
echo "- PostgreSQL: https://postgres.homelab.local:8443"
echo "- Qdrant:     https://qdrant.homelab.local:8443"
echo ""
echo "Port forwarding running in background. To stop, run: pkill -f 'kubectl port-forward'"
```

## Certificate Trust (One-time setup)

Import the CA certificate to trust connections:
```
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /tmp/homelab-certs/homelab-ca.crt
```
