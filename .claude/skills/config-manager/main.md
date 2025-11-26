---
name: config-manager
description: |
  Manages self-updating configuration files for validation rules and code hygiene.
  Discovers services, languages, and project structure automatically.
  Use when adding/removing services or when config seems outdated.
category: infrastructure
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
version: "1.0"
---

# Configuration Manager

## Purpose
Keep validation-rules.yaml and code-hygiene.yaml in sync with actual project state.

## Usage

### 1. Discover Current State
```bash
# Discover all services from K8s/Docker
bash .claude/skills/config-manager/supporting-scripts/discover-services.sh

# Discover codebase structure
bash .claude/skills/config-manager/supporting-scripts/discover-codebase-structure.sh
```

### 2. Review Discovered Changes
```bash
# Services
cat tmp/analysis/discovered-services.yaml

# Structure
cat tmp/analysis/discovered-structure.yaml
```

### 3. Merge into Config
```bash
# Merge services into validation-rules.yaml
bash .claude/skills/config-manager/supporting-scripts/merge-config.sh \
  .claude/config/validation-rules.yaml \
  tmp/analysis/discovered-services.yaml

# Merge structure into code-hygiene.yaml
bash .claude/skills/config-manager/supporting-scripts/merge-config.sh \
  .claude/config/code-hygiene.yaml \
  tmp/analysis/discovered-structure.yaml
```

### 4. Review and Commit
```bash
# Review changes
git diff .claude/config/validation-rules.yaml
git diff .claude/config/code-hygiene.yaml

# Commit if acceptable
git add .claude/config/
git commit -m "chore: update config files based on auto-discovery"
```

## Manual Overrides

To prevent auto-updates from changing specific values:

### Validation Rules
Add `url_manual_override: true` to any service:
```yaml
critical_services:
  - name: custom_service
    url: https://custom.domain.com
    url_manual_override: true  # Prevents auto-update
```

### Code Hygiene
Add `manual_config: true` to prevent language detection overrides:
```yaml
detection:
  languages:
    - python
    - rust  # Not detected, manually added
  manual_config: true
```

## Automation

### Periodic Discovery (Monthly)
Add to cron or run manually:
```bash
bash .claude/skills/config-manager/supporting-scripts/run-discovery-check.sh
```

This will:
1. Run discovery
2. Compare with current config
3. Generate report of differences
4. Prompt for merge approval
