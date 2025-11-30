#!/bin/bash
OUTPUT_FILE="/home/pesu/Rakuflow/systems/homelab/debug-output.txt"
echo "=== Pods in fa-platform ===" > "$OUTPUT_FILE"
kubectl get pods -n fa-platform -o wide >> "$OUTPUT_FILE"
echo -e "\n=== Endpoints in fa-platform ===" >> "$OUTPUT_FILE"
kubectl get endpoints -n fa-platform >> "$OUTPUT_FILE"
echo -e "\n=== Traefik Pods ===" >> "$OUTPUT_FILE"
kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik -o wide >> "$OUTPUT_FILE"
