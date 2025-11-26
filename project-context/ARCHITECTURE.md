# Homelab Architecture

**Last Updated**: 2025-11-26
**Architecture Version**: 2.0 (Phase 2 Clean)

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

**IP Assignments**: [VERIFIED 2025-11-26]
- Service node (asuna): 100.81.76.55 (Tailscale), LAN IP TBD
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

**Current**: Manual kubectl apply
**Future Consideration**: FluxCD or ArgoCD for automated deployments

### CI/CD

**Current**: Manual builds and deployments
**Future**: GitHub Actions for automated builds

### Rollout Strategy

- Rolling updates for stateless services
- Manual coordination for stateful services
- No automated canary or blue-green yet

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

### Short Term
- [ ] Implement automated backups
- [ ] Add alerting with Alertmanager
- [ ] Document disaster recovery procedures
- [ ] Add GPU workload namespace

### Medium Term
- [ ] GitOps with FluxCD
- [ ] External secrets management
- [ ] NFS or distributed storage
- [ ] Service mesh (Linkerd)

### Long Term
- [ ] Multi-cluster federation
- [ ] Advanced traffic management
- [ ] Automated scaling
- [ ] Cost optimization

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

---

**Maintenance Notes**:
- Update this file when making architectural changes
- Record decisions in ADR format
- Keep diagrams in sync with actual infrastructure
- Review quarterly for accuracy
