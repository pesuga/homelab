# Memory-Enabled RAG Agent: Architecture Analysis & Recommendations

**Date**: 2025-10-30
**Status**: Analysis Complete - Recommendations Ready

## Your Requirements

1. **Chat Interface** for Flowise/N8n agent
2. **mem0 Integration** for persistent memory (remembers you over time)
3. **RAG Capability** with Qdrant vector store
4. **Spanish STT** (Speech-to-Text)

## Current Stack Analysis

### ✅ What You Already Have

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| **mem0** | ✅ Running (2 replicas) | http://mem0.homelab.svc.cluster.local:8080 | Already configured with Qdrant + Ollama |
| **Qdrant** | ✅ Running | http://qdrant.homelab.svc.cluster.local:6333 | 20Gi storage, ready for RAG |
| **Flowise** | ✅ Running | http://100.81.76.55:30850 | Has mem0 integration in v2.2.8+ |
| **N8n** | ✅ Running | http://100.81.76.55:30678 | Can integrate with mem0 API |
| **Open WebUI** | ✅ Running | http://100.81.76.55:30080 | Chat interface, but limited mem0 integration |
| **Ollama** | ✅ Running | http://100.72.98.106:11434 | 82 tok/s GPU-accelerated |
| **PostgreSQL** | ✅ Running | postgres.homelab.svc.cluster.local | Shared database |

### 🔴 What You're Missing

| Need | Gap | Recommendation |
|------|-----|----------------|
| **Spanish STT** | None deployed | Add Whisper (supports Spanish natively) |
| **Native mem0 Chat UI** | Open WebUI has limited support | Deploy **LobeChat** (native mem0 + STT support) |
| **TTS for responses** | No voice output | Whisper + Piper TTS |

## Architecture Comparison

### Option 1: Open WebUI + Flowise + mem0 (Current Plan)
```
User → Open WebUI → Pipeline → Flowise → mem0 API → Memory
                    ↓
                  Ollama → Response
```

**Pros**:
- ✅ Minimal new deployments
- ✅ Already have all components

**Cons**:
- ❌ Complex pipeline setup
- ❌ No native mem0 integration in Open WebUI
- ❌ No built-in STT support
- ❌ Requires custom pipeline code
- ❌ Three-hop latency (WebUI → Flowise → mem0)

**Verdict**: ⚠️ **Overcomplicated** - Too many hops, custom code needed

---

### Option 2: LobeChat + mem0 + Qdrant (RECOMMENDED)
```
User (voice/text) → LobeChat → mem0 API → Memory Store
                    ↓               ↓
                  Ollama        Qdrant (RAG)
                    ↓
                  Response (voice/text)
```

**Pros**:
- ✅ **Native mem0 integration** (built-in, no custom code)
- ✅ **Native Spanish STT/TTS** (Whisper + Piper built-in)
- ✅ **Modern UI** with voice interface
- ✅ **Direct integration** - one hop to mem0
- ✅ **RAG support** with Qdrant
- ✅ **Self-hosted** and open source
- ✅ **One-click deployment** on K8s
- ✅ **Mobile-friendly** (important for voice)

**Cons**:
- ⚠️ Need to deploy LobeChat (one new service)
- ⚠️ Need to deploy Whisper (for STT)

**Verdict**: ✅ **BEST CHOICE** - Purpose-built for your exact use case

---

### Option 3: N8n Direct + mem0 API
```
User → N8n Webhook → mem0 API → Memory
         ↓
       Ollama → Response
```

**Pros**:
- ✅ Full workflow control
- ✅ Good for automation

**Cons**:
- ❌ N8n not designed as chat interface
- ❌ No voice support
- ❌ Poor UX for conversation
- ❌ Better for background automation

**Verdict**: ❌ **Wrong Tool** - N8n is for workflows, not chat

---

### Option 4: Flowise Native (Simpler Alternative)
```
User → Flowise UI → mem0 Node → Memory
                  ↓           ↓
                Ollama      Qdrant
```

**Pros**:
- ✅ Flowise has built-in mem0 node (v2.2.8+)
- ✅ Visual workflow builder
- ✅ RAG chain building
- ✅ Already deployed

**Cons**:
- ⚠️ Flowise UI is for building, not daily chat
- ❌ No STT/TTS support
- ❌ Not mobile-friendly
- ❌ Clunky for conversation

**Verdict**: ⚠️ **Good for Development** - Use for building agents, not chatting

---

