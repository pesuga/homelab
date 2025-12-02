#!/bin/bash
set -e

# llama.cpp Metrics Collector
# Real-time performance monitoring and logging

METRICS_ENDPOINT="http://localhost:8081/metrics"
LOG_DIR="/home/pesu/Rakuflow/systems/homelab/logs/metrics"
DB_FILE="$LOG_DIR/llamacpp_metrics.db"
CURRENT_MODEL_FILE="$LOG_DIR/current_model.txt"

# Create directories
mkdir -p "$LOG_DIR"
LOG_PROMPT_FILE="$LOG_DIR/prompt_performance.csv"

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

# Function to get current model from config
get_current_model() {
    local config="/home/pesu/Rakuflow/systems/homelab/config/llamacpp.conf"
    local model=$(grep -m1 "^MODEL_NAME=" "$config" | cut -d'=' -f2-)
    echo "${model:-unknown}"
}

# Function to collect metrics
collect_metrics() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local unix_timestamp=$(date '+%s')
    local current_model=$(get_current_model)

    # Get metrics from llama.cpp
    local metrics_response=$(curl -s "$METRICS_ENDPOINT" 2>/dev/null)

    if [ $? -ne 0 ]; then
        print_status $RED "❌ Failed to fetch metrics from $METRICS_ENDPOINT"
        return 1
    fi

    # Parse metrics (filter out comments and headers)
    local prompt_tokens=$(echo "$metrics_response" | grep "^llamacpp:prompt_tokens_total" | tail -1 | awk '{print $2}')
    local prompt_seconds=$(echo "$metrics_response" | grep "^llamacpp:prompt_seconds_total" | tail -1 | awk '{print $2}')
    local tokens_predicted=$(echo "$metrics_response" | grep "^llamacpp:tokens_predicted_total" | tail -1 | awk '{print $2}')
    local predicted_seconds=$(echo "$metrics_response" | grep "^llamacpp:tokens_predicted_seconds_total" | tail -1 | awk '{print $2}')
    local n_decode=$(echo "$metrics_response" | grep "^llamacpp:n_decode_total" | tail -1 | awk '{print $2}')
    local n_tokens_max=$(echo "$metrics_response" | grep "^llamacpp:n_tokens_max" | tail -1 | awk '{print $2}')
    local n_busy_slots=$(echo "$metrics_response" | grep "^llamacpp:n_busy_slots_per_decode" | tail -1 | awk '{print $2}')

    # Calculate rates
    local prompt_tokens_per_sec=0
    local prediction_tokens_per_sec=0

    if [ -n "$prompt_seconds" ] && [ "$prompt_seconds" != "0" ]; then
        prompt_tokens_per_sec=$(echo "scale=2; $prompt_tokens / $prompt_seconds" | bc -l 2>/dev/null || echo "0")
    fi

    if [ -n "$predicted_seconds" ] && [ "$predicted_seconds" != "0" ]; then
        prediction_tokens_per_sec=$(echo "scale=2; $tokens_predicted / $predicted_seconds" | bc -l 2>/dev/null || echo "0")
    fi

    # Get system metrics
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    local memory_usage=$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2 }')
    local gpu_memory="N/A"

    # Store in simple log file
    echo "$unix_timestamp,$timestamp,$current_model,$prompt_tokens,$tokens_predicted,$prompt_tokens_per_sec,$prediction_tokens_per_sec,$cpu_usage,$memory_usage" >> "$LOG_DIR/metrics.csv"

    # Store current model
    echo "$current_model" > "$CURRENT_MODEL_FILE"

    # Return parsed values for display
    cat << EOF
CURRENT_MODEL:$current_model
TIMESTAMP:$timestamp
PROMPT_TOKENS:$prompt_tokens
PREDICTED_TOKENS:$tokens_predicted
PROMPT_TPS:$prompt_tokens_per_sec
PREDICTION_TPS:$prediction_tokens_per_sec
CPU_USAGE:$cpu_usage
MEMORY_USAGE:$memory_usage
EOF
}

# Function to log prompt performance (privacy‑preserving)
log_prompt_performance() {
    local duration_ms=$1   # total time in ms
    local total_tokens=$2  # total tokens generated
    local tps=$3           # tokens per second
    local ts=$(date '+%Y-%m-%d %H:%M:%S')
    if [ ! -f "$LOG_PROMPT_FILE" ]; then
        echo "timestamp,duration_ms,total_tokens,tokens_per_sec" > "$LOG_PROMPT_FILE"
    fi
    echo "$ts,$duration_ms,$total_tokens,$tps" >> "$LOG_PROMPT_FILE"
}

