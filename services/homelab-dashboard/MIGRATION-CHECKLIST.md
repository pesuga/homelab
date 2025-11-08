# Migration Checklist: Upgrading to Secure Dashboard

This checklist guides you through upgrading from the basic dashboard to the secure version.

## Pre-Migration

- [ ] **Backup current dashboard data** (if any)
  ```bash
  kubectl get all -n homelab -l app=homelab-dashboard -o yaml > dashboard-backup-old.yaml
  ```

- [ ] **Verify PostgreSQL is running**
  ```bash
  kubectl get pods -n homelab -l app=postgres
  # Should show STATUS: Running
  ```

- [ ] **Check PostgreSQL credentials**
  ```bash
  kubectl get secret postgres-secret -n homelab -o jsonpath="{.data.password}" | base64 -d
  # Save this password - you'll need it
  ```

- [ ] **Ensure Docker registry is accessible**
  ```bash
  curl -k https://100.81.76.55:30500/v2/_catalog
  # Should return: {"repositories":[...]}
  ```

## Migration Steps

### Step 1: Generate Secure Credentials

- [ ] **Generate Flask secret key**
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  # Copy output: _________________________________
  ```

- [ ] **Choose strong admin password**
  - Minimum 12 characters
  - Mix of uppercase, lowercase, numbers, symbols
  - Password: _________________________________

- [ ] **Update `k8s/deployment.yaml`** with generated values
  ```yaml
  stringData:
    secret-key: "PASTE_SECRET_KEY_HERE"
    username: "admin"  # or change username
    password: "PASTE_STRONG_PASSWORD_HERE"
    admin-email: "your-email@example.com"
  ```

### Step 2: Initialize Database

- [ ] **Apply database schema**
  ```bash
  # Copy schema to PostgreSQL pod
  kubectl cp services/homelab-dashboard/database/schema.sql \
    homelab/postgres-0:/tmp/schema.sql

  # Execute schema
  kubectl exec -n homelab -it postgres-0 -- \
    psql -U homelab -d homelab -f /tmp/schema.sql
  ```

- [ ] **Verify tables created**
  ```bash
  kubectl exec -n homelab -it postgres-0 -- \
    psql -U homelab -d homelab -c "\dt"

  # Should show: users, audit_logs, sessions, password_history
  ```

### Step 3: Build and Deploy

- [ ] **Navigate to dashboard directory**
  ```bash
  cd /home/pesu/Rakuflow/systems/homelab/services/homelab-dashboard
  ```

- [ ] **Run deployment script** (recommended)
  ```bash
  ./scripts/deploy.sh
  ```

  **OR manually:**

  - [ ] Build Docker image
    ```bash
    docker build -t homelab-dashboard:secure .
    ```

  - [ ] Tag for registry
    ```bash
    docker tag homelab-dashboard:secure 100.81.76.55:30500/homelab-dashboard:latest
    ```

  - [ ] Push to registry
    ```bash
    docker push 100.81.76.55:30500/homelab-dashboard:latest
    ```

  - [ ] Apply Kubernetes manifests
    ```bash
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml
    ```

### Step 4: Verify Deployment

- [ ] **Check pod status**
  ```bash
  kubectl get pods -n homelab -l app=homelab-dashboard
  # STATUS should be: Running
  ```

- [ ] **Check deployment logs**
  ```bash
  POD_NAME=$(kubectl get pod -n homelab -l app=homelab-dashboard -o jsonpath="{.items[0].metadata.name}")
  kubectl logs -n homelab $POD_NAME

  # Should see:
  # ✅ Database schema initialized successfully
  # ✅ Default admin user created
  # ✅ Homelab Dashboard initialized successfully
  ```

- [ ] **Test health endpoint**
  ```bash
  kubectl exec -n homelab $POD_NAME -- wget -q -O- http://localhost:5000/health

  # Should return: {"status":"healthy","timestamp":"..."}
  ```

- [ ] **Verify service is accessible**
  ```bash
  kubectl get svc -n homelab homelab-dashboard

  # Check NodePort is 30800
  ```

### Step 5: Test Security Features

- [ ] **Access dashboard**
  - Via HTTPS: https://dash.pesulabs.net
  - Via NodePort: http://100.81.76.55:30800

- [ ] **Login with admin credentials**
  - Username: (from your K8s Secret)
  - Password: (from your K8s Secret)
  - Should successfully redirect to dashboard

- [ ] **Verify CSRF protection**
  ```bash
  # This should FAIL (no CSRF token)
  curl -X POST https://dash.pesulabs.net/login \
    -d "username=admin&password=wrong" -L

  # Should see CSRF error or no login
  ```

- [ ] **Test rate limiting**
  ```bash
  # Try 6 rapid login attempts
  for i in {1..6}; do
    curl -X POST https://dash.pesulabs.net/login \
      -d "username=admin&password=wrong" -L -s | grep -q "429\|Too many"
    echo "Attempt $i"
  done

  # 6th attempt should show rate limit error
  ```

- [ ] **Test account lockout**
  - Make 5 failed login attempts via browser
  - Should see: "Account locked for 15 minutes"

- [ ] **Verify audit logging**
  ```bash
  kubectl exec -n homelab -it postgres-0 -- \
    psql -U homelab -d homelab -c \
    "SELECT username, event_type, event_status, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10;"

  # Should see your login attempts logged
  ```

### Step 6: Post-Deployment Configuration

- [ ] **Change admin password** (if not already done)
  ```bash
  # Generate password hash
  python3 << EOF
  from werkzeug.security import generate_password_hash
  password = "YourNewSecurePassword123!"
  print(generate_password_hash(password))
  EOF

  # Update in database
  kubectl exec -n homelab -it postgres-0 -- \
    psql -U homelab -d homelab -c \
    "UPDATE users SET password_hash = 'PASTE_HASH_HERE' WHERE username = 'admin';"
  ```

- [ ] **Test new password** by logging out and back in

- [ ] **Configure monitoring** (optional)
  ```bash
  # Set up log monitoring with Grafana
  # Set up alerts for failed login attempts
  # Set up alerts for account lockouts
  ```

- [ ] **Restrict network access** (recommended)
  - Consider limiting to Tailscale network only
  - See DEPLOYMENT.md for Traefik middleware configuration

## Post-Migration Verification

### Functional Tests

- [ ] Login works with correct credentials
- [ ] Logout works and clears session
- [ ] All service links are displayed correctly
- [ ] Dashboard loads without errors
- [ ] API endpoints return data (if admin)

### Security Tests

- [ ] CSRF protection blocks unauthenticated POST requests
- [ ] Rate limiting triggers after 5 login attempts
- [ ] Account locks after 5 failed attempts
- [ ] Session expires after 4 hours
- [ ] Session expires after 30 minutes of inactivity
- [ ] Security headers present in responses
  ```bash
  curl -I https://dash.pesulabs.net
  # Check for: Strict-Transport-Security, X-Frame-Options, etc.
  ```

### Database Verification

- [ ] User exists in database
  ```bash
  kubectl exec -n homelab -it postgres-0 -- \
    psql -U homelab -d homelab -c "SELECT username, is_admin, is_active FROM users;"
  ```

- [ ] Audit logs are being created
  ```bash
  kubectl exec -n homelab -it postgres-0 -- \
    psql -U homelab -d homelab -c "SELECT COUNT(*) FROM audit_logs;"
  ```

- [ ] Sessions are tracked
  ```bash
  kubectl exec -n homelab -it postgres-0 -- \
    psql -U homelab -d homelab -c "SELECT * FROM sessions WHERE is_active = TRUE;"
  ```

## Rollback Plan (If Needed)

If something goes wrong:

- [ ] **Restore old deployment**
  ```bash
  kubectl apply -f dashboard-backup-old.yaml
  ```

- [ ] **Revert database changes** (if needed)
  ```bash
  kubectl exec -n homelab -it postgres-0 -- \
    psql -U homelab -d homelab -c "DROP TABLE IF EXISTS users, audit_logs, sessions, password_history CASCADE;"
  ```

- [ ] **Clear secrets** (if needed)
  ```bash
  kubectl delete secret dashboard-secrets -n homelab
  # Re-create with old values
  ```

## Documentation Review

After successful migration:

- [ ] Read [SECURITY.md](SECURITY.md) for security features
- [ ] Read [DEPLOYMENT.md](DEPLOYMENT.md) for operational guidance
- [ ] Read [README.md](README.md) for overview
- [ ] Bookmark troubleshooting section in DEPLOYMENT.md

## Ongoing Maintenance

Set up recurring tasks:

- [ ] **Weekly**: Review audit logs for suspicious activity
- [ ] **Monthly**: Check for dependency updates
- [ ] **Quarterly**: Rotate secrets and passwords
- [ ] **As needed**: Add/remove users via database

## Support

If you encounter issues:

1. Check pod logs: `kubectl logs -n homelab -l app=homelab-dashboard`
2. Review [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section
3. Check database connectivity
4. Verify secrets are correctly set
5. Open GitHub issue if needed

---

## Success Criteria

You've successfully migrated when:

✅ Dashboard loads at https://dash.pesulabs.net
✅ Login works with new credentials
✅ No errors in pod logs
✅ Audit logs show login events
✅ Rate limiting and lockout work
✅ Session timeout functions correctly
✅ Security headers present

**Congratulations! Your dashboard is now secured with production-ready authentication.**

---

**Estimated Migration Time**: 30-45 minutes

**Difficulty**: Medium (requires database and Kubernetes familiarity)

**Can be reversed**: Yes (rollback plan provided)
