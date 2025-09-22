# Production Apache AGE + PostgreSQL for ninaivalaigal
# Multi-architecture support: linux/amd64, linux/arm64
FROM postgres:15

# Install build dependencies for Apache AGE
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        postgresql-server-dev-15 \
        curl \
        ca-certificates \
        flex \
        bison && \
    rm -rf /var/lib/apt/lists/*

# Use a known working Apache AGE version for PostgreSQL 15
RUN git clone https://github.com/apache/age.git /tmp/age && \
    cd /tmp/age && \
    git checkout PG15/v1.5.0-rc0 && \
    make PG_CONFIG=/usr/bin/pg_config && \
    make PG_CONFIG=/usr/bin/pg_config install && \
    rm -rf /tmp/age

# Copy initialization scripts
COPY init-age.sql /docker-entrypoint-initdb.d/01-init-age.sql
COPY init-schema.sql /docker-entrypoint-initdb.d/02-init-schema.sql

# Set default environment variables
ENV POSTGRES_DB=ninaivalaigal_graph
ENV POSTGRES_USER=graphuser
ENV POSTGRES_PASSWORD=graphpass

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1

# Expose PostgreSQL port
EXPOSE 5432
