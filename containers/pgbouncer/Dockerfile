FROM alpine:3.20
RUN apk add --no-cache pgbouncer ca-certificates
# Copy config in-image (no host mounts needed)
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
COPY userlist.txt /etc/pgbouncer/userlist.txt
EXPOSE 6432
ENTRYPOINT ["pgbouncer","/etc/pgbouncer/pgbouncer.ini"]
