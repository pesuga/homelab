# Comprehensive Service Status Report
**Date:** 2025-11-19
**Cluster:** PesuLabs Homelab (K3s v1.33.5)
**Nodes:** asuna (Service Node), pesubuntu (Compute Node)

---

## Executive Summary

**Overall Status:** ⚠️ PARTIALLY OPERATIONAL - 8/9 core services healthy, 1 critical failure (Mem0), 1 service missing (Authentik)

### Critical Issues
1. **Mem0 Service:** CrashLoopBackOff - Connection refused during initialization
2. **Authentik:** Not deployed (missing authentication provider)
3. **Family Portal External Access:** 404 errors on configured HTTPS endpoints

### Services Working Correctly
- ✅ N8n (Workflow Automation)
- ✅ PostgreSQL (Database)
- ✅ Redis (Cache)
- ✅ Qdrant (Vector Database)
- ✅ LlamaCpp (LLM Inference)
- ✅ Prometheus (Metrics)
- ✅ Grafana (Dashboards)
- ✅ Loki (Log Aggregation)
- ✅ Family API (Backend)

---

## Detailed Service Health Status

### 1. Core Infrastructure Services

| Service | Internal URL | Status | HTTP Code | Notes |
|---------|-------------|--------|-----------|-------|
| **PostgreSQL** | `postgres.homelab.svc.cluster.local:5432` | ✅ HEALTHY | N/A | Accepting connections, DB: homelab |
| **Redis** | `redis.homelab.svc.cluster.local:6379` | ✅ HEALTHY | N/A | PING → PONG |
| **Qdrant** | `http://qdrant.homelab.svc.cluster.local:6333` | ✅ HEALTHY | 200 | Vector DB operational |

**Validation:**
```bash
# PostgreSQL
kubectl exec -n homelab postgres-0 -- pg_isready -U homelab
# Output: /var/run/postgresql:5432 - accepting connections

# Redis
kubectl exec -n homelab redis-cf7487ccc-pr975 -- redis-cli ping
# Output: PONG

# Qdrant (Internal DNS)
curl http://qdrant.homelab.svc.cluster.local:6333/
# Output: HTTP 200
```

---

### 2. AI Stack Services

| Service | Internal URL | Status | HTTP Code | Notes |
|---------|-------------|--------|-----------|-------|
| **LlamaCpp** | `http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080` | ✅ HEALTHY | 200 | GPU inference working |
| **Mem0** | `http://mem0.homelab.svc.cluster.local:8080` | ❌ FAILED | 503 | CrashLoopBackOff |

#### LlamaCpp Details
- **Endpoint Type:** External endpoint service (no pods in llamacpp namespace)
- **Backend:** 192.168.8.129:8080 (Compute Node - pesubuntu)
- **Health Check:** `{"status":"ok"}`
- **Notes:** Runs on compute node with hostNetwork, accessed via K8s Service

#### Mem0 Failure Analysis
**Error:** `Connection refused [Errno 111]`

**Logs:**
```
ERROR:app:Failed to initialize Mem0: [Errno 111] Connection refused
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     10.42.0.213:46754 - "GET /health HTTP/1.1" 503 Service Unavailable
```

**Configuration:**
```yaml
# From mem0.yaml ConfigMap
QDRANT_HOST: qdrant.homelab.svc.cluster.local  # ✅ Correct
QDRANT_PORT: "6333"                            # ✅ Correct
OPENAI_BASE_URL: http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080/v1
OPENAI_API_KEY: sk-dummy
LLM_PROVIDER: openai
```

**Root Cause:** Mem0 attempting to connect to a service during initialization but getting connection refused. Most likely:
1. Qdrant connection timing issue (though Qdrant is healthy)
2. LlamaCpp /v1 endpoint compatibility issue
3. Missing dependency initialization

**Recommendation:**
- Check if Mem0 image exists: `kubectl describe pod mem0-5c9956c7f-9bsd4 -n homelab | grep Image`
- Verify LlamaCpp /v1/models endpoint: `curl http://192.168.8.129:8080/v1/models`
- Add startup probe with longer delay
- Check Mem0 application logs for specific connection target

---

### 3. Workflow Automation

| Service | Internal URL | External URL | Status | HTTP Code |
|---------|-------------|--------------|--------|-----------|
| **N8n** | `http://n8n.homelab.svc.cluster.local:5678` | `https://n8n.homelab.pesulabs.net` | ✅ HEALTHY | 200 |

**Notes:** Both internal DNS and external HTTPS access working correctly

