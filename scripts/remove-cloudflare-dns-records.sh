#!/bin/bash

# Script to remove DNS records from Cloudflare
# This is useful when you want to restrict access to your homelab to local network only

# Check if API token and zone ID are provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <cloudflare-api-token> <zone-id>"
  echo "You can find your zone ID in the Cloudflare dashboard -> Domain Overview -> API section"
  exit 1
fi

API_TOKEN=$1
ZONE_ID=$2

# Services to remove
SERVICES=(
  "owncloud.app"
  "n8n.app"
  "home-assistant.app"
  "glance.app"
  "immich.app"
  "grafana.app"
  "prometheus.app"
  "homer.app"
)

# Function to remove DNS record
remove_record() {
  local name=$1
  
  echo "Checking for record ${name}.pesulabs.net..."
  
  # Check if record exists
  RECORD_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?type=A&name=${name}.pesulabs.net" \
    -H "Authorization: Bearer ${API_TOKEN}" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')
  
  if [ "$RECORD_ID" != "null" ] && [ -n "$RECORD_ID" ]; then
    # Remove existing record
    echo "Removing record for ${name}.pesulabs.net (ID: ${RECORD_ID})"
    RESULT=$(curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${RECORD_ID}" \
      -H "Authorization: Bearer ${API_TOKEN}" \
      -H "Content-Type: application/json")
    
    SUCCESS=$(echo $RESULT | jq -r '.success')
    if [ "$SUCCESS" = "true" ]; then
      echo "Successfully removed record for ${name}.pesulabs.net"
    else
      ERROR=$(echo $RESULT | jq -r '.errors[0].message')
      echo "Failed to remove record for ${name}.pesulabs.net: ${ERROR}"
    fi
  else
    echo "No record found for ${name}.pesulabs.net"
  fi
  
  echo ""
}

echo "=== Removing Cloudflare DNS Records ==="
echo ""
echo "This script will remove DNS records for your homelab services from Cloudflare."
echo "This is useful when you want to restrict access to your local network only."
echo ""
read -p "Are you sure you want to continue? (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Operation cancelled."
  exit 0
fi

echo ""
echo "Removing DNS records..."
echo ""

# Remove records for all services
for service in "${SERVICES[@]}"; do
  remove_record "$service"
done

echo "DNS records removal completed."
echo "Your homelab services should no longer be accessible from the internet via DNS."
echo "Make sure to set up local DNS resolution using the setup-local-dns.sh script."
