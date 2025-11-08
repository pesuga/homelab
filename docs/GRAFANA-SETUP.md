# 📊 Grafana Dashboard Setup Guide

## Overview

This guide explains how to access Grafana and import the pre-configured monitoring dashboards for your homelab.

## 🔐 Access Grafana

### From Service Node or Local Network:
- **URL**: http://192.168.8.185:30300
- **Username**: `admin`
- **Password**: `admin123`

### Via Tailscale (Remote Access):
- **URL**: http://100.81.76.55:30300
- **Username**: `admin`
- **Password**: `admin123`

## 📥 Importing the Homelab Overview Dashboard

### Method 1: Import via UI

1. **Open Grafana** in your browser
2. **Log in** with credentials above
3. Click **"☰"** menu (top-left) → **Dashboards** → **Import**
4. Click **"Upload dashboard JSON file"**
5. Select: `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/monitoring/homelab-overview-dashboard.json`
6. Click **"Load"**
7. Select **"Prometheus"** as the data source
8. Click **"Import"**

### Method 2: Import via CLI (from service node)

```bash
ssh pesu@192.168.8.185

# Copy dashboard JSON to a location accessible from service node
# Then import via Grafana API
curl -X POST \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  http://localhost:30300/api/dashboards/db \
  -d @/path/to/homelab-overview-dashboard.json
```

## 📊 Dashboard Features

The **Homelab Overview** dashboard includes:

### GPU Metrics Section
- **GPU Utilization Gauge** (0-100%)
  - Green: 0-60%
  - Yellow: 60-85%
  - Red: 85-100%

- **GPU Memory Usage Gauge** (0-100%)
  - Shows VRAM utilization
  - Thresholds: Green < 70%, Yellow < 90%, Red ≥ 90%

- **GPU Temperature Gauge** (Celsius)
  - Green: < 75°C
  - Yellow: 75-85°C
  - Red: > 85°C

- **GPU Power Draw Gauge** (Watts)
  - Range: 0-290W (RX 7800 XT TDP)
  - Green: < 200W
  - Yellow: 200-260W
  - Red: > 260W

### Time Series Graphs
- **GPU Utilization Over Time**
  - 5-second refresh rate
  - Shows usage trends
  - Stats: Mean, Last, Max

- **GPU Memory Usage Over Time**
  - Used VRAM vs Total VRAM
  - Helps identify memory leaks
  - Shows model loading patterns

- **Compute Node CPU Usage**
  - System-wide CPU utilization
  - Useful for identifying bottlenecks

- **Compute Node Memory Usage**
  - RAM usage percentage
  - Monitors system memory pressure

## 🎨 Customizing Dashboards

### Adding New Panels

1. Click **"Add"** → **"Visualization"**
2. Select **"Prometheus"** as data source
3. Enter a PromQL query (examples below)
4. Configure visualization type
5. Save panel

### Useful PromQL Queries

**GPU Metrics**:
```promql
# GPU utilization
rocm_gpu_utilization_percent

# VRAM usage in GB
rocm_gpu_memory_used_bytes / 1073741824

# GPU temperature
rocm_gpu_temperature_celsius

# GPU power consumption
rocm_gpu_power_watts
```

**System Metrics**:
```promql
# CPU usage (compute node)
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle", node="pesubuntu"}[5m])) * 100)

# Memory usage (compute node)
100 * (1 - (node_memory_MemAvailable_bytes{node="pesubuntu"} / node_memory_MemTotal_bytes{node="pesubuntu"}))

# Disk usage
100 - ((node_filesystem_avail_bytes{node="pesubuntu",mountpoint="/"} * 100) / node_filesystem_size_bytes{node="pesubuntu",mountpoint="/"})

# Network traffic (bytes received)
rate(node_network_receive_bytes_total{node="pesubuntu",device!~"lo|veth.*"}[5m])
```

**K8s Metrics**:
```promql
# Pod count by namespace
count by(namespace) (kube_pod_info)

# Container CPU usage
sum(rate(container_cpu_usage_seconds_total{namespace="homelab"}[5m])) by (pod)

# Container memory usage
sum(container_memory_working_set_bytes{namespace="homelab"}) by (pod)
```

## 🔔 Setting Up Alerts

### Example: High GPU Temperature Alert

1. Go to **Alerting** → **Alert rules** → **New alert rule**
2. **Query**:
   ```promql
   rocm_gpu_temperature_celsius > 85
   ```
