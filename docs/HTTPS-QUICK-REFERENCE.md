# 🔒 HTTPS Access - Quick Reference

**Last Updated**: 2025-10-22
**Status**: ✅ Fully Operational

---

## 🌐 Access URLs (HTTPS with Tailscale)

All services are now accessible via HTTPS with friendly domain names:

| Service | HTTPS URL | Credentials | Purpose |
|---------|-----------|-------------|---------|
| **Grafana** | https://grafana.homelab.local | admin / admin123 | Monitoring dashboards |
| **Prometheus** | https://prometheus.homelab.local | N/A | Metrics API |
| **N8n** | https://n8n.homelab.local | admin / admin123 | Workflow automation |
| **Open WebUI** | https://webui.homelab.local | Self-signup | LLM chat interface |

---

## 🔐 Certificate Information

**Type**: Self-signed CA with wildcard certificate
**Domain**: `*.homelab.local`
**Valid Until**: January 26, 2028
**Algorithm**: RSA 4096-bit

**Certificate Files**:
- Root CA: `/home/pesu/Rakuflow/systems/homelab/infrastructure/certificates/ca/ca-cert.pem`
- Wildcard Cert: `/home/pesu/Rakuflow/systems/homelab/infrastructure/certificates/ca/homelab-cert.pem`

---

## ✅ What's Deployed

### Ingress Controller
- **Traefik**: Built-in with K3s, running in `kube-system` namespace
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Load Balancer IP**: 192.168.86.169 (exposed via Tailscale: 100.81.76.55)

### TLS Configuration
- **Kubernetes Secret**: `homelab-tls` in `homelab` namespace
- **Covers**: `*.homelab.local`, `*.asuna.homelab.local`, `*.pesubuntu.homelab.local`

### DNS Resolution
- **Method**: `/etc/hosts` entries
- **Configured on**: Both compute and service nodes
- **IP**: 100.81.76.55 (Tailscale IP of service node)

---

## 📱 Browser Setup

### Install Root CA (One-time setup)

The Root CA certificate needs to be installed on any device accessing the services to avoid browser warnings.

**Already installed on**:
- ✅ Compute node (pesubuntu)
- ✅ Service node (asuna)

**To install on other devices**:

1. **Copy Root CA** from compute node:
   ```bash
   scp pesu@100.72.98.106:~/Rakuflow/systems/homelab/infrastructure/certificates/ca/ca-cert.pem ~/
   ```

2. **Linux (Ubuntu/Debian)**:
   ```bash
   sudo cp ca-cert.pem /usr/local/share/ca-certificates/homelab-ca.crt
   sudo update-ca-certificates
   ```

3. **macOS**:
   ```bash
   sudo security add-trusted-cert -d -r trustRoot \
     -k /Library/Keychains/System.keychain ca-cert.pem
   ```

4. **Windows** (PowerShell as Admin):
   ```powershell
   certutil -addstore -f "ROOT" ca-cert.pem
   ```

5. **Firefox** (all platforms):
   - Settings → Privacy & Security → Certificates → View Certificates
   - Authorities tab → Import
   - Select `ca-cert.pem`
   - Check "Trust this CA to identify websites"

6. **Add to /etc/hosts**:
   ```bash
   echo "100.81.76.55  grafana.homelab.local prometheus.homelab.local n8n.homelab.local webui.homelab.local" | sudo tee -a /etc/hosts
   ```

---

## 🔄 Migration Summary

### Before (HTTP + NodePort)
```
http://192.168.8.185:30300  → Grafana
http://192.168.8.185:30090  → Prometheus
http://192.168.8.185:30678  → N8n
http://192.168.8.185:30080  → Open WebUI
```

### Now (HTTPS + Domain)
```
https://grafana.homelab.local     → Grafana ✅
https://prometheus.homelab.local  → Prometheus ✅
https://n8n.homelab.local        → N8n ✅
https://webui.homelab.local      → Open WebUI ✅
```

**Note**: Old HTTP URLs still work as backup access!

---

## 🛠️ Technical Details

### Ingress Resources

All Ingress resources are in: `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/ingress/all-services-ingress.yaml`

**Features**:
- TLS termination at Traefik
- HTTP/2 support
- Automatic HTTP → HTTPS redirect (Traefik default)
- Wildcard certificate reuse

### Routing

