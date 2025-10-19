#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Make scripts executable and run quick validation

echo "🔧 Setting up Task #29 completion scripts..."

# Make scripts executable
chmod +x /Users/swami/WorkSpace/ninaivalaigal/developer_a_task29_completion.sh
chmod +x /Users/swami/WorkSpace/ninaivalaigal/quick_task29_check.sh
chmod +x /Users/swami/WorkSpace/ninaivalaigal/rust-services/memory-service/benchmarks/wrk-benchmark.sh
chmod +x /Users/swami/WorkSpace/ninaivalaigal/rust-services/memory-service/benchmarks/performance-test.sh

echo "✅ Scripts are now executable"

# Run quick check
echo ""
echo "🚀 Running quick validation..."
/Users/swami/WorkSpace/ninaivalaigal/quick_task29_check.sh