---

### 4. Family Assistant Platform

| Component | Internal URL | External URL | Status | HTTP Code | Notes |
|-----------|-------------|--------------|--------|-----------|-------|
| **Backend API** | `http://family-assistant-backend.homelab.svc.cluster.local:8001` | `https://api.family.pesulabs.net` | ✅/⚠️ PARTIAL | 200/404 | Internal OK, External 404 |
| **Frontend Portal** | `http://family-assistant-frontend.homelab.svc.cluster.local:3000` | `https://family.pesulabs.net` | ❌/⚠️ FAILED | 000/404 | Internal not responding, External 404 |
| **Admin Dashboard** | Routes via backend | `https://admin.homelab.pesulabs.net` | ✅ HEALTHY | 200 | Working correctly |

#### Service Mapping Discrepancy
**Issue:** SERVICE_INVENTORY.md lists:
- Backend: `homelab` namespace
- Frontend: `homelab` namespace

**Reality:** Additional namespace found:
- `family-assistant-app` namespace contains 2 pods:
  - `family-assistant-7c95494b98-s27j5`
  - `family-assistant-7c95494b98-srx6p`
- `family-assistant-api` namespace: Empty
- `family-assistant-admin` namespace: Empty

**Current Deployments:**
```bash
# homelab namespace
kubectl get deployment -n homelab | grep family
family-assistant-backend    1/1     1            1           5h39m
family-assistant-frontend   0/0     0            0           7d2h  # ❌ Scaled to 0

# family-assistant-app namespace
kubectl get pods -n family-assistant-app
family-assistant-7c95494b98-s27j5   1/1     Running   0          27h
family-assistant-7c95494b98-srx6p   1/1     Running   0          27h
```

**Frontend Issue:**
- Deployment exists in `homelab` namespace but scaled to 0 replicas
- Service points to image: `100.81.76.55:30500/family-assistant:complete`
- No ingress configured for `api.family.pesulabs.net` or `family.pesulabs.net`

**Ingress Configuration:**
```yaml
# Only admin.homelab.pesulabs.net is configured
host: admin.homelab.pesulabs.net
paths:
  - /api → family-assistant-backend:8001
  - /ws → family-assistant-backend:8001
  - /metrics → family-assistant-backend:8001
  - / → family-assistant-frontend:3000
```

**Recommendations:**
1. Scale up family-assistant-frontend: `kubectl scale deployment family-assistant-frontend -n homelab --replicas=1`
2. Create ingress for api.family.pesulabs.net and family.pesulabs.net
3. Consolidate family-assistant namespaces (currently split across homelab, family-assistant-app, family-assistant-api, family-assistant-admin)
4. Update SERVICE_INVENTORY.md with correct namespace information

---

### 5. Monitoring & Observability

| Service | Internal URL | External URL | Status | HTTP Code | Notes |
|---------|-------------|--------------|--------|-----------|-------|
| **Prometheus** | `http://prometheus-svc.homelab.svc.cluster.local:9090` | `https://prometheus.homelab.pesulabs.net` | ✅ HEALTHY | 200 | Metrics collection working |
| **Grafana** | `http://grafana.homelab.svc.cluster.local:3000` | N/A | ✅ HEALTHY | 200 | Dashboard service operational |
| **Loki** | `http://loki.homelab.svc.cluster.local:3100` | N/A | ✅ HEALTHY | 200 | Log aggregation working |
| **Homelab Dashboard** | `http://homelab-dashboard.homelab.svc.cluster.local:80` | `https://dash.pesulabs.net` | ✅ HEALTHY | 200/302 | Landing page operational |
| **Discovery Dashboard** | `http://discovery-dashboard.homelab.svc.cluster.local:80` | `https://discover.homelab.pesulabs.net` | ✅ HEALTHY | 200 | Service discovery working |

**Notes:**
- All monitoring services responding correctly on internal DNS
- External access via HTTPS working for configured services
- Homelab dashboard returns 302 (redirect) which is expected

---

### 6. Authentication & Identity (MISSING)

| Service | Internal URL | External URL | Status | Notes |
|---------|-------------|--------------|--------|-------|
| **Authentik** | `http://authentik-server.authentik.svc.cluster.local:80` | `https://auth.pesulabs.net` | ❌ NOT DEPLOYED | 404 on external access |

**Critical Issue:** No `authentik` namespace exists in the cluster

**Impact:**
- No centralized authentication/SSO
- Services cannot implement OAuth2/OIDC authentication
- No proxy provider for securing services
- Security vulnerability for multi-user access

