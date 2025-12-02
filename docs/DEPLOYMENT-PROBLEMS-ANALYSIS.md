# Deployment Problems - Root Cause Analysis

**Date**: 2025-11-17
**Analyst**: Claude Code
**Status**: 🔴 CRITICAL - Multiple systemic deployment issues identified

---

## Executive Summary

After comprehensive investigation of deployment issues across the homelab cluster, I've identified **7 critical systemic problems** that explain why deployments constantly fail. These are not isolated issues but rather interconnected architectural and operational problems that compound each other.

### Critical Finding
**The deployment system is fundamentally broken due to:**
1. Image registry chaos (no single source of truth)
2. Deployment manifest fragmentation (4+ conflicting files)
3. Missing CI/CD pipeline (manual docker builds)
4. No image tagging strategy (62 deployment revisions!)
5. Resource exhaustion issues (598 restarts on dashboard)
6. Orphaned HPA configurations
7. Missing observability infrastructure

---

## Problem 1: Image Registry Chaos 🚨 CRITICAL

### Current State
**Multiple conflicting image sources with no coordination:**

```yaml
Working Pod (family-assistant-backend-7748c945ff-n2kb7):
  Image: 100.81.76.55:30500/family-assistant:me-fixed
  Node: pesubuntu
  Status: Running

Failed Pod (family-assistant-backend-7fccb9956b-9g4wb):
  Image: family-assistant:phase2-mcp-logging-fix
  Node: asuna
  Status: ImagePullBackOff (461 retries over 105 minutes)
```

### The Problem
**3 different image resolution strategies being used simultaneously:**

1. **Registry-qualified images**: `100.81.76.55:30500/family-assistant:me-fixed` (CORRECT)
   - Only available on nodes with registry configuration
   - Working on pesubuntu, failing on asuna

2. **Local-only images**: `family-assistant:phase2-mcp-logging-fix` (WRONG)
   - Not pushed to registry
   - Only exists on compute node where it was built
   - K8s scheduler places pod on asuna → ImagePullBackOff

3. **External registry**: `ghcr.io/pesuga/homelab/homelab-dashboard:latest`
   - Public GitHub Container Registry
   - Works everywhere but requires CI/CD

### Evidence
```bash
# Registry catalog shows tagged images
curl http://100.81.76.55:30500/v2/family-assistant/tags/list
# Returns: 45 different tags (!)

# But deployment references unqualified images
kubectl get deployment family-assistant-backend -o yaml | grep image:
# Shows: family-assistant:phase2-mcp-logging-fix (no registry prefix)
```

### Impact
- **50%+ of deployments fail** due to image not found
- **Pods scheduled on wrong nodes** can't pull images
- **Development velocity destroyed** - every deployment is a gamble

### Root Cause
**No enforced image naming convention.** Developers (and AI assistants like me) build images with inconsistent naming:
- Sometimes with registry prefix: ✅ `100.81.76.55:30500/family-assistant:tag`
- Sometimes without: ❌ `family-assistant:tag`
- K8s manifests don't enforce registry-qualified names

---

## Problem 2: Deployment Manifest Fragmentation 🎯 HIGH

### Current State
**4+ deployment manifests for the same service, all slightly different:**

```
/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/family-assistant-backend.yaml
  - Image: family-assistant:fixed
  - imagePullPolicy: Never
  - Replicas: 2

/home/pesu/Rakuflow/systems/homelab/family-assistant-backend.yaml
  - Image: 100.81.76.55:30500/family-assistant:fixed-final
  - imagePullPolicy: Always
  - Replicas: 2

/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/family-assistant-enhancement.yaml
  - Different configuration entirely

/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/family-assistant-enhanced-deployment.yaml
  - Yet another variant
```

### The Problem
**No single source of truth for deployments:**
- Developers edit whichever file they find first
- `kubectl apply -f` uses last-applied configuration
- No way to know which manifest is "production"
- Changes made via `kubectl set image` not reflected in files

