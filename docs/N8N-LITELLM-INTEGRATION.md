# N8n + LiteLLM Integration Guide

**Date**: 2025-10-24
**Sprint**: Sprint 4 - Advanced Services
**Status**: ✅ Ready for Integration

---

## Overview

This guide shows how to integrate your local LiteLLM API (running on the compute node) with N8n workflows for AI-powered automation.

### What You'll Get:
- ✅ Local LLM inference in N8n workflows
- ✅ OpenAI-compatible API (drop-in replacement)
- ✅ Multiple models (Llama 3.1, Mistral, Qwen Coder)
- ✅ Secure API key authentication
- ✅ Free and private (no external API calls)

---

## LiteLLM API Details

### API Endpoint
- **URL**: `http://100.72.98.106:8000/v1` (Compute node via Tailscale)
- **Alternative**: `http://localhost:8000/v1` (if accessing from compute node)
- **Protocol**: OpenAI-compatible REST API
- **Authentication**: Bearer token (API key)

### API Key
```
sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0
```

**Security Note**: This key is stored in:
- `/home/pesu/Rakuflow/systems/homelab/services/llm-router/config/config.yaml`
- Rotate this key if compromised

### Available Models

| Model Name | Description | Use Case | Size |
|------------|-------------|----------|------|
| `gpt-3.5-turbo` | Llama 3.1 8B (aliased) | General purpose, chat | 4.9GB |
| `mistral` | Mistral 7B Instruct | Fast responses, instructions | 4.4GB |
| `qwen-coder` | Qwen 2.5 Coder 14B | Code generation, debugging | 9.0GB |

**Note**: `gpt-3.5-turbo` is aliased to Llama 3.1 for OpenAI compatibility.

---

## Step 1: Add Credentials in N8n

### Method A: Via N8n Web UI (Recommended)

1. **Access N8n**:
   - Open: http://100.81.76.55:30678
   - Login: admin / admin123

2. **Go to Credentials**:
   - Click your profile icon (top right)
   - Select **Settings**
   - Click **Credentials** in left sidebar

3. **Create New Credential**:
   - Click **+ Add Credential**
   - Search for: **OpenAI**
   - Select **OpenAI API**

4. **Configure Credential**:
   ```
   Credential Name: LiteLLM Local
   API Key: sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0
   ```

   **Advanced Options** (expand):
   ```
   Base URL: http://100.72.98.106:8000/v1
   ```

5. **Save**:
   - Click **Save**
   - Credential is now available for workflows

### Method B: Via API/Export (Alternative)

If you prefer to manage credentials programmatically:

```json
{
  "name": "LiteLLM Local",
  "type": "openAiApi",
  "data": {
    "apiKey": "sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0",
    "baseURL": "http://100.72.98.106:8000/v1"
  }
}
```

---

## Step 2: Create Your First AI Workflow

### Example 1: Simple Chat Completion

1. **Create New Workflow**:
   - Click **Workflows** → **Add Workflow**
   - Name it: "Test LLM Chat"

2. **Add Manual Trigger**:
   - Click **+** → Search "Manual Trigger"
   - Add to canvas

3. **Add OpenAI Chat Node**:
   - Click **+** → Search "OpenAI"
   - Select **OpenAI Chat Model**
   - Connect to Manual Trigger

4. **Configure OpenAI Node**:
   ```
   Credential: LiteLLM Local
   Model: gpt-3.5-turbo
   Prompt: What is the capital of France?
   ```

5. **Test**:
   - Click **Test workflow**
   - Click **Execute node** on Manual Trigger
   - Should see response: "The capital of France is Paris."

### Example 2: Dynamic Prompt with Input

1. **Add Set Node** (for input):
   ```json
   {
     "question": "Explain Kubernetes in simple terms"
   }
   ```

2. **Configure OpenAI Node**:
   ```
   Model: gpt-3.5-turbo
   Prompt: {{ $json.question }}
   ```

3. **Test** - Should get K8s explanation

### Example 3: Code Generation

1. **Use Qwen Coder Model**:
   ```
   Model: qwen-coder
   Prompt: Write a Python function to calculate fibonacci numbers
   Temperature: 0.2  # Lower for more deterministic code
   ```

