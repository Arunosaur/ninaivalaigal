-- SPEC-025: Vendor Admin Console (Medhasys Control Panel)
-- Multi-tenant management, usage analytics, rate limiting, and audit logging
-- Created: 2024-09-22

-- Add vendor admin columns to organizations table
ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'trial', 'cancelled')),
ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'starter', 'professional', 'enterprise')),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Create index for status queries
CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations(status);
CREATE INDEX IF NOT EXISTS idx_organizations_subscription_tier ON organizations(subscription_tier);

-- Tenant rate limits configuration
CREATE TABLE IF NOT EXISTS tenant_rate_limits (
    tenant_id UUID PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
    api_calls_per_minute INTEGER NOT NULL DEFAULT 100,
    memory_operations_per_hour INTEGER NOT NULL DEFAULT 1000,
    storage_limit_gb DECIMAL(10,2) NOT NULL DEFAULT 5.0,
    user_limit INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Admin audit logs for compliance and tracking
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    target_tenant_id UUID REFERENCES organizations(id),
    details JSONB NOT NULL DEFAULT '{}',
    ip_address INET,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes for audit log queries
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin_user ON admin_audit_logs(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_action ON admin_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_tenant ON admin_audit_logs(target_tenant_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_timestamp ON admin_audit_logs(timestamp DESC);

-- API usage tracking (for analytics and billing)
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    request_size_bytes INTEGER,
    response_size_bytes INTEGER
);

-- Indexes for usage analytics
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_tenant_timestamp ON api_usage_logs(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_timestamp ON api_usage_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_status_code ON api_usage_logs(status_code);

-- API performance tracking
CREATE TABLE IF NOT EXISTS api_performance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint VARCHAR(200) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    tenant_id UUID REFERENCES organizations(id),
    error_count INTEGER DEFAULT 0
);

-- Index for performance queries
CREATE INDEX IF NOT EXISTS idx_api_performance_logs_timestamp ON api_performance_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_performance_logs_endpoint ON api_performance_logs(endpoint);

-- System health metrics (aggregated data)
CREATE TABLE IF NOT EXISTS system_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT NOW(),
    details JSONB DEFAULT '{}'
);

-- Index for health metrics
CREATE INDEX IF NOT EXISTS idx_system_health_metrics_name_timestamp ON system_health_metrics(metric_name, timestamp DESC);

-- Tenant usage summary (daily aggregates for performance)
CREATE TABLE IF NOT EXISTS tenant_usage_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES organizations(id),
    date DATE NOT NULL,
    api_calls INTEGER DEFAULT 0,
    memory_operations INTEGER DEFAULT 0,
    storage_mb DECIMAL(10,2) DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    response_time_p95 DECIMAL(8,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, date)
);

-- Index for usage summary queries
CREATE INDEX IF NOT EXISTS idx_tenant_usage_summary_tenant_date ON tenant_usage_summary(tenant_id, date DESC);

-- Function to update tenant usage summary
CREATE OR REPLACE FUNCTION update_tenant_usage_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Update daily usage summary when API calls are logged
    INSERT INTO tenant_usage_summary (tenant_id, date, api_calls)
    VALUES (NEW.tenant_id, DATE(NEW.timestamp), 1)
    ON CONFLICT (tenant_id, date)
    DO UPDATE SET
        api_calls = tenant_usage_summary.api_calls + 1,
        created_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update usage summary
DROP TRIGGER IF EXISTS trigger_update_usage_summary ON api_usage_logs;
CREATE TRIGGER trigger_update_usage_summary
    AFTER INSERT ON api_usage_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_tenant_usage_summary();

-- Function to clean old logs (data retention)
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $$
BEGIN
    -- Keep API usage logs for 90 days
    DELETE FROM api_usage_logs
    WHERE timestamp < NOW() - INTERVAL '90 days';

    -- Keep performance logs for 30 days
    DELETE FROM api_performance_logs
    WHERE timestamp < NOW() - INTERVAL '30 days';

    -- Keep admin audit logs for 2 years (compliance)
    DELETE FROM admin_audit_logs
    WHERE timestamp < NOW() - INTERVAL '2 years';

    -- Keep system health metrics for 1 year
    DELETE FROM system_health_metrics
    WHERE timestamp < NOW() - INTERVAL '1 year';

    -- Keep usage summary for 3 years (business analytics)
    DELETE FROM tenant_usage_summary
    WHERE date < CURRENT_DATE - INTERVAL '3 years';
END;
$$ LANGUAGE plpgsql;

-- Add vendor admin role to RBAC if not exists
INSERT INTO roles (name, description, permissions)
VALUES ('vendor_admin', 'Vendor Administrator with full system access',
        '["system:read", "system:write", "tenant:manage", "audit:read", "billing:manage"]'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Create view for tenant overview (commonly used in admin console)
CREATE OR REPLACE VIEW tenant_overview AS
SELECT
    o.id as tenant_id,
    o.name as organization_name,
    o.status,
    o.subscription_tier,
    o.created_at,
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT m.id) as total_memories,
    COALESCE(SUM(LENGTH(m.content)), 0) / (1024 * 1024) as storage_used_mb,
    COALESCE(MAX(u.last_login), o.created_at) as last_active,
    COALESCE(trl.api_calls_per_minute, 100) as api_calls_per_minute,
    COALESCE(trl.storage_limit_gb, 5.0) as storage_limit_gb
FROM organizations o
LEFT JOIN users u ON u.organization_id = o.id
LEFT JOIN memories m ON m.user_id = u.id
LEFT JOIN tenant_rate_limits trl ON trl.tenant_id = o.id
GROUP BY o.id, o.name, o.status, o.subscription_tier, o.created_at,
         trl.api_calls_per_minute, trl.storage_limit_gb;

-- Comments for documentation
COMMENT ON TABLE tenant_rate_limits IS 'Rate limiting configuration per tenant for API throttling';
COMMENT ON TABLE admin_audit_logs IS 'Audit trail for all vendor admin actions for compliance';
COMMENT ON TABLE api_usage_logs IS 'Detailed API usage tracking for analytics and billing';
COMMENT ON TABLE api_performance_logs IS 'API performance metrics for monitoring';
COMMENT ON TABLE system_health_metrics IS 'System-wide health and performance metrics';
COMMENT ON TABLE tenant_usage_summary IS 'Daily aggregated usage metrics per tenant';
COMMENT ON VIEW tenant_overview IS 'Consolidated view of tenant information for admin dashboard';

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_rate_limits TO nina;
GRANT SELECT, INSERT ON admin_audit_logs TO nina;
GRANT SELECT, INSERT ON api_usage_logs TO nina;
GRANT SELECT, INSERT ON api_performance_logs TO nina;
GRANT SELECT, INSERT ON system_health_metrics TO nina;
GRANT SELECT, INSERT, UPDATE ON tenant_usage_summary TO nina;
GRANT SELECT ON tenant_overview TO nina;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO nina;
