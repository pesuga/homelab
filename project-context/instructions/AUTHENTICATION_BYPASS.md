# Authentication Bypass Instructions

## Overview

This document explains how to temporarily bypass authentication in the Family Assistant system for development and testing purposes.

**Important**: This is intended for development/testing only and should be reverted in production environments.

## Current Authentication Bypass Status

### Frontend (React App) ✅ BYPASSED
- **ProtectedRoute.tsx**: Modified to always return children without authentication checks
- **Result**: All React routes (including `/chat`) are accessible without login
- **File**: `apps/family-portal/src/components/ProtectedRoute.tsx`

### Backend API 🔧 PARTIALLY BYPASSED
- **JWT Token**: Generated mock JWT token with admin privileges
- **Nginx Proxy**: Configured to automatically add authentication headers to all API requests
- **Status**: Basic API calls work, but some admin routes may not be implemented

## Implementation Details

### 1. Frontend Authentication Bypass

The React app's `ProtectedRoute.tsx` component has been modified to bypass authentication:

```typescript
export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    // TEMPORARY BYPASS: Always return children (disable authentication)
    // TODO: Re-enable authentication when Let's Encrypt rate limit is resolved
    return <>{children}</>;

    // Original auth logic (commented out for bypass)
    /*
    const { isAuthenticated, loading } = useAuth();
    if (loading) { ... }
    if (!isAuthenticated) { return <Navigate to="/login" replace />; }
    return <>{children}</>;
    */
}
```

### 2. Backend Authentication Bypass

#### Nginx Configuration
The frontend nginx proxy automatically adds authentication headers to all `/api/*` requests:

```nginx
# API proxy to backend
location /api/ {
    # Add mock authentication headers to bypass auth
    proxy_set_header X-User-Id "550e8400-e29b-41d4-a716-446655440000";
    proxy_set_header X-Telegram-User-Id "123456789";
    proxy_set_header Authorization "Bearer eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJzdWIiOiAiNTUwZTg0MDAtZTI5Yi00MWQ0LWE3MTYtNDQ2NjU1NDQwMDAwIiwgImV4cCI6IDE3NjQ1NDA0MzIsICJpYXQiOiAxNzY0NTM2ODMyLCAiZW1haWwiOiAiYWRtaW5AdGVzdC5jb20iLCAiaXNfYWRtaW4iOiB0cnVlLCAicm9sZSI6ICJwYXJlbnQifQ.Zw9LF1Uji6USbgJFMH81lg7BcmktECfVYdIqfTsrAQA";

    proxy_pass http://family-assistant-api.fa-platform.svc.cluster.local:8001/;
    # ... other proxy settings
}
```

#### JWT Token Details
- **User ID**: `550e8400-e29b-41d4-a716-446655440000`
- **Email**: `admin@test.com`
- **Role**: `parent`
- **Admin**: `true`
- **Secret**: `change-me-in-production` (default)
- **Expires**: 1 hour from creation

### 3. Backend API Configuration

The API deployment has been configured with debug mode:

```yaml
env:
- name: DEBUG
  value: "true"
- name: DISABLE_AUTH
  value: "true"
```

## Current Access Status

### ✅ Working (Accessible)
- **Family App**: https://app.fa.pesulabs.net/ - Main dashboard
- **Chat Interface**: https://app.fa.pesulabs.net/chat - Chat without login
- **API Proxy**: All `/api/*` calls from frontend work
- **Chat API**: `/api/v1/chat/completions` - Works with mock user

### ❓ Partially Working
- **Analytics API**: `/api/v1/analytics/*` - Mixed status
  - **Direct API calls** (`api.fa.pesulabs.net`): Returns 403 (authentication required)
  - **Through Family App** (`app.fa.pesulabs.net/api/*`): Returns 404 (may not be implemented in current version)
  - **Root cause**: Analytics routes exist but may not be fully implemented or have version compatibility issues
- **Admin Interface**: https://admin.fa.pesulabs.net/ - Basic UI loads, but analytics API calls get 403
  - **Issue**: Admin interface makes direct API calls without authentication headers

### ❌ Not Working
- **SSL Certificate**: auth.pesulabs.net - Rate limited by Let's Encrypt until Dec 2, 2025

## How to Re-enable Authentication

### Step 1: Restore Frontend Authentication

