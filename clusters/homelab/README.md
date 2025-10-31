# Flux CD Bootstrap Guide

This cluster is configured for GitOps with Flux CD (Option A - Minimal Disruption).

## Prerequisites

1. GitHub Personal Access Token with repo permissions
2. Flux CLI installed (`flux --version`)
3. kubectl configured to access the cluster

## Bootstrap Command

```bash
# Export GitHub token
export GITHUB_TOKEN=<your-github-token>

# Bootstrap Flux to homelab cluster
flux bootstrap github \
  --owner=pesuga \
  --repository=homelab \
  --branch=main \
  --path=./clusters/homelab \
  --personal \
  --private=false \
  --network-policy=false
```

## What Bootstrap Does

1. Installs Flux controllers to `flux-system` namespace
2. Creates `clusters/homelab/flux-system/` directory in Git
3. Commits Flux manifests to repository
4. Configures Flux to watch repository
5. Auto-syncs cluster with Git state

## Manual Bootstrap (if automated fails)

If the bootstrap command fails, you can install Flux manually:

```bash
# Install Flux components
flux install --namespace=flux-system

# Create GitRepository source
flux create source git flux-system \
  --url=https://github.com/pesuga/homelab \
  --branch=main \
  --interval=1m \
  --namespace=flux-system

# Create infrastructure Kustomization
kubectl apply -f clusters/homelab/infrastructure.yaml
```

## Verification

```bash
# Check Flux status
flux check

# View Kustomizations
flux get kustomizations

# View sources
flux get sources all

# Monitor reconciliation
flux logs --follow
```

## Current Status

- ✅ Repository structure created
- ✅ Kustomization files in place
- ✅ Infrastructure manifests organized
- ⏳ Awaiting GitHub token for bootstrap

## Next Steps

1. Generate GitHub Personal Access Token
2. Run bootstrap command
3. Verify Flux controllers deployed
4. Monitor automatic reconciliation
5. Test drift detection and auto-healing

---

**Created**: 2025-10-30
**Author**: Claude Code
**Status**: Ready for bootstrap
