#!/bin/bash
set -e

echo "🚀 Mistral-7B-OpenOrca Terminal Testing"
echo "=================================="

# Function to check if service is active
check_service() {
    local service=$1
    if systemctl is-active $service >/dev/null 2>&1; then
        echo "✅ $service: ACTIVE"
        return 0
    else
        echo "❌ $service: INACTIVE"
        return 1
    fi
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local description=$2

    echo "Testing: $description"
    echo "URL: $url"

    local response=$(curl -s -w "%{http_code}" "$url" 2>/dev/null)
    local http_code="${response: -3}"
    local body="${response%???}"

    if [ "$http_code" = "200" ]; then
        echo "✅ SUCCESS ($http_code)"
        echo "Response: $body" | head -200
        return 0
    else
        echo "❌ FAILED ($http_code)"
        echo "Response: $body"
        return 1
    fi
    echo ""
}

# 1. Check services
echo "1. Service Status"
echo "----------------"
check_service "llamacpp-mistral-webui"
check_service "llamacpp-proxy"
echo ""

# 2. Check what's running on ports
echo "2. Port Status"
echo "-------------"
netstat -tlnp 2>/dev/null | grep -E ':(8080|8081|8082)' || echo "No processes found on ports 8080-8082"
echo ""

# 3. Test API endpoints
echo "3. API Endpoint Tests"
echo "--------------------"

# Test proxy health
test_endpoint "http://localhost:8081/health" "Proxy Health Check"
echo ""

# Test models endpoint
test_endpoint "http://localhost:8081/v1/models" "Models List"
echo ""

# 4. Test inference (simple)
echo "4. Inference Tests"
echo "-----------------"

echo "Testing basic inference..."
inference_response=$(curl -s -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b-openorca",
    "messages": [{"role": "user", "content": "Hello! Say hello back."}],
    "max_tokens": 30
  }' 2>/dev/null)

if [ $? -eq 0 ]; then
    content=$(echo "$inference_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'choices' in data and len(data['choices']) > 0:
        print(data['choices'][0]['message']['content'])
    else:
        print('No content in response')
except:
    print('Failed to parse JSON')
" 2>/dev/null)

    if [ -n "$content" ]; then
        echo "✅ Inference SUCCESS"
        echo "Response: $content"
    else
        echo "❌ Inference FAILED - Invalid response format"
        echo "Raw response: $inference_response"
    fi
else
    echo "❌ Inference FAILED - Request error"
fi
echo ""

# 5. Test concurrent inference
echo "5. Concurrent Inference Test"
echo "-----------------------------"

echo "Testing 2 simultaneous requests..."

# Function to run inference in background
run_inference() {
    local prompt=$1
    local file=$2
    curl -s -X POST http://localhost:8081/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d "{
        \"model\": \"mistral-7b-openorca\",
        \"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}],
        \"max_tokens\": 50
      }" 2>/dev/null > "$file"
}

# Start concurrent requests
start_time=$(date +%s.%N)
run_inference "What is 1+1?" "/tmp/concurrent1.json" &
PID1=$!
run_inference "What is 2+2?" "/tmp/concurrent2.json" &
PID2=$!

# Wait for both to complete
wait $PID1
wait $PID2
end_time=$(date +%s.%N)

# Calculate duration
duration=$(echo "$end_time - $start_time" | bc -l)

echo "✅ Concurrent test completed in ${duration}s"

# Process results
if [ -f "/tmp/concurrent1.json" ] && [ -f "/tmp/concurrent2.json" ]; then
    response1=$(python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['choices'][0]['message']['content'])
except:
    print('Failed to parse')
" < "/tmp/concurrent1.json" 2>/dev/null)

    response2=$(python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['choices'][0]['message']['content'])
except:
    print('Failed to parse')
" < "/tmp/concurrent2.json" 2>/dev/null)

    echo "Request 1: $response1"
    echo "Request 2: $response2"

    rm -f "/tmp/concurrent1.json" "/tmp/concurrent2.json"
else
    echo "❌ Concurrent test failed - responses missing"
fi

echo ""
echo "6. GPU Status Check"
echo "-------------------"
if journalctl -u llamacpp-mistral-webui --since "5 min ago" 2>/dev/null | grep -q "Vulkan\|GPU"; then
    echo "✅ GPU acceleration detected (Vulkan)"
else
    echo "⚠️  GPU status uncertain - may be CPU fallback"
fi

echo ""
echo "🎉 Terminal Testing Complete!"
echo "=================================="

# 7. Quick commands for manual testing
echo ""
echo "Quick commands for manual testing:"
echo "curl http://localhost:8081/health"
echo "curl -X POST http://localhost:8081/v1/chat/completions -H 'Content-Type: application/json' -d '{\"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}'"