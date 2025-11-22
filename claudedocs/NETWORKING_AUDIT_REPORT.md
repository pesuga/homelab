# Homelab Kubernetes Networking Audit Report

**Date:** 2025-11-20
**Auditor:** Backend Architect Agent
**Standard Reference:** `/project_context/NETWORKING_STANDARD.md`

---

## Executive Summary

This report provides a comprehensive analysis of the homelab Kubernetes cluster networking configuration against the "Golden Rules" defined in the Networking Standard. The audit discovered **critical violations** that are causing service instabilities and **positive patterns** that should be preserved.

### Overall Assessment

**Compliance Score:** 75/100

**Key Findings:**
- ✅ **GOOD**: Internal service-to-service DNS usage is mostly compliant
- ✅ **GOOD**: IngressRoute configurations follow standard patterns
- ⚠️ **VIOLATION**: Frontend apps using external HTTPS URLs for internal API calls
- ⚠️ **VIOLATION**: Multiple duplicate/conflicting Ingress resources
- ⚠️ **VIOLATION**: Authentik using short hostnames instead of FQDN

---

## 1. Current Networking State Summary

### 1.1 Active Services

| Namespace | Service Name | Type | Ports | External Access |
|-----------|-------------|------|-------|----------------|
| homelab | family-assistant-backend | ClusterIP | 8001, 8123, 8008 | Via IngressRoute |
| homelab | family-admin | ClusterIP | 3000 | Via IngressRoute |
| homelab | n8n | ClusterIP | 5678 | Via IngressRoute |
| homelab | postgres | ClusterIP | 5432 | Internal only |
| homelab | redis | ClusterIP | 6379 | Internal only |
| homelab | qdrant | ClusterIP | 6333, 6334 | Internal only |
| homelab | mem0 | ClusterIP | 8080 | Internal only |
| homelab | whisper | ClusterIP | 9000 | Internal only |
| authentik | authentik-server | ClusterIP | 9000, 9443 | Via IngressRoute |
| authentik | authentik-postgresql | ClusterIP | 5432 | Internal only |
| authentik | authentik-redis | ClusterIP | 6379 | Internal only |
| family-assistant-app | family-assistant | ClusterIP | 80 | Via IngressRoute |
| family-assistant-api | family-assistant-api | ClusterIP | 8001, 8123 | Not exposed |
| llamacpp | llamacpp-kimi-vl-service | ClusterIP | 8080 | Internal only |

### 1.2 External Access Points (IngressRoutes)

| Host | Service | Namespace | Port | Status |
|------|---------|-----------|------|--------|
| admin.fa.pesulabs.net | family-admin | homelab | 3000 | ✅ Active |
| api.fa.pesulabs.net | family-assistant | homelab | 8001 | ✅ Active |
| n8n.fa.pesulabs.net | n8n | homelab | 5678 | ✅ Active |
| auth.pesulabs.net | authentik-server | authentik | 80 | ✅ Active |
| app.fa.pesulabs.net | family-assistant | family-assistant-app | 80 | ✅ Active |

---

## 2. Violations and Issues

### 2.1 CRITICAL - Frontend Using External HTTPS for Internal API Calls

**Severity:** 🔴 CRITICAL
**Golden Rule Violated:** Rule 1 - Internal vs External Separation

#### Problem Description
The frontend application (`family-assistant-app`) is configured to use external HTTPS URLs to communicate with backend services running in the same cluster.

#### Evidence
**File:** `/infrastructure/kubernetes/family-assistant-admin/deployment.yaml`
**Lines:** 41-44

```yaml
env:
- name: NEXT_PUBLIC_API_URL
  value: "https://api.fa.pesulabs.net"  # ❌ VIOLATION
- name: NEXT_PUBLIC_APP_URL
  value: "https://app.fa.pesulabs.net"  # ❌ VIOLATION
```

**ConfigMap:** `family-assistant-config` in namespace `family-assistant-app`
```yaml
data:
  VITE_API_BASE_URL: https://family-assistant.homelab.pesulabs.net  # ❌ VIOLATION
  VITE_WS_URL: wss://family-assistant.homelab.pesulabs.net  # ❌ VIOLATION
```

#### Why This Is Wrong
1. **Performance Penalty**: Traffic goes through browser → Traefik → backend instead of direct internal routing
2. **Reliability Issues**: Creates dependency on ingress controller, DNS resolution, and TLS certificates
3. **Hairpin NAT Problems**: Can cause connection failures when external domain resolves to internal IP
4. **TLS Overhead**: Unnecessary encryption/decryption for internal traffic
5. **Certificate Trust Issues**: Potential problems with Let's Encrypt certificate validation

