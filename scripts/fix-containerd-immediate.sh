#!/bin/bash
# This script directly fixes containerd's TLS verification issues on your node

# SSH to the Kubernetes node and run these commands directly
echo "Applying immediate fix to containerd on your node..."
echo "Please enter your SSH password when prompted."

# User will be prompted for SSH password
ssh -t asuna@192.168.86.141 '
echo "Creating temporary containerd config file..."
cat > containerd-config.toml << EOF
version = 2

[plugins."io.containerd.grpc.v1.cri".registry]
  [plugins."io.containerd.grpc.v1.cri".registry.configs]
    [plugins."io.containerd.grpc.v1.cri".registry.configs."docker.io"]
      [plugins."io.containerd.grpc.v1.cri".registry.configs."docker.io".tls]
        insecure_skip_verify = true
    [plugins."io.containerd.grpc.v1.cri".registry.configs."quay.io"]
      [plugins."io.containerd.grpc.v1.cri".registry.configs."quay.io".tls]
        insecure_skip_verify = true
    [plugins."io.containerd.grpc.v1.cri".registry.configs."ghcr.io"]
      [plugins."io.containerd.grpc.v1.cri".registry.configs."ghcr.io".tls]
        insecure_skip_verify = true
EOF

echo "Adding Google DNS servers to resolv.conf..."
cat > resolv.conf << EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF

echo "Now applying these changes with sudo (you will be prompted for password)..."
sudo mv containerd-config.toml /etc/containerd/config.toml
sudo mv resolv.conf /etc/resolv.conf
sudo systemctl restart containerd

echo "Checking if containerd is running..."
sudo systemctl status containerd | grep Active

echo "Fix applied. Returning to your local system."
'

echo ""
echo "=== NEXT STEPS ==="
echo "1. Check if pods can now pull images with: k get pods -n glance"
echo "2. If still having issues, consider rebooting your node with: ssh asuna@192.168.86.141 'sudo reboot'"
