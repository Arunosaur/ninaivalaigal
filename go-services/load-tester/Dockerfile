# Developer A Task #37 - Load Tester Dockerfile
# Multi-stage build for optimal image size

# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /app

# Propagate target platform information from buildx
ARG TARGETOS
ARG TARGETARCH

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the binary for the requested target platform
RUN CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-amd64} go build \
    -ldflags="-w -s -X main.Version=$(git describe --tags --always --dirty)" \
    -o load-tester .

# Final stage
FROM alpine:3.18

# Install runtime dependencies
RUN apk --no-cache add ca-certificates tzdata curl jq

# Create non-root user
RUN addgroup -g 1001 -S loadtester && \
    adduser -u 1001 -S loadtester -G loadtester

# Set working directory
WORKDIR /app

# Copy binary from builder stage
COPY --from=builder /app/load-tester /usr/local/bin/load-tester

# Copy example scenarios
COPY scenarios/ /app/scenarios/

# Set ownership
RUN chown -R loadtester:loadtester /app

# Switch to non-root user
USER loadtester

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD load-tester --version || exit 1

# Default command
ENTRYPOINT ["load-tester"]
CMD ["--help"]

# Metadata
LABEL maintainer="Developer A <developer-a@ninaivalaigal.com>" \
      description="High-performance load testing tool for Ninaivalaigal services" \
      version="1.0.0" \
      org.opencontainers.image.title="Ninaivalaigal Load Tester" \
      org.opencontainers.image.description="Load testing tool for microservice performance validation" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Ninaivalaigal Project" \
      org.opencontainers.image.licenses="MIT"
