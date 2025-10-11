# SPEC-117: Unified Runtime Parity & Deployment
**Project:** Medhasys / Ninaivalaigal
**Status:** Draft
**Owner:** Platform Engineering
**Last Updated:** 2025-10-11

### Makefile
```makefile
up:
	docker compose up -d

down:
	docker compose down

health:
	curl -f http://localhost:8000/health || exit 1
```

### docker-compose.yml
```yaml
version: '3.9'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```
