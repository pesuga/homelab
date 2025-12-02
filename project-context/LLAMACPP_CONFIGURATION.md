# llama.cpp Service Configuration

**Status:** PRODUCTION READY
**Last Updated:** 2025-11-22
**Location:** Compute Node (`pesubuntu`)

## 🎯 Service Overview

llama.cpp provides GPU-accelerated LLM inference with configurable model switching and comprehensive monitoring. The service runs as a systemd service with Kubernetes integration for cluster access.

## 📁 File Structure

```
/home/pesu/Rakuflow/systems/homelab/
├── config/
│   └── llamacpp.conf                 # Active model configuration
├── scripts/
│   ├── llamacpp-wrapper.sh           # Service startup script
│   ├── llamacpp-manager.sh           # Model management utility
│   └── llamacpp-metrics-collector.sh # Monitoring & benchmarking
├── monitoring/
│   ├── dashboard.html                # Real-time web dashboard
│   └── server.js                     # Node.js backend for dashboard
├── logs/metrics/
│   └── metrics.csv                   # Historical performance data
└── models/llamacpp/
    ├── Kimi-VL-A3B-Thinking-2506-Q4_K_M.gguf
    ├── mmproj-Kimi-VL-A3B-Thinking-2506-Q8_0.gguf
    └── mistral-7b-openorca.Q5_K_M.gguf
```

## ⚙️ Service Configuration

### Systemd Service
```ini
# /etc/systemd/system/llamacpp-configurable.service
[Unit]
Description=llama.cpp server with configurable model support
After=network.target

[Service]
Type=simple
User=pesu
WorkingDirectory=/home/pesu/Rakuflow/systems/homelab
Environment="GGML_VULKAN_DEVICE=0"
ExecStart=/home/pesu/Rakuflow/systems/homelab/scripts/llamacpp-wrapper.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Model Configuration
```bash
# /home/pesu/Rakuflow/systems/homelab/config/llamacpp.conf
# Current Model: Kimi-VL (multimodal with vision)
MODEL_PATH=/home/pesu/models/llamacpp/Kimi-VL-A3B-Thinking-2506-Q4_K_M.gguf
MMPROJ_PATH=/home/pesu/models/llamacpp/mmproj-Kimi-VL-A3B-Thinking-2506-Q8_0.gguf
MODEL_NAME=Kimi-VL
GPU_LAYERS=1
CTX_SIZE=8192
N_PARALLEL=4
N_THREADS=8
BATCH_SIZE=512
UBATCH_SIZE=128
```

## 🔄 Model Management

### Available Models
| Model | Type | Context | Features | Config Name |
|-------|------|---------|----------|-------------|
| **Kimi-VL** | Multimodal | 8192 | Vision + Text | `kimi-vl` |
| **Mistral-7B-OpenOrca** | Text | 16384 | 16K Context | `mistral-7b` |

### Model Switching
```bash
# Switch to Mistral (faster, 16K context)
./scripts/llamacpp-manager.sh switch mistral-7b

# Switch to Kimi-VL (multimodal)
./scripts/llamacpp-manager.sh switch kimi-vl

# Check current status
./scripts/llamacpp-manager.sh status
```

### Service Management
```bash
# Service operations
systemctl status llamacpp-configurable
sudo systemctl restart llamacpp-configurable
sudo systemctl stop llamacpp-configurable

# View logs
journalctl -u llamacpp-configurable -f
```

## 🌐 Network Configuration

### Local Access
```bash
# Health check
curl http://localhost:8081/health

# OpenAI-compatible API
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llamacpp", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### Kubernetes Integration
```yaml
# Service for cluster access
apiVersion: v1
kind: Service
metadata:
  name: llamacpp-service
  namespace: default
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8081
    targetPort: 8081
---
apiVersion: v1
kind: Endpoints
metadata:
  name: llamacpp-service
  namespace: default
subsets:
- addresses:
  - ip: 100.86.122.109  # Tailscale IP of pesubuntu
  ports:
  - name: http
    port: 8081
```

### Backend URLs
- **Internal Cluster**: `http://llamacpp-service.default.svc.cluster.local:8081`
- **Short Form**: `http://llamacpp-service:8081`
- **Local**: `http://100.86.122.109:8081`

## 📊 Performance Specifications

