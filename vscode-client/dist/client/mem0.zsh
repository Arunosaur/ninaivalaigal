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
    # Prevent duplicate execution by checking if we're already processing
    if [[ -n "$MEM0_PROCESSING" ]]; then
        return
    fi
    export MEM0_PROCESSING=1
    
    mem0_debug "preexec hook triggered for command: $1"
    
    # Check if MEM0_CONTEXT environment variable is set for this terminal
    local active_context=""
    if [[ -n "$MEM0_CONTEXT" ]]; then
        active_context="$MEM0_CONTEXT"
        mem0_debug "using MEM0_CONTEXT env var: '$active_context'"
    else
        # Fall back to server's active context (most recently created)
        active_context=$(mem0_get_active_context)
        mem0_debug "using server active context: '$active_context'"
    fi

    # If we are not recording, do nothing
    if [ -z "$active_context" ] || [ "$active_context" = "null" ]; then
        mem0_debug "no active context, skipping command capture"
        unset MEM0_PROCESSING
        return
    fi

    # Construct the JSON payload with just the command
    local json_payload=$(printf '{ "type": "terminal_command", "source": "zsh_session", "data": { "command": "%s" } }' "$1")
    mem0_debug "constructed payload: $json_payload"

    # Remember the command, in the background
    mem0_debug "sending command to mem0 server..."
    (~/Workspace/mem0/client/mem0 remember "$json_payload" --context "$active_context" &>/dev/null; unset MEM0_PROCESSING) &
}

# Function to clear the context cache (useful when context changes)
mem0_clear_cache() {
    MEM0_CACHED_CONTEXT=""
    MEM0_CACHE_TIMESTAMP=0
    mem0_debug "context cache cleared"
}

# Simple on/off functions - like CCTV switch
mem0_on() {
    local context_name="${1:-$(basename $(pwd))}"
    ~/Workspace/mem0/client/mem0 context start "$context_name" >/dev/null 2>&1
    export MEM0_CONTEXT="$context_name"
    mem0_clear_cache
    echo "mem0 recording: $context_name"
}

mem0_off() {
    if [[ -n "$MEM0_CONTEXT" ]]; then
        echo "mem0 stopped: $MEM0_CONTEXT"
        unset MEM0_CONTEXT
        mem0_clear_cache
    else
        echo "mem0 not recording"
    fi
}

# Register the hook function
if [[ -n "$ZSH_VERSION" ]]; then
    # Check if our function is already in the array to avoid duplicates
    if [[ ! " ${preexec_functions[@]} " =~ " mem0_preexec " ]]; then
        # Initialize preexec_functions array if it doesn't exist
        if [[ -z "$preexec_functions" ]]; then
            typeset -ga preexec_functions
        fi
        
        # Add our function to the preexec_functions array
        preexec_functions+=(mem0_preexec)
        mem0_debug "mem0_preexec hook registered"
    else
        mem0_debug "mem0_preexec hook already registered"
    fi
else
    # For bash or other shells
    echo "Warning: mem0 shell integration is optimized for zsh"
fi

