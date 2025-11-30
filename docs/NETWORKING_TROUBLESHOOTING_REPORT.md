# Networking Troubleshooting Report: Cross-Node Connectivity

**Date:** 2025-11-28
**Status:** ⚠️ Unresolved (Agent Startup Failed)
**Issue:** Worker node (`pesubuntu`) cannot reach Master node (`asuna`) services (DNS, ClusterIP).

## 1. Problem Summary
Pods running on the worker node cannot communicate with the cluster network.
- **Symptoms**:
    - `nslookup kubernetes.default` times out.
    - `curl` to ClusterIPs (e.g., Qdrant) fails (Connection refused).
    - Cross-node ping works (Tailscale IP is reachable), but CNI overlay is broken.

## 2. Root Cause Analysis
- **Network Topology**: Nodes are connected via **Tailscale** (`tailscale0` interface).
- **CNI Configuration**: K3s was using **Flannel with VXLAN** (default).
- **The Conflict**:
    - Tailscale creates a Layer 3 TUN interface.
    - VXLAN requires a Layer 2 underlying network to encapsulate Ethernet frames.
    - Flannel failed to create the `flannel.1` VXLAN interface on the worker node because it couldn't encapsulate over `tailscale0` correctly without specific configuration.
- **Evidence**:
    - `kubectl exec net-debug -- ip link show type vxlan` returned empty (Interface missing).
    - `kubectl exec net-debug -- ip route` showed no routes to the Master's Pod CIDR.

## 3. Attempted Fixes & Actions Taken
1.  **Diagnosis**: Deployed `netshoot` debug pod to inspect network namespace. Confirmed missing interfaces and routes.
2.  **Agent Configuration (`pesubuntu`)**:
    - Installed `wireguard` kernel module and tools.
    - Updated `/etc/rancher/k3s/config.yaml`:
        ```yaml
        flannel-iface: tailscale0
        # flannel-backend: wireguard-native  <-- REMOVED (Server-only flag)
        ```
    - Restarted `k3s-agent`.

## 4. Current Status
- **K3s Agent is failing to start/connect**.
- **Likely Cause**: **Configuration Mismatch**.
    - The Master node (`asuna`) is likely still configured with the default `vxlan` backend.
    - The Agent (`pesubuntu`) might be trying to use `wireguard` (if auto-detected) or is failing to handshake with the Master due to backend mismatch.
    - `journalctl` logs on Agent are needed to confirm the exact error (e.g., "failed to get CA certs" or "handshake failure").

## 5. Required Next Steps (Manual Intervention)

To resolve this, **BOTH** nodes must use the same compatible backend (`wireguard-native` is recommended for Tailscale).

### Step A: Configure Master Node (`asuna`)
1.  SSH into `asuna`.
2.  Edit `/etc/rancher/k3s/config.yaml`:
    ```yaml
    flannel-backend: wireguard-native
    flannel-iface: tailscale0
    ```
3.  Restart K3s: `sudo systemctl restart k3s`.

### Step B: Verify Agent Node (`pesubuntu`)
1.  Ensure `/etc/rancher/k3s/config.yaml` has:
    ```yaml
    flannel-iface: tailscale0
    ```
    *(Note: Agents inherit backend config from the Master, so you don't set `flannel-backend` here).*
2.  Restart Agent: `sudo systemctl restart k3s-agent`.
3.  Check Logs: `sudo journalctl -u k3s-agent -f`.

### Step C: Final Verification
1.  Run `kubectl get nodes -o wide` (Both should be Ready).
2.  Run `kubectl get pods -A -o wide` (All pods running).
3.  Test DNS: `kubectl exec -it <pod-on-worker> -- nslookup kubernetes.default`.