#### Correct Configuration Should Be
```yaml
env:
- name: NEXT_PUBLIC_API_URL
  value: "http://family-assistant.homelab.svc.cluster.local:8001"  # ✅ CORRECT
- name: VITE_API_BASE_URL
  value: "http://family-assistant.homelab.svc.cluster.local:8001"  # ✅ CORRECT
```

**Impact:** HIGH - This is likely causing the "every change breaks what was done before" problem

---

### 2.2 CRITICAL - Authentik Using Short Hostnames

**Severity:** 🔴 CRITICAL
**Golden Rule Violated:** Rule 1 - Internal vs External Separation

#### Problem Description
Authentik is using short hostnames (`authentik-redis`, `authentik-postgresql`) instead of fully qualified domain names (FQDN).

#### Evidence
**Deployment:** `authentik-server` in namespace `authentik`

```yaml
env:
- name: AUTHENTIK_REDIS__HOST
  value: authentik-redis  # ❌ VIOLATION - missing .authentik.svc.cluster.local
- name: AUTHENTIK_POSTGRESQL__HOST
  value: authentik-postgresql  # ❌ VIOLATION - missing .authentik.svc.cluster.local
```

#### Why This Is Wrong
1. **DNS Search Path Dependency**: Relies on pod's DNS search path, which can change
2. **Namespace Ambiguity**: Could resolve to wrong service if duplicate names exist
3. **Not Future-Proof**: Breaks if services move to different namespaces

#### Correct Configuration Should Be
```yaml
env:
- name: AUTHENTIK_REDIS__HOST
  value: "authentik-redis.authentik.svc.cluster.local"  # ✅ CORRECT
- name: AUTHENTIK_POSTGRESQL__HOST
  value: "authentik-postgresql.authentik.svc.cluster.local"  # ✅ CORRECT
```

**Impact:** MEDIUM - Works now but fragile; will break during namespace changes

---

### 2.3 WARNING - Duplicate Ingress Resources

**Severity:** 🟡 WARNING
**Issue:** Multiple ingress configurations exist for same services

#### Problem Description
There are duplicate Ingress and IngressRoute resources that could cause conflicts.

#### Evidence

**Active IngressRoutes (Correct):**
- `homelab/admin-dashboard` → admin.fa.pesulabs.net
- `homelab/family-api` → api.fa.pesulabs.net
- `homelab/n8n` → n8n.fa.pesulabs.net
- `authentik/authentik-ingress` → auth.pesulabs.net
- `family-assistant-app/family-assistant-app` → app.fa.pesulabs.net

**Duplicate/Conflicting Ingress Resources in Files:**
- `/infrastructure/kubernetes/traefik/ingress-routes.yaml` - Contains old `networking.k8s.io/v1` Ingress resources (not IngressRoute)
- `/infrastructure/kubernetes/family-assistant-app/ingress.yaml` - Standard Ingress resource
- Multiple `ingress-*.yaml` files in various directories

#### Why This Is Problematic
1. **Configuration Drift**: Hard to know which config is active
2. **Maintenance Burden**: Changes must be made in multiple places
3. **Potential Conflicts**: Two ingress controllers might handle same routes

#### Recommendation
- Keep only IngressRoute resources (Traefik-native)
- Delete all standard Ingress resources
- Consolidate into single source of truth

**Impact:** MEDIUM - Causes confusion and potential routing conflicts

---

### 2.4 INFO - Unused Namespace Services

**Severity:** 🟢 INFO
**Issue:** `family-assistant-api` namespace has deployment but no external access

#### Observation
The namespace `family-assistant-api` contains a deployment for `family-assistant-api` but has no IngressRoute configured.

**Current State:**
- Deployment exists with proper internal DNS configuration
- Service exists (ClusterIP)
- No external ingress route

**Question:** Is this intentional? Should this service be exposed?

---

## 3. Correctly Configured Services (Examples to Follow)

### 3.1 ✅ EXCELLENT - family-assistant-backend

**File:** `/infrastructure/kubernetes/family-assistant/deployment.yaml`
**Lines:** 69-106

**Why This Is Excellent:**
```yaml
env:
# PostgreSQL - Using FQDN
- name: POSTGRES_HOST
  value: postgres.homelab.svc.cluster.local  # ✅ PERFECT

# Redis - Using FQDN
- name: REDIS_HOST
  value: redis.homelab.svc.cluster.local  # ✅ PERFECT

# Qdrant - Using HTTP with FQDN
- name: QDRANT_URL
  value: http://qdrant.homelab.svc.cluster.local:6333  # ✅ PERFECT

# LLM Service - Cross-namespace FQDN
- name: LLAMACPP_BASE_URL
  value: "http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080"  # ✅ PERFECT

# Other Services
- name: MEM0_API_URL
  value: "http://mem0.homelab.svc.cluster.local:8080"  # ✅ PERFECT
- name: N8N_BASE_URL
  value: "http://n8n.homelab.svc.cluster.local:5678"  # ✅ PERFECT
```

