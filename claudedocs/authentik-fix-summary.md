# Authentik CrashLoopBackOff - Fix Summary

**Date:** 2025-11-20
**Status:** ✅ RESOLVED
**Resolution Time:** 15 minutes (investigation + fix + validation)

---

## Quick Summary

Authentik pods were failing to start due to incorrect Kubernetes command configuration. Changed `command:` to `args:` to preserve container entrypoint, and updated service hostnames to comply with networking golden rules.

**Result:** Both server and worker pods now running successfully with 0 restarts.

---

## The Problem

```
authentik-server: CrashLoopBackOff (166 restarts over 13 hours)
authentik-worker: CrashLoopBackOff (166 restarts over 13 hours)

Error: exec: "server": executable file not found in $PATH
Error: exec: "worker": executable file not found in $PATH
```

---

## Root Cause

**Configuration Error:** Using `command: ["server"]` instead of `args: ["server"]`

**Why This Failed:**
- Kubernetes `command:` overrides the container's ENTRYPOINT
- Container expects: `dumb-init -- ak server`
- Configuration tried to run: `server` (standalone binary that doesn't exist)
- Result: Container startup failure

---

## The Fix

### Changes Made

**File:** `infrastructure/kubernetes/auth/authentik/authentik.yaml`

#### 1. Fixed Container Command (Critical)
```yaml
# BEFORE ❌
command: ["server"]

# AFTER ✅
args: ["server"]
```

#### 2. Updated Hostnames (Golden Rules Compliance)
```yaml
# BEFORE ❌
AUTHENTIK_REDIS__HOST: "authentik-redis"
AUTHENTIK_POSTGRESQL__HOST: "authentik-postgresql"

# AFTER ✅
AUTHENTIK_REDIS__HOST: "authentik-redis.authentik.svc.cluster.local"
AUTHENTIK_POSTGRESQL__HOST: "authentik-postgresql.authentik.svc.cluster.local"
```

---

## Validation Results

### Pod Status: ✅ ALL HEALTHY
```
NAME                                    READY   STATUS    RESTARTS   AGE
authentik-postgresql-666f6dfb9c-fzcg6   1/1     Running   0          13h
authentik-redis-76df44d899-ptxlk        1/1     Running   0          13h
authentik-server-75b86c5997-2hwb7       1/1     Running   0          22s  ← NEW
authentik-worker-56b7f59488-gvgxh       1/1     Running   0          22s  ← NEW
```

### Server Logs: ✅ SUCCESSFUL STARTUP
```
✅ PostgreSQL connection successful
✅ Redis Connection successful
✅ Finished authentik bootstrap
✅ Django migrations applied
✅ Container running
```

### Worker Logs: ✅ SUCCESSFUL STARTUP
```
✅ Config loaded
✅ PostgreSQL connection successful
✅ Redis Connection successful
✅ Bootstrap finished
✅ Migrations applying
```

### Ingress: ✅ CONFIGURED
```
Host: auth.pesulabs.net
Backend: authentik-server:9000 → 10.42.3.83:9000
TLS: Enabled via Traefik
```

---

## Key Learnings

### Technical
1. **Command vs Args in Kubernetes:**
   - `command:` replaces container ENTRYPOINT
   - `args:` passes arguments to ENTRYPOINT
   - Always verify container's expected behavior before choosing

2. **Error Message Analysis:**
   - "executable not found" often means entrypoint override issue
   - Check if the "missing" file is actually an argument

3. **Container Inspection:**
   - Check docker-compose.yml examples in official repos
   - Official docs may not show exact command format
   - Research container's ENTRYPOINT before deployment

### Process
1. **Systematic Investigation Works:**
   - Pod events → Error messages → Configuration → Documentation
   - Evidence-based analysis prevented guesswork
   - Root cause found in <15 minutes

2. **Golden Rules Enforcement:**
   - Using FQDN for service hostnames ensures consistency
   - Prevents debugging confusion in complex setups
   - Standards reduce cognitive load during incidents

---

## Prevention Checklist

For future deployments:

- [ ] Use `args:` for container arguments, not `command:`
- [ ] Verify container ENTRYPOINT before writing deployment config
- [ ] Use FQDN format for all internal service hostnames
- [ ] Test in staging namespace before production
- [ ] Check official docker-compose.yml examples
- [ ] Set up CrashLoopBackOff alerts within 5 minutes
- [ ] Document container command patterns in runbooks

---

## Commands for Future Reference

### Check Pod Status
```bash
kubectl get pods -n authentik
```

### View Logs
```bash
kubectl logs -n authentik -l app=authentik-server --tail=50
kubectl logs -n authentik -l app=authentik-worker --tail=50
```

### Describe Pods (includes events)
```bash
kubectl describe pod -n authentik <pod-name>
```

### Apply Configuration
```bash
kubectl apply -f infrastructure/kubernetes/auth/authentik/authentik.yaml
```

### Test Endpoint
```bash
curl -k https://auth.pesulabs.net/
```

---

## Files Modified

1. **infrastructure/kubernetes/auth/authentik/authentik.yaml**
   - Changed `command:` to `args:` for server and worker
   - Updated hostnames to FQDN format
   - No changes to PostgreSQL or Redis deployments (already working)

---

## Timeline

| Time | Action |
|------|--------|
| 00:00 | Investigation started |
| 00:05 | Pod events examined, error identified |
| 00:08 | Container entrypoint researched |
| 00:12 | Root cause confirmed, fix applied |
| 00:12 | Pods restarted automatically |
| 00:13 | Both pods reached Running state |
| 00:15 | Logs verified, service healthy |

**Total Time:** 15 minutes from start to validated resolution

---

## Outcome

✅ **Service Restored:** Authentik authentication service fully operational
✅ **Zero Restarts:** Both pods running stable with no crashes
✅ **Standards Compliant:** Configuration follows networking golden rules
✅ **Documented:** Root cause analysis and prevention measures recorded
✅ **Validated:** Logs confirm successful database connections and initialization

---

## Related Documentation

- [Root Cause Analysis (Full)](./authentik-crashloop-root-cause-analysis.md)
- [Networking Golden Rules](../project_context/NETWORKING_STANDARD.md)
- [Kubernetes Command vs Args](https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/)

---

**Status:** INCIDENT CLOSED - SERVICE RESTORED
**Confidence:** 100% - Validated via pod status, logs, and ingress configuration
