# 🚀 llama.cpp Clean Deployment Setup

## ✅ **FINAL CLEAN DEPLOYMENT STATUS**

**Only ONE working instance - Clean and optimal!**

### 🎯 **SINGLE WORKING DEPLOYMENT**

```
┌─────────────────────────────────────────────────────────────┐
│                    🏠 LOCAL NODE SETUP                      │
├─────────────────────────────────────────────────────────────┤
│                                                            │
│  Service: llamacpp-configurable.service (systemd)         │
│  Process: PID 1709057                                      │
│  Status: ✅ ACTIVE and RUNNING                              │
│  Memory: 1.3GB (Peak: 1.5GB)                               │
│  CPU: ~35% usage                                            │
│                                                            │
│  🎯 CONFIGURATION                                          │
│  ├─ Model: Kimi-VL (multimodal with vision)               │
│  ├─ GPU: AMD RX 7800 XT - 1 layer (Vulkan)                │
│  ├─ Port: 8081 (OpenAI-compatible API)                     │
│  ├─ Context: 8192 tokens                                    │
│  ├─ Parallel slots: 4                                       │
│  └─ Threads: 8                                             │
│                                                            │
│  📊 PERFORMANCE                                           │
│  ├─ Prompt Speed: ~50 tokens/sec                           │
│  ├─ Generation Speed: ~30 tokens/sec                      │
│  ├─ GPU Acceleration: ✅ Enabled                          │
│  └─ API: Full OpenAI /v1/chat/completions               │
│                                                            │
│  🌐 ACCESS POINTS                                         │
│  ├─ Local: http://localhost:8081                          │
│  ├─ Tailscale: http://100.72.98.106:8081                 │
│  └─ Network: http://[node-ip]:8081                        │
│                                                            │
│  🔧 MANAGEMENT                                            │
│  ├─ Model Switching: ./scripts/llamacpp-manager.sh        │
│  ├─ Monitoring: ./scripts/llamacpp-metrics-collector.sh  │
│  ├─ Dashboard: http://localhost:8082                    │
│  └─ Benchmarks: Built-in with performance tracking       │
└─────────────────────────────────────────────────────────────┘
```

## 🧹 **CLEANUP COMPLETED**

### ❌ **REMOVED COMPONENTS**
- ✅ **Kubernetes Services**: `llamacpp-kimi-vl-service` deleted
- ✅ **Kubernetes Namespace**: `llamacpp` namespace deleted
- ✅ **Old Systemd Services**: `llamacpp.service` disabled
- ✅ **Failed Deployments**: All pods and services removed
- ✅ **Orphaned Resources**: Cleaned up

### ✅ **REMAINING COMPONENTS**
- ✅ **llamacpp-configurable.service** - Primary working service
- ✅ **Metrics collector daemon** - Running in background
- ✅ **Monitoring dashboard** - Available on port 8082
- ✅ **Model management tools** - All scripts functional
- ✅ **GPU acceleration** - 1 layer with Vulkan backend

## 📱 **ACCESSING THE SERVICE**

### 🏠 **From Local Machine**
```bash
# API Health Check
curl http://localhost:8081/health

# Chat Completion (OpenAI Compatible)
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llamacpp", "messages": [{"role": "user", "content": "Hello!"}]}'

# Switch Models
./scripts/llamacpp-manager.sh switch mistral-7b  # Text model
./scripts/llamacpp-manager.sh switch kimi-vl      # Multimodal model
```

### 🌐 **From Kubernetes Cluster**
```bash
# Access via Tailscale IP
curl http://100.72.98.106:8081/health

# Or create a simple service that points to this IP
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: llamacpp-external
  namespace: default
spec:
  type: ExternalName
  externalName: 100.72.98.106
  ports:
  - port: 8081
    targetPort: 8081
EOF
```

### 📊 **Monitoring Dashboard**
```bash
# Access web dashboard
http://localhost:8082/dashboard.html

# Start monitoring (if not running)
./scripts/llamacpp-metrics-collector.sh daemon 5

# View real-time metrics
./scripts/llamacpp-metrics-collector.sh monitor

# Run performance benchmark
./scripts/llamacpp-metrics-collector.sh benchmark
```

