# Service Dependency Map

**Purpose**: Document deployment order and dependencies for proper GitOps organization
**Last Updated**: 2025-11-18

## Deployment Order (Dependencies)

### Layer 1: Base Infrastructure (No dependencies)
Deploy first - other services depend on these

1. **Namespace** (`base/namespace.yaml`)
   - Creates: `homelab` namespace
   - Dependencies: None

2. **Registry** (`registry/`)
   - Purpose: Container image storage
   - Dependencies: None
   - Used by: All services pulling from local registry

### Layer 2: Data Stores (Depend on namespace only)
Deploy second - applications depend on these

3. **PostgreSQL** (`databases/postgres/`)
   - Purpose: Relational database
   - Dependencies: Namespace
   - Used by: N8n, Family Assistant
   - Port: 5432
   - Storage: 10Gi PVC

4. **Redis** (`databases/redis/`)
   - Purpose: Cache and job queue
   - Dependencies: Namespace
   - Used by: Family Assistant, N8n (optional)
   - Port: 6379
   - Storage: Ephemeral with AOF

5. **Qdrant** (`databases/qdrant/`)
   - Purpose: Vector database
   - Dependencies: Namespace
   - Used by: Mem0, Family Assistant
   - Ports: 6333 (HTTP), 6334 (gRPC)
   - Storage: 20Gi PVC

### Layer 3: Support Services (Depend on data stores)
Deploy third - core functionality services

6. **Loki** (`monitoring/loki/`)
   - Purpose: Log aggregation
   - Dependencies: Namespace
   - Used by: Prometheus, Grafana
   - Port: 3100
   - Storage: 20Gi PVC

7. **Mem0** (`ai-services/mem0/`)
   - Purpose: AI memory layer
   - Dependencies: Qdrant, Namespace
   - Used by: Family Assistant
   - Port: 8080
   - Note: Currently scaled to 0

### Layer 4: Core Applications (Depend on data stores + support)
Deploy fourth - main application services

8. **N8n** (`workflows/n8n/`)
   - Purpose: Workflow automation
   - Dependencies: PostgreSQL, Namespace
   - Optional: Redis
   - Port: 5678 (NodePort 30678)
   - Credentials: admin/admin123
   - Storage: 5Gi PVC

9. **Family Assistant Backend** (`family-assistant/backend/`)
   - Purpose: Family AI assistant API
   - Dependencies: PostgreSQL, Redis, Qdrant, Mem0
   - Port: 8000 (NodePort 30080)
   - Image: 100.81.76.55:30500/family-assistant:me-fixed
   - Features: MCP integration, llamacpp client

10. **Family Assistant Frontend** (`family-assistant/frontend/`)
    - Purpose: Admin dashboard
    - Dependencies: Family Assistant Backend
    - Port: 3000
    - Image: 100.81.76.55:30500/family-assistant:complete

### Layer 5: Monitoring & Dashboards (Depend on core apps)
Deploy fifth - observability and management

11. **Prometheus** (`monitoring/prometheus/`)
    - Purpose: Metrics collection
    - Dependencies: Namespace
    - Port: 9090 (NodePort 30090)
    - Storage: 10Gi PVC

12. **Grafana** (`monitoring/grafana/`)
    - Purpose: Metrics visualization
    - Dependencies: Prometheus, Loki
    - Port: 3000
    - Status: Currently deployed but may be deprecated

13. **Homelab Dashboard** (`dashboards/homelab-dashboard/`)
    - Purpose: Unified landing page
    - Dependencies: Namespace
    - Port: 5000 (NodePort 30800)
    - Credentials: admin/ChangeMe!2024#Secure
    - Image: ghcr.io/pesuga/homelab/homelab-dashboard:latest

### Layer 6: Infrastructure Services (Optional/Utility)
Deploy last - networking and utility services

14. **Traefik** (`ingress/traefik/`)
    - Purpose: Ingress controller and reverse proxy
    - Dependencies: Namespace
    - Replicas: 2
    - Ports: 80, 443, 8080 (dashboard)
    - Storage: 1Gi PVC for ACME certificates

15. **CoreDNS Custom** (`dns/coredns-custom/`)
    - Purpose: Custom DNS resolution
    - Dependencies: Namespace
    - Port: 53

16. **Discovery Dashboard** (`dashboards/discovery/`)
    - Purpose: Service discovery UI
    - Dependencies: Namespace
    - Image: nginx:alpine

## Service Groups for Kustomization

### databases/
- postgres
- redis
- qdrant

### monitoring/
- prometheus
- loki
- grafana (deprecated?)

### workflows/
- n8n

### family-assistant/
- backend
- frontend

### dashboards/
- homelab-dashboard
- discovery

### ai-services/
- mem0

### ingress/
- traefik

### dns/
- coredns-custom

### registry/
- docker-registry

## Deployment Dependencies Graph

```
namespace
├── registry (Layer 1)
├── databases (Layer 2)
│   ├── postgres → n8n, family-assistant
│   ├── redis → family-assistant
│   └── qdrant → mem0, family-assistant
├── monitoring (Layer 3)
│   ├── loki → prometheus, grafana
│   └── prometheus → grafana
├── ai-services (Layer 3)
│   └── mem0 → qdrant, family-assistant
├── workflows (Layer 4)
│   └── n8n → postgres
├── family-assistant (Layer 4)
│   ├── backend → postgres, redis, qdrant, mem0
│   └── frontend → backend
├── dashboards (Layer 5)
│   ├── homelab-dashboard
│   └── discovery
└── ingress (Layer 6)
    └── traefik
```

## Critical Deployment Order

**Must Deploy in Order**:
1. Namespace → Everything else
2. PostgreSQL → N8n, Family Assistant
3. Qdrant → Mem0 → Family Assistant
4. Redis → Family Assistant
5. Family Assistant Backend → Frontend

**Can Deploy in Parallel**:
- Databases (postgres, redis, qdrant)
- Monitoring services (prometheus, loki)
- Dashboards (homelab, discovery)

**Independent**:
- Registry (can deploy anytime)
- Traefik (can deploy anytime)
- CoreDNS (can deploy anytime)

## Storage Dependencies

### Persistent Volumes Required
- PostgreSQL: 10Gi
- Qdrant: 20Gi
- Loki: 20Gi
- Prometheus: 10Gi
- N8n: 5Gi
- Registry: 20Gi
- Traefik: 1Gi (ACME)

**Total PV Usage**: ~86Gi

## Network Dependencies

### External Services
- **GitHub**: Family Assistant MCP integration
- **Docker Hub**: Image pulls (when not using registry)
- **GHCR**: Homelab Dashboard image

### Inter-Service Communication
- All services use ClusterIP for internal communication
- NodePort for external access during development
- Ingress (Traefik) for HTTPS access (when configured)

---

**Usage**: Reference this for deployment order when using manual GitOps workflow