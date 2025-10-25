# 🔄 Homelab Session State - 2025-10-25

## 📍 Current Status

**Last Updated**: 2025-10-25
**Current Phase**: Sprint 4 - Advanced Services - IN PROGRESS (75% Complete)
**Active Task**: GitOps, Qdrant, and Grafana Dashboards implementation complete

---

## ✅ Completed Work

### Infrastructure Deployed (Service Node - asuna)
- ✅ **Server**: Ubuntu 24.04.3 LTS (192.168.8.185, Tailscale: 100.81.76.55)
- ✅ **Docker**: v28.5.1 installed and running
- ✅ **K3s**: v1.33.5 cluster operational
  - ✅ **TLS SAN**: Added Tailscale IP (100.81.76.55) to certificate
  - ✅ **Registry Config**: Configured for insecure registry at 100.81.76.55:30500
- ✅ **Tailscale**: Connected (100.81.76.55) with subnet routing
- ✅ **Docker Registry**: Deployed at http://100.81.76.55:30500 (20Gi storage)
- ✅ **PostgreSQL**: Deployed (postgres:16.10-alpine, 10Gi storage, ClusterIP, User: homelab/DB: homelab)
  - ✅ Deployment manifest created and documented
  - ✅ Connection string: postgres.homelab.svc.cluster.local:5432
- ✅ **Redis**: Deployed (redis:7.4.6-alpine, ephemeral storage, ClusterIP)
  - ✅ Deployment manifest created and documented
  - ✅ Connection string: redis.homelab.svc.cluster.local:6379
- ✅ **N8n**: Deployed at http://100.81.76.55:30678 (admin/admin123)
- ✅ **Prometheus**: Deployed at http://100.81.76.55:30090
- ✅ **Grafana**: Deployed at http://100.81.76.55:30300 (admin/admin123)
- ✅ **Open WebUI**: Deployed at http://100.81.76.55:30080
- ✅ **Homelab Dashboard**: Deployed at http://100.81.76.55:30800 (admin/admin123)
  - ✅ PostgreSQL and Redis added to dashboard
  - ✅ Flowise added to dashboard
- ✅ **Flowise**: Deployed at http://100.81.76.55:30850 (admin/admin123)
  - ✅ Low-code LLM flow builder and AI orchestration platform
  - ✅ PostgreSQL integration for data persistence
  - ✅ Ingress: https://flowise.homelab.pesulabs.net
  - ✅ Connected to compute node LLMs via Ollama
- ✅ **Qdrant Vector Database**: Deployed at http://100.81.76.55:30633
  - ✅ v1.12.5 running with 20Gi persistent storage
  - ✅ HTTP API (6333) and gRPC API (6334) operational
  - ✅ Health checks passing
  - ✅ Ready for RAG and semantic search workflows
  - ✅ Integration documented for N8n and Flowise

### Compute Node Setup (pesubuntu - 100.72.98.106)
- ✅ **Fresh Ubuntu 25.10 Installation** (native, not WSL2)
- ✅ **GPU Detection**: AMD Radeon RX 7800 XT properly detected
- ✅ **ROCm 6.4.1**: Installed and GPU fully functional
- ✅ **Ollama 0.12.6**: Installed with GPU acceleration
- ✅ **Models Installed**:
  - qwen2.5-coder:14b (9.0GB) - Code generation
  - llama3.1:8b (4.9GB) - General purpose
  - mistral:7b-instruct-q4_K_M (4.4GB) - Fast inference
- ✅ **LiteLLM 1.78.6**: OpenAI-compatible API running on port 8000
  - ✅ API key authentication configured
  - ✅ Master key: sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0
  - ✅ Ready for N8n integration
- ✅ **Systemd Services**: Ollama and LiteLLM auto-start on boot
- ✅ **Tailscale**: Connected (100.72.98.106)
- ✅ **Docker 28.5.1**: Configured with insecure registry for Tailscale IP
- ✅ **kubectl**: Configured to access K3s via Tailscale IP
- ✅ **GitHub Credentials**: Configured (SSH key added)
- ✅ **Repository**: Cloned and on revised-version branch

