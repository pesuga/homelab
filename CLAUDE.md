# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **homelab agentic workflow platform** - a self-hosted infrastructure for running AI agents and workflows with local LLM inference. The platform consists of two primary nodes:

- **Compute Node**: Native Ubuntu 25.10 (pesubuntu) - will run Ollama with GPU acceleration (AMD RX 7800 XT) and LiteLLM router
- **Service Node**: Ubuntu Server 24.04 (asuna, 192.168.8.185) running K3s with N8n, PostgreSQL, Redis, Prometheus, and Grafana

**Current Status**: Sprint 4 - Advanced Services IN PROGRESS (55% complete, 3 of 7 sprints done, Sprint 4 in progress with database services documented)

## Architecture Overview

### Two-Node Architecture

**Compute Node (pesubuntu - localhost)**:
- Purpose: LLM inference with GPU acceleration
- Hardware: i5-12400F (6C/12T), 32GB RAM, AMD RX 7800 XT (16GB VRAM, Navi 32)
- Services: Ollama (port 11434), LiteLLM (port 8000) - to be installed
- OS: Ubuntu 25.10 (Questing Quetzal) - Native installation
- Kernel: 6.17.0-5-generic
- Storage: 937GB available
- Current State: Fresh Ubuntu installation, GPU detected, ready for ROCm + Ollama setup

**Service Node (asuna - 192.168.8.185)**:
- Purpose: Kubernetes orchestration and workflow automation
- Hardware: i7-4510U, 8GB RAM, 98GB storage
- Services: K3s v1.33.5, N8n, Flowise, PostgreSQL 16.10, Redis 7.4.6, Qdrant v1.12.5, Prometheus, Grafana, Docker Registry, Homelab Dashboard, Open WebUI
- OS: Ubuntu 24.04.3 LTS
- Tailscale IP: 100.81.76.55
- K3s configured with Tailscale IP in TLS SAN for remote kubectl access
- Database Services:
  - PostgreSQL: postgres.homelab.svc.cluster.local:5432 (User: homelab, DB: homelab, 10Gi storage)
  - Redis: redis.homelab.svc.cluster.local:6379 (ephemeral storage, AOF enabled)
  - Qdrant: qdrant.homelab.svc.cluster.local:6333 (HTTP), :6334 (gRPC), 20Gi storage
- GitOps: Flux CD for automated infrastructure deployment (planned)

### Networking

- **IMPORTANT**: Always use Tailscale IPs for inter-node communication
- Local Network: 192.168.8.0/24 (note: some docs reference 192.168.1.0/24, actual is 192.168.8.0/24)
- Tailscale Mesh: 100.64.0.0/10 for secure remote access
- Service Node (asuna): 100.81.76.55
- Compute Node (pesubuntu): 100.72.98.106
- Service Node routes: Subnet routing enabled for 192.168.86.0/24

## Common Commands

### LLM Infrastructure (Compute Node)

**IMPORTANT: Compute node needs setup first!**

```bash
# Step 1: Install ROCm (AMD GPU drivers)
# See infrastructure/compute-node/README.md for full instructions
wget https://repo.radeon.com/amdgpu-install/latest/ubuntu/jammy/amdgpu-install_6.4.60401-1_all.deb
sudo apt install ./amdgpu-install_6.4.60401-1_all.deb
sudo amdgpu-install --usecase=rocm
sudo usermod -a -G render,video $USER
# Log out and back in

# Step 2: Verify GPU detection
rocm-smi
rocminfo
lspci | grep -i vga

# Step 3: Install Ollama with ROCm support
curl -fsSL https://ollama.com/install.sh | sh
systemctl status ollama

# Step 4: Pull models
ollama pull mistral:7b-q4_K_M
ollama pull codellama:7b-q4_K_M
ollama pull llama3.1:8b-q4_K_M

# Step 5: Test Ollama inference (should use GPU)
ollama run mistral:7b-q4_K_M "Hello, who are you?"

# Step 6: Install and start LiteLLM
sudo apt install pipx
pipx install 'litellm[proxy]'
cd services/llm-router/config
litellm --config config.yaml --port 8000

# Step 7: Test LiteLLM endpoint
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3", "messages": [{"role": "user", "content": "Hello!"}]}'

# Step 8: Run health check
./infrastructure/compute-node/scripts/health-check.sh
```

