# System Architecture

## Overview

This document describes the complete system architecture of the homelab agentic workflow platform.

---

## Hardware Architecture

### Node Topology

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet / WAN                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────▼────────────┐
          │   GL-MT2500 Firewall   │
          │   • OpenWRT            │
          │   • Tailscale Exit     │
          │   • DHCP/DNS           │
          │   • Port Forwarding    │
          └───────────┬────────────┘
                      │
          ┌───────────▼────────────┐
          │   Local Network        │
          │   192.168.8.0/24       │
          └───────────┬────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐          ┌──────▼─────────┐
│  Compute Node  │          │  Service Node  │
│  192.168.8.10  │          │  192.168.8.20  │
└────────────────┘          └────────────────┘
```

### Compute Node Specifications

**Purpose**: LLM Inference Engine

- **Hostname**: `pesubuntu`
- **OS**: Ubuntu 25.10 (Questing Quetzal) - Native installation
- **Kernel**: 6.17.0-5-generic
- **CPU**: Intel i5-12400F (6C/12T @ 4.4GHz)
- **RAM**: 32GB DDR4 (30Gi available)
- **GPU**: AMD Radeon RX 7800 XT (Navi 32, 16GB VRAM, gfx1101)
- **Storage**:
  - 937GB NVMe SSD available
- **Network**: 1Gbps Ethernet (to be configured)
- **IP**: TBD (to be assigned)
- **Tailscale IP**: TBD (to be installed)

**Planned Services**:
- ROCm 6.4.1+ (AMD GPU Runtime)
- Ollama (LLM Server with GPU acceleration via K8s)
- Development Environment (Claude Code)
- Docker Engine (optional)
- Tailscale (VPN client)

**Current Status**:
- ✅ Fresh Ubuntu 25.10 installation
- ✅ GPU detected via lspci
- ⏳ ROCm installation pending
- ⏳ All services pending installation

### Service Node Specifications

**Purpose**: Kubernetes Cluster & Services

- **Hostname**: `service-01`
- **OS**: Ubuntu Server 22.04 LTS
- **CPU**: Intel i7 (4C/8T)
- **RAM**: 16GB DDR3
- **Storage**:
  - 256GB SSD (System + K8s)
  - 500GB HDD (Data)
- **Network**: 1Gbps Ethernet
- **IP**: 192.168.8.20
- **Tailscale IP**: 100.64.0.20

**Services Running**:
- K3s Kubernetes
- N8n
- AgentStack
- PostgreSQL
- Redis
- Prometheus
- Grafana
- Loki

### Network Node Specifications

**Purpose**: Secure Gateway & Routing

- **Device**: GL-MT2500 (Brume 2)
- **OS**: OpenWRT 23.05
- **CPU**: MediaTek MT7981B (2C @ 1.3GHz)
- **RAM**: 1GB
- **Storage**: 8GB eMMC
- **Network**:
  - WAN: 2.5Gbps Ethernet
  - LAN: 1Gbps Ethernet
- **IP**: 192.168.8.1
- **Tailscale IP**: 100.64.0.1

**Services Running**:
- Tailscale Exit Node
- OpenWRT Firewall
- DHCP Server
- DNS Server (optional: AdGuard Home)

---

## Software Architecture

### Layer 1: Infrastructure

```
┌─────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                   │
├─────────────────────────────────────────────────────────┤
│  Compute Node          │  Service Node                  │
├────────────────────────┼────────────────────────────────┤
│  • Ubuntu 25.10        │  • K3s (Kubernetes)            │
│  • AMD ROCm 6.4.1+     │  • containerd                  │
│  • systemd             │  • Helm                        │
│  • Tailscale Agent     │  • Tailscale Agent             │
│  • Docker (optional)   │  • Docker v28.5.1              │
└────────────────────────┴────────────────────────────────┘
```

### Layer 2: Data & Compute

```
┌─────────────────────────────────────────────────────────┐
│                Data & Compute Layer                      │
├─────────────────────────────────────────────────────────┤
│  LLM Stack             │  Data Stack                    │
├────────────────────────┼────────────────────────────────┤
│  • Ollama (K8s)        │  • PostgreSQL (HA)             │
│  • Model Storage (PVC) │  • Redis (Cluster)             │
│  • GPU Compute         │  • S3-compatible Storage       │
│  • Traefik Ingress     │  • Backup System               │
└────────────────────────┴────────────────────────────────┘
```

### Layer 3: Service Layer

```
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
├─────────────────────────────────────────────────────────┤
│  Routing      │  Workflows    │  Agents                 │
├───────────────┼───────────────┼─────────────────────────┤
│  • Traefik    │  • N8n        │  • AgentStack           │
│  • Ingress    │  • Temporal   │  • Custom Agents        │
│  • HTTPS/TLS  │  • Workflows  │  • Agent Tools          │
└───────────────┴───────────────┴─────────────────────────┘
```

### Layer 4: Application Layer

```
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
├─────────────────────────────────────────────────────────┤
│  • Web UIs (N8n, Grafana)                               │
│  • API Endpoints                                         │
│  • Agent Interfaces                                      │
│  • Mobile Apps (via Tailscale)                          │
└─────────────────────────────────────────────────────────┘
```

### Layer 5: Observability

```
┌─────────────────────────────────────────────────────────┐
│                 Observability Layer                      │
├─────────────────────────────────────────────────────────┤
│  Metrics      │  Logs         │  Traces                 │
├───────────────┼───────────────┼─────────────────────────┤
│  • Prometheus │  • Loki       │  • Tempo (optional)     │
│  • Grafana    │  • Promtail   │  • OpenTelemetry        │
│  • Alerts     │  • FluentBit  │  • Jaeger (optional)    │
└───────────────┴───────────────┴─────────────────────────┘
```

---

## Network Architecture

### Local Network Design

```
Internet
   │
   ▼
