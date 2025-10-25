# Cloudflare Email Routing Setup for pesulabs.net

**Date**: 2025-10-24
**Domain**: pesulabs.net
**Provider**: Cloudflare Email Routing (Free)
**Status**: 🔄 In Progress

---

## Overview

Setting up Cloudflare Email Routing to receive emails at pesulabs.net domain and forward them to personal email addresses.

### Configuration
- **Domain**: pesulabs.net
- **Primary Email**: gonzalo.iglesias@pesulabs.net → giglesias@gmail.com
- **Type**: Receive-only (forwarding)
- **Cost**: Free

---

## Step 1: Enable Email Routing in Cloudflare

### Manual Steps in Cloudflare Dashboard:

1. **Login to Cloudflare**:
   - Go to https://dash.cloudflare.com
   - Select your account

2. **Navigate to pesulabs.net**:
   - Click on the pesulabs.net domain

3. **Access Email Routing**:
   - In the left sidebar, find "Email" section
   - Click on "Email Routing"

4. **Enable Email Routing**:
   - Click "Get started" or "Enable Email Routing"
   - Cloudflare will automatically configure DNS records
   - Wait for DNS propagation (usually 1-5 minutes)

### Expected DNS Records

Cloudflare will automatically add these MX records:

```
Type: MX
Name: @
Priority: 1
Value: route1.mx.cloudflare.net

Type: MX
Name: @
Priority: 2
Value: route2.mx.cloudflare.net

Type: MX
Name: @
Priority: 3
Value: route3.mx.cloudflare.net

Type: TXT
Name: @
Value: v=spf1 include:_spf.mx.cloudflare.net ~all
```

---

## Step 2: Add Destination Email Address

### Manual Steps:

1. **Add Destination**:
   - In Email Routing dashboard, go to "Destination addresses"
   - Click "Add destination address"
   - Enter: `giglesias@gmail.com`
   - Click "Send verification email"

2. **Verify Email**:
   - Check your Gmail inbox (giglesias@gmail.com)
   - Look for email from Cloudflare
   - Click the verification link
   - Email will show as "Verified" in Cloudflare dashboard

---

## Step 3: Create Forwarding Rule

### Manual Steps:

1. **Create Custom Address**:
   - Go to "Routing rules" tab
   - Click "Create address" or "Add rule"
   - Choose "Custom address"

2. **Configure Rule**:
   ```
   Type: Custom address
   Email address: gonzalo.iglesias@pesulabs.net
   Action: Forward to
   Destination: giglesias@gmail.com
   ```

3. **Save Rule**:
   - Click "Save" or "Create"
   - Rule should show as "Active"

---

## Step 4: Test Email Forwarding

### Testing Methods:

**Method 1: Use Another Email Account**
1. From another email (not Gmail), send a test email to:
   - To: `gonzalo.iglesias@pesulabs.net`
   - Subject: Test Email Routing
   - Body: Testing Cloudflare Email Routing

2. Check giglesias@gmail.com inbox
3. Email should arrive within seconds/minutes

**Method 2: Use Online Service**
1. Visit: https://www.mail-tester.com
2. Send test email to the provided address
3. Forward that email to gonzalo.iglesias@pesulabs.net
4. Check deliverability score

**Method 3: Command Line**
```bash
# Send test email using sendmail (if available)
echo "Subject: Test Email Routing
From: test@example.com
To: gonzalo.iglesias@pesulabs.net

This is a test email." | sendmail -t
```

---

## Step 5: Verify and Monitor

### Check Email Routing Status:

1. **In Cloudflare Dashboard**:
   - Go to Email → Email Routing
   - Check "Status" shows "Active"
   - View "Activity log" for recent emails

2. **Verify DNS Propagation**:
   ```bash
   # Check MX records
   dig MX pesulabs.net

   # Should show:
   # pesulabs.net. IN MX 1 route1.mx.cloudflare.net.
   # pesulabs.net. IN MX 2 route2.mx.cloudflare.net.
   # pesulabs.net. IN MX 3 route3.mx.cloudflare.net.
   ```

3. **Check SPF Record**:
   ```bash
   dig TXT pesulabs.net

   # Should include:
   # v=spf1 include:_spf.mx.cloudflare.net ~all
   ```

---

## Additional Email Addresses (Future)

Once the first address is working, you can add more:

### Recommended Addresses:

```
admin@pesulabs.net → giglesias@gmail.com
alerts@pesulabs.net → giglesias@gmail.com
n8n@pesulabs.net → giglesias@gmail.com
noreply@pesulabs.net → giglesias@gmail.com
contact@pesulabs.net → giglesias@gmail.com
```

### Catch-All (Optional):

Forward ALL emails to your Gmail:
```
Type: Catch-all address
Pattern: *@pesulabs.net
Action: Forward to
Destination: giglesias@gmail.com
```

**Warning**: Catch-all may increase spam. Use with caution.

---

## Integration with Homelab Services

### N8n Workflows

Once email routing is working, you can:

1. **Send Emails FROM N8n**:
   - Use Gmail node with "Send As" feature
   - Or use SendGrid/Mailgun for automated emails

2. **Receive Emails in N8n**:
   - Forward to a webhook URL
   - Or use Gmail node to poll giglesias@gmail.com

### Grafana Alerts

Configure Grafana to send alerts to:
```
alerts@pesulabs.net → giglesias@gmail.com
```

In Grafana:
1. Settings → Alerting → Contact points
2. Add email: alerts@pesulabs.net
3. Test notification

### System Notifications

Configure services to send emails:
```bash
# In service configs
ALERT_EMAIL=alerts@pesulabs.net
ADMIN_EMAIL=gonzalo.iglesias@pesulabs.net
```

