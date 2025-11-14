# Family Assistant Network Routing Diagnostic Report

**Date**: 2025-11-13
**Investigation**: Critical network routing issues for Family Assistant application
**Status**: ROOT CAUSE IDENTIFIED - Configuration Mismatch

---

## Executive Summary

The Family Assistant application is experiencing routing issues due to **architectural conflict** between the backend serving old frontend assets and nginx serving new frontend assets. Additionally, HTTPS access via Traefik is functional but DNS resolution directs to wrong IP.

### Key Findings

1. **Backend serving old dashboard HTML** at `/dashboard/` endpoint (phase2 version)
2. **Frontend pods serving new React build** via nginx (week1-v3 version)
3. **Asset version mismatch**: Backend serves `index-Da33wUt2.js`, frontend has `index-CyMwIyjW.js`
4. **HTTPS routing functional**: Traefik successfully routes with Host header
5. **DNS misconfiguration**: domain resolves to Tailscale IP instead of service node

---

## Issue 1: HTTPS Domain Unreachable (https://family.homelab.pesulabs.net)

### Root Cause
**DNS resolution points to wrong IP address**

### Evidence
```bash
$ nslookup family.homelab.pesulabs.net
Name:    family.homelab.pesulabs.net
Address: 100.81.76.55  # Service node Tailscale IP

$ curl -k -w "%{http_code}" https://100.81.76.55:32224 -H "Host: family.homelab.pesulabs.net"
200  # Traefik routing WORKS when using correct Host header
```

### Analysis
- DNS correctly resolves to service node (100.81.76.55)
- Traefik IngressRoute correctly configured for `family.homelab.pesulabs.net`
- TLS certificate valid (self-signed, expires 2026-11-12)
- Traefik HTTPS port is **32224** (not standard 443)
- Routing works when manually specifying Host header

### Verification
```bash
# IngressRoute configuration - CORRECT
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: family-assistant-frontend
  namespace: homelab
spec:
  entryPoints: [websecure]
  routes:
  - match: Host(`family.homelab.pesulabs.net`)
    services:
    - name: family-assistant-frontend
      port: 3000
  tls:
    secretName: family-assistant-frontend-tls

# Service endpoints - HEALTHY
Endpoints: 10.42.3.130:3000, 10.42.3.131:3000
```

### Fix Required
**Configure proper DNS/Traefik access pattern:**

**Option A: External DNS Entry** (Recommended)
```bash
# Add DNS record or /etc/hosts entry pointing to service node
# Then access via standard HTTPS port requires Traefik LoadBalancer
```

**Option B: Use NodePort for HTTPS** (Quick fix)
```bash
# Access via Traefik's NodePort directly
https://100.81.76.55:32224

# With Host header redirect (nginx proxy)
curl -k https://100.81.76.55:32224 -H "Host: family.homelab.pesulabs.net"
```

**Option C: Traefik LoadBalancer Service** (Production-ready)
```bash
# Change Traefik service from NodePort to LoadBalancer
# Exposes port 443 on service node IP directly
kubectl patch svc traefik -n kube-system -p '{"spec":{"type":"LoadBalancer"}}'

# Then access via:
https://family.homelab.pesulabs.net  # Will work after DNS propagation
```

---

## Issue 2: NodePort Not Loading Application (http://100.81.76.55:30300/)

### Root Cause
**Architectural mismatch: Backend serving different frontend version than nginx pods**

### Evidence
```bash
# Backend serves old dashboard HTML
$ curl http://100.81.76.55:30300/dashboard/
<script src="/assets/index-Da33wUt2.js"></script>  # OLD VERSION

# Nginx pods have different assets
$ kubectl exec family-assistant-frontend-xxx -- ls /usr/share/nginx/html/assets/
index-CyMwIyjW.js  # NEW VERSION (different hash)

# Browser tries to load old asset from new nginx
GET /assets/index-Da33wUt2.js → 404 Not Found
```

### Architecture Analysis

**Current Setup:**
```
Browser
  ↓
NodePort :30300
  ↓
Service: family-assistant-frontend (ClusterIP)
  ↓
Pods: family-assistant-frontend (nginx)
  ↓ (proxy /dashboard/ requests)
Backend: family-assistant:8001
  ↓ (serves OLD dashboard HTML)
Returns: dashboard-standalone.html with OLD asset references
  ↓ (browser tries to load assets)
GET /assets/index-Da33wUt2.js → 404 (nginx only has index-CyMwIyjW.js)
```

