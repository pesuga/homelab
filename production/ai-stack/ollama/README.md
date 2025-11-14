# Ollama Kubernetes Deployment

This directory contains Kubernetes manifests for deploying Ollama with GPU acceleration and HTTPS ingress.

## Architecture

```
User/N8n → Traefik Ingress (HTTPS) → Ollama Service → Ollama Pod → GPU
           ↓
    https://ollama.homelab.pesulabs.net
```

## Prerequisites

1. **K3s Cluster**: Running on service node (asuna)
2. **Traefik**: Installed as ingress controller
3. **Compute Node**: pesubuntu with AMD RX 7800 XT GPU
4. **ROCm**: Installed on compute node for GPU acceleration
5. **GPU Device Plugin**: AMD GPU device plugin (optional but recommended)
6. **TLS Certificate**: For HTTPS access (Let's Encrypt or self-signed)

## Deployment Steps

### 1. Create Namespace and PVC
```bash
kubectl apply -f namespace.yaml
kubectl apply -f pvc.yaml
```

### 2. Deploy Ollama
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### 3. Configure TLS Certificate

**Option A: Let's Encrypt (requires external domain)**
```bash
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ollama-tls
  namespace: ollama
spec:
  secretName: ollama-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - ollama.homelab.pesulabs.net
EOF
```

**Option B: Self-signed Certificate**
```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=ollama.homelab.pesulabs.net"

# Create K8s secret
kubectl create secret tls ollama-tls \
  --cert=tls.crt --key=tls.key -n ollama
```

### 4. Deploy Ingress
```bash
kubectl apply -f ingress.yaml
```

### 5. Verify Deployment
```bash
# Check pod status
kubectl get pods -n ollama

# Check service
kubectl get svc -n ollama

# Check ingress
kubectl get ingressroute -n ollama

# View logs
kubectl logs -n ollama -l app=ollama -f
```

### 6. Test API
```bash
# Test from cluster (internal)
kubectl run -it --rm test --image=curlimages/curl --restart=Never -- \
  curl http://ollama.ollama.svc.cluster.local:11434/api/version

# Test from external (HTTPS)
curl https://ollama.homelab.pesulabs.net/api/version
```

## Configuration

### Node Selection

To ensure Ollama runs on the compute node with GPU:

1. Label compute node:
```bash
kubectl label node pesubuntu gpu=true
```

2. Uncomment nodeSelector in deployment.yaml:
```yaml
nodeSelector:
  kubernetes.io/hostname: pesubuntu
  gpu: "true"
```

### GPU Access

#### Option 1: AMD GPU Device Plugin (Recommended)
```bash
# Deploy AMD GPU device plugin
kubectl apply -f https://raw.githubusercontent.com/RadeonOpenCompute/k8s-device-plugin/master/k8s-ds-amdgpu-dp.yaml

# Uncomment GPU resource limits in deployment.yaml
```

#### Option 2: Host GPU Passthrough
```yaml
# Add to deployment.yaml container spec
securityContext:
  privileged: true
volumeMounts:
- name: dev-dri
  mountPath: /dev/dri
volumes:
- name: dev-dri
  hostPath:
    path: /dev/dri
```

## Loading Models

### Method 1: kubectl exec
```bash
kubectl exec -it -n ollama deployment/ollama -- ollama pull mistral:7b-q4_K_M
kubectl exec -it -n ollama deployment/ollama -- ollama pull codellama:7b-q4_K_M
kubectl exec -it -n ollama deployment/ollama -- ollama pull llama3.1:8b-q4_K_M
```

### Method 2: API
```bash
curl https://ollama.homelab.pesulabs.net/api/pull \
  -d '{"name": "mistral:7b-q4_K_M"}'
```

## Integration with N8n

In N8n workflows, use:
- **Internal URL**: `http://ollama.ollama.svc.cluster.local:11434`
- **External URL**: `https://ollama.homelab.pesulabs.net`

Example N8n HTTP Request node:
```json
{
  "url": "http://ollama.ollama.svc.cluster.local:11434/api/generate",
  "method": "POST",
  "body": {
    "model": "mistral:7b-q4_K_M",
    "prompt": "Hello!"
  }
}
```

## Monitoring

### Prometheus Metrics
Ollama doesn't export Prometheus metrics natively. Options:
1. Use custom exporter
2. Monitor via GPU metrics (ROCm exporter)
3. Monitor K8s pod metrics

### Logs
```bash
# View logs
kubectl logs -n ollama -l app=ollama -f

# Logs via Loki (if deployed)
# Query in Grafana: {namespace="ollama", pod=~"ollama-.*"}
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod -n ollama -l app=ollama
kubectl logs -n ollama -l app=ollama
```

### GPU not detected
```bash
# Check ROCm on compute node
rocm-smi
rocminfo

# Check GPU device plugin
kubectl get nodes -o json | jq '.items[].status.allocatable'
```

### Ingress not accessible
```bash
# Check Traefik
kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik

# Check IngressRoute
kubectl describe ingressroute -n ollama ollama

# Check TLS secret
kubectl get secret -n ollama ollama-tls
```

### Model loading slow
- Increase PVC size if disk is full
- Check network bandwidth
- Consider pre-loading models into PVC

## Scaling

### Horizontal Scaling
Not recommended for single-GPU setup. Consider:
- Multiple compute nodes with GPUs
- Model sharding for large models
- Request queueing

### Vertical Scaling
Adjust resource limits in deployment.yaml:
```yaml
resources:
  limits:
    memory: "32Gi"  # Increase if needed
    cpu: "8"
```

## Security

1. **Authentication**: Add Traefik middleware for basic auth or OAuth
2. **Network Policies**: Restrict pod-to-pod communication
3. **RBAC**: Limit service account permissions
4. **TLS**: Always use HTTPS for external access

## Cleanup

```bash
kubectl delete -f ingress.yaml
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
kubectl delete -f pvc.yaml
kubectl delete -f namespace.yaml
```

## References

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Traefik IngressRoute](https://doc.traefik.io/traefik/routing/providers/kubernetes-crd/)
- [AMD GPU Device Plugin](https://github.com/RadeonOpenCompute/k8s-device-plugin)
- [K3s Documentation](https://docs.k3s.io/)
