# Log Aggregation Implementation Plan

## Overview

Implementing Loki + Promtail for centralized log aggregation across the homelab infrastructure. This will provide:
- Centralized log collection from all pods and nodes
- Query logs via Grafana Explore
- Alert on log patterns
- Retain logs for debugging and troubleshooting

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Service Node (asuna)                     │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   N8n    │  │PostgreSQL│  │  Redis   │  │  Qdrant  │   │
│  │   Pod    │  │   Pod    │  │   Pod    │  │   Pod    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                          │                                  │
│                    ┌─────▼──────┐                           │
│                    │  Promtail  │ (DaemonSet)               │
│                    │  (Agent)   │                           │
│                    └─────┬──────┘                           │
│                          │                                  │
│                    ┌─────▼──────┐                           │
│                    │    Loki    │ (StatefulSet)             │
│                    │  (Server)  │                           │
│                    └─────┬──────┘                           │
│                          │                                  │
│                    ┌─────▼──────┐                           │
│                    │  Grafana   │ ◄─── Query logs           │
│                    │ (Explore)  │                           │
│                    └────────────┘                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Compute Node (pesubuntu)                    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Ollama  │  │ LiteLLM  │  │   ROCm   │                  │
│  │(systemd) │  │(systemd) │  │ Exporter │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │             │              │                        │
│       └─────────────┴──────────────┘                        │
│                     │                                       │
│               ┌─────▼──────┐                                │
│               │  Promtail  │ (systemd service)              │
│               │  (Agent)   │                                │
│               └─────┬──────┘                                │
│                     │                                       │
│                     │ Push logs to Loki                     │
│                     │ (via Tailscale IP)                    │
│                     └───────────────────────────────────────┼──►
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Loki (Log Aggregation Server)
- **Deployment**: StatefulSet in `homelab` namespace
- **Storage**: 20Gi PersistentVolumeClaim for log retention
- **Retention**: 7 days (configurable)
- **Access**: ClusterIP service + NodePort for external access
- **Resource Limits**: 1 CPU, 2Gi RAM (moderate homelab workload)

### 2. Promtail (Log Shipping Agent)
- **Kubernetes Deployment**: DaemonSet on service node
  - Mounts `/var/log/pods` to collect pod logs
  - Mounts `/var/log/containers` for container logs
  - Automatic Kubernetes metadata enrichment
- **Compute Node Deployment**: systemd service
  - Collects journald logs (Ollama, LiteLLM, system services)
  - Scrapes log files from `/var/log`
  - Pushes to Loki via Tailscale IP

### 3. Grafana Integration
- **Data Source**: Loki added to Grafana
- **Explore**: Query logs with LogQL
- **Dashboards**: Pre-built log dashboards for:
  - Kubernetes pod logs
  - Service-specific logs (N8n, PostgreSQL, etc.)
  - Compute node system logs
  - Error rate tracking

## Implementation Steps

### Phase 1: Deploy Loki (15 min)
1. Create Loki ConfigMap with retention and storage settings
2. Create StatefulSet with PVC for log storage
3. Create Service (ClusterIP + NodePort on 30314)
4. Verify Loki API is accessible

### Phase 2: Deploy Promtail on Service Node (15 min)
1. Create Promtail ConfigMap with Kubernetes scrape configs
2. Create DaemonSet with host volume mounts
3. Verify Promtail is shipping logs to Loki
4. Check Loki for incoming log streams

### Phase 3: Configure Grafana (10 min)
1. Add Loki data source to Grafana
2. Import log dashboard from Grafana marketplace
3. Create custom homelab log dashboard
4. Test log queries in Explore

### Phase 4: Compute Node Promtail (20 min)
1. Install Promtail binary on compute node
2. Create systemd service configuration
3. Configure Promtail to scrape:
   - journald (Ollama, LiteLLM)
   - `/var/log/syslog`
   - Application-specific logs
4. Point to Loki via Tailscale IP
5. Enable and start systemd service

### Phase 5: Testing & Validation (15 min)
1. Generate test logs from various services
2. Query logs in Grafana Explore
3. Verify log retention and rotation
4. Test label filtering (namespace, pod, service)
5. Create sample log-based alerts

## Configuration Details

### Loki Configuration
```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  retention_period: 168h  # 7 days
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 168h

table_manager:
  retention_deletes_enabled: true
  retention_period: 168h
```

### Promtail Service Node Configuration
```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki.homelab.svc.cluster.local:3100/loki/api/v1/push

scrape_configs:
  # Kubernetes pod logs
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_node_name]
        target_label: __host__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - action: replace
        source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - action: replace
        source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - action: replace
        source_labels: [__meta_kubernetes_container_name]
        target_label: container
      - replacement: /var/log/pods/*$1/*.log
        separator: /
        source_labels: [__meta_kubernetes_pod_uid, __meta_kubernetes_pod_container_name]
        target_label: __path__
```

