-- nina-intelligence-db User Management
-- Environment-specific users with proper security separation
-- Follows nina_{env}_user naming convention

-- Create read-only user for analytics
CREATE USER nina_readonly WITH PASSWORD 'readonly_secure_password';
GRANT CONNECT ON DATABASE ninaivalaigal TO nina_readonly;
GRANT USAGE ON SCHEMA public TO nina_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nina_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO nina_readonly;

-- Create API user with limited permissions
CREATE USER nina_api WITH PASSWORD 'api_secure_password';
GRANT CONNECT ON DATABASE ninaivalaigal TO nina_api;
GRANT USAGE ON SCHEMA public TO nina_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nina_api;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO nina_api;

-- Create admin user for migrations
CREATE USER nina_admin WITH PASSWORD 'admin_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ninaivalaigal TO nina_admin;
ALTER USER nina_admin CREATEDB;
