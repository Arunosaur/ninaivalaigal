# SPEC-147 Billing Architecture - Entity Relationship Diagram

## Complete ER Structure with Hierarchical Billing

```mermaid
erDiagram
    %% Core Entity Hierarchy
    Organization ||--o{ Team : "contains"
    Team ||--o{ User : "has members"
    Organization ||--o{ User : "has members"

    %% Billing Entity Hierarchy (SPEC-147)
    Organization ||--o| BillingEntity : "has billing"
    Team ||--o| BillingEntity : "has billing"
    User ||--o| BillingEntity : "has billing"

    %% Billing Relationships
    BillingEntity ||--o{ UsageQuota : "has quotas"
    BillingEntity ||--o{ UsageEvent : "generates events"
    BillingEntity ||--o{ UsageBlock : "may have blocks"
    BillingEntity ||--o{ PaymentResponsibility : "has payment"
    BillingEntity ||--|| StripeCustomer : "syncs with"

    %% Usage Tracking (3-Dimensional)
    UsageQuota ||--o{ UsageEvent : "tracks against"
    UsageEvent ||--o| UsageBlock : "may trigger"

    %% Payment Hierarchy
    PaymentResponsibility ||--o{ User : "designates payer"
    PaymentResponsibility ||--o{ PaymentTransfer : "tracks transfers"

    %% Stripe Integration
    StripeCustomer ||--o{ StripeSubscription : "has subscriptions"
    StripeSubscription ||--o{ StripeInvoice : "generates invoices"
    StripeInvoice ||--o{ InvoiceLineItem : "contains items"

    %% Audit Trail
    BillingEntity ||--o{ BillingAuditEvent : "logs events"
    UsageBlock ||--o{ BillingAuditEvent : "logs blocks"
    PaymentTransfer ||--o{ BillingAuditEvent : "logs transfers"

    %% Legacy Tables (SPEC-026 - Enhanced)
    Team ||--o| TeamBilling : "has legacy billing"
    Team ||--o{ TeamSubscription : "has subscriptions"
    Team ||--o{ TeamUsageMetrics : "has usage metrics"

    %% Credits & Discounts
    BillingEntity ||--o{ TeamCredit : "has credits"
    BillingEntity ||--o{ DiscountCodeUsage : "uses discounts"
    DiscountCode ||--o{ DiscountCodeUsage : "applied to"

    %% Entity Definitions

    Organization {
        uuid id PK
        string name
        string description
        string domain
        json settings
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    Team {
        uuid id PK
        uuid organization_id FK
        string name
        string description
        string governance_type
        string status
        timestamp created_at
        timestamp updated_at
    }

    User {
        uuid id PK
        string email
        string name
        string account_type
        string subscription_tier
        string role
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    BillingEntity {
        uuid id PK
        string entity_type "organization|team|user"
        uuid entity_id FK
        string plan_tier "free|starter|pro|enterprise"
        string stripe_customer_id
        string billing_email
        string payment_method_id
        jsonb billing_address
        string tax_id
        string currency
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    UsageQuota {
        uuid id PK
        uuid billing_entity_id FK
        string quota_type "storage|retrieval|token"
        bigint limit_value
        bigint used_value
        timestamp period_start
        timestamp period_end
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    UsageEvent {
        uuid id PK
        uuid billing_entity_id FK
        string usage_type "storage|retrieval|token"
        bigint usage_value
        jsonb event_metadata
        timestamp recorded_at
        timestamp processed_at
        uuid billing_period_id FK
    }

    UsageBlock {
        uuid id PK
        uuid billing_entity_id FK
        string block_type "soft|hard"
        string block_reason
        timestamp blocked_at
        timestamp expires_at
        boolean is_active
        uuid created_by FK
        jsonb metadata
    }

    PaymentResponsibility {
        uuid id PK
        uuid billing_entity_id FK
        uuid current_payer_id FK
        jsonb backup_payers
        timestamp grace_period_start
        timestamp grace_period_end
        string transfer_status "active|grace_period|transferred"
        jsonb notifications_sent
        timestamp created_at
        timestamp updated_at
    }

    PaymentTransfer {
        uuid id PK
        uuid payment_responsibility_id FK
        uuid from_user_id FK
        uuid to_user_id FK
        string transfer_reason
        timestamp initiated_at
        timestamp completed_at
        string status "pending|completed|failed"
    }

    StripeCustomer {
        uuid id PK
        uuid billing_entity_id FK
        string stripe_customer_id
        string email
        jsonb metadata
        timestamp last_synced_at
        timestamp created_at
    }

    StripeSubscription {
        uuid id PK
        uuid stripe_customer_id FK
        string stripe_subscription_id
        string plan_id
        string status "active|past_due|canceled|trialing"
        timestamp current_period_start
        timestamp current_period_end
        boolean cancel_at_period_end
        timestamp last_synced_at
    }

    StripeInvoice {
        uuid id PK
        uuid stripe_subscription_id FK
        string stripe_invoice_id
        bigint amount_due
        string currency
        string status "draft|open|paid|void"
        timestamp period_start
        timestamp period_end
        timestamp created_at
    }

    InvoiceLineItem {
        uuid id PK
        uuid stripe_invoice_id FK
        string description
        string usage_type "storage|retrieval|token"
        bigint quantity
        bigint unit_price
        bigint amount
    }

    BillingAuditEvent {
        uuid id PK
        uuid billing_entity_id FK
        string event_type
        jsonb event_data
        uuid user_id FK
        string ip_address
        string user_agent
        timestamp recorded_at
    }

    TeamBilling {
        uuid id PK
        uuid team_id FK
        string stripe_customer_id
        string billing_email
        string payment_method_id
        jsonb billing_address
        string currency
        timestamp created_at
        timestamp updated_at
    }

    TeamSubscription {
        uuid id PK
        uuid team_id FK
        string plan_id
        string status
        timestamp current_period_start
        timestamp current_period_end
        timestamp trial_start
        timestamp trial_end
        boolean cancel_at_period_end
        timestamp created_at
    }

    TeamUsageMetrics {
        uuid id PK
        uuid team_id FK
        timestamp period_start
        timestamp period_end
        integer memory_count
        integer api_calls
        bigint storage_bytes
        bigint retrieval_count "NEW"
        bigint token_processed "NEW"
        integer context_count
        integer member_count
        timestamp recorded_at
    }

    TeamCredit {
        uuid id PK
        uuid billing_entity_id FK
        decimal amount
        decimal used_amount
        decimal remaining_amount
        uuid granted_by FK
        timestamp expires_at
        string reason
        timestamp created_at
    }

    DiscountCode {
        uuid id PK
        string code
        integer percent_off
        integer amount_off
        timestamp expires_at
        integer usage_limit
        integer used_count
        boolean is_active
        timestamp created_at
    }

    DiscountCodeUsage {
        uuid id PK
        uuid discount_code_id FK
        uuid billing_entity_id FK
        timestamp applied_at
        uuid applied_by FK
    }
```

