# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC

# Multi-stage Dockerfile for Rust microservices
# Used by: graphops-service
#
# Build: docker build -f docker/templates/rust-service.Dockerfile -t graphops-service:tag .
# Run: docker run -p 50051:50051 -p 9090:9090 graphops-service:tag

ARG RUST_VERSION=1.75

# ============================================================================
# Stage 1: Planner - Create recipe for dependencies
# ============================================================================
FROM rust:${RUST_VERSION}-alpine AS planner

WORKDIR /build

# Install cargo-chef
RUN apk add --no-cache musl-dev && \
    cargo install cargo-chef

# Copy manifests
COPY rust-services/graphops/Cargo.toml rust-services/graphops/Cargo.lock ./

# Prepare recipe
RUN cargo chef prepare --recipe-path recipe.json

# ============================================================================
# Stage 2: Builder - Build dependencies and application
# ============================================================================
FROM rust:${RUST_VERSION}-alpine AS builder

LABEL stage=builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache \
    musl-dev \
    postgresql-dev \
    openssl-dev \
    openssl-libs-static

# Install cargo-chef
RUN cargo install cargo-chef

# Copy recipe from planner
COPY --from=planner /build/recipe.json recipe.json

# Build dependencies (cached layer)
RUN cargo chef cook --release --recipe-path recipe.json

# Copy source code
COPY rust-services/graphops ./
COPY shared/contracts/graphops ./proto

# Build application
RUN cargo build --release --bin graphops-service && \
    strip target/release/graphops-service

# ============================================================================
# Stage 3: Runtime - Minimal production image
# ============================================================================
FROM alpine:3.18

# Metadata
LABEL maintainer="platform@medhasys.com" \
      version="1.0.0" \
      description="GraphOps Rust microservice" \
      org.opencontainers.image.source="https://github.com/Arunosaur/ninaivalaigal"

# Install runtime dependencies
RUN apk add --no-cache \
    postgresql-libs \
    libgcc \
    ca-certificates && \
    rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/target/release/graphops-service /app/graphops-service

# Ensure binary is executable
RUN chmod +x /app/graphops-service

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/app/graphops-service", "--health-check"] || exit 1

# Expose ports
EXPOSE 50051 9090

# Run service
ENTRYPOINT ["/app/graphops-service"]
