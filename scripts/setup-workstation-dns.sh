#!/bin/bash
# Script to set up cluster.local DNS resolution on your workstation
# Run this script with sudo permissions

NODE_IP="192.168.86.141"  # Your Kubernetes node IP

echo "Setting up cluster.local DNS resolution on your workstation..."

# Create a directory for dnsmasq config if it doesn't exist
sudo mkdir -p /etc/dnsmasq.d

# Create dnsmasq configuration for cluster.local domains
cat << EOF | sudo tee /etc/dnsmasq.d/k8s.conf
# Forward cluster.local domains to Kubernetes DNS through SSH tunnel
server=/cluster.local/127.0.0.1#5353
# Use regular DNS for everything else
server=8.8.8.8
server=8.8.4.4
EOF

# Set up SSH port forwarding in the background
echo "Setting up SSH port forwarding to Kubernetes DNS..."
ssh -N -L 5353:10.43.0.10:53 asuna@${NODE_IP} &
SSH_PID=$!

# Store the SSH PID for later cleanup
echo $SSH_PID > ~/.k8s-dns-tunnel.pid

# Restart dnsmasq to apply changes
if [ -f /usr/sbin/service ]; then
  sudo service dnsmasq restart
elif [ -f /bin/systemctl ]; then
  sudo systemctl restart dnsmasq
else
  echo "Could not restart dnsmasq - please restart it manually"
fi

# Set the local DNS server as first in resolv.conf
# This is system-dependent and might need adjustments
if [ -f /etc/resolv.conf ]; then
  if ! grep -q "^nameserver 127.0.0.1" /etc/resolv.conf; then
    sudo cp /etc/resolv.conf /etc/resolv.conf.backup
    echo "nameserver 127.0.0.1" | sudo tee /etc/resolv.conf
    cat /etc/resolv.conf.backup | grep -v "^nameserver" | sudo tee -a /etc/resolv.conf
  fi
fi

echo "DNS setup complete!"
echo ""
echo "To test, try: nslookup kubernetes.default.svc.cluster.local"
echo ""
echo "To stop DNS forwarding: kill \$(cat ~/.k8s-dns-tunnel.pid)"
