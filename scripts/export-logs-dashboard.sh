#!/bin/bash

# Extract the dashboard JSON from the ConfigMap
echo "Extracting dashboard JSON..."
kubectl get configmap -n monitoring grafana-loki-dashboards -o jsonpath='{.data.loki-logs-dashboard\.json}' > /tmp/loki-logs-dashboard.json

echo "Dashboard JSON exported to /tmp/loki-logs-dashboard.json"
echo ""
echo "Steps to manually import into Grafana:"
echo "1. Go to https://grafana.app.pesulabs.net"
echo "2. Log in with your credentials"
echo "3. Click on the '+' icon in the left sidebar"
echo "4. Select 'Import'"
echo "5. Click 'Upload JSON file'"
echo "6. Select the file at /tmp/loki-logs-dashboard.json"
echo "7. Click 'Import'"
echo ""
echo "Alternatively, you can copy the JSON content and paste it in the Import dashboard JSON field."
