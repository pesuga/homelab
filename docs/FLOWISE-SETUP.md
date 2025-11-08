# Flowise Setup Guide

## Overview

Flowise is a low-code/no-code tool for building LLM applications and AI workflows. It provides a drag-and-drop interface for creating AI chains, agents, and flows without writing code.

**Status**: ✅ Deployed and ready to use

---

## Access Information

### Local Access
- **URL**: http://100.81.76.55:30850
- **Domain**: https://flowise.homelab.pesulabs.net
- **Credentials**: admin / admin123

### Internal Service
- **Service Name**: flowise.homelab.svc.cluster.local
- **Port**: 3000
- **NodePort**: 30850

---

## Architecture

```
User Browser
    │
    ▼
Traefik Ingress (HTTPS)
    │
    ▼
Flowise Service (3000)
    │
    ├─→ PostgreSQL (flowise database)
    │       - Stores flows, credentials, API keys
    │
    └─→ Ollama (Compute Node - 100.72.98.106:11434)
            - Llama 3.1 8B
            - Mistral 7B
            - Qwen 2.5 Coder 14B
            - GLM-4 9B
```

---

## Key Features

### 1. Visual Flow Builder
- Drag-and-drop interface for building AI workflows
- Connect LLMs, vector databases, tools, and memory
- Real-time testing and debugging

### 2. LLM Support
- **Integrated Models** (via Ollama on compute node):
  - Llama 3.1 8B (general purpose)
  - Mistral 7B (fast inference)
  - Qwen 2.5 Coder 14B (code generation)
  - GLM-4 9B (multilingual, Chinese-optimized)

### 3. Agent Types
- Conversational Agent
- ReAct Agent
- Tool Agent
- OpenAI Function Agent

### 4. Tools & Integrations
- Web scraping
- API calls
- Database queries
- File operations
- Custom code execution

### 5. Memory Types
- Buffer Memory
- Conversation Summary
- Vector Store Memory
- Entity Memory

---

## First-Time Setup

### 1. Access Flowise

Open browser and navigate to:
```
https://flowise.homelab.pesulabs.net
```

Or via local access:
```
http://100.81.76.55:30850
```

### 2. Login

Use the default credentials:
- **Username**: admin
- **Password**: admin123

**⚠️ Security Note**: Change these credentials after first login

---

## Connecting to Local LLMs

### Option 1: Using Ollama (Recommended)

1. **In Flowise**, add a new ChatFlow
2. Drag **Chat Ollama** node to canvas
3. Configure:
   ```
   Base URL: http://100.72.98.106:11434
   Model Name: llama3.1:8b
   Temperature: 0.7
   ```

### Option 2: Using LiteLLM (OpenAI-Compatible)

1. Drag **ChatOpenAI** node to canvas
2. Configure:
   ```
   Base URL: http://100.72.98.106:8000/v1
   API Key: sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0
   Model: gpt-3.5-turbo (or mistral, qwen-coder)
   ```

---

## Sample Workflows

### 1. Basic Chatbot

**Nodes**:
1. Chat Ollama
   - Model: llama3.1:8b
   - Base URL: http://100.72.98.106:11434
2. Conversation Chain
3. Buffer Memory

**Flow**:
```
User Input → Buffer Memory → Conversation Chain → Chat Ollama → Response
```

### 2. RAG (Retrieval-Augmented Generation)

**Nodes**:
1. Document Loader (PDF/Text)
2. Text Splitter (Recursive Character)
3. Embeddings (Hugging Face)
4. Vector Store (In-Memory or Redis)
5. Chat Ollama
6. Conversational Retrieval QA Chain

**Flow**:
```
Documents → Split → Embed → Vector Store
                                  ↓
User Query → Retrieval → Context + Query → Chat Ollama → Answer
```

### 3. Code Generation Assistant

**Nodes**:
1. Chat Ollama
   - Model: qwen2.5-coder:14b
   - System Prompt: "You are an expert programmer..."
2. Code Output Parser
3. Tool Node (for execution)

### 4. Multi-Agent System

**Nodes**:
1. Agent Executor
2. Multiple Chat Ollama nodes (different models)
3. Tools (Calculator, Web Scraper, etc.)
4. Agent Memory

---

## Configuration

### Environment Variables

The Flowise deployment uses these key environment variables (configured in ConfigMap):

```yaml
DATABASE_TYPE: postgres
DATABASE_HOST: postgres.homelab.svc.cluster.local
DATABASE_PORT: 5432
DATABASE_NAME: flowise
DATABASE_USER: homelab

FLOWISE_USERNAME: admin
PORT: 3000

CORS_ORIGINS: "*"
IFRAME_ORIGINS: "*"
```

### Storage

**Persistent Volume**: 5Gi local-path storage
- **Path**: `/root/.flowise`
- **Contains**:
  - API keys
  - Credentials
  - Logs
  - Blob storage (uploaded files)

### Database

**PostgreSQL Database**: `flowise`
- **Tables**:
  - `chat_flow` - Saved workflows
  - `credential` - API keys and credentials
  - `tool` - Custom tools
  - `assistant` - AI assistants
  - `chat_message` - Conversation history

---

## Available Models

### Via Ollama (100.72.98.106:11434)

| Model | Size | Purpose | Performance |
|-------|------|---------|-------------|
| llama3.1:8b | 4.9GB | General purpose | ~75 tok/s |
| mistral:7b-instruct-q4_K_M | 4.4GB | Fast inference | ~90 tok/s |
| qwen2.5-coder:14b | 9.0GB | Code generation | ~45 tok/s |
| glm4:9b | 5.5GB | Multilingual | ~65 tok/s |

### Via LiteLLM (100.72.98.106:8000)

