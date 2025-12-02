# TLS Certificate Issue - Root Cause Analysis

**Date:** 2025-11-29
**Status:** ⚠️ Identified - Requires Manual Fix

## Root Cause

Tailscale Split DNS configuration on the host is adding `pesulabs.net` to the DNS search domains in `/etc/resolv.conf`. This causes Kubernetes pods to append `.pesulabs.net` to external domain lookups, which then match the wildcard DNS record pointing to the local node (`100.75.194.1`).

### Evidence

```bash
# From inside a pod:
$ nslookup acme-v02.api.letsencrypt.org
Name:   acme-v02.api.letsencrypt.org.pesulabs.net  # ← WRONG!
Address: 100.75.194.1

# With trailing dot (FQDN):
$ nslookup acme-v02.api.letsencrypt.org.
Name:   acme-v02.api.letsencrypt.org
Address: 172.65.32.248  # ← CORRECT!
```

### Pod `/etc/resolv.conf`
```
search cert-manager.svc.cluster.local svc.cluster.local cluster.local ts.net lan chimp-ulmer.ts.net pesulabs.net
nameserver 10.43.0.10
options ndots:5
```

The `pesulabs.net` search domain causes non-FQDN lookups to be tried as `<domain>.pesulabs.net` first.

## Impact

- cert-manager cannot register with Let's Encrypt ACME server
- Traefik ACME client fails with same issue
- Any pod trying to reach external HTTPS services may fail if the domain gets resolved to local node

## Solutions

### Option A: Remove pesulabs.net from Tailscale Split DNS (Recommended)

1. On each node, edit Tailscale configuration to remove `pesulabs.net` from Split DNS
2. Restart Tailscale: `sudo systemctl restart tailscaled`
3. Restart CoreDNS: `kubectl rollout restart deployment -n kube-system coredns`
4. Restart cert-manager: `kubectl rollout restart deployment -n cert-manager cert-manager`

### Option B: Use Custom DNS Policy for cert-manager

Update cert-manager deployment to use custom DNS configuration without search domains:

```yaml
spec:
  template:
    spec:
      dnsPolicy: None
      dnsConfig:
        nameservers:
        - 10.43.0.10
        searches:
        - cert-manager.svc.cluster.local
        - svc.cluster.local
        - cluster.local
        options:
        - name: ndots
          value: "5"
```

### Option C: Use External DNS for ACME (Current Workaround)

CoreDNS has been configured to forward to `1.1.1.1` instead of `/etc/resolv.conf`, but this doesn't fix the pod-level search domains.

## Files Modified

- `/etc/coredns/Corefile` (via ConfigMap `coredns` in `kube-system` namespace)
  - Changed `forward . /etc/resolv.conf` to `forward . 1.1.1.1 1.0.0.1`

## Next Steps

1. Choose a solution (A recommended)
2. Apply the fix
3. Verify cert-manager can register with Let's Encrypt
4. Issue wildcard certificate
5. Update IngressRoutes to use the certificate
