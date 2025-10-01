#!/bin/bash
# Test All 9 Runtime/Environment Combinations
# Validates that all combinations work and share data correctly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
RESULTS=()

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Testing All 9 Runtime/Environment Combinations           ║"
echo "║  Validating Cross-Runtime Data Sharing                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" == "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $message"
        ((PASSED_TESTS++))
        RESULTS+=("✅ $message")
    elif [ "$status" == "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC}: $message"
        ((FAILED_TESTS++))
        RESULTS+=("❌ $message")
    elif [ "$status" == "SKIP" ]; then
        echo -e "${YELLOW}⚠️  SKIP${NC}: $message"
        RESULTS+=("⚠️  $message")
    else
        echo -e "${BLUE}ℹ️  INFO${NC}: $message"
    fi
    ((TOTAL_TESTS++))
}

# Function to test a runtime/environment combination
test_combination() {
    local runtime=$1
    local env=$2
    local compose_file=$3
    local postgres_port=$4
    local redis_port=$5
    local api_port=$6

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  Testing: $runtime / $env"
    echo "  Compose: $compose_file"
    echo "  Ports: PG=$postgres_port, Redis=$redis_port, API=$api_port"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    # Check if compose file exists
    if [ ! -f "$compose_file" ]; then
        print_status "SKIP" "$runtime/$env - Compose file not found"
        return
    fi

    # Start the stack
    echo "Starting $runtime/$env..."
    if NINA_ENV=$env POSTGRES_PORT=$postgres_port REDIS_PORT=$redis_port API_PORT=$api_port \
       docker-compose -f "$compose_file" up -d > /dev/null 2>&1; then
        print_status "PASS" "$runtime/$env - Stack started"
    else
        print_status "FAIL" "$runtime/$env - Failed to start stack"
        return
    fi

    # Wait for services
    echo "Waiting for services (30s)..."
    sleep 30

    # Check PostgreSQL
    local db_container=$(docker ps --filter "name=ninaivalaigal.*$env.*db" --format "{{.Names}}" | head -1)
    if [ -n "$db_container" ]; then
        if docker exec "$db_container" pg_isready -U nina > /dev/null 2>&1; then
            print_status "PASS" "$runtime/$env - PostgreSQL healthy"

            # Test data operations
            if docker exec "$db_container" psql -U nina -d "ninaivalaigal_$env" -c \
               "CREATE TABLE IF NOT EXISTS test_$runtime (id SERIAL PRIMARY KEY, data TEXT);
                INSERT INTO test_$runtime (data) VALUES ('$runtime-$env-$(date +%s)') RETURNING *;" \
               > /dev/null 2>&1; then
                print_status "PASS" "$runtime/$env - PostgreSQL write successful"
            else
                print_status "FAIL" "$runtime/$env - PostgreSQL write failed"
            fi
        else
            print_status "FAIL" "$runtime/$env - PostgreSQL unhealthy"
        fi
    else
        print_status "FAIL" "$runtime/$env - PostgreSQL container not found"
    fi

    # Check Redis
    local redis_container=$(docker ps --filter "name=ninaivalaigal.*$env.*redis" --format "{{.Names}}" | head -1)
    if [ -n "$redis_container" ]; then
        if docker exec "$redis_container" redis-cli -a secure_nina_password ping 2>/dev/null | grep -q "PONG"; then
            print_status "PASS" "$runtime/$env - Redis healthy"

            # Test data operations
            if docker exec "$redis_container" redis-cli -a secure_nina_password \
               SET "test_${runtime}_${env}" "$runtime-$env-$(date +%s)" > /dev/null 2>&1; then
                print_status "PASS" "$runtime/$env - Redis write successful"
            else
                print_status "FAIL" "$runtime/$env - Redis write failed"
            fi
        else
            print_status "FAIL" "$runtime/$env - Redis unhealthy"
        fi
    else
        print_status "FAIL" "$runtime/$env - Redis container not found"
    fi

    # Check API
    if curl -s "http://localhost:$api_port/health" | grep -q "ok"; then
        print_status "PASS" "$runtime/$env - API responding"
    else
        print_status "FAIL" "$runtime/$env - API not responding"
    fi

    # Check data directory
    if [ -d "./data/postgres_$env" ] && [ "$(ls -A ./data/postgres_$env)" ]; then
        print_status "PASS" "$runtime/$env - Data directory populated"
    else
        print_status "FAIL" "$runtime/$env - Data directory empty"
    fi

    # Stop the stack
    echo "Stopping $runtime/$env..."
    NINA_ENV=$env docker-compose -f "$compose_file" down > /dev/null 2>&1

    echo ""
}

