#!/bin/bash
# Remove the nginx reverse proxy configuration
# This script should be run on the Kubernetes host node

set -e

echo "===== Uninstalling Nginx Reverse Proxy for Standard Ports ====="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Remove the nginx site configuration
echo "Removing nginx configuration..."
rm -f /etc/nginx/sites-available/k8s-proxy
rm -f /etc/nginx/sites-enabled/k8s-proxy

# Remove SSL certificates
echo "Removing SSL certificates..."
rm -f /etc/nginx/ssl/homelab-tls.crt
rm -f /etc/nginx/ssl/homelab-tls.key

# Restart nginx to apply changes
echo "Restarting nginx service..."
systemctl restart nginx

echo ""
echo "===== Nginx reverse proxy removed! ====="
echo "The Nginx service is still installed, but the Kubernetes proxy configuration has been removed."
echo "To completely remove Nginx, run: sudo apt-get purge nginx nginx-common"
