# Jellyfin Media Server

This directory contains the Kubernetes manifests for deploying Jellyfin, an open-source media server.

## Components

- **Namespace**: Dedicated `jellyfin` namespace
- **PVCs**: 
  - `jellyfin-config`: 10Gi for configuration data
  - `jellyfin-media`: 50Gi for media files
- **Deployment**: Single pod with resource requests/limits
- **Service**: Expose necessary ports for web interface and DLNA discovery
- **Ingress**: Subdomain-based routing via `jellyfin.app.pesulabs.net`

## Usage

### Deployment

```bash
# Make the script executable
chmod +x apply-jellyfin.sh

# Run the script to deploy all resources
./apply-jellyfin.sh
```

### Accessing Jellyfin

Once deployed, Jellyfin will be available at: https://jellyfin.app.pesulabs.net

### Initial Setup

After deployment, access the web interface to:
1. Create an admin user
2. Configure media libraries
3. Set up any additional users and permissions

## Media Library Migration

If migrating from Plex:
1. Ensure media files are accessible via the `jellyfin-media` PVC
2. Create libraries in Jellyfin that point to the same media folders
3. Jellyfin will automatically scan and import metadata for your media
