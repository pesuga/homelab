#!/bin/bash
# Real-time monitoring script for compute node during LLM inference
# Shows GPU metrics, CPU usage, memory, and Ollama status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Header
clear
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Compute Node Performance Monitor${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Function to print section header
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main monitoring loop
while true; do
    clear
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  Compute Node Performance Monitor${NC}"
    echo -e "${CYAN}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${CYAN}========================================${NC}"

    # GPU Metrics (ROCm)
    print_header "GPU Metrics (AMD RX 7800 XT)"
    if command_exists rocm-smi; then
        rocm-smi --showuse --showmeminfo vram --showtemp | grep -v "^=" | head -20
    else
        echo -e "${RED}rocm-smi not found${NC}"
    fi

    # CPU Usage
    print_header "CPU Usage"
    top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "CPU Usage: " 100 - $1"%"}'
    echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"

    # Memory Usage
    print_header "Memory Usage"
    free -h | grep -E "Mem|Swap"

    # Top Processes by CPU
    print_header "Top 5 Processes by CPU"
    ps aux --sort=-%cpu | head -6 | awk '{printf "%-10s %5s %5s %s\n", $1, $3, $4, $11}'

    # Ollama Status
    print_header "Ollama Service"
    if systemctl is-active --quiet ollama; then
        echo -e "${GREEN}Status: Running${NC}"
        if command_exists ss; then
            echo "Listening: $(ss -tlnp 2>/dev/null | grep :11434 || echo 'Not found')"
        fi
        # Check active models
        if curl -s http://localhost:11434/api/ps 2>/dev/null | grep -q "models"; then
            echo -e "\n${YELLOW}Active Models:${NC}"
            curl -s http://localhost:11434/api/ps 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "No models loaded"
        fi
    else
        echo -e "${RED}Status: Not Running${NC}"
    fi

    # Ollama K8s Status
    print_header "Ollama K8s Service"
    if kubectl get pods -n ollama &>/dev/null; then
        echo -e "${GREEN}Status: Running${NC}"
        if command_exists ss; then
            echo "Listening: $(ss -tlnp 2>/dev/null | grep :8000 || echo 'Not found')"
        fi
        # Health check
        if curl -s http://localhost:8000/health 2>/dev/null | grep -q "healthy"; then
            echo -e "${GREEN}Health: OK${NC}"
        fi
    else
        echo -e "${YELLOW}Status: Not a systemd service or not running${NC}"
        if kubectl get pods -n ollama -l app=ollama 2>/dev/null | grep -q "Running"; then
            echo -e "${GREEN}Process: Running (background)${NC}"
        fi
    fi

    # Disk Usage
    print_header "Disk Usage"
    df -h / | tail -1 | awk '{printf "Root: %s used of %s (%s)\n", $3, $2, $5}'

    # Network Connections
    print_header "Active Connections to LLM Services"
    if command_exists ss; then
        echo "Ollama (11434):"
        ss -tn 2>/dev/null | grep :11434 | wc -l | awk '{print "  Active connections: " $1}'
        echo "Ollama K8s:"
        ss -tn 2>/dev/null | grep :8000 | wc -l | awk '{print "  Active connections: " $1}'
    fi

    echo -e "\n${YELLOW}Press Ctrl+C to exit. Refreshing every 5 seconds...${NC}"
    sleep 5
done
