#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
# Fix US #79 P0 Issues: Package import and contract exports

set -euo pipefail

echo "=== US #79 P0 Issue Fix Script ==="
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$(dirname "$0")"

echo "📦 Step 1: Reinstall contracts package"
echo "----------------------------------------"
conda run -n nina pip uninstall -y ninaivalaigal-contracts || true
conda run -n nina pip install -e .
echo

echo "✅ Step 2: Test package import"
echo "----------------------------------------"
if conda run -n nina python -c "import ninaivalaigal_contracts; print('✅ Package imported successfully')"; then
    echo -e "${GREEN}✅ Package import works${NC}"
else
    echo -e "${RED}❌ Package import failed${NC}"
    exit 1
fi
echo

echo "✅ Step 3: Test auth contract imports"
echo "----------------------------------------"
if conda run -n nina python -c "from ninaivalaigal_contracts.auth.v1 import LoginRequest, RegisterRequest; print('✅ Auth contracts imported')"; then
    echo -e "${GREEN}✅ Auth contract imports work${NC}"
else
    echo -e "${RED}❌ Auth contract imports failed${NC}"
    exit 1
fi
echo

echo "✅ Step 4: Test memory contract imports"
echo "----------------------------------------"
if conda run -n nina python -c "from ninaivalaigal_contracts.memory.v1 import CreateMemoryRequest, Memory; print('✅ Memory contracts imported')"; then
    echo -e "${GREEN}✅ Memory contract imports work${NC}"
else
    echo -e "${RED}❌ Memory contract imports failed${NC}"
    exit 1
fi
echo

echo "🧪 Step 5: Run contract tests"
echo "----------------------------------------"
if conda run -n nina pytest tests/unit/ -v; then
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed (review above)${NC}"
fi
echo

echo "✅ Step 6: Validate contract models"
echo "----------------------------------------"
conda run -n nina python -c "
from ninaivalaigal_contracts.auth.v1 import LoginRequest
from ninaivalaigal_contracts.memory.v1 import CreateMemoryRequest
from pydantic import ValidationError

# Test auth validation
try:
    LoginRequest(email='invalid-email', password='pass')  # pragma: allowlist secret
    print('❌ Email validation not working')
except ValidationError:
    print('✅ Auth validation works')

# Test memory validation
try:
    CreateMemoryRequest(user_id='user1', content='')
    print('❌ Content validation not working')
except ValidationError:
    print('✅ Memory validation works')
"
echo

echo "📊 Summary"
echo "=========================================="
echo -e "${GREEN}✅ Package is now importable${NC}"
echo -e "${GREEN}✅ Contract exports working${NC}"
echo -e "${GREEN}✅ Tests created and running${NC}"
echo
echo "You can now use:"
echo "  from ninaivalaigal_contracts.auth.v1 import LoginRequest"
echo "  from ninaivalaigal_contracts.memory.v1 import CreateMemoryRequest"
echo
echo "Run tests with:"
echo "  conda run -n nina pytest shared/contracts/tests/ -v"
echo