# Function to display real-time metrics
display_metrics() {
    local metrics_data=$(collect_metrics)

    if [ $? -ne 0 ]; then
        return 1
    fi

    # Parse metrics
    local current_model=$(echo "$metrics_data" | grep "CURRENT_MODEL:" | cut -d':' -f2-)
    local timestamp=$(echo "$metrics_data" | grep "TIMESTAMP:" | cut -d':' -f2-)
    local prompt_tokens=$(echo "$metrics_data" | grep "PROMPT_TOKENS:" | cut -d':' -f2-)
    local predicted_tokens=$(echo "$metrics_data" | grep "PREDICTED_TOKENS:" | cut -d':' -f2-)
    local prompt_tps=$(echo "$metrics_data" | grep "PROMPT_TPS:" | cut -d':' -f2-)
    local prediction_tps=$(echo "$metrics_data" | grep "PREDICTION_TPS:" | cut -d':' -f2-)
    local cpu_usage=$(echo "$metrics_data" | grep "CPU_USAGE:" | cut -d':' -f2-)
    local memory_usage=$(echo "$metrics_data" | grep "MEMORY_USAGE:" | cut -d':' -f2-)

    # Clear screen and display
    clear
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║              llama.cpp REAL-TIME METRICS                     ║"
    echo "╠════════════════════════════════════════════════════════════════╣"
    printf "║ %-20s: %-40s ║\n" "Current Model" "$current_model"
    printf "║ %-20s: %-40s ║\n" "Last Updated" "$timestamp"
    echo "╠════════════════════════════════════════════════════════════════╣"
    printf "║ %-20s: %-40s ║\n" "Prompt Tokens" "$prompt_tokens"
    printf "║ %-20s: %-40s ║\n" "Predicted Tokens" "$predicted_tokens"
    printf "║ %-20s: %-40s ║\n" "Prompt Speed" "${prompt_tps} tokens/sec"
    printf "║ %-20s: %-40s ║\n" "Prediction Speed" "${prediction_tps} tokens/sec"
    echo "╠════════════════════════════════════════════════════════════════╣"
    printf "║ %-20s: %-40s ║\n" "CPU Usage" "${cpu_usage}%"
    printf "║ %-20s: %-40s ║\n" "Memory Usage" "${memory_usage}%"
    echo "╠════════════════════════════════════════════════════════════════╣"
    printf "║ %-67s ║\n" "Press Ctrl+C to exit monitoring"
    echo "╚════════════════════════════════════════════════════════════════╝"
}

# Function to start monitoring daemon
start_daemon() {
    local interval=${1:-10}  # Default 10 seconds

    print_status $BLUE "🚀 Starting llama.cpp metrics daemon..."
    print_status $BLUE "📊 Collecting metrics every $interval seconds"
    print_status $BLUE "📁 Logs stored in: $LOG_DIR"
    print_status $GREEN "✅ Metrics collector started in background"

    # Create CSV header if file doesn't exist
    if [ ! -f "$LOG_DIR/metrics.csv" ]; then
        echo "timestamp,datetime,model,prompt_tokens,predicted_tokens,prompt_tps,prediction_tps,cpu_usage,memory_usage" > "$LOG_DIR/metrics.csv"
    fi

    # Start collection loop
    while true; do
        collect_metrics > /dev/null
        sleep "$interval"
    done
}

# Function to show historic data
show_history() {
    local hours=${1:-24}

    print_status $BLUE "📈 Showing metrics history for last $hours hours"

    if [ ! -f "$LOG_DIR/metrics.csv" ]; then
        print_status $RED "❌ No metrics data found"
        return 1
    fi

    # Filter by time range
    local since_timestamp=$(($(date '+%s') - hours * 3600))

    echo ""
    echo "RECENT METRICS HISTORY:"
    echo "======================"

    tail -50 "$LOG_DIR/metrics.csv" | while IFS=',' read -r ts datetime model prompt_tokens predicted_tokens prompt_tps prediction_tps cpu memory; do
        if [ "$ts" -gt "$since_timestamp" ] || [ "$ts" = "timestamp" ]; then
            printf "%-20s | %-15s | Prompt: %-8s | Prediction: %-8s | CPU: %-5s%%\n" \
                "$datetime" "$model" "$prompt_tokens" "$predicted_tokens" "$cpu"
        fi
    done
}

# Function to export data for graphing
export_data() {
    local output_file="$LOG_DIR/metrics_export.json"

    print_status $BLUE "📤 Exporting metrics data to JSON..."

    if [ ! -f "$LOG_DIR/metrics.csv" ]; then
        print_status $RED "❌ No metrics data found"
        return 1
    fi

    # Convert CSV to JSON for easy graphing
    echo '{"metrics":[' > "$output_file"

    local first=true
    while IFS=',' read -r ts datetime model prompt_tokens predicted_tokens prompt_tps prediction_tps cpu memory; do
        if [ "$ts" = "timestamp" ]; then
            continue
        fi

        if [ "$first" = true ]; then
            first=false
        else
            echo ',' >> "$output_file"
        fi

        cat >> "$output_file" << EOF
{
    "timestamp": $ts,
    "datetime": "$datetime",
    "model": "$model",
    "prompt_tokens": $prompt_tokens,
    "predicted_tokens": $predicted_tokens,
    "prompt_tps": $prompt_tps,
    "prediction_tps": $prediction_tps,
    "cpu_usage": $cpu,
    "memory_usage": $memory
}
EOF
    done < "$LOG_DIR/metrics.csv"

    echo ']}' >> "$output_file"

    print_status $GREEN "✅ Data exported to: $output_file"
}

