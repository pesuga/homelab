# N8n Domain Setup Guide

## Overview

This guide helps you set up N8n with a custom domain (n8n.pesulabs.net) so OAuth integrations work properly.

**Problem**: N8n shows internal cluster URLs which don't work with OAuth callbacks
**Solution**: Use Traefik Ingress with a proper domain name and TLS certificate

---

## Prerequisites

- ✅ Domain: pesulabs.net with Cloudflare
- ✅ K3s cluster with Traefik Ingress controller (already installed)
- ✅ N8n deployed in homelab namespace
- ⏳ DNS record pointing to service node
- ⏳ TLS certificate configured

---

## Step 1: Configure DNS in Cloudflare

Add an A record for N8n:

```
Type: A
Name: n8n
Target: <YOUR_PUBLIC_IP> or use Cloudflare Tunnel
Proxy: Orange cloud (proxied) - recommended for HTTPS
TTL: Auto
```

### Option A: Direct IP (if you have static public IP)
```
n8n.pesulabs.net → YOUR_PUBLIC_IP
```

### Option B: Cloudflare Tunnel (recommended if behind NAT)
```
Create a Cloudflare Tunnel pointing to:
Internal: 192.168.8.185:30678 (or use Ingress on port 80/443)
```

### Option C: Tailscale + DNS (internal access only)
```
n8n.pesulabs.net → 100.81.76.55 (Tailscale IP)
Note: This won't work for external OAuth providers
```

---

## Step 2: Deploy Ingress Configuration

Apply the Ingress manifest:

```bash
kubectl apply -f infrastructure/kubernetes/ingress/n8n-ingress.yaml
```

Verify Ingress is created:

```bash
kubectl get ingress -n homelab n8n-ingress
kubectl describe ingress -n homelab n8n-ingress
```

---

## Step 3: Set Up TLS Certificate

### Option A: Let's Encrypt with Cert-Manager (Recommended)

Install Cert-Manager:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml
```

Create ClusterIssuer for Let's Encrypt:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: gonzalo.iglesias@pesulabs.net
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: traefik
EOF
```

Update Ingress to use cert-manager:

```bash
kubectl patch ingress n8n-ingress -n homelab --type=json -p='[
  {
    "op": "add",
    "path": "/metadata/annotations/cert-manager.io~1cluster-issuer",
    "value": "letsencrypt-prod"
  }
]'
```

### Option B: Cloudflare Origin Certificate

1. Go to Cloudflare Dashboard → SSL/TLS → Origin Server
2. Create Certificate
3. Save certificate and private key
4. Create Kubernetes Secret:

```bash
kubectl create secret tls n8n-tls-cert -n homelab \
  --cert=origin-cert.pem \
  --key=origin-key.pem
```

### Option C: Self-Signed Certificate (Development Only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=n8n.pesulabs.net"

kubectl create secret tls n8n-tls-cert -n homelab \
  --cert=tls.crt --key=tls.key
```

---

## Step 4: Update N8n Configuration

Update N8n deployment to use the external URL:

```bash
kubectl set env deployment/n8n -n homelab \
  WEBHOOK_URL="https://n8n.pesulabs.net/" \
  N8N_EDITOR_BASE_URL="https://n8n.pesulabs.net"
```

Or edit the deployment directly:

```bash
kubectl edit deployment n8n -n homelab
```

Add these environment variables:

```yaml
env:
- name: WEBHOOK_URL
  value: "https://n8n.pesulabs.net/"
- name: N8N_EDITOR_BASE_URL
  value: "https://n8n.pesulabs.net"
- name: N8N_PROTOCOL
  value: "https"
- name: N8N_HOST
  value: "n8n.pesulabs.net"
```

Restart N8n:

```bash
kubectl rollout restart deployment/n8n -n homelab
```

---

## Step 5: Verify Setup

### Check Ingress Status

```bash
kubectl get ingress -n homelab
```

Expected output:
```
NAME          CLASS     HOSTS               ADDRESS         PORTS     AGE
n8n-ingress   traefik   n8n.pesulabs.net    192.168.8.185   80, 443   1m
```

### Check Certificate

```bash
kubectl get certificate -n homelab
kubectl describe certificate n8n-tls-cert -n homelab
```

### Test Access

From your browser or curl:

```bash
# Test HTTP (should redirect to HTTPS)
curl -I http://n8n.pesulabs.net

