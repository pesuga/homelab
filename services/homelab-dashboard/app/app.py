#!/usr/bin/env python3
"""
Homelab Dashboard - Secure landing page with comprehensive authentication
"""
import os
import sys
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

# Add the app directory to Python path to import database module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

# Initialize Flask app
app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

# Trust proxy headers (X-Forwarded-* from Traefik/Ingress)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Security Configuration
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
# Disable SESSION_COOKIE_SECURE when behind proxy - Traefik handles HTTPS
# The connection from Traefik to Flask is HTTP inside the cluster
app.config['SESSION_COOKIE_SECURE'] = False  # Traefik terminates TLS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)  # Reduced from 24h
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF token doesn't expire

# Initialize security extensions
csrf = CSRFProtect(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use Redis in production: redis://redis.homelab.svc.cluster.local:6379
)

# Security headers with Talisman
csp = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'"],  # Adjust based on your needs
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", "data:", "https:"],
    'font-src': ["'self'"],
    'connect-src': ["'self'"]
}

Talisman(app,
         force_https=False,  # Handled by Ingress/Traefik
         content_security_policy=csp)

# Services configuration with enhanced connectivity info
SERVICES = [
    # Removed Grafana - currently not deployed
    {
        'name': 'Prometheus',
        'description': 'Time series database and metrics collection',
        'url': 'http://100.81.76.55:30190',
        'external_url': 'http://100.81.76.55:30190',
        'health_check_url': 'http://100.81.76.55:30190',
        'internal_url': 'http://prometheus.homelab.svc.cluster.local:9090',
        'icon': '🔥',
        'status_endpoint': '/-/healthy',
        'port': 30190,
        'tags': ['monitoring', 'metrics']
    },
    {
        'name': 'N8n',
        'description': 'Workflow automation and integration platform',
        'url': 'http://100.81.76.55:30678',
        'external_url': 'http://100.81.76.55:30678',
        'health_check_url': 'http://100.81.76.55:30678',
        'internal_url': 'http://n8n.homelab.svc.cluster.local:5678',
        'icon': '🔗',
        'status_endpoint': '/healthz',
        'port': 30678,
        'tags': ['automation', 'workflows']
    },
    {
        'name': 'PostgreSQL',
        'description': 'Relational database (PostgreSQL 16.10)',
        'url': None,
        'external_url': None,
        'internal_url': 'postgres.homelab.svc.cluster.local:5432',
        'icon': '🐘',
        'status_endpoint': None,
        'port': 5432,
        'tags': ['database', 'storage'],
        'internal': True
    },
    {
        'name': 'Redis',
        'description': 'In-memory cache and message broker (Redis 7.4.6)',
        'url': None,
        'external_url': None,
        'internal_url': 'redis.homelab.svc.cluster.local:6379',
        'icon': '🔴',
        'status_endpoint': None,
        'port': 6379,
        'tags': ['cache', 'storage'],
        'internal': True
    },
      # Removed Open WebUI - currently not deployed
    # Removed LiteLLM - currently not deployed
    {
        'name': 'Ollama',
        'description': 'LLM inference API (Kubernetes deployment)',
        'url': 'http://100.81.76.55:30277',
        'external_url': 'http://100.81.76.55:30277',
        'health_check_url': 'http://100.81.76.55:30277',
        'internal_url': 'http://ollama.ollama.svc.cluster.local:11434',
        'icon': '🦙',
        'status_endpoint': '/api/version',
        'port': 30277,
        'tags': ['ai', 'llm', 'api', 'gpu']
    },
    # Removed Flowise - currently not deployed
    {
        'name': 'Qdrant',
        'description': 'Vector database for RAG and semantic search (v1.12.5)',
        'url': 'http://100.81.76.55:30633',
        'external_url': 'http://100.81.76.55:30633',
        'health_check_url': 'http://100.81.76.55:30633',
        'internal_url': 'http://qdrant.homelab.svc.cluster.local:6333',
        'icon': '🔍',
        'status_endpoint': '/collections',
        'port': 30633,
        'tags': ['database', 'vector', 'ai']
    },
    {
        'name': 'LobeChat',
        'description': 'AI chat interface with memory',
        'url': 'http://100.81.76.55:30910',
        'external_url': 'http://100.81.76.55:30910',
        'health_check_url': 'http://100.81.76.55:30910',
        'internal_url': 'http://lobechat.homelab.svc.cluster.local:3000',
        'icon': '🎭',
        'status_endpoint': '/',
        'port': 30910,
        'tags': ['ai', 'chat', 'memory']
    },
    # Removed Whisper - currently experiencing issues (pods crashing)
    {
        'name': 'Mem0',
        'description': 'AI memory layer for contextual conversations',
        'url': 'http://100.81.76.55:30880',
        'external_url': 'http://100.81.76.55:30880',
        'health_check_url': 'http://100.81.76.55:30880',
        'internal_url': 'http://mem0.homelab.svc.cluster.local:8001',
        'icon': '🧠',
        'status_endpoint': '/docs',
        'port': 30880,
        'tags': ['ai', 'memory', 'context']
    },
    {
        'name': 'Loki',
        'description': 'Log aggregation and search system',
        'url': 'http://100.81.76.55:30314',
        'external_url': 'http://100.81.76.55:30314',
        'health_check_url': 'http://100.81.76.55:30314',
        'internal_url': 'http://loki.homelab.svc.cluster.local:3100',
        'icon': '📋',
        'status_endpoint': '/ready',
        'port': 30314,
        'tags': ['logging', 'monitoring']
    },
    {
        'name': 'Docker Registry',
        'description': 'Private container image registry',
        'url': 'http://100.81.76.55:30500',
        'external_url': 'http://100.81.76.55:30500',
        'health_check_url': 'http://100.81.76.55:30500',
        'internal_url': 'http://docker-registry.homelab.svc.cluster.local:5000',
        'icon': '📦',
        'status_endpoint': '/v2/',
        'port': 30500,
        'tags': ['infrastructure', 'registry', 'storage']
    }
]