### Documentation Created
- ✅ README.md updated with current progress (50% complete, Sprint 3 & 4)
- ✅ LLM-SETUP.md created with full AMD GPU deployment plan
- ✅ Architecture and roadmap documented
- ✅ CLAUDE.md created and updated with new services
- ✅ **IMPLEMENTATION-PLAN.md** - GitOps, Qdrant, Grafana roadmap ✅ NEW
- ✅ **GITOPS-SETUP.md** - Complete Flux CD setup guide ✅ NEW
- ✅ **QDRANT-SETUP.md** - Vector database deployment and integration ✅ NEW
- ✅ **GRAFANA-DASHBOARDS.md** - Dashboard creation guide ✅ NEW
- ✅ **QUICKSTART-DASHBOARDS.md** - Quick dashboard setup ✅ NEW
- ✅ **METRICS-ANALYSIS.md** - Prometheus metrics catalog ✅ NEW

---

## 🎯 Current Task: ROCm and Ollama Installation

### Compute Node Specs ✅ VERIFIED
- **Hardware**: Intel i5-12400F (6C/12T), 32GB RAM, 937GB free disk
- **GPU**: AMD Radeon RX 7800 XT (Navi 32, detected via lspci)
- **OS**: Ubuntu 25.10 (Questing Quetzal) - Native installation
- **Kernel**: 6.17.0-5-generic
- **Network**: Connected (ready for Tailscale)

### Major Change: WSL2 → Native Ubuntu
**Previous Setup**: Windows 11 + WSL2 Ubuntu 24.04
**Issue**: AMD GPU driver passthrough limitations in WSL2
**Solution**: Fresh native Ubuntu 25.10 installation
**Benefit**: Full ROCm support, native GPU access, better performance

### Next Steps
1. ⏳ Install AMD ROCm 6.4.1+ (Ubuntu 25.10 compatible)
2. ⏳ Verify GPU detection with rocm-smi
3. ⏳ Install Docker (for optional containerized workflows)
4. ⏳ Install Ollama with ROCm support
5. ⏳ Pull and test models (Mistral 7B, CodeLlama 7B, Llama 3.1 8B)
6. ⏳ Install and configure LiteLLM
7. ⏳ Set up Tailscale for remote access
8. ⏳ Integrate with N8n on service node

---

## 📋 Completed Sprint 3: LLM Infrastructure

### Sprint 3 Tasks - ✅ ALL COMPLETE
1. ✅ Create LLM setup documentation
2. ✅ Install fresh Ubuntu 25.10 on compute node
3. ✅ Verify GPU detection (AMD RX 7800 XT detected)
4. ✅ Configure GitHub credentials and clone repository
5. ✅ Install AMD ROCm 6.4.1+ for Ubuntu 25.10
6. ✅ Verify GPU with rocm-smi and rocminfo
7. ✅ Install Ollama 0.12.6 with ROCm support
8. ✅ Pull and test Mistral 7B Q4_K_M model
9. ✅ Benchmark inference performance (achieved: ~75 tok/s)
10. ✅ Install and configure LiteLLM 1.78.6
11. ✅ Create systemd services for auto-start
12. ✅ Set up Tailscale on compute node
13. ⏳ Integrate LLM endpoint with N8n (NEXT SPRINT)
14. ⏳ Create sample N8n workflow with LLM (NEXT SPRINT)

