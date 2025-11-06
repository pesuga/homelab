# 🎙️ Whisper Speech-to-Text Deployment Guide

**Last Updated**: 2025-11-03
**Status**: Planning Phase

---

## 📋 Overview

Deploy OpenAI Whisper for speech-to-text transcription on the homelab with AMD RX 7800 XT GPU acceleration.

### Deployment Target
- **Node**: Service Node (asuna, 192.168.8.185) via K3s
- **GPU Access**: Remote GPU acceleration via compute node (future enhancement)
- **Initial Deployment**: CPU-based inference on service node
- **Storage**: Kubernetes PVC for model cache

---

## 🎯 Recommended Solution: Faster-Whisper with ROCm

### Selected Image: `beecave-homelab/insanely-fast-whisper-rocm`

**Why This Choice:**
- ✅ Built specifically for AMD GPUs with ROCm 6.1 support
- ✅ Optimized "insanely-fast-whisper" implementation
- ✅ Docker Compose ready (easily convertible to K8s)
- ✅ Active maintenance and homelab-focused
- ✅ Supports RX 7800 XT (Navi 32, gfx1101)

**Alternative Options:**
1. `fyhertz/rocm-wyoming-whisper` - Wyoming protocol for Home Assistant integration
2. `jjajjara/rocm-whisper-api` - REST API focused
3. `whisper.cpp` with Vulkan - Cross-platform but less optimized for AMD

---

## 💾 Resource Requirements

### Model Resource Analysis

| Model Size | VRAM (GPU) | RAM (CPU) | Storage | Speed | Accuracy |
|-----------|------------|-----------|---------|-------|----------|
| **tiny** | 1GB | 1GB | ~75MB | Fastest | Good |
| **base** | 1GB | 1GB | ~150MB | Very Fast | Better |
| **small** | 2GB | 2GB | ~500MB | Fast | Good |
| **medium** | 3GB | 3-4GB | ~1.5GB | Moderate | Very Good |
| **large-v3** | 5GB | 5-6GB | ~3GB | Slower | Best |

### Recommended Starting Point: **Medium Model**

**Rationale:**
- Service node has 8GB RAM (can handle medium model)
- Excellent accuracy/performance balance
- ~1.5GB storage footprint is manageable
- Can run on CPU initially, GPU later

### Pod Resource Allocation (Phase 1: CPU-Only)

```yaml
resources:
  requests:
    cpu: 1000m        # 1 CPU core minimum
    memory: 3Gi       # 3GB for medium model + overhead
  limits:
    cpu: 2000m        # 2 CPU cores max
    memory: 4Gi       # 4GB max to prevent OOM
```

### Pod Resource Allocation (Phase 2: GPU-Accelerated)

```yaml
resources:
  requests:
    cpu: 500m         # Less CPU needed with GPU
    memory: 2Gi       # Reduced RAM when using VRAM
  limits:
    cpu: 1000m
    memory: 3Gi
# GPU passthrough configuration TBD
```

---

## 🏗️ Deployment Architecture

### Phase 1: CPU-Based Deployment (Current)

```
User/LobeChat
    ↓
N8n Workflow (Port 30678)
    ↓
Whisper Service (ClusterIP)
    ↓
Whisper Pod (CPU inference)
    ↓
Model Storage (PVC 5Gi)
```

### Phase 2: GPU-Accelerated (Future)

```
User/LobeChat
    ↓
N8n Workflow
    ↓
Whisper Service (ClusterIP + NodePort)
    ↓
Whisper Pod (GPU passthrough)
    ↓
Compute Node GPU (via device mapping)
    ↓
Model Storage (PVC 5Gi)
```

---

## 🧪 Testing Strategy

### 1. Internal Cluster Testing (kubectl exec)

```bash
# Test from inside the cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- sh

# Inside the pod, test Whisper API
curl -X POST http://whisper.homelab.svc.cluster.local:9000/transcribe \
  -F "audio=@test.wav" \
  -F "language=en" \
  -F "model=medium"
```

### 2. Service Node Testing (NodePort)

```bash
# Test from service node itself
curl -X POST http://localhost:30900/transcribe \
  -F "audio=@test.wav" \
  -F "language=en"
```

### 3. External Testing (via Tailscale)

```bash
# Test from any device on Tailscale network
curl -X POST http://100.81.76.55:30900/transcribe \
  -F "audio=@test.wav" \
  -F "language=en"
```

### 4. N8n Workflow Integration Testing

**N8n Workflow Steps:**
1. HTTP Request node configured for Whisper endpoint
2. Binary file upload (audio file)
3. Response parsing (JSON transcription)
4. Error handling and retry logic

### 5. LobeChat Integration Testing

