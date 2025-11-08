# Prometheus Metrics Analysis

**Date**: 2025-10-25
**Prometheus Version**: Running on http://100.81.76.55:30090

---

## Available Metrics Summary

### Scrape Targets (Up Status)

| Job | Instance | Status | Description |
|-----|----------|--------|-------------|
| `prometheus` | prometheus | ✅ Up | Prometheus self-monitoring |
| `kubernetes-apiservers` | 192.168.86.169:6443 | ✅ Up | K3s API server |
| `kubernetes-cadvisor` | asuna | ✅ Up | Container metrics (cAdvisor) |
| `kubernetes-nodes` | asuna | ❌ Down | Node metrics (troubleshoot) |
| `kubernetes-pods` | 10.42.0.8:9100 | ✅ Up | Pod-level metrics |
| `kubernetes-pods` | 10.42.0.34:9402 | ✅ Up | Pod-level metrics |
| `kubernetes-pods` | 10.42.0.33:9402 | ✅ Up | Pod-level metrics |
| `kubernetes-pods` | 10.42.0.35:9402 | ✅ Up | Pod-level metrics |
| `compute-system` | 100.72.98.106:9100 | ✅ Up | Compute node (node_exporter) |
| `compute-gpu` | 100.72.98.106:9101 | ✅ Up | GPU metrics (ROCm exporter) |

**Note**: `kubernetes-nodes` job is down - need to investigate node_exporter on service node.

---

## Metrics Categories

### 1. Container Metrics (cAdvisor)

**Source**: Kubernetes cAdvisor (built into kubelet)
**Prefix**: `container_*`

**Available Metrics**:
- **CPU**: `container_cpu_usage_seconds_total`, `container_cpu_system_seconds_total`, `container_cpu_user_seconds_total`
- **Memory**: `container_memory_usage_bytes`, `container_memory_working_set_bytes`, `container_memory_cache`, `container_memory_rss`, `container_memory_swap`
- **Network**: `container_network_receive_bytes_total`, `container_network_transmit_bytes_total`, `container_network_receive_packets_total`, `container_network_transmit_packets_total`
- **Filesystem**: `container_fs_usage_bytes`, `container_fs_limit_bytes`, `container_fs_reads_total`, `container_fs_writes_total`
- **Processes**: `container_processes`, `container_threads`, `container_file_descriptors`

**Dashboard Use Cases**:
- Per-pod resource usage
- Container restart detection (`container_last_seen`)
- OOM events (`container_oom_events_total`)
- Network I/O by container

---

### 2. Node Metrics (node_exporter)

**Source**: Node Exporter (running on compute node 100.72.98.106)
**Prefix**: `node_*`

**Available Metrics**:
- **CPU**: `node_cpu_seconds_total`, `node_cpu_scaling_frequency_hertz`
- **Memory**: `node_memory_*` (need to verify with full query)
- **Disk**: `node_disk_read_bytes_total`, `node_disk_written_bytes_total`, `node_disk_io_time_seconds_total`
- **Filesystem**: `node_filesystem_avail_bytes`, `node_filesystem_size_bytes` (likely available)
- **Network**: `node_network_receive_bytes_total`, `node_network_transmit_bytes_total` (likely available)
- **System**: `node_boot_time_seconds`, `node_context_switches_total`, `node_entropy_available_bits`

**Note**: Service node (asuna) is missing node_exporter - should be deployed.

---

### 3. Kubernetes Metrics

**Source**: K3s API server and controllers
**Prefix**: `kube_*`

**Available Metrics**:
- **API Server**: `apiserver_request_duration_seconds_*`, `apiserver_current_inflight_requests`
- **Resource Allocators**: `kube_apiserver_clusterip_allocator_*`, `kube_apiserver_nodeport_allocator_*`
- **Authentication/Authorization**: `apiserver_authorization_decisions_total`, `apiserver_delegated_authn_request_*`
- **Admission**: `apiserver_admission_controller_admission_duration_seconds_*`

**Dashboard Use Cases**:
- API server latency
- Request rate and errors
- Resource allocation (IPs, ports)

---

### 4. GPU Metrics (compute node)

**Source**: Custom ROCm exporter on 100.72.98.106:9101
**Status**: ✅ Scraping successfully

**Expected Metrics** (need to verify):
- GPU utilization
- VRAM usage
- GPU temperature
- Power consumption
- SM (Streaming Multiprocessor) activity

**Dashboard Priority**: HIGH (for LLM inference monitoring)

---

### 5. Application Metrics

#### Currently Missing:
- **PostgreSQL**: No `pg_*` metrics (postgres_exporter not installed)
- **Redis**: No `redis_*` metrics (redis_exporter not installed)
- **N8n**: No custom metrics exported
- **Flowise**: No custom metrics exported
- **Open WebUI**: No custom metrics exported

#### Recommendations:
1. Deploy `postgres_exporter` as sidecar or separate pod
2. Deploy `redis_exporter` as sidecar or separate pod
3. Configure N8n to export Prometheus metrics (if supported)
4. Add custom instrumentation for critical workflows

