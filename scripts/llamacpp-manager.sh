#!/bin/bash
set -e

# llama.cpp Model Manager
# Easily switch between different models and restart the service

CONFIG_FILE="/home/pesu/Rakuflow/systems/homelab/config/llamacpp.conf"
SERVICE_NAME="llamacpp-configurable"

# Available models configurations
declare -A MODELS=(
    ["kimi-vl"]="Kimi-VL-A3B-Thinking-2506-Q4_K_M.gguf|mmproj-Kimi-VL-A3B-Thinking-2506-Q8_0.gguf|Kimi-VL|1|8192"
    ["mistral-7b"]="mistral-7b-openorca.Q5_K_M.gguf||Mistral-7B-OpenOrca|1|16384"
    ["mixtral-8x7b"]="mixtral-8x7b-v0.1.Q4_K_M.gguf||Mixtral-8x7B|28|32768"
    ["llama-3.1-8b"]="llama-3.1-8b-instruct.Q4_K_M.gguf||Llama-3.1-8B-Instruct|28|32768"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to backup current config
backup_config() {
    if [ -f "$CONFIG_FILE" ]; then
        cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d-%H%M%S)"
        print_status $YELLOW "📁 Backed up current config"
    fi
}

# Function to comment out all MODEL_PATH lines except the selected one
configure_model() {
    local model_key=$1
    local config="${MODELS[$model_key]}"

    IFS='|' read -r model_file mmproj_file model_name gpu_layers ctx_size <<< "$config"

    print_status $BLUE "🔧 Configuring model: $model_key"
    print_status $BLUE "   Model: $model_name"
    print_status $BLUE "   File: $model_file"
    print_status $BLUE "   GPU Layers: $gpu_layers"
    print_status $BLUE "   Context: $ctx_size"

    # Backup current config
    backup_config

    # Comment out all existing MODEL_PATH lines
    sed -i 's/^MODEL_PATH=/#MODEL_PATH=/' "$CONFIG_FILE"

    # Set the selected model
    sed -i "s|^#MODEL_PATH=${model_file}$|MODEL_PATH=${model_file}|" "$CONFIG_FILE"

    # Handle multimodal projector
    if [ -n "$mmproj_file" ] && [ "$mmproj_file" != "" ]; then
        sed -i "s|^#MMPROJ_PATH=/home/pesu/models/llamacpp/${mmproj_file}$|MMPROJ_PATH=/home/pesu/models/llamacpp/${mmproj_file}|" "$CONFIG_FILE"
        # Comment out other MMPROJ_PATH lines
        sed -i 's/^MMPROJ_PATH=/#MMPROJ_PATH=/' "$CONFIG_FILE"
        sed -i "s|^#MMPROJ_PATH=/home/pesu/models/llamacpp/${mmproj_file}$|MMPROJ_PATH=/home/pesu/models/llamacpp/${mmproj_file}|" "$CONFIG_FILE"
    else
        # Comment out all MMPROJ_PATH lines for text-only models
        sed -i 's/^MMPROJ_PATH=/#MMPROJ_PATH=/' "$CONFIG_FILE"
    fi

    # Update model name
    sed -i "s/^MODEL_NAME=.*/MODEL_NAME=${model_name}/" "$CONFIG_FILE"

    # Update GPU layers
    sed -i "s/^GPU_LAYERS=.*/GPU_LAYERS=${gpu_layers}/" "$CONFIG_FILE"

    # Update context size
    sed -i "s/^CTX_SIZE=.*/CTX_SIZE=${ctx_size}/" "$CONFIG_FILE"

    # Adjust parallel slots based on model
    if [ "$model_key" = "mixtral-8x7b" ] || [ "$model_key" = "llama-3.1-8b" ]; then
        sed -i "s/^N_PARALLEL=.*/N_PARALLEL=2/" "$CONFIG_FILE"
    else
        sed -i "s/^N_PARALLEL=.*/N_PARALLEL=4/" "$CONFIG_FILE"
    fi

    print_status $GREEN "✅ Model configuration updated"
}

# Function to restart the service
restart_service() {
    print_status $BLUE "🔄 Restarting llama.cpp service..."

    # Stop existing services
    sudo systemctl stop llamacpp llamacpp-simple llamacpp-mistral 2>/dev/null || true

    # Reload systemd
    sudo systemctl daemon-reload

    # Enable and start the configurable service
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl restart $SERVICE_NAME

    # Wait for service to start
    sleep 5

    # Check if service is running
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_status $GREEN "✅ Service started successfully"
    else
        print_status $RED "❌ Failed to start service"
        print_status $RED "Check logs with: journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
}

