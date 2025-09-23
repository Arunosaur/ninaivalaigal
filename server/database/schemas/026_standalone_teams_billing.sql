-- SPEC-026: Standalone Teams & Flexible Billing System
-- Database schema extensions for comprehensive billing infrastructure

-- Enhanced teams table for standalone teams and billing
ALTER TABLE teams ADD COLUMN IF NOT EXISTS org_id INTEGER NULL;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS billing_plan VARCHAR(50) DEFAULT 'free';
ALTER TABLE teams ADD COLUMN IF NOT EXISTS billing_customer_id VARCHAR(255);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS is_standalone BOOLEAN DEFAULT FALSE;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS upgrade_eligible BOOLEAN DEFAULT TRUE;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS created_by_user_id UUID REFERENCES users(id);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS team_invite_code VARCHAR(32) UNIQUE;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS max_members INTEGER DEFAULT 10;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS description TEXT;

-- Discount codes system
CREATE TABLE IF NOT EXISTS discount_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    percent_off INTEGER CHECK (percent_off >= 1 AND percent_off <= 100),
    amount_off INTEGER CHECK (amount_off >= 1), -- in cents
    expires_at TIMESTAMP,
    usage_limit INTEGER CHECK (usage_limit >= 1),
    used_count INTEGER DEFAULT 0 CHECK (used_count >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either percent_off or amount_off is specified, but not both
    CONSTRAINT discount_type_check CHECK (
        (percent_off IS NOT NULL AND amount_off IS NULL) OR 
        (percent_off IS NULL AND amount_off IS NOT NULL)
    ),
    
    -- Ensure usage doesn't exceed limit
    CONSTRAINT usage_limit_check CHECK (
        usage_limit IS NULL OR used_count <= usage_limit
    )
);

-- Create index for efficient discount code lookups
CREATE INDEX IF NOT EXISTS idx_discount_codes_code ON discount_codes(code) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_discount_codes_expires_at ON discount_codes(expires_at) WHERE is_active = TRUE;

-- Credits system for teams and organizations
CREATE TABLE IF NOT EXISTS team_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL CHECK (amount > 0), -- in dollars
    used_amount NUMERIC(10,2) DEFAULT 0 CHECK (used_amount >= 0),
    remaining_amount NUMERIC(10,2) GENERATED ALWAYS AS (amount - used_amount) STORED,
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMP,
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified, but not both
    CONSTRAINT credit_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    ),
    
    -- Ensure used amount doesn't exceed total amount
    CONSTRAINT used_amount_check CHECK (used_amount <= amount)
);

-- Create indexes for efficient credit lookups
CREATE INDEX IF NOT EXISTS idx_team_credits_team_id ON team_credits(team_id) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_team_credits_org_id ON team_credits(org_id) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_team_credits_expires_at ON team_credits(expires_at);

-- Non-profit applications
CREATE TABLE IF NOT EXISTS nonprofit_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    organization_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    website_url TEXT,
    documentation_urls TEXT[], -- Array of URLs for supporting documents
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'under_review')),
    submitted_at TIMESTAMP DEFAULT NOW(),
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified, but not both
    CONSTRAINT nonprofit_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    )
);

-- Create indexes for efficient nonprofit application lookups
CREATE INDEX IF NOT EXISTS idx_nonprofit_applications_team_id ON nonprofit_applications(team_id) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_nonprofit_applications_org_id ON nonprofit_applications(org_id) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_nonprofit_applications_status ON nonprofit_applications(status);
CREATE INDEX IF NOT EXISTS idx_nonprofit_applications_submitted_at ON nonprofit_applications(submitted_at);

-- Usage tracking for teams and organizations
CREATE TABLE IF NOT EXISTS team_usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    metric_name VARCHAR(50) NOT NULL, -- 'memories', 'contexts', 'api_calls', 'storage_mb', 'members'
    metric_value INTEGER NOT NULL CHECK (metric_value >= 0),
    recorded_date DATE DEFAULT CURRENT_DATE,
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified, but not both
    CONSTRAINT usage_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    ),
    
    -- Ensure billing period is valid
    CONSTRAINT billing_period_check CHECK (billing_period_start <= billing_period_end),
    
    -- Unique constraint to prevent duplicate metrics for same period
    CONSTRAINT unique_usage_metric UNIQUE (team_id, org_id, metric_name, billing_period_start, billing_period_end)
);

