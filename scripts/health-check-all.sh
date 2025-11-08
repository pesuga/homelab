#!/bin/bash
# Comprehensive Homelab Health Check Script
# Tests all deployed services across both nodes

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configurations
SERVICE_NODE_IP="100.81.76.55"
COMPUTE_NODE_IP="100.72.98.106"

declare -A SERVICES=(
    # Service Node Services
    ["N8n"]="${SERVICE_NODE_IP}:30678:/healthz"
    ["Prometheus"]="${SERVICE_NODE_IP}:30090:/-/healthy"
    ["Loki"]="${SERVICE_NODE_IP}:30314:/ready"
    ["Qdrant"]="${SERVICE_NODE_IP}:30633:/collections"
    ["Docker Registry"]="${SERVICE_NODE_IP}:30500:/v2/"
    ["Homelab Dashboard"]="${SERVICE_NODE_IP}:30800:/"
    ["Mem0"]="${SERVICE_NODE_IP}:30880:/docs"
    ["LobeChat"]="${SERVICE_NODE_IP}:30910:/"

    # Compute Node Services
    ["Ollama"]="${COMPUTE_NODE_IP}:11434:/api/version"
)

# Function to print colored output
print_status() {
    local status=$1
    local service=$2
    local message=$3

    case $status in
        "OK")
            echo -e "${GREEN}✓${NC} ${service}: ${message}"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠${NC} ${service}: ${message}"
            ;;
        "FAIL")
            echo -e "${RED}✗${NC} ${service}: ${message}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ${NC} ${service}: ${message}"
            ;;
    esac
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local service=$1
    local url=$2
    local timeout=${3:-10}

    if curl -s --max-time "$timeout" --connect-timeout 5 "$url" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to get HTTP status code
get_http_status() {
    local url=$1
    local timeout=${2:-10}

    curl -s --max-time "$timeout" --connect-timeout 5 -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000"
}

echo "=========================================="
echo "🏥 Homelab Comprehensive Health Check"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Check if we can reach both nodes
echo "Network Connectivity Check:"
echo "----------------------------"

if ping -c 1 -W 5 "$SERVICE_NODE_IP" > /dev/null 2>&1; then
    print_status "OK" "Service Node ($SERVICE_NODE_IP)" "Accessible"
else
    print_status "FAIL" "Service Node ($SERVICE_NODE_IP)" "Not accessible"
    exit 1
fi

if ping -c 1 -W 5 "$COMPUTE_NODE_IP" > /dev/null 2>&1; then
    print_status "OK" "Compute Node ($COMPUTE_NODE_IP)" "Accessible"
else
    print_status "FAIL" "Compute Node ($COMPUTE_NODE_IP)" "Not accessible - Ollama will be unreachable"
fi

echo ""

# Check Kubernetes cluster access
echo "Kubernetes Cluster Status:"
echo "----------------------------"

if kubectl cluster-info > /dev/null 2>&1; then
    print_status "OK" "Kubernetes" "Cluster accessible"

    # Check node status
    NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
    READY_NODES=$(kubectl get nodes --no-headers | grep -c "Ready")
    print_status "INFO" "Nodes" "$READY_NODES/$NODE_COUNT ready"

    # Check homelab namespace pods
    TOTAL_PODS=$(kubectl get pods -n homelab --no-headers 2>/dev/null | wc -l)
    RUNNING_PODS=$(kubectl get pods -n homelab --no-headers 2>/dev/null | grep -c "Running")
    if [ "$TOTAL_PODS" -gt 0 ]; then
        print_status "INFO" "Homelab Pods" "$RUNNING_PODS/$TOTAL_PODS running"
    else
        print_status "WARN" "Homelab Pods" "No pods found"
    fi
else
    print_status "FAIL" "Kubernetes" "Cluster not accessible"
fi

echo ""
echo "Service Health Checks:"
echo "======================"

