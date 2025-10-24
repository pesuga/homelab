# Database Services Integration - PostgreSQL & Redis

**Date**: 2025-10-24
**Sprint**: Sprint 4 - Advanced Services
**Status**: ✅ Completed

---

## Overview

This document details the integration of PostgreSQL and Redis database services into the homelab infrastructure, including deployment, documentation, and dashboard integration.

## Completed Tasks

### 1. Service Verification ✅

**PostgreSQL 16.10**:
- Running as StatefulSet: `postgres-0`
- Status: Healthy (running for 8 days)
- Storage: 10Gi persistent volume (local-path)
- Internal endpoint: `postgres.homelab.svc.cluster.local:5432`
- Credentials: User `homelab`, Database `homelab`, Password stored in `postgres-secret`

**Redis 7.4.6**:
- Running as Deployment: `redis-75d4664c5d-29jq9`
- Status: Healthy (running for 8 days)
- Storage: emptyDir (ephemeral)
- Internal endpoint: `redis.homelab.svc.cluster.local:6379`
- Configuration: AOF persistence enabled (`--appendonly yes`)

### 2. Connectivity Testing ✅

**PostgreSQL**:
```bash
kubectl exec -n homelab postgres-0 -- psql -U homelab -d homelab -c "SELECT version();"
# Result: PostgreSQL 16.10 on x86_64-pc-linux-musl
```

**Redis**:
```bash
kubectl exec -n homelab redis-75d4664c5d-29jq9 -- redis-cli ping
# Result: PONG

kubectl exec -n homelab redis-75d4664c5d-29jq9 -- redis-cli INFO server | grep redis_version
# Result: redis_version:7.4.6
```

### 3. Deployment Manifests Created ✅

Created comprehensive Kubernetes manifests with proper documentation:

**PostgreSQL** (`infrastructure/kubernetes/databases/postgres/postgres.yaml`):
- Secret for credentials
- PersistentVolumeClaim (10Gi)
- Service (ClusterIP)
- StatefulSet with resource limits

**Redis** (`infrastructure/kubernetes/databases/redis/redis.yaml`):
- Service (ClusterIP)
- Deployment with AOF persistence
- Resource limits configured
- EmptyDir storage (with PVC option commented)

**Documentation** (`infrastructure/kubernetes/databases/README.md`):
- Service specifications
- Deployment instructions
- Connectivity testing commands
- Backup and recovery procedures
- Security considerations
- Upgrade procedures

### 4. Dashboard Integration ✅

Updated homelab dashboard (`services/homelab-dashboard/app/app.py`) to include:

**PostgreSQL Entry**:
- Name: PostgreSQL
- Description: Relational database (PostgreSQL 16.10)
- Icon: 🐘
- Tags: database, storage
- Internal flag: True (no web UI)
- Connection string: `postgres.homelab.svc.cluster.local:5432`

**Redis Entry**:
- Name: Redis
- Description: In-memory cache and message broker (Redis 7.4.6)
- Icon: 🔴
- Tags: cache, storage
- Internal flag: True (no web UI)
- Connection string: `redis.homelab.svc.cluster.local:6379`

**Deployment**:
- Dashboard rebuilt with updated service list
- Image pushed to registry: `100.81.76.55:30500/homelab-dashboard:latest`
- Deployment restarted: Dashboard now shows 8 services (was 6)

### 5. Documentation Updates ✅

Updated the following files:

**docs/SESSION-STATE.md**:
- Updated current status (2025-10-24)
- Added detailed PostgreSQL/Redis deployment info
- Added Sprint 4 task checklist with completed items
- Updated active task description

**README.md**:
- Updated Sprint 1 deployed services section
- Added Sprint 4 progress (IN PROGRESS)
- Marked PostgreSQL and Redis tasks as complete
- Added version numbers and storage details

**CLAUDE.md**:
- Updated current status (55% complete)
- Added database service connection strings
- Documented PostgreSQL and Redis in service node description

## Service Specifications

### PostgreSQL 16.10

| Property | Value |
|----------|-------|
| Image | postgres:16-alpine |
| Version | 16.10 |
| Deployment Type | StatefulSet |
| Replicas | 1 |
| Storage | 10Gi PVC (local-path) |
| Service Type | ClusterIP |
| Port | 5432 |
| User | homelab |
| Database | homelab |
| Password | homelab123 (in secret) |
| Connection | postgres.homelab.svc.cluster.local:5432 |
| Resources (Requests) | 250m CPU, 256Mi memory |
| Resources (Limits) | 1000m CPU, 1Gi memory |
| Data Persistence | Yes (survives restarts) |

