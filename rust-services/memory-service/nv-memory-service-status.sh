#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Display the status of the Rust memory service container

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/../../.env.dev" ]; then
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/../../.env.dev"
fi

NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-memory-service"

container list | grep "$CONTAINER_NAME" || {
    echo "$CONTAINER_NAME is not running"
    exit 1
}