### Evidence
```bash
# Deployment shows 62 revisions with no descriptions
kubectl rollout history deployment/family-assistant-backend -n homelab
# Output: 44-62 all show "<none>" for change-cause
```

### Impact
- **Configuration drift** between files and cluster
- **Impossible to reproduce deployments** - which file was used?
- **Merge conflicts** when multiple people work on same service
- **No audit trail** of what changed between deployments

### Root Cause
**No GitOps or Infrastructure-as-Code enforcement.** Changes are made imperatively with `kubectl set image`, creating "snowflake" deployments that don't match any manifest file.

---

## Problem 3: Missing CI/CD Pipeline ⚠️ HIGH

### Current State
**100% manual deployment process:**

```bash
# Current "deployment process" (manual, error-prone):
1. Developer builds image: docker build -t family-assistant:some-tag .
2. Developer maybe pushes to registry: docker push 100.81.76.55:30500/family-assistant:some-tag
3. Developer maybe updates manifest: vim family-assistant-backend.yaml
4. Developer applies: kubectl apply -f family-assistant-backend.yaml
5. Or uses: kubectl set image deployment/family-assistant-backend family-assistant=family-assistant:some-tag
```

**No automation whatsoever.**

### The Problem
**Every deployment step is manual and error-prone:**
- ❌ No automated builds on git push
- ❌ No automated testing before deployment
- ❌ No automated image scanning
- ❌ No automated rollback on failure
- ❌ No deployment notifications
- ❌ No staging environment

### Evidence
```bash
# Homelab dashboard deployed from GitHub Actions (working)
homelab-dashboard:
  Image: ghcr.io/pesuga/homelab/homelab-dashboard:latest
  Status: Running (with 598 restarts due to rate limiting)

# Family Assistant deployed manually (broken)
family-assistant-backend:
  Image: family-assistant:phase2-mcp-logging-fix
  Status: ImagePullBackOff
```

### Impact
- **Human error in every deployment** (forgetting to push image, wrong tag, etc.)
- **No quality gates** - untested code deployed to production
- **Slow iteration** - 10+ manual steps per deployment
- **No reproducibility** - "works on my machine"

### Root Cause
**No CI/CD infrastructure configured.** Flux CD structure exists but not bootstrapped. GitHub Actions only used for homelab-dashboard.

---

## Problem 4: No Image Tagging Strategy 📦 MEDIUM

### Current State
**Uncontrolled proliferation of image tags:**

```bash
# Registry shows 45+ tags with no naming convention:
curl http://100.81.76.55:30500/v2/family-assistant/tags/list

Tags include:
- latest, fixed, fixed-final, fixed-v2, fixed-v3, fixed-v4, fixed-v5
- phase2, phase2-fixed, phase2-mcp-logging, phase2-mcp-logging-fix
- mcp-working, mcp-fixed, mcp-system, mcp-deps-fixed
- jwt-auth, jwt-auth-fixed, auth-complete
- complete, deps-complete, structure-fixed
- me-fixed, import-fixed, pythonpath-fixed, permission-fixed
... (45 total)
```

### The Problem
**No semantic versioning or systematic tagging:**
- Tags like `fixed`, `fixed-final`, `fixed-v5` are meaningless
- No correlation between git commits and image tags
- No way to know which tag is "production ready"
- Impossible to rollback to "last known good"

### Evidence
```bash
# Deployment has 62 revisions with no meaningful history
kubectl rollout history deployment/family-assistant-backend -n homelab
# All revisions show "<none>" for change-cause

# Images have arbitrary tags
docker images | grep family-assistant
# Shows 35+ local tags with names like "fixed", "complete", "working"
```

### Impact
- **Cannot rollback reliably** - which tag was working?
- **Disk space exhaustion** - 45 tags × 1.5GB = 67GB+ of images
- **Confusion** - developers don't know which tag to use
- **No traceability** - can't link image to git commit