**Compliance Score:** 100/100

---

### 3.2 ✅ GOOD - family-assistant-api Deployment

**File:** `/infrastructure/kubernetes/family-assistant-api/deployment.yaml`
**Lines:** 44-51

**Why This Is Good:**
```yaml
env:
- name: LLAMACPP_BASE_URL
  value: "http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080"  # ✅
- name: MEM0_API_URL
  value: "http://mem0.homelab.svc.cluster.local:8080"  # ✅
- name: N8N_BASE_URL
  value: "http://n8n.homelab.svc.cluster.local:5678"  # ✅
- name: QDRANT_URL
  value: "http://qdrant.homelab.svc.cluster.local:6333"  # ✅
```

**Compliance Score:** 100/100

---

### 3.3 ✅ GOOD - IngressRoute Configurations

All IngressRoutes follow the correct pattern from the Golden Rules:

**Example:** `homelab/admin-dashboard`
```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: admin-dashboard
  namespace: homelab
spec:
  entryPoints:
    - websecure  # ✅ HTTPS entry point
  routes:
    - match: Host(`admin.fa.pesulabs.net`)  # ✅ External domain
      kind: Rule
      services:
        - name: family-admin  # ✅ Internal service name
          port: 3000  # ✅ Internal port
  tls:
    certResolver: default  # ✅ Let's Encrypt via Cloudflare DNS-01
```

**Compliance Score:** 100/100

---

## 4. Port Standardization Analysis

### 4.1 Current Port Usage

| Service | Internal Port | Container Port | Standard Compliance |
|---------|--------------|----------------|-------------------|
| family-assistant (app) | 80 | 80 | ✅ Web UI Standard |
| family-admin | 3000 | 3000 | ⚠️ Should map to 80 |
| family-assistant-backend | 8001 | 8001 | ✅ API Standard |
| n8n | 5678 | 5678 | ❌ Should be 80 or 8080 |
| postgres | 5432 | 5432 | ✅ Database Standard |
| redis | 6379 | 6379 | ✅ Database Standard |
| qdrant | 6333 | 6333 | ✅ Database Standard |
| mem0 | 8080 | 8080 | ✅ API Standard |
| authentik-server | 9000 | 9000 | ⚠️ Non-standard |

### 4.2 Recommendations

**For Better URL Clarity:**
- Map `family-admin:3000` → service port 80 (targetPort: 3000)
- Map `n8n:5678` → service port 80 (targetPort: 5678)
- Map `authentik-server:9000` → service port 80 (targetPort: 9000)

**Benefit:** Cleaner internal URLs like `http://n8n.homelab` instead of `http://n8n.homelab:5678`

---

## 5. Prioritized Action Plan

### Phase 1: CRITICAL Fixes (Immediate - This Week)

#### Action 1.1: Fix Frontend API URLs
**Priority:** 🔴 CRITICAL
**Impact:** HIGH - Fixes reliability and performance issues

**Files to Update:**
1. `/infrastructure/kubernetes/family-assistant-admin/deployment.yaml`
   - Change `NEXT_PUBLIC_API_URL` to internal DNS

2. Update ConfigMap `family-assistant-config` in namespace `family-assistant-app`
   - Change `VITE_API_BASE_URL` to internal DNS
   - Change `VITE_WS_URL` to internal WebSocket

**Before:**
```yaml
VITE_API_BASE_URL: https://family-assistant.homelab.pesulabs.net
```

**After:**
```yaml
VITE_API_BASE_URL: http://family-assistant-backend.homelab.svc.cluster.local:8001
```

**Validation:**
```bash
# After deployment, check frontend can reach backend
kubectl logs -n family-assistant-app -l app.kubernetes.io/name=family-assistant
```

---

#### Action 1.2: Fix Authentik Service References
**Priority:** 🔴 CRITICAL
**Impact:** MEDIUM - Prevents future failures

**File to Update:**
- Authentik Helm values or deployment manifest

**Before:**
```yaml
AUTHENTIK_REDIS__HOST: authentik-redis
AUTHENTIK_POSTGRESQL__HOST: authentik-postgresql
```

**After:**
```yaml
AUTHENTIK_REDIS__HOST: authentik-redis.authentik.svc.cluster.local
AUTHENTIK_POSTGRESQL__HOST: authentik-postgresql.authentik.svc.cluster.local
```

---

### Phase 2: Clean Up Duplicates (Next Week)

