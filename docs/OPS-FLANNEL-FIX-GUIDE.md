# Ops Guide: Applying Flannel Network Fix

**Objective**: Resolve Flux CD git clone timeouts and cross-node MTU issues by switching Flannel backend to `wireguard-native`.

**Target Nodes**:
1.  `asuna` (Service Node / Master)
2.  `pesubuntu` (Compute Node / Worker)

## Prerequisites
- SSH access to both nodes.
- Root or sudo privileges on both nodes.
- The script `scripts/fix-k3s-flannel.sh` must be available (or copied) to the nodes.

## Procedure

### Step 1: Copy Script to Nodes
If the script is not already present on the nodes via a shared mount, copy it:

```bash
# From your local machine or where the repo is checked out
scp scripts/fix-k3s-flannel.sh user@asuna:/tmp/
scp scripts/fix-k3s-flannel.sh user@pesubuntu:/tmp/
```

### Step 2: Apply Fix on Service Node (asuna)
SSH into `asuna` and run the script:

```bash
ssh user@asuna
sudo chmod +x /tmp/fix-k3s-flannel.sh
sudo /tmp/fix-k3s-flannel.sh
```

**Verify**:
- Check that `k3s` service restarted successfully: `systemctl status k3s`
- Check logs for Flannel backend: `journalctl -u k3s | grep "flannel-backend"`

### Step 3: Apply Fix on Compute Node (pesubuntu)
SSH into `pesubuntu` and run the script:

```bash
ssh user@pesubuntu
sudo chmod +x /tmp/fix-k3s-flannel.sh
sudo /tmp/fix-k3s-flannel.sh
```

**Verify**:
- Check that `k3s-agent` service restarted successfully: `systemctl status k3s-agent`

### Step 4: Validate Cluster Health
After applying the fix on both nodes, return to the control plane (or use kubectl locally) to verify:

1.  **Nodes Ready**:
    ```bash
    kubectl get nodes
    ```
    *Both nodes should be `Ready`.*

2.  **Pods Running**:
    ```bash
    kubectl get pods -A
    ```
    *Check for any `CrashLoopBackOff` or `Error` states.*

3.  **Flux Sync (The Goal)**:
    Trigger a reconciliation to test the fix:
    ```bash
    flux reconcile source git homelab
    kubectl get gitrepository -n flux-system
    ```
    *Status should eventually become `Ready`.*

## Rollback (If needed)
If the fix causes issues, edit `/etc/rancher/k3s/config.yaml` on both nodes and revert `flannel-backend` to `vxlan` (or remove the line), then restart the service.

---

## Important Notes

### Agent Node Configuration
**⚠️ CRITICAL**: The `flannel-backend` setting is a **server-only** configuration option. Do NOT add this to agent node configurations.

- **Master Node (asuna)**: Add `flannel-backend: wireguard-native` to `/etc/rancher/k3s/config.yaml`
- **Worker Nodes (pesubuntu)**: Do NOT add `flannel-backend` - agents inherit this from the master

**Error if applied to agent**:
```
level=fatal msg="Error: flag provided but not defined: -flannel-backend"
```

### Current Configuration Status (2025-12-01)

**Service Node (asuna)** ✅:
```yaml
tls-san:
  - "100.75.194.1"
flannel-backend: wireguard-native
flannel-iface: tailscale0
```

**Compute Node (pesubuntu)** ✅:
```yaml
server: https://100.75.194.1:6443
token: [REDACTED]
flannel-iface: tailscale0
# NO flannel-backend setting (inherited from master)
```

### Verification Commands

**Check master config**:
```bash
ssh pesu@100.75.194.1 'cat /etc/rancher/k3s/config.yaml'
```

**Check agent config**:
```bash
ssh pesu@100.86.122.109 'cat /etc/rancher/k3s/config.yaml'
```

**Check cluster health**:
```bash
kubectl get nodes
kubectl get pods -A | grep -E "(CrashLoop|Error|Pending)"
```
