# Authentik SSO Integration for Family Admin Panel

**Status:** WORKING - Authentication flow functional, redirect URL needs configuration
**Date:** 2025-11-22 (Updated: 2025-11-23)
**Integration Method:** Proxy Provider with dedicated outpost

## Overview

The Family Admin Panel has been integrated with Authentik using the **Proxy Provider** method. This provides Single Sign-On (SSO) capabilities and centralized user management through Authentik.

## Architecture

### Authentication Flow

1. **User Access**: User visits `https://admin.fa.pesulabs.net`
2. **Authentik Intercept**: Traefik middleware intercepts request and forwards to Authentik
3. **Authentik Authentication**: User authenticates with Authentik (forms, SSO, etc.)
4. **Header Injection**: Authentik forwards authenticated request with user headers
5. **Header Extraction**: Family Admin extracts user info from headers and creates session
6. **Authenticated Access**: User accesses admin panel with proper permissions

### Key Components

#### 1. Authentik Headers (`/lib/authentik.ts`)
- Extracts user information from Authentik ForwardAuth headers
- Headers processed:
  - `X-authentik-username`: Username
  - `X-authentik-email`: Email address
  - `X-authentik-name`: Full name
  - `X-authentik-groups`: Comma-separated groups
  - `X-authentik-uid`: User UUID

#### 2. API Endpoint (`/app/api/auth/me/route.ts`)
- Server-side endpoint to read Authentik headers
- Returns user profile in frontend-expected format
- Handles development mode with mock users

#### 3. Updated AuthContext (`/context/AuthContext.tsx`)
- Removed JWT token dependency
- Reads user profile from `/api/auth/me` endpoint
- Handles SSO logout redirection
- Maintains development mode compatibility

#### 4. SSO Sign-In Component (`/components/auth/SSOSignIn.tsx`)
- Production: Redirects to Authentik for authentication
- Development: Falls back to form-based authentication
- Handles automatic authentication check

#### 5. Middleware (`/middleware.ts`)
- Route protection based on Authentik headers
- Public route exclusions for sign-in, health, etc.
- Development mode bypass

## Configuration

### Kubernetes Ingress Update

The Family Admin Ingress has been updated to include Authentik middleware:

```yaml
annotations:
  traefik.ingress.kubernetes.io/router.middlewares: authentik@authentik,family-assistant-admin-rate-limit@kubernetescrd,family-assistant-admin-security@kubernetescrd
```

### Development Mode

In development (`NODE_ENV=development`):
- Authentication is bypassed
- Mock user created automatically
- Form-based authentication still available for testing

### Production Mode

In production (`NODE_ENV=production`):
- All requests must go through Authentik
- Automatic redirect to Authentik for unauthenticated users
- Header-based authentication extraction

## User Groups and Permissions

### Admin Access
Users in the following groups get admin access:
- `admins`
- `family-admins`

### User Profile Format

```typescript
{
  id: string;           // X-authentik-uid
  email: string;        // X-authentik-email
  username: string;     // X-authentik-username
  role: string;         // 'admin' | 'user'
  is_admin: boolean;    // Based on group membership
  display_name: string; // X-authentik-name
  first_name: string;   // Extracted from display_name
  last_name: string;    // Extracted from display_name
  groups: string[];     // X-authentik-groups
}
```

## Deployment Steps

### 1. Authentik Configuration

1. **Create Proxy Provider** in Authentik:
   - Type: Proxy Provider
   - Name: "Family Admin Provider"
   - Authentication Flow: `default-authentication-flow`
   - Authorization Flow: `default-provider-authorization-implicit-consent`
   - Forward Auth: Selected
   - External Host: `https://admin.fa.pesulabs.net`

2. **Create Application** in Authentik:
   - Name: "Family Admin"
   - Slug: "family-admin"
   - Provider: Select provider created above

### 2. Kubernetes Deployment

1. **Apply Ingress Update**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/family-assistant-admin/ingress.yaml
   ```

2. **Verify Middleware**:
   ```bash
   kubectl describe middleware authentik -n authentik
   ```

3. **Check Ingress**:
   ```bash
   kubectl describe ingress family-assistant-admin -n family-assistant-admin
   ```

### 3. Testing

1. **Production Test**:
   - Visit `https://admin.fa.pesulabs.net`
   - Should redirect to Authentik
   - Login with Authentik credentials
   - Should return to admin panel authenticated

2. **Development Test**:
   - Run locally with `NODE_ENV=development`
   - Should automatically authenticate as mock user

## Security Considerations

### Header Validation
- All authentication relies on Traefik-Authentik middleware
- Headers cannot be spoofed due to middleware placement
- No direct access to application without Authentik validation

### Session Management
- No server-side sessions stored in application
- Authentication state maintained by Authentik
- Frontend stores minimal user profile for UI

### Logout
- Production: Redirects to Authentik logout endpoint
- Development: Clears local state only

## Troubleshooting

### Common Issues

1. **401 Unauthorized**:
   - Check Authentik middleware is properly applied
   - Verify user is authenticated in Authentik
   - Check user group membership

