FROM debian:12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    pgbouncer ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --system --no-create-home --shell /bin/false pgbouncer && \
    mkdir -p /etc/pgbouncer /var/log/pgbouncer && \
    chown -R pgbouncer:pgbouncer /etc/pgbouncer /var/log/pgbouncer

WORKDIR /etc/pgbouncer

USER pgbouncer

EXPOSE 6432

CMD ["pgbouncer", "/etc/pgbouncer/pgbouncer.ini"]
