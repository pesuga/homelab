# Fix Authentik Public Client Configuration

## Current Problem

The Authentik logs show:
```
"auth_via": "oauth_client_secret"
"event": "Invalid client secret"
```

This confirms that the Authentik provider is configured as a **Confidential Client** and is expecting a client secret, but the family-assistant app (a browser-based SPA) cannot securely store client secrets.

## Solution: Configure as Public Client

### Step 1: Access Authentik Admin Panel

1. Open your browser and navigate to: **https://auth.pesulabs.net/if/admin/**
2. Log in with your Authentik admin credentials

### Step 2: Navigate to Providers

1. In the left sidebar, click **Applications**
2. Click on **Providers** (it should be highlighted or visible in the submenu)
3. You should see a list of OAuth2/OpenID providers

### Step 3: Find and Edit the Family Assistant Provider

1. Look for a provider with:
   - **Name**: Something like "family-assistant-provider" or "family-assistant"
   - **Client ID**: `tw2kzde62QPl0dzYhY6YR9vjEQ4GYHcJ4KIa7fbD`

2. Click on the provider name or the **Edit** button (pencil icon)

### Step 4: Change Client Type to Public

In the provider edit form, find these settings:

#### Critical Setting: Client Type
- **Current value**: Likely "Confidential"
- **Change to**: **"Public"**
- **Location**: Usually in the "Protocol settings" or "Client settings" section

#### Other Important Settings to Verify:

**Authorization Flow**:
- Set to: `default-provider-authorization-implicit-consent`

**Redirect URIs** (must match exactly):
```
https://app.fa.pesulabs.net/auth/callback
https://app.fa.pesulabs.net
http://localhost:5173/auth/callback (for development)
```

**Client ID**:
```
tw2kzde62QPl0dzYhY6YR9vjEQ4GYHcJ4KIa7fbD
```
(Should already be set - don't change this)

**Client Secret**:
- For **Public clients**, this should be:
  - Empty/blank, OR
  - Automatically generated but not required for authentication
- If there's a checkbox like "Require client secret" → **Uncheck it**

**Scopes** (under "Advanced protocol settings" or similar):
- Ensure these are selected:
  - `openid`
  - `profile`
  - `email`

### Step 5: Save and Verify

1. Click **Save** or **Update** at the bottom of the form
2. Verify your changes were saved by refreshing the page and checking the Client Type is still "Public"

### Step 6: Test the Authentication Flow

1. **Clear browser data** for https://app.fa.pesulabs.net:
   - Open Developer Tools (F12)
   - Go to Application → Storage → Clear site data
   - Or use Incognito/Private mode

2. **Navigate to the app**: https://app.fa.pesulabs.net

3. **Try logging in**:
   - You should be redirected to Authentik
   - After logging in, you should be redirected back successfully
   - No "Client authentication failed" error should appear

### Step 7: Verify in Logs

After testing, check Authentik logs to confirm proper authentication:

```bash
kubectl logs -n authentik deployment/authentik-server --tail=50 | grep -i token
```

You should see successful token exchanges instead of "Invalid client secret" errors.

## Troubleshooting

### If you still get "Client authentication failed":

1. **Double-check Client Type**:
   - Go back to the provider settings
   - Verify "Client Type" is set to **"Public"** (not "Confidential")
   - Some Authentik versions may have different labels:
     - "Public client" vs "Confidential client"
     - A checkbox for "Is confidential client" (should be unchecked)

2. **Check for Client Authentication Method**:
   - Look for a setting called "Token endpoint auth method" or similar
   - For public clients, this should be:
     - "none" OR
     - "client_secret_post" with an option to not require it OR
     - Simply not configured

3. **Verify PKCE Support**:
   - Ensure PKCE is enabled or allowed
   - Some Authentik versions require explicit PKCE configuration
   - Look for "PKCE" or "Code Challenge Method" settings
   - Should support `S256` (SHA-256)

### If the provider doesn't have a "Public" client type option:

Some older Authentik versions might handle this differently:

1. **Check Authentik Version**:
   ```bash
   kubectl get deployment -n authentik authentik-server -o jsonpath='{.spec.template.spec.containers[0].image}'
   ```

2. **Look for alternative settings**:
   - "Client authentication" → Set to "None" or disable
   - "Require client authentication" → Uncheck
   - "Token endpoint authentication" → "None"

### Still having issues?

Check the complete Authentik provider configuration:

```bash
# Get a shell in the Authentik pod
kubectl exec -it -n authentik deployment/authentik-server -- bash

# Check the provider configuration in the database
# (This requires database access - be careful!)
```

Or check Authentik documentation for your specific version:
- Version 2024.2.1 documentation: https://docs.goauthentik.io/docs/providers/oauth2/

## Expected Behavior After Fix

Once configured correctly as a Public client:

1. **Authorization flow**:
   - User clicks "Login" → Redirected to Authentik
   - User authenticates → Redirected back with authorization code
   - App exchanges code for token **without client secret**
   - App uses PKCE code_verifier for security

2. **Authentik logs should show**:
   ```
   "auth_via": "none" (or similar - NOT "oauth_client_secret")
   "event": "Token issued successfully"
   ```

3. **No errors in browser console**

## Reference: Current Configuration

**App Configuration** (already correct):
- Authority: `https://auth.pesulabs.net/application/o/family-assistant/`
- Client ID: `tw2kzde62QPl0dzYhY6YR9vjEQ4GYHcJ4KIa7fbD`
- Response Type: `code` (Authorization Code Flow)
- PKCE: Enabled (automatic in oidc-client-ts)
- Scopes: `openid profile email`

**What needs to be changed** (in Authentik):
- ✅ CORS: Already fixed
- ❌ Client Type: Needs to be changed to "Public"
- ❌ Client Secret: Should not be required for authentication
