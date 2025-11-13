# HTTPS Deployment Summary - Phase 1 Complete

## Deployment Status: ✅ Ready for Port Forwarding

Date: 2025-11-13
Status: Infrastructure configured, awaiting router port forwarding

---

## What Was Completed

### 1. ✅ Traefik HTTPS Ingress Configuration

**DNS-01 Challenge with Cloudflare**:
- Configured Traefik to use Cloudflare DNS-01 challenge for Let's Encrypt certificates
- Environment variable `CF_DNS_API_TOKEN` configured with Cloudflare API token
- ACME storage configured at `/acme/acme.json` (persistent volume)
- Email: admin@pesulabs.net

**Traefik Configuration** ([infrastructure/kubernetes/traefik/traefik-deployment.yaml](../infrastructure/kubernetes/traefik/traefik-deployment.yaml:33-37)):
```yaml
args:
  - --certificatesresolvers.default.acme.dnschallenge=true
  - --certificatesresolvers.default.acme.dnschallenge.provider=cloudflare
  - --certificatesresolvers.default.acme.dnschallenge.resolvers=1.1.1.1:53,8.8.8.8:53
  - --certificatesresolvers.default.acme.email=admin@pesulabs.net
  - --certificatesresolvers.default.acme.storage=/acme/acme.json
```

### 2. ✅ Ingress Resources Updated

**All 4 services configured with auto-ACME**:

1. **Dashboard** ([production/monitoring/homelab-dashboard/k8s/ingress.yaml](../production/monitoring/homelab-dashboard/k8s/ingress.yaml)):
   - Host: `dash.pesulabs.net`
   - Cert Resolver: `default` (auto-ACME)
   - Service: `homelab-dashboard:80`

2. **N8n** ([infrastructure/kubernetes/ingress-acme-fix.yaml](../infrastructure/kubernetes/ingress-acme-fix.yaml)):
   - Host: `n8n.homelab.pesulabs.net`
   - Cert Resolver: `default` (auto-ACME)
   - Service: `n8n:5678`

3. **Family Assistant** ([services/ingress-fix.yaml](../services/ingress-fix.yaml:6-14)):
   - Host: `family-assistant.homelab.pesulabs.net`
   - Cert Resolver: `default` (auto-ACME)
   - Service: `family-assistant:8001`

4. **Discovery Dashboard** ([services/ingress-fix.yaml](../services/ingress-fix.yaml:32-40)):
   - Host: `discover.homelab.pesulabs.net`
   - Cert Resolver: `default` (auto-ACME)
   - Service: `discovery-dashboard:80`

**Key Changes**:
- Removed `secretName` from TLS sections (lets Traefik auto-generate)
- Added annotation: `traefik.ingress.kubernetes.io/router.tls.certresolver: default`
- All ingresses use `ingressClassName: traefik`

### 3. ✅ Cloudflare DNS Records Configured

**All DNS records pointing to public IP `181.117.166.31`**:

| Domain | Type | Content | Proxied |
|--------|------|---------|---------|
| dash.pesulabs.net | A | 181.117.166.31 | No |
| n8n.homelab.pesulabs.net | A | 181.117.166.31 | No |
| family-assistant.homelab.pesulabs.net | A | 181.117.166.31 | No |
| discover.homelab.pesulabs.net | A | 181.117.166.31 | No |

**Verification**:
```bash
$ dig +short @1.1.1.1 dash.pesulabs.net A
181.117.166.31

$ dig +short @1.1.1.1 n8n.homelab.pesulabs.net A
181.117.166.31
```

✅ All records resolving correctly

### 4. ✅ Internal HTTPS Access Working

**Services accessible via Traefik NodePort (internal network)**:

Test from within Tailscale network:
```bash
# Dashboard (302 redirect to login - expected)
$ curl -skI https://100.81.76.55:30253 -H "Host: dash.pesulabs.net"
HTTP/2 302
location: /login?next=https://dash.pesulabs.net/

# Family Assistant (405 - service responding)
$ curl -skI https://100.81.76.55:30253/health -H "Host: family-assistant.homelab.pesulabs.net"
HTTP/2 405
allow: GET
```

