#!/bin/bash
#
# build-and-push.sh - Complete build and push pipeline
#
# Usage:
#   ./scripts/build-and-push.sh <service-path> <service-name> <tag> [additional-tags...]
#
# Examples:
#   ./scripts/build-and-push.sh services/family-assistant-enhanced family-assistant v2.0.0 latest
#   ./scripts/build-and-push.sh production/monitoring/homelab-dashboard homelab-dashboard v1.1.0

set -euo pipefail

# Configuration
REGISTRY="${REGISTRY:-100.81.76.55:30500}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${GREEN}INFO: $1${NC}"
}

main() {
    if [ $# -lt 3 ]; then
        cat <<EOF
Usage: $0 <service-path> <service-name> <tag> [additional-tags...]

Arguments:
  service-path    Path to service directory (where Dockerfile lives)
  service-name    Name for the image (e.g., family-assistant)
  tag            Primary tag (e.g., v1.0.0)
  additional-tags Additional tags (e.g., latest stable)

Examples:
  $0 services/family-assistant-enhanced family-assistant v2.0.0 latest
  $0 production/monitoring/homelab-dashboard homelab-dashboard \$(git describe --tags)
EOF
        exit 1
    fi

    local service_path="$1"
    local service_name="$2"
    local primary_tag="$3"
    shift 3
    local additional_tags=("$@")

    # Validate service path
    if [ ! -d "${service_path}" ]; then
        error "Service path does not exist: ${service_path}"
    fi

    if [ ! -f "${service_path}/Dockerfile" ]; then
        error "Dockerfile not found in: ${service_path}"
    fi

    info "Building ${service_name}:${primary_tag} from ${service_path}..."

    # Build image
    if docker build -t "${service_name}:${primary_tag}" "${service_path}"; then
        info "✓ Build successful"
    else
        error "Build failed"
    fi

    # Tag with registry prefix
    local qualified_image="${REGISTRY}/${service_name}:${primary_tag}"
    info "Tagging as ${qualified_image}..."
    docker tag "${service_name}:${primary_tag}" "${qualified_image}"

    # Push using standardized script
    info "Pushing to registry..."
    "${SCRIPT_DIR}/push-image.sh" "${service_name}" "${primary_tag}" "${additional_tags[@]}"

    info ""
    info "✓ Build and push complete!"
    info ""
    info "To deploy:"
    info "  kubectl set image deployment/<deployment-name> <container-name>=${qualified_image} -n homelab"
    info ""
    info "Or update deployment.yaml:"
    info "  image: ${qualified_image}"
}

main "$@"