### Promtail Compute Node Configuration
```yaml
server:
  http_listen_port: 9080

positions:
  filename: /var/lib/promtail/positions.yaml

clients:
  - url: http://100.81.76.55:30314/loki/api/v1/push  # Loki NodePort via Tailscale

scrape_configs:
  # Systemd journal
  - job_name: systemd
    journal:
      max_age: 12h
      labels:
        job: systemd-journal
        host: pesubuntu
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: unit

  # Syslog
  - job_name: syslog
    static_configs:
      - targets:
          - localhost
        labels:
          job: syslog
          host: pesubuntu
          __path__: /var/log/syslog

  # Ollama logs (if file-based)
  - job_name: ollama
    static_configs:
      - targets:
          - localhost
        labels:
          job: ollama
          host: pesubuntu
          service: ollama
          __path__: /var/log/ollama/*.log
```

## Resource Requirements

| Component | CPU | Memory | Storage | Replicas |
|-----------|-----|--------|---------|----------|
| Loki | 500m-1000m | 1-2Gi | 20Gi PVC | 1 |
| Promtail (K8s) | 100m-200m | 128Mi | - | 1 (DaemonSet) |
| Promtail (Compute) | 50m | 64Mi | - | 1 (systemd) |

**Total Additional Load on Service Node**: ~600m CPU, ~2.2Gi RAM, 20Gi storage

## Log Retention Strategy

- **Default Retention**: 7 days (168 hours)
- **Storage**: 20Gi PVC on service node (should handle ~2-3GB/day log volume)
- **Rotation**: Automatic via Loki chunk retention
- **Compression**: Built-in Loki compression (~10:1 ratio)

## Grafana Log Dashboards

### 1. Kubernetes Pod Logs Dashboard
- Top 10 pods by log volume
- Error rate by namespace
- Log level distribution
- Recent errors and warnings

### 2. Service-Specific Dashboards
- **N8n Workflow Logs**: Workflow execution traces, errors
- **PostgreSQL Logs**: Query logs, slow queries, connection errors
- **Redis Logs**: Command logs, eviction events
- **Qdrant Logs**: Search operations, indexing status

### 3. Compute Node Logs Dashboard
- Ollama inference logs
- LiteLLM routing decisions
- ROCm GPU driver messages
- System events

### 4. Error Aggregation Dashboard
- All errors across homelab
- Error frequency heatmap
- Top error messages
- Error rate trends

## LogQL Query Examples

```logql
# All logs from N8n pod
{namespace="homelab", pod=~"n8n.*"}

# Errors from any service
{namespace="homelab"} |= "error" or "ERROR" or "Error"

# Ollama inference logs on compute node
{job="systemd-journal", unit="ollama.service"}

# Slow PostgreSQL queries
{namespace="homelab", pod=~"postgres.*"} |= "duration" | json | duration > 1000

# LiteLLM request routing
{host="pesubuntu", service="litellm"} |= "model:" | logfmt

# Kubernetes events
{job="kubernetes-events"}

# Log volume by namespace (rate over 1 minute)
sum(rate({namespace=~".+"}[1m])) by (namespace)
```

## Alerts Based on Logs

### 1. High Error Rate
```yaml
- alert: HighErrorRate
  expr: |
    sum(rate({namespace="homelab"} |= "error" [5m])) by (pod)
    > 10
  for: 5m
  annotations:
    summary: "High error rate in {{ $labels.pod }}"
```

### 2. Ollama Service Down
```yaml
- alert: OllamaServiceDown
  expr: |
    absent_over_time({job="systemd-journal", unit="ollama.service"}[5m])
  for: 2m
  annotations:
    summary: "Ollama service not logging (possibly down)"
```

### 3. Disk Space Warning
```yaml
- alert: DiskSpaceWarning
  expr: |
    count_over_time({job="syslog"} |= "disk" |= "space" [1h])
    > 5
  annotations:
    summary: "Repeated disk space warnings in syslog"
```

## Benefits

1. **Unified Log Access**: Single pane of glass for all logs
2. **Troubleshooting**: Quickly correlate errors across services
3. **Debugging**: Trace workflow execution through N8n → Ollama → Mem0
4. **Compliance**: Centralized log retention for audit trails
5. **Performance**: Identify slow queries, bottlenecks via log analysis
6. **Alerting**: Proactive alerts on error patterns

## Future Enhancements

- **Log-based Metrics**: Extract metrics from logs (e.g., inference latency)
- **Trace Integration**: Correlate logs with Prometheus metrics
- **Log Sampling**: Sample high-volume logs to reduce storage
- **Multi-tenancy**: Separate log streams per project/workflow
- **Log Forwarding**: Forward critical logs to external systems

## Next Steps

1. **Review and Approve Plan**: Ensure resource allocation is acceptable
2. **Deploy Loki**: Implement Phase 1
3. **Deploy Promtail (K8s)**: Implement Phase 2
4. **Configure Grafana**: Implement Phase 3
5. **Deploy Promtail (Compute)**: Implement Phase 4
6. **Test and Validate**: Implement Phase 5
7. **Document**: Update SESSION-STATE.md and CLAUDE.md

---

**Estimated Total Implementation Time**: 75 minutes
**Priority**: P2 (Medium) - Sprint 4 objective
**Dependencies**: Grafana already deployed
**Storage Impact**: +20Gi on service node

---

**Created**: 2025-10-30
**Status**: Ready for Implementation
