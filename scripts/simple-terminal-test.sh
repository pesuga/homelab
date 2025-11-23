#!/bin/bash
set -e

echo "🧪 Simple Terminal Testing for Mistral"
echo "===================================="

# Function to test an endpoint
test_request() {
    local url=$1
    local data=$2
    local description=$3

    echo "Testing: $description"
    echo "URL: $url"

    response=$(curl -s -w "%{http_code}" -X POST "$url" \
      -H "Content-Type: application/json" \
      -d "$data" 2>/dev/null)

    http_code="${response: -3}"
    body="${response%???}"

    if [ "$http_code" = "200" ]; then
        echo "✅ SUCCESS"
        echo "Response: $body" | head -200
    else
        echo "❌ FAILED (HTTP $http_code)"
        echo "Response: $body"
    fi
    echo ""
}

# 1. Check what services are running
echo "1. Service Status"
echo "----------------"
echo "Active services:"
systemctl list-units --type=service --state=running | grep -E "(llamacpp|proxy)" || echo "No llama.cpp services running"
echo ""

echo "Ports in use:"
netstat -tlnp 2>/dev/null | grep -E ':(8080|8081|8082)' || echo "No services on ports 8080-8082"
echo ""

# 2. Test basic endpoints
echo "2. Basic Endpoint Tests"
echo "------------------------"

# Test proxy health
if curl -s http://localhost:8081/health >/dev/null 2>&1; then
    echo "✅ Proxy health: OK"
else
    echo "❌ Proxy health: FAILED"
fi

# Test models endpoint
test_request "http://localhost:8081/v1/models" "" "Models List"

# 3. Simple inference test
echo "3. Inference Test"
echo "----------------"
test_request "http://localhost:8081/v1/chat/completions" \
  '{"model": "mistral-7b-openorca", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 20}' \
  "Simple Chat Completion"

# 4. Concurrent test (simple)
echo "4. Concurrent Request Test"
echo "------------------------"
echo "Starting 2 concurrent requests..."

# Function to run request in background
run_request() {
    local prompt=$1
    local result_file=$2

    curl -s -X POST "http://localhost:8081/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"mistral-7b-openorca\", \"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}], \"max_tokens\": 30}" \
      2>/dev/null > "$result_file"
}

start_time=$(date +%s)

# Run two requests concurrently
run_request "What is 1+1?" "/tmp/test1.json" &
PID1=$!
run_request "What is 2+2?" "/tmp/test2.json" &
PID2=$!

# Wait for completion
wait $PID1
wait $PID2

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "✅ Concurrent test completed in ${duration}s"

if [ -f "/tmp/test1.json" ] && [ -f "/tmp/test2.json" ]; then
    echo "Request 1: $(cat /tmp/test1.json | grep -o '"content":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo 'Parse failed')"
    echo "Request 2: $(cat /tmp/test2.json | grep -o '"content":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo 'Parse failed')"
    rm -f /tmp/test1.json /tmp/test2.json
else
    echo "❌ Concurrent test failed - no responses"
fi

echo ""
echo "5. Manual Testing Commands"
echo "=========================="
echo "# Test proxy health:"
echo "curl http://localhost:8081/health"
echo ""
echo "# Test inference:"
echo "curl -X POST http://localhost:8081/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}'"
echo ""
echo "# Service status:"
echo "systemctl status llamacpp-proxy"
echo "systemctl status llamacpp-mistral"

echo ""
echo "🎉 Terminal Testing Complete!"