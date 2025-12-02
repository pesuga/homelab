# Pod Startup Troubleshooting Report

**Date:** 2025-11-30
**Status:** ✅ Resolved

## 1. Problem Description

After resolving the cluster networking and TLS certificate issues, the services were still not accessible via Traefik ("No available server"). Investigation revealed two distinct issues with the application pods:

1.  **Family Assistant API (`family-assistant-api`)**: Pod was running but **Not Ready** (`0/1`).
2.  **Family Assistant Admin (`family-assistant-admin`)**: Pod was in **CrashLoopBackOff** loop.

## 2. Investigation & Root Cause Analysis

### Family Assistant API
- **Symptom:** Readiness probe failing with `404 Not Found`, pod Running but 0/1.
- **Diagnosis:** Running pod had readiness probe checking `/ready`, but deployment.yaml already specified `/health`.
- **Root Cause 1:** Pod was from old deployment - needed rollout to apply updated probe configuration.
- **Root Cause 2:** Service selector mismatch - service used `app: family-assistant-api` but pod had `app.kubernetes.io/name: family-assistant-api`.
- **Fix 1:** Redeployed API pod with `kubectl apply -f deployment.yaml` (triggers rollout).
- **Fix 2:** Updated service.yaml namespace from `family-assistant-api` to `fa-platform` and applied.
- **Result:** Pod now 1/1 Ready, service endpoints populated, external access via Traefik working.
- **Status:** ✅ Resolved - API accessible at https://api.fa.pesulabs.net/health

### Family Assistant Admin
- **Symptom:** Pod restarts continuously (367 restarts in 24h), CrashLoopBackOff.
- **Logs:** Next.js starts successfully and reports "Ready in 385ms".
- **Diagnosis:**
  - Pod events showed `Liveness probe failed: dial tcp 10.42.2.55:80: connect: connection refused`
  - App runs on port 3000 but liveness probe checked port 80
  - Running pod had different config than deployment.yaml
- **Root Cause:** Liveness probe port mismatch - probe checked port 80, app listens on port 3000.
- **Fix:** Used `kubectl patch deployment family-assistant-admin` to update both liveness and readiness probe ports to 3000.
- **Result:** New pod rolled out successfully, now 1/1 Running with 0 restarts.
- **Status:** ✅ Resolved - Admin accessible at https://admin.fa.pesulabs.net/

## 3. Resolution Summary

### Actions Taken
1. **API Pod:**
   - Applied deployment.yaml to trigger rollout with correct probe config
   - Fixed service.yaml namespace mismatch (family-assistant-api → fa-platform)
   - Applied updated service to populate endpoints

2. **Admin Pod:**
   - Patched deployment to fix liveness/readiness probe ports (80 → 3000)
   - Waited for automatic rollout to replace crashing pod

### Final Status
```bash
kubectl get pods -n fa-platform
```
- `family-assistant-api-9c7fb649d-5hhgn`: **1/1 Running**
- `family-assistant-admin-65555cddcd-5whcl`: **1/1 Running**

### External Access Verification
- API: https://api.fa.pesulabs.net/health → **200 OK** (status: degraded due to unreachable llamacpp/mem0)
- Admin: https://admin.fa.pesulabs.net/ → **307 Redirect** (app responding)

## 4. Lessons Learned

### Probe Configuration
- **Always verify probe ports match container ports** - most common cause of CrashLoopBackOff
- **Check running pod config vs deployment file** - may be out of sync after manual changes
- Use `kubectl describe pod` to see exact probe failure messages

### Service Configuration
- **Verify service selectors match pod labels** - mismatch causes empty endpoints
- **Check service namespace** - must match pod namespace for endpoint discovery
- Use `kubectl get endpoints` to verify service is discovering pods

### Deployment Mismatch Detection
- Compare `kubectl get deployment -o yaml` vs deployment.yaml files
- Check `kubectl.kubernetes.io/last-applied-configuration` annotation for actual config
- Running config may differ from git-tracked files after manual patches

## 5. Known Issues

### Cross-Node Networking (Unresolved)
Internal pod-to-pod communication fails when pods try to reach services (DNS resolves but connection refused to Tailscale IPs). This is the Flannel VXLAN over Layer 3 Tailscale issue documented in SESSION-STATE.md. However, **external access via Traefik works** because Traefik runs on the same node.

**Workaround:** All Family Assistant pods currently scheduled on same node (pesubuntu), so intra-service communication works.

**Permanent Fix Required:** Switch Flannel backend to wireguard-native (per SESSION-STATE.md).

### Service Dependencies
API health shows "degraded" status due to:
- `llamacpp` unreachable (cross-node networking issue)
- `mem0` unreachable (cross-node networking issue)

These will be resolved when cross-node networking is fixed.

---

## 6. Traefik Certificate Issues - Resolution

**Date**: 2025-11-30 (continued)

