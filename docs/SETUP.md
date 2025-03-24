# Homelab GitOps Setup Guide with K3s and Flux

This guide walks through setting up a K3s cluster with Flux CD for GitOps-based management using plain Kubernetes manifests.

## Prerequisites

- A server for running K3s (Raspberry Pi 4 or similar ARM device works great)
- A workstation with Git installed
- GitHub account with a personal access token
- Basic knowledge of Kubernetes and YAML

## Setup Checklist

- [ ] 1. Server OS Installation
- [ ] 2. K3s Installation
- [ ] 3. Repository Structure Setup
- [ ] 4. Flux Installation and Bootstrap
- [ ] 5. Application Deployment
- [ ] 6. Verify End-to-End GitOps Flow

## 1. Server OS Installation

1. Install your preferred Linux distribution (Ubuntu Server recommended)
2. Configure networking (static IP recommended)
3. Update system packages:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl vim
```

## 2. K3s Installation

K3s is a lightweight Kubernetes distribution perfect for home labs.

```bash
# Install K3s as a server (master)
curl -sfL https://get.k3s.io | sh -

# Verify the installation
sudo systemctl status k3s
sudo k3s kubectl get nodes
```

### Set Up Remote Access to K3s

To manage your K3s cluster from your workstation:

```bash
# On the server, copy the kubeconfig content
sudo cat /etc/rancher/k3s/k3s.yaml

# On your workstation, create ~/.kube/config
# Replace SERVER_IP with your server's IP address
mkdir -p ~/.kube
vim ~/.kube/config
# Paste the content and change 127.0.0.1 to your server's IP
```

Test the connection:

```bash
k get nodes
```

## 3. Repository Structure Setup

Create your GitOps repository structure:

```bash
# Clone your repository (or create a new one)
git clone https://github.com/yourusername/homelab.git
cd homelab

# Create directory structure
mkdir -p clusters/homelab/infrastructure
mkdir -p clusters/homelab/apps
mkdir -p docs

# Create the main kustomization file
cat > clusters/homelab/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - infrastructure
  - apps
EOF
```

## 4. Flux Installation and Bootstrap

Install the Flux CLI on your workstation:

```bash
# For macOS with Homebrew
brew install fluxcd/tap/flux

# For Linux
curl -s https://fluxcd.io/install.sh | sudo bash
```

Check if your cluster is ready for Flux:

```bash
flux check --pre
```

Bootstrap Flux onto your cluster:

```bash
# Create a GitHub personal access token
export GITHUB_TOKEN=<your-github-token>
export GITHUB_USER=<your-github-username>

# Bootstrap Flux
flux bootstrap github \
  --owner=$GITHUB_USER \
  --repository=homelab \
  --branch=main \
  --path=./clusters/homelab \
  --personal
```

## 5. Application Deployment

Create the necessary manifests for your applications:

1. Create namespace:
```bash
cat > clusters/homelab/apps/[app-name]/namespace.yaml << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: [app-name]
EOF
```

2. Create kustomization file:
```bash
cat > clusters/homelab/apps/[app-name]/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
  - ingress.yaml
EOF
```

3. Create deployment, service, and other manifests as needed (see examples in the repository)

4. Commit and push your changes:
```bash
git add .
git commit -m "Add application manifests"
git push
```

## Application Installation

Once Flux is operational, the system will automatically deploy the following applications:

1. **OwnCloud**: File storage and sharing platform
2. **N8N**: Workflow automation platform
3. **Home Assistant**: Home automation platform
4. **Glance**: Dashboard for quick access to services
5. **Immich**: Photo and video backup/management solution

### Required Steps
1. Configure DNS for all applications by running:
   ```bash
   ./scripts/setup-local-dns.sh pesulabs.net 192.168.1.100
   ```
   This will configure local DNS entries for apps like Grafana, Prometheus, Home Assistant, N8N, OwnCloud, and more.

### Check application status
```bash
kubectl get pods -A | grep -v kube-system
```

You should see pods running for:
- n8n
- owncloud
- home-assistant
- glance
- immich

### Application Access
Once all applications are running, you can access them at:
- **OwnCloud**: https://owncloud.app.pesulabs.net
- **N8N**: https://n8n.app.pesulabs.net
- **Home Assistant**: https://home-assistant.app.pesulabs.net
- **Glance**: https://glance.app.pesulabs.net
- **Immich**: https://immich.app.pesulabs.net

## 6. Verify the GitOps Flow

Once your manifests are pushed to the repository, Flux will automatically deploy them to your cluster:

```bash
# Check Flux status
flux get all -A

# Check application deployment
k -n [app-name] get pods,svc,ingress

# Force reconciliation if needed
flux reconcile source git flux-system
flux reconcile kustomization flux-system
```

## Troubleshooting

If you encounter issues:

1. Check Flux logs:
```bash
flux logs
```

2. Check pod logs:
```bash
k -n [app-name] logs -l app=[app-name]
```

3. Check Flux components:
```bash
k -n flux-system get pods
```

## Next Steps

- Add monitoring (Prometheus/Grafana)
- Set up secure ingress with cert-manager
- Add more applications

For detailed specifics on K3s and Flux, refer to:
- K3s documentation: https://docs.k3s.io/
- Flux documentation: https://fluxcd.io/docs/