## Hierarchical Billing Design

### 1. Payment Responsibility Hierarchy

```
OrganizationBilling (overrides all)
    ↓
TeamBilling (team-level subscription)
    ↓
UserBilling (individual usage)
```

**Business Rules:**
- If org pays, teams don't pay separately
- If team pays, members don't pay individually
- Clear billing ownership hierarchy

### 2. Usage Limits & Blocking Logic

```mermaid
graph TD
    A[Usage Event] --> B{Check Quota}
    B -->|< 75%| C[Normal Operation]
    B -->|75-99%| D[Soft Block]
    B -->|≥ 100%| E[Hard Block]

    D --> F[Warn User]
    D --> G[Read-Only Access]

    E --> H[Block New Operations]
    E --> I[Notify Admin]
    E --> J[Escalate to Backup Payers]
```

### 3. Three-Dimensional Usage Tracking

```
Storage (GB-month)
├── Memory uploads
├── Context storage
└── File attachments

Retrievals (count)
├── Memory recalls
├── Search queries
└── Context retrievals

Tokens (processed)
├── Text embeddings
├── AI processing
└── Semantic search
```

## Key Relationships

### Payment Transfer Workflow

```mermaid
sequenceDiagram
    participant Payer as Current Payer
    participant System as Billing System
    participant Backup as Backup Payers
    participant Admin as Team Admin

    Payer->>System: Leaves team
    System->>System: Initiate grace period (30 days)
    System->>Backup: Notify backup payers
    System->>Admin: Notify team admin

    alt Day 1-14: Normal Operation
        System->>Backup: Daily reminders
    end

    alt Day 15: Soft Block
        System->>System: Enable read-only mode
        System->>Backup: Urgent notification
    end

    alt Day 30: Hard Block
        System->>System: Block all operations
        System->>Admin: Final warning
    end

    alt Payment Assigned
        Backup->>System: Accept payment responsibility
        System->>System: Transfer complete
        System->>System: Restore full access
    end
```