✅ Traefik HTTPS ingress working internally

### 5. ✅ Homelab Dashboard URLs Configured

Dashboard already configured with HTTPS URLs ([production/monitoring/homelab-dashboard/app/app.py](../production/monitoring/homelab-dashboard/app/app.py:66-154)):

**Services with HTTPS**:
- Prometheus: `https://prometheus.homelab.pesulabs.net`
- N8n: `https://n8n.homelab.pesulabs.net`
- LobeChat: `https://chat.homelab.pesulabs.net`

**Services with HTTP (NodePort for internal tools)**:
- Ollama: `http://100.81.76.55:30277`
- Qdrant: `http://100.81.76.55:30633`
- Mem0: `http://100.81.76.55:30880`
- Loki: `http://100.81.76.55:30314`
- Docker Registry: `http://100.81.76.55:30500`

---

## What Needs Manual Configuration

### ⏳ Router Port Forwarding Required

**To enable public HTTPS access, configure these port forwarding rules on your router:**

| External Port | Internal IP | Internal Port | Protocol | Description |
|---------------|-------------|---------------|----------|-------------|
| 80 | 192.168.8.185 | 32060 | TCP | HTTP → Traefik (redirects to HTTPS) |
| 443 | 192.168.8.185 | 30253 | TCP | HTTPS → Traefik |

**Why These Ports?**
- Traefik service is type `LoadBalancer` with NodePorts assigned:
  - Port 80 → NodePort 32060 (web/HTTP)
  - Port 443 → NodePort 30253 (websecure/HTTPS)
- K3s service node (asuna) IP: 192.168.8.185

**Router Access**:
- Typically accessed at: http://192.168.8.1 or http://192.168.1.1
- Look for "Port Forwarding", "NAT", or "Virtual Servers" section
- Some routers may call it "Application & Gaming"

**Detailed Instructions**: See [PORT-FORWARDING-SETUP.md](./PORT-FORWARDING-SETUP.md)

---

## Certificate Issuance Process

### How Let's Encrypt Certificates Will Be Issued

1. **DNS-01 Challenge Flow**:
   ```
   Browser → https://dash.pesulabs.net:443
   ↓ (router forwards to Traefik)
   Traefik → Sees unknown certificate needed
   ↓
   Traefik → Cloudflare API (creates TXT record)
   Cloudflare DNS → _acme-challenge.dash.pesulabs.net TXT "verification-string"
   ↓
   Let's Encrypt → Verifies TXT record via DNS
   ↓
   Let's Encrypt → Issues certificate
   ↓
   Traefik → Saves to /acme/acme.json (persistent volume)
   ↓
   Traefik → Serves HTTPS with valid cert
   ```

2. **Why DNS-01 Challenge?**
   - Works with private/Tailscale IPs (no public HTTP access needed)
   - Only requires DNS record verification
   - Cloudflare API creates verification TXT records automatically

3. **Certificate Renewal**:
   - Auto-renewal 30 days before expiration
   - Handled automatically by Traefik
   - No manual intervention required

---

## Network Architecture

### Current Network Setup

```
┌─────────────────────────────────────────────────────────────┐
│ Internet                                                    │
│ Public IP: 181.117.166.31                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                  ┌─────▼──────┐
                  │   Router   │ ⚠️ Port forwarding needed
                  │ (192.168   │
                  │  .8.1)     │
                  └─────┬──────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
  ┌─────▼─────┐   ┌────▼────┐    ┌────▼────┐
  │pesubuntu  │   │  asuna  │    │ Other   │
  │(compute)  │   │ (K3s)   │    │ Devices │
  │100.72.    │   │100.81.  │    │         │
  │  98.106   │   │  76.55  │    │         │
  └───────────┘   └────┬────┘    └─────────┘
                       │
              ┌────────▼─────────┐
              │   Traefik        │
              │ NodePort 32060   │ HTTP (redirects →HTTPS)
              │ NodePort 30253   │ HTTPS ✓
              └────────┬─────────┘
                       │
         ┌─────────────┼──────────────┐
         │             │              │
    ┌────▼────┐   ┌───▼────┐   ┌────▼──────┐
    │Dashboard│   │  N8n   │   │  Family   │
    │ :80     │   │ :5678  │   │ Assistant │
    └─────────┘   └────────┘   │  :8001    │
                                └───────────┘
```

