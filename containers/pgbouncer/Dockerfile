FROM alpine:3.20

# Packages: pgbouncer + certs
RUN apk add --no-cache pgbouncer ca-certificates \
&& addgroup -S pgbouncer \
&& adduser -S -G pgbouncer -H -D -s /sbin/nologin pgbouncer \
&& mkdir -p /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer /var/lib/pgbouncer \
&& chown -R pgbouncer:pgbouncer /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer /var/lib/pgbouncer

# Install gettext for envsubst
RUN apk add --no-cache gettext

# Create pgbouncer.ini.template with templating
RUN echo '[databases]' > /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'nina = host=${DB_HOST} port=5432 dbname=nina pool_mode=session' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo '' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo '[pgbouncer]' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'listen_addr = 0.0.0.0' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'listen_port = 6432' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'auth_type = trust' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'auth_file = /etc/pgbouncer/userlist.txt' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'admin_users = postgres' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'logfile = /var/log/pgbouncer/pgbouncer.log' >> /etc/pgbouncer/pgbouncer.ini.template \
&& echo 'pidfile = /var/lib/pgbouncer/pgbouncer.pid' >> /etc/pgbouncer/pgbouncer.ini.template

# Create userlist.txt with MD5 hash
RUN echo '"nina" "md5c5c6bdc297551f8464af199238dbcee4"' > /etc/pgbouncer/userlist.txt

USER pgbouncer
EXPOSE 6432
ENTRYPOINT ["/bin/sh","-c","envsubst < /etc/pgbouncer/pgbouncer.ini.template > /etc/pgbouncer/pgbouncer.ini && exec pgbouncer /etc/pgbouncer/pgbouncer.ini"]
