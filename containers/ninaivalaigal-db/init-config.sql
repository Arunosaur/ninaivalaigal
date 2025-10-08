-- Ninaivalaigal Database Configuration
-- Performance and security optimizations

-- Configure pg_stat_statements for API monitoring (SPEC-018)
ALTER SYSTEM SET pg_stat_statements.max = 10000;
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET pg_stat_statements.track_utility = on;

-- Configure auto_explain for performance optimization (SPEC-069)
ALTER SYSTEM SET auto_explain.log_min_duration = '1000'; -- Log queries > 1s
ALTER SYSTEM SET auto_explain.log_analyze = on;
ALTER SYSTEM SET auto_explain.log_buffers = on;

-- Configure pgAudit for compliance (SPEC-065)
ALTER SYSTEM SET pgaudit.log = 'write, ddl';
ALTER SYSTEM SET pgaudit.log_catalog = off;

-- Configure pg_cron for auto-healing (SPEC-071)
ALTER SYSTEM SET cron.database_name = 'postgres';

-- Create cron job for pg_stat_statements cleanup
SELECT cron.schedule('cleanup-pg-stat', '0 2 * * *', 'SELECT pg_stat_statements_reset()');

-- Grant access for monitoring
GRANT EXECUTE ON FUNCTION pg_stat_statements_reset() TO PUBLIC;

-- Log configuration complete
DO $$
BEGIN
    RAISE NOTICE 'Ninaivalaigal database configured for production';
END $$;
