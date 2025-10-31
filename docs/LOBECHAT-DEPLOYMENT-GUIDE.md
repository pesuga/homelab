# LobeChat + mem0 + Whisper Deployment Guide

**Complete setup for memory-enabled, Spanish-speaking AI chat interface**

**Date**: 2025-10-30
**Estimated Time**: 2-3 hours
**Status**: Ready to Deploy

---

## 🎯 What We're Building

A modern AI chat interface with:
- ✅ **Persistent Memory** (mem0 integration)
- ✅ **Spanish Voice Input** (Whisper STT)
- ✅ **Spanish Voice Output** (Edge TTS)
- ✅ **RAG Capability** (Qdrant vector database)
- ✅ **GPU-Accelerated LLM** (Ollama at 82 tok/s)
- ✅ **Mobile-Friendly** (PWA support)

## 📋 Prerequisites

### Already Running ✅
- [x] K3s cluster (asuna node)
- [x] PostgreSQL database
- [x] Qdrant vector database
- [x] mem0 API (2 replicas)
- [x] Ollama on compute node (100.72.98.106:11434)

### To Deploy 🚀
- [ ] Whisper STT service
- [ ] LobeChat mem0 middleware
- [ ] LobeChat UI

---

## 📁 Project Structure

```
homelab/
├── infrastructure/kubernetes/services/
│   ├── whisper/
│   │   └── whisper.yaml                    # STT service
│   └── lobechat/
│       ├── lobechat.yaml                   # Main UI
│       ├── mem0-middleware.yaml            # Memory bridge
│       └── mem0-plugin.yaml                # Configuration
└── services/
    └── lobechat-mem0-middleware/
        ├── server.js                       # Middleware code
        ├── package.json
        ├── Dockerfile
        └── README.md
```

---

## 🔧 Step 1: Build Middleware Docker Image

The middleware bridges LobeChat with mem0 for automatic memory management.

### Option A: Build on Service Node (Recommended)

```bash
# SSH to service node
ssh pesu@192.168.8.185

# Navigate to project
cd /path/to/homelab/services/lobechat-mem0-middleware

# Build Docker image
docker build -t lobechat-mem0-middleware:latest .

# Verify image
docker images | grep lobechat-mem0-middleware
```

### Option B: Build Locally and Push to Registry

If you have a local Docker registry:

```bash
# Build locally
cd services/lobechat-mem0-middleware
docker build -t localhost:5000/lobechat-mem0-middleware:latest .

# Push to registry
docker push localhost:5000/lobechat-mem0-middleware:latest

# Update mem0-middleware.yaml to use registry image
# image: localhost:5000/lobechat-mem0-middleware:latest
```

### Option C: Build on Compute Node and Save/Load

```bash
# On compute node
cd services/lobechat-mem0-middleware
docker build -t lobechat-mem0-middleware:latest .
docker save lobechat-mem0-middleware:latest -o /tmp/middleware.tar

# Transfer to service node
scp /tmp/middleware.tar pesu@192.168.8.185:/tmp/

# On service node
docker load -i /tmp/middleware.tar
rm /tmp/middleware.tar
```

---

## 🚀 Step 2: Deploy Services

### Deploy in Correct Order

#### 2.1 Deploy Whisper STT

```bash
# Apply Whisper deployment
kubectl apply -f infrastructure/kubernetes/services/whisper/whisper.yaml

# Watch deployment
kubectl get pods -n homelab -l app=whisper -w

# Wait for running (this may take 2-3 minutes for model download)
kubectl wait --for=condition=ready pod -l app=whisper -n homelab --timeout=300s

# Verify Whisper is healthy
kubectl logs -n homelab -l app=whisper --tail=50

# Test STT endpoint
curl http://100.81.76.55:30900/health
```

**Expected**: Whisper pod running, model `large-v3` loaded

#### 2.2 Deploy mem0 Middleware

```bash
# Apply middleware deployment
kubectl apply -f infrastructure/kubernetes/services/lobechat/mem0-middleware.yaml

# Watch deployment
kubectl get pods -n homelab -l app=lobechat-mem0-middleware -w

# Wait for running
kubectl wait --for=condition=ready pod -l app=lobechat-mem0-middleware -n homelab --timeout=120s

# Verify middleware is healthy
kubectl logs -n homelab -l app=lobechat-mem0-middleware --tail=50

# Test middleware endpoint
kubectl exec -n homelab deployment/lobechat-mem0-middleware -- \
  curl -s http://localhost:11435/health
```

