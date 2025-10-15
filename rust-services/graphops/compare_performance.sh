#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.

set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PY_BASELINE="$PROJECT_ROOT/benchmarks/python_graphops_baseline.py"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL not set – cannot run comparison." >&2
  exit 1
fi

echo "=== Python Baseline ==="
python3 "$PY_BASELINE"

echo

echo "=== Rust Implementation ==="
cargo bench --bench graphops_benchmark --manifest-path "$PROJECT_ROOT/Cargo.toml"

echo

echo "=== Reminder ==="
echo "Use the generated outputs to compute improvement percentages (target >5x)."
