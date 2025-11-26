#!/bin/bash
# Auto-discover services from Kubernetes manifests and docker-compose files

OUTPUT="tmp/analysis/discovered-services.yaml"
mkdir -p tmp/analysis

echo "🔍 Discovering services from infrastructure..." >&2
echo "# Auto-discovered services - $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$OUTPUT"
echo "services:" >> "$OUTPUT"

# Discover from Kubernetes manifests
if [ -d "infrastructure/kubernetes" ]; then
  echo "  📦 Scanning Kubernetes manifests..." >&2

  find infrastructure/kubernetes -name "*.yaml" -o -name "*.yml" | while read -r manifest; do
    # Extract IngressRoute for Traefik
    if grep -q "kind: IngressRoute" "$manifest"; then
      SERVICE_NAME=$(grep -A 5 "kind: IngressRoute" "$manifest" | grep "name:" | head -1 | awk '{print $2}')
      HOST=$(grep -A 20 "kind: IngressRoute" "$manifest" | grep "Host(" | head -1 | grep -oP 'Host\(\`\K[^`]+')

      if [ -n "$SERVICE_NAME" ] && [ -n "$HOST" ]; then
        cat >> "$OUTPUT" << EOF
  - name: $SERVICE_NAME
    url: https://$HOST
    health_endpoint: /
    source: kubernetes
    manifest: $manifest
EOF
      fi
    fi

    # Extract Service endpoints
    if grep -q "kind: Service" "$manifest"; then
      SERVICE_NAME=$(grep -A 5 "kind: Service" "$manifest" | grep "name:" | head -1 | awk '{print $2}')
      PORT=$(grep -A 10 "kind: Service" "$manifest" | grep "port:" | head -1 | awk '{print $2}')

      if [ -n "$SERVICE_NAME" ] && [ -n "$PORT" ]; then
        cat >> "$OUTPUT" << EOF
  - name: ${SERVICE_NAME}_internal
    url: http://$SERVICE_NAME:$PORT
    health_endpoint: /
    source: kubernetes
    manifest: $manifest
EOF
      fi
    fi
  done
fi

# Discover from Docker Compose
if [ -d "infrastructure/docker" ]; then
  echo "  🐳 Scanning Docker Compose files..." >&2

  find infrastructure/docker -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | while read -r compose; do
    # Extract service names and ports
    grep -A 10 "services:" "$compose" | grep "^\s\+[a-z]" | while read -r service_line; do
      SERVICE_NAME=$(echo "$service_line" | sed 's/://g' | xargs)
      PORT=$(grep -A 5 "$SERVICE_NAME:" "$compose" | grep "ports:" -A 1 | tail -1 | grep -oP '\d+:\K\d+' | head -1)

      if [ -n "$SERVICE_NAME" ] && [ -n "$PORT" ]; then
        cat >> "$OUTPUT" << EOF
  - name: ${SERVICE_NAME}_docker
    url: http://localhost:$PORT
    health_endpoint: /
    source: docker_compose
    manifest: $compose
EOF
      fi
    done
  done
fi

echo "✅ Service discovery complete: $OUTPUT" >&2
cat "$OUTPUT" >&2
