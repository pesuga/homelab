# 🧠 LLM Infrastructure Setup - AMD RX 7800 XT

> **Purpose**: Deploy local LLM inference on compute node with AMD RX 7800 XT GPU using ROCm

**Last Updated**: 2025-10-22
**Status**: Fresh Ubuntu Installation - Ready for ROCm Setup

---

## 📊 Hardware Specifications

**Compute Node (pesubuntu):**
- **GPU**: AMD Radeon RX 7800 XT (16GB VRAM, Navi 32, gfx1101)
- **CPU**: Intel i5-12400F (6 cores, 12 threads)
- **RAM**: 32GB DDR4 (30Gi available)
- **Storage**: 937GB NVMe SSD available
- **OS**: Ubuntu 25.10 (Questing Quetzal) - Native installation
- **Kernel**: 6.17.0-5-generic

**ROCm Compatibility:**
- ✅ RX 7800 XT officially supported in ROCm 6.4.1+
- ✅ ROCm 7.0 support available
- ✅ gfx1101 architecture fully supported
- ✅ Native Ubuntu installation (no WSL2 limitations)

---

## 🎯 Deployment Strategy

### Phase 1: Foundation 🔄 IN PROGRESS
**Goal**: Get ROCm and Ollama working with basic model

**Steps:**
1. ✅ Install fresh Ubuntu 25.10 on compute node
2. ✅ Verify GPU detection via lspci
3. ⏳ Install ROCm 6.4.1 or 7.0 (Ubuntu 25.10 compatible)
4. ⏳ Verify GPU detection with rocm-smi and rocminfo
5. ⏳ Install Ollama with ROCm support
6. ⏳ Test with Mistral 7B Q4_K_M
7. ⏳ Verify performance benchmarks

**Success Criteria:**
- ✅ Native Ubuntu installation complete
- ✅ GPU detected via lspci
- ⏳ ROCm detects RX 7800 XT
- ⏳ Ollama runs inference on GPU
- ⏳ Achieve 20+ tokens/second on 7B model

---

### Phase 2: Production Stack
**Goal**: Deploy LiteLLM router and multiple models

**Steps:**
1. Deploy LiteLLM as API gateway
2. Configure OpenAI-compatible endpoints
3. Load production models:
   - Mistral 7B Q4_K_M (general purpose)
   - CodeLlama 7B Q4_K_M (coding)
   - Llama 3.1 8B Q4_K_M (chat/reasoning)
4. Set up model routing rules
5. Configure health checks and monitoring
6. Integrate with N8n on service node

**Success Criteria:**
- LiteLLM routes requests to appropriate models
- N8n can call LLM via OpenAI API
- Models load and unload efficiently
- Monitoring shows GPU utilization

---

### Phase 3: Advanced Features
**Goal**: Optimize and expand capabilities

**Steps:**
1. Fine-tune model selection based on usage
2. Consider vLLM for high-throughput scenarios
3. Set up model caching strategies
4. Implement automatic model updates
5. Create custom model fine-tuning pipeline
6. Document common workflows and patterns

---

## 🛠️ Software Stack

### Primary Components

#### 1. ROCm (AMD GPU Runtime)
- **Version**: 6.4.1 or 7.0+
- **Purpose**: GPU acceleration for AMD cards
- **Installation**: Official AMD repository
- **Config**: May need `HSA_OVERRIDE_GFX_VERSION=11.0.0`

#### 2. Ollama ⭐ RECOMMENDED
- **Version**: Latest with ROCm support
- **Purpose**: Primary LLM inference engine
- **Features**:
  - Automatic model management
  - OpenAI-compatible API
  - Simple CLI and API
  - Built-in quantization support
- **Installation**: Official binary with ROCm

#### 3. LiteLLM
- **Version**: Latest
- **Purpose**: API gateway and router
- **Features**:
  - Unified API interface
  - Load balancing
  - Fallback routing
  - Usage tracking
