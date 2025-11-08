# Flowise + Open WebUI Integration Guide

**Status**: Both services running and accessible
**Last Updated**: 2025-10-30

## Overview

Flowise and Open WebUI are complementary tools that can work together for enhanced AI workflow capabilities:

- **Flowise**: Low-code LLM orchestration for building AI chains and agents
- **Open WebUI**: Chat interface with pipeline support for custom processing

## Current Deployment Status

### Flowise
- **URL**: http://100.81.76.55:30850 (Tailscale) | https://flowise.homelab.pesulabs.net
- **Status**: ✅ Running (pod: flowise-656477f7d8-8x7rp)
- **Credentials**: admin/admin123
- **Database**: PostgreSQL (flowise database)
- **Storage**: 5Gi PVC

### Open WebUI
- **URL**: http://100.81.76.55:30080 (Tailscale) | https://webui.homelab.pesulabs.net
- **Status**: ✅ Running (pod: open-webui-0)
- **Pipeline Service**: open-webui-pipelines-67867f6bbc-g7q8z
- **Ollama Backend**: http://100.72.98.106:11434 (Compute Node via Tailscale)

### Shared LLM Backend
Both services connect to the same Ollama instance:
- **Location**: Compute Node (pesubuntu)
- **Tailscale IP**: 100.72.98.106:11434
- **Models Available**:
  - gpt-oss:20b (82 tok/s, benchmarked)
  - llama3.1:8b
  - mistral:7b-instruct-q4_K_M
  - qwen2.5-coder:14b
  - glm4:9b
  - nomic-embed-text (embeddings)

## Integration Patterns

### 1. Flowise API → Open WebUI Pipeline (Recommended)

**Use Case**: Execute Flowise chatflows from within Open WebUI conversations

**Architecture**:
```
User → Open WebUI → Pipeline → Flowise API → Chatflow → Ollama → Response
```

**Benefits**:
- Combine Flowise's visual workflow builder with WebUI's chat interface
- Access RAG chains, agents, and tools from Flowise within chat
- Unified user experience

**Setup Steps**:

#### Step 1: Get Flowise API Endpoint
```bash
# Flowise API is available at:
# Internal: http://flowise.homelab.svc.cluster.local:3000
# External: http://100.81.76.55:30850
```

#### Step 2: Create Flowise Chatflow
1. Access Flowise: http://100.81.76.55:30850
2. Login: admin/admin123
3. Create a new chatflow with:
   - Chat Model (Ollama)
   - Optional: Vector Store (Qdrant), Tools, Agents
   - Save and note the Chatflow ID

#### Step 3: Get Chatflow API Details
1. In Flowise, click your chatflow
2. Click "API" button (top right)
3. Copy the Chatflow ID and API endpoint
4. Example: `http://100.81.76.55:30850/api/v1/prediction/{chatflowId}`

#### Step 4: Create Open WebUI Pipeline

Create a custom pipeline that calls Flowise:

```python
# File: flowise_pipeline.py
from typing import List, Optional
import requests
import os

class Pipeline:
    def __init__(self):
        self.name = "Flowise Integration"
        self.flowise_url = os.getenv("FLOWISE_URL", "http://flowise.homelab.svc.cluster.local:3000")
        self.chatflow_id = os.getenv("FLOWISE_CHATFLOW_ID", "YOUR_CHATFLOW_ID")

    async def on_startup(self):
        print(f"Flowise Pipeline initialized: {self.flowise_url}")

    async def on_shutdown(self):
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> str:
        # Call Flowise chatflow
        url = f"{self.flowise_url}/api/v1/prediction/{self.chatflow_id}"

        payload = {
            "question": user_message,
            "overrideConfig": {},
            "history": messages[-5:] if len(messages) > 5 else messages  # Last 5 messages
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Extract response from Flowise
            if isinstance(data, dict):
                return data.get("text", data.get("output", str(data)))
            return str(data)

        except Exception as e:
            return f"Error calling Flowise: {str(e)}"
```

#### Step 5: Deploy Pipeline to Open WebUI

```bash
# Copy pipeline to Open WebUI pipelines pod
kubectl cp flowise_pipeline.py homelab/open-webui-pipelines-67867f6bbc-g7q8z:/app/pipelines/

# Restart pipelines to load new pipeline
kubectl rollout restart deployment/open-webui-pipelines -n homelab

# OR use Open WebUI's pipeline upload interface:
# 1. Go to Open WebUI Settings → Pipelines
# 2. Upload flowise_pipeline.py
# 3. Configure FLOWISE_CHATFLOW_ID
```

#### Step 6: Use in Open WebUI

1. Open WebUI: http://100.81.76.55:30080
2. Settings → Pipelines → Enable "Flowise Integration"
3. Start chatting - messages route through Flowise chatflow

