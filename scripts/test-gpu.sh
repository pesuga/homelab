#!/bin/bash
set -e

echo "🔍 Testing llama.cpp GPU Support"
echo "================================"

MODEL_PATH="/home/pesu/models/mistral-7b-openorca.Q5_K_M.gguf"

test_gpu_layers() {
    local layers=$1
    local port=$((8090 + layers))

    echo ""
    echo "Testing with $layers GPU layers on port $port..."

    # Start server in background
    timeout 60s /home/pesu/llama.cpp/bin/llama-server \
        -m "$MODEL_PATH" \
        --host 127.0.0.1 \
        --port "$port" \
        -np 1 \
        --n-gpu-layers "$layers" \
        --ctx-size 1024 \
        --threads 4 \
        > /tmp/gpu_test_${layers}.log 2>&1 &

    local server_pid=$!

    # Wait for server to start
    echo "Waiting for server to start..."
    for i in {1..30}; do
        if curl -s "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
            echo "✅ Server started successfully with $layers GPU layers!"

            # Test a simple request
            echo "Testing inference..."
            curl -s -X POST "http://127.0.0.1:$port/v1/chat/completions" \
                -H "Content-Type: application/json" \
                -d '{"model": "llamacpp", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 5}' \
                > /tmp/gpu_response_${layers}.json 2>&1

            if grep -q '"choices"' /tmp/gpu_response_${layers}.json; then
                echo "✅ Inference working with $layers GPU layers!"
            else
                echo "❌ Inference failed with $layers GPU layers"
                cat /tmp/gpu_response_${layers}.json
            fi

            # Clean up
            kill $server_pid 2>/dev/null || true
            wait $server_pid 2>/dev/null || true
            return 0
        fi
        sleep 2
    done

    echo "❌ Server failed to start with $layers GPU layers"
    echo "Last 10 lines of log:"
    tail -10 /tmp/gpu_test_${layers}.log

    # Clean up
    kill $server_pid 2>/dev/null || true
    wait $server_pid 2>/dev/null || true
    return 1
}

# Test different GPU layer counts
echo "Testing GPU acceleration with AMD RX 7800 XT..."

for layers in 1 2 5 10 20; do
    if test_gpu_layers $layers; then
        echo ""
        echo "🎉 SUCCESS: $layers GPU layers work!"

        # Show performance info
        if [ -f "/tmp/gpu_response_${layers}.json" ]; then
            echo "Performance info:"
            grep -o '"prompt_ms":[^,]*' /tmp/gpu_response_${layers}.json | sed 's/"prompt_ms":/Prompt: /'
            grep -o '"predicted_ms":[^,]*' /tmp/gpu_response_${layers}.json | sed 's/"predicted_ms":/Prediction: /'
        fi
        break
    else
        echo "❌ FAILED: $layers GPU layers don't work"
    fi
done

echo ""
echo "🧹 Cleaning up test files..."
rm -f /tmp/gpu_test_*.log /tmp/gpu_response_*.json

echo ""
echo "✅ GPU testing complete!"