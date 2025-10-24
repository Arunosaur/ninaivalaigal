#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
set -euo pipefail

if [[ -z "${1-}" ]]; then
  echo "Usage: $0 <load-tester-binary>" >&2
  echo "Example: $0 ./go-services/load-tester/bin/load-tester" >&2
  exit 1
fi

if [[ -z "${NINA_TOKEN-}" ]]; then
  echo "Please export NINA_TOKEN with a valid JWT (see scripts/generate_jwt_token.py)." >&2
  exit 1
fi

BINARY=$1
SCENARIO_JSON="benchmarks/memory/recall_write.json"
TMP_JSON=$(mktemp)
trap 'rm -f "$TMP_JSON"' EXIT

SCENARIO_CONCURRENCY=${SCENARIO_CONCURRENCY:-60}
SCENARIO_DURATION=${SCENARIO_DURATION:-120s}
SCENARIO_RATE_LIMIT=${SCENARIO_RATE_LIMIT:-25000}
SCENARIO_THINK=${SCENARIO_THINK:-50ms}

# Substitute token placeholder
sed "s/{{TOKEN}}/$NINA_TOKEN/g" "$SCENARIO_JSON" > "$TMP_JSON"

export LOAD_TESTER_SCENARIO_TOKEN_SOURCE="US86-realistic-mix"

"$BINARY" scenario "$TMP_JSON" \
  --concurrency "$SCENARIO_CONCURRENCY" \
  --duration "$SCENARIO_DURATION" \
  --rate-limit "$SCENARIO_RATE_LIMIT" \
  --think-time "$SCENARIO_THINK"
