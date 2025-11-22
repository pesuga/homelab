#!/bin/bash
# Test script for Kimi-VL model via llama.cpp API
# Usage: ./test-kimi.sh [optional custom prompt]

set -e

LLAMACPP_URL="http://100.86.122.109:8081"
DEFAULT_PROMPT="Hello! Can you introduce yourself?"

# Use provided prompt or default
PROMPT="${1:-$DEFAULT_PROMPT}"

echo "========================================="
echo "Testing Kimi-VL Model"
echo "========================================="
echo "Endpoint: $LLAMACPP_URL"
echo "Prompt: $PROMPT"
echo "========================================="
echo ""

# Test 1: Health check
echo "1. Health Check:"
curl -s "$LLAMACPP_URL/health" | jq -r '.' 2>/dev/null || curl -s "$LLAMACPP_URL/health"
echo ""
echo ""

# Test 2: Model info
echo "2. Model Information:"
curl -s "$LLAMACPP_URL/v1/models" | jq -r '.' 2>/dev/null || curl -s "$LLAMACPP_URL/v1/models"
echo ""
echo ""

# Test 3: Simple chat completion
echo "3. Chat Completion Test:"
echo "Sending prompt: \"$PROMPT\""
echo ""

curl -s "$LLAMACPP_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"kimi-vl\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"$PROMPT\"}
    ],
    \"temperature\": 0.7,
    \"max_tokens\": 256,
    \"stream\": false
  }" | jq -r '.choices[0].message.content' 2>/dev/null || \
  curl -s "$LLAMACPP_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"kimi-vl\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"$PROMPT\"}
    ],
    \"temperature\": 0.7,
    \"max_tokens\": 256,
    \"stream\": false
  }"

echo ""
echo ""
echo "========================================="
echo "Test Complete!"
echo "========================================="
