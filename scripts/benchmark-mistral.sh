#!/bin/bash
set -e

# Benchmark script for Mistral-7B-OpenOrca with concurrent inference
# Tests 2 simultaneous requests to verify concurrent processing

ENDPOINT="http://10.43.11.93:8081/v1/chat/completions"
RESULTS_FILE="/tmp/mistral-benchmark-$(date +%Y%m%d-%H%M%S).json"

echo "=== Mistral-7B-OpenOrca Benchmark ==="
echo "Endpoint: $ENDPOINT"
echo "Results will be saved to: $RESULTS_FILE"
echo ""

# Test prompts
PROMPT1="Explain what machine learning is in simple terms."
PROMPT2="Write a short poem about artificial intelligence."

echo "Test 1: Single inference baseline"
echo "Prompt: $PROMPT1"
START=$(date +%s.%N)
RESPONSE1=$(curl -s "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"mistral\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT1\"}],
    \"max_tokens\": 100,
    \"temperature\": 0.7
  }")
END=$(date +%s.%N)
DURATION1=$(echo "$END - $START" | bc)
TOKENS1=$(echo "$RESPONSE1" | jq '.usage.completion_tokens')
echo "Duration: ${DURATION1}s"
echo "Tokens: $TOKENS1"
echo "Tokens/sec: $(echo "scale=2; $TOKENS1 / $DURATION1" | bc)"
echo ""

echo "Test 2: Concurrent inference (2 parallel requests)"
echo "Prompt 1: $PROMPT1"
echo "Prompt 2: $PROMPT2"
START=$(date +%s.%N)

# Run both requests in parallel
(curl -s "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"mistral\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT1\"}],
    \"max_tokens\": 100,
    \"temperature\": 0.7
  }" > /tmp/response1.json) &
PID1=$!

(curl -s "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"mistral\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT2\"}],
    \"max_tokens\": 100,
    \"temperature\": 0.7
  }" > /tmp/response2.json) &
PID2=$!

# Wait for both to complete
wait $PID1
wait $PID2

END=$(date +%s.%N)
DURATION2=$(echo "$END - $START" | bc)
TOKENS2_1=$(jq '.usage.completion_tokens' /tmp/response1.json)
TOKENS2_2=$(jq '.usage.completion_tokens' /tmp/response2.json)
TOTAL_TOKENS=$(echo "$TOKENS2_1 + $TOKENS2_2" | bc)

echo "Duration: ${DURATION2}s"
echo "Request 1 tokens: $TOKENS2_1"
echo "Request 2 tokens: $TOKENS2_2"
echo "Total tokens: $TOTAL_TOKENS"
echo "Combined throughput: $(echo "scale=2; $TOTAL_TOKENS / $DURATION2" | bc) tokens/sec"
echo ""

# Calculate efficiency
EFFICIENCY=$(echo "scale=2; ($DURATION1 * 2) / $DURATION2 * 100" | bc)
echo "Parallel efficiency: ${EFFICIENCY}%"
echo "(100% = perfect scaling, concurrent runs in same time as single)"
echo ""

# Save detailed results
cat > "$RESULTS_FILE" <<EOF
{
  "benchmark": "mistral-7b-openorca-concurrent",
  "timestamp": "$(date -Iseconds)",
  "endpoint": "$ENDPOINT",
  "tests": {
    "single_inference": {
      "duration_seconds": $DURATION1,
      "tokens": $TOKENS1,
      "tokens_per_second": $(echo "scale=2; $TOKENS1 / $DURATION1" | bc)
    },
    "concurrent_inference": {
      "duration_seconds": $DURATION2,
      "request1_tokens": $TOKENS2_1,
      "request2_tokens": $TOKENS2_2,
      "total_tokens": $TOTAL_TOKENS,
      "tokens_per_second": $(echo "scale=2; $TOTAL_TOKENS / $DURATION2" | bc),
      "parallel_efficiency_percent": $EFFICIENCY
    }
  }
}
EOF

echo "Results saved to: $RESULTS_FILE"
echo ""
echo "Sample responses:"
echo "=== Response 1 ==="
jq -r '.choices[0].message.content' /tmp/response1.json | head -100
echo ""
echo "=== Response 2 ==="
jq -r '.choices[0].message.content' /tmp/response2.json | head -100

# Cleanup
rm -f /tmp/response1.json /tmp/response2.json
