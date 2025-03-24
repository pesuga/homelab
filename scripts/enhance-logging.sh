#!/bin/bash

# Apply the enhanced logging configuration
echo "Applying Loki logging setup..."
kubectl apply -f clusters/homelab/apps/monitoring/loki-logging-setup.yaml

# Restart Grafana to apply the plugin changes
echo "Restarting Grafana to apply plugin changes..."
kubectl rollout restart deployment -n monitoring grafana

# Restart Promtail to apply the new configuration
echo "Restarting Promtail to apply new configuration..."
kubectl rollout restart daemonset -n monitoring promtail

echo "Waiting for Grafana rollout to complete..."
kubectl rollout status deployment -n monitoring grafana -w

echo "Done! Enhanced logging setup has been applied."
echo ""
echo "Access your new logging dashboard at:"
echo "https://grafana.app.pesulabs.net/dashboards"
echo ""
echo "Look for the 'Application Logs Explorer' dashboard."
echo ""
echo "Tips for using LogQL:"
echo "• {namespace=\"monitoring\"} - Filter logs by namespace"
echo "• {namespace=\"monitoring\"} |= \"error\" - Search for logs containing 'error'"
echo "• {pod=~\"grafana.*\"} - Filter logs from pods starting with 'grafana'"
echo "• {namespace=\"monitoring\"} |~ \"error|warning\" - Regex search for logs with 'error' or 'warning'"
echo ""
echo "For more complex queries, use the LogQL Explorer in Grafana's Explore section."
