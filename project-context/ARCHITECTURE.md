# Homelab Architecture

**Last Updated**: 2025-12-03
**Architecture Version**: 2.1 (GitOps + CI/CD)

---

## System Overview

Two-node Kubernetes homelab providing self-hosted AI services, automation, and family applications.

```
┌─────────────────────────────────────────────────────────────┐
│                    Tailscale Mesh Network                    │
│                  (100.x.x.x IP addresses)                    │
└─────────────────────────────────────────────────────────────┘
           │                                    │
           │                                    │
    ┌──────▼──────┐                      ┌─────▼──────┐
    │ Service Node│                      │Compute Node│
    │   (asuna)   │                      │            │
    │ 100.81.76.55│                      │100.72.98.106│
    │             │                      │            │
    │ K3s Master  │                      │ K3s Worker │
    │ Core Svcs   │                      │ GPU Workld │
    └─────────────┘                      └────────────┘
```

---

## Infrastructure Components

### Service Node (asuna) - 100.81.76.55

**Role**: K3s master, core services, ingress, monitoring

**Specifications**: [VERIFIED 2025-11-26]
- CPU: Intel Core i7-4510U (2 cores, 4 threads @ 2.00GHz)
- RAM: 7.7GB
- Storage: TBD
- OS: Ubuntu 24.04.3 LTS
- Kernel: 6.8.0-85-generic
- LAN IP: TBD (requires SSH to verify)

**Services**:
- K3s control plane (v1.33.5+k3s1)
- Traefik ingress controller
- PostgreSQL databases
- N8n workflow automation
- Authentik SSO
- Mem0, Qdrant, Redis

### Compute Node (pesubuntu) - 100.86.122.109

**Role**: GPU workloads, LLM inference

**Specifications**: [VERIFIED 2025-11-26]
- CPU: Intel Core i5-12400F (6 cores, 12 threads)
- RAM: 31GB
- GPU: AMD Radeon RX 7800 XT (Navi 32)
- Storage: TBD
- OS: Ubuntu 24.04.3 LTS
- Kernel: 6.14.0-36-generic
- LAN IP: 192.168.8.129

**Services**:
- LlamaCpp (systemd service, GPU-accelerated)
- GPU-accelerated inference workloads
- Future: Whisper, Stable Diffusion

---

## Networking Architecture

### Tailscale Mesh

**Purpose**: Secure inter-node communication and remote access

**Configuration**:
- All nodes joined to Tailscale network
- MagicDNS enabled for hostname resolution
- Exit node: TBD
- ACLs: TBD

**IP Assignments**: [VERIFIED 2025-11-30]
- Service node (asuna): 100.75.194.1 (Tailscale), 192.168.8.185 (LAN)
- Compute node (pesubuntu): 100.86.122.109 (Tailscale), 192.168.8.129 (LAN)

### Traefik Ingress

**Purpose**: HTTP/HTTPS ingress with automatic TLS

**Configuration**:
- Automatic Let's Encrypt certificates
- HTTP to HTTPS redirect
- IngressRoute CRDs for service routing
- Middleware for authentication (where needed)

**Entrypoints**:
- web: Port 80 (HTTP) → redirect to websecure
- websecure: Port 443 (HTTPS)

### Service Mesh

**Current**: None (direct Kubernetes services)
**Future Consideration**: Linkerd or Istio for advanced traffic management

---

## Kubernetes Architecture

### K3s Configuration

**Distribution**: K3s (lightweight Kubernetes) [VERIFIED 2025-11-26]
**Version**: v1.33.5+k3s1
**Container Runtime**: containerd 2.1.4-k3s1
**CNI**: Flannel (K3s default)
**Storage**: Local path provisioner

**Control Plane**: Service node (asuna)
**Worker Nodes**: Compute node (pesubuntu)

### Namespaces

```
default           # Core services
monitoring        # Prometheus, Grafana, Loki
n8n               # Workflow automation
family-assistant  # Family services
gpu-workloads     # GPU-accelerated services (planned)
```

### Storage Classes

- **local-path** (default): Local node storage
- Future: NFS or distributed storage for shared volumes

---

## Service Architecture

### Family Assistant

**Architecture**: Microservices

**Components**:
- **API** (family-api): Python 3.12, FastAPI, PostgreSQL
  - Authentication & user management
  - Memory system
  - Knowledge base
  - Profile management
- **Admin UI** (family-assistant-admin): React 18, TypeScript
  - Profile editing
  - Knowledge base management
  - System configuration

