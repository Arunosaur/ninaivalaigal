# Redis Container - Apple Container CLI
**Redis 7 for caching, rate limiting, and sessions**

---

## Container Information

- **Name**: `ninaivalaigal-dev-redis`
- **Image**: `redis:7-alpine`
- **Architecture**: ARM64
- **Port Mapping**: `6389:6379` (dev)
- **Use Cases**: Caching, rate limiting, session storage, SPEC-031 relevance scoring

---

## Prerequisites

### No Build Required
Redis uses official pre-built image from Docker Hub (ARM64 compatible).

### Tools Required
```bash
# Redis CLI (for testing)
brew install redis

# jq (for JSON parsing)
brew install jq
```

---

## Runtime Configuration

### Basic Start (No Password - NOT RECOMMENDED)
```bash
container run -d --name ninaivalaigal-dev-redis \
  -p 6389:6379 \
  redis:7-alpine

# ❌ Don't use this - no authentication
```

### Recommended Start (With Password)
```bash
container run -d --name ninaivalaigal-dev-redis \
  -p 6389:6379 \
  redis:7-alpine redis-server \
  --requirepass nina_redis_dev_password \  # pragma: allowlist secret
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru
```

### Production Start
```bash
container run -d --name ninaivalaigal-dev-redis \
  -p 6389:6379 \
  -v ninaivalaigal_dev_redis_data:/data \
  redis:7-alpine redis-server \
  --requirepass ${REDIS_PASSWORD} \  # pragma: allowlist secret
  --maxmemory 512mb \
  --maxmemory-policy allkeys-lru \
  --appendonly yes \
  --appendfsync everysec
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `--requirepass` | Yes (prod) | - | Redis password |  # pragma: allowlist secret
| `--maxmemory` | Recommended | unlimited | Max memory usage |
| `--maxmemory-policy` | Recommended | `noeviction` | Eviction policy |
| `--appendonly` | Recommended | `no` | Enable AOF persistence |

---

## Configuration Options

### Memory Management
```bash
# Development (256MB)
--maxmemory 256mb --maxmemory-policy allkeys-lru

# Production (512MB-1GB)
--maxmemory 1gb --maxmemory-policy allkeys-lru
```

**Eviction Policies**:
- `allkeys-lru` - Remove least recently used keys (recommended for cache)
- `volatile-lru` - Remove LRU keys with expiration set
- `allkeys-random` - Remove random keys
- `noeviction` - Return errors when memory limit reached

### Persistence
```bash
# AOF (Append-Only File) - Better durability
--appendonly yes --appendfsync everysec

# RDB (Snapshots) - Better performance
--save 900 1 --save 300 10 --save 60 10000
```

### Security
```bash
# Password
--requirepass ${SECURE_PASSWORD}  # pragma: allowlist secret

# Disable dangerous commands
--rename-command FLUSHDB "" --rename-command FLUSHALL ""
```

---

## Verification

### Check Container Status
```bash
container list | grep ninaivalaigal-dev-redis
```

### Check Logs
```bash
container logs ninaivalaigal-dev-redis

# Should see:
# * Ready to accept connections
```

### Test Connection (No Password)
```bash
# From host
redis-cli -h localhost -p 6389 ping
# Expected: PONG

# From container
container exec ninaivalaigal-dev-redis redis-cli ping
# Expected: PONG
```

### Test Connection (With Password)
```bash
# From host
redis-cli -h localhost -p 6389 -a nina_redis_dev_password ping
# Expected: PONG

# From container
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password ping
# Expected: PONG
```

### Test Basic Operations
```bash
# Set a key
redis-cli -h localhost -p 6389 -a nina_redis_dev_password SET test_key "hello"

# Get the key
redis-cli -h localhost -p 6389 -a nina_redis_dev_password GET test_key
# Expected: "hello"

# Delete the key
redis-cli -h localhost -p 6389 -a nina_redis_dev_password DEL test_key
```

---

## Get Container IP

```bash
# Get IP for API configuration
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "Redis IP: $REDIS_IP"

# Test from another container
container run --rm redis:7-alpine redis-cli -h ${REDIS_IP} -a nina_redis_dev_password ping
```

---

## Connection Strings

### For API Configuration
```bash
# Get Redis IP
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Connection URL
REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0"

# Or individual variables
REDIS_HOST="${REDIS_IP}"
REDIS_PORT="6379"
REDIS_PASSWORD="nina_redis_dev_password"  # pragma: allowlist secret
REDIS_DB="0"
```

### Start API with Redis
```bash
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

