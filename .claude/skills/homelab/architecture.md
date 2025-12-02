---
name: homelab-architecture
description: Complete homelab architecture knowledge and context
category: homelab
version: "1.0"
---

# 🏗️ Homelab Architecture Knowledge

Complete understanding of your two-node homelab architecture, services, networking, and operational procedures.

## System Overview

Your homelab is a **Family AI Platform** built for private, trustworthy AI services with local processing and family-aligned content filtering.

### Core Architecture Philosophy
- **Local-First**: All compute and data stays on-premises
- **Two-Node Design**: Separation of concerns (compute vs orchestration)
- **GPU-Accelerated**: AMD RX 7800 XT for LLM inference
- **Kubernetes-Native**: All services run in K3s cluster
- **Tailscale Mesh**: Secure private networking

## Node Architecture

### 🖥️ Service Node (asuna)
**Hostname**: asuna
**Local IP**: 192.168.8.185
**Tailscale IP**: 100.81.76.55
**OS**: Ubuntu 24.04.3 LTS (Jammy Jellyfish)
**Purpose**: Kubernetes orchestration and service hosting

#### Hardware Specifications
- **CPU**: Intel Core i7-4510U @ 2.00GHz (4 cores, 8 threads)
- **Memory**: 8GB DDR3L
- **Storage**: 98GB SSD
- **Network**: Built-in Ethernet + Tailscale VPN
- **Role**: Service orchestration, databases, web interfaces

#### Software Stack
- **Container Runtime**: Docker 28.5.1
- **Kubernetes**: K3s v1.33.5
- **Process Manager**: systemd
- **Package Manager**: apt
- **Security**: UFW firewall + Tailscale

#### Service Responsibilities
- Kubernetes control plane (K3s)
- Database services (PostgreSQL, Redis, Qdrant)
- Web interfaces (N8n, LobeChat, Dashboards)
- Log aggregation (Loki, Promtail)
- Monitoring (Prometheus)
- Container registry

### 🚀 Compute Node (pesubuntu)
**Hostname**: pesubuntu
**Local IP**: 192.168.8.x (dynamic)
**Tailscale IP**: 100.72.98.106
**OS**: Ubuntu 25.10 (Questing Quetzal) - Native Installation
**Purpose**: LLM inference with GPU acceleration

#### Hardware Specifications
- **CPU**: Intel Core i5-12400F (6 cores, 12 threads)
- **Memory**: 32GB DDR4
- **Storage**: 937GB available
- **GPU**: AMD Radeon RX 7800 XT (16GB VRAM, Navi 32)
- **Network**: Built-in Ethernet + Tailscale VPN
- **Role**: AI/ML workloads, GPU computing

#### Software Stack
- **GPU Stack**: ROCm 6.4.1 + HSA stack
- **LLM Runtime**: Ollama 0.12.6 (native + K8s)
- **Container Runtime**: Docker 28.5.1
- **Package Manager**: apt
- **Security**: UFW firewall + Tailscale

#### Service Responsibilities
- LLM inference (Ollama native + K8s)
- GPU acceleration for AI workloads
- Model storage and management
- Speech-to-text processing (Whisper)
- Compute-intensive family assistant features

## Network Architecture

### Network Topology
```
Internet
    │
┌───┴───┐
│ Router │ (192.168.8.1)
└───┬───┘
    │ (192.168.8.0/24)
┌───┴─────────────┐
│                 │
┌──┴───┐       ┌──┴───┐
│asuna │       │pesu  │
│.185  │       │.x    │
└──┬───┘       └──┬───┘
    │               │
└───┴───────┬───────┘
            │
    ┌───────┴───────┐
    │ Tailscale VPN │
    │ 100.64.0.0/10 │
    └───────┬───────┘
            │
    ┌───────┴───────┐
    │ 100.81.76.55  │ ← asuna
    │ 100.72.98.106 │ ← pesubuntu
    └───────────────┘
```

### Network Services

#### Tailscale Mesh
- **Mesh Network**: 100.64.0.0/10
- **asuna**: 100.81.76.55 (service node)
- **pesubuntu**: 100.72.98.106 (compute node)
- **Status**: Always-on, auto-reconnect
- **Use Case**: Secure inter-node communication, remote access

#### Kubernetes Networking
- **CNI**: Flannel (default K3s)
- **Service Network**: 10.43.0.0/16
- **Pod Network**: 10.42.0.0/16
- **Ingress**: NodePort (direct port access)
- **DNS**: CoreDNS (cluster DNS)

#### Service Exposure
- **NodePort Range**: 30000-32767
- **HTTP Services**: 300xx ports
- **Custom Ports**: 30500-309xx for specific services
- **No Ingress Controller**: Direct NodePort access (current)

## Service Architecture

### Kubernetes Namespaces

#### homelab (Primary)
- **Purpose**: Main application services
- **Services**: N8n, PostgreSQL, Redis, Qdrant, Loki, Prometheus, Dashboards
- **Storage**: PersistentVolumeClaims for each service
- **Network**: ClusterIP services with NodePort exposure

