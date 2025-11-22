# Authentik OIDC Configuration for Family Assistant

## Issue
The family-assistant app is getting "Client authentication failed" error when trying to exchange the authorization code for tokens.

## Root Cause
The Authentik OAuth2/OpenID Provider for family-assistant is configured as a **Confidential Client** (requiring client secret), but it should be configured as a **Public Client** since it's a Single Page Application (SPA) running in the browser.

## Solution

### Step 1: Access Authentik Admin Interface

1. Navigate to https://auth.pesulabs.net/if/admin/
2. Log in with your admin credentials

### Step 2: Configure the OAuth2/OpenID Provider

1. Go to **Applications** → **Providers**
2. Find the provider for "family-assistant" (or create a new one if it doesn't exist)
3. Click **Edit** on the provider

### Step 3: Required Provider Settings

Configure the provider with these settings:

#### Basic Settings
- **Name**: `family-assistant-provider` (or your preferred name)
- **Authorization flow**: `default-provider-authorization-implicit-consent`
- **Protocol settings**: `OAuth2/OIDC`

#### Client Settings (CRITICAL)
- **Client Type**: Select **"Public"** (not Confidential)
  - This is the key setting! Public clients don't require client secrets
- **Client ID**: `tw2kzde62QPl0dzYhY6YR9vjEQ4GYHcJ4KIa7fbD` (already configured in app)
- **Client Secret**: Leave empty or remove (not used for public clients)

#### Redirect URIs
Add these redirect URIs (one per line):
```
https://app.fa.pesulabs.net/auth/callback
https://app.fa.pesulabs.net
http://localhost:5173/auth/callback
http://localhost:5173
```

#### Scopes
Ensure these scopes are included:
- `openid`
- `profile`
- `email`

#### Advanced Settings
- **Subject mode**: `Based on the User's hashed ID`
- **Include claims in id_token**: ✓ (checked)
- **Token validity**: `minutes=10` (or your preference)
- **Signing Key**: `authentik Self-signed Certificate` (or your certificate)

#### PKCE Settings
- **PKCE**: Should be automatically enabled for public clients
- No additional configuration needed

### Step 4: Configure the Application

1. Go to **Applications** → **Applications**
2. Find or create the "Family Assistant" application
3. Edit the application:
   - **Name**: `Family Assistant`
   - **Slug**: `family-assistant`
   - **Provider**: Select the provider configured above
   - **Launch URL**: `https://app.fa.pesulabs.net`

### Step 5: Test the Configuration

After making these changes:

1. Clear browser cache and localStorage for https://app.fa.pesulabs.net
2. Navigate to https://app.fa.pesulabs.net
3. Click login
4. You should be redirected to Authentik
5. After authentication, you should be redirected back to the app

### Step 6: Verify OIDC Discovery

Test that the OIDC discovery endpoint is accessible:

```bash
curl https://auth.pesulabs.net/application/o/family-assistant/.well-known/openid-configuration
```

Should return a JSON response with configuration details.

### Troubleshooting

#### Still getting "Client authentication failed"
- Verify "Client Type" is set to **"Public"** in the provider settings
- Ensure there's no client secret configured
- Clear browser cache and localStorage
- Check that redirect URIs exactly match (including trailing slashes)

#### CORS errors
- Already fixed with the CORS middleware
- Verify the middleware is applied to the Authentik ingress

#### Token exchange errors
- Check Authentik logs: `kubectl logs -n authentik deployment/authentik-server`
- Verify the authorization code is being sent correctly
- Ensure PKCE code_verifier is being included in the token request

### Current Configuration

The family-assistant app (auth.ts) is configured with:
- **Authority**: `https://auth.pesulabs.net/application/o/family-assistant/`
- **Client ID**: `tw2kzde62QPl0dzYhY6YR9vjEQ4GYHcJ4KIa7fbD`
- **Redirect URI**: `https://app.fa.pesulabs.net/auth/callback`
- **Response Type**: `code` (Authorization Code Flow)
- **PKCE**: Enabled automatically by oidc-client-ts

This configuration expects a **Public Client** provider in Authentik.

## References

- [Authentik OAuth2/OpenID Provider Documentation](https://goauthentik.io/docs/providers/oauth2/)
- [PKCE RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636)
- [oidc-client-ts Documentation](https://github.com/authts/oidc-client-ts)
