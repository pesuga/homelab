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

### Glance Dashboard

A dedicated dashboard for quick service monitoring:

- Service uptime checks for all applications
- Visual indicators for service status
- Quick links to all services
- Weather and calendar widgets

The Glance dashboard is accessible at: https://glance.app.pesulabs.net

#### Glance Configuration

The Glance dashboard is configured using a YAML file stored in the repository at:
`clusters/homelab/apps/glance/configmap.yaml`

Key features of the current configuration:
- Monitor widget for service health checks (refreshes every 5 minutes)
- Bookmarks widget for quick access to services organized by category
- Weather widget showing conditions in Don Torcuato, Buenos Aires
- Calendar widget for date reference

To modify the dashboard:
1. Edit the `configmap.yaml` file
2. Apply the changes with `kubectl apply -f clusters/homelab/apps/glance/configmap.yaml`
3. Restart the Glance pod with `kubectl rollout restart deployment glance -n glance`

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

### Known Issues with Logging

**Status: Currently Troubleshooting**

There is an ongoing issue with the Promtail and Loki integration:
- Promtail appears to be running correctly but logs are not being sent to Loki
- Loki is not showing any log data in Grafana
- The Promtail configuration has been updated to use the correct log path pattern: `/var/log/pods/*/*/*.log`

Troubleshooting steps taken:
1. Verified Promtail pod has access to log files
2. Confirmed Loki service is running correctly
3. Updated Promtail configuration with correct log path pattern
4. Checked Promtail and Loki logs for errors
5. Created a test pod that sends logs directly to Loki, which worked successfully
6. Added JSON parsing stages to the Promtail configuration
7. Modified the log path pattern to match the actual directory structure

Next steps for resolution:
1. Further investigate Promtail configuration, focusing on the log format and parsing
2. Check network connectivity between Promtail and Loki
3. Verify Loki storage configuration
4. Consider using a more verbose logging level for Promtail to debug the issue
5. Test with a simpler Promtail configuration that focuses on a single namespace

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

## Troubleshooting

### Common Issues

#### No Logs in Grafana
If logs are not appearing in Grafana:
1. Check that Promtail pods are running: `k get pods -n monitoring -l app=promtail`
2. Verify Loki is running: `k get pods -n monitoring -l app=loki`
3. Check Promtail logs: `k logs -n monitoring -l app=promtail`
4. Verify Loki is receiving data: `curl -s "http://localhost:3100/loki/api/v1/labels" | jq` (requires port-forwarding)
5. Ensure the Grafana Loki data source is configured correctly

#### Prometheus Metrics Not Showing
If Prometheus metrics are not appearing:
1. Check that Prometheus pods are running: `k get pods -n monitoring -l app=prometheus`
2. Verify node-exporter is running: `k get pods -n monitoring -l app=node-exporter`
3. Check Prometheus targets: `curl -s "http://localhost:9090/api/v1/targets" | jq` (requires port-forwarding)
4. Ensure the Grafana Prometheus data source is configured correctly

#### Prometheus OOMKilled Errors
If Prometheus is being terminated with OOMKilled errors:
1. Check the pod status: `k get pods -n monitoring -l app=prometheus`
2. View the pod details: `k describe pod -n monitoring -l app=prometheus`
3. If you see "OOMKilled" in the events, the pod is running out of memory
4. Increase the memory limits in the Prometheus deployment:
   ```yaml
   resources:
     limits:
       memory: 1Gi
     requests:
       memory: 512Mi
   ```
5. Apply the changes: `k apply -f clusters/homelab/apps/monitoring/prometheus-deployment.yaml`

#### Glance Dashboard Service Status Issues
If services are showing as "ERROR" on the Glance dashboard, try the following:

1. Check if the service is running: `k get pods -n <namespace> -l app=<app-name>`
2. Verify the service URL is correct in the Glance configuration
3. For DNS resolution issues, you can use the internal service IP instead:
   ```yaml
   # Example for Qdrant service
   - title: Qdrant
     url: http://<cluster-ip>:6333/dashboard
     icon: si:database
   ```
4. To find the cluster IP: `k get svc -n <namespace> <service-name> -o jsonpath='{.spec.clusterIP}'`
5. Apply the changes and restart the Glance pod:
   ```bash
   k apply -f clusters/homelab/apps/glance/configmap.yaml
   k rollout restart deployment glance -n glance
   ```
