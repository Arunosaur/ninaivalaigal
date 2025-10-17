# Developer B - Database Connection Fix

**Date:** Oct 16, 2025 @ 1:20 PM
**Issue:** Integration tests failing due to database connection errors

---

## 🔍 Problem Analysis

Based on your screenshots:

### Error 1: Database Connection Failed
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
connection to server at "192.168.64.137", port 6432 failed: FATAL:
no such database: ninaivalaigal_dev
```

### Error 2: Integration Tests Failing
```
test_create_subscription ERROR
test_get_subscription ERROR
test_add_payment_method ERROR
test_get_invoices ERROR
```

---

## ✅ Solutions

### Step 1: Check Database Container Status

```bash
# Check if database is running
container list | grep ninaivalaigal-dev-db

# Check if PgBouncer is running
container list | grep ninaivalaigal-dev-pgbouncer
```

**Expected output:**
```
ninaivalaigal-dev-db          # Should be running
ninaivalaigal-dev-pgbouncer   # Should be running
```

---

### Step 2: Get Current PgBouncer IP

The IP `192.168.64.137` in your test is likely stale.

```bash
# Get current PgBouncer IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "Current PgBouncer IP: $PGB_IP"
```

---

### Step 3: Check if Database Exists

```bash
# Test connection to PgBouncer
psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/postgres"  # pragma: allowlist secret -c "\l" | grep ninaivalaigal_dev  # pragma: allowlist secret
```

**If database doesn't exist, create it:**

```bash
# Create the database
psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/postgres"  # pragma: allowlist secret << EOF
CREATE DATABASE ninaivalaigal_dev;
\c ninaivalaigal_dev
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
EOF
```

---

### Step 4: Run Migrations

```bash
# From project root
cd /Users/swami/WorkSpace/ninaivalaigal

# Run Alembic migrations
alembic upgrade head
```

---

### Step 5: Update Test Configuration

Your tests are using a hardcoded IP. Let's fix that.

**Check your test configuration:**

```bash
# Look at test config
cat tests/integration/test_business_service.py | grep -A5 "192.168"
```

**Update to use environment variable or dynamic IP:**

```python
# Instead of hardcoded:
# DATABASE_URL = "postgresql://nina:pass@192.168.64.137:6432/ninaivalaigal_dev"  # pragma: allowlist secret  # pragma: allowlist secret

# Use environment variable:
import os
PGB_IP = os.getenv('PGBOUNCER_IP', 'localhost')
DATABASE_URL = f"postgresql://nina:dev_password_change_in_production@{PGB_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret
```

**Or get it dynamically:**

```python
import subprocess
import json

