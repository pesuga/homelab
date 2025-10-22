# 🔄 Homelab Session State - 2025-10-17

## 📍 Current Status

**Last Updated**: 2025-10-17
**Current Phase**: LLM Infrastructure Setup (Sprint 3)
**Active Task**: Configuring WSL2 GPU Passthrough for AMD RX 7800 XT

---

## ✅ Completed Work

### Infrastructure Deployed (Service Node - asuna)
- ✅ **Server**: Ubuntu 24.04.3 LTS (192.168.8.185)
- ✅ **Docker**: v28.5.1 installed and running
- ✅ **K3s**: v1.33.5 cluster operational
- ✅ **Tailscale**: Connected (100.81.76.55) with subnet routing
- ✅ **PostgreSQL**: Deployed (postgres:16-alpine, 10Gi storage)
- ✅ **Redis**: Deployed (redis:7-alpine)
- ✅ **N8n**: Deployed and accessible at http://192.168.8.185:30678 (admin/admin123)
- ✅ **Prometheus**: Deployed at http://192.168.8.185:30090
- ✅ **Grafana**: Deployed at http://192.168.8.185:30300 (admin/admin123)

### Documentation Created
- ✅ README.md updated with current progress (45% complete)
- ✅ LLM-SETUP.md created with full AMD GPU deployment plan
- ✅ Architecture and roadmap documented

---

## 🎯 Current Task: ROCm and Ollama Installation

### Compute Node Specs
- **Hardware**: Intel i5-12400F, 32GB RAM, 938GB free disk
- **GPU**: AMD Radeon RX 7800 XT (16GB VRAM)
- **OS**: Windows 11 with WSL2 (Ubuntu 24.04.3 LTS)
- **WSL Kernel**: 6.6.87.2-microsoft-standard-WSL2

### WSL2 Configuration ✅ COMPLETED
- ✅ Memory: 24GB allocated
- ✅ Processors: 6 cores allocated
- ✅ Swap: 6GB configured and active
- ✅ WSL2 restarted successfully

### Next Steps
1. ⏳ Verify GPU passthrough in WSL2
2. ⏳ Install ROCm 6.4.1 or 7.0
3. ⏳ Configure AMD GPU environment
4. ⏳ Install Ollama with ROCm support
5. ⏳ Test with Mistral 7B model

---

## 📋 Active Todo List

### Current Sprint: LLM Infrastructure
1. ✅ Create LLM setup documentation
2. ✅ Configure WSL2 resources (24GB RAM, 6 cores, 6GB swap)
3. 🔄 Verify GPU passthrough in WSL2 (NEXT)
4. ⏳ Install ROCm 6.4.1+ on compute node
5. ⏳ Configure AMD GPU environment variables
6. ⏳ Install Ollama with ROCm support
7. ⏳ Pull and test Mistral 7B Q4_K_M model
8. ⏳ Benchmark inference performance
9. ⏳ Install and configure LiteLLM
10. ⏳ Integrate LLM endpoint with N8n
11. ⏳ Create sample N8n workflow with LLM

---

## 🔗 Important Endpoints

### Service Node (asuna)
- **Local IP**: 192.168.8.185
- **Tailscale IP**: 100.81.76.55
- **N8n**: http://192.168.8.185:30678 (admin/admin123)
- **Grafana**: http://192.168.8.185:30300 (admin/admin123)
- **Prometheus**: http://192.168.8.185:30090
- **SSH**: ssh pesu@192.168.8.185 (passwordless sudo configured)

### Compute Node (this machine)
- **OS**: WSL2 Ubuntu 24.04.3 LTS
- **Working Directory**: /mnt/c/Users/gigle/Rakuflow/systems/homelab
- **WSL Access**: Direct (no SSH needed)

---

## 📝 Next Steps

1. **Verify GPU Passthrough** ⏳ READY:
   ```bash
   ls -la /dev/dri/
   lspci | grep -i vga
   ```
   Expected: Should see AMD RX 7800 XT and /dev/dri/renderD128

2. **If GPU Detected**:
   - Install ROCm 6.4.1 or 7.0
   - Configure environment variables (HSA_OVERRIDE_GFX_VERSION=11.0.0)
   - Install Ollama with ROCm support
   - Test with Mistral 7B Q4_K_M

3. **If GPU NOT Detected**:
   - Check Windows GPU drivers installed
   - Verify GPU-Z shows RX 7800 XT on Windows
   - Update AMD Adrenalin drivers
   - May need additional WSL GPU support configuration

---

## 🎯 Project Goals

### Sprint 3 Goal (Current)
Deploy local LLM inference on compute node with:
- Ollama + ROCm for AMD GPU acceleration
- LiteLLM as API gateway
- 3 models: Mistral 7B, CodeLlama 7B, Llama 3.1 8B
- Integration with N8n workflows

### Success Metrics
- GPU detected in WSL2
- ROCm functional with RX 7800 XT
- Ollama achieves 20+ tokens/second on 7B models
- N8n can call LLM via OpenAI-compatible API

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
cd /mnt/c/Users/gigle/Rakuflow/systems/homelab
claude
```

Then say: **"Let's continue the LLM setup, I've restarted the PC"**

---

**Status**: WSL2 configured, ready to verify GPU passthrough and install ROCm
**Branch**: revised-version
**Last Commit**: Add revised homelab infrastructure setup
