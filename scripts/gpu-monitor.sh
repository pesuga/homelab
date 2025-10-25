#!/bin/bash
# Simple GPU monitoring script focused on AMD GPU metrics
# Ideal for watching during LLM inference

set -e

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}GPU Monitor - Press Ctrl+C to exit${NC}\n"

# Watch GPU metrics every 2 seconds
watch -n 2 -c '
    echo -e "\033[1;36m=== AMD RX 7800 XT Metrics ===\033[0m"
    echo ""

    # Full rocm-smi output
    rocm-smi

    echo ""
    echo -e "\033[1;33m=== GPU Processes ===\033[0m"
    rocm-smi --showpids

    echo ""
    echo -e "\033[1;33m=== Top GPU-using Processes ===\033[0m"
    ps aux | grep -E "ollama|python|llama" | grep -v grep | head -5
'
