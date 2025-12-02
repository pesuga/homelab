# Service Inventory

**Last Updated**: 2025-11-26
**Total Services**: [VERIFIED 2025-11-26] 8 critical services + support infrastructure

---

## Critical Services

### Homelab Dashboard

**Status**: ⚠️ Service Orphaned [VERIFIED 2025-11-26]
**Version**: N/A (No deployment exists)
**Type**: Frontend (React SPA)

**Endpoints**:
- **Production**: https://dash.pesulabs.net (404 - Not Found)
- **NodePort**: http://100.81.76.55:30800 (Unreachable)

**Deployment**:
- Namespace: `homelab`
- Service: `homelab-dashboard` (NodePort 30800)
- **Issue**: Service exists but no deployment/pods found
- **Status**: Orphaned service - needs deployment or cleanup

**Technology**:
- Frontend: React 18, TypeScript, Vite (presumed from project structure)
- Hosting: Static files via nginx (intended)

**Purpose**: Central dashboard for homelab service status and quick links

**Last Deployment**: Never deployed or removed
**Health Status**: ⚠️ Service unreachable - deployment missing

---

### N8n Workflow Automation

**Status**: ✅ Active [VERIFIED 2025-12-02]
**Version**: n8nio/n8n:latest
**Type**: Workflow Automation Platform

**Endpoints**:
- **Production**: https://n8n.fa.pesulabs.net
- **Internal**: `n8n.homelab.svc:80` (K8s ClusterIP: 10.43.166.66)
- **Health Check**: https://n8n.fa.pesulabs.net/

**Deployment**: [VERIFIED 2025-12-02]
- Namespace: `homelab`
- Pod: `n8n-6cdb74c9f6-kvksf` (1/1 Running, 3 restarts)
- IngressRoute: `n8n`
- Replicas: 1
- ConfigMap: `n8n-config` (environment configuration)
- PVC: `n8n-pvc` (5Gi persistent storage)

**Technology**:
- Platform: N8n
- Database: PostgreSQL (homelab namespace, database: n8n)
- Storage: Persistent volume (local-path)

**Purpose**: Workflow automation and integration platform

**Last Deployment**: 2025-12-02 (ConfigMap fix applied)
**Health Status**: ✅ Pod Running, HTTP 200 OK

---

### Family Assistant (App)

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: 100.81.76.55:30500/family-assistant:latest
**Type**: Frontend Application

**Endpoints**:
- **App**: https://app.fa.pesulabs.net
- **Internal**: `family-assistant.family-assistant-app.svc:80` (K8s ClusterIP: 10.43.9.183)
- **NodePort**: `100.81.76.55:30080` (K8s NodePort: 10.43.40.50)
- **Health Check**: https://app.fa.pesulabs.net/health

**Deployment**: [VERIFIED 2025-11-26]
- Namespace: `family-assistant-app`
- Pods:
  - `family-assistant-5c5bd647d9-4k9h6` (1/1 Running)
  - `family-assistant-5c5bd647d9-5p4fh` (1/1 Running)
- Replicas: 2/2

**Technology**:
- Frontend: React (verified from image registry)
- Backend API: See Family API (Backend) section
- Features: AI chat interface, memory system, knowledge base

**Purpose**: AI-powered family assistant frontend application

**Last Deployment**: 2 days ago (from kubectl age)
**Health Status**: ✅ 2/2 Pods Running

---

### Family Assistant (Admin)

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: 100.81.76.55:30500/family-admin:v1.3.0
**Type**: Admin Frontend

**Endpoints**:
- **Admin**: https://admin.fa.pesulabs.net
- **Internal**: `family-admin.homelab.svc:3000` (K8s ClusterIP: 10.43.56.173)
- **Health Check**: https://admin.fa.pesulabs.net/

**Deployment**: [VERIFIED 2025-11-26]
- Namespace: `homelab`
- Pods:
  - `family-admin-98d88c878-hq9dt` (1/1 Running, 1 restart)
  - `family-admin-98d88c878-ng89t` (1/1 Running, 1 restart)
- IngressRoute: `family-assistant-admin`
- Replicas: 2/2

