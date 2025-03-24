#!/bin/bash

# This script adds bookmarks to the Grafana UI for quick access to common log queries
# It's a workaround for the Loki dashboard issues

# Create simplified queries for common logs
cat > /tmp/loki-queries.json << 'EOF'
[
  {
    "uid": "n8n-all-logs",
    "title": "N8N - All Logs",
    "url": "https://grafana.app.pesulabs.net/explore?left=%7B%22datasource%22:%22loki%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22%7Bnamespace%3D%5C%22n8n%5C%22%7D%22,%22queryType%22:%22range%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D",
    "isStarred": true
  },
  {
    "uid": "n8n-errors",
    "title": "N8N - Errors",
    "url": "https://grafana.app.pesulabs.net/explore?left=%7B%22datasource%22:%22loki%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22%7Bnamespace%3D%5C%22n8n%5C%22%7D%20%7C%3D%20%5C%22error%5C%22%20or%20%7C%3D%20%5C%22ECONNREFUSED%5C%22%22,%22queryType%22:%22range%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D",
    "isStarred": true
  },
  {
    "uid": "monitoring-logs",
    "title": "Monitoring - All Logs",
    "url": "https://grafana.app.pesulabs.net/explore?left=%7B%22datasource%22:%22loki%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22%7Bnamespace%3D%5C%22monitoring%5C%22%7D%22,%22queryType%22:%22range%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D",
    "isStarred": true
  },
  {
    "uid": "all-error-logs",
    "title": "All Namespaces - Errors",
    "url": "https://grafana.app.pesulabs.net/explore?left=%7B%22datasource%22:%22loki%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22%7B%7D%20%7C%3D%20%5C%22error%5C%22%20or%20%7C%3D%20%5C%22ERROR%5C%22%20or%20%7C%3D%20%5C%22Error%5C%22%20or%20%7C%3D%20%5C%22exception%5C%22%20or%20%7C%3D%20%5C%22Exception%5C%22%22,%22queryType%22:%22range%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D",
    "isStarred": true
  },
  {
    "uid": "recent-logs",
    "title": "Recent Logs (All)",
    "url": "https://grafana.app.pesulabs.net/explore?left=%7B%22datasource%22:%22loki%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22%7B%7D%22,%22queryType%22:%22range%22%7D%5D,%22range%22:%7B%22from%22:%22now-15m%22,%22to%22:%22now%22%7D%7D",
    "isStarred": true
  }
]
EOF

echo "Launching a simple log viewer for N8N..."
echo ""
echo "Visit this direct link to see N8N logs:"
echo "https://grafana.app.pesulabs.net/explore?left=%7B%22datasource%22:%22loki%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22%7Bnamespace%3D%5C%22n8n%5C%22%7D%22,%22queryType%22:%22range%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D"
echo ""
echo "Visit this direct link to see N8N error logs:"
echo "https://grafana.app.pesulabs.net/explore?left=%7B%22datasource%22:%22loki%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22%7Bnamespace%3D%5C%22n8n%5C%22%7D%20%7C%3D%20%5C%22error%5C%22%20or%20%7C%3D%20%5C%22ECONNREFUSED%5C%22%22,%22queryType%22:%22range%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D"
echo ""

echo "Updating Glance config to add direct log viewing links..."
kubectl patch configmap -n glance glance-config --type=json -p='[{"op":"add","path":"/data/glance.yml","value":"'$(kubectl get configmap -n glance glance-config -o jsonpath='{.data.glance\.yml}' | sed 's/                  - title: Logs Explorer/                  - title: Logs Explorer\n                    url: https:\/\/grafana.app.pesulabs.net\/explore?left=%7B%22datasource%22:%22loki%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22%7B%7D%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D\n                    icon: mdi:file-document-multiple\n                    icon_color: "#9C27B0"\n                  - title: N8N Logs\n                    url: https:\/\/grafana.app.pesulabs.net\/explore?left=%7B%22datasource%22:%22loki%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22%7Bnamespace%3D%5C%22n8n%5C%22%7D%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D\n                    icon: si:n8n\n                    icon_color: "#FF6D00"/g')'"}'

echo "Restarting Glance to apply changes..."
kubectl delete pod -n glance -l app=glance
