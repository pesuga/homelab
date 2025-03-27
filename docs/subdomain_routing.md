# Subdomain Routing Configuration

This document provides information about the subdomain-based routing setup in the homelab environment.

## Overview

All services in the homelab are configured to use subdomain-based routing (e.g., `service.app.pesulabs.net`) rather than path-based routing (e.g., `app.pesulabs.net/service`). This approach provides several benefits:

- Cleaner URLs for each service
- Better isolation between services
- Simplified configuration for services that don't support path-based routing
- Improved security through domain separation

## Components

The subdomain routing setup consists of the following components:

1. **NGINX Ingress Controller**: Handles incoming HTTP/HTTPS traffic
2. **External-DNS**: Manages DNS records in Cloudflare
3. **Cert-Manager**: Manages SSL certificates for each subdomain

## Prerequisites

- Kubernetes cluster with Flux CD
- Cloudflare account with control over your domain (pesulabs.net)
- Cloudflare API token with permissions for DNS management

## Setup Process

### Step 1: Create a Cloudflare API Token

1. Log in to your Cloudflare account
2. Go to your profile (click on your email in the top right)
3. Select "API Tokens"
4. Click "Create Token"
5. Choose the "Edit zone DNS" template or create a custom token with:
   - Zone > DNS > Edit
   - Zone > Zone > Read
   - Include specific zone: pesulabs.net
6. Copy the token value

### Step 2: Set up Cloudflare Token in Kubernetes

Run the setup script:

```bash
./scripts/setup-cloudflare-token.sh YOUR_CLOUDFLARE_API_TOKEN
```

This will update the kustomization files with your token.

### Step 3: Apply Configuration

Apply the kustomization files directly:

```bash
kubectl apply -k /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/
kubectl apply -k /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/cert-manager/
```

### Step 4: Verify Setup

1. Check if external-dns is running:
   ```bash
   k get pods -n external-dns
   ```

2. Check if DNS records are being created:
   ```bash
   k logs -n external-dns $(k get pods -n external-dns -o name)
   ```

## Service URLs

| Service | URL | Description |
| --- | --- | --- |
| Immich | https://immich.app.pesulabs.net | Photo & video backup |
| Home Assistant | https://home-assistant.app.pesulabs.net | Home automation |
| N8N | https://n8n.app.pesulabs.net | Workflow automation |
| OwnCloud | https://owncloud.app.pesulabs.net | File storage |
| Grafana | https://grafana.app.pesulabs.net | Monitoring dashboards |
| Prometheus | https://prometheus.app.pesulabs.net | Metrics database |
| Glance | https://glance.app.pesulabs.net | Service dashboard |
| Qdrant | https://qdrant.app.pesulabs.net | Vector database |

## Configuration

### Ingress Configuration

Each service has its own Ingress resource that defines the subdomain routing. Example:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: immich
  namespace: immich
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    kubernetes.io/ingress.class: nginx
spec:
  tls:
  - hosts:
    - immich.app.pesulabs.net
    secretName: immich-tls
  rules:
  - host: immich.app.pesulabs.net
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: immich-server
            port:
              number: 2283
```

### DNS Configuration

DNS records are managed through:

1. **External-DNS**: Automatically creates DNS records in Cloudflare for services with Ingress resources
2. **Manual DNS**: For local network access, DNS records can be added manually using the `scripts/add-manual-dns-records.sh` script

### SSL Certificates

SSL certificates are managed by Cert-Manager using Let's Encrypt. For local-only access, self-signed certificates are used.

## Troubleshooting

### Common Issues

#### Service Not Accessible via Subdomain

If a service is not accessible via its subdomain:

1. Check the Ingress resource: `k get ingress -n <namespace>`
2. Verify DNS resolution: `nslookup <service>.app.pesulabs.net`
3. Check NGINX Ingress logs: `k logs -n kube-system -l app=nginx-ingress-controller`
4. Verify the service is running: `k get pods -n <namespace>`

#### SSL Certificate Issues

If there are SSL certificate issues:

1. Check Cert-Manager logs: `k logs -n cert-manager -l app=cert-manager`
2. Verify certificate status: `k get certificate -n <namespace>`
3. Check certificate request status: `k get certificaterequest -n <namespace>`

#### External-DNS Issues

If external-dns is not creating DNS records:

1. Check external-dns logs: `k logs -n external-dns -l app=external-dns`
2. Verify Cloudflare API token permissions
3. Check if the ingress resources have the correct annotations

## Secure Access

For secure access to services:

1. **Local Network**: Services are accessible directly via their subdomains on the local network
2. **Remote Access**: Use Tailscale for secure remote access (see `docs/tailscale_secure_access.md`)

## Mobile Access

For mobile access to services:

1. Connect to your home network or use Tailscale on your mobile device
2. Access services via their subdomains
3. For specific mobile apps (like Immich), configure the app to use the service's subdomain
