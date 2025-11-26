---
name: homelab-health
description: Complete homelab system health dashboard
parameters:
  section:
    type: string
    enum: ["all", "services", "infrastructure", "network", "resources"]
    default: "all"
    description: "Which section to display (all for complete dashboard)"
  refresh:
    type: boolean
    default: false
    description: "Force refresh of all service status"
  format:
    type: string
    enum: ["table", "detailed", "urls", "json"]
    default: "table"
    description: "Output format for the health data"
---

# 🏥 Homelab Health Dashboard

Complete real-time health monitoring of your two-node homelab architecture with service status, resource utilization, and network connectivity.

## Dashboard Architecture

Your homelab consists of two nodes with distinct responsibilities:

### 🖥️ Service Node (asuna - 100.81.76.55)
**Purpose**: Kubernetes orchestration and service hosting
- **OS**: Ubuntu 24.04.3 LTS
- **Hardware**: i7-4510U, 8GB RAM, 98GB storage
- **Services**: 10+ containerized workloads
- **Role**: Central service hub

### 🚀 Compute Node (pesubuntu - 100.86.122.109)
**Purpose**: LLM inference with GPU acceleration
- **OS**: Ubuntu 25.10 (Questing Quetzal)
- **Hardware**: i5-12400F, 32GB RAM, AMD RX 7800 XT (16GB VRAM)
- **Services**: llama.cpp, Kimi-VL vision model, ROCm, GPU workloads
- **Role**: AI/ML compute engine

## Health Sections

> **🎉 Recent Recovery**: Homelab fully restored as of 2025-11-18. Network connectivity fixed, AI/ML pipeline operational with llama.cpp + Kimi-VL vision model.

### 📊 All Services (default)
Complete service inventory with real-time status:

| Service | Node | URL | Status | Response | Details |
|---------|------|-----|--------|----------|---------|
| **Core Services** |
| Homelab Dashboard | asuna | http://100.81.76.55:30800 | ⏳ Testing | - | Main UI interface |
| N8n | asuna | http://100.81.76.55:30678 | ⏳ Testing | - | Workflow automation |
| Prometheus | asuna | http://100.81.76.55:30190 | ⏳ Testing | - | Metrics collection |
| **AI/ML Services** |
| llama.cpp (Kimi-VL) | pesubuntu | http://100.86.122.109:8080 | ⏳ Testing | - | Vision-language LLM |
| Mem0 | asuna | http://100.81.76.55:30880 | ⏳ Testing | - | AI memory layer |
| Whisper | asuna | http://100.81.76.55:30900 | ⏳ Testing | - | Speech-to-text |
| ~~Ollama~~ | ~~asuna~~ | ~~http://100.81.76.55:30277~~ | ~~Removed~~ | - | ~~Replaced by llama.cpp~~ |
| ~~LobeChat~~ | ~~asuna~~ | ~~http://100.81.76.55:30910~~ | ~~Removed~~ | - | ~~Deprecated service~~ |
| **Data Services** |
| PostgreSQL | asuna | Internal | ⏳ Testing | - | Database (port 5432) |
| Redis | asuna | Internal | ⏳ Testing | - | Cache (port 6379) |
| Qdrant | asuna | http://100.81.76.55:30633 | ⏳ Testing | - | Vector database |
| **Infrastructure** |
| Loki | asuna | http://100.81.76.55:30314 | ⏳ Testing | - | Log aggregation |
| Docker Registry | asuna | http://100.81.76.55:30500 | ⏳ Testing | - | Container registry |
| Family Assistant | asuna | http://100.81.76.55:30080 | ⏳ Testing | - | Family platform |

### 🏗️ Infrastructure Status
Kubernetes cluster and system health:

**Kubernetes Cluster:**
- Cluster Status: ⏳ Checking
- Nodes: 2/2 Ready (⏳ Checking)
- Pods: ⏳ Calculating
- Namespaces: homelab, flux-system, kube-system
- Storage: ⏳ Checking PVCs

**System Resources:**
- asuna CPU: ⏳ Checking
- asuna Memory: ⏳ Checking
- asuna Storage: ⏳ Checking
- pesubuntu CPU: ⏳ Checking
- pesubuntu Memory: ⏳ Checking
- pesubuntu Storage: ⏳ Checking
- GPU Utilization: ⏳ Checking

