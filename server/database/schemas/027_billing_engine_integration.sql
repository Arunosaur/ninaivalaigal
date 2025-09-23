-- SPEC-027: Billing Engine Integration
-- Database schema for Stripe integration, webhook processing, and automated billing

-- Stripe customers tracking
CREATE TABLE IF NOT EXISTS stripe_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    billing_address JSONB,
    tax_id VARCHAR(50),
    default_payment_method VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified
    CONSTRAINT stripe_customer_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    )
);

-- Create indexes for efficient customer lookups
CREATE INDEX IF NOT EXISTS idx_stripe_customers_team_id ON stripe_customers(team_id) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_stripe_customers_org_id ON stripe_customers(org_id) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_stripe_customers_stripe_id ON stripe_customers(stripe_customer_id);

-- Stripe subscriptions tracking
CREATE TABLE IF NOT EXISTS stripe_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) REFERENCES stripe_customers(stripe_customer_id),
    plan_id VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL, -- active, canceled, incomplete, past_due, trialing, unpaid
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP,
    ended_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified
    CONSTRAINT stripe_subscription_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    )
);

-- Create indexes for efficient subscription lookups
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_team_id ON stripe_subscriptions(team_id) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_org_id ON stripe_subscriptions(org_id) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_stripe_id ON stripe_subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_status ON stripe_subscriptions(status);

-- Webhook events tracking
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    api_version VARCHAR(20),
    created_timestamp TIMESTAMP NOT NULL,
    data JSONB NOT NULL,
    livemode BOOLEAN DEFAULT FALSE,
    pending_webhooks INTEGER DEFAULT 0,
    request_id VARCHAR(255),
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    processing_time_ms INTEGER,
    team_id UUID,
    subscription_id VARCHAR(255),
    invoice_id VARCHAR(255),
    actions_taken TEXT[],
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for efficient webhook processing
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_id ON webhook_events(event_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_type ON webhook_events(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON webhook_events(processed, created_timestamp);
CREATE INDEX IF NOT EXISTS idx_webhook_events_team_id ON webhook_events(team_id) WHERE team_id IS NOT NULL;

-- Payment attempts and failures tracking
CREATE TABLE IF NOT EXISTS payment_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES billing_invoices(id) ON DELETE CASCADE,
    stripe_payment_intent_id VARCHAR(255),
    amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'usd',
    status VARCHAR(50) NOT NULL, -- requires_payment_method, requires_confirmation, requires_action, processing, succeeded, canceled
    failure_code VARCHAR(50),
    failure_message TEXT,
    payment_method_id VARCHAR(255),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP,
    retry_strategy VARCHAR(20) DEFAULT 'exponential', -- immediate, exponential, scheduled
    attempted_at TIMESTAMP DEFAULT NOW(),
    succeeded_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified
    CONSTRAINT payment_attempt_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    )
);

-- Create indexes for payment attempts
CREATE INDEX IF NOT EXISTS idx_payment_attempts_team_id ON payment_attempts(team_id) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payment_attempts_org_id ON payment_attempts(org_id) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payment_attempts_invoice_id ON payment_attempts(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payment_attempts_status ON payment_attempts(status);
CREATE INDEX IF NOT EXISTS idx_payment_attempts_retry ON payment_attempts(next_retry_at) WHERE next_retry_at IS NOT NULL;

-- Dunning campaigns for failed payments
CREATE TABLE IF NOT EXISTS dunning_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES billing_invoices(id) ON DELETE CASCADE,
    campaign_type VARCHAR(20) DEFAULT 'standard', -- standard, aggressive, gentle
    status VARCHAR(20) DEFAULT 'active', -- active, paused, completed, canceled
    current_step INTEGER DEFAULT 1,
    total_steps INTEGER DEFAULT 4,
    escalation_days INTEGER[] DEFAULT ARRAY[1, 3, 7, 14],
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    next_action_at TIMESTAMP,
    emails_sent INTEGER DEFAULT 0,
    customer_responded BOOLEAN DEFAULT FALSE,
    resolution_type VARCHAR(50), -- payment_received, subscription_canceled, manual_resolution
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified
    CONSTRAINT dunning_campaign_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    )
);

-- Create indexes for dunning campaigns
CREATE INDEX IF NOT EXISTS idx_dunning_campaigns_team_id ON dunning_campaigns(team_id) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dunning_campaigns_org_id ON dunning_campaigns(org_id) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dunning_campaigns_status ON dunning_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_dunning_campaigns_next_action ON dunning_campaigns(next_action_at) WHERE status = 'active';

