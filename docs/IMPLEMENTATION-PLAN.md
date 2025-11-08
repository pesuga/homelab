# Implementation Plan: GitOps, Qdrant, and Grafana Dashboards

**Created**: 2025-10-25
**Status**: Planning Phase
**Sprint**: 4 Enhancement

---

## Executive Summary

This document outlines the implementation plan for three major enhancements to the homelab platform:

1. **GitOps with Flux CD**: Automated infrastructure deployment and multi-repository management
2. **Qdrant Vector Database**: Semantic search and RAG capabilities for AI workflows
3. **Grafana Dashboards**: Comprehensive observability with pre-configured dashboards

---

## 1. GitOps with Flux CD

### Overview

Implement Flux CD for declarative, Git-driven infrastructure management with support for both local infrastructure and external application repositories.

### Current State Analysis

**Existing Infrastructure**:
- Kubernetes manifests in `infrastructure/kubernetes/` organized by service type
- Manual `kubectl apply` deployment process
- No automated sync or reconciliation
- Services: N8n, Flowise, PostgreSQL, Redis, Prometheus, Grafana, Registry
- K3s cluster on service node (asuna - 192.168.8.185)

**Challenges**:
- Manual deployments are error-prone
- No drift detection
- Difficult to manage multiple application sources
- No automated rollback capabilities

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Git Repository                             │
│  github.com/pesuga/homelab (main repo)                       │
├─────────────────────────────────────────────────────────────┤
│  flux-system/                                                │
│  ├── gotk-components.yaml    (Flux controllers)             │
│  ├── gotk-sync.yaml           (Main repo sync)              │
│  └── kustomization.yaml                                      │
│                                                               │
│  infrastructure/kubernetes/                                  │
│  ├── flux/                    (NEW)                          │
│  │   ├── sources/             (GitRepository CRDs)          │
│  │   ├── kustomizations/      (Kustomization CRDs)          │
│  │   └── helmrepositories/    (HelmRepository CRDs)         │
│  ├── base/                                                   │
│  ├── databases/                                              │
│  ├── monitoring/                                             │
│  └── apps/                    (NEW - external apps)          │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Flux watches
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              K3s Cluster (asuna)                             │
│  ┌───────────────────────────────────────┐                  │
│  │   flux-system namespace               │                  │
│  │   ├── source-controller               │                  │
│  │   ├── kustomize-controller            │                  │
│  │   ├── helm-controller                 │                  │
│  │   └── notification-controller         │                  │
│  └───────────────────────────────────────┘                  │
│                          │                                   │
│                          │ reconciles                        │
│                          ▼                                   │
│  ┌───────────────────────────────────────┐                  │
│  │   homelab namespace                   │                  │
│  │   All services auto-deployed          │                  │
│  └───────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Repository Structure (Post-Implementation)

```
homelab/
├── flux-system/                  # Flux bootstrap configs
│   ├── gotk-components.yaml
│   ├── gotk-sync.yaml
│   └── kustomization.yaml
│
├── infrastructure/
│   └── kubernetes/
│       ├── flux/                 # NEW: Flux resources
│       │   ├── sources/
│       │   │   ├── homelab.yaml           # This repo
│       │   │   └── external-apps.yaml     # External repos
│       │   ├── kustomizations/
│       │   │   ├── infrastructure.yaml    # Core infra
│       │   │   ├── databases.yaml
│       │   │   ├── monitoring.yaml
│       │   │   └── apps.yaml
│       │   └── helmrepositories/
│       │       └── bitnami.yaml           # Example Helm repo
│       │
│       ├── base/                 # Existing
│       │   └── namespace.yaml
│       ├── databases/            # Existing
│       │   ├── postgres/
│       │   └── redis/
│       ├── monitoring/           # Existing
│       │   ├── prometheus-deployment.yaml
│       │   └── grafana-deployment.yaml
│       └── apps/                 # NEW: Managed external apps
│           └── README.md
│
└── docs/
    ├── GITOPS-SETUP.md          # NEW
    └── IMPLEMENTATION-PLAN.md   # This file
```

