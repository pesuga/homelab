# Security Remediation Plan
**Date**: 2025-10-31
**Status**: Action Required - Public Repository with Exposed Credentials

## Executive Summary

Following the security audit, this plan provides step-by-step remediation for exposed credentials in the public GitHub repository. The approach uses Kubernetes Secrets with externalized values to prevent future credential leaks.

## Critical Findings Recap

**Exposed Credentials**:
- PostgreSQL password: `homelab123` (3+ files)
- Grafana admin password: `admin123`
- Dashboard password: `ChangeMe!2024#Secure`

**Impact**: Anyone with repository access can connect to services and access data.

## Remediation Strategy

### Phase 1: Create Secure Secret Management (IMMEDIATE)

**Approach**: Use Kubernetes Secrets with externalized values
- Secrets manifests committed to Git **without** sensitive values
- Actual credentials created manually via `kubectl create secret`
- Documentation updated with "create your own" instructions

**Why this approach**:
- ✅ No sensitive data in Git history
- ✅ Simple to implement immediately
- ✅ Compatible with existing GitOps workflow
- ✅ Can migrate to Sealed Secrets/SOPS later

### Phase 2: Rotate All Credentials (IMMEDIATE)

New credentials will be generated and stored only in cluster:

```bash
# Generate strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
GRAFANA_PASSWORD=$(openssl rand -base64 24)
DASHBOARD_PASSWORD=$(openssl rand -base64 24)
```

### Phase 3: Update Deployments (SHORT-TERM)

Remove hardcoded values from:
1. ConfigMaps (DATABASE_URL connection strings)
2. Deployment manifests (environment variables)
3. Documentation (credential examples)

## Detailed Remediation Steps

### 1. PostgreSQL Secret Remediation

**Current state** (`infrastructure/kubernetes/databases/postgres/postgres.yaml:14`):
```yaml
stringData:
  POSTGRES_PASSWORD: homelab123  # ❌ EXPOSED
```

**Remediated state** (Secret template):
```yaml
# infrastructure/kubernetes/databases/postgres/postgres-secret-template.yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: homelab
type: Opaque
stringData:
  POSTGRES_USER: homelab
  POSTGRES_PASSWORD: REPLACE_WITH_YOUR_PASSWORD  # ⚠️ NOT COMMITTED
  POSTGRES_DB: homelab
```

**Manual creation** (not committed):
```bash
# scripts/secrets/create-postgres-secret.sh
kubectl create secret generic postgres-secret \
  --namespace=homelab \
  --from-literal=POSTGRES_USER=homelab \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 32)" \
  --from-literal=POSTGRES_DB=homelab \
  --dry-run=client -o yaml | kubectl apply -f -
```

**Deployment changes**:
- postgres.yaml: Remove stringData section entirely (lines 12-15)
- Add comment: "# Secret created manually - see scripts/secrets/create-postgres-secret.sh"

### 2. LobeChat Secret Remediation

**Issues**:
1. `lobechat.yaml:16` - DATABASE_URL with embedded password in ConfigMap
2. `lobechat.yaml:75` - DB_PASSWORD in Secret stringData

**Remediated approach** - Use environment variable substitution:

**ConfigMap** (no password):
```yaml
data:
  DATABASE_DRIVER: "node"
  # Connection string uses environment variable substitution
  # Actual password injected from lobechat-secret
```

**Deployment** (environment variables):
```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: lobechat-secret
        key: DB_PASSWORD
  - name: DATABASE_URL
    value: "postgresql://homelab:$(DB_PASSWORD)@postgres.homelab.svc.cluster.local:5432/lobechat"
```

**Secret creation script**:
```bash
# scripts/secrets/create-lobechat-secret.sh
kubectl create secret generic lobechat-secret \
  --namespace=homelab \
  --from-literal=DB_PASSWORD="$(openssl rand -base64 32)" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Grafana Secret Remediation

**Current state** (`infrastructure/kubernetes/monitoring/grafana-deployment.yaml`):
```yaml
env:
  - name: GF_SECURITY_ADMIN_PASSWORD
    value: admin123  # ❌ EXPOSED
```

**Remediated state**:
```yaml
env:
  - name: GF_SECURITY_ADMIN_PASSWORD
    valueFrom:
      secretKeyRef:
        name: grafana-secret
        key: admin-password
```

**Secret creation**:
```bash
# scripts/secrets/create-grafana-secret.sh
kubectl create secret generic grafana-secret \
  --namespace=homelab \
  --from-literal=admin-password="$(openssl rand -base64 24)" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 4. Homelab Dashboard Secret Remediation

**Current state** (`services/homelab-dashboard/k8s/deployment.yaml:91`):
```yaml
stringData:
  password: "ChangeMe!2024#Secure"  # ❌ EXPOSED
```

**Remediated state** (Secret template):
```yaml
# Template - actual secret created manually
apiVersion: v1
kind: Secret
metadata:
  name: dashboard-secret
  namespace: homelab
type: Opaque
# stringData removed - create manually
```

