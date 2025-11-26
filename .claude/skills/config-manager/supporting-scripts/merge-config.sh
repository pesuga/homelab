#!/bin/bash
# Merge discovered config with existing config, preserving manual overrides

CONFIG_FILE="$1"
DISCOVERED_FILE="$2"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Config file not found: $CONFIG_FILE" >&2
  exit 1
fi

if [ ! -f "$DISCOVERED_FILE" ]; then
  echo "❌ Discovered file not found: $DISCOVERED_FILE" >&2
  exit 1
fi

BACKUP="${CONFIG_FILE}.backup-$(date +%Y%m%d-%H%M%S)"
cp "$CONFIG_FILE" "$BACKUP"
echo "📦 Backed up config to $BACKUP" >&2

# Python script for intelligent YAML merging
python3 << 'PYTHON_MERGE_SCRIPT' "$CONFIG_FILE" "$DISCOVERED_FILE"
import sys
import yaml
import os
from datetime import datetime

config_file = sys.argv[1]
discovered_file = sys.argv[2]

# Load existing config
with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

# Load discovered data
with open(discovered_file, 'r') as f:
    discovered = yaml.safe_load(f)

# Merge strategy: Add new, preserve existing with manual overrides

if 'services' in discovered:
    if 'service_validation' not in config:
        config['service_validation'] = {}
    if 'critical_services' not in config['service_validation']:
        config['service_validation']['critical_services'] = []

    existing_names = {s['name'] for s in config['service_validation']['critical_services']}

    for discovered_service in discovered['services']:
        if discovered_service['name'] not in existing_names:
            # Add new service
            new_service = {
                'name': discovered_service['name'],
                'url': discovered_service['url'],
                'health_endpoint': discovered_service.get('health_endpoint', '/'),
                'required': False,  # Default to optional, let user decide
                'auto_discovered': True,
                'discovered_at': datetime.utcnow().isoformat() + 'Z'
            }
            config['service_validation']['critical_services'].append(new_service)
            print(f"✅ Added new service: {discovered_service['name']}", file=sys.stderr)
        else:
            # Check if URL changed
            for existing_service in config['service_validation']['critical_services']:
                if existing_service['name'] == discovered_service['name']:
                    if existing_service.get('url') != discovered_service['url']:
                        if not existing_service.get('url_manual_override'):
                            old_url = existing_service.get('url')
                            existing_service['url'] = discovered_service['url']
                            existing_service['url_updated_at'] = datetime.utcnow().isoformat() + 'Z'
                            print(f"🔄 Updated URL for {discovered_service['name']}: {old_url} → {discovered_service['url']}", file=sys.stderr)

if 'languages' in discovered:
    if 'code_hygiene' not in config:
        config['code_hygiene'] = {}
    if 'detection' not in config['code_hygiene']:
        config['code_hygiene']['detection'] = {}

    discovered_langs = [lang['name'] for lang in discovered['languages']]
    existing_langs = config['code_hygiene']['detection'].get('languages', [])

    for lang in discovered_langs:
        if lang not in existing_langs:
            existing_langs.append(lang)
            print(f"✅ Added language: {lang}", file=sys.stderr)

    config['code_hygiene']['detection']['languages'] = existing_langs

if 'exclude_paths' in discovered:
    if 'code_hygiene' not in config:
        config['code_hygiene'] = {}
    if 'detection' not in config['code_hygiene']:
        config['code_hygiene']['detection'] = {}

    existing_excludes = config['code_hygiene']['detection'].get('exclude_paths', [])

    for exclude in discovered['exclude_paths']:
        if exclude not in existing_excludes:
            existing_excludes.append(exclude)
            print(f"✅ Added exclude path: {exclude}", file=sys.stderr)

    config['code_hygiene']['detection']['exclude_paths'] = existing_excludes

# Write updated config
with open(config_file, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

print(f"✅ Config merged successfully: {config_file}", file=sys.stderr)
PYTHON_MERGE_SCRIPT

echo "" >&2
echo "Review changes with: git diff $CONFIG_FILE" >&2
