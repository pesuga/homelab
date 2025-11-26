---
name: validate-session
description: Validate session claims against actual service status
parameters:
  session_file:
    type: string
    default: "docs/SESSION-STATE.md"
    description: "Path to session state file to validate"
  verbose:
    type: boolean
    default: false
    description: "Show detailed validation output"
  save_report:
    type: boolean
    default: true
    description: "Save validation report to file"
---

# 🔍 Session Validation

Validates completion claims in SESSION-STATE.md against actual service health to prevent false "all services working perfectly" claims.

## Validation Process

I will systematically validate all completion claims from your session documentation:

### 1. Parse Session Claims
- Extract ✅ completion markers from SESSION-STATE.md
- Identify service deployment claims
- Parse sprint objectives and their stated status
- Extract service URLs and endpoints

### 2. Actual Service Testing
- Run existing health check scripts (`scripts/health-check-all.sh`)
- Test all claimed service URLs
- Validate Kubernetes deployments
- Check compute node services (Ollama, GPU)

### 3. Compare Claims vs Reality
- Identify discrepancies between claimed and actual status
- Categorize validation results (VALID/INVALID/WARNING)
- Generate specific feedback for each mismatch

### 4. Generate Iteration Plan
- Prioritize issues by severity
- Provide actionable troubleshooting steps
- Suggest next session focus areas

## Expected Services to Validate

Based on your homelab architecture, I'll validate:

### Service Node (asuna - 100.81.76.55)
- **N8n**: http://100.81.76.55:30678 (workflow automation)
- **Prometheus**: http://100.81.76.55:30090 (metrics collection)
- **Loki**: http://100.81.76.55:30314 (log aggregation)
- **Qdrant**: http://100.81.76.55:30633 (vector database)
- **Docker Registry**: http://100.81.76.55:30500 (container registry)
- **Homelab Dashboard**: http://100.81.76.55:30800 (main dashboard)
- **Mem0**: http://100.81.76.55:30880 (AI memory layer)
- **LobeChat**: http://100.81.76.55:30910 (AI chat interface)
- **Whisper**: http://100.81.76.55:30900 (speech-to-text)
- **Family Assistant**: http://100.81.76.55:30080 (family platform)

### Compute Node (pesubuntu - 100.72.98.106)
- **Ollama Native**: http://100.72.98.106:11434 (LLM inference)
- **Ollama K8s**: http://100.81.76.55:30277 (Kubernetes deployment)
- **GPU Services**: ROCm 6.4.1 + AMD RX 7800 XT

### Internal Services
- **PostgreSQL**: postgres.homelab.svc.cluster.local:5432
- **Redis**: redis.homelab.svc.cluster.local:6379

## Validation Categories

### ✅ VALID
Service is actually working as claimed
- HTTP endpoint responds correctly (2xx/3xx)
- Kubernetes pods are running and ready
- Service is accessible via claimed URL

### ❌ INVALID
Service is NOT working despite being claimed complete
- Connection refused or timeout
- HTTP errors (4xx/5xx)
- Pods not running or CrashLoopBackOff
- Service missing from cluster

### ⚠️ WARNING
Service working but with issues
- Slow response times
- Partial functionality
- Configuration warnings
- Resource constraints

## Validation Output

I will provide:

1. **Summary Table**: Service-by-service validation results
2. **Detailed Analysis**: What works, what doesn't, and why
3. **Troubleshooting Steps**: Specific commands to fix issues
4. **Iteration Plan**: What to focus on next session

## Usage Examples

```bash
/validate-session
# Validate current SESSION-STATE.md against actual services

/validate-session verbose:true
# Show detailed validation output with debugging info

/validate-session session_file:docs/SESSION-STATE.md save_report:false
# Validate specific file without saving report
```

## Integration with Your Workflow

This command helps maintain honest progress tracking by:
- Preventing false positive "all services working" claims
- Identifying what actually needs to be fixed
- Providing specific next steps for iteration
- Maintaining technical accuracy in documentation

## Report Storage

When `save_report:true`, validation reports are saved to:
- `claudedocs/validation-reports/`
- Filename: `session-validation-YYYY-MM-DD-HHMMSS.md`

## Dependencies

This command uses your existing infrastructure:
- `scripts/health-check-all.sh` - Comprehensive health checker
- `scripts/service-check-urls.sh` - URL-based verification
- `kubectl` - Kubernetes cluster access
- `curl` - HTTP endpoint testing

---

*Ready to validate your session claims against reality?*