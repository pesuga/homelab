#!/bin/bash

# Script to test subdomain access for all applications

# Check if arguments are provided
if [ -z "$1" ]; then
  echo "Usage: $0 <domain-base> [--no-ssl]"
  echo "Example: $0 pesulabs.net"
  echo "Options:"
  echo "  --no-ssl: Use HTTP instead of HTTPS"
  exit 1
fi

DOMAIN_BASE=$1
USE_HTTPS=true

# Check for --no-ssl flag
if [ "$2" == "--no-ssl" ]; then
  USE_HTTPS=false
fi

# Function to test a subdomain
test_subdomain() {
  local app=$1
  local subdomain="${app}.app.${DOMAIN_BASE}"
  local protocol="https"
  local curl_opts="-k -s -o /dev/null -w '%{http_code}'"
  
  if [ "$USE_HTTPS" == "false" ]; then
    protocol="http"
  fi
  
  echo -n "Testing ${subdomain}... "
  
  # Execute curl command
  STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "${protocol}://${subdomain}")
  
  # Check the HTTP status code
  if [ "$STATUS" == "000" ]; then
    echo "❌ Failed to connect"
  elif [ "$STATUS" -ge 200 ] && [ "$STATUS" -lt 400 ]; then
    echo "✅ Success (HTTP ${STATUS})"
  else
    echo "⚠️ Received HTTP ${STATUS}"
  fi
}

# Test all application subdomains
echo "Testing subdomain access..."
echo "======================================="
test_subdomain "owncloud"
test_subdomain "n8n"
test_subdomain "home-assistant"
test_subdomain "glance"
test_subdomain "immich"
echo "======================================="
echo "Note: If tests are failing but DNS is set up correctly,"
echo "check your application ingress configurations and"
echo "ensure certificates are valid."
