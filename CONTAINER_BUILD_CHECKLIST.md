# Container Build & Deploy Checklist

## Pre-Build Verification
- [ ] 1. Code changes saved in workspace
- [ ] 2. Verify `run_server.py` has `/app/server` in sys.path
- [ ] 3. Verify `server/main.py` has lifespan pattern (no import-time DB connection)
- [ ] 4. Verify startup scripts have correct PYTHONPATH

## Build (Use Docker to avoid DNS issues)
- [ ] 5. Build with Docker: `docker build --no-cache --platform linux/arm64 -t nina-api:arm64 -f containers/api/Dockerfile .`
- [ ] 6. Wait for build to complete (check with `docker images nina-api:arm64`)

## Verification (CRITICAL - DO NOT SKIP)
- [ ] 7. Test dependencies: `docker run --rm nina-api:arm64 pip list | grep structlog`
- [ ] 8. Test file exists: `docker run --rm nina-api:arm64 ls -la /app/run_server.py`
- [ ] 9. Test run_server.py has correct code: `docker run --rm nina-api:arm64 cat /app/run_server.py | grep "/app/server"`
- [ ] 10. Test import works: `docker run --rm -e PYTHONPATH=/app:/app/server nina-api:arm64 python -c "import sys; sys.path.insert(0, '/app/server'); from approval_workflow import ApprovalWorkflowManager; print('✅')"`

## Transfer to Apple Container CLI
- [ ] 11. Save NEW image: `docker save nina-api:arm64 -o /tmp/nina-api-NEW-$(date +%H%M).tar`
- [ ] 12. Load into Apple Container CLI: `container image load -i /tmp/nina-api-NEW-*.tar`
- [ ] 13. Verify loaded: `container image list | grep nina-api`

## Deploy
- [ ] 14. Stop old container: `container stop ninaivalaigal-dev-api; container delete ninaivalaigal-dev-api`
- [ ] 15. Get IPs: `container list | grep -E "(db|redis)"`
- [ ] 16. Start with correct env vars (see command below)
- [ ] 17. Check running: `container list | grep ninaivalaigal-dev-api`
- [ ] 18. Check logs for lifespan messages: `container logs ninaivalaigal-dev-api`
- [ ] 19. Test health endpoint: `curl http://localhost:13390/health`

## Deployment Command Template
```bash
container run -d --name ninaivalaigal-dev-api -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:secure_nina_password@192.168.64.208:6432/ninaivalaigal_dev" \
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:secure_nina_password@192.168.64.208:6432/ninaivalaigal_dev" \
  -e REDIS_HOST="192.168.64.189" \
  -e REDIS_PORT=6379 \
  -e REDIS_PASSWORD="secure_nina_password" \
  -e NINAIVALAIGAL_JWT_SECRET="dev-secret-change-in-production" \
  -e PYTHONPATH=/app:/app/server \
  -e ENVIRONMENT=development \
  nina-api:arm64
```

## Troubleshooting
If container stops immediately:
1. Check logs: `container logs ninaivalaigal-dev-api 2>&1 | tail -50`
2. Verify image hash matches: `docker images nina-api:arm64` vs `container image list | grep nina-api`
3. Re-verify step 9 (run_server.py content in container)
