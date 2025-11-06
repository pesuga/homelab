# Service Endpoints Quick Reference

**Last Updated**: 2025-11-04

Quick reference for all homelab service URLs and ports.

## 🌐 DNS Access

**Tailscale MagicDNS + CoreDNS Split DNS is now active!**

All `*.pesulabs.net` domains resolve to `100.81.76.55` automatically on Tailscale devices.

- **DNS Server**: `100.81.76.55:53` (via socat forwarder → CoreDNS NodePort 30053)
- **Works On**: Any device connected to Tailscale (laptop, mobile, desktop)
- **No Configuration Needed**: Automatic via Tailscale split DNS

---

## 🎯 Primary Services

### LobeChat (AI Chat Interface)
- **DNS URL**: http://chat.homelab.pesulabs.net/chat ⭐ (Recommended)
- **NodePort URL**: http://100.81.76.55:30910
- **Internal**: http://lobechat.homelab.svc.cluster.local:3210
- **Port**: 30910 (NodePort)
- **Status**: ✅ Running (DNS + Ingress working)
- **Use**: AI chat interface with Ollama integration, voice input support

### Whisper (Speech-to-Text)
- **URL**: http://100.81.76.55:30900
- **API Docs**: http://100.81.76.55:30900/docs (Swagger UI)
- **Internal**: http://whisper.homelab.svc.cluster.local:9000
- **Port**: 30900 (NodePort)
- **Status**: ✅ Running (Medium model, CPU-based)
- **Use**: Audio transcription for voice workflows

### N8n (Workflow Automation)
- **DNS URL**: http://n8n.homelab.pesulabs.net ⭐ (Recommended)
- **NodePort URL**: http://100.81.76.55:30678
- **Internal**: http://n8n.homelab.svc.cluster.local:5678
- **Port**: 30678 (NodePort)
- **Credentials**: admin / admin123
- **Status**: ✅ Running (DNS + Ingress working)
- **Use**: Workflow automation and integration platform

### Flowise (LLM Flows)
- **DNS URL**: http://flowise.homelab.pesulabs.net ⭐ (Recommended)
- **NodePort URL**: http://100.81.76.55:30850
- **Internal**: http://flowise.homelab.svc.cluster.local:3000
- **Port**: 30850 (NodePort)
- **Credentials**: admin / flowise2025
- **Status**: ✅ Running (DNS + Ingress working)
- **Use**: Visual LLM workflow builder

---

## 📊 Monitoring & Observability

### Grafana (Dashboards)
- **DNS URL**: http://grafana.homelab.pesulabs.net ⭐ (Recommended)
- **NodePort URL**: http://100.81.76.55:30300
- **Internal**: http://grafana.homelab.svc.cluster.local:3000
- **Port**: 30300 (NodePort)
- **Credentials**: admin / admin123
- **Status**: ✅ Running (DNS + Ingress working)
- **Dashboards**:
  - Homelab Infrastructure - Dual Node
  - Loki Logs (Explore tab)

### Prometheus (Metrics)
- **DNS URL**: http://prometheus.homelab.pesulabs.net ⭐ (Recommended)
- **NodePort URL**: http://100.81.76.55:30090
- **Internal**: http://prometheus.homelab.svc.cluster.local:9090
- **Port**: 30090 (NodePort)
- **Status**: ✅ Running (DNS + Ingress working)
- **Use**: Metrics collection and storage

### Loki (Log Aggregation)
- **URL**: http://100.81.76.55:30314
- **Internal**: http://loki.homelab.svc.cluster.local:3100
- **Port**: 30314 (NodePort)
- **Status**: ✅ Running
- **Use**: Log aggregation (query via Grafana)

### Homelab Dashboard
- **DNS URL**: http://dash.pesulabs.net ⭐ (Recommended)
- **NodePort URL**: http://100.81.76.55:30800
- **Internal**: http://homelab-dashboard.homelab.svc.cluster.local:80
- **Port**: 30800 (NodePort)
- **Credentials**: admin / ChangeMe!2024#Secure
- **Status**: ✅ Running (DNS + Ingress working)
- **Use**: Unified landing page for all services

---

## 💾 Databases & Storage

