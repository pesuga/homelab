# Authentik Provider Configuration Check

## Critical Provider Settings to Verify

### Step 1: Check Provider Configuration

1. **Go to Authentik Admin UI** → `https://auth.pesulabs.net`
2. Navigate to: **Applications** → **Providers**
3. Click on your **Family Admin Provider**

### Step 2: Verify These Exact Settings

Look for these fields and verify the values:

#### Required Settings:

**1. Type:**
- Must be: `Proxy Provider`

**2. Mode:** (CRITICAL - This is likely the issue)
- Should be: **`Forward auth (single application)`**
- NOT: `Proxy`
- NOT: `Forward auth (domain level)`

**3. External host:**
- Must be: `https://admin.fa.pesulabs.net`
- No trailing slash
- Must include `https://`

**4. Authorization flow:**
- Should be: `default-provider-authorization-implicit-consent`

**5. Internal host:**
- Leave empty (or set to: `http://family-admin.homelab.svc.cluster.local:3000`)

**6. Intercept header authentication:**
- Should be: Unchecked (disabled)

**7. Token validity:**
- Default: `hours=24`

### Step 3: Report Back

Please check the **Mode** field and tell me which option is currently selected:

```
Mode: _________________________
```

Options you might see:
- [ ] Proxy
- [ ] Forward auth (single application)  ← Should be THIS ONE
- [ ] Forward auth (domain level)

## Why This Matters

The "Mode" setting determines how Authentik handles authentication:

- **Proxy**: Traditional reverse proxy (Authentik sits in front of app)
- **Forward auth (single application)**: Uses ForwardAuth for a single app (what we need)
- **Forward auth (domain level)**: Uses ForwardAuth for multiple apps on same domain

If it's NOT set to "Forward auth (single application)", that's why the ForwardAuth endpoint returns 404.

## Next Steps After Fixing

Once you change the Mode to "Forward auth (single application)":

1. Click **Update** to save the provider
2. Go to **Applications** → **Outposts** → **authentik Embedded Outpost**
3. Make sure **Family Admin** application is in the Applications list
4. Click **Update**
5. Optionally restart the outpost (⋮ menu → Restart)

Then test:
```bash
curl -I https://admin.fa.pesulabs.net
```

You should get redirected to Authentik for login.