#!/bin/bash
# Benchmark script for testing LLM inference performance with monitoring
# Tests both Ollama and LiteLLM endpoints while monitoring GPU usage

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
LITELLM_URL="${LITELLM_URL:-http://localhost:8000}"
MODEL="${MODEL:-llama3.1:8b}"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  LLM Inference Benchmark Tool${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Ollama URL: ${OLLAMA_URL}"
echo -e "  LiteLLM URL: ${LITELLM_URL}"
echo -e "  Model: ${MODEL}"
echo ""

# Function to capture GPU metrics
capture_gpu_metrics() {
    local label=$1
    echo -e "\n${YELLOW}GPU Metrics (${label}):${NC}"
    rocm-smi --showuse --showmeminfo vram | grep -v "^=" | head -10
}

# Function to test Ollama endpoint
test_ollama() {
    echo -e "\n${CYAN}=== Testing Ollama Direct API ===${NC}"

    # Capture metrics before
    capture_gpu_metrics "Before Inference"

    # Run inference and time it
    echo -e "\n${BLUE}Prompt:${NC} \"Explain what Kubernetes is in 3 sentences.\""
    echo -e "\n${GREEN}Response:${NC}"

    START_TIME=$(date +%s.%N)

    curl -s -X POST "${OLLAMA_URL}/api/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"${MODEL}\",
            \"prompt\": \"Explain what Kubernetes is in 3 sentences.\",
            \"stream\": false
        }" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('response', 'No response'))
print(f\"\n{'-'*50}\")
print(f\"Eval count: {data.get('eval_count', 'N/A')} tokens\")
print(f\"Eval duration: {data.get('eval_duration', 0) / 1e9:.2f}s\")
if 'eval_count' in data and 'eval_duration' in data:
    tokens_per_sec = data['eval_count'] / (data['eval_duration'] / 1e9)
    print(f\"Tokens/second: {tokens_per_sec:.2f}\")
"

    END_TIME=$(date +%s.%N)
    DURATION=$(echo "$END_TIME - $START_TIME" | bc)
    echo -e "\nTotal time: ${DURATION}s"

    # Capture metrics after
    capture_gpu_metrics "After Inference"
}

# Function to test LiteLLM endpoint
test_litellm() {
    echo -e "\n${CYAN}=== Testing LiteLLM OpenAI-Compatible API ===${NC}"

    # Capture metrics before
    capture_gpu_metrics "Before Inference"

    # Run inference and time it
    echo -e "\n${BLUE}Prompt:${NC} \"Write a Python function to calculate fibonacci numbers.\""
    echo -e "\n${GREEN}Response:${NC}"

    START_TIME=$(date +%s.%N)

    curl -s -X POST "${LITELLM_URL}/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Write a Python function to calculate fibonacci numbers. Keep it concise."}
            ]
        }' | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    content = data['choices'][0]['message']['content']
    print(content)
    print(f\"\n{'-'*50}\")
    print(f\"Model: {data.get('model', 'N/A')}\")
    usage = data.get('usage', {})
    print(f\"Completion tokens: {usage.get('completion_tokens', 'N/A')}\")
    print(f\"Total tokens: {usage.get('total_tokens', 'N/A')}\")
except Exception as e:
    print(f\"Error parsing response: {e}\", file=sys.stderr)
    sys.exit(1)
"

    END_TIME=$(date +%s.%N)
    DURATION=$(echo "$END_TIME - $START_TIME" | bc)
    echo -e "\nTotal time: ${DURATION}s"

    # Capture metrics after
    capture_gpu_metrics "After Inference"
}

# Function to run continuous load test
continuous_load_test() {
    local duration=${1:-60}
    echo -e "\n${CYAN}=== Continuous Load Test (${duration}s) ===${NC}"
    echo -e "${YELLOW}Running continuous requests to stress test GPU...${NC}"

    local count=0
    local start_time=$(date +%s)
    local end_time=$((start_time + duration))

    while [ $(date +%s) -lt $end_time ]; do
        curl -s -X POST "${OLLAMA_URL}/api/generate" \
            -H "Content-Type: application/json" \
            -d "{
                \"model\": \"${MODEL}\",
                \"prompt\": \"Count from 1 to 10.\",
                \"stream\": false
            }" > /dev/null &

        count=$((count + 1))
        echo -ne "\rRequests sent: ${count}"
        sleep 1
    done

    wait
    echo -e "\n${GREEN}Completed ${count} requests${NC}"

    # Final GPU metrics
    capture_gpu_metrics "After Load Test"
}

# Main menu
echo -e "\n${CYAN}Select test mode:${NC}"
echo "1) Test Ollama endpoint"
echo "2) Test LiteLLM endpoint"
echo "3) Test both endpoints"
echo "4) Continuous load test (60s)"
echo "5) Exit"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        test_ollama
        ;;
    2)
        test_litellm
        ;;
    3)
        test_ollama
        test_litellm
        ;;
    4)
        echo ""
        read -p "Duration in seconds (default 60): " duration
        duration=${duration:-60}
        continuous_load_test $duration
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}Benchmark complete!${NC}"
