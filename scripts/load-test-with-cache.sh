#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
# scripts/load-test-with-cache.sh
# Purpose: Load test with identical queries to warm and trigger the cache

set -euo pipefail

if ! command -v grpcurl >/dev/null 2>&1; then
  echo "grpcurl is required for this script" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

GRPC_TARGET="${GRPC_TARGET:-127.0.0.1:50051}"
GRPC_METHOD="${GRPC_METHOD:-ninaivalaigal.graphops.v1.GraphOpsService/ExecuteQuery}"
PROTO_FILE="${PROTO_FILE:-${REPO_ROOT}/shared/contracts/graphops/v1/graphops.proto}"
PROTO_DIR="$(dirname "${PROTO_FILE}")"
PROTO_NAME="$(basename "${PROTO_FILE}")"
QUERY_PAYLOAD='{"query": "MATCH (n) RETURN n LIMIT 10"}'
TOTAL_REQUESTS="${TOTAL_REQUESTS:-1000}"
CONCURRENCY="${CONCURRENCY:-10}"

echo "Starting cache warm-up load test against ${GRPC_TARGET} (${GRPC_METHOD})"
echo "Total requests: ${TOTAL_REQUESTS}; concurrency: ${CONCURRENCY}"
echo

echo "Warming up cache..."
for _ in $(seq 1 10); do
  grpcurl -plaintext -import-path "${PROTO_DIR}" -proto "${PROTO_NAME}" -d "${QUERY_PAYLOAD}" \
    "${GRPC_TARGET}" "${GRPC_METHOD}" >/dev/null
done
echo "Cache warm-up complete."
echo

echo "Executing parallel load test..."
seq "${TOTAL_REQUESTS}" | xargs -P "${CONCURRENCY}" -I{} \
  grpcurl -plaintext -import-path "${PROTO_DIR}" -proto "${PROTO_NAME}" -d "${QUERY_PAYLOAD}" \
    "${GRPC_TARGET}" "${GRPC_METHOD}" >/dev/null

echo
echo "✅ Load test complete."