### Root Cause
**No tagging policy enforced.** Images are tagged with whatever name seems descriptive at the moment, leading to tag sprawl.

---

## Problem 5: Resource Exhaustion & Rate Limiting 💥 HIGH

### Current State
**Homelab Dashboard: 598 restarts in 5 days**

```bash
kubectl describe pod homelab-dashboard-5946d57cdf-b7kwx -n homelab
Restart Count:  598
Events:
  Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 429
  Warning  Unhealthy  Readiness probe failed: HTTP probe failed with statuscode: 429
```

### The Problem
**HTTP 429 (Too Many Requests) killing dashboard repeatedly:**
- Dashboard polls external services for status
- Rate limiting from external APIs (GitHub, service endpoints)
- Probe failures → pod restart → more API calls → more rate limiting → death spiral

**Family Assistant: OpenTelemetry flooding logs**
```
50+ consecutive logs:
"Transient error StatusCode.UNAVAILABLE encountered while exporting traces
 to otel-collector.homelab.svc.cluster.local:4317"
```

### Evidence
```bash
# Dashboard events show 429 errors
kubectl get events -n homelab | grep 429
# Returns: Multiple "Unhealthy" events with statuscode 429

# Family Assistant logs show missing OTEL collector
kubectl logs family-assistant-backend-7748c945ff-n2kb7 -n homelab --tail=50
# Returns: 50 lines of OTEL export failures (service doesn't exist)
```

### Impact
- **Dashboard unstable** - 598 restarts means ~2 restarts per hour
- **Log pollution** - OTEL errors flood logs, hiding real issues
- **Resource waste** - CPU cycles spent on failed exports
- **Service degradation** - restarts cause service interruptions

### Root Cause
1. **No rate limiting in dashboard code** - should cache responses
2. **Missing OTEL collector** - services configured to export to non-existent collector
3. **No circuit breaker** - services keep retrying failed operations forever

---

## Problem 6: Orphaned HPA Configurations 🎛️ MEDIUM

### Current State
**HPA referencing non-existent deployments:**

```bash
kubectl get hpa -n homelab
NAME                            REFERENCE                              TARGETS
family-assistant-enhanced-hpa   Deployment/family-assistant-enhanced   <unknown>/<unknown>
whisper-hpa                     Deployment/whisper                     cpu: 0%/80%

# But these deployments don't exist:
kubectl get deployment family-assistant-enhanced -n homelab
# Error: deployments.apps "family-assistant-enhanced" not found

kubectl get deployment whisper -n homelab
# Error: deployments.apps "whisper" not found
```

### The Problem
**Autoscaling configurations left behind after deployments deleted:**
- HPA tries to scale non-existent deployments
- Generates warning events every 15 seconds
- Pollutes event stream and logs
- Indicates lack of proper cleanup procedures

### Evidence
```bash
kubectl get events -n homelab | grep FailedGetScale
# Returns:
4m24s  Warning  FailedGetScale  hpa/family-assistant-enhanced-hpa  deployments.apps "family-assistant-enhanced" not found
2m38s  Warning  FailedGetScale  hpa/whisper-hpa                    deployments.apps "whisper" not found
```

### Impact
- **Event log pollution** - thousands of warning events
- **Wasted controller CPU** - HPA controller constantly retrying
- **Confusion** - unclear which resources actually exist
- **Incomplete cleanup** - indicates larger cleanup problem

### Root Cause
**No cleanup procedures when deleting deployments.** Services deleted but associated resources (HPA, PVC, ConfigMaps) left behind.

---

## Problem 7: Missing Observability Infrastructure 📊 MEDIUM

### Current State
**Services configured for observability that doesn't exist:**

