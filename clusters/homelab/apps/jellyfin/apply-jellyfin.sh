#!/bin/bash

# Create namespace if it doesn't exist
kubectl create namespace jellyfin --dry-run=client -o yaml | kubectl apply -f -

# Apply Jellyfin resources
kubectl apply -f namespace.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Show resources
echo "Deployed Jellyfin resources:"
kubectl get all -n jellyfin