### Example 4: Multi-Step Workflow

```
Manual Trigger
  ↓
Set (Define task)
  ↓
OpenAI Chat (Plan the task)
  ↓
Code (Process response)
  ↓
OpenAI Chat (Refine based on results)
  ↓
Send Email (Notify with results)
```

---

## Step 3: Advanced Configuration

### Temperature Settings

```
Temperature: 0.0-0.3   # Focused, deterministic (code, facts)
Temperature: 0.7-0.9   # Creative, varied (writing, brainstorming)
Temperature: 1.0+      # Very random (experimental)
```

### Max Tokens

```
Max Tokens: 50-100     # Short responses
Max Tokens: 500        # Paragraphs
Max Tokens: 2000       # Long content
Max Tokens: 4000       # Maximum (context limit)
```

### System Prompts

Add system message for better control:

```
System Message: You are a helpful assistant that provides concise answers in JSON format.
User Message: {{ $json.question }}
```

---

## Step 4: Example Workflows

### Workflow 1: Email Summarizer

```
Email Trigger (Gmail/IMAP)
  ↓
Extract Email Content
  ↓
OpenAI Chat (Summarize email)
  ↓
Send to Slack/Discord
```

**Prompt**:
```
Summarize this email in 3 bullet points:

{{ $json.body }}
```

### Workflow 2: Code Reviewer

```
GitHub Webhook (PR created)
  ↓
Get PR Diff
  ↓
OpenAI Chat (Review code - qwen-coder)
  ↓
Post Comment to PR
```

**Prompt**:
```
Review this code diff and suggest improvements:

{{ $json.diff }}

Focus on: security, performance, readability
```

### Workflow 3: Daily Homelab Report

```
Schedule Trigger (Daily 8am)
  ↓
HTTP Request (Get Prometheus metrics)
  ↓
OpenAI Chat (Analyze metrics)
  ↓
Format Report
  ↓
Send Email
```

**Prompt**:
```
Analyze these homelab metrics and create a daily report:

CPU Usage: {{ $json.cpu }}%
Memory: {{ $json.memory }}%
Disk: {{ $json.disk }}%

Provide insights and recommendations.
```

### Workflow 4: Smart Home Automation

```
Webhook (Sensor data)
  ↓
OpenAI Chat (Decide action)
  ↓
IF Node (Check recommendation)
  ↓
Home Assistant API (Execute)
  ↓
Log to Database
```

---

## Troubleshooting

### Connection Refused

**Symptom**: `ECONNREFUSED 100.72.98.106:8000`

**Solutions**:
1. Check LiteLLM is running:
   ```bash
   systemctl status litellm
   ```

2. Check Tailscale connectivity:
   ```bash
   tailscale status | grep pesubuntu
   ```

3. Test endpoint manually:
   ```bash
   curl http://100.72.98.106:8000/health
   ```

### Authentication Error

**Symptom**: `401 Authentication Error`

**Solutions**:
1. Verify API key in N8n credentials
2. Check LiteLLM config:
   ```bash
   cat services/llm-router/config/config.yaml | grep master_key
   ```

3. Restart LiteLLM if key was changed:
   ```bash
   sudo systemctl restart litellm
   ```

### Slow Response

**Symptom**: Timeout or very slow

**Solutions**:
1. Use smaller model (mistral instead of qwen-coder)
2. Reduce max_tokens
3. Check GPU usage:
   ```bash
   rocm-smi
   ```

4. Check if Ollama is using GPU:
   ```bash
   journalctl -u ollama -n 50 | grep GPU
   ```

### Model Not Found

**Symptom**: `Model not found: xyz`

**Solutions**:
1. Use exact model name: `gpt-3.5-turbo`, `mistral`, or `qwen-coder`
2. Check available models:
   ```bash
   curl http://100.72.98.106:8000/models
   ```

---

## Performance Tips

### 1. Choose Right Model

```
Fast responses (< 5s):   mistral
Balanced:                gpt-3.5-turbo (llama3.1)
Best code:               qwen-coder (slower)
```

### 2. Optimize Prompts

```
❌ Bad:  "Tell me everything about Docker"
✅ Good: "List 3 main benefits of Docker in 50 words"
```

