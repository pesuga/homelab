# Homer Dashboard

This directory contains the Kubernetes manifests for deploying the Homer dashboard in the homelab environment.

## Overview

Homer is a lightweight, static dashboard that provides a clean and simple entry point to all applications in the homelab. It is configured via a YAML file that defines the services, categories, and appearance of the dashboard.

## Components

- **Namespace**: Dedicated `homer` namespace
- **ConfigMap**: Contains the Homer configuration with links to all homelab services
- **Deployment**: Homer container with resource limits
- **Service**: Exposes Homer on port 8080
- **Ingress**: Configures subdomain access via https://homer.app.pesulabs.net

## Configuration

The configuration for Homer is stored in a ConfigMap and mounted into the container. The configuration includes:

- Dashboard title, subtitle, and theme
- Services organized by categories:
  - Media & Storage
  - Automation
  - Monitoring
  - Infrastructure
- Each service entry includes name, icon, subtitle, and URL

## Access

Homer is accessible at: https://homer.app.pesulabs.net

## Maintenance

To update the Homer configuration:

1. Edit the `configmap.yaml` file in this directory
2. Apply the changes: `k apply -f configmap.yaml -n homer`
3. Restart the Homer pod: `k rollout restart deployment homer -n homer`

To add a new service to the dashboard:

1. Edit the `configmap.yaml` file
2. Add the new service under the appropriate category
3. Apply the changes as above
