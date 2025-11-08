# Homelab Service Inventory

## Overview

This document provides a comprehensive inventory of all services running in the PesuLabs Homelab cluster, including their current status, connection details, and health information. The inventory is based on real-time data from the homelab dashboard.

## Last Updated: 2025-11-03

---

## 🟢 Online Services (6/14)

### AI & Machine Learning
| Service | Status | URL | Port | Health Message | Access |
|---------|--------|-----|------|---------------|---------|
| **Ollama** | 🟢 Online | http://100.72.98.106:11434 | 11434 | HTTP 200 | Compute Node |
| **Qdrant** | 🟢 Online | http://100.81.76.55:30633 | 30633 | HTTP 200 | Service Node |
| **Mem0** | 🟢 Online | http://100.81.76.55:30880 | 30880 | HTTP 200 | Service Node |
| **Loki** | 🟢 Online | http://100.81.76.55:30314 | 30314 | HTTP 200 | Service Node |

### Databases & Storage
| Service | Status | URL | Port | Health Message | Access |
|---------|--------|-----|------|---------------|---------|
| **PostgreSQL** | 🟢 Online | postgres.homelab.svc.cluster.local | 5432 | No health endpoint | Internal Only |
| **Redis** | 🟢 Online | redis.homelab.svc.cluster.local | 6379 | No health endpoint | Internal Only |

---

## 🔴 Offline Services (6/14)

### Monitoring & Observability
| Service | Status | URL | Port | Health Message | Notes |
|---------|--------|-----|------|---------------|-------|
| **Grafana** | 🔴 Offline | https://grafana.homelab.pesulabs.net | 30300 | Connection error | Internal cluster network TLS issue |
| **Prometheus** | 🔴 Offline | https://prometheus.homelab.pesulabs.net | 30090 | Connection error | Internal cluster network TLS issue |

### AI & Machine Learning
| Service | Status | URL | Port | Health Message | Notes |
|---------|--------|-----|------|---------------|-------|
| **Open WebUI** | 🔴 Offline | https://webui.homelab.pesulabs.net | 30080 | Connection error | Disabled by user |
| **Flowise** | 🔴 Offline | https://flowise.homelab.pesulabs.net | 30850 | Connection error | Internal cluster network TLS issue |
| **LiteLLM** | 🔴 Offline | https://litellm.homelab.pesulabs.net | 8000 | HTTP 401 | Auth required |
| **LobeChat** | 🔴 Offline | https://chat.pesulabs.net | 30844 | Connection error | Service available |

### Automation & Workflows
| Service | Status | URL | Port | Health Message | Notes |
|---------|--------|-----|------|---------------|-------|
| **N8n** | 🔴 Offline | https://n8n.homelab.pesulabs.net | 30678 | Connection error | Internal cluster network TLS issue |
| **Whisper** | 🔴 Offline | https://whisper.homelab.pesulabs.net | 30900 | HTTP 404 | Health endpoint not found |

---

## 🔵 Unknown Services (2/14)

| Service | Status | URL | Port | Health Message | Notes |
|---------|--------|-----|------|---------------|-------|
| **PostgreSQL** | 🔵 Unknown | postgres.homelab.svc.cluster.local | 5432 | No health endpoint | Internal service |
| **Redis** | 🔵 Unknown | redis.homelab.svc.cluster.local | 6379 | No health endpoint | Internal service |

---

## Service Categories

### 🤖 AI & Machine Learning (7 services)
- **Online**: Ollama, Qdrant, Mem0 (3/7)
- **Offline**: Open WebUI, Flowise, LiteLLM, LobeChat (4/7)
- **Status**: 43% online

### 📊 Monitoring & Observability (2 services)
- **Online**: None (0/2)
- **Offline**: Grafana, Prometheus (2/2)
- **Status**: 0% online

### 🔄 Automation & Workflows (2 services)
- **Online**: None (0/2)
- **Offline**: N8n, Whisper (2/2)
- **Status**: 0% online

### 🗄️ Databases & Storage (3 services)
- **Online**: PostgreSQL, Redis (2/3)
- **Offline**: None (0/3)
- **Unknown**: PostgreSQL, Redis (internal services)
- **Status**: 67% online

---

## Network Architecture

### Two-Node Setup
- **Service Node** (asuna): 100.81.76.55 - K3s Kubernetes cluster
- **Compute Node** (pesubuntu): 100.72.98.106 - LLM inference with GPU

### Access Patterns
- **External Access**: via `pesulabs.net` subdomains or direct IP:port
- **Internal Access**: Kubernetes service names within the cluster
- **Tailscale**: Mesh VPN for secure inter-node communication