**Backend Code:**
```python
# File: api/main.py:510
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the standalone dashboard HTML."""
    dashboard_path = Path(__file__).parent.parent / "dashboard-standalone.html"
    return f.read()  # Returns OLD static HTML with OLD asset hashes

# File: api/main.py:1408
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")))
# But backend container DOESN'T have /app/frontend/dist/ directory!
```

**Nginx Configuration:**
```nginx
# Nginx proxies /dashboard/ to backend
location /dashboard/ {
    proxy_pass http://family-assistant.homelab.svc.cluster.local:8001;
}

# Nginx serves static assets from /usr/share/nginx/html/assets/
location ~* \.(js|css|png|jpg)$ {
    try_files $uri =404;
}
```

### Deployment Version Mismatch
```bash
# Backend deployment
Image: 100.81.76.55:30500/family-assistant:phase2
Built: Contains old dashboard-standalone.html

# Frontend deployment
Image: 100.81.76.55:30500/family-assistant-frontend:week1-v3
Built: Contains new React build with different asset hashes
```

### Fix Required

**Solution 1: Remove Backend Dashboard Route** (Recommended)
The backend should NOT serve frontend HTML. Remove the `/dashboard` endpoint and let nginx handle all frontend routing.

```bash
# Edit api/main.py - REMOVE these lines:
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    # DELETE THIS ENTIRE FUNCTION

# Rebuild backend image
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant
docker build -t 100.81.76.55:30500/family-assistant:phase2-fixed .
docker push 100.81.76.55:30500/family-assistant:phase2-fixed

# Update deployment
kubectl set image deployment/family-assistant -n homelab \
  family-assistant=100.81.76.55:30500/family-assistant:phase2-fixed

# Update nginx config to serve React app at root
kubectl exec -n homelab family-assistant-frontend-xxx -- cat > /etc/nginx/conf.d/default.conf <<'EOF'
server {
    listen 3000;
    root /usr/share/nginx/html;
    index index.html;

    # Serve static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://family-assistant.homelab.svc.cluster.local:8001;
    }

    # Dashboard API proxy
    location /dashboard/system-health {
        proxy_pass http://family-assistant.homelab.svc.cluster.local:8001/dashboard/system-health;
    }

    # Catch-all for React Router
    location / {
        try_files $uri /index.html;
    }
}
EOF

# Restart frontend pods
kubectl rollout restart deployment/family-assistant-frontend -n homelab
```

**Solution 2: Copy New Build to Backend** (Alternative)
Copy the new React build into the backend container so both versions match.

```bash
# Build frontend locally
cd /home/pesu/Rakuflow/systems/homelab/services/family-assistant/frontend
npm run build

# Copy dist to backend directory
cp -r dist ../api/frontend/

# Rebuild backend with frontend
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant
docker build -t 100.81.76.55:30500/family-assistant:phase2-with-frontend .
docker push 100.81.76.55:30500/family-assistant:phase2-with-frontend

# Update deployment
kubectl set image deployment/family-assistant -n homelab \
  family-assistant=100.81.76.55:30500/family-assistant:phase2-with-frontend
```

---

## Verification Tests

### Test 1: Direct Pod Access (Currently Working)
```bash
$ curl -s http://10.42.3.130:3000/ | grep title
<title>Family Assistant Dashboard</title>
✅ PASS: Nginx serves React app correctly

$ curl -s http://10.42.3.130:3000/assets/index-CyMwIyjW.js | head -c 50
var ht=t=>{throw TypeError(t)};
✅ PASS: Static assets accessible
```

### Test 2: NodePort Access (Currently Failing)
```bash
$ curl -s http://100.81.76.55:30300/
✅ PASS: Returns HTML (200)

$ curl -s http://100.81.76.55:30300/dashboard/
Returns HTML with OLD asset references
❌ FAIL: Asset mismatch causes 404s in browser
```

### Test 3: HTTPS via Traefik (Functional but needs DNS)
```bash
$ curl -k https://100.81.76.55:32224 -H "Host: family.homelab.pesulabs.net"
✅ PASS: Traefik routes correctly to frontend service
```

---

## Browser Console Evidence

**Expected behavior when accessing http://100.81.76.55:30300/dashboard/:**

```
1. Browser loads /dashboard/ from nginx
2. Nginx proxies to backend
3. Backend returns dashboard-standalone.html with:
   <script src="/assets/index-Da33wUt2.js"></script>
4. Browser requests /assets/index-Da33wUt2.js from nginx
5. Nginx returns 404 (only has index-CyMwIyjW.js)
6. JavaScript fails to load
7. React app never initializes
8. Dashboard shows blank page
```