### Service Node Operations

```bash
# SSH to service node
ssh pesu@192.168.8.185

# Check K3s cluster status
kubectl get nodes
kubectl get pods -A

# View N8n logs
kubectl logs -n homelab -l app=n8n -f

# Check service endpoints
kubectl get svc -n homelab

# Monitor resource usage
kubectl top nodes
kubectl top pods -A
```

### Monitoring & Observability

**Access Dashboards** (via Tailscale IPs):
- **Homelab Dashboard**: http://100.81.76.55:30800 (admin/admin123) - Unified landing page
- N8n Workflows: http://100.81.76.55:30678 (admin/admin123) | https://n8n.homelab.pesulabs.net
- Flowise LLM Flows: http://100.81.76.55:30850 (admin/admin123) | https://flowise.homelab.pesulabs.net
- Grafana: http://100.81.76.55:30300 (admin/admin123) | https://grafana.homelab.pesulabs.net
- Prometheus: http://100.81.76.55:30090 | https://prometheus.homelab.pesulabs.net
- Open WebUI: http://100.81.76.55:30080 (LLM chat interface) | https://webui.homelab.pesulabs.net
- Qdrant Vector DB: http://100.81.76.55:30633 (API access for testing)
- Ollama API: http://100.72.98.106:11434 (compute node)
- LiteLLM API: http://100.72.98.106:8000 (compute node)

**Grafana Dashboards** (docs/GRAFANA-DASHBOARDS.md):
- Homelab Overview: High-level cluster health and resource usage
- Kubernetes Cluster: Detailed K8s pod/node metrics
- Service Health: Individual service monitoring (N8n, PostgreSQL, Redis, etc.)
- Compute Node: LLM inference node with GPU metrics
- Database Performance: PostgreSQL and Redis monitoring (requires exporters)

### Qdrant Vector Database

```bash
# Deploy Qdrant
kubectl apply -f infrastructure/kubernetes/databases/qdrant/qdrant.yaml

# Verify deployment
kubectl get pods -n homelab -l app=qdrant
kubectl get svc -n homelab qdrant

# Test health check (via NodePort)
curl http://100.81.76.55:30633/healthz

# Create test collection
curl -X PUT http://100.81.76.55:30633/collections/test \
  -H 'Content-Type: application/json' \
  -d '{"vectors": {"size": 384, "distance": "Cosine"}}'

# List collections
curl http://100.81.76.55:30633/collections

# See docs/QDRANT-SETUP.md for N8n/Flowise integration
```

### GitOps with Flux CD (Planned)

```bash
# Install Flux CLI
curl -s https://fluxcd.io/install.sh | sudo bash

# Bootstrap Flux to K3s cluster
flux bootstrap github \
  --owner=pesuga \
  --repository=homelab \
  --branch=revised-version \
  --path=./clusters/homelab \
  --personal

# Verify Flux components
kubectl get pods -n flux-system
flux get all

# See docs/GITOPS-SETUP.md for complete setup
```

### Grafana Dashboard Management

```bash
# Access Grafana
# http://100.81.76.55:30300 (admin/admin123)

# Import recommended dashboards (via UI):
# - ID 1860: Node Exporter Full
# - ID 15760: Kubernetes Cluster Monitoring
# - ID 9628: PostgreSQL (requires postgres_exporter)
# - ID 11835: Redis (requires redis_exporter)

# Query Prometheus metrics
curl http://100.81.76.55:30090/api/v1/label/__name__/values

# See docs/GRAFANA-DASHBOARDS.md for dashboard creation guide
```

### Development Workflow

```bash
# Clone and setup (already done)
git clone https://github.com/pesuga/homelab.git
cd homelab
git checkout revised-version

# Copy environment template
cp .env-example .env
# Edit .env with your values

# Run setup script (minimal - needs expansion)
./scripts/setup.sh
```

## Key Architecture Patterns

### LLM Request Flow

```
User/N8n → LiteLLM (port 8000) → Ollama (port 11434) → LLM Model → GPU/CPU
          ↓
     OpenAI-compatible API
     (allows drop-in replacement)
```

