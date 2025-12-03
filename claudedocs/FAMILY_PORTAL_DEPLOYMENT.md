# Family Portal Deployment Guide

**Last Updated**: 2025-12-03
**Status**: ✅ Fully Automated CI/CD Pipeline

---

## Overview

The Family Portal uses a fully automated GitOps deployment pipeline:
1. Code changes pushed to `apps/family-portal/**` trigger GitHub Actions
2. GitHub Actions builds and pushes Docker image to GitHub Container Registry (ghcr.io)
3. Flux CD automatically reconciles Kubernetes manifests from Git
4. Kubernetes pulls the latest image and deploys the updated application

---

## Automated Deployment Process

### How to Deploy a New Version

**Simple Process**:
1. Make changes to code in `apps/family-portal/` directory
2. Commit and push to `main` branch
3. GitHub Actions automatically builds and pushes new image
4. Flux CD reconciles within 1 minute
5. Kubernetes automatically pulls and deploys new image (due to `imagePullPolicy: Always`)

**Example**:
```bash
# Make your code changes
cd /home/pesu/Rakuflow/systems/homelab/apps/family-portal
# ... edit files ...

# Commit and push
git add .
git commit -m "feat: Add new feature to Family Portal"
git push

# GitHub Actions will automatically:
# - Build the application (npm ci && vite build)
# - Build Docker image
# - Push to ghcr.io/pesuga/homelab/family-portal:latest
# - Run security scan (Trivy)

# Flux will automatically (within 1 minute):
# - Detect the Git repository change
# - Reconcile Kubernetes manifests
# - Kubernetes will pull new image and rolling update pods
```

---

## CI/CD Pipeline Components

### 1. GitHub Actions Workflow

**Location**: `.github/workflows/build-family-portal.yaml`

**Triggers**:
- **Automatic**: Push to `main` branch with changes in:
  - `apps/family-portal/**`
  - `.github/workflows/build-family-portal.yaml`
- **Manual**: Workflow dispatch via GitHub Actions UI

**What It Does**:
1. Checks out repository
2. Sets up Node.js 18 with npm caching
3. Builds application:
   ```bash
   npm ci
   npx vite build
   ```
4. Builds multi-platform Docker image (amd64/arm64)
5. Pushes to `ghcr.io/pesuga/homelab/family-portal:latest`
6. Runs Trivy vulnerability scan
7. Uploads security results to GitHub Security tab

**Authentication**:
- Uses `GITHUB_TOKEN` (automatically provided by GitHub Actions)
- No additional secrets required
- Permissions: `contents: read`, `packages: write`, `security-events: write`

### 2. Docker Build Configuration

**Dockerfile**: `apps/family-portal/Dockerfile.simple`

**Build Context**: `apps/family-portal/`

**Multi-stage Build**:
1. Build stage: Vite builds React app
2. Runtime stage: Nginx serves static files

**Image Tags**:
- `ghcr.io/pesuga/homelab/family-portal:latest` (always points to main branch)
- `ghcr.io/pesuga/homelab/family-portal:main-<git-sha>` (specific commit)
- `ghcr.io/pesuga/homelab/family-portal:main` (main branch tag)

### 3. Kubernetes Deployment

**Location**: `infrastructure/kubernetes/apps/family-assistant/app/deployment.yaml`

**Key Configuration**:
```yaml
spec:
  containers:
    - name: app
      image: ghcr.io/pesuga/homelab/family-portal:latest
      imagePullPolicy: Always  # CRITICAL: Always pull latest image
```

**Why `imagePullPolicy: Always`**:
- Ensures Kubernetes always checks for new image versions
- Since we use `:latest` tag, this ensures deployments get the newest build
- Without this, Kubernetes might use cached older versions

**Rollout Strategy**:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0  # Zero downtime deployments
    maxSurge: 1        # One extra pod during rollout
