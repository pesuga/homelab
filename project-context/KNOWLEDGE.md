# Knowledge Base

Reusable patterns, troubleshooting procedures, and lessons learned.

**Last Updated**: 2025-11-26

---

## Common Patterns

### Kubernetes Deployment Pattern

**When to Use**: Deploying new services to the homelab

**Standard Pattern**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-name
  namespace: appropriate-namespace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: service-name
  template:
    metadata:
      labels:
        app: service-name
    spec:
      containers:
      - name: service-name
        image: registry/image:tag
        ports:
        - containerPort: 8080
        env:
        - name: CONFIG_VAR
          value: "value"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Key Points**:
- Always set resource requests and limits
- Use appropriate namespace
- Label consistently for service selection
- Use ConfigMaps for configuration
- Use Secrets for sensitive data

---

### Traefik IngressRoute Pattern

**When to Use**: Exposing services via HTTPS

**Standard Pattern**:
```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: service-name
  namespace: service-namespace
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`service.pesulabs.net`)
      kind: Rule
      services:
        - name: service-name
          port: 80
  tls:
    certResolver: letsencrypt
```

**Key Points**:
- Use `websecure` entrypoint for HTTPS
- Match host with proper domain
- TLS cert resolver: `letsencrypt`
- Ensure DNS points to correct IP

**Common Issues**:
- Certificate not provisioning → Check Let's Encrypt logs
- 404 errors → Verify service name and port match
- Mixed content warnings → Ensure all API calls use HTTPS

---

### PostgreSQL Deployment Pattern

**When to Use**: Adding a database for a new service

**Standard Pattern**:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-service
  namespace: service-namespace
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres-service
  template:
    metadata:
      labels:
        app: postgres-service
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: dbname
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

**Key Points**:
- Use StatefulSet (not Deployment) for databases
- Always use Secrets for credentials
- Mount persistent volume for data
- Use alpine images for smaller footprint

---

## Troubleshooting Procedures

### Service Not Responding (HTTP 502/503/504)

**Symptoms**: Service endpoint returns 5xx errors or timeouts

**Diagnostic Steps**:
1. Check pod status:
   ```bash
   kubectl get pods -n <namespace>
   ```

2. Check pod logs:
   ```bash
   kubectl logs -f <pod-name> -n <namespace>
   ```

3. Check service configuration:
   ```bash
   kubectl describe service <service-name> -n <namespace>
   ```

4. Check ingress/ingressroute:
   ```bash
   kubectl describe ingressroute <name> -n <namespace>
   ```

5. Test service internally:
   ```bash
   kubectl run curl --image=curlimages/curl -it --rm -- \
     curl http://<service-name>.<namespace>.svc.cluster.local:<port>
   ```

**Common Fixes**:
- Pod CrashLoopBackOff → Check logs for errors, fix configuration
- Service selector mismatch → Ensure labels match between deployment and service
- Port mismatch → Verify container port, service port, ingress port all align
- Resource limits → Check if pod is OOMKilled, increase memory limits

---

### Certificate Issues (HTTPS Not Working)

**Symptoms**: HTTPS endpoint returns certificate errors or uses wrong cert

**Diagnostic Steps**:
1. Check Traefik logs:
   ```bash
   kubectl logs -n kube-system -l app.kubernetes.io/name=traefik
   ```

2. Check certificate status:
   ```bash
   kubectl get certificate -A
   ```

3. Test certificate:
   ```bash
   openssl s_client -connect service.pesulabs.net:443 -servername service.pesulabs.net
   ```

**Common Fixes**:
- Rate limit hit → Wait for Let's Encrypt rate limit reset (hourly/daily)
- DNS not propagated → Verify DNS with `dig service.pesulabs.net`
- Challenge failed → Ensure port 80 accessible for HTTP-01 challenge
- Wrong cert resolver → Check IngressRoute uses `certResolver: letsencrypt`

---

### Database Connection Issues

**Symptoms**: Application can't connect to PostgreSQL

**Diagnostic Steps**:
1. Verify database pod running:
   ```bash
   kubectl get pods -n <namespace> -l app=postgres
   ```

2. Check database logs:
   ```bash
   kubectl logs <postgres-pod> -n <namespace>
   ```

3. Test connection from app pod:
   ```bash
   kubectl exec -it <app-pod> -n <namespace> -- \
     psql -h <db-service> -U <user> -d <dbname>
   ```

