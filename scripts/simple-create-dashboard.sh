#!/bin/bash

# Create a JSON file for our dashboard with a simpler configuration
cat > /tmp/simple-dashboard.json << 'EOF'
{
  "dashboard": {
    "title": "Application Logs Explorer",
    "uid": "loki-logs-explorer",
    "panels": [
      {
        "type": "logs",
        "title": "Application Logs",
        "gridPos": {
          "h": 24,
          "w": 24,
          "x": 0,
          "y": 0
        },
        "targets": [
          {
            "refId": "A",
            "expr": "{namespace=~\".+\"}"
          }
        ]
      }
    ],
    "refresh": "5s",
    "schemaVersion": 37,
    "version": 1
  },
  "overwrite": true
}
EOF

# The dashboard will be forwarded via kubectl port-forward
echo "Creating port-forward to Grafana..."
kubectl port-forward -n monitoring svc/grafana 3000:3000 &
PF_PID=$!
sleep 3

# Import the dashboard
echo "Importing dashboard..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  http://localhost:3000/api/dashboards/db \
  -d @/tmp/simple-dashboard.json

# Clean up
echo "Cleaning up..."
kill $PF_PID 2>/dev/null || true
rm /tmp/simple-dashboard.json

echo "Done! Your simple Loki dashboard has been created."
echo "Access it at: https://grafana.app.pesulabs.net/d/loki-logs-explorer/application-logs-explorer"
