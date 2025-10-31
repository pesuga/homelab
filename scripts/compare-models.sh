#!/bin/bash
# Compare performance across multiple Ollama models

PROMPT="${1:-Explain quantum computing in simple terms.}"

echo "=== Ollama Model Comparison ==="
echo "Prompt: $PROMPT"
echo ""

# Get list of installed models
MODELS=$(ollama list | tail -n +2 | awk '{print $1}')

if [ -z "$MODELS" ]; then
    echo "No models found. Run 'ollama pull <model>' first."
    exit 1
fi

echo "Testing models..."
echo ""

# Results table header
printf "%-30s | %10s | %10s | %15s\n" "Model" "Tokens" "Tok/Sec" "Time (s)"
printf "%-30s-+-%-10s-+-%-10s-+-%-15s\n" "------------------------------" "----------" "----------" "---------------"

for MODEL in $MODELS; do
    # Skip embedding models
    if [[ "$MODEL" == *"embed"* ]]; then
        continue
    fi

    # Run benchmark
    START=$(date +%s.%N)

    RESPONSE=$(curl -s http://localhost:11434/api/generate \
        -d "{
            \"model\": \"$MODEL\",
            \"prompt\": $(echo "$PROMPT" | jq -Rs .),
            \"stream\": false
        }")

    END=$(date +%s.%N)

    # Extract metrics
    EVAL_COUNT=$(echo "$RESPONSE" | jq -r '.eval_count // 0')
    EVAL_NS=$(echo "$RESPONSE" | jq -r '.eval_duration // 0')

    # Calculate
    WALL_TIME=$(echo "scale=2; $END - $START" | bc)

    if [ "$EVAL_NS" != "0" ] && [ "$EVAL_COUNT" != "0" ]; then
        TOK_PER_SEC=$(echo "scale=1; ($EVAL_COUNT * 1000000000) / $EVAL_NS" | bc)
    else
        TOK_PER_SEC="N/A"
    fi

    # Print results
    printf "%-30s | %10s | %10s | %15s\n" "$MODEL" "$EVAL_COUNT" "$TOK_PER_SEC" "$WALL_TIME"
done

echo ""
echo "=== GPU Status ==="
if command -v rocm-smi &> /dev/null; then
    rocm-smi --showuse | grep -A 1 "GPU is busy"
else
    echo "ROCm not installed"
fi