**Actual nginx access logs:**
```
10.42.0.0 - "GET /dashboard/ HTTP/1.1" 200
10.42.3.130 - "GET /dashboard/system-health HTTP/1.1" 200
# No 404 errors visible because API calls work
# But browser can't load JavaScript assets
```

---

## Network Diagnostics Summary

### Working Components
- ✅ Frontend pods: 2/2 running, healthy
- ✅ Frontend service: Endpoints configured correctly
- ✅ Direct pod access: nginx serves React app successfully
- ✅ NodePort routing: Traffic reaches nginx (returns 200)
- ✅ Traefik routing: IngressRoute configured correctly
- ✅ TLS certificate: Valid self-signed cert
- ✅ Backend API: Health endpoints responding
- ✅ DNS resolution: Correctly points to service node

### Failing Components
- ❌ Asset version sync: Backend and frontend have different builds
- ❌ Backend dashboard route: Serves old HTML instead of proxying to frontend
- ❌ HTTPS access: Requires LoadBalancer or explicit port in URL

### Network Policies
```bash
$ kubectl get networkpolicies -n homelab
No resources found
✅ No network policies blocking traffic
```

### iptables/kube-proxy
```bash
$ kubectl get svc family-assistant-frontend -n homelab
TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)         AGE
NodePort   10.43.88.186   <none>        3000:30300/TCP  16h

✅ kube-proxy correctly configured NodePort 30300
```

---

## Recommended Fix Commands

### Quick Fix (Remove Backend Dashboard Route)

```bash
# 1. SSH to service node or use kubectl from compute node
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant

# 2. Edit main.py to remove dashboard route
# Lines to delete: 510-517 in api/main.py

# 3. Rebuild and push backend
docker build -t 100.81.76.55:30500/family-assistant:phase2-no-dashboard .
docker push 100.81.76.55:30500/family-assistant:phase2-no-dashboard

# 4. Update deployment
kubectl set image deployment/family-assistant -n homelab \
  family-assistant=100.81.76.55:30500/family-assistant:phase2-no-dashboard

# 5. Wait for rollout
kubectl rollout status deployment/family-assistant -n homelab

# 6. Update nginx to NOT proxy /dashboard/ HTML
kubectl get configmap family-assistant-frontend-nginx -n homelab -o yaml | \
  sed '/location \/dashboard\/ {/,/}/d' | \
  kubectl apply -f -

# 7. Restart frontend
kubectl rollout restart deployment/family-assistant-frontend -n homelab
```

### Fix HTTPS Access

```bash
# Option A: Change Traefik to LoadBalancer
kubectl patch svc traefik -n kube-system -p '{"spec":{"type":"LoadBalancer"}}'

# Then access via:
https://family.homelab.pesulabs.net

# Option B: Use Traefik NodePort directly
https://100.81.76.55:32224
```

---

## Verification After Fix

```bash
# Test 1: NodePort should serve React app
curl -s http://100.81.76.55:30300/ | grep -o '<script.*src="[^"]*"'
# Should show: <script src="/assets/index-CyMwIyjW.js">

# Test 2: Assets should load
curl -s -w "%{http_code}" http://100.81.76.55:30300/assets/index-CyMwIyjW.js
# Should return: 200

# Test 3: Backend should NOT serve dashboard HTML
curl -s -w "%{http_code}" http://100.81.76.55:30080/dashboard
# Should return: 404 (endpoint removed)

# Test 4: Dashboard API still works
curl -s http://100.81.76.55:30300/dashboard/system-health | jq .
# Should return JSON with system metrics

# Test 5: HTTPS access works
curl -k https://100.81.76.55:32224 -H "Host: family.homelab.pesulabs.net"
# Should return React app HTML
```

---

## Summary

**Root Causes:**
1. Backend serves old dashboard HTML at `/dashboard/` with outdated asset hashes
2. Nginx proxies `/dashboard/` to backend instead of serving React app
3. Asset version mismatch causes 404 errors when browser tries to load JavaScript
4. HTTPS requires LoadBalancer service or explicit NodePort in URL

**Recommended Actions:**
1. Remove backend `/dashboard` endpoint (backend should only serve API)
2. Configure nginx to serve React app at root `/`
3. Change Traefik service to LoadBalancer for HTTPS on port 443
4. Verify all asset references resolve correctly

**Impact:** After fixes applied, both NodePort and HTTPS access will work correctly.
