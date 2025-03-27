#!/bin/bash

# Script to set up local DNS records for homelab services
# This script generates configuration for either dnsmasq or Pi-hole

# Internal IP of the Kubernetes cluster's ingress controller
CLUSTER_IP="192.168.86.141"

# Domain suffix
DOMAIN_SUFFIX="app.pesulabs.net"

# Services to configure
SERVICES=(
  "immich"
  "grafana"
  "prometheus"
  "home-assistant"
  "n8n"
  "owncloud"
  "glance"
  "qdrant"
  "homer"
)

# Function to generate dnsmasq configuration
generate_dnsmasq_config() {
  echo "# Homelab services DNS configuration for dnsmasq"
  echo "# Add this to your dnsmasq.conf file"
  echo ""
  
  for service in "${SERVICES[@]}"; do
    echo "address=/${service}.${DOMAIN_SUFFIX}/${CLUSTER_IP}"
  done
}

# Function to generate Pi-hole configuration
generate_pihole_config() {
  echo "# Homelab services DNS configuration for Pi-hole"
  echo "# Add these entries through the Pi-hole admin interface or custom.list"
  echo ""
  
  for service in "${SERVICES[@]}"; do
    echo "${CLUSTER_IP} ${service}.${DOMAIN_SUFFIX}"
  done
}

# Function to generate hosts file entries
generate_hosts_entries() {
  echo "# Homelab services entries for /etc/hosts"
  echo "# Add these lines to your /etc/hosts file"
  echo ""
  
  for service in "${SERVICES[@]}"; do
    echo "${CLUSTER_IP} ${service}.${DOMAIN_SUFFIX}"
  done
}

# Display usage information
echo "=== Homelab Local DNS Configuration ==="
echo ""
echo "This script generates DNS configuration for your homelab services."
echo "Choose one of the following options based on your setup:"
echo ""
echo "1. dnsmasq configuration"
echo "2. Pi-hole configuration"
echo "3. /etc/hosts entries"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
  1)
    echo ""
    generate_dnsmasq_config
    ;;
  2)
    echo ""
    generate_pihole_config
    ;;
  3)
    echo ""
    generate_hosts_entries
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

echo ""
echo "=== Instructions ==="
echo ""
case $choice in
  1)
    echo "1. Add the above lines to your dnsmasq.conf file"
    echo "2. Restart dnsmasq: sudo systemctl restart dnsmasq"
    echo "3. Configure your devices to use your dnsmasq server as DNS"
    ;;
  2)
    echo "1. Add the above entries to Pi-hole through the admin interface"
    echo "   or by adding them to /etc/pihole/custom.list"
    echo "2. Run 'pihole restartdns' to apply changes"
    echo "3. Ensure your devices use Pi-hole as their DNS server"
    ;;
  3)
    echo "1. Add the above lines to /etc/hosts on each device"
    echo "2. Flush DNS cache if needed:"
    echo "   - macOS: sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
    echo "   - Linux: sudo systemd-resolve --flush-caches"
    echo "   - Windows: ipconfig /flushdns"
    ;;
esac