## Detailed Recommendation: LobeChat Stack

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                     │
│  LobeChat (http://100.81.76.55:30900)               │
│  • Text + Voice input (Spanish STT via Whisper)     │
│  • Voice output (TTS via Piper)                      │
│  • Mobile-friendly PWA                               │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌──────────────┐
│   mem0 API    │   │  Ollama LLM  │
│  (Memory)     │   │  82 tok/s    │
│               │   │  GPU accel   │
└───────┬───────┘   └──────────────┘
        │
        ▼
┌──────────────────┐
│ Qdrant Vector DB │
│ (RAG + Memory)   │
│ • User memories  │
│ • Document store │
└──────────────────┘
```

### Component Breakdown

**1. LobeChat** (New - Primary Chat UI)
- Modern React-based chat interface
- **Native mem0 support** (no custom code)
- **Multilingual STT/TTS** including Spanish
- Knowledge base (file upload → RAG)
- Plugin marketplace
- Mobile PWA support
- Self-hosted Docker/K8s deployment

**2. mem0** (Already Running)
- API endpoint: `http://mem0.homelab.svc.cluster.local:8080`
- Already configured with:
  - Qdrant backend
  - Ollama LLM (mistral:7b)
  - Embeddings (nomic-embed-text)
- LobeChat connects directly via API

**3. Qdrant** (Already Running)
- Vector DB for:
  - mem0 memory storage
  - RAG document embeddings
  - Semantic search
- Already has 20Gi storage

**4. Whisper** (New - STT Engine)
- Open-source multilingual STT
- **Native Spanish support** (trained on 680k hours)
- Can run locally on CPU or GPU
- LobeChat connects via API

**5. Ollama** (Already Running)
- LLM backend: gpt-oss:20b at 82 tok/s
- Embeddings: nomic-embed-text
- GPU-accelerated on compute node

### Spanish STT Options

#### Option A: Whisper (Recommended)
- **Model**: openai/whisper-large-v3
- **Spanish Support**: Excellent (native multilingual)
- **Deployment**: Docker container
- **Resource**: CPU (500-1000m) or GPU offload
- **Latency**: ~1-2s for 10s audio
- **Accuracy**: State-of-the-art for Spanish

```yaml
# Whisper deployment (simplified)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whisper
  namespace: homelab
spec:
  containers:
  - name: whisper
    image: onerahmet/openai-whisper-asr-webservice:latest
    env:
    - name: ASR_MODEL
      value: "large-v3"
    - name: ASR_ENGINE
      value: "faster_whisper"
```

#### Option B: Faster-Whisper (Optimized)
- **Speed**: 4x faster than Whisper
- **Accuracy**: Same model, optimized inference
- **Resource**: Lower CPU/memory usage
- **Better for**: Real-time transcription

### Deployment Plan

#### Step 1: Deploy Whisper STT
```bash
# Create Whisper deployment
kubectl apply -f infrastructure/kubernetes/services/whisper/whisper.yaml

# Service endpoint: whisper.homelab.svc.cluster.local:9000
```

#### Step 2: Deploy LobeChat
```bash
# Create LobeChat deployment with config:
# - Ollama endpoint: http://100.72.98.106:11434
# - mem0 endpoint: http://mem0.homelab.svc.cluster.local:8080
# - Whisper endpoint: http://whisper.homelab.svc.cluster.local:9000

kubectl apply -f infrastructure/kubernetes/services/lobechat/lobechat.yaml

# Access: http://100.81.76.55:30900
```

#### Step 3: Configure LobeChat
```javascript
// LobeChat config (environment variables)
{
  "OLLAMA_BASE_URL": "http://100.72.98.106:11434",
  "MEM0_API_URL": "http://mem0.homelab.svc.cluster.local:8080",
  "WHISPER_API_URL": "http://whisper.homelab.svc.cluster.local:9000",
  "QDRANT_URL": "http://qdrant.homelab.svc.cluster.local:6333",
  "DEFAULT_LANGUAGE": "es"  // Spanish
}
```

#### Step 4: Configure mem0 Integration
```javascript
// LobeChat mem0 plugin config
{
  "memory": {
    "provider": "mem0",
    "config": {
      "apiUrl": "http://mem0.homelab.svc.cluster.local:8080",
      "userId": "user_default",  // Or dynamic per user
      "enableMemory": true,
      "memoryRetention": "permanent"
    }
  }
}
```

### How It Works (User Flow)

1. **User speaks in Spanish** → Whisper transcribes → Text
2. **LobeChat sends to mem0** → Extracts user facts → Stores in Qdrant
3. **mem0 recalls relevant memories** → Adds context to prompt
4. **Ollama generates response** → 82 tok/s GPU-accelerated
5. **LobeChat reads response** → TTS (optional) → User hears

**Example Conversation**:
```
User (Spanish): "Hola, mi nombre es Pedro y me gusta el ciclismo"
↓ Whisper STT
LobeChat → mem0 API
↓ mem0 stores: {"user": "Pedro", "interests": ["cycling"]}
↓ Ollama (with context)
Response: "Hola Pedro! Es un placer conocerte. El ciclismo es genial..."

[Next day]
User: "Qué rutas de ciclismo me recomiendas?"
↓ mem0 recalls: User is Pedro, likes cycling
↓ Ollama (with memory context)
Response: "Hola Pedro! Como te gusta el ciclismo, te recomiendo..."
```

### Comparison: LobeChat vs Open WebUI

| Feature | LobeChat | Open WebUI | Winner |
|---------|----------|------------|--------|
| **mem0 Integration** | Native, built-in | Manual pipeline | ✅ LobeChat |
| **Spanish STT** | Native support | Requires custom setup | ✅ LobeChat |
| **Voice UI** | Built-in, mobile-ready | Limited | ✅ LobeChat |
| **RAG** | Knowledge base + Qdrant | Plugin system | 🟰 Tie |
| **Deployment** | Simple Docker/K8s | Simple Docker/K8s | 🟰 Tie |
| **Customization** | Plugin marketplace | Pipeline system | 🟰 Tie |
| **Mobile** | PWA, excellent | Good | ✅ LobeChat |
| **Documentation** | Excellent | Good | ✅ LobeChat |
| **Active Dev** | Very active | Active | ✅ LobeChat |

**Verdict**: ✅ LobeChat is purpose-built for your exact requirements

### Resource Requirements

**New Services**:
```yaml
Whisper:
  CPU: 500m-1000m
  Memory: 2Gi
  Storage: 2Gi (model)

LobeChat:
  CPU: 250m
  Memory: 512Mi
  Storage: 1Gi
```

**Total New Resources**: ~3.5Gi RAM, ~1 CPU core

**Service Node Capacity**:
- Current: 8GB RAM, 98GB disk
- After: ~6.5GB free RAM remaining ✅ Acceptable

## Alternative: Keep It Simple with Flowise

If you want **minimal new deployments**, you can use Flowise's native mem0 support:

### Flowise mem0 Setup (Already Possible)

1. **In Flowise** (http://100.81.76.55:30850):
   - Create new chatflow
   - Add "Chat Model" → Ollama (gpt-oss:20b)
   - Add "Memory" → **mem0 Memory** node
   - Configure mem0:
     - API URL: `http://mem0.homelab.svc.cluster.local:8080`
     - User ID: `pedro` (or dynamic)
   - Add "Retrieval QA Chain" for RAG
   - Connect to Qdrant vector store
   - Deploy chatflow

2. **Access via**:
   - Flowise built-in chat UI
   - Or N8n webhook → Flowise API
   - Or Custom React app → Flowise API

**Pros**: Zero new deployments, use what you have
**Cons**: No voice, clunky UI, not mobile-friendly

## Final Recommendation

### For Your Use Case: **Deploy LobeChat**

**Why**:
1. ✅ **Native mem0** - No custom code, just works
2. ✅ **Spanish STT** - Whisper built-in support
3. ✅ **Voice-first** - Designed for conversation
4. ✅ **Mobile-ready** - Use from phone with voice
5. ✅ **Modern UX** - Clean, fast, professional
6. ✅ **RAG support** - Qdrant integration
7. ✅ **Minimal overhead** - ~3.5Gi resources

**Keep**:
- Flowise: For building complex agent workflows
- N8n: For automation and background tasks
- LobeChat: For daily conversational interaction

**Architecture**:
```
Daily Chat → LobeChat (mem0 + voice)
Agent Development → Flowise (visual builder)
Automation → N8n (workflows)
All share → Ollama (GPU) + Qdrant (vectors) + mem0 (memory)
```

## Implementation Checklist

### Phase 1: Deploy STT (Week 1)
- [ ] Create Whisper deployment YAML
- [ ] Deploy to homelab namespace
- [ ] Test Spanish transcription
- [ ] Verify resource usage

### Phase 2: Deploy LobeChat (Week 1)
- [ ] Create LobeChat deployment YAML
- [ ] Configure Ollama connection
- [ ] Configure mem0 integration
- [ ] Configure Whisper STT
- [ ] Test chat interface

### Phase 3: Configure Memory (Week 1)
- [ ] Set up user profiles in mem0
- [ ] Test memory persistence
- [ ] Verify Qdrant storage
- [ ] Test Spanish conversation flow

### Phase 4: Add RAG (Week 2)
- [ ] Upload documents to Qdrant via LobeChat
- [ ] Configure knowledge base
- [ ] Test document Q&A
- [ ] Test memory + RAG together

### Phase 5: Polish (Week 2)
- [ ] Configure TTS for voice responses
- [ ] Set up mobile PWA
- [ ] Create monitoring dashboard
- [ ] Document user guide

## Estimated Timeline

- **Whisper Deployment**: 2 hours
- **LobeChat Deployment**: 3 hours
- **Configuration & Testing**: 4 hours
- **Total**: ~1 day of focused work

## Next Steps

1. **Review this analysis** - Confirm LobeChat approach
2. **I'll create deployment YAMLs** - Ready to apply
3. **Deploy and test** - Get it running
4. **Iterate** - Refine based on usage

Would you like me to proceed with creating the LobeChat + Whisper deployment manifests?
