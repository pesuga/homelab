# New Service Deployment Checklist

**IMPORTANT**: Follow this checklist when adding ANY new service to the homelab cluster.

## Required: DNS and TLS Configuration

### 1. ✅ Subdomain Requirements
- **MUST** use a `*.pesulabs.net` subdomain
- **DO NOT** use `.homelab.local` domains (Let's Encrypt doesn't support `.local` TLD)
- Choose a descriptive subdomain:
  - Pattern: `<service>.homelab.pesulabs.net`
  - Short names: `dash.pesulabs.net`, `chat.pesulabs.net`

### 2. ✅ DNS Configuration
Add DNS record in Tailscale MagicDNS or Cloudflare:
```bash
# Example for a new service called "myservice"
# Add to CoreDNS custom config or Cloudflare:
myservice.homelab.pesulabs.net → 100.81.76.55 (Traefik on asuna node)
```

### 3. ✅ TLS Certificate Configuration
**Ingress must include**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myservice-ingress
  namespace: homelab
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod  # REQUIRED for auto cert
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure  # REQUIRED for HTTP + HTTPS
    traefik.ingress.kubernetes.io/router.tls: "true"  # REQUIRED for TLS
    traefik.ingress.kubernetes.io/router.middlewares: homelab-https-redirect@kubernetescrd  # REQUIRED for HTTP→HTTPS
spec:
  ingressClassName: traefik
  tls:  # REQUIRED TLS section
  - hosts:
    - myservice.homelab.pesulabs.net
    secretName: myservice-tls  # cert-manager will create this automatically
  rules:
  - host: myservice.homelab.pesulabs.net
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myservice
            port:
              number: 8080
```

### 4. ✅ Certificate Auto-Creation
When you apply the ingress:
- cert-manager will automatically detect the `cert-manager.io/cluster-issuer` annotation
- It will create a Certificate resource named `myservice-tls`
- It will request a Let's Encrypt certificate via DNS-01 challenge (Cloudflare)
- The certificate will be stored in the Secret `myservice-tls`
- Traefik will automatically use the certificate

**Verify certificate creation**:
```bash
# Watch certificate creation
kubectl get certificate -n homelab -w

# Check certificate status
kubectl describe certificate myservice-tls -n homelab

# Should show:
# Status:
#   Conditions:
#     Status: True
#     Type:   Ready
```

## Service Deployment Template

### Step 1: Create Service Manifest
```yaml
# infrastructure/kubernetes/services/myservice/myservice.yaml
---
apiVersion: v1
kind: Service
metadata:
  name: myservice
  namespace: homelab
spec:
  type: ClusterIP
  ports:
    - port: 8080
      targetPort: 8080
  selector:
    app: myservice
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myservice
  namespace: homelab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myservice
  template:
    metadata:
      labels:
        app: myservice
      annotations:
        prometheus.io/scrape: "true"  # Optional: for Prometheus monitoring
        prometheus.io/port: "8080"
    spec:
      containers:
      - name: myservice
        image: myservice:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        # RECOMMENDED: Add health probes
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
---
# Ingress with TLS - REQUIRED
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myservice-ingress
  namespace: homelab
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
    traefik.ingress.kubernetes.io/router.middlewares: homelab-https-redirect@kubernetescrd
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - myservice.homelab.pesulabs.net
    secretName: myservice-tls
  rules:
  - host: myservice.homelab.pesulabs.net
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myservice
            port:
              number: 8080
```

### Step 2: Deploy
```bash
# Apply the manifest
kubectl apply -f infrastructure/kubernetes/services/myservice/myservice.yaml

# Wait for certificate to be issued (takes 1-2 minutes)
kubectl get certificate -n homelab -w

# Verify ingress is created
kubectl get ingress -n homelab | grep myservice
```

### Step 3: Verify HTTPS Access
```bash
# Test HTTPS with valid certificate
curl -I https://myservice.homelab.pesulabs.net

# Test HTTP→HTTPS redirect
curl -I http://myservice.homelab.pesulabs.net
# Should show: HTTP/1.1 308 Permanent Redirect

# Check certificate details
openssl s_client -connect myservice.homelab.pesulabs.net:443 -servername myservice.homelab.pesulabs.net </dev/null 2>&1 | grep -E "issuer="
# Should show: issuer=C=US, O=Let's Encrypt, CN=R12 (or R13)
```

## Common Mistakes to Avoid

### ❌ DO NOT Use `.homelab.local` Domains
```yaml
# WRONG - Let's Encrypt will reject this
tls:
- hosts:
  - myservice.homelab.local  # ❌ Will fail
