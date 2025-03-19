# Monitoring Setup Documentation

This document provides information about the monitoring stack setup in the homelab environment.

## Components

The monitoring stack consists of the following components:

1. **Prometheus**: Time-series database for metrics collection
2. **Grafana**: Visualization and dashboarding tool
3. **Loki**: Log aggregation system
4. **Promtail**: Log collection agent that sends logs to Loki

## Access

- **Grafana**: https://grafana.app.pesulabs.net
  - Username: `admin`
  - Password: `admin123` (change this after first login)
- **Prometheus**: https://prometheus.app.pesulabs.net

## Dashboards

### Homelab Overview Dashboard

A comprehensive dashboard that provides:

- System metrics (CPU, memory, disk, network)
- Application status and uptime
- Application error logs

### Asuna Cluster Dashboard

A dashboard focused on Kubernetes metrics:

- Node resource usage
- Pod resource usage
- Cluster health

## Adding New Dashboards

To add a new dashboard:

1. Create a JSON file with the dashboard configuration
2. Add it to the `grafana-dashboards.yaml` ConfigMap in `clusters/homelab/apps/monitoring/`
3. Restart the Grafana deployment with `k rollout restart deployment grafana -n monitoring`

## Logging

Logs are collected by Promtail and stored in Loki. You can query logs in Grafana using LogQL.

Example queries:

- View all logs from a specific namespace:
  ```
  {namespace="immich"}
  ```

- View error logs across all applications:
  ```
  {namespace=~"immich|plex|home-assistant|n8n|owncloud|glance"} |~ "error|warning|critical|exception"
  ```

## Alerting

Alerting can be configured in Grafana for critical metrics. Common alert scenarios:

- High CPU/memory usage
- Disk space running low
- Application downtime
- Error rate spikes

## Maintenance

- Prometheus data is stored in a PersistentVolume
- Loki data is stored in a PersistentVolume
- Grafana configuration is stored in a PersistentVolume

To update components, edit the respective deployment files and apply the changes with Flux or kubectl.
