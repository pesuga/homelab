# Infrastructure

Infrastructure-as-code and configuration for the homelab.

---

## Structure

```
infrastructure/
├── kubernetes/          # Kubernetes manifests and Kustomize configs
│   ├── traefik/        # Ingress controller
│   ├── monitoring/     # Prometheus, Grafana, Loki
│   ├── databases/      # PostgreSQL instances
│   └── apps/           # Application deployments
└── docker/              # Docker Compose files (if any)
```

---

## Kubernetes Deployment

### Prerequisites
- K3s installed on service node (asuna) and compute node
- Tailscale configured for inter-node communication
- kubectl configured to access cluster

### Deployment Pattern

**Standard Deployment**:
```bash
kubectl apply -f <manifest>.yaml
# or
kubectl apply -k <directory>/
```

**With Kustomize**:
```bash
kubectl kustomize <directory>/ | kubectl apply -f -
```

---

## Key Services

### Traefik Ingress Controller
- **Location**: `kubernetes/traefik/`
- **Purpose**: HTTP/HTTPS ingress with automatic Let's Encrypt certificates
- **Configuration**: IngressRoute CRDs for service routing

### Monitoring Stack
- **Location**: `kubernetes/monitoring/`
- **Components**: Prometheus, Grafana, Loki
- **Purpose**: Metrics collection, visualization, log aggregation

### Databases
- **Location**: `kubernetes/databases/`
- **Type**: PostgreSQL StatefulSets
- **Instances**: Family API DB, N8n DB

---

## Networking

### Tailscale Mesh
- All nodes joined to Tailscale network
- Service node: 100.81.76.55
- Compute node: 100.72.98.106

### Traefik Entry Points
- **web** (80): HTTP → HTTPS redirect
- **websecure** (443): HTTPS with TLS termination

### DNS
- External domains: *.pesulabs.net
- Internal: Kubernetes DNS (cluster.local)

---

## Common Operations

### Deploy New Service
1. Create deployment manifest
2. Create service manifest
3. Create IngressRoute for HTTPS access
4. Apply manifests: `kubectl apply -f .`
5. Verify deployment: `kubectl get pods -n <namespace>`
6. Test endpoint: `curl https://service.pesulabs.net`

### Update Existing Service
1. Modify manifest or update image tag
2. Apply changes: `kubectl apply -f <manifest>.yaml`
3. Watch rollout: `kubectl rollout status deployment/<name> -n <namespace>`
4. Verify: Check logs and test endpoint

### Troubleshooting
1. Check pod status: `kubectl get pods -A`
2. View logs: `kubectl logs <pod> -n <namespace>`
3. Describe resource: `kubectl describe <resource> <name> -n <namespace>`
4. Check ingress: `kubectl describe ingressroute <name> -n <namespace>`

---

## References

- **K3s Documentation**: https://docs.k3s.io
- **Traefik Documentation**: https://doc.traefik.io/traefik/
- **Kubernetes Documentation**: https://kubernetes.io/docs/

**For detailed architecture information, see**: `project-context/ARCHITECTURE.md`
**For service inventory, see**: `project-context/SERVICES.md`
