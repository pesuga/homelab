#!/bin/bash

# Chat Session Log Analyzer for llama.cpp interactions
# Comprehensive tool for analyzing chat session logs with various filtering and reporting options

set -euo pipefail

# Default configuration
LOG_DIR="/var/log/family-assistant/chat-sessions"
DEFAULT_DATE=$(date +%Y-%m-%d)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Usage information
usage() {
    cat << 'EOF'
Chat Session Log Analyzer
===================

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --date, -d DATE           Analyze logs for specific date (YYYY-MM-DD) [default: today]
    --user, -u USER_ID       Filter by user ID
    --session, -s SESSION_ID  Filter by session ID
    --thread, -t THREAD_ID    Filter by thread ID
    --summary                Show daily summary statistics
    --tokens                 Show token economics analysis
    --performance            Show performance metrics
    --errors                 Show error analysis only
    --cost                   Show cost analysis
    --last-week              Analyze last 7 days
    --last-month             Analyze last 30 days
    --export-json FILE       Export results to JSON file
    --slow-requests          Show slow requests (>threshold ms)
    --threshold MS           Set slow request threshold [default: 3000]
    --system-prompts         Show system prompt analysis
    --hourly                 Show hourly activity breakdown
    --models                 Show model usage statistics
    --help, -h               Show this help message

EXAMPLES:
    # Daily summary
    $0 --date 2025-12-01 --summary

    # User-specific analysis for last week
    $0 --user "user123" --last-week --tokens --performance

    # Cost analysis for this month
    $0 --last-month --cost --export-json monthly-costs.json

    # Find slow requests
    $0 --date today --slow-requests --threshold 5000

    # System prompt analysis
    $0 --date 2025-12-01 --system-prompts

    # Error analysis
    $0 --last-week --errors

EOF
}

# Parse command line arguments
parse_args() {
    DATE="$DEFAULT_DATE"
    USER_ID=""
    SESSION_ID=""
    THREAD_ID=""
    SHOW_SUMMARY=false
    SHOW_TOKENS=false
    SHOW_PERFORMANCE=false
    SHOW_ERRORS=false
    SHOW_COST=false
    LAST_WEEK=false
    LAST_MONTH=false
    EXPORT_JSON=""
    SLOW_REQUESTS=false
    THRESHOLD=3000
    SHOW_SYSTEM_PROMPTS=false
    HOURLY=false
    SHOW_MODELS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --date|-d)
                DATE="$2"
                shift 2
                ;;
            --user|-u)
                USER_ID="$2"
                shift 2
                ;;
            --session|-s)
                SESSION_ID="$2"
                shift 2
                ;;
            --thread|-t)
                THREAD_ID="$2"
                shift 2
                ;;
            --summary)
                SHOW_SUMMARY=true
                shift
                ;;
            --tokens)
                SHOW_TOKENS=true
                shift
                ;;
            --performance)
                SHOW_PERFORMANCE=true
                shift
                ;;
            --errors)
                SHOW_ERRORS=true
                shift
                ;;
            --cost)
                SHOW_COST=true
                shift
                ;;
            --last-week)
                LAST_WEEK=true
                shift
                ;;
            --last-month)
                LAST_MONTH=true
                shift
                ;;
            --export-json)
                EXPORT_JSON="$2"
                shift 2
                ;;
            --slow-requests)
                SLOW_REQUESTS=true
                shift
                ;;
            --threshold)
                THRESHOLD="$2"
                shift 2
                ;;
            --system-prompts)
                SHOW_SYSTEM_PROMPTS=true
                shift
                ;;
            --hourly)
                HOURLY=true
                shift
                ;;
            --models)
                SHOW_MODELS=true
                shift
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            *)
                echo -e "${RED}Error: Unknown option $1${NC}" >&2
                usage
                exit 1
                ;;
        esac
    done

    # Handle date ranges
    if [[ "$LAST_WEEK" == true ]]; then
        START_DATE=$(date -d '7 days ago' +%Y-%m-%d)
        END_DATE="$DEFAULT_DATE"
        DATE_RANGE=true
    elif [[ "$LAST_MONTH" == true ]]; then
        START_DATE=$(date -d '30 days ago' +%Y-%m-%d)
        END_DATE="$DEFAULT_DATE"
        DATE_RANGE=true
    else
        START_DATE="$DATE"
        END_DATE="$DATE"
        DATE_RANGE=false
    fi
}

# Validate log directory
validate_log_dir() {
    if [[ ! -d "$LOG_DIR" ]]; then
        echo -e "${RED}Error: Log directory not found: $LOG_DIR${NC}" >&2
        echo -e "${YELLOW}Tip: Make sure the Family Assistant API is running and generating logs.${NC}" >&2
        exit 1
    fi
}