# Test data sharing between runtimes
test_data_sharing() {
    local env=$1

    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║  Testing Data Sharing in $env Environment                 "
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    # Start Docker, create data
    echo "1. Starting Docker/$env and creating test data..."
    NINA_ENV=$env docker-compose -f compose.docker.yml up -d > /dev/null 2>&1
    sleep 30

    local db_container=$(docker ps --filter "name=ninaivalaigal.*$env.*db" --format "{{.Names}}" | head -1)
    docker exec "$db_container" psql -U nina -d "ninaivalaigal_$env" -c \
        "CREATE TABLE IF NOT EXISTS sharing_test (id SERIAL PRIMARY KEY, runtime VARCHAR(50), timestamp TIMESTAMP DEFAULT NOW());
         INSERT INTO sharing_test (runtime) VALUES ('docker') RETURNING *;" \
        > /dev/null 2>&1

    local docker_count=$(docker exec "$db_container" psql -U nina -d "ninaivalaigal_$env" -t -c \
        "SELECT COUNT(*) FROM sharing_test;" 2>/dev/null | tr -d ' ')

    NINA_ENV=$env docker-compose -f compose.docker.yml down > /dev/null 2>&1

    # Start Apple CLI, check if it sees Docker's data
    echo "2. Starting Apple CLI/$env and checking for Docker's data..."
    NINA_ENV=$env docker-compose -f compose.apple.dev.yml up -d > /dev/null 2>&1
    sleep 30

    db_container=$(docker ps --filter "name=ninaivalaigal.*$env.*db" --format "{{.Names}}" | head -1)
    local apple_count=$(docker exec "$db_container" psql -U nina -d "ninaivalaigal_$env" -t -c \
        "SELECT COUNT(*) FROM sharing_test;" 2>/dev/null | tr -d ' ')

    if [ "$docker_count" == "$apple_count" ]; then
        print_status "PASS" "Data sharing $env - Apple CLI sees Docker's data"
    else
        print_status "FAIL" "Data sharing $env - Apple CLI doesn't see Docker's data (Docker: $docker_count, Apple: $apple_count)"
    fi

    # Add data from Apple CLI
    docker exec "$db_container" psql -U nina -d "ninaivalaigal_$env" -c \
        "INSERT INTO sharing_test (runtime) VALUES ('apple-cli');" \
        > /dev/null 2>&1

    NINA_ENV=$env docker-compose -f compose.apple.dev.yml down > /dev/null 2>&1

    # Start Docker again, check if it sees Apple CLI's data
    echo "3. Starting Docker/$env again and checking for Apple CLI's data..."
    NINA_ENV=$env docker-compose -f compose.docker.yml up -d > /dev/null 2>&1
    sleep 30

    db_container=$(docker ps --filter "name=ninaivalaigal.*$env.*db" --format "{{.Names}}" | head -1)
    local final_count=$(docker exec "$db_container" psql -U nina -d "ninaivalaigal_$env" -t -c \
        "SELECT COUNT(*) FROM sharing_test;" 2>/dev/null | tr -d ' ')

    if [ "$final_count" -gt "$docker_count" ]; then
        print_status "PASS" "Data sharing $env - Docker sees Apple CLI's data"
    else
        print_status "FAIL" "Data sharing $env - Docker doesn't see Apple CLI's data"
    fi

    NINA_ENV=$env docker-compose -f compose.docker.yml down > /dev/null 2>&1

    echo ""
}

# Main test execution
cd /Users/swami/WorkSpace/ninaivalaigal

echo "Starting comprehensive 9-combination test..."
echo ""

# Test Matrix: 3 runtimes × 3 environments = 9 combinations
# Format: test_combination runtime env compose_file postgres_port redis_port api_port

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Phase 1: Testing All 9 Combinations                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"

# Dev Environment
test_combination "Docker" "dev" "compose.docker.yml" "5432" "6379" "13370"
test_combination "Colima" "dev" "compose.colima.yml" "5442" "6389" "13380"
test_combination "Apple-CLI" "dev" "compose.apple.dev.yml" "5452" "6399" "13390"

# Test Environment
test_combination "Docker" "test" "compose.docker.yml" "5532" "6479" "13470"
test_combination "Colima" "test" "compose.colima.yml" "5542" "6489" "13480"
test_combination "Apple-CLI" "test" "compose.apple.dev.yml" "5552" "6499" "13490"

# Prod Environment
test_combination "Docker" "prod" "compose.docker.yml" "5632" "6579" "13570"
test_combination "Colima" "prod" "compose.colima.yml" "5642" "6589" "13580"
test_combination "Apple-CLI" "prod" "compose.apple.dev.yml" "5652" "6599" "13590"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Phase 2: Testing Cross-Runtime Data Sharing              ║"
echo "╚═══════════════════════════════════════════════════════════╝"

# Test data sharing in each environment
test_data_sharing "dev"
test_data_sharing "test"
test_data_sharing "prod"

# Summary
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  TEST SUMMARY                                              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Total Tests:  $TOTAL_TESTS"
echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
echo -e "${RED}Failed:       $FAILED_TESTS${NC}"
echo ""

# Detailed results
echo "Detailed Results:"
for result in "${RESULTS[@]}"; do
    echo "  $result"
done

echo ""
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ ALL TESTS PASSED!                                     ║${NC}"
    echo -e "${GREEN}║  All 9 combinations validated successfully                ║${NC}"
    echo -e "${GREEN}║  Cross-runtime data sharing confirmed                     ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ SOME TESTS FAILED                                     ║${NC}"
    echo -e "${RED}║  Please review the failures above                         ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
