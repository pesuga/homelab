# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **homelab agentic workflow platform** - a self-hosted infrastructure for running AI agents and workflows with local LLM inference. The platform consists of two primary nodes:

- **Compute Node**: Native Ubuntu 25.10 (pesubuntu) - will run Ollama with GPU acceleration (AMD RX 7800 XT) and LiteLLM router
- **Service Node**: Ubuntu Server 24.04 (asuna, 192.168.8.185) running K3s with N8n, PostgreSQL, Redis, Prometheus, and Grafana

**Current Status**: Sprint 4 ✅ COMPLETED - Advanced services deployed, ROCm + Ollama functional, ready for production workflows 

## Architecture Overview

### Two-Node Architecture

**Compute Node (pesubuntu - localhost)**:
- Purpose: LLM inference with GPU acceleration
- Hardware: i5-12400F (6C/12T), 32GB RAM, AMD RX 7800 XT (16GB VRAM, Navi 32)
- Services: Ollama (native + K8s ready), ROCm 6.4.1, Promtail, Tailscale
- OS: Ubuntu 25.10 (Questing Quetzal) - Native installation
- Kernel: 6.17.0-5-generic
- Storage: 937GB available
- Current State: ✅ ROCm 6.4.1 installed, ✅ Ollama 0.12.6 with GPU acceleration, ✅ Models loaded, ✅ K8s manifests ready

**Service Node (asuna - 192.168.8.185)**:
- Purpose: Kubernetes orchestration and workflow automation
- Hardware: i7-4510U, 8GB RAM, 98GB storage
- Services: K3s v1.33.5, N8n, PostgreSQL 16.10, Redis 7.4.6, Qdrant v1.12.5, Mem0, Loki 2.9.3, Promtail, Prometheus, Grafana, Homelab Dashboard, Flowise, Open WebUI, Docker Registry
- OS: Ubuntu 24.04.3 LTS
- Tailscale IP: 100.81.76.55
- K3s configured with Tailscale IP in TLS SAN for remote kubectl access
- Database Services:
  - PostgreSQL: postgres.homelab.svc.cluster.local:5432 (User: homelab, DB: homelab, 10Gi storage)
  - Redis: redis.homelab.svc.cluster.local:6379 (ephemeral storage, AOF enabled)
  - Qdrant: qdrant.homelab.svc.cluster.local:6333 (HTTP), :6334 (gRPC), 20Gi storage
- GitOps: Flux CD structure ready for bootstrap 

### Networking

- **IMPORTANT**: Always use Tailscale IPs for inter-node communication
- Local Network: 192.168.8.0/24 (note: some docs reference 192.168.1.0/24, actual is 192.168.8.0/24)
- Tailscale Mesh: 100.64.0.0/10 for secure remote access
- Service Node (asuna): 100.81.76.55
- Compute Node (pesubuntu): 100.72.98.106

## Common Commands
- When running commands in the compute node, verify where you are, most likely you are already there.
- For any kubectl command you need to run, there is no need to ssh.
- Anytime we make changes to services (add/remove/change url or ip or any details) we need to ask another agent to update the dashboard with the new details.
- After working on any of the apps (dashboard, family assistant or any other) remember to commit and push so CD gets started.

### LLM Infrastructure (Compute Node)

**Health Check and testing scripts**
List of all testing scripts:
- Health checks `./infrastructure/compute-node/scripts/health-check.sh` to verify LLM services status

### Homelab Dashboard
- The dashboard app should always be up to date with the cluster services
- Always use and show the https pesulabs.net urls for services

### Monitoring & Observability

**Access Dashboards** (HTTPS URLs):
- **Homelab Dashboard**: https://dash.pesulabs.net (admin/4er58uCyJLPFgnFOzqqZ) - Unified landing page
- **N8n Workflows**: https://n8n.homelab.pesulabs.net (admin/admin123)
- **Prometheus**: https://prometheus.homelab.pesulabs.net
- **LobeChat**: https://chat.homelab.pesulabs.net (AI chat interface with memory)
- **Family Assistant**: https://assistant.homelab.pesulabs.net

