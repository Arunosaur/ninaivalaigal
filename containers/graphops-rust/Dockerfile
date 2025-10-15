# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Multi-stage Dockerfile for Rust GraphOps service
# SPEC-099: High-performance Apache AGE query execution

FROM rust:1.75-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    musl-dev \
    protobuf-dev \
    openssl-dev \
    pkgconfig

WORKDIR /app

# Copy dependency manifests
COPY rust-services/graphops/Cargo.toml rust-services/graphops/Cargo.lock ./

# Cache dependencies (build with dummy main)
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy source code
COPY rust-services/graphops/src ./src
COPY shared/contracts/graphops/v1/graphops.proto ./proto/

# Build application
RUN cargo build --release --bin graphops-service

# Runtime stage
FROM alpine:latest

RUN apk add --no-cache \
    ca-certificates \
    libgcc

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/graphops-service .

# Create non-root user
RUN addgroup -g 1000 graphops && \
    adduser -D -u 1000 -G graphops graphops && \
    chown -R graphops:graphops /app

USER graphops

# Expose gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["/app/graphops-service", "--health-check"]

ENTRYPOINT ["/app/graphops-service"]
