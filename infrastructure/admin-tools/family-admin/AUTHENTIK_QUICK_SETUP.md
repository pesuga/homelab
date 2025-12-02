# Authentik Quick Setup for Family Admin

## 🎯 The Missing Configuration

**The most likely issue**: The Family Admin application is **not assigned to the embedded outpost**.

## ⚡ Quick Fix Steps

### 1. Create Proxy Provider
```
Authentik Admin → Applications → Providers → Create

Type: Proxy Provider
Name: Family Admin Provider
Authorization flow: default-provider-authorization-implicit-consent
Forward auth (single application): ✅ CHECKED
External host: https://admin.fa.pesulabs.net

→ Click Finish
```

### 2. Create Application
```
Authentik Admin → Applications → Applications → Create

Name: Family Admin
Slug: family-admin
Provider: Family Admin Provider
Launch URL: https://admin.fa.pesulabs.net

→ Click Create
```

### 3. 🔥 CRITICAL: Assign to Embedded Outpost
```
Authentik Admin → Applications → Outposts → authentik Embedded Outpost

Click on "authentik Embedded Outpost"

In the "Applications" field:
- Click to open dropdown
- Find and SELECT "Family Admin"
- Should show: ✅ Family Admin

→ Click Update
→ Optionally restart outpost
```

## ✅ Verification

Test ForwardAuth endpoint:
```bash
kubectl run test-auth --image=curlimages/curl --restart=Never --rm -i -- \
  curl -I http://authentik-server.authentik.svc.cluster.local:9000/outpost.goauthentik.io/auth/traefik
```

**Expected**: `401 Unauthorized` or `302 Found` (NOT `404 Not Found`)

Then visit: `https://admin.fa.pesulabs.net`

**Expected**: Redirect to Authentik login

## 📋 Configuration Checklist

- [ ] Proxy Provider created with "Forward auth" enabled
- [ ] External host set to `https://admin.fa.pesulabs.net`
- [ ] Application created with slug `family-admin`
- [ ] Application linked to provider
- [ ] **Application assigned to embedded outpost** ⚠️ CRITICAL
- [ ] ForwardAuth endpoint returns 401/302 (not 404)
- [ ] Test URL redirects to Authentik login

## 🐛 Still Not Working?

Check the troubleshooting guide: `AUTHENTIK_TROUBLESHOOTING.md`