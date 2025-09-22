#!/usr/bin/env bash
# Start ninaivalaigal admin UI with Apple `container`
set -euo pipefail

CONTAINER_NAME="${UI_CONTAINER_NAME:-nv-ui}"
IMAGE="${UI_IMAGE:-ninaivalaigal-ui:latest}"
HOST_PORT="${UI_PORT:-8080}"
WAIT_SEC="${WAIT_SEC:-30}"

log(){ printf "\033[1;33m[ui]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

need(){ command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

ensure_container(){ container system status >/dev/null 2>&1 || container system start; }

stop_existing(){
  if container list | awk '{print $NF}' | grep -qx "$CONTAINER_NAME"; then
    log "Stopping existing $CONTAINER_NAME…"
    container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    container delete "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

build_image(){
  log "Building UI image: $IMAGE"

  # Check if client directory exists
  if [[ ! -d "client" ]]; then
    log "Creating placeholder client directory for development..."
    mkdir -p client

    # Create minimal package.json
    cat > client/package.json <<EOF
{
  "name": "ninaivalaigal-ui",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "build": "mkdir -p dist && echo 'Building UI...' && cp -r public/* dist/ 2>/dev/null || echo 'No public files found'"
  },
  "devDependencies": {}
}
EOF

    # Create minimal build output
    mkdir -p client/dist client/public
    cat > client/public/index.html <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ninaivalaigal Admin</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 2rem; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status { padding: 1rem; background: #e8f5e8; border: 1px solid #4caf50; border-radius: 4px; margin: 1rem 0; }
        .api-status { padding: 0.5rem; margin: 0.5rem 0; border-radius: 4px; }
        .online { background: #e8f5e8; color: #2e7d32; }
        .offline { background: #ffebee; color: #c62828; }
        pre { background: #f5f5f5; padding: 1rem; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Ninaivalaigal Admin Dashboard</h1>
        <div class="status">
            <h3>✅ UI Container Running</h3>
            <p>Admin interface is online and ready for development.</p>
        </div>

        <h3>🔗 Service Status</h3>
        <div id="services">
            <div class="api-status" id="api-status">🔄 Checking API...</div>
            <div class="api-status" id="mem0-status">🔄 Checking Mem0...</div>
        </div>

        <h3>🚀 Next Steps</h3>
        <ul>
            <li>Develop React/Vue/Svelte UI in <code>client/</code> directory</li>
            <li>Use <code>VITE_API_BASE=http://studio-ip:13370</code> for development</li>
            <li>Build production UI with <code>npm run build</code></li>
            <li>Container will auto-rebuild on changes</li>
        </ul>

        <h3>🛠 Development Commands</h3>
        <pre>
# Start full stack
make stack-up

# UI development mode (laptop)
cd client && npm run dev

# Production build
container build -t ninaivalaigal-ui:latest -f Dockerfile.ui .
        </pre>
    </div>

    <script>
        // Check API status
        fetch('/api/health')
            .then(r => r.json())
            .then(data => {
                document.getElementById('api-status').innerHTML = '✅ API Online';
                document.getElementById('api-status').className = 'api-status online';
            })
            .catch(e => {
                document.getElementById('api-status').innerHTML = '❌ API Offline';
                document.getElementById('api-status').className = 'api-status offline';
            });

        // Check Mem0 status
        fetch('http://localhost:7070/health')
            .then(r => r.json())
            .then(data => {
                document.getElementById('mem0-status').innerHTML = '✅ Mem0 Online';
                document.getElementById('mem0-status').className = 'api-status online';
            })
            .catch(e => {
                document.getElementById('mem0-status').innerHTML = '❌ Mem0 Offline';
                document.getElementById('mem0-status').className = 'api-status offline';
            });
    </script>
</body>
</html>
EOF

    log "Created placeholder UI structure for development"
  fi

  container build -t "$IMAGE" -f Dockerfile.ui .
}

run_container(){
  log "Starting $CONTAINER_NAME on :$HOST_PORT…"
  container run -d --name "$CONTAINER_NAME" \
    --publish "${HOST_PORT}:8080" \
    "$IMAGE"
}

wait_ready(){
  log "Waiting for UI /health (timeout ${WAIT_SEC}s)…"
  local t=0
  until curl -fsS "http://127.0.0.1:${HOST_PORT}/health" >/dev/null 2>&1; do
    sleep 2; t=$((t+2))
    if [ "$t" -ge "$WAIT_SEC" ]; then
      container logs "$CONTAINER_NAME" | tail -n 20 || true
      die "UI did not become healthy in ${WAIT_SEC}s."
    fi
  done
  log "UI is healthy."
}

summary(){
  cat <<EOF

✅ Admin UI up

Base:    http://localhost:${HOST_PORT}
Health:  http://localhost:${HOST_PORT}/health
API:     http://localhost:${HOST_PORT}/api/health
Logs:    container logs -f ${CONTAINER_NAME}
Stop:    container stop ${CONTAINER_NAME} && container delete ${CONTAINER_NAME}

Development:
  cd client && npm run dev    # Hot reload development
  VITE_API_BASE=http://studio-ip:13370 npm run dev

EOF
}

main(){
  need container
  need curl
  ensure_container
  stop_existing
  build_image
  run_container
  wait_ready
  summary
}
main "$@"
