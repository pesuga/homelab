# Family Assistant Networking Fix - 2025-11-19

## Problem Summary

Frontend on compute node (100.86.122.109) could not reach backend API on service node (100.81.76.55:30801) via Tailscale mesh network.

### Error Symptoms
- Connection refused when accessing http://100.81.76.55:30801
- Service appeared healthy in K3s
- Pod was running successfully
- Tailscale mesh connectivity was working

## Root Cause Analysis

### Investigation Steps

1. **Verified Tailscale connectivity**
   - ✅ Both nodes in mesh: 100.86.122.109 (compute), 100.81.76.55 (service)
   - ✅ Ping successful between nodes
   - ✅ Direct connection established

2. **Checked K3s service configuration**
   ```bash
   kubectl describe svc -n homelab family-assistant-nodeport
   ```
   - ⚠️ **Critical Finding**: Endpoints field was empty
   - Service had no backend pods to route traffic to

3. **Identified label mismatch**
   ```bash
   # Service selector
   kubectl get svc -n homelab family-assistant-nodeport -o jsonpath='{.spec.selector}'
   {"app":"family-assistant"}

   # Pod labels
   kubectl get pod -n homelab family-assistant-backend-xxx -o jsonpath='{.metadata.labels}'
   {"app":"family-assistant-backend","component":"familyai-v3"}
   ```

### Root Cause

**Label mismatch between service selector and pod labels**:
- Service was selecting: `app: family-assistant`
- Pods had labels: `app: family-assistant-backend`, `component: familyai-v3`
- Result: Service could not find any matching pods
- Consequence: NodePort had no endpoints, refused all connections

## Solution

### Fix Applied

1. Updated service-nodeport.yaml selector to match pod labels:
   ```yaml
   selector:
     app: family-assistant-backend
     component: familyai-v3
   ```

2. Applied fix:
   ```bash
   kubectl apply -f service-nodeport.yaml
   ```

3. Verified endpoints populated:
   ```bash
   kubectl get endpoints -n homelab family-assistant-nodeport
   # Output: family-assistant-nodeport   10.42.3.29:8001
   ```

### Verification Results

```bash
# Test via Tailscale IP - ✅ SUCCESS
curl http://100.81.76.55:30801/health
{"status":"healthy","ollama":"http://100.86.122.109:8080",...}

# Test via local network - ⚠️ Firewall blocks local network access
# This is expected - Tailscale mesh is the primary access method
```

## Prevention Measures

### 1. Label Consistency Pattern
All Family Assistant services must use consistent labels:
```yaml
# Deployment
labels:
  app: family-assistant-backend
  component: familyai-v3
  version: v2.0.0

# Service (must match)
selector:
  app: family-assistant-backend
  component: familyai-v3
```

### 2. Verification Checklist
Before deploying services, verify:
- [ ] Service selector matches deployment labels
- [ ] `kubectl get endpoints` shows populated endpoints
- [ ] Health check accessible via NodePort

### 3. Monitoring
Add to health checks:
```bash
# Check service has endpoints
kubectl get endpoints -n homelab family-assistant-nodeport

# Verify endpoint count
kubectl get endpoints -n homelab family-assistant-nodeport -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w
```

## Architecture Notes

### Network Topology
```
Frontend (Compute Node: 100.86.122.109)
    |
    | Tailscale Mesh
    ↓
NodePort Service (100.81.76.55:30801)
    |
    | K3s Service Mesh
    ↓
Backend Pod (10.42.3.29:8001)
```

### Why Local Network Failed
- Local network (192.168.8.0/24) requires firewall rules
- Tailscale mesh bypasses firewall with encrypted tunnel
- **Best Practice**: Always use Tailscale IPs for inter-node communication

## Files Modified

1. **Created**: `service-nodeport.yaml` - NodePort service with correct selectors
2. **Fixed**: Applied corrected configuration to cluster
3. **Documented**: This file for future reference

## Lessons Learned

1. **Always verify endpoints**: Empty endpoints = selector mismatch
2. **Label consistency is critical**: Small label differences break service routing
3. **Tailscale simplifies networking**: No firewall rules needed for mesh traffic
4. **Document network topology**: Clear architecture prevents confusion

## Related Documentation

- [Family Assistant README](./README.md)
- [K3s Node Configuration](/home/pesu/Rakuflow/systems/homelab/docs/SESSION-STATE.md)
- [Tailscale Mesh Setup](../../docs/NETWORKING.md)

## Quick Reference Commands

```bash
# Verify service health
kubectl describe svc -n homelab family-assistant-nodeport
kubectl get endpoints -n homelab family-assistant-nodeport

# Test connectivity
curl http://100.81.76.55:30801/health

# Check pod labels
kubectl get pods -n homelab -l app=family-assistant-backend --show-labels

# Restart service if needed
kubectl delete svc -n homelab family-assistant-nodeport
kubectl apply -f service-nodeport.yaml
```