# Service categories for better organization
SERVICE_CATEGORIES = {
    'Monitoring & Observability': ['Prometheus', 'Loki'],
    'AI & Machine Learning': ['Ollama', 'Mem0', 'LobeChat'],
    'Automation & Workflows': ['N8n'],
    'Databases & Storage': ['PostgreSQL', 'Redis', 'Qdrant'],
    'Infrastructure': ['Docker Registry']
}

# ===== HELPER FUNCTIONS =====

def get_client_ip():
    """Get client IP address, handling proxy headers"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def get_user_agent():
    """Get user agent string"""
    return request.headers.get('User-Agent', 'Unknown')

def regenerate_session():
    """Regenerate session ID to prevent fixation attacks"""
    # Store user data
    user_data = dict(session)

    # Clear old session
    session.clear()

    # Generate new session ID and restore data
    for key, value in user_data.items():
        session[key] = value

    # Generate new session token
    session['_session_token'] = secrets.token_hex(32)

# ===== HEALTH CHECKING FUNCTIONS =====

def check_service_health(service):
    """Check if a service is healthy"""
    try:
        name = service['name']
        status_endpoint = service.get('status_endpoint')

        # Skip health check for internal-only services without endpoints
        if status_endpoint is None and service.get('internal'):
            return {'status': 'unknown', 'message': 'No health endpoint configured', 'name': name}

        # Use health_check_url if available, otherwise fall back to internal/external logic
        if 'health_check_url' in service:
            base_url = service['health_check_url']
        elif service.get('internal'):
            base_url = service['internal_url']
        else:
            base_url = service['external_url']

        # Skip health check if no endpoint available
        if status_endpoint is None:
            return {'status': 'unknown', 'message': 'No health endpoint', 'name': name}

        # Construct full URL for health check
        if status_endpoint.startswith('http'):
            url = status_endpoint
        else:
            url = f"{base_url}{status_endpoint}"

        # Health check with timeout
        import requests
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return {'status': 'online', 'message': f'HTTP {response.status_code}', 'name': name, 'url': url}
            else:
                return {'status': 'offline', 'message': f'HTTP {response.status_code}', 'name': name, 'url': url}
        except requests.exceptions.Timeout:
            return {'status': 'timeout', 'message': 'Connection timeout', 'name': name, 'url': url}
        except requests.exceptions.ConnectionError:
            return {'status': 'offline', 'message': 'Connection error', 'name': name, 'url': url}
        except requests.exceptions.RequestException as e:
            return {'status': 'offline', 'message': str(e), 'name': name, 'url': url}

    except Exception as e:
        return {'status': 'error', 'message': str(e), 'name': name}

def get_all_services_health():
    """Get health status for all services"""
    health_results = []
    for service in SERVICES:
        health = check_service_health(service)
        service_copy = service.copy()
        service_copy['health'] = health
        health_results.append(service_copy)
    return health_results

# ===== DECORATORS =====

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))

        # Check session validity and activity timeout
        session_id = session.get('_session_token')
        if not session_id:
            session.clear()
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('login'))

        # Update session activity
        session_data = db.update_session_activity(session_id)
        if not session_data:
            session.clear()
            flash('Session expired due to inactivity. Please login again.', 'warning')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

# ===== ROUTES =====

@app.route('/')
@login_required
def index():
    """Main dashboard page with health checking and sorting"""
    user = db.get_user_by_id(session['user_id'])

    # Get services with health status and sort by online/offline
    services_with_health = get_all_services_health()

    # Sort services: online first, then offline, then unknown
    def get_sort_key(service):
        health_status = service['health']['status']
        if health_status == 'online':
            return 0
        elif health_status == 'offline':
            return 1
        else:  # unknown, error, timeout
            return 2

    sorted_services = sorted(services_with_health, key=get_sort_key)

    return render_template('index.html', services=sorted_services, user=user)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per 15 minutes")  # Rate limit login attempts
def login():
    """Login page with comprehensive security"""
    # Redirect if already logged in
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        ip_address = get_client_ip()
        user_agent = get_user_agent()

        # Validate input
        if not username or not password:
            db.log_audit_event(
                username=username,
                event_type='login_failed',
                event_status='failure',
                ip_address=ip_address,
                user_agent=user_agent,
                details={'reason': 'Empty credentials'}
            )
            flash('Username and password are required.', 'error')
            return render_template('login.html')

        # Check if account is locked
        if db.is_account_locked(username):
            db.log_audit_event(
                username=username,
                event_type='access_denied',
                event_status='warning',
                ip_address=ip_address,
                user_agent=user_agent,
                details={'reason': 'Account locked'}
            )
            flash('Account is temporarily locked due to too many failed login attempts. Please try again in 15 minutes.', 'error')
            return render_template('login.html')

        # Get user from database
        user = db.get_user_by_username(username)

        # Verify credentials
        if user and user['is_active'] and check_password_hash(user['password_hash'], password):
            # Successful login
            # Generate session token
            session_token = secrets.token_hex(32)

            # Record in database
            db.record_successful_login(username, ip_address, session_token)

            # Set session
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            session['_session_token'] = session_token
            session.permanent = True

            # Log success
            db.log_audit_event(
                user_id=user['id'],
                username=username,
                event_type='login_success',
                event_status='success',
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            # Failed login
            if user:
                # Record failed attempt (may lock account)
                was_locked = db.record_failed_login(username, ip_address)
                if was_locked:
                    flash('Too many failed login attempts. Account locked for 15 minutes.', 'error')
                else:
                    flash('Invalid username or password.', 'error')
            else:
                flash('Invalid username or password.', 'error')

            # Log failure
            db.log_audit_event(
                username=username,
                event_type='login_failed',
                event_status='failure',
                ip_address=ip_address,
                user_agent=user_agent,
                details={'reason': 'Invalid credentials'}
            )

            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout route with session cleanup"""
    session_token = session.get('_session_token')
    user_id = session.get('user_id')

    # Invalidate session in database
    if session_token:
        db.invalidate_session(session_token, reason='logout')

    # Log logout
    if user_id:
        db.log_audit_event(
            user_id=user_id,
            event_type='logout',
            event_status='success',
            ip_address=get_client_ip()
        )

    # Clear session
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/api/services')
@login_required
def api_services():
    """API endpoint to get services info with health status"""
    services_with_health = get_all_services_health()
    sorted_services = sorted(services_with_health, key=lambda s: s['health']['status'])
    return jsonify(sorted_services)

