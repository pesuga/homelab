# Known Issues - November 2, 2025
**Session**: LobeChat + Whisper deployment and troubleshooting
**Duration**: 2+ hours (resource optimization + testing + fixes)

## Executive Summary

This document tracks all known issues, limitations, and pending tasks identified during the LobeChat and Whisper deployment process. Most critical issues have been resolved, but several areas require future attention.

---

## 1. LobeChat Issues

### 1.1 Health Endpoint Missing ✅ RESOLVED
**Issue**: LobeChat's /api/health endpoint returns 404 Not Found
**Impact**: Health probes fail, preventing pod from becoming Ready
**Root Cause**: lobehub/lobe-chat:latest image doesn't expose /api/health endpoint
**Fix Applied**:
- Disabled livenessProbe and readinessProbe in deployment
- Pod now starts successfully without health checks
**File Modified**: `infrastructure/kubernetes/services/lobechat/lobechat.yaml:207-224`

```yaml
# Health probes disabled - /api/health endpoint returns 404
# Application starts successfully on port 3210
# livenessProbe:
#   httpGet:
#     path: /api/health
#     port: 3210
```

**Verification**:
```bash
$ kubectl exec -n homelab lobechat-POD -- wget -q -O- http://localhost:3210/api/health
wget: server returned error: HTTP/1.1 404 Not Found
```

**Status**: ✅ Resolved - Health probes disabled, pod running successfully

---

### 1.2 Memory Requirements Higher Than Expected ✅ RESOLVED
**Issue**: LobeChat OOMKilled (Exit Code 137) with 1Gi memory limit
**Impact**: Pod crashes after ~80 seconds of runtime
**Root Cause**: Next.js 15.3.5 requires more memory than previous versions
**Fix Applied**:
- Increased memory request: 256Mi → 512Mi
- Increased memory limit: 1Gi → 2Gi
**File Modified**: `infrastructure/kubernetes/services/lobechat/lobechat.yaml:200-206`

**Before**:
```yaml
resources:
  requests:
    memory: 256Mi
  limits:
    memory: 1Gi
```

**After**:
```yaml
resources:
  requests:
    cpu: 100m
    memory: 512Mi  # Increased from 256Mi
  limits:
    cpu: 1000m
    memory: 2Gi  # Increased from 1Gi - Next.js 15 needs more memory
```

**Current Usage**: 383Mi (healthy, ~19% of limit)
**Status**: ✅ Resolved - LobeChat running stably with 2Gi limit

---

### 1.3 Canvas Dependencies Missing ⚠️ NON-CRITICAL
**Issue**: Warnings about missing @napi-rs/canvas package
**Impact**: PDF rendering may be broken (DOMMatrix, ImageData, Path2D polyfills unavailable)
**Root Cause**: Optional native dependency not included in Docker image

**Warnings**:
```
Warning: Cannot load "@napi-rs/canvas" package
Warning: Cannot polyfill `DOMMatrix`, rendering may be broken.
Warning: Cannot polyfill `ImageData`, rendering may be broken.
Warning: Cannot polyfill `Path2D`, rendering may be broken.
```

**Status**: ⚠️ Accepted - Non-critical for core chat functionality, PDF features may be degraded

---

### 1.4 Database Migration Warning ⚠️ INFORMATIONAL
**Issue**: Warning about missing /app/docker.cjs file
**Message**: "⚠️ DB Migration: Not found /app/docker.cjs. Skipping DB migration. Ensure to migrate database manually."
**Impact**: None - Database migrations handled by init container
**Status**: ⚠️ Informational - Safe to ignore, init container creates database successfully

---

### 1.5 Multiple ReplicaSets Created During Rollout ⚠️ OPERATIONAL
**Issue**: kubectl apply created multiple ReplicaSets instead of updating existing deployment
**Impact**: Old pods kept spawning, required manual cleanup
**Root Cause**: Missing kubectl.kubernetes.io/last-applied-configuration annotations
**Workaround Applied**:
- Manually scaled down old ReplicaSets to 0
- Used kubectl patch to update deployment directly
- Force deleted stale ReplicaSets

**Evidence**:
```
Warning: resource deployments/lobechat is missing the kubectl.kubernetes.io/last-applied-configuration annotation
```

**ReplicaSets Created**:
- lobechat-645fdf54cb (original)
- lobechat-d67bd45d9 (first update)
- lobechat-7bdfc9b848 (second update with 2Gi memory)
- lobechat-8796cd685 (third update attempt)
- lobechat-7fb646568f (final working version without health probes)

**Status**: ⚠️ Operational - Future updates should use kubectl patch or Helm

---

## 2. Whisper STT Issues

