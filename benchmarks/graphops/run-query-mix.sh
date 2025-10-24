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

BINARY=$1
TARGET=${TARGET:-localhost:13398}
SERVICE=${SERVICE:-ninaivalaigal.graphops.v1.GraphOpsService}
METHOD=${METHOD:-ExecuteQuery}
DURATION=${DURATION:-120s}
PER_QUERY_CONCURRENCY=${PER_QUERY_CONCURRENCY:-20}
PER_QUERY_RPS=${PER_QUERY_RPS:-500}
GRPC_HEADERS=${GRPC_HEADERS:-}

PAYLOAD_DIR=${PAYLOAD_DIR:-benchmarks/graphops/queries}
PAYLOADS=()
while IFS= read -r -d '' file; do
  PAYLOADS+=("$file")
done < <(find "$PAYLOAD_DIR" -maxdepth 1 -name '*.json' -print0 | sort -z)

if [[ ${#PAYLOADS[@]} -eq 0 ]]; then
  echo "No payloads found in $PAYLOAD_DIR" >&2
  exit 1
fi

echo "Running GraphOps query mix against $TARGET"
echo "Payload count: ${#PAYLOADS[@]}"
echo "Duration per stream: $DURATION"
echo "Per-query concurrency: $PER_QUERY_CONCURRENCY"
echo "Per-query RPS: $PER_QUERY_RPS"
echo

PIDS=()
for payload in "${PAYLOADS[@]}"; do
  echo "→ Launching load for $(basename "$payload")"
  CMD=("$BINARY" grpc "$TARGET" \
    --service "$SERVICE" \
    --method "$METHOD" \
    --data-file "$payload" \
    --duration "$DURATION" \
    --concurrency "$PER_QUERY_CONCURRENCY" \
    --rps "$PER_QUERY_RPS" \
    --timeout 5s)

  if [[ -n "$GRPC_HEADERS" ]]; then
    IFS=',' read -r -a header_array <<< "$GRPC_HEADERS"
    for header in "${header_array[@]}"; do
      CMD+=(--header "$header")
    done
  fi

  "${CMD[@]}" &
  PIDS+=($!)
  sleep 1
 done

status=0
for pid in "${PIDS[@]}"; do
  if ! wait "$pid"; then
    status=1
  fi
 done

exit $status