- **Deployment**: Docker or direct install

---

## 🤖 Recommended Models

### Tier 1: Primary Models (Start Here) ⭐

#### Mistral 7B Q4_K_M
- **Size**: ~6.5GB VRAM
- **Speed**: 25-30 tok/s
- **Use**: General purpose, instruction following
- **Ollama**: `ollama pull mistral:7b-q4_K_M`

#### CodeLlama 7B Q4_K_M
- **Size**: ~6.5GB VRAM
- **Speed**: 25-30 tok/s
- **Use**: Code generation, debugging
- **Ollama**: `ollama pull codellama:7b-q4_K_M`

#### Llama 3.1 8B Q4_K_M
- **Size**: ~7.2GB VRAM
- **Speed**: 25-30 tok/s
- **Use**: Chat, reasoning, analysis
- **Ollama**: `ollama pull llama3.1:8b-q4_K_M`

---

### Tier 2: Advanced Models (Optional)

#### Llama 2 13B Q4_K_M
- **Size**: ~9GB VRAM
- **Speed**: 20-25 tok/s
- **Use**: More capable reasoning
- **Ollama**: `ollama pull llama2:13b-q4_K_M`

#### Mixtral 8x7B Q3_K_M
- **Size**: ~14GB VRAM
- **Speed**: 12-18 tok/s
- **Use**: Expert mixture model
- **Ollama**: `ollama pull mixtral:8x7b-q3_K_M`

---

## 📋 Installation Checklist

### Prerequisites
- [x] Ubuntu 25.10 native installation complete
- [x] GPU detected via lspci (AMD RX 7800 XT Navi 32)
- [x] 32GB RAM available (30Gi free)
- [x] 937GB free disk space
- [x] Git configured and repository cloned
- [x] GitHub SSH credentials configured
- [ ] Network configured for internet access
- [ ] Tailscale installed (for remote access)

### ROCm Installation (Ubuntu 25.10)
- [ ] Add AMD ROCm repository (may need Ubuntu 24.04 repo)
- [ ] Install ROCm 6.4.1 or 7.0
- [ ] Verify GPU detection: `rocm-smi`
- [ ] Set environment variables if needed (HSA_OVERRIDE_GFX_VERSION)
- [ ] Test with `rocminfo`
- [ ] Verify /dev/dri/renderD128 exists

### Ollama Installation
- [ ] Download Ollama with ROCm support
- [ ] Install Ollama binary
- [ ] Start Ollama service
- [ ] Verify GPU acceleration
- [ ] Pull test model (Mistral 7B)
- [ ] Run inference test
- [ ] Benchmark performance

### LiteLLM Setup
- [ ] Install LiteLLM
- [ ] Create configuration file
- [ ] Set up model routing
- [ ] Configure API endpoints
- [ ] Test OpenAI compatibility
- [ ] Document API endpoints

### Integration
- [ ] Configure firewall rules
- [ ] Set up reverse proxy (if needed)
- [ ] Test from service node
- [ ] Integrate with N8n
- [ ] Create sample workflows
- [ ] Document usage patterns

---

## ⚙️ Configuration

### ROCm Environment Variables (Native Ubuntu)
```bash
# Add to ~/.bashrc or /etc/environment
export HSA_OVERRIDE_GFX_VERSION=11.0.0  # May be needed for RX 7800 XT (gfx1101)
export ROCM_PATH=/opt/rocm
export PATH=$PATH:/opt/rocm/bin
export LD_LIBRARY_PATH=/opt/rocm/lib:$LD_LIBRARY_PATH
```

### Ollama Service
```bash
# Start Ollama
ollama serve

# API endpoint
http://localhost:11434

# Pull models
ollama pull mistral:7b-q4_K_M
ollama pull codellama:7b-q4_K_M
ollama pull llama3.1:8b-q4_K_M

# Test inference
ollama run mistral:7b-q4_K_M "Hello, who are you?"
```

