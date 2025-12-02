"""
Session tracking middleware for performance timing and context propagation.

Provides request/session ID generation, performance timing, and context
propagation across FastAPI requests for comprehensive chat session tracking.
"""

import time
import uuid
import logging
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class SessionTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for session tracking and performance timing."""

    def __init__(self, app, call_next: Callable = None):
        super().__init__(app)
        self.call_next = call_next

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with session tracking and timing."""
        # Generate unique request ID
        request_id = f"req_{uuid.uuid4().hex[:12]}"

        # Extract or generate session/thread ID
        session_id = self._get_or_create_session_id(request)
        thread_id = self._get_or_create_thread_id(request)

        # Extract user ID from request (header, query param, or path)
        user_id = self._extract_user_id(request)

        # Start timing
        start_time = time.time()

        # Add context to request state
        request.state.session_id = session_id
        request.state.thread_id = thread_id
        request.state.user_id = user_id
        request.state.request_id = request_id
        request.state.start_time = start_time

        # Log request start
        logger.info(f"Request started: {request.method} {request.url.path} - "
                   f"request_id={request_id}, user_id={user_id}, thread_id={thread_id}")

        try:
            # Process request
            response = await call_next(request)

            # Calculate total processing time
            processing_time = time.time() - start_time

            # Add timing headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Session-ID"] = session_id
            response.headers["X-Processing-Time-Ms"] = str(int(processing_time * 1000))

            # Log request completion
            logger.info(f"Request completed: {request.method} {request.url.path} - "
                       f"status={response.status_code}, time={processing_time:.3f}s, "
                       f"request_id={request_id}")

            return response

        except Exception as e:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time

            logger.error(f"Request failed: {request.method} {request.url.path} - "
                        f"error={str(e)}, time={processing_time:.3f}s, "
                        f"request_id={request_id}", exc_info=True)

            # Re-raise the exception
            raise

    def _get_or_create_session_id(self, request: Request) -> str:
        """Get existing session ID from request or create new one."""
        # Check headers first
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            return session_id

        # Check query parameters
        session_id = request.query_params.get("session_id")
        if session_id:
            return session_id

        # Check for OpenAI session context
        if hasattr(request.state, 'openai_session_id'):
            return request.state.openai_session_id

        # Create new session ID
        return f"sess_{uuid.uuid4().hex[:12]}"

    def _get_or_create_thread_id(self, request: Request) -> str:
        """Get existing thread ID from request or create new one."""
        # Check headers first
        thread_id = request.headers.get("X-Thread-ID")
        if thread_id:
            return thread_id

        # Check query parameters
        thread_id = request.query_params.get("thread_id")
        if thread_id:
            return thread_id

        # Check for OpenAI thread context
        if hasattr(request.state, 'openai_thread_id'):
            return request.state.openai_thread_id

        # For chat endpoints, create thread ID from user_id
        if "/chat" in request.url.path or "/v1/chat/completions" in request.url.path:
            user_id = self._extract_user_id(request)
            return f"thread_{user_id}_{uuid.uuid4().hex[:8]}"

        # Create generic thread ID
        return f"thread_{uuid.uuid4().hex[:12]}"

    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request in various ways."""
        # Check headers first
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id

        # Check query parameters
        user_id = request.query_params.get("user_id")
        if user_id:
            return user_id

        # Check for authenticated user from JWT
        if hasattr(request.state, 'user') and request.state.user:
            return getattr(request.state.user, 'user_id', 'unknown')

        # Check for user in request state (set by auth middleware)
        if hasattr(request.state, 'user_id'):
            return request.state.user_id

        # For OpenAI-compatible endpoint, check request body user field
        if "/v1/chat/completions" in request.url.path:
            # This will be handled in the endpoint itself since we need to parse JSON
            return "pending_openai"

        return "anonymous"

class PerformanceTimer:
    """Context manager for timing specific operations."""

    def __init__(self, operation_name: str, request: Request):
        self.operation_name = operation_name
        self.request = request
        self.start_time = None
        self.end_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        logger.debug(f"Starting operation: {self.operation_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = (self.end_time - self.start_time) * 1000  # Convert to ms

        logger.debug(f"Completed operation: {self.operation_name} - {duration:.2f}ms")

        # Store timing in request state for later use
        if not hasattr(self.request.state, 'operation_timings'):
            self.request.state.operation_timings = {}

        self.request.state.operation_timings[self.operation_name] = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": duration
        }

class SessionContext:
    """Utility class for managing session context across requests."""

    @staticmethod
    def get_session_context(request: Request) -> Dict[str, Any]:
        """Get complete session context from request."""
        return {
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "session_id": getattr(request.state, 'session_id', 'unknown'),
            "thread_id": getattr(request.state, 'thread_id', 'unknown'),
            "user_id": getattr(request.state, 'user_id', 'unknown'),
            "start_time": getattr(request.state, 'start_time', time.time()),
            "operation_timings": getattr(request.state, 'operation_timings', {}),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else "unknown"
        }

    @staticmethod
    def get_performance_metrics(request: Request) -> Dict[str, float]:
        """Get performance metrics from request."""
        metrics = {}

        # Add operation timings
        operation_timings = getattr(request.state, 'operation_timings', {})
        for op_name, timing in operation_timings.items():
            metrics[f"{op_name}_ms"] = timing["duration_ms"]

        # Add total processing time if available
        if hasattr(request.state, 'start_time'):
            total_time = (time.time() - request.state.start_time) * 1000
            metrics["total_processing_ms"] = total_time

        return metrics

    @staticmethod
    @asynccontextmanager
    async def timer_context(request: Request, operation_name: str):
        """Create a timer context for an operation."""
        async with PerformanceTimer(operation_name, request) as timer:
            yield timer

def add_session_timing(request: Request, operation_name: str, duration_ms: float):
    """Add timing information for an operation."""
    if not hasattr(request.state, 'operation_timings'):
        request.state.operation_timings = {}

    request.state.operation_timings[operation_name] = {
        "duration_ms": duration_ms,
        "timestamp": time.time()
    }

def get_user_agent_info(request: Request) -> Dict[str, str]:
    """Extract user agent information from request."""
    user_agent = request.headers.get("User-Agent", "Unknown")

    # Parse common user agent patterns
    ua_info = {
        "raw": user_agent,
        "is_lobechat": "LobeChat" in user_agent,
        "is_browser": any(browser in user_agent.lower() for browser in
                          ["chrome", "firefox", "safari", "edge"]),
        "is_curl": "curl" in user_agent.lower(),
        "is_postman": "PostmanRuntime" in user_agent
    }

    return ua_info

# Utility functions for endpoint usage
async def time_chat_operation(request: Request, operation_name: str):
    """Create a performance timer for chat operations."""
    return PerformanceTimer(operation_name, request)

def extract_chat_context(request: Request) -> Dict[str, Any]:
    """Extract chat-specific context from request."""
    context = SessionContext.get_session_context(request)

    # Add chat-specific information
    context.update({
        "user_agent": get_user_agent_info(request),
        "content_type": request.headers.get("Content-Type", "unknown"),
        "content_length": request.headers.get("Content-Length", "0")
    })

    return context