**Technology**:
- Frontend: React 18, TypeScript, Next.js
- Features: Profile management, knowledge base admin
- Image: `100.81.76.55:30500/family-admin:v1.3.0`

**Purpose**: Administrative interface for Family Assistant

**Last Deployment**: 2 days ago (from kubectl age)
**Health Status**: ✅ 2/2 Pods Running (1 restart each after 42h uptime)

---

### Family API (Backend)

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: 100.81.76.55:30500/family-assistant:v2.2.0-enhanced
**Type**: Backend API

**Endpoints**:
- **API**: https://api.fa.pesulabs.net
- **Internal**: `family-assistant-backend.homelab.svc:8001` (K8s ClusterIP: 10.43.116.179)
- **NodePort**: `100.81.76.55:30801` (direct access)
- **Health Check**: https://api.fa.pesulabs.net/health

**Deployment**: [VERIFIED 2025-11-26]
- Namespace: `homelab`
- Pod: `family-assistant-backend-6f7cc74569-vs9x5` (1/1 Running, 1 restart)
- Replicas: 1

**Technology**:
- Backend: Python 3.12, FastAPI
- Database: PostgreSQL (homelab namespace)
- Features: Authentication, memory system, knowledge base, AI integration
- Ports: 8001 (main), 8123, 8008

**Purpose**: Backend API for Family Assistant applications

**Last Deployment**: 2 days ago (from kubectl age)
**Health Status**: ✅ Pod Running

---

### LlamaCpp (Native)

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: Configurable (Kimi-VL / Mistral-7B)
**Type**: LLM Inference Engine

**Endpoints**:
- **API**: http://100.86.122.109:8081
- **Internal K8s**: `llamacpp-service.default.svc:8081` (K8s ClusterIP: 10.43.213.114)
- **Health Check**: http://100.86.122.109:8081/health

**Deployment**:
- Type: Native systemd service (not Kubernetes pod)
- Node: Compute node (pesubuntu - 100.86.122.109)
- Service: `llamacpp-configurable.service`
- GPU: AMD RX 7800 XT (1 layer, Vulkan backend)

**Technology**:
- Platform: llama.cpp with configurable wrapper
- GPU Acceleration: Vulkan (GGML_VULKAN_DEVICE=0)
- Models: Kimi-VL (multimodal, 8K context), Mistral-7B-OpenOrca (text, 16K context)
- Performance: ~50 tps (prompt), ~30 tps (generation)

**Purpose**: Local LLM inference with GPU acceleration and model switching

**Last Update**: 2025-11-22 (llama.cpp configuration)
**Health Status**: ✅ Service Running (see LLAMACPP_CONFIGURATION.md for details)

---

## Monitoring Stack

### Prometheus

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: prom/prometheus:v2.54.1
**Type**: Metrics Collection & Alerting

**Endpoints**:
- **UI**: http://100.81.76.55:30190
- **Internal**: `prometheus-svc.homelab.svc:9090` (K8s ClusterIP: 10.43.16.14)
- **Health**: http://100.81.76.55:30190/-/healthy

**Deployment**: [VERIFIED 2025-11-26]
- Namespace: `homelab`
- Pod: `prometheus-85c79974-nkls4` (1/1 Running, 8 days uptime)
- Replicas: 1/1
- Storage: 10Gi PVC (15 days retention)

**Technology**:
- Platform: Prometheus 2.54.1
- Scrape Targets: K8s API, nodes, pods, cAdvisor, compute node GPU metrics
- Retention: 15 days

**Purpose**: Metrics collection, monitoring, and alerting for homelab infrastructure

**Last Deployment**: 8 days ago
**Health Status**: ✅ Healthy

---

### Loki

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: grafana/loki:2.9.3
**Type**: Log Aggregation

**Endpoints**:
- **HTTP**: http://100.81.76.55:30314
- **Internal**: `loki.homelab.svc:3100` (K8s ClusterIP: 10.43.177.96)
- **gRPC**: `loki.homelab.svc:9096`
- **Health**: http://100.81.76.55:30314/ready

**Deployment**: [VERIFIED 2025-11-26]
- Namespace: `homelab`
- Pod: `loki-0` (StatefulSet, 1/1 Running, 27 days uptime)
- Replicas: 1/1
- Storage: 20Gi PVC (7 days retention)

