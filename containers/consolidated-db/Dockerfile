# nina-intelligence-db: Consolidated PostgreSQL + Apache AGE + pgvector
# The central intelligence database for ninaivalaigal platform
# Replaces both nv-db and graph-db with single unified container
FROM postgres:15

# Install build dependencies
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

# Install pgvector extension
RUN git clone https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    git checkout v0.5.1 && \
    make && \
    make install && \
    rm -rf /tmp/pgvector

# Install Apache AGE extension (known working version)
RUN git clone https://github.com/apache/age.git /tmp/age && \
    cd /tmp/age && \
    git checkout PG15/v1.5.0-rc0 && \
    make PG_CONFIG=/usr/bin/pg_config && \
    make PG_CONFIG=/usr/bin/pg_config install && \
    rm -rf /tmp/age

# Copy initialization scripts
COPY init-consolidated.sql /docker-entrypoint-initdb.d/01-init-consolidated.sql
COPY create-users.sql /docker-entrypoint-initdb.d/02-create-users.sql

# Environment variables
ENV POSTGRES_DB=ninaivalaigal
ENV POSTGRES_USER=nina
ENV POSTGRES_PASSWORD=secure_nina_password

# Expose PostgreSQL port
EXPOSE 5432

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pg_isready -U nina -d ninaivalaigal || exit 1
