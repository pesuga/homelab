---
name: verify-claim
description: Real-time validation of "all services working" claims
parameters:
  claim:
    type: string
    description: "The claim being made (e.g., 'all services working perfectly')"
  services:
    type: array
    description: "Specific services to check (optional, defaults to critical services)"
  quick_check:
    type: boolean
    default: true
    description: "Perform quick validation of critical services only"
---

# 🔍 Real-Time Claim Verification

Immediately validates claims about service status to prevent false "all services working perfectly" statements.

## When to Use This Command

Use this command whenever:
- You're about to claim "all services are working perfectly"
- Someone asks about service status
- You need to verify system health before proceeding
- Session documentation claims need validation

## Claim Analysis

I will analyze your claim and test the reality:

### Common Claims and What I'll Verify

**"All services working perfectly"** → Test all 12+ critical services
**"Deployment complete"** → Verify specific service is actually running
**"Infrastructure ready"** → Check cluster, networking, storage
**"LLM services operational"** → Validate Ollama, GPU, models

### Quick vs Full Validation

**Quick Check (default)** - Tests critical 5 services:
- Homelab Dashboard (main UI)
- N8n (workflow automation)
- Ollama (LLM inference)
- Kubernetes cluster health
- Network connectivity

**Full Validation** - Tests complete service stack:
- All 10+ external services
- Internal services (PostgreSQL, Redis)
- Resource utilization
- Storage and networking

## Critical Service Matrix

### Must-Have Services (Quick Check)
| Service | URL | Success Criteria |
|---------|-----|------------------|
| Homelab Dashboard | http://100.81.76.55:30800 | HTTP 200, responsive UI |
| N8n | http://100.81.76.55:30678 | HTTP 200, login accessible |
| Ollama | http://100.72.98.106:11434 | HTTP 200, API responds |
| K8s Cluster | kubectl get nodes | All nodes Ready |
| Network | ping tests | Both nodes reachable |

### Complete Service List (Full Check)
**Service Node Services:**
- Prometheus (metrics) - http://100.81.76.55:30090
- Loki (logs) - http://100.81.76.55:30314
- Qdrant (vectors) - http://100.81.76.55:30633
- Mem0 (AI memory) - http://100.81.76.55:30880
- LobeChat (AI chat) - http://100.81.76.55:30910
- Whisper (STT) - http://100.81.76.55:30900
- Docker Registry - http://100.81.76.55:30500

**Compute Node Services:**
- Ollama K8s - http://100.81.76.55:30277
- GPU Services - ROCm + AMD RX 7800 XT

## Verification Process

### 1. Claim Parsing
I'll extract what you're claiming is working and identify the specific services that should be validated.

### 2. Rapid Testing
- HTTP endpoint checks with timeouts
- Kubernetes status validation
- Network connectivity tests
- Service health endpoint calls

### 3. Reality Assessment
I'll categorize the actual status:
- ✅ **FACTUALLY CORRECT**: Services are actually working
- ⚠️ **PARTIALLY TRUE**: Some services working, others not
- ❌ **FACTUALLY INCORRECT**: Claim is false, services are down

### 4. Immediate Feedback
I provide:
- **Verdict**: Whether your claim is supported by evidence
- **Evidence**: Specific test results proving the verdict
- **Correction**: Accurate statement if claim is false
- **Action**: What needs to be fixed to make claim true

## Usage Examples

```bash
/verify-claim claim:"all services working perfectly"
# Quick validation of critical services

/verify-claim claim:"all services working perfectly" quick_check:false
# Full validation of all services

/verify-claim claim:"n8n deployment complete" services:["n8n"]
# Validate specific service claim

/verify-claim claim:"kubernetes cluster healthy"
# Verify cluster status specifically
```

## Response Patterns

### ✅ Claim Verified
```
✅ FACTUALLY CORRECT: "all services working perfectly"

Evidence:
• Homelab Dashboard: HTTP 200 (52ms) ✅
• N8n: HTTP 200 (145ms) ✅
• Ollama: HTTP 200 (89ms) ✅
• K8s Cluster: 2/2 nodes Ready ✅
• Network: Both nodes reachable ✅

Your claim is supported by evidence. All critical services are operational.
```

### ❌ Claim Incorrect
```
❌ FACTUALLY INCORRECT: "all services working perfectly"

Evidence:
• Homelab Dashboard: Connection refused ❌
• N8n: HTTP 503 Service Unavailable ❌
• Ollama: HTTP 200 (89ms) ✅
• K8s Cluster: 2/2 nodes Ready ✅
• Network: Both nodes reachable ✅

CORRECTED STATEMENT: "3/5 critical services working, N8n and Dashboard down"

ACTIONS NEEDED:
1. Check Homelab Dashboard pod: kubectl get pods -n homelab | grep dashboard
2. Restart N8n deployment: kubectl rollout restart deployment/n8n -n homelab
3. Check logs: kubectl logs -n homelab -l app=homelab-dashboard
```

## Integration with Session Management

This command maintains honesty in your documentation by:
- Providing immediate factual verification
- Preventing optimistic but false claims
- Suggesting accurate alternative statements
- Creating actionable remediation plans

## Technical Implementation

I use your existing infrastructure:
- `curl` for HTTP endpoint testing
- `kubectl` for Kubernetes validation
- Network connectivity tests
- Response time measurements
- Existing health check scripts when available

---

*Ready to verify your service status claims against reality?*