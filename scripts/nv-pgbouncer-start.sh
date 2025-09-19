set -euo pipefail
IMAGE="nina-pgbouncer:arm64"

# Build if missing
if ! container images | grep -q "^${IMAGE}\b"; then
    container build -t "${IMAGE}" -f containers/pgbouncer/Dockerfile containers/pgbouncer
fi

# (Re)start
container rm -f nv-pgbouncer >/dev/null 2>&1 || true
container run -d --name nv-pgbouncer -p 6432:6432 "${IMAGE}"

# Wait until ready
for i in {1..30}; do
  if psql "host=127.0.0.1 port=6432 dbname=testdb user=postgres password=${POSTGRES_PASSWORD:-test123}" \
      -c 'SHOW VERSION;' >/dev/null 2>&1; then
    echo "[ok] PgBouncer is ready."
    exit 0
  fi
  sleep 1
done

echo "[fail] PgBouncer did not become ready"; container logs nv-pgbouncer || true; exit 2