### Service Types
- **External Services**: Accessible via public URLs with TLS termination
- **Internal Services**: Only accessible within the Kubernetes cluster
- **Compute Services**: Running on GPU-enabled compute node

---

## Issues Identified

### 1. Internal Cluster Network TLS Issues (4 services)
- Grafana, Prometheus, N8n, Flowise showing "Connection error" from internal cluster
- **Root Cause**: Services can't reach external HTTPS endpoints from within K3s cluster
- **Impact**: Health monitoring fails, but external access works correctly
- **Investigation Needed**: Network routing or TLS termination issues within cluster

### 2. Authentication Issues (1 service)
- LiteLLM returning HTTP 401
- **Impact**: API access requires authentication, expected behavior

### 3. Health Endpoint Mismatches (1 service)
- Whisper returning HTTP 404 on health check
- **Impact**: Health monitoring not functioning properly, needs endpoint fix

### 4. Service Disabled (1 service)
- Open WebUI intentionally disabled due to resource usage
- **Status**: Expected behavior, no action needed

### 5. Dashboard Health Check Logic (FIXED)
- **Previously**: Dashboard was using external URLs with ports for health checks
- **Solution**: Added separate health_check_url field and logic
- **Result**: Health checking now uses correct port-specific URLs for external services

---

## Recommendations

### Immediate Actions
1. **Fix Internal Cluster Network TLS**: Investigate why services can't reach external HTTPS endpoints from within K3s cluster
2. **Fix Health Endpoints**: Update Whisper service configuration with correct health endpoint
3. **Authentication Review**: Configure proper authentication for LiteLLM API access

### Network Architecture
1. **Internal Service Access**: Implement service discovery or internal ingress for health checks
2. **Network Policy Review**: Check if network policies block outbound HTTPS connections
3. **Alternative Health Check Strategy**: Use internal URLs for health monitoring where possible

### Monitoring Improvements
1. **Internal Health Checks**: Add health endpoints for internal-only services
2. **Better Error Handling**: Improve error reporting for connection issues
3. **Status Categorization**: Distinguish between "offline" and "network unreachable" states
4. **Dual Health Checking**: Support both internal and external health check URLs

### Architecture Consistency
1. **Standardize URL Patterns**: Ensure consistent use of `pesulabs.net` subdomains without ports
2. **Health Endpoint Standardization**: Implement consistent health check endpoints across all services
3. **Documentation Updates**: Keep this inventory updated with service changes
4. **Dashboard Configuration**: Maintain separate display URLs and health check URLs in dashboard config

---

## Technical Details

### Service Endpoints Matrix
| Service | External URL | Internal URL | Health Endpoint | Status Port |
|---------|-------------|--------------|----------------|-------------|
| N8n | https://n8n.homelab.pesulabs.net:30678 | http://n8n.homelab.svc.cluster.local:5678 | /healthz | 30678 |
| Grafana | https://grafana.homelab.pesulabs.net:30300 | http://grafana.homelab.svc.cluster.local:3000 | /api/health | 30300 |
| Prometheus | https://prometheus.homelab.pesulabs.net:30090 | http://prometheus.homelab.svc.cluster.local:9090 | /-/healthy | 30090 |
| Flowise | https://flowise.homelab.pesulabs.net:30850 | http://flowise.homelab.svc.cluster.local:3000 | / | 30850 |
| Qdrant | http://100.81.76.55:30633 | http://qdrant.homelab.svc.cluster.local:6333 | /healthz | 30633 |
| Mem0 | http://100.81.76.55:30880 | http://mem0.homelab.svc.cluster.local:8000 | /health | 30880 |
| Loki | http://100.81.76.55:30314 | http://loki.homelab.svc.cluster.local:3100 | /ready | 30314 |
| Ollama | http://100.72.98.106:11434 | - | /api/version | 11434 |
| LiteLLM | http://100.72.98.106:8000 | - | /health | 8000 |
| Whisper | http://100.81.76.55:30900 | http://whisper.homelab.svc.cluster.local:3000 | /health | 30900 |
| LobeChat | https://chat.pesulabs.net | http://lobechat.homelab.svc.cluster.local:3000 | /api/health | 30844 |
| Open WebUI | https://webui.homelab.pesulabs.net:30080 | http://webui.homelab.svc.cluster.local:8080 | /health | 30080 |

### Performance Metrics
- **Total Services**: 14
- **Online Services**: 6 (43%)
- **Offline Services**: 6 (43%)
- **Unknown Services**: 2 (14%)
- **Critical Services Online**: 2/3 (PostgreSQL, Redis operational)

---

*This document is automatically generated from the homelab dashboard health check data and should be updated regularly to reflect service status changes.*