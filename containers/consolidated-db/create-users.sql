-- nina-intelligence-db User Management
-- Environment-specific users with proper security separation
-- Follows nina_{env}_user naming convention

-- Note: POSTGRES_DB environment variable is used by init scripts
-- This script runs after database creation, grants work with current_database()

-- Create read-only user for analytics
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nina_readonly') THEN
        CREATE ROLE nina_readonly WITH LOGIN PASSWORD 'readonly_secure_password';
    END IF;
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO nina_readonly', current_database());
    EXECUTE 'GRANT USAGE ON SCHEMA public TO nina_readonly';
    EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA public TO nina_readonly';
    EXECUTE 'GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO nina_readonly';
END $$;

-- Create API user with limited permissions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nina_api') THEN
        CREATE ROLE nina_api WITH LOGIN PASSWORD 'api_secure_password';
    END IF;
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO nina_api', current_database());
    EXECUTE 'GRANT USAGE ON SCHEMA public TO nina_api';
    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nina_api';
    EXECUTE 'GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO nina_api';
END $$;

-- Create admin user for migrations
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nina_admin') THEN
        CREATE ROLE nina_admin WITH LOGIN PASSWORD 'admin_secure_password' CREATEDB;
    END IF;
    EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE %I TO nina_admin', current_database());
END $$;
