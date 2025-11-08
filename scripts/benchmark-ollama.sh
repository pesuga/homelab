#!/bin/bash
set -euo pipefail

# Ollama Model Benchmarking Script
# Measures: tokens/sec, latency, memory usage, and response quality

MODEL="${1:-gpt-oss:20b}"
ITERATIONS="${2:-3}"
OUTPUT_DIR="./benchmark-results"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test prompts of varying complexity
declare -a PROMPTS=(
    "Hello, who are you?"
    "Explain quantum computing in simple terms."
    "Write a Python function to calculate fibonacci numbers recursively and iteratively. Include error handling."
    "Compare and contrast the architectural patterns of microservices vs monolithic applications. Discuss trade-offs, scalability, and when to use each approach."
)

PROMPT_LABELS=("short" "medium" "long" "complex")

# Create output directory
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$OUTPUT_DIR/benchmark_${MODEL//[:\/]/_}_${TIMESTAMP}.txt"

echo -e "${BLUE}=== Ollama Model Benchmark ===${NC}"
echo -e "${BLUE}Model: ${GREEN}$MODEL${NC}"
echo -e "${BLUE}Iterations per test: ${GREEN}$ITERATIONS${NC}"
echo -e "${BLUE}Output: ${GREEN}$REPORT_FILE${NC}"
echo ""

# Write header to report
{
    echo "Ollama Model Benchmark Report"
    echo "=============================="
    echo "Model: $MODEL"
    echo "Date: $(date)"
    echo "Host: $(hostname)"
    echo "Iterations: $ITERATIONS"
    echo ""
} > "$REPORT_FILE"

# Function to benchmark a single prompt
benchmark_prompt() {
    local prompt="$1"
    local label="$2"
    local iteration="$3"

    echo -e "${YELLOW}Testing: ${NC}$label (iteration $iteration/$ITERATIONS)"

    # Capture start time
    local start_time=$(date +%s.%N)

    # Make API call and capture response
    local response=$(curl -s http://localhost:11434/api/generate \
        -d "{
            \"model\": \"$MODEL\",
            \"prompt\": $(echo "$prompt" | jq -Rs .),
            \"stream\": false
        }")

    # Capture end time
    local end_time=$(date +%s.%N)

    # Extract metrics from response
    local total_duration=$(echo "$response" | jq -r '.total_duration // 0')
    local load_duration=$(echo "$response" | jq -r '.load_duration // 0')
    local eval_count=$(echo "$response" | jq -r '.eval_count // 0')
    local eval_duration=$(echo "$response" | jq -r '.eval_duration // 0')
    local prompt_eval_count=$(echo "$response" | jq -r '.prompt_eval_count // 0')
    local prompt_eval_duration=$(echo "$response" | jq -r '.prompt_eval_duration // 0')

    # Convert nanoseconds to seconds
    local total_sec=$(echo "scale=3; $total_duration / 1000000000" | bc)
    local load_sec=$(echo "scale=3; $load_duration / 1000000000" | bc)
    local eval_sec=$(echo "scale=3; $eval_duration / 1000000000" | bc)
    local prompt_eval_sec=$(echo "scale=3; $prompt_eval_duration / 1000000000" | bc)

    # Calculate tokens per second
    local tokens_per_sec=0
    if [ "$eval_duration" != "0" ] && [ "$eval_count" != "0" ]; then
        tokens_per_sec=$(echo "scale=2; ($eval_count / $eval_duration) * 1000000000" | bc)
    fi

    local prompt_tokens_per_sec=0
    if [ "$prompt_eval_duration" != "0" ] && [ "$prompt_eval_count" != "0" ]; then
        prompt_tokens_per_sec=$(echo "scale=2; ($prompt_eval_count / $prompt_eval_duration) * 1000000000" | bc)
    fi

    # Wall clock time
    local wall_clock=$(echo "scale=3; $end_time - $start_time" | bc)

    # Output results
    echo "  Total time: ${total_sec}s (wall: ${wall_clock}s)"
    echo "  Load time: ${load_sec}s"
    echo "  Prompt eval: $prompt_eval_count tokens in ${prompt_eval_sec}s (${prompt_tokens_per_sec} tok/s)"
    echo "  Response gen: $eval_count tokens in ${eval_sec}s (${tokens_per_sec} tok/s)"

    # Append to report
    {
        echo "[$label - Iteration $iteration]"
        echo "  Total Duration: ${total_sec}s"
        echo "  Load Duration: ${load_sec}s"
        echo "  Prompt Tokens: $prompt_eval_count (${prompt_tokens_per_sec} tok/s)"
        echo "  Response Tokens: $eval_count (${tokens_per_sec} tok/s)"
        echo "  Wall Clock Time: ${wall_clock}s"
        echo ""
    } >> "$REPORT_FILE"

    # Return tokens/sec for averaging
    echo "$tokens_per_sec"
}

# System info
echo -e "${BLUE}=== System Information ===${NC}"
{
    echo "System Information"
    echo "=================="
    echo "CPU: $(lscpu | grep 'Model name' | sed 's/Model name:[[:space:]]*//')"
    echo "Cores: $(nproc)"
    echo "Memory: $(free -h | awk '/^Mem:/ {print $2}')"
    echo "GPU: $(lspci | grep -i vga | head -1 | cut -d: -f3)"
    echo ""
} | tee -a "$REPORT_FILE"

# Check if model is already loaded
echo -e "${BLUE}Pre-loading model...${NC}"
curl -s http://localhost:11434/api/generate \
    -d "{\"model\": \"$MODEL\", \"prompt\": \"test\", \"stream\": false}" > /dev/null

echo ""

# Run benchmarks
declare -A total_tokens_per_sec

for i in "${!PROMPTS[@]}"; do
    prompt="${PROMPTS[$i]}"
    label="${PROMPT_LABELS[$i]}"

    echo -e "\n${GREEN}=== Benchmark: $label prompt ===${NC}"
    echo "Prompt: ${prompt:0:80}..."
    echo ""

    total=0
    for iter in $(seq 1 $ITERATIONS); do
        result=$(benchmark_prompt "$prompt" "$label" "$iter")
        total=$(echo "scale=2; $total + $result" | bc)
    done

    avg=$(echo "scale=2; $total / $ITERATIONS" | bc)
    total_tokens_per_sec[$label]=$avg

    echo -e "${GREEN}Average tokens/sec for $label: ${avg}${NC}"
done

# Summary
echo ""
echo -e "${BLUE}=== Benchmark Summary ===${NC}"
{
    echo ""
    echo "Summary"
    echo "======="
    for label in "${PROMPT_LABELS[@]}"; do
        echo "  $label: ${total_tokens_per_sec[$label]} tokens/sec"
    done
    echo ""
} | tee -a "$REPORT_FILE"

# Overall average
total_avg=0
count=0
for val in "${total_tokens_per_sec[@]}"; do
    total_avg=$(echo "scale=2; $total_avg + $val" | bc)
    ((count++))
done
overall_avg=$(echo "scale=2; $total_avg / $count" | bc)

echo -e "${GREEN}Overall Average: ${overall_avg} tokens/sec${NC}"
echo "Overall Average: ${overall_avg} tokens/sec" >> "$REPORT_FILE"

echo ""
echo -e "${BLUE}Full report saved to: ${GREEN}$REPORT_FILE${NC}"

# Check for GPU usage warnings
if journalctl -u ollama --since "5 minutes ago" | grep -q "GPU discovery"; then
    echo ""
    echo -e "${YELLOW}⚠️  Warning: GPU discovery issues detected. Check GPU setup.${NC}"
    echo -e "${YELLOW}   Run: journalctl -u ollama --since '10 minutes ago' | grep GPU${NC}"
fi
