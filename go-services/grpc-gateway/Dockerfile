# syntax=docker/dockerfile:1
# gRPC Gateway - Production Dockerfile
# Follows: docs/standards/CONTAINERIZATION_STANDARD.md

# ============================================================================
# Stage 1: Builder - Compile Go binary
# ============================================================================
FROM golang:1.24-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git

WORKDIR /build

# Copy dependency manifests first for layer caching
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build static binary (no CGO) and respect target platform when provided.
ARG TARGETOS=linux
ARG TARGETARCH=arm64
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
  go build -trimpath -ldflags="-s -w" -o /build/grpc-gateway ./

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM alpine:3.18

# Install runtime dependencies only
RUN apk --no-cache add ca-certificates tzdata

# Create non-root user for security (aligned with standard: UID 1000)
RUN addgroup -g 1000 nina && \
    adduser -D -u 1000 -G nina nina

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/grpc-gateway .

# Ensure binary is executable
RUN chmod +x /app/grpc-gateway

# Change ownership to non-root user
RUN chown -R nina:nina /app

# Switch to non-root user
USER nina

# Expose canonical port from ports.nv.yaml (grpc_gateway: 13395)
EXPOSE 13395

# Health check (standard port 13395)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:13395/health || exit 1

# Set default environment
ENV GATEWAY_PORT=13395

# Run the gateway
CMD ["./grpc-gateway"]
