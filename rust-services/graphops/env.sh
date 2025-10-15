#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

# Source this file to load GraphOps development environment
# Usage: source env.sh  OR  . env.sh

export DATABASE_URL="postgresql://nina:dev_password_change_in_production@192.168.64.137:6432/ninaivalaigal_dev"  # pragma: allowlist secret
export GRAPHOPS_GRAPH="ninaivalaigal_intelligence"
export GRAPHOPS_PY_ITERATIONS="10"
export RUST_LOG="graphops_service=debug,info"

echo "✅ GraphOps environment loaded:"
echo "   DATABASE_URL: ${DATABASE_URL%%@*}@***"  # Hide credentials
echo "   GRAPHOPS_GRAPH: $GRAPHOPS_GRAPH"
