#!/bin/bash
# LLM Services Health Check Script

set -e

echo "=== LLM Services Health Check ==="
echo "Date: $(date)"
echo ""

# Check llama.cpp
echo "Checking llama.cpp..."
if systemctl is-active --quiet llamacpp-kimi-vision; then
    echo "✓ llama.cpp Kimi-VL service is running"
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✓ llama.cpp API is responding"
        echo "  Endpoint: http://localhost:8080"
        echo "  Model: Kimi-VL-A3B-Thinking-2506 (vision-language)"
    else
        echo "✗ llama.cpp API is not responding"
        exit 1
    fi
else
    echo "✗ llama.cpp service is not running"
    exit 1
fi

echo ""

# Test llama.cpp inference
echo "Testing llama.cpp inference..."
RESPONSE=$(curl -s -X POST http://localhost:8080/completion \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Say OK", "n_predict": 5}')

if echo "$RESPONSE" | grep -q "content"; then
    echo "✓ Inference test passed"
else
    echo "✗ Inference test failed"
    echo "Response: $RESPONSE"
    exit 1
fi

echo ""
echo "=== All health checks passed! ==="
