# Homelab Dashboard - Security Documentation

## Overview

This document describes the comprehensive security enhancements implemented in the Homelab Dashboard to protect sensitive homelab data and infrastructure access.

## Security Features Implemented

### 1. Authentication & Authorization

#### Database-Backed User Management
- **PostgreSQL Integration**: Users stored in `homelab` database, not in-memory
- **Password Hashing**: Werkzeug bcrypt-based hashing (PBKDF2-SHA256)
- **User Attributes**:
  - Username (unique, 3+ chars, alphanumeric + `_-`)
  - Email (optional)
  - Active status flag
  - Admin role flag
  - Last login timestamp and IP
  - Failed login attempt counter
  - Account lock timestamp

#### Account Lockout Protection
- **Failed Attempt Tracking**: Counter increments on each failed login
- **Automatic Locking**: Account locked after 5 failed attempts
- **Lockout Duration**: 15 minutes (configurable in `database.py:137`)
- **Auto-Unlock**: Lock expires automatically after duration
- **Audit Trail**: All lockout events logged to audit table

### 2. Session Management

#### Enhanced Security
- **Session Lifetime**: Reduced from 24 hours to 4 hours (`app.py:27`)
- **Inactivity Timeout**: 30 minutes of inactivity triggers session expiration (`database.py:276`)
- **Session Tokens**: Cryptographically random 64-character tokens
- **Database Tracking**: All active sessions stored in `sessions` table
- **Session Fixation Prevention**: Session cleared and regenerated on login
- **Secure Cookies**:
  - `Secure` flag: HTTPS only
  - `HttpOnly` flag: No JavaScript access
  - `SameSite=Lax`: CSRF protection

### 3. CSRF Protection

- **Flask-WTF**: Automatic CSRF token generation and validation
- **Token in Forms**: All POST forms include hidden CSRF token (`login.html:28`)
- **Header Support**: Accepts tokens in `X-CSRFToken` header
- **Exemptions**: Only `/health` endpoint exempt (no state changes)

### 4. Rate Limiting

#### Flask-Limiter Configuration
- **Global Limits**: 200 requests/day, 50 requests/hour per IP
- **Login Endpoint**: Strict 5 attempts per 15 minutes (`app.py:214`)
- **Storage**: In-memory (upgrade to Redis for production: `redis://redis.homelab.svc.cluster.local:6379`)
- **429 Handling**: Custom error page with audit logging

### 5. Security Headers

#### Flask-Talisman Implementation
- **HSTS**: Strict-Transport-Security with 1-year max-age
- **Content Security Policy**:
  - `default-src 'self'`: Only load resources from same origin
  - `script-src 'self' 'unsafe-inline'`: Scripts from app only (adjust if needed)
  - `style-src 'self' 'unsafe-inline'`: Styles from app only
  - `img-src 'self' data: https:`: Images from app, data URIs, HTTPS
  - `frame-ancestors 'none'`: Prevent clickjacking (X-Frame-Options: DENY)
- **X-Content-Type-Options**: `nosniff` to prevent MIME sniffing
- **X-XSS-Protection**: Legacy XSS filter enabled

### 6. Audit Logging

#### Comprehensive Event Tracking
**Logged Events**:
- `login_success`: Successful authentication
- `login_failed`: Invalid credentials or validation failure
- `logout`: User-initiated logout
- `account_locked`: Too many failed attempts
- `account_unlocked`: Manual or automatic unlock
- `password_changed`: Password update
- `user_created`: New user account
- `user_deleted`: Account deletion
- `session_expired`: Timeout or expiration
- `access_denied`: Authorization failure or rate limit

**Event Attributes**:
- User ID and username
- Event type and status (success/failure/warning/info)
- IP address
- User agent
- Timestamp (UTC)
- JSON details field for additional context

**Viewing Audit Logs** (Admin only):
```bash
# API endpoint
curl -X GET https://dash.pesulabs.net/api/audit-logs?limit=100 \
  -H "Cookie: session=YOUR_SESSION"

# Database query
kubectl exec -n homelab -it postgres-0 -- \
  psql -U homelab -d homelab -c "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 20;"
```

### 7. Password Management

#### Password Policies (Enforced at Application Level)
- **Minimum Length**: 8 characters (recommended: 12+)
- **Complexity**: Mixed case, numbers, special characters recommended
- **History Tracking**: Last 5 passwords stored in `password_history` table
- **Reuse Prevention**: New passwords checked against history (implementation ready)
- **Change Tracking**: `password_changed_at` timestamp in users table

