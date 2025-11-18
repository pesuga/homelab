# Next Task: TLS/HTTPS Implementation

**Priority**: High
**Scheduled**: Tomorrow (2025-01-04)
**Status**: Planning Phase

## Current State

✅ **What's Working**:
- DNS resolution via CoreDNS + Tailscale split DNS
- HTTP access to all 6 services via Traefik Ingress
- All services accessible via friendly DNS names

⚠️ **Current Limitation**:
- All traffic is HTTP only (no encryption)
- Traefik Ingress annotations changed to accept HTTP because HTTPS wasn't configured
- No TLS certificates deployed
- No automatic HTTP → HTTPS redirect

## Goal

Implement **fully-fledged TLS certificates** with:
1. ✅ Valid TLS certificates for all `*.pesulabs.net` domains
2. ✅ Automatic HTTPS redirect for all traffic
3. ✅ HTTP fallback only for services that don't support HTTPS
4. ✅ Automated certificate management (renewal, etc.)
5. ✅ Proper certificate validation and trust

## Requirements

### Must Have
- Valid TLS certificates (not self-signed)
- All services accessible via HTTPS
- Automatic HTTP → HTTPS redirect
- Certificate auto-renewal
- Works with Tailscale (internal network)

### Should Have
- Wildcard certificate for `*.pesulabs.net` OR individual certificates per service
- Certificate management via cert-manager
- Monitoring/alerting for certificate expiration
- Proper security headers (HSTS, etc.)

### Nice to Have
- ACME DNS-01 challenge for wildcard certs
- Certificate transparency monitoring
- Automated security scanning

## Technical Approach Options

### Option 1: Let's Encrypt + cert-manager (Recommended)

**Pros**:
- Free, automated, trusted certificates
- cert-manager handles renewal automatically
- Industry standard solution
- Integrates well with Traefik

**Cons**:
- Requires DNS-01 challenge for internal-only domains (or HTTP-01 if publicly accessible)
- Needs domain ownership verification
- 90-day certificate lifetime (but auto-renewed)

