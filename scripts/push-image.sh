#!/bin/bash
#
# push-image.sh - Standardized image push script with registry enforcement
#
# Usage:
#   ./scripts/push-image.sh <service-name> <tag> [additional-tags...]
#
# Examples:
#   ./scripts/push-image.sh family-assistant v1.0.0
#   ./scripts/push-image.sh family-assistant v1.0.0 latest stable
#
# This script enforces:
# - Registry-qualified image names
# - Semantic versioning tags
# - Multi-arch support (optional)
# - Tag validation
# - Registry availability check

set -euo pipefail

# Configuration
REGISTRY="${REGISTRY:-100.81.76.55:30500}"
REGISTRY_PROTOCOL="${REGISTRY_PROTOCOL:-http}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" >&2
}

info() {
    echo -e "${GREEN}INFO: $1${NC}"
}

check_registry() {
    info "Checking registry availability at ${REGISTRY_PROTOCOL}://${REGISTRY}..."
    if ! curl -sf "${REGISTRY_PROTOCOL}://${REGISTRY}/v2/" > /dev/null; then
        error "Registry at ${REGISTRY} is not accessible"
    fi
    info "Registry is accessible"
}

validate_tag() {
    local tag="$1"

    # Allow latest, stable, dev
    if [[ "$tag" =~ ^(latest|stable|dev)$ ]]; then
        return 0
    fi

    # Semantic versioning: v1.0.0, v1.0.0-alpha.1, etc.
    if [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$ ]]; then
        return 0
    fi

    # Git commit SHA (short or long)
    if [[ "$tag" =~ ^[a-f0-9]{7,40}$ ]]; then
        return 0
    fi

    # Feature branches: feature-name
    if [[ "$tag" =~ ^[a-z0-9-]+$ ]]; then
        warning "Tag '$tag' doesn't follow semantic versioning"
        return 0
    fi

    error "Invalid tag format: $tag"
}

push_image() {
    local service="$1"
    local tag="$2"
    local qualified_image="${REGISTRY}/${service}:${tag}"

    # Check if local image exists
    if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${service}:${tag}$"; then
        error "Local image ${service}:${tag} not found. Build it first with: docker build -t ${service}:${tag} ."
    fi

    info "Tagging image ${service}:${tag} as ${qualified_image}..."
    docker tag "${service}:${tag}" "${qualified_image}"

    info "Pushing ${qualified_image} to registry..."
    if docker push "${qualified_image}"; then
        info "✓ Successfully pushed ${qualified_image}"
        return 0
    else
        error "Failed to push ${qualified_image}"
    fi
}

# Main script
main() {
    # Check arguments
    if [ $# -lt 2 ]; then
        cat <<EOF
Usage: $0 <service-name> <tag> [additional-tags...]

Arguments:
  service-name    Name of the service (e.g., family-assistant)
  tag            Primary tag (e.g., v1.0.0, latest)
  additional-tags Additional tags to apply (optional)

Tag Formats:
  - Semantic versioning: v1.0.0, v2.1.3-alpha.1
  - Git commit: abc1234, abc1234567890abcdef
  - Environment: latest, stable, dev
  - Feature branch: feature-auth, fix-bug-123

Examples:
  $0 family-assistant v1.0.0
  $0 family-assistant v1.0.0 latest stable
  $0 homelab-dashboard \$(git describe --tags)
  $0 family-assistant \$(git rev-parse --short HEAD) dev

Environment Variables:
  REGISTRY          Registry host:port (default: 100.81.76.55:30500)
  REGISTRY_PROTOCOL Protocol to use (default: http)
EOF
        exit 1
    fi

    local service="$1"
    shift
    local primary_tag="$1"
    shift
    local additional_tags=("$@")

    # Validate inputs
    info "Service: ${service}"
    info "Primary tag: ${primary_tag}"
    validate_tag "${primary_tag}"

    # Check registry
    check_registry

    # Push primary tag
    push_image "${service}" "${primary_tag}"

    # Push additional tags
    for tag in "${additional_tags[@]}"; do
        info "Processing additional tag: ${tag}"
        validate_tag "${tag}"

        # Tag from primary
        qualified_primary="${REGISTRY}/${service}:${primary_tag}"
        qualified_additional="${REGISTRY}/${service}:${tag}"

        info "Tagging ${qualified_primary} as ${qualified_additional}..."
        docker tag "${qualified_primary}" "${qualified_additional}"

        info "Pushing ${qualified_additional}..."
        if docker push "${qualified_additional}"; then
            info "✓ Successfully pushed ${qualified_additional}"
        else
            error "Failed to push ${qualified_additional}"
        fi
    done

    info ""
    info "===== Push Summary ====="
    info "Service: ${service}"
    info "Primary tag: ${REGISTRY}/${service}:${primary_tag}"
    for tag in "${additional_tags[@]}"; do
        info "Additional: ${REGISTRY}/${service}:${tag}"
    done
    info ""
    info "✓ All images pushed successfully!"
    info ""
    info "To use in Kubernetes:"
    info "  image: ${REGISTRY}/${service}:${primary_tag}"
}

main "$@"