### Multi-Repository Pattern

**Use Cases**:
1. **Infrastructure repositories**: This homelab repo manages core services
2. **Application repositories**: Separate repos for specific workloads
3. **Third-party Helm charts**: Bitnami, Prometheus community charts, etc.

**Pattern**: GitRepository + Kustomization

Example for external app:
```yaml
# infrastructure/kubernetes/flux/sources/my-app.yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/user/my-app
  ref:
    branch: main
  secretRef:  # If private repo
    name: my-app-git-credentials
---
# infrastructure/kubernetes/flux/kustomizations/my-app.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 5m
  path: ./deploy/kubernetes
  prune: true
  sourceRef:
    kind: GitRepository
    name: my-app
  targetNamespace: homelab
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: my-app
      namespace: homelab
```

### Implementation Steps

1. **Install Flux CLI** (on local machine or service node)
2. **Bootstrap Flux to K3s cluster**
3. **Migrate existing manifests** to Flux-compatible structure
4. **Test reconciliation** with a simple change
5. **Add external repository support**
6. **Configure notifications** (optional: Slack/Discord webhooks)

### Benefits

- **Automated deployments**: Push to Git → automatic K8s deployment
- **Drift detection**: Flux corrects manual changes
- **Multi-source**: Manage apps from different repos
- **Rollback**: Git revert = infrastructure revert
- **Audit trail**: All changes in Git history
- **Progressive delivery**: Canary deployments with Flagger (future)

---

## 2. Qdrant Vector Database

### Overview

Add Qdrant as a vector database for semantic search, embeddings storage, and Retrieval-Augmented Generation (RAG) workflows.

### Use Cases

1. **RAG for N8n workflows**: Store and retrieve document embeddings
2. **Semantic search**: Find similar documents/code/logs
3. **Memory for LLM agents**: Persistent agent memory
4. **Recommendation systems**: Similarity-based recommendations
5. **Flowise integration**: Vector stores for LangChain

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Application Layer                                           │
│  ┌─────────┐  ┌─────────┐  ┌───────────┐                   │
│  │   N8n   │  │ Flowise │  │  Agents   │                   │
│  └────┬────┘  └────┬────┘  └─────┬─────┘                   │
│       │            │              │                          │
│       └────────────┴──────────────┘                          │
│                    │                                         │
│                    │ gRPC (6334) or REST (6333)             │
│                    ▼                                         │
│  ┌─────────────────────────────────────────┐                │
│  │         Qdrant Service                  │                │
│  │  qdrant.homelab.svc.cluster.local       │                │
│  │  Ports: 6333 (HTTP), 6334 (gRPC)        │                │
│  └─────────────────────────────────────────┘                │
│                    │                                         │
│                    ▼                                         │
│  ┌─────────────────────────────────────────┐                │
│  │    Persistent Storage (20Gi)            │                │
│  │    /qdrant/storage                      │                │
│  └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘

Integration with LLM Stack:
┌──────────┐      ┌──────────┐      ┌─────────┐      ┌─────────┐
│   N8n    │─────▶│  Ollama  │─────▶│Embedding│─────▶│ Qdrant  │
│ Workflow │      │(compute) │      │ Model   │      │ Storage │
└──────────┘      └──────────┘      └─────────┘      └─────────┘
                                                            │
                                                            │
                                                      Store vectors