**Test Flow:**
1. User records voice message in LobeChat
2. LobeChat sends audio to N8n webhook
3. N8n forwards to Whisper service
4. Transcription returned to LobeChat
5. LLM processes transcribed text

---

## 📱 Development Client Choice: LobeChat vs Telegram

### Analysis Summary

| Feature | LobeChat | Telegram Bot |
|---------|----------|--------------|
| **Setup Complexity** | Low (already deployed) | Medium (bot API + webhook) |
| **Voice Input** | ✅ Built-in | ✅ Native support |
| **LLM Integration** | ✅ Native (Ollama) | ⚠️ Manual integration |
| **Multi-Model Support** | ✅ Yes | ❌ Custom implementation |
| **Knowledge Base** | ✅ Yes | ❌ Custom implementation |
| **Development Speed** | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐ Slower |
| **User Experience** | Modern web UI | Native mobile app |
| **Production Path** | Different (web vs messaging) | ✅ Direct (Telegram is target) |
| **Debugging** | ✅ Easy (browser devtools) | ⚠️ Harder (API logs) |

### Recommendation: **Hybrid Approach**

**Development Phase: Use LobeChat**
- Faster iteration cycles
- Better debugging tools
- Already deployed and integrated with Ollama
- Built-in voice recording and transcription UI
- Can test full agent workflow immediately

**Production Phase: Deploy to Telegram**
- Build Telegram bot using lessons from LobeChat
- Reuse N8n workflows and Whisper integration
- Leverage LobeChat's proven architecture
- Transition when agent behavior is stable

### Why This Approach Works

1. **Speed to Market**: Start testing "Tana" agent today with LobeChat
2. **Risk Reduction**: Validate agent logic before committing to Telegram
3. **Code Reuse**: N8n workflows work for both platforms
4. **Learning Path**: Understand agent behavior before building custom bot
5. **Flexibility**: Can support both web and messaging interfaces

---

## 📝 Deployment Manifest (Phase 1: CPU-Based)

### whisper-deployment.yaml

```yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: whisper-models-pvc
  namespace: homelab
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: local-path
---
apiVersion: v1
kind: Service
metadata:
  name: whisper
  namespace: homelab
  labels:
    app: whisper
spec:
  type: NodePort
  ports:
    - port: 9000
      targetPort: 9000
      nodePort: 30900
      protocol: TCP
      name: whisper-api
  selector:
    app: whisper
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whisper
  namespace: homelab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: whisper
  template:
    metadata:
      labels:
        app: whisper
    spec:
      containers:
      - name: whisper
        # Using faster-whisper for CPU efficiency
        image: onerahmet/openai-whisper-asr-webservice:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 9000
          protocol: TCP
        env:
        - name: ASR_MODEL
          value: "medium"  # medium model for balanced performance
        - name: ASR_ENGINE
          value: "faster_whisper"  # CPU-optimized engine
        resources:
          requests:
            cpu: 1000m
            memory: 3Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        volumeMounts:
        - name: models-storage
          mountPath: /root/.cache/whisper
        readinessProbe:
          httpGet:
            path: /
            port: 9000
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /
            port: 9000
          initialDelaySeconds: 60
          periodSeconds: 30
      volumes:
      - name: models-storage
        persistentVolumeClaim:
          claimName: whisper-models-pvc
```

---

## 🚀 Deployment Steps

### Step 1: Create Deployment Manifest

```bash
# Save the manifest above to:
mkdir -p infrastructure/kubernetes/ai-services
nano infrastructure/kubernetes/ai-services/whisper-deployment.yaml
```

### Step 2: Deploy to Cluster

```bash
# Deploy Whisper service
kubectl apply -f infrastructure/kubernetes/ai-services/whisper-deployment.yaml

# Verify deployment
kubectl get pods -n homelab -l app=whisper
kubectl get svc -n homelab whisper
```

### Step 3: Wait for Model Download

```bash
# Watch pod logs (first startup downloads model)
kubectl logs -n homelab -l app=whisper -f

# This may take 5-10 minutes for medium model download
```

### Step 4: Test Service

```bash
# Get a test audio file
wget https://github.com/openai/whisper/raw/main/tests/jfk.flac -O /tmp/test.flac

# Test from service node
curl -X POST http://100.81.76.55:30900/asr \
  -F "audio_file=@/tmp/test.flac" \
  -F "task=transcribe" \
  -F "language=en"
```

### Step 5: Integrate with LobeChat

**LobeChat Configuration:**
1. Access LobeChat at http://100.81.76.55:30080
2. Create new agent workflow
3. Configure voice input settings
4. Point transcription endpoint to Whisper service
5. Test voice recording → transcription → LLM flow

---

## 🔧 Configuration Options

### Environment Variables