@app.route('/api/services/health')
def api_services_health():
    """API endpoint to get service health status"""
    try:
        services_with_health = get_all_services_health()
        health_summary = []
        for service in services_with_health:
            health_info = {
                'name': service['name'],
                'status': service['health']['status'],
                'message': service['health']['message'],
                'url': service['health'].get('url', '')
            }
            health_summary.append(health_info)
        return jsonify(health_summary)
    except Exception as e:
        return jsonify({'error': str(e), 'services': health_summary}), 500

@app.route('/api/services/health/<service_name>')
def api_service_health(service_name):
    """API endpoint to get health for specific service"""
    service = None
    for s in SERVICES:
        if s['name'].lower() == service_name.lower():
            service = s
            break

    if not service:
        return jsonify({'error': 'Service not found'}), 404

    health = check_service_health(service)
    return jsonify(health)

@app.route('/api/system-info')
@login_required
def system_info():
    """API endpoint for system information"""
    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'services_count': len(SERVICES),
        'user': session.get('username'),
        'is_admin': session.get('is_admin', False)
    })

@app.route('/api/audit-logs')
@login_required
def api_audit_logs():
    """API endpoint for audit logs (admin only)"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403

    limit = min(int(request.args.get('limit', 100)), 500)
    logs = db.get_recent_audit_logs(limit=limit)

    # Convert to serializable format
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log['id'],
            'username': log['username'],
            'event_type': log['event_type'],
            'event_status': log['event_status'],
            'ip_address': log['ip_address'],
            'created_at': log['created_at'].isoformat() if log['created_at'] else None,
            'details': log['details']
        })

    return jsonify(logs_data)

@app.route('/api/login-stats')
@login_required
def api_login_stats():
    """API endpoint for login statistics (admin only)"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403

    days = min(int(request.args.get('days', 7)), 30)
    stats = db.get_login_statistics(days=days)

    # Convert to serializable format
    stats_data = []
    for stat in stats:
        stats_data.append({
            'date': stat['date'].isoformat() if stat['date'] else None,
            'successful_logins': stat['successful_logins'],
            'failed_logins': stat['failed_logins'],
            'unique_users': stat['unique_users']
        })

    return jsonify(stats_data)