---

## Metrics Gaps & Fixes

### Gap 1: Service Node System Metrics
**Problem**: `kubernetes-nodes` job down (asuna node_exporter missing)
**Solution**: Deploy node_exporter DaemonSet to K3s cluster
**Priority**: HIGH

### Gap 2: Database Metrics
**Problem**: No PostgreSQL or Redis metrics
**Solution**:
- Deploy postgres_exporter (sidecar container or separate deployment)
- Deploy redis_exporter (sidecar container or separate deployment)
**Priority**: MEDIUM

### Gap 3: Application-Level Metrics
**Problem**: No insight into N8n workflow execution, Flowise flows, etc.
**Solution**:
- Enable N8n metrics endpoint (check documentation)
- Add custom Prometheus client to critical applications
- Use log-based metrics as fallback (requires Loki)
**Priority**: LOW (can use pod metrics as proxy initially)

---

## Dashboard Design Based on Available Metrics

### Dashboard 1: Homelab Overview
**Data Sources**: container_*, node_*, kube_*, up

**Panels**:
1. Cluster Health (up metrics) - ✅ Ready
2. Overall CPU Usage (container_cpu_usage_seconds_total aggregated) - ✅ Ready
3. Overall Memory Usage (container_memory_working_set_bytes) - ✅ Ready
4. Network I/O (container_network_*_total) - ✅ Ready
5. Disk Usage (node_filesystem_avail_bytes - PENDING node_exporter fix)
6. Pod Status (kube_pod_status_phase - need to verify metric exists)

---

### Dashboard 2: Kubernetes Cluster
**Data Sources**: kube_*, container_*, apiserver_*

**Panels**:
1. Node Resources (node_* - PENDING fix)
2. Pod Resource Usage by Namespace (container_*)  - ✅ Ready
3. Container Restarts (container_last_seen) - ✅ Ready
4. Network Traffic by Pod (container_network_*) - ✅ Ready
5. API Server Latency (apiserver_request_duration_seconds) - ✅ Ready
6. Persistent Volume Usage (kubelet_volume_*  - need to verify)

---

### Dashboard 3: Compute Node (LLM Infrastructure)
**Data Sources**: node_* (100.72.98.106), GPU metrics

**Panels**:
1. CPU Usage (node_cpu_seconds_total) - ✅ Ready
2. Memory Usage (node_memory_*) - ✅ Ready
3. GPU Utilization - ⚠️ Need to query GPU metrics
4. VRAM Usage - ⚠️ Need to query GPU metrics
5. Disk I/O (node_disk_*) - ✅ Ready
6. Network I/O (node_network_*) - ✅ Ready
7. System Load (node_load*) - Need to verify

---

### Dashboard 4: Service Health
**Data Sources**: up, container_memory_working_set_bytes, container_cpu_usage_seconds_total

**Panels**:
1. Service Availability (up metric by job) - ✅ Ready
2. N8n Resource Usage (container metrics filtered by pod) - ✅ Ready
3. PostgreSQL Resource Usage (container metrics) - ✅ Ready
4. Redis Resource Usage (container metrics) - ✅ Ready
5. Flowise Resource Usage (container metrics) - ✅ Ready
6. Grafana Resource Usage (container metrics) - ✅ Ready
7. Prometheus Resource Usage (container metrics) - ✅ Ready

---

## Priority Actions

### Immediate (Before Dashboard Creation)
1. ✅ Query GPU metrics to understand available data
2. ⚠️ Fix kubernetes-nodes scrape target (deploy node_exporter to service node)
3. ⚠️ Verify kube_pod_* metrics availability

### Short-term (Dashboard Enhancement)
4. Deploy postgres_exporter
5. Deploy redis_exporter
6. Add node_exporter to service node

### Long-term (Advanced Monitoring)
7. Enable N8n metrics
8. Add Loki for log aggregation
9. Create LLM-specific metrics (tokens/sec, latency, etc.)
10. Set up AlertManager rules

---

## Queries for Dashboard Creation

### Query 1: Total Cluster CPU Usage
```promql
sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (namespace)
```

### Query 2: Total Cluster Memory Usage
```promql
sum(container_memory_working_set_bytes{container!=""}) by (namespace)
```

### Query 3: Pod Restarts (last hour)
```promql
increase(kube_pod_container_status_restarts_total[1h])
```

### Query 4: Network I/O Rate
```promql
sum(rate(container_network_receive_bytes_total[5m])) by (pod)
```

### Query 5: Disk Usage Percentage (when node_exporter fixed)
```promql
(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100
```

### Query 6: Service Uptime
```promql
up{job=~"kubernetes-.*|prometheus|compute-.*"}
```

---

## Next Steps

1. Query GPU metrics endpoint to catalog available metrics
2. Test sample PromQL queries in Grafana
3. Create first dashboard (Homelab Overview) using available metrics
4. Deploy node_exporter to service node
5. Deploy database exporters
6. Iterate on dashboard designs

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