**Expected**: Middleware running, connected to Ollama and mem0

#### 2.3 Update LobeChat Configuration

Before deploying LobeChat, we need to point it to the middleware:

```bash
# Edit lobechat.yaml
nano infrastructure/kubernetes/services/lobechat/lobechat.yaml

# Update OLLAMA_PROXY_URL in ConfigMap:
# FROM: OLLAMA_PROXY_URL: "http://100.72.98.106:11434"
# TO:   OLLAMA_PROXY_URL: "http://lobechat-mem0-middleware.homelab.svc.cluster.local:11435"
```

Or use kubectl edit:

```bash
kubectl create configmap lobechat-config \
  --from-literal=OLLAMA_PROXY_URL=http://lobechat-mem0-middleware.homelab.svc.cluster.local:11435 \
  --from-literal=STT_SERVER_URL=http://whisper.homelab.svc.cluster.local:9000 \
  --from-literal=ENABLE_STT=1 \
  --from-literal=ENABLE_TTS=1 \
  --from-literal=DEFAULT_LANG=es-ES \
  --from-literal=QDRANT_URL=http://qdrant.homelab.svc.cluster.local:6333 \
  --from-literal=PORT=3210 \
  --dry-run=client -o yaml | kubectl apply -f -
```

#### 2.4 Deploy LobeChat

```bash
# Apply LobeChat deployment
kubectl apply -f infrastructure/kubernetes/services/lobechat/lobechat.yaml

# Watch deployment
kubectl get pods -n homelab -l app=lobechat -w

# Wait for running
kubectl wait --for=condition=ready pod -l app=lobechat -n homelab --timeout=180s

# Verify LobeChat is healthy
kubectl logs -n homelab -l app=lobechat --tail=50
```

---

## ✅ Step 3: Verify Deployment

### Check All Services

```bash
# View all services
kubectl get pods -n homelab -l 'app in (whisper,lobechat-mem0-middleware,lobechat)'

# Expected output:
# NAME                                        READY   STATUS    RESTARTS   AGE
# whisper-xxx                                 1/1     Running   0          5m
# lobechat-mem0-middleware-xxx                1/1     Running   0          4m
# lobechat-mem0-middleware-yyy                1/1     Running   0          4m
# lobechat-xxx                                1/1     Running   0          3m
```

### Test Each Component

#### Test 1: Whisper STT

```bash
# Test Spanish transcription
curl -X POST http://100.81.76.55:30900/asr \
  -F "audio_file=@test_audio.mp3" \
  -F "task=transcribe" \
  -F "language=es"

# Expected: Spanish transcription text
```

#### Test 2: mem0 Middleware

```bash
# Test middleware health
curl http://lobechat-mem0-middleware.homelab.svc.cluster.local:11435/health

# Test chat with memory injection
curl -X POST http://lobechat-mem0-middleware.homelab.svc.cluster.local:11435/api/chat \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d '{
    "model": "gpt-oss:20b",
    "messages": [
      {"role": "user", "content": "Hola, me llamo Pedro"}
    ],
    "stream": false
  }'

# Expected: Response + memories stored in mem0
```

#### Test 3: mem0 Memory Storage

```bash
# Check if memory was stored
curl "http://mem0.homelab.svc.cluster.local:8080/v1/memories/?user_id=test_user"

# Expected: JSON with stored memories about Pedro
```

#### Test 4: LobeChat UI

```bash
# Access LobeChat
# Browser: http://100.81.76.55:30910

# Or via curl
curl -s http://100.81.76.55:30910 | grep -i "lobe"

# Expected: LobeChat HTML page
```

---

## 🎉 Step 4: First Conversation

### Access LobeChat

1. **Open browser**: `http://100.81.76.55:30910`
2. **First load**: May take 10-15 seconds
3. **Create account** (optional - local storage only)
4. **Select model**: gpt-oss:20b

### Test Memory Persistence

**Conversation 1** (Introduce yourself):
```
You: "Hola, me llamo Pedro y soy de Argentina. Me gusta el ciclismo de montaña."

AI: [Responds and stores memories: name=Pedro, location=Argentina, interest=mountain biking]
```