### DNS Resolution Flow

```
User Browser
    ↓
DNS Query: dash.pesulabs.net
    ↓
Cloudflare DNS (1.1.1.1)
    ↓
Returns: 181.117.166.31
    ↓
Browser connects to: https://181.117.166.31:443
    ↓
Router (⚠️ needs port forward 443→192.168.8.185:30253)
    ↓
Traefik (reads Host header: dash.pesulabs.net)
    ↓
Routes to: homelab-dashboard:80
    ↓
Dashboard responds
```

---

## Verification Steps (After Port Forwarding)

### 1. Test from External Network (Mobile Data/VPS)

**Cannot test from same network** - NAT loopback may not work. Use mobile data or external VPS.

```bash
# Test HTTP redirect
curl -I http://dash.pesulabs.net
# Expected: HTTP/1.1 308 Permanent Redirect to https://

# Test HTTPS
curl -I https://dash.pesulabs.net
# Expected: HTTP/2 200 or 302 (working service)

# Test certificate
openssl s_client -connect dash.pesulabs.net:443 -servername dash.pesulabs.net < /dev/null 2>&1 | grep -A5 "Certificate chain"
# Expected: Valid Let's Encrypt certificate
```

### 2. Browser Test

Open in browser (from external network):
- https://dash.pesulabs.net - Should load dashboard login
- https://n8n.homelab.pesulabs.net - Should load N8n interface
- https://family-assistant.homelab.pesulabs.net - Should load assistant

### 3. Certificate Verification

Check Traefik logs for certificate issuance:
```bash
kubectl logs -n homelab -l app=traefik --tail=100 | grep -i "certificate\|acme"
# Should see: "Certificates obtained for domains [dash.pesulabs.net]"
```

---

## Security Considerations

### Current Security Posture

✅ **Strong Points**:
- HTTPS with Let's Encrypt certificates
- Auto-renewal configured
- DNS-01 challenge (secure, no HTTP exposure needed)
- Traefik handles TLS termination
- Rate limiting configured in dashboard app
- CSRF protection enabled
- Secure session cookies

⚠️ **Potential Improvements**:
1. **Cloudflare Proxy**: Enable proxied mode for DDoS protection and WAF
2. **Traefik Rate Limiting**: Add middleware for API endpoint protection
3. **Fail2ban**: Implement for brute force protection
4. **2FA**: Add two-factor authentication to critical services
5. **IP Whitelisting**: Restrict admin panels to known IPs

### Access Control

**Public Services** (Internet accessible after port forwarding):
- Dashboard (login required)
- N8n (authentication configured)
- Family Assistant (authentication required)

**Internal Services** (Tailscale/LAN only):
- Ollama API
- Qdrant
- Mem0
- Loki
- Docker Registry
- Prometheus

---

## Troubleshooting

### Issue: Cannot access services from internet

1. **Verify port forwarding is active**:
   - Log into router
   - Check rules are enabled
   - Verify internal IP is correct (192.168.8.185)

2. **Check from external network**:
   - Use mobile data or external VPS
   - Cannot test from same LAN (NAT loopback)

3. **Verify DNS**:
   ```bash
   dig +short dash.pesulabs.net
   # Should return: 181.117.166.31
   ```

4. **Check ISP restrictions**:
   - Some ISPs block ports 80/443 on residential connections
   - Try using alternative ports if blocked

### Issue: Certificates not issuing

1. **Check Traefik logs**:
   ```bash
   kubectl logs -n homelab -l app=traefik --tail=200 | grep -i error
   ```