### 2. Shared Ollama Backend (Current Setup)

**Use Case**: Both tools use the same LLM models independently

**Architecture**:
```
Flowise → Ollama (100.72.98.106:11434) → GPU Inference
Open WebUI → Ollama (100.72.98.106:11434) → GPU Inference
```

**Current Configuration**:

Both services already point to the same Ollama instance:
- Flowise: Configured in ConfigMap (lines 30-52 in flowise-deployment.yaml)
- Open WebUI: Connected during setup

**Benefits**:
- No duplicate model storage
- Shared GPU acceleration (82 tok/s on gpt-oss:20b)
- Consistent model versions

**Verification**:
```bash
# Check Flowise can reach Ollama
kubectl exec -n homelab deployment/flowise -- curl -s http://100.72.98.106:11434/api/tags

# Check Open WebUI can reach Ollama
kubectl exec -n homelab statefulset/open-webui -- curl -s http://100.72.98.106:11434/api/tags
```

### 3. Flowise Embeddings + Qdrant → Open WebUI RAG

**Use Case**: Build RAG system in Flowise, query from Open WebUI

**Architecture**:
```
Documents → Flowise (vectorize) → Qdrant Vector DB
User Query → Open WebUI → Flowise RAG Chain → Qdrant → Context → Ollama → Response
```

**Setup**:

#### In Flowise:
1. Create "Document Loader" node (PDF, text, web scraper)
2. Add "Recursive Character Text Splitter"
3. Add "Ollama Embeddings" (nomic-embed-text)
4. Add "Qdrant" vector store:
   - URL: `http://qdrant.homelab.svc.cluster.local:6333`
   - Collection name: `flowise-docs`
5. Create "Conversational Retrieval QA Chain"
6. Connect to Chat Model (Ollama)
7. Deploy chatflow

#### In Open WebUI:
1. Create pipeline that calls Flowise RAG chatflow
2. Use pipeline for document Q&A

**Benefits**:
- Visual RAG chain building in Flowise
- Clean chat interface in Open WebUI
- Persistent vector storage in Qdrant

### 4. Workflow Automation: N8n → Flowise → Open WebUI

**Use Case**: Automated workflows trigger Flowise chains, results displayed in WebUI

**Architecture**:
```
N8n Trigger → Flowise API → Process → Open WebUI Notification
```

**Example**: Document processing workflow
1. N8n monitors folder for new PDFs
2. Calls Flowise embedding chain
3. Stores vectors in Qdrant
4. Sends notification to Open WebUI via webhook

## API Endpoints

### Flowise API
```bash
# Base URL
FLOWISE_API="http://flowise.homelab.svc.cluster.local:3000/api/v1"

# List chatflows
curl "$FLOWISE_API/chatflows"

# Execute chatflow
curl -X POST "$FLOWISE_API/prediction/{chatflowId}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is quantum computing?",
    "overrideConfig": {}
  }'

# Upload to vector store
curl -X POST "$FLOWISE_API/vector/upsert/{chatflowId}" \
  -H "Content-Type: application/json" \
  -d '{
    "overrideConfig": {},
    "document": "Document content here..."
  }'
```

### Open WebUI Pipeline API
```bash
# Base URL
WEBUI_API="http://open-webui.homelab.svc.cluster.local:8080"

# List pipelines
curl "$WEBUI_API/api/pipelines"

# Execute pipeline
curl -X POST "$WEBUI_API/api/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "flowise-integration",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Configuration Examples

### Flowise: Add New Model to Existing Deployment

```bash
# Edit Flowise ConfigMap
kubectl edit configmap flowise-config -n homelab

# Add to MODEL_LIST_CONFIG_JSON array:
{
  "name": "gpt-oss-20b",
  "model": "gpt-oss:20b",
  "baseURL": "http://100.72.98.106:11434"
}

# Restart Flowise to apply
kubectl rollout restart deployment/flowise -n homelab
```

### Open WebUI: Add Flowise as External LLM Provider

In Open WebUI Admin Settings:
1. Settings → Connections → OpenAI API
2. Add new connection:
   - Name: "Flowise Chatflows"
   - Base URL: `http://flowise.homelab.svc.cluster.local:3000/api/v1`
   - API Key: (get from Flowise settings)

## Use Case Examples

### Example 1: Code Review Agent
**Flowise**: Build code review chain with:
- Tools: GitHub API, Code Analyzer
- Agent: React Agent with code review tools
- Model: qwen2.5-coder:14b

**Open WebUI**: Create pipeline to call Flowise agent for `/review` commands

### Example 2: Document Q&A with Context
**Flowise**: RAG chain with:
- Document Loader: Upload PDFs
- Embeddings: nomic-embed-text
- Vector Store: Qdrant
- Chat Model: llama3.1:8b

