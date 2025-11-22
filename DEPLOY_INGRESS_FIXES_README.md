# Quick Start: Deploy Ingress Routing Fixes

**Status:** ✅ READY TO DEPLOY
**Risk Level:** Low (backups included, rollback available)
**Estimated Time:** 10-15 minutes
**Downtime:** < 5 minutes per service

---

## TL;DR - Quick Deploy

```bash
# From homelab project root
cd /home/pesu/Rakuflow/systems/homelab

# Review what will be changed (dry-run)
./scripts/deploy-ingress-fixes.sh --dry-run

# Deploy the fixes
./scripts/deploy-ingress-fixes.sh

# Monitor the deployment
watch kubectl get ingressroutes -A
```

---

## What This Fixes

### Golden Rules Compliance Issues:
1. ❌ **Mixed Ingress Formats** → ✅ All using IngressRoute
2. ❌ **Port Mapping Mismatches** → ✅ Standard port 80 mappings
3. ❌ **Direct Container Ports** → ✅ Service port abstraction
4. ❌ **NodePort Exposure** → ✅ ClusterIP with IngressRoute only

### Services Fixed:
- **Authentik:** Port 80 → 9000 mapping added
- **Family Admin:** Port 80 → 3000 mapping added
- **N8N:** Port 80 → 5678 mapping added, changed to ClusterIP

---

## Pre-Deployment Checklist

