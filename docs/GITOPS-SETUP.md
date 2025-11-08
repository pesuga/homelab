# GitOps with Flux CD Setup Guide

**Version**: 1.0
**Date**: 2025-10-25
**Flux Version**: v2.4+

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Repository Structure](#repository-structure)
- [Migrating Existing Infrastructure](#migrating-existing-infrastructure)
- [Managing External Repositories](#managing-external-repositories)
- [Verification and Testing](#verification-and-testing)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)

---

## Overview

GitOps is a declarative approach to infrastructure management where Git is the single source of truth. Flux CD is a continuous delivery tool that automates the deployment of Kubernetes resources from Git repositories.

### Benefits

- **Automated Deployments**: Push to Git → automatic K8s deployment
- **Drift Detection**: Flux reverts manual changes to match Git state
- **Audit Trail**: All changes tracked in Git history
- **Multi-Repository Support**: Manage apps from different repos
- **Rollback**: Git revert = infrastructure revert
- **Progressive Delivery**: Canary deployments (with Flagger)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Repository: pesuga/homelab                          │
│  └── infrastructure/kubernetes/                             │
│       ├── base/              (namespaces, core config)      │
│       ├── databases/         (postgres, redis, qdrant)      │
│       ├── monitoring/        (prometheus, grafana)          │
│       ├── flux/              (GitOps resources)             │
│       │   ├── sources/       (GitRepository CRDs)           │
│       │   └── kustomizations/ (Kustomization CRDs)          │
│       └── apps/              (external apps)                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ Flux watches (every 1m)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  K3s Cluster (asuna - 192.168.8.185)                        │
│  ┌───────────────────────────────────────┐                 │
│  │  flux-system namespace                │                 │
│  │  ├── source-controller    (Git sync)  │                 │
│  │  ├── kustomize-controller (Apply)     │                 │
│  │  ├── helm-controller      (Helm)      │                 │
│  │  └── notification-controller          │                 │
│  └───────────────────────────────────────┘                 │
│                          │                                  │
│                          │ Reconciles                       │
│                          ▼                                  │
│  ┌───────────────────────────────────────┐                 │
│  │  homelab namespace                    │                 │
│  │  All services auto-deployed & synced  │                 │
│  └───────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### On Local Machine (or Service Node)

1. **Flux CLI** (v2.4+)
   ```bash
   curl -s https://fluxcd.io/install.sh | sudo bash

   # Verify installation
   flux --version
   ```

2. **kubectl** configured for K3s cluster
   ```bash
   kubectl get nodes
   # Should show: asuna   Ready   control-plane,master
   ```

3. **GitHub Personal Access Token** (for private repos)
   - Go to: https://github.com/settings/tokens
   - Generate new token (classic)
   - Scopes: `repo` (all), `workflow`
   - Save token securely

4. **Git credentials configured**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

---

## Installation

### Step 1: Pre-flight Check

```bash
# Check cluster compatibility
flux check --pre

# Expected output:
# ✔ Kubernetes 1.33.5 >=1.28.0-0
# ✔ prerequisites checks passed
```

### Step 2: Bootstrap Flux

**Option A: Public Repository (easiest)**

```bash
flux bootstrap github \
  --owner=pesuga \
  --repository=homelab \
  --branch=revised-version \
  --path=./clusters/homelab \
  --personal
```

**Option B: Private Repository (requires token)**

```bash
export GITHUB_TOKEN=<your-token>

flux bootstrap github \
  --token-auth \
  --owner=pesuga \
  --repository=homelab \
  --branch=revised-version \
  --path=./clusters/homelab \
  --personal
```

**What This Does**:
1. Installs Flux controllers to `flux-system` namespace
2. Creates `clusters/homelab/flux-system/` directory in your repo
3. Configures Flux to watch this repo
4. Commits and pushes changes to GitHub

### Step 3: Verify Installation

```bash
# Check Flux components
kubectl get pods -n flux-system

# Expected output:
# NAME                                       READY   STATUS    RESTARTS   AGE
# helm-controller-xxxxxxxxx-xxxxx            1/1     Running   0          2m
# kustomize-controller-xxxxxxxxx-xxxxx       1/1     Running   0          2m
# notification-controller-xxxxxxxxx-xxxxx    1/1     Running   0          2m
# source-controller-xxxxxxxxx-xxxxx          1/1     Running   0          2m

# Check Flux sync status
flux get sources git
flux get kustomizations
```

---

## Repository Structure

### Before Flux (Current)

```
homelab/
└── infrastructure/
    └── kubernetes/
        ├── base/
        │   └── namespace.yaml
        ├── databases/
        │   ├── postgres/postgres.yaml
        │   ├── redis/redis.yaml
        │   └── qdrant/qdrant.yaml
        ├── monitoring/
        │   ├── prometheus-deployment.yaml
        │   └── grafana-deployment.yaml
        └── ...
```

### After Flux (Target)

```
homelab/
├── clusters/
│   └── homelab/                    # NEW: Flux bootstrap configs
│       └── flux-system/
│           ├── gotk-components.yaml
│           ├── gotk-sync.yaml
│           └── kustomization.yaml
│
└── infrastructure/
    └── kubernetes/
        ├── flux/                   # NEW: Flux resources
        │   ├── sources/
        │   │   ├── homelab.yaml         # This repo
        │   │   └── external-app.yaml    # External repos
        │   ├── kustomizations/
        │   │   ├── base.yaml            # Base namespace
        │   │   ├── databases.yaml       # DB services
        │   │   ├── monitoring.yaml      # Observability
        │   │   └── apps.yaml            # Applications
        │   └── helmrepositories/        # Optional Helm repos
        │       └── bitnami.yaml
        │
        ├── base/                   # Existing (unchanged)
        ├── databases/              # Existing (unchanged)
        ├── monitoring/             # Existing (unchanged)
        └── apps/                   # NEW: External app manifests
```

---

## Migrating Existing Infrastructure

### Step 1: Create Flux Directory Structure

```bash
mkdir -p infrastructure/kubernetes/flux/{sources,kustomizations,helmrepositories}
```

### Step 2: Create Source for This Repo

Create `infrastructure/kubernetes/flux/sources/homelab.yaml`:

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: homelab
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/pesuga/homelab
  ref:
    branch: revised-version
  ignore: |
    # Exclude non-K8s files
    /*.md
    /docs/
    /scripts/
    /services/
```

### Step 3: Create Kustomizations for Each Layer

**Base Layer** (`infrastructure/kubernetes/flux/kustomizations/base.yaml`):

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: base
  namespace: flux-system
spec:
  interval: 5m
  path: ./infrastructure/kubernetes/base
  prune: true
  sourceRef:
    kind: GitRepository
    name: homelab
  targetNamespace: homelab
  timeout: 2m
```

**Databases Layer** (`infrastructure/kubernetes/flux/kustomizations/databases.yaml`):

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: databases
  namespace: flux-system
spec:
  interval: 5m
  path: ./infrastructure/kubernetes/databases
  prune: true
  sourceRef:
    kind: GitRepository
    name: homelab
  dependsOn:
    - name: base  # Wait for namespace to be created
  targetNamespace: homelab
  timeout: 5m
  healthChecks:
    - apiVersion: apps/v1
      kind: StatefulSet
      name: postgres
      namespace: homelab
    - apiVersion: apps/v1
      kind: Deployment
      name: redis
      namespace: homelab
```

**Monitoring Layer** (`infrastructure/kubernetes/flux/kustomizations/monitoring.yaml`):

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: monitoring
  namespace: flux-system
spec:
  interval: 5m
  path: ./infrastructure/kubernetes/monitoring
  prune: true
  sourceRef:
    kind: GitRepository
    name: homelab
  dependsOn:
    - name: base
  targetNamespace: homelab
  timeout: 5m
```

### Step 4: Apply Flux Resources

```bash
# Apply source
kubectl apply -f infrastructure/kubernetes/flux/sources/homelab.yaml

# Wait for source to sync
flux get sources git homelab

# Apply kustomizations in order
kubectl apply -f infrastructure/kubernetes/flux/kustomizations/base.yaml
kubectl apply -f infrastructure/kubernetes/flux/kustomizations/databases.yaml
kubectl apply -f infrastructure/kubernetes/flux/kustomizations/monitoring.yaml

# Watch reconciliation
flux get kustomizations --watch
```

### Step 5: Commit and Push

```bash
git add infrastructure/kubernetes/flux/
git commit -m "Add Flux GitOps configuration"
git push origin revised-version
```

### Step 6: Verify Automatic Sync

```bash
# Make a change to a manifest (e.g., change replica count)
# Commit and push
# Wait up to 1 minute

# Check if Flux applied the change
kubectl get deployments -n homelab

# View Flux events
flux events
```

---

## Managing External Repositories

### Use Case: Deploy an App from a Separate Repo

**Scenario**: You have a custom application in `https://github.com/user/my-app` with Kubernetes manifests in `deploy/kubernetes/`.

### Step 1: Create GitRepository for External App

Create `infrastructure/kubernetes/flux/sources/my-app.yaml`:

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/user/my-app
  ref:
    branch: main
  # For private repos:
  # secretRef:
  #   name: my-app-git-credentials
```

### Step 2: Create Secret for Private Repo (if needed)

```bash
# Create Git credentials secret
flux create secret git my-app-git-credentials \
  --url=https://github.com/user/my-app \
  --username=your-username \
  --password=$GITHUB_TOKEN \
  --namespace=flux-system

# Or manually:
kubectl create secret generic my-app-git-credentials \
  --from-literal=username=your-username \
  --from-literal=password=$GITHUB_TOKEN \
  -n flux-system
```

### Step 3: Create Kustomization for External App

Create `infrastructure/kubernetes/flux/kustomizations/my-app.yaml`:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 5m
  path: ./deploy/kubernetes
  prune: true
  sourceRef:
    kind: GitRepository
    name: my-app
  targetNamespace: homelab
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: my-app
      namespace: homelab
  postBuild:
    substitute:
      ENVIRONMENT: "production"
      REPLICAS: "2"
```

### Step 4: Apply and Verify

```bash
kubectl apply -f infrastructure/kubernetes/flux/sources/my-app.yaml
kubectl apply -f infrastructure/kubernetes/flux/kustomizations/my-app.yaml

flux get sources git my-app
flux get kustomizations my-app
```

Now any push to `user/my-app` main branch will trigger automatic deployment!

---

## Verification and Testing

### Test 1: Drift Detection

```bash
# Manually change a deployment
kubectl scale deployment/n8n -n homelab --replicas=3

# Wait up to 5 minutes (Flux interval)
# Flux should revert the change back to Git state

# Check events
flux events -n flux-system
```

### Test 2: Git-Driven Update

```bash
# Edit a manifest (e.g., change N8n replica count in Git)
vim infrastructure/kubernetes/apps/n8n.yaml

# Commit and push
git add .
git commit -m "Scale N8n to 2 replicas"
git push

# Wait up to 1 minute
# Check deployment
kubectl get deployment n8n -n homelab -w
```

### Test 3: Suspension and Resumption

```bash
# Suspend a kustomization (stop reconciliation)
flux suspend kustomization databases

# Resume
flux resume kustomization databases
```

---

## Common Operations

### View All Flux Resources

```bash
flux get all
```

### Force Reconciliation

```bash
# Reconcile a specific kustomization immediately
flux reconcile kustomization databases --with-source

# Reconcile source (fetch from Git)
flux reconcile source git homelab
```

### View Logs

```bash
# Kustomize controller logs
flux logs --kind=Kustomization --name=databases

# Source controller logs
flux logs --kind=GitRepository --name=homelab
```

### Delete a Kustomization

```bash
# This will also delete all resources managed by it (if prune: true)
kubectl delete kustomization databases -n flux-system
```

### Uninstall Flux

```bash
flux uninstall --silent

# Or with confirmation
flux uninstall
```

---

## Troubleshooting

### Issue: Kustomization Stuck in "Reconciling"

```bash
# Check events
kubectl describe kustomization databases -n flux-system

# Common causes:
# - Missing dependencies (check dependsOn)
# - Invalid YAML syntax
# - Namespace doesn't exist
# - Health checks failing

# Fix: Check logs
flux logs --kind=Kustomization --name=databases
```

### Issue: GitRepository Not Syncing

```bash
# Check source status
flux get sources git homelab

# If "Authentication failed":
# - Verify Git credentials (for private repos)
# - Check secret exists: kubectl get secret -n flux-system

# If "Repository not found":
# - Verify URL in GitRepository spec
# - Check branch exists
```

### Issue: Flux Controllers Crash Looping

```bash
# Check pod status
kubectl get pods -n flux-system

# View logs
kubectl logs -n flux-system <pod-name>

# Common causes:
# - Insufficient resources
# - Network connectivity issues
# - Invalid Flux configuration

# Fix: Restart Flux
flux uninstall
flux bootstrap github ... (re-run bootstrap)
```

### Issue: Secret Changes Not Applied

**Problem**: Flux doesn't update Secrets by default (security feature).

**Solution**: Add annotation to force updates:

```yaml
apiVersion: v1
kind: Secret
metadata:
  annotations:
    kustomize.toolkit.fluxcd.io/force: "enabled"
  name: my-secret
```

---

## Best Practices

### 1. Use Dependencies

Order kustomizations with `dependsOn`:

```yaml
spec:
  dependsOn:
    - name: base
    - name: databases
```

### 2. Add Health Checks

Ensure deployments are healthy before marking as reconciled:

```yaml
spec:
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: my-app
      namespace: homelab
```

### 3. Set Timeouts

Prevent long-running reconciliations:

```yaml
spec:
  timeout: 5m
```

### 4. Use Separate Branches for Testing

```yaml
spec:
  ref:
    branch: staging  # Test changes here first
```

### 5. Enable Notifications (Advanced)

Set up Slack/Discord alerts for deployment events:

```bash
flux create alert-provider slack \
  --type=slack \
  --channel=homelab-alerts \
  --address=<webhook-url>

flux create alert homelab-alerts \
  --provider-ref=slack \
  --event-severity=info
```

---

## Next Steps

1. Bootstrap Flux to your K3s cluster
2. Migrate existing infrastructure to Flux management
3. Test drift detection and Git-driven updates
4. Add external repository for a sample app
5. Configure notifications (optional)
6. Update documentation and runbooks

---

## Resources

- **Flux Documentation**: https://fluxcd.io/flux/
- **Flux CLI Reference**: https://fluxcd.io/flux/cmd/
- **Flux Get Started Guide**: https://fluxcd.io/flux/get-started/
- **Flux Slack**: https://cloud-native.slack.com (#flux)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
