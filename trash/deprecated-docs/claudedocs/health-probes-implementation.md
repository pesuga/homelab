# Health Probes Implementation Summary

**Date**: 2025-11-04
**Task**: Add health probes and Prometheus monitoring to N8n, PostgreSQL, and Redis services

## Implemented Changes

### 1. N8n Deployment
**File**: `infrastructure/kubernetes/services/n8n/n8n.yaml` (created)

**Health Probes**:
- **Liveness**: HTTP GET on `/healthz` port 5678
  - Initial delay: 60s
  - Period: 30s
  - Timeout: 5s
  - Failure threshold: 3

- **Readiness**: HTTP GET on `/healthz` port 5678
  - Initial delay: 30s
  - Period: 10s
  - Timeout: 5s
  - Failure threshold: 3

**Prometheus Annotations**:
```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "5678"
prometheus.io/path: "/metrics"
```

### 2. PostgreSQL StatefulSet
**File**: `infrastructure/kubernetes/databases/postgres/postgres.yaml` (updated)

**Health Probes**:
- **Liveness**: Command execution `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`
  - Initial delay: 30s
  - Period: 10s
  - Timeout: 5s
  - Failure threshold: 3

- **Readiness**: Command execution `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`
  - Initial delay: 10s
  - Period: 5s
  - Timeout: 3s
  - Failure threshold: 3

**Prometheus Annotations**:
```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "5432"
```

### 3. Redis Deployment
**File**: `infrastructure/kubernetes/databases/redis/redis.yaml` (updated)

**Health Probes**:
- **Liveness**: Command execution `redis-cli ping`
  - Initial delay: 30s
  - Period: 10s
  - Timeout: 5s
  - Failure threshold: 3

- **Readiness**: Command execution `redis-cli ping`
  - Initial delay: 10s
  - Period: 5s
  - Timeout: 3s
  - Failure threshold: 3

**Prometheus Annotations**:
```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "6379"
```

## Deployment Status

All three services are now running with health probes enabled:

```
n8n-68cbb87fb8-48f2q   True  true
postgres-0             True  true
redis-cf7487ccc-fmmbr  True  true
```

## Benefits

1. **Health Monitoring**: Kubernetes can now automatically detect and restart unhealthy pods
2. **Prometheus Integration**: Services are annotated for automatic metrics scraping
3. **Readiness Gates**: Prevents traffic from being routed to pods that aren't ready
4. **Observability**: Prometheus can now track service health and availability

## Known Limitations (Option A Implementation)

- **Basic Health Checks Only**: Using TCP/HTTP probes, not full metrics exporters
- **Limited Metrics**: PostgreSQL and Redis don't natively expose Prometheus metrics
  - For detailed database metrics, consider Option B (postgres-exporter, redis-exporter)
- **No Custom Metrics**: Only basic up/down status, not detailed performance metrics

## Next Steps (Optional - Option B)

If you need more detailed metrics:

1. Deploy `postgres-exporter` for PostgreSQL metrics:
   - Connection pool stats
   - Query performance
   - Database size and growth
   - Replication lag

2. Deploy `redis-exporter` for Redis metrics:
   - Memory usage
   - Key statistics
   - Command statistics
   - Persistence status

3. Update Grafana dashboards to visualize the new metrics

## Verification Commands

```bash
# Check health probe status
kubectl get pods -n homelab -o wide | grep -E "n8n|postgres|redis"

# Verify health probes configuration
kubectl describe pod <pod-name> -n homelab | grep -A 10 "Liveness:\|Readiness:"

# Check Prometheus annotations
kubectl get pod <pod-name> -n homelab -o yaml | grep -A 5 "annotations:"

# Test health endpoints
kubectl exec -n homelab <n8n-pod> -- curl -s http://localhost:5678/healthz
kubectl exec -n homelab postgres-0 -- pg_isready -U homelab -d homelab
kubectl exec -n homelab <redis-pod> -- redis-cli ping
```

## Troubleshooting

During implementation, we encountered:

1. **CPU Resource Exhaustion**: asuna node was at 97% CPU allocation
   - Resolution: Deleted duplicate pods from rolling updates

2. **StatefulSet Update Issues**: postgres pod couldn't schedule due to PVC node affinity
   - Resolution: Scaled statefulset down to 0, then back to 1

3. **Rolling Update Conflicts**: Multiple replicasets created duplicate pods
   - Resolution: Deleted old replicasets and cleaned up pending/crashing pods

## Files Modified/Created

- ✅ Created: `infrastructure/kubernetes/services/n8n/n8n.yaml`
- ✅ Updated: `infrastructure/kubernetes/databases/postgres/postgres.yaml`
- ✅ Updated: `infrastructure/kubernetes/databases/redis/redis.yaml`
- ✅ Applied all manifests to cluster
- ✅ Verified health probes are working
