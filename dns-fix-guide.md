# DNS Configuration for NodePort Access

## Current Setup
- Your DNS correctly resolves homelab.pesulabs.net to 100.81.76.55
- Traefik NodePort: HTTP=31365, HTTPS=31773
- Services work on http://100.81.76.55:30080 (direct NodePort)

## Recommended DNS Configuration

### Option 1: Use Direct NodePort in DNS
Update your DNS records to include port numbers:
```
dash.pesulabs.net     A   100.81.76.55
n8n.homelab.pesulabs.net  A   100.81.76.55
```

Then access via:
- https://dash.pesulabs.net:30443
- https://n8n.homelab.pesulabs.net:30443

### Option 2: Use Reverse Proxy
Set up nginx/apache as reverse proxy on port 80/443 forwarding to NodePorts

### Option 3: Use Port Forwarding
For development:
```bash
kubectl port-forward -n homelab svc/traefik 80:80 443:443
```

## Testing
```bash
# Test NodePort access
curl -I http://100.81.76.55:31365
curl -I https://100.81.76.55:31773 -k

# Test with hostname
curl -I http://dash.pesulabs.net:31365
```