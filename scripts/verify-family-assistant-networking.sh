#!/bin/bash
# Family Assistant Network Connectivity Verification
# Run this script to verify backend is accessible from compute node
#
# Usage: ./verify-family-assistant-networking.sh

set -e

TAILSCALE_IP="100.81.76.55"
NODEPORT="30801"
NAMESPACE="homelab"
SERVICE_NAME="family-assistant-nodeport"

echo "=========================================="
echo "Family Assistant Network Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Check Tailscale connectivity
echo "1. Checking Tailscale Connectivity"
echo "-------------------------------------------"
if ping -c 1 -W 2 $TAILSCALE_IP > /dev/null 2>&1; then
    check_pass "Tailscale mesh connectivity to $TAILSCALE_IP"
else
    check_fail "Cannot ping $TAILSCALE_IP via Tailscale"
    exit 1
fi
echo ""

# 2. Check K3s service exists
echo "2. Checking K3s Service Configuration"
echo "-------------------------------------------"
if kubectl get svc -n $NAMESPACE $SERVICE_NAME > /dev/null 2>&1; then
    check_pass "Service $SERVICE_NAME exists in namespace $NAMESPACE"
else
    check_fail "Service $SERVICE_NAME not found in namespace $NAMESPACE"
    exit 1
fi
echo ""

# 3. Check service has endpoints
echo "3. Checking Service Endpoints"
echo "-------------------------------------------"
ENDPOINTS=$(kubectl get endpoints -n $NAMESPACE $SERVICE_NAME -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null)
if [ -z "$ENDPOINTS" ]; then
    check_fail "Service has NO endpoints - selector mismatch with pods!"
    echo ""
    echo "Debugging information:"
    echo "Service selector:"
    kubectl get svc -n $NAMESPACE $SERVICE_NAME -o jsonpath='{.spec.selector}' | jq '.'
    echo ""
    echo "Pod labels:"
    kubectl get pods -n $NAMESPACE -l app=family-assistant-backend --show-labels
    exit 1
else
    check_pass "Service has endpoints: $ENDPOINTS"
    kubectl get endpoints -n $NAMESPACE $SERVICE_NAME
fi
echo ""

# 4. Check pod status
echo "4. Checking Backend Pod Status"
echo "-------------------------------------------"
POD_STATUS=$(kubectl get pods -n $NAMESPACE -l app=family-assistant-backend -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
if [ "$POD_STATUS" == "Running" ]; then
    check_pass "Backend pod is running"
    kubectl get pods -n $NAMESPACE -l app=family-assistant-backend
else
    check_fail "Backend pod is not running (status: $POD_STATUS)"
    exit 1
fi
echo ""

# 5. Test HTTP connectivity via Tailscale
echo "5. Testing HTTP Connectivity"
echo "-------------------------------------------"
HEALTH_URL="http://${TAILSCALE_IP}:${NODEPORT}/health"
echo "Testing: $HEALTH_URL"
if HTTP_RESPONSE=$(curl -s --connect-timeout 5 "$HEALTH_URL"); then
    check_pass "Backend responds to health check"
    echo "Response: $HTTP_RESPONSE" | jq '.' 2>/dev/null || echo "Response: $HTTP_RESPONSE"
else
    check_fail "Backend does not respond on $HEALTH_URL"
    exit 1
fi
echo ""

# 6. Verify label consistency
echo "6. Verifying Label Consistency"
echo "-------------------------------------------"
SERVICE_SELECTOR=$(kubectl get svc -n $NAMESPACE $SERVICE_NAME -o jsonpath='{.spec.selector.app}')
POD_LABEL=$(kubectl get pods -n $NAMESPACE -l app=family-assistant-backend -o jsonpath='{.items[0].metadata.labels.app}' 2>/dev/null)

if [ "$SERVICE_SELECTOR" == "$POD_LABEL" ]; then
    check_pass "Service selector matches pod labels (app: $POD_LABEL)"
else
    check_warn "Service selector ($SERVICE_SELECTOR) differs from pod label ($POD_LABEL)"
fi
echo ""

# Summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo ""
check_pass "All connectivity checks passed"
echo ""
echo "Frontend Connection String:"
echo "  API_URL=http://${TAILSCALE_IP}:${NODEPORT}"
echo ""
echo "Available Endpoints:"
echo "  Health Check: http://${TAILSCALE_IP}:${NODEPORT}/health"
echo "  API Root: http://${TAILSCALE_IP}:${NODEPORT}/"
echo ""