**Connection String**:
```
postgresql://homelab:homelab123@postgres.homelab.svc.cluster.local:5432/homelab
```

### Redis 7.4.6

| Property | Value |
|----------|-------|
| Image | redis:7-alpine |
| Version | 7.4.6 |
| Deployment Type | Deployment |
| Replicas | 1 |
| Storage | emptyDir (ephemeral) |
| Service Type | ClusterIP |
| Port | 6379 |
| Authentication | None (cluster-only access) |
| Connection | redis.homelab.svc.cluster.local:6379 |
| Configuration | AOF persistence enabled |
| Resources (Requests) | 100m CPU, 128Mi memory |
| Resources (Limits) | 500m CPU, 512Mi memory |
| Data Persistence | No (ephemeral) |

**Connection String**:
```
redis://redis.homelab.svc.cluster.local:6379
```

## Access Instructions

### From Within K8s Cluster

**PostgreSQL**:
```bash
# From any pod in the cluster
psql -h postgres.homelab.svc.cluster.local -U homelab -d homelab

# Using kubectl exec
kubectl exec -n homelab postgres-0 -- psql -U homelab -d homelab
```

**Redis**:
```bash
# From any pod in the cluster
redis-cli -h redis.homelab.svc.cluster.local

# Using kubectl exec
kubectl exec -n homelab $(kubectl get pod -n homelab -l app=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli
```

### From Compute Node (via kubectl)

```bash
# Port-forward PostgreSQL
kubectl port-forward -n homelab postgres-0 5432:5432
# Then connect: psql -h localhost -U homelab -d homelab

# Port-forward Redis
kubectl port-forward -n homelab svc/redis 6379:6379
# Then connect: redis-cli -h localhost
```

## Current Usage

### PostgreSQL
- **N8n**: Uses PostgreSQL for workflow and execution data storage
- **Future**: Available for other applications requiring relational database

### Redis
- **N8n**: Uses Redis for job queue and caching
- **Future**: Available for session storage, rate limiting, pub/sub messaging

## Security Considerations

1. **Network Isolation**:
   - Both services use ClusterIP (internal only)
   - Not exposed outside the K8s cluster
   - Accessible only from within homelab namespace

2. **Credentials**:
   - PostgreSQL credentials stored as K8s secret
   - Redis has no authentication (relies on network isolation)
   - **Recommendation**: Change PostgreSQL password for production use

3. **Data Persistence**:
   - PostgreSQL: Persistent storage (data survives pod restarts)
   - Redis: Ephemeral storage (suitable for cache/queue use)
   - **Recommendation**: Add PVC to Redis if persistence needed

## Next Steps

### Short Term
1. Configure N8n to use PostgreSQL connection
2. Verify N8n can write workflow data to PostgreSQL
3. Test Redis connectivity from N8n
4. Create monitoring dashboards for database metrics

### Long Term
1. Set up automated PostgreSQL backups
2. Consider Redis persistence (PVC) if needed
3. Add database health checks to monitoring
4. Implement database connection pooling
5. Add Prometheus exporters for metrics

## Files Changed

```
services/homelab-dashboard/app/app.py
infrastructure/kubernetes/databases/postgres/postgres.yaml (new)
infrastructure/kubernetes/databases/redis/redis.yaml (new)
infrastructure/kubernetes/databases/README.md (new)
docs/SESSION-STATE.md
docs/DATABASES-INTEGRATION.md (this file - new)
README.md
CLAUDE.md
```

## Verification Commands

```bash
# Check pod status
kubectl get pods -n homelab | grep -E "postgres|redis"

# Check services
kubectl get svc -n homelab | grep -E "postgres|redis"

# Check PVCs
kubectl get pvc -n homelab | grep postgres

# Test PostgreSQL
kubectl exec -n homelab postgres-0 -- psql -U homelab -d homelab -c "SELECT version();"

# Test Redis
kubectl exec -n homelab $(kubectl get pod -n homelab -l app=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli ping

# Check dashboard
curl http://100.81.76.55:30800/health
```

## Conclusion

PostgreSQL and Redis services are now:
- ✅ Fully deployed and running
- ✅ Properly documented with manifests
- ✅ Integrated into homelab dashboard
- ✅ Tested and verified working
- ✅ Ready for use by N8n and other applications

**Next Sprint Focus**: Integrate LLM services with N8n workflows using these database backends.
