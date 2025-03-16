# Owncloud for Homelab

This directory contains Kubernetes manifests for deploying Owncloud in a Kubernetes cluster with path-based routing via Traefik ingress.

## Prerequisites

Before deploying, ensure you have created the following directories on your Kubernetes node(s):

```bash
mkdir -p /mnt/homedrive/owncloud/data
mkdir -p /mnt/homedrive/owncloud/mariadb
mkdir -p /mnt/homedrive/owncloud/apache
```

Also ensure proper permissions are set:

```bash
chown -R 1000:1000 /mnt/homedrive/owncloud
```

## Configuration

- Owncloud is configured to use path-based routing, accessible at https://asuna.chimp-ulmer.ts.net/owncloud
- Persistent storage is provided via hostPath volumes pointing to `/mnt/homedrive/owncloud/`
- MariaDB is deployed as part of this setup for database storage
- Secrets contain default passwords that should be changed

## Security Note

Update the passwords in the secrets.yaml file before deploying to production.
