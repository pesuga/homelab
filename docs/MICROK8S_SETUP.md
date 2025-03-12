# Complete MicroK8s and Flux GitOps Setup Guide

This guide provides step-by-step instructions for setting up a MicroK8s Kubernetes cluster on Ubuntu ARM64 with Flux GitOps.

## Part 1: MicroK8s Installation [CRITICAL]

### Install MicroK8s
```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install MicroK8s
sudo snap install microk8s --classic --channel=1.28/stable

# Add your user to the MicroK8s group
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube

# Create .kube directory if it doesn't exist
mkdir -p ~/.kube

# Apply group changes without logging out
newgrp microk8s

# Wait for MicroK8s to be ready
microk8s status --wait-ready
```

### Configure MicroK8s with Required Addons
```bash
# Enable essential add-ons
microk8s enable dns
microk8s enable storage
microk8s enable ingress
microk8s enable helm3
microk8s enable metrics-server

# Wait for add-ons to be ready (wait a minute or so)
microk8s status
```

### Setup kubectl alias and access
```bash
# Create alias for kubectl
echo 'alias k="microk8s kubectl"' >> ~/.bashrc
source ~/.bashrc

# Configure kubectl to use MicroK8s
microk8s config > ~/.kube/config
chmod 600 ~/.kube/config

# Test connection
k get nodes
```

## Part 2: Flux Installation [CRITICAL]

### Install Flux CLI
```bash
# Install prerequisites
sudo apt install -y curl tar

# Install Flux CLI
curl -s https://fluxcd.io/install.sh | sudo bash
```

### Setup Git Repository
```bash
# Create a personal access token in GitHub with repo permissions
# Then set it as an environment variable
export GITHUB_TOKEN=<your-github-token>
export GITHUB_USER=<your-github-username>

# Clone your GitOps repository
git clone https://github.com/$GITHUB_USER/homelab.git
cd homelab
```

### Pre-Installation Checks
```bash
# Verify MicroK8s cluster is ready for Flux
flux check --pre
```

### Install Flux controllers
```bash
# Export manifests and apply them directly
flux install --export > flux-components.yaml

# Apply the manifests
k apply -f flux-components.yaml
```

### Verify Flux controllers are running
```bash
# Check the controllers are running
k get pods -n flux-system
```

### Configure Flux with your Git repository
```bash
# Create a flux-system namespace if it doesn't exist
k create namespace flux-system

# Export GitHub credentials as files
echo "${GITHUB_USER}" > ./github-user.txt
echo "${GITHUB_TOKEN}" > ./github-token.txt

# Create a secret for GitHub credentials
k -n flux-system create secret generic github-credentials \
  --from-file=username=./github-user.txt \
  --from-file=password=./github-token.txt

# Delete the temporary files
rm ./github-user.txt ./github-token.txt

# Create GitRepository source
cat << EOF | k apply -f -
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/${GITHUB_USER}/homelab
  ref:
    branch: main
  secretRef:
    name: github-credentials
EOF

# Create Kustomization for applying resources
cat << EOF | k apply -f -
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 10m
  path: ./clusters/homelab
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
  validation: client
EOF
```

## Part 3: Deploy Infrastructure Components [IMPORTANT]

### Create necessary secrets first
```bash
# Create monitoring namespace
k create namespace monitoring

# Create Grafana admin secret
k create secret generic -n monitoring grafana-admin-credentials \
  --from-literal=admin-user=admin \
  --from-literal=admin-password=YOUR_SECURE_PASSWORD
```

### Check GitRepository and Kustomization status
```bash
# Verify Git source is connected
flux get sources git

# Verify kustomizations are being applied
flux get kustomizations
```

### Monitor deployment progress
```bash
# Check all helm releases
flux get helmreleases --all-namespaces

# Check pods across key namespaces
k get pods -A
```

## Part 4: Troubleshooting [USEFUL]

### Fixing common issues

#### If namespaces get stuck in Terminating state
```bash
# Get the namespace in JSON format
k get namespace <stuck-namespace> -o json > namespace.json

# Edit the file to remove finalizers
# Then use the API to update it
k proxy &
curl -k -H "Content-Type: application/json" -X PUT --data-binary @namespace.json \
  http://127.0.0.1:8001/api/v1/namespaces/<stuck-namespace>/finalize
```

#### If Flux components need to be restarted
```bash
# Restart all Flux controllers
k -n flux-system rollout restart deployment
```

#### Viewing Flux logs
```bash
# View all Flux logs
flux logs --all-namespaces

# View logs for a specific controller
flux logs --kind=helmrelease --name=prometheus -n monitoring
```

## Part 5: Ongoing Maintenance [IMPORTANT]

### Backing up Kubernetes configuration
```bash
# Backup MicroK8s configuration
sudo microk8s.export -o microk8s-backup.tar.gz
```

### Backing up Sealed Secrets
```bash
# Backup the SealedSecrets key (after it's installed)
k get secret -n kube-system sealed-secrets-key -o yaml > sealed-secrets-key.yaml
```

### Updating MicroK8s
```bash
# Check for updates
sudo snap refresh --list

# Apply updates
sudo snap refresh microk8s
```

### Upgrading Flux
```bash
# Update the Flux CLI
curl -s https://fluxcd.io/install.sh | sudo bash

# Update the Flux controllers
flux install
```

---

## Resource Optimization Notes for ARM64 [PRO TIP]

- All components in this setup have conservative resource limits suitable for ARM64 devices
- Consider using the `top` command to monitor system resources
- For extremely resource-constrained environments, consider disabling the metrics-server addon
- Use node affinity to ensure workloads are properly scheduled on ARM64 nodes
- Monitor resource usage: `k top nodes` and `k top pods -A`
