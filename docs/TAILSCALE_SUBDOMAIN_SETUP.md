# Tailscale Subdomain Configuration Guide

## Prerequisites
- Tailscale account with admin access
- A domain you own (e.g., yourdomain.com)
- Cloudflare account (or other DNS provider)

## Steps to Enable Subdomain Support in Tailscale

### 1. Configure a Custom Domain in Tailscale

1. Log in to the Tailscale admin console: https://login.tailscale.com/admin
2. Navigate to "DNS" settings
3. Under "HTTPS Certificates", click "Add domain"
4. Enter your domain (e.g., yourdomain.com)
5. Follow the verification instructions (usually involves adding TXT records to your DNS)

### 2. Configure MagicDNS

1. In the Tailscale admin console, go to "DNS" settings
2. Enable "MagicDNS"
3. This will allow your Tailscale nodes to be addressable by hostname

### 3. Add a Nameserver at Your Domain Registrar

1. Log in to your domain registrar
2. Find the DNS settings or nameserver settings
3. Add the Tailscale nameservers provided in the Tailscale admin console
   - ns1.tailscale.net
   - ns2.tailscale.net

### A Note on Wildcard Domains for Kubernetes Ingress

For your Kubernetes cluster to use subdomains (e.g., app1.yourdomain.com, app2.yourdomain.com), you'll need to:

1. Make sure the Tailscale nameservers are authoritative for your domain
2. Configure your applications to use the subdomain hostnames in their Ingress resources
3. Ensure external-dns is properly configured to update the DNS records

## Testing Your Configuration

Once configured, you should be able to access your applications using subdomains:

```
https://app1.yourdomain.com
https://app2.yourdomain.com
```

## Troubleshooting

- If DNS resolution doesn't work, verify that Tailscale nameservers are correctly configured
- Check that MagicDNS is enabled in your Tailscale account
- Ensure your Ingress resources are correctly configured with the proper hostname
- Verify external-dns logs to ensure DNS records are being created/updated

Remember that DNS changes can take time to propagate (up to 24 hours, though usually much less).
