#!/bin/bash
set -euo pipefail

# SPEC-011: Migration runner for memory lifecycle management
# Usage: ./scripts/run-migration.sh <migration-file>

MIGRATION_FILE="${1:-}"

if [[ -z "$MIGRATION_FILE" ]]; then
    echo "❌ Usage: $0 <migration-file>"
    exit 1
fi

if [[ ! -f "$MIGRATION_FILE" ]]; then
    echo "❌ Migration file not found: $MIGRATION_FILE"
    exit 1
fi

# Get database connection details from existing config system
if [[ -z "${DATABASE_URL:-}" && -z "${NINAIVALAIGAL_DATABASE_URL:-}" ]]; then
    echo "❌ No database URL configured. Set DATABASE_URL or NINAIVALAIGAL_DATABASE_URL"
    exit 1
fi

DATABASE_URL="${DATABASE_URL:-${NINAIVALAIGAL_DATABASE_URL}}"

echo "🔄 Running migration: $(basename "$MIGRATION_FILE")"
echo "📍 Database: $DATABASE_URL"

# Check if psql is available
if ! command -v psql >/dev/null 2>&1; then
    echo "❌ psql not found. Please install PostgreSQL client tools."
    exit 1
fi

# Run the migration
if psql "$DATABASE_URL" -f "$MIGRATION_FILE"; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi
