# Monitoring Stack

This directory contains the Kubernetes manifests for deploying a complete monitoring stack consisting of:

- **Prometheus**: For metrics collection and storage
- **Grafana**: For visualization and dashboards
- **Loki**: For log aggregation
- **Promtail**: For collecting logs from Kubernetes pods

## Components

### Prometheus

Prometheus is an open-source monitoring system with a dimensional data model, flexible query language, efficient time series database and modern alerting approach.

- Accessible at: https://prometheus.app.pesulabs.net
- Collects metrics from Kubernetes API server, nodes, and services
- Stores metrics in a time-series database

### Grafana

Grafana is an open-source platform for monitoring and observability that allows you to query, visualize, alert on, and explore your metrics.

- Accessible at: https://grafana.app.pesulabs.net
- Default credentials: admin/admin123 (change these in production)
- Pre-configured with Prometheus and Loki data sources

### Loki

Loki is a horizontally-scalable, highly-available, multi-tenant log aggregation system inspired by Prometheus.

- Stores and indexes logs from Kubernetes pods
- Integrated with Grafana for log visualization
- Uses a set of labels for efficient log queries

### Promtail

Promtail is an agent which ships the contents of local logs to a Loki instance.

- Runs as a DaemonSet on each Kubernetes node
- Collects logs from all pods
- Adds Kubernetes metadata as labels to logs

## Deployment

To deploy the entire monitoring stack, run:

```bash
./apply-monitoring.sh
```

## Access

- Grafana: https://grafana.app.pesulabs.net
- Prometheus: https://prometheus.app.pesulabs.net

## Default Dashboards

After deployment, you can import the following dashboards in Grafana:

1. Kubernetes Cluster Overview: ID 13770
2. Node Exporter Full: ID 1860
3. Loki Logs: ID 12019

## Maintenance

To update configurations:

1. Edit the relevant ConfigMap
2. Apply the changes with `kubectl apply -f <configmap-file.yaml>`
3. Restart the affected deployment if necessary

## Troubleshooting

If you encounter issues:

1. Check pod status: `kubectl get pods -n monitoring`
2. View logs: `kubectl logs -n monitoring <pod-name>`
3. Verify persistent volumes: `kubectl get pvc -n monitoring`
