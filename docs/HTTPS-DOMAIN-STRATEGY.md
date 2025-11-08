# 🔒 HTTPS & Domain Strategy for Homelab

## Overview

This document outlines the strategy for implementing HTTPS certificates and domain-based access for all homelab services, replacing direct IP:port access with secure, user-friendly URLs.

---

## 🎯 Goals

1. **Security**: Encrypt all traffic with TLS/HTTPS
2. **Usability**: Access services via memorable domains (e.g., `grafana.homelab.local`)
3. **Professional**: Production-like setup for development/learning
4. **Automation**: Certificate management with auto-renewal
5. **Flexibility**: Support both internal and external access

---

## 📋 Proposed Domain Structure

### Internal Domain: `.homelab.local`

**Service Subdomains**:
```
grafana.homelab.local       → Grafana (monitoring dashboards)
prometheus.homelab.local    → Prometheus (metrics API)
n8n.homelab.local          → N8n (workflow automation)
webui.homelab.local        → Open WebUI (LLM chat interface)
ollama.homelab.local       → Ollama API (LLM inference)
litellm.homelab.local      → LiteLLM API (OpenAI-compatible)
postgres.homelab.local     → PostgreSQL (database)
```

**Alternative: Node-based Naming**:
```
asuna.homelab.local        → Service node main page
pesubuntu.homelab.local    → Compute node main page

grafana.asuna.homelab.local
n8n.asuna.homelab.local
ollama.pesubuntu.homelab.local
```

### External Domain (Optional): `yourdomain.com`

For Tailscale or public access:
```
grafana.home.yourdomain.com
n8n.home.yourdomain.com
```

---

## 🔧 Implementation Options

### Option 1: Self-Signed Certificates (Quick Start)

**Pros**:
- ✅ Free and immediate
- ✅ No external dependencies
- ✅ Works offline
- ✅ Full control

**Cons**:
- ❌ Browser warnings (must manually trust)
- ❌ Not suitable for public access
- ❌ Manual trust on each device

**Best for**: Internal development, learning, testing

---

### Option 2: Let's Encrypt + Traefik (Production)

**Pros**:
- ✅ Trusted by all browsers
- ✅ Automated renewal
- ✅ Industry standard
- ✅ Free

**Cons**:
- ❌ Requires public domain
- ❌ Needs DNS challenge or port 80/443 exposed
- ❌ More complex setup

**Best for**: Services exposed to internet, production-like setup

---

### Option 3: Let's Encrypt + DNS Challenge (Recommended)

**Pros**:
- ✅ Trusted certificates
- ✅ Works with private IPs
- ✅ No port forwarding needed
- ✅ Wildcard certificate support
- ✅ Automated renewal

**Cons**:
- ❌ Requires domain with DNS API support (Cloudflare, etc.)
- ❌ Initial setup complexity

**Best for**: Homelab with Tailscale, internal services with trusted certs

---

### Option 4: Internal CA with Step-CA (Advanced)

**Pros**:
- ✅ Full control over certificate authority
- ✅ Issue certs for any domain
- ✅ No external dependencies
- ✅ Works offline
- ✅ Automated renewal

**Cons**:
- ❌ Must install root CA on all devices
- ❌ Complex initial setup

**Best for**: Enterprise-like homelab, learning PKI

---

## 🚀 Recommended Implementation Plan

### Phase 1: DNS Setup (Local Resolution)

**Option A: Local DNS Server (Recommended)**

Deploy **Pihole** or **AdGuard Home** on the GL-MT2500 router:

```yaml
# DNS Records to configure:
grafana.homelab.local       A    192.168.8.185
prometheus.homelab.local    A    192.168.8.185
n8n.homelab.local          A    192.168.8.185
webui.homelab.local        A    192.168.8.185
ollama.homelab.local       A    192.168.8.185  # Points to service node, then proxied
litellm.homelab.local      A    192.168.8.185

# Wildcard (optional)
*.homelab.local            A    192.168.8.185
*.asuna.homelab.local      A    192.168.8.185
*.pesubuntu.homelab.local  A    100.72.98.106
```

**Option B: /etc/hosts on Each Device**

For quick testing without DNS server:

```bash
# Add to /etc/hosts on each device
192.168.8.185  grafana.homelab.local
192.168.8.185  prometheus.homelab.local
192.168.8.185  n8n.homelab.local
192.168.8.185  webui.homelab.local
100.72.98.106  ollama.homelab.local
100.72.98.106  litellm.homelab.local
```

**Option C: Router DHCP + DNS**

Configure GL-MT2500 to serve DNS records via DHCP.