2. **Verify Cloudflare API token**:
   ```bash
   kubectl get secret -n homelab cloudflare-api-token -o jsonpath='{.data.api-token}' | base64 -d
   # Should match: kpxQeDSVqRzXzpWoHN2Zz6_iX266ljsDFYCd0rYG
   ```

3. **Check DNS records exist**:
   ```bash
   dig +short @1.1.1.1 dash.pesulabs.net
   # Must return public IP
   ```

### Issue: Services timeout or connection refused

1. **Verify Traefik pods running**:
   ```bash
   kubectl get pods -n homelab -l app=traefik
   # Should show 2/2 Running pods
   ```

2. **Test internal access**:
   ```bash
   curl -skI https://100.81.76.55:30253 -H "Host: dash.pesulabs.net"
   # Should get HTTP/2 response
   ```

3. **Check service endpoints**:
   ```bash
   kubectl get svc -n homelab
   kubectl get endpoints -n homelab homelab-dashboard
   ```

---

## Alternative: Tailscale Funnel

If port forwarding doesn't work (ISP restrictions, CGNAT, etc.):

```bash
# On service node (asuna)
ssh pesu@192.168.8.185
tailscale funnel 443
```

This exposes port 443 publicly through Tailscale infrastructure. DNS records would need to point to Tailscale's public endpoint.

---

## Next Steps

### Immediate (Manual Configuration)

1. ⏳ **Configure Router Port Forwarding**
   - Access router admin interface
   - Add rules: 80→192.168.8.185:32060, 443→192.168.8.185:30253
   - Save and verify rules are active

2. ⏳ **Test from External Network**
   - Use mobile data or external VPS
   - Verify HTTPS access works
   - Check certificate validity

### Future Enhancements

- **Monitoring**: Add Prometheus alerting for certificate expiration
- **Backup**: Backup `/acme/acme.json` for disaster recovery
- **Documentation**: Update CLAUDE.md with HTTPS URLs
- **CI/CD**: Integrate HTTPS testing into deployment pipeline
- **Security**: Implement rate limiting middleware in Traefik
- **High Availability**: Deploy additional Traefik replicas

---

## Files Modified

### Infrastructure
- [infrastructure/kubernetes/traefik/traefik-deployment.yaml](../infrastructure/kubernetes/traefik/traefik-deployment.yaml) - DNS-01 challenge, Cloudflare env var
- [infrastructure/kubernetes/traefik/traefik-pvc.yaml](../infrastructure/kubernetes/traefik/traefik-pvc.yaml) - ACME storage (existing)

### Ingress Resources
- [production/monitoring/homelab-dashboard/k8s/ingress.yaml](../production/monitoring/homelab-dashboard/k8s/ingress.yaml) - dash.pesulabs.net
- [infrastructure/kubernetes/ingress-acme-fix.yaml](../infrastructure/kubernetes/ingress-acme-fix.yaml) - n8n ingress
- [services/ingress-fix.yaml](../services/ingress-fix.yaml) - family-assistant, discovery

### Documentation
- [docs/PORT-FORWARDING-SETUP.md](./PORT-FORWARDING-SETUP.md) - Router configuration guide
- [docs/HTTPS-DEPLOYMENT-SUMMARY.md](./HTTPS-DEPLOYMENT-SUMMARY.md) - This document

### Configuration
- Created Kubernetes secret: `cloudflare-api-token` in homelab namespace

---

## Summary

✅ **Completed**:
- Traefik HTTPS ingress fully configured
- DNS-01 challenge with Cloudflare ready
- All 4 service ingresses configured with auto-ACME
- Cloudflare DNS records pointing to public IP
- Internal HTTPS access verified working
- Dashboard already has HTTPS URLs configured
- Comprehensive documentation created

⏳ **Pending**:
- Router port forwarding configuration (manual)
- External HTTPS access verification (after port forwarding)

🎯 **Next Action**: Configure router port forwarding rules (80→32060, 443→30253) to enable public HTTPS access.

---

**Deployment Team**: Claude Code + Homelab Infrastructure
**Contact**: See [docs/SESSION-STATE.md](./SESSION-STATE.md) for current session details
