#!/bin/bash

# Prompt Source Analyzer - Complete System Prompt Tracking and Analysis
# Traces exactly what system prompts are injected and their sources

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
Prompt Source Analyzer - Complete System Prompt Tracing
======================================================

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --date, -d DATE           Analyze prompts for specific date (YYYY-MM-DD) [default: today]
    --session, -s SESSION_ID  Filter by session ID
    --user, -u USER_ID       Filter by user ID
    --trace                  Show complete prompt assembly trace
    --sources                Show detailed source breakdown
    --memory                 Show memory system contributions
    --tokens                 Show token analysis by source
    --roles                  Show role-based prompt analysis
    --skills                 Show skill-based prompt analysis
    --export-json FILE       Export results to JSON file
    --compare-users USER1 USER2  Compare prompt patterns between users
    --timeline               Show prompt assembly timeline
    --help, -h               Show this help message

EXAMPLES:
    # Complete prompt trace for today
    $0 --date today --trace --sources --memory

    # User-specific prompt analysis
    $0 --user "user123" --trace --tokens --roles

    # Compare prompt patterns between users
    $0 --compare-users "user123" "user456" --trace --sources

    # Memory system analysis
    $0 --date 2025-12-01 --memory --tokens

    # Export detailed analysis
    $0 --date today --trace --export-json prompt-analysis-$(date +%Y-%m-%d).json

EOF
}

# Parse command line arguments
parse_args() {
    DATE="$DEFAULT_DATE"
    SESSION_ID=""
    USER_ID=""
    SHOW_TRACE=false
    SHOW_SOURCES=false
    SHOW_MEMORY=false
    SHOW_TOKENS=false
    SHOW_ROLES=false
    SHOW_SKILLS=false
    EXPORT_JSON=""
    COMPARE_USERS=""
    SHOW_TIMELINE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --date|-d)
                DATE="$2"
                shift 2
                ;;
            --session|-s)
                SESSION_ID="$2"
                shift 2
                ;;
            --user|-u)
                USER_ID="$2"
                shift 2
                ;;
            --trace)
                SHOW_TRACE=true
                shift
                ;;
            --sources)
                SHOW_SOURCES=true
                shift
                ;;
            --memory)
                SHOW_MEMORY=true
                shift
                ;;
            --tokens)
                SHOW_TOKENS=true
                shift
                ;;
            --roles)
                SHOW_ROLES=true
                shift
                ;;
            --skills)
                SHOW_SKILLS=true
                shift
                ;;
            --export-json)
                EXPORT_JSON="$2"
                shift 2
                ;;
            --compare-users)
                COMPARE_USERS="$2 $3"
                shift 3
                ;;
            --timeline)
                SHOW_TIMELINE=true
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
}

# Validate log directory
validate_log_dir() {
    if [[ ! -d "$LOG_DIR" ]]; then
        echo -e "${RED}Error: Log directory not found: $LOG_DIR${NC}" >&2
        echo -e "${YELLOW}Tip: Make sure the Family Assistant API is generating logs.${NC}" >&2
        exit 1
    fi
}

# Get log files to analyze
get_log_files() {
    local date_dir="$LOG_DIR/$DATE"
    local log_files=()

    if [[ -d "$date_dir" ]]; then
        local log_file="$date_dir/chat-sessions-$DATE.ndjson"
        if [[ -f "$log_file" ]]; then
            log_files+=("$log_file")
        fi

        # Check for compressed version
        local gz_file="$log_file.gz"
        if [[ -f "$gz_file" ]]; then
            log_files+=("$gz_file")
        fi
    fi

    echo "${log_files[@]}"
}

# Process prompt-related log entries
process_prompt_logs() {
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
                    # Filter for entries with prompt data
                    if echo "$line" | jq -e '.system_prompt or .prompt_stats or .prompt_assembly' >/dev/null 2>&1; then
                        entries+=("$line")
                    fi
                fi
            done < <(gunzip -c "$log_file")
        else
            while IFS= read -r line; do
                if [[ -n "$line" ]]; then
                    # Filter for entries with prompt data
                    if echo "$line" | jq -e '.system_prompt or .prompt_stats or .prompt_assembly' >/dev/null 2>&1; then
                        entries+=("$line")
                    fi
                fi
            done < "$log_file"
        fi
    done

    echo "${entries[@]}"
}

