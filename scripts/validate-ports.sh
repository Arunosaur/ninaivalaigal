#!/usr/bin/env bash
# Validate Port Bindings Against Canonical Matrix
# Reads config/ports.nv.yaml and validates actual port bindings

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$ROOT_DIR/config/ports.nv.yaml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect runtime and environment
RUNTIME="${1:-apple}"
ENVIRONMENT="${2:-dev}"

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          Port Validation Against Canonical Matrix V2                ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Runtime: ${RUNTIME}"
echo "Environment: ${ENVIRONMENT}"
echo ""

# Function to extract port from YAML
get_expected_port() {
    local service=$1
    # Use yq if available, otherwise grep/awk
    if command -v yq &> /dev/null; then
        yq eval ".matrix.${RUNTIME}.${ENVIRONMENT}.${service}" "$CONFIG_FILE"
    else
        # Fallback to grep/awk parsing
        grep -A 20 "${RUNTIME}:" "$CONFIG_FILE" | \
        grep -A 10 "${ENVIRONMENT}:" | \
        grep "${service}:" | \
        awk '{print $2}'
    fi
}

# Function to check if port is listening
check_port() {
    local port=$1
    lsof -nP -iTCP:"$port" -sTCP:LISTEN &> /dev/null
}

# Function to get process listening on port
get_port_process() {
    local port=$1
    lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | tail -1 | awk '{print $1}'
}

# Services to validate
SERVICES=("postgresql" "pgbouncer" "redis" "api" "ui_external" "ui_internal" "em")
SERVICE_NAMES=("PostgreSQL" "PgBouncer" "Redis" "API" "Customer UI" "Admin Console" "Enhanced Memory")

echo "=== Port Binding Validation ==="
echo ""

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

for i in "${!SERVICES[@]}"; do
    service="${SERVICES[$i]}"
    service_name="${SERVICE_NAMES[$i]}"

    # Get expected port from config
    expected_port=$(get_expected_port "$service")

    if [[ -z "$expected_port" ]] || [[ "$expected_port" == "null" ]]; then
        echo -e "${YELLOW}⚠️  ${service_name}: No port defined in matrix${NC}"
        ((WARNINGS++))
        continue
    fi

    ((TOTAL_CHECKS++))

    # Check if port is actually listening
    if check_port "$expected_port"; then
        process=$(get_port_process "$expected_port")
        echo -e "${GREEN}✅ ${service_name}: Port ${expected_port} listening ($process)${NC}"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}❌ ${service_name}: Port ${expected_port} NOT listening${NC}"
        ((FAILED_CHECKS++))
    fi
done

echo ""
echo "=== Container Name Validation ==="
echo ""

# Check container names match pattern
CONTAINERS=$(container list 2>/dev/null | grep ninaivalaigal || echo "")

if [[ -z "$CONTAINERS" ]]; then
    echo -e "${RED}❌ No ninaivalaigal containers running${NC}"
    ((FAILED_CHECKS++))
else
    # Expected container names (no runtime suffix!)
    # Container names are by environment only: ninaivalaigal-{env}-{service}
    EXPECTED_CONTAINERS=(
        "ninaivalaigal-${ENVIRONMENT}-db"
        "ninaivalaigal-${ENVIRONMENT}-pgbouncer"
        "ninaivalaigal-${ENVIRONMENT}-redis"
        "ninaivalaigal-${ENVIRONMENT}-api"
        "ninaivalaigal-${ENVIRONMENT}-ui-customer"
        "ninaivalaigal-${ENVIRONMENT}-ui-admin"
        "ninaivalaigal-${ENVIRONMENT}-em"
    )

    for expected in "${EXPECTED_CONTAINERS[@]}"; do
        if echo "$CONTAINERS" | grep -q "^$expected "; then
            echo -e "${GREEN}✅ Container found: ${expected}${NC}"
        else
            # Check if it's optional (EM)
            if [[ "$expected" =~ "em" ]]; then
                echo -e "${YELLOW}⚠️  Optional container missing: ${expected}${NC}"
                ((WARNINGS++))
            else
                echo -e "${RED}❌ Required container missing: ${expected}${NC}"
                ((FAILED_CHECKS++))
            fi
        fi
    done
fi

echo ""
echo "=== Port Collision Check ==="
echo ""

# Check for unexpected ports in our range
UNEXPECTED_PORTS=0
for port_range in "5432-5699" "6379-6699" "8081-8499" "13370-13699"; do
    start_port=$(echo "$port_range" | cut -d'-' -f1)
    end_port=$(echo "$port_range" | cut -d'-' -f2)

    # Get all listening ports in range
    listening_ports=$(lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | \
                     awk '{print $9}' | \
                     grep -oE "\\*:[0-9]+" | \
                     cut -d':' -f2 | \
                     awk -v start="$start_port" -v end="$end_port" '$1 >= start && $1 <= end' || true)

    if [[ -n "$listening_ports" ]]; then
        while IFS= read -r port; do
            # Check if this port is expected
            is_expected=false
            for service in "${SERVICES[@]}"; do
                expected=$(get_expected_port "$service")
                if [[ "$port" == "$expected" ]]; then
                    is_expected=true
                    break
                fi
            done

            if [[ "$is_expected" == "false" ]]; then
                process=$(get_port_process "$port")
                echo -e "${YELLOW}⚠️  Unexpected port in reserved range: ${port} ($process)${NC}"
                ((UNEXPECTED_PORTS++))
                ((WARNINGS++))
            fi
        done <<< "$listening_ports"
    fi
done

if [[ $UNEXPECTED_PORTS -eq 0 ]]; then
    echo -e "${GREEN}✅ No port collisions detected${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          Validation Summary                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "Total Checks:    ${TOTAL_CHECKS}"
echo -e "${GREEN}Passed:          ${PASSED_CHECKS}${NC}"
echo -e "${RED}Failed:          ${FAILED_CHECKS}${NC}"
echo -e "${YELLOW}Warnings:        ${WARNINGS}${NC}"
echo ""

if [[ $FAILED_CHECKS -gt 0 ]]; then
    echo -e "${RED}❌ Port validation FAILED${NC}"
    echo ""
    echo "To fix port mismatches, run:"
    echo "  ./scripts/fix-ports-spec-086.sh"
    echo ""
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Port validation passed with warnings${NC}"
    exit 0
else
    echo -e "${GREEN}✅ All ports validated successfully!${NC}"
    echo ""
    echo "Your stack is fully compliant with SPEC-086 / Port Matrix V2"
    exit 0
fi