container run -d --name ninaivalaigal-dev-api \
  -e REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0" \
  nina-api:arm64
```

---

## Monitoring

### Info
```bash
# General info
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password INFO

# Memory stats
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password INFO memory

# CPU stats
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password INFO cpu

# Replication stats
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password INFO replication
```

### Memory Usage
```bash
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password INFO memory | grep -E "used_memory_human|maxmemory_human"
```

### Connected Clients
```bash
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password CLIENT LIST
```

### Key Statistics
```bash
# Number of keys
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password DBSIZE

# Key space info
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password INFO keyspace
```

### Slow Log
```bash
# Get slow queries
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password SLOWLOG GET 10
```

---

## Data Management

### Backup (RDB Snapshot)
```bash
# Create snapshot
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password BGSAVE

# Check status
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password LASTSAVE

# Copy snapshot file
container exec ninaivalaigal-dev-redis cat /data/dump.rdb > backup-$(date +%Y%m%d-%H%M%S).rdb
```

### Restore from Backup
```bash
# Stop Redis
container stop ninaivalaigal-dev-redis

# Copy backup to volume
# (Depends on volume setup)

# Start Redis
container start ninaivalaigal-dev-redis
```

### Clear All Data
```bash
# Clear current database
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password FLUSHDB

# Clear all databases
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password FLUSHALL
```

---

## Common Operations

### Rate Limiting (Used by API)
```bash
# Increment counter with expiration
redis-cli -h localhost -p 6389 -a nina_redis_dev_password INCR rate_limit:user:123
redis-cli -h localhost -p 6389 -a nina_redis_dev_password EXPIRE rate_limit:user:123 60

# Check counter
redis-cli -h localhost -p 6389 -a nina_redis_dev_password GET rate_limit:user:123
```

### Session Storage
```bash
# Store session
redis-cli -h localhost -p 6389 -a nina_redis_dev_password SET session:abc123 '{"user_id": 1, "logged_in": true}' EX 3600

# Get session
redis-cli -h localhost -p 6389 -a nina_redis_dev_password GET session:abc123

# Delete session
redis-cli -h localhost -p 6389 -a nina_redis_dev_password DEL session:abc123
```

### Caching
```bash
# Cache API response
redis-cli -h localhost -p 6389 -a nina_redis_dev_password SET cache:api:/users:page:1 '{"users": [...]}' EX 300

# Get cached response
redis-cli -h localhost -p 6389 -a nina_redis_dev_password GET cache:api:/users:page:1

# Invalidate cache
redis-cli -h localhost -p 6389 -a nina_redis_dev_password DEL cache:api:/users:page:1
```

### SPEC-031 Relevance Scoring
```bash
# Store relevance score
redis-cli -h localhost -p 6389 -a nina_redis_dev_password ZADD relevance:search:query1 0.95 doc:123 0.87 doc:456

# Get top N results
redis-cli -h localhost -p 6389 -a nina_redis_dev_password ZREVRANGE relevance:search:query1 0 9 WITHSCORES
```

---

## Performance Tuning

### Development Settings
```bash
container run -d --name ninaivalaigal-dev-redis \
  -p 6389:6379 \
  redis:7-alpine redis-server \
  --requirepass nina_redis_dev_password \  # pragma: allowlist secret
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru \
  --maxclients 100
```

### Production Settings
```bash
container run -d --name ninaivalaigal-prod-redis \
  -p 6379:6379 \
  -v ninaivalaigal_prod_redis_data:/data \
  redis:7-alpine redis-server \
  --requirepass ${REDIS_PASSWORD} \  # pragma: allowlist secret
  --maxmemory 1gb \
  --maxmemory-policy allkeys-lru \
  --maxclients 1000 \
  --appendonly yes \
  --appendfsync everysec \
  --tcp-backlog 511 \
  --timeout 300
```

---

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
container logs ninaivalaigal-dev-redis
```

**Common issues**:
1. **Port conflict**:
   ```bash
   lsof -i :6389
   # Kill conflicting process or use different port
   ```

2. **Permission issues**:
   ```bash
   # Check container logs for permission errors
   container logs ninaivalaigal-dev-redis | grep -i permission
   ```

### Authentication Failures

**Wrong password**:
```bash
# Error: NOAUTH Authentication required
# Solution: Use -a flag with password
redis-cli -h localhost -p 6389 -a nina_redis_dev_password ping

# Error: WRONGPASS invalid username-password pair
# Solution: Check password is correct
echo $REDIS_PASSWORD
```

