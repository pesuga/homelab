# Multi-stage production Dockerfile for Family AI Platform
# Build stage
FROM python:3.12-slim as builder

# Set build arguments
ARG BUILD_ENV=production
ARG APP_VERSION=1.0.0

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY core/requirements.txt .
COPY core/requirements-dev.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    if [ "$BUILD_ENV" = "development" ]; then \
        pip install -r requirements-dev.txt; \
    fi

# Production stage
FROM python:3.12-slim as production

# Set production arguments
ARG BUILD_ENV=production
ARG APP_VERSION=1.0.0
ARG VCS_REF
ARG BUILD_DATE
ARG BUILD_URL

# Set labels for container metadata
LABEL maintainer="Family AI Platform Team" \
      version="${APP_VERSION}" \
      build.env="${BUILD_ENV}" \
      vcs.ref="${VCS_REF}" \
      build.date="${BUILD_DATE}" \
      build.url="${BUILD_URL}" \
      org.opencontainers.image.title="Family AI Platform" \
      org.opencontainers.image.description="Private, trustworthy AI for families with voice interaction, secure communication, and family management" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="${BUILD_URL}"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_VERSION="${APP_VERSION}" \
    BUILD_ENV="${BUILD_ENV}"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    jq \
    netcat-openbsd \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r familyai && \
    useradd -r -g familyai -d /app -s /bin/bash familyai

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application directory
WORKDIR /app

# Copy application code with proper permissions
COPY --chown=familyai:familyai ./core/ ./core/
COPY --chown=familyai:familyai ./production/ ./production/
COPY --chown=familyai:familyai .env.example .env

# Set ownership and permissions
RUN chown -R familyai:familyai /app && \
    chmod +x /app/core/start.sh

# Switch to non-root user
USER familyai

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Set default command
CMD ["python", "core/api/main.py", "--host", "0.0.0.0", "--port", "8000"]