---

## Sending Emails FROM Your Domain

Cloudflare Email Routing is **receive-only**. To send:

### Option 1: Gmail "Send As" (Free)

1. **In Gmail Settings**:
   - Settings → Accounts and Import
   - "Send mail as" → Add another email address
   - Email: gonzalo.iglesias@pesulabs.net
   - Name: Gonzalo Iglesias
   - Use Gmail's SMTP server

2. **Result**:
   - Emails appear from gonzalo.iglesias@pesulabs.net
   - Actually sent through Gmail
   - Recipients see pesulabs.net address

### Option 2: SendGrid/Mailgun (For Automation)

**SendGrid** (100 emails/day free):
1. Sign up at sendgrid.com
2. Verify domain pesulabs.net
3. Add DNS records (DKIM, SPF)
4. Use API key in N8n workflows

**Mailgun** (5,000 emails/month free):
1. Sign up at mailgun.com
2. Add domain pesulabs.net
3. Configure DNS records
4. Use API for sending

### Option 3: Cloudflare Email Workers (Paid)

- Cost: ~$5/month
- Full programmatic sending
- Use MailChannels API
- Good for high-volume automation

---

## DNS Records Summary

After setup, your pesulabs.net DNS should have:

```dns
# MX Records (Mail routing)
MX  @  route1.mx.cloudflare.net  Priority: 1
MX  @  route2.mx.cloudflare.net  Priority: 2
MX  @  route3.mx.cloudflare.net  Priority: 3

# SPF Record (Sender verification)
TXT @  v=spf1 include:_spf.mx.cloudflare.net ~all

# DMARC Record (Email authentication - optional but recommended)
TXT _dmarc  v=DMARC1; p=quarantine; rua=mailto:gonzalo.iglesias@pesulabs.net

# Existing records
A   @         Your-IP
TXT @         Tailscale verification (if present)
CNAME *       pesulabs.net (for wildcard)
```

---

## Troubleshooting

### Email Not Arriving

1. **Check Cloudflare Activity Log**:
   - Email → Email Routing → Activity
   - Look for rejected/failed emails

2. **Check Gmail Spam Folder**:
   - Emails might be marked as spam initially
   - Mark as "Not Spam" to train filter

3. **Verify DNS Propagation**:
   ```bash
   dig MX pesulabs.net
   dig TXT pesulabs.net
   ```
   Wait up to 24 hours for full propagation

4. **Check Destination Email Status**:
   - Ensure giglesias@gmail.com is verified in Cloudflare
   - Re-verify if needed

### Emails Going to Spam

1. **Add DMARC Record**:
   ```
   Type: TXT
   Name: _dmarc
   Value: v=DMARC1; p=quarantine; rua=mailto:gonzalo.iglesias@pesulabs.net
   ```

2. **Add to Gmail Contacts**:
   - Add gonzalo.iglesias@pesulabs.net to Gmail contacts
   - Prevents future emails from being marked as spam

3. **Set Up SPF/DKIM** (if sending):
   - Required for outbound emails
   - Provider-specific (SendGrid, Mailgun, etc.)

---

## Security Considerations

1. **No Sensitive Data**:
   - Email is forwarded through Cloudflare
   - Use for non-sensitive communications

2. **Spam Protection**:
   - Cloudflare provides basic spam filtering
   - Additional filtering in Gmail

3. **Rate Limits**:
   - Cloudflare Email Routing has generous limits
   - Unlimited incoming emails (within reason)

4. **Privacy**:
   - Cloudflare can see email metadata
   - Use end-to-end encryption for sensitive content

---

## Monitoring

### Cloudflare Dashboard

- Check "Activity" tab regularly
- Monitor for rejected emails
- Review spam patterns

### Gmail Filters (Optional)

Create Gmail filter for pesulabs.net emails:
1. Gmail → Settings → Filters
2. Create filter:
   - To: gonzalo.iglesias@pesulabs.net
   - Action: Apply label "Pesulabs"
   - Action: Never send to Spam
   - Action: Mark as important

---

## Cost Summary

| Service | Cost | Purpose |
|---------|------|---------|
| Cloudflare Email Routing | **Free** | Receive & forward emails |
| Gmail (existing) | **Free** | Personal mailbox |
| SendGrid (optional) | Free tier | Send automated emails (100/day) |
| Mailgun (optional) | Free tier | Send automated emails (5000/month) |

**Total Cost: $0/month** for basic email forwarding

---

## Next Steps

1. ✅ Enable Email Routing in Cloudflare
2. ✅ Verify giglesias@gmail.com
3. ✅ Create gonzalo.iglesias@pesulabs.net forwarding rule
4. ⏳ Test email forwarding
5. ⏳ Add additional email addresses (admin@, alerts@, etc.)
6. ⏳ Configure Gmail "Send As" for sending
7. ⏳ Integrate with N8n workflows
8. ⏳ Set up Grafana alerts

---

## Commands Reference

```bash
# Check MX records
dig MX pesulabs.net

# Check all DNS records
dig ANY pesulabs.net

# Check SPF record
dig TXT pesulabs.net | grep spf

# Test email delivery from command line
echo -e "Subject: Test\n\nTest email" | sendmail gonzalo.iglesias@pesulabs.net

# Check email headers (after receiving)
# In Gmail: More → Show original → View headers
```

---

## Support

- **Cloudflare Docs**: https://developers.cloudflare.com/email-routing/
- **Status Page**: https://www.cloudflarestatus.com/
- **Community**: https://community.cloudflare.com/

---

**Status**: Ready to configure in Cloudflare dashboard
**Expected Time**: 5-10 minutes
**Verification Time**: 1-5 minutes (DNS propagation)
