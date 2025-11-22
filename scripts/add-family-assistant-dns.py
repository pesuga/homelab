#!/usr/bin/env python3
"""
Add Family Assistant DNS record to Cloudflare
Creates app.fa.pesulabs.net → 100.81.76.55
"""

import os
import sys
from cloudflare import Cloudflare

# Configuration
DOMAIN = "pesulabs.net"
SUBDOMAIN = "app"  # For app.fa.pesulabs.net
TAILSCALE_IP = "100.81.76.55"

def get_client():
    """Initialize Cloudflare client from environment variables or credentials file"""
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")

    # If not in environment, try to load from credentials file
    if not api_token:
        creds_file = os.path.expanduser("~/.cloudflare/credentials")
        if os.path.exists(creds_file):
            try:
                with open(creds_file, 'r') as f:
                    for line in f:
                        if line.startswith("CLOUDFLARE_API_TOKEN="):
                            api_token = line.split("=", 1)[1].strip()
                            break
            except Exception as e:
                print(f"ERROR: Failed to read credentials file: {e}")

    if not api_token:
        print("ERROR: CLOUDFLARE_API_TOKEN not found")
        print("\nTo set it up:")
        print("1. Go to https://dash.cloudflare.com/profile/api-tokens")
        print("2. Create Token → Edit zone DNS template")
        print("3. Zone Resources: Include → Specific zone → pesulabs.net")
        print("4. Continue to summary → Create Token")
        print("5. Save the token:")
        print("   echo 'CLOUDFLARE_API_TOKEN=your-token-here' > ~/.cloudflare/credentials")
        print("   chmod 600 ~/.cloudflare/credentials")
        sys.exit(1)

    return Cloudflare(api_token=api_token)

def get_zone_id(client):
    """Get zone ID for pesulabs.net"""
    zones = client.zones.list(name=DOMAIN)
    if not zones.result:
        print(f"ERROR: Zone {DOMAIN} not found in your Cloudflare account")
        sys.exit(1)

    return zones.result[0].id

def add_family_assistant_dns():
    """Add app.fa.pesulabs.net DNS record"""
    print(f"🔧 Adding DNS record for app.{DOMAIN}...\n")

    # Initialize client
    client = get_client()
    zone_id = get_zone_id(client)

    fqdn = f"{SUBDOMAIN}.{DOMAIN}"

    # Check if record already exists
    try:
        existing_records = client.dns.records.list(zone_id=zone_id)
        matching = [r for r in existing_records.result if r.name == fqdn]

        if matching:
            print(f"⏭️  {fqdn} already exists → {matching[0].content}")
            return
    except Exception as e:
        print(f"⚠️  Warning checking existing records: {e}")

    # Create the DNS record
    try:
        record = client.dns.records.create(
            zone_id=zone_id,
            name=fqdn,
            content=TAILSCALE_IP,
            type="A",
            ttl=1,  # Auto (Cloudflare proxy)
            proxied=False  # Don't proxy through Cloudflare (direct to your service)
        )
        print(f"✅ Created {fqdn} → {TAILSCALE_IP}")
        print(f"\n🌐 DNS record created successfully!")
        print(f"📱 Family Assistant will be accessible at: https://{fqdn}/")
        print(f"⏱️  DNS propagation may take a few minutes")
    except Exception as e:
        print(f"❌ Failed to create {fqdn}: {e}")
        sys.exit(1)

def main():
    """Main function"""
    add_family_assistant_dns()

if __name__ == "__main__":
    main()