#!/bin/bash
# Setup a reverse proxy on the host to forward standard ports to NodePorts
# This script should be run on the Kubernetes host node

set -e

echo "===== Installing Nginx Reverse Proxy for Standard Ports ====="
echo "This will setup Nginx to forward ports 80/443 to Kubernetes NodePorts"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Install nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    apt-get update
    apt-get install -y nginx
else
    echo "Nginx already installed."
fi

# Create directory for TLS certificates if it doesn't exist
mkdir -p /etc/nginx/ssl

# Copy certificates from Kubernetes secret
echo "Copying TLS certificates from Kubernetes..."
kubectl get secret -n monitoring homelab-tls -o jsonpath='{.data.tls\.crt}' | base64 -d > /etc/nginx/ssl/homelab-tls.crt
kubectl get secret -n monitoring homelab-tls -o jsonpath='{.data.tls\.key}' | base64 -d > /etc/nginx/ssl/homelab-tls.key

# Create nginx configuration for reverse proxy
echo "Creating nginx configuration..."
cat << EOF > /etc/nginx/sites-available/k8s-proxy
server {
    listen 80;
    listen [::]:80;
    
    server_name *.homelab.local;
    
    # Redirect all HTTP requests to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    
    server_name *.homelab.local;
    
    # TLS configuration
    ssl_certificate /etc/nginx/ssl/homelab-tls.crt;
    ssl_certificate_key /etc/nginx/ssl/homelab-tls.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    
    # Forward all traffic to the ingress-nginx NodePort
    location / {
        proxy_pass https://127.0.0.1:32720;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Increase timeout for long-running requests
        proxy_connect_timeout 90;
        proxy_send_timeout 90;
        proxy_read_timeout 90;
        
        # Disable buffering for event streams
        proxy_buffering off;
    }
}
EOF

# Enable the site
echo "Enabling reverse proxy configuration..."
ln -sf /etc/nginx/sites-available/k8s-proxy /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

# Restart nginx to apply changes
echo "Restarting nginx..."
systemctl restart nginx
systemctl enable nginx

echo ""
echo "===== Nginx reverse proxy setup complete! ====="
echo "You can now access your services with standard ports:"
echo "- Grafana:    https://grafana.homelab.local"
echo "- Prometheus: https://prometheus.homelab.local"
echo "- Loki:       https://loki.homelab.local"
echo "- PostgreSQL: https://postgres.homelab.local"
echo "- Qdrant:     https://qdrant.homelab.local"
echo ""
echo "To uninstall, run the uninstall-nginx-proxy.sh script"