Access via OpenAI-compatible API:
- Model names: `gpt-3.5-turbo`, `mistral`, `qwen-coder`, `glm4`
- API Key required: `sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0`

---

## Common Use Cases

### 1. Customer Support Bot
- Use Conversational Agent
- Add company knowledge base (vector store)
- Connect to Slack/Discord via webhook

### 2. Document Q&A
- Upload PDFs/documents
- Use RAG pattern
- Conversational retrieval chain

### 3. Code Review Assistant
- Use Qwen Coder model
- Add code parsing tools
- GitHub integration

### 4. Data Analysis Agent
- Connect to PostgreSQL
- Use function calling
- CSV/JSON processing

### 5. Content Generator
- Blog posts, emails, summaries
- Template-based generation
- Multi-step workflows

---

## Troubleshooting

### Cannot Connect to Ollama

**Symptom**: "Connection refused" or timeout errors

**Solution**:
```bash
# Check Ollama is running on compute node
ssh pesubuntu
systemctl status ollama

# Test Ollama endpoint
curl http://localhost:11434/api/version
```

### Database Connection Issues

**Symptom**: "Cannot connect to database"

**Solution**:
```bash
# Check PostgreSQL
kubectl exec -it -n homelab postgres-0 -- psql -U homelab -d flowise -c "SELECT 1;"

# Check Flowise logs
kubectl logs -n homelab -l app=flowise
```

### Slow Model Response

**Symptom**: Long wait times for responses

**Solutions**:
- Use smaller models (mistral:7b instead of qwen2.5-coder:14b)
- Reduce `max_tokens` in model config
- Check GPU utilization: `rocm-smi` on compute node
- Ensure no other processes using GPU

### Memory Issues

**Symptom**: Pod crashes or restarts

**Solution**:
```bash
# Check resource limits
kubectl describe pod -n homelab -l app=flowise

# Increase memory limits if needed
kubectl edit deployment flowise -n homelab
# Update: resources.limits.memory: "4Gi"
```

---

## Advanced Configuration

### Custom API Keys

Add custom API keys for external services:

1. Go to **Credentials** tab
2. Click **+ Add Credential**
3. Select credential type (OpenAI, Hugging Face, etc.)
4. Enter API key
5. Save

### Embedding Models

For RAG applications, configure embeddings:

**Option 1: Hugging Face (Local)**
```
Model: sentence-transformers/all-MiniLM-L6-v2
```

**Option 2: Ollama Embeddings**
```
Base URL: http://100.72.98.106:11434
Model: nomic-embed-text
```

### Vector Stores

**Redis Integration**:
```
Host: redis.homelab.svc.cluster.local
Port: 6379
Password: (none - no authentication)
```

**PostgreSQL pgvector**:
```
Already available in the flowise database
Enable pgvector extension if needed
```

---

## Deployment Details

### Kubernetes Resources

**ConfigMap**: `flowise-config`
- Environment variables
- Model configuration

**Secret**: `flowise-secret`
- Database password
- Flowise admin password
- Encryption keys

**PVC**: `flowise-pvc`
- 5Gi persistent storage
- Local-path storage class

**Deployment**: `flowise`
- 1 replica
- Init container for database setup
- Resource limits: 2Gi RAM, 1 CPU

**Service**: `flowise`
- Type: NodePort
- Port: 3000
- NodePort: 30850

**Ingress**: `flowise-pesulabs`
- Host: flowise.homelab.pesulabs.net
- TLS: Let's Encrypt certificate
- Traefik ingress controller

### Files

- **Deployment**: `/infrastructure/kubernetes/flowise/flowise-deployment.yaml`
- **Ingress**: `/infrastructure/kubernetes/flowise/flowise-ingress.yaml`
- **Documentation**: `/docs/FLOWISE-SETUP.md` (this file)

---

## Security Considerations

### 1. Change Default Credentials

```bash
# Update secret
kubectl edit secret flowise-secret -n homelab

# Or patch it
kubectl patch secret flowise-secret -n homelab --type merge -p '{"stringData":{"FLOWISE_PASSWORD":"new-secure-password"}}'

# Restart Flowise
kubectl rollout restart deployment/flowise -n homelab
```

### 2. Restrict Access

- Use Ingress authentication (OAuth, Basic Auth)
- Limit network access via NetworkPolicy
- Use RBAC for API access

### 3. API Key Management

- Store API keys in Flowise Credentials (encrypted)
- Never hardcode keys in flows
- Rotate keys regularly

---

## Integration with N8n

Flowise and N8n can work together:

1. **Trigger N8n from Flowise**:
   - Use Webhook Tool in Flowise
   - Call N8n webhook endpoint

2. **Trigger Flowise from N8n**:
   - Use HTTP Request node
   - Call Flowise API endpoint
   - Pass input and get AI response

3. **Use Case Examples**:
   - N8n orchestrates workflow
   - Flowise handles AI logic
   - N8n performs actions based on AI output

---

## Next Steps

1. ✅ Access Flowise at https://flowise.homelab.pesulabs.net
2. ✅ Create your first chatflow
3. ✅ Connect to local LLMs via Ollama
4. 📋 Build a RAG application
5. 📋 Integrate with external APIs
6. 📋 Deploy production agents

---

## Resources

- **Flowise Docs**: https://docs.flowiseai.com
- **Ollama Integration**: https://docs.flowiseai.com/integrations/ollama
- **LangChain Docs**: https://python.langchain.com/docs/
- **Homelab Dashboard**: http://100.81.76.55:30800

---

**Last Updated**: 2025-10-24
**Status**: Deployed and Operational ✅
**Version**: Latest (flowiseai/flowise:latest)
