# Deployment Quick Reference

**Last Updated**: 2025-12-03

---

## Family Portal Deployment

### ✅ Automated Deployment (Recommended)

**To deploy a new version:**
```bash
# 1. Make your changes
cd apps/family-portal
# ... edit files ...

# 2. Commit and push
git add .
git commit -m "feat: Your feature description"
git push

# That's it! GitHub Actions + Flux CD handle the rest automatically.
```

**What happens automatically:**
1. GitHub Actions builds and pushes image to ghcr.io (~2-5 min)
2. Flux CD detects changes and reconciles (~1 min)
3. Kubernetes pulls new image and deploys

**Verify deployment:**
```bash
# Check workflow status
gh run list --workflow="Build and Push Family Portal" --limit 1

# Check pod status
kubectl get pods -n fa-platform -l app=family-assistant-app

# Test endpoint
curl -s -o /dev/null -w "%{http_code}" https://app.fa.pesulabs.net
# Should return: 200
```

### 🚨 Manual Deployment (Emergency Only)

**If automated pipeline is broken:**
```bash
# Build and push manually
cd apps/family-portal
docker build -t ghcr.io/pesuga/homelab/family-portal:latest -f Dockerfile.simple .
docker push ghcr.io/pesuga/homelab/family-portal:latest

# Force Kubernetes to restart
kubectl rollout restart deployment/family-assistant-app -n fa-platform
```

### 🔄 Rollback

**Quick rollback to previous version:**
```bash
kubectl rollout undo deployment/family-assistant-app -n fa-platform
```

---

## CI/CD Pipeline Status

### Current Configuration

| Component | Status | Details |
|-----------|--------|---------|
| GitHub Actions | ✅ Active | Workflow ID: 212575249 |
| Image Registry | ✅ ghcr.io | ghcr.io/pesuga/homelab/family-portal |
| Flux CD | ✅ Active | 1-minute sync interval |
| Deployment | ✅ Active | fa-platform namespace |
| Image Pull | ✅ Always | imagePullPolicy: Always |

### Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/build-family-portal.yaml` | GitHub Actions workflow |
| `apps/family-portal/Dockerfile.simple` | Docker build configuration |
| `infrastructure/kubernetes/apps/family-assistant/app/deployment.yaml` | Kubernetes deployment |
| `apps/family-portal/src/lib/auth.ts` | ⚠️ Force-tracked (was gitignored) |
| `apps/family-portal/src/lib/api.ts` | ⚠️ Force-tracked (was gitignored) |

---

## Troubleshooting

### Build Fails

**Check GitHub Actions:**
```bash
gh run list --workflow="Build and Push Family Portal" --limit 5
gh run view <run-id> --log-failed
```

**Common issues:**
- TypeScript errors → Fix type annotations in code
- Missing files → Verify `git ls-files apps/family-portal/src/lib/`
- Dependency errors → Check package-lock.json is committed

### Pod Not Updating

**Force reconciliation:**
```bash
# Force Flux to sync
flux reconcile kustomization infrastructure

# Force Kubernetes to restart
kubectl rollout restart deployment/family-assistant-app -n fa-platform
```

### Application Error

**Check logs:**
```bash
kubectl logs -f -n fa-platform -l app=family-assistant-app
```

---

## Important Notes

⚠️ **Critical Files**: `apps/family-portal/src/lib/*.ts` files are force-tracked in Git (excluded by `.gitignore` pattern `lib/`). If these files are removed from Git, builds will fail.

✅ **Zero Manual Steps**: Once code is pushed, everything is automated. No need to manually build, push, or deploy.

📊 **Monitoring**: Check GitHub Actions tab for build status, kubectl for pod status.

---

## Full Documentation

See `claudedocs/FAMILY_PORTAL_DEPLOYMENT.md` for complete details including:
- Detailed troubleshooting procedures
- Rollback procedures
- Security scanning
- Configuration updates
- Best practices
