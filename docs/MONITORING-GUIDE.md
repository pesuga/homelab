# 📊 Compute Node Monitoring Guide

## Overview

This guide explains how to monitor the compute node's performance during LLM model usage, including GPU metrics, system resources, and inference performance.

## Quick Start

### 1. Real-Time Monitoring Dashboard

For a comprehensive view of all metrics, run:

```bash
cd /home/pesu/Rakuflow/systems/homelab
./scripts/monitor-compute.sh
```

This script shows:
- GPU utilization and VRAM usage (AMD RX 7800 XT)
- GPU temperature and power consumption
- CPU usage and load average
- Memory and disk usage
- Ollama and LiteLLM service status
- Active network connections

**Updates every 5 seconds**. Press `Ctrl+C` to exit.

### 2. GPU-Only Monitoring

For a focused view of GPU metrics:

```bash
./scripts/gpu-monitor.sh
```

Shows detailed ROCm GPU metrics updated every 2 seconds.

### 3. Manual GPU Checks

```bash
# Quick GPU status
rocm-smi

# Detailed GPU info
rocminfo

# GPU usage only
rocm-smi --showuse

# VRAM usage
rocm-smi --showmeminfo vram

# Temperature
rocm-smi --showtemp

# Power consumption
rocm-smi --showpower

# Running processes using GPU
rocm-smi --showpids
```

## Benchmarking and Load Testing

### Run Inference Benchmark

Test LLM inference performance while monitoring GPU:

```bash
./scripts/inference-benchmark.sh
```

Options:
1. **Test Ollama endpoint** - Direct Ollama API test
2. **Test LiteLLM endpoint** - OpenAI-compatible API test
3. **Test both endpoints** - Comprehensive test
4. **Continuous load test** - Stress test GPU under sustained load

The benchmark script automatically captures GPU metrics before, during, and after inference.

### Manual Inference Test

```bash
# Test Ollama with llama3.1:8b
time ollama run llama3.1:8b "Explain quantum computing in 3 sentences."

# Watch GPU usage in another terminal
watch -n 1 rocm-smi
```

## Prometheus Monitoring (Service Node Integration)

### ROCm GPU Exporter

A Prometheus exporter runs on the compute node, exposing GPU metrics:

**Endpoint**: `http://100.72.98.106:9101/metrics` (Tailscale IP)

**Metrics exposed**:
- `rocm_gpu_utilization_percent` - GPU usage percentage
- `rocm_gpu_memory_total_bytes` - Total VRAM (16GB = ~17GB)
- `rocm_gpu_memory_used_bytes` - Used VRAM
- `rocm_gpu_memory_utilization_percent` - VRAM usage percentage
- `rocm_gpu_temperature_celsius` - GPU temperature
- `rocm_gpu_power_watts` - Power consumption in watts

**Service management**:
```bash
# Check exporter status
sudo systemctl status rocm-exporter

# View logs
sudo journalctl -u rocm-exporter -f

# Restart exporter
sudo systemctl restart rocm-exporter

# Test endpoint locally
curl http://localhost:9101/metrics
curl http://localhost:9101/health
```

### Prometheus Configuration

Prometheus on the service node is configured to scrape the compute node:

**Location**: `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/monitoring/prometheus-config.yaml`

**Jobs configured**:
- `rocm-gpu-exporter` - GPU metrics from compute node
- `ollama` - Ollama service (if it exposes metrics)
- `litellm` - LiteLLM service metrics

**Access Prometheus**:
- Local: http://192.168.8.185:30090
- Tailscale: http://100.81.76.55:30090

**Check if metrics are being scraped**:
1. Open Prometheus UI
2. Go to Status → Targets
3. Look for `rocm-gpu-exporter` job
4. Should show state "UP" and last scrape time

### Grafana Dashboard

A pre-configured GPU monitoring dashboard is available.

**Dashboard file**: `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/monitoring/grafana-gpu-dashboard.json`

**Panels included**:
- GPU Utilization (time series graph)
- GPU Memory Usage (time series graph)
- GPU Temperature (time series graph)
- GPU Power Consumption (time series graph)
- Current GPU Utilization (stat)
- Memory Utilization (stat)
- Current Temperature (stat)
- Current Power Draw (stat)

**To import into Grafana**:
1. Access Grafana: http://192.168.8.185:30300 (admin/admin123)
2. Go to Dashboards → Import
3. Upload `grafana-gpu-dashboard.json`
4. Select Prometheus as data source
5. Click Import

The dashboard auto-refreshes every 5 seconds.

## Performance Metrics to Watch

### GPU Metrics

**Normal idle state**:
- GPU utilization: 0-5%
- VRAM usage: ~1-2GB (Ollama loaded)
- Temperature: 40-50°C
- Power: 20-40W

**During inference (7B-8B models)**:
- GPU utilization: 60-95%
- VRAM usage: 6-8GB (Q4 quantized models)
- Temperature: 60-75°C
- Power: 150-250W
- Token generation: 20-30 tokens/second (target)

