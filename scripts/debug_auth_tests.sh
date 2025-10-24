#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Quick diagnostic script for auth test failures
#
# PORTABLE: Works on both macOS (BSD) and Linux (GNU) systems
# - Can be run locally on macOS during development
# - Can be run inside Linux containers for CI/testing
#
# Uses POSIX-compliant commands:
# - sed '$d' instead of head -n -1 (BSD compatible)
# - Standard curl/jq/tail commands

set -e

API_URL="${CORE_API_BASE_URL:-http://localhost:13370}"
DB_URL="${DATABASE_URL:-postgresql://nina:dev_password_change_in_production@localhost:6452/ninaivalaigal_dev}"

echo "🔍 Auth Test Diagnostics"
echo "========================"
echo ""

# Check API is running
echo "1. Checking API availability..."
if curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "   ✅ API is running at $API_URL"
else
    echo "   ❌ API not reachable at $API_URL"
    echo "   Start it with: python services/core-api/local_run.py"
    exit 1
fi
echo ""

# Test signup endpoint
echo "2. Testing signup endpoint..."
RANDOM_EMAIL="test_$(date +%s)@example.com"
SIGNUP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/signup/individual" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$RANDOM_EMAIL\", \"password\":\"StrongPass123!\", \"full_name\":\"Test User\"}")

SIGNUP_BODY=$(echo "$SIGNUP_RESPONSE" | sed '$d')  # Remove last line (portable: works on BSD/GNU)
SIGNUP_CODE=$(echo "$SIGNUP_RESPONSE" | tail -n 1)

echo "   Status code: $SIGNUP_CODE"
if [ "$SIGNUP_CODE" = "201" ]; then
    echo "   ✅ Signup working correctly"
elif [ "$SIGNUP_CODE" = "500" ]; then
    echo "   ❌ Signup returning 500 - check logs!"
    echo "   Response: $SIGNUP_BODY"
else
    echo "   ⚠️  Unexpected status: $SIGNUP_CODE"
    echo "   Response: $SIGNUP_BODY"
fi
echo ""

# Test duplicate email
echo "3. Testing duplicate email..."
DUP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/signup/individual" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$RANDOM_EMAIL\", \"password\":\"StrongPass123!\", \"full_name\":\"Test User\"}")

DUP_BODY=$(echo "$DUP_RESPONSE" | sed '$d')  # Portable across BSD/GNU
DUP_CODE=$(echo "$DUP_RESPONSE" | tail -n 1)
echo "   Status code: $DUP_CODE"
if [ "$DUP_CODE" = "409" ]; then
    echo "   ✅ Duplicate email returns 409 (Conflict)"
elif [ "$DUP_CODE" = "400" ]; then
    echo "   ⚠️  Duplicate email returns 400 (test expects 409 or 400, acceptable)"
elif [ "$DUP_CODE" = "500" ]; then
    echo "   ❌ Duplicate email returns 500 - HTTPException not preserved!"
    echo "   Response: $DUP_BODY"
else
    echo "   ⚠️  Unexpected status: $DUP_CODE"
fi
echo ""

# Test malformed JSON
echo "4. Testing malformed JSON..."
MALFORMED_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test","password":}' 2>/dev/null || echo -e "\n400")

MALFORMED_BODY=$(echo "$MALFORMED_RESPONSE" | sed '$d')  # Portable
MALFORMED_CODE=$(echo "$MALFORMED_RESPONSE" | tail -n 1)
echo "   Status code: $MALFORMED_CODE"
if [ "$MALFORMED_CODE" = "400" ]; then
    echo "   ✅ Malformed JSON returns 400"
elif [ "$MALFORMED_CODE" = "422" ]; then
    echo "   ❌ Malformed JSON returns 422 (test expects 400)"
    echo "   This is a FastAPI/Starlette design issue - complex to fix"
else
    echo "   ⚠️  Unexpected status: $MALFORMED_CODE"
fi
echo ""

# Test empty JSON payload
echo "5. Testing empty JSON payload..."
EMPTY_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{}')

EMPTY_BODY=$(echo "$EMPTY_RESPONSE" | sed '$d')  # Portable
EMPTY_CODE=$(echo "$EMPTY_RESPONSE" | tail -n 1)
echo "   Status code: $EMPTY_CODE"
if [ "$EMPTY_CODE" = "400" ]; then
    echo "   ✅ Empty payload returns 400"
elif [ "$EMPTY_CODE" = "422" ]; then
    echo "   ❌ Empty payload returns 422 (test expects 400)"
    echo "   Missing fields trigger validation error"
else
    echo "   ⚠️  Unexpected status: $EMPTY_CODE"
fi
echo ""

# Test token validation
echo "6. Testing invalid token..."
TOKEN_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/memory/health" \
  -H "Authorization: Bearer invalid_token_123")

TOKEN_BODY=$(echo "$TOKEN_RESPONSE" | sed '$d')  # Portable
TOKEN_CODE=$(echo "$TOKEN_RESPONSE" | tail -n 1)
echo "   Status code: $TOKEN_CODE"
if [ "$TOKEN_CODE" = "401" ]; then
    echo "   ✅ Invalid token returns 401"
elif [ "$TOKEN_CODE" = "404" ]; then
    echo "   ❌ Invalid token returns 404 (test expects 401)"
    echo "   This is a middleware order issue"
else
    echo "   ⚠️  Unexpected status: $TOKEN_CODE"
fi
echo ""

# Summary
echo "========================"
echo "📊 Summary"
echo "========================"
echo ""
echo "Expected improvements from current fixes:"
echo "- Signup 500 → 201: Check API logs for actual error"
echo "- Duplicate 500 → 409: Should work after signup fix"
echo "- JSON 422 → 400: Complex FastAPI issue, may skip"
echo "- Token 404 → 401: Middleware order issue, complex"
echo ""
echo "Next steps:"
echo "1. If signup returns 500, check: tail -100 core_api_13370.log | grep -i error"
echo "2. Clean test data: psql $DB_URL -c \"DELETE FROM users WHERE email LIKE '%@example.com';\""
echo "3. Restart API and re-run this diagnostic"
echo "4. Run full test suite: pytest tests/auth/ -v --tb=short"
echo ""
