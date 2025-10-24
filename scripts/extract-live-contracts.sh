#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Extract live OpenAPI specifications from running services
# Task #79: Shared Contracts Layer (SPEC-100 Phase 0)

set -euo pipefail

OUTPUT_DIR="shared/contracts-live"
mkdir -p "$OUTPUT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Extracting Live OpenAPI Contracts"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to extract OpenAPI from a service
extract_openapi() {
    local service_name=$1
    local service_url=$2
    local output_file="${OUTPUT_DIR}/${service_name}-live.json"

    echo "📡 Extracting from ${service_name}..."
    echo "   URL: ${service_url}"

    if curl -sf "${service_url}/openapi.json" -o "$output_file" 2>/dev/null; then
        # Convert JSON to YAML for easier diff
        python3 -c "import json, yaml, sys; yaml.dump(json.load(open('$output_file')), sys.stdout, default_flow_style=False)" > "${output_file%.json}.yaml"
        echo "   ✅ Saved to ${output_file%.json}.yaml"
    else
        echo "   ❌ Failed to extract (service may not have OpenAPI endpoint)"
    fi
    echo ""
}

# Extract from all services
extract_openapi "core-api" "http://localhost:13390"
extract_openapi "memory-service" "http://localhost:13393"
extract_openapi "graph-service" "http://localhost:13394"
extract_openapi "business-service" "http://localhost:13391"
extract_openapi "admin-vendor" "http://localhost:13392"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Live Contract Extraction Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Live contracts saved to: ${OUTPUT_DIR}/"
echo ""
echo "🔍 Next steps:"
echo "   1. Compare live contracts with existing specs"
echo "   2. Identify contract drift"
echo "   3. Update contracts to match reality"
echo ""