### LiteLLM Configuration
```yaml
# litellm-config.yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: ollama/mistral:7b-q4_K_M
      api_base: http://localhost:11434

  - model_name: gpt-4
    litellm_params:
      model: ollama/llama3.1:8b-q4_K_M
      api_base: http://localhost:11434

  - model_name: code
    litellm_params:
      model: ollama/codellama:7b-q4_K_M
      api_base: http://localhost:11434
```

---

## 🔍 Troubleshooting

### GPU Not Detected
```bash
# Check ROCm installation
rocm-smi
rocminfo

# Verify GPU
lspci | grep -i vga

# Check environment
echo $HSA_OVERRIDE_GFX_VERSION
```

### Poor Performance
- Check GPU utilization: `rocm-smi`
- Verify model quantization level
- Try different quantization (Q4 vs Q5)
- Monitor VRAM usage
- Check CPU isn't bottlenecking

### Model Loading Issues
- Ensure sufficient VRAM
- Check disk space for model files
- Verify model format compatibility
- Try re-pulling model

---

## 📈 Performance Targets

### Expected Performance (RX 7800 XT)

| Model Size | Quantization | VRAM | Speed (tok/s) |
|-----------|--------------|------|---------------|
| 7B | Q4_K_M | ~6.5GB | 25-30 |
| 7B | Q5_K_M | ~7.5GB | 22-28 |
| 8B | Q4_K_M | ~7.2GB | 25-30 |
| 13B | Q4_K_M | ~9GB | 20-25 |
| 34B | Q4_K_M | ~15GB | 10-15 |

### Success Metrics
- **Latency**: < 2s for first token
- **Throughput**: > 20 tokens/second
- **GPU Utilization**: 60-80%
- **Availability**: > 99%
- **Model Loading**: < 10s

---

## 🔗 Integration Points

### N8n Workflows
- **Endpoint**: http://compute-node:11434 (via Ollama)
- **Endpoint**: http://compute-node:8000 (via LiteLLM)
- **API Type**: OpenAI-compatible
- **Auth**: Optional API key

### AgentStack
- **Integration**: Via LiteLLM proxy
- **Models**: All available models
- **Routing**: Automatic based on task

### Monitoring
- **Prometheus**: GPU metrics via ROCm exporter
- **Grafana**: Custom LLM dashboard
- **Metrics**: Tokens/s, VRAM usage, request latency

---

## 📚 Resources

### Official Documentation
- [AMD ROCm Documentation](https://rocm.docs.amd.com/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [LiteLLM Documentation](https://docs.litellm.ai/)

### Community Resources
- [ROCm GitHub Discussions](https://github.com/ROCm/ROCm/discussions)
- [Ollama Discord](https://discord.gg/ollama)
- [r/LocalLLaMA](https://reddit.com/r/LocalLLaMA)

### Model Resources
- [Ollama Model Library](https://ollama.com/library)
- [Hugging Face Models](https://huggingface.co/models)
- [GGUF Models](https://huggingface.co/models?library=gguf)

---

## 🎯 Next Steps

1. ✅ Create this documentation
2. ✅ Install fresh Ubuntu 25.10 on compute node
3. ✅ Verify GPU detection via lspci
4. ✅ Configure Git and clone repository
5. ⏳ Install ROCm 6.4.1+ on Ubuntu 25.10 (NEXT)
6. ⏳ Verify GPU with rocm-smi and rocminfo
7. ⏳ Install and test Ollama with ROCm
8. ⏳ Deploy first model (Mistral 7B)
9. ⏳ Benchmark performance (target 20+ tok/s)
10. ⏳ Set up LiteLLM router
11. ⏳ Install Tailscale for remote access
12. ⏳ Integrate with N8n on service node
13. ⏳ Create sample workflows

---

**Status**: Fresh Ubuntu 25.10 installation, GPU detected, ready for ROCm
**Next Action**: Install ROCm 6.4.1+ for Ubuntu (may need 24.04 repository)
