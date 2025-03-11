FROM n8nio/n8n:latest

# Install additional monitoring tools
RUN npm install --global prom-client@14.2.0

# Add custom healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5678/healthz || exit 1

# Enable metrics by default
ENV N8N_METRICS=true
ENV N8N_METRICS_PREFIX=n8n_

# Add security hardening
RUN addgroup --system --gid 1001 n8n && \
    adduser --system --uid 1001 --ingroup n8n n8n
USER n8n
