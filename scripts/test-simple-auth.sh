#!/bin/bash

# Simple Authentication Test
# Tests basic auth functionality with proper error handling

set -euo pipefail

API_BASE="http://localhost:13370"

echo "🧪 Simple Authentication Test"
echo "============================="

# Test 1: Health check
echo "1. Testing health endpoint..."
health_response=$(curl -s "$API_BASE/health")
echo "Health: $health_response"

# Test 2: Check what endpoints are available
echo -e "\n2. Testing available endpoints..."

# Test signup endpoint structure
echo "Testing signup endpoint availability..."
signup_test=$(curl -s -w "HTTP:%{http_code}" -X GET "$API_BASE/auth/signup/individual" || echo "HTTP:000")
echo "Signup endpoint test: $signup_test"

# Test login endpoint structure  
echo "Testing login endpoint availability..."
login_test=$(curl -s -w "HTTP:%{http_code}" -X GET "$API_BASE/auth/login" || echo "HTTP:000")
echo "Login endpoint test: $login_test"

# Test 3: Try to create a user with minimal data
echo -e "\n3. Testing user creation..."
simple_user='{
    "email": "simple@test.com",
    "password": "simplepass123",
    "name": "Simple User"
}'

echo "Attempting to create user..."
signup_response=$(curl -s -w "HTTP:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$simple_user" \
    "$API_BASE/auth/signup/individual" || echo "HTTP:000")

echo "Signup response: $signup_response"

# Test 4: Try to login with the user
echo -e "\n4. Testing login..."
login_data='{
    "email": "simple@test.com", 
    "password": "simplepass123"
}'

echo "Attempting login..."
login_response=$(curl -s -w "HTTP:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$login_data" \
    "$API_BASE/auth/login" || echo "HTTP:000")

echo "Login response: $login_response"

# Test 5: Test our new AI endpoints without auth (should get 401)
echo -e "\n5. Testing protected endpoints without auth..."

echo "Testing vendor admin endpoint..."
vendor_test=$(curl -s -w "HTTP:%{http_code}" "$API_BASE/vendor/admin/dashboard/overview" || echo "HTTP:000")
echo "Vendor admin: $vendor_test"

echo "Testing memory suggestions endpoint..."
suggestions_test=$(curl -s -w "HTTP:%{http_code}" "$API_BASE/memory/suggestions/algorithms" || echo "HTTP:000")
echo "Memory suggestions: $suggestions_test"

echo "Testing memory injection endpoint..."
injection_test=$(curl -s -w "HTTP:%{http_code}" "$API_BASE/memory/injection/triggers" || echo "HTTP:000")
echo "Memory injection: $injection_test"

echo -e "\n✅ Simple authentication test complete!"
echo "Expected results:"
echo "- Health: should return {\"status\":\"ok\"}"
echo "- Signup: should work or return user exists error"
echo "- Login: should return JWT token if signup worked"
echo "- Protected endpoints: should return HTTP:401 or HTTP:403"