### Problem Discovery
After resolving pod startup issues, browser showed certificate warnings for `admin.fa.pesulabs.net`. Investigation revealed:
- **API cert**: Valid Let's Encrypt production certificate ✅
- **Admin cert**: Self-signed Traefik default certificate ❌

### Root Cause Analysis

**Issue 1: Let's Encrypt Staging Server**
```bash
# Traefik deployment was configured with staging URL
--certificatesresolvers.letsencrypt.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory
```
This caused Traefik to request staging certificates instead of production ones.

**Issue 2: Cloudflare API Token Format**
```bash
# Secret contained comments and instructions instead of clean token
kubectl get secret cloudflare-api-token -n kube-system -o jsonpath='{.data.api-token}' | base64 -d
# Output showed:
# Add your Cloudflare API token here:
# ... instructions ...
CLOUDFLARE_API_TOKEN=4bYCeveMKuDhdT7XDioeHT5fPlWdRedwgPwx05hk
```
The secret contained multi-line content with comments, causing `invalid header field value` errors.

**Issue 3: Environment Variable Name**
Traefik expected `CLOUDFLARE_DNS_API_TOKEN` but was configured with `CF_API_TOKEN`.

### Fixes Applied

**1. Remove Staging Server Configuration**
```bash
# Export deployment
kubectl get deployment traefik -n kube-system -o yaml > /tmp/traefik-deployment.yaml

# Remove staging server line
sed -i '/acme.caserver.*staging/d' /tmp/traefik-deployment.yaml

# Apply updated configuration
kubectl apply -f /tmp/traefik-deployment.yaml
```

**2. Clean Cloudflare Secret**
```bash
# Extract clean token from secret
TOKEN=$(kubectl get secret cloudflare-api-token -n kube-system -o jsonpath='{.data.api-token}' | base64 -d | grep "^CLOUDFLARE_API_TOKEN=" | cut -d'=' -f2)

# Recreate secret with clean token only
kubectl delete secret cloudflare-api-token -n kube-system
kubectl create secret generic cloudflare-api-token -n kube-system --from-literal=api-token="$TOKEN"
```

**3. Fix Environment Variable Name**
```bash
# Update deployment to use correct env var name
kubectl set env deployment/traefik -n kube-system \
  --from=secret/cloudflare-api-token \
  --keys=api-token \
  --prefix=CLOUDFLARE_DNS_
```

**4. Restart Traefik**
```bash
# Restart to clear ACME cache (stored in emptyDir) and obtain new certificates
kubectl rollout restart deployment/traefik -n kube-system
```

### Verification

**Certificate Check**:
```bash
# API certificate
echo | openssl s_client -connect api.fa.pesulabs.net:443 -servername api.fa.pesulabs.net 2>/dev/null | openssl x509 -noout -subject -issuer
# Output:
# subject=CN = api.fa.pesulabs.net
# issuer=C = US, O = Let's Encrypt, CN = R13 ✅

# Admin certificate
echo | openssl s_client -connect admin.fa.pesulabs.net:443 -servername admin.fa.pesulabs.net 2>/dev/null | openssl x509 -noout -subject -issuer
# Output:
# subject=CN = admin.fa.pesulabs.net
# issuer=C = US, O = Let's Encrypt, CN = R12 ✅
```

**Traefik Logs**:
```bash
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik --tail=20 | grep -i acme
# No more ACME errors for admin.fa.pesulabs.net
# Using production Let's Encrypt: https://acme-v02.api.letsencrypt.org/directory
```

### Final Status
| Domain | Certificate | Issuer | Status |
|--------|-------------|--------|--------|
| api.fa.pesulabs.net | Let's Encrypt | R13 | ✅ Trusted |
| admin.fa.pesulabs.net | Let's Encrypt | R12 | ✅ Trusted |

**Browser Security**: No more certificate warnings - both sites show secure padlock icon.

### Key Learnings

**Traefik ACME Configuration**:
- Always use production Let's Encrypt unless explicitly testing
- ACME storage in `emptyDir` means certificates are lost on pod restart (use PVC for persistence)
- Staging certificates cause browser warnings and can't be trusted

**Kubernetes Secrets Best Practices**:
- Store only the actual value, not comments or instructions
- Use `--from-literal` for clean single-value secrets
- Validate secret content after creation (`kubectl get secret ... -o jsonpath='{.data.key}' | base64 -d`)

**Environment Variable Naming**:
- Check Traefik/provider documentation for exact env var names
- Different providers expect different naming conventions (CF_*, CLOUDFLARE_*, etc.)
- Use `kubectl exec` to verify env vars are set correctly in running pod

### Prevention Checklist
- [ ] Verify certificate resolver uses production Let's Encrypt (or remove caserver to use default)
- [ ] Test secrets contain clean values: `kubectl get secret NAME -o jsonpath='{.data.KEY}' | base64 -d`
- [ ] Confirm environment variables match provider documentation
- [ ] Use PersistentVolumeClaim for ACME storage to preserve certificates across restarts
- [ ] Monitor Traefik logs for ACME errors after deployment