**Why LiteLLM?**: Provides unified OpenAI-compatible interface, load balancing, fallback routing, and usage tracking across multiple LLM backends.

### Service Deployment Pattern

All services on the service node run as Kubernetes workloads:
- Base namespace: `homelab`
- Storage: Persistent Volume Claims (10Gi for PostgreSQL, 5Gi for N8n/Grafana)
- Networking: ClusterIP for internal, NodePort for external access
- No Ingress controller yet - direct NodePort access

### Data Persistence Strategy

- **PostgreSQL**: Used by N8n for workflow storage, uses PVC
- **Redis**: In-memory cache and job queue, uses PVC
- **LLM Models**: Stored in Ollama's model directory (managed by Ollama)
- **Grafana Dashboards**: Stored in PVC
- **Prometheus Metrics**: 10Gi retention with PVC

## Current Sprint Goals

### Sprint 3: LLM Infrastructure (Current - Week 7-8) - RESTARTED

**Major Change**: Moved from Windows + WSL2 to native Ubuntu 25.10 installation due to AMD GPU driver limitations in WSL2.

**Objectives**:
1. ✅ Install fresh Ubuntu 25.10 on compute node
2. ✅ Verify GPU detection (AMD RX 7800 XT)
3. ⏳ Install ROCm 6.4.1+ for AMD GPU support (NEXT)
4. ⏳ Deploy Ollama with GPU acceleration
5. ⏳ Load production models: Mistral 7B, CodeLlama 7B, Llama 3.1 8B
6. ⏳ Benchmark GPU-accelerated inference
7. ⏳ Install and configure LiteLLM router
8. ⏳ Set up Tailscale on compute node
9. ⏳ Integrate LLM endpoint with N8n workflows

**Success Criteria**:
- ✅ Native Ubuntu installation complete
- ✅ GPU detected via lspci
- ⏳ ROCm detects and uses RX 7800 XT
- ⏳ GPU-accelerated inference achieving 20+ tokens/second on 7B models
- ⏳ LiteLLM routing requests to appropriate models
- ⏳ N8n can call LLM via OpenAI API
- ⏳ Monitoring shows GPU utilization

**Benefits of Native Ubuntu**:
- Full ROCm support without WSL2 limitations
- Better GPU performance
- Native hardware access
- Simplified troubleshooting

## Important Files & Locations

### Documentation
- `README.md` - Main project overview and status
- `docs/architecture.md` - Detailed system architecture
- `docs/LLM-SETUP.md` - Complete AMD GPU LLM deployment guide
- `docs/SESSION-STATE.md` - Current session state and progress tracking
- `docs/IMPLEMENTATION-PLAN.md` - GitOps, Qdrant, and Grafana implementation plan
- `docs/GITOPS-SETUP.md` - Flux CD GitOps setup and multi-repo management
- `docs/QDRANT-SETUP.md` - Qdrant vector database deployment and integration
- `docs/GRAFANA-DASHBOARDS.md` - Grafana dashboard creation and setup guide
- `docs/METRICS-ANALYSIS.md` - Prometheus metrics analysis and available data

### Configuration
- `.env-example` - Environment variable template (comprehensive)
- `services/llm-router/config/config.yaml` - LiteLLM model routing configuration
- `infrastructure/kubernetes/base/namespace.yaml` - K8s namespace definition

### Scripts
- `infrastructure/compute-node/scripts/health-check.sh` - LLM services health check
- `scripts/setup.sh` - Basic setup script (needs expansion)

### Service Configurations
- `infrastructure/compute-node/` - Ollama and LiteLLM setup docs
- `infrastructure/kubernetes/` - K8s manifests
  - `base/` - Namespace and core configs
  - `databases/` - PostgreSQL, Redis, Qdrant deployments
  - `monitoring/` - Prometheus, Grafana
  - `monitoring/dashboards/` - Grafana dashboard JSONs and provisioning
  - `flux/` - Flux CD GitOps resources (planned)
- `services/llm-router/` - LiteLLM configuration
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

**LiteLLM** (API Gateway):
- Unified interface across model providers
- Built-in load balancing and fallback
- OpenAI-compatible endpoints

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

