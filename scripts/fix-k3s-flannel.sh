#!/bin/bash

# Fix K3s Flannel Backend for Tailscale Compatibility
# This script updates the K3s configuration to use 'wireguard-native' backend
# to resolve MTU/fragmentation issues with VXLAN over Tailscale.

set -e

CONFIG_FILE="/etc/rancher/k3s/config.yaml"
BACKUP_FILE="/etc/rancher/k3s/config.yaml.bak.$(date +%Y%m%d%H%M%S)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

echo "=== Starting K3s Flannel Fix ==="

# 1. Backup existing config
if [ -f "$CONFIG_FILE" ]; then
    echo "-> Backing up $CONFIG_FILE to $BACKUP_FILE"
    cp "$CONFIG_FILE" "$BACKUP_FILE"
else
    echo "-> Warning: $CONFIG_FILE not found. Creating new."
    mkdir -p /etc/rancher/k3s
    touch "$CONFIG_FILE"
fi

# 2. Update configuration
echo "-> Updating flannel-backend to wireguard-native"

# Check if flannel-backend is already set
if grep -q "flannel-backend" "$CONFIG_FILE"; then
    # Replace existing setting
    sed -i 's/flannel-backend:.*/flannel-backend: wireguard-native/' "$CONFIG_FILE"
else
    # Append setting
    echo "flannel-backend: wireguard-native" >> "$CONFIG_FILE"
fi

# 3. Restart K3s service
echo "-> Restarting K3s service..."

if systemctl is-active --quiet k3s; then
    SERVICE_NAME="k3s"
elif systemctl is-active --quiet k3s-agent; then
    SERVICE_NAME="k3s-agent"
else
    echo "Error: Neither k3s nor k3s-agent service is running."
    exit 1
fi

echo "-> Detected service: $SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo "=== Fix Applied Successfully ==="
echo "Backend set to: wireguard-native"
echo "Service restarted: $SERVICE_NAME"