-- Create indexes for efficient usage stats lookups
CREATE INDEX IF NOT EXISTS idx_team_usage_stats_team_id ON team_usage_stats(team_id, billing_period_start) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_team_usage_stats_org_id ON team_usage_stats(org_id, billing_period_start) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_team_usage_stats_metric ON team_usage_stats(metric_name, recorded_date);

-- Billing invoices for teams and organizations
CREATE TABLE IF NOT EXISTS billing_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    stripe_invoice_id VARCHAR(255) UNIQUE,
    amount_due NUMERIC(10,2) NOT NULL CHECK (amount_due >= 0),
    amount_paid NUMERIC(10,2) DEFAULT 0 CHECK (amount_paid >= 0),
    currency VARCHAR(3) DEFAULT 'usd',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'open', 'paid', 'void', 'uncollectible')),
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    due_date DATE,
    paid_at TIMESTAMP,
    description TEXT,
    line_items JSONB, -- Detailed line items for the invoice
    discount_codes_applied TEXT[], -- Array of discount codes applied
    credits_used NUMERIC(10,2) DEFAULT 0 CHECK (credits_used >= 0),
    tax_amount NUMERIC(10,2) DEFAULT 0 CHECK (tax_amount >= 0),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified, but not both
    CONSTRAINT invoice_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    ),
    
    -- Ensure billing period is valid
    CONSTRAINT invoice_billing_period_check CHECK (billing_period_start <= billing_period_end),
    
    -- Ensure amounts are consistent
    CONSTRAINT invoice_amount_check CHECK (amount_paid <= amount_due)
);

-- Create indexes for efficient invoice lookups
CREATE INDEX IF NOT EXISTS idx_billing_invoices_team_id ON billing_invoices(team_id, billing_period_start) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_billing_invoices_org_id ON billing_invoices(org_id, billing_period_start) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_billing_invoices_status ON billing_invoices(status);
CREATE INDEX IF NOT EXISTS idx_billing_invoices_due_date ON billing_invoices(due_date) WHERE status IN ('open', 'draft');
CREATE INDEX IF NOT EXISTS idx_billing_invoices_stripe_id ON billing_invoices(stripe_invoice_id) WHERE stripe_invoice_id IS NOT NULL;

-- Discount code usage tracking
CREATE TABLE IF NOT EXISTS discount_code_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discount_code_id UUID REFERENCES discount_codes(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES billing_invoices(id) ON DELETE CASCADE,
    amount_discounted NUMERIC(10,2) NOT NULL CHECK (amount_discounted >= 0),
    used_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified, but not both
    CONSTRAINT discount_usage_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    )
);

-- Create indexes for discount code usage tracking
CREATE INDEX IF NOT EXISTS idx_discount_code_usage_code_id ON discount_code_usage(discount_code_id);
CREATE INDEX IF NOT EXISTS idx_discount_code_usage_team_id ON discount_code_usage(team_id) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_discount_code_usage_org_id ON discount_code_usage(org_id) WHERE org_id IS NOT NULL;

-- Team billing settings
CREATE TABLE IF NOT EXISTS team_billing_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE UNIQUE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE UNIQUE,
    billing_email VARCHAR(255) NOT NULL,
    billing_address JSONB, -- Structured billing address
    tax_id VARCHAR(50),
    auto_pay_enabled BOOLEAN DEFAULT TRUE,
    billing_notifications_enabled BOOLEAN DEFAULT TRUE,
    invoice_delivery_method VARCHAR(20) DEFAULT 'email' CHECK (invoice_delivery_method IN ('email', 'portal', 'both')),
    payment_terms_days INTEGER DEFAULT 30 CHECK (payment_terms_days > 0),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified, but not both
    CONSTRAINT billing_settings_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    )
);

-- Create indexes for billing settings
CREATE INDEX IF NOT EXISTS idx_team_billing_settings_team_id ON team_billing_settings(team_id) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_team_billing_settings_org_id ON team_billing_settings(org_id) WHERE org_id IS NOT NULL;

-- Functions for automatic updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_discount_codes_updated_at BEFORE UPDATE ON discount_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_team_credits_updated_at BEFORE UPDATE ON team_credits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_nonprofit_applications_updated_at BEFORE UPDATE ON nonprofit_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_billing_invoices_updated_at BEFORE UPDATE ON billing_invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_team_billing_settings_updated_at BEFORE UPDATE ON team_billing_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically update discount code usage count
CREATE OR REPLACE FUNCTION increment_discount_code_usage()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE discount_codes 
    SET used_count = used_count + 1
    WHERE id = NEW.discount_code_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for automatic discount code usage tracking
