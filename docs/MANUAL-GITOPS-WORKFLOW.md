# Manual GitOps Workflow Guide

**Status**: Active workaround for Flux CD sync issues
**Purpose**: Maintain Git as source of truth while deploying manually
**Duration**: Until network connectivity issue resolved

## Overview

This workflow maintains GitOps principles (Git as source of truth, declarative manifests) while using manual `kubectl apply` commands instead of automatic Flux synchronization.

## Core Principles

1. **Git is Source of Truth**: All changes committed to repository first
2. **Review Before Apply**: Always review changes with `git diff` before deploying
3. **Structured Deployments**: Use Kustomize for organized manifest application
4. **Validation**: Verify deployments after each apply
5. **Documentation**: Track all manual deployments

## Workflow Process

### 1. Make Changes

```bash
# Make changes to Kubernetes manifests
vim infrastructure/kubernetes/service-name/deployment.yaml

# Review changes
git diff
```

### 2. Commit to Git

```bash
# Stage changes
git add infrastructure/kubernetes/service-name/

# Commit with descriptive message
git commit -m "Update service-name deployment: description of changes"

# Push to GitHub
git push origin main
```

### 3. Apply to Cluster

```bash
# Apply single manifest
kubectl apply -f infrastructure/kubernetes/service-name/deployment.yaml

# OR apply entire directory with Kustomize
kubectl apply -k infrastructure/kubernetes/service-name/

# OR apply multiple related manifests
kubectl apply -f infrastructure/kubernetes/service-name/
```

### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n <namespace> -l app=<service-name>

# Check deployment rollout
kubectl rollout status deployment/<deployment-name> -n <namespace>

# Check service endpoints
kubectl get svc -n <namespace>

# View logs if issues
kubectl logs -n <namespace> deployment/<deployment-name> --tail=50
```

### 5. Document Deployment

Add entry to deployment log (optional but recommended for tracking).

## Directory Structure

```
infrastructure/kubernetes/
├── base/
│   └── namespace.yaml
├── databases/
│   ├── postgres/
│   ├── redis/
│   └── qdrant/
├── monitoring/
│   ├── prometheus/
│   ├── loki/
│   └── homelab-dashboard/
├── family-assistant/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── [service-name]/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml (if needed)
    └── kustomization.yaml (optional)
```

## Common Operations

### Deploy New Service

```bash
# 1. Create manifests
mkdir -p infrastructure/kubernetes/new-service
vim infrastructure/kubernetes/new-service/deployment.yaml
vim infrastructure/kubernetes/new-service/service.yaml

# 2. Commit to Git
git add infrastructure/kubernetes/new-service/
git commit -m "Add new-service deployment manifests"
git push

# 3. Apply to cluster
kubectl apply -f infrastructure/kubernetes/new-service/

# 4. Verify
kubectl get pods -n homelab -l app=new-service
kubectl get svc -n homelab new-service
```

### Update Existing Service

```bash
# 1. Edit manifest
vim infrastructure/kubernetes/service-name/deployment.yaml

# 2. Review changes
git diff infrastructure/kubernetes/service-name/deployment.yaml

# 3. Commit
git add infrastructure/kubernetes/service-name/deployment.yaml
git commit -m "Update service-name: new container image v1.2.3"
git push

# 4. Apply
kubectl apply -f infrastructure/kubernetes/service-name/deployment.yaml

# 5. Watch rollout
kubectl rollout status deployment/service-name -n homelab
```

### Rollback Deployment

```bash
# Git-based rollback (recommended)
git revert HEAD
git push
kubectl apply -f infrastructure/kubernetes/service-name/deployment.yaml

# OR kubectl rollback
kubectl rollout undo deployment/service-name -n homelab
```

### Delete Service

```bash
# 1. Delete from cluster
kubectl delete -f infrastructure/kubernetes/service-name/

# 2. Remove from Git (if permanently removing)
git rm -r infrastructure/kubernetes/service-name/
git commit -m "Remove service-name (reason)"
git push
```

## Helper Scripts

### Quick Deployment Script

Location: `scripts/manual-deploy.sh`

```bash
#!/bin/bash
# Usage: ./scripts/manual-deploy.sh <service-name>

