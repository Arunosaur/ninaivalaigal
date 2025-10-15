#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Query Performance Monitoring Script
# SPEC-099 Phase 1: Database Optimization

set -euo pipefail

DB_HOST="${DB_HOST:-192.168.64.135}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ninaivalaigal_dev}"
DB_USER="${DB_USER:-nina}"
DB_PASSWORD="${DB_PASSWORD:-dev_password_change_in_production}"

export PGPASSWORD="$DB_PASSWORD"

echo "🔍 GraphOps Query Performance Monitor"
echo "======================================"
echo ""

# Reset pg_stat_statements if requested
if [[ "${1:-}" == "--reset" ]]; then
    echo "🔄 Resetting pg_stat_statements..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "SELECT pg_stat_statements_reset();" > /dev/null
    echo "✅ Statistics reset"
    echo ""
fi

# Check current query statistics
echo "📊 Cypher Query Statistics:"
echo ""
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -c "SELECT COUNT(*) FROM pg_stat_statements;" &>/dev/null; then
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT
    substring(query, 1, 80) as query_preview,
    calls,
    round(mean_exec_time::numeric, 2) as mean_ms,
    round(stddev_exec_time::numeric, 2) as stddev_ms,
    round(min_exec_time::numeric, 2) as min_ms,
    round(max_exec_time::numeric, 2) as max_ms
FROM pg_stat_statements
WHERE query LIKE '%cypher%'
   OR query LIKE '%ag_catalog%'
   OR query LIKE '%ninaivalaigal_intelligence%'
ORDER BY mean_exec_time DESC
LIMIT 10;
EOF
else
    echo "⚠️  pg_stat_statements not loaded (requires shared_preload_libraries config + restart)"
    echo "   Check PostgreSQL logs for query timing information instead"
fi

echo ""
echo "📈 Index Usage Statistics:"
echo ""
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT
    schemaname,
    relname as tablename,
    indexrelname as indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'ninaivalaigal_intelligence'
ORDER BY idx_scan DESC;
EOF

echo ""
echo "🗄️  Table Statistics:"
echo ""
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT
    schemaname,
    relname as tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'ninaivalaigal_intelligence'
ORDER BY n_live_tup DESC;
EOF

echo ""
echo "💾 Database Size:"
echo ""
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT
    pg_size_pretty(pg_database_size('ninaivalaigal_dev')) as total_size,
    pg_size_pretty(pg_table_size('ninaivalaigal_intelligence._ag_label_vertex')) as vertex_size,
    pg_size_pretty(pg_table_size('ninaivalaigal_intelligence._ag_label_edge')) as edge_size;
EOF

echo ""
echo "✅ Monitoring complete"
echo ""
echo "Usage:"
echo "  ./scripts/monitor-query-performance.sh         # View current statistics"
echo "  ./scripts/monitor-query-performance.sh --reset # Reset statistics and view"
