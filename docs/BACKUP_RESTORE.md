# Database Backup & Restore Guide

## Overview

The ninaivalaigal project includes automated backup and restore capabilities for the PostgreSQL database with pgvector extension.

## Backup Process

### Manual Backup

```bash
# Basic backup (uses defaults from .env)
./scripts/backup-db.sh

# Custom backup location
BACKUP_DIR=/custom/path ./scripts/backup-db.sh

# Custom retention (default: 14 days)
RETENTION_DAYS=7 ./scripts/backup-db.sh
```

### Automated Backups

Set up nightly backups via cron:

```bash
# Edit crontab
crontab -e

# Add nightly backup at 2 AM
0 2 * * * cd /path/to/ninaivalaigal && ./scripts/backup-db.sh >> /var/log/ninaivalaigal-backup.log 2>&1
```

### Backup Files

- **Location**: `/srv/ninaivalaigal/backups/` (configurable via `BACKUP_DIR`)
- **Format**: `ninaivalaigal_YYYYMMDD_HHMMSS.dump`
- **Compression**: pg_dump custom format with level 9 compression
- **Retention**: 14 days (configurable via `RETENTION_DAYS`)

## Restore Process

### Quick Restore to New Database

```bash
# Restore to timestamped database
./scripts/restore-db.sh /srv/ninaivalaigal/backups/ninaivalaigal_20240101_120000.dump

# Restore to specific database name
./scripts/restore-db.sh backup.dump nina_test
```

### Production Restore (Careful!)

```bash
# 1. Stop the stack
make stack-down

# 2. Backup current data first
./scripts/backup-db.sh

# 3. Drop and recreate main database
PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p 5433 -U nina -d postgres -c "DROP DATABASE IF EXISTS nina;"
PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p 5433 -U nina -d postgres -c "CREATE DATABASE nina;"

# 4. Restore from backup
PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
  -h localhost -p 5433 -U nina -d nina \
  --verbose --clean --if-exists \
  /srv/ninaivalaigal/backups/ninaivalaigal_20240101_120000.dump

# 5. Restart stack
make stack-up
```

## Verification Steps

### Test Backup Integrity

```bash
# Create test restore
./scripts/restore-db.sh /srv/ninaivalaigal/backups/latest.dump nina_test

# Verify table count matches
PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p 5433 -U nina -d nina_test -c "
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables 
ORDER BY schemaname, tablename;
"

# Test pgvector functionality
PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p 5433 -U nina -d nina_test -c "
SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';
"

# Cleanup test database
PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p 5433 -U nina -d postgres -c "DROP DATABASE nina_test;"
```

### Monitor Backup Health

```bash
# Check recent backups
ls -lah /srv/ninaivalaigal/backups/

# Verify backup sizes (should be consistent)
du -h /srv/ninaivalaigal/backups/*.dump | tail -5

# Test latest backup
LATEST_BACKUP=$(ls -t /srv/ninaivalaigal/backups/ninaivalaigal_*.dump | head -1)
./scripts/restore-db.sh "$LATEST_BACKUP" nina_backup_test
```

## Troubleshooting

### Common Issues

**Permission Denied**
```bash
# Ensure backup directory exists and is writable
sudo mkdir -p /srv/ninaivalaigal/backups
sudo chown $(whoami):$(whoami) /srv/ninaivalaigal/backups
```

**Connection Refused**
```bash
# Ensure database is running
make stack-status

# Check if using correct host/port
echo "POSTGRES_HOST: $POSTGRES_HOST"
echo "POSTGRES_PORT: $POSTGRES_PORT"
```

**Backup Too Large**
```bash
# Check database size
PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p 5433 -U nina -d nina -c "
SELECT pg_size_pretty(pg_database_size('nina')) as db_size;
"

# Consider increasing retention or backup frequency
```

### Recovery Scenarios

**Corrupted Database**
1. Stop stack: `make stack-down`
2. Restore from latest backup (see Production Restore above)
3. Verify data integrity
4. Restart stack: `make stack-up`

**Accidental Data Loss**
1. Don't panic - data may still be in WAL
2. Immediately stop writes: `make stack-down`
3. Create emergency backup: `./scripts/backup-db.sh`
4. Restore from backup before the incident
5. Assess data loss and recovery options

**Disk Space Issues**
1. Check backup directory: `du -sh /srv/ninaivalaigal/backups/`
2. Manually clean old backups: `find /srv/ninaivalaigal/backups/ -name "*.dump" -mtime +7 -delete`
3. Consider reducing retention period

## Best Practices

1. **Test restores regularly** - Backups are only good if they can be restored
2. **Monitor backup sizes** - Sudden changes may indicate issues
3. **Keep multiple backup locations** - Consider offsite storage for critical data
4. **Document recovery procedures** - Ensure team knows the process
5. **Automate verification** - Set up alerts for backup failures

## Integration with CI/CD

The backup scripts integrate with your GitHub Actions workflows:

```yaml
- name: Create backup before deployment
  run: ./scripts/backup-db.sh

- name: Upload backup artifact
  uses: actions/upload-artifact@v4
  with:
    name: pre-deployment-backup
    path: /srv/ninaivalaigal/backups/
```
