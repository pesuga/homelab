# DNS Records Configuration for Homelab Services

**Status**: Required for external DNS access via Cloudflare
**Last Updated**: 2025-11-07
**Environment**: pesulabs.net domain via Cloudflare

---

## Overview

This document outlines the DNS A records that need to be added to your Cloudflare DNS provider to enable external access to homelab services.

**Service Node IP**: `100.81.76.55` (Tailscale IP for asuna)

---

## Required DNS A Records

Add these A records to your Cloudflare DNS panel:

| Hostname | Type | IP Address | TTL | Purpose |
|----------|------|------------|-----|---------|
| `ollama.homelab.pesulabs.net` | A | `100.81.76.55` | 300s (testing) / 3600s (prod) | LLM API via Traefik HTTPS ingress |
| `lobechat.homelab.pesulabs.net` | A | `100.81.76.55` | 300s (testing) / 3600s (prod) | AI Chat Interface |
| ~~`flowise.homelab.pesulabs.net`~~ | ~~A~~ | ~~`100.81.76.55`~~ | ~~300s~~ | **DEPRECATED**: Service being removed |

---

## Step-by-Step Cloudflare Setup

### 1. Access Cloudflare DNS Panel

1. Go to: https://dash.cloudflare.com
2. Sign in with your account
3. Select your domain: **pesulabs.net**
4. Navigate to: **DNS** → **Records** tab

### 2. Add Ollama DNS Record

1. Click **"+ Add record"**
2. Configure:
   - **Type**: A
   - **Name**: `ollama.homelab` (Cloudflare auto-appends domain)
   - **IPv4 address**: `100.81.76.55`
   - **TTL**: 300 (for testing/development) or 3600 (for production)
   - **Proxy status**: ⚠️ **DNS only** (do NOT proxy through Cloudflare)
   - Click **"Save"**

### 3. Add LobeChat DNS Record

1. Click **"+ Add record"**
2. Configure:
   - **Type**: A
   - **Name**: `lobechat.homelab` (Cloudflare auto-appends domain)
   - **IPv4 address**: `100.81.76.55`
   - **TTL**: 300 (for testing/development) or 3600 (for production)
   - **Proxy status**: ⚠️ **DNS only** (do NOT proxy through Cloudflare)
   - Click **"Save"**

### 4. (OPTIONAL) Remove Flowise Record

If you previously had a Flowise record:

1. Find: `flowise.homelab.pesulabs.net` in your DNS records
2. Click the **trash icon** to delete it
3. Confirm deletion

---

## Verification & Testing

### Immediate DNS Verification

**From your local machine:**

```bash
# Test DNS resolution (may require 1-5 minutes to propagate)
dig +short ollama.homelab.pesulabs.net
dig +short lobechat.homelab.pesulabs.net

# Alternative using nslookup
nslookup ollama.homelab.pesulabs.net
nslookup lobechat.homelab.pesulabs.net

# Using host command
host ollama.homelab.pesulabs.net
host lobechat.homelab.pesulabs.net
```

**Expected Output**:
```
100.81.76.55
```

### HTTPS Connectivity Test

```bash
# Test Ollama HTTPS endpoint
curl -I https://ollama.homelab.pesulabs.net
# Expected: HTTP/2 200 (with valid Let's Encrypt certificate)

# Test LobeChat HTTPS endpoint
curl -I https://lobechat.homelab.pesulabs.net
# Expected: HTTP/2 200 (with redirect or proper response)

# Test with certificate validation
curl -v https://ollama.homelab.pesulabs.net

# Test actual API response
curl https://ollama.homelab.pesulabs.net/api/version
```

### Certificate Verification

```bash
# Check Ollama certificate expiry
echo | openssl s_client -servername ollama.homelab.pesulabs.net \
  -connect ollama.homelab.pesulabs.net:443 2>/dev/null | \
  openssl x509 -noout -dates

# Check LobeChat certificate expiry
echo | openssl s_client -servername lobechat.homelab.pesulabs.net \
  -connect lobechat.homelab.pesulabs.net:443 2>/dev/null | \
  openssl x509 -noout -dates
```

---

## TTL (Time To Live) Recommendations

### For Development/Testing
- **TTL: 300 seconds (5 minutes)**
- Allows quick DNS propagation for testing
- Use when troubleshooting DNS or IP changes
- Higher API rate limit from Cloudflare

### For Production
- **TTL: 3600 seconds (1 hour)**
- Reduces DNS lookup overhead
- Better for stable, unchanging configurations
- Standard production practice

### Quick Change Strategy
1. Set TTL to 300 before making any IP changes
2. Wait 5 minutes for full propagation
3. Make the IP change
4. Test the change
5. Set TTL back to 3600 after verification

---

## DNS Propagation Timeline

| Time | Status | Notes |
|------|--------|-------|
| 0-1 min | Pending | Cloudflare processing |
| 1-5 min | Partial | Some resolvers updated |
| 5-15 min | Full (TTL=300) | Most resolvers updated |
| 15-60 min | Full (TTL=3600) | All resolvers updated |
| 60+ min | Complete | All caches cleared |

