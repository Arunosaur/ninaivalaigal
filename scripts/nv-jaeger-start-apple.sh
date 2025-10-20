#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start Jaeger for distributed tracing using Apple Container CLI (Task #84)

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Starting Jaeger Distributed Tracing (Apple Container CLI)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration
CONTAINER_NAME="ninaivalaigal-dev-jaeger"
IMAGE_NAME="jaegertracing/all-in-one:1.51"

# Ports (from docker-compose.jaeger.yml)
OTLP_GRPC_PORT=4317      # Primary OTLP gRPC endpoint
OTLP_HTTP_PORT=4318      # OTLP HTTP endpoint
JAEGER_UI_PORT=16686     # Jaeger UI
JAEGER_HTTP_PORT=14268   # Jaeger HTTP collector
JAEGER_GRPC_PORT=14250   # Jaeger gRPC
ZIPKIN_PORT=9411         # Zipkin compatibility

# Stop existing container if running
if container list | grep -q "$CONTAINER_NAME"; then
    echo "🛑 Stopping existing $CONTAINER_NAME..."
    container stop "$CONTAINER_NAME" || true
    container rm "$CONTAINER_NAME" || true
    sleep 2
fi

# Start Jaeger container
echo ""
echo "🚀 Starting Jaeger..."
container run -d \
  --name "$CONTAINER_NAME" \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -e COLLECTOR_OTLP_ENABLED=true \
  -e SPAN_STORAGE_TYPE=memory \
  -e MEMORY_MAX_TRACES=10000 \
  -e QUERY_BASE_PATH=/ \
  -e LOG_LEVEL=info \
  -p "${OTLP_GRPC_PORT}:4317" \
  -p "${OTLP_HTTP_PORT}:4318" \
  -p "${JAEGER_UI_PORT}:16686" \
  -p "${JAEGER_HTTP_PORT}:14268" \
  -p "${JAEGER_GRPC_PORT}:14250" \
  -p "${ZIPKIN_PORT}:9411" \
  --cpus 2 \
  --memory 2g \
  "$IMAGE_NAME"

# Wait for Jaeger to be ready
echo ""
echo "⏳ Waiting for Jaeger to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f "http://localhost:${JAEGER_UI_PORT}/" >/dev/null 2>&1; then
        echo "   ✅ Jaeger is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "   ⚠️  Jaeger took longer than expected to start"
    echo "   Check logs: container logs $CONTAINER_NAME"
fi

# Get container IP
JAEGER_IP=$(container list | grep "$CONTAINER_NAME" | awk '{print $6}')

# Show status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Jaeger Started Successfully"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Service Info:"
echo "   Container:  $CONTAINER_NAME"
echo "   IP:         $JAEGER_IP"
echo "   Image:      $IMAGE_NAME"
echo ""
echo "🔌 Endpoints:"
echo "   OTLP gRPC:  localhost:${OTLP_GRPC_PORT}  ← Use this for tracing"
echo "   OTLP HTTP:  localhost:${OTLP_HTTP_PORT}"
echo "   Jaeger UI:  http://localhost:${JAEGER_UI_PORT}"
echo "   Jaeger gRPC: localhost:${JAEGER_GRPC_PORT}"
echo "   Jaeger HTTP: localhost:${JAEGER_HTTP_PORT}"
echo "   Zipkin:     localhost:${ZIPKIN_PORT}"
echo ""
echo "🔗 Container Info:"
echo "   Name:       $CONTAINER_NAME"
echo "   IP:         $JAEGER_IP"
echo "   Network:    Default (container networking)"
echo ""
echo "🧪 Quick Test:"
echo "   # Check health"
echo "   curl http://localhost:${JAEGER_UI_PORT}/"
echo ""
echo "   # View in browser"
echo "   open http://localhost:${JAEGER_UI_PORT}"
echo ""
echo "   # View logs"
echo "   container logs $CONTAINER_NAME"
echo ""
echo "   # Check traces"
echo "   curl http://localhost:${JAEGER_UI_PORT}/api/services"
echo ""
