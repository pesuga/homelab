#!/bin/bash
# Ollama benchmark script with real-time tokens/sec calculation
# Runs a test prompt and extracts performance metrics

set -e

MODEL="${1:-gpt-oss}"
PROMPT="${2:-Explain quantum computing in one paragraph.}"

echo "🧪 Benchmarking $MODEL..."
echo "📝 Prompt: $PROMPT"
echo ""

# Run Ollama and capture timing info
START_TIME=$(date +%s%3N)

RESPONSE=$(curl -s http://localhost:11434/api/generate -d "{
  \"model\": \"$MODEL\",
  \"prompt\": \"$PROMPT\",
  \"stream\": false
}" 2>&1)

END_TIME=$(date +%s%3N)
DURATION=$((END_TIME - START_TIME))

# Extract metrics from response
EVAL_COUNT=$(echo "$RESPONSE" | jq -r '.eval_count // 0')
EVAL_DURATION=$(echo "$RESPONSE" | jq -r '.eval_duration // 0')
PROMPT_EVAL_COUNT=$(echo "$RESPONSE" | jq -r '.prompt_eval_count // 0')
PROMPT_EVAL_DURATION=$(echo "$RESPONSE" | jq -r '.prompt_eval_duration // 0')

# Calculate tokens per second
if [ "$EVAL_DURATION" -gt 0 ]; then
    TOKENS_PER_SEC=$(echo "scale=2; $EVAL_COUNT / ($EVAL_DURATION / 1000000000)" | bc)
else
    TOKENS_PER_SEC="N/A"
fi

if [ "$PROMPT_EVAL_DURATION" -gt 0 ]; then
    PROMPT_TOKENS_PER_SEC=$(echo "scale=2; $PROMPT_EVAL_COUNT / ($PROMPT_EVAL_DURATION / 1000000000)" | bc)
else
    PROMPT_TOKENS_PER_SEC="N/A"
fi

TOTAL_DURATION=$(echo "scale=2; $DURATION / 1000" | bc)

# Display results
echo "📊 Performance Metrics:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔤 Output tokens generated: $EVAL_COUNT"
echo "⚡ Generation speed: ${TOKENS_PER_SEC} tokens/sec"
echo ""
echo "📥 Prompt tokens processed: $PROMPT_EVAL_COUNT"
echo "🚀 Prompt processing speed: ${PROMPT_TOKENS_PER_SEC} tokens/sec"
echo ""
echo "⏱️  Total time: ${TOTAL_DURATION}s"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Display response
echo "💬 Response:"
echo "$RESPONSE" | jq -r '.response'
