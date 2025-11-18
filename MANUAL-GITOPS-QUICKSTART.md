# Manual GitOps Quick Start

**⚠️ Active**: Manual workflow until Flux Git sync resolved

## Quick Deployment

```bash
# 1. Edit manifest
vim infrastructure/kubernetes/service-name/deployment.yaml

# 2. Commit changes
git add infrastructure/kubernetes/service-name/
git commit -m "Update service-name: description"
git push origin main

# 3. Deploy using helper script
./scripts/manual-deploy.sh service-name

# 4. Verify
./scripts/verify-deployment.sh service-name
```

## Common Commands

```bash
# Deploy service
./scripts/manual-deploy.sh <service-name> [namespace]

# Verify deployment
./scripts/verify-deployment.sh <service-name> [namespace]

# Manual kubectl apply
kubectl apply -k infrastructure/kubernetes/<service-name>/

# Check status
kubectl get pods -n homelab
kubectl get svc -n homelab

# View logs
kubectl logs -n homelab deployment/<service-name>

# Rollback
git revert HEAD && git push
kubectl apply -k infrastructure/kubernetes/<service-name>/
```

## File Locations

- **Workflow Guide**: `docs/MANUAL-GITOPS-WORKFLOW.md`
- **Network Investigation**: `docs/FLUX-NETWORK-INVESTIGATION.md`
- **Helper Scripts**: `scripts/manual-deploy.sh`, `scripts/verify-deployment.sh`
- **Phase 2 Plan**: `docs/PHASE2-ARCHITECTURE-PLAN.md`

## Flux Status

```bash
# Check Flux health
flux check

# View controllers
kubectl get pods -n flux-system

# Check GitRepository (will show timeout error)
kubectl get gitrepository -n flux-system
```

## Migration to Full GitOps

When network issue resolved:
1. Verify: `flux get sources git`
2. Enable: Flux auto-syncs from Git
3. Cleanup: Manual scripts become optional

---

**Quick Help**: `cat docs/MANUAL-GITOPS-WORKFLOW.md | less`