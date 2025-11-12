"""
Structured JSON logging configuration for Family Assistant.

Provides consistent, parseable log output for aggregation in Loki.
"""

import os
import logging
import sys
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with additional context fields.

    Adds service metadata to every log entry for better filtering and aggregation.
    """

    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add service metadata
        log_record['service'] = 'family-assistant-api'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_record['version'] = os.getenv('SERVICE_VERSION', '2.0.0')

        # Add trace context if available (from OpenTelemetry)
        if hasattr(record, 'otelTraceID'):
            log_record['trace_id'] = record.otelTraceID
            log_record['span_id'] = record.otelSpanID


def setup_logging(log_level: str = None):
    """
    Configure structured JSON logging.

    Logs are output to stdout in JSON format for collection by Promtail/Loki.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  Defaults to INFO in production, DEBUG in development

    Environment Variables:
        LOG_LEVEL: Override log level
        ENVIRONMENT: Set to 'development' for more verbose logging
        TESTING: Set to 'true' to disable logging in tests
    """
    # Skip logging setup in tests
    if os.getenv("TESTING") == "true":
        logging.disable(logging.CRITICAL)
        return

    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL")

    if log_level is None:
        # Default to DEBUG in development, INFO in production
        environment = os.getenv("ENVIRONMENT", "development")
        log_level = "DEBUG" if environment == "development" else "INFO"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create stdout handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)

    # JSON format with all necessary fields
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={
            'levelname': 'level',
            'name': 'logger',
            'asctime': 'timestamp'
        },
        datefmt='%Y-%m-%dT%H:%M:%S'
    )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Reduce noise from verbose libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    print(f"✅ Structured logging configured: {log_level}")


def get_logger(name: str = __name__):
    """
    Get logger instance for a module.

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing request", extra={"user_id": user.id})

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Logger instance with JSON formatting
    """
    return logging.getLogger(name)