**Tip**: Use `dig +trace` to check DNS propagation across multiple nameservers:
```bash
dig +trace ollama.homelab.pesulabs.net
```

---

## Troubleshooting DNS Issues

### DNS Not Resolving

```bash
# Check if Cloudflare has the record
nslookup ollama.homelab.pesulabs.net 1.1.1.1
# Should return 100.81.76.55

# Check Google DNS
nslookup ollama.homelab.pesulabs.net 8.8.8.8
# Should return 100.81.76.55

# Check Quad9 DNS
nslookup ollama.homelab.pesulabs.net 9.9.9.9
# Should return 100.81.76.55
```

### HTTPS Certificate Not Valid

```bash
# Check if Traefik has issued a certificate
kubectl get certificate -n homelab
kubectl describe certificate ollama -n homelab

# Check Traefik logs for ACME errors
kubectl logs -n kube-system -l app=traefik -f | grep -i "ollama\|acme\|error"

# Verify Let's Encrypt can reach your domain
curl -I https://ollama.homelab.pesulabs.net
# Certificate should be valid (not self-signed)
```

### Service Not Responding

```bash
# Check if Ollama service is running
kubectl get pod -n homelab -l app=ollama
# Should show pod in Running state

# Check service status
kubectl get svc -n homelab ollama
# Should show external IP or NodePort

# Test direct service access
curl -I https://ollama.homelab.pesulabs.net

# View service logs
kubectl logs -n homelab -l app=ollama -f
```

---

## Current DNS Configuration Summary

### Existing Records (No Changes Needed)

These are already configured and working:

```
n8n.homelab.pesulabs.net          → 100.81.76.55  ✅
grafana.homelab.pesulabs.net      → 100.81.76.55  ✅
prometheus.homelab.pesulabs.net   → 100.81.76.55  ✅
webui.homelab.pesulabs.net        → 100.81.76.55  ✅
```

### New Records (Add via Cloudflare)

```
ollama.homelab.pesulabs.net       → 100.81.76.55  ⏳
lobechat.homelab.pesulabs.net     → 100.81.76.55  ⏳
```

### Records to Remove

```
flowise.homelab.pesulabs.net      (DELETE)         ❌
```

---

## Integration with Ingress Controller

Your Traefik ingress controller automatically:

1. **Detects new DNS records** once they resolve
2. **Requests HTTPS certificates** from Let's Encrypt
3. **Routes HTTPS traffic** to the appropriate Kubernetes service
4. **Renews certificates** automatically before expiry

**No additional configuration needed** - just add the DNS records and wait for propagation.

---

## Testing via Tailscale (Optional)

If external DNS isn't working yet, test via Tailscale network:

```bash
# Test on Tailscale devices (100.81.76.55 is directly accessible)
curl -I https://100.81.76.55

# Test with specific host headers
curl -I https://100.81.76.55 -H "Host: ollama.homelab.pesulabs.net"
curl -I https://100.81.76.55 -H "Host: lobechat.homelab.pesulabs.net"
```

---

## Quick Reference Commands

```bash
# Add these aliases to your shell for easy testing
alias test-ollama='curl -I https://ollama.homelab.pesulabs.net'
alias test-lobechat='curl -I https://lobechat.homelab.pesulabs.net'
alias test-dns='dig +short ollama.homelab.pesulabs.net && dig +short lobechat.homelab.pesulabs.net'

# Run all DNS tests
test-dns
test-ollama
test-lobechat
```

---

## Important Notes

### Why "DNS Only" Mode?

When adding records to Cloudflare, set to **"DNS only"** (gray cloud icon):
- Let Traefik handle HTTPS termination
- Cloudflare doesn't proxy the traffic
- Certificates work correctly with Let's Encrypt
- Better performance for internal services

### Tailscale IP Stability

The IP `100.81.76.55` is:
- **Assigned by Tailscale** to your service node
- **Stable and persistent** (won't change unless you change nodes)
- **Accessible from anywhere** on your Tailscale network
- **Safe to publish** in DNS records

---

## Next Steps

1. ✅ Add two A records to Cloudflare (ollama, lobechat)
2. ✅ Wait 5-15 minutes for DNS propagation
3. ✅ Test DNS resolution with `dig` or `nslookup`
4. ✅ Test HTTPS connectivity with `curl`
5. ✅ Update test-all-services.sh to verify everything works
6. 📝 Update this document if service IPs change

---

## Related Documentation

- **Service Endpoints**: `/docs/SERVICE-ENDPOINTS.md`
- **HTTPS/TLS Setup**: `/docs/HTTPS-DOMAIN-STRATEGY.md`
- **Traefik Configuration**: `/infrastructure/kubernetes/traefik/`
- **DNS Setup Guide**: `/docs/DNS-SETUP-GUIDE.md`

---

**Questions?** Check the Cloudflare DNS docs: https://developers.cloudflare.com/dns/