**Open WebUI**: Chat interface for asking questions about documents

### Example 3: Multi-Agent System
**Flowise**: Orchestrate multiple agents:
- Research Agent (web search + summarization)
- Writing Agent (content generation)
- Review Agent (fact-checking)

**Open WebUI**: Single chat interface controlling all agents

## Monitoring Integration

### Check Both Services Health
```bash
# Flowise health
curl http://100.81.76.55:30850/api/v1/chatflows

# Open WebUI health
curl http://100.81.76.55:30080/health

# Shared Ollama backend
curl http://100.72.98.106:11434/api/tags
```

### View Logs
```bash
# Flowise logs
kubectl logs -n homelab -l app=flowise -f

# Open WebUI logs
kubectl logs -n homelab -l app=open-webui -f

# Pipeline logs
kubectl logs -n homelab -l app=open-webui-pipelines -f
```

### Grafana Dashboard
Access: http://100.81.76.55:30300

Monitor:
- Flowise pod resources
- Open WebUI pod resources
- Shared Ollama GPU usage (on compute node)

## Troubleshooting

### Issue: Flowise can't reach Ollama
```bash
# Test connectivity from Flowise pod
kubectl exec -n homelab deployment/flowise -- curl -v http://100.72.98.106:11434/api/tags

# Check Tailscale on compute node
tailscale status

# Verify Ollama is listening
sudo lsof -i :11434
```

### Issue: Open WebUI pipeline can't call Flowise
```bash
# Check Flowise service DNS
kubectl exec -n homelab statefulset/open-webui -- nslookup flowise.homelab.svc.cluster.local

# Test Flowise API from pipeline pod
kubectl exec -n homelab deployment/open-webui-pipelines -- \
  curl -s http://flowise.homelab.svc.cluster.local:3000/api/v1/chatflows
```

### Issue: Slow responses from integrated setup
```bash
# Check GPU utilization on compute node
rocm-smi --showuse

# Monitor pod resources
kubectl top pods -n homelab

# Check for memory pressure
kubectl describe node asuna | grep -A 5 "Allocated resources"
```

## Performance Considerations

### Current Performance Baseline
- **Ollama (gpt-oss:20b)**: 82 tok/s with GPU
- **Flowise**: Lightweight overhead (~50-100ms per chain step)
- **Open WebUI Pipeline**: Minimal latency (<50ms)

### Optimization Tips
1. **Use smaller models for chains**: llama3.1:8b for intermediate steps
2. **Cache embeddings**: Store in Qdrant, don't re-embed
3. **Parallel chains**: Use Flowise's parallel node execution
4. **Limit history**: Only send last N messages to Flowise

## Security Considerations

### Current Security Posture
- ✅ Services isolated in homelab namespace
- ✅ Internal communication via ClusterIP DNS
- ✅ Credentials in Kubernetes Secrets
- ⚠️ Default admin passwords (change in production)
- ⚠️ No HTTPS between services (TLS needed for production)

### Recommended Improvements
1. Change default passwords
2. Enable API key authentication in Flowise
3. Add network policies for pod-to-pod communication
4. Use cert-manager for internal TLS
5. Implement rate limiting on APIs

## Next Steps

### Quick Start
1. ✅ Both services deployed and running
2. Create first Flowise chatflow using Ollama models
3. Test chatflow via Flowise UI
4. Create Open WebUI pipeline to call Flowise
5. Test integration end-to-end

### Advanced Integration
1. Build RAG chain with Qdrant in Flowise
2. Create multi-agent system
3. Integrate with N8n for automation
4. Add custom tools and APIs

### Production Readiness
1. Change default credentials
2. Set up monitoring alerts
3. Implement backup for Flowise database
4. Configure rate limiting
5. Add TLS encryption

## Resources

- **Flowise Docs**: https://docs.flowiseai.com/
- **Open WebUI Docs**: https://docs.openwebui.com/
- **Flowise API Reference**: https://docs.flowiseai.com/api-reference
- **Pipeline Development**: https://docs.openwebui.com/pipelines

## Summary

**Integration Status**: ✅ **READY**

Both Flowise and Open WebUI are:
- ✅ Running and accessible
- ✅ Connected to same Ollama backend (82 tok/s GPU-accelerated)
- ✅ Database-backed with persistent storage
- ✅ Internally networked via Kubernetes DNS
- ✅ Externally accessible via Tailscale NodePorts

**Recommended Integration**: Flowise API → Open WebUI Pipeline

This allows you to:
- Build complex AI chains visually in Flowise
- Access them through clean chat UI in Open WebUI
- Share GPU-accelerated Ollama models
- Scale independently as needed

Start with Pattern 1 (Flowise API → Pipeline) for best user experience!
