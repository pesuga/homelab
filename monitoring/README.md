# llama.cpp Performance Monitoring System

🚀 **Complete real-time and historic monitoring solution for your llama.cpp deployment!**

## ✅ What's Available

### 📊 **Real-Time Metrics Collection**
- **Prometheus-compatible metrics** from llama.cpp
- **GPU performance tracking** with token/second speeds
- **System resource monitoring** (CPU, Memory)
- **Model-specific performance** (Kimi-VL, Mistral, etc.)
- **5-second collection intervals** with daemon mode

### 📈 **Historic Data Logging**
- **CSV-based time-series storage** with timestamps
- **Automatic backup** and rotation
- **Export to JSON** for external graphing tools
- **Performance benchmark history** with detailed results

### 🎯 **Interactive Web Dashboard**
- **Real-time charts** with Chart.js visualizations
- **Multiple graph types**: Line charts, bar charts, area charts
- **Responsive design** for mobile and desktop
- **Live updates** with 5-second refresh rate

### 🏃 **Automated Benchmarking**
- **Standardized test suites** with configurable parameters
- **Performance comparison** across models and configurations
- **Detailed timing analysis** (prompt vs prediction speeds)
- **Historical benchmark tracking**

## 🚀 Quick Start

### 1. Start Metrics Collection
```bash
# Start collecting metrics every 5 seconds
./scripts/llamacpp-metrics-collector.sh daemon 5

# View real-time metrics in terminal
./scripts/llamacpp-metrics-collector.sh monitor
```

### 2. Access Web Dashboard
```bash
# Open in browser (if server running)
http://localhost:8082/dashboard.html

# Or start the web server
cd monitoring && node server.js
```

### 3. Run Performance Benchmarks
```bash
# Quick benchmark with default settings
./scripts/llamacpp-metrics-collector.sh benchmark

# Custom benchmark
./scripts/llamacpp-metrics-collector.sh benchmark \
  "current" \
  "Test prompt for performance evaluation" \
  100 \
  5
```

## 📊 Available Metrics

### 🎯 **llama.cpp Performance Metrics**
- `llamacpp:prompt_tokens_total` - Total prompt tokens processed
- `llamacpp:tokens_predicted_total` - Total generation tokens
- `llamacpp:prompt_seconds_total` - Total prompt processing time
- `llamacpp:tokens_predicted_seconds_total` - Total generation time
- `llamacpp:n_decode_total` - Number of decode operations
- `llamacpp:n_busy_slots_per_decode` - Concurrent slot utilization

### 💻 **System Metrics**
- **CPU Usage** - System processor utilization (%)
- **Memory Usage** - RAM utilization (%)
- **GPU Utilization** - AMD RX 7800 XT usage (when available)

### 🚀 **Calculated Performance Metrics**
- **Prompt TPS** - Tokens per second (prompt processing)
- **Prediction TPS** - Tokens per second (text generation)
- **Average Response Time** - Overall latency measurements
- **Throughput Analysis** - Performance over time

## 🔧 Command Reference

### Metrics Collection
```bash
# One-time collection
./scripts/llamacpp-metrics-collector.sh collect

# Start background daemon (interval in seconds)
./scripts/llamacpp-metrics-collector.sh daemon 10

# Real-time monitoring dashboard
./scripts/llamacpp-metrics-collector.sh monitor

# Show historical data (last N hours)
./scripts/llamacpp-metrics-collector.sh history 24

# Export data to JSON
./scripts/llamacpp-metrics-collector.sh export
```

### Benchmarking
```bash
# Standard benchmark (current model, 50 tokens, 5 iterations)
./scripts/llamacpp-metrics-collector.sh benchmark

# Custom benchmark
./scripts/llamacpp-metrics-collector.sh benchmark \
  [model] [prompt] [max_tokens] [iterations]

# Example:
./scripts/llamacpp-metrics-collector.sh benchmark \
  "current" \
  "Performance test with longer prompt" \
  200 \
  10
```

### Web Dashboard API
```bash
# Get current model
curl http://localhost:8082/api/current-model

# Get metrics data
curl http://localhost:8082/api/metrics-data

# Get benchmark history
curl http://localhost:8082/api/benchmarks

# Health check
curl http://localhost:8082/api/health

# System info
curl http://localhost:8082/api/system-info
```

## 📁 File Structure

```
monitoring/
├── dashboard.html          # Web interface
├── server.js               # Node.js backend server
├── package.json            # Node.js dependencies
└── README.md               # This file

logs/metrics/
├── metrics.csv             # Time-series metrics data
├── benchmark_*.csv         # Benchmark results
└── *.json                  # Exported data files

scripts/
├── llamacpp-metrics-collector.sh  # Main metrics tool
├── llamacpp-manager.sh           # Model management
└── test-gpu.sh                   # GPU testing utility
```

## 🎯 Performance Insights

### 📊 **Current Performance (GPU-Enabled)**
- **Model**: Kimi-VL (multimodal) / Mistral-7B (text)
- **GPU**: AMD Radeon RX 7800 XT with 1 layer acceleration
- **Prompt Speed**: ~50 tokens/second
- **Generation Speed**: ~30 tokens/second
- **CPU Usage**: 8-20% during inference
- **Memory Usage**: ~35% system memory

### ⚡ **GPU Acceleration Benefits**
- **1 GPU layer** provides optimal stability + performance balance
- **Vulkan backend** more stable than ROCm for this setup
- **Hybrid CPU+GPU** approach gives good throughput
- **Multimodal support** with vision capabilities for Kimi-VL

### 📈 **Monitoring Capabilities**
- **5-second collection intervals** for real-time tracking
- **Historical data retention** with CSV logging
- **Performance trend analysis** over days/weeks
- **Benchmark comparison** across model switches
- **System resource tracking** for capacity planning

## 🌐 Dashboard Features

### 📊 **Live Charts**
1. **Token Generation Speed** - Real-time TPS monitoring
2. **Model Performance** - Prompt vs prediction timing
3. **Tokens Over Time** - Cumulative usage tracking
4. **System Resources** - CPU and memory utilization

### 🎛️ **Interactive Controls**
- Start/stop monitoring
- Time range selection (hour/week/month)
- Run benchmarks on demand
- Clear and reset data
- Export functionality

### 📱 **Responsive Design**
- Mobile-friendly interface
- Auto-refreshing data
- Color-coded performance indicators
- Model status badges

## 🔍 Troubleshooting

### **Common Issues**

1. **Metrics not collecting**
   ```bash
   # Check if llama.cpp is running
   curl http://localhost:8081/health

   # Check metrics endpoint
   curl http://localhost:8081/metrics
   ```

2. **Web dashboard not accessible**
   ```bash
   # Check if server is running
   ps aux | grep node | grep server.js

   # Restart server
   cd monitoring && node server.js
   ```

3. **GPU not detected**
   ```bash
   # Test GPU detection
   ./scripts/test-gpu.sh

   # Check ROCm status
   rocminfo
   ```

### **Performance Optimization**
- Use **1 GPU layer** for optimal stability
- **Monitor CPU usage** - high CPU may indicate bottlenecks
- **Check memory usage** - ensure sufficient RAM for large contexts
- **Benchmark regularly** to track performance degradation

## 📞 Getting Help

```bash
# Show all available commands
./scripts/llamacpp-metrics-collector.sh help

# Check system status
./scripts/llamacpp-manager.sh status

# View logs
tail -f /tmp/metrics_daemon.log
tail -f /tmp/monitoring_server.log
```

---

**🎉 Your llama.cpp deployment now has comprehensive monitoring with real-time metrics, historic logging, and performance benchmarking!**