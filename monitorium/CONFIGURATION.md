# Monitorium Configuration Guide

This guide explains how to configure Monitorium for your homelab environment.

## Configuration File Location

Monitorium looks for its configuration at:
```
~/.monitorium/config.yaml
```

If no configuration file exists, Monitorium will create a default one automatically.

## Quick Setup

1. **Copy the example configuration:**
   ```bash
   cp config.example.yaml ~/.monitorium/config.yaml
   ```

2. **Edit the configuration:**
   ```bash
   nano ~/.monitorium/config.yaml
   ```

3. **Run Monitorium:**
   ```bash
   monitorium
   ```

## Configuration Sections

### General Settings

Control the basic application behavior:

```yaml
general:
  update_interval_secs: 5      # How often to refresh metrics
  history_retention: 60          # Data points to keep for graphs
  connection_timeout_secs: 10    # Timeout for external services
  fullscreen: false              # Start in fullscreen mode
  theme: "default"               # UI theme
```

### Prometheus Configuration

Configure metrics collection from Prometheus:

```yaml
prometheus:
  url: "http://100.81.76.55:30090"  # Prometheus server URL
  timeout_secs: 10                      # Connection timeout
  query_interval_secs: 5                # Query frequency

  # Custom Prometheus queries
  node_queries:
    cpu_usage: "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
    memory_usage: "((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100)"
    network_rx: "irate(node_network_receive_bytes_total[5m]) / 1024 / 1024"
    network_tx: "irate(node_network_transmit_bytes_total[5m]) / 1024 / 1024"

  service_queries:
    service_status: "up"
    cpu_usage: "rate(container_cpu_usage_seconds_total[5m]) * 100"
    memory_usage: "container_memory_usage_bytes / container_spec_memory_limit_bytes * 100"
```

### Health Checks

Configure service health monitoring:

```yaml
health_checks:
  enabled: true
  interval_secs: 30              # Health check frequency
  timeout_secs: 5                # Health check timeout
  failure_threshold: 3            # Failures before unhealthy

  services:
    - name: "n8n-0"
      endpoint: "http://100.81.76.55:30678/healthz"
      method: "GET"
      expected_status: [200]
      enabled: true
      response_time_threshold_ms: 1000
```

### Node Configuration

Define which nodes to monitor:

```yaml
nodes:
  defaults:
    temperature_unit: "C"
    network_unit: "MB/s"
    show_gpu: false

  nodes:
    - name: "pesubuntu"
      address: "100.72.98.106"
      labels:
        type: "compute"
        location: "homelab"
      overrides:
        display_name: "Compute Node"
        show_gpu: true
```

### UI Configuration

Customize the interface:

```yaml
ui:
  refresh_rate_ms: 250           # UI refresh rate
  show_graphs: true              # Enable graphs
  show_service_logs: true         # Show service logs
  show_health_checks: true        # Show health panel
  max_log_lines: 10              # Max log lines

  layout:
    main_split: [50, 50]           # Nodes vs Services
    service_split: [40, 35, 25]    # Graphs vs Health vs Logs
    node_split: [50, 50]            # Specs vs Graphs
```

## Agent Setup

For automated deployment by agents:

1. **Create config directory:**
   ```bash
   mkdir -p ~/.monitorium
   ```

2. **Deploy configuration:**
   ```bash
   # Agent can copy a pre-configured config.yaml to ~/.monitorium/
   # All URLs, endpoints, and settings should be customized for the environment
   ```

3. **Set executable permissions:**
   ```bash
   chmod +x monitorium
   ```

4. **Run in background (optional):**
   ```bash
   nohup monitorium > ~/.monitorium/monitorium.log 2>&1 &
   ```

## Environment Variables

You can also override configuration with environment variables:

```bash
export MONITORIUM_PROMETHEUS_URL="http://your-prometheus:9090"
export MONITORIUM_UPDATE_INTERVAL="10"
monitorium
```

## Configuration Validation

Monitorium will validate the configuration on startup and report any errors:

- **Missing URLs:** Ensure all service endpoints are accessible
- **Invalid queries:** Prometheus queries must be syntactically correct
- **Network connectivity:** Verify all URLs are reachable
- **File permissions:** Config directory must be writable

## Troubleshooting

### Configuration Not Loading

1. Check file location: `ls -la ~/.monitorium/config.yaml`
2. Verify syntax: `python3 -c "import yaml; yaml.safe_load(open('~/.monitorium/config.yaml'))"`
3. Check permissions: `ls -ld ~/.monitorium/`

### Health Checks Not Working

1. Verify endpoints are accessible: `curl -I http://service:port/health`
2. Check timeouts are appropriate for your network
3. Review service logs for health check failures

### Prometheus Connection Issues

1. Test Prometheus URL: `curl http://your-prometheus:9090/api/v1/query?query=up`
2. Verify network connectivity
3. Check authentication if Prometheus requires it

## Example Configurations

### Minimal Configuration
```yaml
general:
  update_interval_secs: 10

prometheus:
  url: "http://localhost:9090"

health_checks:
  enabled: false

ui:
  show_graphs: true
  show_service_logs: true
  show_health_checks: false
```

### High-Frequency Monitoring
```yaml
general:
  update_interval_secs: 1
  history_retention: 120

ui:
  refresh_rate_ms: 100

health_checks:
  interval_secs: 10
  timeout_secs: 2
  failure_threshold: 2
```

### External Service Monitoring
```yaml
prometheus:
  url: "https://prometheus.company.com"
  auth:
    username: "monitoring"
    password: "secure-password"

health_checks:
  services:
    - name: "external-api"
      endpoint: "https://api.company.com/health"
      method: "GET"
      headers:
        Authorization: "Bearer your-token"
      timeout_secs: 15
      response_time_threshold_ms: 5000
```

## Configuration Reload

Currently, Monitorium requires a restart to load configuration changes. Future versions may support hot-reloading.

## Security Considerations

- **Sensitive Data:** Avoid storing passwords in plain text config files
- **Network Exposure:** Be cautious with public Prometheus URLs
- **Authentication:** Use secure authentication methods for external services
- **File Permissions:** Ensure config files have appropriate permissions (600 or 644)

## Migration from Previous Versions

If upgrading from a version without configuration support:

1. The new system will automatically create a default config
2. Previous hardcoded settings will be replaced by config defaults
3. Custom themes and settings need to be migrated to the new format

## Getting Help

For additional help with configuration:

1. Check the example configuration: `config.example.yaml`
2. Review the default values in the codebase
3. Test your configuration: `monitorium --validate-config` (future feature)
4. Check logs for configuration errors during startup