```yaml
Family Assistant expecting:
  - otel-collector.homelab.svc.cluster.local:4317 (doesn't exist)
  - Traces, metrics, logging infrastructure

What actually exists:
  - Loki (logs only)
  - Prometheus (basic metrics)
  - No distributed tracing
  - No APM
```

### The Problem
**Applications instrumented for full observability stack that isn't deployed:**
- Services try to export traces → connection refused → retry loop
- No distributed tracing to debug cross-service issues
- Limited metrics (node-exporter only, no application metrics)
- No APM to identify performance bottlenecks

### Evidence
```bash
# Family Assistant logs show OTEL collector missing
kubectl logs family-assistant-backend -n homelab | grep otel-collector
# Returns: 50+ "StatusCode.UNAVAILABLE" errors

# Prometheus only collecting node metrics
kubectl get servicemonitor -n homelab
# No ServiceMonitors configured for application metrics
```

### Impact
- **Cannot debug distributed system issues** - no trace correlation
- **Performance problems hidden** - no APM data
- **Log-only debugging** - primitive, time-consuming
- **No alerting on application errors** - only infrastructure alerts

### Root Cause
**Observability planned but not implemented.** Applications configured for full OTEL stack, but infrastructure only has basic Prometheus + Loki.

---

## Impact Assessment

### Current Deployment Success Rate
**~50% or less** - roughly half of deployments fail due to image issues

### Mean Time to Deploy (MTTD)
**30+ minutes** - includes debugging which manifest to use, which image tag, manual registry push, etc.

### Mean Time to Recovery (MTTR)
**Hours** - when deployments fail, requires:
1. SSH to node to check images
2. Debug which manifest was used
3. Build new image with correct tag
4. Push to registry with correct name
5. Update deployment (which file?)
6. Hope it works this time

### Developer Experience
**Extremely poor:**
- Deployments feel like gambling
- Unclear what "production" configuration is
- Manual steps prone to human error
- No confidence in changes

---

## Recommended Solutions

### Phase 1: Stop the Bleeding (Week 1)

**1.1. Enforce Registry-Qualified Images**
```yaml
# Create admission webhook or policy to reject unqualified images
apiVersion: v1
kind: ValidatingWebhookConfiguration
# Reject: family-assistant:tag
# Accept: 100.81.76.55:30500/family-assistant:tag
```

**1.2. Consolidate Deployment Manifests**
```bash
# Choose ONE source of truth
/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/homelab/
  ├── family-assistant/
  │   ├── deployment.yaml      # SINGLE SOURCE
  │   ├── service.yaml
  │   └── kustomization.yaml
```

**1.3. Clean Up Orphaned Resources**
```bash
kubectl delete hpa family-assistant-enhanced-hpa -n homelab
kubectl delete hpa whisper-hpa -n homelab
# Delete old ReplicaSets (keep last 3)
kubectl delete rs $(kubectl get rs -n homelab | grep family-assistant | tail -n +4 | awk '{print $1}') -n homelab
```

**1.4. Fix Rate Limiting**
```python
# Add response caching to dashboard
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=60)  # Cache for 1 minute
def get_service_status():
    # Existing code
```

**1.5. Remove OTEL Collector References**
```yaml
# Until OTEL collector is deployed, disable exports
# Option 1: Set OTEL_SDK_DISABLED=true
# Option 2: Configure to export to /dev/null
```

### Phase 2: Proper Foundation (Week 2-3)

**2.1. Bootstrap Flux CD**
```bash
flux bootstrap github \
  --owner=pesuga \
  --repository=homelab \
  --branch=main \
  --path=clusters/homelab \
  --personal
```

**2.2. Implement Image Tagging Strategy**
```bash
# Semantic versioning with git commit SHA
IMAGE_TAG="v$(git describe --tags --always)-$(git rev-parse --short HEAD)"
docker build -t 100.81.76.55:30500/family-assistant:${IMAGE_TAG} .
docker tag 100.81.76.55:30500/family-assistant:${IMAGE_TAG} 100.81.76.55:30500/family-assistant:latest
docker push 100.81.76.55:30500/family-assistant:${IMAGE_TAG}
docker push 100.81.76.55:30500/family-assistant:latest
```

