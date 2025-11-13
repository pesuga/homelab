# Port Forwarding Setup for Public HTTPS Access

## Overview
To enable public HTTPS access to homelab services, configure port forwarding on your router to forward external traffic to Traefik ingress controller.

## Router Configuration Required

### Port Forwarding Rules

Configure these rules on your router (typically accessed via http://192.168.8.1 or similar):

1. **HTTP to HTTPS Redirect**
   - External Port: `80`
   - Internal IP: `192.168.8.185` (asuna - K3s node)
   - Internal Port: `32060`
   - Protocol: TCP
   - Description: "Traefik HTTP (redirects to HTTPS)"

2. **HTTPS Traffic**
   - External Port: `443`
   - Internal IP: `192.168.8.185` (asuna - K3s node)
   - Internal Port: `30253`
   - Protocol: TCP
   - Description: "Traefik HTTPS"

### Network Details
- **Public IP**: 181.117.166.31 (as of 2025-11-13)
- **Internal Network**: 192.168.8.0/24
- **Service Node**: asuna (192.168.8.185)
- **Traefik Service**: LoadBalancer type with NodePorts

## DNS Configuration (Already Completed ✅)

The following DNS records are configured in Cloudflare pointing to public IP:

- `dash.pesulabs.net` → 181.117.166.31
- `n8n.homelab.pesulabs.net` → 181.117.166.31
- `family-assistant.homelab.pesulabs.net` → 181.117.166.31
- `discover.homelab.pesulabs.net` → 181.117.166.31

## SSL/TLS Certificates (Already Configured ✅)

Traefik is configured with:
- **ACME Provider**: Let's Encrypt
- **Challenge Type**: DNS-01 (Cloudflare)
- **Auto-renewal**: Enabled
- **Certificate Resolver**: `default`

Certificates will be automatically issued and renewed via Cloudflare DNS challenge.

## Verification Steps

After configuring port forwarding:

1. **Test HTTP Redirect** (should redirect to HTTPS):
   ```bash
   curl -I http://dash.pesulabs.net
   # Expected: HTTP/1.1 308 Permanent Redirect to https://
   ```

2. **Test HTTPS Access**:
   ```bash
   curl -I https://dash.pesulabs.net
   # Expected: HTTP/2 200 or 302 (working service)

   curl -I https://family-assistant.homelab.pesulabs.net/health
   # Expected: HTTP/2 200 (health check)

   curl -I https://n8n.homelab.pesulabs.net
   # Expected: HTTP/2 200 or 302 (N8n login)
   ```

3. **Check Certificate**:
   ```bash
   openssl s_client -connect dash.pesulabs.net:443 -servername dash.pesulabs.net < /dev/null 2>&1 | grep -A5 "Certificate chain"
   # Expected: Valid Let's Encrypt certificate
   ```

## Troubleshooting

### Cannot Access Services from Internet

1. **Verify Router Port Forwarding**:
   - Log into router admin interface
   - Check port forwarding rules are active
   - Verify internal IP is correct (192.168.8.185)

2. **Test from Outside Network**:
   - Use mobile data or external VPS to test
   - Cannot test from same network (NAT loopback may not work)

3. **Check Firewall**:
   - Verify ISP doesn't block ports 80/443
   - Some ISPs block residential port 80 - if so, use alternative ports

### Certificates Not Issuing

1. **Check Traefik Logs**:
   ```bash
   kubectl logs -n homelab -l app=traefik --tail=100 | grep -i acme
   ```

2. **Verify Cloudflare API Token**:
   ```bash
   kubectl get secret -n homelab cloudflare-api-token -o yaml
   ```

3. **Check DNS Records Exist**:
   ```bash
   dig +short @1.1.1.1 dash.pesulabs.net A
   # Should return: 181.117.166.31
   ```

### Alternative: Tailscale Funnel

If port forwarding doesn't work (ISP restrictions, CGNAT, etc.), use Tailscale Funnel:

```bash
# On service node (asuna)
tailscale funnel 443
```

This exposes port 443 publicly through Tailscale's infrastructure.

## Security Considerations

1. **Rate Limiting**: Consider adding Traefik rate limiting middleware
2. **WAF**: Cloudflare offers WAF if you enable proxied mode
3. **Monitoring**: Watch access logs for suspicious activity
4. **Fail2ban**: Consider implementing fail2ban for brute force protection

## Current Status

- ✅ DNS records configured
- ✅ Traefik deployed with ACME
- ✅ SSL certificates configured (DNS-01 challenge)
- ⏳ Port forwarding (manual configuration required)
- ⏳ Public HTTPS access verification

## Next Steps

1. Configure port forwarding on router
2. Wait 2-5 minutes for DNS propagation
3. Test HTTPS access from external network
4. Verify SSL certificates issued correctly
5. Update homelab dashboard with HTTPS URLs
