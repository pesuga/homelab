#!/bin/bash

# This script will test various Loki queries to help diagnose log query issues

echo "Checking if Loki is collecting logs from n8n namespace..."
kubectl exec -n monitoring deploy/grafana -- curl -s -X GET -H "Content-Type: application/json" \
  -u admin:admin123 \
  "http://loki:3100/loki/api/v1/query?query=%7Bnamespace%3D%22n8n%22%7D&limit=5" | jq .

echo -e "\nChecking for specific pod logs..."
kubectl exec -n monitoring deploy/grafana -- curl -s -X GET -H "Content-Type: application/json" \
  -u admin:admin123 \
  "http://loki:3100/loki/api/v1/query?query=%7Bnamespace%3D%22n8n%22%2C%20pod%3D~%22n8n-.*%22%7D&limit=5" | jq .

echo -e "\nChecking for error logs with simplified query..."
kubectl exec -n monitoring deploy/grafana -- curl -s -X GET -H "Content-Type: application/json" \
  -u admin:admin123 \
  "http://loki:3100/loki/api/v1/query?query=%7Bnamespace%3D%22n8n%22%7D%20%7C%3D%20%22error%22&limit=5" | jq .

echo -e "\nChecking for connection errors..."
kubectl exec -n monitoring deploy/grafana -- curl -s -X GET -H "Content-Type: application/json" \
  -u admin:admin123 \
  "http://loki:3100/loki/api/v1/query?query=%7Bnamespace%3D%22n8n%22%7D%20%7C%3D%20%22ECONNREFUSED%22&limit=5" | jq .

echo -e "\nChecking labels available for n8n namespace..."
kubectl exec -n monitoring deploy/grafana -- curl -s -X GET -H "Content-Type: application/json" \
  -u admin:admin123 \
  "http://loki:3100/loki/api/v1/labels?match=%7Bnamespace%3D%22n8n%22%7D" | jq .
