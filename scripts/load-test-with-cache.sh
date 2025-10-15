#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
# scripts/load-test-with-cache.sh
# Purpose: Load test with identical queries to warm and trigger the cache

set -euo pipefail

ENDPOINT="http://localhost:8080/query"
QUERY='{"query": "MATCH (n) RETURN n LIMIT 10"}'
TOTAL_REQUESTS=1000
CONCURRENCY=10

echo "Starting cache warm-up load test..."
echo "Sending ${TOTAL_REQUESTS} requests with concurrency ${CONCURRENCY} to ${ENDPOINT}"
echo

echo "Warming up cache..."
for _ in $(seq 1 10); do
  curl -s -X POST "${ENDPOINT}" \
    -H "Content-Type: application/json" \
    -d "${QUERY}" > /dev/null
done
echo "Cache warm-up complete."
echo

echo "Executing parallel load test..."
seq "${TOTAL_REQUESTS}" | xargs -P "${CONCURRENCY}" -I{} \
  curl -s -X POST "${ENDPOINT}" \
    -H "Content-Type: application/json" \
    -d "${QUERY}" > /dev/null

echo
echo "✅ Load test complete."
