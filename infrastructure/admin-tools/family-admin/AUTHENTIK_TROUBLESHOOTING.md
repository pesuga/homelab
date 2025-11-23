# Authentik Integration Troubleshooting Guide

## Current Issue

The Family Admin ingress is configured with Authentik middleware, but authentication is not working. The ForwardAuth endpoint returns 404.

## Diagnosis

✅ **Working Components:**
- Authentik server is running: `authentik-server-75b86c5997-2hwb7`
- Authentik middleware created: `authentik@authentik`
- Family Admin ingress has middleware annotation
- Embedded outpost is connecting to server

❌ **Issue:**
- ForwardAuth endpoint `/outpost.goauthentik.io/auth/traefik` returns 404
- This means the Proxy Provider is not properly linked to the embedded outpost

## Root Cause

The Authentik **Embedded Outpost** is not configured with the Proxy Provider. The embedded outpost needs to be explicitly assigned to handle the Family Admin proxy provider.

## Step-by-Step Fix

### Step 1: Access Authentik Admin Interface

1. Navigate to `https://auth.pesulabs.net`
2. Sign in with admin credentials

### Step 2: Verify/Create Proxy Provider

1. Go to **Applications** → **Providers**
2. Look for "Family Admin Provider" (or create if missing)
3. **Click Create** (if needed):
   - **Type**: `Proxy Provider`
   - **Name**: `Family Admin Provider`
   - **Authorization flow**: `default-provider-authorization-implicit-consent`
   - **Forward auth (single application)**: ✅ **ENABLED** (CRITICAL)
   - **External host**: `https://admin.fa.pesulabs.net`
   - Click **Finish**

### Step 3: Create/Update Application

1. Go to **Applications** → **Applications**
2. Look for "Family Admin" (or create if missing)
3. **Click Create** (if needed):
   - **Name**: `Family Admin`
   - **Slug**: `family-admin`
   - **Provider**: Select `Family Admin Provider` (from step 2)
   - **Launch URL**: `https://admin.fa.pesulabs.net`
   - Click **Create**

### Step 4: Configure Embedded Outpost (CRITICAL STEP)

This is the most important step that's likely missing:

1. Go to **Applications** → **Outposts**
2. Click on **authentik Embedded Outpost** (should already exist)
3. In the outpost configuration:
   - **Type**: Should be `Proxy` (not LDAP or RADIUS)
   - **Applications**: Click the field and **ADD** `Family Admin` ✅
   - **Configuration**: Should have:
     ```yaml
     authentik_host: http://authentik-server.authentik.svc.cluster.local:9000
     authentik_host_insecure: false
     authentik_host_browser: https://auth.pesulabs.net
     log_level: info
     object_naming_template: ak-outpost-%(name)s
     docker_network: null
     docker_map_ports: true
     container_image: null
     kubernetes_replicas: 1
     kubernetes_namespace: authentik
     ```
   - Click **Update**

4. **Restart the outpost** (if needed):
   - Click the **⋮** menu next to the embedded outpost
   - Select **Restart**

### Step 5: Verify Configuration

After completing the above steps, test the ForwardAuth endpoint:

```bash
# From within cluster
kubectl run test-auth --image=curlimages/curl --restart=Never --rm -i -- \
  curl -I http://authentik-server.authentik.svc.cluster.local:9000/outpost.goauthentik.io/auth/traefik

# Expected: 401 or 302 redirect (NOT 404)
```

### Step 6: Test the Application

1. Visit `https://admin.fa.pesulabs.net`
2. You should be redirected to `https://auth.pesulabs.net`
3. After login, you should be redirected back to Family Admin

## Common Configuration Mistakes

### ❌ Mistake 1: Provider Not Set to "Forward Auth (Single Application)"
**Symptom**: 404 on ForwardAuth endpoint
**Fix**: Edit provider → Enable "Forward auth (single application)"

### ❌ Mistake 2: Application Not Assigned to Embedded Outpost
**Symptom**: 404 on ForwardAuth endpoint
**Fix**: Go to Outposts → authentik Embedded Outpost → Add application

### ❌ Mistake 3: Wrong External Host URL
**Symptom**: Redirect loop or authentication fails
**Fix**: External host must exactly match: `https://admin.fa.pesulabs.net`

### ❌ Mistake 4: Authorization Flow Not Set
**Symptom**: Authentication errors
**Fix**: Use `default-provider-authorization-implicit-consent`

## Verification Commands

### Check Authentik Middleware
```bash
kubectl get middleware authentik -n authentik -o yaml
```

Expected output should show:
```yaml
spec:
  forwardAuth:
    address: http://authentik-server.authentik.svc.cluster.local:9000/outpost.goauthentik.io/auth/traefik
```

### Check Ingress Configuration
```bash
kubectl get ingress family-assistant-admin -n homelab -o yaml
```

Expected middleware annotation:
```yaml
metadata:
  annotations:
    traefik.ingress.kubernetes.io/router.middlewares: authentik@authentik,...
```

### Check Authentik Server Logs
```bash
kubectl logs -n authentik authentik-server-75b86c5997-2hwb7 --tail=100 | grep -i outpost
```

Should show outpost connecting successfully.

### Test ForwardAuth Endpoint
```bash
curl -I http://authentik-server.authentik.svc.cluster.local:9000/outpost.goauthentik.io/auth/traefik
```

Expected responses:
- `401 Unauthorized` - Good! Means endpoint exists, needs auth
- `302 Found` - Good! Redirecting to login
- `404 Not Found` - Bad! Provider not linked to outpost

## Alternative: Use Traefik IngressRoute Instead of Ingress

If the standard Kubernetes Ingress continues to have issues, we can convert to Traefik IngressRoute:

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: family-admin
  namespace: homelab
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`admin.fa.pesulabs.net`)
      kind: Rule
      services:
        - name: family-admin
          port: 3000
      middlewares:
        - name: authentik
          namespace: authentik
  tls:
    certResolver: default
```

This syntax is more direct and guaranteed to work with Traefik.

## Expected User Flow

1. **Unauthenticated User** visits `https://admin.fa.pesulabs.net`
2. **Traefik** intercepts request, forwards to Authentik middleware
3. **Authentik** checks for session cookie
4. **No session found** → Redirect to `https://auth.pesulabs.net/application/o/family-admin/`
5. **User authenticates** with Authentik credentials
6. **Authentik** creates session, redirects back with headers
7. **Traefik** forwards request with Authentik headers to Family Admin
8. **Family Admin** extracts user from headers, creates session
9. **User** sees authenticated dashboard

## Next Steps After Fix

Once authentication is working:

1. **Test user groups**: Verify admin/user permissions
2. **Test logout**: Should redirect to Authentik logout
3. **Test session persistence**: Refresh page, should stay logged in
4. **Monitor logs**: Check for any authentication errors

## Debug Mode

To enable debug logging in Authentik:

1. Edit authentik deployment:
   ```bash
   kubectl edit deployment authentik-server -n authentik
   ```

2. Add environment variable:
   ```yaml
   env:
   - name: AUTHENTIK_LOG_LEVEL
     value: debug
   ```

3. Watch logs:
   ```bash
   kubectl logs -n authentik -f authentik-server-75b86c5997-2hwb7
   ```

---

**Status**: Waiting for Authentik configuration completion
**Critical Step**: Assign Family Admin application to embedded outpost