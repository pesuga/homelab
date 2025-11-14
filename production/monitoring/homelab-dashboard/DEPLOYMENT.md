# Homelab Dashboard - Deployment Guide

## Prerequisites

- K3s cluster running with PostgreSQL deployed
- Docker registry accessible at `100.81.76.55:30500`
- `kubectl` configured to access your cluster
- Traefik ingress controller with cert-manager

## Quick Deployment

### Option 1: Automated Script (Recommended)

```bash
cd services/homelab-dashboard
./scripts/deploy.sh
```

The script will:
1. Build Docker image
2. Push to local registry
3. Initialize PostgreSQL schema
4. Deploy to Kubernetes
5. Verify deployment

### Option 2: Manual Deployment

#### Step 1: Build and Push Image

```bash
cd services/homelab-dashboard

# Build image
docker build -t homelab-dashboard:latest .

# Tag for registry
docker tag homelab-dashboard:latest 100.81.76.55:30500/homelab-dashboard:latest

# Push to registry
docker push 100.81.76.55:30500/homelab-dashboard:latest
```

#### Step 2: Initialize Database Schema

```bash
# Copy schema to PostgreSQL pod
kubectl cp database/schema.sql homelab/postgres-0:/tmp/schema.sql

# Execute schema
kubectl exec -n homelab -it postgres-0 -- \
  psql -U homelab -d homelab -f /tmp/schema.sql
```

#### Step 3: Update Secrets (IMPORTANT!)

**Generate a strong secret key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Edit the secret in `k8s/deployment.yaml`:**
```yaml
stringData:
  secret-key: "YOUR_GENERATED_KEY_HERE"      # Replace with generated key
  username: "admin"                           # Change if desired
  password: "YOUR_STRONG_PASSWORD_HERE"       # Use a strong password!
  admin-email: "your-email@example.com"       # Optional
```

**Best Practices for Passwords:**
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, special characters
- Avoid dictionary words
- Don't reuse passwords from other systems

#### Step 4: Deploy to Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Wait for rollout
kubectl rollout status deployment/homelab-dashboard -n homelab

# Check pod status
kubectl get pods -n homelab -l app=homelab-dashboard
```

#### Step 5: Verify Deployment

```bash
# Check pod logs
POD_NAME=$(kubectl get pod -n homelab -l app=homelab-dashboard -o jsonpath="{.items[0].metadata.name}")
kubectl logs -n homelab $POD_NAME

# Test health endpoint
kubectl exec -n homelab $POD_NAME -- wget -q -O- http://localhost:5000/health

# Expected output: {"status":"healthy","timestamp":"2025-10-28T..."}
```

## Access the Dashboard

### Via Ingress (HTTPS)
```
URL: https://dash.pesulabs.net
```

### Via NodePort (HTTP - Local Network)
```
URL: http://100.81.76.55:30800
```

### Via Port Forward (Testing)
```bash
kubectl port-forward -n homelab svc/homelab-dashboard 5000:80
# Access: http://localhost:5000
```

## Initial Login

1. Navigate to dashboard URL
2. Login with credentials from K8s Secret:
   - Username: `admin` (or your configured username)
   - Password: From `dashboard-secrets` secret
3. **IMPORTANT**: Change password immediately after first login

## Post-Deployment Configuration

### 1. Change Default Password

After first login, you'll need to manually update the password in PostgreSQL:

```bash
# Generate new password hash in Python
python3 << EOF
from werkzeug.security import generate_password_hash
password = "YourNewStrongPassword123!"
print(generate_password_hash(password))
EOF

# Update in database
kubectl exec -n homelab -it postgres-0 -- \
  psql -U homelab -d homelab -c \
  "UPDATE users SET password_hash = 'PASTE_HASH_HERE' WHERE username = 'admin';"
```

*Note: Password change UI will be added in future version*

### 2. Configure Rate Limiting with Redis (Optional)

For production use with multiple replicas, configure Redis backend:

**Update `app.py` line 38:**
```python
storage_uri="redis://redis.homelab.svc.cluster.local:6379"
```

**Rebuild and redeploy:**
```bash
./scripts/deploy.sh
```

### 3. Restrict Access to Tailscale Network (Recommended)

**Create Traefik middleware:**
```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: tailscale-whitelist
  namespace: homelab
spec:
  ipWhiteList:
    sourceRange:
      - 100.64.0.0/10  # Tailscale CGNAT range
```

**Update Ingress annotation:**
```yaml
annotations:
  traefik.ingress.kubernetes.io/router.middlewares: homelab-tailscale-whitelist@kubernetescrd
```

### 4. Set Up Monitoring

**View Logs:**
```bash
# Real-time logs
kubectl logs -f -n homelab -l app=homelab-dashboard

# Filter for security events
kubectl logs -n homelab -l app=homelab-dashboard | grep -E "(login|audit|security)"
```

**Prometheus Metrics (Future Enhancement):**
- Login success/failure rates
- Active sessions count
- Rate limit hits
- Response times

## Troubleshooting

### Pod Won't Start

**Check pod events:**
```bash
kubectl describe pod -n homelab -l app=homelab-dashboard
```

**Common issues:**
- Image pull failure: Verify registry is accessible
- Secret missing: Ensure `dashboard-secrets` exists
- Database connection: Check PostgreSQL is running and accessible

### Database Connection Errors

**Verify PostgreSQL:**
```bash
kubectl get pods -n homelab -l app=postgres
kubectl logs -n homelab postgres-0 --tail=50
```

**Test connection from dashboard pod:**
```bash
kubectl exec -n homelab $POD_NAME -- \
  python3 -c "import psycopg2; psycopg2.connect(host='postgres.homelab.svc.cluster.local', database='homelab', user='homelab', password='YOUR_PASSWORD')"