### Current Configuration (Kimi-VL)
- **Model Size**: 3B parameters
- **Quantization**: Q4_K_M (4-bit)
- **GPU**: AMD RX 7800 XT, Vulkan backend
- **GPU Layers**: 1 (optimal stability)
- **Memory Usage**: 1.1GB steady state
- **Performance**: ~50 tokens/sec (prompt), ~30 tokens/sec (generation)

### Alternative Model (Mistral-7B)
- **Model Size**: 7B parameters
- **Quantization**: Q5_K_M (5-bit)
- **Context Window**: 16384 tokens
- **Specialization**: Text-only, faster inference

## 📈 Monitoring System

### Metrics Collection
```bash
# Start monitoring daemon (5s intervals)
./scripts/llamacpp-metrics-collector.sh daemon 5

# View real-time metrics
./scripts/llamacpp-metrics-collector.sh monitor

# Run performance benchmark
./scripts/llamacpp-metrics-collector.sh benchmark
```

### Web Dashboard
```bash
# Access real-time dashboard
http://localhost:8082/dashboard.html

# API endpoints
curl http://localhost:8082/api/current-model
curl http://localhost:8082/api/metrics-data
curl http://localhost:8082/api/system-info
```

### Available Metrics
- **Token Generation**: TPS (tokens per second) tracking
- **System Resources**: CPU, Memory usage
- **Model Performance**: Prompt vs generation speeds
- **Concurrent Requests**: Slot utilization
- **Historical Data**: CSV logging with timestamps

## 🛠️ Configuration Options

### GPU Acceleration
```bash
# Current optimal setting
export GGML_VULKAN_DEVICE=0

# Test different GPU layer counts
# 1 layer = optimal stability (current)
# 5+ layers = may crash with this GPU/setup
```

### Performance Tuning
```bash
# Concurrent requests
N_PARALLEL=4        # Current setting
CTX_SIZE=8192       # Kimi-VL context
CTX_SIZE=16384      # Mistral context

# Thread configuration
N_THREADS=8         # CPU threads
BATCH_SIZE=512      # Batch processing
UBATCH_SIZE=128     # Micro-batch size
```

## 🔧 API Endpoints

### Core Endpoints
- **Health**: `GET /health` → `{"status":"ok"}`
- **Metrics**: `GET /metrics` → Prometheus format
- **Chat**: `POST /v1/chat/completions` → OpenAI compatible
- **Models**: `GET /v1/models` → Available models list

### Chat Completion Example
```bash
curl -X POST http://llamacpp-service:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llamacpp",
    "messages": [
      {"role": "user", "content": "Explain quantum computing"}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

## 🚨 Troubleshooting

### Common Issues
1. **Service not responding**: Check `systemctl status llamacpp-configurable`
2. **GPU not working**: Verify `export GGML_VULKAN_DEVICE=0`
3. **Model switching fails**: Ensure model files exist in `/home/pesu/models/llamacpp/`
4. **Cluster connectivity**: Verify Kubernetes service endpoint IP

### Performance Optimization
- Use 1 GPU layer for stability with AMD RX 7800 XT
- Monitor memory usage with `./scripts/llamacpp-metrics-collector.sh monitor`
- Adjust `N_PARALLEL` based on concurrent request needs
- Use Mistral model for faster text-only inference

## 📋 Maintenance

### Regular Tasks
- Monitor performance metrics weekly
- Check disk space for model files and logs
- Update models as new versions become available
- Backup configuration files

### Backup Locations
```bash
# Configuration
cp config/llamacpp.conf backup/
cp scripts/llamacpp-*.sh backup/

# Performance logs
cp logs/metrics/metrics.csv backup/metrics_$(date +%Y%m%d).csv
```

---

## ✅ Service Validation Checklist

- [x] **llamacpp-configurable.service**: Active and running
- [x] **GPU Acceleration**: 1 layer with Vulkan backend
- [x] **Model Switching**: Kimi-VL ↔ Mistral-7B functional
- [x] **Monitoring System**: Metrics collection and dashboard active
- [x] **Kubernetes Integration**: Service reachable from cluster
- [x] **OpenAI API**: Compatible endpoints working
- [x] **Performance**: Stable 30-50 tokens/sec generation
- [x] **Resource Usage**: 1.1GB memory, moderate CPU

**Status**: ✅ PRODUCTION READY with full monitoring and model switching capabilities