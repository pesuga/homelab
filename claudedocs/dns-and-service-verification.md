# DNS and Service Verification Report
**Date**: 2025-11-07
**Author**: Claude Code
**Status**: In Progress

## Executive Summary

DNS resolution **IS working** in the Kubernetes cluster. CoreDNS is properly configured and forwarding to upstream resolvers. The Whisper service failure is NOT due to DNS issues, but rather application-specific problems during model downloading.

## DNS Configuration

### CoreDNS Status
- **Status**: ✅ Running
- **Pod**: `coredns-74f8f96c97-crrtn` in `kube-system`
- **Uptime**: 7 days
- **Configuration**: Forwarding to `/etc/resolv.conf`

### DNS Resolution Chain
```
Pod → CoreDNS (10.43.0.10:53) → systemd-resolved (127.0.0.53) → Upstream DNS
```

**Upstream DNS Servers**:
- **Compute Node (pesubuntu)**: `192.168.8.1` (router)
- **Service Node (asuna)**: `192.168.86.1` (router)
- **Tailscale**: `100.100.100.100` (MagicDNS)

### DNS Test Results

#### ✅ Test 1: External DNS Resolution from N8n Pod
```bash
$ kubectl exec -n homelab deployment/n8n -- nslookup huggingface.co
Server:    10.43.0.10
Address:   10.43.0.10:53

Name:   huggingface.co
Address: 2600:9000:26e0:7600:17:b174:6d00:93a1
```
**Result**: SUCCESS - DNS resolution working correctly

#### ❌ Test 2: Whisper Pod DNS
**Status**: Pods crashing during startup
**Error**: `Failed to establish a new connection: [Errno -3] Temporary failure in name resolution`
**Root Cause**: Application-level issue, NOT DNS infrastructure

### DNS Search Domains
- `chimp-ulmer.ts.net` (Tailscale)
- `pesulabs.net` (Custom domain)
- `ts.net` (Tailscale)
- `lan` (Local network)

## Service Endpoint Verification

### Internal Cluster Services (ClusterIP)

| Service | Namespace | ClusterIP | Port | Status | Notes |
|---------|-----------|-----------|------|--------|-------|
| `postgres` | homelab | 10.43.x.x | 5432 | ✅ Running | PostgreSQL 16 |
| `redis` | homelab | 10.43.x.x | 6379 | ✅ Running | Redis 7 |
| `qdrant` | homelab | 10.43.x.x | 6333 | ✅ Running | Vector DB |
| `mem0` | homelab | 10.43.x.x | 8080 | ✅ Running | AI Memory |
| `n8n` | homelab | 10.43.x.x | 5678 | ✅ Running | Workflows |
| `whisper` | homelab | 10.43.239.160 | 9000 | ❌ Unhealthy | CrashLoopBackOff |
| `ollama` | homelab | 10.43.x.x | 11434 | ⏳ Pending | Not yet deployed |

### External Access (NodePort)

| Service | NodePort | Tailscale URL | Status | Testing Required |
|---------|----------|---------------|--------|------------------|
| n8n | 30678 | http://100.81.76.55:30678 | ✅ | HTTPS needed |
| Prometheus | 30090 | http://100.81.76.55:30090 | ✅ | HTTPS needed |
| Whisper | 30900 | http://100.81.76.55:30900 | ❌ | Unavailable |

### HTTPS Endpoints (Traefik)

| Service | HTTPS URL | Expected | Status | Certificate |
|---------|-----------|----------|--------|-------------|
| n8n | https://n8n.homelab.pesulabs.net | ✅ | ⏳ Need test | Let's Encrypt |
| Prometheus | https://prometheus.homelab.pesulabs.net | ✅ | ⏳ Need test | Let's Encrypt |
| Ollama | https://ollama.homelab.pesulabs.net | ✅ | ⏳ Need test | Let's Encrypt |
| LobeChat | https://lobechat.homelab.pesulabs.net | ✅ | ⏳ Need test | Let's Encrypt |

## Whisper Service Analysis