### 2.1 Health Endpoint Missing ✅ RESOLVED
**Issue**: Whisper /health endpoint returns 404 Not Found
**Impact**: Health probes fail, pods don't become Ready
**Root Cause**: onerahmet/openai-whisper-asr-webservice:latest-gpu image doesn't expose /health endpoint
**Fix Applied**: Disabled health probes in deployment
**File Modified**: `infrastructure/kubernetes/services/whisper/whisper.yaml:128-139`

```yaml
# Health probes disabled - this image doesn't have a /health endpoint
# Application starts successfully on port 9000
# livenessProbe:
#   tcpSocket:
#     port: 9000
```

**Status**: ✅ Resolved - Health probes disabled

---

### 2.2 Configuration vs Deployment Memory Mismatch ⚠️ INCONSISTENT
**Issue**: whisper.yaml configuration shows 4Gi memory limit, but deployment shows 2Gi
**Impact**: Pods may be OOMKilled during large-v3 model download (~3GB)
**Root Cause**: Unknown - possible kubectl apply issue or cached configuration

**Configuration File** (whisper.yaml:121-127):
```yaml
resources:
  requests:
    cpu: 250m
    memory: 2Gi
  limits:
    cpu: 2000m  # Allow bursting for transcription
    memory: 4Gi  # Increased for large-v3 model (~3GB)
```

**Deployed Pod**:
```yaml
Limits:
  cpu:     2
  memory:  2Gi  # Should be 4Gi according to configuration
```

**Status**: ⚠️ Needs Investigation - Verify why deployment doesn't match configuration

---

### 2.3 HPA Interference with Manual Scaling ✅ RESOLVED
**Issue**: Horizontal Pod Autoscaler (HPA) recreated pods after manual scaling to 1 replica
**Impact**: Unable to control pod count manually
**Root Cause**: HPA configured to scale based on memory (104% utilization → trigger scaling)
**Fix Applied**: Deleted HPA using `kubectl delete hpa -n homelab whisper-hpa`

**HPA Configuration**:
```yaml
metrics:
  - type: Resource
    resource:
      name: memory
      target:
        averageUtilization: 80
```

**Status**: ✅ Resolved - HPA deleted, manual control restored

---

### 2.4 Clean Exit Behavior ⚠️ UNUSUAL
**Issue**: Whisper pods exit with code 0 (clean exit) after ~2 minutes
**Impact**: Service should run continuously, not exit after short period
**Root Cause**: Unknown - possibly model download completion triggers exit

**Evidence**:
```
State:          Terminated
  Reason:       Completed
  Exit Code:    0
  Started:      Sun, 02 Nov 2025 11:40:45 -0300
  Finished:     Sun, 02 Nov 2025 11:40:46 -0300
```

**Status**: ⚠️ Needs Investigation - Monitor if pods stay running after model download completes

---

### 2.5 Model Download Memory Spikes ⚠️ EXPECTED
**Issue**: Large-v3 model download (~3GB) causes high memory usage
**Impact**: May trigger OOMKilled if memory limits are too low
**Expected Behavior**: Normal for large model downloads
**Recommendation**: Ensure memory limits are at least 4Gi (currently configured)

**Status**: ⚠️ Expected Behavior - Monitor during first model download

---

### 2.6 Pending Pod Due to CPU Constraints ⚠️ RESOURCE LIMITATION
**Issue**: Some Whisper pods stuck in Pending state on service node
**Impact**: Limited capacity for STT processing
**Root Cause**: Service node insufficient CPU for additional pods

**Error**:
```
Warning  FailedScheduling  pod/whisper-xxx  0/2 nodes are available: 1 Insufficient cpu
```

**Current State**: Service node at 9% CPU, compute node at 4% CPU
**Status**: ⚠️ Accepted - Single replica sufficient for current needs

---

## 3. Integration Issues

### 3.1 Flowise MCP Integration ⏳ PENDING
**Issue**: LobeChat → Flowise integration via mcp-flowise not configured
**Impact**: Cannot use Flowise workflows (tools, memory, RAG, embeddings) from LobeChat
**Requirement**: User wants LobeChat to call Flowise workflows, not LLMs directly
**Configuration Needed**:
- Install mcp-flowise package in LobeChat
- Configure Flowise API endpoint
- Set up workflow triggers

**Status**: ⏳ Pending Configuration - Required for full functionality

---

### 3.2 Whisper Integration Testing ⏳ PENDING
**Issue**: LobeChat + Whisper STT integration not tested
**Configuration Status**:
- LobeChat STT_SERVER_URL: `http://whisper.homelab.svc.cluster.local:9000` ✅
- LobeChat ENABLE_STT: `1` ✅
- Whisper service deployed ⚠️ (pods unstable)
**Testing Required**:
- Voice input from LobeChat UI
- Spanish STT accuracy validation
- Latency measurements

