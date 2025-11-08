# 🛠️ Monitoring Scripts

Quick reference for compute node monitoring tools.

## Available Scripts

### 1. `monitor-compute.sh` - Comprehensive Monitoring
**Best for**: General overview of all system metrics

```bash
./scripts/monitor-compute.sh
```

**Shows**:
- GPU utilization, memory, temperature, power (AMD RX 7800 XT)
- CPU usage and load average
- System memory and disk usage
- Ollama and LiteLLM service status
- Active network connections
- Top processes by CPU

**Update rate**: 5 seconds
**Exit**: Ctrl+C

---

### 2. `gpu-monitor.sh` - GPU-Focused Monitoring
**Best for**: Detailed GPU metrics during inference

```bash
./scripts/gpu-monitor.sh
```

**Shows**:
- Full rocm-smi output with all GPU details
- GPU processes (PIDs using the GPU)
- Related processes (Ollama, Python, etc.)

**Update rate**: 2 seconds
**Exit**: Ctrl+C

---

### 3. `inference-benchmark.sh` - Performance Testing
**Best for**: Testing and benchmarking LLM inference

```bash
./scripts/inference-benchmark.sh
```

**Options**:
1. Test Ollama endpoint (direct API)
2. Test LiteLLM endpoint (OpenAI-compatible)
3. Test both endpoints
4. Continuous load test (stress test GPU)

**Features**:
- Captures GPU metrics before/after inference
- Measures response time and tokens/second
- Reports GPU temperature, power, VRAM usage
- Load testing with configurable duration

---

## Quick Commands

### Check GPU Status
```bash
# Simple status
rocm-smi

# Detailed info
rocminfo

# Just utilization
rocm-smi --showuse

# Just memory
rocm-smi --showmeminfo vram

# Just temperature
rocm-smi --showtemp

# Processes using GPU
rocm-smi --showpids
```

### Check Services
```bash
# Ollama
systemctl status ollama
journalctl -u ollama -f

# LiteLLM
systemctl status litellm
journalctl -u litellm -f

# ROCm Exporter (Prometheus)
systemctl status rocm-exporter
journalctl -u rocm-exporter -f
```

### Test Endpoints
```bash
# Ollama health
curl http://localhost:11434/api/version

# Ollama active models
curl http://localhost:11434/api/ps

# LiteLLM health
curl http://localhost:8000/health

# Prometheus exporter
curl http://localhost:9101/metrics
```

## Prometheus Metrics

The ROCm exporter runs on port 9101 and exposes metrics for Prometheus:

**Endpoint**: http://localhost:9101/metrics

**Available metrics**:
- `rocm_gpu_utilization_percent` - GPU usage (0-100%)
- `rocm_gpu_memory_total_bytes` - Total VRAM
- `rocm_gpu_memory_used_bytes` - Used VRAM
- `rocm_gpu_memory_utilization_percent` - VRAM usage (0-100%)
- `rocm_gpu_temperature_celsius` - GPU temperature
- `rocm_gpu_power_watts` - Power consumption

## Usage Examples

### Example 1: Monitor GPU During Chat
```bash
# Terminal 1: Start monitoring
./scripts/gpu-monitor.sh

# Terminal 2: Use Open WebUI or test with curl
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "llama3.1:8b", "prompt": "Explain Docker in simple terms."}'
```

### Example 2: Benchmark Performance
```bash
# Run benchmark and observe GPU metrics
./scripts/inference-benchmark.sh
# Select option 3 (test both endpoints)
```

### Example 3: Stress Test
```bash
# Terminal 1: Monitor GPU
./scripts/monitor-compute.sh

# Terminal 2: Run load test
./scripts/inference-benchmark.sh
# Select option 4 (continuous load test)
# Enter duration: 60 (seconds)
```

### Example 4: Log Metrics to File
```bash
# Capture 5 minutes of GPU metrics
for i in {1..60}; do
  echo "=== $(date) ===" >> gpu_metrics.log
  rocm-smi >> gpu_metrics.log
  sleep 5
done
```

## Performance Expectations

### Idle State
- GPU: 0-5% utilization
- VRAM: ~1.5-2GB (with Ollama loaded)
- Temp: 40-50°C
- Power: 20-40W

### During Inference (7B-8B models)
- GPU: 60-95% utilization
- VRAM: 6-8GB (Q4 quantized)
- Temp: 60-75°C
- Power: 150-250W
- Tokens/sec: 20-30 (target)

### Warning Levels
- 🟡 Temp > 80°C: Monitor cooling
- 🔴 Temp > 85°C: Check airflow
- 🟡 VRAM > 14GB: Approaching limit
- 🔴 VRAM > 15.5GB: Risk of OOM
- 🟡 Power > 250W: High load
- 🔴 Power > 280W: Near TDP limit (290W)

## See Also

- **Full Monitoring Guide**: `/docs/MONITORING-GUIDE.md`
- **LLM Setup Guide**: `/docs/LLM-SETUP.md`
- **Session State**: `/docs/SESSION-STATE.md`

---

**Last Updated**: 2025-10-22
