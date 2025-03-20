# PostgreSQL Database Setup

This document outlines the setup and configuration of PostgreSQL in the homelab Kubernetes cluster.

## Overview

PostgreSQL is deployed as a stateful application in the `database` namespace with persistent storage. The deployment includes:

- PostgreSQL 15 (Alpine-based image for smaller footprint)
- Persistent storage for data
- Custom configuration via ConfigMap
- Secure credentials stored in Kubernetes Secrets
- Ingress for external access

## Configuration

The PostgreSQL instance is configured with the following settings:

- Memory optimized for a small homelab environment
- Logging enabled for monitoring and debugging
- Autovacuum enabled for maintenance
- Replication settings configured for potential future scaling

## Connection Details

### Internal Access (within the cluster)
- **Service Name**: `postgresql.database.svc.cluster.local`
- **Port**: 5432
- **Default Database**: postgres
- **Default User**: postgres (stored in secret)
- **Default Password**: postgrespassword (stored in secret)

### External Access
- **URL**: https://postgresql.app.pesulabs.net
- **Port**: 5432
- **Default Database**: postgres
- **Default User**: postgres
- **Default Password**: postgrespassword

## Usage

To connect to PostgreSQL from within the cluster, applications should use the following connection string:

```
postgresql://postgres:postgrespassword@postgresql.database.svc.cluster.local:5432/postgres
```

For external access, use:

```
postgresql://postgres:postgrespassword@postgresql.app.pesulabs.net:5432/postgres
```

For security reasons, it's recommended to:

1. Create application-specific users and databases
2. Use Kubernetes Secrets to store and inject credentials
3. Implement proper access controls

## Maintenance

### Backup and Restore

To backup the PostgreSQL database:

```bash
kubectl exec -n database $(kubectl get pods -n database -l app=postgresql -o jsonpath='{.items[0].metadata.name}') -- \
  pg_dump -U postgres postgres > backup.sql
```

To restore from a backup:

```bash
cat backup.sql | kubectl exec -i -n database $(kubectl get pods -n database -l app=postgresql -o jsonpath='{.items[0].metadata.name}') -- \
  psql -U postgres postgres
```

### Accessing the PostgreSQL Shell

To access the PostgreSQL interactive shell:

```bash
kubectl exec -it -n database $(kubectl get pods -n database -l app=postgresql -o jsonpath='{.items[0].metadata.name}') -- \
  psql -U postgres
```

## Resource Management

The PostgreSQL pod is configured with the following resource limits:

- CPU: 200m (request: 20m)
- Memory: 256Mi (request: 64Mi)

These values can be adjusted based on the workload and available cluster resources.

## Future Improvements

- Implement automated backups
- Configure high availability with replication
- Set up monitoring with Prometheus and Grafana
- Create a PostgreSQL operator for easier management
