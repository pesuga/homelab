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
