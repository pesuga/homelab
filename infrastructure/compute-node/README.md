# Compute Node Setup

LLM inference infrastructure running on the compute node (WSL2/Ubuntu 24.04).

## Architecture

```
Compute Node (localhost)
├── Ollama (Port 11434)
│   └── Model: llama3.2:3b (2GB)
└── LiteLLM Router (Port 8000)
    └── OpenAI-compatible API
```

## Installed Services

### Ollama v0.12.6
- **Purpose**: Local LLM model hosting and inference
- **Port**: 11434
- **Models**: llama3.2:3b
- **Compute**: CPU-based (i5-12400F, 6 cores, 24GB RAM)
- **Service**: systemd (ollama.service)
- **API**: http://localhost:11434

### LiteLLM v1.78.3
- **Purpose**: OpenAI-compatible proxy and router
- **Port**: 8000
- **Config**: services/llm-router/config/config.yaml
- **API**: http://localhost:8000
- **Endpoints**:
  - Health: GET /health
  - Chat: POST /v1/chat/completions
  - Models: GET /v1/models

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

## Quick Start

### 1. Install Dependencies
```bash
# Ollama (requires sudo)
curl -fsSL https://ollama.com/install.sh | sh

# LiteLLM with proxy support
pipx install 'litellm[proxy]'
pipx ensurepath
```

### 2. Pull Models
```bash
ollama pull llama3.2:3b
```

### 3. Start LiteLLM
```bash
cd services/llm-router/config
litellm --config config.yaml --port 8000
```

### 4. Health Check
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

## Performance

- **CPU Inference**: ~2-5 tokens/sec (i5-12400F)
- **Memory Usage**: ~3-4GB during inference
- **Context Window**: 4096 tokens
- **Concurrent Requests**: 1 (OLLAMA_NUM_PARALLEL=1)

## Future Enhancements

- [ ] GPU acceleration with AMD ROCm (RX 7800 XT)
- [ ] Additional models (Mistral, CodeLlama)
- [ ] Systemd service installation
- [ ] Prometheus metrics export
- [ ] Load balancing across multiple models
- [ ] Remote access via Tailscale

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

### GPU not detected (WSL2)
WSL2 GPU passthrough for AMD is experimental. Currently running CPU-only mode.
To enable GPU: Configure GPU-PV in Windows or use native Linux.

## References

- [Ollama Documentation](https://github.com/ollama/ollama)
- [LiteLLM Documentation](https://docs.litellm.ai)
- [Sprint 3 Roadmap](../../README.md#sprint-3-llm-infrastructure-weeks-7-8)