```
Browser (HTTPS)
    ↓
https://grafana.homelab.local
    ↓
DNS Resolution (/etc/hosts)
    ↓
100.81.76.55:443 (Tailscale IP)
    ↓
Traefik Ingress (K3s)
    ↓
TLS Termination (homelab-tls secret)
    ↓
Route to Service (grafana:3000)
    ↓
Pod (Grafana)
```

---

## 🎯 Common Tasks

### Test HTTPS Access
```bash
# From compute node or service node
curl -I https://grafana.homelab.local
curl -I https://prometheus.homelab.local
curl -I https://n8n.homelab.local
curl -I https://webui.homelab.local
```

### View Ingress Resources
```bash
ssh pesu@192.168.8.185 "kubectl get ingress -n homelab"
```

### Check TLS Secret
```bash
ssh pesu@192.168.8.185 "kubectl get secret homelab-tls -n homelab -o yaml"
```

### Verify Traefik
```bash
ssh pesu@192.168.8.185 "kubectl get pods -n kube-system | grep traefik"
```

### View Certificate Details
```bash
openssl x509 -in infrastructure/certificates/ca/homelab-cert.pem -text -noout
```

---

## 🔍 Troubleshooting

### Browser Shows "Not Secure" Warning

**Solution**: Install the Root CA certificate on your device (see Browser Setup above)

### Domain Not Resolving

**Check /etc/hosts**:
```bash
cat /etc/hosts | grep homelab
# Should show: 100.81.76.55  grafana.homelab.local ...
```

**Add if missing**:
```bash
echo "100.81.76.55  grafana.homelab.local prometheus.homelab.local n8n.homelab.local webui.homelab.local" | sudo tee -a /etc/hosts
```

### Connection Refused

**Check Traefik is running**:
```bash
ssh pesu@192.168.8.185 "kubectl get pods -n kube-system | grep traefik"
```

**Check Ingress resources**:
```bash
ssh pesu@192.168.8.185 "kubectl get ingress -n homelab"
```

### Certificate Expired

**Check expiry date**:
```bash
openssl x509 -in infrastructure/certificates/ca/homelab-cert.pem -noout -enddate
# Valid until: Jan 26 11:24:15 2028 GMT
```

**Regenerate if needed**:
```bash
./infrastructure/certificates/generate-certs.sh
# Then update Kubernetes secret
```

---

## 📊 What This Gives You

### Security Benefits
- ✅ **Encrypted traffic**: All communication is TLS-encrypted
- ✅ **Certificate validation**: Browser verifies server identity
- ✅ **Modern protocols**: HTTP/2 support for better performance
- ✅ **No plain-text credentials**: Passwords encrypted in transit

### Usability Benefits
- ✅ **Memorable URLs**: No need to remember IPs and ports
- ✅ **Professional setup**: Production-like infrastructure
- ✅ **Browser bookmarks**: Easy to bookmark and share
- ✅ **Tailscale integration**: Works from anywhere on VPN

### Operational Benefits
- ✅ **Centralized routing**: Single entry point (Traefik)
- ✅ **Easy to add services**: Just create Ingress resource
- ✅ **Backup access**: Old NodePort URLs still work
- ✅ **Monitoring ready**: Traefik metrics available

---

## 🚀 Next Steps

Now that HTTPS is working, you can:

1. **Access Grafana**: https://grafana.homelab.local
   - Import the dashboard we created earlier
   - Start monitoring your GPU metrics

2. **Use Open WebUI**: https://webui.homelab.local
   - Create an account
   - Chat with llama3.1:8b model

3. **Create N8n Workflows**: https://n8n.homelab.local
   - Build your first workflow with LLM integration
   - Connect to Ollama/LiteLLM APIs

4. **Optional Improvements**:
   - Deploy a local DNS server (Pihole/AdGuard)
   - Upgrade to Let's Encrypt (if you have a domain)
   - Add authentication layer (Authelia/Keycloak)
   - Set up HTTP → HTTPS redirects

---

## 📚 Related Documentation

- **Full Strategy**: `/docs/HTTPS-DOMAIN-STRATEGY.md`
- **Architecture**: `/docs/architecture.md`
- **Deployment Summary**: `/docs/DEPLOYMENT-SUMMARY.md`
- **Grafana Setup**: `/docs/GRAFANA-SETUP.md`

---

**Status**: ✅ All services accessible via HTTPS
**Certificate**: Valid until 2028-01-26
**Services**: 4 (Grafana, Prometheus, N8n, Open WebUI)
