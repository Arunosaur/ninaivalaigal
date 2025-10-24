#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Perform a lightweight readiness check against GraphOps before running mix workloads.

set -euo pipefail

if ! command -v grpcurl >/dev/null 2>&1; then
  echo "grpcurl is required on PATH" >&2
  exit 1
fi

TARGET=${TARGET:-"localhost:13398"}
SERVICE=${SERVICE:-"ninaivalaigal.graphops.v1.GraphOpsService"}
METHOD=${METHOD:-"ExecuteQuery"}
TRACE_ID=${TRACE_ID:-"graph-ready-check"}

read -r -d '' QUERY <<'EOF'
{
  "query": "MATCH (u:User {id: 'perf_user_001'}) RETURN u LIMIT 1",
  "timeout_ms": 2000,
  "trace_id": "graph-ready"
}
EOF

echo "🔍 Validating GraphOps readiness via $SERVICE/$METHOD @ $TARGET"

set -x
grpcurl -plaintext \
  -H "x-nv-trace-id: $TRACE_ID" \
  -d "$QUERY" \
  "$TARGET" "$SERVICE/$METHOD"
set +x

echo "✅ GraphOps readiness check completed"