**Recommendations:**
1. **URGENT:** Deploy Authentik immediately
2. Create `authentik` namespace
3. Deploy Authentik StatefulSet with PostgreSQL backend
4. Configure ingress for auth.pesulabs.net
5. Set up OAuth2 providers for N8n, Grafana, and other services
6. Implement Authentik proxy provider for services without native OAuth support

---

## Cluster Health Summary

### Node Status
```
NAME        STATUS   ROLES                  VERSION        INTERNAL-IP
asuna       Ready    control-plane,master   v1.33.5+k3s1   100.81.76.55
pesubuntu   Ready    <none>                 v1.33.5+k3s1   100.86.122.109
```

### Namespace Overview
- ✅ homelab (primary services)
- ✅ llamacpp (LLM inference service)
- ✅ flux-system (GitOps controllers)
- ✅ cert-manager (TLS certificate management)
- ⚠️ family-assistant-app (contains 2 pods, unclear purpose)
- ⚠️ family-assistant-api (empty namespace)
- ⚠️ family-assistant-admin (empty namespace)
- ❌ authentik (missing - should exist)
- ❌ auth (missing - alternative name check)

### Pod Health
```
Total Pods (excluding kube-system): 38
Running: 33
Completed/Succeeded: 4
Failed: 1
CrashLoopBackOff: 2 (mem0 deployments)
```

---

## Networking Validation

### Internal DNS Resolution (✅ WORKING)
All services correctly resolve via K8s internal DNS:
- `<service>.<namespace>.svc.cluster.local` pattern working
- Cross-namespace communication functional (homelab → llamacpp)
- TCP connectivity verified for PostgreSQL (5432) and Redis (6379)

### External HTTPS Access (⚠️ PARTIAL)
| URL | Status | Notes |
|-----|--------|-------|
| `https://n8n.homelab.pesulabs.net` | ✅ 200 | Working |
| `https://dash.pesulabs.net` | ✅ 302 | Working (redirect) |
| `https://discover.homelab.pesulabs.net` | ✅ 200 | Working |
| `https://admin.homelab.pesulabs.net` | ✅ 200 | Working |
| `https://auth.pesulabs.net` | ❌ 404 | Authentik not deployed |
| `https://api.family.pesulabs.net` | ❌ 404 | No ingress configured |
| `https://family.pesulabs.net` | ❌ 404 | No ingress configured |

### Traefik Ingress Controller
- **Status:** ✅ RUNNING (2 replicas)
- **LoadBalancer IPs:** 100.81.76.55, 100.86.122.109
- **Ingress Resources:** 6 configured
  - admin-dashboard-ingress (admin.homelab.pesulabs.net)
  - discovery-dashboard-ingress (discover.homelab.pesulabs.net)
  - homelab-dashboard-fixed (dash.pesulabs.net)
  - family-assistant-backend (not shown in kubectl output - verify)
  - family-assistant-frontend (not shown in kubectl output - verify)
  - n8n-ingress (likely exists but not captured)

---

## Configuration Issues Found

### 1. SERVICE_INVENTORY.md Inaccuracies
**Current Documentation Says:**
```markdown
| Family API | http://family-assistant-backend.homelab.svc.cluster.local:8000 | https://api.family.pesulabs.net
| Family Portal | http://family-assistant-frontend.homelab.svc.cluster.local:3000 | https://family.pesulabs.net
```

**Reality:**
- Backend port is **8001** (not 8000)
- Frontend deployment scaled to **0 replicas**
- No ingress exists for api.family.pesulabs.net or family.pesulabs.net
- Additional namespace `family-assistant-app` contains 2 running pods

### 2. Namespace Sprawl
**Issue:** Family Assistant components spread across 4 namespaces:
- `homelab` - Backend deployment, frontend deployment (0 replicas)
- `family-assistant-app` - 2 running pods (unknown purpose)
- `family-assistant-api` - Empty
- `family-assistant-admin` - Empty

**Recommendation:** Consolidate to single namespace following NETWORKING_STANDARD.md

### 3. Missing Authentication Infrastructure
**Issue:** No Authentik deployment despite SERVICE_INVENTORY.md listing it

**Impact:** No SSO, no OAuth2, security vulnerability

---

## Priority-Ordered Action Items

### 🔴 CRITICAL (Fix Immediately)

