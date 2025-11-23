#!/bin/bash
# Quick performance diagnostic for chat API

echo "=== Chat Performance Diagnostic ==="
echo ""

# Test 1: Direct LLM
echo "1. Testing Direct LLM (baseline)..."
time curl -s -X POST "http://localhost:8081/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model": "llamacpp", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 20}' \
    | jq -r '.usage.total_tokens, .choices[0].message.content' | head -2
echo ""

# Test 2: Family API health
echo "2. Testing Family API health..."
time curl -s "http://localhost:8000/health" | jq '.'
echo ""

# Test 3: Family API chat (simple)
echo "3. Testing Family API chat endpoint..."
time curl -s -X POST "http://localhost:8000/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model": "llamacpp", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 20}' \
    | jq -r '.usage.total_tokens, .choices[0].message.content' | head -2
echo ""

# Test 4: Check recent API logs for slow operations
echo "4. Checking API logs for slow operations..."
kubectl logs -n homelab deployment/family-assistant-backend --tail=20 | grep -E "INFO|ERROR|WARNING" | tail -10
echo ""

echo "=== Diagnostic Complete ==="
