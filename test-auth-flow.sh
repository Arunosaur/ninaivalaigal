#!/bin/bash

# Complete Auth Flow Test Script
# Tests login → token validation → protected routes

BASE_URL="http://localhost:13370"
echo "🔐 Testing Complete Auth Flow"
echo "=============================="

# Step 1: Test auth health
echo ""
echo "1️⃣ Testing auth health..."
curl -s "$BASE_URL/auth-working/health" | jq .

# Step 2: Login (you'll need real credentials)
echo ""
echo "2️⃣ Testing login..."
echo "ℹ️  Replace with real credentials:"
echo "curl '$BASE_URL/auth-working/login?email=YOUR_EMAIL&password=YOUR_PASSWORD'"

# For demo, let's try with test credentials
LOGIN_RESPONSE=$(curl -s "$BASE_URL/auth-working/login?email=test@ninaivalaigal.com&password=test")
echo "Login response: $LOGIN_RESPONSE"

# Extract token (if login successful)
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.jwt_token // empty')

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo ""
    echo "✅ Login successful! Token: ${TOKEN:0:20}..."
    
    # Step 3: Test token validation
    echo ""
    echo "3️⃣ Testing token validation..."
    curl -s "$BASE_URL/auth-working/validate-token?token=$TOKEN" | jq .
    
    # Step 4: Test protected routes
    echo ""
    echo "4️⃣ Testing protected routes..."
    
    echo "📋 Profile:"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/protected/profile" | jq .
    
    echo ""
    echo "👥 Teams:"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/protected/teams" | jq .
    
    echo ""
    echo "🧠 Memory:"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/protected/memory" | jq .
    
    echo ""
    echo "📁 Contexts:"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/protected/contexts" | jq .
    
    echo ""
    echo "✅ Approvals:"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/protected/approval" | jq .
    
else
    echo "❌ Login failed or no token received"
    echo "💡 To test with real credentials:"
    echo "   1. Create a user account"
    echo "   2. Replace test credentials in this script"
    echo "   3. Run again"
fi

echo ""
echo "5️⃣ Testing unauthorized access (should fail)..."
curl -s "$BASE_URL/protected/profile" | jq .

echo ""
echo "🎉 Auth flow test complete!"
echo ""
echo "📚 Usage Examples:"
echo "=================="
echo ""
echo "JavaScript/Frontend:"
echo "const token = 'your-jwt-token';"
echo "fetch('/protected/profile', {"
echo "  headers: { 'Authorization': \`Bearer \${token}\` }"
echo "});"
echo ""
echo "cURL:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' $BASE_URL/protected/profile"
