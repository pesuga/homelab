#!/bin/bash

# Create a more advanced dashboard with template variables for filtering
cat > /tmp/advanced-dashboard.json << 'EOF'
{
  "dashboard": {
    "title": "Application Logs Explorer",
    "uid": "loki-logs-explorer",
    "editable": true,
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
            "expr": "{namespace=~\"$namespace\", pod=~\"$pod\", container=~\"$container\"}"
          }
        ],
        "options": {
          "showLabels": true,
          "showTime": true,
          "sortOrder": "Descending",
          "wrapLogMessage": false,
          "enableLogDetails": true
        }
      }
    ],
    "templating": {
      "list": [
        {
          "name": "namespace",
          "type": "query",
          "datasource": {
            "type": "loki"
          },
          "query": "label_values(namespace)",
          "refresh": 1,
          "includeAll": true,
          "multi": false,
          "label": "Namespace"
        },
        {
          "name": "pod",
          "type": "query",
          "datasource": {
            "type": "loki"
          },
          "query": "label_values({namespace=~\"$namespace\"}, pod)",
          "refresh": 1,
          "includeAll": true,
          "multi": false,
          "label": "Pod"
        },
        {
          "name": "container",
          "type": "query",
          "datasource": {
            "type": "loki"
          },
          "query": "label_values({namespace=~\"$namespace\", pod=~\"$pod\"}, container)",
          "refresh": 1,
          "includeAll": true,
          "multi": false,
          "label": "Container"
        }
      ]
    },
    "refresh": "5s",
    "schemaVersion": 37,
    "version": 1,
    "time": {
      "from": "now-15m",
      "to": "now"
    }
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
  -d @/tmp/advanced-dashboard.json

# Clean up
echo "Cleaning up..."
kill $PF_PID 2>/dev/null || true
rm /tmp/advanced-dashboard.json

# Make sure the link in Glance dashboard is updated
kubectl patch configmap -n glance glance-config --type='json' \
-p='[{"op":"replace","path":"/data/glance.yml","value":"'$(kubectl get configmap -n glance glance-config -o jsonpath='{.data.glance\.yml}' | sed 's|https://grafana.app.pesulabs.net/explore.*|https://grafana.app.pesulabs.net/d/loki-logs-explorer/application-logs-explorer|g')'"}'

# Restart Glance pod
echo "Restarting Glance pod..."
kubectl delete pod -n glance -l app=glance

echo "Done! Your advanced Loki dashboard has been created."
echo "Access it at: https://grafana.app.pesulabs.net/d/loki-logs-explorer/application-logs-explorer"
echo "The link in your Glance dashboard has been updated to point to this dashboard."
