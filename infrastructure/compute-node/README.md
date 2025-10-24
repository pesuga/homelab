# Compute Node Setup

LLM inference infrastructure running on the compute node (Native Ubuntu 25.10).

## Architecture

```
Compute Node (pesubuntu)
├── ROCm 6.4.1+ (AMD GPU Runtime)
│   └── AMD RX 7800 XT (16GB VRAM)
├── Ollama (Port 11434)
│   └── GPU-accelerated LLM inference
└── LiteLLM Router (Port 8000)
    └── OpenAI-compatible API
```

## System Specifications

### Hardware
- **Hostname**: pesubuntu
- **CPU**: Intel i5-12400F (6 cores, 12 threads)
- **RAM**: 32GB DDR4 (30Gi available)
- **GPU**: AMD Radeon RX 7800 XT (Navi 32, 16GB VRAM, gfx1101)
- **Storage**: 937GB NVMe SSD available
- **OS**: Ubuntu 25.10 (Questing Quetzal)
- **Kernel**: 6.17.0-5-generic

### Planned Services

#### ROCm (AMD GPU Runtime)
- **Version**: 6.4.1+ (to be installed)
- **Purpose**: GPU acceleration for AMD hardware
- **Status**: Not yet installed

#### Ollama (LLM Server)
- **Version**: Latest with ROCm support (to be installed)
- **Purpose**: Local LLM model hosting and inference
- **Port**: 11434
- **Compute**: GPU-accelerated (AMD RX 7800 XT)
- **Service**: systemd (ollama.service)
- **API**: http://localhost:11434
- **Status**: Not yet installed

#### LiteLLM (API Router)
- **Version**: Latest (to be installed)
- **Purpose**: OpenAI-compatible proxy and router
- **Port**: 8000
- **Config**: services/llm-router/config/config.yaml
- **API**: http://localhost:8000
- **Endpoints**:
  - Health: GET /health
  - Chat: POST /v1/chat/completions
  - Models: GET /v1/models
- **Status**: Not yet installed

## Directory Structure

```
infrastructure/compute-node/
├── README.md              # This file
├── ollama/                # Ollama configuration
│   └── litellm.service    # Systemd service file
├── litellm/              # LiteLLM configuration
│   └── litellm.service   # Systemd service file
└── scripts/              # Utility scripts
    └── health-check.sh   # Health monitoring script
```

## Installation Guide

### 1. Install ROCm (AMD GPU Support)
```bash
# Add ROCm repository (for Ubuntu 24.04, may work on 25.10)
wget https://repo.radeon.com/amdgpu-install/latest/ubuntu/jammy/amdgpu-install_6.4.60401-1_all.deb
sudo apt install ./amdgpu-install_6.4.60401-1_all.deb

# Install ROCm
sudo amdgpu-install --usecase=rocm

# Verify installation
rocm-smi
rocminfo

# Add user to groups
sudo usermod -a -G render,video $USER
# Log out and back in for group changes to take effect
```

### 2. Install Ollama with ROCm
```bash
# Install Ollama (automatically detects ROCm)
curl -fsSL https://ollama.com/install.sh | sh

# Verify Ollama service
systemctl status ollama

# Test GPU detection
ollama --version
```

### 3. Install LiteLLM
```bash
# Install pipx if not available
sudo apt install pipx
pipx ensurepath

# Install LiteLLM with proxy support
pipx install 'litellm[proxy]'
```

### 4. Pull Models
```bash
# Start with smaller models for testing
ollama pull mistral:7b-q4_K_M
ollama pull codellama:7b-q4_K_M
ollama pull llama3.1:8b-q4_K_M
```

### 5. Start Services
```bash
# Ollama starts automatically via systemd
systemctl status ollama

# Start LiteLLM manually (or use systemd service)
cd services/llm-router/config
litellm --config config.yaml --port 8000
```

### 6. Health Check
```bash
./infrastructure/compute-node/scripts/health-check.sh
```

## API Usage

### Test Ollama Directly
```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "llama3.2:3b", "prompt": "Hello!"}'
```

### Test via LiteLLM (OpenAI-compatible)
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Configuration

### LiteLLM Config
Location: `services/llm-router/config/config.yaml`

Current models:
- `llama3` → `ollama/llama3.2:3b`

Router settings:
- Strategy: simple-shuffle
- Retries: 2
- Timeout: 300s

## Expected Performance

### With GPU Acceleration (AMD RX 7800 XT)
- **GPU Inference**: 20-30 tokens/sec on 7B models (target)
- **VRAM Usage**: 6-7GB for Q4 quantized 7B models
- **Context Window**: Up to 8192 tokens
- **Concurrent Requests**: 2-4 (configurable via OLLAMA_NUM_PARALLEL)

### CPU Fallback (if ROCm issues)
- **CPU Inference**: ~2-5 tokens/sec (i5-12400F)
- **Memory Usage**: ~3-4GB during inference
- **Context Window**: 4096 tokens

## Current Status

- [x] Fresh Ubuntu 25.10 installation
- [x] GPU detected (AMD RX 7800 XT)
- [ ] ROCm installed and verified
- [ ] Ollama installed with GPU support
- [ ] Models downloaded and tested
- [ ] LiteLLM router configured
- [ ] Tailscale for remote access
- [ ] Prometheus metrics export
- [ ] Integration with N8n on service node

## Monitoring

### Check Service Status
```bash
systemctl status ollama
pgrep -f litellm
```

### View Logs
```bash
# Ollama logs
journalctl -u ollama -f

# LiteLLM logs
tail -f /tmp/litellm.log
```

### Health Check
```bash
./infrastructure/compute-node/scripts/health-check.sh
```

## Troubleshooting

### Ollama not responding
```bash
systemctl restart ollama
curl http://localhost:11434/api/version
```

### LiteLLM config issues
```bash
cd services/llm-router/config
litellm --config config.yaml --debug
```

### GPU not detected by ROCm
```bash
# Check if GPU is visible to system
lspci | grep -i vga

# Verify render device exists
ls -la /dev/dri/

# Check ROCm version and compatibility
rocm-smi --showdriverversion

# May need to set environment variable for gfx1101
export HSA_OVERRIDE_GFX_VERSION=11.0.0
```

## References

- [Ollama Documentation](https://github.com/ollama/ollama)
- [LiteLLM Documentation](https://docs.litellm.ai)
- [Sprint 3 Roadmap](../../README.md#sprint-3-llm-infrastructure-weeks-7-8)