@app.route('/health')
@csrf.exempt  # Health checks don't need CSRF
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.before_request
def before_request():
    """Run before each request"""
    # Clean up expired sessions periodically
    # TODO: Fix database import issue
    # if secrets.randbelow(100) < 5:  # 5% chance per request
    #     db.cleanup_expired_sessions()
    pass

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors"""
    db.log_audit_event(
        event_type='access_denied',
        event_status='warning',
        ip_address=get_client_ip(),
        user_agent=get_user_agent(),
        details={'reason': 'Rate limit exceeded', 'limit': str(e.description)}
    )
    return render_template('error.html',
                         error_code=429,
                         error_message='Too many requests. Please slow down.'), 429

@app.errorhandler(403)
def forbidden_handler(e):
    """Handle forbidden errors"""
    return render_template('error.html',
                         error_code=403,
                         error_message='Access forbidden.'), 403

@app.errorhandler(404)
def not_found_handler(e):
    """Handle not found errors"""
    return render_template('error.html',
                         error_code=404,
                         error_message='Page not found.'), 404

@app.errorhandler(500)
def server_error_handler(e):
    """Handle server errors"""
    return render_template('error.html',
                         error_code=500,
                         error_message='Internal server error.'), 500

# ===== INITIALIZATION =====

def initialize_app():
    """Initialize application on startup"""
    try:
        print("🔧 Initializing Homelab Dashboard...")

        # Initialize database
        if not db.init_database():
            print("⚠️  Database initialization failed, but continuing...")

        # Create default admin user if it doesn't exist
        default_user = os.environ.get('DASHBOARD_USER', 'admin')
        default_pass = os.environ.get('DASHBOARD_PASSWORD', 'admin123')
        password_hash = generate_password_hash(default_pass)

        db.create_default_user(
            username=default_user,
            password_hash=password_hash,
            email=os.environ.get('ADMIN_EMAIL')
        )

        print("✅ Homelab Dashboard initialized successfully")
    except Exception as e:
        print(f"❌ Initialization error: {e}")

# Initialize app when module is loaded (works with both Gunicorn and direct run)
initialize_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
