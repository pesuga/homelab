# Database Services

This directory contains Kubernetes manifests for database and caching services.

## Deployed Services

### PostgreSQL
- **Version**: PostgreSQL 16.10 (Alpine)
- **Purpose**: Primary relational database for N8n workflows and application data
- **Storage**: 10Gi persistent volume (local-path storage class)
- **Credentials**: Stored in `postgres-secret` (User: homelab, DB: homelab)
- **Access**: Internal only via `postgres.homelab.svc.cluster.local:5432`
- **Resources**:
  - Requests: 250m CPU, 256Mi memory
  - Limits: 1000m CPU, 1Gi memory

### Redis
- **Version**: Redis 7.4.6 (Alpine)
- **Purpose**: In-memory cache and message broker
- **Storage**: emptyDir (ephemeral - data lost on pod restart)
- **Access**: Internal only via `redis.homelab.svc.cluster.local:6379`
- **Configuration**: AOF persistence enabled (`--appendonly yes`)
- **Resources**:
  - Requests: 100m CPU, 128Mi memory
  - Limits: 500m CPU, 512Mi memory

## Deployment

To deploy or update these services:

```bash
# Deploy PostgreSQL
kubectl apply -f postgres/postgres.yaml

# Deploy Redis
kubectl apply -f redis/redis.yaml

# Verify deployments
kubectl get pods -n homelab | grep -E "postgres|redis"
kubectl get svc -n homelab | grep -E "postgres|redis"
kubectl get pvc -n homelab | grep -E "postgres|redis"
```

## Testing Connectivity

```bash
# Test PostgreSQL connection
kubectl exec -n homelab postgres-0 -- psql -U homelab -d homelab -c "SELECT version();"

# Test Redis connection
kubectl exec -n homelab $(kubectl get pod -n homelab -l app=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli ping

# List PostgreSQL databases
kubectl exec -n homelab postgres-0 -- psql -U homelab -d homelab -c "\l"

# Get Redis info
kubectl exec -n homelab $(kubectl get pod -n homelab -l app=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli INFO server
```

## Credentials

### PostgreSQL
- **User**: homelab
- **Password**: homelab123 (stored in `postgres-secret`)
- **Database**: homelab
- **Connection String**: `postgresql://homelab:homelab123@postgres.homelab.svc.cluster.local:5432/homelab`

### Redis
- No authentication configured (internal cluster access only)
- Connection: `redis://redis.homelab.svc.cluster.local:6379`

## Storage Notes

### PostgreSQL
- Uses persistent storage (10Gi PVC)
- Data survives pod restarts
- Backup recommended before upgrades

### Redis
- Currently uses ephemeral storage (emptyDir)
- Data is lost on pod restart
- Suitable for cache use case
- For persistent storage, uncomment PVC section in redis.yaml

## Monitoring

Both services are monitored via:
- Kubernetes native health checks
- Homelab Dashboard (http://100.81.76.55:30800)
- Prometheus metrics (if exporters added)

## Security Considerations

1. **PostgreSQL**:
   - Credentials stored as Kubernetes secret
   - ClusterIP service (not exposed externally)
   - Change default password in production

2. **Redis**:
   - No authentication (relies on network isolation)
   - ClusterIP service (not exposed externally)
   - Consider adding password in production

## Backup & Recovery

### PostgreSQL Backup
```bash
# Create backup
kubectl exec -n homelab postgres-0 -- pg_dump -U homelab homelab > backup.sql

# Restore from backup
kubectl exec -i -n homelab postgres-0 -- psql -U homelab homelab < backup.sql
```

### Redis Backup
```bash
# Trigger save
kubectl exec -n homelab $(kubectl get pod -n homelab -l app=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli SAVE

# Note: Data is ephemeral with current emptyDir configuration
```

## Upgrading

### PostgreSQL
```bash
# Update image version in postgres.yaml
# Apply changes
kubectl apply -f postgres/postgres.yaml

# For major version upgrades, backup first!
```

### Redis
```bash
# Update image version in redis.yaml
kubectl apply -f redis/redis.yaml

# Rolling update will be performed automatically
```
