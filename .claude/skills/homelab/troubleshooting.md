---
name: homelab-troubleshooting
description: Complete troubleshooting procedures and diagnostic patterns
category: homelab
version: "1.0"
---

# 🔧 Homelab Troubleshooting Guide

Comprehensive troubleshooting procedures for your two-node homelab with diagnostic patterns, log sources, and remediation steps.

## Diagnostic Framework

### Troubleshooting Methodology
1. **Identify Scope**: Single service vs systemic issue
2. **Gather Evidence**: Logs, metrics, status checks
3. **Analyze Patterns**: Common failure modes
4. **Apply Solution**: Targeted remediation steps
5. **Verify Fix**: Confirm resolution and monitor

### Triage Categories
- **🔴 Critical**: Service down, impacting functionality
- **🟡 Warning**: Service degraded, performance issues
- **🔵 Info**: Configuration or optimization needed

## Common Issue Patterns

### 1. Service Not Responding

#### Symptoms
- HTTP connection refused
- Timeout errors
- Service unreachable via URL

#### Diagnostic Steps
```bash
# 1. Check if service exists in Kubernetes
kubectl get services -n homelab | grep <service-name>

# 2. Check pod status
kubectl get pods -n homelab | grep <service-name>

# 3. Check pod logs for errors
kubectl logs -n homelab -l app=<service-name> --tail=20

# 4. Check if service has endpoints
kubectl get endpoints -n homelab <service-name>

# 5. Test local connectivity
curl -v http://localhost:<port>
```

#### Common Causes & Solutions
- **Pod CrashLoopBackOff**: Check logs, restart deployment
- **No Endpoints**: Pods not ready, check resource issues
- **Port Mismatch**: Service port vs container port mismatch
- **Network Policies**: Blocked communication between pods

### 2. Kubernetes Cluster Issues

#### Symptoms
- kubectl commands failing
- Pods stuck in Pending state
- Node not ready

#### Diagnostic Steps
```bash
# 1. Check cluster status
kubectl cluster-info

# 2. Check node status
kubectl get nodes -o wide

# 3. Check system pods
kubectl get pods -n kube-system

# 4. Check K3s service status
sudo systemctl status k3s

# 5. Check K3s logs
sudo journalctl -u k3s -f
```

#### Common Causes & Solutions
- **K3s Service Down**: Restart with `sudo systemctl restart k3s`
- **Node Not Ready**: Check kubelet, network, disk space
- **Resource Exhaustion**: Check CPU, memory, disk usage
- **Network Issues**: Check Flannel CNI, firewall rules

### 3. GPU and LLM Issues

#### Symptoms
- Ollama not using GPU
- Slow inference speed
- ROCm errors

#### Diagnostic Steps
```bash
# 1. Check GPU detection
rocminfo
rocm-smi

# 2. Check ROCm libraries
ls -la /opt/rocm/
ldconfig -p | grep roc

# 3. Check Ollama GPU usage
curl http://localhost:11434/api/tags

# 4. Test GPU inference
ollama run qwen2.5-coder:14b "test"

# 5. Check ROCm kernel modules
lsmod | grep amdgpu
dmesg | grep -i rocm
```

#### Common Causes & Solutions
- **ROCm Not Loaded**: Reinstall ROCm 6.4.1, check kernel compatibility
- **GPU Not Detected**: Check PCIe, power, drivers
- **Ollama CPU Only**: Restart Ollama with GPU environment variables
- **Memory Issues**: Check VRAM usage, model size compatibility

### 4. Storage and Database Issues

#### Symptoms
- Database connection refused
- PVCs stuck in Pending state
- Service restart loops due to storage

#### Diagnostic Steps
```bash
# 1. Check PVC status
kubectl get pvc -n homelab

# 2. Check storage classes
kubectl get storageclass

# 3. Check node storage
df -h
lsblk

# 4. Test database connectivity
kubectl exec -it postgres-pod -- psql -U homelab -d homelab

# 5. Check database logs
kubectl logs -n homelab -l app=postgres
```