# Function to show current status
show_status() {
    print_status $BLUE "📊 Current Status:"
    echo "=================="

    if [ -f "$CONFIG_FILE" ]; then
        local current_model=$(grep "^MODEL_PATH=" "$CONFIG_FILE" | cut -d'=' -f2- | sed 's/.*\///')
        local current_name=$(grep "^MODEL_NAME=" "$CONFIG_FILE" | cut -d'=' -f2-)
        print_status $GREEN "Active Model: $current_name ($current_model)"

        if grep -q "^MMPROJ_PATH=" "$CONFIG_FILE"; then
            local mmproj=$(grep "^MMPROJ_PATH=" "$CONFIG_FILE" | cut -d'=' -f2- | sed 's/.*\///')
            print_status $GREEN "Multimodal: Yes ($mmproj)"
        else
            print_status $YELLOW "Multimodal: No (text-only)"
        fi

        local gpu_layers=$(grep "^GPU_LAYERS=" "$CONFIG_FILE" | cut -d'=' -f2-)
        local ctx_size=$(grep "^CTX_SIZE=" "$CONFIG_FILE" | cut -d'=' -f2-)
        print_status $GREEN "GPU Layers: $gpu_layers"
        print_status $GREEN "Context Size: $ctx_size"
    fi

    echo ""
    print_status $BLUE "Service Status:"
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_status $GREEN "✅ $SERVICE_NAME: ACTIVE"
    else
        print_status $RED "❌ $SERVICE_name: INACTIVE"
    fi

    echo ""
    print_status $BLUE "Available Models:"
    for model_key in "${!MODELS[@]}"; do
        local config="${MODELS[$model_key]}"
        IFS='|' read -r model_file mmproj_file model_name gpu_layers ctx_size <<< "$config"
        echo "  - $model_key: $model_name"
    done
}

# Function to test the service
test_service() {
    print_status $BLUE "🧪 Testing service..."

    # Wait a moment for service to be fully ready
    sleep 2

    local port=$(grep "^PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

    if curl -s "http://localhost:$port/health" >/dev/null 2>&1; then
        print_status $GREEN "✅ Health endpoint responding"
    else
        print_status $YELLOW "⚠️  Health endpoint not responding (may be starting up)"
    fi

    # Test models endpoint
    if curl -s "http://localhost:$port/v1/models" >/dev/null 2>&1; then
        print_status $GREEN "✅ Models endpoint responding"
    else
        print_status $YELLOW "⚠️  Models endpoint not responding"
    fi

    # Test simple completion
    local response=$(curl -s -X POST "http://localhost:$port/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{"model": "llamacpp", "messages": [{"role": "user", "content": "Hello!"}], "max_tokens": 10}' 2>/dev/null)

    if echo "$response" | grep -q '"choices"'; then
        print_status $GREEN "✅ Chat completion working"
        local reply=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['content'])" 2>/dev/null || echo "N/A")
        print_status $GREEN "   Test response: $reply"
    else
        print_status $YELLOW "⚠️  Chat completion test failed"
    fi
}

# Main function
main() {
    case "${1:-help}" in
        "switch")
            if [ -z "$2" ]; then
                print_status $RED "❌ Please specify a model to switch to"
                echo "Available models: ${!MODELS[@]}"
                exit 1
            fi
            if [ -z "${MODELS[$2]}" ]; then
                print_status $RED "❌ Unknown model: $2"
                echo "Available models: ${!MODELS[@]}"
                exit 1
            fi
            configure_model "$2"
            restart_service
            test_service
            ;;
        "status")
            show_status
            ;;
        "restart")
            restart_service
            test_service
            ;;
        "test")
            test_service
            ;;
        "help"|*)
            echo "llama.cpp Model Manager"
            echo "======================"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  switch <model>    Switch to specified model and restart service"
            echo "  status           Show current configuration and status"
            echo "  restart          Restart the service with current configuration"
            echo "  test             Test the current service"
            echo "  help             Show this help"
            echo ""
            echo "Available models:"
            for model_key in "${!MODELS[@]}"; do
                local config="${MODELS[$model_key]}"
                IFS='|' read -r model_file mmproj_file model_name gpu_layers ctx_size <<< "$config"
                echo "  - $model_key: $model_name"
            done
            echo ""
            echo "Examples:"
            echo "  $0 switch kimi-vl       # Switch to Kimi-VL multimodal model"
            echo "  $0 switch mistral-7b    # Switch to Mistral-7B text model"
            echo "  $0 status               # Show current status"
            exit 0
            ;;
    esac
}

main "$@"