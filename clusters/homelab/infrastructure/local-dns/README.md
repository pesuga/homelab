# Local DNS Service

This directory contains the Kubernetes manifests for deploying a custom CoreDNS server in the homelab environment to provide local DNS resolution for all services.

## Overview

Instead of configuring DNS on each individual device, this service provides centralized DNS resolution for all `.app.pesulabs.net` domains within your local network. The CoreDNS server is configured to resolve all homelab service domains to the ingress controller's IP address.

## Components

- **Namespace**: Dedicated `local-dns` namespace
- **ConfigMap**: Contains the CoreDNS configuration with rules for resolving application domains
- **Deployment**: CoreDNS container with resource limits
- **Service**: Exposes CoreDNS on port 53 (UDP and TCP) as a LoadBalancer

## Configuration

The CoreDNS configuration includes:

1. Explicit host entries for all current applications
2. A template rule to catch any new `.app.pesulabs.net` subdomains and resolve them automatically
3. Forwarding of all other DNS queries to public DNS resolvers (8.8.8.8 and 8.8.4.4)

## Usage

To use this DNS service for your entire network:

1. Configure your router to use the CoreDNS LoadBalancer IP as the primary DNS server
2. Alternatively, configure individual devices to use this DNS server

To find the DNS server IP after deployment:

```bash
k get svc -n local-dns
```

## Maintenance

To add new application domains, update the `configmap.yaml` file with additional host entries.

The template rule will automatically resolve any `*.app.pesulabs.net` domains to your ingress controller's IP without requiring manual updates for each new service.
