"""
Security headers middleware for Family Assistant.

Adds security headers to all responses following OWASP best practices.
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements OWASP security headers recommendations:
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Enforce HTTPS
    - Content-Security-Policy: Prevent XSS and injection attacks
    - Permissions-Policy: Control browser features
    - Referrer-Policy: Control referrer information
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Add security headers to response."""
        response: Response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable browser XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS for 1 year (31536000 seconds)
        # Include subdomains and allow preloading
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Content Security Policy
        # Restrict resource loading to same origin by default
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow inline scripts for React
            "style-src 'self' 'unsafe-inline'",  # Allow inline styles
            "img-src 'self' data: https:",  # Allow images from data URLs and HTTPS
            "font-src 'self' data:",  # Allow fonts from data URLs
            "connect-src 'self'",  # API calls to same origin
            "frame-ancestors 'none'",  # Prevent framing (same as X-Frame-Options)
            "base-uri 'self'",  # Restrict base tag URLs
            "form-action 'self'",  # Forms can only submit to same origin
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Permissions Policy (formerly Feature-Policy)
        # Disable potentially dangerous browser features
        permissions_directives = [
            "geolocation=()",  # Disable geolocation
            "microphone=()",  # Disable microphone
            "camera=()",  # Disable camera
            "payment=()",  # Disable payment API
            "usb=()",  # Disable USB API
            "magnetometer=()",  # Disable magnetometer
            "gyroscope=()",  # Disable gyroscope
            "accelerometer=()",  # Disable accelerometer
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)

        # Referrer Policy
        # Send referrer only for same-origin requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Cross-Origin policies
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        return response
