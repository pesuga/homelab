#!/bin/bash
# GPU monitoring script with tokens per second calculation
# Ideal for watching during LLM inference

set -e

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Temp files for tracking token generation
TOKEN_FILE="/tmp/ollama_tokens.txt"
TIMESTAMP_FILE="/tmp/ollama_timestamp.txt"

echo -e "${CYAN}GPU Monitor with Token Tracking - Press Ctrl+C to exit${NC}\n"

# Function to calculate tokens/sec from Ollama logs
calculate_tokens_per_sec() {
    # Check if ollama is running and generating
    if journalctl -u ollama -n 50 --no-pager 2>/dev/null | grep -q "eval rate"; then
        # Extract the most recent eval rate from logs
        RATE=$(journalctl -u ollama -n 100 --no-pager 2>/dev/null | \
               grep "eval rate" | tail -1 | \
               grep -oP '\d+\.\d+(?= tokens/s)')

        if [ ! -z "$RATE" ]; then
            echo -e "\033[1;32m📊 Token Generation Rate: ${RATE} tokens/s\033[0m"
        else
            echo -e "\033[0;33m⏸️  No active generation\033[0m"
        fi
    else
        echo -e "\033[0;33m⏸️  No active generation detected\033[0m"
    fi
}

# Watch GPU metrics every 2 seconds
watch -n 2 -c '
    echo -e "\033[1;36m=== AMD RX 7800 XT Metrics ===\033[0m"
    echo ""

    # Full rocm-smi output
    rocm-smi

    echo ""
    echo -e "\033[1;33m=== Token Generation Rate ===\033[0m"
    # Calculate and display tokens per second
    if journalctl -u ollama -n 50 --no-pager 2>/dev/null | grep -q "eval rate"; then
        RATE=$(journalctl -u ollama -n 100 --no-pager 2>/dev/null | \
               grep "eval rate" | tail -1 | \
               grep -oP "[\d.]+(?= tokens/s)")

        if [ ! -z "$RATE" ]; then
            echo -e "\033[1;32m📊 Current: ${RATE} tokens/s\033[0m"

            # Also show prompt processing rate if available
            PROMPT_RATE=$(journalctl -u ollama -n 100 --no-pager 2>/dev/null | \
                         grep "prompt eval rate" | tail -1 | \
                         grep -oP "[\d.]+(?= tokens/s)")
            if [ ! -z "$PROMPT_RATE" ]; then
                echo -e "\033[1;36m🔤 Prompt Processing: ${PROMPT_RATE} tokens/s\033[0m"
            fi
        else
            echo -e "\033[0;33m⏸️  No active generation\033[0m"
        fi
    else
        echo -e "\033[0;33m⏸️  Ollama idle or not running\033[0m"
    fi

    echo ""
    echo -e "\033[1;33m=== GPU Processes ===\033[0m"
    rocm-smi --showpids

    echo ""
    echo -e "\033[1;33m=== Top GPU-using Processes ===\033[0m"
    ps aux | grep -E "ollama|python|llama" | grep -v grep | head -5
'