```

```yaml
# CORRECT - Use .pesulabs.net
tls:
- hosts:
  - myservice.homelab.pesulabs.net  # ✅ Will work
```

### ❌ DO NOT Forget TLS Section
```yaml
# WRONG - No TLS section = no certificate
spec:
  rules:
  - host: myservice.homelab.pesulabs.net  # ❌ Missing TLS section
```

```yaml
# CORRECT - TLS section required
spec:
  tls:  # ✅ Required
  - hosts:
    - myservice.homelab.pesulabs.net
    secretName: myservice-tls
  rules:
  - host: myservice.homelab.pesulabs.net
```

### ❌ DO NOT Use `websecure` Only
```yaml
# WRONG - HTTP won't work
annotations:
  traefik.ingress.kubernetes.io/router.entrypoints: websecure  # ❌ No HTTP redirect
```

```yaml
# CORRECT - Accept both HTTP and HTTPS
annotations:
  traefik.ingress.kubernetes.io/router.entrypoints: web,websecure  # ✅ HTTP redirects to HTTPS
  traefik.ingress.kubernetes.io/router.middlewares: homelab-https-redirect@kubernetescrd
```

### ❌ DO NOT Forget cert-manager Annotation
```yaml
# WRONG - No automatic certificate
metadata:
  annotations:
    traefik.ingress.kubernetes.io/router.tls: "true"  # ❌ Missing cert-manager annotation
```

```yaml
# CORRECT - cert-manager will auto-create certificate
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod  # ✅ Auto cert creation
    traefik.ingress.kubernetes.io/router.tls: "true"
```

## Troubleshooting

### Certificate Not Issuing
```bash
# Check certificate status
kubectl describe certificate myservice-tls -n homelab

# Common issues:
# - "Domain name does not end with a valid public suffix (TLD)" → Using .local domain
# - "Failed to create Order" → Check Cloudflare API token permissions
# - "DNS record not found" → Add DNS record first

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager --tail=50
```

### HTTP Not Redirecting to HTTPS
```bash
# Verify middleware exists
kubectl get middleware -n homelab

# Verify ingress has middleware annotation
kubectl get ingress myservice-ingress -n homelab -o yaml | grep middlewares

# Should show:
# traefik.ingress.kubernetes.io/router.middlewares: homelab-https-redirect@kubernetescrd
```

### Self-Signed Certificate Error
```bash
# Check if Traefik is using the correct certificate
openssl s_client -connect myservice.homelab.pesulabs.net:443 -servername myservice.homelab.pesulabs.net </dev/null 2>&1 | grep issuer

# Should show Let's Encrypt, not Traefik:
# issuer=C=US, O=Let's Encrypt, CN=R12  ✅ Correct
# issuer=CN=TRAEFIK DEFAULT CERT         ❌ Wrong - cert not being used
```

## Reference: Existing Services

**All current services follow this pattern**:
- LobeChat: `https://chat.homelab.pesulabs.net`
- N8n: `https://n8n.homelab.pesulabs.net`
- Grafana: `https://grafana.homelab.pesulabs.net`
- Prometheus: `https://prometheus.homelab.pesulabs.net`
- Flowise: `https://flowise.homelab.pesulabs.net`
- Open WebUI: `https://webui.homelab.pesulabs.net`
- Dashboard: `https://dash.pesulabs.net`

**Check existing ingresses for examples**:
```bash
kubectl get ingress -n homelab -o yaml | less
```

## Quick Copy-Paste Template

```yaml
# Replace 'myservice' with your service name
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myservice-ingress
  namespace: homelab
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
    traefik.ingress.kubernetes.io/router.middlewares: homelab-https-redirect@kubernetescrd
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - myservice.homelab.pesulabs.net
    secretName: myservice-tls
  rules:
  - host: myservice.homelab.pesulabs.net
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myservice
            port:
              number: 8080
```

## Summary

**Every new service MUST have**:
1. ✅ A `*.pesulabs.net` subdomain (NOT `.local`)
2. ✅ Ingress with TLS configuration
3. ✅ `cert-manager.io/cluster-issuer: letsencrypt-prod` annotation
4. ✅ Both `web,websecure` entrypoints
5. ✅ HTTP→HTTPS redirect middleware
6. ✅ Valid Let's Encrypt certificate (auto-created)

**NO EXCEPTIONS** - This is a hard requirement for all services in the homelab cluster.
