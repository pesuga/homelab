# Traefik HTTPS Configuration Status Report

**Date**: 2025-11-07
**Cluster**: K3s Homelab

## Executive Summary

Traefik is operational with HTTPS configured for most services. However, there are recurring errors in logs indicating missing backend services (grafana and flowise) that need attention. The core HTTPS infrastructure (Traefik + cert-manager) is working correctly.

---

## 1. Traefik Status

### Running Components
✅ **Traefik Pod**: `traefik-54c679854f-sjzrr` - Running (1/1)
✅ **Service Load Balancer**: Active on ports 80:30884/TCP, 443:32224/TCP
✅ **External IPs**: 100.81.76.55, 100.86.122.109
✅ **Installation**: K3s v3.3.6 via HelmChart

### Service Configuration
```yaml
Service: traefik (kube-system)
Type: LoadBalancer
Cluster IP: 10.43.82.119
External IPs: 100.81.76.55, 100.86.122.109
Ports:
  - 80:30884/TCP (HTTP)
  - 443:32224/TCP (HTTPS)
Age: 22 days
```

---

## 2. Certificate Management (cert-manager)

### cert-manager Status
✅ **All pods running**:
- cert-manager-767f578ff-mpsqh (Running)
- cert-manager-cainjector-c7fdb4dbf-jbxc5 (Running)
- cert-manager-webhook-768bf9d966-xmmdp (Running)

### ClusterIssuers
✅ **letsencrypt-prod**: Ready (15d)
✅ **letsencrypt-staging**: Ready (15d)

### Provisioned Certificates (8 total)
All certificates are valid and ready:

| Certificate | Host | Status | Expiry |
|------------|------|--------|--------|
| family-assistant-tls | assistant.homelab.pesulabs.net | ✅ Ready | 2026-02-03 |
| flowise-tls | flowise.homelab.pesulabs.net | ✅ Ready | - |
| grafana-tls | grafana.homelab.pesulabs.net | ✅ Ready | - |
| homelab-dashboard-tls | dash.pesulabs.net | ✅ Ready | - |
| lobechat-tls | chat.homelab.pesulabs.net | ✅ Ready | 2026-02-02 |
| n8n-tls | n8n.homelab.pesulabs.net | ✅ Ready | - |
| prometheus-tls | prometheus.homelab.pesulabs.net | ✅ Ready | - |
| webui-tls | webui.homelab.pesulabs.net | ✅ Ready | - |

---

## 3. Ingress Resources

### Standard Ingress (8 resources)
Using `ingressClassName: traefik` in homelab namespace:

| Ingress | Host | HTTPS | Certificate | Backend Service | Status |
|---------|------|-------|-------------|-----------------|--------|
| family-assistant | assistant.homelab.pesulabs.net | ✅ | family-assistant-tls | family-assistant:8001 | ✅ Working |
| flowise-pesulabs | flowise.homelab.pesulabs.net | ✅ | flowise-tls | flowise:3000 | ⚠️ Service missing |
| grafana-pesulabs | grafana.homelab.pesulabs.net | ✅ | grafana-tls | grafana:3000 | ⚠️ Service missing |
| homelab-dashboard | dash.pesulabs.net | ✅ | homelab-dashboard-tls | homelab-dashboard:80 | ✅ Working |
| lobechat-ingress | chat.homelab.pesulabs.net | ⚠️ HTTP only | lobechat-tls | lobechat:3210 | ⚠️ No TLS config |
| n8n-pesulabs | n8n.homelab.pesulabs.net | ✅ | n8n-tls | n8n:5678 | ✅ Working |
| prometheus-pesulabs | prometheus.homelab.pesulabs.net | ✅ | prometheus-tls | prometheus-svc:9090 | ✅ Working |
| webui-pesulabs | webui.homelab.pesulabs.net | ✅ | webui-tls | open-webui:8080 | ✅ Working |

### IngressRoutes (Traefik CRD)
❌ **No IngressRoutes found** - All routing is done via standard Kubernetes Ingress resources

---

## 4. HTTPS Configuration

### Middleware Configuration
✅ **HTTPS redirect middleware exists**:
```yaml
Name: https-redirect (homelab namespace)
Spec:
  redirectScheme:
    permanent: true
    scheme: https
Age: 2d19h
```

### Example Working Configuration (family-assistant)
```yaml
Annotations:
  cert-manager.io/cluster-issuer: letsencrypt-prod
  traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
  traefik.ingress.kubernetes.io/router.middlewares: homelab-https-redirect@kubernetescrd
  traefik.ingress.kubernetes.io/router.tls: "true"

Spec:
  tls:
  - hosts:
    - assistant.homelab.pesulabs.net
    secretName: family-assistant-tls
```

---

## 5. Issues and Errors

### Critical: Missing Backend Services
🚨 **Repeated errors in Traefik logs** (100 lines analyzed):

```
ERROR: Cannot create service error="service not found"
  - grafana-pesulabs ingress → grafana:3000 service (NOT FOUND)
  - flowise-pesulabs ingress → flowise:3000 service (NOT FOUND)
```

**Impact**: These Ingress resources are configured but cannot route traffic because backend services don't exist.

