"""
OpenTelemetry distributed tracing setup for Family Assistant.

Instruments FastAPI, SQLAlchemy, and Redis for distributed tracing.
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor


def setup_tracing(app, service_name: str = "family-assistant-api"):
    """
    Configure OpenTelemetry distributed tracing.

    Instruments:
    - FastAPI for HTTP request tracing
    - SQLAlchemy for database query tracing
    - Redis for cache operation tracing

    Args:
        app: FastAPI application instance
        service_name: Name of the service for trace identification

    Environment Variables:
        OTEL_EXPORTER_OTLP_ENDPOINT: OpenTelemetry collector endpoint
        ENVIRONMENT: Deployment environment (development, staging, production)
        SERVICE_VERSION: Application version for tracing
    """
    # Skip tracing setup in test environment
    if os.getenv("TESTING") == "true":
        return

    # Create resource with service information
    resource = Resource(attributes={
        "service.name": service_name,
        "service.version": os.getenv("SERVICE_VERSION", "2.0.0"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "service.namespace": "homelab",
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter (sends to OpenTelemetry Collector)
    otlp_endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://otel-collector.homelab.svc.cluster.local:4317"
    )

    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True  # Use TLS in production
    )

    # Add span processor with batching for performance
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        excluded_urls="health,metrics,favicon.ico"
    )

    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument(
        tracer_provider=provider,
        enable_commenter=True,  # Add trace context to SQL queries
    )

    # Instrument Redis
    RedisInstrumentor().instrument(tracer_provider=provider)

    print(f"✅ OpenTelemetry tracing configured: {service_name} -> {otlp_endpoint}")


def get_tracer(name: str = __name__):
    """
    Get tracer for creating custom spans.

    Usage:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("operation_name"):
            # Your code here
            pass

    Args:
        name: Tracer name (usually __name__ of the module)

    Returns:
        Tracer instance for creating spans
    """
    return trace.get_tracer(name)
