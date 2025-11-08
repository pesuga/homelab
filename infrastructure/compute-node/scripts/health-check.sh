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

# Check Ollama K8s Deployment
echo "Checking Ollama K8s..."
if kubectl get pods -n ollama &>/dev/null; then
    if kubectl get pods -n ollama -l app=ollama 2>/dev/null | grep -q "Running"; then
        echo "✓ Ollama K8s pod is running"
        if curl -s https://ollama.homelab.pesulabs.net/ > /dev/null 2>&1; then
            echo "✓ Ollama HTTPS endpoint is responding"
        else
            echo "⚠ Ollama HTTPS endpoint not accessible (may not be deployed yet)"
        exit 1
    fi
else
    echo "✗ LiteLLM process is not running"
    exit 1
fi

echo ""

# Test Ollama inference
echo "Testing Ollama inference..."
RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
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
