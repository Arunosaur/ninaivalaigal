# Cutover & Rollback Procedures

## Overview

This document outlines the procedures for switching between memory providers (native vs http) and rolling back if issues occur.

## Memory Provider Options

- **Native**: Direct memory operations within the API process
- **HTTP**: Memory operations via mem0 sidecar container

## Cutover Procedure (Native → HTTP)

### Pre-Cutover Checklist

```bash
# 1. Verify current state
make stack-status
echo "Current MEMORY_PROVIDER: ${MEMORY_PROVIDER:-native}"

# 2. Create backup
./scripts/backup-db.sh

# 3. Test mem0 sidecar independently
./scripts/nv-mem0-start.sh
curl http://localhost:7070/health
./scripts/nv-mem0-stop.sh
```

### Cutover Steps

```bash
# 1. Stop current stack
make stack-down

# 2. Update environment configuration
# Edit .env file:
MEMORY_PROVIDER=http
MEMORY_HTTP_BASE=http://localhost:7070

# 3. Start stack with mem0
make stack-up

# 4. Verify all services
make stack-status

# 5. Test mem0 endpoints
curl http://localhost:7070/health
curl -X POST http://localhost:7070/remember -H "Content-Type: application/json" -d '{"text": "test memory"}'
curl "http://localhost:7070/recall?q=test&k=5"
```

### Post-Cutover Validation

```bash
# 1. API health check
curl http://localhost:13370/health

# 2. Database connectivity
./scripts/db-stats.sh

# 3. Full stack status
make stack-status

# 4. Check logs for errors
container logs nv-api | tail -20
container logs nv-mem0 | tail -20

# 5. Run smoke tests (if available)
# pytest tests/test_memory_integration.py
```

## Rollback Procedure (HTTP → Native)

### When to Rollback

- mem0 sidecar failing to start
- API unable to connect to mem0
- Performance degradation
- Memory operations failing

### Rollback Steps

```bash
# 1. Stop current stack immediately
make stack-down

# 2. Revert environment configuration
# Edit .env file:
MEMORY_PROVIDER=native
# MEMORY_HTTP_BASE=  # Comment out or remove

# 3. Start stack without mem0
make stack-up

# 4. Verify rollback success
make stack-status
curl http://localhost:13370/health

# 5. Confirm native memory operations
# Test your API endpoints that use memory
```

### Emergency Rollback (Fast)

```bash
# One-liner emergency rollback
MEMORY_PROVIDER=native make stack-down && make stack-up
```

## Testing Both Providers

### Automated Testing

```bash
# Test native provider
MEMORY_PROVIDER=native make stack-up
# Run your tests
make stack-down

# Test http provider
MEMORY_PROVIDER=http make stack-up
# Run your tests
make stack-down
```

### Manual Validation

```bash
# Native provider test
export MEMORY_PROVIDER=native
make stack-up
# Your API should work without mem0 container
make stack-status  # Should show mem0 as "not running"

# HTTP provider test
export MEMORY_PROVIDER=http
make stack-up
# Your API should connect to mem0 sidecar
make stack-status  # Should show all services running
curl http://localhost:7070/health
```

## Troubleshooting

### Common Issues

**mem0 Container Won't Start**
```bash
# Check Docker/container system
container system status

# Check port conflicts
lsof -i :7070

# Check logs
container logs nv-mem0

# Manual cleanup
container stop nv-mem0 || true
container delete nv-mem0 || true
```

**API Can't Connect to mem0**
```bash
# Check network connectivity
curl http://localhost:7070/health

# Check API logs for connection errors
container logs nv-api | grep -i mem0

# Verify environment variables
container exec nv-api env | grep MEMORY
```

**Performance Issues**
```bash
# Check resource usage
container stats

# Monitor database performance
./scripts/db-stats.sh

# Check API response times
time curl http://localhost:13370/health
```

### Recovery Scenarios

**Partial Failure (API up, mem0 down)**
```bash
# Quick restart of mem0 only
./scripts/nv-mem0-stop.sh
./scripts/nv-mem0-start.sh

# Or restart entire stack
make stack-down && make stack-up
```

**Complete Failure**
```bash
# Emergency rollback to native
MEMORY_PROVIDER=native make stack-down
make stack-up

# Investigate issues
container logs nv-mem0
container logs nv-api
```

## Monitoring During Cutover

### Key Metrics to Watch

```bash
# Service health
watch -n 5 'make stack-status'

# API response times
watch -n 10 'time curl -s http://localhost:13370/health'

# Memory usage
watch -n 5 'container stats --no-stream'

# Database connections
watch -n 10 './scripts/db-stats.sh | grep -A 5 "Connection Statistics"'
```

### Log Monitoring

```bash
# Real-time log monitoring
make logs

# Or individual services
container logs -f nv-api &
container logs -f nv-mem0 &
container logs -f nv-pgbouncer &
```

## Best Practices

1. **Always backup before cutover** - Database state is critical
2. **Test in non-production first** - Validate the process
3. **Monitor closely** - Watch for issues in first 30 minutes
4. **Have rollback ready** - Know the exact steps to revert
5. **Document issues** - Keep notes for future improvements
6. **Communicate status** - Keep team informed during process

## Automation

### Scripted Cutover

```bash
#!/bin/bash
# cutover-to-http.sh
set -euo pipefail

echo "Starting cutover to HTTP memory provider..."

# Backup
./scripts/backup-db.sh

# Stop stack
make stack-down

# Update config (you'll need to implement config update)
# sed -i 's/MEMORY_PROVIDER=native/MEMORY_PROVIDER=http/' .env

# Start with HTTP
MEMORY_PROVIDER=http make stack-up

# Validate
make stack-status
curl http://localhost:7070/health
curl http://localhost:13370/health

echo "Cutover complete!"
```

### Scheduled Health Checks

```bash
# Add to crontab for monitoring
*/5 * * * * cd /path/to/ninaivalaigal && make stack-status > /tmp/stack-status.log 2>&1
```
