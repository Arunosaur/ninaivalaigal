#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Pre-commit hook to validate SPDX headers in source files

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Find the repo root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Track failures
MISSING_COUNT=0
INVALID_COUNT=0
FAILED_FILES=()

echo "🔍 Checking SPDX headers in staged files..."

# Get list of staged Python, TypeScript, JavaScript, and Shell files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | \
    grep -E '\.(py|ts|tsx|js|jsx|sh|yml|yaml)$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo -e "${GREEN}✅ No source files staged for commit${NC}"
    exit 0
fi

# Function to check if file has SPDX header
check_spdx_header() {
    local file=$1
    local header_found=0
    local valid_license=0

    # Read first 10 lines of file
    head -n 10 "$file" | while IFS= read -r line; do
        if [[ $line =~ SPDX-License-Identifier ]]; then
            header_found=1

            # Check for valid license identifiers
            if [[ $line =~ (MIT|Apache-2\.0|Proprietary|Elastic-2\.0) ]]; then
                valid_license=1
            fi
        fi
    done

    # Check exit status
    if ! head -n 10 "$file" | grep -q "SPDX-License-Identifier"; then
        return 1  # Missing header
    fi

    if ! head -n 10 "$file" | grep -E "SPDX-License-Identifier.*( MIT|Apache-2\.0|Proprietary|Elastic-2\.0)" > /dev/null; then
        return 2  # Invalid license
    fi

    return 0  # Valid header
}

# Check each staged file
for file in $STAGED_FILES; do
    if [ ! -f "$file" ]; then
        continue
    fi

    # Skip certain directories
    if [[ $file =~ (node_modules|\.venv|venv|\.git|__pycache__|dist|build) ]]; then
        continue
    fi

    check_result=0
    check_spdx_header "$file" || check_result=$?

    case $check_result in
        1)
            echo -e "${RED}❌ Missing SPDX header: $file${NC}"
            MISSING_COUNT=$((MISSING_COUNT + 1))
            FAILED_FILES+=("$file")
            ;;
        2)
            echo -e "${YELLOW}⚠️  Invalid SPDX license: $file${NC}"
            INVALID_COUNT=$((INVALID_COUNT + 1))
            FAILED_FILES+=("$file")
            ;;
        0)
            # Valid header - silent success
            ;;
    esac
done

# Summary
echo ""
echo "========================================"
if [ $MISSING_COUNT -eq 0 ] && [ $INVALID_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ All staged files have valid SPDX headers${NC}"
    echo "========================================"
    exit 0
else
    echo -e "${RED}❌ SPDX header validation failed${NC}"
    echo "========================================"
    echo ""
    echo "Missing headers: $MISSING_COUNT"
    echo "Invalid licenses: $INVALID_COUNT"
    echo ""
    echo "Failed files:"
    for failed_file in "${FAILED_FILES[@]}"; do
        echo "  - $failed_file"
    done
    echo ""
    echo "To fix this:"
    echo "1. Run: python3 SPDX-header-inserter.py --path <directory>"
    echo "2. Or manually add SPDX header to each file"
    echo ""
    echo "Valid license identifiers:"
    echo "  - MIT (for frontend-*, packages/*, scripts/)"
    echo "  - Apache-2.0 (for cli/, sdk/)"
    echo "  - Proprietary (for server/*)"
    echo "  - Elastic-2.0 (for containers/, k8s/, terraform/)"
    echo ""
    echo "Example header (Python):"
    echo "  # SPDX-License-Identifier: MIT"
    echo "  # Copyright (c) 2025 Medhasys LLC"
    echo ""
    echo "Example header (TypeScript/JavaScript):"
    echo "  // SPDX-License-Identifier: MIT"
    echo "  // Copyright (c) 2025 Medhasys LLC"
    echo ""
    exit 1
fi