- [ ] Read `INGRESS_ROUTING_AUDIT_REPORT.md` (understand what's broken)
- [ ] Read `INGRESS_ROUTING_FIXES_SUMMARY.md` (understand the fixes)
- [ ] Have kubectl access to the cluster
- [ ] Verify current state: `kubectl get ingressroutes -A`
- [ ] (Optional) Schedule maintenance window

---

## Deployment Options

### Option 1: Automated Script (Recommended)

```bash
# Standard deployment with backups
./scripts/deploy-ingress-fixes.sh

# Dry-run first (review changes)
./scripts/deploy-ingress-fixes.sh --dry-run

# Deploy without backups (faster, but riskier)
./scripts/deploy-ingress-fixes.sh --skip-backup
```

### Option 2: Manual Step-by-Step

Follow instructions in `INGRESS_ROUTING_FIXES_SUMMARY.md` under "Deployment Instructions"

---

## Files Created

### 1. Configuration Files
- `infrastructure/kubernetes/traefik/ingress-routes-fixed.yaml` - All compliant IngressRoutes
- `infrastructure/kubernetes/services/authentik-server-service-fixed.yaml` - Fixed port mapping
- `infrastructure/kubernetes/services/family-admin-service-fixed.yaml` - Fixed port mapping
- `infrastructure/kubernetes/services/n8n-service-fixed.yaml` - Fixed port mapping

### 2. Documentation
- `INGRESS_ROUTING_AUDIT_REPORT.md` - Detailed audit findings
- `INGRESS_ROUTING_FIXES_SUMMARY.md` - Complete fix documentation
- `DEPLOY_INGRESS_FIXES_README.md` - This quick start guide

### 3. Automation
- `scripts/deploy-ingress-fixes.sh` - Automated deployment script

---

## Validation After Deployment

### Quick Tests

```bash
# Test all HTTPS endpoints
curl -I https://auth.pesulabs.net
curl -I https://app.fa.pesulabs.net
curl -I https://admin.fa.pesulabs.net
curl -I https://api.fa.pesulabs.net
curl -I https://n8n.fa.pesulabs.net
```

Expected: HTTP 200, 301, 302, 401, or 403 (not 404 or 503)

### Verify IngressRoutes

```bash
# List all IngressRoutes
kubectl get ingressroutes -A

# Check specific IngressRoute
kubectl describe ingressroute admin-dashboard -n homelab
```

Expected: 5 IngressRoutes, all with `entryPoints: [websecure]` and `certResolver: default`

### Check Service Endpoints

```bash
# Verify services have endpoints
kubectl get endpoints -n authentik authentik-server
kubectl get endpoints -n homelab family-admin
kubectl get endpoints -n homelab n8n
```

Expected: Each should have at least one IP address

### Monitor Traefik Logs

```bash
# Watch for errors
kubectl logs -n homelab deployment/traefik --tail=100 | grep -i error

# Follow logs in real-time
kubectl logs -n homelab deployment/traefik -f
```

Expected: No routing or certificate errors

---

## Troubleshooting

### Issue: Service returns 503 Service Unavailable

**Cause:** Service endpoints not ready

**Fix:**
```bash
# Check pod status
kubectl get pods -n <namespace>

# Check service endpoints
kubectl get endpoints -n <namespace> <service-name>

# Restart deployment if needed
kubectl rollout restart deployment/<deployment-name> -n <namespace>
```

---

### Issue: Certificate errors in browser

**Cause:** TLS certificate not issued yet

**Fix:**
```bash
# Check Traefik logs for certificate errors
kubectl logs -n homelab deployment/traefik | grep -i certificate

# Wait a few minutes for Let's Encrypt to issue certificate
# Then clear browser cache and retry
```

---

### Issue: 404 Not Found

**Cause:** IngressRoute not applied or misconfigured

**Fix:**
```bash
# Verify IngressRoute exists
kubectl get ingressroute <name> -n <namespace>

# Check IngressRoute configuration
kubectl describe ingressroute <name> -n <namespace>

# Reapply if needed
kubectl apply -f infrastructure/kubernetes/traefik/ingress-routes-fixed.yaml
```

---

### Issue: Internal DNS resolution fails

**Cause:** This deployment only fixes external routing, not internal

**Fix:**
Internal service-to-service communication was fixed in a previous session.
See `NETWORKING_AUDIT_REPORT.md` for internal traffic fixes.

---

## Rollback Instructions

If something goes wrong, rollback using the automated backups:

```bash
# Backups are saved in /tmp/homelab-ingress-backup-TIMESTAMP/

# Find latest backup
ls -lt /tmp/homelab-ingress-backup-* | head -1

# Rollback services
kubectl apply -f /tmp/homelab-ingress-backup-TIMESTAMP/authentik-server-backup.yaml
kubectl apply -f /tmp/homelab-ingress-backup-TIMESTAMP/family-admin-backup.yaml
kubectl apply -f /tmp/homelab-ingress-backup-TIMESTAMP/n8n-backup.yaml

# Rollback IngressRoutes
kubectl apply -f /tmp/homelab-ingress-backup-TIMESTAMP/ingressroutes-backup.yaml
```

---

## Success Criteria

- [ ] All 5 services accessible via HTTPS
- [ ] Valid TLS certificates (Let's Encrypt)
- [ ] No 404 or 503 errors
- [ ] No Traefik routing errors in logs
- [ ] Service endpoints healthy
- [ ] Applications functioning normally
- [ ] 100% Golden Rules compliance

---

## Post-Deployment Actions

1. **Test User Workflows:**
   - Login to admin panel at https://admin.fa.pesulabs.net
   - Access N8N at https://n8n.fa.pesulabs.net
   - Test Authentik authentication at https://auth.pesulabs.net
   - Verify API endpoints at https://api.fa.pesulabs.net

2. **Monitor for 24 Hours:**
   ```bash
   # Watch for any issues
   kubectl logs -n homelab deployment/traefik -f
   ```

3. **Delete Old Files (After Verification):**
   ```bash
   # Only delete after confirming everything works for 24+ hours
   rm infrastructure/kubernetes/family-app/ingress.yaml
   rm infrastructure/kubernetes/family-assistant-app/ingress.yaml
   rm infrastructure/kubernetes/family-assistant-admin/ingress.yaml
   rm infrastructure/kubernetes/traefik/ingress-routes.yaml
   ```

4. **Update Project Documentation:**
   - Mark this deployment as complete
   - Update SESSION-STATE.md
   - Document any additional observations

---

## Support & References

### Documentation
- **Golden Rules:** `project_context/NETWORKING_STANDARD.md`
- **Audit Report:** `INGRESS_ROUTING_AUDIT_REPORT.md`
- **Fixes Summary:** `INGRESS_ROUTING_FIXES_SUMMARY.md`
- **Internal Traffic Fixes:** `NETWORKING_AUDIT_REPORT.md`

### Quick Commands
```bash
# View all IngressRoutes
kubectl get ingressroutes -A

# View all services with ports
kubectl get svc -A -o wide

# Check Traefik configuration
kubectl describe deployment traefik -n homelab

# View TLS certificates
kubectl get certificates -A
```

### Getting Help
If you encounter issues:
1. Check Traefik logs for specific errors
2. Verify service endpoints have IPs
3. Test internal connectivity from a pod
4. Review Golden Rules compliance
5. Check if backups are available for rollback

---

## Architecture Overview

### Before Fixes:
```
User → HTTPS → Traefik → Ingress (old) → Service (wrong port) → 503 Error
```

### After Fixes:
```
User → HTTPS → Traefik → IngressRoute (websecure) → Service (port 80) → Container (target port) → ✅
```

### Port Mapping Standard:
```
IngressRoute (port 80) → Service (port 80 → targetPort: container-port) → Container
```

---

## Summary

This deployment brings the homelab cluster to **100% Golden Rules compliance** for external routing:

- ✅ All external traffic via HTTPS (websecure entryPoint)
- ✅ TLS via Let's Encrypt with Cloudflare DNS-01
- ✅ Standardized port 80 mappings
- ✅ Consistent IngressRoute format
- ✅ Proper service abstraction

Combined with the previous internal traffic fixes, the entire networking stack now follows the Golden Rules from `NETWORKING_STANDARD.md`.

**Result:** Reliable, maintainable, and secure routing configuration that "just works."