**Conversation 2** (Later or new session):
```
You: "¿Qué me recomiendas hacer este fin de semana?"

AI: "Hola Pedro! Considerando que te gusta el ciclismo de montaña, te recomiendo..."
[Uses stored memories to provide personalized response]
```

### Test Spanish Voice Input

1. Click microphone icon in LobeChat
2. Speak in Spanish: "Hola, ¿cómo estás?"
3. Whisper transcribes → sends to middleware → LLM responds
4. Response appears in chat

---

## 🔍 Monitoring & Troubleshooting

### View Logs

```bash
# LobeChat logs
kubectl logs -n homelab -l app=lobechat -f

# Middleware logs (shows mem0 operations)
kubectl logs -n homelab -l app=lobechat-mem0-middleware -f

# Whisper logs
kubectl logs -n homelab -l app=whisper -f

# mem0 logs
kubectl logs -n homelab -l app=mem0 -f
```

### Check Resource Usage

```bash
# Pod resources
kubectl top pods -n homelab -l 'app in (whisper,lobechat,lobechat-mem0-middleware)'

# Node resources
kubectl top node asuna
```

### Common Issues

#### Issue 1: Whisper Model Download Slow
```bash
# Check download progress
kubectl logs -n homelab -l app=whisper --tail=100

# Whisper downloads ~3GB model on first run
# This can take 5-10 minutes depending on internet speed
```

#### Issue 2: Middleware Can't Reach mem0
```bash
# Test mem0 connectivity from middleware pod
kubectl exec -n homelab deployment/lobechat-mem0-middleware -- \
  curl -s http://mem0.homelab.svc.cluster.local:8080/health

# Expected: {"status": "healthy"}
```

#### Issue 3: Middleware Can't Reach Ollama
```bash
# Test Ollama connectivity from middleware pod
kubectl exec -n homelab deployment/lobechat-mem0-middleware -- \
  curl -s http://100.72.98.106:11434/api/tags

# Expected: JSON with model list
```

#### Issue 4: No Memories Being Stored
```bash
# Check middleware logs for mem0 API calls
kubectl logs -n homelab -l app=lobechat-mem0-middleware | grep mem0

# Check mem0 directly
curl "http://mem0.homelab.svc.cluster.local:8080/v1/memories/?user_id=default_user"
```

#### Issue 5: Spanish STT Not Working
```bash
# Test Whisper directly
curl -X POST http://100.81.76.55:30900/asr \
  -F "audio_file=@test.mp3" \
  -F "language=es"

# Check LobeChat STT configuration
kubectl get configmap lobechat-config -n homelab -o yaml | grep STT
```

---

## 📊 Performance Expectations

### Response Times (Expected)

| Component | Latency | Notes |
|-----------|---------|-------|
| **Whisper STT** | 1-3s | Per 10s audio (CPU) |
| **mem0 Memory Fetch** | 50-200ms | From Qdrant |
| **Middleware Processing** | <50ms | Memory injection |
| **Ollama Generation** | Variable | ~82 tok/s for gpt-oss:20b |
| **Total (voice → response)** | 2-5s | First token |

### Resource Usage (Expected)

| Service | CPU | Memory | Storage |
|---------|-----|--------|---------|
| **Whisper** | 500m-2000m | 2-4Gi | 5Gi (model) |
| **Middleware** | 100-500m | 128-512Mi | - |
| **LobeChat** | 250-1000m | 512Mi-2Gi | 2Gi |
| **Total New** | ~2 cores | ~6Gi | ~9Gi |

**Service Node Capacity**: 8GB RAM → ~2GB free after deployment (acceptable)

---

## 🎨 Advanced Configuration

### Custom User IDs

Edit middleware to extract user ID from LobeChat:

```javascript
// In server.js
const userId = req.headers['x-user-id'] ||
               req.body.user ||
               'default_user';
```

### Multiple Language Support

Whisper supports auto-detection:

```yaml
# In whisper ConfigMap
ASR_LANGUAGE: ""  # Auto-detect
ASR_DETECT_LANGUAGE: "true"
```

### Faster STT (GPU Acceleration)

If you want to move Whisper to compute node with GPU:

```yaml
# Update whisper.yaml
ASR_DEVICE: "cuda"
# Deploy to compute node instead of service node
```

