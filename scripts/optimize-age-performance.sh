#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Apache AGE Performance Optimization Script
# SPEC-099 Phase 1: Database Tuning

set -euo pipefail

DB_HOST="${DB_HOST:-192.168.64.135}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ninaivalaigal_dev}"
DB_USER="${DB_USER:-nina}"
DB_PASSWORD="${DB_PASSWORD:-dev_password_change_in_production}"

export PGPASSWORD="$DB_PASSWORD"

echo "🚀 Apache AGE Performance Optimization"
echo "======================================="
echo ""

# Function to execute SQL
execute_sql() {
    local sql="$1"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
}

# 1. Enable Query Logging
echo "📝 Step 1: Enable Query Logging"
execute_sql "ALTER SYSTEM SET log_min_duration_statement = 0;" > /dev/null
execute_sql "SELECT pg_reload_conf();" > /dev/null
echo "✅ Query logging enabled"
echo ""

# 2. Create pg_stat_statements extension
echo "📊 Step 2: Enable pg_stat_statements"
execute_sql "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;" > /dev/null
echo "✅ pg_stat_statements enabled"
echo ""

# 3. VACUUM ANALYZE on graph tables
echo "🧹 Step 3: VACUUM ANALYZE Graph Tables"
execute_sql "VACUUM (ANALYZE, VERBOSE) ninaivalaigal_intelligence._ag_label_vertex;" | grep -E "(INFO|tuples|pages)" || true
execute_sql "VACUUM (ANALYZE, VERBOSE) ninaivalaigal_intelligence._ag_label_edge;" | grep -E "(INFO|tuples|pages)" || true
echo "✅ VACUUM ANALYZE complete"
echo ""

# 4. Create Performance Indexes
echo "🔍 Step 4: Create Performance Indexes"
echo "  Creating index on edge (start_id, end_id)..."
execute_sql "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ag_edge_start_end ON ninaivalaigal_intelligence._ag_label_edge (start_id, end_id);" > /dev/null
echo "  Creating index on edge (start_id)..."
execute_sql "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ag_edge_start ON ninaivalaigal_intelligence._ag_label_edge (start_id);" > /dev/null
echo "  Creating index on edge (end_id)..."
execute_sql "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ag_edge_end ON ninaivalaigal_intelligence._ag_label_edge (end_id);" > /dev/null
echo "✅ Performance indexes created"
echo ""

# 5. Increase Statistics Target
echo "📈 Step 5: Increase Statistics Target"
execute_sql "ALTER TABLE ninaivalaigal_intelligence._ag_label_vertex ALTER COLUMN properties SET STATISTICS 1000;" > /dev/null
execute_sql "ALTER TABLE ninaivalaigal_intelligence._ag_label_edge ALTER COLUMN properties SET STATISTICS 1000;" > /dev/null
execute_sql "ANALYZE ninaivalaigal_intelligence._ag_label_vertex;" > /dev/null
execute_sql "ANALYZE ninaivalaigal_intelligence._ag_label_edge;" > /dev/null
echo "✅ Statistics target increased"
echo ""

# 6. Show Current Configuration
echo "⚙️  Step 6: Database Configuration"
echo ""
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT name, setting, unit, short_desc
FROM pg_settings
WHERE name IN (
    'shared_buffers',
    'effective_cache_size',
    'work_mem',
    'random_page_cost',
    'effective_io_concurrency',
    'max_parallel_workers_per_gather',
    'log_min_duration_statement'
)
ORDER BY name;
EOF

echo ""
echo "📋 Step 7: Index Status"
echo ""
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'ninaivalaigal_intelligence'
ORDER BY tablename, indexname;
EOF

echo ""
echo "✅ Optimization Complete!"
echo ""
echo "Next Steps:"
echo "1. Run benchmarks: cd rust-services/graphops && cargo bench"
echo "2. Monitor queries: ./scripts/monitor-query-performance.sh"
echo "3. Check logs: Look for query execution times in PostgreSQL logs"
echo ""
echo "Session-Level Tuning (add to connection string):"
echo "  SET work_mem = '64MB';"
echo "  SET jit = off;"
echo "  SET enable_seqscan = off;  -- Test only"
echo ""
