"""
Database connection and helper functions for Homelab Dashboard
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime, timedelta
import json

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'postgres.homelab.svc.cluster.local'),
    'port': int(os.environ.get('DB_PORT', '5432')),
    'database': os.environ.get('DB_NAME', 'homelab'),
    'user': os.environ.get('DB_USER', 'homelab'),
    'password': os.environ.get('DB_PASSWORD', ''),
}

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

@contextmanager
def get_db_cursor(commit=True):
    """Context manager for database cursor with auto-commit"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

def init_database():
    """Initialize database schema if not exists"""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'db_schema', 'schema.sql')

    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        with get_db_cursor() as cursor:
            cursor.execute(schema_sql)

        print("✅ Database schema initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_default_user(username='admin', password_hash=None, email=None):
    """Create default admin user if not exists"""
    try:
        with get_db_cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                print(f"ℹ️  User '{username}' already exists")
                return False

            # Create user
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, is_admin, is_active)
                VALUES (%s, %s, %s, TRUE, TRUE)
                RETURNING id
            """, (username, password_hash, email))

            user_id = cursor.fetchone()['id']
            print(f"✅ Default admin user created: {username} (ID: {user_id})")
            return True
    except Exception as e:
        print(f"❌ Failed to create default user: {e}")
        return False

# ===== USER MANAGEMENT =====

def get_user_by_username(username):
    """Get user by username"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT id, username, password_hash, email, is_active, is_admin,
                   failed_login_attempts, locked_until, last_login_at
            FROM users
            WHERE username = %s
        """, (username,))
        return cursor.fetchone()

def get_user_by_id(user_id):
    """Get user by ID"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT id, username, email, is_active, is_admin,
                   failed_login_attempts, locked_until, last_login_at
            FROM users
            WHERE id = %s
        """, (user_id,))
        return cursor.fetchone()

def is_account_locked(username):
    """Check if account is currently locked"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT locked_until FROM users
            WHERE username = %s AND is_active = TRUE
        """, (username,))

        result = cursor.fetchone()
        if not result or not result['locked_until']:
            return False

        # Check if lock has expired
        if result['locked_until'] > datetime.utcnow():
            return True

        # Lock expired, clear it
        cursor.execute("""
            UPDATE users
            SET locked_until = NULL, failed_login_attempts = 0
            WHERE username = %s
        """, (username,))
        return False

def record_failed_login(username, ip_address):
    """Record failed login attempt and lock account if threshold exceeded"""
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    with get_db_cursor() as cursor:
        # Increment failed attempts
        cursor.execute("""
            UPDATE users
            SET failed_login_attempts = failed_login_attempts + 1
            WHERE username = %s
            RETURNING failed_login_attempts
        """, (username,))

        result = cursor.fetchone()
        if not result:
            return False

        failed_attempts = result['failed_login_attempts']

        # Lock account if threshold exceeded
        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            cursor.execute("""
                UPDATE users
                SET locked_until = %s
                WHERE username = %s
            """, (locked_until, username))

            # Log the lockout
            log_audit_event(
                username=username,
                event_type='account_locked',
                event_status='warning',
                ip_address=ip_address,
                details={'reason': 'Too many failed login attempts', 'attempts': failed_attempts}
            )
            return True

        return False

def record_successful_login(username, ip_address, session_id):
    """Record successful login and reset failed attempts"""
    with get_db_cursor() as cursor:
        # Get user ID
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return False

        user_id = user['id']

        # Update user login info and reset failed attempts
        cursor.execute("""
            UPDATE users
            SET last_login_at = CURRENT_TIMESTAMP,
                last_login_ip = %s,
                failed_login_attempts = 0,
                locked_until = NULL
            WHERE id = %s
        """, (ip_address, user_id))

        # Create session record
        expires_at = datetime.utcnow() + timedelta(hours=4)
        cursor.execute("""
            INSERT INTO sessions (session_id, user_id, ip_address, expires_at)
            VALUES (%s, %s, %s, %s)
        """, (session_id, user_id, ip_address, expires_at))

        return True

def update_session_activity(session_id):
    """Update session last activity timestamp"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE sessions
            SET last_activity_at = CURRENT_TIMESTAMP
            WHERE session_id = %s AND is_active = TRUE
            RETURNING user_id, last_activity_at, expires_at
        """, (session_id,))

        result = cursor.fetchone()
        if not result:
            return None

        # Check for inactivity timeout (30 minutes)
        inactivity_timeout = timedelta(minutes=30)
        time_since_activity = datetime.utcnow() - result['last_activity_at']

        if time_since_activity > inactivity_timeout or datetime.utcnow() > result['expires_at']:
            invalidate_session(session_id, reason='timeout')
            return None

        return result

def invalidate_session(session_id, reason='logout'):
    """Invalidate a session"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE sessions
            SET is_active = FALSE
            WHERE session_id = %s
            RETURNING user_id
        """, (session_id,))

        result = cursor.fetchone()
        if result:
            log_audit_event(
                user_id=result['user_id'],
                event_type='logout' if reason == 'logout' else 'session_expired',
                event_status='info',
                details={'reason': reason}
            )
        return result is not None

def cleanup_expired_sessions():
    """Clean up expired sessions"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT cleanup_expired_sessions()")

# ===== AUDIT LOGGING =====

def log_audit_event(username=None, user_id=None, event_type='', event_status='info',
                    ip_address=None, user_agent=None, details=None):
    """Log an audit event"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs
                (user_id, username, event_type, event_status, ip_address, user_agent, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, username, event_type, event_status, ip_address, user_agent,
                  json.dumps(details) if details else None))
    except Exception as e:
        print(f"⚠️  Failed to log audit event: {e}")

def get_recent_audit_logs(limit=100, user_id=None, event_type=None):
    """Get recent audit logs with optional filtering"""
    with get_db_cursor(commit=False) as cursor:
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)

        if event_type:
            query += " AND event_type = %s"
            params.append(event_type)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        return cursor.fetchall()

# ===== PASSWORD MANAGEMENT =====

def check_password_history(user_id, new_password_hash):
    """Check if password was recently used (prevent reuse)"""
    HISTORY_LIMIT = 5

    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT password_hash FROM password_history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, HISTORY_LIMIT))

        # This would need to compare hashes properly in production
        # For now, just check if we have history
        return cursor.fetchall()

def save_password_to_history(user_id, password_hash):
    """Save password hash to history"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO password_history (user_id, password_hash)
            VALUES (%s, %s)
        """, (user_id, password_hash))

def change_password(user_id, new_password_hash):
    """Change user password and save to history"""
    with get_db_cursor() as cursor:
        # Update password
        cursor.execute("""
            UPDATE users
            SET password_hash = %s, password_changed_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_password_hash, user_id))

        # Save to history
        save_password_to_history(user_id, new_password_hash)

        return True

# ===== STATISTICS =====

def get_login_statistics(days=7):
    """Get login statistics for the past N days"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) FILTER (WHERE event_type = 'login_success') as successful_logins,
                COUNT(*) FILTER (WHERE event_type = 'login_failed') as failed_logins,
                COUNT(DISTINCT username) as unique_users
            FROM audit_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
                AND event_type IN ('login_success', 'login_failed')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (days,))

        return cursor.fetchall()
