#!/bin/bash

# Disable Jellyfin and media-management apps to improve cluster performance

# Scale down deployments to 0 replicas
echo "Scaling down Jellyfin deployment..."
kubectl scale deployment --replicas=0 -n jellyfin jellyfin

echo "Scaling down media-management deployments..."
kubectl scale deployment --replicas=0 -n media-management bazarr prowlarr radarr sonarr tdarr-server

# Update Glance dashboard
echo "Updating Glance dashboard (already done)"

# Update DNS records to ensure they don't resolve
echo "Checking for DNS records that need to be removed..."
kubectl -n external-dns logs deploy/external-dns --tail=100 | grep -E "jellyfin|bazarr|prowlarr|radarr|sonarr|tdarr"

echo "Done! All resources have been scaled down."
echo "To re-enable these services in the future, run 'kubectl scale deployment --replicas=1' for each deployment."
