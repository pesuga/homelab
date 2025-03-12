# Homelab GitOps Setup Guide

This guide walks through setting up Flux CD for your home Kubernetes cluster.

## Prerequisites

- A running Kubernetes cluster
- kubectl configured to communicate with your cluster
- GitHub account with a personal access token
- Git installed on your local machine

## Bootstrap Steps

### Step 1: Install Flux CLI [CRITICAL]

```bash
# Install Flux CLI
curl -s https://fluxcd.io/install.sh | bash
```

### Step 2: Export GitHub credentials [CRITICAL]

```bash
# Set your GitHub personal access token
export GITHUB_TOKEN=<your-github-token>
export GITHUB_USER=<your-github-username>
```

### Step 3: Bootstrap Flux [CRITICAL]

```bash
# Bootstrap Flux with your GitHub repository
flux bootstrap github \
  --owner=$GITHUB_USER \
  --repository=homelab \
  --branch=main \
  --path=clusters/homelab \
  --personal
```

### Step 4: Verify the installation [IMPORTANT]

```bash
# Check Flux components
k get pods -n flux-system

# Check GitRepository status
flux get sources git

# Check kustomization status
flux get kustomizations
```

### Step 5: Create secrets [IMPORTANT]

For the Grafana admin credentials:

```bash
# Create secret for Grafana admin
k create secret generic -n monitoring grafana-admin-credentials \
  --from-literal=admin-user=admin \
  --from-literal=admin-password=YOUR_SECURE_PASSWORD
```

For the n8n database credentials:

```bash
# Create secret for n8n database
k create secret generic -n n8n n8n-db-auth \
  --from-literal=DB_POSTGRESDB_PASSWORD=YOUR_DB_PASSWORD
```

## Maintenance Commands

### View Flux logs [USEFUL]

```bash
# View logs from Flux controllers
flux logs --all-namespaces

# View logs for a specific HelmRelease
flux logs --kind=HelmRelease --name=n8n -n n8n
```

### Reconcile resources [USEFUL]

```bash
# Trigger reconciliation for all resources
flux reconcile source git flux-system

# Reconcile a specific HelmRelease
flux reconcile helmrelease n8n -n n8n
```

### Suspend/Resume resources [OPTIONAL]

```bash
# Suspend a HelmRelease (prevent reconciliation)
flux suspend helmrelease n8n -n n8n

# Resume a suspended HelmRelease
flux resume helmrelease n8n -n n8n
```

## Adding New Applications

To add new applications to your GitOps workflow:

1. Create a new directory under `clusters/homelab/apps/`
2. Add the necessary HelmRepository, HelmRelease, and other resources
3. Create a kustomization.yaml file in the application directory
4. Add the application to the root kustomization.yaml file
5. Commit and push the changes to your Git repository

Flux will automatically detect the changes and apply them to your cluster.

## Backup Recommendations [IMPORTANT]

1. Backup your Kubernetes etcd data regularly
2. Save a copy of the SealedSecrets controller key:
   ```bash
   k get secret -n kube-system sealed-secrets-key -o yaml > sealed-secrets-key.yaml
   ```
3. Keep your Git repository backed up as it contains all your infrastructure definitions
