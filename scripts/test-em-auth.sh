#!/usr/bin/env bash
# Test eM sidecar authentication
set -euo pipefail

EM_PORT="${EM_PORT:-7070}"
MEM0_BASE="http://localhost:${EM_PORT}"
MEMORY_SHARED_SECRET="${MEMORY_SHARED_SECRET:-}"

log(){ printf "\033[1;35m[mem0-auth]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }
success(){ printf "\033[1;32m[pass]\033[0m %s\n" "$*"; }

need(){ command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

generate_hmac_token(){
    local secret="$1"
    local timestamp=$(date +%s)
    local signature=$(echo -n "$timestamp" | openssl dgst -sha256 -hmac "$secret" -hex | cut -d' ' -f2)
    echo "${timestamp}:${signature}"
}

test_health_endpoint(){
    log "Testing health endpoint (no auth required)..."

    local response=$(if ! curl -fsS "${MEM0_BASE}/health" >/dev/null 2>&1; then
  echo "eM is not running or not healthy"
  echo "   Start with: make with-em"
  exit 1
fi)
    local auth_status=$(echo "$response" | jq -r '.authentication // "unknown"')

    if [[ "$response" == *"ok"* ]]; then
        success "Health check passed"
        log "Authentication status: $auth_status"
        return 0
    else
        die "Health check failed: $response"
    fi
}

test_unauthenticated_access(){
    log "Testing unauthenticated access (should fail if auth enabled)..."

    local response=$(curl -s -w "%{http_code}" "${MEM0_BASE}/auth/test" || echo "000")
    local http_code="${response: -3}"

    if [[ -z "$MEMORY_SHARED_SECRET" ]]; then
        # Auth disabled - should succeed
        if [[ "$http_code" == "200" ]]; then
            success "Unauthenticated access allowed (auth disabled)"
            return 0
        else
            die "Unexpected response when auth disabled: $http_code"
        fi
    else
        # Auth enabled - should fail
        if [[ "$http_code" == "401" ]]; then
            success "Unauthenticated access properly blocked"
            return 0
        else
            die "Expected 401 but got: $http_code"
        fi
    fi
}

test_simple_secret_auth(){
    if [[ -z "$MEMORY_SHARED_SECRET" ]]; then
        log "Skipping simple secret test (no secret configured)"
        return 0
    fi

    log "Testing simple shared secret authentication..."

    local response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $MEMORY_SHARED_SECRET" \
        "$MEM0_BASE/auth/test")

    local http_code="${response: -3}"
    local body="${response%???}"

    if [[ "$http_code" == "200" ]]; then
        success "Simple secret authentication successful"
        log "Response: $(echo "$body" | jq -c '.')"
        return 0
    else
        die "Simple secret auth failed: $http_code - $body"
    fi
}

test_hmac_auth(){
    if [[ -z "$MEMORY_SHARED_SECRET" ]]; then
        log "Skipping HMAC test (no secret configured)"
        return 0
    fi

    log "Testing HMAC-based authentication..."

    local token=$(generate_hmac_token "$MEMORY_SHARED_SECRET")
    local response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $token" \
        "$MEM0_BASE/auth/test")

    local http_code="${response: -3}"
    local body="${response%???}"

    if [[ "$http_code" == "200" ]]; then
        success "HMAC authentication successful"
        log "Response: $(echo "$body" | jq -c '.')"
        return 0
    else
        die "HMAC auth failed: $http_code - $body"
    fi
}

test_context_headers(){
    if [[ -z "$MEMORY_SHARED_SECRET" ]]; then
        log "Skipping context test (no secret configured)"
        return 0
    fi

    log "Testing user context headers..."

    local response=$(curl -s \
        -H "Authorization: Bearer $MEMORY_SHARED_SECRET" \
        -H "X-User-Id: test-user-123" \
        -H "X-Team-Id: test-team-456" \
        -H "X-Org-Id: test-org-789" \
        "$MEM0_BASE/auth/test")

    local user_id=$(echo "$response" | jq -r '.context.user_id // "null"')
    local team_id=$(echo "$response" | jq -r '.context.team_id // "null"')
    local org_id=$(echo "$response" | jq -r '.context.org_id // "null"')

    if [[ "$user_id" == "test-user-123" && "$team_id" == "test-team-456" && "$org_id" == "test-org-789" ]]; then
        success "Context headers properly extracted"
        log "User: $user_id, Team: $team_id, Org: $org_id"
        return 0
    else
        die "Context extraction failed: user=$user_id, team=$team_id, org=$org_id"
    fi
}

test_memory_operations(){
    if [[ -z "$MEMORY_SHARED_SECRET" ]]; then
        log "Skipping memory operations test (no secret configured)"
        return 0
    fi

    log "Testing authenticated memory operations..."

    # Test remember endpoint
    local remember_response=$(curl -s \
        -H "Authorization: Bearer $MEMORY_SHARED_SECRET" \
        -H "X-User-Id: test-user" \
        -H "Content-Type: application/json" \
        -d '{"text": "Test memory for authentication"}' \
        "$MEM0_BASE/remember")

    local memory_id=$(echo "$remember_response" | jq -r '.id // "null"')

    if [[ "$memory_id" != "null" ]]; then
        success "Memory creation successful: $memory_id"
    else
        die "Memory creation failed: $remember_response"
    fi

    # Test recall endpoint
    local recall_response=$(curl -s \
        -H "Authorization: Bearer $MEMORY_SHARED_SECRET" \
        -H "X-User-Id: test-user" \
        "$MEM0_BASE/recall?q=test&k=5")

    local recall_ok=$(echo "$recall_response" | jq -r '.ok // false')

    if [[ "$recall_ok" == "true" ]]; then
        success "Memory recall successful"
    else
        die "Memory recall failed: $recall_response"
    fi
}

main(){
    need curl
    need jq
    need openssl

    log "mem0 Sidecar Authentication Test"
    log "Base URL: $MEM0_BASE"
    log "Auth Secret: $([ -n "$MEMORY_SHARED_SECRET" ] && echo "configured" || echo "not configured")"
    echo ""

    # Run tests
    test_health_endpoint
    test_unauthenticated_access
    test_simple_secret_auth
    test_hmac_auth
    test_context_headers
    test_memory_operations

    echo ""
    success "All authentication tests passed! 🎉"

    if [[ -z "$MEMORY_SHARED_SECRET" ]]; then
        log "⚠️  Consider setting MEMORY_SHARED_SECRET for production security"
    else
        log "✅ Authentication is properly configured and working"
    fi
}

main "$@"
