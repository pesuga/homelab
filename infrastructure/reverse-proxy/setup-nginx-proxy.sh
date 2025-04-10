#!/bin/bash
# Setup a reverse proxy on the host to forward standard ports to NodePorts

# Install nginx
sudo apt-get update
sudo apt-get install -y nginx

# Create nginx configuration for reverse proxy
cat << EOF | sudo tee /etc/nginx/sites-available/k8s-proxy
server {
    listen 80;
    listen [::]:80;
    
    server_name *.homelab.local;
    
    location / {
        proxy_pass http://localhost:32737;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    
    server_name *.homelab.local;
    
    # Self-signed certificate paths (you can replace these with your actual certificates)
    ssl_certificate /tmp/homelab-certs/homelab-tls.crt;
    ssl_certificate_key /tmp/homelab-certs/homelab-tls.key;
    
    location / {
        proxy_pass https://localhost:32720;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/k8s-proxy /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx to apply changes
sudo systemctl restart nginx

echo "Nginx reverse proxy setup complete. Standard ports (80/443) will now forward to NodePorts (32737/32720)."
