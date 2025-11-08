#!/bin/bash
# Comprehensive service endpoint testing script
# Tests DNS, HTTP, HTTPS, and certificates for all homelab services

# Don't exit on error, we want to see all test results
# set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

# Configuration
SERVICE_NODE_IP="100.81.76.55"
COMPUTE_NODE_IP="100.72.98.106"
DOMAIN="homelab.pesulabs.net"

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Homelab Service Verification Test Suite${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# Function to test HTTP endpoint
test_http() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    printf "%-30s" "$name"

    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")

    if [ "$response" == "$expected_code" ] || [ "$response" == "302" ] || [ "$response" == "301" ]; then
        echo -e "${GREEN}✓${NC} HTTP $response"
        return 0
    else
        echo -e "${RED}✗${NC} HTTP $response (expected $expected_code)"
        return 1
    fi
}

# Function to test HTTPS endpoint with certificate validation
test_https() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    printf "%-30s" "$name"

    # Test HTTP status
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")

    # Get certificate info
    cert_info=$(echo | openssl s_client -servername "$(echo $url | sed -e 's|https://||' -e 's|/.*||')" -connect "$(echo $url | sed -e 's|https://||' -e 's|/.*||'):443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")

    if [ "$response" == "$expected_code" ] || [ "$response" == "302" ] || [ "$response" == "301" ]; then
        if [ ! -z "$cert_info" ]; then
            expiry=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
            echo -e "${GREEN}✓${NC} HTTPS $response | Cert expires: $expiry"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} HTTPS $response | Cert validation failed"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} HTTPS $response (expected $expected_code)"
        return 1
    fi
}

# Function to test DNS resolution
test_dns() {
    local hostname=$1

    printf "%-30s" "DNS: $hostname"

    ip=$(dig +short "$hostname" @8.8.8.8 | head -1)

    if [ ! -z "$ip" ]; then
        echo -e "${GREEN}✓${NC} Resolves to $ip"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to resolve"
        return 1
    fi
}

# Test DNS Resolution
echo -e "\n${BLUE}━━━ DNS Resolution Tests ━━━${NC}"
test_dns "n8n.$DOMAIN"
test_dns "grafana.$DOMAIN"
test_dns "prometheus.$DOMAIN"
test_dns "ollama.$DOMAIN"
test_dns "webui.$DOMAIN"
test_dns "lobechat.$DOMAIN"

# Test NodePort Services (HTTP)
echo -e "\n${BLUE}━━━ NodePort Services (HTTP) ━━━${NC}"
test_http "N8n NodePort" "http://$SERVICE_NODE_IP:30678"
test_http "Grafana NodePort" "http://$SERVICE_NODE_IP:30300" 200
test_http "Prometheus NodePort" "http://$SERVICE_NODE_IP:30090" 200
test_http "Open WebUI NodePort" "http://$SERVICE_NODE_IP:30080" 200
test_http "Whisper NodePort" "http://$SERVICE_NODE_IP:30900/health" 200
test_http "Qdrant NodePort" "http://$SERVICE_NODE_IP:30633" 200
test_http "Mem0 NodePort" "http://$SERVICE_NODE_IP:30820/health" 200

# Test HTTPS Services (Traefik Ingress)
echo -e "\n${BLUE}━━━ HTTPS Services (Let's Encrypt) ━━━${NC}"
test_https "N8n HTTPS" "https://n8n.$DOMAIN"
test_https "Grafana HTTPS" "https://grafana.$DOMAIN"
test_https "Prometheus HTTPS" "https://prometheus.$DOMAIN"
test_https "Open WebUI HTTPS" "https://webui.$DOMAIN"
test_https "Ollama HTTPS" "https://ollama.$DOMAIN"
test_https "LobeChat HTTPS" "https://lobechat.$DOMAIN"

# Test Ollama on Compute Node
echo -e "\n${BLUE}━━━ Ollama API (Compute Node) ━━━${NC}"
test_http "Ollama Local API" "http://$COMPUTE_NODE_IP:11434/api/version" 200

# Test Internal ClusterIP Services (from within cluster)
echo -e "\n${BLUE}━━━ Internal Cluster Services ━━━${NC}"
~/bin/kubectl run curl-test --image=curlimages/curl:latest --rm --restart=Never -n homelab -- curl -s -o /dev/null -w "%{http_code}" http://postgres.homelab.svc.cluster.local:5432 > /dev/null 2>&1 && echo -e "PostgreSQL Internal${GREEN}✓${NC}" || echo -e "PostgreSQL Internal${RED}✗${NC}"
~/bin/kubectl run curl-test --image=curlimages/curl:latest --rm --restart=Never -n homelab -- curl -s -o /dev/null -w "%{http_code}" http://redis.homelab.svc.cluster.local:6379 > /dev/null 2>&1 && echo -e "Redis Internal${GREEN}✓${NC}" || echo -e "Redis Internal${RED}✗${NC}"
~/bin/kubectl run curl-test --image=curlimages/curl:latest --rm --restart=Never -n homelab -- curl -s -o /dev/null -w "%{http_code}" http://qdrant.homelab.svc.cluster.local:6333 > /dev/null 2>&1 && echo -e "Qdrant Internal${GREEN}✓${NC}" || echo -e "Qdrant Internal${RED}✗${NC}"

# Certificate Expiry Check
echo -e "\n${BLUE}━━━ Certificate Expiry Details ━━━${NC}"
for service in n8n grafana prometheus webui ollama lobechat; do
    printf "%-20s" "$service.$DOMAIN:"
    expiry=$(echo | openssl s_client -servername "$service.$DOMAIN" -connect "$service.$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep "notAfter" | cut -d= -f2 || echo "N/A")
    if [ "$expiry" != "N/A" ]; then
        echo -e "${GREEN}$expiry${NC}"
    else
        echo -e "${RED}Certificate not found${NC}"
    fi
done

# Summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Test Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""
echo "For detailed logs, check:"
echo "  - CoreDNS: kubectl logs -n kube-system deployment/coredns"
echo "  - Traefik: kubectl logs -n kube-system deployment/traefik"
echo "  - Service logs: kubectl logs -n homelab deployment/<service-name>"
echo ""