#### ollama (LLM Services)
- **Purpose**: LLM inference services
- **Services**: Ollama deployment with GPU scheduling
- **Storage**: 10Gi PVC for model storage
- **GPU**: AMD GPU acceleration via device plugins

#### kube-system (K3s System)
- **Purpose**: Kubernetes control plane
- **Services**: CoreDNS, Traefik (disabled), metrics-server
- **Management**: Handled by K3s automatically

### Service Categories

#### Core Infrastructure
- **PostgreSQL 16.10**: Primary database (10Gi storage)
- **Redis 7.4.6**: Cache and job queue (ephemeral + AOF)
- **Qdrant v1.12.5**: Vector database (20Gi storage)
- **Loki 2.9.3**: Log aggregation (20Gi storage)

#### Application Services
- **N8n**: Workflow automation (port 30678)
- **Homelab Dashboard**: Main interface (port 30800)
- **Family Assistant**: Family AI platform (port 30080)
- **LobeChat**: AI chat interface (port 30910)

#### AI/ML Services
- **Ollama Native**: LLM inference on compute node (port 11434)
- **Ollama K8s**: LLM inference in cluster (port 30277)
- **Mem0**: AI memory layer (port 30880)
- **Whisper**: Speech-to-text (port 30900)

#### Monitoring & Observability
- **Prometheus**: Metrics collection (port 30090)
- **Loki**: Log aggregation API (port 30314)
- **Docker Registry**: Container images (port 30500)

## Storage Architecture

### Persistent Storage Strategy

#### Service Node Storage
- **Root Partition**: ~98GB total
- **Database Storage**: PostgreSQL (10Gi), Redis (ephemeral)
- **Log Storage**: Loki (20Gi, 7-day retention)
- **Application Storage**: Qdrant (20Gi), Registry (20Gi)

#### Compute Node Storage
- **Root Partition**: 937GB available
- **Model Storage**: Ollama models (10Gi Kubernetes + unlimited native)
- **GPU Storage**: ROCm libraries and tools
- **Temp Storage**: Processing and temporary files

#### Backup Strategy
- **Database Backups**: PostgreSQL dumps (manual)
- **Configuration**: Git repository (version controlled)
- **Models**: Ollama models can be re-downloaded
- **Logs**: 7-day retention, not backed up

## Security Architecture

### Network Security
- **Private Network**: Tailscale mesh for inter-node communication
- **Firewall**: UFW on both nodes
- **VPN-Only Access**: Services accessible via Tailscale
- **No Public Exposure**: No ports open to internet

### Container Security
- **Isolation**: Kubernetes namespaces and pods
- **Resource Limits**: CPU/memory limits per service
- **Non-root Containers**: Most services run as non-root
- **Image Security**: Use official images when possible

### Data Security
- **Local Processing**: No data leaves the homelab
- **Family Privacy**: All conversations stored locally
- **Encrypted Communication**: Tailscale provides encryption
- **Access Control**: Family member roles and permissions

## Performance Architecture

### GPU Acceleration
- **Hardware**: AMD RX 7800 XT (16GB VRAM)
- **Software Stack**: ROCm 6.4.1 + HSA
- **LLM Support**: 7B/14B models with 4-9GB VRAM usage
- **Performance**: 20-30 tokens/second on 7B models

### Resource Allocation
- **Service Node**: Lightweight services (web, databases)
- **Compute Node**: Heavy workloads (LLM, GPU tasks)
- **Load Balancing**: Single instance per service (no scaling)
- **Resource Monitoring**: Prometheus + custom metrics

### Network Performance
- **Local Network**: Gigabit Ethernet between nodes
- **Tailscale**: WireGuard performance (~100Mbps)
- **Service Latency**: <10ms local, <50ms via Tailscale
- **Internet**: Limited by router bandwidth

## Operational Architecture

### Deployment Strategy
- **GitOps Ready**: Flux CD structure prepared
- **Manual Deployments**: Current approach with kubectl apply
- **Configuration Management**: YAML manifests in git
- **Version Control**: All infrastructure version controlled

### Monitoring Strategy
- **Metrics**: Prometheus collection from all services
- **Logs**: Loki aggregation from all nodes and pods
- **Health Checks**: Custom scripts for comprehensive validation
- **Alerting**: Manual monitoring (no alerting system yet)

### Maintenance Strategy
- **Updates**: Manual OS and application updates
- **Backups**: Manual database and configuration backups
- **Troubleshooting**: Log analysis + health check scripts
- **Documentation**: Comprehensive session tracking

## Integration Points

### Claude Code Integration
- **Project Context**: Full architecture awareness via .claude/ files
- **Validation Commands**: Service health verification
- **Session Management**: Progress tracking and validation
- **Knowledge Persistence**: Architecture context across sessions

### External Integrations
- **Git Repository**: GitHub for configuration tracking
- **Family Access**: Tailscale for secure family member access
- **Mobile Access**: Tailscale clients for remote access
- **Development**: Local development with full stack access

---

*This architecture knowledge enables precise troubleshooting, informed decision-making, and comprehensive system management across all Claude Code sessions.*