### Quota Enforcement Flow

```mermaid
stateDiagram-v2
    [*] --> Normal: Usage < 75%
    Normal --> SoftWarning: Usage ≥ 75%
    SoftWarning --> Normal: Usage drops
    SoftWarning --> HardBlock: Usage ≥ 100%
    HardBlock --> SoftWarning: Credits added
    HardBlock --> Normal: Quota reset

    SoftWarning: Soft Block\n- Email notifications\n- In-app warnings\n- Read operations allowed

    HardBlock: Hard Block\n- All new operations blocked\n- Admin notifications\n- Escalation to backup payers
```

## Data Flow

### Usage Metering Pipeline

```mermaid
graph LR
    A[API Request] --> B[Usage Middleware]
    B --> C[Capture Event]
    C --> D[Redis Cache]
    D --> E[Quota Check]
    E -->|OK| F[Allow Request]
    E -->|Exceeded| G[Block Request]
    C --> H[Async Worker]
    H --> I[Usage Events Table]
    I --> J[Aggregation Job]
    J --> K[Update Quotas]
```

### Billing Cycle

```mermaid
graph TD
    A[Month Start] --> B[Reset Quotas]
    B --> C[Track Usage Events]
    C --> D[Daily Aggregation]
    D --> E[Check Limits]
    E --> F[Month End]
    F --> G[Calculate Overages]
    G --> H[Generate Invoice]
    H --> I[Stripe Sync]
    I --> J[Send Notifications]
```

## Migration Strategy

### Phase 1: Enhancement (Weeks 1-2)
- Add fields to `team_usage_metrics` (retrieval_count, token_processed)
- Create new SPEC-147 tables
- Maintain backward compatibility

### Phase 2: Dual Write (Weeks 3-4)
- Write to both old and new structures
- Validate data consistency
- Monitor performance

### Phase 3: Migration (Weeks 5-6)
- Migrate historical data
- Switch reads to new tables
- Keep old tables for rollback

### Phase 4: Deprecation (Months 2-6)
- Mark old tables as deprecated
- Monitor for any remaining usage
- Plan final cleanup

### Phase 5: Cleanup (Month 7+)
- Remove deprecated tables
- Update documentation
- Archive historical data

## Indexes and Performance

### Critical Indexes

```sql
-- BillingEntity lookups
CREATE INDEX idx_billing_entity_type_id ON billing_entities(entity_type, entity_id);
CREATE INDEX idx_billing_entity_stripe ON billing_entities(stripe_customer_id);

-- Usage quota checks (hot path)
CREATE INDEX idx_usage_quota_entity_type ON usage_quotas(billing_entity_id, quota_type, is_active);
CREATE INDEX idx_usage_quota_period ON usage_quotas(period_start, period_end);

-- Usage events (high volume)
CREATE INDEX idx_usage_event_entity_time ON usage_events(billing_entity_id, recorded_at);
CREATE INDEX idx_usage_event_period ON usage_events(billing_period_id);
CREATE INDEX idx_usage_event_type ON usage_events(usage_type, recorded_at);

-- Blocks (enforcement)
CREATE INDEX idx_usage_block_entity_active ON usage_blocks(billing_entity_id, is_active);
CREATE INDEX idx_usage_block_expires ON usage_blocks(expires_at) WHERE is_active = true;

-- Payment responsibility
CREATE INDEX idx_payment_resp_entity ON payment_responsibilities(billing_entity_id);
CREATE INDEX idx_payment_resp_status ON payment_responsibilities(transfer_status);

-- Audit trail
CREATE INDEX idx_audit_entity_time ON billing_audit_events(billing_entity_id, recorded_at);
CREATE INDEX idx_audit_event_type ON billing_audit_events(event_type, recorded_at);
```

## Summary

This ER structure provides:

✅ **Hierarchical Billing** - Org → Team → User with clear payment responsibility
✅ **3D Usage Tracking** - Storage, Retrievals, Tokens
✅ **Quota Enforcement** - Soft/hard blocks with graceful degradation
✅ **Payment Transfer** - 30-day grace period workflow
✅ **Stripe Integration** - Subscription sync and invoicing
✅ **Audit Trail** - Complete compliance tracking
✅ **Backward Compatibility** - Gradual migration from SPEC-026
✅ **Performance** - Optimized indexes for hot paths

The design prevents double charging, ensures graceful payment transfers, and provides production-grade scalability across multiple regions.
