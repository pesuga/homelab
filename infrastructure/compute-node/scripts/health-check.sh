#!/bin/bash
# LLM Services Health Check Script

set -e

echo "=== LLM Services Health Check ==="
echo "Date: $(date)"
echo ""

# Check Ollama
echo "Checking Ollama..."
if systemctl is-active --quiet ollama; then
    echo "✓ Ollama service is running"
    if curl -s http://localhost:11434/api/version > /dev/null; then
        echo "✓ Ollama API is responding"
        OLLAMA_VERSION=$(curl -s http://localhost:11434/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        echo "  Version: $OLLAMA_VERSION"
    else
        echo "✗ Ollama API is not responding"
        exit 1
    fi
else
    echo "✗ Ollama service is not running"
    exit 1
fi

echo ""

# Check LiteLLM
echo "Checking LiteLLM..."
if pgrep -f "litellm.*--config" > /dev/null; then
    echo "✓ LiteLLM process is running"
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✓ LiteLLM API is responding"
    else
        echo "✗ LiteLLM API is not responding"
        exit 1
    fi
else
    echo "✗ LiteLLM process is not running"
    exit 1
fi

echo ""

# Test inference
echo "Testing inference..."
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "llama3", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}')

if echo "$RESPONSE" | grep -q "assistant"; then
    echo "✓ Inference test passed"
else
    echo "✗ Inference test failed"
    echo "Response: $RESPONSE"
    exit 1
fi

echo ""
echo "=== All health checks passed! ==="