def get_pgbouncer_ip():
    """Get PgBouncer container IP dynamically"""
    result = subprocess.run(
        ["container", "inspect", "ninaivalaigal-dev-pgbouncer"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        ip = data[0]['networks'][0]['address'].split('/')[0]
        return ip
    return 'localhost'

PGB_IP = get_pgbouncer_ip()
DATABASE_URL = f"postgresql://nina:dev_password_change_in_production@{PGB_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret
```

---

### Step 6: Test Database Connection

```bash
# Quick connection test
psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret -c "SELECT 1;"
```

**Expected output:**
```
 ?column?
----------
        1
(1 row)
```

---

### Step 7: Re-run Your Tests

```bash
conda activate nina
pytest tests/integration/test_business_service.py -v
```

---

## 🔍 Debugging Checklist

If tests still fail, check these:

### Container Health
```bash
# Check all containers
container list

# Check database logs
container logs ninaivalaigal-dev-db | tail -20

# Check PgBouncer logs
container logs ninaivalaigal-dev-pgbouncer | tail -20
```

### Database Accessibility
```bash
# Test direct database connection (bypassing PgBouncer)
DB_IP=$(container inspect ninaivalaigal-dev-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
psql "postgresql://nina:dev_password_change_in_production@${DB_IP}:5432/ninaivalaigal_dev"  # pragma: allowlist secret -c "SELECT 1;"
```

### Network Connectivity
```bash
# Check if port is accessible
nc -zv ${PGB_IP} 6432
```

---

## 🚀 Complete Fix Script

**Run this to fix everything:**

```bash
#!/usr/bin/env bash
# fix-developer-b-db.sh

set -euo pipefail

echo "🔧 Fixing Developer B Database Connection"
echo "=========================================="
echo ""

# 1. Check containers
echo "1. Checking containers..."
if ! container list | grep -q "ninaivalaigal-dev-db.*running"; then
    echo "❌ Database not running! Starting..."
    cd /Users/swami/WorkSpace/ninaivalaigal
    ./scripts/nv-db-start.sh
fi

if ! container list | grep -q "ninaivalaigal-dev-pgbouncer.*running"; then
    echo "❌ PgBouncer not running! Starting..."
    ./scripts/nv-pgbouncer-start.sh
fi

# 2. Get current IPs
echo "2. Getting container IPs..."
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "   PgBouncer IP: $PGB_IP"

# 3. Check database exists
echo "3. Checking if ninaivalaigal_dev database exists..."
if ! psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/postgres"  # pragma: allowlist secret -tAc "SELECT 1 FROM pg_database WHERE datname='ninaivalaigal_dev'" | grep -q 1; then
    echo "   Creating ninaivalaigal_dev database..."
    psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/postgres"  # pragma: allowlist secret << EOF
CREATE DATABASE ninaivalaigal_dev;
\c ninaivalaigal_dev
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
EOF
else
    echo "   ✅ Database exists"
fi

# 4. Test connection
echo "4. Testing database connection..."
if psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret -c "SELECT 1;" > /dev/null 2>&1; then
    echo "   ✅ Connection successful!"
else
    echo "   ❌ Connection failed!"
    exit 1
fi

# 5. Run migrations
echo "5. Running migrations..."
cd /Users/swami/WorkSpace/ninaivalaigal
alembic upgrade head || echo "   ⚠️  Migrations may have issues (check manually)"

echo ""
echo "=========================================="
echo "✅ Database setup complete!"
echo "=========================================="
echo ""
echo "Current connection string:"
echo "postgresql://nina:***@${PGB_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret
echo ""
echo "Update your test configuration to use:"
echo "export PGBOUNCER_IP=${PGB_IP}"
echo ""
echo "Now run your tests:"
echo "conda activate nina && pytest tests/integration/test_business_service.py -v"
```

**Make it executable and run:**
```bash
chmod +x fix-developer-b-db.sh
./fix-developer-b-db.sh
```

---

## 📝 For Your Test File

**Update `tests/integration/test_business_service.py`:**

Add at the top:

```python
import os
import subprocess
import json

def get_pgbouncer_ip():
    """Get PgBouncer container IP dynamically"""
    try:
        result = subprocess.run(
            ["container", "inspect", "ninaivalaigal-dev-pgbouncer"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data[0]['networks'][0]['address'].split('/')[0]
    except:
        return os.getenv('PGBOUNCER_IP', 'localhost')

# Use in your database URL
PGB_IP = get_pgbouncer_ip()
DATABASE_URL = f"postgresql://nina:dev_password_change_in_production@{PGB_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret
```

---

## ✅ Success Criteria

Your tests should pass when:

- ✅ Both containers running
- ✅ Database exists
- ✅ Connection successful
- ✅ All 4 tests pass

---

## 🆘 Still Not Working?

### Check Developer A's Progress

Developer A just set up Memory Service. Make sure their database setup is complete:

```bash
# Check what databases exist
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/postgres"  # pragma: allowlist secret -c "\l"
```

### Contact Team

If still blocked:
- Pair with Developer C (backend expert)
- Check with Developer A (they just set up database)
- Review TEAM_STATUS_OCT16.md for team help

---

**You're working on backend services correctly! This is just an infrastructure issue.** 🚀
