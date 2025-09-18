#!/usr/bin/env bash
# Database performance monitoring and statistics
set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5433}"
POSTGRES_USER="${POSTGRES_USER:-nina}"
POSTGRES_DB="${POSTGRES_DB:-nina}"

log(){ printf "\033[1;34m[stats]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

need(){ command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

run_query(){
  PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    --host="$POSTGRES_HOST" \
    --port="$POSTGRES_PORT" \
    --username="$POSTGRES_USER" \
    --dbname="$POSTGRES_DB" \
    --quiet \
    --tuples-only \
    --command="$1"
}

main(){
  need psql
  
  log "Database Statistics for $POSTGRES_DB"
  echo "=================================="
  
  # Top 20 queries by execution time
  log "Top 20 Slowest Queries:"
  echo "SELECT query, mean_exec_time, calls, total_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 20;" | \
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
      --host="$POSTGRES_HOST" \
      --port="$POSTGRES_PORT" \
      --username="$POSTGRES_USER" \
      --dbname="$POSTGRES_DB" \
      --expanded \
      2>/dev/null || echo "pg_stat_statements not available"
  
  echo ""
  
  # Database size
  echo "Database Size:"
  run_query "SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB')) as size;"
  echo ""
  
  # Table sizes
  echo "Top 5 Largest Tables:"
  run_query "
    SELECT 
      schemaname,
      tablename,
      pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
    FROM pg_tables 
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
    LIMIT 5;
  "
  echo ""
  
  # Connection stats
  echo "Connection Statistics:"
  run_query "
    SELECT 
      state,
      COUNT(*) as connections
    FROM pg_stat_activity 
    WHERE datname = '$POSTGRES_DB'
    GROUP BY state
    ORDER BY connections DESC;
  "
  echo ""
  
  # Enable pg_stat_statements if not already enabled
  EXTENSION_EXISTS=$(run_query "SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_stat_statements';" || echo "0")
  
  if [[ "$EXTENSION_EXISTS" -eq "0" ]]; then
    log "Enabling pg_stat_statements extension..."
    run_query "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;" || log "Failed to enable pg_stat_statements (may need superuser)"
  fi
  
  # Top slow queries (if pg_stat_statements is available)
  echo "Top 5 Slowest Queries (avg time):"
  run_query "
    SELECT 
      ROUND(mean_exec_time::numeric, 2) as avg_ms,
      calls,
      ROUND((total_exec_time/1000)::numeric, 2) as total_sec,
      LEFT(query, 80) as query_preview
    FROM pg_stat_statements 
    WHERE calls > 1
    ORDER BY mean_exec_time DESC 
    LIMIT 5;
  " 2>/dev/null || echo "pg_stat_statements not available"
  echo ""
  
  # Vector extension check
  echo "Vector Extension:"
  VECTOR_EXISTS=$(run_query "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';" || echo "0")
  if [[ "$VECTOR_EXISTS" -gt "0" ]]; then
    echo "✅ pgvector extension enabled"
    # Vector table stats if any exist
    VECTOR_TABLES=$(run_query "
      SELECT COUNT(*) 
      FROM information_schema.columns 
      WHERE data_type = 'USER-DEFINED' 
      AND udt_name = 'vector';
    " || echo "0")
    echo "   Vector columns found: $VECTOR_TABLES"
  else
    echo "❌ pgvector extension not found"
  fi
  echo ""
  
  # Recent activity
  echo "Recent Activity (last 5 minutes):"
  run_query "
    SELECT 
      query_start,
      state,
      LEFT(query, 60) as query_preview
    FROM pg_stat_activity 
    WHERE datname = '$POSTGRES_DB'
    AND query_start > NOW() - INTERVAL '5 minutes'
    AND query NOT LIKE '%pg_stat_activity%'
    ORDER BY query_start DESC
    LIMIT 5;
  "
}

main "$@"