4. Verify service DNS:
   ```bash
   kubectl exec -it <app-pod> -n <namespace> -- \
     nslookup <db-service>.<namespace>.svc.cluster.local
   ```

**Common Fixes**:
- Wrong credentials → Check Secret values
- Wrong host → Use full service DNS: `service.namespace.svc.cluster.local`
- Database not initialized → Check if database schema needs creation
- Connection pool exhausted → Adjust max_connections in PostgreSQL config

---

### GPU Not Available in Ollama

**Symptoms**: Ollama not using GPU, slow inference

**Diagnostic Steps**:
1. Check GPU status on compute node:
   ```bash
   ssh pesu@100.72.98.106 'rocm-smi'
   ```

2. Check Ollama process:
   ```bash
   ssh pesu@100.72.98.106 'ps aux | grep ollama'
   ```

3. Check Ollama logs:
   ```bash
   ssh pesu@100.72.98.106 'journalctl -u ollama -f'
   ```

4. Test GPU with simple task:
   ```bash
   curl http://100.72.98.106:11434/api/generate -d '{
     "model": "llama2",
     "prompt": "test"
   }'
   ```

**Common Fixes**:
- ROCm not loaded → Restart ollama service
- Wrong model → Ensure model supports GPU acceleration
- Driver issues → Reinstall ROCm drivers
- Memory issues → Check GPU VRAM usage

---

## Configuration Patterns

### Environment Variable Configuration

**Pattern**: Use ConfigMaps for non-sensitive config, Secrets for sensitive data

**ConfigMap Example**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: app-namespace
data:
  API_URL: "https://api.example.com"
  LOG_LEVEL: "info"
  FEATURE_FLAG: "enabled"
```

**Secret Example**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: app-namespace
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@host:5432/db"
  API_KEY: "secret-key-here"
```

**Usage in Deployment**:
```yaml
env:
  - name: API_URL
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: API_URL
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: DATABASE_URL
```

---

### Health Check Pattern

**Pattern**: Always implement health checks for services

**Kubernetes Probes**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

**FastAPI Health Endpoint**:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    # Check database connection
    try:
        await db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")
```

---

## Lessons Learned

### Mixed Content Errors (2025-11-15)

**Problem**: Dashboard loading over HTTPS but making HTTP API calls, causing mixed content errors

**Root Cause**: API routes hardcoded with `http://` instead of using relative paths or HTTPS

**Solution**:
- Use relative paths for same-origin API calls
- Use full HTTPS URLs for cross-origin calls
- Configure CORS properly for HTTPS

**Prevention**:
- Always use HTTPS in production
- Test in production-like environment
- Use environment variables for API URLs

---

### Traefik Port Configuration (Previous)

**Problem**: Initially configured Traefik with wrong port, causing certificate provisioning failures

**Root Cause**: Misunderstanding of Traefik's entrypoint configuration

**Solution**:
- Use port 443 for `websecure` entrypoint
- Use port 80 for `web` entrypoint (HTTP → HTTPS redirect)
- Let Traefik handle TLS termination

**Prevention**:
- Always consult official documentation for infrastructure tools
- Test with curl before declaring success
- Use validation hooks to catch configuration issues

---

### Database Migration Without Backup (Previous)

**Problem**: Attempted migration from SQLite to PostgreSQL without proper backup

**Root Cause**: Rushing deployment without following proper procedures

**Solution**:
- Always backup before migrations
- Test migration on copy first
- Have rollback plan ready

**Prevention**:
- Create backup automation
- Document migration procedures
- Use validation gates for risky operations

---

## Best Practices

### Deployment Workflow

1. **Develop locally** with docker-compose or similar
2. **Test changes** in isolated environment
3. **Create backup** of existing deployment
4. **Apply changes** with kubectl
5. **Validate deployment** with health checks
6. **Monitor logs** for issues
7. **Rollback if needed** with previous version

### Validation Before Claims

- Never claim "service working" without actual verification
- Use `/verify-claim` command for validation
- Check both HTTP status and actual functionality
- Test from external network, not just internal

### Documentation Maintenance

- Update SERVICES.md after deployments
- Record architecture decisions in ARCHITECTURE.md
- Capture patterns immediately when discovered
- Review knowledge base quarterly for accuracy

---

**Contribution Guidelines**:
- Add new patterns as you discover them
- Update troubleshooting procedures with new solutions
- Record lessons learned immediately after incidents
- Keep examples up-to-date with current configurations
