#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Shell hook for automatic memory capture
# Implements FR-010: Shell Integration for Auto-Capture
#
# Installation:
#   1. Source this file in your shell RC file:
#      # For zsh: Add to ~/.zshrc
#      source /path/to/ninaivalaigal/adapters/shell_hooks/store_memory.sh
#
#      # For bash: Add to ~/.bashrc
#      source /path/to/ninaivalaigal/adapters/shell_hooks/store_memory.sh
#
#   2. Set required environment variables:
#      export NINA_MEMORY_SERVICE_URL="http://localhost:13393"
#      export NINA_AUTH_TOKEN="your-jwt-token-here"
#      export NINA_CONTEXT="your-active-context"
#
#   3. Optional configuration:
#      export NINA_CAPTURE_ENABLED=true  # Set to false to disable capture

# Configuration with sensible defaults
: "${NINA_MEMORY_SERVICE_URL:=http://localhost:13393}"
: "${NINA_CAPTURE_ENABLED:=true}"
: "${NINA_CONTEXT:=default}"

# Internal state tracking
_NINA_LAST_EXIT_CODE=0
_NINA_LAST_COMMAND=""
_NINA_LAST_TIMESTAMP=""

# Function to store command in memory service
# Usage: _nina_store_command <command> <exit_code> <working_directory> <timestamp>
_nina_store_command() {
    # Check if capture is enabled
    if [[ "$NINA_CAPTURE_ENABLED" != "true" ]]; then
        return 0
    fi

    # Check if auth token is set
    if [[ -z "$NINA_AUTH_TOKEN" ]]; then
        # Silently skip if no token (camera off)
        return 0
    fi

    # Check if context is set (camera off protection)
    if [[ -z "$NINA_CONTEXT" ]]; then
        # No active context - skip capture
        return 0
    fi

    local command="$1"
    local exit_code="$2"
    local working_dir="$3"
    local timestamp="$4"

    # Skip empty commands
    if [[ -z "$command" ]]; then
        return 0
    fi

    # Skip commands that shouldn't be captured
    case "$command" in
        # Internal shell commands
        _nina_*|source*|export*|alias*)
            return 0
            ;;
        # Password/secret commands
        *password*|*secret*|*token*|*key*)
            return 0
            ;;
    esac

    # Build JSON payload
    local payload=$(cat <<EOF
{
  "type": "terminal_command",
  "source": "shell_hook",
  "data": {
    "context": "$NINA_CONTEXT",
    "command": "$command",
    "exit_code": $exit_code,
    "working_directory": "$working_dir",
    "timestamp": "$timestamp",
    "shell": "$SHELL"
  }
}
EOF
)

    # Send to memory service (background, non-blocking)
    curl -s -X POST "$NINA_MEMORY_SERVICE_URL/memory" \
        -H "Authorization: Bearer $NINA_AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        > /dev/null 2>&1 &

    return 0
}

# Hook function for command execution (zsh)
if [[ -n "$ZSH_VERSION" ]]; then
    autoload -Uz add-zsh-hook

    _nina_precmd_hook() {
        _NINA_LAST_EXIT_CODE=$?
        _NINA_LAST_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        if [[ -n "$_NINA_LAST_COMMAND" ]]; then
            _nina_store_command \
                "$_NINA_LAST_COMMAND" \
                "$_NINA_LAST_EXIT_CODE" \
                "$PWD" \
                "$_NINA_LAST_TIMESTAMP"
        fi
    }

    _nina_preexec_hook() {
        _NINA_LAST_COMMAND="$1"
    }

    add-zsh-hook precmd _nina_precmd_hook
    add-zsh-hook preexec _nina_preexec_hook

# Hook function for command execution (bash)
elif [[ -n "$BASH_VERSION" ]]; then
    _nina_bash_precmd() {
        _NINA_LAST_EXIT_CODE=$?
        _NINA_LAST_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        if [[ -n "$_NINA_LAST_COMMAND" ]]; then
            _nina_store_command \
                "$_NINA_LAST_COMMAND" \
                "$_NINA_LAST_EXIT_CODE" \
                "$PWD" \
                "$_NINA_LAST_TIMESTAMP"
        fi
    }

    # Set up PROMPT_COMMAND
    if [[ -z "$PROMPT_COMMAND" ]]; then
        PROMPT_COMMAND="_nina_bash_precmd"
    else
        PROMPT_COMMAND="_nina_bash_precmd; $PROMPT_COMMAND"
    fi

    # Trap DEBUG to capture command
    trap '_NINA_LAST_COMMAND="$BASH_COMMAND"' DEBUG
fi

# Utility functions for user control

# Enable memory capture
nina_capture_on() {
    export NINA_CAPTURE_ENABLED=true
    echo "✅ Nina memory capture enabled"
}

# Disable memory capture (camera off)
nina_capture_off() {
    export NINA_CAPTURE_ENABLED=false
    echo "🔒 Nina memory capture disabled (camera off)"
}

# Set active context
nina_context() {
    if [[ -n "$1" ]]; then
        export NINA_CONTEXT="$1"
        echo "📁 Nina context set to: $NINA_CONTEXT"
    else
        echo "📁 Current Nina context: ${NINA_CONTEXT:-<none>}"
    fi
}

# Show current configuration
nina_status() {
    echo "Nina Memory Shell Hook Status:"
    echo "  Capture Enabled: ${NINA_CAPTURE_ENABLED:-false}"
    echo "  Active Context: ${NINA_CONTEXT:-<none>}"
    echo "  Memory Service: ${NINA_MEMORY_SERVICE_URL}"
    echo "  Auth Token: ${NINA_AUTH_TOKEN:+<set>}"
    echo "  Shell: $SHELL"
}

# Welcome message (optional, can be disabled)
if [[ "${NINA_QUIET:-false}" != "true" ]]; then
    echo "🧠 Nina memory capture initialized"
    echo "   Use 'nina_status' to view configuration"
    echo "   Use 'nina_capture_off' to disable capture"
    echo "   Use 'nina_context <name>' to set active context"
fi
