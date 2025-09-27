#!/bin/bash
# 🧬 ninaivalaigal API Test Collection - curl Commands
# Comprehensive test suite for auth endpoints

set -e  # Exit on any error

# Configuration
BASE_URL="http://localhost:13370"
CONTENT_TYPE="application/json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_TOTAL=0

# Helper function to run test
run_test() {
    local test_name="$1"
    local expected_status="$2"
    local curl_cmd="$3"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -e "${BLUE}🧪 Test $TESTS_TOTAL: $test_name${NC}"

    # Run curl and capture status code
    local status_code
    status_code=$(eval "$curl_cmd" -w "%{http_code}" -s -o /dev/null)

    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS - Status: $status_code${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL - Expected: $expected_status, Got: $status_code${NC}"
    fi
    echo
}

# Helper function to run test with output
run_test_with_output() {
    local test_name="$1"
    local expected_status="$2"
    local curl_cmd="$3"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -e "${BLUE}🧪 Test $TESTS_TOTAL: $test_name${NC}"

    # Run curl and capture both output and status
    local response
    local status_code
    response=$(eval "$curl_cmd" -w "\\n%{http_code}" -s)
    status_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)

    echo "Response: $body"

    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS - Status: $status_code${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL - Expected: $expected_status, Got: $status_code${NC}"
    fi
    echo
}

echo -e "${YELLOW}🚀 Starting ninaivalaigal API Test Suite${NC}"
echo "Base URL: $BASE_URL"
echo "=========================================="
echo

# ===== HEALTH CHECK TESTS =====
echo -e "${YELLOW}🏥 HEALTH CHECK TESTS${NC}"

run_test_with_output "Health Check" "200" \
    "curl -X GET '$BASE_URL/health'"

run_test "API Documentation" "200" \
    "curl -X GET '$BASE_URL/docs'"

run_test "OpenAPI Schema" "200" \
    "curl -X GET '$BASE_URL/openapi.json'"

# ===== AUTHENTICATION TESTS =====
echo -e "${YELLOW}🔐 AUTHENTICATION TESTS${NC}"

# Valid login test (will fail with 401 for non-existent user, which is expected)
run_test "Valid Login Format" "401" \
    "curl -X POST '$BASE_URL/auth/login' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"test@example.com\",\"password\":\"testpassword123\"}'"

# Missing email test
run_test "Login Missing Email" "422" \
    "curl -X POST '$BASE_URL/auth/login' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"password\":\"testpassword123\"}'"

# Invalid email format test
run_test "Login Invalid Email Format" "400" \
    "curl -X POST '$BASE_URL/auth/login' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"not-an-email\",\"password\":\"testpassword123\"}'"

# Empty credentials test
run_test "Login Empty Credentials" "400" \
    "curl -X POST '$BASE_URL/auth/login' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"\",\"password\":\"\"}'"

# ===== SIGNUP TESTS =====
echo -e "${YELLOW}📝 SIGNUP TESTS${NC}"

# Valid signup test (might fail if user exists, but format should be correct)
run_test "Valid Individual Signup Format" "201" \
    "curl -X POST '$BASE_URL/auth/signup/individual' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"newuser$(date +%s)@example.com\",\"password\":\"strongpassword123\",\"full_name\":\"John Doe\"}'"

# Weak password test
run_test "Signup Weak Password" "400" \
    "curl -X POST '$BASE_URL/auth/signup/individual' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"weakpass@example.com\",\"password\":\"123\",\"full_name\":\"Weak Password User\"}'"

# Invalid email test
run_test "Signup Invalid Email" "400" \
    "curl -X POST '$BASE_URL/auth/signup/individual' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"invalid-email\",\"password\":\"validpassword123\",\"full_name\":\"Invalid Email User\"}'"

# Missing required fields test
run_test "Signup Missing Fields" "422" \
    "curl -X POST '$BASE_URL/auth/signup/individual' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"incomplete@example.com\"}'"

# ===== SECURITY TESTS =====
echo -e "${YELLOW}🔒 SECURITY TESTS${NC}"

# SQL injection attempt (should be handled safely)
run_test "SQL Injection Attempt" "400" \
    "curl -X POST '$BASE_URL/auth/login' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"\\'; DROP TABLE users; --\",\"password\":\"test123\"}'"

# XSS attempt (should be sanitized)
run_test "XSS Attempt" "400" \
    "curl -X POST '$BASE_URL/auth/login' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"<script>alert(\\\"xss\\\")</script>@example.com\",\"password\":\"test123\"}'"

# Unicode characters test
run_test "Unicode Characters" "401" \
    "curl -X POST '$BASE_URL/auth/login' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"tëst@éxample.com\",\"password\":\"tëstpässwörd123\"}'"

# Very long input test
run_test "Very Long Input" "400" \
    "curl -X POST '$BASE_URL/auth/login' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"email\":\"verylongemailaddressthatexceedsnormallimitsandtestsvalidation@example.com\",\"password\":\"verylongpasswordthatmightcauseissuesifnothandledproperly123456789\"}'"

# ===== TEST ENDPOINTS =====
echo -e "${YELLOW}🧪 TEST ENDPOINTS${NC}"

# Test endpoint
run_test_with_output "Auth Test Endpoint" "200" \
    "curl -X POST '$BASE_URL/auth/test' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"test_data\":\"Hello from curl\",\"timestamp\":\"$(date -Iseconds)\"}'"

# Login test endpoint
run_test_with_output "Login Test Endpoint" "200" \
    "curl -X POST '$BASE_URL/auth/login-test' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{}'"

# ===== PERFORMANCE TESTS =====
echo -e "${YELLOW}⚡ PERFORMANCE TESTS${NC}"

# Rate limiting test (rapid fire requests)
echo "Testing rate limiting with 5 rapid requests..."
for i in {1..5}; do
    run_test "Rate Limit Test $i" "401" \
        "curl -X POST '$BASE_URL/auth/login' \
         -H 'Content-Type: $CONTENT_TYPE' \
         -d '{\"email\":\"ratelimit@example.com\",\"password\":\"testpassword123\"}'"
done

# ===== ORGANIZATION TESTS =====
echo -e "${YELLOW}🏢 ORGANIZATION TESTS${NC}"

# Organization signup test
run_test "Organization Signup Format" "201" \
    "curl -X POST '$BASE_URL/auth/signup/organization' \
     -H 'Content-Type: $CONTENT_TYPE' \
     -d '{\"organization_name\":\"Test Company $(date +%s)\",\"admin_email\":\"admin$(date +%s)@testcompany.com\",\"admin_password\":\"adminpassword123\",\"admin_full_name\":\"Admin User\",\"industry\":\"Technology\",\"size\":\"small\"}'"

# ===== FINAL RESULTS =====
echo
echo "=========================================="
echo -e "${YELLOW}📊 TEST RESULTS SUMMARY${NC}"
echo -e "Total Tests: $TESTS_TOTAL"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$((TESTS_TOTAL - TESTS_PASSED))${NC}"
echo -e "Success Rate: $(( TESTS_PASSED * 100 / TESTS_TOTAL ))%"

if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check the output above.${NC}"
    exit 1
fi