```

### Deployment Specification

**Container**: `qdrant/qdrant:latest` (or pinned version v1.7.4+)

**Resource Requirements**:
- CPU: 500m (request), 2 cores (limit)
- Memory: 512Mi (request), 2Gi (limit)
- Storage: 20Gi persistent volume

**Ports**:
- 6333: HTTP/REST API
- 6334: gRPC API (recommended for performance)

**Configuration**:
- Storage path: `/qdrant/storage`
- Collections auto-created via API
- No authentication by default (internal cluster access only)
- Optional: Enable API key authentication for production

### Kubernetes Manifests Structure

```
infrastructure/kubernetes/databases/qdrant/
├── qdrant.yaml              # Main deployment manifest
│   ├── PersistentVolumeClaim (20Gi)
│   ├── Service (ClusterIP)
│   ├── Service (NodePort - optional for external access)
│   └── StatefulSet
└── qdrant-config.yaml       # ConfigMap for custom config (optional)
```

### Integration Points

1. **N8n**: Use HTTP Request node or community Qdrant node
2. **Flowise**: Built-in Qdrant vector store support
3. **LangChain (Python)**: `langchain-qdrant` package
4. **Direct API**: REST or gRPC client libraries

### Testing Strategy

```bash
# 1. Verify deployment
kubectl get pods -n homelab -l app=qdrant
kubectl get svc -n homelab qdrant

# 2. Port-forward for local testing
kubectl port-forward -n homelab svc/qdrant 6333:6333

# 3. Health check
curl http://localhost:6333/health

# 4. Create test collection
curl -X PUT http://localhost:6333/collections/test \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'

# 5. Verify collection
curl http://localhost:6333/collections/test
```

### Data Persistence

- **Storage Class**: `local-path` (K3s default)
- **Backup Strategy**:
  - Qdrant supports snapshot API
  - Schedule periodic snapshots to backup volume
  - Future: Integrate with Velero for cluster backups

---

## 3. Grafana Dashboards

### Overview

Configure comprehensive Grafana dashboards for observability across all homelab services.

### Current State

- Grafana deployed and accessible at http://100.81.76.55:30300
- Prometheus configured as data source
- **No dashboards configured yet**

### Available Metrics Sources

**Prometheus Exporters**:
1. **Node Exporter** (system metrics): CPU, memory, disk, network
2. **cAdvisor** (container metrics): Built into K3s kubelet
3. **Kubernetes metrics**: Pods, deployments, services
4. **Application metrics**:
   - N8n (if instrumented)
   - PostgreSQL (via postgres_exporter if installed)
   - Redis (via redis_exporter if installed)

**Metrics Categories**:
```
System Metrics:
├── node_cpu_seconds_total
├── node_memory_*
├── node_disk_*
├── node_network_*
└── node_filesystem_*

Kubernetes Metrics:
├── kube_pod_*
├── kube_deployment_*
├── kube_node_*
└── container_*

Database Metrics:
├── pg_stat_* (PostgreSQL)
└── redis_* (Redis)

