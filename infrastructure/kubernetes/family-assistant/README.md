# Family Assistant Backend - Kubernetes Deployment

**Single Source of Truth** for Family Assistant Backend deployment.

## 📁 Directory Structure

```
family-assistant/
├── deployment.yaml       # Main deployment configuration
├── service.yaml         # Service definition
├── kustomization.yaml   # Kustomize configuration
└── README.md           # This file
```

## 🚀 Deployment

### Using kubectl
```bash
# Apply all resources
kubectl apply -k infrastructure/kubernetes/family-assistant/

# Or apply individually
kubectl apply -f infrastructure/kubernetes/family-assistant/deployment.yaml
kubectl apply -f infrastructure/kubernetes/family-assistant/service.yaml
```

### Using Kustomize
```bash
# Preview changes
kubectl kustomize infrastructure/kubernetes/family-assistant/

# Apply with kustomize
kustomize build infrastructure/kubernetes/family-assistant/ | kubectl apply -f -
```

## 📋 Current Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| **Image** | `100.81.76.55:30500/family-assistant:me-fixed` | Registry-qualified |
| **Replicas** | 1 | Single replica due to resource constraints |
| **Node** | pesubuntu | Pinned until images in registry |
| **Resources** | 250m CPU, 512Mi RAM (request) | 1 CPU, 2Gi RAM (limit) |
| **Health Check** | `/health` on port 8001 | Liveness & Readiness |

## 🔄 Updating the Deployment

### Option 1: Edit and Apply (Recommended)
```bash
# Edit deployment.yaml
vim infrastructure/kubernetes/family-assistant/deployment.yaml

# Apply changes
kubectl apply -f infrastructure/kubernetes/family-assistant/deployment.yaml

# Watch rollout
kubectl rollout status deployment/family-assistant-backend -n homelab
```

### Option 2: Imperative Update (Quick fixes only)
```bash
# Update image
kubectl set image deployment/family-assistant-backend \
  family-assistant=100.81.76.55:30500/family-assistant:new-tag \
  -n homelab

# IMPORTANT: Sync changes back to deployment.yaml after imperative updates!
```

### Option 3: Kustomize Image Update
```bash
# Edit kustomization.yaml and uncomment image section
# Update newTag value
kubectl apply -k infrastructure/kubernetes/family-assistant/
```

## 🔍 Troubleshooting

### Check Pod Status
```bash
kubectl get pods -n homelab -l app=family-assistant-backend
kubectl describe pod <pod-name> -n homelab
kubectl logs <pod-name> -n homelab --tail=50
```

### Check Deployment
```bash
kubectl get deployment family-assistant-backend -n homelab
kubectl describe deployment family-assistant-backend -n homelab
kubectl rollout history deployment/family-assistant-backend -n homelab
```

### Rollback Deployment
```bash
# Rollback to previous version
kubectl rollout undo deployment/family-assistant-backend -n homelab

# Rollback to specific revision
kubectl rollout undo deployment/family-assistant-backend -n homelab --to-revision=2
```

### Force Restart
```bash
# Update restart annotation
kubectl patch deployment family-assistant-backend -n homelab \
  -p "{\"spec\":{\"template\":{\"metadata\":{\"annotations\":{\"kubectl.kubernetes.io/restartedAt\":\"$(date -Iseconds)\"}}}}}"
```

## 🗑️ Deprecated Files

The following files are **DEPRECATED** and should not be used:

- `/home/pesu/Rakuflow/systems/homelab/family-assistant-backend.yaml`
- `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/family-assistant-backend.yaml`
- `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/family-assistant-enhancement.yaml`
- `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/family-assistant-enhanced-deployment.yaml`

These files have been moved to `trash/deprecated-manifests/` for reference.

## ⚠️ Important Notes

### Image Registry
- **Always use registry-qualified images**: `100.81.76.55:30500/family-assistant:tag`
- **Never use unqualified images**: ~~`family-assistant:tag`~~ (will fail on different nodes)

### Node Selector
- Currently pinned to `pesubuntu` node
- Remove `nodeSelector` when images are properly pushed to registry
- This allows pods to schedule on any node

### OTEL Collector
- OpenTelemetry exports are currently DISABLED
- Enable when OTEL collector is deployed to cluster
- Uncomment OTEL environment variables in deployment.yaml

### Secrets
- Passwords currently in plain text (TODO)
- Migrate to Kubernetes Secrets before production
- Use `kubectl create secret` or external secrets operator

## 📚 Related Documentation

- [Deployment Problems Analysis](../../../docs/DEPLOYMENT-PROBLEMS-ANALYSIS.md)
- [Family Assistant README](../../../services/family-assistant-enhanced/README.md)
- [GitOps Setup Guide](../../../docs/GITOPS-SETUP.md)

## 🔄 Version History

| Date | Version | Image Tag | Changes |
|------|---------|-----------|---------|
| 2025-11-17 | v2.0.0 | me-fixed | Consolidated to single manifest, fixed image pull |
| 2025-11-16 | v1.x | phase2-mcp-logging-fix | Multiple failed deployments |
| 2025-11-15 | v1.x | jwt-auth-fixed | Previous baseline |

## 🎯 Roadmap

- [ ] Push images to registry for multi-node scheduling
- [ ] Migrate secrets to Kubernetes Secret objects
- [ ] Deploy OTEL collector and enable tracing
- [ ] Implement HPA when resources allow (2+ replicas)
- [ ] Add Ingress for external HTTPS access
- [ ] Setup GitOps with Flux CD
