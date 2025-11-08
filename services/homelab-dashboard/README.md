# Homelab Dashboard - Secure Landing Page

A secure, production-ready dashboard for accessing your homelab services with comprehensive authentication and audit logging.

## Features

### 🔐 Security
- **CSRF Protection**: Flask-WTF tokens prevent cross-site attacks
- **Rate Limiting**: Brute force protection (5 login attempts per 15 minutes)
- **Account Lockout**: Automatic 15-minute lock after failed attempts
- **Security Headers**: HSTS, CSP, X-Frame-Options, and more
- **Audit Logging**: Complete security event trail
- **Session Management**: 4-hour lifetime, 30-minute inactivity timeout
- **Secure Cookies**: HttpOnly, Secure, SameSite protection

### 👥 User Management
- **Database-Backed**: PostgreSQL storage for scalability
- **Password Security**: bcrypt hashing with salt
- **Password History**: Prevents reuse of last 5 passwords
- **Session Tracking**: Monitor active sessions and activity
- **Role-Based Access**: Admin and standard user roles

### 📊 Monitoring
- **Audit Logs**: All authentication events logged
- **Login Statistics**: Track successful/failed attempts
- **Session Tracking**: Active session monitoring
- **Admin API**: Query logs and statistics programmatically

### 🚀 Service Integration
Current services displayed:
- Grafana (metrics visualization)
- Prometheus (metrics collection)
- N8n (workflow automation)
- PostgreSQL (database)
- Redis (cache)
- Open WebUI (LLM chat)
- Ollama (LLM inference)
- LiteLLM (API gateway)
- Flowise (LLM flows)
- Qdrant (vector database)

## Quick Start

### Prerequisites
- K3s cluster with PostgreSQL
- Docker registry at `100.81.76.55:30500`
- `kubectl` configured

### Deploy

```bash
cd services/homelab-dashboard
./scripts/deploy.sh
```

Access at: `https://dash.pesulabs.net` or `http://100.81.76.55:30800`

### First Login

1. Login with default credentials (from K8s Secret)
2. **Change password immediately!**

## Documentation

