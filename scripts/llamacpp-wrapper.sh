#!/bin/bash
set -e

# llama.cpp wrapper script for configurable model switching
# Reads configuration from /home/pesu/Rakuflow/systems/homelab/config/llamacpp.conf

CONFIG_FILE="/home/pesu/Rakuflow/systems/homelab/config/llamacpp.conf"
LLAMACPP_BIN="/home/pesu/llama.cpp/bin/llama-server"

# Function to read config values
read_config() {
    local key=$1
    local optional=${2:-false}
    local value=$(grep -m1 "^${key}=" "$CONFIG_FILE" | cut -d'=' -f2- | tr -d ' ')
    if [ -z "$value" ]; then
        if [ "$optional" = "true" ]; then
            echo ""
        else
            echo "❌ Error: ${key} not found in config file"
            exit 1
        fi
    else
        echo "$value"
    fi
}

# Function to check if value is commented out and uncomment
ensure_uncommented() {
    local key=$1
    sed -i "s/^#${key}=/${key}=/" "$CONFIG_FILE"
}

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

echo "🚀 Starting llama.cpp with configuration from $CONFIG_FILE"
echo "========================================================"

# Read configuration values
ensure_uncommented "MODEL_PATH"
ensure_uncommented "HOST"
ensure_uncommented "PORT"
ensure_uncommented "N_PARALLEL"
ensure_uncommented "CTX_SIZE"
ensure_uncommented "THREADS"

MODEL_PATH=$(read_config "MODEL_PATH")
MMPROJ_PATH=$(read_config "MMPROJ_PATH" "true")
MODEL_NAME=$(read_config "MODEL_NAME")
HOST=$(read_config "HOST")
PORT=$(read_config "PORT")
N_PARALLEL=$(read_config "N_PARALLEL")
CTX_SIZE=$(read_config "CTX_SIZE")
THREADS=$(read_config "THREADS")

# Handle optional GPU layers for different models
if grep -q "^GPU_LAYERS=" "$CONFIG_FILE"; then
    GPU_LAYERS=$(read_config "GPU_LAYERS")
    GPU_LAYERS_ARG="--n-gpu-layers $GPU_LAYERS"
else
    GPU_LAYERS_ARG=""
fi

# Handle optional batch size
if grep -q "^BATCH_SIZE=" "$CONFIG_FILE"; then
    BATCH_SIZE=$(read_config "BATCH_SIZE")
    BATCH_SIZE_ARG="--batch-size $BATCH_SIZE"
else
    BATCH_SIZE_ARG=""
fi

# Handle optional ubatch size
if grep -q "^U_BATCH_SIZE=" "$CONFIG_FILE"; then
    U_BATCH_SIZE=$(read_config "U_BATCH_SIZE")
    U_BATCH_SIZE_ARG="--ubatch-size $U_BATCH_SIZE"
else
    U_BATCH_SIZE_ARG=""
fi

# Handle metrics flag
if grep -q "^METRICS=" "$CONFIG_FILE"; then
    METRICS=$(read_config "METRICS")
    if [ "$METRICS" = "true" ]; then
        METRICS_ARG="--metrics"
    else
        METRICS_ARG=""
    fi
else
    METRICS_ARG=""
fi

# Handle log disable flag
if grep -q "^LOG_DISABLE=" "$CONFIG_FILE"; then
    LOG_DISABLE=$(read_config "LOG_DISABLE")
    if [ "$LOG_DISABLE" = "true" ]; then
        LOG_DISABLE_ARG="--log-disable"
    else
        LOG_DISABLE_ARG=""
    fi
else
    LOG_DISABLE_ARG=""
fi

# Handle environment variables
if grep -q "^ENVIRONMENT=" "$CONFIG_FILE"; then
    ENVIRONMENT=$(read_config "ENVIRONMENT")
    export $ENVIRONMENT
fi

echo "Configuration:"
echo "  Model: $MODEL_NAME"
echo "  Path: $MODEL_PATH"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Parallel Slots: $N_PARALLEL"
echo "  Context Size: $CTX_SIZE"
echo "  Threads: $THREADS"
if [ -n "$GPU_LAYERS_ARG" ]; then
    echo "  GPU Layers: $GPU_LAYERS"
fi
if [ -n "$MMPROJ_PATH" ] && [ "$MMPROJ_PATH" != "" ]; then
    echo "  Multimodal Projector: $MMPROJ_PATH"
fi
echo ""

# Build the command
CMD="$LLAMACPP_BIN -m $MODEL_PATH"

# Add multimodal projector if specified
if [ -n "$MMPROJ_PATH" ] && [ "$MMPROJ_PATH" != "" ]; then
    CMD="$CMD --mmproj $MMPROJ_PATH"
fi

# Add server arguments
CMD="$CMD --host $HOST --port $PORT -np $N_PARALLEL --ctx-size $CTX_SIZE --threads $THREADS"

# Add optional arguments
if [ -n "$GPU_LAYERS_ARG" ]; then
    CMD="$CMD $GPU_LAYERS_ARG"
fi
if [ -n "$BATCH_SIZE_ARG" ]; then
    CMD="$CMD $BATCH_SIZE_ARG"
fi
if [ -n "$U_BATCH_SIZE_ARG" ]; then
    CMD="$CMD $U_BATCH_SIZE_ARG"
fi
if [ -n "$METRICS_ARG" ]; then
    CMD="$CMD $METRICS_ARG"
fi
if [ -n "$LOG_DISABLE_ARG" ]; then
    CMD="$CMD $LOG_DISABLE_ARG"
fi

echo "Starting llama.cpp with command:"
echo "$CMD"
echo ""

# Execute the command
exec $CMD