# llama.cpp Deployment State - Current Reality

**Date**: 2025-11-22
**Status**: Mixed deployment approach (systemd + Kubernetes)

## Current Deployments

### 1. Systemd Services (Native Host)

#### Service: `llamacpp-kimi-vision.service`
- **Status**: ✅ Running
- **Port**: 8080 (host network)
- **Model**: Kimi-VL-A3B-Thinking-2506-Q4_K_M
- **GPU**: 45 layers loaded
- **Slots**: 4 parallel
- **Access**: `http://localhost:8080` or `http://100.72.98.106:8080`

#### Service: `llamacpp.service`
- **Status**: ✅ Running
- **Port**: 8081 (host network)
- **Model**: Kimi-VL-A3B-Thinking-2506-Q4_K_M (DUPLICATE!)
- **GPU**: 0 layers (CPU only)
- **Slots**: 4 parallel
- **Access**: `http://localhost:8081` or `http://100.72.98.106:8081`

### 2. Kubernetes Deployments

#### Deployment: `llamacpp-mistral`
- **Status**: ✅ Running
- **Namespace**: llamacpp
- **Port**: 8081 (pod network, different from host)
- **Model**: Mistral-7B-OpenOrca Q5_K_M
- **GPU**: CPU only (no Vulkan)
- **Slots**: 2 parallel
- **ClusterIP**: 10.43.11.93:8081
- **Access**: `http://llamacpp-mistral.llamacpp.svc.cluster.local:8081`

#### Service: `llamacpp-kimi-vl-service`
- **Status**: ⚠️ Service exists but NO DEPLOYMENT
- **Port**: 8080
- **Note**: Orphaned service, no pods backing it

## Network Isolation

The systemd services and Kubernetes pods **DO NOT conflict** because:
- Systemd services bind to **host network** (`0.0.0.0:808x`)
- Kubernetes pods use **pod network** (separate network namespace)
- Both can use port 8081 without conflict

However, the Kubernetes pod has `hostPID: true` which means it can see host processes, causing confusion when checking `ps aux`.

## Issues & Concerns

### 1. **Duplicate Kimi-VL Deployments**
- Two systemd services running the same Kimi-VL model
- Port 8080: GPU-accelerated (45 layers)
- Port 8081: CPU-only (0 layers)
- **Wasteful**: Running the same model twice

### 2. **Mixed Deployment Strategy**
- Some services use systemd (native host)
- Some use Kubernetes (container orchestration)
- **Confusing**: Hard to track what's where
- **Management**: Different commands for different services

### 3. **Orphaned Kubernetes Service**
- `llamacpp-kimi-vl-service` exists but has no deployment/pods
- Leftover from previous deployment attempt

## Recommendations

### Option A: Consolidate to Kubernetes
**Benefits**:
- Single management interface (kubectl)
- Better resource isolation
- Easier scaling and updates
- Clear service discovery

**Actions**:
1. Stop and disable systemd services
2. Create proper Kubernetes deployments for all models
3. Use different ports or separate services
4. Remove orphaned services

### Option B: Consolidate to Systemd
**Benefits**:
- Direct hardware access
- Lower overhead
- Simpler for single-node setup
- Better GPU performance

**Actions**:
1. Delete Kubernetes deployments
2. Configure systemd services properly
3. Use different ports for different models
4. Create systemd templates for easier management

### Option C: Keep Mixed (Current State)
**Benefits**:
- Nothing changes
- Both work independently

**Drawbacks**:
- Confusing to manage
- Hard to track resource usage
- Duplicate deployments waste resources

## Recommended Path Forward

**Suggested**: **Option B - Consolidate to Systemd**

Rationale:
- Single compute node (not multi-node cluster)
- Need direct GPU access for best performance
- Simpler management for this use case
- Lower overhead

### Proposed Configuration:
```
Port 8080: Kimi-VL (GPU-accelerated, 45 layers)
Port 8081: Mistral-7B-OpenOrca (CPU/GPU, 2 slots)
Port 8082: [Future model slot]
```

## Current Resource Usage

**Systemd Services**:
- Kimi-VL (8080): 962.6M RAM, GPU active
- Kimi-VL (8081): 1.0G RAM, CPU only ❌ WASTE

**Kubernetes**:
- Mistral pod: 6GB RAM limit, CPU only

**Total**: ~8GB RAM for llama.cpp services (with duplication)

## Action Items

- [ ] Decide on deployment strategy (systemd vs Kubernetes)
- [ ] Remove duplicate Kimi-VL service on port 8081
- [ ] Clean up orphaned Kubernetes service
- [ ] Document final deployment architecture
- [ ] Create management scripts for chosen approach