### Custom System Prompt

Edit LobeChat system prompt to emphasize memory usage:

```javascript
// In lobechat ConfigMap
SYSTEM_PROMPT: |
  You are a helpful AI assistant with perfect memory.
  Always recall and reference past conversations.
  Use the provided memories to personalize your responses.
```

---

## 🔐 Security Considerations

### Current Setup (Development)

- ⚠️ No authentication on LobeChat
- ⚠️ No TLS/HTTPS
- ⚠️ Services on internal network only

### Production Recommendations

1. **Enable Authentication**
   ```yaml
   # In lobechat ConfigMap
   ENABLE_NEXT_AUTH: "1"
   ACCESS_CODE: "your-secret-code"
   ```

2. **Add TLS**
   - Deploy cert-manager
   - Configure Ingress with TLS
   - Update all HTTP → HTTPS

3. **Network Policies**
   ```yaml
   # Restrict middleware access
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   # Only allow LobeChat → Middleware
   ```

4. **API Rate Limiting**
   - Add rate limiting to middleware
   - Prevent abuse of Ollama/mem0 resources

---

## 📈 Scaling & Optimization

### Horizontal Scaling

```bash
# Scale middleware for high load
kubectl scale deployment/lobechat-mem0-middleware -n homelab --replicas=3

# Scale LobeChat
kubectl scale deployment/lobechat -n homelab --replicas=2
```

### Whisper Optimization

Use `faster-whisper` with quantization (already configured):
- 4x faster than regular Whisper
- Lower memory usage
- Same accuracy

### mem0 Optimization

```bash
# Increase mem0 replicas for read-heavy workload
kubectl scale deployment/mem0 -n homelab --replicas=4
```

---

## 🎯 Next Steps

### Phase 1: Basic Usage (Week 1)
- [ ] Deploy all services
- [ ] Test Spanish conversations
- [ ] Verify memory persistence
- [ ] Test voice input

### Phase 2: RAG Integration (Week 2)
- [ ] Upload documents to Qdrant via LobeChat
- [ ] Configure knowledge base
- [ ] Test document Q&A with memory

### Phase 3: Mobile Access (Week 2)
- [ ] Configure PWA settings
- [ ] Install on mobile device
- [ ] Test voice input on mobile

### Phase 4: Advanced Features (Week 3)
- [ ] Add custom tools/plugins
- [ ] Integrate with N8n workflows
- [ ] Set up monitoring dashboards

---

## 📚 Resources

### Documentation
- **LobeChat**: https://lobehub.com/docs
- **Whisper**: https://github.com/openai/whisper
- **mem0**: https://docs.mem0.ai/
- **Qdrant**: https://qdrant.tech/documentation/

### Monitoring
- **Grafana**: http://100.81.76.55:30300
- **Prometheus**: http://100.81.76.55:30090

### Service Endpoints
- **LobeChat**: http://100.81.76.55:30910
- **Whisper**: http://100.81.76.55:30900
- **mem0**: Internal only (via middleware)
- **Ollama**: http://100.72.98.106:11434

---

## 🤝 Support

If you encounter issues:

1. Check logs: `kubectl logs -n homelab -l app=<service> -f`
2. Verify services: `kubectl get pods -n homelab`
3. Test connectivity: `kubectl exec` + `curl`
4. Review troubleshooting section above

---

## ✅ Deployment Checklist

```
[ ] Pre-deployment
    [ ] Verify mem0 running
    [ ] Verify Qdrant running
    [ ] Verify Ollama accessible
    [ ] Verify PostgreSQL running

[ ] Build Phase
    [ ] Build middleware Docker image
    [ ] Verify image available in cluster

[ ] Deployment Phase
    [ ] Deploy Whisper STT
    [ ] Deploy mem0 Middleware
    [ ] Deploy LobeChat
    [ ] Verify all pods running

[ ] Testing Phase
    [ ] Test Whisper STT (Spanish)
    [ ] Test middleware mem0 connection
    [ ] Test LobeChat UI access
    [ ] Test memory persistence
    [ ] Test voice input

[ ] Production Ready
    [ ] Enable authentication
    [ ] Configure TLS
    [ ] Set up monitoring alerts
    [ ] Create backup strategy
    [ ] Document user guide
```

**Ready to deploy!** 🚀
