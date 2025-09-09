# mem0.zsh - Zsh integration for the mem0 system

# This function will run before each command is executed
mem0_preexec() {
    # Get the active recording context from the server
    local active_context=$(./client/mem0 context active 2>/dev/null)

    # If we are not recording, do nothing
    if [ -z "$active_context" ]; then
        return
    fi

    # Capture the command string
    _MEM0_COMMAND_STRING=$1

    # Create a temporary file to store the command output
    _MEM0_OUTPUT_FILE=$(mktemp)

    # Start a script session to capture output
    script -q "$_MEM0_OUTPUT_FILE"
}

# This function will run after each command has finished
mem0_precmd() {
    # If we are not recording, do nothing
    if [ -z "$_MEM0_COMMAND_STRING" ]; then
        return
    fi

    # Stop the script session
    exit

    # Capture the exit code of the last command
    local exit_code=$?

    # Read the output from the temporary file
    local output=$(cat "$_MEM0_OUTPUT_FILE")
    rm "$_MEM0_OUTPUT_FILE"

    # Construct the JSON payload
    local json_payload=$(printf '{ "type": "terminal_command", "source": "zsh_session", "data": { "command": "%s", "output": "%s", "exit_code": %d } }' "$_MEM0_COMMAND_STRING" "$output" "$exit_code")

    # Remember the captured data
    ./client/mem0 remember "$json_payload"

    # Clear the command string to mark that we are done
    _MEM0_COMMAND_STRING=""
}

# Register the hook functions
autoload -U add-zsh-hook
add-zsh-hook preexec mem0_preexec
add-zsh-hook precmd mem0_precmd

