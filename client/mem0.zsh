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
    local active_context_json=$(~/Workspace/mem0/client/mem0 active 2>/dev/null)
    mem0_debug "active context response: $active_context_json"
    
    # Parse the response - extract context name from "Terminal context: <name>" format
    local active_context=$(echo "$active_context_json" | sed -n 's/.*Terminal context: \(.*\)/\1/p')
    
    # Update cache
    MEM0_CACHED_CONTEXT="$active_context"
    MEM0_CACHE_TIMESTAMP=$current_time
    mem0_debug "cached new context: '$active_context'"
    
    echo "$active_context"
}

# This function will run before each command is executed
mem0_preexec() {
    # Skip if command is empty or starts with space (private command)
    if [[ -z "$1" || "$1" =~ ^[[:space:]] ]]; then
        return
    fi
    
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

    # Store command for output capture in precmd
    export MEM0_LAST_COMMAND="$1"
    export MEM0_LAST_CONTEXT="$active_context"
    export MEM0_COMMAND_START_TIME="$(date -Iseconds)"
    
    mem0_debug "command queued for capture: '$1' in context '$active_context'"
    
    # Clear processing flag immediately - we'll capture everything in precmd
    unset MEM0_PROCESSING
}

# This function runs after each command completes
mem0_precmd() {
    # Only capture output if we have a recent command and context
    if [[ -n "$MEM0_LAST_COMMAND" && -n "$MEM0_LAST_CONTEXT" ]]; then
        local exit_code=$?
        mem0_debug "precmd hook triggered, exit code: $exit_code"
        
        # Escape command for JSON - replace quotes and newlines
        local escaped_command=$(echo "$MEM0_LAST_COMMAND" | sed 's/"/\\"/g' | tr '\n' ' ')
        local escaped_pwd=$(pwd | sed 's/"/\\"/g')
        
        # Capture complete command execution (command + result in one entry)
        local complete_payload=$(printf '{ "type": "command_execution", "source": "zsh_session", "data": { "command": "%s", "exit_code": %d, "start_time": "%s", "end_time": "%s", "pwd": "%s" } }' "$escaped_command" "$exit_code" "$MEM0_COMMAND_START_TIME" "$(date -Iseconds)" "$escaped_pwd")
        
        # Send complete execution record in background with proper error handling
        {
            ~/Workspace/mem0/client/mem0 remember "$complete_payload" --context "$MEM0_LAST_CONTEXT" 2>&1 | while read line; do
                mem0_debug "remember output: $line"
            done
        } &
        
        # Clear stored command variables
        unset MEM0_LAST_COMMAND
        unset MEM0_LAST_CONTEXT
        unset MEM0_COMMAND_START_TIME
    fi
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

    echo "Starting context: $context_name"
    mem0 context start "$context_name"

    export MEM0_CONTEXT="$context_name"
    mem0_clear_cache
    echo "mem0 recording: $context_name"
}

# Wrapper function that matches the CLI suggestion
mem0_context_start() {
    local context_name="$1"
    if [[ -z "$context_name" ]]; then
        echo "Usage: mem0_context_start <context_name>"
        return 1
    fi
    
    # Create or activate the context
    ~/Workspace/mem0/client/mem0 context start "$context_name"
    
    # Set the terminal environment variable
    export MEM0_CONTEXT="$context_name"
    mem0_clear_cache
    echo "Terminal context set to: $context_name"
}

# Function to delete context and clean up environment
mem0_context_delete() {
    local context_name="$1"
    if [[ -z "$context_name" ]]; then
        echo "Usage: mem0_context_delete <context_name>"
        return 1
    fi
    
    # Delete the context
    ~/Workspace/mem0/client/mem0 context delete "$context_name"
    
    # Clear environment if this was the active context
    if [[ "$MEM0_CONTEXT" == "$context_name" ]]; then
        unset MEM0_CONTEXT
        mem0_clear_cache
        echo "Terminal context cleared"
    fi
}

mem0_off() {
    local context_name="$1"

    if [[ -n "$context_name" ]]; then
        # Stop the specific context
        echo "Stopping context: $context_name"
        ~/Workspace/mem0/mem0.sh context stop "$context_name"
        echo "mem0 stopped: $context_name"
    elif [[ -n "$MEM0_CONTEXT" ]]; then
        # Stop the context set in MEM0_CONTEXT
        echo "Stopping context: $MEM0_CONTEXT"
        ~/Workspace/mem0/mem0.sh context stop "$MEM0_CONTEXT"

        # Clear local environment
        unset MEM0_CONTEXT
        mem0_clear_cache
        echo "mem0 stopped: $MEM0_CONTEXT"
    else
        # Check if there's an active context on the server that we should stop
        echo "Checking for active context on server..."
        ~/Workspace/mem0/mem0.sh context stop
        echo "mem0 stopped active context"
    fi
}

# Register the hook functions
if [[ -n "$ZSH_VERSION" ]]; then
    # Check if our preexec function is already in the array to avoid duplicates
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
    
    # Check if our precmd function is already in the array to avoid duplicates
    if [[ ! " ${precmd_functions[@]} " =~ " mem0_precmd " ]]; then
        # Initialize precmd_functions array if it doesn't exist
        if [[ -z "$precmd_functions" ]]; then
            typeset -ga precmd_functions
        fi
        
        # Add our function to the precmd_functions array
        precmd_functions+=(mem0_precmd)
        mem0_debug "mem0_precmd hook registered"
    else
        mem0_debug "mem0_precmd hook already registered"
    fi
else
    # For bash or other shells
    echo "Warning: mem0 shell integration is optimized for zsh"
fi

# Direct mem0 command function
mem0() {
    # Change to the mem0 project directory
    local original_dir=$(pwd)
    local mem0_dir="$HOME/Workspace/mem0"

    if [[ ! -d "$mem0_dir" ]]; then
        echo "Error: mem0 directory not found at $mem0_dir"
        return 1
    fi

    cd "$mem0_dir"

    # Run the Python client with all arguments
    python3 client/mem0 "$@"

    # Return to original directory
    cd "$original_dir"
}

# Register the hooks with zsh
autoload -U add-zsh-hook
add-zsh-hook preexec mem0_preexec
add-zsh-hook precmd mem0_precmd