# Filter entries by criteria
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

        if [[ "$include" == true ]]; then
            filtered_entries+=("$entry")
        fi
    done

    echo "${filtered_entries[@]}"
}

# Generate complete prompt trace
generate_prompt_trace() {
    local entries=($@)

    if [[ ${#entries[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No prompt-related entries found for analysis.${NC}"
        echo -e "${CYAN}Tip: Ensure the API is logging prompt assembly data.${NC}"
        return
    fi

    echo -e "${CYAN}=== Complete Prompt Assembly Trace ===${NC}"
    echo -e "${BLUE}Analyzing ${#entries[@]} prompt entries...${NC}"
    echo ""

    for entry in "${entries[@]}"; do
        local timestamp=$(echo "$entry" | jq -r '.timestamp // "Unknown"')
        local session_id=$(echo "$entry" | jq -r '.session_id // "Unknown"')
        local user_id=$(echo "$entry" | jq -r '.user_id // "Unknown"')
        local thread_id=$(echo "$entry" | jq -r '.thread_id // "Unknown"')

        echo -e "${PURPLE}📍 Session: $session_id | User: $user_id | Thread: $thread_id${NC}"
        echo -e "${CYAN}   Time: $timestamp${NC}"
        echo ""

        # Extract system prompt
        local system_prompt=$(echo "$entry" | jq -r '.system_prompt // null')
        if [[ "$system_prompt" != "null" && -n "$system_prompt" ]]; then
            echo -e "${GREEN}📝 System Prompt Preview:${NC}"
            echo -e "${YELLOW}   $(echo "$system_prompt" | head -c 200)${NC}"
            if [[ ${#system_prompt} -gt 200 ]]; then
                echo -e "${YELLOW}... (${#system_prompt} characters total)${NC}"
            fi
            echo ""

            # Analyze prompt components
            analyze_prompt_components "$system_prompt"
        fi

        # Extract prompt stats if available
        local prompt_stats=$(echo "$entry" | jq -r '.prompt_stats // null')
        if [[ "$prompt_stats" != "null" ]]; then
            echo -e "${GREEN}📊 Prompt Statistics:${NC}"
            echo -e "${YELLOW}   Total Length: $(echo "$prompt_stats" | jq -r '.total_length // "Unknown"')${NC}"
            echo -e "${YELLOW}   Estimated Tokens: $(echo "$prompt_stats" | jq -r '.estimated_tokens // "Unknown"')${NC}"
            echo -e "${YELLOW}   Component Count: $(echo "$prompt_stats" | jq -r '.section_count // "Unknown"')${NC}"
            echo -e "${YELLOW}   Has Memory Context: $(echo "$prompt_stats" | jq -r '.has_memory_context // "Unknown"')${NC}"
            echo ""
        fi

        # Extract performance data
        local performance=$(echo "$entry" | jq -r '.performance // null')
        if [[ "$performance" != "null" ]]; then
            local prompt_time=$(echo "$performance" | jq -r '.prompt_assembly_ms // 0')
            if [[ "$prompt_time" != "0" && "$prompt_time" != "null" ]]; then
                echo -e "${GREEN}⚡ Prompt Assembly Time: ${prompt_time}ms${NC}"
                echo ""
            fi
        fi

        echo -e "${BLUE}$(printf '=%.0s' {1..80})${NC}"
        echo ""
    done
}

# Analyze prompt components and sources
analyze_prompt_components() {
    local system_prompt="$1"

    # Core system prompts
    if echo "$system_prompt" | grep -qi "juanita\|family assistant"; then
        echo -e "${CYAN}   🔧 Core System Prompts:${NC}"
        echo -e "${YELLOW}      ✓ FAMILY_ASSISTANT.md - AI identity as Juanita${NC}"
    fi

    if echo "$system_prompt" | grep -qi "principles\|family-centric"; then
        echo -e "${YELLOW}      ✓ PRINCIPLES.md - Behavioral principles${NC}"
    fi

    # Role-based prompts
    if echo "$system_prompt" | grep -qi "parent\|professional helper"; then
        echo -e "${CYAN}   👤 Role-Based Prompts:${NC}"
        echo -e "${YELLOW}      ✓ parent.md - Professional helper role${NC}"
    elif echo "$system_prompt" | grep -qi "teenager\|friendly peer"; then
        echo -e "${YELLOW}      ✓ teenager.md - Friendly peer role${NC}"
    elif echo "$system_prompt" | grep -qi "child\|simple.*encouraging"; then
        echo -e "${YELLOW}      ✓ child.md - Child-safe role${NC}"
    elif echo "$system_prompt" | grep -qi "grandparent\|warm.*family"; then
        echo -e "${YELLOW}      ✓ grandparent.md - Grandparent role${NC}"
    fi

    # Skill-based prompts
    if echo "$system_prompt" | grep -qi "calendar\|scheduling"; then
        echo -e "${CYAN}   🛠️ Skill-Based Prompts:${NC}"
        echo -e "${YELLOW}      ✓ calendar.md - Calendar management${NC}"
    fi

    if echo "$system_prompt" | grep -qi "reminder\|task.*management"; then
        echo -e "${YELLOW}      ✓ reminders.md - Task reminders${NC}"
    fi

    if echo "$system_prompt" | grep -qi "homework\|educational"; then
        echo -e "${YELLOW}      ✓ homework_help.md - Educational support${NC}"
    fi

    # Memory system prompts
    if echo "$system_prompt" | grep -qi "recent conversation\|## recent"; then
        echo -e "${CYAN}   🧠 Memory System:${NC}"
        echo -e "${YELLOW}      ✓ Redis context - Recent conversation (Layer 1)${NC}"
    fi

    if echo "$system_prompt" | grep -qi "user preferences\|## user preferences"; then
        echo -e "${YELLOW}      ✓ Mem0 context - User preferences (Layer 2)${NC}"
    fi

    if echo "$system_prompt" | grep -qi "relevant memories\|## relevant"; then
        echo -e "${YELLOW}      ✓ Qdrant context - Semantic memories (Layer 4)${NC}"
    fi

    # Language prompts
    if echo "$system_prompt" | grep -qi "bilingual\|spanish.*english"; then
        echo -e "${CYAN}   🌐 Language Context:${NC}"
        echo -e "${YELLOW}      ✓ bilingual_context.md - Spanish-English support${NC}"
    fi
}

# Generate detailed source breakdown
generate_source_breakdown() {
    local entries=($@)

    if [[ ${#entries[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No entries found for source analysis.${NC}"
        return
    fi

    echo -e "${CYAN}=== Detailed Prompt Source Breakdown ===${NC}"
    echo ""

    # Source statistics
    declare -A source_counts
    declare -A source_tokens
    declare -A source_types

    local total_prompts=0
    local total_tokens=0

    for entry in "${entries[@]}"; do
        local system_prompt=$(echo "$entry" | jq -r '.system_prompt // ""')
        local user_id=$(echo "$entry" | jq -r '.user_id // "unknown"')
        local prompt_tokens=$(echo "$entry" | jq -r '.token_economics.prompt_tokens // 0')

        if [[ -n "$system_prompt" ]]; then
            ((total_prompts++))
            total_tokens=$((total_tokens + prompt_tokens))

            # Count source occurrences
            if echo "$system_prompt" | grep -qi "juanita\|family assistant"; then
                source_counts["FAMILY_ASSISTANT"]=$((source_counts["FAMILY_ASSISTANT"] + 1))
                source_tokens["FAMILY_ASSISTANT"]=$((source_tokens["FAMILY_ASSISTANT"] + 450))
                source_types["FAMILY_ASSISTANT"]="core_system"
            fi

            if echo "$system_prompt" | grep -qi "principles"; then
                source_counts["PRINCIPLES"]=$((source_counts["PRINCIPLES"] + 1))
                source_tokens["PRINCIPLES"]=$((source_tokens["PRINCIPLES"] + 400))
                source_types["PRINCIPLES"]="core_system"
            fi

            if echo "$system_prompt" | grep -qi "parent"; then
                source_counts["ROLE_PARENT"]=$((source_counts["ROLE_PARENT"] + 1))
                source_tokens["ROLE_PARENT"]=$((source_tokens["ROLE_PARENT"] + 200))
                source_types["ROLE_PARENT"]="role_based"
            elif echo "$system_prompt" | grep -qi "teenager"; then
                source_counts["ROLE_TEENAGER"]=$((source_counts["ROLE_TEENAGER"] + 1))
                source_tokens["ROLE_TEENAGER"]=$((source_tokens["ROLE_TEENAGER"] + 150))
                source_types["ROLE_TEENAGER"]="role_based"
            elif echo "$system_prompt" | grep -qi "child"; then
                source_counts["ROLE_CHILD"]=$((source_counts["ROLE_CHILD"] + 1))
                source_tokens["ROLE_CHILD"]=$((source_tokens["ROLE_CHILD"] + 100))
                source_types["ROLE_CHILD"]="role_based"
            fi

            if echo "$system_prompt" | grep -qi "calendar"; then
                source_counts["SKILL_CALENDAR"]=$((source_counts["SKILL_CALENDAR"] + 1))
                source_tokens["SKILL_CALENDAR"]=$((source_tokens["SKILL_CALENDAR"] + 120))
                source_types["SKILL_CALENDAR"]="skill_based"
            fi

            if echo "$system_prompt" | grep -qi "recent conversation\|user preferences"; then
                source_counts["MEMORY_SYSTEM"]=$((source_counts["MEMORY_SYSTEM"] + 1))
                source_tokens["MEMORY_SYSTEM"]=$((source_tokens["MEMORY_SYSTEM"] + 300))
                source_types["MEMORY_SYSTEM"]="memory_system"
            fi
        fi
    done

    # Display source statistics
    echo -e "${GREEN}📊 Source Statistics (${total_prompts} prompts analyzed)${NC}"
    echo ""

    printf "%-30s %8s %12s %12s %15s\n" "SOURCE" "COUNT" "TOKENS" "PERCENT" "TYPE"
    echo -e "${BLUE}$(printf '=%.0s' {1..85})${NC}"

    for source in "${!source_counts[@]}"; do
        local count=${source_counts[$source]}
        local tokens=${source_tokens[$source]}
        local type=${source_types[$source]}
        local percent=0
        if [[ $total_tokens -gt 0 ]]; then
            percent=$(echo "scale=1; $tokens * 100 / $total_tokens" | bc -l)
        fi

        printf "%-30s %8d %12d %11.1f%% %15s\n" "$source" "$count" "$tokens" "$percent" "$type"
    done

    echo ""
    echo -e "${GREEN}📈 Summary:${NC}"
    echo -e "${YELLOW}   Total Prompts Analyzed: $total_prompts${NC}"
    echo -e "${YELLOW}   Total Estimated Tokens: $total_tokens${NC}"
    echo -e "${YELLOW}   Average Tokens per Prompt: $((total_tokens / total_prompts))${NC}"
}

# Generate memory system analysis
generate_memory_analysis() {
    local entries=($@)

    if [[ ${#entries[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No entries found for memory analysis.${NC}"
        return
    fi

    echo -e "${CYAN}=== Memory System Contribution Analysis ===${NC}"
    echo ""

    local memory_layer_counts=("Redis:0" "Mem0:0" "PostgreSQL:0" "Qdrant:0" "Archive:0")
    local total_with_memory=0

    for entry in "${entries[@]}"; do
        local system_prompt=$(echo "$entry" | jq -r '.system_prompt // ""')
        local memory_context=$(echo "$entry" | jq -r '.memory_context // {}')

        if [[ -n "$system_prompt" ]]; then
            local has_memory=false

            # Check for different memory layers
            if echo "$system_prompt" | grep -qi "recent conversation"; then
                memory_layer_counts[0]="${memory_layer_counts[0]%%:*}:$(( ${memory_layer_counts[0]##*:} + 1 ))"
                has_memory=true
            fi

            if echo "$system_prompt" | grep -qi "user preferences"; then
                memory_layer_counts[1]="${memory_layer_counts[1]%%:*}:$(( ${memory_layer_counts[1]##*:} + 1 ))"
                has_memory=true
            fi

            if echo "$memory_context" | jq -e '.redis_hits' >/dev/null 2>&1; then
                local redis_hits=$(echo "$memory_context" | jq -r '.redis_hits // 0')
                if [[ $redis_hits -gt 0 ]]; then
                    has_memory=true
                fi
            fi

            if [[ "$has_memory" == true ]]; then
                ((total_with_memory++))
            fi
        fi
    done

    echo -e "${GREEN}🧠 Memory Layer Usage:${NC}"
    for layer_count in "${memory_layer_counts[@]}"; do
        local layer="${layer_count%%:*}"
        local count="${layer_count##*:}"
        echo -e "${YELLOW}   $layer: $count prompts${NC}"
    done

    echo ""
    echo -e "${GREEN}📊 Memory Statistics:${NC}"
    echo -e "${YELLOW}   Prompts with Memory Context: $total_with_memory${NC}"
    echo -e "${YELLOW}   Memory Coverage: $(echo "scale=1; $total_with_memory * 100 / ${#entries[@]}" | bc -l)%${NC}"
}

# Export to JSON
export_to_json() {
    local entries=($@)
    local output_file="$1"

    if [[ ${#entries[@]} -eq 0 ]]; then
        echo -e "${RED}No entries to export.${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}Exporting ${#entries[@]} entries to $output_file...${NC}"

    # Create JSON export with enhanced prompt analysis
    printf '%s\n' "${entries[@]}" | jq -s '.' > "$output_file"

    # Add metadata
    local temp_file=$(mktemp)
    jq --arg date "$DATE" --arg count "${#entries[@]}" --arg generated "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" \
        '{
            "metadata": {
                "analysis_date": $date,
                "generated_at": $generated,
                "total_entries": $count,
                "analyzer_version": "1.0.0"
            },
            "entries": .
        }' "$output_file" > "$temp_file"

    mv "$temp_file" "$output_file"

    echo -e "${GREEN}Exported ${#entries[@]} entries to $output_file${NC}"
}

# Main execution
main() {
    parse_args "$@"
    validate_log_dir

    echo -e "${CYAN}Prompt Source Analyzer${NC}"
    echo -e "${BLUE}Analyzing prompt assembly for: $DATE${NC}"

    # Get log files
    local log_files=($(get_log_files))

    if [[ ${#log_files[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No prompt log files found for the specified date.${NC}"
        echo -e "${CYAN}Tip: Ensure the API is logging prompt assembly data with system_prompt field.${NC}"
        exit 0
    fi

    echo -e "${BLUE}Found ${#log_files[@]} log file(s)${NC}"

    # Process prompt logs
    local entries=($(process_prompt_logs "${log_files[@]}"))

    if [[ ${#entries[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No prompt-related entries found in logs.${NC}"
        echo -e "${CYAN}Make sure the API is logging system_prompt and prompt_stats fields.${NC}"
        exit 0
    fi

    echo -e "${BLUE}Found ${#entries[@]} prompt entries${NC}"

    # Apply filters
    local filtered_entries=($(filter_entries "${entries[@]}"))
    echo -e "${BLUE}Filtered to ${#filtered_entries[@]} relevant entries${NC}"

    # Generate reports based on options
    if [[ "$SHOW_TRACE" == true ]]; then
        generate_prompt_trace "${filtered_entries[@]}"
    fi

    if [[ "$SHOW_SOURCES" == true ]]; then
        generate_source_breakdown "${filtered_entries[@]}"
    fi

    if [[ "$SHOW_MEMORY" == true ]]; then
        generate_memory_analysis "${filtered_entries[@]}"
    fi

    if [[ "$SHOW_TOKENS" == true ]]; then
        # Token analysis would be implemented here
        echo -e "${CYAN}=== Token Analysis ===${NC}"
        echo "Token analysis feature coming soon..."
    fi

    if [[ -n "$EXPORT_JSON" ]]; then
        export_to_json "${filtered_entries[@]}" "$EXPORT_JSON"
    fi

    # If no specific options, show trace by default
    if [[ "$SHOW_TRACE" == false && "$SHOW_SOURCES" == false && "$SHOW_MEMORY" == false && "$SHOW_TOKENS" == false ]]; then
        generate_prompt_trace "${filtered_entries[@]}"
    fi

    echo -e "${GREEN}Prompt source analysis complete.${NC}"
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