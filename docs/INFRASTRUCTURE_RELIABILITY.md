# Infrastructure Reliability Guide

**Version:** 1.0.0
**Date:** 2024-10-06
**Status:** Day 3 - Infrastructure Reliability Complete

## Overview

This document describes the bulletproof infrastructure management system for ninaivalaigal, designed to prevent "working environment suddenly broken" scenarios and enable confident development.

## Architecture

### Unified Naming Convention

**Containers:**
- Database: `ninaivalaigal-{env}-db` (shared per environment)
- Redis: `ninaivalaigal-{env}-redis` (environment-specific)

**Ports (Apple CLI Dev):**
- Database: `5452` (PostgreSQL + pgvector + Apache AGE)
- Redis: `6399` (with authentication)

### Benefits

1. **No Confusion:** Clear naming eliminates duplicate container issues
2. **Environment Isolation:** Dev/test/prod separation
3. **Predictable:** Always know which container is which
4. **Safe:** Old `nv-*` containers removed to prevent conflicts

## Quick Start

### Starting the Stack

```bash
# Recommended: Use new bulletproof scripts with health checks
make stack-start

# Alternative: Direct script execution
./scripts/stack-start.sh
```

**What happens:**
1. ✅ Checks Apple Container CLI is available
2. ✅ Cleans up any existing stopped containers
3. ✅ Starts database with health monitoring
4. ✅ Waits for database to be ready (max 60s)
5. ✅ Runs health checks (PostgreSQL queries)
6. ✅ Starts Redis with health monitoring
7. ✅ Verifies Redis is responding
8. ✅ Displays connection information

### Checking Stack Status

```bash
# Detailed status with health checks
make stack-check

# Legacy command (less detail)
make stack-status
```

**Status includes:**
- Container running state
- Database version and extensions
- Redis version and memory usage
- Connection test results

### Stopping the Stack

```bash
make stack-stop
```

**What happens:**
1. Stops Redis gracefully
2. Stops database gracefully
3. Confirms all containers stopped

### Restarting the Stack

```bash
make stack-restart
```

Equivalent to `stop` + `start` with full health checks.

## Features

### 1. Health Checks

**Database Health:**
- Connection test via `psql`
- Query execution verification
- Extension detection (pgvector, Apache AGE)
- Version reporting

**Redis Health:**
- PING/PONG test
- Memory usage reporting
- Server info verification

### 2. Auto-Restart (Optional)

Enable automatic container restart on failure:

```bash
# Start with auto-restart enabled (default)
ENABLE_AUTO_RESTART=true make stack-start

# Start without auto-restart
ENABLE_AUTO_RESTART=false make stack-start
```

**Restart Policy Options:**
- `unless-stopped` (default): Restart unless manually stopped
- `always`: Always restart, even after system reboot
- `on-failure`: Only restart on error exit codes

### 3. Comprehensive Logging

All operations include:
- Timestamps
- Color-coded output (info/success/warning/error)
- Detailed progress indicators
- Error messages with context

### 4. Port Conflict Detection

Scripts check if ports are already in use and provide clear warnings.

### 5. Timeout Protection

All health checks have configurable timeouts:
- Container startup: 30-60s max
- Database health: 60s max (30 retries × 2s)
- Redis health: 60s max (30 retries × 2s)

## Configuration

### Environment Variables

```bash
# Environment (dev/test/prod)
export NINA_ENV=dev

# Database password
export NINA_DB_PASSWORD=dev_password_change_in_production

# Redis password
export NINA_REDIS_PASSWORD=dev_redis_password

# Auto-restart settings
export ENABLE_AUTO_RESTART=true
export RESTART_POLICY=unless-stopped
```

### Default Values

If not set, scripts use safe defaults:
- `NINA_ENV`: `dev`
- `NINA_DB_PASSWORD`: `dev_password_change_in_production`
- `NINA_REDIS_PASSWORD`: `dev_redis_password`
- `ENABLE_AUTO_RESTART`: `true`
- `RESTART_POLICY`: `unless-stopped`

## Troubleshooting

### Container Won't Start

**Symptom:** `stack-start.sh` fails during container startup

**Solutions:**

1. Check if port is already in use:
   ```bash
   lsof -i :5452  # Database
   lsof -i :6399  # Redis
   ```

2. Check for old containers:
   ```bash
   container list --all | grep ninaivalaigal
   ```

3. Clean up manually:
   ```bash
   container stop ninaivalaigal-dev-db ninaivalaigal-dev-redis
   container delete ninaivalaigal-dev-db ninaivalaigal-dev-redis
   ```

4. Check disk space:
   ```bash
   df -h
   ```

### Health Check Fails

**Symptom:** Container starts but health check fails

**Solutions:**

1. Check container logs:
   ```bash
   container logs ninaivalaigal-dev-db
   container logs ninaivalaigal-dev-redis
   ```

2. Increase timeout:
   ```bash
   # Edit scripts/stack-start.sh
   readonly HEALTH_CHECK_TIMEOUT=120  # Increase from 60
   ```

3. Test connection manually:
   ```bash
   # Database
   PGPASSWORD=dev_password_change_in_production \
     psql -h localhost -p 5452 -U nina -d ninaivalaigal_dev

   # Redis
   redis-cli -h localhost -p 6399 -a dev_redis_password ping
   ```

### Database Extensions Missing

**Symptom:** `pgvector` or `Apache AGE` not showing in status

**Solution:**

1. Rebuild database image:
   ```bash
   cd containers/consolidated-db
   container build --no-cache -t nina-intelligence-db:arm64 .
   ```

2. Restart stack:
   ```bash
   make stack-restart
   ```

