# syntax=docker/dockerfile:1

FROM rust:1.80-bullseye AS builder
WORKDIR /app

# Create a dummy project structure to leverage Docker layer caching
COPY Cargo.toml Cargo.lock ./
COPY src ./src

# Build release binary
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ca-certificates \
        libssl3 \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/memory-service /usr/local/bin/memory-service

ENV RUST_LOG=info
ENV PORT=8000

EXPOSE 8000

CMD ["/usr/local/bin/memory-service"]