### 🌐 Network Connectivity
Inter-node and service communication:

**Tailscale Mesh:**
- asuna (100.81.76.55): ⏳ Checking
- pesubuntu (100.86.122.109): ⏳ Checking
- Mesh Status: ⏳ Checking

**Service Connectivity:**
- Service Node → Compute Node: ⏳ Checking
- Compute Node → Service Node: ⏳ Checking
- Internet Access: ⏳ Checking
- DNS Resolution: ⏳ Checking

### 💾 Resource Utilization
Current system performance:

**Service Node (asuna):**
- CPU Load: ⏳ Checking
- Memory Usage: ⏳ Checking
- Disk Usage: ⏳ Checking
- Network I/O: ⏳ Checking

**Compute Node (pesubuntu):**
- CPU Load: ⏳ Checking
- Memory Usage: ⏳ Checking
- Disk Usage: ⏳ Checking
- GPU Utilization: ⏳ Checking
- GPU Memory: ⏳ Checking
- Network I/O: ⏳ Checking

## Status Indicators

### Service Status
- ✅ **Healthy**: Service responding correctly
- ⚠️ **Warning**: Responding but with issues
- ❌ **Down**: Service not responding
- ❓ **Unknown**: Cannot determine status

### Response Times
- **🟢 Fast**: <200ms
- **🟡 Medium**: 200-1000ms
- **🔴 Slow**: >1000ms

### Resource Levels
- **🟢 Normal**: <70% usage
- **🟡 High**: 70-90% usage
- **🔴 Critical**: >90% usage

## Usage Examples

```bash
/homelab-health
# Show complete dashboard with all sections

/homelab-health section:services format:detailed
# Detailed service status with troubleshooting info

/homelab-health section:infrastructure format:json
# Infrastructure status as JSON for automation

/homelab-health refresh:true
# Force refresh all service status (slower but more accurate)
```

## Output Formats

### Table (default)
Compact tabular view with color coding
- Best for quick status checks
- Color-coded status indicators
- Summary statistics

### Detailed
Comprehensive information per service
- HTTP status codes and response times
- Pod status and restart counts
- Error messages and warnings
- Troubleshooting suggestions

### URLs Only
Clean list of accessible service URLs
- Perfect for bookmarking
- Quick access links
- Service descriptions

### JSON
Machine-readable format for automation
- Structured data output
- API-friendly format
- Integration with monitoring tools

## Health Checks Performed

### HTTP Service Tests
- Endpoint connectivity (curl with timeouts)
- HTTP status code validation
- Response time measurement
- Content validation (where applicable)

### Kubernetes Tests
- Cluster connectivity (kubectl cluster-info)
- Node readiness status
- Pod health and restart counts
- Service endpoint availability
- Persistent volume claim status

### System Tests
- Network connectivity (ping tests)
- Resource utilization (top, df)
- Service process status
- Log error analysis
- GPU status (ROCm/Vulkan tools)
- llama.cpp model verification

### Integration Tests
- Inter-node communication
- Database connectivity
- Service dependencies
- Authentication flows

## Troubleshooting Integration

When issues are detected, I provide:
- **Root Cause Analysis**: Most likely failure reason
- **Diagnostic Commands**: Specific commands to investigate
- **Remediation Steps**: Actions to fix the issue
- **Verification Steps**: How to confirm the fix worked

## Historical Data

Each run stores historical data in `.claude/data/health-history.json` for:
- Service uptime trends
- Performance degradation detection
- Resource utilization patterns
- Common failure identification

## 📋 Quick Service URLs

**Core Services**:
- Homelab Dashboard: http://100.81.76.55:30800
- N8n Workflows: http://100.81.76.55:30678
- Prometheus: http://100.81.76.55:30190

**AI/ML Services**:
- llama.cpp (Kimi-VL): http://100.86.122.109:8080
- Mem0 AI Memory: http://100.81.76.55:30880
- Whisper STT: http://100.81.76.55:30900

**Data Services**:
- Qdrant Vector DB: http://100.81.76.55:30633
- PostgreSQL: Internal (port 5432)
- Redis: Internal (port 6379)

**Infrastructure**:
- Loki Logs: http://100.81.76.55:30314
- Docker Registry: http://100.81.76.55:30500
- Family Assistant: http://100.81.76.55:30080

---

*Ready to check your complete homelab health status?*