---

### Phase 2: Deploy Ingress Controller (Traefik)

**Why Traefik?**
- Native Kubernetes integration
- Automatic Let's Encrypt support
- Built-in dashboard
- Simple configuration
- HTTP/HTTPS routing

**Deployment**:

```bash
# Deploy Traefik to K3s
kubectl apply -f infrastructure/kubernetes/ingress/traefik-deployment.yaml
```

**Features**:
- Single entry point (ports 80/443)
- Automatic routing based on hostname
- TLS termination
- Automatic certificate management

---

### Phase 3: Certificate Strategy

#### **Recommended: Let's Encrypt + DNS Challenge**

**Requirements**:
1. Domain name (e.g., `yourdomain.com` or free DuckDNS)
2. DNS provider with API (Cloudflare, Route53, etc.)
3. Traefik with DNS challenge configured

**Configuration**:

```yaml
# Traefik certificate resolver
certificatesResolvers:
  letsencrypt:
    acme:
      email: your-email@example.com
      storage: /certs/acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"
          - "8.8.8.8:53"
```

**Benefits**:
- Wildcard certificate: `*.homelab.yourdomain.com`
- Valid for internal IPs
- No port forwarding required
- Auto-renewal

#### **Alternative: Self-Signed CA**

**Step 1: Create Root CA**

```bash
# Generate root CA
openssl genrsa -out ca-key.pem 4096
openssl req -new -x509 -days 3650 -key ca-key.pem -out ca-cert.pem \
  -subj "/C=US/ST=State/L=City/O=Homelab/CN=Homelab Root CA"
```

**Step 2: Create Wildcard Certificate**

```bash
# Generate certificate for *.homelab.local
openssl genrsa -out homelab-key.pem 4096
openssl req -new -key homelab-key.pem -out homelab.csr \
  -subj "/C=US/ST=State/L=City/O=Homelab/CN=*.homelab.local"

# Sign with CA
openssl x509 -req -days 365 -in homelab.csr \
  -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial \
  -out homelab-cert.pem
```

**Step 3: Install Root CA on Devices**

```bash
# Linux
sudo cp ca-cert.pem /usr/local/share/ca-certificates/homelab-ca.crt
sudo update-ca-certificates

# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ca-cert.pem

# Windows
certutil -addstore -f "ROOT" ca-cert.pem
```

**Step 4: Create Kubernetes Secret**

```bash
kubectl create secret tls homelab-tls \
  --cert=homelab-cert.pem \
  --key=homelab-key.pem \
  -n homelab
```

---

### Phase 4: Configure Ingress for Each Service

**Example: Grafana Ingress**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana
  namespace: homelab
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
spec:
  ingressClassName: traefik
  tls:
    - hosts:
        - grafana.homelab.local
      secretName: homelab-tls
  rules:
    - host: grafana.homelab.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: grafana
                port:
                  number: 3000
```

**Example: N8n Ingress**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: n8n
  namespace: homelab
spec:
  ingressClassName: traefik
  tls:
    - hosts:
        - n8n.homelab.local
      secretName: homelab-tls
  rules:
    - host: n8n.homelab.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: n8n
                port:
                  number: 5678
```

---

## 📦 Complete Implementation

### Directory Structure

```
infrastructure/
├── kubernetes/
│   ├── ingress/
│   │   ├── traefik-deployment.yaml
│   │   ├── traefik-config.yaml
│   │   ├── grafana-ingress.yaml
│   │   ├── n8n-ingress.yaml
│   │   ├── prometheus-ingress.yaml
│   │   ├── webui-ingress.yaml
│   │   └── README.md
│   └── certificates/
│       ├── cert-manager-deployment.yaml (optional)
│       ├── letsencrypt-issuer.yaml
│       └── README.md
└── certs/
    ├── ca-cert.pem
    ├── ca-key.pem (secure!)
    └── generate-certs.sh
```

---

## 🔄 Migration Path

### Current State (HTTP + NodePort)
```
http://192.168.8.185:30300  → Grafana
http://192.168.8.185:30090  → Prometheus
http://192.168.8.185:30678  → N8n
http://192.168.8.185:30080  → Open WebUI
```

### Target State (HTTPS + Domains)
```
https://grafana.homelab.local     → Grafana
https://prometheus.homelab.local  → Prometheus
https://n8n.homelab.local        → N8n
https://webui.homelab.local      → Open WebUI
```

### Migration Steps