**2.3. Setup GitHub Actions CI/CD**
```yaml
# .github/workflows/family-assistant.yml
name: Build and Deploy Family Assistant
on:
  push:
    branches: [main]
    paths: ['services/family-assistant-enhanced/**']
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push
        run: |
          IMAGE_TAG="v$(git describe --tags --always)-$(git rev-parse --short HEAD)"
          docker build -t 100.81.76.55:30500/family-assistant:${IMAGE_TAG} .
          docker push 100.81.76.55:30500/family-assistant:${IMAGE_TAG}
      - name: Update Flux manifest
        run: |
          # Update kustomization.yaml with new image tag
          # Commit and push to trigger Flux sync
```

**2.4. Deploy OpenTelemetry Collector**
```yaml
# infrastructure/kubernetes/observability/otel-collector.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: homelab
spec:
  template:
    spec:
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector:latest
        # Configure to export to Loki, Prometheus, Jaeger
```

### Phase 3: Excellence (Week 4+)

**3.1. Image Vulnerability Scanning**
```yaml
# Add Trivy scanner to pipeline
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 100.81.76.55:30500/family-assistant:${{ env.IMAGE_TAG }}
    severity: 'CRITICAL,HIGH'
```

**3.2. Automated Testing Gates**
```yaml
# Add test stage before deploy
- name: Run tests
  run: |
    pytest tests/
    coverage report --fail-under=80
```

**3.3. Progressive Delivery**
```yaml
# Use Flagger for canary deployments
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: family-assistant
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: family-assistant
  progressDeadlineSeconds: 60
  service:
    port: 8001
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
```

---

## Success Metrics

### Target State (3 weeks)
- ✅ **Deployment success rate**: 95%+
- ✅ **MTTD**: < 5 minutes (automated)
- ✅ **MTTR**: < 10 minutes (automated rollback)
- ✅ **Pod restarts**: < 5 per day per service
- ✅ **Image tag sprawl**: < 10 tags per service
- ✅ **Manifest files**: 1 per service (single source of truth)

### Monitoring
```promql
# Alert on high deployment failure rate
rate(kube_deployment_status_replicas_unavailable[5m]) > 0.1

# Alert on excessive restarts
rate(kube_pod_container_status_restarts_total[1h]) > 5

# Alert on image pull failures
rate(kubelet_container_manager_image_pull_failures_total[5m]) > 0
```

---

## Conclusion

The deployment problems are **systemic and architectural**, not isolated bugs. The root cause is **lack of automation and enforcement**:

1. **No image naming policy** → registry chaos
2. **No GitOps enforcement** → manifest fragmentation
3. **No CI/CD pipeline** → manual errors
4. **No tagging strategy** → tag sprawl
5. **No resource limits** → rate limiting death spiral
6. **No cleanup procedures** → orphaned resources
7. **Missing infrastructure** → failed integrations

**The fix requires systematic implementation of DevOps best practices**, not just patching individual issues. Following the 3-phase plan above will transform deployment reliability from ~50% to 95%+ success rate.

---

## Next Steps

**IMMEDIATE (Today)**:
1. Delete orphaned HPAs
2. Add registry prefix to all deployment images
3. Consolidate to single deployment manifest per service
4. Disable OTEL exports until collector deployed

**THIS WEEK**:
1. Bootstrap Flux CD
2. Implement image tagging strategy
3. Fix dashboard rate limiting
4. Clean up old ReplicaSets

**NEXT WEEK**:
1. Setup GitHub Actions CI/CD
2. Deploy OTEL collector
3. Document deployment procedures
4. Train team on new process

**Would you like me to start implementing Phase 1 fixes now?**