```

### 4. Flux CD Configuration

**GitRepository Source**: `flux-system`
- Repository: `github.com/pesuga/homelab`
- Branch: `main`
- Sync interval: 1 minute

**Kustomization**: `infrastructure`
- Path: `infrastructure/kubernetes/apps/family-assistant`
- Includes: `app/deployment.yaml`, `app/service.yaml`, `app/ingress.yaml`

**How Flux Works**:
1. Every 1 minute, Flux checks Git repository for changes
2. If manifests changed, Flux applies updates to Kubernetes
3. Kubernetes detects image change (via `imagePullPolicy: Always`)
4. Kubernetes performs rolling update with new pods
5. Old pods terminated after new pods ready

---

## Critical Files for Deployment

### Source Code Files (Must Be Tracked in Git)

**IMPORTANT**: These files were previously excluded by `.gitignore` pattern `lib/`

These files are **force-added** to Git and must remain tracked:
- `apps/family-portal/src/lib/auth.ts` - Authentication logic
- `apps/family-portal/src/lib/api.ts` - API client

**Verification**:
```bash
git ls-files apps/family-portal/src/lib/
# Should show:
# apps/family-portal/src/lib/api.ts
# apps/family-portal/src/lib/auth.ts
```

**If Files Missing**:
```bash
# Force add them back
git add -f apps/family-portal/src/lib/auth.ts
git add -f apps/family-portal/src/lib/api.ts
git commit -m "fix: Re-add critical lib files excluded by gitignore"
```

### Configuration Files

1. **Package Files**:
   - `apps/family-portal/package.json`
   - `apps/family-portal/package-lock.json`

2. **Build Configuration**:
   - `apps/family-portal/vite.config.ts`
   - `apps/family-portal/tsconfig.json`

3. **Docker Configuration**:
   - `apps/family-portal/Dockerfile.simple`

4. **Kubernetes Manifests**:
   - `infrastructure/kubernetes/apps/family-assistant/app/deployment.yaml`
   - `infrastructure/kubernetes/apps/family-assistant/app/service.yaml`
   - `infrastructure/kubernetes/apps/family-assistant/app/ingress.yaml`
   - `infrastructure/kubernetes/apps/family-assistant/kustomization.yaml`

---

## Troubleshooting

### Build Fails in GitHub Actions

**Symptom**: GitHub Actions workflow fails during npm build

**Common Causes**:
1. **Missing files**: Check if `src/lib/` files are tracked in Git
   ```bash
   git ls-files apps/family-portal/src/lib/
   ```

2. **TypeScript errors**: Check workflow logs for type errors
   - Fix type annotations in source code
   - Ensure strict mode compliance

3. **Dependency issues**: Check package-lock.json is committed
   ```bash
   git status apps/family-portal/package-lock.json
   ```

**Fix**: Review GitHub Actions logs, fix errors, commit and push

### Pod Not Updating After Push

**Symptom**: Code changes pushed but pod still running old version

**Diagnostic Steps**:
1. Check if GitHub Actions workflow completed:
   ```bash
   gh workflow view "Build and Push Family Portal"
   gh run list --workflow="Build and Push Family Portal" --limit 5
   ```

2. Check if Flux reconciled:
   ```bash
   flux get kustomizations
   flux reconcile kustomization infrastructure
   ```

3. Check pod image:
   ```bash
   kubectl describe pod -n fa-platform -l app=family-assistant-app | grep "Image:"
   ```

4. Check image digest:
   ```bash
   kubectl get pod -n fa-platform -l app=family-assistant-app -o jsonpath='{.items[0].status.containerStatuses[0].imageID}'
   ```

**Common Fixes**:
- Wait for GitHub Actions to complete (~2-5 minutes)
- Force Flux reconciliation: `flux reconcile kustomization infrastructure`
- Restart deployment: `kubectl rollout restart deployment/family-assistant-app -n fa-platform`

### Image Pull Errors

**Symptom**: Pod shows `ImagePullBackOff` or `ErrImagePull`

**Diagnostic Steps**:
```bash
kubectl describe pod -n fa-platform -l app=family-assistant-app
# Look for "Events" section with pull errors
```

**Common Causes**:
1. **Image doesn't exist**: Check if GitHub Actions pushed image
2. **Authentication issue**: Verify imagePullSecrets (should not be needed for public ghcr.io)
3. **Network issue**: Check node internet connectivity

**Fix**:
- Verify image exists: `docker manifest inspect ghcr.io/pesuga/homelab/family-portal:latest`
- Check GitHub Actions logs for push step
- Make repository/package public in GitHub settings

### Application Not Loading (404/502)

**Symptom**: https://app.fa.pesulabs.net returns error

**Diagnostic Steps**:
1. Check pod status:
   ```bash
   kubectl get pods -n fa-platform -l app=family-assistant-app
   ```

2. Check pod logs:
   ```bash
   kubectl logs -n fa-platform -l app=family-assistant-app
   ```

3. Check service endpoints:
   ```bash
   kubectl get endpoints -n fa-platform family-assistant-app
   ```

4. Check ingress:
   ```bash
   kubectl get ingressroute -n fa-platform family-assistant-app-ingress
   ```

**Common Fixes**:
- Pod not running: Check pod logs and fix errors
- Service selector mismatch: Verify labels match between deployment and service
- Ingress misconfiguration: Verify IngressRoute points to correct service/port

---

## Manual Deployment (Emergency)

If automated pipeline fails and you need to deploy manually:

### Option 1: Manual GitHub Actions Trigger
1. Go to GitHub Actions tab
2. Select "Build and Push Family Portal" workflow
3. Click "Run workflow"
4. Select branch and environment
5. Wait for completion
6. Flux will auto-reconcile

### Option 2: Manual Image Build and Deploy
```bash
# Build and push manually
cd apps/family-portal
npm ci
npm run build
docker build -t ghcr.io/pesuga/homelab/family-portal:latest -f Dockerfile.simple .
docker push ghcr.io/pesuga/homelab/family-portal:latest

