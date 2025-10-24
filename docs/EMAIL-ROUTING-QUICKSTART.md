# Quick Start: Cloudflare Email Routing

**Goal**: Set up gonzalo.iglesias@pesulabs.net → giglesias@gmail.com

**Time**: 5 minutes

---

## Step-by-Step Instructions

### 1. Login to Cloudflare Dashboard

**URL**: https://dash.cloudflare.com

1. Login with your Cloudflare credentials
2. Click on **pesulabs.net** domain

---

### 2. Enable Email Routing

1. In the left sidebar, click **Email**
2. Click **Email Routing**
3. Click **Get started** (or **Enable Email Routing**)
4. Cloudflare will show a status message: "Configuring DNS records..."
5. Wait for "✅ Email Routing is ready" (1-2 minutes)

**What happened**: Cloudflare added MX records automatically

---

### 3. Add Your Gmail as Destination

1. Look for **Destination addresses** section
2. Click **Add destination address**
3. Enter: `giglesias@gmail.com`
4. Click **Send verification email**

**Now**: Check your Gmail inbox

5. Open email from Cloudflare (subject: "Verify your email for Cloudflare Email Routing")
6. Click the **Verify** button/link
7. Return to Cloudflare dashboard
8. Refresh - should show "✅ Verified" next to giglesias@gmail.com

---

### 4. Create Email Forwarding Rule

1. Look for **Routing rules** section (or tab)
2. Click **Create address** or **Add rule**
3. Fill in:
   - **Type**: Custom address
   - **Email address**: `gonzalo.iglesias`
   - **Domain**: `@pesulabs.net` (should be pre-filled)
   - **Action**: Send to
   - **Destination**: `giglesias@gmail.com`

4. Click **Save** or **Create**

**Result**: Should see rule listed as "Active"

```
gonzalo.iglesias@pesulabs.net → giglesias@gmail.com [Active]
```

---

### 5. Test It!

**Option A - Send from another email**:
1. Use any other email account (not Gmail)
2. Send email to: `gonzalo.iglesias@pesulabs.net`
3. Check `giglesias@gmail.com` inbox
4. Should arrive in seconds

**Option B - Send from Gmail**:
1. Compose new email in Gmail
2. To: `gonzalo.iglesias@pesulabs.net`
3. From: Use a different email or alias
4. Send
5. Check if it arrives (might take 1-2 minutes)

---

## That's It! ✅

Your email forwarding is now active:
- **gonzalo.iglesias@pesulabs.net** → **giglesias@gmail.com**

---

## What You Can Do Now

### Add More Email Addresses

Repeat Step 4 for:
- `admin@pesulabs.net`
- `alerts@pesulabs.net`
- `contact@pesulabs.net`
- `n8n@pesulabs.net`

All can forward to the same giglesias@gmail.com

### Send Emails FROM Your Domain

In Gmail:
1. Settings (⚙️) → **See all settings**
2. **Accounts and Import** tab
3. **Send mail as** → Click **Add another email address**
4. Fill in:
   - Name: Gonzalo Iglesias
   - Email: gonzalo.iglesias@pesulabs.net
   - ✅ Treat as an alias
5. Click **Next Step** → **Send verification**
6. Check Gmail for verification code
7. Enter code
8. **Done!** You can now send as gonzalo.iglesias@pesulabs.net

---

## Troubleshooting

**Email not arriving?**
- Check Gmail **Spam** folder
- Check Cloudflare Email Routing → **Activity** tab
- Wait 5 minutes (DNS propagation)

**Can't verify giglesias@gmail.com?**
- Check spam folder for Cloudflare email
- Try adding again
- Make sure you have access to that Gmail account

**Rule not working?**
- Make sure destination is "Verified"
- Make sure rule shows "Active"
- Check for typos in email address

---

## Quick Check Commands

```bash
# Verify MX records are set up (wait 5 mins after enabling)
dig MX pesulabs.net

# Should show:
# pesulabs.net. IN MX 1 route1.mx.cloudflare.net.
# pesulabs.net. IN MX 2 route2.mx.cloudflare.net.
# pesulabs.net. IN MX 3 route3.mx.cloudflare.net.
```

---

**Need help?** Check the full guide: `docs/EMAIL-ROUTING-SETUP.md`
