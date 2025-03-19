# Secure Remote Access with Tailscale

This document outlines how to configure Tailscale for secure remote access to your homelab services.

## Overview

Tailscale provides a secure way to access your homelab services remotely without exposing them directly to the internet. By using Tailscale, you can:

1. Access your services from anywhere
2. Maintain security by not exposing services to the public internet
3. Use end-to-end encryption for all traffic
4. Authenticate users with your identity provider

## Setup Instructions

### 1. Install Tailscale on Your Kubernetes Cluster

If you haven't already installed Tailscale on your Kubernetes cluster, you can do so using Helm:

```bash
# Add the Tailscale Helm repository
helm repo add tailscale https://pkgs.tailscale.com/helmcharts

# Update your Helm repositories
helm repo update

# Install Tailscale
helm install tailscale tailscale/tailscale \
  --namespace tailscale \
  --create-namespace \
  --set oauth.clientID=<your-client-id> \
  --set oauth.clientSecret=<your-client-secret> \
  --set oauth.baseURL=https://api.tailscale.com
```

### 2. Configure Tailscale Subnet Router

To make your entire Kubernetes cluster accessible through Tailscale, configure it as a subnet router:

```bash
# Create a ConfigMap for Tailscale configuration
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: tailscale-config
  namespace: tailscale
data:
  TS_ROUTES: "192.168.86.0/24"  # Adjust this to your cluster's CIDR
  TS_AUTH_ONCE: "true"
  TS_USERSPACE: "true"
  TS_EXTRA_ARGS: "--advertise-routes=192.168.86.0/24"  # Adjust this to your cluster's CIDR
EOF
```

### 3. Configure DNS for Tailscale

To make your service domains resolvable through Tailscale:

```bash
# Create MagicDNS configuration
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: tailscale-dns-config
  namespace: tailscale
data:
  TS_ACCEPT_DNS: "true"
  TS_EXTRA_ARGS: "--advertise-exit-node --hostname=homelab-k8s"
EOF
```

### 4. Configure Tailscale on Your Devices

1. Install Tailscale on your devices (laptops, phones, etc.)
2. Log in with the same account used for your Kubernetes Tailscale setup
3. Enable MagicDNS in the Tailscale admin console

### 5. Testing Remote Access

To test remote access:

1. Connect to your Tailscale network on your remote device
2. Try accessing one of your services using its domain name:
   ```
   curl -I https://immich.app.pesulabs.net
   ```

## Security Considerations

1. **Access Controls**: Use Tailscale ACLs to control which users can access which services
2. **MFA**: Enable multi-factor authentication for your Tailscale account
3. **Regular Updates**: Keep Tailscale and your Kubernetes cluster updated
4. **Monitoring**: Monitor access to your services through Tailscale

## Troubleshooting

If you encounter issues:

1. Check Tailscale status: `tailscale status`
2. Verify subnet routes are advertised: `tailscale netcheck`
3. Check Tailscale logs: `kubectl logs -n tailscale deployment/tailscale`
4. Verify DNS resolution: `nslookup immich.app.pesulabs.net`

## Additional Resources

- [Tailscale Documentation](https://tailscale.com/kb/)
- [Kubernetes with Tailscale](https://tailscale.com/kb/1185/kubernetes/)
- [Tailscale MagicDNS](https://tailscale.com/kb/1081/magicdns/)
- [Tailscale ACLs](https://tailscale.com/kb/1018/acls/)
