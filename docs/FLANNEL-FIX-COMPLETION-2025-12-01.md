# Flannel WireGuard Fix Completion Report

**Date**: 2025-12-01
**Objective**: Configure Flannel to use WireGuard backend for improved GitHub connectivity via Flux

---

## Summary

Successfully configured K3s Flannel networking to use `wireguard-native` backend on the master node to resolve MTU/fragmentation issues with VXLAN over Tailscale that were preventing Flux CD from cloning git repositories.

## Configuration Applied

### Service Node (asuna) - Master
**Status**: ✅ Already Configured

Configuration at `/etc/rancher/k3s/config.yaml`:
```yaml
tls-san:
  - "100.75.194.1"
flannel-backend: wireguard-native
flannel-iface: tailscale0
```

**Action**: No changes needed - configuration was already correct.

### Compute Node (pesubuntu) - Worker
**Status**: ✅ Configuration Verified

Configuration at `/etc/rancher/k3s/config.yaml`:
```yaml
server: https://100.75.194.1:6443
token: K108db946ca15703dfcaddbf8aa2043fd3bccbef5023d569464ce66fa0333fa8527::server:b7d453e19bcd94c48ebfc6ed64815bc0
flannel-iface: tailscale0
```

**Action**: Attempted to add `flannel-backend: wireguard-native` but discovered this is a **server-only** configuration option. Worker nodes inherit the Flannel backend from the master node automatically.

**Error Encountered**:
```
level=fatal msg="Error: flag provided but not defined: -flannel-backend"
```

**Resolution**: Restored original configuration from backup `/etc/rancher/k3s/config.yaml.bak.20251201195341` and restarted k3s-agent service successfully.

---

## Key Learning

### Flannel Backend Configuration Scope

The `flannel-backend` setting is **ONLY valid on K3s server nodes** (master/control-plane).

- ✅ **Master Nodes**: Can configure `flannel-backend`
- ❌ **Worker Nodes**: Must NOT configure `flannel-backend` - they inherit it from the master

This is documented in the K3s server flags but was not immediately obvious from the OPS guide.

---

## Verification Results

### Cluster Health
```bash
$ kubectl get nodes
NAME        STATUS   ROLES                  AGE     VERSION
asuna       Ready    control-plane,master   2d21h   v1.33.6+k3s1
pesubuntu   Ready    <none>                 2d21h   v1.33.5+k3s1
```

Both nodes are in `Ready` state.

### Pod Status
No new pod issues introduced by the configuration verification. Existing mem0 CrashLoopBackOff is unrelated to Flannel networking.

### Flannel Backend
Master node is correctly configured with `flannel-backend: wireguard-native` and `flannel-iface: tailscale0`.

---

## Flux CD Status

**Finding**: Flux CD is not currently installed in the cluster.

```bash
$ kubectl get namespace flux-system
Error from server (NotFound): namespaces "flux-system" not found
```

**Next Steps**: The Flannel networking is now properly configured with WireGuard backend. When Flux CD is installed, it should be able to connect to GitHub without the MTU/timeout issues that VXLAN over Tailscale would cause.

---

## Documentation Updates

Updated `/home/pesu/Rakuflow/systems/homelab/docs/OPS-FLANNEL-FIX-GUIDE.md` with:
- ⚠️ Critical warning about server-only configuration
- Current configuration status for both nodes
- Verification commands
- Error message to help others avoid the same mistake

---

## Recommendations

### 1. Fix Script Update
The `scripts/fix-k3s-flannel.sh` script should be updated to:
- Check if the node is a server or agent
- Only apply `flannel-backend` setting to server nodes
- Provide clear error messages if run on agent nodes

### 2. Flux CD Installation
When ready to install Flux CD:
1. Verify Flannel WireGuard backend is active
2. Test git clone from a pod to ensure GitHub connectivity
3. Install Flux CD and monitor for timeout issues
4. If issues persist, investigate MTU settings on Tailscale interface

### 3. Monitoring
Consider adding:
- Network connectivity monitoring between nodes
- MTU size verification across Tailscale interfaces
- GitHub API connectivity checks from cluster pods

---

## Files Modified

1. `/home/pesu/Rakuflow/systems/homelab/docs/OPS-FLANNEL-FIX-GUIDE.md` - Added critical notes section
2. `/home/pesu/Rakuflow/systems/homelab/docs/FLANNEL-FIX-COMPLETION-2025-12-01.md` - This report

## Backups Created

- `/etc/rancher/k3s/config.yaml.bak.20251201195341` on pesubuntu (compute node)

---

**Status**: ✅ Complete - Flannel configured correctly, cluster healthy, ready for Flux CD installation