CREATE TRIGGER increment_discount_usage AFTER INSERT ON discount_code_usage FOR EACH ROW EXECUTE FUNCTION increment_discount_code_usage();

-- Function to validate discount code usage limits
CREATE OR REPLACE FUNCTION validate_discount_code_usage()
RETURNS TRIGGER AS $$
DECLARE
    code_record discount_codes%ROWTYPE;
BEGIN
    SELECT * INTO code_record FROM discount_codes WHERE id = NEW.discount_code_id;
    
    -- Check if code is active
    IF NOT code_record.is_active THEN
        RAISE EXCEPTION 'Discount code is not active';
    END IF;
    
    -- Check expiration
    IF code_record.expires_at IS NOT NULL AND code_record.expires_at < NOW() THEN
        RAISE EXCEPTION 'Discount code has expired';
    END IF;
    
    -- Check usage limit
    IF code_record.usage_limit IS NOT NULL AND code_record.used_count >= code_record.usage_limit THEN
        RAISE EXCEPTION 'Discount code usage limit exceeded';
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for discount code validation
CREATE TRIGGER validate_discount_usage BEFORE INSERT ON discount_code_usage FOR EACH ROW EXECUTE FUNCTION validate_discount_code_usage();

-- Views for convenient data access

-- Active discount codes view
CREATE OR REPLACE VIEW active_discount_codes AS
SELECT 
    id,
    code,
    percent_off,
    amount_off,
    expires_at,
    usage_limit,
    used_count,
    (usage_limit IS NULL OR used_count < usage_limit) AS can_be_used,
    (expires_at IS NULL OR expires_at > NOW()) AS not_expired,
    created_at
FROM discount_codes 
WHERE is_active = TRUE
    AND (expires_at IS NULL OR expires_at > NOW())
    AND (usage_limit IS NULL OR used_count < usage_limit);

-- Team billing summary view
CREATE OR REPLACE VIEW team_billing_summary AS
SELECT 
    t.id AS team_id,
    t.name AS team_name,
    t.billing_plan,
    t.is_standalone,
    COUNT(tm.id) AS current_members,
    t.max_members,
    COALESCE(SUM(tc.remaining_amount), 0) AS total_credits,
    COUNT(CASE WHEN na.status = 'approved' THEN 1 END) > 0 AS nonprofit_approved,
    t.created_at
FROM teams t
LEFT JOIN team_memberships tm ON t.id = tm.team_id AND tm.status = 'active'
LEFT JOIN team_credits tc ON t.id = tc.team_id AND (tc.expires_at IS NULL OR tc.expires_at > NOW())
LEFT JOIN nonprofit_applications na ON t.id = na.team_id
WHERE t.is_standalone = TRUE
GROUP BY t.id, t.name, t.billing_plan, t.is_standalone, t.max_members, t.created_at;

-- Usage summary view for current billing period
CREATE OR REPLACE VIEW current_period_usage AS
SELECT 
    team_id,
    org_id,
    metric_name,
    SUM(metric_value) AS total_usage,
    MAX(recorded_date) AS last_recorded,
    billing_period_start,
    billing_period_end
FROM team_usage_stats 
WHERE billing_period_start <= CURRENT_DATE 
    AND billing_period_end >= CURRENT_DATE
GROUP BY team_id, org_id, metric_name, billing_period_start, billing_period_end;

-- Grant permissions (adjust based on your user roles)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated_users;
GRANT SELECT ON ALL VIEWS IN SCHEMA public TO authenticated_users;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated_users;

-- Insert default billing plans data
INSERT INTO discount_codes (code, percent_off, expires_at, usage_limit, created_by, is_active) 
VALUES 
    ('WELCOME10', 10, NOW() + INTERVAL '30 days', 100, (SELECT id FROM users WHERE role = 'admin' LIMIT 1), TRUE),
    ('STARTUP50', 50, NOW() + INTERVAL '90 days', 50, (SELECT id FROM users WHERE role = 'admin' LIMIT 1), TRUE)
ON CONFLICT (code) DO NOTHING;

-- Create initial admin user if not exists (for testing)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE role = 'admin') THEN
        INSERT INTO users (id, email, role, created_at) 
        VALUES (gen_random_uuid(), 'admin@ninaivalaigal.com', 'admin', NOW());
    END IF;
END $$;