[GL-MT2500] (192.168.8.1)
   │
   ├─[Compute Node] (192.168.8.10)
   │   └─WSL: (172.20.0.0/16)
   │
   ├─[Service Node] (192.168.8.20)
   │   └─K8s Pod Network: (10.42.0.0/16)
   │   └─K8s Service Network: (10.43.0.0/16)
   │
   └─[Clients] (192.168.8.100-200)
```

### Tailscale Overlay Network

```
Tailscale Mesh (100.64.0.0/10)
   │
   ├─[Firewall] (100.64.0.1) - Exit Node
   ├─[Compute] (100.64.0.10)
   ├─[Service] (100.64.0.20)
   ├─[Mobile] (100.64.0.50)
   └─[Laptop] (100.64.0.51)
```

### Port Mapping

#### Compute Node (192.168.8.10)

| Port | Service | Protocol | Description |
|------|---------|----------|-------------|
| 11434 | Ollama | HTTP | LLM Inference API (local) |
| 22 | SSH | TCP | Remote Access |

**Note**: Ollama is also accessible via K8s Ingress at https://ollama.homelab.pesulabs.net

#### Service Node (192.168.8.20)

| Port | Service | Protocol | Description |
|------|---------|----------|-------------|
| 6443 | K8s API | HTTPS | Kubernetes API |
| 5678 | N8n | HTTP | Workflow UI |
| 3000 | Grafana | HTTP | Monitoring Dashboard |
| 9090 | Prometheus | HTTP | Metrics API |
| 5432 | PostgreSQL | TCP | Database |
| 6379 | Redis | TCP | Cache |
| 22 | SSH | TCP | Remote Access |

---

## Data Flow

### LLM Inference Flow

```
User Request
     │
     ▼
[N8n Workflow]
     │
     ▼
[Traefik Ingress] (HTTPS)
     │
     ▼
[Ollama Service] (K8s)
     │
     ▼
[Ollama Pod] → [GPU Compute]
     │
     ▼
[Response]
```

### Agent Workflow Flow

```
Trigger (Time/Event/API)
         │
         ▼
    [N8n Workflow]
         │
    ┌────┴────┐
    ▼         ▼
[Data Fetch] [LLM Call]
    │         │
    └────┬────┘
         ▼
   [Agent Logic]
         │
    ┌────┴────┐
    ▼         ▼
[Actions]  [Storage]
    │         │
    └────┬────┘
         ▼
     [Results]
```

### Monitoring Data Flow

```
Applications
     │
     ├─[Metrics]──────────▶[Prometheus]
     │                           │
     ├─[Logs]─────────────▶[Loki]
     │                           │
     └─[Traces]───────────▶[Tempo]
                                 │
                                 ▼
                           [Grafana]
                                 │
                                 ▼
                          [AlertManager]
                                 │
                                 ▼
                          [Notifications]
```

---

## Security Architecture

### Defense in Depth

```
Layer 1: Network Perimeter
├─ Firewall Rules (GL-MT2500)
├─ DDoS Protection
└─ Geographic Filtering

Layer 2: Network Segmentation
├─ VLANs (optional)
├─ K8s Network Policies
└─ Tailscale ACLs

Layer 3: Access Control
├─ Zero-Trust (Tailscale)
├─ OAuth/OIDC
├─ API Keys (Rotated)
└─ RBAC (Kubernetes)

Layer 4: Application Security
├─ TLS/HTTPS Everywhere
├─ Service Mesh (mTLS)
├─ Input Validation
└─ Rate Limiting

Layer 5: Data Security
├─ Encryption at Rest
├─ Encrypted Backups
├─ Secret Management (K8s Secrets)
└─ Data Retention Policies

Layer 6: Monitoring & Response
├─ Audit Logging
├─ Security Alerts
├─ Intrusion Detection
└─ Incident Response
```

---

## Deployment Architecture

### GitOps Workflow

```
Developer
    │
    ▼
[Git Push] ────▶ [GitHub]
                    │
                    ▼
              [GitHub Actions]
                    │
    ┌───────────────┴────────────────┐
    ▼                                ▼
[Build Images]              [Run Tests]
    │                                │
    ▼                                ▼
[Push to Registry]          [Security Scan]
    │                                │
    └───────────────┬────────────────┘
                    ▼
            [Deploy to K8s]
                    │
    ┌───────────────┴────────────────┐
    ▼                                ▼