**Warning thresholds**:
- Temperature > 85°C: Check cooling
- Power > 280W: Near TDP limit (290W)
- VRAM > 15GB: Risk of OOM

### System Metrics

**CPU Usage**:
- Normal: 10-30%
- During inference: 40-70% (model loading, pre/post-processing)

**Memory (RAM)**:
- Baseline: ~4-6GB used (OS + services)
- With models loaded: 8-12GB
- Available: 32GB total

**Network**:
- Ollama connections: Check with `ss -tn | grep :11434`
- LiteLLM connections: Check with `ss -tn | grep :8000`

## Troubleshooting

### GPU Not Being Used

```bash
# Check if ROCm detects GPU
rocminfo | grep "Name:" | head -3

# Check Ollama is using GPU
ps aux | grep ollama
# Should show process running

# Check environment variables
systemctl show ollama | grep Environment
# Should include ROCm paths

# Verify model is loaded
curl http://localhost:11434/api/ps
```

### High Temperature

```bash
# Check current temperature
rocm-smi --showtemp

# Check fan speed (if available)
rocm-smi --showfan

# Monitor temperature continuously
watch -n 1 'rocm-smi --showtemp'
```

If temperature consistently exceeds 80°C:
1. Check case airflow
2. Clean GPU fans and heatsink
3. Verify fan curves in BIOS
4. Consider limiting power target

### Poor Inference Performance

```bash
# Run benchmark
./scripts/inference-benchmark.sh

# Check if GPU is actually being used during inference
# Terminal 1:
watch -n 0.5 rocm-smi

# Terminal 2:
ollama run llama3.1:8b "Count from 1 to 100"
```

Expected: GPU utilization should spike to 60-95% during generation.

If GPU usage is low:
- Model might not be optimized for ROCm
- Check Ollama logs: `journalctl -u ollama -f`
- Try different model or quantization
- Verify ROCm installation

## Monitoring During Development

### Watch GPU While Testing

```bash
# Terminal 1: Monitor GPU
./scripts/gpu-monitor.sh

# Terminal 2: Run your tests
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Log GPU Metrics to File

```bash
# Capture metrics every 5 seconds for 5 minutes
for i in {1..60}; do
  echo "=== $(date) ===" >> gpu_metrics.log
  rocm-smi >> gpu_metrics.log
  sleep 5
done
```

### Monitor Multiple Sessions

Use `tmux` or `screen` to monitor different metrics:

```bash
# Install tmux if needed
sudo apt install tmux

# Start tmux session
tmux

# Split panes (Ctrl+B then ")
# Pane 1: ./scripts/gpu-monitor.sh
# Pane 2: htop
# Pane 3: journalctl -u ollama -f
```

## Integration with Open WebUI

When using Open WebUI (http://192.168.8.185:30080), you can monitor performance:

1. **Before starting chat**: Note baseline GPU metrics
2. **During chat**: Watch GPU utilization spike during response generation
3. **After response**: GPU should return to idle

This helps correlate user experience (response time) with system metrics.

## Automated Alerts (Future)

### Prometheus Alerting Rules

Create alerts for critical conditions:

```yaml
# Example alert rules (to be implemented)
groups:
  - name: gpu_alerts
    rules:
      - alert: HighGPUTemperature
        expr: rocm_gpu_temperature_celsius > 85
        for: 5m
        annotations:
          summary: "GPU temperature is high"

      - alert: HighVRAMUsage
        expr: rocm_gpu_memory_utilization_percent > 90
        for: 2m
        annotations:
          summary: "GPU memory usage is high"
```

## Best Practices

1. **Always monitor during initial setup**: Verify GPU acceleration is working
2. **Benchmark new models**: Test performance before deploying to workflows
3. **Set up Grafana dashboard**: Easier to spot trends over time
4. **Log performance data**: Helps troubleshoot issues later
5. **Monitor temperature**: Prevent thermal throttling
6. **Watch VRAM**: Ensure models fit in memory
7. **Compare with CPU**: Verify GPU provides benefit

## Summary of Monitoring Tools

| Tool | Purpose | Update Rate | Best For |
|------|---------|-------------|----------|
| `./scripts/monitor-compute.sh` | Comprehensive monitoring | 5s | General overview |
| `./scripts/gpu-monitor.sh` | GPU-focused monitoring | 2s | Deep GPU analysis |
| `./scripts/inference-benchmark.sh` | Performance testing | On-demand | Benchmarking |
| `rocm-smi` | Manual GPU checks | On-demand | Quick checks |
| Prometheus exporter | Historical data | 15s | Long-term trends |
| Grafana dashboard | Visual monitoring | 5s | Operations dashboard |

## Additional Resources

- **ROCm Documentation**: https://rocm.docs.amd.com
- **Ollama API Docs**: https://github.com/ollama/ollama/blob/main/docs/api.md
- **Prometheus Exporters**: https://prometheus.io/docs/instrumenting/exporters/

---

**Last Updated**: 2025-10-22
**Compute Node**: pesubuntu (100.72.98.106)
**GPU**: AMD Radeon RX 7800 XT (16GB VRAM)
