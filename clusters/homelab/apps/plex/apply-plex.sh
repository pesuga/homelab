#!/bin/bash

# Apply Plex resources
kubectl apply -f namespace.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

echo "Plex Media Server deployed successfully!"
echo "Access Plex at: https://plex.app.pesulabs.net"
echo "Note: Initial setup may require accessing Plex directly through the IP:32400/web interface"