#### Common Causes & Solutions
- **Storage Full**: Clean up old logs, images, expand storage
- **PVC Pending**: Check storage class, node availability
- **Database Corruption**: Restart from backup, check disk health
- **Permission Issues**: Fix volume mount permissions

### 5. Network and Connectivity Issues

#### Symptoms
- Cannot access services via Tailscale
- Inter-node communication failures
- DNS resolution issues

#### Diagnostic Steps
```bash
# 1. Check Tailscale status
tailscale status

# 2. Test inter-node connectivity
ping 100.81.76.55
ping 100.72.98.106

# 3. Check service connectivity
curl -v http://100.81.76.55:30678

# 4. Check DNS resolution
nslookup postgres.homelab.svc.cluster.local

# 5. Check firewall rules
sudo ufw status
iptables -L
```

#### Common Causes & Solutions
- **Tailscale Down**: Restart Tailscale service
- **Firewall Blocking**: Open required ports, adjust rules
- **DNS Issues**: Check CoreDNS, network policies
- **MTU Issues**: Adjust MTU for Tailscale compatibility

## Service-Specific Troubleshooting

### N8n (Workflow Automation)
```bash
# Check N8n status
kubectl get pods -n homelab | grep n8n
kubectl logs -n homelab -l app=n8n

# Check database connectivity
kubectl exec -it n8n-pod -- wget -qO- postgres.homelab.svc.cluster.local:5432

# Restart N8n
kubectl rollout restart deployment/n8n -n homelab

# Common Issues:
# - Database connection errors: Check PostgreSQL status
# - Slow performance: Check resources, workflow complexity
# - Authentication issues: Check user settings, Redis cache
```

### Ollama (LLM Inference)
```bash
# Native Ollama on compute node
systemctl status ollama
journalctl -u ollama -f

# Check GPU usage
curl http://localhost:11434/api/version
ollama list

# Kubernetes Ollama
kubectl get pods -n ollama
kubectl logs -n ollama -l app=ollama

# Common Issues:
# - Models not loading: Check storage, download again
# - CPU-only inference: Check ROCm, GPU detection
# - Out of memory: Check VRAM, use smaller models
```

### PostgreSQL (Database)
```bash
# Check database pod
kubectl get pods -n homelab | grep postgres
kubectl exec -it postgres-pod -- psql -U homelab -d homelab -c "SELECT version();"

# Check database connections
kubectl exec -it postgres-pod -- psql -U homelab -d homelab -c "SELECT count(*) FROM pg_stat_activity;"

# Check disk usage
kubectl exec -it postgres-pod -- df -h /var/lib/postgresql/data

# Common Issues:
# - Connection refused: Check pod status, service configuration
# - Slow queries: Check indexes, query performance
# - Storage full: Vacuum database, clean old data
```

### Prometheus (Metrics)
```bash
# Check Prometheus
kubectl get pods -n homelab | grep prometheus
kubectl logs -n homelab -l app=prometheus

# Check targets
curl http://100.81.76.55:30090/api/v1/targets

# Check metrics collection
curl http://100.81.76.55:30090/api/v1/query?query=up

# Common Issues:
# - No targets: Check service discovery, network policies
# - Storage issues: Check PVC, disk space
# - Slow queries: Check metric cardinality, scraping intervals
```

## Log Analysis

### Log Sources by Service

#### System Logs
```bash
# Compute Node (pesubuntu)
journalctl -u ollama -f                    # Ollama service
journalctl -u promtail -f                  # Log collection
journalctl -u tailscaled -f                # VPN service
dmesg | grep -i rocm                       # GPU kernel messages

# Service Node (asuna) via SSH
ssh pesu@192.168.8.185 "sudo journalctl -u k3s -f"
ssh pesu@192.168.8.185 "sudo journalctl -u docker -f"
```

