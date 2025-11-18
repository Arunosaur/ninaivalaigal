# Ninaivalaigal CLI Tools Dockerfile
# Developer A Task #38 - Multi-stage build for production deployment

# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata make

# Set working directory
WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download && go mod verify

# Copy source code
COPY . .

# Build the application (ARM64 for Apple Container CLI)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o nina .

# Verify the binary
RUN ./nina --version

# Production stage
FROM alpine:3.18

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    tzdata \
    curl \
    jq \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 nina && \
    adduser -D -u 1001 -G nina nina

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/nina /usr/local/bin/nina

# Copy configuration templates
COPY --from=builder /build/*.yaml /app/ 2>/dev/null || true

# Create directories for user
RUN mkdir -p /home/nina/.nina /app/logs /app/config && \
    chown -R nina:nina /home/nina /app

# Switch to non-root user
USER nina

# Create default configuration
RUN nina config init --example || true

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD nina --version || exit 1

# Set environment variables
ENV NINA_OUTPUT_COLORS=true
ENV NINA_OUTPUT_FORMAT=table
ENV PATH="/usr/local/bin:${PATH}"

# Labels for metadata
LABEL maintainer="Ninaivalaigal Team <dev@ninaivalaigal.com>"
LABEL version="1.0.0"
LABEL description="Comprehensive CLI tools for Ninaivalaigal services"
LABEL org.opencontainers.image.title="Ninaivalaigal CLI Tools"
LABEL org.opencontainers.image.description="Command-line interface for managing Ninaivalaigal microservices"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created="2025-10-18"
LABEL org.opencontainers.image.source="https://github.com/Arunosaur/ninaivalaigal"
LABEL org.opencontainers.image.licenses="MIT"

# Expose default port for metrics (if running server mode)
EXPOSE 9090

# Volume for configuration and data
VOLUME ["/home/nina/.nina", "/app/logs"]

# Default command
ENTRYPOINT ["nina"]
CMD ["--help"]