# Test HTTPS
curl -I https://n8n.pesulabs.net

# Full test
curl -k https://n8n.pesulabs.net
```

Expected: You should see the N8n login page

---

## Step 6: Configure OAuth Applications

Now you can use the proper URL in OAuth provider settings:

**Redirect/Callback URL format**:
```
https://n8n.pesulabs.net/rest/oauth2-credential/callback
```

**Example for Google OAuth**:
- Authorized redirect URIs: `https://n8n.pesulabs.net/rest/oauth2-credential/callback`

**Example for GitHub OAuth**:
- Authorization callback URL: `https://n8n.pesulabs.net/rest/oauth2-credential/callback`

---

## Troubleshooting

### Ingress Not Working

```bash
# Check Traefik is running
kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik

# Check Traefik logs
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik

# Check Ingress events
kubectl describe ingress n8n-ingress -n homelab
```

### Certificate Not Issuing

```bash
# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager

# Check certificate request
kubectl get certificaterequest -n homelab
kubectl describe certificaterequest -n homelab

# Check ACME challenge
kubectl get challenges -n homelab
```

### DNS Not Resolving

```bash
# Test DNS resolution
nslookup n8n.pesulabs.net
dig n8n.pesulabs.net

# Check Cloudflare DNS propagation
https://www.whatsmydns.net/#A/n8n.pesulabs.net
```

### N8n Still Shows Internal URL

```bash
# Check environment variables
kubectl get deployment n8n -n homelab -o yaml | grep -A 10 env:

# Check N8n logs
kubectl logs -n homelab -l app=n8n

# Restart N8n
kubectl rollout restart deployment/n8n -n homelab
```

---

## Architecture After Setup

```
Internet
  │
  ▼
Cloudflare (Optional Proxy/Tunnel)
  │
  ▼
Your Router/Firewall (Port 80/443)
  │
  ▼
Service Node (192.168.8.185)
  │
  ▼
Traefik Ingress Controller
  │
  ├─ HTTP (port 80) ──→ HTTPS redirect
  └─ HTTPS (port 443) ──→ TLS termination
      │
      ▼
  N8n Service (ClusterIP:5678)
      │
      ▼
  N8n Pod
```

---

## Security Considerations

1. **Use HTTPS Only**: Never use HTTP for OAuth callbacks
2. **Valid Certificate**: Use Let's Encrypt or Cloudflare Origin certificates
3. **Firewall Rules**: Only open ports 80/443 on your router
4. **Cloudflare Proxy**: Enable orange cloud for DDoS protection
5. **Rate Limiting**: Configure Traefik or Cloudflare rate limits

---

## Alternative: Cloudflare Tunnel (No Port Forwarding)

If you don't want to expose your homelab directly:

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create n8n-homelab

# Configure tunnel
cat > ~/.cloudflared/config.yml <<EOF
tunnel: n8n-homelab
credentials-file: /home/pesu/.cloudflared/<TUNNEL-ID>.json

ingress:
  - hostname: n8n.pesulabs.net
    service: http://192.168.8.185:30678
  - service: http_status:404
EOF

# Run tunnel
cloudflared tunnel run n8n-homelab

# Or create systemd service for auto-start
sudo cloudflared service install
```

Then in Cloudflare dashboard, add DNS record:
```
Type: CNAME
Name: n8n
Target: <TUNNEL-ID>.cfargotunnel.com
Proxy: Enabled
```

---

## Next Steps

1. ✅ Set up DNS record
2. ✅ Apply Ingress configuration
3. ✅ Configure TLS certificate
4. ✅ Update N8n environment variables
5. ✅ Test OAuth integrations
6. 📋 Configure additional services (Grafana, etc.)

---

**Last Updated**: 2025-10-24
**Status**: Configuration Ready
**Requires**: DNS setup + TLS certificate configuration
