# Stage 1: Build
FROM rustlang/rust:nightly-bullseye AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        pkg-config \
        libssl-dev \
        libpq-dev \
        ca-certificates \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Create dummy source to cache dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy actual source
COPY src ./src

# Build for release
RUN touch src/main.rs && \
    cargo build --release

# Stage 2: Runtime
FROM debian:bullseye-slim

# Install runtime dependencies (libssl1.1 for ring crate compatibility, libpq for PostgreSQL, wget for health check)
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        ca-certificates \
        libssl1.1 \
        libpq5 \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (Debian syntax)
RUN groupadd --gid 1000 memory && \
    useradd --uid 1000 --gid memory --shell /bin/bash --create-home memory

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/memory-service /app/memory-service

# Set ownership
RUN chown -R memory:memory /app

# Switch to non-root user
USER memory

# Expose port (internal)
EXPOSE 8000

# Health check (using wget - install if needed, or use curl)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Run the binary
CMD ["/app/memory-service"]
