#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Generator script to create standardized service start scripts
# Follows CONTAINERIZATION_STANDARD.md and ports.nv.yaml

set -euo pipefail

SERVICE_NAME=$1
SERVICE_PORT=$2
CONTAINER_PORT=${3:-8000}
SERVICE_TYPE=${4:-python}  # python, rust, go

SCRIPT_NAME="nv-${SERVICE_NAME}-start.sh"
OUTPUT_FILE="scripts/${SCRIPT_NAME}"

cat > "$OUTPUT_FILE" << 'SCRIPT_TEMPLATE'
#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Start {SERVICE_NAME} service with Apple Container CLI
# Follows CONTAINERIZATION_STANDARD.md and ports.nv.yaml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting ninaivalaigal {SERVICE_NAME}"
echo "==========================================="

# Load environment variables from configs/env-{env}.env (STANDARDS COMPLIANCE)
NINA_ENV=${NINA_ENV:-dev}
ENV_FILE="$PROJECT_ROOT/configs/env-${NINA_ENV}.env"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    echo "✅ Loaded environment from $ENV_FILE"
else
    echo "⚠️  $ENV_FILE not found, using defaults"
    NINA_ENV=${NINA_ENV:-dev}
fi

# Set defaults
NINA_DB_USER=${NINA_DB_USER:-nina}
NINA_DB_PASSWORD=${NINA_DB_PASSWORD:-dev_password_change_in_production}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-{SERVICE_NAME}"
IMAGE_NAME="nina-{SERVICE_NAME}:arm64"
PORT_EXTERNAL={SERVICE_PORT}
PORT_INTERNAL={CONTAINER_PORT}

echo ""
echo "📊 Configuration:"
echo "   Environment: $NINA_ENV"
echo "   Container: $CONTAINER_NAME"
echo "   Image: $IMAGE_NAME"
echo "   Port: $PORT_EXTERNAL → $PORT_INTERNAL"
echo ""

# Discover dependency IPs
echo "🔍 Discovering service IPs..."

DB_CONTAINER="ninaivalaigal-${NINA_ENV}-db"
DB_IP=$(container inspect "$DB_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$DB_IP" ] || [ "$DB_IP" = "null" ]; then
    echo "❌ Database container not found: $DB_CONTAINER"
    exit 1
fi
echo "   ✅ Database: $DB_IP:5432"

REDIS_CONTAINER="ninaivalaigal-${NINA_ENV}-redis"
REDIS_IP=$(container inspect "$REDIS_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$REDIS_IP" ] || [ "$REDIS_IP" = "null" ]; then
    echo "   ⚠️  Redis not found (optional)"
    REDIS_IP="127.0.0.1"
fi
echo "   ✅ Redis: $REDIS_IP:6379"

DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${DB_IP}:5432/ninaivalaigal_${NINA_ENV}"
REDIS_URL="redis://${REDIS_IP}:6379/0"

echo ""

# Stop existing container
echo "🛑 Stopping existing container (if any)..."
container stop "$CONTAINER_NAME" 2>/dev/null || true
container rm "$CONTAINER_NAME" 2>/dev/null || true
echo ""

# Start container
echo "🚀 Starting {SERVICE_NAME} container..."
container run -d \
    --name "$CONTAINER_NAME" \
    --memory 1g \
    --cpus 1 \
    -p "${PORT_EXTERNAL}:${PORT_INTERNAL}" \
    -e NINA_ENV="$NINA_ENV" \
    -e DATABASE_URL="$DATABASE_URL" \
    -e REDIS_URL="$REDIS_URL" \
    -e LOG_LEVEL="${LOG_LEVEL:-info}" \
    "$IMAGE_NAME"

echo "✅ Container started: $CONTAINER_NAME"
echo ""

# Wait for health
echo "⏳ Waiting for service to be healthy..."
sleep 5

for i in {1..10}; do
    if curl -sf "http://localhost:${PORT_EXTERNAL}/health" > /dev/null 2>&1; then
        echo "✅ {SERVICE_NAME} is healthy!"
        break
    fi
    echo "   Waiting... ($i/10)"
    sleep 2
done

echo ""
echo "✅ {SERVICE_NAME} started successfully!"
echo "   Health: http://localhost:${PORT_EXTERNAL}/health"
echo "   Logs: container logs -f $CONTAINER_NAME"
SCRIPT_TEMPLATE

# Replace placeholders
sed -i.bak "s/{SERVICE_NAME}/$SERVICE_NAME/g" "$OUTPUT_FILE"
sed -i.bak "s/{SERVICE_PORT}/$SERVICE_PORT/g" "$OUTPUT_FILE"
sed -i.bak "s/{CONTAINER_PORT}/$CONTAINER_PORT/g" "$OUTPUT_FILE"
rm -f "${OUTPUT_FILE}.bak"

chmod +x "$OUTPUT_FILE"
echo "✅ Created: $OUTPUT_FILE"
