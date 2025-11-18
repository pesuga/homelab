"""
Prometheus metrics collection for Family Assistant.

Tracks request rates, durations, errors, and custom business metrics.
"""

import time
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    ['method', 'endpoint']
)

# Authentication metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['status']  # success, failure
)

auth_token_validations_total = Counter(
    'auth_token_validations_total',
    'Total JWT token validations',
    ['status']  # valid, invalid, expired
)

# Business metrics
active_users_gauge = Gauge(
    'active_users',
    'Number of active users'
)

conversations_total = Counter(
    'conversations_total',
    'Total conversations processed',
    ['user_role']
)

memory_operations_total = Counter(
    'memory_operations_total',
    'Total memory operations',
    ['operation', 'status']  # operation: store, retrieve, search
)

# Database metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation']  # select, insert, update, delete
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics.

    Tracks request count, duration, and in-progress requests.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and collect metrics."""
        # Skip metrics for /metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            status = response.status_code

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            return response

        finally:
            # Always decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


def setup_metrics(app):
    """
    Configure Prometheus metrics collection.

    Adds metrics middleware and /metrics endpoint.

    Args:
        app: FastAPI application instance
    """
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)

    # Add /metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Expose Prometheus metrics."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

    print("✅ Prometheus metrics configured: /metrics endpoint")


def track_request(method: str, endpoint: str, status: int, duration: float):
    """
    Manually track a request metric.

    Useful for custom instrumentation outside middleware.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request path
        status: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_auth_attempt(success: bool):
    """Track authentication attempt."""
    status = "success" if success else "failure"
    auth_attempts_total.labels(status=status).inc()


def track_token_validation(valid: bool, expired: bool = False):
    """Track JWT token validation."""
    if valid:
        status = "valid"
    elif expired:
        status = "expired"
    else:
        status = "invalid"

    auth_token_validations_total.labels(status=status).inc()


def track_conversation(user_role: str):
    """Track conversation processing."""
    conversations_total.labels(user_role=user_role).inc()


def track_memory_operation(operation: str, success: bool):
    """Track memory system operations."""
    status = "success" if success else "failure"
    memory_operations_total.labels(operation=operation, status=status).inc()


def set_active_users(count: int):
    """Set current active user count."""
    active_users_gauge.set(count)