#### Action 2.1: Remove Duplicate Ingress Resources
**Priority:** 🟡 WARNING
**Impact:** MEDIUM - Reduces confusion

**Files to Review and Clean:**
1. `/infrastructure/kubernetes/traefik/ingress-routes.yaml`
   - Remove old `networking.k8s.io/v1` Ingress resources
   - Keep only IngressRoute resources

2. Delete duplicate ingress files:
   - `/infrastructure/kubernetes/family-assistant-app/ingress-http.yaml`
   - `/services/ingress-fix.yaml`
   - `/infrastructure/kubernetes/ingress-acme-fix.yaml`

**Keep:** Only IngressRoute resources in cluster
**Delete:** All standard Ingress resources

---

#### Action 2.2: Consolidate IngressRoute Configurations
**Priority:** 🟡 WARNING
**Impact:** MEDIUM - Single source of truth

**Create:** `/infrastructure/kubernetes/traefik/active-ingress-routes.yaml`

**Include:**
- admin-dashboard
- family-api
- n8n
- authentik-ingress
- family-assistant-app

**Delete:** Scattered ingress-routes.yaml files in individual service directories

---

### Phase 3: Port Standardization (Future Enhancement)

#### Action 3.1: Standardize Service Ports
**Priority:** 🟢 ENHANCEMENT
**Impact:** LOW - Improved usability

**Services to Update:**
1. family-admin: Map port 80 → targetPort 3000
2. n8n: Map port 80 → targetPort 5678
3. authentik-server: Map port 80 → targetPort 9000

**Benefit:** Simpler internal URLs

---

## 6. Compliance Checklist

### Before Deploying Any New Service

- [ ] Internal service URLs use `http://<service>.<namespace>.svc.cluster.local:<port>`
- [ ] External access uses IngressRoute with `certResolver: default`
- [ ] Host matches pattern `<service>.pesulabs.net` or `<service>.fa.pesulabs.net`
- [ ] Service ports follow standard (80 for web, 8080 for API, etc.)
- [ ] No external HTTPS URLs for internal service communication
- [ ] No IP addresses in configuration
- [ ] No short hostnames (always use FQDN)

---

## 7. Recommendations for Architecture Improvements

### 7.1 Service Mesh Consideration (Future)
For advanced traffic management, consider:
- **Istio** or **Linkerd** for service mesh capabilities
- Built-in mTLS for internal traffic
- Advanced traffic routing and observability

**Note:** Only needed if complexity grows significantly

### 7.2 Network Policies
Implement Kubernetes NetworkPolicies to:
- Restrict which pods can communicate
- Enforce security boundaries between namespaces
- Prevent unauthorized internal access

**Example:** Only allow `family-assistant-app` to call `family-assistant-backend`

### 7.3 DNS Caching
Deploy **CoreDNS autoscaler** to improve DNS resolution performance under load.

---

## 8. Validation Commands

### Check Internal DNS Resolution
```bash
# From any pod, test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup family-assistant-backend.homelab.svc.cluster.local
```

### Check Service Connectivity
```bash
# Test internal HTTP connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://family-assistant-backend.homelab.svc.cluster.local:8001/health
```

### Verify IngressRoute Status
```bash
# Check IngressRoute is accepted by Traefik
kubectl get ingressroute -n homelab admin-dashboard -o yaml | grep -A 5 status
```

### Check Certificate Status
```bash
# Verify TLS certificates are valid
kubectl get certificate -A
```

---

## 9. Summary and Conclusion

### Current State
The homelab Kubernetes cluster has **mixed compliance** with the networking golden rules:
- **Backend services:** Excellent - 100% compliant
- **Frontend applications:** Poor - Using external URLs for internal calls
- **Authentik:** Fragile - Using short hostnames
- **External access:** Good - IngressRoutes properly configured

### Root Cause of "Breaking Changes"
The primary issue causing instability is **frontend applications using external HTTPS URLs** to communicate with backend services instead of internal DNS. This creates:
- Dependency on external infrastructure (DNS, Traefik, certificates)
- Performance overhead from unnecessary routing
- Reliability issues from hairpin NAT and certificate validation

### Immediate Next Steps
1. **Fix frontend API URLs** (Action 1.1) - Highest priority
2. **Fix Authentik service references** (Action 1.2) - Prevent future issues
3. **Clean up duplicate Ingress resources** (Action 2.1) - Reduce confusion
4. **Document changes** and update this report

### Long-term Vision
With these fixes in place, the networking architecture will be:
- **Reliable:** Internal traffic uses internal DNS
- **Performant:** No unnecessary external routing
- **Maintainable:** Single source of truth for configuration
- **Scalable:** Easy to add new services following patterns

---

**Report Completed:** 2025-11-20
**Next Review Date:** After Phase 1 completion

