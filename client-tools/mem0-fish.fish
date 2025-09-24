#!/usr/bin/env fish
# mem0 Shell Integration for Fish Shell
# Compatible with Fish shell on Linux, macOS, and other Unix systems

# Configuration
set -q MEM0_PORT; or set -g MEM0_PORT 13370
set -q MEM0_DEBUG; or set -g MEM0_DEBUG 0
set -q MEM0_CONTEXT; or set -g MEM0_CONTEXT ""
set -q MEM0_PROCESSING; or set -g MEM0_PROCESSING 0
set -q MEM0_CACHE_TTL; or set -g MEM0_CACHE_TTL 30

# Global variables
set -g CURRENT_CONTEXT ""
set -g CONTEXT_CACHE ""
set -g CACHE_TIMESTAMP 0
set -g LAST_COMMAND ""
set -g LAST_PWD ""

function debug_log
    if test "$MEM0_DEBUG" = "1"
        echo "[mem0-debug] $argv[1]" >&2
    end
end

function check_server
    if command -q curl
        if curl -s "http://127.0.0.1:$MEM0_PORT/health" >/dev/null 2>&1
            return 0
        end
    else if command -q wget
        if wget -q -O /dev/null "http://127.0.0.1:$MEM0_PORT/health" 2>/dev/null
            return 0
        end
    end
    return 1
end

function get_context_cache
    set -l current_time (date +%s)

    if test -n "$CONTEXT_CACHE"; and test (math $current_time - $CACHE_TIMESTAMP) -lt $MEM0_CACHE_TTL
        debug_log "Using cached context: $CONTEXT_CACHE"
        echo $CONTEXT_CACHE
        return 0
    end

    # Try to get active context from server
    if check_server
        if command -q curl
            set -l response (curl -s "http://127.0.0.1:$MEM0_PORT/context/active" 2>/dev/null)
            if test $status -eq 0; and test -n "$response"
                set -g CONTEXT_CACHE $response
                set -g CACHE_TIMESTAMP $current_time
                debug_log "Fetched context from server: $CONTEXT_CACHE"
                echo $CONTEXT_CACHE
                return 0
            end
        end
    end

    echo ""
end

function send_command
    set -l command $argv[1]
    set -l pwd $argv[2]
    set -l exit_code $argv[3]

    # Skip if already processing
    if test "$MEM0_PROCESSING" = "1"
        debug_log "Already processing, skipping: $command"
        return
    end

    # Skip if no context
    set -l context (get_context_cache)
    if test -z "$context"
        debug_log "No active context, skipping command"
        return
    end

    # Skip short or irrelevant commands
    if test (string length $command) -lt 3
        or string match -q -r '^(ls|pwd|cd|echo|set|alias|history|exit)$' $command
        return
    end

    # Set processing flag
    set -g MEM0_PROCESSING 1

    debug_log "Sending command: $command (pwd: $pwd, exit: $exit_code)"

    # Prepare JSON payload
    set -l json_payload "{
        \"type\": \"terminal_command\",
        \"source\": \"fish_session\",
        \"data\": {
            \"command\": \"$command\",
            \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\",
            \"pwd\": \"$pwd\",
            \"exit_code\": $exit_code,
            \"context\": \"$context\",
            \"shell\": \"fish\",
            \"os\": \"$(uname -s)\"
        }
    }"

    # Send to server asynchronously
    if check_server
        if command -q curl
            fish -c "curl -s -X POST 'http://127.0.0.1:$MEM0_PORT/memory' -H 'Content-Type: application/json' -d '$json_payload' >/dev/null 2>&1" &
        else if command -q wget
            fish -c "echo '$json_payload' | wget -q -O /dev/null --post-data=- 'http://127.0.0.1:$MEM0_PORT/memory' 2>/dev/null" &
        end
    else
        debug_log "Server not available, command not sent"
    end

    # Clear processing flag after background job starts
    fish -c "sleep 0.1; set -e MEM0_PROCESSING" &
end

function preexec_function
    set -l command $argv[1]
    set -g LAST_COMMAND $command
    set -g LAST_PWD $PWD
    debug_log "Pre-exec: $command"
end

function precmd_function
    set -l exit_code $status

    if test -n "$LAST_COMMAND"
        send_command $LAST_COMMAND $LAST_PWD $exit_code
        set -e LAST_COMMAND
        set -e LAST_PWD
    end
end

# Utility functions
function mem0_clear_cache
    set -g CONTEXT_CACHE ""
    set -g CACHE_TIMESTAMP 0
    debug_log "Context cache cleared"
    echo "Cache cleared"
end

function mem0_context_start
    set -l context_name $argv[1]
    if test -z "$context_name"
        echo "Usage: mem0_context_start <context_name>"
        return 1
    end

    if check_server
        if command -q curl
            curl -s -X POST "http://127.0.0.1:$MEM0_PORT/context/start" \
                 -H "Content-Type: application/json" \
                 -d "{\"name\": \"$context_name\"}" >/dev/null 2>&1
            if test $status -eq 0
                set -gx MEM0_CONTEXT $context_name
                mem0_clear_cache
                echo "Started recording to context: $context_name"
            else
                echo "Failed to start context"
            end
        else
            echo "curl not available"
        end
    else
        echo "mem0 server not running"
    end
end

function mem0_context_stop
    if check_server
        if command -q curl
            curl -s -X POST "http://127.0.0.1:$MEM0_PORT/context/stop" >/dev/null 2>&1
            if test $status -eq 0
                set -e MEM0_CONTEXT
                mem0_clear_cache
                echo "Stopped recording"
            else
                echo "Failed to stop context"
            end
        else
            echo "curl not available"
        end
    else
        echo "mem0 server not running"
    end
end

function mem0_context_active
    set -l context (get_context_cache)
    if test -n "$context"
        echo "Active context: $context"
    else
        echo "No active context"
    end
end

# Initialize Fish shell hooks
function __mem0_init
    # Set up preexec and precmd functions
    functions -c fish_prompt __mem0_original_fish_prompt

    function fish_prompt
        precmd_function
        __mem0_original_fish_prompt
    end

    # Hook into command execution
    function __mem0_preexec --on-event fish_preexec
        preexec_function "$argv"
    end

    debug_log "Initialized mem0 for Fish shell on $(uname -s)"
end

# Initialize if not already done
if not set -q __mem0_initialized
    __mem0_init
    set -g __mem0_initialized 1
end
