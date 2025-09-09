# mem0.zsh - Zsh integration for the mem0 system

# This function will run before each command is executed
mem0_preexec() {
    # Get the active recording context from the server
    # Note: This makes an API call on every command, which may have performance implications.
    # We will address this in a future iteration.
    local active_context_json=$(./client/mem0 context active 2>/dev/null)
    local active_context=$(echo $active_context_json | sed -n 's/.*"recording_context": "\([^"]*\)".*/\1/p')

    # If we are not recording, do nothing
    if [ -z "$active_context" ]; then
        return
    fi

    # Construct the JSON payload with just the command
    local json_payload=$(printf '{ "type": "terminal_command", "source": "zsh_session", "data": { "command": "%s" } }' "$1")

    # Remember the command, in the background
    ./client/mem0 remember "$json_payload" --context "$active_context" &>/dev/null &
}

# Register the hook function
autoload -U add-zsh-hook
add-zsh-hook preexec mem0_preexec

