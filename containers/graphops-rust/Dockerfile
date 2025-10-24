# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Multi-stage Dockerfile for GraphOps Rust service
# SPEC-099: High-performance Apache AGE query execution

# syntax=docker/dockerfile:1.6

ARG RUST_VERSION=1.81

FROM --platform=$BUILDPLATFORM rust:${RUST_VERSION}-slim-bookworm AS builder

ARG TARGETPLATFORM
ARG TARGETARCH
ARG TARGETOS

WORKDIR /workspace

# Install build dependencies required for tonic-build (prost) and postgres
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        pkg-config \
        libssl-dev \
        libpq-dev \
        ca-certificates \
        curl \
        build-essential \
        protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Copy manifests early to leverage Docker layer caching
COPY rust-services/graphops/Cargo.toml rust-services/graphops/Cargo.lock rust-services/graphops/build.rs ./rust-services/graphops/

# Copy protobuf contracts required during build.rs execution
COPY shared/contracts ./shared/contracts

# Copy source code (excluding target directory to keep image small)
COPY rust-services/graphops/src ./rust-services/graphops/src
COPY rust-services/graphops/benches ./rust-services/graphops/benches
COPY rust-services/graphops/benchmarks ./rust-services/graphops/benchmarks
COPY rust-services/graphops/tests ./rust-services/graphops/tests

WORKDIR /workspace/rust-services/graphops

# Create proto directory for descriptor generation
RUN mkdir -p proto

# Ensure the correct compilation target is available when cross-compiling
RUN if [ "$TARGETARCH" = "arm64" ]; then rustup target add aarch64-unknown-linux-gnu; fi \
    && if [ "$TARGETARCH" = "amd64" ]; then rustup target add x86_64-unknown-linux-gnu; fi

# Build release binary (build.rs will generate proto/graphops_descriptor.bin)
RUN cargo build --release --bin graphops-service

FROM debian:bookworm-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ca-certificates \
        libssl3 \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled binary from builder stage (includes embedded descriptor from include_bytes!)
COPY --from=builder /workspace/rust-services/graphops/target/release/graphops-service /usr/local/bin/graphops

# Default environment configuration (can be overridden at runtime)
ENV RUST_LOG=info \
    GRAPHOPS_GRPC_ADDR=0.0.0.0:50051 \
    GRAPHOPS_METRICS_ADDR=0.0.0.0:9090

# Expose gRPC and metrics ports
EXPOSE 50051 9090

# Container health check leverages the lightweight CLI probe
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/graphops", "--health-check"]

ENTRYPOINT ["/usr/local/bin/graphops"]
