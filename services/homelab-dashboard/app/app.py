#!/usr/bin/env python3
"""
Homelab Dashboard - A simple landing page with authentication
"""
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Simple in-memory user storage (replace with database in production)
USERS = {
    os.environ.get('DASHBOARD_USER', 'admin'): generate_password_hash(
        os.environ.get('DASHBOARD_PASSWORD', 'admin123')
    )
}

# Services configuration - Using Tailscale IPs for reliability
# Service Node (asuna): 100.81.76.55
# Compute Node (pesubuntu): 100.72.98.106
SERVICES = [
    {
        'name': 'Grafana',
        'description': 'Metrics visualization and monitoring dashboards',
        'url': 'http://100.81.76.55:30300',
        'icon': '📊',
        'status_endpoint': '/api/health',
        'tags': ['monitoring', 'visualization']
    },
    {
        'name': 'Prometheus',
        'description': 'Time series database and metrics collection',
        'url': 'http://100.81.76.55:30090',
        'icon': '🔥',
        'status_endpoint': '/-/healthy',
        'tags': ['monitoring', 'metrics']
    },
    {
        'name': 'N8n',
        'description': 'Workflow automation and integration platform',
        'url': 'http://100.81.76.55:30678',
        'icon': '🔗',
        'status_endpoint': '/healthz',
        'tags': ['automation', 'workflows']
    },
    {
        'name': 'PostgreSQL',
        'description': 'Relational database (PostgreSQL 16.10)',
        'url': None,  # Internal service, no web UI
        'icon': '🐘',
        'status_endpoint': None,
        'tags': ['database', 'storage'],
        'internal': True,
        'connection': 'postgres.homelab.svc.cluster.local:5432'
    },
    {
        'name': 'Redis',
        'description': 'In-memory cache and message broker (Redis 7.4.6)',
        'url': None,  # Internal service, no web UI
        'icon': '🔴',
        'status_endpoint': None,
        'tags': ['cache', 'storage'],
        'internal': True,
        'connection': 'redis.homelab.svc.cluster.local:6379'
    },
    {
        'name': 'Open WebUI',
        'description': 'Local LLM chat interface (Llama 3.1 8B)',
        'url': 'http://100.81.76.55:30080',
        'icon': '🤖',
        'status_endpoint': '/health',
        'tags': ['ai', 'llm']
    },
    {
        'name': 'Ollama',
        'description': 'LLM inference API (direct)',
        'url': 'http://100.72.98.106:11434',
        'icon': '🦙',
        'status_endpoint': '/api/version',
        'tags': ['ai', 'llm', 'api']
    },
    {
        'name': 'LiteLLM',
        'description': 'OpenAI-compatible LLM API gateway',
        'url': 'http://100.72.98.106:8000',
        'icon': '⚡',
        'status_endpoint': '/health',
        'tags': ['ai', 'llm', 'api']
    },
    {
        'name': 'Flowise',
        'description': 'Low-code LLM flow builder and AI orchestration',
        'url': 'http://100.81.76.55:30850',
        'icon': '🌊',
        'status_endpoint': '/',
        'tags': ['ai', 'llm', 'workflows']
    }
]

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('index.html', services=SERVICES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in USERS and check_password_hash(USERS[username], password):
            session['user'] = username
            session.permanent = True
            app.permanent_session_lifetime = timedelta(hours=24)

            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout route"""
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/api/services')
@login_required
def api_services():
    """API endpoint to get services info"""
    return jsonify(SERVICES)

@app.route('/api/system-info')
@login_required
def system_info():
    """API endpoint for system information"""
    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'services_count': len(SERVICES),
        'uptime': 'N/A'  # TODO: Implement actual uptime tracking
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