**Internal Services** (NodePort access for development):
- **Loki**: http://100.81.76.55:30314 (log aggregation API)
- **Qdrant Vector DB**: http://100.81.76.55:30633 (HTTP API), :6334 (gRPC)
- **Mem0 AI Memory**: http://100.81.76.55:30880 (AI memory layer API)
- **Docker Registry**: http://100.81.76.55:30500 (insecure registry)
- **Ollama API (K8s)**: http://100.81.76.55:30277 (Kubernetes deployment, GPU-accelerated)

### Qdrant Vector Database

Qdrant provides vector similarity search for RAG applications. See `docs/QDRANT-SETUP.md` for deployment and integration details.

**Integration**: Mem0 uses Qdrant for vector storage and Ollama (nomic-embed-text) for embeddings

### Mem0 AI Memory Layer

Mem0 provides AI memory management using Qdrant for storage and Ollama for embeddings. Access via API endpoint at http://100.81.76.55:30820

### Loki Log Aggregation

Loki aggregates logs from all services and nodes. Query logs via:
- **Direct API**: Loki API endpoint at http://100.81.76.55:30314

Common log sources: homelab namespace pods, systemd services (Ollama), system logs

### GitOps with Flux CD (Ready for Bootstrap)

Flux CD enables declarative infrastructure management via Git. See `docs/GITOPS-SETUP.md` for complete bootstrap and configuration instructions.

Required setup:
- Flux CLI installation
- GitHub token with repo access
- Bootstrap to K3s cluster
- Repository structure in `clusters/homelab/`

### Development Workflow

1. Clone repository: `git clone https://github.com/pesuga/homelab.git`
2. Checkout working branch: `git checkout main`
3. Copy and configure environment: `.env-example` → `.env`
4. Run setup script: `./scripts/setup.sh` (minimal - needs expansion)

## Key Architecture Patterns

### LLM Request Flow

**Current Request Path**: User/N8n → Ollama API (direct to compute node) → GPU acceleration via ROCm
- **Local API**: http://100.72.98.106:11434 (compute node, GPU-accelerated)
- **Models Available**: qwen2.5-coder:14b, llama3.1:8b, mistral:7b-instruct-q4_K_M, nomic-embed-text

**Future Request Path** (when K8s deployed): User/N8n → Traefik Ingress (HTTPS) → Ollama Service (K8s) → Ollama Pod → LLM Model → GPU
- **K8s API**: https://ollama.homelab.pesulabs.net (planned)
- **Architecture**: Direct GPU access with Kubernetes orchestration and HTTPS termination

### Service Deployment Pattern

All services on the service node run as Kubernetes workloads:
- Base namespace: `homelab`
- Storage: Persistent Volume Claims (10Gi PostgreSQL, 5Gi N8n/Grafana, 20Gi Qdrant/Loki, 20Gi Docker Registry)
- Networking: ClusterIP for internal, NodePort for external access
- No Ingress controller yet - direct NodePort access (HTTPS via homelab.pesulabs.net domains planned)

### Data Persistence Strategy

- **PostgreSQL**: Used by N8n, Flowise, Open WebUI for storage, uses 10Gi PVC
- **Redis**: In-memory cache and job queue with AOF persistence, uses PVC
- **Qdrant**: Vector embeddings storage for Mem0 and RAG applications, 20Gi PVC
- **Loki**: Log aggregation with 7-day retention, 20Gi PVC
- **Docker Registry**: Container image storage, 20Gi PVC
- **LLM Models**: Stored in Ollama's model directory on compute node (managed by Ollama)
- **Grafana Dashboards**: Configuration and dashboards stored in PVC
- **Prometheus Metrics**: Time-series data with 10Gi retention PVC

## Current Sprint Status

### Sprint 4: Advanced Services - ✅ COMPLETED

