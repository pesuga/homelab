# K3s Setup Guide

This document outlines the steps to install K3s on a server and configure it for GitOps with Flux.

## Prerequisites

- A server with a modern Linux distribution (Ubuntu, Debian, etc.)
- Sudo/root access
- Internet connectivity
- At least 2GB of RAM (4GB+ recommended)
- At least 20GB of storage

## 1. Prepare the Server

Ensure your server has a static IP address and update all packages:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y curl git vim
```

## 2. Install K3s

K3s is a lightweight Kubernetes distribution perfect for home labs.

```bash
# Install K3s as a server (master)
curl -sfL https://get.k3s.io | sh -

# Check that K3s is running
sudo systemctl status k3s

# Wait for the node to be ready
sudo k3s kubectl get nodes
```

## 3. Configure K3s for Remote Access

To manage your K3s cluster from your workstation:

```bash
# On the server, copy the kubeconfig file
sudo cat /etc/rancher/k3s/k3s.yaml

# On your workstation, create a directory for the kubeconfig
mkdir -p ~/.kube

# Create the kubeconfig file on your workstation
# Replace SERVER_IP with your server's IP address
cat > ~/.kube/config << EOF
# Paste the copied kubeconfig content here
# Make sure to change the server address from 127.0.0.1 to your server's IP
EOF

# Set proper permissions
chmod 600 ~/.kube/config

# Test the connection
kubectl get nodes
```

## 4. Important K3s Directories and Files

- Config directory: `/etc/rancher/k3s/`
- Kubeconfig: `/etc/rancher/k3s/k3s.yaml`
- Service definition: `/etc/systemd/system/k3s.service`
- Data directory: `/var/lib/rancher/k3s/`

## 5. Basic K3s Operations

```bash
# Check K3s status
sudo systemctl status k3s

# Restart K3s
sudo systemctl restart k3s

# View K3s logs
sudo journalctl -u k3s -f

# Stop K3s
sudo systemctl stop k3s

# Uninstall K3s if needed
/usr/local/bin/k3s-uninstall.sh
```