**Implementation**:
1. Deploy cert-manager to K3s cluster
2. Configure ClusterIssuer (Let's Encrypt staging + production)
3. Choose challenge method:
   - **DNS-01**: For wildcard certs (requires Cloudflare API access)
   - **HTTP-01**: For individual certs (requires public HTTP access)
4. Update Ingress resources with TLS configuration
5. Configure Traefik to redirect HTTP → HTTPS

### Option 2: Cloudflare Origin Certificates

**Pros**:
- Free for Cloudflare customers
- 15-year validity
- Works well with Cloudflare Tunnel or DNS

**Cons**:
- Only trusted by Cloudflare (not publicly trusted)
- Requires Cloudflare as DNS provider
- Manual certificate management

**Implementation**:
1. Generate Origin Certificate in Cloudflare dashboard
2. Create Kubernetes Secret with certificate
3. Configure Ingress resources to use certificate
4. Set up Traefik middleware for HTTP → HTTPS redirect

### Option 3: Self-Signed Certificates + Private CA

**Pros**:
- Complete control
- No external dependencies
- Works offline

**Cons**:
- Not publicly trusted (browser warnings)
- Manual trust distribution to all devices
- Manual renewal process
- Not recommended for production

## Recommended Solution: Let's Encrypt + cert-manager + DNS-01

### Why This Approach?

1. **Fully Trusted**: Let's Encrypt certificates are trusted by all browsers/devices
2. **Automated**: cert-manager handles certificate lifecycle automatically
3. **Wildcard Support**: DNS-01 challenge allows `*.pesulabs.net` wildcard certificate
4. **Tailscale Compatible**: Works with internal-only domains
5. **Industry Standard**: Well-documented, widely adopted solution

### Prerequisites

- Cloudflare account with `pesulabs.net` domain (already exists)
- Cloudflare API token with DNS edit permissions
- cert-manager deployed to K3s cluster
- Traefik configured to use TLS certificates from cert-manager

## Implementation Plan

### Phase 1: Deploy cert-manager
1. Install cert-manager via kubectl or Helm
2. Verify cert-manager pods are running
3. Configure RBAC and CRDs

### Phase 2: Configure Let's Encrypt Issuers
1. Create ClusterIssuer for Let's Encrypt **staging** (for testing)
2. Create ClusterIssuer for Let's Encrypt **production** (after staging validation)
3. Configure Cloudflare DNS-01 challenge with API token
4. Test staging issuer with a single service

### Phase 3: Request Wildcard Certificate
1. Create Certificate resource for `*.pesulabs.net`
2. Wait for cert-manager to complete DNS-01 challenge
3. Verify certificate is issued and stored in Kubernetes Secret
4. Test certificate validity

### Phase 4: Update Ingress Resources
1. Add TLS configuration to all 6 Ingress resources
2. Reference wildcard certificate Secret
3. Test HTTPS access to all services
4. Verify certificate is served correctly

### Phase 5: Configure HTTP → HTTPS Redirect
1. Create Traefik Middleware for redirect
2. Apply middleware to all Ingress resources
3. Test HTTP requests redirect to HTTPS
4. Verify services still accessible

### Phase 6: Production Rollout
1. Switch from staging to production Let's Encrypt
2. Request production certificates
3. Update all Ingress resources
4. Monitor certificate renewal
5. Document final configuration

## Services to Configure

All 6 services will get HTTPS:
1. LobeChat: `https://chat.homelab.pesulabs.net`
2. N8n: `https://n8n.homelab.pesulabs.net`
3. Grafana: `https://grafana.homelab.pesulabs.net`
4. Prometheus: `https://prometheus.homelab.pesulabs.net`
5. Flowise: `https://flowise.homelab.pesulabs.net`
6. Dashboard: `https://dash.pesulabs.net`

## Success Criteria

- ✅ All services accessible via HTTPS with valid certificates
- ✅ HTTP requests automatically redirect to HTTPS
- ✅ No browser certificate warnings
- ✅ Certificate auto-renewal configured (tested with staging)
- ✅ Monitoring in place for certificate expiration
- ✅ Documentation updated with HTTPS URLs

## Risks and Mitigations

### Risk 1: Let's Encrypt Rate Limits
- **Mitigation**: Use staging environment first, then production
- **Rate Limits**: 50 certificates per registered domain per week

### Risk 2: DNS-01 Challenge Failure
- **Mitigation**: Verify Cloudflare API token has DNS edit permissions
- **Fallback**: Use HTTP-01 challenge if DNS-01 fails

### Risk 3: Traefik Configuration Issues
- **Mitigation**: Test redirect middleware on single service first
- **Rollback**: Keep HTTP access working during transition

### Risk 4: Certificate Renewal Failure
- **Mitigation**: Set up monitoring alerts for certificate expiration
- **Backup**: Document manual renewal process

## Testing Strategy

### Test 1: Certificate Validity
```bash
# Check certificate details
openssl s_client -connect chat.homelab.pesulabs.net:443 -servername chat.homelab.pesulabs.net

# Verify certificate chain
curl -vI https://chat.homelab.pesulabs.net/chat 2>&1 | grep -i certificate
```

### Test 2: HTTP → HTTPS Redirect
```bash
# Should return 301/302 redirect to HTTPS
curl -I http://chat.homelab.pesulabs.net/chat

# Should return 200 OK
curl -I https://chat.homelab.pesulabs.net/chat
```

### Test 3: Browser Access
1. Open browser to `http://chat.homelab.pesulabs.net/chat`
2. Verify automatic redirect to HTTPS
3. Check certificate in browser (should be valid, no warnings)
4. Verify lock icon in address bar

### Test 4: Mobile Access
1. Connect to Tailscale on mobile
2. Navigate to HTTPS URLs
3. Verify no certificate warnings
4. Test HTTP redirect on mobile browser

## Documentation to Update

1. `docs/SERVICE-ENDPOINTS.md` - Change HTTP to HTTPS URLs
2. `docs/TAILSCALE-DNS-SETUP.md` - Add TLS configuration section
3. `docs/TLS-SETUP.md` - New document for certificate management
4. `README.md` - Update service URLs to HTTPS
5. `claudedocs/dns-ingress-completion-summary.md` - Add TLS completion

## Reference Materials

- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Let's Encrypt DNS-01 Challenge](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge)
- [Traefik HTTPS Configuration](https://doc.traefik.io/traefik/https/overview/)
- [Cloudflare API Tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)
- [Traefik Middlewares](https://doc.traefik.io/traefik/middlewares/http/redirectscheme/)

## Estimated Time

- **Research/Planning**: 30 minutes
- **cert-manager Installation**: 30 minutes
- **Let's Encrypt Configuration**: 1 hour
- **Certificate Request + Validation**: 30 minutes
- **Ingress Updates**: 1 hour
- **Redirect Middleware**: 30 minutes
- **Testing + Verification**: 1 hour
- **Documentation**: 30 minutes

**Total**: ~5-6 hours for complete implementation

## Next Steps for Tomorrow

1. Review this plan
2. Verify Cloudflare account access and domain ownership
3. Create Cloudflare API token with DNS edit permissions
4. Deploy cert-manager to K3s cluster
5. Begin Let's Encrypt staging configuration
6. Test with a single service first (LobeChat or Dashboard)
7. Roll out to all services after validation

---

**Status**: Ready to start tomorrow
**Created**: 2025-01-03
**Owner**: homelab admin
