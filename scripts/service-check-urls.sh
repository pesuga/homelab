#!/bin/bash
# URL-based Service Status Checker
# Tests actual deployed services via their URLs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🔗 Homelab Service URL Status Checker"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Service list based on actual deployment status
# These are the services that should be working based on our health check

declare -A SERVICES=(
    ["N8n"]="http://100.81.76.55:30678/healthz"
    ["Prometheus"]="http://100.81.76.55:30090/-/healthy"
    ["Loki"]="http://100.81.76.55:30314/ready"
    ["Qdrant"]="http://100.81.76.55:30633/collections"
    ["Docker Registry"]="http://100.81.76.55:30500/v2/_catalog"
    ["Mem0"]="http://100.81.76.55:30880/docs"
    ["Homelab Dashboard"]="http://100.81.76.55:30800/"
)

# Function to check HTTP endpoint with detailed output
check_service() {
    local service=$1
    local url=$2

    echo -n "Testing $service... "

    # Check HTTP status with timeout
    if response=$(curl -s --max-time 10 --connect-timeout 5 -w "HTTP_STATUS:%{http_code}" "$url" 2>/dev/null); then
        # Extract HTTP status
        http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
        body=$(echo "$response" | sed 's/HTTP_STATUS:[0-9]*$//')

        case $http_status in
            200)
                echo -e "${GREEN}✓ OK${NC} (HTTP $http_status)"
                return 0
                ;;
            307|302)
                echo -e "${GREEN}✓ OK${NC} (HTTP $http_status - Redirecting to login)"
                return 0
                ;;
            429)
                echo -e "${YELLOW}⚠ OK${NC} (HTTP $http_status - Rate limited but responding)"
                return 0
                ;;
            *)
                echo -e "${RED}✗ FAIL${NC} (HTTP $http_status)"
                return 1
                ;;
        esac
    else
        echo -e "${RED}✗ FAIL${NC} (Connection failed)"
        return 1
    fi
}

# Track statistics
TOTAL=${#SERVICES[@]}
SUCCESS=0
FAILED=0

# Check each service
echo "Service Status:"
echo "==============="

for service in "${!SERVICES[@]}"; do
    url="${SERVICES[$service]}"
    if check_service "$service" "$url"; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi
done

echo ""
echo "=========================================="
echo "📊 Summary"
echo "=========================================="
echo -e "Total Services: ${BLUE}$TOTAL${NC}"
echo -e "Successful: ${GREEN}$SUCCESS${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ "$TOTAL" -gt 0 ]; then
    SUCCESS_RATE=$((SUCCESS * 100 / TOTAL))
    echo -e "Success Rate: ${SUCCESS_RATE}%"

    if [ "$SUCCESS_RATE" -ge 80 ]; then
        echo -e "Status: ${GREEN}✓ Healthy${NC}"
    elif [ "$SUCCESS_RATE" -ge 60 ]; then
        echo -e "Status: ${YELLOW}⚠ Degraded${NC}"
    else
        echo -e "Status: ${RED}✗ Critical${NC}"
    fi
fi

echo ""
echo "=========================================="
echo "📝 Service Access URLs"
echo "=========================================="
echo "Access these services in your browser:"
echo ""

for service in "${!SERVICES[@]}"; do
    url="${SERVICES[$service]}"
    # Extract base URL (without health check path)
    base_url=$(echo "$url" | sed 's|/healthz$||' | sed 's|/-/healthy$||' | sed 's|/ready$||' | sed 's|/collections$||' | sed 's|/v2/_catalog$||' | sed 's|/docs$||')
    echo "• $service: $base_url"
done

echo ""
echo "=========================================="
echo "🔍 Additional Notes"
echo "=========================================="
echo "• Ollama is currently running on compute node (100.72.98.106:11434)"
echo "  but the compute node is not accessible from service node"
echo "• Grafana, Open WebUI, and Flowise are not currently deployed"
echo "• Whisper service is experiencing pod restart issues"
echo "• All databases (PostgreSQL, Redis, Qdrant) are running internally"
echo ""
echo "To access services remotely via Tailscale:"
echo "• Homelab Dashboard: http://100.81.76.55:30800"
echo "• N8n: http://100.81.76.55:30678"
echo "• Prometheus: http://100.81.76.55:30090"
echo "• Loki API: http://100.81.76.55:30314"
echo "• Qdrant Dashboard: http://100.81.76.55:30633"

echo ""
echo "=========================================="

# Exit with status code based on success rate
if [ "$SUCCESS_RATE" -ge 80 ]; then
    exit 0
elif [ "$SUCCESS_RATE" -ge 60 ]; then
    exit 2
else
    exit 1
fi