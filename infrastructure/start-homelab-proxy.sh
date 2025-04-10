#!/bin/bash
# Simple script to enable standard port access to homelab services
# This avoids the need for complex port forwarding or firewall configurations

# Check if port forwarding is already running
if pgrep -f "kubectl port-forward -n ingress-nginx" > /dev/null; then
  echo "Port forwarding is already running."
  echo "To stop it, run: pkill -f 'kubectl port-forward'"
  exit 0
fi

# Start port forwarding for HTTP (8080) and HTTPS (8443)
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 8443:443 --address 0.0.0.0 &

# Save the PID for later reference
PID=$!
echo "Port forwarding started with PID: $PID"

# Display access information
echo ""
echo "Access your homelab services at:"
echo "---------------------------------------"
echo "Grafana:    https://grafana.homelab.local:8443"
echo "Prometheus: https://prometheus.homelab.local:8443"
echo "Loki:       https://loki.homelab.local:8443"
echo "PostgreSQL: https://postgres.homelab.local:8443"
echo "Qdrant:     https://qdrant.homelab.local:8443"
echo ""
echo "To stop port forwarding, run: pkill -f 'kubectl port-forward'"
echo ""
echo "IMPORTANT: Make sure your /etc/hosts file contains entries for these services"
echo "pointing to 127.0.0.1 (for local access) or your computer's IP (for network access)"
