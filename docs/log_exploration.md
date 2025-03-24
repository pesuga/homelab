# Log Exploration Guide for Homelab

This guide explains how to use Grafana's Explore feature with Loki to effectively search and analyze logs from your homelab Kubernetes cluster.

## Accessing the Log Explorer

There are two ways to access the log explorer:

1. **Via Glance Dashboard**:
   - Open the Glance dashboard at https://glance.app.pesulabs.net
   - Click on the "Logs Explorer" link in the Monitoring section

2. **Direct Access**:
   - Go to https://grafana.app.pesulabs.net/explore
   - Select "Loki" from the data source dropdown at the top

## Basic Log Queries

Loki uses LogQL, a query language specifically designed for logs. Here are some basic queries:

### View logs from all namespaces:
```
{namespace=~".+"}
```

### View logs from a specific namespace:
```
{namespace="monitoring"}
```

### View logs from a specific pod:
```
{namespace="monitoring", pod="grafana-57b8c97445-7nkgz"}
```

### Filter logs by content:
```
{namespace="monitoring"} |= "error"
```

## Advanced Queries

### Use regular expressions for content filtering:
```
{namespace="monitoring"} |~ "error|warn|critical"
```

### Use negation to exclude content:
```
{namespace="monitoring"} != "healthy"
```

### Combine multiple filters:
```
{namespace="monitoring", pod=~"grafana.*"} |= "error" != "timeout"
```

### Extract and process log lines with regex:
```
{namespace="monitoring"} | regexp "(?P<level>(ERROR|INFO|WARN))"
```

### Count occurrences:
```
count_over_time({namespace="monitoring", pod=~"grafana.*"} |= "error" [1h])
```

## Log Visualization Tips

1. **Time Range**: Use the time picker at the top right to select the time range for your logs

2. **Live Tail**: Click the "Live" button at the top right to see logs in real-time

3. **Split View**: Click "Split" to compare two different log queries side by side

4. **Log Statistics**: Click "Log volume" to see a histogram of log volume over time

5. **Log Labels**: Click on any label value (namespace, pod, container) to add it as a filter

## Common Use Cases

### Troubleshooting Application Errors:
```
{namespace="app-namespace", pod=~"app-name.*"} |= "error" | json
```

### Monitoring Ingress Traffic:
```
{namespace="ingress-nginx"} |~ "GET|POST|PUT|DELETE"
```

### Investigating Pod Restarts:
```
{namespace=~".+", container="POD"}
```

### System-level Issues:
```
{namespace="kube-system"} |= "failed" |= "node"
```

## Saving Queries

You can save frequently used queries:
1. Create your query in the Explore view
2. Click the star icon in the query row
3. Give your query a name
4. Access saved queries from the dropdown next to the query input

This flexible log exploration interface should make troubleshooting and monitoring your homelab much easier.
