# Plex Media Server

This directory contains the Kubernetes manifests for deploying Plex Media Server in the homelab environment.

## Components

- **Namespace**: Dedicated `plex` namespace for isolation
- **PersistentVolumeClaims**: For Plex configuration and media storage
- **Deployment**: Plex server container with appropriate resource limits
- **Service**: For accessing Plex on port 32400
- **Ingress**: For accessing Plex via https://plex.app.pesulabs.net

## Configuration

### Media Storage

The Plex deployment is configured with two persistent volumes:

1. `plex-config`: 10Gi volume for Plex server configuration
2. `plex-media`: 50Gi volume for media storage

### Network Configuration

Plex requires several ports to be exposed for full functionality:

- 32400: Main port for Plex web interface and streaming
- 1900: DLNA discovery (UDP)
- 3005: Plex Companion
- 5353: Bonjour/Avahi discovery (UDP)
- 8324: Roku control
- 32410-32414: GDM network discovery (UDP)

### Environment Variables

- `TZ`: Set to "America/Argentina/Buenos_Aires" for correct time display
- `PLEX_CLAIM`: Optional claim token for Plex account linking
- `ADVERTISE_IP`: Set to https://plex.app.pesulabs.net
- `ALLOWED_NETWORKS`: Set to allow local networks

## Deployment

To deploy Plex Media Server, run:

```bash
kubectl apply -f namespace.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

## Initial Setup

After deployment, access Plex at https://plex.app.pesulabs.net to complete the initial setup:

1. Create a Plex account or sign in with an existing one
2. Set up your media libraries by pointing to the `/media` directory
3. Configure transcoding settings based on your server's capabilities

## Maintenance

- **Updates**: Plex can be updated by changing the image tag in the deployment.yaml file
- **Backups**: Regularly back up the `plex-config` volume to preserve your settings
- **Monitoring**: Use the monitoring stack to keep an eye on Plex resource usage