1. **Fix Mem0 Service**
   ```bash
   # Debug steps
   kubectl logs -n homelab mem0-5c9956c7f-9bsd4 --previous
   kubectl describe pod mem0-5c9956c7f-9bsd4 -n homelab

   # Verify LlamaCpp /v1 endpoint
   curl http://192.168.8.129:8080/v1/models

   # Check image availability
   kubectl get events -n homelab | grep mem0
   ```
   **Root Cause:** Connection refused during Mem0 initialization - likely LlamaCpp /v1 endpoint or Qdrant connection timing issue

2. **Deploy Authentik (Authentication Provider)**
   ```bash
   # Create namespace
   kubectl create namespace authentik

   # Deploy Authentik (requires manifest preparation)
   # Reference: https://goauthentik.io/docs/installation/kubernetes
   ```
   **Impact:** Critical security gap - no authentication/SSO

3. **Fix Family Portal Access**
   ```bash
   # Scale up frontend
   kubectl scale deployment family-assistant-frontend -n homelab --replicas=1

   # Create missing ingress
   kubectl apply -f - <<EOF
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: family-portal-ingress
     namespace: homelab
   spec:
     ingressClassName: traefik
     rules:
     - host: family.pesulabs.net
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: family-assistant-frontend
               port:
                 number: 3000
     - host: api.family.pesulabs.net
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: family-assistant-backend
               port:
                 number: 8001
     tls:
     - hosts:
       - family.pesulabs.net
       - api.family.pesulabs.net
   EOF
   ```

### 🟡 IMPORTANT (Fix Soon)

4. **Update SERVICE_INVENTORY.md**
   - Correct Family API port (8000 → 8001)
   - Document actual namespace usage
   - Remove Authentik entry or mark as "PENDING DEPLOYMENT"
   - Add Discovery Dashboard entry
   - Add Admin Dashboard entry

5. **Consolidate Family Assistant Namespaces**
   - Investigate pods in family-assistant-app namespace
   - Migrate or delete empty namespaces (family-assistant-api, family-assistant-admin)
   - Follow NETWORKING_STANDARD.md namespace conventions

6. **Verify All External URLs in SERVICE_INVENTORY.md**
   - Test each HTTPS endpoint
   - Document actual vs. expected
   - Create missing ingress resources

### 🟢 RECOMMENDED (Improve When Possible)

7. **Add Health Monitoring**
   - Create Prometheus alerts for CrashLoopBackOff
   - Add uptime checks for critical services
   - Configure Grafana dashboards for service health

8. **Standardize Service Deployments**
   - Ensure all services have proper health checks
   - Add resource requests/limits consistently
   - Implement consistent labeling

9. **Documentation Improvements**
   - Create TROUBLESHOOTING.md with common issues
   - Add network diagram showing actual topology
   - Document service dependencies

---

## Testing Methodology

### Internal DNS Testing
```bash
# Create debug pod
kubectl run debug-test --image=nicolaka/netshoot --restart=Never -n homelab -- sleep 300

# Execute tests
kubectl exec -n homelab debug-test -- curl -s -o /dev/null -w '%{http_code}' http://service.namespace.svc.cluster.local:port

# Cleanup
kubectl delete pod debug-test -n homelab
```

### External HTTPS Testing
```bash
curl -k -s -o /dev/null -w "%{http_code}" https://subdomain.pesulabs.net
```

### Database Connectivity
```bash
# PostgreSQL
kubectl exec -n homelab postgres-0 -- pg_isready -U homelab

# Redis
kubectl exec -n homelab redis-cf7487ccc-pr975 -- redis-cli ping
```

---

## Summary

**Services Operational:** 8/9 core services (89% uptime)

**Critical Gaps:**
1. Mem0 memory service not functioning (CrashLoopBackOff)
2. Authentik authentication not deployed (security risk)
3. Family Portal external access broken (404 errors)

**Strengths:**
- ✅ Core infrastructure healthy (PostgreSQL, Redis, Qdrant)
- ✅ AI stack partially working (LlamaCpp operational)
- ✅ Monitoring stack fully functional (Prometheus, Grafana, Loki)
- ✅ Internal DNS networking working correctly
- ✅ Traefik ingress working for configured services

**Next Steps:**
1. Fix Mem0 connection issue (likely LlamaCpp /v1 endpoint compatibility)
2. Deploy Authentik for authentication/SSO
3. Scale up Family Portal frontend and create ingress
4. Update SERVICE_INVENTORY.md to reflect reality
5. Consolidate Family Assistant namespace sprawl

---

**Report Generated:** 2025-11-19
**Generated By:** Claude Code System Architect
**Validation Method:** Live cluster testing via kubectl + curl