Custom Metrics:
└── Application-specific (N8n, Ollama, etc.)
```

### Proposed Dashboards

#### Dashboard 1: Homelab Overview
**Purpose**: High-level health and status of entire platform

**Panels**:
- Cluster status (nodes, pods running/failed)
- Overall CPU/Memory usage
- Storage utilization
- Network I/O
- Service uptime
- Recent alerts

**Layout**: Single-page overview, 6-8 panels

---

#### Dashboard 2: Kubernetes Cluster
**Purpose**: Detailed K8s cluster metrics

**Panels**:
- Node resources (per-node CPU/memory/disk)
- Pod status by namespace
- Container restarts
- Deployment replica status
- PVC usage
- Network traffic by pod

**Layout**: Multi-row layout, ~12 panels

---

#### Dashboard 3: Database Performance
**Purpose**: PostgreSQL and Redis monitoring

**PostgreSQL Panels**:
- Connections (active/idle)
- Query performance (slow queries)
- Cache hit ratio
- Transaction rate
- Locks and conflicts
- Database size growth

**Redis Panels**:
- Memory usage
- Commands per second
- Hit/miss ratio
- Connected clients
- Keyspace statistics

**Layout**: Two sections (PostgreSQL + Redis)

---

#### Dashboard 4: LLM Infrastructure (Future)
**Purpose**: Monitor Ollama and LiteLLM

**Panels**:
- Model inference latency
- GPU utilization (ROCm metrics)
- VRAM usage
- Tokens per second
- Request queue depth
- Model cache hit ratio
- LiteLLM router performance

**Note**: Requires custom exporters (to be implemented in Sprint 3)

---

#### Dashboard 5: N8n Workflows
**Purpose**: Workflow execution metrics

**Panels**:
- Workflow execution count
- Success/failure rate
- Execution duration
- Active workflows
- Error rate by workflow
- Webhook response times

**Note**: Requires N8n metrics instrumentation

---

### Implementation Approach

**Option 1: Manual Dashboard Creation** (Recommended for customization)
- Use Grafana UI to build dashboards
- Export JSON for version control
- Store in `infrastructure/kubernetes/monitoring/dashboards/`

**Option 2: Pre-built Dashboard Import**
- Import community dashboards from grafana.com
- Recommended IDs:
  - `1860`: Node Exporter Full
  - `6417`: Kubernetes Cluster Monitoring
  - `9628`: PostgreSQL Database
  - `11835`: Redis Dashboard
- Customize after import

**Option 3: Provisioned Dashboards** (GitOps-friendly)
- Define dashboards as JSON/YAML
- Mount as ConfigMaps
- Auto-loaded on Grafana startup

### Dashboard Provisioning Structure

```
infrastructure/kubernetes/monitoring/
├── grafana-deployment.yaml           # Existing
├── dashboards/                       # NEW
│   ├── provisioning/
│   │   └── dashboards.yaml           # Dashboard provider config
│   ├── homelab-overview.json
│   ├── kubernetes-cluster.json
│   ├── database-performance.json
│   ├── llm-infrastructure.json       # Future
│   └── n8n-workflows.json            # Future
└── datasources/                      # NEW
    └── prometheus.yaml               # Prometheus datasource config
```

### Grafana ConfigMap Pattern

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: homelab
data:
  dashboards.yaml: |
    apiVersion: 1
    providers:
      - name: 'default'
        orgId: 1
        folder: 'Homelab'
        type: file
        options:
          path: /var/lib/grafana/dashboards
  homelab-overview.json: |
    {
      "dashboard": { ... },
      "overwrite": true
    }
```

---

## Implementation Timeline

### Phase 1: Qdrant Deployment (Week 1, Days 1-2)
- [ ] Create Qdrant Kubernetes manifests
- [ ] Deploy to K3s cluster
- [ ] Verify deployment and health
- [ ] Test basic collection creation
- [ ] Document connection details for N8n/Flowise

### Phase 2: Grafana Dashboards (Week 1, Days 3-4)
- [ ] Query Prometheus for available metrics
- [ ] Identify gaps (install exporters if needed)
- [ ] Create Dashboard 1: Homelab Overview
- [ ] Create Dashboard 2: Kubernetes Cluster
- [ ] Create Dashboard 3: Database Performance
- [ ] Export and version control dashboard JSONs

### Phase 3: Flux GitOps Setup (Week 1-2, Days 5-7)
- [ ] Install Flux CLI
- [ ] Bootstrap Flux to K3s cluster
- [ ] Create Flux directory structure
- [ ] Migrate existing manifests to Flux structure
- [ ] Create GitRepository and Kustomization CRDs
- [ ] Test reconciliation loop
- [ ] Document multi-repo pattern
- [ ] Add example external app integration

### Phase 4: Documentation & Testing (Week 2, Day 8)
- [ ] Update CLAUDE.md with new services
- [ ] Update README.md architecture diagrams
- [ ] Create GITOPS-SETUP.md guide
- [ ] Create QDRANT-SETUP.md guide
- [ ] Create GRAFANA-DASHBOARDS.md guide
- [ ] End-to-end testing
- [ ] Update session state

---