2. **Missing Headers**:
   - Verify Traefik middleware configuration
   - Check Authentik outpost connectivity
   - Review Ingress annotations

3. **Redirect Loop**:
   - Check middleware order in Ingress
   - Verify Authentik application URL configuration
   - Ensure proper authentication flow selection

### Debug Logging

Enable debug logging in development:
```bash
NODE_ENV=development npm run dev
```

Check browser console for:
- Authentik header extraction messages
- Authentication state changes
- API response errors

## Files Modified

- `/lib/authentik.ts` - NEW: Authentik header processing
- `/app/api/auth/me/route.ts` - NEW: User profile endpoint
- `/components/auth/SSOSignIn.tsx` - NEW: SSO sign-in component
- `/middleware.ts` - NEW: Route protection middleware
- `/context/AuthContext.tsx` - UPDATED: SSO integration
- `/lib/api-client.ts` - UPDATED: Auth flow changes
- `/app/(full-width-pages)/(auth)/signin/page.tsx` - UPDATED: SSO integration
- `/infrastructure/kubernetes/family-assistant-admin/ingress.yaml` - UPDATED: Authentik middleware

## Next Steps

1. **Create Authentik Provider and Application** (manual step)
2. **Deploy updated Ingress configuration**
3. **Test authentication flow**
4. **Configure user groups in Authentik**
5. **Update user documentation**

---

**Status**: ✅ IMPLEMENTED - Ready for Authentik configuration and testing

## Current Status (2025-11-23)

### ✅ Working Components

1. **Traefik Middleware Integration**
   - Middleware correctly deployed in homelab namespace
   - IngressRoute properly configured without namespace conflicts
   - No more "middleware not in namespace" errors

2. **Authentik Proxy Outpost**
   - Deployed and running: `authentik-proxy-7f8999c6b-jhr4n`
   - ForwardAuth endpoint accessible: `http://authentik-proxy.authentik.svc.cluster.local:9000/outpost.goauthentik.io/auth/traefik`
   - Successfully connected to Authentik server via websocket
   - Proper outpost token configured in Kubernetes secret

3. **Authentication Flow**
   - Accessing `https://admin.fa.pesulabs.net` triggers 302 redirect to Authentik
   - Authentik headers successfully passed through Traefik
   - ForwardAuth integration functioning correctly

### ⚠️ Known Issues

1. **Redirect URL Configuration**
   - Issue: Redirect location uses internal cluster DNS instead of external URL
   - Current: `http://authentik-server.authentik.svc.cluster.local:9000/application/o/authorize/...`
   - Expected: `https://auth.pesulabs.net/application/o/authorize/...`
   - Impact: Users cannot complete login flow (internal URL not accessible from browser)
   - Fix Required: Update Authentik provider "External host" setting to use `https://auth.pesulabs.net`

### 📋 Next Steps

1. Update Authentik Provider Configuration:
   - Go to Authentik Admin UI → Applications → Providers → Family Admin Provider
   - Update "External host" field to: `https://auth.pesulabs.net`
   - Save provider configuration

2. Test Complete Authentication Flow:
   - Visit `https://admin.fa.pesulabs.net`
   - Verify redirect to `https://auth.pesulabs.net`
   - Complete authentication
   - Verify redirect back to Family Admin
   - Confirm user headers are passed correctly

3. Verify User Session:
   - Check that `/api/auth/me` returns correct user profile
   - Verify admin panel functionality with SSO session
   - Test logout flow

### 🔧 Deployment Commands Reference

```bash
# Check proxy outpost status
kubectl get pods -n authentik -l app.kubernetes.io/name=authentik-proxy

# View proxy outpost logs
kubectl logs -n authentik -l app.kubernetes.io/name=authentik-proxy --tail=50

# Check middleware configuration
kubectl get middleware -n homelab authentik -o yaml

# Verify IngressRoute configuration
kubectl get ingressroute family-admin -n homelab -o yaml

# Test ForwardAuth endpoint (through Traefik)
curl -I https://admin.fa.pesulabs.net

# Check Traefik logs for errors
kubectl logs -n homelab -l app=traefik --tail=100 | grep -i "middleware\|family-admin"
```

### 📝 Troubleshooting Resolved

1. **Middleware Namespace Conflict** (RESOLVED)
   - Problem: Traefik couldn't reference middleware from different namespace
   - Solution: Created copy of authentik middleware in homelab namespace
   - File: `/infrastructure/kubernetes/homelab/authentik-middleware.yaml`

2. **Embedded Outpost Limitation** (RESOLVED)
   - Problem: Embedded outpost doesn't serve ForwardAuth endpoint
   - Solution: Deployed dedicated proxy outpost with proper configuration
   - File: `/infrastructure/kubernetes/auth/authentik/proxy-outpost.yaml`

3. **Invalid Outpost Token** (RESOLVED)
   - Problem: 403 Forbidden errors from proxy outpost
   - Solution: Generated new token from Authentik UI and updated Kubernetes secret
   - Command: `kubectl create secret generic authentik-outpost-token --from-literal=token=... -n authentik`

