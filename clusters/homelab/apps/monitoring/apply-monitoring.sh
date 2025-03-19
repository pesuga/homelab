#!/bin/bash

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

echo "Monitoring stack deployed successfully!"
echo "Access Grafana at: https://grafana.app.pesulabs.net"
echo "Access Prometheus at: https://prometheus.app.pesulabs.net"
echo "Default Grafana credentials: admin/admin123"