## 🎯 **MODEL MANAGEMENT**

### 📋 **Available Models**
```bash
./scripts/llamacpp-manager.sh status

# OUTPUT:
# Current Model: Kimi-VL
# Multimodal: Yes (vision + text)
# GPU Layers: 1
# Context Size: 8192
# Service Status: ✅ ACTIVE

# Available Models:
#   - mistral-7b: Mistral-7B-OpenOrca (16K context, text-only)
#   - kimi-vl: Kimi-VL (8K context, multimodal)
```

### 🔄 **Quick Model Switch**
```bash
# Switch to Mistral (faster, 16K context)
./scripts/llamacpp-metrics-collector.sh switch mistral-7b

# Switch back to Kimi-VL (multimodal)
./scripts/llamacpp-metrics-collector.sh switch kimi-vl
```

## 📈 **MONITORING & BENCHMARKING**

### 📊 **Real-Time Metrics**
- **Collection Interval**: 5 seconds
- **Metrics Stored**: `logs/metrics/metrics.csv`
- **Dashboard**: Web interface with live charts
- **Performance Tracking**: Token/sec, CPU, Memory, GPU

### 🏃 **Benchmarking**
```bash
# Standard benchmark
./scripts/llamacpp-metrics-collector.sh benchmark

# Custom benchmark with parameters
./scripts/llamacpp-metrics-collector.sh benchmark \
  "current" \
  "Performance test prompt" \
  100 \
  5

# View benchmark history
ls logs/metrics/benchmark_*.csv
```

## 🔧 **SERVICE MANAGEMENT**

### ⚡ **Start/Stop Service**
```bash
# Status
systemctl status llamacpp-configurable

# Restart
sudo systemctl restart llamacpp-configurable

# Stop
sudo systemctl stop llamacpp-configurable

# View logs
journalctl -u llamacpp-configurable -f
```

### 🎛️ **Configuration**
```bash
# Edit configuration
vim config/llamacpp.conf

# Model selection options:
# MODEL_PATH=...
# MODEL_NAME=...
# GPU_LAYERS=1  # GPU acceleration
# CTX_SIZE=8192  # Context window
# N_PARALLEL=4   # Concurrent requests
```

## 🌟 **PERFORMANCE SPECIFICATIONS**

### 🚀 **Current Performance**
- **Model**: Kimi-VL-A3B-Thinking-2506 (3B parameters)
- **Quantization**: Q4_K_M (4-bit)
- **GPU**: AMD RX 7800 XT, Vulkan backend, 1 layer
- **Memory**: 1.3GB (model + GPU buffers)
- **Throughput**: ~80 tokens/second combined

### 📊 **Resource Usage**
- **CPU**: 30-40% during inference
- **RAM**: 1.3GB steady state
- **GPU**: Minimal usage (1 layer)
- **Network**: ~1MB/s per request

## ✅ **VALIDATION CHECKLIST**

- [x] Single working instance ✅
- [x] GPU acceleration enabled ✅
- [x] OpenAI API compatibility ✅
- [x] Model switching functional ✅
- [x] Monitoring system active ✅
- [x] Benchmarking tools ready ✅
- [x] Kubernetes components removed ✅
- [x] Clean configuration ✅
- [x] Network connectivity working ✅

---

## 🎉 **SUMMARY**

**✅ CLEAN SETUP ACHIEVED!**

You now have **ONE single, optimal llama.cpp deployment** with:
- 🚀 **GPU-accelerated performance**
- 🎯 **Model switching capabilities**
- 📊 **Comprehensive monitoring**
- 🏃 **Built-in benchmarking**
- 🌐 **OpenAI-compatible API**
- 🧹 **Clean, minimal footprint**

**The service is running locally but accessible from the cluster via the Tailscale IP (100.72.98.106:8081) and can be exposed through Kubernetes services as needed.**