**Prometheus + Grafana** (Observability):
- Prometheus: Metrics collection and storage
- Grafana: Visualization and dashboards
- Pre-configured dashboards for cluster, services, and GPU

## Testing

Currently no automated test suite. Health checks available:

```bash
# LLM services health check
./infrastructure/compute-node/scripts/health-check.sh

# Kubernetes cluster health
kubectl get nodes
kubectl get pods -A
kubectl get svc -A

# Service connectivity
curl http://192.168.8.185:30678  # N8n
curl http://192.168.8.185:30300  # Grafana
curl http://192.168.8.185:30090  # Prometheus
curl http://192.168.8.185:30633/healthz  # Qdrant

# GitOps (when deployed)
flux check
flux get all
```

## Deployment Notes

### Service Node Deployment (Completed)
All services deployed via `kubectl apply` to K3s cluster. No GitOps or Helm charts yet.

Current deployments in `homelab` namespace:
- PostgreSQL (postgres:16-alpine)
- Redis (redis:7-alpine)
- N8n (n8nio/n8n)
- Prometheus (prom/prometheus)
- Grafana (grafana/grafana)

### Compute Node Deployment (In Progress)
Currently manual installation:
1. Ollama installed via official installer
2. LiteLLM installed via pipx
3. Services started manually (systemd service files exist but not active)

**Future**: Systemd services for auto-start, monitoring integration

## Troubleshooting

### LLM Inference Issues
```bash
# Check if Ollama is running
systemctl status ollama

# Restart Ollama
systemctl restart ollama

# Check GPU detection (when ROCm installed)
rocm-smi
rocminfo

# View Ollama logs
journalctl -u ollama -f
```

### Service Node Issues
```bash
# SSH to service node
ssh pesu@192.168.8.185

# Check K3s
systemctl status k3s

# View pod logs
kubectl logs -n homelab POD_NAME

# Restart a deployment
kubectl rollout restart deployment/n8n -n homelab
```

### Network Connectivity
```bash
# Check Tailscale status
tailscale status

# Test local network
ping 192.168.8.185

# Test from service node to compute node (LLM endpoint)
curl http://COMPUTE_NODE_IP:11434/api/version
```

## Future Enhancements

### Sprint 4: Advanced Services (Weeks 9-10)
- AgentStack deployment for advanced agent orchestration
- Service mesh (Istio/Linkerd) for better observability
- Log aggregation with Loki
- Alert rules and runbooks

### Sprint 5: Networking & Security (Weeks 11-12)
- Tailscale exit node on GL-MT2500 router
- Enhanced authentication (OAuth/OIDC)
- Mobile access optimization
- TLS/HTTPS everywhere

### Sprint 6: Agent Workflows (Weeks 13-14)
- First production N8n workflows with LLM integration
- AgentStack agent development
- Agent templates and pattern library

### Sprint 7: CI/CD & Automation (Weeks 15-16)
- GitHub Actions for automated testing and deployment
- Backup automation (local + Google Drive)
- Disaster recovery procedures

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

### Expected Performance (Post-Setup)
- GPU-accelerated inference: 20-30 tokens/second on 7B models (target)
- VRAM usage: ~6-7GB for Q4 quantized 7B models
- CPU fallback if needed: ~2-5 tokens/second
- Current state: No LLM services installed yet

## Session Continuity

When resuming work, check:
1. `docs/SESSION-STATE.md` for current task and progress
2. `README.md` roadmap section for sprint status
3. Git branch (should be `revised-version`)
4. Service health: N8n, Grafana, Prometheus accessible
5. LLM health: `./infrastructure/compute-node/scripts/health-check.sh`

## Important Notes

- **IP Addressing**: Documentation sometimes references 192.168.1.0/24, but actual network is 192.168.8.0/24
- **OS Change**: Moved from Windows + WSL2 to native Ubuntu 25.10 for better GPU support
- **Compute Node**: Fresh installation, needs ROCm + Ollama + LiteLLM setup
- **Credentials**: Default admin/admin123 for N8n and Grafana (change in production)
- **Storage**: Service node has limited disk (98GB) - monitor usage
- **No root access needed**: Both nodes have passwordless sudo configured for user `pesu`

## Git Workflow

- Main development branch: `revised-version`
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