**Technology**:
- Platform: Loki 2.9.3
- Schema: v11 with boltdb-shipper
- Storage: Filesystem-based
- Retention: 7 days (168h)

**Purpose**: Centralized log aggregation and querying for homelab services

**Last Deployment**: 27 days ago
**Health Status**: ✅ Ready

---

### Grafana

**Status**: ❌ Deprecated [2025-11-26]
**Reason**: Visualization features integrated into Family Assistant Admin dashboard

**Migration**:
- Metrics visualization → Family Assistant Admin
- Dashboard creation → Family Assistant Admin
- Data sources: Prometheus (metrics), Loki (logs), K8s API (direct)

---

## Support Services

### Authentik (SSO/Identity)

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: ghcr.io/goauthentik/server:2024.2.1
**Type**: Identity Provider & SSO

**Endpoints**:
- **Web**: https://auth.pesulabs.net
- **Server Internal**: `authentik-server.authentik.svc:9000` (K8s ClusterIP: 10.43.166.212)
- **Proxy Internal**: `authentik-proxy.authentik.svc:9000` (K8s ClusterIP: 10.43.200.77)

**Deployment**: [VERIFIED 2025-11-26]
- Namespace: `authentik`
- Pods:
  - `authentik-server-6bbf7c7bb8-pbgph` (1/1 Running, 1 restart)
  - `authentik-worker-7cff6b4c5-zxdrk` (1/1 Running, 1 restart)
  - `authentik-proxy-84f75d96cb-4wvsm` (1/1 Running, 1 restart)
- PostgreSQL: `authentik-postgresql-666f6dfb9c-fzcg6` (1/1 Running)
- Redis: `authentik-redis-76df44d899-ptxlk` (1/1 Running)

**Technology**:
- Platform: Authentik
- Database: PostgreSQL (authentik namespace)
- Cache: Redis (authentik namespace)
- Protocol: OAuth2/OIDC, Proxy Provider

**Purpose**: Centralized authentication and SSO for all services

**Last Deployment**: 3 days ago
**Health Status**: ✅ All pods running (see AUTHENTIK_INTEGRATION.md for integration guide)

---

### PostgreSQL (Homelab)

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: PostgreSQL 16 (postgres:16-alpine)
**Type**: Database

**Deployment**: [VERIFIED 2025-11-26]
- Namespace: `homelab`
- Pod: `postgres-0` (StatefulSet, 1/1 Running, 21 days uptime)
- Internal: `postgres.homelab.svc:5432` (K8s ClusterIP: 10.43.239.209)
- Type: StatefulSet
- Storage: Persistent volume

**Purpose**: Primary database for Family API, N8n workflows, and homelab services

**Health Status**: ✅ Running (21 days uptime)

---

### Redis (Homelab)

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: Redis 7 (redis:7-alpine)
**Type**: Cache & Message Queue

**Deployment**: [VERIFIED 2025-11-26]
- Namespace: `homelab`
- Pod: `redis-cf7487ccc-pr975` (1/1 Running, 19 days uptime)
- Internal: `redis.homelab.svc:6379` (K8s ClusterIP: 10.43.241.212)

**Purpose**: Caching layer and message queue for services

**Health Status**: ✅ Running (19 days uptime)

---

### Qdrant (Vector Database)

**Status**: ✅ Active [VERIFIED 2025-11-26]
**Version**: v1.12.5
**Type**: Vector Database

**Endpoints**:
- **Internal**: `qdrant.homelab.svc:6333` (K8s ClusterIP: 10.43.153.251)
- **NodePort**: `100.81.76.55:30633` (K8s NodePort: 10.43.138.141)

**Deployment**: [VERIFIED 2025-11-26]
- Namespace: `homelab`
- Pod: `qdrant-0` (StatefulSet, 1/1 Running, 14 days uptime)
- Ports: 6333 (HTTP), 6334 (gRPC)

**Purpose**: Vector storage for AI embeddings and semantic search

**Health Status**: ✅ Running (14 days uptime)

---

### Mem0 (Memory Service)

