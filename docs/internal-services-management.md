# Internal Services Management Guide

This document provides guidance on how to securely access and manage the internal services in your homelab environment, including Prometheus, Loki, PostgreSQL, and Qdrant.

## Overview

For security reasons, direct external access to the following services has been removed:
- **Prometheus**: Metrics collection and monitoring
- **Loki**: Log aggregation and querying
- **PostgreSQL**: Relational database
- **Qdrant**: Vector database

These services can now only be accessed:
1. From within the cluster by other applications
2. Via port-forwarding for administrative purposes
3. Through the Tailscale subnet router for remote access

## Accessing Services for Administration

### Using kubectl port-forward

For temporary access to a service for administrative purposes, use `kubectl port-forward`:

```bash
# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Loki
kubectl port-forward -n monitoring svc/loki 3100:3100

# PostgreSQL
kubectl port-forward -n databases svc/postgres 5432:5432

# Qdrant
kubectl port-forward -n databases svc/qdrant 6333:6333
```

Then access via localhost with the appropriate port in your browser or client application.

### Using Tailscale Subnet Router

For persistent remote access, use the existing Tailscale subnet router which exposes all cluster services:

- **Prometheus**: http://10.43.184.103:9090
- **Loki**: http://10.43.81.86:3100
- **PostgreSQL**: postgresql://postgres:postgres@10.43.186.130:5432
- **Qdrant**: http://10.43.210.80:6333

## Service-Specific Management

### Prometheus

**Default credentials**: No authentication by default

**Querying metrics from applications**:
```yaml
prometheus_url: "http://prometheus.monitoring.svc.cluster.local:9090"
```

**Adding new scrapers**: Add configuration to the Prometheus ConfigMap:

```bash
kubectl edit configmap -n monitoring prometheus-config
```

Add targets under the `scrape_configs` section.

### Loki

**Default credentials**: No authentication by default

**Sending logs from applications**:
```yaml
loki_url: "http://loki.monitoring.svc.cluster.local:3100"
```

**Using Loki API**: The Loki API can be accessed at the `/loki/api/v1/` endpoint.

### PostgreSQL

**Default credentials**:
- Username: postgres
- Password: postgres (change for production use)

**Connection string for applications**:
```
postgresql://postgres:postgres@postgres.databases.svc.cluster.local:5432/your_database
```

**Creating new databases and users**:

Connect using port-forwarding and run:

```sql
-- Create a new database
CREATE DATABASE my_application;

-- Create a new user with password
CREATE USER my_app_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE my_application TO my_app_user;
```

**Backup and restore**:

Backup:
```bash
kubectl exec -n databases postgres-0 -- pg_dump -U postgres -d your_database > backup.sql
```

Restore:
```bash
cat backup.sql | kubectl exec -i -n databases postgres-0 -- psql -U postgres -d your_database
```

### Qdrant

**Default credentials**: No authentication by default

**Connection string for applications**:
```
http://qdrant.databases.svc.cluster.local:6333
```

**API access**: The Qdrant API can be accessed at the following endpoints:
- Collections API: `/collections`
- Points API: `/collections/{collection_name}/points`

**Creating collections**:

```bash
curl -X PUT http://qdrant.databases.svc.cluster.local:6333/collections/my_collection \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'
```

## Integrating with New Applications

### N8n

To connect N8n to PostgreSQL:
1. Create a credentials entry in N8n
2. Use `postgres.databases.svc.cluster.local` as host
3. Use port `5432`
4. Enter the database user and password

### Gitea

To configure Gitea with PostgreSQL (instead of SQLite):
1. Edit the configmap for Gitea
2. Update the database section:

```ini
[database]
DB_TYPE = postgres
HOST = postgres.databases.svc.cluster.local:5432
NAME = gitea
USER = gitea
PASSWD = your_secure_password
```

## Security Best Practices

1. **Create dedicated users** for each application rather than using the default postgres user
2. **Use specific database privileges** rather than granting all privileges
3. **Change default passwords** after initial setup
4. **Use network policies** to restrict which pods can access database services
5. **Regularly backup** critical database data

## Monitoring

You can monitor the internal services via Grafana, which already has dashboards configured for:
- Prometheus metrics
- PostgreSQL performance
- Kubernetes cluster monitoring
