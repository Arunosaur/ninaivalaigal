#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
set -euo pipefail

OUTPUT_DIR=${1:-benchmarks/results}
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_FILE="$OUTPUT_DIR/resource-usage-$TIMESTAMP.txt"

cat <<EOF >"$OUT_FILE"
# Resource snapshot captured at $TIMESTAMP
# Commands: docker stats --no-stream, sysctl vm.swapusage
EOF

echo "\n## docker stats (GraphOps + Memory Service)" >>"$OUT_FILE"
docker stats --no-stream ninaivalaigal-dev-graph-service ninaivalaigal-dev-memory-service >>"$OUT_FILE" 2>&1 || echo "docker stats failed" >>"$OUT_FILE"

echo "\n## Host CPU (top -l 1 -stats pid,command,cpu,mem)" >>"$OUT_FILE"
(top -l 1 -stats pid,command,cpu,mem | head -n 20) >>"$OUT_FILE" 2>&1 || true

echo "\n## Swap usage" >>"$OUT_FILE"
sysctl vm.swapusage >>"$OUT_FILE" 2>&1 || true

echo "Resource snapshot saved to $OUT_FILE"