**Status**: ✅ Active [VERIFIED 2025-12-02]
**Version**: python:3.11-slim with runtime dependencies
**Type**: AI Memory Management

**Endpoints**:
- **Internal**: `mem0.homelab.svc:8080` (K8s ClusterIP: 10.43.105.77)
- **Health Check**: http://mem0.homelab.svc:8080/health

**Deployment**: [VERIFIED 2025-12-02]
- Namespace: `homelab`
- Pod: `mem0-647cbd5dc6-twkrf` (1/1 Running)
- ConfigMap: `mem0-config` (environment configuration)
- ConfigMap: `mem0-source-code` (FastAPI application source)
- Dependencies: Installed at runtime (fastapi, uvicorn, mem0ai, pydantic, qdrant-client, redis, python-dotenv)

**Technology**:
- Platform: Mem0 API (FastAPI wrapper)
- Base Image: python:3.11-slim
- Vector DB: Qdrant integration (qdrant.homelab.svc.cluster.local:6333)
- LLM: OpenAI-compatible endpoint (mistral:7b-instruct-q4_K_M)
- Embeddings: text-embedding-3-small (OpenAI-compatible)
- Collection: mem0_memories

**Purpose**: Long-term memory management for AI assistants with semantic search

**Last Deployment**: 2025-12-02 (Fixed image configuration from nginx to Python)
**Health Status**: ✅ Running, Health endpoint responding 200 OK

---

## Service Dependencies

```
Dashboard
  └─ (no dependencies)

N8n
  └─ PostgreSQL (N8n)

Family Assistant App
  ├─ PostgreSQL (Family API)
  └─ Ollama (for AI features)

Family Assistant Admin
  └─ Family Assistant App API

Ollama
  └─ (no dependencies)
```

---

## Service Status Summary [VERIFIED 2025-12-02]

| Service | Status | Endpoint | Health Check |
|---------|--------|----------|--------------|
| Homelab Dashboard | ⚠️ Orphaned | https://dash.pesulabs.net (404) | N/A |
| N8n | ✅ Active | https://n8n.fa.pesulabs.net | / |
| Family App | ✅ Active | https://app.fa.pesulabs.net | /health |
| Family Admin | ✅ Active | https://admin.fa.pesulabs.net | / |
| Family API | ✅ Active | https://api.fa.pesulabs.net | /health |
| LlamaCpp | ✅ Active | http://100.86.122.109:8081 | /health |
| Authentik | ✅ Active | https://auth.pesulabs.net | / |
| PostgreSQL | ✅ Active | Internal | - |
| Redis | ✅ Active | Internal | - |
| Qdrant | ✅ Active | Internal | - |
| Mem0 | ✅ Active | Internal | /health |
| Prometheus | ✅ Active | http://100.75.194.1:30190 | /-/healthy |
| Loki | ✅ Active | http://100.75.194.1:30314 | /ready |

---

## Recent Service Changes

### 2025-12-02: N8n and Mem0 Fixes
**N8n Deployment Fix**:
- Created missing ConfigMap `n8n-config` with required environment variables
- Created PVC `n8n-pvc` for persistent storage (5Gi)
- Created database `n8n` in PostgreSQL
- Status: ✅ Fixed - Pod running successfully

**Mem0 Deployment Fix**:
- Changed base image from `nginx:alpine` to `python:3.11-slim`
- Implemented runtime dependency installation (fastapi, uvicorn, mem0ai, etc.)
- Fixed CrashLoopBackOff issue caused by incorrect container image
- Status: ✅ Fixed - Pod running with health endpoint responding

### 2025-11-23: Family Assistant v1.1.0
- Added comprehensive Knowledge Base management
- Profile editing features
- Image: family-api:v1.1.0

### 2025-11-15: Mixed Content Fix
- Updated API routes to use HTTPS
- Fixed dashboard HTTPS issues

---

## Planned Service Changes

- [ ] Add health check endpoints to all services
- [ ] Implement service versioning strategy
- [ ] Add automated health monitoring
- [ ] Document backup and restore procedures

---

**Maintenance Notes**:
- Use /verify-claim to validate service status before updating this file
- Update version information after deployments
- Record significant service changes with timestamps
- Run service discovery monthly to keep inventory accurate