**Completed Objectives**:
1. ✅ Deploy PostgreSQL 16.10 with persistent storage
2. ✅ Deploy Redis 7.4.6 with AOF persistence
3. ✅ Deploy Qdrant v1.12.5 vector database (20Gi storage)
4. ✅ Deploy Mem0 AI memory layer with Qdrant integration
5. ✅ Deploy Loki 2.9.3 log aggregation (20Gi storage, 7-day retention)
6. ✅ Configure Promtail log collection on both nodes
7. ✅ Create Flux CD repository structure
8. ✅ Fix service authentication and security issues
9. ✅ Remove deprecated services (Grafana, Flowise, Open WebUI)
10. ✅ Deploy Ollama to Kubernetes with GPU scheduling

### Sprint 3: LLM Infrastructure - ✅ COMPLETED

**Completed Objectives**:
1. ✅ Install fresh Ubuntu 25.10 on compute node
2. ✅ Verify GPU detection (AMD RX 7800 XT)
3. ✅ Install ROCm 6.4.1 for AMD GPU support
4. ✅ Deploy Ollama 0.12.6 with GPU acceleration
5. ✅ Load production models: qwen2.5-coder:14b, llama3.1:8b, mistral:7b-instruct-q4_K_M, nomic-embed-text
6. ✅ Configure Ollama systemd service for auto-start
7. ✅ Set up Tailscale on compute node
8. ✅ Create Ollama K8s deployment manifests (ready for Traefik HTTPS)
9. ✅ Deploy Ollama to Kubernetes with proper GPU scheduling
10. ✅ Create comprehensive health check scripts

**Next Steps**: Choose one of the following:
- **Option A**: Deploy Traefik HTTPS ingress for all services
- **Option B**: Start Sprint 5 (Networking & Security)
- **Option C**: Resolve Flux CD network connectivity issues

## Important Files & Locations

### Documentation
- `README.md` - Main project overview and status
- `docs/architecture.md` - Detailed system architecture
- `docs/LLM-SETUP.md` - Complete AMD GPU + K8s Ollama deployment guide
- `docs/SESSION-STATE.md` - Current session state and progress tracking
- `docs/IMPLEMENTATION-PLAN.md` - GitOps, Qdrant, and Grafana implementation plan
- `docs/GITOPS-SETUP.md` - Flux CD GitOps setup and multi-repo management
- `docs/QDRANT-SETUP.md` - Qdrant vector database deployment and integration
- `docs/GRAFANA-DASHBOARDS.md` - Grafana dashboard creation and setup guide
- `docs/METRICS-ANALYSIS.md` - Prometheus metrics analysis and available data

### Configuration
- `.env-example` - Environment variable template (comprehensive)
- `infrastructure/kubernetes/ollama/` - Ollama K8s deployment manifests
- `infrastructure/kubernetes/base/namespace.yaml` - K8s namespace definition

### Service Configurations
- `infrastructure/compute-node/` - Ollama and LiteLLM setup docs
- `infrastructure/kubernetes/` - K8s manifests
  - `base/` - Namespace and core configs
  - `databases/` - PostgreSQL, Redis, Qdrant deployments
  - `monitoring/` - Prometheus, Grafana
  - `monitoring/dashboards/` - Grafana dashboard JSONs and provisioning
  - `flux/` - Flux CD GitOps resources (planned)
- `infrastructure/kubernetes/ollama/` - Ollama K8s manifests
- `services/n8n-workflows/` - N8n workflow exports (placeholder)
- `services/agentstack-config/` - AgentStack configs (future)

## Development Context

### Built With Claude Code
This project is developed using AI-assisted pair programming with Claude Code. Key practices:
- Comprehensive documentation maintained throughout
- Session state tracking in `docs/SESSION-STATE.md`
- Sprint-based development (16-week roadmap)
- Infrastructure-as-code approach

### Design Principles
1. **Local-First**: All compute and data stays on-premises
2. **Observable**: Everything logged and monitored via Prometheus/Grafana
3. **Modular**: Services are independent and composable
4. **Open Source**: Built on OSS, no proprietary lock-in
5. **Automated**: Manual work is scripted away