1. **Edit ProtectedRoute.tsx**:
   ```bash
   # Navigate to app directory
   cd /home/pesu/Rakuflow/systems/homelab/apps/family-portal

   # Edit the file to restore original authentication
   nano src/components/ProtectedRoute.tsx
   ```

2. **Replace with original code**:
   ```typescript
   import { Navigate } from 'react-router-dom';
   import { useAuth } from '../context/AuthContext';

   export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
       const { isAuthenticated, loading } = useAuth();

       if (loading) {
           return (
               <div className="flex items-center justify-center min-h-screen">
                   <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
               </div>
           );
       }

       if (!isAuthenticated) {
           return <Navigate to="/login" replace />;
       }

       return <>{children}</>;
   }
   ```

3. **Rebuild and redeploy frontend**:
   ```bash
   npm run build
   # Deploy to Kubernetes
   ```

### Step 2: Remove Backend Authentication Bypass

1. **Remove environment variables**:
   ```bash
   kubectl patch deployment family-assistant-api -n fa-platform \
     --type=json -p='[{"op": "remove", "path": "/spec/template/spec/containers/0/env/0"}, {"op": "remove", "path": "/spec/template/spec/containers/0/env/1"}]'
   ```

2. **Remove JWT token from nginx**:
   ```bash
   # Edit nginx config to remove Authorization header
   # Remove this line from location /api/ block:
   # proxy_set_header Authorization "Bearer <token>";
   ```

### Step 3: Restart Services

```bash
kubectl rollout restart deployment family-assistant-api -n fa-platform
kubectl rollout restart deployment family-assistant-app-working -n fa-platform
```

## File Locations

### Frontend Files
- **ProtectedRoute**: `apps/family-portal/src/components/ProtectedRoute.tsx`
- **Nginx Config**: In pod at `/etc/nginx/conf.d/default.conf`

### Backend Files
- **Dependencies**: `/app/src/api/dependencies.py` (in container)
- **Analytics Routes**: `/app/src/api/routes/analytics.py` (in container)
- **JWT Auth**: `/app/src/api/auth/jwt_auth.py` (in container)

### Kubernetes Configurations
- **Frontend Deployment**: `deployment/family-assistant-app-working` in `fa-platform` namespace
- **Backend Deployment**: `deployment/family-assistant-api` in `fa-platform` namespace

## Security Notes

1. **JWT Secret**: The backend uses the default secret `change-me-in-production`. In production, this should be changed.
2. **Mock User**: The bypass uses a mock user ID. This user doesn't exist in the database but legacy authentication allows it.
3. **Expiry**: JWT tokens expire after 1 hour. New tokens can be generated using the script in `/tmp/create_jwt.py`.
4. **Rate Limiting**: SSL certificate rate limiting is the original issue requiring this bypass (resets Dec 2, 2025).

## Testing the Bypass

### Test Frontend Bypass
```bash
# These should all work without authentication
curl -I https://app.fa.pesulabs.net/
curl -I https://app.fa.pesulabs.net/chat
```

### Test API Bypass
```bash
# This should work with automatic authentication headers
curl -X POST https://app.fa.pesulabs.net/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello test"}]}'
```

### Test Analytics (when implemented)
```bash
# Should work once analytics routes are implemented
curl -X GET https://app.fa.pesulabs.net/api/v1/analytics/sub-agents/overview
```

## Troubleshooting

### Analytics API Returns 404
- **Cause**: Analytics routes may not be implemented in current version
- **Solution**: Check if analytics feature is included in the current API image version

### Authentication Still Required
- **Cause**: JWT token may have expired
- **Solution**: Generate new token using `/tmp/create_jwt.py` and update nginx config

### Frontend Still Redirects to Login
- **Cause**: React app may need rebuild
- **Solution**: Rebuild React app and redeploy to Kubernetes

## Notes for Future Development

1. **Database Users**: For proper authentication, create users in the database with appropriate roles
2. **JWT Implementation**: Consider implementing proper JWT authentication flow for development
3. **Environment Variables**: Consider adding proper DISABLE_AUTH support to the backend code
4. **SSL Certificate**: Renew SSL certificates after rate limit reset (Dec 2, 2025)

---

**Created**: November 30, 2025
**Purpose**: Temporary authentication bypass for development testing
**Revert**: After SSL certificate rate limit is resolved