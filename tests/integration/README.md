# Integration Tests for ninaivalaigal

## Overview

Integration tests validate the complete system behavior by testing against running services (Core API, Database, PgBouncer, Redis).

## Test Requirements

### Running Services

Integration tests require these services to be running:

1. **Database**: `ninaivalaigal-dev-db` (PostgreSQL 15)
2. **PgBouncer TX**: `ninaivalaigal-dev-pgbouncer-tx` (port 6432)
3. **Core API**: `ninaivalaigal-dev-core-api` (container internal port 8000)

### Environment Configuration

Tests use `.env.test` for configuration. Key variables:

```bash
# Database credentials
POSTGRES_USER=nina
POSTGRES_PASSWORD=dev_password_change_in_production  # pragma: allowlist secret
POSTGRES_DB=ninaivalaigal_dev

# PgBouncer
PGBOUNCER_TX_PORT=6432
DATABASE_URL=postgresql://nina:dev_password_change_in_production@localhost:6432/ninaivalaigal_dev  # pragma: allowlist secret

# Core API
CORE_API_BASE_URL=http://192.168.66.131:8000  # Container IP, not localhost
```

## Running Integration Tests

### Option 1: With Port Forwarding (Recommended for Local Development)

**NOT YET CONFIGURED** - Core API container needs port mapping to localhost:8000

```bash
# This will work once container exposes port
source .env.test
conda activate nina
pytest tests/integration/ -v
```

### Option 2: Direct Container IP Access

```bash
# Get Core API container IP
CORE_API_IP=$(container inspect ninaivalaigal-dev-core-api | grep IPAddress | tail -1 | awk -F'"' '{print $4}')

# Run tests with container IP
source .env.test
export CORE_API_BASE_URL="http://$CORE_API_IP:8000"
conda activate nina
pytest tests/integration/test_auth_pgbouncer.py -v
```

### Current Limitation

⚠️ **Integration tests currently skip** because:
- Core API container is NOT exposing port 8000 to localhost
- Tests designed for localhost:8000 but container uses internal IP

**Solution**: Update container startup to expose port 8000, or update tests to use container IP.

## Test Categories

### Auth + PgBouncer Integration (`test_auth_pgbouncer.py`)

Tests authentication flows through PgBouncer connection pooling:

- **`test_signup_persists_bcrypt_hash`**: Validates bcrypt password hashing on signup
- **`test_login_updates_last_login`**: Verifies last_login timestamp updates

**What they validate**:
1. Core API `/auth/signup/individual` and `/auth/login` endpoints
2. PgBouncer transaction mode connection pooling
3. Bcrypt password utilities (`utils/password.py`)
4. Database persistence through PgBouncer

## Troubleshooting

### Tests Skip with "Core API not reachable"

**Cause**: Core API container not exposed on localhost:8000

**Fix**:
1. Update container to expose port: `-p 8000:8000`
2. OR use container IP: `export CORE_API_BASE_URL=http://192.168.66.131:8000`

### Tests Skip with "SASL authentication failed"

**Cause**: Wrong database credentials in `.env.test`

**Fix**: Update `.env.test` with correct credentials:
```bash
POSTGRES_USER=nina
POSTGRES_PASSWORD=dev_password_change_in_production
```

### Database Connection Refused

**Cause**: PgBouncer not running

**Fix**:
```bash
container list | grep pgbouncer  # Verify it's running
container logs ninaivalaigal-dev-pgbouncer-tx  # Check logs
```

## Developer Notes

- Integration tests are **designed to skip gracefully** when services aren't available
- Unit tests in `services/core-api/tests/auth/` don't require running services
- For rapid development, use unit tests (39 tests, all passing)
- Run integration tests before PR/commit to validate full stack

## Last Updated

2025-10-30 - Initial integration test documentation (Developer A work validation)