3. Verify extensions:
   ```bash
   PGPASSWORD=dev_password_change_in_production \
     psql -h localhost -p 5452 -U nina -d ninaivalaigal_dev -c "\dx"
   ```

### "Old Container" Confusion

**Symptom:** Multiple containers with similar names

**Prevention:**

1. Always use unified naming convention
2. Clean up old containers:
   ```bash
   # List all containers
   container list --all

   # Remove old nv-* containers
   container stop nv-db nv-redis
   container delete nv-db nv-redis
   ```

3. Use `make stack-start` (automatic cleanup)

### Stack Mysteriously Stopped

**Symptom:** Containers not running, no error messages

**Investigation:**

1. Check container exit codes:
   ```bash
   container list --all | grep ninaivalaigal
   ```

2. View last logs:
   ```bash
   container logs ninaivalaigal-dev-db 2>&1 | tail -50
   container logs ninaivalaigal-dev-redis 2>&1 | tail -50
   ```

3. Check system resources:
   ```bash
   # Memory
   vm_stat

   # Disk
   df -h

   # CPU
   top -l 1 | head -10
   ```

4. Enable auto-restart:
   ```bash
   ENABLE_AUTO_RESTART=true make stack-start
   ```

## Crash Recovery Testing

### Simulating Database Crash

```bash
# Kill database container
container stop ninaivalaigal-dev-db

# Verify auto-restart (if enabled)
sleep 5
container list | grep ninaivalaigal-dev-db

# Manual recovery
make stack-restart
```

### Simulating Redis Crash

```bash
# Kill Redis container
container stop ninaivalaigal-dev-redis

# Verify auto-restart (if enabled)
sleep 5
container list | grep ninaivalaigal-dev-redis

# Manual recovery
make stack-restart
```

### Complete Stack Recovery

```bash
# Nuclear option: stop everything and restart fresh
make stack-stop
sleep 5
make stack-start
make stack-check
```

## Monitoring

### Continuous Health Monitoring

```bash
# Watch stack status (manual)
watch -n 5 'make stack-check'

# Check logs continuously
container logs -f ninaivalaigal-dev-db
container logs -f ninaivalaigal-dev-redis
```

### Integration with Pre-Push Hook

The pre-push Git hook automatically runs smoke tests that verify:
- Database connectivity
- Redis connectivity
- Alembic migrations applied

**Located at:** `.git/hooks/pre-push`

## Best Practices

### 1. Always Use Make Commands

✅ **Good:**
```bash
make stack-start
make stack-check
make stack-stop
```

❌ **Avoid:**
```bash
container run -d --name db ...  # Manual, error-prone
```

### 2. Check Status Before Debugging

```bash
# First thing when something seems wrong
make stack-check
```

### 3. Clean Restarts

```bash
# When in doubt, clean restart
make stack-restart
```

### 4. Enable Auto-Restart in Development

```bash
# Add to ~/.zshrc or ~/.bashrc
export ENABLE_AUTO_RESTART=true
```

### 5. Never Delete Volumes Manually

Volumes contain persistent data. Use these commands instead:

```bash
# List volumes
container volume list | grep ninaivalaigal

# Backup before deleting (if needed)
# ... create backup first ...

# Then delete if absolutely necessary
container volume rm ninaivalaigal_dev_db_data
```

## Migration from Old System

### If you have old `nv-*` containers:

```bash
# 1. Stop old containers
container stop nv-db nv-redis nv-api

# 2. Export data (if needed)
# ... backup steps ...

# 3. Delete old containers
container delete nv-db nv-redis nv-api

# 4. Start new unified stack
make stack-start

# 5. Verify
make stack-check
```

### If you have old scripts:

| Old Command | New Command |
|-------------|-------------|
| `./scripts/nv-stack-start.sh` | `make stack-start` |
| `./scripts/nv-stack-stop.sh` | `make stack-stop` |
| `./scripts/nv-stack-status.sh` | `make stack-check` |
| `./scripts/nv-db-start.sh` | `make stack-start` (starts DB) |

## Scripts Reference

### Core Scripts

- **`stack-start.sh`**: Bulletproof startup with health checks
- **`stack-stop.sh`**: Clean shutdown
- **`stack-status.sh`**: Detailed status and health reporting
- **`stack-restart.sh`**: Stop + Start wrapper

### Script Features

All scripts include:
- ✅ Colored output for clarity
- ✅ Timestamp logging
- ✅ Error handling with exit codes
- ✅ Comprehensive health checks
- ✅ Progress indicators
- ✅ Helpful error messages

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General failure (container start, health check) |

## Future Enhancements

Planned for Days 4-5:

1. **Automated Recovery**: Watchdog script to auto-restart failed containers
2. **Performance Monitoring**: Track response times and resource usage
3. **Backup Automation**: Scheduled database backups
4. **Health Dashboards**: Web-based monitoring UI
5. **Alert System**: Notifications for failures

## Summary

**What We've Built:**

✅ Bulletproof stack startup with comprehensive health checks
✅ Unified naming convention (no more confusion)
✅ Auto-restart capability for resilience
✅ Detailed status reporting
✅ Clean shutdown procedures
✅ Comprehensive error handling
✅ Make command integration

**What This Prevents:**

❌ "Working environment suddenly broken" scenarios
❌ Container naming confusion
❌ Silent failures
❌ Mystery crashes
❌ Port conflicts
❌ Resource exhaustion

**Development Impact:**

- **Before:** Infrastructure failures interrupt development
- **After:** Self-healing infrastructure enables uninterrupted work

---

**Last Updated:** 2024-10-06
**Maintainer:** Ninaivalaigal Infrastructure Team
**Status:** Production-ready for development environments
