"""
Rate limiting middleware using SlowAPI.

Protects API endpoints from abuse with configurable rate limits.
"""

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request


def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Uses authenticated user ID if available, otherwise falls back to IP address.

    Args:
        request: FastAPI request object

    Returns:
        User identifier string for rate limiting
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=[
        "100/minute",  # 100 requests per minute per user/IP
        "1000/hour"    # 1000 requests per hour per user/IP
    ],
    storage_uri=os.getenv(
        "RATE_LIMIT_STORAGE",
        "redis://redis.homelab.svc.cluster.local:6379"
    ),
    strategy="fixed-window"
)


def setup_rate_limiting(app):
    """
    Configure rate limiting for FastAPI application.

    Applies default rate limits to all endpoints.
    Individual endpoints can override with @limiter.limit() decorator.

    Args:
        app: FastAPI application instance

    Example:
        @app.get("/expensive-operation")
        @limiter.limit("5/minute")  # Override default
        async def expensive_operation():
            pass
    """
    # Register limiter with app
    app.state.limiter = limiter

    # Register exception handler for rate limit exceeded
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    print("✅ Rate limiting configured: 100/min, 1000/hour per user/IP")


# Decorators for common rate limit patterns
def auth_rate_limit():
    """
    Strict rate limit for authentication endpoints.

    5 attempts per minute to prevent brute force attacks.
    """
    return limiter.limit("5/minute")


def sensitive_operation_limit():
    """
    Rate limit for sensitive operations (password reset, profile changes).

    10 operations per hour.
    """
    return limiter.limit("10/hour")


def heavy_operation_limit():
    """
    Rate limit for computationally expensive operations.

    20 requests per minute.
    """
    return limiter.limit("20/minute")
