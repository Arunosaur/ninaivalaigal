# mem0.zsh - Zsh integration for the mem0 system

# Debug logging function
mem0_debug() {
    if [[ -n "$MEM0_DEBUG" ]]; then
        echo "[mem0-debug] $1" >&2
    fi
}

# This function will run before each command is executed
mem0_preexec() {
    mem0_debug "preexec hook triggered for command: $1"
    
    # Get the active recording context from the server
    # Note: This makes an API call on every command, which may have performance implications.
    # We will address this in a future iteration.
    local active_context_json=$(./client/mem0 context active 2>/dev/null)
    mem0_debug "active context response: $active_context_json"
    
    local active_context=$(echo $active_context_json | sed -n 's/.*"recording_context": "\([^"]*\)".*/\1/p')
    mem0_debug "parsed active context: '$active_context'"

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

# Register the hook function
autoload -U add-zsh-hook
add-zsh-hook preexec mem0_preexec