**Database**: PostgreSQL (dedicated instance)

**Deployment**:
- Kubernetes Deployment with 1 replica
- Service for internal communication
- IngressRoute for HTTPS access

### Dashboard

**Architecture**: Single-page application

**Stack**:
- Frontend: React 18, TypeScript, Vite
- Backend: None (static hosting)

**Features**:
- Service status overview
- Quick links to services
- System health dashboard

### N8n Workflow Automation

**Architecture**: Standalone application

**Storage**: PostgreSQL backend
**Deployment**: Kubernetes StatefulSet
**Access**: HTTPS via Traefik IngressRoute

### LlamaCpp LLM Inference

**Architecture**: Native systemd service on compute node [VERIFIED 2025-11-26]

**Why Native**:
- Direct GPU access (AMD RX 7800 XT)
- Better performance than containerized
- Simpler GPU driver management
- Configurable model switching (Kimi-VL multimodal, Mistral-7B text)

**Access**:
- HTTP API on port 8081
- Tailscale IP: 100.86.122.109:8081
- K8s Internal: `llamacpp-service.default.svc:8081`
- No HTTPS (internal only)
- Service: llamacpp-configurable.service

---

## Data Architecture

### Databases

**PostgreSQL Instances**:
1. **Family API DB**: User data, memories, knowledge
2. **N8n DB**: Workflow definitions and execution history

**Backup Strategy**: TBD

### Persistent Volumes

- Local path storage on service node
- No shared storage yet (future consideration)

### State Management

- Kubernetes ConfigMaps for configuration
- Kubernetes Secrets for sensitive data
- Environment variables for runtime config

---

## Security Architecture

### Network Security

**External Access**:
- Only HTTPS ports exposed (443)
- Tailscale for admin access
- No direct SSH to nodes (Tailscale only)

**Internal Communication**:
- Service-to-service via Kubernetes DNS
- Inter-node via Tailscale mesh

### Authentication & Authorization

**Traefik**:
- Let's Encrypt automatic certificates
- Optional middleware for auth (not implemented)

**Applications**:
- Family Assistant: JWT-based authentication
- N8n: Built-in user management
- Dashboard: No auth (read-only)

**Kubernetes RBAC**: Default K3s configuration

### Secrets Management

**Current**: Kubernetes Secrets
**Future Consideration**: External secrets operator (sealed-secrets, external-secrets)

---

## Monitoring & Observability

### Metrics (Prometheus)

**Targets**:
- Kubernetes metrics (kube-state-metrics)
- Node metrics (node-exporter)
- Application metrics (service-specific exporters)

**Storage**: Local Prometheus instance

### Visualization (Family Assistant Admin)

**Integrated Dashboards**:
- Service health monitoring
- System resource usage
- Application metrics

**Data Sources**:
- Prometheus (metrics)
- Loki (logs)
- Direct K8s API queries

### Logging (Loki)

**Architecture**: Loki + Promtail
**Log Sources**: All Kubernetes pods
**Storage**: Local Loki instance

### Alerting

**Current**: TBD
**Future**: Prometheus Alertmanager + notification channels

---

## Deployment Strategy

### GitOps Approach

**Current**: Flux CD (Implemented 2025-12-01) [VERIFIED 2025-12-03]

**Configuration**:
- GitOps tool: Flux CD v2.x
- Git repository: github.com/pesuga/homelab
- Branch: main
- Sync interval: 1 minute
- Kustomization paths:
  - `flux-system`: Core Flux components
  - `infrastructure`: All Kubernetes manifests

**How It Works**:
1. Changes committed to Git repository
2. Flux detects changes within 1 minute
3. Flux applies updated manifests to Kubernetes
4. Kubernetes reconciles to desired state

**Benefits**:
- Declarative infrastructure as code
- Automatic drift detection and correction
- Git as single source of truth
- Audit trail via Git history

### CI/CD

**Current**: GitHub Actions (Implemented 2025-12-03) [VERIFIED 2025-12-03]

**Family Portal Pipeline**:
- **Trigger**: Push to `main` with changes in `apps/family-portal/**`
- **Build**: npm ci → vite build → Docker build
- **Registry**: GitHub Container Registry (ghcr.io)
- **Image**: ghcr.io/pesuga/homelab/family-portal:latest
- **Security**: Trivy vulnerability scanning
- **Duration**: ~2-5 minutes

**Workflow**:
```
Code Push → GitHub Actions → Build & Push Image → Flux CD → Kubernetes Deploy
```