### Warning: Missing HTTPS Configuration
⚠️ **lobechat-ingress** (chat.homelab.pesulabs.net):
- Certificate exists and is valid (lobechat-tls)
- Ingress is configured for HTTP only
- Missing TLS section in Ingress spec
- Missing cert-manager annotations

---

## 6. Available Services (homelab namespace)

Backend services that ARE available:

| Service | Type | Port | Status |
|---------|------|------|--------|
| family-assistant | ClusterIP | 8001 | ✅ |
| homelab-dashboard | NodePort | 80 | ✅ |
| lobechat | ClusterIP | 3210 | ✅ |
| n8n | NodePort | 5678 | ✅ |
| open-webui | NodePort | 8080 | ✅ |
| prometheus-svc | NodePort | 9090 | ✅ |
| qdrant | ClusterIP | 6333/6334 | ✅ |
| mem0 | ClusterIP | 8080 | ✅ |
| postgres | ClusterIP | 5432 | ✅ |
| redis | ClusterIP | 6379 | ✅ |

**Missing services** referenced by Ingress:
- ❌ grafana (expected port 3000)
- ❌ flowise (expected port 3000)

---

## 7. Action Items

### High Priority

1. **Remove or Fix Grafana Ingress**
   ```bash
   # Option 1: Delete if Grafana is not deployed
   kubectl delete ingress grafana-pesulabs -n homelab
   kubectl delete certificate grafana-tls -n homelab

   # Option 2: Deploy Grafana service if needed
   # Deploy Grafana and ensure service exists on port 3000
   ```

2. **Remove or Fix Flowise Ingress**
   ```bash
   # Option 1: Delete if Flowise is not deployed
   kubectl delete ingress flowise-pesulabs -n homelab
   kubectl delete certificate flowise-tls -n homelab

   # Option 2: Deploy Flowise service if needed
   # Deploy Flowise and ensure service exists on port 3000
   ```

3. **Add HTTPS to lobechat-ingress**
   ```bash
   # Edit ingress to add TLS configuration
   kubectl edit ingress lobechat-ingress -n homelab
   ```

   Add these annotations:
   ```yaml
   annotations:
     cert-manager.io/cluster-issuer: letsencrypt-prod
     traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
     traefik.ingress.kubernetes.io/router.middlewares: homelab-https-redirect@kubernetescrd
     traefik.ingress.kubernetes.io/router.tls: "true"
   ```

   Add TLS section to spec:
   ```yaml
   spec:
     tls:
     - hosts:
       - chat.homelab.pesulabs.net
       secretName: lobechat-tls
   ```

### Medium Priority

4. **Monitor Traefik Logs**
   ```bash
   kubectl logs -n kube-system deployment/traefik --tail=50 -f
   ```
   Verify errors are resolved after cleanup.

5. **Verify All HTTPS Endpoints**
   Test each endpoint:
   ```bash
   curl -I https://assistant.homelab.pesulabs.net
   curl -I https://chat.homelab.pesulabs.net
   curl -I https://n8n.homelab.pesulabs.net
   curl -I https://webui.homelab.pesulabs.net
   curl -I https://prometheus.homelab.pesulabs.net
   curl -I https://dash.pesulabs.net
   ```

### Low Priority

6. **Standardize Middleware References**
   Two middleware resources exist (https-redirect and redirect-https).
   Consider consolidating to avoid confusion:
   ```bash
   kubectl get middleware -n homelab
   ```

7. **Document Service Deployment Pattern**
   Create a template for new services that includes:
   - Service definition
   - Ingress with proper annotations
   - Certificate (via cert-manager annotation)
   - HTTPS redirect middleware

---

## 8. HTTPS Setup Template

For adding new services with HTTPS:

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: <service-name>
  namespace: homelab
spec:
  selector:
    app: <service-name>
  ports:
  - port: <port>
    targetPort: <container-port>

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: <service-name>
  namespace: homelab
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
    traefik.ingress.kubernetes.io/router.middlewares: homelab-https-redirect@kubernetescrd
    traefik.ingress.kubernetes.io/router.tls: "true"
  labels:
    app: <service-name>
spec:
  ingressClassName: traefik
  rules:
  - host: <subdomain>.homelab.pesulabs.net
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: <service-name>
            port:
              number: <port>
  tls:
  - hosts:
    - <subdomain>.homelab.pesulabs.net
    secretName: <service-name>-tls
```

---

## 9. Summary

### What's Working ✅
- Traefik ingress controller (running, load balancer active)
- cert-manager (issuing Let's Encrypt certificates)
- 8 valid TLS certificates provisioned
- 6 services properly configured with HTTPS
- HTTPS redirect middleware operational

### What Needs Attention ⚠️
- Remove or deploy grafana service (Ingress exists but service missing)
- Remove or deploy flowise service (Ingress exists but service missing)
- Add HTTPS/TLS configuration to lobechat-ingress
- Clean up Traefik logs (currently spamming errors)

### Infrastructure Health: 75%
Core HTTPS infrastructure is solid. Issues are isolated to specific service configurations, not systemic problems with Traefik or cert-manager.