### 3. Cache Results

Use N8n's "Sticky" node to cache responses:
```
Set Sticky Node → Check if exists → If not, call LLM
```

### 4. Batch Requests

Process multiple items in parallel:
```
Split in Batches (5 items)
  ↓
OpenAI Chat (parallel)
  ↓
Merge Results
```

---

## Security Best Practices

### 1. Rotate API Keys

```bash
# Generate new key
python3 -c "import secrets; print('sk-' + secrets.token_urlsafe(32))"

# Update config.yaml
# Restart LiteLLM
sudo systemctl restart litellm

# Update N8n credentials
```

### 2. Network Security

- ✅ Use Tailscale IPs (100.x.x.x) for security
- ✅ LiteLLM not exposed to internet
- ✅ API key required for all requests
- ❌ Don't use plain HTTP over public networks

### 3. Rate Limiting (Optional)

Add to config.yaml:
```yaml
general_settings:
  master_key: your-key
  max_parallel_requests: 10
  max_user_requests_per_minute: 30
```

---

## Monitoring

### Check LiteLLM Logs

```bash
# Real-time logs
journalctl -u litellm -f

# Last 50 lines
journalctl -u litellm -n 50

# Errors only
journalctl -u litellm -p err -n 20
```

### Check GPU Usage

```bash
# AMD GPU stats
rocm-smi

# Watch GPU in real-time
watch -n 1 rocm-smi
```

### N8n Execution History

In N8n UI:
1. Go to **Executions** tab
2. Filter by workflow
3. Check execution time and errors
4. View detailed logs

---

## Cost Comparison

### Local LiteLLM (Your Setup)
- **Cost**: $0/month (free)
- **Privacy**: Complete (data never leaves homelab)
- **Speed**: 20-30 tokens/second (GPU accelerated)
- **Limit**: Unlimited requests

### OpenAI API (Cloud)
- **Cost**: ~$0.002 per 1K tokens (GPT-3.5-turbo)
- **Privacy**: Data sent to OpenAI
- **Speed**: 40-60 tokens/second
- **Limit**: Pay-per-use

**Example Monthly Cost Savings**:
- 100K tokens/day × 30 days = 3M tokens
- OpenAI cost: 3M × $0.002/1K = $6/month
- Your setup: **$0/month**

---

## Next Steps

1. ✅ Create first test workflow
2. ⏳ Build email summarizer workflow
3. ⏳ Set up daily homelab report
4. ⏳ Integrate with Grafana alerts
5. ⏳ Create workflow templates library
6. ⏳ Add PostgreSQL logging for LLM calls

---

## Example: Complete Workflow JSON

Save this as a workflow in N8n:

```json
{
  "name": "LiteLLM Test Workflow",
  "nodes": [
    {
      "parameters": {},
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [240, 300]
    },
    {
      "parameters": {
        "values": {
          "string": [
            {
              "name": "question",
              "value": "What are the benefits of self-hosted LLMs?"
            }
          ]
        }
      },
      "name": "Set Question",
      "type": "n8n-nodes-base.set",
      "position": [460, 300]
    },
    {
      "parameters": {
        "model": "gpt-3.5-turbo",
        "messages": {
          "values": [
            {
              "role": "user",
              "content": "={{ $json.question }}"
            }
          ]
        }
      },
      "name": "OpenAI Chat",
      "type": "n8n-nodes-base.openAi",
      "credentials": {
        "openAiApi": {
          "name": "LiteLLM Local"
        }
      },
      "position": [680, 300]
    }
  ],
  "connections": {
    "Manual Trigger": {
      "main": [[{"node": "Set Question", "type": "main", "index": 0}]]
    },
    "Set Question": {
      "main": [[{"node": "OpenAI Chat", "type": "main", "index": 0}]]
    }
  }
}
```

---

## Resources

- **LiteLLM Docs**: https://docs.litellm.ai
- **N8n Docs**: https://docs.n8n.io
- **OpenAI API Reference**: https://platform.openai.com/docs/api-reference

---

**Created**: 2025-10-24
**Last Updated**: 2025-10-24
**Author**: Homelab AI Integration
**Status**: Production Ready ✅
