#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Seed the GraphOps benchmark dataset via the gRPC ExecuteQuery endpoint.
# This ensures the AGE graph hosted inside ninaivalaigal-dev-db
# mirrors the fixtures used by the benchmark mix workloads.

set -euo pipefail

if ! command -v grpcurl >/dev/null 2>&1; then
  echo "grpcurl is required on PATH" >&2
  exit 1
fi

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PAYLOAD=${PAYLOAD:-"$REPO_ROOT/benchmarks/graphops/perf_user_seed.json"}
TARGET=${TARGET:-"localhost:13398"}
SERVICE=${SERVICE:-"ninaivalaigal.graphops.v1.GraphOpsService"}
METHOD=${METHOD:-"ExecuteQuery"}
TRACE_ID=${TRACE_ID:-"seed-perf-graph"}

if [[ ! -f "$PAYLOAD" ]]; then
  echo "Seed payload not found: $PAYLOAD" >&2
  exit 1
fi

echo "🌱 Seeding perf graph via $SERVICE/$METHOD @ $TARGET"
echo "   payload: $PAYLOAD"

set -x
grpcurl -plaintext \
  -H "x-nv-trace-id: $TRACE_ID" \
  -d @"$PAYLOAD" \
  "$TARGET" "$SERVICE/$METHOD"
set +x

echo "✅ GraphOps seed completed"