#### Kubernetes Logs
```bash
# Application logs
kubectl logs -n homelab -f deployment/n8n
kubectl logs -n homelab -f deployment/postgres
kubectl logs -n ollama -f deployment/ollama

# System logs
kubectl logs -n kube-system -f
kubectl logs -n homelab -f loki
```

#### Centralized Logs (Loki)
```bash
# Query logs via Loki API
curl -G -s "http://100.81.76.55:30314/loki/api/v1/query_range" \
  --data-urlencode 'query="{job=~\".*\"}"' \
  --data-urlencode 'start=2024-01-01T00:00:00Z' \
  --data-urlencode 'end=2024-01-02T00:00:00Z'

# Check specific service logs
curl "http://100.81.76.55:30314/loki/api/v1/query_range?query={job=\"n8n\"}"
```

### Log Patterns and Meaning

#### Common Error Patterns
- **Connection refused**: Service not running or wrong port
- **Permission denied**: Security, RBAC, or file permissions
- **Out of memory**: Resource exhaustion, memory leaks
- **No route to host**: Network connectivity issues
- **File not found**: Missing files, incorrect paths

#### Success Patterns
- **Server started**: Service initialized successfully
- **Healthy**: Service responding to health checks
- **Ready**: Container ready to accept traffic
- **Connection established**: Network connectivity working

## Performance Diagnostics

### System Performance
```bash
# CPU and Memory
top
htop
kubectl top pods -n homelab
kubectl top nodes

# Disk Usage
df -h
du -sh /var/lib/docker/
kubectl exec -it postgres-pod -- df -h

# Network
iftop
ss -tuln
kubectl get svc -n homelab
```

### GPU Performance
```bash
# GPU utilization
rocm-smi
watch -n 1 rocm-smi

# GPU memory
rocm-smi --showmemuse

# GPU processes
rocm-smi --showrep
```

### Application Performance
```bash
# Response times
curl -w "@curl-format.txt" -o /dev/null -s http://100.81.76.55:30678/healthz

# Database performance
kubectl exec -it postgres-pod -- psql -U homelab -d homelab -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Service metrics
curl http://100.81.76.55:30090/api/v1/query?query=http_request_duration_seconds_bucket
```

## Emergency Procedures

### Complete Service Recovery
```bash
# 1. Restart all critical services
kubectl rollout restart deployment/n8n -n homelab
kubectl rollout restart deployment/postgres -n homelab
kubectl rollout restart deployment/redis -n homelab

# 2. Restart compute node services
ssh pesu@100.72.98.106 "sudo systemctl restart ollama"

# 3. Clear resource issues
kubectl delete pods -n homelab --field-selector=status.phase=Failed
docker system prune -f

# 4. Verify recovery
./scripts/health-check-all.sh
```

### Disaster Recovery
```bash
# 1. Check what's running
kubectl get all -n homelab
docker ps

# 2. Restart K3s if needed
ssh pesu@192.168.8.185 "sudo systemctl restart k3s"

# 3. Reapply critical configurations
kubectl apply -f infrastructure/kubernetes/databases/
kubectl apply -f infrastructure/kubernetes/monitoring/

# 4. Restore from backups if needed
# (Manual process based on backup strategy)
```

## Preventive Maintenance

### Regular Health Checks
```bash
# Daily automated health check
./scripts/health-check-all.sh

# Weekly comprehensive check
./scripts/service-check-urls.sh
kubectl get pods -A
df -h
docker system df
```

### Resource Monitoring
- Disk usage trends
- Memory utilization patterns
- GPU performance tracking
- Network traffic analysis

### Update Procedures
- Regular OS updates (monthly)
- Application updates (as needed)
- Security patches (promptly)
- Configuration backups (before changes)

---

*This troubleshooting guide enables rapid diagnosis and resolution of homelab issues, with specific procedures for each service and system component.*