FROM alpine:3.20

# Packages: pgbouncer + certs
RUN apk add --no-cache pgbouncer ca-certificates

# Create non-root user and group
RUN addgroup -S pgbouncer \
&& adduser -S -G pgbouncer -H -D -s /sbin/nologin pgbouncer

# Config
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
COPY userlist.txt /etc/pgbouncer/userlist.txt

# Runtime dirs + permissions
RUN mkdir -p /var/run/pgbouncer /var/log/pgbouncer /var/lib/pgbouncer \
&& chown -R pgbouncer:pgbouncer \
   /etc/pgbouncer /var/run/pgbouncer /var/log/pgbouncer /var/lib/pgbouncer

EXPOSE 6432

# Drop privileges permanently
USER pgbouncer

# Start PgBouncer
ENTRYPOINT ["pgbouncer", "/etc/pgbouncer/pgbouncer.ini"]