-- Dunning campaign actions/emails
CREATE TABLE IF NOT EXISTS dunning_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES dunning_campaigns(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- email, sms, phone_call, account_suspension
    template_name VARCHAR(100),
    recipient_email VARCHAR(255),
    subject VARCHAR(255),
    content TEXT,
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, delivered, failed, bounced
    response_received BOOLEAN DEFAULT FALSE,
    response_type VARCHAR(50), -- payment_made, dispute_raised, unsubscribe, other
    response_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for dunning actions
CREATE INDEX IF NOT EXISTS idx_dunning_actions_campaign_id ON dunning_actions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_dunning_actions_scheduled ON dunning_actions(scheduled_at, status);
CREATE INDEX IF NOT EXISTS idx_dunning_actions_status ON dunning_actions(status);

-- Usage tracking for metered billing
CREATE TABLE IF NOT EXISTS usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES stripe_subscriptions(id),
    metric_name VARCHAR(50) NOT NULL, -- api_calls, storage_gb, memory_tokens, contexts
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    unit_price NUMERIC(10,4), -- price per unit if applicable
    timestamp TIMESTAMP NOT NULL,
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    aggregation_type VARCHAR(20) DEFAULT 'sum', -- sum, max, last_value
    metadata JSONB,
    processed_for_billing BOOLEAN DEFAULT FALSE,
    invoice_line_item_id UUID,
    recorded_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified
    CONSTRAINT usage_record_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    ),
    
    -- Ensure billing period is valid
    CONSTRAINT usage_billing_period_check CHECK (billing_period_start <= billing_period_end)
);