[Rolling Update]              [Health Check]
    │                                │
    ▼                                ▼
[Success]                      [Rollback if Failed]
```

---

## Scaling Considerations

### Vertical Scaling

**Compute Node**:
- Add more RAM (up to 64GB)
- Upgrade GPU (e.g., RX 7900 XTX)
- Add NVMe storage

**Service Node**:
- Add more RAM (up to 32GB)
- Add storage for data
- Upgrade CPU if needed

### Horizontal Scaling

**Future Expansion**:
- Add additional compute nodes for LLM inference
- Add K8s worker nodes for services
- Implement K8s federation for multi-cluster

**Load Balancing**:
- LiteLLM handles LLM request distribution
- K8s handles service load balancing
- Traefik handles ingress traffic

---

## Disaster Recovery

### Backup Strategy

```
┌─────────────────────────────────────┐
│         Backup Sources              │
├─────────────────────────────────────┤
│  • K8s etcd                         │
│  • PostgreSQL databases             │
│  • Redis snapshots                  │
│  • LLM models                       │
│  • Configuration files              │
│  • Application data                 │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│      Backup Destinations            │
├─────────────────────────────────────┤
│  • Local NAS/External Drive         │
│  • Google Drive (encrypted)         │
│  • Offsite backup (optional)        │
└─────────────────────────────────────┘
```

### Recovery Time Objectives (RTO)

- **Critical Services**: < 1 hour
- **Standard Services**: < 4 hours
- **Full System**: < 24 hours

### Recovery Point Objectives (RPO)

- **Databases**: < 1 hour (continuous backup)
- **Configurations**: < 24 hours (daily backup)
- **Models**: < 7 days (weekly backup)

---

## Performance Targets

### Latency Targets

- LLM Inference: < 2 seconds (P95)
- API Response: < 200ms (P95)
- Workflow Execution: < 5 seconds (P95)

### Throughput Targets

- LLM Requests: 10 req/sec sustained
- API Requests: 100 req/sec sustained
- Concurrent Workflows: 20+ simultaneous

### Resource Utilization Targets

- GPU: 60-80% utilization
- CPU: < 70% average
- Memory: < 75% average
- Disk I/O: < 80% capacity

---

## Technology Choices

### Why These Technologies?

**Ollama**:
- Simple model management
- Excellent AMD GPU support via ROCm (on native Ubuntu)
- REST API for easy integration
- Active development
- Automatic GPU detection
- No proxy needed for single-GPU homelab

**K3s**:
- Lightweight Kubernetes
- Perfect for resource-constrained nodes
- Easy installation and maintenance
- Full K8s compatibility

**N8n**:
- Low-code workflow builder
- Extensive integrations (400+)
- Self-hostable
- Active community

**Tailscale**:
- Zero-config VPN
- WireGuard based (fast)
- Mesh networking
- Works on mobile

**PostgreSQL**:
- Robust and reliable
- Excellent K8s operators
- Strong consistency
- Rich query capabilities

**Grafana Stack**:
- Industry standard
- Comprehensive observability
- Good K8s integration
- Powerful visualization

---

## Security & Access Strategy

### HTTPS & Domain Strategy

**Current State**: Services accessed via HTTP with IP:port (e.g., `http://192.168.8.185:30300`)

**Target State**: HTTPS with friendly domains (e.g., `https://grafana.homelab.local`)

**See**: `/docs/HTTPS-DOMAIN-STRATEGY.md` for complete implementation guide

**Planned Implementation**:
1. Deploy Traefik ingress controller
2. Configure local DNS (`.homelab.local` domain)
3. Implement Let's Encrypt with DNS challenge OR self-signed CA
4. Create Ingress resources for all services
5. Migrate from NodePort to domain-based access

**Service Domains** (Proposed):
```
grafana.homelab.local       → Grafana (monitoring)
prometheus.homelab.local    → Prometheus (metrics)
n8n.homelab.local          → N8n (workflows)
webui.homelab.local        → Open WebUI (LLM chat)
ollama.homelab.pesulabs.net → Ollama API (Traefik HTTPS)
```

### Authentication Strategy

**Phase 1** (Current): Basic auth per-service
- Grafana: admin/admin123
- N8n: admin/admin123
- Open WebUI: self-signup

**Phase 2** (Future): Centralized SSO
- Deploy Authelia or Keycloak
- OAuth/OIDC for all services
- MFA support

---

## Future Enhancements

### Phase 2 (6-12 months)

- **Security**: HTTPS everywhere, centralized auth (SSO)
- **Networking**: Traefik ingress, domain-based access
- Multi-GPU support
- Model fine-tuning pipeline
- Advanced agent capabilities
- Multi-cluster federation

### Phase 3 (12-18 months)

- Edge deployment
- Mobile-first agents
- Voice interface
- Advanced RAG systems
- Service mesh with mTLS
- Zero-trust architecture

---

**Last Updated**: 2025-10-22
**Version**: 1.1.0
**Status**: Active Development