1. **Deploy Traefik** (Ingress stays alongside NodePort initially)
2. **Configure DNS** (add local DNS records)
3. **Generate/obtain certificates**
4. **Create Ingress resources** (test alongside NodePort)
5. **Verify HTTPS access works**
6. **Update documentation and bookmarks**
7. **Optionally remove NodePort services** (keep for backup access)

---

## 🛠️ Tools & Technologies

### Required
- **Traefik** or **Nginx Ingress**: Ingress controller
- **Cert-manager** (optional): Kubernetes certificate automation
- **DNS Server**: Local DNS resolution (Pihole, AdGuard, or router DNS)

### Optional
- **Cloudflare**: DNS provider for Let's Encrypt DNS challenge
- **DuckDNS**: Free dynamic DNS service
- **Step-CA**: Internal certificate authority

---

## 📋 Deployment Checklist

### Prerequisites
- [ ] Choose domain strategy (.homelab.local vs real domain)
- [ ] Choose certificate approach (self-signed vs Let's Encrypt)
- [ ] Configure local DNS or /etc/hosts
- [ ] Install Traefik in K3s cluster

### Certificate Setup
- [ ] Generate or obtain certificates
- [ ] Create Kubernetes TLS secrets
- [ ] Configure Traefik to use certificates
- [ ] (Optional) Install root CA on devices

### Service Configuration
- [ ] Create Ingress resources for each service
- [ ] Update service configs with new URLs
- [ ] Test HTTPS access to each service
- [ ] Verify certificate validity

### Finalization
- [ ] Update documentation with new URLs
- [ ] Create bookmarks for easy access
- [ ] Set up monitoring for certificate expiry
- [ ] (Optional) Remove NodePort services

---

## 🎯 Recommended Quick Start

**For immediate HTTPS access:**

1. **Deploy Traefik**:
   ```bash
   helm install traefik traefik/traefik -n kube-system \
     --set ports.web.port=80 \
     --set ports.websecure.port=443 \
     --set ports.websecure.tls.enabled=true
   ```

2. **Generate Self-Signed Wildcard Cert**:
   ```bash
   ./scripts/generate-homelab-certs.sh
   ```

3. **Add to /etc/hosts**:
   ```bash
   echo "192.168.8.185 grafana.homelab.local n8n.homelab.local webui.homelab.local prometheus.homelab.local" | sudo tee -a /etc/hosts
   ```

4. **Create Ingress for Services**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/ingress/
   ```

5. **Access Services**:
   - https://grafana.homelab.local (accept self-signed cert warning)
   - https://n8n.homelab.local
   - https://webui.homelab.local

---

## 🔮 Future Enhancements

### Short Term
- [ ] Traefik dashboard with authentication
- [ ] HTTP → HTTPS redirect
- [ ] Rate limiting on ingress
- [ ] IP whitelisting for admin interfaces

### Medium Term
- [ ] OAuth/OIDC authentication (Authelia, Keycloak)
- [ ] Automatic certificate monitoring
- [ ] Certificate expiry alerts
- [ ] Backup DNS server (redundancy)

### Long Term
- [ ] Service mesh (Istio/Linkerd) with mTLS
- [ ] Zero-trust network access
- [ ] Integration with external identity providers
- [ ] API gateway with authentication

---

## 📖 Additional Resources

- **Traefik Documentation**: https://doc.traefik.io/traefik/
- **Cert-manager**: https://cert-manager.io/docs/
- **Let's Encrypt**: https://letsencrypt.org/docs/
- **Cloudflare DNS API**: https://developers.cloudflare.com/api/
- **Step-CA**: https://smallstep.com/docs/step-ca/

---

## 🔒 Security Considerations

### Certificate Storage
- **Private keys**: Must be kept secure
- **Kubernetes secrets**: Use RBAC to restrict access
- **Backup**: Encrypted backups of certificates and keys

### Access Control
- **Internal only**: Keep services on local network
- **Tailscale**: Use for secure remote access
- **Authentication**: Add auth layer (OAuth, basic auth)

### Monitoring
- **Certificate expiry**: Alert 30 days before expiry
- **Failed renewals**: Monitor cert-manager logs
- **Unusual access**: Set up alerts in Grafana

---

## ✅ Success Criteria

After implementation, you should have:

- ✅ All services accessible via HTTPS
- ✅ User-friendly domain names (no IP:port)
- ✅ Valid certificates (self-signed or Let's Encrypt)
- ✅ Automated certificate management
- ✅ Simplified access for users
- ✅ Professional homelab setup

---

**Next Steps**: Choose your certificate strategy and we can implement Traefik + HTTPS for all services!

---

**Last Updated**: 2025-10-22
**Version**: 1.0.0
**Status**: Planning Document
