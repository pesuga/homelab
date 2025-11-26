# Homelab Scripts

Utility scripts for building, pushing, and managing homelab services.

## Image Management Scripts

### push-image.sh

Push Docker images to the homelab registry with proper naming enforcement.

**Usage**: `./scripts/push-image.sh <service-name> <tag> [additional-tags...]`

**Examples**:
```bash
./scripts/push-image.sh family-assistant v2.0.0
./scripts/push-image.sh family-assistant v2.0.0 latest stable
```

### build-and-push.sh

Complete build and push pipeline for services.

**Usage**: `./scripts/build-and-push.sh <service-path> <service-name> <tag> [additional-tags...]`

**Examples**:
```bash
./scripts/build-and-push.sh services/family-assistant-enhanced family-assistant v2.0.0 latest
```

See script files for detailed documentation and troubleshooting.

---

## Health Check Scripts

### health-check-all.sh

Comprehensive service validation script used by validation hooks and manual checks.

**Usage**: `./scripts/health-check-all.sh`

**Purpose**:
- Validates all critical services are responding
- Checks HTTP status codes
- Measures response times
- Used by `/verify-claim` and `/validate-session` commands

**Output**:
- ✅ Service responding correctly
- ❌ Service failing validation
- Summary report with all services

### service-check-urls.sh

HTTP endpoint verification for services.

**Usage**: `./scripts/service-check-urls.sh`

**Purpose**:
- Test HTTP/HTTPS endpoints
- Verify certificates
- Check response codes
- Quick service status check

---

## Script Categories

### Permanent Scripts (This Directory)
- **Image Management**: build-and-push.sh, push-image.sh
- **Health Checks**: health-check-all.sh, service-check-urls.sh
- **Validation**: Scripts used by hooks and commands

### Temporary Scripts (tmp/scripts/)
- One-time debugging scripts
- Experimental automation
- Quick helper scripts
- Should be deleted after use

---

## Usage Guidelines

### When to Add New Scripts

Add scripts to this directory when:
- Script will be used repeatedly
- Script is part of deployment workflow
- Script is used by hooks or commands
- Script provides reusable utility

### When to Use tmp/scripts/

Use tmp/scripts/ for:
- One-time migrations
- Debugging sessions
- Experimental automation
- Quick throwaway helpers

---

## References

- **Validation Rules**: `.claude/config/validation-rules.yaml`
- **Hook Configuration**: `.claude/hooks/hooks.json`
- **Project Context**: `project-context/README.md`
