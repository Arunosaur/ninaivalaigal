# syntax=docker/dockerfile:1
# Rust Memory Service - Production Dockerfile
# Follows: docs/standards/CONTAINERIZATION_STANDARD.md

# ============================================================================
# Stage 1: Builder - Compile Rust binary with static linking
# ============================================================================
FROM rustlang/rust:nightly-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    musl-dev \
    postgresql-dev \
    openssl-dev \
    openssl-libs-static \
    pkgconfig

WORKDIR /build

# Copy dependency manifests and benchmarks first for layer caching
COPY Cargo.toml Cargo.lock ./
COPY benches ./benches

# Create dummy main to cache dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy actual source code
COPY src ./src

# Touch main.rs to force rebuild
RUN touch src/main.rs

# Build release binary with musl for static linking
RUN cargo build --release

# Strip binary to reduce size
RUN strip target/release/memory-service

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM alpine:3.18

# Install runtime dependencies only
RUN apk add --no-cache \
    ca-certificates \
    libpq \
    libgcc \
    && rm -rf /var/cache/apk/*

# Create non-root user for security
RUN addgroup -g 1000 nina && \
    adduser -D -u 1000 -G nina nina

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/target/release/memory-service /usr/local/bin/memory-service

# Ensure binary is executable
RUN chmod +x /usr/local/bin/memory-service

# Switch to non-root user
USER nina

# Health check (requires health endpoint at /health)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["/bin/sh", "-c", "wget -q --spider http://localhost:${PORT:-8000}/health || exit 1"]

# Expose service port (internal container port)
EXPOSE 8000

# Set default environment
ENV RUST_LOG=info
ENV PORT=8000

# Run service
CMD ["/usr/local/bin/memory-service"]
