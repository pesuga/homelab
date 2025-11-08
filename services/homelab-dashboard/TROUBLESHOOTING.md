# Homelab Dashboard - Known Issues & Troubleshooting

## 🔴 CRITICAL: Authentication CSRF Issue (2025-10-30)

### Symptoms
- Login page loads correctly
- Entering credentials results in "400 Bad Request - The CSRF session token is missing"
- Dashboard pod has experienced 181+ restarts (as of 2025-10-30)

### Root Cause Analysis

**Primary Issue**: Flask session storage not persisting properly, causing CSRF tokens to fail validation.

**Contributing Factors**:
1. **Pod Restart Loop** - Database initialization script attempts to create triggers that already exist
   - Error: `trigger "update_users_updated_at" for relation "users" already exists`
   - Causes continuous restarts (Exit Code: 0, but restarts immediately)
   - Session cookies become invalid across restarts

2. **Session Storage** - Using default Flask session (signed cookies)
   - No external session store (Redis recommended)
   - Sessions don't persist across pod restarts
   - Current config: `storage_uri="memory://"` in rate limiter (line 48 of app.py)

3. **Cookie Configuration** - Possible cookie domain/path issues
   - `SESSION_COOKIE_SECURE = False` (correct for behind proxy)
   - `SESSION_COOKIE_SAMESITE = 'Lax'`
   - No explicit `SESSION_COOKIE_DOMAIN` set

### Temporary Workaround

**Current Credentials** (documented for reference):
- Username: `admin`
- Password: `ChangeMe!2024#Secure` (from deployment secret, NOT `admin123` as documented elsewhere)

**Direct Service Access**:
Services can be accessed directly without dashboard authentication:
- Grafana: https://grafana.homelab.pesulabs.net
- N8n: https://n8n.homelab.pesulabs.net
- Prometheus: https://prometheus.homelab.pesulabs.net
- Open WebUI: https://webui.homelab.pesulabs.net

### Permanent Fix Required

#### Phase 1: Stop Restart Loop (15 min)

1. **Fix Database Init Script** - Make idempotent
   ```python
   # In database.py or init script
   # Change from:
   cursor.execute("CREATE TRIGGER update_users_updated_at ...")

   # To:
   cursor.execute("""
       CREATE TRIGGER IF NOT EXISTS update_users_updated_at
       BEFORE UPDATE ON users
       FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
   """)
   ```

2. **Add Init Check** - Skip if already initialized
   ```python
   def init_db():
       """Initialize database - idempotent"""
       with get_db_cursor() as cursor:
           # Check if already initialized
           cursor.execute("""
               SELECT EXISTS (
                   SELECT FROM information_schema.tables
                   WHERE table_schema = 'public'
                   AND table_name = 'users'
               )
           """)
           if cursor.fetchone()['exists']:
               logger.info("Database already initialized, skipping")
               return

           # Proceed with initialization...
   ```

3. **Update Deployment** - Rebuild and redeploy image

#### Phase 2: Fix Session Storage (30 min)

1. **Integrate Redis for Sessions**
   ```python
   # In app.py
   from flask_session import Session

   app.config['SESSION_TYPE'] = 'redis'
   app.config['SESSION_REDIS'] = redis.from_url('redis://redis.homelab.svc.cluster.local:6379')
   app.config['SESSION_PERMANENT'] = False
   app.config['SESSION_USE_SIGNER'] = True

   Session(app)
   ```

2. **Update Requirements**
   ```txt
   Flask-Session==0.5.0
   redis==5.0.0
   ```

3. **Update Deployment** - Add Redis dependency check

#### Phase 3: Improve Session Security (15 min)

1. **Set Cookie Domain** - Ensure cookies work across subdomains
   ```python
   app.config['SESSION_COOKIE_DOMAIN'] = '.pesulabs.net'
   ```

2. **Add Session Validation** - Detect and handle invalid sessions gracefully
   ```python
   @app.before_request
   def validate_session():
       if request.endpoint and request.endpoint != 'login':
           if 'user_id' in session:
               # Validate session is still valid
               try:
                   user = db.get_user_by_id(session['user_id'])
                   if not user:
                       session.clear()
                       return redirect(url_for('login'))
               except Exception:
                   session.clear()
                   return redirect(url_for('login'))
   ```

### Testing Checklist

After implementing fixes:

- [ ] Pod restarts should stop (check with `kubectl get pods -n homelab -l app=homelab-dashboard`)
- [ ] Login page loads without errors
- [ ] CSRF token validation succeeds
- [ ] Sessions persist across browser refresh
- [ ] Sessions persist across pod restarts (if using Redis)
- [ ] Logout works correctly
- [ ] Session timeout works (4 hours)
- [ ] Rate limiting works (5 attempts per 15 min)

### Related Files

- `services/homelab-dashboard/app/app.py` - Main application (lines 30-50 for session config)
- `services/homelab-dashboard/app/database.py` - Database initialization
- `services/homelab-dashboard/k8s/deployment.yaml` - Kubernetes deployment (line 91: password secret)
- `services/homelab-dashboard/Dockerfile` - Image build
- `services/homelab-dashboard/requirements.txt` - Python dependencies

### Impact Assessment

**Current Impact**:
- Dashboard authentication non-functional
- All services still accessible via direct URLs
- No security breach (services have own authentication)

**Priority**: Medium (P2)
- Services accessible without dashboard
- No data at risk
- User experience degraded but not blocking

**Estimated Fix Time**: 1-2 hours total
- Phase 1: 15 minutes
- Phase 2: 30 minutes
- Phase 3: 15 minutes
- Testing: 30 minutes

### Next Steps

1. Schedule fix for next session or when time permits
2. Continue with higher priority items (monitoring dashboards, Flux CD)
3. Update documentation to reflect temporary workaround
4. Create GitHub issue to track this work

---

**Last Updated**: 2025-10-30
**Discovered By**: Claude Code (Sprint 4 implementation)
**Assigned To**: Future session
**Status**: Documented, Fix Deferred
