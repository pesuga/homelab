#!/bin/bash
set -e

# Chat Performance Testing Script
# Tests the entire chain: Frontend → API → LLM

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_result() {
    local label=$1
    local value=$2
    printf "  %-30s: %s\n" "$label" "$value"
}

# Test 1: Direct LLM (baseline)
print_header "TEST 1: Direct LLM Performance (Baseline)"
echo -e "${YELLOW}Testing direct llama.cpp endpoint...${NC}"

PROMPT="Hello, how are you?"
START=$(date +%s%3N)

RESPONSE=$(curl -s -X POST "http://localhost:8081/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"llamacpp\", \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}], \"max_tokens\": 50}")

END=$(date +%s%3N)
DIRECT_TIME=$((END - START))

TOKENS=$(echo "$RESPONSE" | grep -o '"total_tokens":[^,]*' | cut -d':' -f2 | tr -d '{}\"')
TPS=$(echo "scale=2; $TOKENS * 1000 / $DIRECT_TIME" | bc -l)

print_result "Direct LLM Time" "${DIRECT_TIME}ms"
print_result "Tokens Generated" "$TOKENS"
print_result "Tokens/Second" "$TPS"

# Test 2: Family API (without auth)
print_header "TEST 2: Family API Performance (No Auth)"
echo -e "${YELLOW}Testing family-api endpoint...${NC}"

START=$(date +%s%3N)

API_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"llamacpp\", \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}], \"max_tokens\": 50}")

END=$(date +%s%3N)
API_TIME=$((END - START))

API_TOKENS=$(echo "$API_RESPONSE" | grep -o '"total_tokens":[^,]*' | cut -d':' -f2 | tr -d '{}\"')
API_TPS=$(echo "scale=2; $API_TOKENS * 1000 / $API_TIME" | bc -l)

print_result "API Time" "${API_TIME}ms"
print_result "Tokens Generated" "$API_TOKENS"
print_result "Tokens/Second" "$API_TPS"
print_result "Overhead vs Direct" "$((API_TIME - DIRECT_TIME))ms"

# Test 3: Check prompt size
print_header "TEST 3: Prompt Analysis"
echo -e "${YELLOW}Analyzing system prompt size...${NC}"

CORE_PROMPTS_DIR="/home/pesu/Rakuflow/systems/homelab/services/family-api/src/prompts/core"
TOTAL_SIZE=0

for file in "$CORE_PROMPTS_DIR"/*.md; do
    if [ -f "$file" ]; then
        SIZE=$(wc -c < "$file")
        TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
        print_result "$(basename $file)" "${SIZE} bytes"
    fi
done

print_result "Total Core Prompts" "${TOTAL_SIZE} bytes"

# Estimate token count (rough: 1 token ≈ 4 chars)
ESTIMATED_TOKENS=$((TOTAL_SIZE / 4))
print_result "Estimated Prompt Tokens" "~${ESTIMATED_TOKENS}"

# Test 4: Network latency to API
print_header "TEST 4: Network Latency"
echo -e "${YELLOW}Testing network latency...${NC}"

# Ping family-api health endpoint
START=$(date +%s%3N)
curl -s "http://localhost:8000/health" > /dev/null
END=$(date +%s%3N)
HEALTH_TIME=$((END - START))

print_result "Health Endpoint Latency" "${HEALTH_TIME}ms"

# Test 5: Check for database queries
print_header "TEST 5: Backend Processing Analysis"
echo -e "${YELLOW}Checking backend logs for slow operations...${NC}"

# Get recent family-api logs
kubectl logs -n homelab deployment/family-assistant-backend --tail=50 | grep -i "slow\|timeout\|error" || echo "  No slow operations detected in recent logs"

# Test 6: Streaming vs Non-streaming
print_header "TEST 6: Streaming Performance"
echo -e "${YELLOW}Testing streaming response...${NC}"

START=$(date +%s%3N)

curl -s -X POST "http://localhost:8081/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"llamacpp\", \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}], \"max_tokens\": 50, \"stream\": true}" \
    > /dev/null

END=$(date +%s%3N)
STREAM_TIME=$((END - START))

print_result "Streaming Time" "${STREAM_TIME}ms"
print_result "vs Non-streaming" "$((STREAM_TIME - DIRECT_TIME))ms difference"

# Summary
print_header "PERFORMANCE SUMMARY"

echo -e "${GREEN}Baseline (Direct LLM):${NC}     ${DIRECT_TIME}ms @ ${TPS} tok/s"
echo -e "${GREEN}Through API:${NC}               ${API_TIME}ms @ ${API_TPS} tok/s"
echo -e "${GREEN}API Overhead:${NC}              $((API_TIME - DIRECT_TIME))ms"
echo -e "${GREEN}Network Latency:${NC}           ${HEALTH_TIME}ms"
echo -e "${GREEN}System Prompt Size:${NC}        ${TOTAL_SIZE} bytes (~${ESTIMATED_TOKENS} tokens)"

# Recommendations
print_header "RECOMMENDATIONS"

if [ $((API_TIME - DIRECT_TIME)) -gt 500 ]; then
    echo -e "${RED}⚠️  High API overhead detected (>500ms)${NC}"
    echo "  Possible causes:"
    echo "  - Database queries (memory/user lookups)"
    echo "  - Large system prompts"
    echo "  - Authentication overhead"
    echo "  - Memory/embedding operations"
fi

if [ $ESTIMATED_TOKENS -gt 2000 ]; then
    echo -e "${YELLOW}⚠️  Large system prompt detected (>${ESTIMATED_TOKENS} tokens)${NC}"
    echo "  Consider further condensing core prompts"
fi

if [ $HEALTH_TIME -gt 100 ]; then
    echo -e "${YELLOW}⚠️  High network latency (>${HEALTH_TIME}ms)${NC}"
    echo "  Check network configuration and service health"
fi

echo -e "\n${GREEN}✅ Performance test complete!${NC}\n"