- **[SECURITY.md](SECURITY.md)**: Comprehensive security documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Detailed deployment and troubleshooting guide
- **[SECURITY-SUMMARY.md](SECURITY-SUMMARY.md)**: High-level security overview

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Traefik Ingress                        │
│              (HTTPS, Let's Encrypt, Rate Limit)             │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Homelab Dashboard Pod                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Flask App (app.py)                                  │  │
│  │  - CSRF Protection (Flask-WTF)                       │  │
│  │  - Rate Limiting (Flask-Limiter)                     │  │
│  │  - Security Headers (Flask-Talisman)                 │  │
│  │  - Session Management (4h lifetime, 30m timeout)     │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │  Database Module (database.py)                       │  │
│  │  - User authentication                               │  │
│  │  - Audit logging                                     │  │
│  │  - Session tracking                                  │  │
│  │  - Account lockout                                   │  │
│  └────────────────────┬─────────────────────────────────┘  │
└───────────────────────┼──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                 PostgreSQL Database                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Tables:                                              │  │
│  │  - users (authentication, lockout, timestamps)        │  │
│  │  - audit_logs (security events, IP, user agent)      │  │
│  │  - sessions (active sessions, expiration)            │  │
│  │  - password_history (prevent reuse)                  │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Security Highlights

### Before Security Enhancement
- ❌ No CSRF protection
- ❌ Unlimited login attempts
- ❌ 24-hour sessions with no timeout
- ❌ In-memory user storage (1 user)
- ❌ No audit logging
- ⚠️ Weak default password

### After Security Enhancement
- ✅ CSRF tokens on all forms
- ✅ 5 attempts per 15 minutes rate limit
- ✅ 4-hour sessions with 30-minute inactivity timeout
- ✅ PostgreSQL-backed user management
- ✅ Comprehensive audit logging
- ✅ Strong password requirements
- ✅ Account lockout protection
- ✅ Security headers (HSTS, CSP, etc.)

## API Reference

### Public Endpoints
- `GET /login` - Login page
- `POST /login` - Submit credentials
- `GET /health` - Health check (no auth)

### Authenticated Endpoints
- `GET /` - Dashboard homepage
- `GET /logout` - Logout
- `GET /api/services` - List services
- `GET /api/system-info` - System information

### Admin Endpoints
- `GET /api/audit-logs?limit=N` - Audit logs
- `GET /api/login-stats?days=N` - Login statistics

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | Random | Flask session encryption key |
| `DASHBOARD_USER` | Yes | `admin` | Initial admin username |
| `DASHBOARD_PASSWORD` | Yes | - | Initial admin password |
| `ADMIN_EMAIL` | No | - | Admin email for notifications |
| `DB_HOST` | Yes | `postgres.homelab...` | PostgreSQL host |
| `DB_PORT` | Yes | `5432` | PostgreSQL port |
| `DB_NAME` | Yes | `homelab` | Database name |
| `DB_USER` | Yes | `homelab` | Database user |
| `DB_PASSWORD` | Yes | - | Database password |

### Security Thresholds

Adjustable in source code:

| Parameter | Value | Location |
|-----------|-------|----------|
| Max failed attempts | 5 | `database.py:137` |
| Lockout duration | 15 min | `database.py:138` |
| Session lifetime | 4 hours | `app.py:27` |
| Inactivity timeout | 30 min | `database.py:276` |
| Login rate limit | 5/15min | `app.py:214` |
| Global rate limit | 200/day, 50/hr | `app.py:37` |

## Troubleshooting

### Can't Login
```bash
# Check if account is locked
kubectl exec -n homelab postgres-0 -- \
  psql -U homelab -d homelab -c \
  "SELECT username, failed_login_attempts, locked_until FROM users;"

# Unlock account
kubectl exec -n homelab postgres-0 -- \
  psql -U homelab -d homelab -c \
  "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE username = 'admin';"
```

### Database Connection Failed
```bash
# Check PostgreSQL is running
kubectl get pods -n homelab -l app=postgres

# Test connection from pod
kubectl exec -n homelab $(kubectl get pod -n homelab -l app=homelab-dashboard -o name) -- \
  python3 -c "import psycopg2; psycopg2.connect(host='postgres.homelab.svc.cluster.local', database='homelab', user='homelab', password='YOUR_PASSWORD')"
```

### CSRF Token Errors
- Clear browser cookies and cache
- Try incognito/private browsing mode
- Verify CSRF protection is enabled in logs

## Maintenance

### View Logs
```bash
# Real-time logs
kubectl logs -f -n homelab -l app=homelab-dashboard

# Security events only
kubectl logs -n homelab -l app=homelab-dashboard | grep -E "(login|audit|lockout)"
```

### Backup Database
```bash
# Full backup
kubectl exec -n homelab postgres-0 -- \
  pg_dump -U homelab homelab > dashboard-backup-$(date +%Y%m%d).sql

# Restore
cat dashboard-backup-20251028.sql | \
  kubectl exec -i -n homelab postgres-0 -- psql -U homelab homelab
```

### Update Application
```bash
# Rebuild and deploy
./scripts/deploy.sh

# Or manually
docker build -t homelab-dashboard:v2 .
docker push 100.81.76.55:30500/homelab-dashboard:v2
kubectl set image deployment/homelab-dashboard dashboard=100.81.76.55:30500/homelab-dashboard:v2 -n homelab
```

## Development

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
export DASHBOARD_USER=admin
export DASHBOARD_PASSWORD=admin123
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=homelab
export DB_USER=homelab
export DB_PASSWORD=your_password

# Run locally
python app/app.py
```

### Database Schema
```bash
# Initialize schema
psql -U homelab -d homelab < database/schema.sql

# View tables
psql -U homelab -d homelab -c "\dt"

# View users
psql -U homelab -d homelab -c "SELECT * FROM users;"
```

## Technology Stack

- **Backend**: Python 3.12, Flask 3.1
- **Database**: PostgreSQL 16.10
- **Security**: Flask-WTF, Flask-Limiter, Flask-Talisman
- **Deployment**: Docker, Kubernetes (K3s)
- **Web Server**: Gunicorn
- **Ingress**: Traefik with Let's Encrypt

## License

This is part of the PesuLabs Homelab project. See main repository for license.

## Contributing

Issues and pull requests welcome at: https://github.com/pesuga/homelab

## Support

- **Documentation**: See [SECURITY.md](SECURITY.md) and [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: https://github.com/pesuga/homelab/issues
- **Email**: admin@pesulabs.net (if configured)

---

**Built with ❤️ for secure homelab automation**
