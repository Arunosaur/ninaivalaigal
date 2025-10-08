# Configuration Directory

This directory contains the unified configuration system for ninaivalaigal.

## File Structure

```
configs/
├── defaults.env                # Global defaults (committed)
├── runtime-{runtime}.env       # Runtime-specific (committed)
├── env-{environment}.env       # Environment-specific (committed)
├── secrets-{runtime}-{env}.env # Secrets (gitignored, create locally)
└── secrets.env.template        # Template for secrets files
```

## Configuration Hierarchy

Configuration is loaded in this order (later overrides earlier):

1. **defaults.env** - Global defaults and SPEC-086 port allocation
2. **runtime-{runtime}.env** - Runtime-specific (docker/colima/apple)
3. **env-{environment}.env** - Environment-specific (dev/test/prod)
4. **secrets-{runtime}-{env}.env** - Secrets (passwords, tokens)

## Quick Start

### For Development (Apple CLI)

```bash
# 1. Copy the secrets template
cp secrets.env.template secrets-apple-dev.env

# 2. Edit and fill in your passwords
nano secrets-apple-dev.env

# 3. Example contents:
cat > secrets-apple-dev.env <<EOF
NINA_DB_PASSWORD=my_dev_db_password_123
NINA_REDIS_PASSWORD=my_dev_redis_password_456
NINA_JWT_SECRET=my_dev_jwt_secret_at_least_32_chars_long
EOF

# 4. Start the stack (will auto-load config)
make stack-start
# Or: ./scripts/stack-start-unified.sh apple dev
```

### For Other Runtimes

```bash
# Docker + Dev
cp secrets.env.template secrets-docker-dev.env
# Edit secrets-docker-dev.env
./scripts/stack-start-unified.sh docker dev

# Colima + Test
cp secrets.env.template secrets-colima-test.env
# Edit secrets-colima-test.env
./scripts/stack-start-unified.sh colima test
```

## Available Runtimes

- **docker** - Docker Desktop or standard Docker Engine
- **colima** - Colima container runtime on macOS
- **apple** - Apple Container CLI (M1/M2/M3 Macs)

## Available Environments

- **dev** - Development (permissive, debug enabled)
- **test** - Testing (restricted, no debug)
- **prod** - Production (very restricted, secure)

## SPEC-086 Port Calculation

Ports are calculated automatically using the formula:

```
Final Port = Base Port + Environment Offset + Runtime Offset
```

### Offsets

| Factor | Offset |
|--------|--------|
| Docker | +0 |
| Colima | +10 |
| Apple  | +20 |
| Dev    | +0 |
| Test   | +100 |
| Prod   | +200 |

### Example Ports

| Runtime | Env | DB | PgBouncer | Redis | API |
|---------|-----|----|-----------| ------|-----|
| Apple | Dev | 5452 | 6452 | 6399 | 13390 |
| Docker | Dev | 5432 | 6432 | 6379 | 13370 |
| Colima | Test | 5542 | 6542 | 6489 | 13480 |

## Security Notes

### ⚠️ NEVER Commit Secrets

The following files are automatically gitignored:
- `secrets-*.env`
- `*.secret.env`

### ✅ Safe to Commit

These files are safe to commit (no secrets):
- `defaults.env`
- `runtime-*.env`
- `env-*.env`
- `secrets.env.template`

### Production Secrets

For production, use proper secrets management:

```bash
# Option 1: External secrets manager
./scripts/fetch-secrets.sh prod

# Option 2: Environment variables
export NINA_DB_PASSWORD=$(op read "op://prod/db/password")
export NINA_REDIS_PASSWORD=$(op read "op://prod/redis/password")
export NINA_JWT_SECRET=$(op read "op://prod/jwt/secret")

# Option 3: Kubernetes secrets
kubectl create secret generic ninaivalaigal-prod-secrets \
  --from-literal=db-password="..." \
  --from-literal=redis-password="..." \
  --from-literal=jwt-secret="..."
```

## Validation

The configuration system validates:
- All required files exist
- All required variables are set
- Container command is available
- Port calculations are correct
- No conflicts with running containers

## Troubleshooting

### "Secrets file required"

```bash
# Error: Secrets file required for test: configs/secrets-apple-test.env

# Solution: Create the secrets file
cp secrets.env.template secrets-apple-test.env
nano secrets-apple-test.env
```

### "Container command not found"

```bash
# Error: Container command not found: container

# Solution for Apple CLI:
which container
# If not found: Install Apple Container CLI or use docker runtime instead
./scripts/stack-start-unified.sh docker dev
```

### "Missing required configuration variables"

Check that your secrets file has all required values:
- `NINA_DB_PASSWORD`
- `NINA_REDIS_PASSWORD`
- `NINA_JWT_SECRET`

## Benefits

✅ **One configuration system for all runtimes**
✅ **SPEC-086 compliant automatically**
✅ **Secrets never in git**
✅ **Easy to switch runtimes/environments**
✅ **Validated at load time**
✅ **Clear error messages**

## Migration from Old System

If you have existing environment variables:

```bash
# Old way (hardcoded)
export NINA_DB_PASSWORD=mypass
./scripts/stack-start-complete.sh

# New way (config system)
echo "NINA_DB_PASSWORD=mypass" > configs/secrets-apple-dev.env
./scripts/stack-start-unified.sh apple dev
```

## See Also

- `docs/UNIFORM_ARCHITECTURE_DESIGN.md` - Complete architecture design
- `scripts/common/config-loader.sh` - Configuration loader implementation
- `specs/SPEC-086-multi-runtime-port-allocation.md` - Port allocation specification