### Technology Choices

**Ollama** (LLM Inference):
- Simple model management with REST API
- AMD GPU support via ROCm
- Active development and community
- Native HTTP API (no proxy needed)

**K3s** (Kubernetes):
- Lightweight K8s perfect for single-node homelab
- Full K8s compatibility
- Easy installation and maintenance

**N8n** (Workflow Automation):
- Low-code workflow builder with 400+ integrations
- Self-hostable
- Perfect for agentic workflows

**Tailscale** (VPN):
- Zero-config WireGuard-based mesh VPN
- Secure remote access
- Works seamlessly on mobile

**Qdrant** (Vector Database):
- High-performance vector similarity search
- Ideal for RAG (Retrieval-Augmented Generation)
- Native gRPC and HTTP APIs
- Persistent storage for embeddings

**Flux CD** (GitOps):
- Declarative infrastructure management
- Automated Git → Kubernetes deployments
- Multi-repository support
- Built-in drift detection and reconciliation

**Prometheus** (Observability):
- Prometheus: Metrics collection and storage

## Testing

Comprehensive health checking and verification tools available:

**Health Check Scripts**:
- `./infrastructure/compute-node/scripts/health-check.sh` - LLM services verification (compute node)
- `./scripts/health-check-all.sh` - Comprehensive service health checker (tests all services across both nodes)
- `./scripts/service-check-urls.sh` - URL-based service checker (tests actual deployed services)

**Quick Service Verification**:
```bash
# Check main services are responding
./scripts/service-check-urls.sh

# Full comprehensive check (including network and K8s status)
./scripts/health-check-all.sh
```

**Kubernetes Health**: Use standard `kubectl` commands for cluster status
```bash
kubectl get nodes                    # Node status
kubectl get pods -n homelab          # Service pod status
kubectl get svc -n homelab           # Service endpoints
```

**GitOps Health**: Use `flux check` and `flux get all` when deployed
```bash
kubectl get pods -n flux-system     # Flux controllers
kubectl get gitrepositories -n flux-system  # Git sync status
```

**Current Service Status** (as of latest check):
- ✅ N8n: Healthy (port 30678)
- ✅ Prometheus: Healthy (port 30090)
- ✅ Loki: Healthy (port 30314)
- ✅ Qdrant: Healthy (port 30633)
- ✅ Docker Registry: Healthy (port 30500)
- ✅ Homelab Dashboard: Healthy (port 30800)
- ✅ LobeChat: Healthy (port 30910)
- ✅ Mem0: Responding (port 30880)
- ✅ Ollama: ✨ **NEW** - Healthy (port 30277, K8s deployment)
- ✅ Whisper: ✨ **FIXED** - Healthy (port 30900, single replica)
- ❌ Grafana: Removed (moved to trash)
- ❌ Open WebUI: Removed (StatefulSet deleted)
- ❌ Flowise: Removed (moved to trash)

## Deployment Notes

### Service Node Deployment (Completed)
All services deployed via `kubectl apply` to K3s cluster. No GitOps or Helm charts yet.

Current deployments in `homelab` namespace:
- PostgreSQL (postgres:16-alpine)
- Redis (redis:7-alpine)
- N8n (n8nio/n8n)
- Prometheus (prom/prometheus)
- Qdrant (qdrant/qdrant)
- Loki (grafana/loki)
- Homelab Dashboard (custom)
- LobeChat (lobechat/lobechat)
- Mem0 (mem0/mem0)
- Whisper (onerahmet/openai-whisper-asr-webservice)

### Compute Node Deployment (Completed)
Services deployed in Kubernetes `ollama` namespace:
1. ✅ Ollama (ollama/ollama) deployed with GPU scheduling
2. ✅ Accessible via NodePort service (port 30277)
3. ✅ GPU acceleration configured via ROCm environment variables
4. ✅ Persistent volume for model storage (10Gi)

