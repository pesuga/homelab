# DNS + Traefik Ingress Setup - Completion Summary

**Date**: 2025-01-03
**Status**: ✅ COMPLETE

## What Was Accomplished

Successfully deployed and configured a complete DNS + Ingress solution for the homelab, enabling all services to be accessible via friendly DNS names from any Tailscale-connected device.

## Architecture Deployed

### DNS Layer
- **CoreDNS**: Custom DNS server running in K3s cluster (NodePort 30053)
- **socat Forwarder**: systemd service forwarding port 53 → 30053 on asuna node
- **Tailscale Split DNS**: Configured to forward `*.pesulabs.net` queries to `100.81.76.55:53`

### Ingress Layer
- **Traefik**: Kubernetes Ingress controller routing HTTP traffic
- **6 Ingress Resources**: All configured to accept both HTTP and HTTPS
- **Host-Based Routing**: Routes traffic based on DNS hostname to correct service

## Complete Request Flow

```
Tailscale Device → DNS Query (chat.homelab.pesulabs.net)
    ↓
Tailscale MagicDNS → Forwards to 100.81.76.55:53
    ↓
socat Forwarder → Forwards to 127.0.0.1:30053
    ↓
CoreDNS → Returns 100.81.76.55
    ↓
HTTP Request → 100.81.76.55:80
    ↓
Traefik Ingress → Routes to LobeChat pod
    ↓
Success ✅
```

## Services Working

| Service | DNS URL | Status |
|---------|---------|--------|
| LobeChat | http://chat.homelab.pesulabs.net/chat | ✅ HTTP 200 |
| N8n | http://n8n.homelab.pesulabs.net | ✅ HTTP 200 |
| Grafana | http://grafana.homelab.pesulabs.net | ✅ HTTP 302 |
| Prometheus | http://prometheus.homelab.pesulabs.net | ✅ HTTP 302 |
| Flowise | http://flowise.homelab.pesulabs.net | ✅ HTTP 200 |
| Dashboard | http://dash.pesulabs.net | ✅ HTTP 302 |

## Key Technical Decisions

### 1. Port 53 Forwarding
**Challenge**: Tailscale split DNS only accepts standard port 53, but CoreDNS was on NodePort 30053.

**Solution**:
- Deployed socat as systemd service on asuna node
- Forwards UDP/TCP port 53 → 30053
- Binds only to Tailscale IP (100.81.76.55) to avoid systemd-resolved conflict

**Why Not HostPort**: Service node (asuna) had insufficient CPU for pod with `hostNetwork: true` and node selector.

### 2. HTTP-Only Access
**Challenge**: Ingress resources had HTTPS-only annotations causing 404 errors.

**Solution**:
- Changed `router.entrypoints` from `"websecure"` to `"web,websecure"`
- Removed `router.tls` annotation
- Allows both HTTP and HTTPS (HTTPS setup is optional future enhancement)

### 3. DNS Template Matching
**Challenge**: Need all `*.pesulabs.net` to resolve to service node.

**Solution**:
- CoreDNS template plugin with regex: `.*pesulabs\.net\.$`
- Returns `100.81.76.55` for any matching query
- 60-second TTL for reasonable caching

## Files Created/Modified

### Created
1. `/etc/systemd/system/dns-forwarder.service` (on asuna node)
   - socat port forwarder service

### Modified
1. `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/dns/coredns-custom.yaml`
   - Final CoreDNS configuration (NodePort, no hostNetwork)

2. Ingress Resources (6 files):
   - `n8n-pesulabs`
   - `grafana-pesulabs`
   - `prometheus-pesulabs`
   - `homelab-dashboard`
   - `flowise-pesulabs`
   - `webui-pesulabs`
   - Changed annotations to accept HTTP + HTTPS

3. `/home/pesu/Rakuflow/systems/homelab/docs/TAILSCALE-DNS-SETUP.md`
   - Updated with complete working configuration and test results

4. `/home/pesu/Rakuflow/systems/homelab/docs/SERVICE-ENDPOINTS.md`
   - Added DNS URLs as recommended access method

## Testing Performed

### DNS Resolution
```bash
dig @100.81.76.55 chat.homelab.pesulabs.net +short
# Returns: 100.81.76.55 ✅
```

### HTTP Connectivity
All services tested and confirmed working:
```bash
curl -I http://chat.homelab.pesulabs.net/chat      # 200 OK ✅
curl -I http://n8n.homelab.pesulabs.net/           # 200 OK ✅
curl -I http://grafana.homelab.pesulabs.net/       # 302 ✅
curl -I http://prometheus.homelab.pesulabs.net/    # 302 ✅
curl -I http://flowise.homelab.pesulabs.net/       # 200 OK ✅
curl -I http://dash.pesulabs.net/                  # 302 ✅
```

## Important Notes

### Hostname Convention
- Most services use format: `SERVICE.homelab.pesulabs.net`
- Dashboard uses shorter format: `dash.pesulabs.net`
- Always include the subdomain in URLs (e.g., `chat.homelab.pesulabs.net`, not `chat.pesulabs.net`)

### Override Local DNS
- **Not required** for Tailscale split DNS to work
- Tailscale automatically forwards only `*.pesulabs.net` queries
- Other DNS queries use default DNS servers

### Service Discovery
Adding new services is automatic:
1. Create Kubernetes Ingress with desired hostname
2. CoreDNS automatically resolves `*.pesulabs.net` to `100.81.76.55`
3. Traefik routes based on Host header
4. No additional DNS configuration needed

## Troubleshooting Guide

### DNS Not Resolving
```bash
# Check DNS forwarder
ssh pesu@192.168.8.185
sudo systemctl status dns-forwarder

# Check CoreDNS
kubectl logs -n homelab -l app=coredns-custom --tail=50

# Test direct
dig @100.81.76.55 test.pesulabs.net +short  # Should return 100.81.76.55
```

### HTTP 404 Errors
```bash
# Check Ingress configuration
kubectl get ingress -n homelab SERVICE-NAME -o yaml

# Verify entrypoints annotation
# Should be: traefik.ingress.kubernetes.io/router.entrypoints: "web,websecure"

# Check Traefik logs
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik -f
```

## Future Enhancements

1. **TLS/HTTPS** (Optional)
   - Configure Let's Encrypt with Traefik
   - Deploy cert-manager for automated certificate management
   - Add TLS configuration to Ingress resources

2. **Monitoring**
   - Add DNS query metrics to Prometheus
   - Create Grafana dashboard for DNS/Ingress monitoring
   - Alert on DNS forwarder failures

3. **Additional Domains**
   - Configure additional subdomains as needed
   - Consider separate domains for different service types
   - Implement external DNS for public access (if desired)

## Success Metrics

- ✅ All 6 services accessible via DNS names
- ✅ DNS resolution working from all Tailscale devices
- ✅ HTTP access working without errors
- ✅ No manual `/etc/hosts` configuration needed on any device
- ✅ Mobile devices can access services when connected to Tailscale
- ✅ Automatic service discovery for new Ingress resources

## Conclusion

The DNS + Ingress infrastructure is fully operational and provides seamless access to all homelab services via friendly DNS names. The solution is:

- **Scalable**: New services automatically get DNS resolution
- **Reliable**: socat forwarder + CoreDNS provide robust DNS
- **Flexible**: Works across all Tailscale devices (desktop, laptop, mobile)
- **Maintainable**: Simple architecture with clear troubleshooting steps

No further action required - the system is production-ready for homelab use.
