# Tailscale Subdomain Configuration Guide

## Overview

This guide explains how to enable subdomain-based access to your Kubernetes applications using Tailscale. Instead of accessing services via path-based routing (e.g., `asuna.chimp-ulmer.ts.net/immich`), you'll be able to use subdomains (e.g., `immich.yourdomain.com`).

This approach offers several advantages:
- Cleaner URLs for your applications
- Avoiding path-based routing complexities
- Better application compatibility (many apps work better with root paths)

## Prerequisites

- A domain you own (registered with a provider like Cloudflare, Namecheap, etc.)
- Tailscale set up on your Kubernetes cluster
- External-DNS and NGINX Ingress Controller (from our previous setup)

## Implementation Steps

### 1. Configure MagicDNS in Tailscale

1. Log in to the Tailscale admin console: https://login.tailscale.com/admin
2. Navigate to the "DNS" settings
3. Enable "MagicDNS" if not already enabled
   - This allows your Tailscale nodes to be addressable by hostname

### 2. Set Up CNAME Records at Your DNS Provider

1. Log in to your DNS provider (e.g., Cloudflare)
2. Create a wildcard CNAME record:
   - Type: `CNAME`
   - Name: `*.yourdomain.com` (or use a specific subdomain like `*.apps.yourdomain.com`)
   - Target: `asuna.chimp-ulmer.ts.net` (your Tailscale node's MagicDNS name)
   - Proxy status: DNS Only (don't proxy through Cloudflare)
   - TTL: Auto
3. Optionally, create individual CNAME records for specific applications:
   - Type: `CNAME`
   - Name: `immich.yourdomain.com`
   - Target: `asuna.chimp-ulmer.ts.net`
   - Proxy status: DNS Only
   - TTL: Auto

### 3. Configure External-DNS for Subdomain Management

Update your external-dns configuration to work with your domain:

```yaml
# In clusters/homelab/apps/external-dns/release.yaml
spec:
  values:
    provider: cloudflare  # Or your DNS provider
    domainFilters:
      - "yourdomain.com"  # Your actual domain
    policy: sync
    sources:
      - ingress
```

### 4. Update Ingress Resources for Subdomain Routing

Update your application's Ingress resources to use subdomain-based routing:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: immich-web-ingress
  namespace: immich
  annotations:
    kubernetes.io/ingress.class: "nginx"
    # Remove any path-based rewrite annotations
spec:
  rules:
  - host: immich.yourdomain.com  # Use your subdomain
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: immich-web
            port:
              number: 3000
  # Add additional rules for the API if needed
  - host: immich.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: immich-server
            port:
              number: 3001
```

### 5. Configure TLS Certificates (Optional but Recommended)

For secure HTTPS connections, set up cert-manager to automatically provision certificates:

1. Install cert-manager (to be detailed in a separate guide)
2. Configure a ClusterIssuer for your domain
3. Add TLS configuration to your Ingress resources

## Testing Your Configuration

Once configured, you should be able to access your applications using subdomains:

```
https://immich.yourdomain.com
https://nextapp.yourdomain.com
```

## Troubleshooting

- **DNS Resolution Issues**: Ensure your CNAME records are correctly set up
- **Certificate Errors**: Check cert-manager logs if using HTTPS
- **Application Access Problems**: Review your Ingress resources and NGINX controller logs

## Additional Resources

- [Tailscale MagicDNS Documentation](https://tailscale.com/kb/1081/magicdns)
- [External-DNS with Kubernetes](https://github.com/kubernetes-sigs/external-dns)
- [Cloudflare DNS Documentation](https://developers.cloudflare.com/dns/)
