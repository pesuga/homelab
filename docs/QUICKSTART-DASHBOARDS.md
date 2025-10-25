# Quick Start: Grafana Dashboards

**Date**: 2025-10-25

This guide provides quick steps to get Grafana dashboards up and running immediately.

---

## Access Grafana

1. Open browser: **http://100.81.76.55:30300**
2. Login: **admin** / **admin123**

---

## Import Community Dashboards (5 minutes)

### Dashboard 1: Node Exporter Full (System Metrics)

**Purpose**: Monitor compute node system resources

1. Click **+** (left sidebar) → **Import**
2. Enter Dashboard ID: **1860**
3. Click **Load**
4. Select **Prometheus** as data source
5. Click **Import**
6. **Customize**:
   - Edit dashboard
   - Add variable filter: `instance="100.72.98.106:9100"` to queries
   - Save dashboard

**Panels you'll see**:
- CPU usage by core
- Memory usage
- Disk I/O
- Network traffic
- System load

---

### Dashboard 2: Kubernetes Cluster Monitoring

**Purpose**: Overview of K3s cluster health

1. Click **+** → **Import**
2. Enter Dashboard ID: **15760**
3. Click **Load**
4. Select **Prometheus** as data source
5. Click **Import**

**Panels you'll see**:
- Node resources
- Pod status
- Container restarts
- Network usage
- Storage usage

---

### Dashboard 3: Prometheus 2.0 Stats

**Purpose**: Monitor Prometheus itself

1. Click **+** → **Import**
2. Enter Dashboard ID: **3662**
3. Click **Load**
4. Select **Prometheus** as data source
5. Click **Import**

**Panels you'll see**:
- Scrape duration
- Samples ingested
- Rule evaluation
- Storage usage

---

## Create Custom "Homelab Overview" Dashboard (10 minutes)

### Step 1: Create New Dashboard

1. Click **+** → **Dashboard**
2. Click **Add visualization**
3. Select **Prometheus**

### Step 2: Add "Services Up" Panel

**Query**:
```promql
up{job=~"kubernetes-.*|prometheus|compute-.*"}
```

**Settings**:
- Visualization: **Stat**
- Title: "Service Health"
- Value mappings:
  - 1 → "Up" (Green)
  - 0 → "Down" (Red)

Click **Apply**

### Step 3: Add "CPU Usage" Panel

1. Click **Add** → **Visualization**
2. **Query**:
```promql
sum(rate(container_cpu_usage_seconds_total{container!="",namespace="homelab"}[5m])) by (pod)
```

**Settings**:
- Visualization: **Time series**
- Title: "CPU Usage by Pod"
- Legend: `{{pod}}`

Click **Apply**

### Step 4: Add "Memory Usage" Panel

1. Click **Add** → **Visualization**
2. **Query**:
```promql
sum(container_memory_working_set_bytes{container!="",namespace="homelab"}) by (pod)
```

**Settings**:
- Visualization: **Time series**
- Title: "Memory Usage by Pod"
- Unit: **bytes(IEC)**
- Legend: `{{pod}}`

Click **Apply**

### Step 5: Add "Network I/O" Panel

1. Click **Add** → **Visualization**
2. **Query A** (Receive):
```promql
sum(rate(container_network_receive_bytes_total{namespace="homelab"}[5m])) by (pod)
```

**Query B** (Transmit):
```promql
sum(rate(container_network_transmit_bytes_total{namespace="homelab"}[5m])) by (pod)
```

**Settings**:
- Visualization: **Time series**
- Title: "Network I/O"
- Unit: **bytes/sec**

Click **Apply**

### Step 6: Save Dashboard

1. Click **Save** (top right)
2. Name: "Homelab Overview"
3. Folder: Create "Homelab" folder
4. Click **Save**

---

## Export Dashboards for Version Control

### After creating/importing dashboards:

1. Open dashboard
2. Click **Dashboard settings** (gear icon)
3. Click **JSON Model**
4. **Copy** the JSON
5. Save to repository:
   ```bash
   # Create file
   nano infrastructure/kubernetes/monitoring/dashboards/homelab-overview.json
   # Paste JSON
   # Ctrl+X, Y, Enter to save
   ```

6. Commit to Git:
   ```bash
   git add infrastructure/kubernetes/monitoring/dashboards/
   git commit -m "Add Grafana dashboard: Homelab Overview"
   git push
   ```

---

## Troubleshooting

### No Data in Panels

**Check Prometheus**:
```bash
# Open Prometheus
http://100.81.76.55:30090

# Go to Status → Targets
# Verify all targets are "UP"
```

**Test query in Prometheus first**:
1. Go to **Graph** tab
2. Paste query
3. Click **Execute**
4. If no data, metric doesn't exist or query is wrong

### Dashboard Panels Load Slowly

**Reduce time range**:
- Top right: Change from "Last 24 hours" to "Last 1 hour"

**Simplify queries**:
- Increase interval: `[5m]` → `[1m]`
- Add filters: `{namespace="homelab"}`

---

## Next Steps

1. ✅ Import 3 community dashboards (1860, 15760, 3662)
2. ✅ Create custom "Homelab Overview" dashboard
3. ✅ Export dashboards to Git
4. 🔄 Deploy postgres_exporter for database metrics
5. 🔄 Deploy redis_exporter for Redis metrics
6. 🔄 Create "Service Health" dashboard
7. 🔄 Create "Database Performance" dashboard

---

## Quick Reference

**Grafana**: http://100.81.76.55:30300 (admin/admin123)
**Prometheus**: http://100.81.76.55:30090

**Recommended Community Dashboards**:
- 1860: Node Exporter Full
- 15760: Kubernetes Cluster Monitoring
- 3662: Prometheus 2.0 Stats
- 9628: PostgreSQL (requires postgres_exporter)
- 11835: Redis (requires redis_exporter)

**Full Documentation**: `docs/GRAFANA-DASHBOARDS.md`

---

**Version**: 1.0
**Last Updated**: 2025-10-25