# Get list of log files to analyze
get_log_files() {
    local files=()

    if [[ "$DATE_RANGE" == true ]]; then
        # Get files for date range
        local current_date="$START_DATE"
        while [[ "$current_date" < "$END_DATE" || "$current_date" == "$END_DATE" ]]; do
            local date_dir="$LOG_DIR/$current_date"
            if [[ -d "$date_dir" ]]; then
                local log_file="$date_dir/chat-sessions-$current_date.ndjson"
                if [[ -f "$log_file" ]]; then
                    files+=("$log_file")
                fi

                # Check for compressed version
                local gz_file="$log_file.gz"
                if [[ -f "$gz_file" ]]; then
                    files+=("$gz_file")
                fi
            fi

            current_date=$(date -d "$current_date + 1 day" +%Y-%m-%d)
        done
    else
        # Get files for single date
        local date_dir="$LOG_DIR/$DATE"
        if [[ -d "$date_dir" ]]; then
            local log_file="$date_dir/chat-sessions-$DATE.ndjson"
            if [[ -f "$log_file" ]]; then
                files+=("$log_file")
            fi

            # Check for compressed version
            local gz_file="$log_file.gz"
            if [[ -f "$gz_file" ]]; then
                files+=("$gz_file")
            fi
        fi
    fi

    echo "${files[@]}"
}

# Read and process log entries
process_logs() {
    local log_files=($@)
    local entries=()

    for log_file in "${log_files[@]}"; do
        if [[ ! -f "$log_file" ]]; then
            echo -e "${YELLOW}Warning: Log file not found: $log_file${NC}" >&2
            continue
        fi

        echo -e "${BLUE}Processing: $log_file${NC}" >&2

        # Handle compressed files
        if [[ "$log_file" == *.gz ]]; then
            while IFS= read -r line; do
                if [[ -n "$line" ]]; then
                    entries+=("$line")
                fi
            done < <(gunzip -c "$log_file")
        else
            while IFS= read -r line; do
                if [[ -n "$line" ]]; then
                    entries+=("$line")
                fi
            done < "$log_file"
        fi
    done

    echo "${entries[@]}"
}

# Filter entries based on criteria
filter_entries() {
    local entries=($@)
    local filtered_entries=()

    for entry in "${entries[@]}"; do
        local include=true

        # Filter by user ID
        if [[ -n "$USER_ID" ]]; then
            if ! echo "$entry" | jq -e ".user_id == \"$USER_ID\"" >/dev/null 2>&1; then
                include=false
            fi
        fi

        # Filter by session ID
        if [[ -n "$SESSION_ID" && "$include" == true ]]; then
            if ! echo "$entry" | jq -e ".session_id == \"$SESSION_ID\"" >/dev/null 2>&1; then
                include=false
            fi
        fi

        # Filter by thread ID
        if [[ -n "$THREAD_ID" && "$include" == true ]]; then
            if ! echo "$entry" | jq -e ".thread_id == \"$THREAD_ID\"" >/dev/null 2>&1; then
                include=false
            fi
        fi

        # Filter errors if not showing errors
        if [[ "$SHOW_ERRORS" == false && "$include" == true ]]; then
            if echo "$entry" | jq -e '.response.error' >/dev/null 2>&1; then
                include=false
            fi
        fi

        if [[ "$include" == true ]]; then
            filtered_entries+=("$entry")
        fi
    done

    echo "${filtered_entries[@]}"
}

# Generate summary statistics
generate_summary() {
    local entries=($@)

    if [[ ${#entries[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No entries found for analysis.${NC}"
        return
    fi

    echo -e "${CYAN}=== Daily Summary ===${NC}"

    # Basic stats
    local total_sessions=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.session_id) | unique | length')
    local total_messages=$(printf '%s\n' "${entries[@]}" | jq -s 'length')
    local unique_users=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.user_id) | unique | length')

    echo -e "${GREEN}Total Sessions:${NC} $total_sessions"
    echo -e "${GREEN}Total Messages:${NC} $total_messages"
    echo -e "${GREEN}Unique Users:${NC} $unique_users"

    # Token statistics
    local total_tokens=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.token_economics.total_tokens) | add // 0')
    local total_prompt_tokens=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.token_economics.prompt_tokens) | add // 0')
    local total_completion_tokens=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.token_economics.completion_tokens) | add // 0')
    local total_cost=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.token_economics.estimated_cost_usd) | add // 0')

    echo -e "${GREEN}Total Tokens:${NC} $total_tokens"
    echo -e "${GREEN}  - Prompt Tokens:${NC} $total_prompt_tokens"
    echo -e "${GREEN}  - Completion Tokens:${NC} $total_completion_tokens"
    echo -e "${GREEN}Total Cost:${NC} \$$(printf '%.6f' "$total_cost")"

    # Performance statistics
    local avg_latency=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.performance.total_latency_ms) | add / length // 0')
    local max_latency=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.performance.total_latency_ms) | max // 0')

    echo -e "${GREEN}Average Latency:${NC} ${avg_latency}ms"
    echo -e "${GREEN}Max Latency:${NC} ${max_latency}ms"

    # Error statistics
    local error_count=$(printf '%s\n' "${entries[@]}" | jq -s 'map(select(.response.error)) | length')
    local error_rate=$(echo "scale=2; $error_count * 100 / $total_messages" | bc -l)

    echo -e "${GREEN}Errors:${NC} $error_count (${error_rate}%)"
}