#### Secure Storage
- Werkzeug `generate_password_hash()` with default parameters
- Algorithm: pbkdf2:sha256 with salt
- Never store plaintext passwords

### 8. Database Security

#### PostgreSQL Best Practices
- **Separate Database User**: `homelab` user with limited privileges
- **Connection Security**: Internal K8s service (no external exposure)
- **Parameterized Queries**: All queries use `%s` placeholders (prevents SQL injection)
- **Transaction Safety**: Context managers ensure commit/rollback
- **Schema Validation**: Constraints enforce data integrity
  - Username length and format
  - Event type enumeration
  - Foreign key relationships

#### Schema Highlights
```sql
-- User table with security constraints
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    CONSTRAINT username_length CHECK (char_length(username) >= 3),
    CONSTRAINT username_format CHECK (username ~ '^[a-zA-Z0-9_-]+$')
);

-- Audit logs with event type validation
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_status VARCHAR(20) NOT NULL,
    ip_address VARCHAR(45),
    details JSONB,
    CONSTRAINT valid_event_type CHECK (event_type IN (...))
);
```

## Deployment Security

### 1. Kubernetes Secrets

**Sensitive Data in Secrets** (not ConfigMaps):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dashboard-secrets
  namespace: homelab
type: Opaque
stringData:
  secret-key: "31a75bf7dc74eecf5e5c837ff698b369..."  # Flask secret
  username: "admin"                                  # Initial admin user
  password: "ChangeMe!2024#Secure"                   # CHANGE IMMEDIATELY
  admin-email: "admin@pesulabs.net"                  # Optional
```

**Database Password** (from existing PostgreSQL secret):
```yaml
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: postgres-secret
      key: password
