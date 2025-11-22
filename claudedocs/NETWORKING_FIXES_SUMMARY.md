# Networking Fixes - Quick Reference

**Date:** 2025-11-20
**Full Report:** `NETWORKING_AUDIT_REPORT.md`

---

## Critical Issues Found

### 1. Frontend Using External HTTPS for Internal API Calls 🔴

**Problem:** Frontend apps are calling backend APIs via `https://api.fa.pesulabs.net` instead of internal DNS.

**Why Bad:**
- Goes through browser → Traefik → backend (slow, fragile)
- Creates dependency on external DNS and certificates
- Causes hairpin NAT issues
- Unnecessary TLS overhead

**Fix Required:**

**File:** `/infrastructure/kubernetes/family-assistant-admin/deployment.yaml`
```yaml
# BEFORE (WRONG):
- name: NEXT_PUBLIC_API_URL
  value: "https://api.fa.pesulabs.net"

# AFTER (CORRECT):
- name: NEXT_PUBLIC_API_URL
  value: "http://family-assistant.homelab.svc.cluster.local:8001"
```

**ConfigMap:** Update `family-assistant-config` in namespace `family-assistant-app`
```yaml
# BEFORE (WRONG):
VITE_API_BASE_URL: https://family-assistant.homelab.pesulabs.net
VITE_WS_URL: wss://family-assistant.homelab.pesulabs.net

# AFTER (CORRECT):
VITE_API_BASE_URL: http://family-assistant-backend.homelab.svc.cluster.local:8001
VITE_WS_URL: ws://family-assistant-backend.homelab.svc.cluster.local:8001
```

---

### 2. Authentik Using Short Hostnames 🔴

**Problem:** Authentik uses `authentik-redis` instead of FQDN `authentik-redis.authentik.svc.cluster.local`

**Why Bad:**
- Relies on DNS search path (fragile)
- Breaks if services move to different namespaces
- Namespace ambiguity

**Fix Required:**

**Authentik Deployment:**
```yaml
# BEFORE (WRONG):
- name: AUTHENTIK_REDIS__HOST
  value: authentik-redis
- name: AUTHENTIK_POSTGRESQL__HOST
  value: authentik-postgresql

# AFTER (CORRECT):
- name: AUTHENTIK_REDIS__HOST
  value: "authentik-redis.authentik.svc.cluster.local"
- name: AUTHENTIK_POSTGRESQL__HOST
  value: "authentik-postgresql.authentik.svc.cluster.local"
```

---

### 3. Duplicate Ingress Resources 🟡

**Problem:** Multiple ingress configurations exist for the same services.

**Files to Clean:**
- `/infrastructure/kubernetes/traefik/ingress-routes.yaml` - Remove old Ingress (keep IngressRoute)
- `/infrastructure/kubernetes/family-assistant-app/ingress-http.yaml` - Delete
- `/services/ingress-fix.yaml` - Delete
- `/infrastructure/kubernetes/ingress-acme-fix.yaml` - Delete

**Keep Only:** IngressRoute resources (Traefik-native)

---

## Good Examples to Follow ✅

### Perfect Backend Configuration
**File:** `/infrastructure/kubernetes/family-assistant/deployment.yaml`

```yaml
env:
- name: POSTGRES_HOST
  value: postgres.homelab.svc.cluster.local  # ✅ FQDN
- name: REDIS_HOST
  value: redis.homelab.svc.cluster.local  # ✅ FQDN
- name: QDRANT_URL
  value: http://qdrant.homelab.svc.cluster.local:6333  # ✅ HTTP + FQDN
- name: LLAMACPP_BASE_URL
  value: "http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080"  # ✅ Cross-namespace FQDN
```

**Score:** 100/100 - Perfect compliance

---

### Perfect IngressRoute Configuration
```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: admin-dashboard
  namespace: homelab
spec:
  entryPoints:
    - websecure  # ✅ HTTPS for external traffic
  routes:
    - match: Host(`admin.fa.pesulabs.net`)
      kind: Rule
      services:
        - name: family-admin  # ✅ Internal service name
          port: 3000
  tls:
    certResolver: default  # ✅ Cloudflare DNS-01
```

---

## Quick Action Checklist

### Phase 1: CRITICAL (Do This Week)
- [ ] Update `family-assistant-admin` deployment with internal API URL
- [ ] Update `family-assistant-config` ConfigMap with internal URLs
- [ ] Update Authentik deployment with FQDN service names
- [ ] Restart affected pods
- [ ] Validate frontend can reach backend via internal DNS
- [ ] Test external access still works

### Phase 2: Cleanup (Next Week)
- [ ] Remove duplicate Ingress resources
- [ ] Consolidate IngressRoute configs into single file
- [ ] Delete unused ingress-*.yaml files
- [ ] Document the single source of truth location

### Phase 3: Enhancement (Future)
- [ ] Standardize service ports (map to 80 where appropriate)
- [ ] Implement NetworkPolicies for security
- [ ] Consider service mesh for advanced features

---

## Validation Commands

```bash
# Test internal DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup family-assistant-backend.homelab.svc.cluster.local

# Test internal HTTP connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://family-assistant-backend.homelab.svc.cluster.local:8001/health

# Check IngressRoute status
kubectl get ingressroute -A

# Verify certificates
kubectl get certificate -A
```

---

## The Golden Rules (Quick Reference)

### Rule 1: Internal vs External Separation

**Internal Traffic (Service-to-Service):**
- ✅ Use: `http://<service>.<namespace>.svc.cluster.local:<port>`
- ❌ Never: `https://<subdomain>.pesulabs.net`
- ❌ Never: IP addresses

**External Traffic (User-to-Service):**
- ✅ Use: `https://<subdomain>.pesulabs.net`
- ✅ Via: Traefik IngressRoute with TLS

### Rule 2: TLS Strategy
- External: HTTPS via Traefik with Let's Encrypt (Cloudflare DNS-01)
- Internal: HTTP only (no TLS overhead)

### Rule 3: Port Standardization
- Web UI: 80
- API: 8080
- Metrics: 9090
- Databases: Standard ports (5432, 6379, etc.)

---

## Impact Assessment

### Before Fixes
- **Reliability:** Poor (external dependencies for internal calls)
- **Performance:** Degraded (unnecessary routing and TLS)
- **Maintainability:** Confusing (multiple configs)

### After Fixes
- **Reliability:** Excellent (internal DNS always works)
- **Performance:** Optimal (direct internal routing)
- **Maintainability:** Clean (single source of truth)

---

**Next Step:** Review full report in `NETWORKING_AUDIT_REPORT.md` and execute Phase 1 fixes.
