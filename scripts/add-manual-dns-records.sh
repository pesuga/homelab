#!/bin/bash

# Script to manually add DNS records to Cloudflare
# This is a temporary solution while we fix external-dns

# Check if API token, zone ID, and IP are provided
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
  echo "Usage: $0 <cloudflare-api-token> <zone-id> <server-ip>"
  echo "You can find your zone ID in the Cloudflare dashboard -> Domain Overview -> API section"
  exit 1
fi

API_TOKEN=$1
ZONE_ID=$2
SERVER_IP=$3

# Function to create or update DNS record
create_record() {
  local name=$1
  
  echo "Creating/updating record for ${name}.pesulabs.net..."
  
  # Check if record exists
  RECORD_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?type=A&name=${name}.pesulabs.net" \
    -H "Authorization: Bearer ${API_TOKEN}" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')
  
  if [ "$RECORD_ID" != "null" ] && [ -n "$RECORD_ID" ]; then
    # Update existing record
    echo "Updating existing record for ${name}.pesulabs.net"
    curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${RECORD_ID}" \
      -H "Authorization: Bearer ${API_TOKEN}" \
      -H "Content-Type: application/json" \
      --data "{\"type\":\"A\",\"name\":\"${name}\",\"content\":\"${SERVER_IP}\",\"ttl\":120,\"proxied\":false}"
  else
    # Create new record
    echo "Creating new record for ${name}.pesulabs.net"
    curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
      -H "Authorization: Bearer ${API_TOKEN}" \
      -H "Content-Type: application/json" \
      --data "{\"type\":\"A\",\"name\":\"${name}\",\"content\":\"${SERVER_IP}\",\"ttl\":120,\"proxied\":false}"
  fi
  
  echo ""
}

# Create/update records for all applications
create_record "owncloud.app"
create_record "n8n.app"
create_record "home-assistant.app"
create_record "glance.app"
create_record "immich.app"

echo "DNS records created/updated. Changes may take a few minutes to propagate."
echo "You can verify the records in the Cloudflare dashboard."