# Force Kubernetes to pull new image
kubectl rollout restart deployment/family-assistant-app -n fa-platform
kubectl rollout status deployment/family-assistant-app -n fa-platform
```

### Option 3: Direct kubectl Apply (Not Recommended)
```bash
# Only use if Flux is broken
kubectl apply -k infrastructure/kubernetes/apps/family-assistant/app/
```

---

## Monitoring Deployments

### Check Deployment Status
```bash
# Watch pod rollout
kubectl rollout status deployment/family-assistant-app -n fa-platform

# Check pod status
kubectl get pods -n fa-platform -l app=family-assistant-app

# Check pod events
kubectl describe pod -n fa-platform -l app=family-assistant-app

# Check application logs
kubectl logs -f -n fa-platform -l app=family-assistant-app
```

### Verify Deployment Success
```bash
# Check HTTP status
curl -s -o /dev/null -w "%{http_code}" https://app.fa.pesulabs.net
# Should return: 200

# Check content
curl -s https://app.fa.pesulabs.net | head -n 5
# Should return: HTML with "Family Assistant" title

# Check image version
kubectl get pod -n fa-platform -l app=family-assistant-app -o jsonpath='{.items[0].spec.containers[0].image}'
# Should return: ghcr.io/pesuga/homelab/family-portal:latest
```

---

## Security Scanning

### Automatic Scanning
- Trivy vulnerability scanner runs on every build
- Results uploaded to GitHub Security tab
- Scans for CRITICAL and HIGH severity vulnerabilities

### View Scan Results
1. Go to GitHub repository
2. Click "Security" tab
3. Click "Code scanning"
4. View Trivy results

### Manual Scan
```bash
# Scan latest image
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image ghcr.io/pesuga/homelab/family-portal:latest
```

---

## Configuration Updates

### Update Environment Variables
1. Edit `infrastructure/kubernetes/apps/family-assistant/app/deployment.yaml`
2. Add/modify `env:` section under container spec
3. Commit and push
4. Flux auto-applies changes

### Update Resource Limits
1. Edit `deployment.yaml` resources section:
   ```yaml
   resources:
     requests:
       cpu: 50m
       memory: 64Mi
     limits:
       cpu: 100m
       memory: 128Mi
   ```
2. Commit and push
3. Flux auto-applies changes

### Update Replica Count
1. Edit `deployment.yaml`:
   ```yaml
   spec:
     replicas: 2  # Increase for HA
   ```
2. Commit and push
3. Flux auto-applies changes

---

## Rollback Procedure

### Rollback to Previous Deployment
```bash
# View rollout history
kubectl rollout history deployment/family-assistant-app -n fa-platform

# Rollback to previous version
kubectl rollout undo deployment/family-assistant-app -n fa-platform

# Rollback to specific revision
kubectl rollout undo deployment/family-assistant-app -n fa-platform --to-revision=2
```

### Rollback to Specific Git Commit
```bash
# Revert deployment.yaml to specific commit
git revert <commit-hash> -- infrastructure/kubernetes/apps/family-assistant/app/deployment.yaml
git commit -m "rollback: Revert Family Portal to working version"
git push

# Flux will auto-apply the reverted version
```

### Rollback to Specific Image Version
```bash
# If you tagged images with git SHA
kubectl set image deployment/family-assistant-app -n fa-platform \
  app=ghcr.io/pesuga/homelab/family-portal:main-<git-sha>

# Or edit deployment.yaml and change image tag
```

---

## Best Practices

### Development Workflow
1. **Test locally first**: Use `npm run dev` to test changes
2. **Commit atomically**: One feature/fix per commit
3. **Write descriptive commits**: Helps track deployment history
4. **Monitor deployments**: Watch GitHub Actions and pod status

### Deployment Safety
1. **Always test builds**: Verify GitHub Actions completes successfully
2. **Monitor logs**: Check pod logs after deployment
3. **Health checks**: Verify https://app.fa.pesulabs.net returns 200 OK
4. **Keep rollback ready**: Know how to revert if issues occur

### Git Hygiene
1. **Never remove src/lib/ from tracking**: These files are critical
2. **Keep package-lock.json committed**: Ensures reproducible builds
3. **Update this documentation**: Document any process changes

---

## Summary

**For Next Deployment**:
1. Edit code in `apps/family-portal/`
2. Commit and push to `main`
3. GitHub Actions builds and pushes image (~2-5 minutes)
4. Flux reconciles and Kubernetes deploys (~1 minute)
5. Verify at https://app.fa.pesulabs.net

**No manual intervention required** - fully automated pipeline!

**Emergency Contact**:
- GitHub Actions: https://github.com/pesuga/homelab/actions
- Flux Status: `flux get all -A`
- Pod Logs: `kubectl logs -n fa-platform -l app=family-assistant-app`