### Sprint 4: Advanced Services - IN PROGRESS (75% Complete)
- [x] PostgreSQL deployment and documentation (postgres:16.10, 10Gi storage)
- [x] Redis deployment and documentation (redis:7.4.6, ephemeral storage)
- [x] Database services added to homelab dashboard
- [x] Database deployment manifests created (infrastructure/kubernetes/databases/)
- [x] LiteLLM API key authentication configured
- [x] N8n integration guide created (docs/N8N-LITELLM-INTEGRATION.md)
- [x] N8n domain configuration (https://n8n.homelab.pesulabs.net for OAuth)
- [x] Flowise deployment and integration (low-code LLM flow builder)
- [x] Flowise ingress and TLS configuration (https://flowise.homelab.pesulabs.net)
- [x] **Qdrant vector database** - Deployed and tested ✅ NEW
  - [x] Kubernetes manifests created (infrastructure/kubernetes/databases/qdrant/)
  - [x] Deployed to K3s (v1.12.5, 20Gi storage, HTTP + gRPC APIs)
  - [x] Health checks passing
  - [x] API tested and verified
  - [x] Integration documentation created (docs/QDRANT-SETUP.md)
- [x] **GitOps with Flux CD** - Planned and documented ✅ NEW
  - [x] Architecture designed for multi-repository support
  - [x] Repository structure planned
  - [x] Complete setup guide created (docs/GITOPS-SETUP.md)
  - [x] Implementation plan documented (docs/IMPLEMENTATION-PLAN.md)
  - [ ] Bootstrap Flux to K3s cluster (next)
  - [ ] Migrate existing manifests to Flux management
- [x] **Grafana Dashboards** - Planned and documented ✅ NEW
  - [x] Prometheus metrics analyzed (docs/METRICS-ANALYSIS.md)
  - [x] 5 dashboards designed (Overview, K8s, Services, Compute, Databases)
  - [x] Dashboard creation guide created (docs/GRAFANA-DASHBOARDS.md)
  - [x] Quick start guide created (docs/QUICKSTART-DASHBOARDS.md)
  - [ ] Import community dashboards (IDs: 1860, 15760, 3662)
  - [ ] Create custom "Homelab Overview" dashboard
  - [ ] Deploy postgres_exporter for database metrics
  - [ ] Deploy redis_exporter for Redis metrics
- [ ] Add LiteLLM credentials to N8n (manual step)
- [ ] Create first N8n workflow using local LLM
- [ ] Create sample Flowise workflows with local LLMs
- [ ] AgentStack deployment (optional)

---

## 🔗 Important Endpoints

### Service Node (asuna)
- **Local IP**: 192.168.8.185
- **Tailscale IP**: 100.81.76.55
- **N8n**: http://192.168.8.185:30678 (admin/admin123) | https://n8n.homelab.pesulabs.net
- **Flowise**: http://192.168.8.185:30850 (admin/admin123) | https://flowise.homelab.pesulabs.net
- **Grafana**: http://192.168.8.185:30300 (admin/admin123) | https://grafana.homelab.pesulabs.net
- **Prometheus**: http://192.168.8.185:30090 | https://prometheus.homelab.pesulabs.net
- **Qdrant**: http://192.168.8.185:30633 (vector database API) ✅ NEW
- **Homelab Dashboard**: http://192.168.8.185:30800 (admin/admin123) | https://homelab.pesulabs.net
- **SSH**: ssh pesu@192.168.8.185 (passwordless sudo configured)

### Compute Node (pesubuntu)
- **OS**: Ubuntu 25.10 (Native installation)
- **Hostname**: pesubuntu
- **Local IP**: TBD (to be configured)
- **Tailscale IP**: 100.72.98.106
- **Working Directory**: /home/pesu/Rakuflow/systems/homelab
- **Access**: Direct (local machine) or Tailscale
- **LLM API Endpoints**:
  - Ollama: http://localhost:11434 or http://100.72.98.106:11434
  - LiteLLM: http://localhost:8000 or http://100.72.98.106:8000

---

## 📝 Next Steps

1. **Install ROCm** ⏳ READY:
   ```bash
   # Add ROCm repository for Ubuntu
   # Install ROCm 6.4.1+ (compatible with Ubuntu 25.10)
   # Note: May need Ubuntu 24.04 repository or build from source
   ```
   GPU is already detected: AMD Radeon RX 7800 XT (Navi 32)

2. **Verify ROCm Installation**:
   ```bash
   rocm-smi
   rocminfo
   ```
   Expected: Should show RX 7800 XT with full details

3. **Install Dependencies**:
   - Docker (for containerized workflows)
   - Python 3.11+ (for LiteLLM)
   - Git (already installed)
   - Tailscale (for remote access)

4. **Deploy LLM Stack**:
   - Install Ollama with ROCm support
   - Configure systemd service
   - Pull initial models
   - Install LiteLLM
   - Test inference and benchmarks

---

## 🎯 Project Goals

### Sprint 3 Goal (Current)
Deploy local LLM inference on compute node with:
- Ollama + ROCm for AMD GPU acceleration
- LiteLLM as API gateway
- 3 models: Mistral 7B, CodeLlama 7B, Llama 3.1 8B
- Integration with N8n workflows

### Success Metrics
- ✅ GPU detected in native Ubuntu (AMD RX 7800 XT)
- ⏳ ROCm functional with RX 7800 XT
- ⏳ Ollama achieves 20+ tokens/second on 7B models
- ⏳ N8n can call LLM via OpenAI-compatible API

---

## 📚 Key Documentation Files

- `/README.md` - Main project overview
- `/docs/LLM-SETUP.md` - Complete AMD GPU LLM setup guide
- `/docs/SESSION-STATE.md` - This file (current session state)
- `/docs/architecture.md` - System architecture

---

## 🚀 Resume Command

When resuming after restart, run:
```bash
cd /home/pesu/Rakuflow/systems/homelab
claude
```

Then say: **"Let's continue the LLM setup"**

---

**Status**: Fresh Ubuntu 25.10 installation, GPU detected, ready for ROCm installation
**Branch**: revised-version
**Last Commit**: Add revised homelab infrastructure setup