# Track overall statistics
TOTAL_SERVICES=${#SERVICES[@]}
HEALTHY_SERVICES=0
WARNING_SERVICES=0
FAILED_SERVICES=0

# Check each service
for service in "${!SERVICES[@]}"; do
    IFS=':' read -r ip port path <<< "${SERVICES[$service]}"
    url="http://${ip}${port}${path}"

    echo -n "Checking ${service}... "

    # Special handling for services with known behaviors
    case $service in
        "Homelab Dashboard")
            # Dashboard may rate-limit, so we're more lenient
            status_code=$(get_http_status "$url" 15)
            if [ "$status_code" = "429" ] || [ "$status_code" = "200" ]; then
                if [ "$status_code" = "429" ]; then
                    print_status "WARN" "$service" "Rate limited but responding (HTTP $status_code)"
                    ((WARNING_SERVICES++))
                else
                    print_status "OK" "$service" "Healthy (HTTP $status_code)"
                    ((HEALTHY_SERVICES++))
                fi
            else
                print_status "FAIL" "$service" "Not responding (HTTP $status_code)"
                ((FAILED_SERVICES++))
            fi
            ;;
        "Ollama")
            # Ollama may take longer to respond
            if check_http_endpoint "$service" "$url" 20; then
                # Try to get version info
                version=$(curl -s --max-time 10 "$url" 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
                print_status "OK" "$service" "Healthy (v${version})"
                ((HEALTHY_SERVICES++))
            else
                print_status "FAIL" "$service" "Not responding"
                ((FAILED_SERVICES++))
            fi
            ;;
        "LobeChat")
            # LobeChat redirects, handle redirects properly
            status_code=$(get_http_status "$url" 10)
            if [ "$status_code" = "307" ] || [ "$status_code" = "302" ] || [ "$status_code" = "200" ]; then
                print_status "OK" "$service" "Responding (redirects to login, HTTP $status_code)"
                ((HEALTHY_SERVICES++))
            else
                print_status "FAIL" "$service" "Not responding (HTTP $status_code)"
                ((FAILED_SERVICES++))
            fi
            ;;
        *)
            # Standard HTTP check for other services
            if check_http_endpoint "$service" "$url" 10; then
                status_code=$(get_http_status "$url" 5)
                if [ "$status_code" = "200" ]; then
                    print_status "OK" "$service" "Healthy (HTTP $status_code)"
                    ((HEALTHY_SERVICES++))
                elif [ "$status_code" != "000" ]; then
                    print_status "WARN" "$service" "Responding but not 200 (HTTP $status_code)"
                    ((WARNING_SERVICES++))
                else
                    print_status "FAIL" "$service" "Not responding"
                    ((FAILED_SERVICES++))
                fi
            else
                print_status "FAIL" "$service" "Not responding"
                ((FAILED_SERVICES++))
            fi
            ;;
    esac
done

echo ""
echo "=========================================="
echo "📊 Health Check Summary"
echo "=========================================="
echo -e "Total Services: ${BLUE}$TOTAL_SERVICES${NC}"
echo -e "Healthy: ${GREEN}$HEALTHY_SERVICES${NC}"
echo -e "Warnings: ${YELLOW}$WARNING_SERVICES${NC}"
echo -e "Failed: ${RED}$FAILED_SERVICES${NC}"

# Calculate health percentage
if [ "$TOTAL_SERVICES" -gt 0 ]; then
    HEALTH_PERCENT=$(( (HEALTHY_SERVICES + WARNING_SERVICES) * 100 / TOTAL_SERVICES ))
    echo ""
    echo -e "Overall Health: ${HEALTH_PERCENT}%"

    if [ "$HEALTH_PERCENT" -ge 80 ]; then
        echo -e "Status: ${GREEN}✓ Healthy${NC}"
    elif [ "$HEALTH_PERCENT" -ge 60 ]; then
        echo -e "Status: ${YELLOW}⚠ Degraded${NC}"
    else
        echo -e "Status: ${RED}✗ Critical${NC}"
    fi
fi

echo ""
echo "=========================================="
echo "🔗 Service URLs"
echo "=========================================="

echo "Service Node Services:"
for service in "${!SERVICES[@]}"; do
    IFS=':' read -r ip port path <<< "${SERVICES[$service]}"
    if [ "$ip" = "$SERVICE_NODE_IP" ]; then
        echo "• $service: http://$ip:$port$path"
    fi
done

echo ""
echo "Compute Node Services:"
for service in "${!SERVICES[@]}"; do
    IFS=':' read -r ip port path <<< "${SERVICES[$service]}"
    if [ "$ip" = "$COMPUTE_NODE_IP" ]; then
        echo "• $service: http://$ip:$port$path"
    fi
done

echo ""
echo "=========================================="

# Exit with appropriate code
if [ "$FAILED_SERVICES" -gt 0 ]; then
    exit 1
elif [ "$WARNING_SERVICES" -gt 0 ]; then
    exit 2
else
    exit 0
fi