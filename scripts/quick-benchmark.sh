#!/bin/bash
# Quick Ollama benchmark - single test for fast feedback

MODEL="${1:-gpt-oss:20b}"
PROMPT="${2:-Explain quantum computing in simple terms.}"

echo "=== Quick Ollama Benchmark ==="
echo "Model: $MODEL"
echo "Testing..."

START=$(date +%s.%N)

RESPONSE=$(curl -s http://localhost:11434/api/generate \
    -d "{
        \"model\": \"$MODEL\",
        \"prompt\": $(echo "$PROMPT" | jq -Rs .),
        \"stream\": false
    }")

END=$(date +%s.%N)

# Extract metrics
TOTAL_NS=$(echo "$RESPONSE" | jq -r '.total_duration // 0')
LOAD_NS=$(echo "$RESPONSE" | jq -r '.load_duration // 0')
EVAL_COUNT=$(echo "$RESPONSE" | jq -r '.eval_count // 0')
EVAL_NS=$(echo "$RESPONSE" | jq -r '.eval_duration // 0')
PROMPT_COUNT=$(echo "$RESPONSE" | jq -r '.prompt_eval_count // 0')
PROMPT_NS=$(echo "$RESPONSE" | jq -r '.prompt_eval_duration // 0')

# Calculate
WALL_TIME=$(echo "scale=2; $END - $START" | bc)
TOTAL_SEC=$(echo "scale=2; $TOTAL_NS / 1000000000" | bc)
LOAD_SEC=$(echo "scale=2; $LOAD_NS / 1000000000" | bc)

# Tokens per second
if [ "$EVAL_NS" != "0" ] && [ "$EVAL_COUNT" != "0" ]; then
    TOK_PER_SEC=$(echo "scale=1; ($EVAL_COUNT * 1000000000) / $EVAL_NS" | bc)
else
    TOK_PER_SEC="N/A"
fi

if [ "$PROMPT_NS" != "0" ] && [ "$PROMPT_COUNT" != "0" ]; then
    PROMPT_TOK_SEC=$(echo "scale=1; ($PROMPT_COUNT * 1000000000) / $PROMPT_NS" | bc)
else
    PROMPT_TOK_SEC="N/A"
fi

# Results
echo ""
echo "=== Results ==="
echo "Wall clock time: ${WALL_TIME}s"
echo "Total duration: ${TOTAL_SEC}s"
echo "Model load: ${LOAD_SEC}s"
echo ""
echo "Prompt processing: $PROMPT_COUNT tokens at $PROMPT_TOK_SEC tok/s"
echo "Response generation: $EVAL_COUNT tokens at $TOK_PER_SEC tok/s"
echo ""
echo "=== Performance Rating ==="

if [ "$TOK_PER_SEC" != "N/A" ]; then
    if (( $(echo "$TOK_PER_SEC > 30" | bc -l) )); then
        echo "⚡ Excellent (>30 tok/s) - GPU acceleration working well"
    elif (( $(echo "$TOK_PER_SEC > 15" | bc -l) )); then
        echo "✓ Good (15-30 tok/s) - Decent performance"
    elif (( $(echo "$TOK_PER_SEC > 5" | bc -l) )); then
        echo "⚠ Fair (5-15 tok/s) - May be CPU only"
    else
        echo "❌ Poor (<5 tok/s) - Check GPU setup"
    fi
fi

# Check GPU usage
echo ""
echo "=== GPU Check ==="
if command -v rocm-smi &> /dev/null; then
    echo "GPU detected via rocm-smi:"
    rocm-smi --showuse | head -10
else
    echo "ROCm not installed - likely running on CPU only"
    echo "Install ROCm for GPU acceleration: https://rocm.docs.amd.com/"
fi