3. **Condition**: `WHEN last() OF query(A) IS ABOVE 85`
4. **Evaluation**: Every 1m for 5m
5. **Annotations**:
   - Summary: `GPU temperature is critically high`
   - Description: `GPU temperature is {{ $value }}°C, which exceeds the safe threshold of 85°C`
6. **Save**

### Example: High VRAM Usage Alert

```promql
rocm_gpu_memory_utilization_percent > 90
```

Condition: Trigger if VRAM usage > 90% for 2 minutes

## 📱 Dashboard Tips

### Auto-Refresh
- Dashboard refreshes every **5 seconds** by default
- Change in top-right: Refresh dropdown
- Options: 5s, 10s, 30s, 1m, 5m

### Time Range
- Default: Last 30 minutes
- Click time range (top-right) to adjust
- Useful ranges:
  - Last 5 minutes: Real-time monitoring
  - Last 1 hour: Recent trends
  - Last 24 hours: Daily patterns
  - Last 7 days: Weekly analysis

### Variables (Advanced)
You can add template variables for dynamic filtering:

1. **Dashboard settings** → **Variables** → **Add variable**
2. **Type**: Query
3. **Query**: `label_values(rocm_gpu_utilization_percent, node)`
4. Use in queries: `rocm_gpu_utilization_percent{node="$node"}`

## 🖥️ Monitoring During LLM Inference

### Best Practices

1. **Before testing**:
   - Open Grafana dashboard
   - Set refresh to 5s
   - Set time range to "Last 5 minutes"

2. **During testing**:
   - Watch GPU utilization spike
   - Monitor VRAM usage
   - Check temperature rise
   - Observe power draw

3. **After testing**:
   - Review peak metrics
   - Check for thermal throttling
   - Analyze performance patterns

### Example Workflow

```bash
# Terminal 1: Open Grafana
# Navigate to: http://192.168.8.185:30300

# Terminal 2: Run LLM inference
ollama run llama3.1:8b "Explain quantum computing"

# Observe in Grafana:
# - GPU utilization jumps to 60-95%
# - VRAM usage increases by 6-8GB
# - Temperature rises to 60-75°C
# - Power draw increases to 150-250W
```

## 🔍 Troubleshooting

### Dashboard Shows "No Data"

**Check Prometheus**:
```bash
# Verify Prometheus is running
ssh pesu@192.168.8.185 "kubectl get pods -n homelab -l app=prometheus"

# Check if metrics are being scraped
curl -s http://192.168.8.185:30090/api/v1/targets | grep rocm
```

**Check Data Source**:
1. Grafana → **Configuration** → **Data Sources**
2. Click **"Prometheus"**
3. Scroll down, click **"Test"**
4. Should show: "Data source is working"

### Metrics Not Updating

**Check Exporters**:
```bash
# ROCm GPU Exporter (compute node)
sudo systemctl status rocm-exporter
curl http://localhost:9101/metrics | grep rocm_gpu

# Node Exporter (compute node)
sudo systemctl status node-exporter
curl http://localhost:9100/metrics | grep node_cpu
```

### Can't Access Grafana

**Check Service**:
```bash
ssh pesu@192.168.8.185

# Check Grafana pod
kubectl get pods -n homelab -l app=grafana

# Check Grafana logs
kubectl logs -n homelab -l app=grafana --tail=50

# Check service
kubectl get svc -n homelab grafana
```

**Try via Pod IP**:
```bash
POD_IP=$(kubectl get pods -n homelab -l app=grafana -o jsonpath='{.items[0].status.podIP}')
curl http://$POD_IP:3000/api/health
```

## 📖 Additional Resources

- **Grafana Documentation**: https://grafana.com/docs/grafana/latest/
- **PromQL Guide**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Prometheus Best Practices**: https://prometheus.io/docs/practices/naming/

## 🎯 Next Steps

1. **Explore the dashboard** - Familiarize yourself with the panels
2. **Run LLM tests** - Observe metrics during inference
3. **Create custom panels** - Add metrics specific to your use case
4. **Set up alerts** - Get notified of issues proactively
5. **Export & share** - Save dashboard configs for backup

---

**Last Updated**: 2025-10-22
**Grafana Version**: 11.3.2
**Dashboard**: Homelab Overview v1.0