```

### 2. Network Security

#### Ingress Configuration
- **TLS/HTTPS**: Let's Encrypt certificate via cert-manager
- **Domain**: `dash.pesulabs.net` (public DNS)
- **Traefik**: Kubernetes ingress controller with automatic HTTPS redirect

#### Access Control Recommendations
**Option 1: Tailscale-Only Access** (Most Secure)
```yaml
# Restrict to Tailscale IPs at Ingress level
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    traefik.ingress.kubernetes.io/router.middlewares: homelab-tailscale-whitelist@kubernetescrd
```

**Option 2: VPN + Strong Authentication** (Current)
- Dashboard accessible via Tailscale VPN
- Strong password + account lockout + rate limiting
- Audit logging for all access

### 3. Container Security

- **Non-Root User**: Container runs as unprivileged user (recommended)
- **Read-Only Filesystem**: Consider making `/app` read-only
- **Resource Limits**: Memory and CPU limits prevent DoS
- **Health Checks**: Liveness and readiness probes

## Operational Security

### Regular Maintenance Tasks

#### Weekly
1. Review audit logs for suspicious activity:
   ```bash
   kubectl logs -n homelab -l app=homelab-dashboard | grep -E "(login_failed|account_locked|access_denied)"
   ```

2. Check for locked accounts:
   ```sql
   SELECT username, locked_until, failed_login_attempts
   FROM users
   WHERE locked_until > NOW();
   ```

#### Monthly
1. Review active sessions and expire stale ones:
   ```sql
   SELECT * FROM sessions WHERE expires_at < NOW() AND is_active = TRUE;
   ```

2. Analyze login statistics:
   ```bash
   curl -X GET https://dash.pesulabs.net/api/login-stats?days=30
   ```

3. Update dependencies: `pip list --outdated`

#### Quarterly
1. Rotate Flask `SECRET_KEY` (requires session invalidation)
2. Review and update password policies
3. Audit user accounts and remove inactive ones

### Incident Response

#### Suspected Breach
1. **Immediately**: Change all passwords and rotate secrets
2. Review audit logs for unauthorized access:
   ```sql
   SELECT * FROM audit_logs
   WHERE event_type = 'login_success'
   AND created_at > '2025-10-01'
   ORDER BY created_at DESC;
   ```
3. Check sessions table for suspicious activity
4. Invalidate all active sessions: `UPDATE sessions SET is_active = FALSE;`

#### Brute Force Attack
1. Check for patterns in audit logs:
   ```sql
   SELECT ip_address, COUNT(*) as attempts
   FROM audit_logs
   WHERE event_type = 'login_failed'
   AND created_at > NOW() - INTERVAL '1 hour'
   GROUP BY ip_address
   HAVING COUNT(*) > 20
   ORDER BY attempts DESC;
   ```
2. Consider IP blocking at Ingress/Traefik level
3. Reduce rate limits if needed (app.py:34-38)

## Security Configuration Reference

### Environment Variables

| Variable | Purpose | Required | Default | Location |
|----------|---------|----------|---------|----------|
| `SECRET_KEY` | Flask session encryption | Yes | Random | K8s Secret |
| `DASHBOARD_USER` | Initial admin username | Yes | `admin` | K8s Secret |
| `DASHBOARD_PASSWORD` | Initial admin password | Yes | N/A | K8s Secret |
| `ADMIN_EMAIL` | Admin email for notifications | No | None | K8s Secret |
| `DB_HOST` | PostgreSQL hostname | Yes | `postgres.homelab...` | Deployment |
| `DB_PORT` | PostgreSQL port | Yes | `5432` | Deployment |
| `DB_NAME` | Database name | Yes | `homelab` | Deployment |
| `DB_USER` | Database username | Yes | `homelab` | Deployment |
| `DB_PASSWORD` | Database password | Yes | N/A | K8s Secret |

### Security Thresholds (Configurable)

| Parameter | Value | File | Line |
|-----------|-------|------|------|
| Max failed attempts | 5 | `database.py` | 137 |
| Lockout duration | 15 minutes | `database.py` | 138 |
| Session lifetime | 4 hours | `app.py` | 27 |
| Inactivity timeout | 30 minutes | `database.py` | 276 |
| Login rate limit | 5 per 15 min | `app.py` | 214 |
| Global rate limit | 200/day, 50/hour | `app.py` | 37 |
| Password history | 5 passwords | `database.py` | 402 |

## API Endpoints

### Public (No Authentication)
- `GET /health` - Health check
- `GET /login` - Login page
- `POST /login` - Submit credentials

### Authenticated
- `GET /` - Dashboard homepage
- `GET /logout` - Logout and clear session
- `GET /api/services` - List of homelab services
- `GET /api/system-info` - Basic system information

### Admin Only
- `GET /api/audit-logs?limit=N` - Audit log entries
- `GET /api/login-stats?days=N` - Login statistics

## Testing Security

### Manual Tests

1. **CSRF Protection**:
   ```bash
   # Should fail without CSRF token
   curl -X POST https://dash.pesulabs.net/login \
     -d "username=admin&password=test" -L
   ```

2. **Rate Limiting**:
   ```bash
   # Try 6 login attempts in quick succession
   for i in {1..6}; do
     curl -X POST https://dash.pesulabs.net/login \
       -d "username=admin&password=wrong" -L
   done
   # 6th should return 429 Too Many Requests
   ```

3. **Account Lockout**:
   ```bash
   # 5 failed attempts should lock account
   for i in {1..5}; do
     curl -X POST https://dash.pesulabs.net/login \
       -d "username=admin&password=wrong" -L
   done
   # Next attempt should show "account locked" message
   ```

4. **Session Timeout**:
   - Login, note session cookie
   - Wait 31 minutes
   - Try to access dashboard - should redirect to login

### Automated Security Scanning

```bash
# OWASP ZAP (Docker)
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://dash.pesulabs.net

# Nikto web scanner
nikto -h https://dash.pesulabs.net

# SSL/TLS check
sslscan dash.pesulabs.net
```

## Future Enhancements

### Potential Improvements
1. **Multi-Factor Authentication (MFA)**: TOTP (Google Authenticator) support
2. **OAuth/OIDC Integration**: Single sign-on with external providers
3. **API Key Authentication**: Token-based access for automation
4. **IP Whitelisting**: Restrict access to known IPs/ranges
5. **Redis-Backed Rate Limiting**: Distributed rate limiting across pods
6. **Webhook Notifications**: Alert on security events (login failures, lockouts)
7. **Password Expiration**: Force password changes every N days
8. **Role-Based Access Control (RBAC)**: Granular permissions system
9. **Security Dashboards**: Grafana dashboard with security metrics

## Compliance & Standards

This implementation follows:
- **OWASP Top 10**: Mitigates SQL injection, XSS, CSRF, broken authentication
- **NIST Cybersecurity Framework**: Identify, Protect, Detect, Respond
- **CIS Controls**: Strong authentication, audit logging, secure configuration

## Support & Contact

For security issues or questions:
- GitHub Issues: https://github.com/pesuga/homelab/issues
- Email: admin@pesulabs.net (if configured)

**Responsible Disclosure**: If you discover a security vulnerability, please report it privately before public disclosure.