## Success Criteria

### GitOps
- ✅ Flux controllers running in `flux-system` namespace
- ✅ Existing infrastructure managed by Flux
- ✅ Commit to Git → auto-deploy to cluster (< 5 min)
- ✅ External repository pattern documented and tested
- ✅ Drift detection working (manual change reverted)

### Qdrant
- ✅ Qdrant pod running and healthy
- ✅ gRPC and HTTP APIs accessible
- ✅ Test collection created successfully
- ✅ Integration example with N8n documented
- ✅ Data persists across pod restarts

### Grafana Dashboards
- ✅ At least 3 dashboards created and functional
- ✅ All panels showing real data (no "No data" errors)
- ✅ Dashboards version-controlled in Git
- ✅ Auto-provisioning working (if implemented)
- ✅ Useful for day-to-day operations

---

## Risk Mitigation

### Risk 1: Flux Migration Breaks Existing Services
**Mitigation**:
- Take K3s etcd snapshot before migration
- Test Flux in separate namespace first
- Migrate one service at a time
- Keep manual deployment scripts as backup

### Risk 2: Qdrant Resource Exhaustion
**Mitigation**:
- Set resource limits (2Gi memory max)
- Monitor disk usage (20Gi should be sufficient initially)
- Configure collection size limits
- Document cleanup procedures

### Risk 3: Grafana Performance with Many Dashboards
**Mitigation**:
- Limit query time ranges
- Use query caching
- Optimize Prometheus queries (avoid high-cardinality labels)
- Consider separate Grafana instance for different dashboard groups

### Risk 4: GitOps Secret Management
**Challenge**: Secrets can't be stored in Git plaintext

**Solutions**:
1. **Sealed Secrets**: Encrypt secrets, safe for Git
2. **SOPS**: Mozilla's Secret OPerationS
3. **External Secrets Operator**: Fetch from external vault
4. **Initial approach**: Keep existing Secret manifests, manage outside Flux

---

## Dependencies

### Software Requirements
- Flux CLI v2.0+
- kubectl with K3s cluster access
- Git access to homelab repository
- Grafana v9.0+ (already deployed)
- Prometheus (already deployed)

### Service Node Resources
- **Current**: 8GB RAM, 98GB storage
- **Qdrant addition**: +512Mi RAM, +20Gi storage
- **Flux addition**: +256Mi RAM (controllers)
- **Total additional**: ~1GB RAM, 20GB storage
- **Assessment**: Should be within limits, monitor closely

---

## Rollback Plan

### Flux Rollback
```bash
# Uninstall Flux
flux uninstall

# Revert to manual kubectl apply
kubectl apply -f infrastructure/kubernetes/base/
kubectl apply -f infrastructure/kubernetes/databases/
# etc.
```

### Qdrant Rollback
```bash
# Delete Qdrant resources
kubectl delete -f infrastructure/kubernetes/databases/qdrant/

# PVC will persist (manual deletion required)
kubectl delete pvc qdrant-pvc -n homelab
```

### Dashboard Rollback
- No rollback needed (non-destructive)
- Delete unwanted dashboards via Grafana UI

---

## Next Steps

After plan approval:

1. **Review this plan** with user for feedback
2. **Prioritize**: Which feature to implement first?
3. **Begin implementation** following the timeline
4. **Iterative testing** after each phase
5. **Documentation updates** throughout

---

## Questions for Clarification

1. **Flux**: Do you want to manage ALL infrastructure via Flux, or keep some services manually deployed?
2. **Qdrant**: Do you have specific embedding models in mind? (affects vector dimensions)
3. **Dashboards**: Should we start with imported community dashboards or build custom from scratch?
4. **Timeline**: Is 1-2 weeks acceptable, or should we accelerate/decelerate?
5. **Secrets**: Preference for secret management approach (Sealed Secrets, SOPS, or manual)?

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
**Next Review**: After Phase 1 completion