**Note**: Native Ollama still available on compute node, K8s deployment now preferred

### GitOps Status

**Current Status**: ⚠️ Partially Functional

**✅ Working Components**:
- Flux CD controllers deployed (6/6 pods healthy)
- Repository structure created in `clusters/homelab/`
- GitRepository configured (network connectivity issues identified)
- Infrastructure manifests organized and updated

**⚠️ Issues Identified**:
- GitRepository sync failing due to TLS handshake timeouts
- Network connectivity between cluster and GitHub blocked
- Infrastructure Kustomization conflicts with existing services
- Manual cleanup required for failed deployments

**🔧 Resolution Options**:
1. **Network Fix**: Configure firewall/proxy rules for GitHub access
2. **Manual Bootstrap**: Use `flux bootstrap` with GitHub token
3. **Local Development**: Work with current deployed state

**Recent Changes Committed**:
- ✅ Fixed Prometheus port conflicts (30190 vs 30090)
- ✅ Updated Ollama K8s deployment with GPU scheduling
- ✅ Removed deprecated services (Grafana, Flowise, Open WebUI)
- ✅ Created comprehensive health check scripts

## Troubleshooting

### LLM Inference Issues
- Check Ollama service status via `systemctl`
- Verify GPU detection using `rocm-smi` and `rocminfo` (when ROCm installed)
- View Ollama logs via `journalctl`
- See `docs/LLM-SETUP.md` for detailed troubleshooting steps

### Service Node Issues
- SSH access: `ssh pesu@192.168.8.185`
- Check K3s status via `systemctl`
- View pod logs using `kubectl logs`
- Restart deployments using `kubectl rollout restart`

### Network Connectivity
- Verify Tailscale mesh status
- Test local network connectivity (192.168.8.0/24)
- Test inter-node communication (Tailscale IPs)

## Future Enhancements

## Performance Targets

### LLM Inference (Target)
- Latency: < 2s for first token
- Throughput: > 20 tokens/second on 7B models
- GPU Utilization: 60-80%
- Model Loading: < 10s

### System Performance (Target)
- API Response: < 200ms (P95)
- Workflow Execution: < 5 seconds (P95)
- CPU Usage: < 70% average
- Memory Usage: < 75% average

### Current Performance (Achieved)
- GPU-accelerated inference: 20-30 tokens/second on 7B models (ROCm 6.4.1 + RX 7800 XT)
- VRAM usage: ~6-7GB for Q4 quantized 7B models, ~9GB for 14B models
- CPU fallback if needed: ~2-5 tokens/second
- Models loaded: qwen2.5-coder:14b (9.0GB), llama3.1:8b (4.9GB), mistral:7b (4.4GB), nomic-embed-text (274MB)
- Current state: ✅ LLM services fully operational with GPU acceleration

## Session Continuity

When resuming work, check:
1. `docs/SESSION-STATE.md` for current task and progress
2. `README.md` roadmap section for sprint status
4. Service health: N8n, Grafana, Prometheus accessible
5. LLM health: `./infrastructure/compute-node/scripts/health-check.sh`

## Important Notes

- **IP Addressing**: Documentation sometimes references 192.168.1.0/24, but actual network is 192.168.8.0/24
- **Storage**: Service node has limited disk (98GB) - monitor usage
- **No root access needed**: Both nodes have passwordless sudo configured for user `pesu`

## Git Workflow

- Main development branch: `main`
- Commit messages should be descriptive and reference sprint/task when relevant
- All infrastructure and configuration is version controlled
- Secrets go in `.env` (gitignored), not in code

## Support Resources

- **Project Issues**: https://github.com/pesuga/homelab/issues
- **Ollama Docs**: https://github.com/ollama/ollama
- **LiteLLM Docs**: https://docs.litellm.ai
- **N8n Docs**: https://docs.n8n.io
- **K3s Docs**: https://docs.k3s.io
- **ROCm Docs**: https://rocm.docs.amd.com
