#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Memory Service - Performance Benchmark with wrk
# Task #29: Performance Benchmarks
#
# wrk is recommended for macOS (especially M1/M2/M3) instead of Apache Bench

set -euo pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

# Configuration
readonly SERVICE_URL="${MEMORY_SERVICE_URL:-http://localhost:13393}"
readonly RESULTS_DIR="$(pwd)/benchmark-results"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$RESULTS_DIR"

echo ""
echo "═══════════════════════════════════════════════"
echo "  Memory Service - wrk Performance Benchmark"
echo "═══════════════════════════════════════════════"
echo ""

# Check prerequisites
if ! command -v wrk >/dev/null 2>&1; then
    log_warn "wrk not installed. Installing..."
    brew install wrk || {
        echo "Failed to install wrk. Please run: brew install wrk"
        exit 1
    }
fi

# Check service health
if ! curl -sf "$SERVICE_URL/health" > /dev/null; then
    echo "❌ Memory service not responding at $SERVICE_URL"
    exit 1
fi

log_success "Service health check passed"
echo ""

# Test 1: Light Load (10 connections, 10 seconds)
log_info "Test 1: Light Load (10 connections, 10s)"
wrk -t2 -c10 -d10s "$SERVICE_URL/health" \
    | tee "$RESULTS_DIR/light_load_${TIMESTAMP}.txt"
echo ""

# Test 2: Medium Load (50 connections, 30 seconds)
log_info "Test 2: Medium Load (50 connections, 30s)"
wrk -t4 -c50 -d30s "$SERVICE_URL/health" \
    | tee "$RESULTS_DIR/medium_load_${TIMESTAMP}.txt"
echo ""

# Test 3: Heavy Load (100 connections, 30 seconds)
log_info "Test 3: Heavy Load (100 connections, 30s)"
wrk -t8 -c100 -d30s "$SERVICE_URL/health" \
    | tee "$RESULTS_DIR/heavy_load_${TIMESTAMP}.txt"
echo ""

# Check connection stats after load
log_info "Connection Pool Stats After Load:"
curl -s "$SERVICE_URL/health" | jq '.database'
echo ""

# Generate summary
log_success "Benchmark complete!"
echo ""
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Performance Targets:"
echo "  - P95 Latency: < 30ms"
echo "  - Throughput: > 1,000 req/s"
echo "  - Failed requests: 0"
echo ""
echo "Next Steps for Developer A:"
echo "  1. Review latency percentiles in results"
echo "  2. Test authenticated endpoints with JWT"
echo "  3. Measure Redis cache hit rates"
echo "  4. Document findings in Task #29"
echo ""
