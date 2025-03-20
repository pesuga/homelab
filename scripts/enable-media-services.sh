#!/bin/bash

# Script to re-enable Jellyfin and media management services

# Enable Jellyfin
echo "Scaling up Jellyfin deployment..."
kubectl scale deployment --replicas=1 -n jellyfin jellyfin

# Enable media management services
echo "Scaling up media management deployments..."
kubectl scale deployment --replicas=1 -n media-management bazarr prowlarr radarr sonarr tdarr-server

echo "Done! All services have been scaled up."
echo "Note: You may need to update the Glance dashboard configuration to show these services again."
echo "Edit the configmap at: /clusters/homelab/apps/glance/configmap.yaml"