**Creation script**:
```bash
# scripts/secrets/create-dashboard-secret.sh
kubectl create secret generic dashboard-secret \
  --namespace=homelab \
  --from-literal=password="$(openssl rand -base64 24)" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 5. Flowise Secret Remediation

**Current state** (`infrastructure/kubernetes/flowise/flowise-deployment.yaml`):
```yaml
data:
  DATABASE_PASSWORD: "homelab123"  # ❌ EXPOSED
```

**Remediated state**:
```yaml
env:
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: postgres-secret  # Reuse PostgreSQL secret
        key: POSTGRES_PASSWORD
```

## .gitignore Updates

Add patterns to prevent future credential leaks:

```gitignore
# Kubernetes Secrets (actual values)
*-secret.yaml
!*-secret-template.yaml
secrets/
.env.production
.env.local

# Backup files that may contain credentials
*.backup
*.bak

# Temporary credential files
credentials/
keys/
*.key
*.pem
```

## Documentation Updates

### Files Requiring Updates

1. **README.md**
   - Remove hardcoded credential examples
   - Add link to secret creation guide
   - Update "Access Dashboards" section with "create your own credentials"

2. **docs/*.md**
   - Replace credential examples with placeholders
   - Add "See scripts/secrets/create-*.sh" references

3. **CLAUDE.md**
   - Update "Common Commands" with secret creation workflow
   - Remove default credential references

### New Documentation

Create `docs/SECRETS-MANAGEMENT.md`:
```markdown
# Secrets Management Guide

## Initial Setup

Run secret creation scripts in order:

```bash
# 1. PostgreSQL (required first)
./scripts/secrets/create-postgres-secret.sh

# 2. Application secrets
./scripts/secrets/create-lobechat-secret.sh
./scripts/secrets/create-grafana-secret.sh
./scripts/secrets/create-dashboard-secret.sh

# 3. Verify creation
kubectl get secrets -n homelab
```

## Rotating Credentials

To rotate a password:

```bash
# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. Update secret
kubectl create secret generic SECRET_NAME \
  --from-literal=KEY="$NEW_PASSWORD" \
  --namespace=homelab \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart affected deployments
kubectl rollout restart deployment/DEPLOYMENT_NAME -n homelab
```
```

## Implementation Timeline

### Immediate (Today)

1. ✅ Create `scripts/secrets/` directory
2. ✅ Write secret creation scripts
3. ✅ Create secret template files
4. ✅ Update .gitignore
5. ⏳ Update deployment manifests to reference secrets
6. ⏳ Test deployment with new secrets

### Short-Term (This Week)

7. ⏳ Rotate all credentials using scripts
8. ⏳ Update all documentation
9. ⏳ Remove hardcoded values from all YAML files
10. ⏳ Commit and push changes

### Long-Term (Optional)

11. Consider git history cleanup with `git-filter-repo`
12. Implement Sealed Secrets or SOPS for encrypted secrets in Git
13. Set up pre-commit hooks (gitleaks, detect-secrets)
14. Enable GitHub secret scanning

## Migration Checklist

- [ ] Create scripts/secrets/ directory structure
- [ ] Write all secret creation scripts
- [ ] Create secret template files (without values)
- [ ] Update .gitignore with secret patterns
- [ ] Update postgres.yaml to remove stringData
- [ ] Update lobechat.yaml to use env var substitution
- [ ] Update grafana-deployment.yaml to use secretKeyRef
- [ ] Update dashboard deployment to use secretKeyRef
- [ ] Update flowise-deployment.yaml to use secretKeyRef
- [ ] Create docs/SECRETS-MANAGEMENT.md
- [ ] Update README.md to remove credentials
- [ ] Update CLAUDE.md with secret workflow
- [ ] Test: Deploy with new secret management
- [ ] Rotate all credentials
- [ ] Commit and push remediated code

## Security Best Practices Going Forward

1. **Never commit credentials** - Always use Secret templates
2. **Generate strong passwords** - Use `openssl rand -base64 32`
3. **Rotate regularly** - Change passwords every 90 days
4. **Use RBAC** - Limit who can read secrets in cluster
5. **Audit access** - Monitor secret access via K8s audit logs
6. **Backup secrets** - Encrypted backup of secret values (off-Git)

## Recovery Procedure

If credentials are accidentally committed:

```bash
# 1. Immediately rotate the exposed credential
kubectl create secret generic SECRET_NAME \
  --from-literal=KEY="$(openssl rand -base64 32)" \
  --namespace=homelab \
  --dry-run=client -o yaml | kubectl apply -f -

# 2. Restart affected services
kubectl rollout restart deployment/SERVICE -n homelab

# 3. Remove from Git history (coordinate with team)
git filter-repo --path PATH_TO_FILE --invert-paths
git push origin --force --all

# 4. Notify GitHub to invalidate the exposed secret
```

## Notes

- Secret values are **never** committed to Git
- Scripts generate secrets locally and apply directly to cluster
- Templates in Git show structure but contain placeholders
- This approach is secure and GitOps-compatible
- Migration to Sealed Secrets can happen later without disrupting workflow
