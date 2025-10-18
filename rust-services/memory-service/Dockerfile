# syntax=docker/dockerfile:1

FROM rustlang/rust:nightly-bullseye AS builder
WORKDIR /app

# Create a dummy project structure to leverage Docker layer caching
COPY Cargo.toml Cargo.lock ./
COPY src ./src

# Build release binary
RUN cargo build --release

FROM debian:bullseye-slim
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ca-certificates \
        libssl1.1 \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/memory-service /usr/local/bin/memory-service

ENV RUST_LOG=info
ENV PORT=8000

EXPOSE 8000

CMD ["/usr/local/bin/memory-service"]
