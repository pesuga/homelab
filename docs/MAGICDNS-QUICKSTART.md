# 🪄 MagicDNS Quick Start Guide

**Last Updated**: 2025-10-23
**Time to Complete**: 5 minutes
**Difficulty**: Easy ⭐

---

## What is MagicDNS?

MagicDNS is Tailscale's built-in DNS service that automatically works on all devices in your Tailnet. No client configuration needed!

**Benefits**:
- ✅ Zero per-device configuration
- ✅ Centrally managed DNS records
- ✅ Automatic for all Tailscale devices
- ✅ Works on mobile, desktop, servers
- ✅ Updates propagate instantly

---

## Step-by-Step Setup

### Step 1: Enable MagicDNS (2 minutes)

1. Go to Tailscale Admin Console: https://login.tailscale.com/admin/dns
2. Find the "MagicDNS" section
3. Toggle **MagicDNS** to ON
4. Click "Save"

That's it! MagicDNS is now enabled for your entire Tailnet.

### Step 2: Add DNS Records (3 minutes)

There are two options:

#### Option A: Global Nameservers (Recommended - Simpler)

1. Still on the DNS page (https://login.tailscale.com/admin/dns)
2. Scroll to **"Global nameservers"** section
3. Click "Add nameserver"
4. Add each record:
   ```
   grafana.homelab.local     → 100.81.76.55
   prometheus.homelab.local  → 100.81.76.55
   n8n.homelab.local        → 100.81.76.55
   webui.homelab.local      → 100.81.76.55
   ```
5. Click "Save"

#### Option B: Split DNS (Advanced - For Custom DNS Server)

If you want to run your own DNS server (CoreDNS/DNSMasq):

1. Deploy a DNS server on your service node (see DNS-SETUP-GUIDE.md)
2. In the "Nameservers" section, click "Add nameserver"
3. Enter: `100.81.76.55`
4. In "Restrict to domain", enter: `homelab.local`
5. Click "Save"

**Note**: Option A is recommended for most users. Option B is only needed if you want to run your own DNS server for advanced features.

---

## Step 3: Test It! (1 minute)

From **ANY** device on your Tailnet:

```bash
# Test DNS resolution
nslookup grafana.homelab.local
# Expected output:
# Server:  100.100.100.100
# Address: 100.100.100.100#53
#
# Name:    grafana.homelab.local
# Address: 100.81.76.55

# Test HTTPS access
curl -I https://grafana.homelab.local
# Expected: HTTP/2 200 or 302 (redirect)

# Open in browser
# Just navigate to: https://grafana.homelab.local
```

---

## Troubleshooting

### DNS not resolving?

1. **Check MagicDNS is enabled**:
   - Go to https://login.tailscale.com/admin/dns
   - Verify MagicDNS toggle is ON

2. **Check DNS records are configured**:
   - Scroll to "Global nameservers" section
   - Verify your homelab.local entries are present

3. **Restart Tailscale on your device**:
   ```bash
   # Linux/macOS
   sudo tailscale down && sudo tailscale up

   # Windows (PowerShell as Admin)
   Restart-Service Tailscale
   ```

4. **Check Tailscale status**:
   ```bash
   tailscale status
   # Verify your device shows as connected
   ```

### Browser shows "Not Secure"?

This is expected - you need to install the Root CA certificate on your device.

**Solution**: See `/docs/HTTPS-QUICK-REFERENCE.md` section "Browser Setup"

Quick fix:
```bash
# Copy Root CA from compute node
scp pesu@100.72.98.106:~/Rakuflow/systems/homelab/infrastructure/certificates/ca/ca-cert.pem ~/

# Linux
sudo cp ca-cert.pem /usr/local/share/ca-certificates/homelab-ca.crt
sudo update-ca-certificates

# macOS
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain ca-cert.pem

# Windows (PowerShell as Admin)
certutil -addstore -f "ROOT" ca-cert.pem
```

### Connection refused?

1. **Check Tailscale is connected**:
   ```bash
   tailscale status
   # Verify service node (asuna) shows as online
   ```

2. **Check services are running**:
   ```bash
   # SSH to service node
   ssh pesu@192.168.8.185

   # Check K3s services
   kubectl get pods -n homelab
   # All pods should show Running

   # Check Traefik (ingress controller)
   kubectl get pods -n kube-system | grep traefik
   # Should show traefik pod running
   ```

---

## What DNS Records Were Added?

| Domain | IP Address | Purpose |
|--------|------------|---------|
| grafana.homelab.local | 100.81.76.55 | Grafana monitoring dashboard |
| prometheus.homelab.local | 100.81.76.55 | Prometheus metrics API |
| n8n.homelab.local | 100.81.76.55 | N8n workflow automation |
| webui.homelab.local | 100.81.76.55 | Open WebUI (LLM chat) |

**All point to**: Service node Tailscale IP (100.81.76.55)

---

## Adding More Services

When you deploy a new service with an Ingress:

1. Go to https://login.tailscale.com/admin/dns
2. Scroll to "Global nameservers"
3. Add: `newservice.homelab.local → 100.81.76.55`
4. Create Ingress resource in K3s (see `infrastructure/kubernetes/ingress/`)
5. Test from any Tailscale device!

---

## Benefits of This Setup

### For Users
- ✅ **Memorable URLs**: No more IP:port combinations
- ✅ **Works everywhere**: Home network, mobile, remote
- ✅ **No manual config**: Install Tailscale once, done
- ✅ **HTTPS everywhere**: Secure encrypted connections

### For Admins
- ✅ **Single source of truth**: Tailscale admin console
- ✅ **Instant updates**: Changes propagate immediately
- ✅ **No client updates needed**: Add services without touching devices
- ✅ **Monitoring ready**: All traffic goes through Tailscale metrics

### Technical
- ✅ **Encrypted**: All traffic over WireGuard VPN
- ✅ **NAT traversal**: Works behind routers/firewalls
- ✅ **Low latency**: Direct peer-to-peer connections
- ✅ **High availability**: Automatic failover

---

## Your Devices

Based on your Tailscale network, these devices will automatically get DNS:

| Device | Platform | Status | Notes |
|--------|----------|--------|-------|
| **asuna** | Ubuntu Server | ✅ Service Node | Hosts all services |
| **pesubuntu** | Ubuntu Desktop | ✅ Compute Node | LLM inference |
| **pesu-mobile** | Android | ⏳ Needs CA cert | Install Root CA for HTTPS |
| **pesu-stensul** | macOS | ⏳ Needs CA cert | Install Root CA for HTTPS |
| **pesutop** | Windows | ⏳ Needs CA cert | Install Root CA for HTTPS |

---

## Next Steps

1. **Enable MagicDNS** (if not done already)
2. **Add DNS records** to Tailscale admin console
3. **Test access** from your devices
4. **Install Root CA** on devices that need HTTPS
5. **Access your services**:
   - Grafana: https://grafana.homelab.local
   - N8n: https://n8n.homelab.local
   - Open WebUI: https://webui.homelab.local
   - Prometheus: https://prometheus.homelab.local

---

## Documentation Links

- **Full DNS Setup Guide**: `/docs/DNS-SETUP-GUIDE.md`
- **HTTPS Setup**: `/docs/HTTPS-QUICK-REFERENCE.md`
- **Deployment Summary**: `/docs/DEPLOYMENT-SUMMARY.md`
- **Tailscale MagicDNS Docs**: https://tailscale.com/kb/1081/magicdns/

---

**Status**: ✅ MagicDNS is the recommended DNS solution
**Complexity**: Low (5-minute setup)
**Maintenance**: None (fully managed)