**No password set**:
```bash
# If you forgot to set --requirepass
# Stop and restart with password
container stop ninaivalaigal-dev-redis
container delete ninaivalaigal-dev-redis

container run -d --name ninaivalaigal-dev-redis \
  -p 6389:6379 \
  redis:7-alpine redis-server --requirepass nina_redis_dev_password  # pragma: allowlist secret
```

### Connection Refused

**From host**:
```bash
# Check if container is running
container list | grep ninaivalaigal-dev-redis

# Check port mapping
container inspect ninaivalaigal-dev-redis | jq '.[0].ports'

# Test with redis-cli
redis-cli -h localhost -p 6389 -a nina_redis_dev_password ping
```

**From other containers**:
```bash
# Use container IP, not hostname
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Test
container run --rm redis:7-alpine redis-cli -h ${REDIS_IP} -a nina_redis_dev_password ping
```

### Out of Memory

**Check memory usage**:
```bash
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password INFO memory | grep used_memory_human
```

**Solutions**:
1. **Increase maxmemory**:
   ```bash
   # Recreate with more memory
   container stop ninaivalaigal-dev-redis
   container delete ninaivalaigal-dev-redis

   container run -d --name ninaivalaigal-dev-redis \
     -p 6389:6379 \
     redis:7-alpine redis-server \
     --requirepass nina_redis_dev_password \  # pragma: allowlist secret
     --maxmemory 512mb \
     --maxmemory-policy allkeys-lru
   ```

2. **Clear unused keys**:
   ```bash
   container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password FLUSHDB
   ```

3. **Check for key leaks**:
   ```bash
   # Find keys without TTL
   container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password --scan | \
   while read key; do
     ttl=$(container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password TTL "$key")
     if [ "$ttl" = "-1" ]; then
       echo "No TTL: $key"
     fi
   done
   ```

### Slow Performance

**Check slow log**:
```bash
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password SLOWLOG GET 10
```

**Check connected clients**:
```bash
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password CLIENT LIST | wc -l
```

**Check for blocking commands**:
```bash
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password INFO stats | grep blocked_clients
```

---

## Security

### Change Password
```bash
# Stop container
container stop ninaivalaigal-dev-redis
container delete ninaivalaigal-dev-redis

# Start with new password
container run -d --name ninaivalaigal-dev-redis \
  -p 6389:6379 \
  redis:7-alpine redis-server --requirepass ${NEW_PASSWORD}  # pragma: allowlist secret

# Update API configuration
REDIS_URL="redis://:${NEW_PASSWORD}@${REDIS_IP}:6379/0"
```

### Disable Dangerous Commands
```bash
container run -d --name ninaivalaigal-dev-redis \
  -p 6389:6379 \
  redis:7-alpine redis-server \
  --requirepass nina_redis_dev_password \  # pragma: allowlist secret
  --rename-command FLUSHDB "" \
  --rename-command FLUSHALL "" \
  --rename-command CONFIG "" \
  --rename-command SHUTDOWN ""
```

---

## Clean Up

### Stop and Remove Container
```bash
container stop ninaivalaigal-dev-redis
container delete ninaivalaigal-dev-redis
```

### Remove Volume
```bash
container volume rm ninaivalaigal_dev_redis_data
```

---

## Integration with API

### API Rate Limiting Middleware
The API uses Redis for rate limiting in `/server/security/middleware/redis_rate_limiter.py`:

```python
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
self.redis = aioredis.from_url(redis_url, decode_responses=True)
```

**Start API with Redis**:
```bash
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

container run -d --name ninaivalaigal-dev-api \
  -p 13390:8000 \
  -e REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0" \
  nina-api:arm64
```

### Test Rate Limiting
```bash
# Make multiple requests
for i in {1..10}; do
  curl -w "\n" http://localhost:13390/health
done

# Check Redis for rate limit counters
redis-cli -h localhost -p 6389 -a nina_redis_dev_password --scan --pattern "rate_limit:*"
```

---

## Quick Reference

```bash
# Start with password and memory limit
container run -d --name ninaivalaigal-dev-redis \
  -p 6389:6379 \
  redis:7-alpine redis-server \
  --requirepass nina_redis_dev_password \  # pragma: allowlist secret
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru

# Verify
redis-cli -h localhost -p 6389 -a nina_redis_dev_password ping

# Get IP
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

# Connection URL
REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0"

# Monitor
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password MONITOR

# Info
container exec ninaivalaigal-dev-redis redis-cli -a nina_redis_dev_password INFO
```
