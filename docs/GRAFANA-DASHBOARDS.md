# Grafana Dashboards Setup Guide

**Version**: 1.0
**Date**: 2025-10-25
**Grafana Version**: 9.0+

---

## Table of Contents

- [Overview](#overview)
- [Available Metrics](#available-metrics)
- [Dashboard Catalog](#dashboard-catalog)
- [Installation Methods](#installation-methods)
- [Dashboard Creation Guide](#dashboard-creation-guide)
- [Importing Community Dashboards](#importing-community-dashboards)
- [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers setting up Grafana dashboards for comprehensive homelab monitoring. Dashboards are categorized by function:

- **Homelab Overview**: High-level cluster health
- **Kubernetes Cluster**: Detailed K8s metrics
- **Service Health**: Individual service monitoring
- **Compute Node**: LLM inference node metrics
- **Databases**: PostgreSQL and Redis performance

**Grafana Access**:
- **Local**: http://100.81.76.55:30300
- **HTTPS** (future): https://grafana.homelab.pesulabs.net
- **Credentials**: admin / admin123 (default - change in production)

---

## Available Metrics

### Current Prometheus Targets

| Target | Status | Metrics | Description |
|--------|--------|---------|-------------|
| `kubernetes-apiservers` | ✅ Up | apiserver_* | K8s API server performance |
| `kubernetes-cadvisor` | ✅ Up | container_* | Container resource usage |
| `kubernetes-pods` | ✅ Up | Pod-specific | Application metrics |
| `compute-system` | ✅ Up | node_* | Compute node system metrics |
| `compute-gpu` | ✅ Up | GPU-specific | GPU utilization (ROCm) |
| `prometheus` | ✅ Up | prometheus_* | Prometheus self-monitoring |
| `kubernetes-nodes` | ❌ Down | node_* | Service node (needs fix) |

**Note**: See [METRICS-ANALYSIS.md](./METRICS-ANALYSIS.md) for detailed metrics breakdown.

### Key Metric Families

1. **Container Metrics** (`container_*`): CPU, memory, network, filesystem per container
2. **Node Metrics** (`node_*`): System-level CPU, disk, network, memory
3. **Kubernetes Metrics** (`kube_*`, `apiserver_*`): Cluster state, API performance
4. **GPU Metrics**: VRAM, utilization, temperature (compute node)

---

## Dashboard Catalog

### 1. Homelab Overview Dashboard

**Purpose**: Single-pane-of-glass view of entire homelab health

**Panels**:
- Cluster Health (all services up/down)
- Total CPU Usage (all containers)
- Total Memory Usage
- Network I/O Rate
- Pod Count by Namespace
- Recent Alerts

**Queries**:
```promql
# Service uptime
up{job=~"kubernetes-.*|prometheus|compute-.*"}

# Total cluster CPU
sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (namespace)

# Total cluster memory
sum(container_memory_working_set_bytes{container!=""}) by (namespace)

# Network I/O
sum(rate(container_network_receive_bytes_total[5m]))
sum(rate(container_network_transmit_bytes_total[5m]))
```

**Dashboard ID**: `homelab-overview.json`

---

### 2. Kubernetes Cluster Dashboard

**Purpose**: Detailed Kubernetes cluster monitoring

**Panels**:
- Node Resources (CPU/Memory/Disk per node)
- Pod Status by Namespace (running/pending/failed)
- Container Restarts (last 24h)
- API Server Latency
- Network Traffic by Pod
- Storage Usage (PVCs)

**Queries**:
```promql
# Pod restarts
increase(kube_pod_container_status_restarts_total[1h])

# API server latency (P95)
histogram_quantile(0.95,
  rate(apiserver_request_duration_seconds_bucket[5m]))

# Container memory by pod
sum(container_memory_working_set_bytes{container!=""}) by (pod, namespace)
```

**Recommended Import**: Grafana ID `15760` (Kubernetes Cluster Monitoring)

---

### 3. Service Health Dashboard

**Purpose**: Monitor individual homelab services (N8n, PostgreSQL, Redis, etc.)

**Panels** (per service):
- CPU Usage
- Memory Usage
- Network I/O
- Uptime
- Restart Count

**Services Monitored**:
- N8n
- Flowise
- PostgreSQL
- Redis
- Qdrant (when deployed)
- Prometheus
- Grafana
- Open WebUI

**Queries**:
```promql
# N8n CPU usage
rate(container_cpu_usage_seconds_total{pod=~"n8n-.*",container!=""}[5m])

# PostgreSQL memory
container_memory_working_set_bytes{pod=~"postgres-.*",container!=""}

# Service uptime (time since last restart)
time() - container_start_time_seconds{pod=~"n8n-.*"}
```

**Dashboard ID**: `service-health.json`

---

### 4. Compute Node Dashboard

**Purpose**: Monitor LLM inference node (pesubuntu - 100.72.98.106)

**Panels**:
- CPU Usage by Core
- Memory Usage
- GPU Utilization
- VRAM Usage
- Disk I/O
- Network I/O
- System Load Average
- GPU Temperature

**Queries**:
```promql
# CPU usage by mode
rate(node_cpu_seconds_total{instance="100.72.98.106:9100"}[5m])

# Memory usage
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes

# Disk I/O
rate(node_disk_read_bytes_total{instance="100.72.98.106:9100"}[5m])
rate(node_disk_written_bytes_total{instance="100.72.98.106:9100"}[5m])

# GPU metrics (verify metric names from exporter)
# Example: rocm_gpu_utilization, rocm_vram_used_bytes
```

**Dashboard ID**: `compute-node.json`

---

### 5. Database Performance Dashboard

**Purpose**: PostgreSQL and Redis monitoring

**PostgreSQL Panels** (when postgres_exporter added):
- Active Connections
- Query Rate
- Cache Hit Ratio
- Transaction Rate
- Database Size
- Slow Queries

**Redis Panels** (when redis_exporter added):
- Memory Usage
- Commands per Second
- Hit/Miss Ratio
- Connected Clients
- Keyspace Size

**Current State**: Using container metrics only (CPU/memory)

**Future Queries** (with exporters):
```promql
# PostgreSQL connections
pg_stat_database_numbackends

# PostgreSQL cache hit ratio
rate(pg_stat_database_blks_hit[5m]) /
  (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m]))

# Redis memory
redis_memory_used_bytes

# Redis hit ratio
redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)
```

**Dashboard ID**: `database-performance.json`

---

## Installation Methods

### Method 1: Manual Creation (Recommended for Learning)

**Best for**: Understanding queries, custom dashboards

**Steps**:
1. Access Grafana: http://100.81.76.55:30300
2. Click **+** → **Dashboard** → **Add visualization**
3. Select **Prometheus** as data source
4. Write PromQL query
5. Configure visualization (Graph, Gauge, Stat, etc.)
6. Repeat for each panel
7. **Save dashboard**
8. **Export JSON**: Settings → JSON Model → Copy
9. Save to `infrastructure/kubernetes/monitoring/dashboards/`

**Pros**: Full control, learn PromQL
**Cons**: Time-consuming

---

### Method 2: Import Community Dashboards (Fastest)

**Best for**: Quick setup with proven dashboards

**Steps**:
1. Access Grafana: http://100.81.76.55:30300
2. Click **+** → **Import**
3. Enter Dashboard ID (from grafana.com)
4. Select **Prometheus** as data source
5. Click **Import**
6. Customize if needed
7. Export JSON for version control

**Recommended Dashboard IDs**:
| ID | Name | Use Case |
|----|------|----------|
| `1860` | Node Exporter Full | System metrics (compute node) |
| `15760` | Kubernetes Cluster Monitoring | K8s overview |
| `9628` | PostgreSQL Database | PostgreSQL (requires postgres_exporter) |
| `11835` | Redis Dashboard | Redis (requires redis_exporter) |
| `3662` | Prometheus 2.0 Stats | Prometheus self-monitoring |

**Pros**: Fast, community-tested
**Cons**: May need customization

---

### Method 3: Provisioned Dashboards (GitOps-friendly)

**Best for**: Automated, version-controlled dashboards

**Steps**:

1. **Create dashboard JSON** files in `infrastructure/kubernetes/monitoring/dashboards/`

2. **Create ConfigMap** for dashboard provisioning:

```yaml
# infrastructure/kubernetes/monitoring/dashboards/provisioning/dashboards.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-provider
  namespace: homelab
data:
  dashboards.yaml: |
    apiVersion: 1
    providers:
      - name: 'default'
        orgId: 1
        folder: 'Homelab'
        type: file
        disableDeletion: false
        updateIntervalSeconds: 30
        allowUiUpdates: true
        options:
          path: /var/lib/grafana/dashboards
```

3. **Create ConfigMap for each dashboard**:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-homelab-overview
  namespace: homelab
data:
  homelab-overview.json: |
    {
      "dashboard": { ... },
      "overwrite": true
    }
```

4. **Update Grafana Deployment** to mount ConfigMaps:

```yaml
volumeMounts:
  - name: dashboard-provider
    mountPath: /etc/grafana/provisioning/dashboards
  - name: dashboard-homelab-overview
    mountPath: /var/lib/grafana/dashboards/homelab-overview.json
    subPath: homelab-overview.json

volumes:
  - name: dashboard-provider
    configMap:
      name: grafana-dashboard-provider
  - name: dashboard-homelab-overview
    configMap:
      name: grafana-dashboard-homelab-overview
```

5. **Apply changes**:

```bash
kubectl apply -f infrastructure/kubernetes/monitoring/dashboards/
kubectl rollout restart deployment/grafana -n homelab
```

**Pros**: Automated, version-controlled, GitOps-compatible
**Cons**: More complex setup

---

## Dashboard Creation Guide

### Step-by-Step: Create "Homelab Overview" Dashboard

#### Step 1: Access Grafana

```bash
# Open browser
http://100.81.76.55:30300

# Login: admin / admin123
```

#### Step 2: Create New Dashboard

1. Click **+** (top-right) → **Dashboard**
2. Click **Add visualization**
3. Select **Prometheus** data source

#### Step 3: Add "Service Health" Panel

1. **Query**:
   ```promql
   up{job=~"kubernetes-.*|prometheus|compute-.*"}
   ```

2. **Visualization**: **Stat**

3. **Options**:
   - Value: Last (not null)
   - Show: Value and name
   - Color mode: Value

4. **Value mappings**:
   - 1 → "Up" (green)
   - 0 → "Down" (red)

5. **Title**: "Service Health"

6. Click **Apply**

#### Step 4: Add "CPU Usage" Panel

1. Click **Add** → **Visualization**

2. **Query**:
   ```promql
   sum(rate(container_cpu_usage_seconds_total{container!="",namespace="homelab"}[5m])) by (pod)
   ```

3. **Visualization**: **Time series**

4. **Legend**: {{pod}}

5. **Title**: "CPU Usage by Pod"

6. Click **Apply**

#### Step 5: Add "Memory Usage" Panel

1. **Query**:
   ```promql
   sum(container_memory_working_set_bytes{container!="",namespace="homelab"}) by (pod)
   ```

2. **Visualization**: **Time series**

3. **Unit**: bytes (IEC)

4. **Title**: "Memory Usage by Pod"

5. Click **Apply**

#### Step 6: Save Dashboard

1. Click **Save** (top-right)
2. **Name**: "Homelab Overview"
3. **Folder**: Create "Homelab" folder
4. Click **Save**

#### Step 7: Export for Version Control

1. Click **Dashboard settings** (gear icon)
2. **JSON Model**
3. **Copy to clipboard**
4. Save to `infrastructure/kubernetes/monitoring/dashboards/homelab-overview.json`

---

## Importing Community Dashboards

### Example: Import Node Exporter Dashboard

```bash
# Access Grafana UI
http://100.81.76.55:30300

# Steps:
# 1. Click + → Import
# 2. Enter Dashboard ID: 1860
# 3. Click "Load"
# 4. Select Prometheus data source
# 5. Click "Import"
```

**Customization Tips**:
- Edit panel queries to filter by instance (e.g., `{instance="100.72.98.106:9100"}`)
- Remove irrelevant panels
- Adjust time ranges
- Update thresholds for alerts

---

## Common PromQL Queries

### Container Resource Usage

```promql
# CPU usage by pod (in cores)
sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod)

# Memory usage by pod (in bytes)
sum(container_memory_working_set_bytes{container!=""}) by (pod)

# Network receive rate
sum(rate(container_network_receive_bytes_total[5m])) by (pod)

# Network transmit rate
sum(rate(container_network_transmit_bytes_total[5m])) by (pod)
```

### Node System Metrics

```promql
# CPU usage by mode
avg(rate(node_cpu_seconds_total[5m])) by (mode)

# Available memory
node_memory_MemAvailable_bytes

# Disk usage percentage
(node_filesystem_size_bytes - node_filesystem_avail_bytes) /
  node_filesystem_size_bytes * 100

# Disk I/O
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])
```

### Kubernetes Metrics

```promql
# Pod count by namespace
count(kube_pod_info) by (namespace)

# Container restarts in last hour
increase(kube_pod_container_status_restarts_total[1h])

# API server request rate
sum(rate(apiserver_request_total[5m])) by (verb, resource)
```

---

## Troubleshooting

### Issue: "No data" in panels

**Cause**: Metric doesn't exist or query is incorrect

**Fix**:
1. Test query in Prometheus: http://100.81.76.55:30090
2. Check if target is scraping: **Status** → **Targets**
3. Verify metric name: **Graph** → search for metric
4. Adjust query syntax

---

### Issue: Grafana can't connect to Prometheus

**Cause**: Data source misconfigured

**Fix**:
1. Go to **Configuration** → **Data Sources**
2. Edit **Prometheus**
3. **URL**: `http://prometheus-svc.homelab.svc.cluster.local:9090`
4. Click **Save & Test**

---

### Issue: Dashboard panels load slowly

**Cause**: Too much data or complex queries

**Fix**:
1. Reduce time range (e.g., last 1h instead of 24h)
2. Increase query interval (e.g., `[5m]` → `[1m]`)
3. Add filters to reduce cardinality
4. Enable query caching in Prometheus

---

### Issue: Imported dashboard shows wrong data

**Cause**: Instance/job labels don't match

**Fix**:
1. Edit panel
2. Update query to match your labels:
   ```promql
   # Before:
   node_cpu_seconds_total{instance="node1"}

   # After:
   node_cpu_seconds_total{instance="100.72.98.106:9100"}
   ```

---

## Next Steps

1. **Immediate**:
   - Import community dashboards for quick setup
   - Create "Homelab Overview" dashboard manually
   - Export dashboards to version control

2. **Short-term**:
   - Deploy postgres_exporter and redis_exporter
   - Create Database Performance dashboard
   - Fix kubernetes-nodes scrape target

3. **Long-term**:
   - Set up dashboard provisioning (Method 3)
   - Create custom LLM inference dashboard
   - Add AlertManager integration
   - Set up Loki for log aggregation

---

## Resources

- **Grafana Documentation**: https://grafana.com/docs/
- **PromQL Basics**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Dashboard Library**: https://grafana.com/grafana/dashboards/
- **Grafana Dashboards Best Practices**: https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
