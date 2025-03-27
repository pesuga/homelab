# Tailscale Hybrid DNS Setup

This document explains how Tailscale hybrid DNS resolution is configured in the homelab.

## Overview

The setup enables seamless DNS resolution between the Kubernetes cluster and resources in your Tailscale network. This is achieved through:

1. Tailscale running as a cluster egress controller
2. CoreDNS configured to forward Tailscale domain queries to Tailscale DNS
3. ExternalName services with Tailscale annotations for specific services

## Adding New Services

To add a new Tailscale network resource for access from the cluster:

1. Create a new YAML file in `clusters/homelab/apps/tailscale/hybrid-services/` following this template:

```yaml
apiVersion: v1
kind: Service
metadata:
  annotations:
    tailscale.com/tailnet-fqdn: "your-service-name.tailnet.ts."
  name: your-service-name
  namespace: default  # Change to desired namespace
spec:
  externalName: placeholder
  type: ExternalName
```

2. Add the new file to `clusters/homelab/apps/tailscale/hybrid-services/kustomization.yaml`

3. Apply the changes with:
```bash
git add clusters/homelab/apps/tailscale/hybrid-services/
git commit -m "Add new hybrid DNS service for your-service-name"
git push
```

4. Wait for Flux to reconcile or manually apply:
```bash
k apply -f clusters/homelab/apps/tailscale/hybrid-services/your-service-name.yaml
```

## Usage

After configuration, you can access Tailscale services from inside your cluster using their Kubernetes service name, for example:

```bash
ping database-prod
curl http://database-prod:port/path
```

## Troubleshooting

If DNS resolution isn't working:

1. Check Tailscale pod is running:
```bash
k get pods -n tailscale
```

2. Check CoreDNS configuration:
```bash
k get configmap -n kube-system coredns -o yaml
```

3. Test DNS resolution from a debug pod:
```bash
k run -it --rm debug --image=busybox -- nslookup database-prod.tailnet.ts
```
