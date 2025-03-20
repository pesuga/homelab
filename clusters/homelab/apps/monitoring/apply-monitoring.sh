#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

# Apply namespace first
kubectl apply -f namespace.yaml

# Apply Prometheus resources
kubectl apply -f prometheus-configmap.yaml
kubectl apply -f prometheus-pvc.yaml
kubectl apply -f prometheus-rbac.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f prometheus-service.yaml
kubectl apply -f prometheus-ingress.yaml

# Apply Grafana resources
kubectl apply -f grafana-pvc.yaml
kubectl apply -f grafana-datasources.yaml
kubectl apply -f grafana-dashboards.yaml
kubectl apply -f grafana-k8s-dashboards.yaml
kubectl apply -f grafana-deployment.yaml
kubectl apply -f grafana-service.yaml
kubectl apply -f grafana-ingress.yaml

# Apply Loki resources
kubectl apply -f loki-pvc.yaml
kubectl apply -f loki-config.yaml
kubectl apply -f loki-deployment.yaml
kubectl apply -f loki-service.yaml

# Apply Promtail resources
kubectl apply -f promtail-config.yaml
kubectl apply -f promtail-rbac.yaml
kubectl apply -f promtail-daemonset.yaml

# Apply kube-state-metrics
kubectl apply -f kube-state-metrics/rbac.yaml
kubectl apply -f kube-state-metrics/service.yaml
kubectl apply -f kube-state-metrics/deployment.yaml

# Apply node-exporter
kubectl apply -f node-exporter.yaml

# Restart Grafana to pick up the new dashboards
kubectl rollout restart deployment grafana -n monitoring

echo "Monitoring stack deployed successfully!"
echo "Access Grafana at: https://grafana.app.pesulabs.net"
echo "Access Prometheus at: https://prometheus.app.pesulabs.net"
echo "Default Grafana credentials: admin/admin123"