SERVICE=$1
MANIFEST_DIR="infrastructure/kubernetes/${SERVICE}"

if [ ! -d "$MANIFEST_DIR" ]; then
    echo "Error: $MANIFEST_DIR does not exist"
    exit 1
fi

echo "Deploying ${SERVICE}..."
kubectl apply -f ${MANIFEST_DIR}/

echo "Waiting for rollout..."
kubectl rollout status deployment/${SERVICE} -n homelab --timeout=300s

echo "Deployment complete. Pod status:"
kubectl get pods -n homelab -l app=${SERVICE}
```

### Verification Script

Location: `scripts/verify-deployment.sh`

```bash
#!/bin/bash
# Usage: ./scripts/verify-deployment.sh <namespace> <deployment-name>

NAMESPACE=$1
DEPLOYMENT=$2

echo "=== Deployment Status ==="
kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE}

echo -e "\n=== Pod Status ==="
kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT}

echo -e "\n=== Service Status ==="
kubectl get svc -n ${NAMESPACE} ${DEPLOYMENT}

echo -e "\n=== Recent Events ==="
kubectl get events -n ${NAMESPACE} --field-selector involvedObject.name=${DEPLOYMENT} --sort-by='.lastTimestamp' | tail -10

echo -e "\n=== Container Logs (last 20 lines) ==="
kubectl logs -n ${NAMESPACE} deployment/${DEPLOYMENT} --tail=20
```

## Best Practices

### 1. Always Review Before Apply
```bash
# Check what will change
kubectl diff -f infrastructure/kubernetes/service-name/

# Dry-run to see what would be created/updated
kubectl apply -f infrastructure/kubernetes/service-name/ --dry-run=client
```

### 2. Use Labels Consistently
```yaml
metadata:
  labels:
    app: service-name
    version: v1.2.3
    managed-by: manual-gitops
```

### 3. Namespace Everything
```yaml
metadata:
  namespace: homelab
```

### 4. Use Kustomization for Organization
```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
```

### 5. Document Changes
- Descriptive git commit messages
- Include ticket/issue numbers if applicable
- Note reason for changes

## Migration Path to Full GitOps

When network issue is resolved:

1. **Verify Flux is syncing**:
   ```bash
   flux get sources git
   flux get kustomizations
   ```

2. **Let Flux take over**:
   - Flux will automatically sync from Git
   - No manual applies needed
   - Drift detection enabled

3. **Monitor transition**:
   ```bash
   watch kubectl get gitrepository -n flux-system
   ```

4. **Cleanup**:
   - Remove manual deployment scripts (optional)
   - Update documentation to reflect automatic sync

## Troubleshooting

### Manifest Doesn't Apply
```bash
# Validate YAML syntax
kubectl apply -f manifest.yaml --dry-run=client --validate=true

# Check for schema errors
kubectl apply -f manifest.yaml --server-dry-run
```

### Pod Won't Start
```bash
# Check events
kubectl describe pod <pod-name> -n homelab

# Check logs
kubectl logs <pod-name> -n homelab

# Check resource limits
kubectl top pods -n homelab
```

### Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints <service-name> -n homelab

# Check pod labels match service selector
kubectl get pods -n homelab --show-labels
```

## Quick Reference

### Essential Commands
```bash
# Apply manifest
kubectl apply -f <file>

# Apply directory
kubectl apply -f <directory>/

# Apply with Kustomize
kubectl apply -k <directory>

# Check status
kubectl get pods -n homelab
kubectl get svc -n homelab
kubectl get deployments -n homelab

# View logs
kubectl logs -n homelab deployment/<name>

# Rollout status
kubectl rollout status deployment/<name> -n homelab

# Rollback
kubectl rollout undo deployment/<name> -n homelab
```

### Git Workflow
```bash
# Check status
git status

# Review changes
git diff

# Stage and commit
git add <files>
git commit -m "message"

# Push to remote
git push origin main

# Pull latest
git pull origin main
```

---

**Last Updated**: 2025-11-17
**Status**: Active
**Migration to Full GitOps**: Pending network issue resolution