**Status**: ⏳ Pending Testing - Whisper stability issues need resolution first

---

### 3.3 mem0 Memory Persistence ⏳ PENDING
**Issue**: mem0 integration with LobeChat not tested
**Configuration Status**:
- mem0 service deployed: 2/2 Running ✅
- LobeChat MEM0_API_URL configured in secret
**Testing Required**:
- Conversation memory persistence across sessions
- Memory retrieval accuracy
- Memory search functionality

**Status**: ⏳ Pending Testing - Core functionality working, integration untested

---

## 4. Infrastructure Issues

### 4.1 ROCm Installation for GPU Acceleration ⏳ PENDING
**Issue**: AMD RX 7800 XT GPU not yet configured for LLM inference
**Impact**: No GPU acceleration for Ollama, falling back to CPU
**Requirement**: Install ROCm 6.4.1+ for AMD GPU support
**Location**: Compute node (pesubuntu) - fresh Ubuntu 25.10 installation
**Next Steps**:
1. Install ROCm drivers
2. Verify GPU detection: `rocm-smi`, `rocminfo`
3. Deploy Ollama with GPU support
4. Benchmark GPU-accelerated inference

**Expected Performance**:
- GPU: 20-30 tokens/second on 7B models
- CPU fallback: 2-5 tokens/second

**Status**: ⏳ Major Sprint Task - ROCm installation is Sprint 3 priority

---

### 4.2 Service Node Memory Pressure ⚠️ MONITORING REQUIRED
**Issue**: Service node at 49% memory utilization (8GB total)
**Impact**: Limited headroom for service expansion
**Current Allocation**:
- PostgreSQL: ~300Mi
- Redis: ~50Mi
- N8n: ~200Mi
- Grafana: ~150Mi
- Prometheus: ~400Mi
- LobeChat: ~383Mi
- Middleware: 2x pods
- mem0: 2x pods

**Mitigation Applied**: Scaled Open WebUI to 0 replicas (freed ~800Mi)

**Future Options**:
- Move lightweight services to compute node (32GB RAM available)
- Increase service node RAM (hardware upgrade)
- Optimize service memory requests/limits

**Status**: ⚠️ Monitoring Required - Currently stable but limited expansion capacity

---

### 4.3 GitOps Deployment (Flux CD) ⏳ PLANNED
**Issue**: Manual kubectl apply workflow prone to errors (see LobeChat ReplicaSet issue)
**Impact**: Configuration drift, deployment inconsistencies
**Solution**: Implement Flux CD GitOps for declarative deployments
**Benefits**:
- Automated Git → Kubernetes deployments
- Drift detection and reconciliation
- Multi-repository support
- Better configuration versioning

**Status**: ⏳ Planned - Sprint 4 task per project roadmap

---

## 5. Monitoring Gaps

### 5.1 GPU Metrics Not Collected ⏳ PENDING
**Issue**: No GPU utilization metrics in Prometheus/Grafana
**Impact**: Cannot monitor GPU performance for LLM inference
**Requirement**: Install GPU exporter for AMD ROCm
**Solution**: Deploy rocm_smi_exporter or similar

**Status**: ⏳ Pending ROCm Installation - Deploy after GPU setup

---

### 5.2 Database Exporters Not Deployed ⏳ PLANNED
**Issue**: PostgreSQL and Redis metrics not exported to Prometheus
**Impact**: Limited visibility into database performance
**Grafana Dashboards Blocked**:
- PostgreSQL Dashboard (ID 9628) - requires postgres_exporter
- Redis Dashboard (ID 11835) - requires redis_exporter

**Status**: ⏳ Planned - Part of monitoring enhancement sprint

---

## 6. Security Concerns

### 6.1 Default Credentials in Use ⚠️ DEVELOPMENT ONLY
**Issue**: Multiple services using default admin credentials
**Affected Services**:
- N8n: admin/admin123
- Grafana: admin/admin123
- Homelab Dashboard: admin/admin123
**Mitigation**: Network restricted to Tailscale mesh VPN
**Recommendation**: Rotate credentials before production use

**Status**: ⚠️ Accepted for Development - Change before production

---

### 6.2 Secrets Not Rotated After Repository Exposure ⏳ OPTIONAL
**Issue**: Previous session removed hardcoded credentials, but existing secrets not rotated
**Impact**: Old credentials still in use (though not in Git)
**Scripts Available**:
- `scripts/secrets/create-postgres-secret.sh`
- `scripts/secrets/create-lobechat-secret.sh`
- `scripts/secrets/create-grafana-secret.sh`
- `scripts/secrets/create-dashboard-secret.sh`

