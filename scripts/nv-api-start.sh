set -euo pipefail

# Find a local image that starts with nina-api and use its full Ref
API_REF="$(container images --format '{{.Ref}}' \
  | grep -E '^nina-api:[^|@]$' | head -n1 || true)"

if [ -z "$API_REF" ]; then
  # Build one if missing
  container build -t nina-api:arm64 -f containers/api/Dockerfile .
  API_REF="nina-api:arm64"
fi

DB_URL="${DATABASE_URL:-postgresql://postgres:${POSTGRES_PASSWORD:-test123}@127.0.0.1:5433/testdb}"

container rm -f nv-api >/dev/null 2>&1 || true
container run -d --name nv-api -e DATABASE_URL="${DB_URL}" -p 13370:8000 "${API_REF}"

# Health wait
for i in {1..30}; do
  if curl -sf http://localhost:13370/health >/dev/null; then
    echo "[ok] API is healthy"; exit 0
  fi
  sleep 1
done
echo "[fail] API health failed"; container logs nv-api || true; exit 1
