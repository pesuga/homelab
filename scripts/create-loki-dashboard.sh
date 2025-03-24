#!/bin/bash

# This script creates a simplified Loki logs dashboard directly in Grafana using the API

# Set variables
GRAFANA_URL="http://grafana.monitoring.svc.cluster.local"
ADMIN_USER="admin"
ADMIN_PASSWORD="admin123"
DASHBOARD_TITLE="Application Logs Explorer"
DASHBOARD_UID="loki-logs-explorer"

# First, let's determine the UID of the Loki datasource
echo "Identifying Loki datasource..."

# Create a temporary file for the dashboard JSON
TEMP_FILE=$(mktemp)

# Generate a simple dashboard with logs panel
cat > $TEMP_FILE << EOF
{
  "dashboard": {
    "annotations": {
      "list": [
        {
          "builtIn": 1,
          "datasource": {
            "type": "grafana",
            "uid": "-- Grafana --"
          },
          "enable": true,
          "hide": true,
          "iconColor": "rgba(0, 211, 255, 1)",
          "name": "Annotations & Alerts",
          "type": "dashboard"
        }
      ]
    },
    "editable": true,
    "fiscalYearStartMonth": 0,
    "graphTooltip": 0,
    "links": [],
    "liveNow": true,
    "panels": [
      {
        "datasource": {
          "type": "loki"
        },
        "gridPos": {
          "h": 24,
          "w": 24,
          "x": 0,
          "y": 0
        },
        "id": 2,
        "options": {
          "dedupStrategy": "none",
          "enableLogDetails": true,
          "prettifyLogMessage": false,
          "showCommonLabels": false,
          "showLabels": true,
          "showTime": true,
          "sortOrder": "Descending",
          "wrapLogMessage": false
        },
        "targets": [
          {
            "datasource": {
              "type": "loki"
            },
            "editorMode": "builder",
            "expr": "{namespace=~\"$namespace\", pod=~\"$pod\", container=~\"$container\"}",
            "queryType": "range",
            "refId": "A"
          }
        ],
        "title": "Application Logs",
        "type": "logs"
      }
    ],
    "refresh": "5s",
    "schemaVersion": 37,
    "style": "dark",
    "tags": ["logs", "loki"],
    "templating": {
      "list": [
        {
          "current": {
            "selected": false,
            "text": "All",
            "value": "\$__all"
          },
          "datasource": {
            "type": "loki"
          },
          "definition": "label_values(namespace)",
          "hide": 0,
          "includeAll": true,
          "label": "Namespace",
          "multi": false,
          "name": "namespace",
          "options": [],
          "query": "label_values(namespace)",
          "refresh": 1,
          "regex": "",
          "skipUrlSync": false,
          "sort": 0,
          "type": "query"
        },
        {
          "current": {
            "selected": false,
            "text": "All",
            "value": "\$__all"
          },
          "datasource": {
            "type": "loki"
          },
          "definition": "label_values({namespace=\"\$namespace\"}, pod)",
          "hide": 0,
          "includeAll": true,
          "label": "Pod",
          "multi": false,
          "name": "pod",
          "options": [],
          "query": "label_values({namespace=\"\$namespace\"}, pod)",
          "refresh": 1,
          "regex": "",
          "skipUrlSync": false,
          "sort": 0,
          "type": "query"
        },
        {
          "current": {
            "selected": false,
            "text": "All",
            "value": "\$__all"
          },
          "datasource": {
            "type": "loki"
          },
          "definition": "label_values({namespace=\"\$namespace\", pod=\"\$pod\"}, container)",
          "hide": 0,
          "includeAll": true,
          "label": "Container",
          "multi": false,
          "name": "container",
          "options": [],
          "query": "label_values({namespace=\"\$namespace\", pod=\"\$pod\"}, container)",
          "refresh": 1,
          "regex": "",
          "skipUrlSync": false,
          "sort": 0,
          "type": "query"
        }
      ]
    },
    "time": {
      "from": "now-15m",
      "to": "now"
    },
    "timepicker": {
      "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]
    },
    "timezone": "",
    "title": "${DASHBOARD_TITLE}",
    "uid": "${DASHBOARD_UID}",
    "version": 1,
    "weekStart": ""
  },
  "overwrite": true,
  "message": "Created by script"
}
EOF

# Apply the dashboard using kubectl exec
echo "Creating dashboard via API..."
cat $TEMP_FILE | kubectl exec -n monitoring deploy/grafana -- \
  curl -s -X POST -H "Content-Type: application/json" \
  -u ${ADMIN_USER}:${ADMIN_PASSWORD} \
  http://localhost:3000/api/dashboards/db -d @-

# Update the Glance configmap to point to this dashboard
echo "Updating Glance configmap to link to the new dashboard..."
kubectl patch configmap -n glance glance-config --type=json \
  -p='[{"op": "replace", "path": "/data/glance.yml", "value": "'"$(kubectl get configmap -n glance glance-config -o jsonpath='{.data.glance\.yml}' | sed 's#url: https://grafana.app.pesulabs.net/explore.*#url: https://grafana.app.pesulabs.net/d/loki-logs-explorer/application-logs-explorer#')"'"}]'

# Restart Glance pod to apply the changes
echo "Restarting Glance pod..."
kubectl delete pod -n glance -l app=glance

echo "Cleanup..."
rm -f $TEMP_FILE

echo "Done! Your Loki logs dashboard has been created."
echo "Access it at: https://grafana.app.pesulabs.net/d/loki-logs-explorer/application-logs-explorer"
echo "You can also access it via the Logs Explorer link in your Glance dashboard."