**Authentication**: GitHub Actions uses built-in GITHUB_TOKEN

**Additional Services**:
- Family Assistant API: Manual builds (future automation planned)
- Admin UI: Manual builds (future automation planned)

### Rollout Strategy

**Automated Rolling Updates**:
- Family Portal: RollingUpdate with zero downtime
  - `maxUnavailable: 0` (no downtime)
  - `maxSurge: 1` (one extra pod during rollout)
  - `imagePullPolicy: Always` (always pull latest image)

**Manual Coordination**:
- Stateful services (PostgreSQL, Redis)
- Services requiring schema migrations

**Rollback**:
- Kubernetes: `kubectl rollout undo`
- Git: Revert commit and Flux auto-applies

---

## Disaster Recovery

### Backup Strategy

**Current**: TBD
**Needs**:
- PostgreSQL backups
- Kubernetes manifests in git
- Persistent volume snapshots

### Recovery Procedures

**Current**: TBD
**Needs**:
- Node rebuild procedures
- Database restore procedures
- Service restoration order

---

## Future Architecture Plans

### Completed
- [✅] GitOps with FluxCD (2025-12-01)
- [✅] GitHub Actions CI/CD for Family Portal (2025-12-03)

### Short Term
- [ ] Implement automated backups
- [ ] Add alerting with Alertmanager
- [ ] Document disaster recovery procedures
- [ ] Add GPU workload namespace
- [ ] Extend GitHub Actions to Family Assistant API and Admin
- [ ] Automated security scanning alerts

### Medium Term
- [ ] External secrets management (sealed-secrets or external-secrets operator)
- [ ] NFS or distributed storage for shared volumes
- [ ] Service mesh (Linkerd) for advanced traffic management
- [ ] Multi-environment deployments (staging, production)

### Long Term
- [ ] Multi-cluster federation
- [ ] Advanced traffic management (canary, blue-green)
- [ ] Automated scaling based on metrics
- [ ] Cost optimization and resource efficiency

---

## Architecture Decision Records

### ADR-001: Two-Node Kubernetes vs Single Node
**Decision**: Two-node setup with dedicated GPU compute node
**Rationale**: Separate GPU workloads from core services, better resource isolation
**Trade-offs**: More complexity vs better performance for LLM inference

### ADR-002: Native LlamaCpp vs Kubernetes
**Decision**: Native LlamaCpp installation on compute node with systemd
**Rationale**: Direct GPU access, simpler driver management, better performance, configurable model switching
**Trade-offs**: Not container-native but significant performance gain. K8s service provides cluster DNS access.
**Update 2025-11-22**: Migrated from Ollama to LlamaCpp with configurable wrapper for model switching

### ADR-003: Traefik vs Nginx Ingress
**Decision**: Traefik for ingress
**Rationale**: Better K8s integration, automatic Let's Encrypt, IngressRoute CRDs
**Trade-offs**: Less common than Nginx but more Kubernetes-native

### ADR-004: PostgreSQL vs SQLite
**Decision**: PostgreSQL for production data
**Rationale**: Better concurrent access, production-ready, backup tools
**Trade-offs**: More resource usage but necessary for multi-user apps

### ADR-005: Flux CD for GitOps
**Decision**: Flux CD for GitOps deployments
**Rationale**: Automatic reconciliation, drift detection, declarative infrastructure
**Trade-offs**: Learning curve but better than manual kubectl apply
**Date**: 2025-12-01

### ADR-006: GitHub Container Registry vs Local Registry
**Decision**: GitHub Container Registry (ghcr.io) for image storage
**Rationale**: Integrated with GitHub Actions, no maintenance overhead, free for public repos, multi-arch support
**Trade-offs**: Requires internet access but more reliable than local registry
**Date**: 2025-12-03
**Context**: Local registry had IP address changes and reliability issues. Migrated to ghcr.io for better integration with CI/CD pipeline.

### ADR-007: imagePullPolicy Always for Latest Tag
**Decision**: Use `imagePullPolicy: Always` with `:latest` tag for automated deployments
**Rationale**: Ensures Kubernetes always pulls newest image from registry after CI/CD builds
**Trade-offs**: Slightly slower pod startup but necessary for automated deployments to work correctly
**Date**: 2025-12-03
**Context**: Without this, Kubernetes caches images and doesn't pull updates even when new builds are pushed.

---

**Maintenance Notes**:
- Update this file when making architectural changes
- Record decisions in ADR format
- Keep diagrams in sync with actual infrastructure
- Review quarterly for accuracy
