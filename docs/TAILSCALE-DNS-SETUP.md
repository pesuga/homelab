# 🔧 Tailscale DNS Configuration Guide

**Last Updated**: 2025-01-03
**Status**: ✅ COMPLETE - DNS + Traefik Ingress Fully Working

---

## ✅ What's Been Deployed

CoreDNS custom DNS server is running on your K3s cluster with port forwarding:

**Architecture:**
- **CoreDNS Pod**: Running in `homelab` namespace (NodePort 30053)
- **DNS Forwarder**: systemd service on asuna forwarding port 53 → NodePort 30053
- **Endpoint**: `100.81.76.55:53` (standard DNS port via socat forwarder)
- **Status**: Running and forwarding successfully

**Why Port Forwarding?**
Tailscale split DNS only accepts standard port 53 (no custom ports). We use `socat` to forward DNS queries from port 53 on the Tailscale IP to CoreDNS NodePort 30053.

**Test Confirmation:**
```bash
dig @100.81.76.55 chat.homelab.pesulabs.net +short
# Returns: 100.81.76.55 ✅
```

---

## ✅ Tailscale Split DNS Configured

Tailscale is now configured to forward `*.pesulabs.net` DNS queries to your CoreDNS server.

**Configuration:**
- Nameserver: `100.81.76.55` (standard port 53)
- Search domain: `pesulabs.net`
- Override local DNS: Not required (split DNS works without it)

**How It Was Configured:**

### Via Tailscale Web Console
1. Opened https://login.tailscale.com/admin/dns
2. Added custom nameserver: `100.81.76.55`
3. Restricted to search domain: `pesulabs.net`
4. Saved changes

**Note**: "Override local DNS" is not needed for split DNS to work. Tailscale automatically forwards only `*.pesulabs.net` queries to the custom nameserver.

---

## ✅ Testing Completed - All Services Working

All services have been tested and verified working via DNS + HTTP:

### Service Status

| Service | URL | Status | Test Result |
|---------|-----|--------|-------------|
| **LobeChat** | http://chat.homelab.pesulabs.net/chat | ✅ Working | HTTP 200 OK |
| **N8n** | http://n8n.homelab.pesulabs.net | ✅ Working | HTTP 200 OK |
| **Grafana** | http://grafana.homelab.pesulabs.net | ✅ Working | HTTP 302 (login) |
| **Prometheus** | http://prometheus.homelab.pesulabs.net | ✅ Working | HTTP 302 (redirect) |
| **Flowise** | http://flowise.homelab.pesulabs.net | ✅ Working | HTTP 200 OK |
| **Dashboard** | http://dash.pesulabs.net | ✅ Working | HTTP 302 (login) |

### Testing Commands

```bash
# Test DNS resolution
dig chat.homelab.pesulabs.net +short
# Returns: 100.81.76.55 ✅

# Test HTTP access to all services
curl -I http://chat.homelab.pesulabs.net/chat      # 200 OK ✅
curl -I http://n8n.homelab.pesulabs.net/           # 200 OK ✅
curl -I http://grafana.homelab.pesulabs.net/       # 302 ✅
curl -I http://prometheus.homelab.pesulabs.net/    # 302 ✅
curl -I http://flowise.homelab.pesulabs.net/       # 200 OK ✅
curl -I http://dash.pesulabs.net/                  # 302 ✅
```

### Mobile Testing

Once connected to Tailscale on mobile:
1. Open browser (Safari/Chrome)
2. Navigate to: `http://chat.homelab.pesulabs.net/chat`
3. Should load LobeChat interface immediately

**Important**: Use the full hostname including "homelab" subdomain (e.g., `chat.homelab.pesulabs.net`, not `chat.pesulabs.net`)

---

## 📋 Complete DNS Resolution Flow

```
Tailscale Device (laptop/mobile/compute node)
           ↓
    Query: chat.homelab.pesulabs.net?
           ↓
    Tailscale MagicDNS checks: Is this .pesulabs.net?
           ↓ YES
    Forward to: 100.81.76.55:53 (DNS forwarder)
           ↓
    socat DNS Forwarder (systemd service on asuna)
           ↓
    Forwards to: 127.0.0.1:30053 (CoreDNS NodePort)
           ↓
    CoreDNS template matches: .*pesulabs\.net\.$
           ↓
    Returns: 100.81.76.55
           ↓
    Device makes HTTP request to: http://100.81.76.55:80
           ↓
    Traefik Ingress Controller (routes by Host header)
           ↓
    Matches: chat.homelab.pesulabs.net → LobeChat service
           ↓
    Service responds: HTTP 200 OK ✅
```

---

## 🌐 Available Services via DNS

Once Tailscale is configured, these URLs will work from ANY Tailscale device:

| Service | URL | Description |
|---------|-----|-------------|
| **LobeChat** | http://chat.homelab.pesulabs.net/chat | AI chat with voice input |
| **N8n** | http://n8n.homelab.pesulabs.net | Workflow automation |
| **Grafana** | http://grafana.homelab.pesulabs.net | Monitoring dashboards |
| **Prometheus** | http://prometheus.homelab.pesulabs.net | Metrics database |
| **Flowise** | http://flowise.homelab.pesulabs.net | LLM flow builder |
| **Dashboard** | http://dash.pesulabs.net | Homelab dashboard |
| **Whisper** | http://whisper.pesulabs.net (not configured yet) | Speech-to-text API |

**Note**: The actual Ingress hostnames vary, but all `*.pesulabs.net` will resolve to `100.81.76.55`.

---

## 🔧 Troubleshooting

### DNS Not Resolving

**Check Tailscale DNS Settings:**
```bash
# View current Tailscale status
tailscale status

# Check if MagicDNS is enabled
# Visit: https://login.tailscale.com/admin/dns
# Verify "MagicDNS" is enabled
```

**Test CoreDNS Directly:**
```bash
# Test on standard port 53 (via socat forwarder)
dig @100.81.76.55 test.pesulabs.net +short
# Should return: 100.81.76.55

# Or test NodePort directly (bypass forwarder)
dig @100.81.76.55 -p 30053 test.pesulabs.net +short
# Should also return: 100.81.76.55
```

**Check CoreDNS Logs:**
```bash
kubectl logs -n homelab -l app=coredns-custom --tail=50
```

**Check DNS Forwarder Status:**
```bash
# SSH to service node
ssh pesu@192.168.8.185

# Check forwarder service
sudo systemctl status dns-forwarder

# View forwarder logs
sudo journalctl -u dns-forwarder -f

# Restart if needed
sudo systemctl restart dns-forwarder
```

### DNS Resolves But Can't Connect

**Check Tailscale Connection:**
```bash
tailscale ping 100.81.76.55
# Should successfully ping service node
```

**Check Ingress Status:**
```bash
kubectl get ingress -n homelab
# Verify ingress resources exist
```

**Test Direct NodePort:**
```bash
# Bypass DNS and ingress, test service directly
curl -I http://100.81.76.55:30910/chat
# LobeChat should respond
```

### Mobile Not Working

1. Ensure Tailscale VPN is connected on mobile
2. Check Tailscale app shows "Connected"
3. Verify mobile device appears in: https://login.tailscale.com/admin/machines
4. Try pinging service node from mobile Tailscale app

---

## 📱 Mobile-Specific Notes

### iOS/Android Tailscale App

**DNS Settings:**
- MagicDNS must be enabled globally (not per-device)
- "Override local DNS" may be needed for split DNS to work
- Some mobile carriers block custom DNS - connect via WiFi for testing

**Testing on Mobile:**
1. Connect to Tailscale
2. Open Safari/Chrome
3. Navigate to `http://chat.homelab.pesulabs.net/chat`
4. Should load (may take a few seconds first time)

---

## ✅ Setup Complete

DNS and Traefik Ingress are fully configured and working. All services are accessible via friendly DNS names.

### What's Working
- ✅ CoreDNS resolving all `*.pesulabs.net` domains to `100.81.76.55`
- ✅ socat DNS forwarder providing standard port 53 for Tailscale
- ✅ Tailscale split DNS forwarding queries to CoreDNS
- ✅ Traefik Ingress routing HTTP requests to correct services
- ✅ All 6 services (LobeChat, N8n, Grafana, Prometheus, Flowise, Dashboard) accessible via HTTP

### Optional Future Enhancements
1. **SSL/TLS**: Configure Let's Encrypt with Traefik for HTTPS (optional)
2. **Additional Services**: Any new Ingress automatically gets DNS resolution
3. **Certificate Management**: Use cert-manager for automated TLS certificates
4. **Monitoring**: Add DNS query monitoring to Grafana dashboards

---

## 📚 Reference

**Tailscale Documentation:**
- [MagicDNS Overview](https://tailscale.com/kb/1081/magicdns)
- [Split DNS Configuration](https://tailscale.com/kb/1054/dns)

**CoreDNS Documentation:**
- [Template Plugin](https://coredns.io/plugins/template/)
- [CoreDNS Manual](https://coredns.io/manual/toc/)

**Service Manifests:**
- CoreDNS: `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/dns/coredns-custom.yaml`
- Solution Design: `/home/pesu/Rakuflow/systems/homelab/docs/DNS-SOLUTION-DESIGN.md`

---

**Status**: ✅ COMPLETE - All services accessible via DNS + HTTP
**Deployment Date**: 2025-01-03