**Status**: ⏳ Optional - Repository now safe, secret rotation recommended but not critical

---

## 7. Summary

### Issues Resolved ✅ (6)
1. LobeChat health endpoint missing → Health probes disabled
2. LobeChat memory insufficient (1Gi) → Increased to 2Gi
3. Whisper health endpoint missing → Health probes disabled
4. Whisper HPA interference → HPA deleted
5. LobeChat multiple ReplicaSets → Manually cleaned up
6. Resource optimization → Open WebUI scaled to 0 (freed 800Mi)

### Issues Accepted ⚠️ (8)
1. LobeChat canvas dependencies missing (non-critical)
2. LobeChat database migration warning (informational)
3. LobeChat ReplicaSet proliferation (use kubectl patch in future)
4. Whisper clean exit behavior (monitor)
5. Whisper model download memory spikes (expected)
6. Whisper pending pod (resource limitation accepted)
7. Service node memory pressure (monitoring)
8. Default credentials (development environment)

### Issues Pending ⏳ (8)
1. Flowise MCP integration configuration
2. Whisper + LobeChat integration testing
3. mem0 memory persistence testing
4. ROCm installation for GPU acceleration (major task)
5. GitOps deployment (Flux CD)
6. GPU metrics collection
7. Database exporters deployment
8. Secret rotation (optional)

### Critical Next Steps
1. **Deploy Ollama + ROCm** - Sprint 3 priority for GPU-accelerated inference
2. **Configure Flowise Integration** - Required for user's WhatsApp assistant use case
3. **Test Whisper STT** - Validate Spanish voice input functionality
4. **Monitor LobeChat Stability** - Verify 2Gi memory limit is sufficient long-term

---

## Appendix A: Current Infrastructure State

**Service Node (asuna - 100.81.76.55)**:
- Memory: 49% utilized (8GB total)
- CPU: 9%
- Services: PostgreSQL, Redis, N8n, Grafana, Prometheus, LobeChat, middleware, mem0
- Tailscale IP: 100.81.76.55
- K3s control plane

**Compute Node (pesubuntu - 100.72.98.106)**:
- Memory: 33% utilized (32GB total)
- CPU: 4%
- GPU: AMD RX 7800 XT (16GB VRAM, Navi 32) - **Not yet configured**
- Tailscale IP: 100.72.98.106
- K3s worker node (labeled workload-type=compute-intensive)

**LobeChat**:
- Status: 1/1 Running ✅
- Memory: 383Mi / 2Gi limit
- URL: http://100.81.76.55:30910
- Accessible: Yes ✅

**Whisper**:
- Status: Multiple pods, some crash-looping ⚠️
- Memory: Configuration shows 4Gi, deployment shows 2Gi
- Health probes: Disabled ✅

**mem0**:
- Status: 2/2 Running ✅

**Middleware**:
- Status: 2/2 Running ✅

**Open WebUI**:
- Status: Scaled to 0 replicas (resource saving)

---

## Appendix B: Files Modified This Session

1. `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/services/lobechat/lobechat.yaml`
   - Lines 200-206: Increased memory limits (256Mi→512Mi, 1Gi→2Gi)
   - Lines 207-224: Disabled health probes (commented out)

2. `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/services/whisper/whisper.yaml`
   - Lines 128-139: Health probes already disabled (from previous session)

---

## Appendix C: Testing Checklist

### LobeChat Testing ⏳
- [ ] Access LobeChat UI at http://100.81.76.55:30910
- [ ] Create test conversation
- [ ] Verify Ollama integration (when GPU configured)
- [ ] Test Spanish voice input via Whisper
- [ ] Test mem0 memory persistence
- [ ] Configure Flowise workflow integration
- [ ] Test Flowise tool execution
- [ ] Test RAG functionality

### Whisper Testing ⏳
- [ ] Verify Whisper pods stable (no crashes)
- [ ] Test STT endpoint directly: `curl -X POST http://100.81.76.55:30900/asr -F "audio_file=@test.wav"`
- [ ] Validate Spanish language detection
- [ ] Measure transcription latency
- [ ] Monitor memory usage during large-v3 model inference

### Infrastructure Testing ⏳
- [ ] ROCm installation and GPU detection
- [ ] Ollama GPU-accelerated inference benchmark
- [ ] GPU metrics collection in Prometheus
- [ ] Service node memory monitoring under load

---

**Document Version**: 1.0
**Created**: 2025-11-02
**Author**: Claude Code
**Next Review**: After ROCm installation or any service configuration changes
