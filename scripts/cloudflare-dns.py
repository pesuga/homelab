#!/usr/bin/env python3
"""
Cloudflare DNS Management Script for Homelab
Manages DNS records for homelab.pesulabs.net subdomain
"""

import os
import sys
from cloudflare import Cloudflare

# Configuration
DOMAIN = "pesulabs.net"
SUBDOMAIN = "homelab"
TAILSCALE_IP = "100.81.76.55"

# Services to create DNS records for
# Note: These create subdomains under homelab.pesulabs.net (e.g., grafana.homelab.pesulabs.net)
SERVICES = [
    "grafana",
    "prometheus",
    "n8n",
    "webui"
]

# Root homelab domain (homelab.pesulabs.net) for the landing page
ROOT_HOMELAB_DOMAIN = True

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

def list_dns_records(client, zone_id):
    """List all DNS records for homelab subdomain"""
    records = client.dns.records.list(zone_id=zone_id)

    print(f"\n📋 DNS Records for {SUBDOMAIN}.{DOMAIN}:\n")

    all_records = []

    # Check root homelab domain
    if ROOT_HOMELAB_DOMAIN:
        root_fqdn = f"{SUBDOMAIN}.{DOMAIN}"
        matching = [r for r in records.result if r.name == root_fqdn]

        if matching:
            record = matching[0]
            all_records.append(record)
            print(f"✅ {record.name:<40} → {record.content:<15} (Dashboard)")
        else:
            print(f"❌ {root_fqdn:<40} → Not configured")

    # Check service subdomains
    for service in SERVICES:
        fqdn = f"{service}.{SUBDOMAIN}.{DOMAIN}"
        matching = [r for r in records.result if r.name == fqdn]

        if matching:
            record = matching[0]
            all_records.append(record)
            print(f"✅ {record.name:<40} → {record.content:<15}")
        else:
            print(f"❌ {fqdn:<40} → Not configured")

    return all_records

def create_dns_records(client, zone_id):
    """Create DNS records for all homelab services"""
    print(f"\n🔧 Creating DNS records for {SUBDOMAIN}.{DOMAIN}...\n")

    existing_records = client.dns.records.list(zone_id=zone_id)
    existing_names = {r.name for r in existing_records.result}

    # Create root homelab domain record
    if ROOT_HOMELAB_DOMAIN:
        root_fqdn = f"{SUBDOMAIN}.{DOMAIN}"

        if root_fqdn in existing_names:
            print(f"⏭️  {root_fqdn} (Dashboard) already exists, skipping")
        else:
            try:
                record = client.dns.records.create(
                    zone_id=zone_id,
                    name=root_fqdn,
                    content=TAILSCALE_IP,
                    type="A",
                    ttl=1,  # Auto (Cloudflare proxy)
                    proxied=False  # Don't proxy through Cloudflare (Tailscale only)
                )
                print(f"✅ Created {root_fqdn} → {TAILSCALE_IP} (Dashboard)")
            except Exception as e:
                print(f"❌ Failed to create {root_fqdn}: {e}")

    # Create service subdomain records
    for service in SERVICES:
        fqdn = f"{service}.{SUBDOMAIN}.{DOMAIN}"

        if fqdn in existing_names:
            print(f"⏭️  {fqdn} already exists, skipping")
            continue

        try:
            record = client.dns.records.create(
                zone_id=zone_id,
                name=fqdn,
                content=TAILSCALE_IP,
                type="A",
                ttl=1,  # Auto (Cloudflare proxy)
                proxied=False  # Don't proxy through Cloudflare (Tailscale only)
            )
            print(f"✅ Created {fqdn} → {TAILSCALE_IP}")
        except Exception as e:
            print(f"❌ Failed to create {fqdn}: {e}")

    print("\n✨ DNS record creation complete!")

def delete_dns_records(client, zone_id):
    """Delete all homelab DNS records"""
    print(f"\n🗑️  Deleting DNS records for {SUBDOMAIN}.{DOMAIN}...\n")

    records = client.dns.records.list(zone_id=zone_id)

    # Delete root homelab domain
    if ROOT_HOMELAB_DOMAIN:
        root_fqdn = f"{SUBDOMAIN}.{DOMAIN}"
        matching = [r for r in records.result if r.name == root_fqdn]

        if not matching:
            print(f"⏭️  {root_fqdn} (Dashboard) doesn't exist, skipping")
        else:
            try:
                client.dns.records.delete(zone_id=zone_id, dns_record_id=matching[0].id)
                print(f"✅ Deleted {root_fqdn} (Dashboard)")
            except Exception as e:
                print(f"❌ Failed to delete {root_fqdn}: {e}")

    # Delete service subdomains
    for service in SERVICES:
        fqdn = f"{service}.{SUBDOMAIN}.{DOMAIN}"
        matching = [r for r in records.result if r.name == fqdn]

        if not matching:
            print(f"⏭️  {fqdn} doesn't exist, skipping")
            continue

        try:
            client.dns.records.delete(zone_id=zone_id, dns_record_id=matching[0].id)
            print(f"✅ Deleted {fqdn}")
        except Exception as e:
            print(f"❌ Failed to delete {fqdn}: {e}")

    print("\n✨ DNS record deletion complete!")

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  ./cloudflare-dns.py list      - List current DNS records")
        print("  ./cloudflare-dns.py create    - Create DNS records for all services")
        print("  ./cloudflare-dns.py delete    - Delete all homelab DNS records")
        sys.exit(1)

    command = sys.argv[1]

    # Initialize client
    client = get_client()
    zone_id = get_zone_id(client)

    print(f"🌐 Managing DNS for zone: {DOMAIN} (ID: {zone_id})")

    if command == "list":
        list_dns_records(client, zone_id)
    elif command == "create":
        create_dns_records(client, zone_id)
        print("\n" + "="*60)
        list_dns_records(client, zone_id)
    elif command == "delete":
        delete_dns_records(client, zone_id)
    else:
        print(f"ERROR: Unknown command '{command}'")
        sys.exit(1)

if __name__ == "__main__":
    main()
