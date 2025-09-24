#!/bin/bash
# mem0 Shell Integration for Linux/Unix Systems
# Supports bash, zsh, fish, and various Linux distributions

# Detect shell and OS
detect_shell() {
    if [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    elif [ -n "$BASH_VERSION" ]; then
        echo "bash"
    elif [ -n "$FISH_VERSION" ]; then
        echo "fish"
    else
        echo "unknown"
    fi
}

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            echo "$ID"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Configuration
NINAIVALAIGAL_PORT=${NINAIVALAIGAL_PORT:-13370}
NINAIVALAIGAL_DEBUG=${NINAIVALAIGAL_DEBUG:-0}
NINAIVALAIGAL_CONTEXT=${NINAIVALAIGAL_CONTEXT:-""}
NINAIVALAIGAL_PROCESSING=${NINAIVALAIGAL_PROCESSING:-0}
NINAIVALAIGAL_CACHE_TTL=${NINAIVALAIGAL_CACHE_TTL:-30}

# Global variables
CURRENT_CONTEXT=""
CONTEXT_CACHE=""
CACHE_TIMESTAMP=0

# Debug logging
debug_log() {
    if [ "$NINAIVALAIGAL_DEBUG" = "1" ]; then
        echo "[ninaivalaigal-debug] $1" >&2
    fi
}

# Check if mem0 server is running
check_server() {
    if command -v curl >/dev/null 2>&1; then
        if curl -s "http://127.0.0.1:$NINAIVALAIGAL_PORT/health" >/dev/null 2>&1; then
            return 0
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget -q -O /dev/null "http://127.0.0.1:$NINAIVALAIGAL_PORT/health" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Get context from cache or server
get_context_cache() {
    local current_time
    current_time=$(date +%s)

    if [ -n "$CONTEXT_CACHE" ] && [ $((current_time - CACHE_TIMESTAMP)) -lt $NINAIVALAIGAL_CACHE_TTL ]; then
        debug_log "Using cached context: $CONTEXT_CACHE"
        echo "$CONTEXT_CACHE"
        return 0
    fi

    # Try to get active context from server
    if check_server; then
        if command -v curl >/dev/null 2>&1; then
            local response
            response=$(curl -s "http://127.0.0.1:$NINAIVALAIGAL_PORT/context/active" 2>/dev/null)
            if [ $? -eq 0 ] && [ -n "$response" ]; then
                CONTEXT_CACHE="$response"
                CACHE_TIMESTAMP=$current_time
                debug_log "Fetched context from server: $CONTEXT_CACHE"
                echo "$CONTEXT_CACHE"
                return 0
            fi
        fi
    fi

    echo ""
}

# Send command to mem0 server
send_command() {
    local command="$1"
    local pwd="$2"
    local exit_code="$3"

    # Skip if already processing
    if [ "$NINAIVALAIGAL_PROCESSING" = "1" ]; then
        debug_log "Already processing, skipping: $command"
        return
    fi

    # Skip if no context
    local context
    context=$(get_context_cache)
    if [ -z "$context" ]; then
        debug_log "No active context, skipping command"
        return
    fi

    # Skip short or irrelevant commands
    if [ ${#command} -lt 3 ] || [[ "$command" =~ ^(ls|pwd|cd|echo|export|alias|history|exit)$ ]]; then
        return
    fi

    # Set processing flag
    NINAIVALAIGAL_PROCESSING=1

    debug_log "Sending command: $command (pwd: $pwd, exit: $exit_code)"

    # Prepare JSON payload
    local json_payload
    json_payload=$(cat <<EOF
{
    "type": "terminal_command",
    "source": "$(detect_shell)_session",
    "data": {
        "command": "$command",
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
        "pwd": "$pwd",
        "exit_code": $exit_code,
        "context": "$context",
        "shell": "$(detect_shell)",
        "os": "$(detect_os)"
    }
}
EOF
)

    # Send to server asynchronously
    if check_server; then
        if command -v curl >/dev/null 2>&1; then
            (curl -s -X POST "http://127.0.0.1:$NINAIVALAIGAL_PORT/memory" \
                 -H "Content-Type: application/json" \
                 -d "$json_payload" >/dev/null 2>&1 && debug_log "Command sent successfully") &
        elif command -v wget >/dev/null 2>&1; then
            (echo "$json_payload" | wget -q -O /dev/null --post-data=- \
                 "http://127.0.0.1:$NINAIVALAIGAL_PORT/memory" 2>/dev/null && debug_log "Command sent successfully") &
        fi
    else
        debug_log "Server not available, command not sent"
    fi

    # Clear processing flag after background job starts
    (sleep 0.1 && unset NINAIVALAIGAL_PROCESSING) &
}

# Pre-execution hook (capture command before execution)
preexec_function() {
    local command="$1"
    LAST_COMMAND="$command"
    LAST_PWD="$PWD"
    debug_log "Pre-exec: $command"
}

# Post-execution hook (capture command result after execution)
precmd_function() {
    local exit_code=$?

    if [ -n "$LAST_COMMAND" ]; then
        send_command "$LAST_COMMAND" "$LAST_PWD" $exit_code
        unset LAST_COMMAND
        unset LAST_PWD
    fi
}

# Initialize based on shell
init_shell_integration() {
    local shell_type
    shell_type=$(detect_shell)

    case $shell_type in
        bash)
            init_bash
            ;;
        zsh)
            init_zsh
            ;;
        fish)
            init_fish
            ;;
        *)
            debug_log "Unsupported shell: $shell_type"
            return 1
            ;;
    esac

    debug_log "Initialized mem0 for $shell_type on $(detect_os)"
}