### PostgreSQL
- **Internal**: postgres.homelab.svc.cluster.local:5432
- **Port**: 5432 (ClusterIP only)
- **Database**: homelab
- **User**: homelab
- **Status**: ✅ Running
- **Storage**: 10Gi PVC
- **Used By**: N8n, Flowise

### Redis
- **Internal**: redis.homelab.svc.cluster.local:6379
- **Port**: 6379 (ClusterIP only)
- **Status**: ✅ Running
- **Storage**: Ephemeral (AOF enabled)
- **Used By**: N8n job queue

### Qdrant (Vector Database)
- **HTTP**: http://100.81.76.55:30633
- **gRPC**: 100.81.76.55:30634
- **Internal HTTP**: http://qdrant.homelab.svc.cluster.local:6333
- **Internal gRPC**: qdrant.homelab.svc.cluster.local:6334
- **Port**: 30633 (HTTP), 30634 (gRPC)
- **Status**: ✅ Running
- **Storage**: 20Gi PVC
- **Use**: Vector similarity search for RAG

### Mem0 (AI Memory Layer)
- **URL**: http://100.81.76.55:30820
- **Internal**: http://mem0.homelab.svc.cluster.local:8000
- **Port**: 30820 (NodePort)
- **Status**: ✅ Running
- **Use**: AI memory layer (uses Qdrant + Ollama embeddings)

---

## 🤖 LLM Services (Compute Node)

### Ollama (LLM Inference)
- **URL**: http://100.72.98.106:11434
- **API**: http://100.72.98.106:11434/api
- **Status**: ⏳ Not yet deployed
- **Location**: Compute node (pesubuntu)
- **GPU**: AMD RX 7800 XT (16GB VRAM)
- **Use**: Local LLM inference

### LiteLLM (API Router)
- **URL**: http://100.72.98.106:8000
- **API**: http://100.72.98.106:8000/v1
- **Status**: ⏳ Not yet deployed
- **Location**: Compute node (pesubuntu)
- **Use**: OpenAI-compatible API gateway

---

## ❌ Disabled Services

### Open WebUI
- **URL**: http://100.81.76.55:30080 (404 - scaled to 0)
- **Status**: ❌ Scaled down (0/0 replicas)
- **Note**: Use LobeChat instead (port 30910)

---

## 📝 Quick Access Commands

### Test Service Connectivity
```bash
# LobeChat
curl -I http://100.81.76.55:30910

# Whisper API
curl http://100.81.76.55:30900/docs

# N8n
curl -I http://100.81.76.55:30678

# Grafana
curl -I http://100.81.76.55:30300

# Prometheus
curl http://100.81.76.55:30090/-/healthy
```

### Internal Service Resolution (from pods)
```bash
# Test from inside cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- sh

# Inside pod:
curl http://whisper.homelab.svc.cluster.local:9000/
curl http://postgres.homelab.svc.cluster.local:5432
curl http://redis.homelab.svc.cluster.local:6379
```

---

## 🌐 Network Information

### Service Node (asuna)
- **Local IP**: 192.168.8.185
- **Tailscale IP**: 100.81.76.55
- **K3s Version**: v1.33.5
- **OS**: Ubuntu 24.04.3 LTS

### Compute Node (pesubuntu)
- **Local IP**: 192.168.8.xxx (to be confirmed)
- **Tailscale IP**: 100.72.98.106
- **OS**: Ubuntu 25.10 (Questing Quetzal)
- **GPU**: AMD RX 7800 XT (16GB VRAM)

---

## 🔧 Common Tasks

### Check All Service Status
```bash
kubectl get all -n homelab
```

### View Service Logs
```bash
kubectl logs -n homelab -l app=whisper -f
kubectl logs -n homelab -l app=lobechat -f
kubectl logs -n homelab -l app=n8n -f
```

### Restart a Service
```bash
kubectl rollout restart deployment/whisper -n homelab
kubectl rollout restart deployment/lobechat -n homelab
```

### Check Resource Usage
```bash
kubectl top pods -n homelab
kubectl top nodes
```

---

**Note**: All external URLs use Tailscale IP (100.81.76.55) for secure access from anywhere on your Tailscale network.
