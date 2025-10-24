# 🚀 Continue VS Code Setup - Local LLM Configuration

**Last Updated**: 2025-10-23
**LiteLLM Endpoint**: http://localhost:8000 (or http://100.72.98.106:8000 from other devices)

---

## What is Continue?

Continue is a VS Code extension that provides AI-powered coding assistance with support for local LLMs via OpenAI-compatible APIs (like our LiteLLM setup).

---

## Configuration

### Option 1: Auto-Configuration (Recommended)

1. Open VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Continue: Open config.json"
4. Replace the contents with the configuration below

### Option 2: Manual File Edit

Edit: `~/.continue/config.json`

```json
{
  "models": [
    {
      "title": "Llama 3.1 8B (128K)",
      "provider": "openai",
      "model": "gpt-3.5-turbo",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "dummy-key-not-needed"
    },
    {
      "title": "Qwen2.5-Coder 14B (32K)",
      "provider": "openai",
      "model": "qwen-coder",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "dummy-key-not-needed"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Qwen2.5-Coder 14B",
    "provider": "openai",
    "model": "qwen-coder",
    "apiBase": "http://localhost:8000/v1",
    "apiKey": "dummy-key-not-needed"
  },
  "embeddingsProvider": {
    "provider": "openai",
    "model": "text-embedding-ada-002",
    "apiBase": "http://localhost:8000/v1",
    "apiKey": "dummy-key-not-needed"
  },
  "customCommands": [
    {
      "name": "test",
      "prompt": "Write a comprehensive set of unit tests for the selected code. Use the testing framework that is most common for the language.",
      "description": "Write unit tests for highlighted code"
    }
  ],
  "allowAnonymousTelemetry": false,
  "docs": []
}
```

---

## Features Enabled

### 1. Chat Interface
- Access via Continue sidebar
- Use Llama 3.1 8B for general questions (128K context)
- Use Qwen2.5-Coder 14B for coding tasks

### 2. Tab Autocomplete
- Configured to use Qwen2.5-Coder 14B
- Press `Tab` to accept suggestions
- Works like GitHub Copilot but with your local model

### 3. Quick Actions
- Select code → Right-click → "Continue: ..."
- `/edit` - Edit selected code with instructions
- `/comment` - Add comments to code
- `/test` - Generate unit tests
- `/explain` - Explain selected code

### 4. Custom Commands
- Pre-configured `/test` command for unit test generation
- Add more in config.json `customCommands` section

---

## Usage Examples

### Chat with Context
```
You: How do I connect to PostgreSQL in Node.js?
AI: [Qwen2.5-Coder provides code example]
```

### Code Editing
1. Select code block
2. Press `Ctrl+I` (or `Cmd+I`)
3. Type instruction: "Add error handling"
4. AI generates diff with changes

### Tab Autocomplete
```javascript
function calculateFib
// Press Tab after typing "calculateFib"
// AI completes: function calculateFibonacci(n) { ... }
```

---

## Troubleshooting

### Continue can't connect to LiteLLM

**Check LiteLLM is running:**
```bash
curl http://localhost:8000/v1/models
# Should return list of models
```

**If not running:**
```bash
cd ~/Rakuflow/systems/homelab
/home/pesu/.local/bin/litellm --config services/llm-router/config/config.yaml --port 8000
```

### Model not available

**List available models:**
```bash
curl http://localhost:8000/v1/models
```

**Check Ollama:**
```bash
ollama list
# Should show: llama3.1:8b, qwen2.5-coder:14b
```

### Slow responses

**Monitor GPU usage:**
```bash
rocm-smi
# Check VRAM and utilization
```

**Switch to faster model:**
- Use `gpt-3.5-turbo` (Llama 3.1 8B) for faster responses
- Use `qwen-coder` (Qwen2.5-Coder 14B) for better code quality

---

## Remote Access (From Other Devices)

If you want to use Continue from another machine on your Tailscale network:

### Update config.json on remote machine:
```json
{
  "models": [
    {
      "title": "Llama 3.1 8B (Remote)",
      "provider": "openai",
      "model": "gpt-3.5-turbo",
      "apiBase": "http://100.72.98.106:8000/v1",
      "apiKey": "dummy-key-not-needed"
    }
  ]
}
```

Replace `localhost` with `100.72.98.106` (your compute node's Tailscale IP).

---

## Advanced Configuration

### Add More Models

When more models are available in LiteLLM, add them:

```json
{
  "title": "Model Name",
  "provider": "openai",
  "model": "model-id-from-litellm",
  "apiBase": "http://localhost:8000/v1",
  "apiKey": "dummy-key-not-needed"
}
```

### Custom System Prompts

```json
{
  "models": [
    {
      "title": "Python Expert",
      "provider": "openai",
      "model": "gpt-3.5-turbo",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "dummy-key-not-needed",
      "systemMessage": "You are an expert Python developer. Always follow PEP 8 and write comprehensive docstrings."
    }
  ]
}
```

### Temperature and Sampling

```json
{
  "models": [
    {
      "title": "Creative Coder",
      "provider": "openai",
      "model": "qwen-coder",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "dummy-key-not-needed",
      "temperature": 0.8,
      "topP": 0.9
    }
  ]
}
```

---

## Performance Tips

### 1. Use Appropriate Model for Task
- **Quick edits**: Llama 3.1 8B (faster)
- **Complex refactoring**: Qwen2.5-Coder 14B (better quality)
- **Large context**: Llama 3.1 8B (128K context)

### 2. Monitor VRAM
```bash
watch -n 1 rocm-smi
# Keep VRAM usage under 14GB for smooth operation
```

### 3. Close Other GPU Applications
- Stop other Ollama instances
- Close GPU-accelerated browsers if needed

### 4. Adjust Context Window
In Continue config, limit context for faster responses:
```json
{
  "models": [
    {
      "title": "Fast Llama",
      "provider": "openai",
      "model": "gpt-3.5-turbo",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "dummy-key-not-needed",
      "contextLength": 8192
    }
  ]
}
```

---

## Keyboard Shortcuts

- `Ctrl+I` / `Cmd+I` - Inline edit
- `Ctrl+L` / `Cmd+L` - Open chat
- `Ctrl+Shift+R` / `Cmd+Shift+R` - Quick action menu
- `Tab` - Accept autocomplete suggestion
- `Esc` - Dismiss suggestion

---

## Next Steps

1. **Test the setup**: Open VS Code and try chatting
2. **Try autocomplete**: Start typing a function
3. **Custom commands**: Add project-specific commands to config.json
4. **Share config**: Copy config to other machines via Tailscale

---

## Related Documentation

- **LiteLLM Config**: `/services/llm-router/config/config.yaml`
- **Ollama Models**: Run `ollama list` to see installed models
- **Continue Docs**: https://continue.dev/docs
- **LiteLLM Docs**: https://docs.litellm.ai

---

**Status**: ✅ Ready to use local LLMs in VS Code
**Models**: Llama 3.1 8B (128K), Qwen2.5-Coder 14B (32K)
**Endpoint**: http://localhost:8000/v1 (OpenAI-compatible)