```

### Login Issues

**Check audit logs:**
```bash
kubectl exec -n homelab -it postgres-0 -- \
  psql -U homelab -d homelab -c "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 20;"
```

**Verify user exists:**
```bash
kubectl exec -n homelab -it postgres-0 -- \
  psql -U homelab -d homelab -c "SELECT username, is_active, failed_login_attempts, locked_until FROM users;"
```

**Unlock locked account manually:**
```bash
kubectl exec -n homelab -it postgres-0 -- \
  psql -U homelab -d homelab -c "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE username = 'admin';"
```

### CSRF Token Errors

**Clear browser cookies:**
- Delete all cookies for `dash.pesulabs.net`
- Clear browser cache
- Try in incognito mode

**Verify CSRF protection is active:**
```bash
kubectl logs -n homelab $POD_NAME | grep -i csrf
```

### Rate Limit Exceeded

**Check IP address:**
```bash
# From logs
kubectl logs -n homelab $POD_NAME | grep "Rate limit exceeded"

# Clear rate limit (restart pod)
kubectl delete pod -n homelab -l app=homelab-dashboard
```

**Adjust rate limits if needed** (in `app.py:37` and `app.py:214`)

## Backup & Recovery

### Backup Database

```bash
# Full database backup
kubectl exec -n homelab postgres-0 -- \
  pg_dump -U homelab homelab > homelab-dashboard-backup-$(date +%Y%m%d).sql

# Backup users and audit logs only
kubectl exec -n homelab postgres-0 -- \
  pg_dump -U homelab -t users -t audit_logs -t sessions homelab > dashboard-data-backup-$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Restore full backup
cat homelab-dashboard-backup-20251028.sql | \
  kubectl exec -i -n homelab postgres-0 -- psql -U homelab homelab
```

### Backup Secrets

```bash
# Export secrets to file (KEEP SECURE!)
kubectl get secret dashboard-secrets -n homelab -o yaml > dashboard-secrets-backup.yaml

# Restore secrets
kubectl apply -f dashboard-secrets-backup.yaml
```

## Scaling

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: homelab-dashboard
  namespace: homelab
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: homelab-dashboard
  minReplicas: 1
  maxReplicas: 3
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Note**: When scaling beyond 1 replica, use Redis for rate limiting:
```python
storage_uri="redis://redis.homelab.svc.cluster.local:6379"
```

## Updating the Application

### Rolling Update

```bash
# Build new image with version tag
docker build -t homelab-dashboard:v2.0 .
docker tag homelab-dashboard:v2.0 100.81.76.55:30500/homelab-dashboard:v2.0
docker push 100.81.76.55:30500/homelab-dashboard:v2.0

# Update deployment
kubectl set image deployment/homelab-dashboard \
  dashboard=100.81.76.55:30500/homelab-dashboard:v2.0 \
  -n homelab

# Monitor rollout
kubectl rollout status deployment/homelab-dashboard -n homelab

# Rollback if needed
kubectl rollout undo deployment/homelab-dashboard -n homelab
```

### Database Schema Migration

When updating schema:

```bash
# 1. Backup current database
kubectl exec -n homelab postgres-0 -- pg_dump -U homelab homelab > backup-pre-migration.sql

# 2. Apply migration SQL
kubectl exec -n homelab -it postgres-0 -- \
  psql -U homelab -d homelab -f /tmp/migration.sql

# 3. Verify migration
kubectl exec -n homelab -it postgres-0 -- \
  psql -U homelab -d homelab -c "\d users"
```

## Monitoring & Maintenance

### Health Checks

```bash
# Manual health check
curl -k https://dash.pesulabs.net/health

# Automated monitoring with Prometheus
# Add ServiceMonitor for scraping metrics (future enhancement)
```

### Log Rotation

Kubernetes handles container log rotation automatically. For audit logs in PostgreSQL:

```sql
-- Archive old audit logs (older than 90 days)
CREATE TABLE audit_logs_archive AS
SELECT * FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';
```

### Security Maintenance

**Monthly:**
- Review audit logs for suspicious activity
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Rotate secrets (SECRET_KEY, passwords)

**Quarterly:**
- Full security audit
- Penetration testing (if applicable)
- Review and update access controls

## Environment-Specific Configuration

### Development

```yaml
# Relaxed security for local development
spec:
  containers:
  - env:
    - name: FLASK_DEBUG
      value: "true"
    - name: CSRF_ENABLED
      value: "false"  # Only for local dev!
```

### Production

```yaml
# Strict security for production
spec:
  replicas: 2  # High availability
  containers:
  - env:
    - name: FLASK_DEBUG
      value: "false"
    - name: SESSION_COOKIE_SECURE
      value: "true"
    # Use Redis for rate limiting
```

## Support

For issues or questions:
- Check logs: `kubectl logs -n homelab -l app=homelab-dashboard`
- Review [SECURITY.md](SECURITY.md) for security-specific guidance
- Open GitHub issue: https://github.com/pesuga/homelab/issues

## Next Steps

1. ✅ Deploy dashboard
2. ✅ Login and verify functionality
3. ✅ Change default password
4. 📋 Add more users (via PostgreSQL for now, UI coming soon)
5. 📊 Set up monitoring and alerting
6. 🔐 Consider enabling MFA (future feature)
7. 🌐 Restrict access to Tailscale network