```yaml
env:
  - name: ASR_MODEL
    value: "medium"  # Options: tiny, base, small, medium, large-v3

  - name: ASR_ENGINE
    value: "faster_whisper"  # Options: openai_whisper, faster_whisper

  - name: ASR_MODEL_PATH
    value: "/root/.cache/whisper"  # Model cache location
```

### API Endpoints

**Transcription Endpoint:**
```bash
POST /asr
- audio_file: Audio file (WAV, MP3, FLAC, etc.)
- task: "transcribe" or "translate"
- language: ISO language code (optional, auto-detect)
- output: "json" or "txt"
```

**Health Check Endpoint:**
```bash
GET /
- Returns: API status and loaded model info
```

---

## 📊 Monitoring Integration

### Prometheus Metrics (Future)

```yaml
# Add to whisper deployment
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9000"
  prometheus.io/path: "/metrics"
```

### Grafana Dashboard

**Key Metrics to Track:**
- Transcription requests per minute
- Average transcription time
- Model load time
- Memory usage (RAM)
- CPU utilization
- Error rate

---

## 🔄 Migration Path to GPU

### Phase 2: GPU Acceleration (Future)

**Requirements:**
1. GPU node selection (compute node)
2. ROCm device plugin for K3s
3. Device mapping configuration
4. Image swap to ROCm-compatible version

**Deployment Changes:**

```yaml
# Add to pod spec
nodeSelector:
  gpu: amd-rx7800xt

resources:
  limits:
    amd.com/gpu: 1  # Request 1 AMD GPU

# Update image
image: beecave-homelab/insanely-fast-whisper-rocm:latest

# Add device mounts
volumeMounts:
  - name: dri
    mountPath: /dev/dri
  - name: kfd
    mountPath: /dev/kfd

volumes:
  - name: dri
    hostPath:
      path: /dev/dri
  - name: kfd
    hostPath:
      path: /dev/kfd
```

---

## 🎯 Success Criteria

### Phase 1 (CPU-Based) Completion

- ✅ Whisper pod deployed and running
- ✅ Medium model downloaded and loaded
- ✅ API responds to test requests
- ✅ Transcription accuracy > 90% for clear audio
- ✅ N8n workflow can call Whisper API
- ✅ LobeChat can use Whisper for voice input
- ✅ Monitoring shows healthy metrics

### Phase 2 (GPU-Accelerated) Completion

- ⏳ GPU passthrough working
- ⏳ ROCm detects RX 7800 XT in pod
- ⏳ GPU utilization metrics available
- ⏳ Transcription speed > 5x faster than CPU
- ⏳ VRAM usage < 4GB for medium model

---

## 🔍 Troubleshooting

### Pod Won't Start

```bash
# Check pod status
kubectl describe pod -n homelab -l app=whisper

# Check logs
kubectl logs -n homelab -l app=whisper

# Common issues:
# - Insufficient memory (increase limits)
# - Model download timeout (wait longer)
# - PVC not bound (check storage)
```

### Slow Transcription

**CPU-Based Solutions:**
- Switch to smaller model (small or base)
- Increase CPU limits
- Use faster_whisper engine
- Optimize audio file size before upload

**GPU-Based Solutions:**
- Implement GPU acceleration (Phase 2)
- Use quantized models
- Batch processing for multiple files

### Memory Issues

```bash
# Check memory usage
kubectl top pod -n homelab whisper

# Solutions:
# - Switch to smaller model
# - Increase memory limits
# - Clear model cache
```

---

## 📚 Resources

### Documentation
- [OpenAI Whisper GitHub](https://github.com/openai/whisper)
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper)
- [Insanely-Fast-Whisper ROCm](https://github.com/beecave-homelab/insanely-fast-whisper-rocm)
- [Whisper ASR Webservice](https://github.com/ahmetoner/whisper-asr-webservice)

### Model Information
- [Whisper Model Card](https://github.com/openai/whisper/blob/main/model-card.md)
- [Performance Benchmarks](https://github.com/openai/whisper#available-models-and-languages)

### Integration Guides
- [N8n HTTP Request Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
- [LobeChat Voice Input](https://docs.lobehub.com/)

---

## 🎯 Next Steps

1. ✅ Create this deployment guide
2. ⏳ Create Whisper deployment manifest
3. ⏳ Deploy to K3s cluster
4. ⏳ Test basic transcription
5. ⏳ Integrate with N8n workflow
6. ⏳ Configure LobeChat voice input
7. ⏳ Test full "Tana" agent workflow
8. ⏳ Document lessons learned
9. ⏳ Plan Telegram bot migration
10. ⏳ Implement GPU acceleration (Phase 2)

---

**Status**: Ready for deployment
**Next Action**: Create deployment manifest and deploy to cluster
