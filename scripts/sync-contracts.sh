#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Sync stored contracts with live service specifications
# Task #79: Shared Contracts Layer (SPEC-100 Phase 0)

set -euo pipefail

CONTRACTS_DIR="shared/contracts"
LIVE_DIR="shared/contracts-live"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Syncing Contracts with Live Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to sync a single service contract
sync_contract() {
    local service_name=$1
    local live_file=$2
    local stored_file=$3

    echo "📋 Syncing ${service_name}..."

    if [ ! -f "$live_file" ]; then
        echo "   ⏭️  Skipped - no live contract available"
        return
    fi

    if [ ! -f "$stored_file" ]; then
        echo "   ⚠️  Warning - stored contract doesn't exist"
    fi

    # Backup existing contract
    if [ -f "$stored_file" ]; then
        cp "$stored_file" "${stored_file}.backup"
        echo "   💾 Backed up existing contract"
    fi

    # Copy live contract to stored location
    cp "$live_file" "$stored_file"
    echo "   ✅ Synced contract from live service"
    echo ""
}

# Sync all service contracts
sync_contract "Core API" \
    "${LIVE_DIR}/core-api-live.yaml" \
    "${CONTRACTS_DIR}/core-api/v1/openapi.yaml"

sync_contract "Business Service" \
    "${LIVE_DIR}/business-service-live.yaml" \
    "${CONTRACTS_DIR}/business-service/v1/openapi.yaml"

sync_contract "Admin/Vendor Service" \
    "${LIVE_DIR}/admin-vendor-live.yaml" \
    "${CONTRACTS_DIR}/admin-vendor-service/v1/openapi.yaml"

sync_contract "Graph/AI Service" \
    "${LIVE_DIR}/graph-service-live.yaml" \
    "${CONTRACTS_DIR}/graph-ai-service/v1/openapi.yaml"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Contract Sync Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Backup files created: *.backup"
echo "📝 Review changes: git diff ${CONTRACTS_DIR}"
echo ""
echo "🔍 Next steps:"
echo "   1. Review synced contracts for accuracy"
echo "   2. Validate with: python ci/validate-api-contracts.py"
echo "   3. Commit changes: git add ${CONTRACTS_DIR} && git commit"
echo ""
