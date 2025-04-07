#!/bin/bash

# List of service URLs to test
# Assuming HTTPS for all services based on ingress configurations
services=(
  "https://homer.app.pesulabs.net"
  "https://glance.app.pesulabs.net"
  "https://home-assistant.app.pesulabs.net"
  "https://immich.app.pesulabs.net"
  "https://jellyfin.app.pesulabs.net"
  "https://n8n.app.pesulabs.net"
  "https://owncloud.app.pesulabs.net"
)

echo "Starting Homelab Service Health Check..."
echo "========================================"

all_ok=true

for url in "${services[@]}"; do
  echo -n "Checking $url ... "
  # Use curl to get the HTTP status code
  # -s: Silent mode
  # -o /dev/null: Discard output
  # -w '%{http_code}': Write out the HTTP status code
  # --max-time 5: Timeout after 5 seconds
  # -k: Allow insecure connections (useful for self-signed certs like homer/immich)
  status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -k "$url")

  # Check if the status code is 2xx or 3xx (indicating success or redirect)
  if [[ "$status_code" =~ ^[23] ]]; then
    echo "OK (Status: $status_code)"
  else
    echo "FAILED (Status: $status_code)"
    all_ok=false
  fi
done

echo "========================================"
if $all_ok; then
  echo "All services checked successfully."
  exit 0
else
  echo "Some services failed the health check."
  exit 1
fi
