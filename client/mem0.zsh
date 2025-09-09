# mem0.zsh - Zsh integration for the mem0 system

# Global variables for caching
MEM0_CACHED_CONTEXT=""
MEM0_CACHE_TIMESTAMP=0
MEM0_CACHE_TTL=30  # Cache for 30 seconds

# Debug logging function
mem0_debug() {
    if [[ -n "$MEM0_DEBUG" ]]; then
        echo "[mem0-debug] $1" >&2
    fi
}

# Get current timestamp
mem0_timestamp() {
    date +%s
}

# Get active context with caching
mem0_get_active_context() {
    local current_time=$(mem0_timestamp)
    local cache_age=$((current_time - MEM0_CACHE_TIMESTAMP))
    
    # Use cached context if it's still valid
    if [[ $cache_age -lt $MEM0_CACHE_TTL ]]; then
        mem0_debug "using cached context: '$MEM0_CACHED_CONTEXT' (age: ${cache_age}s)"
        echo "$MEM0_CACHED_CONTEXT"
        return
    fi
    
    # Fetch fresh context from server
    mem0_debug "fetching fresh context from server (cache expired)"
    local active_context_json=$(./client/mem0 context active 2>/dev/null)
    mem0_debug "active context response: $active_context_json"
    
    # Parse JSON response - extract context name
    local active_context=$(echo "$active_context_json" | sed "s/.*'recording_context': '\([^']*\)'.*/\1/")
    
    # Update cache
    MEM0_CACHED_CONTEXT="$active_context"
    MEM0_CACHE_TIMESTAMP=$current_time
    mem0_debug "cached new context: '$active_context'"
    
    echo "$active_context"
}

# This function will run before each command is executed
mem0_preexec() {
    mem0_debug "preexec hook triggered for command: $1"
    
    # Get the active recording context (with caching)
    local active_context=$(mem0_get_active_context)
    mem0_debug "active context: '$active_context'"

    # If we are not recording, do nothing
    if [ -z "$active_context" ] || [ "$active_context" = "null" ]; then
        mem0_debug "no active context, skipping command capture"
        return
    fi

    # Construct the JSON payload with just the command
    local json_payload=$(printf '{ "type": "terminal_command", "source": "zsh_session", "data": { "command": "%s" } }' "$1")
    mem0_debug "constructed payload: $json_payload"

    # Remember the command, in the background
    mem0_debug "sending command to mem0 server..."
    ./client/mem0 remember "$json_payload" --context "$active_context" &>/dev/null &
}

# Function to clear the context cache (useful when context changes)
mem0_clear_cache() {
    MEM0_CACHED_CONTEXT=""
    MEM0_CACHE_TIMESTAMP=0
    mem0_debug "context cache cleared"
}

# Register the hook function
autoload -U add-zsh-hook
add-zsh-hook preexec mem0_preexec

