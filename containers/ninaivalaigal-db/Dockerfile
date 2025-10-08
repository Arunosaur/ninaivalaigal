# Ninaivalaigal Production Database Image
# PostgreSQL 15 + All Required Extensions
# Platform: linux/arm64 and linux/amd64

FROM postgres:15-bookworm

LABEL org.opencontainers.image.source=https://github.com/arunosaur/ninaivalaigal
LABEL org.opencontainers.image.description="Ninaivalaigal PostgreSQL with pgvector, AGE, and all extensions"
LABEL org.opencontainers.image.version="1.0.0"

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        postgresql-server-dev-15 \
        curl \
        ca-certificates \
        libssl-dev \
        pkg-config \
        cmake \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector (v0.5.1 - stable for both ARM64 and x86_64)
RUN cd /tmp && \
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make clean && \
    make OPTFLAGS="" && \
    make install && \
    cd / && \
    rm -rf /tmp/pgvector

# Install Apache AGE (v1.5.0-rc0 - proven stable)
RUN cd /tmp && \
    git clone --branch PG15/v1.5.0-rc0 https://github.com/apache/age.git && \
    cd age && \
    make PG_CONFIG=/usr/bin/pg_config && \
    make PG_CONFIG=/usr/bin/pg_config install && \
    cd / && \
    rm -rf /tmp/age

# Install pg_cron (for scheduled tasks - SPEC-071)
RUN cd /tmp && \
    git clone https://github.com/citusdata/pg_cron.git && \
    cd pg_cron && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/pg_cron

# Install pg_stat_statements, auto_explain, pgAudit via apt (Core extensions)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-15-pgaudit \
        postgresql-15-repack \
        postgresql-15-cron \
    && rm -rf /var/lib/apt/lists/*

# Install pg_similarity (for RAG/GraphOps - SPEC-041)
RUN cd /tmp && \
    git clone https://github.com/eulerto/pg_similarity.git && \
    cd pg_similarity && \
    USE_PGXS=1 make && \
    USE_PGXS=1 make install && \
    cd / && \
    rm -rf /tmp/pg_similarity

# Install citext (case-insensitive text - SPEC-002)
# Already included in PostgreSQL contrib

# Copy initialization scripts
COPY ./init-extensions.sql /docker-entrypoint-initdb.d/01-init-extensions.sql
COPY ./init-config.sql /docker-entrypoint-initdb.d/02-init-config.sql

# Configure PostgreSQL for extensions
RUN echo "shared_preload_libraries = 'pg_stat_statements,auto_explain,pg_cron,pgaudit'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "pg_stat_statements.track = all" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "auto_explain.log_min_duration = '1s'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "cron.database_name = 'postgres'" >> /usr/share/postgresql/postgresql.conf.sample

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} || exit 1

# Labels for multi-arch builds
LABEL org.opencontainers.image.arch="arm64,amd64"

EXPOSE 5432