# Generate token economics analysis
generate_token_analysis() {
    local entries=($@)

    if [[ ${#entries[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No entries found for token analysis.${NC}"
        return
    fi

    echo -e "${CYAN}=== Token Economics Analysis ===${NC}"

    # Overall statistics
    local total_tokens=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.token_economics.total_tokens) | add // 0')
    local total_cost=$(printf '%s\n' "${entries[@]}" | jq -s 'map(.token_economics.estimated_cost_usd) | add // 0')

    echo -e "${GREEN}Total Tokens Processed:${NC} $(printf '%.0f' "$total_tokens")"
    echo -e "${GREEN}Total Cost:${NC} \$$(printf '%.6f' "$total_cost")"

    # Per-model breakdown
    echo -e "\n${BLUE}Model Usage Breakdown:${NC}"
    printf '%s\n' "${entries[@]}" | jq -s '
        group_by(.token_economics.model_used) |
        map({
            model: .[0].token_economics.model_used,
            tokens: map(.token_economics.total_tokens) | add,
            cost: map(.token_economics.estimated_cost_usd) | add,
            requests: length
        }) |
        sort_by(.tokens) | reverse
    ' | while IFS= read -r line; do
        local model=$(echo "$line" | jq -r '.model')
        local tokens=$(echo "$line" | jq '.tokens')
        local cost=$(echo "$line" | jq '.cost')
        local requests=$(echo "$line" | jq '.requests')

        echo -e "  ${YELLOW}$model:${NC}"
        echo -e "    Tokens: $(printf '%.0f' "$tokens"), Cost: \$$(printf '%.6f' "$cost"), Requests: $requests"
    done

    # Top users by token usage
    echo -e "\n${BLUE}Top Users by Token Usage:${NC}"
    printf '%s\n' "${entries[@]}" | jq -s '
        group_by(.user_id) |
        map({
            user_id: .[0].user_id,
            tokens: map(.token_economics.total_tokens) | add,
            cost: map(.token_economics.estimated_cost_usd) | add,
            sessions: map(.session_id) | unique | length
        }) |
        sort_by(.tokens) | reverse | limit(5)
    ' | while IFS= read -r line; do
        local user_id=$(echo "$line" | jq -r '.user_id')
        local tokens=$(echo "$line" | jq '.tokens')
        local cost=$(echo "$line" | jq '.cost')
        local sessions=$(echo "$line" | jq '.sessions')

        echo -e "  ${YELLOW}$user_id:${NC}"
        echo -e "    Tokens: $(printf '%.0f' "$tokens"), Cost: \$$(printf '%.6f' "$cost"), Sessions: $sessions"
    done
}

# Generate performance analysis
generate_performance_analysis() {
    local entries=($@)

    if [[ ${#entries[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No entries found for performance analysis.${NC}"
        return
    fi

    echo -e "${CYAN}=== Performance Analysis ===${NC}"

    # Latency statistics
    local latencies=$(printf '%s\n' "${entries[@]}" | jq -r '.performance.total_latency_ms // empty')
    local avg_latency=$(echo "$latencies" | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}')
    local min_latency=$(echo "$latencies" | sort -n | head -1)
    local max_latency=$(echo "$latencies" | sort -n | tail -1)
    local p95_latency=$(echo "$latencies" | sort -n | awk '{all[NR]=$1} END {if(NR>0) print all[int(NR*0.95)]; else print 0}')

    echo -e "${GREEN}Latency Statistics (ms):${NC}"
    echo -e "  Average: ${avg_latency}"
    echo -e "  Min: ${min_latency}"
    echo -e "  Max: ${max_latency}"
    echo -e "  95th percentile: ${p95_latency}"

    # Slow requests
    if [[ "$SLOW_REQUESTS" == true ]]; then
        echo -e "\n${BLUE}Slow Requests (>${THRESHOLD}ms):${NC}"
        printf '%s\n' "${entries[@]}" | jq --arg threshold "$THRESHOLD" '
            select(.performance.total_latency_ms > ($threshold | tonumber)) |
            {
                session_id: .session_id,
                user_id: .user_id,
                latency_ms: .performance.total_latency_ms,
                model: .token_economics.model_used,
                timestamp: .timestamp
            }
        ' | while IFS= read -r line; do
            local session_id=$(echo "$line" | jq -r '.session_id')
            local user_id=$(echo "$line" | jq -r '.user_id')
            local latency=$(echo "$line" | jq '.latency_ms')
            local model=$(echo "$line" | jq -r '.model')
            local timestamp=$(echo "$line" | jq -r '.timestamp')

            echo -e "  ${YELLOW}Session: $session_id${NC} (${RED}${latency}ms${NC})"
            echo -e "    User: $user_id, Model: $model, Time: $timestamp"
        done
    fi

    # Performance breakdown by component
    echo -e "\n${BLUE}Performance Breakdown:${NC}"
    printf '%s\n' "${entries[@]}" | jq -s '
        map({
            http: .performance.http_request_ms // 0,
            generation: .performance.generation_ms // 0,
            prompt_assembly: .performance.prompt_assembly_ms // 0,
            total: .performance.total_latency_ms // 0
        }) |
        {
            avg_http: map(.http) | add / length,
            avg_generation: map(.generation) | add / length,
            avg_prompt_assembly: map(.prompt_assembly) | add / length,
            avg_total: map(.total) | add / length
        }
    ' | while IFS= read -r line; do
        local http_avg=$(echo "$line" | jq '.avg_http')
        local gen_avg=$(echo "$line" | jq '.avg_generation')
        local prompt_avg=$(echo "$line" | jq '.avg_prompt_assembly')
        local total_avg=$(echo "$line" | jq '.avg_total')

        echo -e "  HTTP Request: ${http_avg}ms"
        echo -e "  Generation: ${gen_avg}ms"
        echo -e "  Prompt Assembly: ${prompt_avg}ms"
        echo -e "  Total: ${total_avg}ms"
    done
}

# Export results to JSON
export_json() {
    local entries=($@)
    local output_file="$1"

    echo -e "${BLUE}Exporting results to $output_file...${NC}"

    # Create JSON export
    printf '%s\n' "${entries[@]}" | jq -s '.' > "$output_file"

    echo -e "${GREEN}Exported ${#entries[@]} entries to $output_file${NC}"
}

# Main execution
main() {
    parse_args "$@"
    validate_log_dir

    echo -e "${CYAN}Chat Session Log Analyzer${NC}"
    echo -e "${BLUE}Analyzing logs for: $START_DATE to $END_DATE${NC}"

    # Get log files
    local log_files=($(get_log_files))

    if [[ ${#log_files[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No log files found for the specified date range.${NC}"
        exit 0
    fi

    echo -e "${BLUE}Found ${#log_files[@]} log file(s)${NC}"

    # Process logs
    local entries=($(process_logs "${log_files[@]}"))

    if [[ ${#entries[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No log entries found.${NC}"
        exit 0
    fi

    echo -e "${BLUE}Processing ${#entries[@]} log entries...${NC}"

    # Apply filters
    local filtered_entries=($(filter_entries "${entries[@]}"))
    echo -e "${BLUE}Filtered to ${#filtered_entries[@]} relevant entries${NC}"

    # Generate reports based on options
    if [[ "$SHOW_SUMMARY" == true ]]; then
        generate_summary "${filtered_entries[@]}"
    fi

    if [[ "$SHOW_TOKENS" == true ]]; then
        generate_token_analysis "${filtered_entries[@]}"
    fi

    if [[ "$SHOW_PERFORMANCE" == true || "$SLOW_REQUESTS" == true ]]; then
        generate_performance_analysis "${filtered_entries[@]}"
    fi

    if [[ "$SHOW_ERRORS" == true ]]; then
        echo -e "${CYAN}=== Error Analysis ===${NC}"
        printf '%s\n' "${filtered_entries[@]}" | jq -s 'map(select(.response.error)) | length' | while read -r count; do
            echo -e "${RED}Total Errors: $count${NC}"
        done
    fi

    if [[ -n "$EXPORT_JSON" ]]; then
        export_json "${filtered_entries[@]}" "$EXPORT_JSON"
    fi

    echo -e "${GREEN}Analysis complete.${NC}"
}

# Check dependencies
check_dependencies() {
    local missing_deps=()

    if ! command -v jq >/dev/null 2>&1; then
        missing_deps+=("jq")
    fi

    if ! command -v bc >/dev/null 2>&1; then
        missing_deps+=("bc")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo -e "${RED}Error: Missing required dependencies: ${missing_deps[*]}${NC}" >&2
        echo -e "${YELLOW}Install with: sudo apt-get install ${missing_deps[*]}${NC}" >&2
        exit 1
    fi
}

# Run main function with all arguments
check_dependencies
main "$@"