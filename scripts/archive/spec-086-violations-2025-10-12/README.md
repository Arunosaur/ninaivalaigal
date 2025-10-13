# Archived Scripts - SPEC-086 Violations

**Date:** October 12, 2025
**Reason:** Container naming violations

## Archived Files

- `nina-intelligence-stack-start.sh`
- `nina-intelligence-stack-start-unified.sh`

## Violation Details

These scripts violated **SPEC-086: Multi-Runtime Port Allocation** by adding runtime suffixes to container names:

```bash
# ❌ WRONG (what these scripts did)
DB_CONTAINER="ninaivalaigal-${NINA_ENV}-db-${NINA_RUNTIME}"
API_CONTAINER="ninaivalaigal-${NINA_ENV}-api-${NINA_RUNTIME}"

# ✅ CORRECT (SPEC-086 compliant)
DB_CONTAINER="ninaivalaigal-${NINA_ENV}-db"
API_CONTAINER="ninaivalaigal-${NINA_ENV}-api"
```

## Correct Script to Use

Use `scripts/stack-start-complete.sh` which is SPEC-086 compliant:
- Container names: `ninaivalaigal-{env}-{service}` (NO runtime suffix)
- Port allocation: Uses runtime-specific ports via SPEC-086 formula
- PgBouncer mandate: All DB connections through PgBouncer

## Reference

See SPEC-086 documentation:
- `specs/086-multi-runtime-port-allocation/README.md`
- Lines 232-263 show correct container naming