# Bash-specific initialization
init_bash() {
    # Use DEBUG trap for pre-exec
    trap 'preexec_function "$BASH_COMMAND"' DEBUG

    # Use PROMPT_COMMAND for post-exec
    if [ -z "$PROMPT_COMMAND" ]; then
        PROMPT_COMMAND="precmd_function"
    else
        PROMPT_COMMAND="$PROMPT_COMMAND; precmd_function"
    fi
}

# Zsh-specific initialization
init_zsh() {
    # Use preexec and precmd functions
    autoload -Uz add-zsh-hook
    add-zsh-hook preexec preexec_function
    add-zsh-hook precmd precmd_function
}

# Fish-specific initialization
init_fish() {
    # Fish uses event handlers
    # Note: This would need to be adapted for fish syntax
    debug_log "Fish shell detected - manual configuration required"
}

# Utility functions
mem0_clear_cache() {
    CONTEXT_CACHE=""
    CACHE_TIMESTAMP=0
    debug_log "Context cache cleared"
}

mem0_context_start() {
    local context_name="$1"
    if [ -z "$context_name" ]; then
        echo "Usage: mem0_context_start <context_name>"
        return 1
    fi

    if check_server; then
        if command -v curl >/dev/null 2>&1; then
            curl -s -X POST "http://127.0.0.1:$NINAIVALAIGAL_PORT/context/start" \
                 -H "Content-Type: application/json" \
                 -d "{\"name\": \"$context_name\"}" >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                export NINAIVALAIGAL_CONTEXT="$context_name"
                mem0_clear_cache
                echo "Started recording to context: $context_name"
            else
                echo "Failed to start context"
            fi
        else
            echo "curl not available"
        fi
    else
        echo "mem0 server not running"
    fi
}

mem0_context_stop() {
    if check_server; then
        if command -v curl >/dev/null 2>&1; then
            curl -s -X POST "http://127.0.0.1:$NINAIVALAIGAL_PORT/context/stop" >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                unset NINAIVALAIGAL_CONTEXT
                mem0_clear_cache
                echo "Stopped recording"
            else
                echo "Failed to stop context"
            fi
        else
            echo "curl not available"
        fi
    else
        echo "mem0 server not running"
    fi
}

mem0_context_active() {
    local context
    context=$(get_context_cache)
    if [ -n "$context" ]; then
        echo "Active context: $context"
    else
        echo "No active context"
    fi
}

# Initialize if not already done
if [ -z "$NINAIVALAIGAL_INITIALIZED" ]; then
    init_shell_integration
    export NINAIVALAIGAL_INITIALIZED=1
fi