-- Create indexes for usage records
CREATE INDEX IF NOT EXISTS idx_usage_records_team_id ON usage_records(team_id, billing_period_start) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_usage_records_org_id ON usage_records(org_id, billing_period_start) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_usage_records_metric ON usage_records(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_records_billing_period ON usage_records(billing_period_start, billing_period_end);
CREATE INDEX IF NOT EXISTS idx_usage_records_unprocessed ON usage_records(processed_for_billing, billing_period_end) WHERE processed_for_billing = FALSE;

-- Tax calculations and compliance
CREATE TABLE IF NOT EXISTS tax_calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID REFERENCES billing_invoices(id) ON DELETE CASCADE,
    tax_provider VARCHAR(50), -- taxjar, avalara, stripe_tax, manual
    calculation_request JSONB NOT NULL,
    calculation_response JSONB NOT NULL,
    total_tax_amount NUMERIC(10,2) NOT NULL CHECK (total_tax_amount >= 0),
    tax_breakdown JSONB, -- detailed breakdown by jurisdiction
    billing_address JSONB NOT NULL,
    tax_exempt BOOLEAN DEFAULT FALSE,
    tax_exempt_reason VARCHAR(100),
    calculated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for tax calculations
CREATE INDEX IF NOT EXISTS idx_tax_calculations_invoice_id ON tax_calculations(invoice_id);
CREATE INDEX IF NOT EXISTS idx_tax_calculations_provider ON tax_calculations(tax_provider);

-- Invoice PDF storage and delivery
CREATE TABLE IF NOT EXISTS invoice_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID REFERENCES billing_invoices(id) ON DELETE CASCADE,
    document_type VARCHAR(20) DEFAULT 'pdf', -- pdf, html, csv
    file_path TEXT,
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    generation_status VARCHAR(20) DEFAULT 'pending', -- pending, generating, completed, failed
    generated_at TIMESTAMP,
    delivery_method VARCHAR(20) DEFAULT 'email', -- email, download, api
    delivery_status VARCHAR(20) DEFAULT 'pending', -- pending, sent, delivered, failed
    delivery_attempts INTEGER DEFAULT 0,
    last_delivery_attempt TIMESTAMP,
    recipient_email VARCHAR(255),
    download_count INTEGER DEFAULT 0,
    last_downloaded_at TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for invoice documents
CREATE INDEX IF NOT EXISTS idx_invoice_documents_invoice_id ON invoice_documents(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_documents_status ON invoice_documents(generation_status, delivery_status);
CREATE INDEX IF NOT EXISTS idx_invoice_documents_expires ON invoice_documents(expires_at) WHERE expires_at IS NOT NULL;

-- Billing analytics and reporting
CREATE TABLE IF NOT EXISTS billing_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- mrr, arr, churn_rate, ltv, cac
    metric_value NUMERIC(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'usd',
    calculation_method VARCHAR(100),
    metadata JSONB,
    calculated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure either team_id or org_id is specified
    CONSTRAINT billing_metrics_target_check CHECK (
        (team_id IS NOT NULL AND org_id IS NULL) OR 
        (team_id IS NULL AND org_id IS NOT NULL)
    ),
    
    -- Unique constraint for metric per entity per date
    CONSTRAINT unique_billing_metric UNIQUE (team_id, org_id, metric_date, metric_type)
);

-- Create indexes for billing metrics
CREATE INDEX IF NOT EXISTS idx_billing_metrics_team_id ON billing_metrics(team_id, metric_date) WHERE team_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_billing_metrics_org_id ON billing_metrics(org_id, metric_date) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_billing_metrics_type ON billing_metrics(metric_type, metric_date);

-- Functions and triggers for automated processing

-- Function to update subscription status from webhooks
CREATE OR REPLACE FUNCTION update_subscription_from_webhook()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.event_type = 'customer.subscription.updated' AND NEW.processed = TRUE THEN
        UPDATE stripe_subscriptions 
        SET 
            status = (NEW.data->'object'->>'status'),
            current_period_start = to_timestamp((NEW.data->'object'->>'current_period_start')::bigint),
            current_period_end = to_timestamp((NEW.data->'object'->>'current_period_end')::bigint),
            updated_at = NOW()
        WHERE stripe_subscription_id = (NEW.data->'object'->>'id');
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for webhook subscription updates
CREATE TRIGGER update_subscription_webhook AFTER UPDATE ON webhook_events 
FOR EACH ROW EXECUTE FUNCTION update_subscription_from_webhook();

-- Function to automatically retry failed payments
CREATE OR REPLACE FUNCTION schedule_payment_retry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('requires_payment_method', 'requires_action') AND 
       NEW.retry_count < NEW.max_retries THEN
        
        -- Calculate next retry time based on strategy
        IF NEW.retry_strategy = 'immediate' THEN
            NEW.next_retry_at = NOW();
        ELSIF NEW.retry_strategy = 'exponential' THEN
            NEW.next_retry_at = NOW() + INTERVAL '1 hour' * (2 ^ NEW.retry_count);
        ELSE -- scheduled
            NEW.next_retry_at = NOW() + INTERVAL '24 hours';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for payment retry scheduling
CREATE TRIGGER schedule_retry BEFORE INSERT OR UPDATE ON payment_attempts 
FOR EACH ROW EXECUTE FUNCTION schedule_payment_retry();

-- Function to advance dunning campaigns
CREATE OR REPLACE FUNCTION advance_dunning_campaign()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.executed_at IS NOT NULL AND OLD.executed_at IS NULL THEN
        -- Action was just executed, advance campaign if needed
        UPDATE dunning_campaigns 
        SET 
            current_step = current_step + 1,
            emails_sent = emails_sent + 1,
            next_action_at = CASE 
                WHEN current_step < total_steps THEN 
                    NOW() + INTERVAL '1 day' * escalation_days[current_step + 1]
                ELSE NULL
            END,
            updated_at = NOW()
        WHERE id = NEW.campaign_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for dunning campaign advancement
CREATE TRIGGER advance_campaign AFTER UPDATE ON dunning_actions 
FOR EACH ROW EXECUTE FUNCTION advance_dunning_campaign();

-- Function to calculate daily billing metrics
CREATE OR REPLACE FUNCTION calculate_daily_billing_metrics()
RETURNS void AS $$
DECLARE
    target_date DATE := CURRENT_DATE - INTERVAL '1 day';
    team_record RECORD;
BEGIN
    -- Calculate MRR for each team
    FOR team_record IN 
        SELECT DISTINCT t.id as team_id, NULL as org_id
        FROM teams t 
        WHERE t.is_standalone = TRUE
        UNION
        SELECT NULL as team_id, o.id as org_id
        FROM organizations o
    LOOP
        -- Calculate MRR
        INSERT INTO billing_metrics (team_id, org_id, metric_date, metric_type, metric_value, calculation_method)
        SELECT 
            team_record.team_id,
            team_record.org_id,
            target_date,
            'mrr',
            COALESCE(
                (SELECT SUM(
                    CASE 
                        WHEN ss.status = 'active' THEN 
                            (SELECT price FROM unnest(ARRAY['free', 'starter', 'nonprofit']) AS plan_name 
                             JOIN (VALUES ('free', 0), ('starter', 10), ('nonprofit', 5)) AS plans(name, price) 
                             ON plan_name = plans.name WHERE plan_name = ss.plan_id)
                        ELSE 0
                    END
                )
                FROM stripe_subscriptions ss 
                WHERE (ss.team_id = team_record.team_id OR ss.org_id = team_record.org_id)
                AND ss.current_period_end >= target_date), 
                0
            ),
            'subscription_based'
        ON CONFLICT (team_id, org_id, metric_date, metric_type) 
        DO UPDATE SET 
            metric_value = EXCLUDED.metric_value,
            calculated_at = NOW();
    END LOOP;
END;
$$ language 'plpgsql';

-- Views for convenient data access

-- Active subscriptions view
CREATE OR REPLACE VIEW active_subscriptions AS
SELECT 
    ss.*,
    COALESCE(t.name, o.name) as entity_name,
    CASE WHEN t.id IS NOT NULL THEN 'team' ELSE 'organization' END as entity_type,
    sc.email as billing_email,
    sc.billing_address
FROM stripe_subscriptions ss
LEFT JOIN teams t ON ss.team_id = t.id
LEFT JOIN organizations o ON ss.org_id = o.id
LEFT JOIN stripe_customers sc ON ss.stripe_customer_id = sc.stripe_customer_id
WHERE ss.status IN ('active', 'trialing', 'past_due');

-- Payment failures requiring attention
CREATE OR REPLACE VIEW failed_payments_summary AS
SELECT 
    pa.*,
    bi.invoice_number,
    bi.due_date,
    COALESCE(t.name, o.name) as entity_name,
    sc.email as billing_email,
    CASE 
        WHEN pa.retry_count >= pa.max_retries THEN 'max_retries_reached'
        WHEN pa.next_retry_at < NOW() THEN 'ready_for_retry'
        ELSE 'scheduled_for_retry'
    END as retry_status
FROM payment_attempts pa
JOIN billing_invoices bi ON pa.invoice_id = bi.id
LEFT JOIN teams t ON pa.team_id = t.id
LEFT JOIN organizations o ON pa.org_id = o.id
LEFT JOIN stripe_customers sc ON (sc.team_id = pa.team_id OR sc.org_id = pa.org_id)
WHERE pa.status NOT IN ('succeeded', 'canceled');

-- Dunning campaigns requiring action
CREATE OR REPLACE VIEW active_dunning_campaigns AS
SELECT 
    dc.*,
    bi.invoice_number,
    bi.amount_due,
    COALESCE(t.name, o.name) as entity_name,
    sc.email as billing_email,
    COUNT(da.id) as total_actions,
    COUNT(da.id) FILTER (WHERE da.status = 'sent') as actions_sent
FROM dunning_campaigns dc
JOIN billing_invoices bi ON dc.invoice_id = bi.id
LEFT JOIN teams t ON dc.team_id = t.id
LEFT JOIN organizations o ON dc.org_id = o.id
LEFT JOIN stripe_customers sc ON (sc.team_id = dc.team_id OR sc.org_id = dc.org_id)
LEFT JOIN dunning_actions da ON dc.id = da.campaign_id
WHERE dc.status = 'active'
GROUP BY dc.id, bi.invoice_number, bi.amount_due, t.name, o.name, sc.email;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated_users;
GRANT SELECT ON ALL VIEWS IN SCHEMA public TO authenticated_users;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated_users;

-- Create initial webhook event types for reference
INSERT INTO webhook_events (event_id, event_type, api_version, created_timestamp, data, livemode, processed) 
VALUES 
    ('evt_example_payment_succeeded', 'invoice.payment_succeeded', '2023-10-16', NOW(), '{"object": "event"}', FALSE, TRUE),
    ('evt_example_payment_failed', 'invoice.payment_failed', '2023-10-16', NOW(), '{"object": "event"}', FALSE, TRUE),
    ('evt_example_subscription_updated', 'customer.subscription.updated', '2023-10-16', NOW(), '{"object": "event"}', FALSE, TRUE)
ON CONFLICT (event_id) DO NOTHING;