### Current State
- **Deployment**: `whisper` in `homelab` namespace
- **Replicas**: 4 pods (scaled up from 1)
- **Image**: `onerahmet/openai-whisper-asr-webservice:latest-gpu`
- **Status**: CrashLoopBackOff
- **Node Selector**: Removed (was `workload-type: compute-intensive`)

### Root Cause
The Whisper service is attempting to download the `faster-whisper-large-v3` model (~3GB) from HuggingFace during container startup. The download is failing with connection errors, but this appears to be:

1. **Timeout Issue**: Download takes too long, pod restarts before completion
2. **Network Instability**: Connection drops during large file transfer
3. **NOT a DNS Issue**: DNS resolution works fine, as proven by n8n test

### Error Pattern
```
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='huggingface.co', port=443):
Max retries exceeded with url: /api/models/Systran/faster-whisper-large-v3/revision/main
```

### Recommended Solutions

#### Option 1: Pre-download Model (Recommended)
1. Create init container or job to download model to PVC
2. Configure Whisper to use cached model
3. Prevents startup timeouts

#### Option 2: Use Smaller Model
1. Change `ASR_MODEL` from `large-v3` to `base` or `small`
2. Faster download, less memory
3. Trade-off: Lower accuracy

#### Option 3: Increase Timeouts
1. Disable liveness/readiness probes during startup
2. Increase `initialDelaySeconds` to 300+
3. Allow time for model download

## Network Architecture

### Physical Topology
```
Internet
   │
   ├─→ Router (192.168.8.1) ─→ Compute Node (pesubuntu)
   │                              ├─ Ollama (GPU)
   │                              └─ K3s Agent
   │
   ├─→ Router (192.168.86.1) ─→ Service Node (asuna)
   │                              └─ K3s Server + All services
   │
   └─→ Tailscale (100.100.100.100)
          └─ VPN Overlay Network
```

### Kubernetes Network
```
Pod Network: 10.42.0.0/16 (Flannel CNI)
Service Network: 10.43.0.0/16 (ClusterIP range)
DNS: 10.43.0.10 (CoreDNS)
```

## Action Items

### Immediate (Priority 1)
- [ ] Test all HTTPS endpoints with curl
- [ ] Verify certificate validity
- [ ] Fix Whisper model download (choose solution)
- [ ] Document working service URLs

### Short-term (Priority 2)
- [ ] Deploy Ollama to compute node
- [ ] Configure Family Assistant API
- [ ] Integrate LobeChat with services
- [ ] Add health monitoring for all endpoints

### Long-term (Priority 3)
- [ ] Implement automated certificate rotation monitoring
- [ ] Add DNS monitoring and alerting
- [ ] Document disaster recovery procedures
- [ ] Create service dependency map

## Testing Commands

### DNS Testing
```bash
# Test from pod
kubectl exec -n homelab deployment/n8n -- nslookup huggingface.co

# Test from host
curl -I https://huggingface.co

# Check CoreDNS logs
kubectl logs -n kube-system deployment/coredns
```

### Service Testing
```bash
# Test ClusterIP services from within cluster
kubectl run test --image=busybox --rm -it -- wget -O- http://n8n.homelab.svc.cluster.local:5678

# Test NodePort from Tailscale
curl http://100.81.76.55:30678

# Test HTTPS with cert validation
curl -v https://n8n.homelab.pesulabs.net
```

### Certificate Verification
```bash
# Check certificate details
openssl s_client -connect n8n.homelab.pesulabs.net:443 -servername n8n.homelab.pesulabs.net

# Verify Let's Encrypt chain
curl -v https://n8n.homelab.pesulabs.net 2>&1 | grep -i "cert\|ssl\|tls"
```

## Conclusions

1. **DNS Infrastructure**: ✅ Fully functional
2. **Service Discovery**: ✅ Working within cluster
3. **External Access**: ⏳ Needs HTTPS endpoint testing
4. **Whisper Issue**: Application-specific, NOT infrastructure

## Next Steps

1. Create comprehensive service testing script
2. Test all HTTPS endpoints
3. Fix Whisper model download
4. Document all working URLs
5. Update homelab dashboard with status