# Function to run performance benchmark
run_benchmark() {
    local model=${1:-"current"}
    local prompt=${2:-"Benchmark test: The quick brown fox jumps over the lazy dog."}
    local max_tokens=${3:-50}
    local iterations=${4:-5}

    print_status $BLUE "🏃 Running performance benchmark..."
    print_status $BLUE "📝 Prompt: $prompt"
    print_status $BLUE "🔢 Max tokens: $max_tokens"
    print_status $BLUE "🔄 Iterations: $iterations"

    local benchmark_results="$LOG_DIR/benchmark_$(date +%Y%m%d_%H%M%S).csv"
    echo "iteration,timestamp,prompt_ms,prediction_ms,total_tokens,tokens_per_sec" > "$benchmark_results"

    for i in $(seq 1 $iterations); do
        print_status $YELLOW "⚡ Running test $i/$iterations..."

        local start_time=$(date '+%s%3N')

        local response=$(curl -s -X POST "http://localhost:8081/v1/chat/completions" \
            -H "Content-Type: application/json" \
            -d "{\"model\": \"llamacpp\", \"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}], \"max_tokens\": $max_tokens}")

        local end_time=$(date '+%s%3N')
        local total_time=$((end_time - start_time))

        # Extract timing from response
        local prompt_ms=$(echo "$response" | grep -o '"prompt_ms":[^,]*' | cut -d':' -f2 | tr -d '{}"')
        local pred_ms=$(echo "$response" | grep -o '"predicted_ms":[^,]*' | cut -d':' -f2 | tr -d '{}"')
        local total_tokens=$(echo "$response" | grep -o '"total_tokens":[^,]*' | cut -d':' -f2 | tr -d '{}"')

        local tps=0
        if [ "$total_time" -gt 0 ]; then
            tps=$(echo "scale=2; $total_tokens * 1000 / $total_time" | bc -l)
        fi

        echo "$i,$(date '+%Y-%m-%d %H:%M:%S'),$prompt_ms,$pred_ms,$total_tokens,$tps" >> "$benchmark_results"
    # Log performance metrics (duration in ms, total tokens, tokens/sec)
    log_prompt_performance "$total_time" "$total_tokens" "$tps"

        sleep 2  # Brief pause between tests
    done

    print_status $GREEN "✅ Benchmark complete!"
    print_status $BLUE "📊 Results saved to: $benchmark_results"

    # Show summary
    echo ""
    echo "BENCHMARK SUMMARY:"
    echo "=================="
    echo "Average tokens/sec: $(awk -F',' 'NR>1{sum+=$6; count++} END{if(count>0) print sum/count; else print 0}' "$benchmark_results")"
    echo "Average prompt time: $(awk -F',' 'NR>1{sum+=$3; count++} END{if(count>0) printf "%.2f", sum/count; else print 0}' "$benchmark_results") ms"
    echo "Average prediction time: $(awk -F',' 'NR>1{sum+=$4; count++} END{if(count>0) printf "%.2f", sum/count; else print 0}' "$benchmark_results") ms"
}

# Main function
main() {
    case "${1:-help}" in
        "monitor")
            trap 'clear; print_status $GREEN "👋 Monitoring stopped"; exit 0' INT
            while true; do
                display_metrics
                sleep 5
            done
            ;;
        "daemon")
            start_daemon "${2:-10}"
            ;;
        "collect")
            collect_metrics
            ;;
        "history")
            show_history "${2:-24}"
            ;;
        "export")
            export_data
            ;;
        "benchmark")
            run_benchmark "${2:-current}" "${3:-Benchmark test: The quick brown fox jumps over the lazy dog.}" "${4:-50}" "${5:-5}"
            ;;
        "help"|*)
            echo "llama.cpp Metrics Collector"
            echo "=========================="
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  monitor              Show real-time metrics dashboard"
            echo "  daemon [interval]    Start background metrics collector (default: 10s)"
            echo "  collect              Collect metrics once"
            echo "  history [hours]      Show metrics history (default: 24h)"
            echo "  export               Export data to JSON for graphing"
            echo "  benchmark [model] [prompt] [tokens] [iterations]"
            echo "                       Run performance benchmark"
            echo "  help                 Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 monitor           # Real-time dashboard"
            echo "  $0 daemon 5          # Collect every 5 seconds"
            echo "  $0 history 12        # Show last 12 hours"
            echo "  $0 benchmark         # Run standard benchmark"
            exit 0
            ;;
    esac
}

main "$@"