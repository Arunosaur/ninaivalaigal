# Enterprise Intelligence Model - Complete 3-Tier Architecture
## Organizations, Teams, and Users with Full Provenance Tracking

**Status**: ✅ PRODUCTION OPERATIONAL
**Version**: 2.0 (Complete 3-Tier System)
**Last Updated**: October 23, 2025
**Migrations Applied**: 0115-0120 ✅

---

## 🏗️ Architecture Overview

The ninaivalaigal platform now features a **complete 3-tier enterprise intelligence system** with consistent provenance tracking, lifecycle management, and analytical capabilities across all organizational entities:

```
┌─────────────────────────────────────────────────────────────┐
│                  ORGANIZATIONS (Tier 1)                     │
│  Corporate Structure | M&A History | Subsidiaries           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ├──────────────────────────┐
                   ▼                          ▼
       ┌──────────────────────┐   ┌──────────────────────┐
       │   TEAMS (Tier 2)     │   │   USERS (Tier 3)     │
       │  Team Provenance     │   │  Employment          │
       │  Operational Status  │   │  Provenance          │
       │  Governance          │   │  Reporting Chain     │
       └──────────────────────┘   └──────────────────────┘
```

---

## 📊 Tier 1: Organizations (Corporate Intelligence)

### Dimensions

#### **Dimension 1: Organization Origin**
Tracks how the organization came into existence.

| origin | Meaning | Use Case |
|--------|---------|----------|
| `founding` | Originally created entity | Parent company, startup |
| `acquired` | Purchased via M&A | Acquired subsidiary |
| `merger` | Combined from multiple orgs | Merger of equals |
| `subsidiary` | Division of parent company | Regional office, division |
| `spin_off` | Separated from parent | IPO spin-off, divestiture |
| `joint_venture` | Co-owned by multiple parties | Strategic partnership |

#### **Dimension 2: Organization Status**
Current operational state of the organization.

| organization_status | Meaning | Use Case |
|---------------------|---------|----------|
| `active` | Currently operating | Normal business |
| `acquired` | Now part of parent company | Post-M&A integration |
| `merged` | Combined with another org | Merger completion |
| `dissolved` | Shut down/closed | Business closure |
| `dormant` | Inactive but not dissolved | Holding company |
| `bankrupt` | Insolvent | Chapter 11/bankruptcy |

#### **Dimension 3: Corporate Lineage**
Tracks parent-subsidiary relationships and M&A history.

**Fields**:
- `parent_organization_id` - Parent company (for subsidiaries)
- `acquired_by_organization_id` - Acquiring company (for M&A)
- `acquisition_date` - When acquired
- `full_corporate_hierarchy` - Array of UUIDs from root to current org

#### **Operational Metadata**
Essential business information.

- `legal_name` - Official registered name
- `tax_id` - EIN/Tax ID
- `headquarters_location` - Primary office
- `employee_count_range` - Size bracket (1-10, 11-50, 51-200, etc.)
- `revenue_tier` - Revenue bracket
- `industry_sector` - Business vertical
- `organization_type` - Legal entity (corporation, LLC, non-profit, etc.)

### Real-World Example: Complex Corporate Structure

```python
# Parent Company
parent_corp = Organization(
    name="MegaCorp International",
    legal_name="MegaCorp International Inc.",
    origin="founding",
    organization_status="active",
    organization_type="corporation",
    founded_date=datetime(1995, 3, 15),
    headquarters_location="San Francisco, CA",
    employee_count_range="1000-5000",
    revenue_tier="500M-1B",
    industry_sector="Enterprise Software",
    corporate_metadata={
        "stock_ticker": "MEGA",
        "public_company": True,
        "board_size": 9
    }
)

# Acquired Subsidiary
acquired_subsidiary = Organization(
    name="TechStartup AI",
    legal_name="TechStartup AI Corporation",
    origin="acquired",
    organization_status="acquired",
    organization_type="corporation",
    founded_date=datetime(2019, 6, 1),
    parent_organization_id=parent_corp.id,
    acquired_by_organization_id=parent_corp.id,
    acquisition_date=datetime(2024, 9, 1),
    headquarters_location="Austin, TX",
    employee_count_range="51-200",
    corporate_metadata={
        "acquisition_price": "$45M",
        "integration_status": "in_progress",
        "retain_brand": True,
        "original_founders_retained": 2
    }
)
```

---

## 👥 Tier 2: Teams (Already Documented in v1.1)

**6 Dimensions**:
1. Organizational Affiliation (ad-hoc vs institutional)
2. Team Origin (native, acquired, merged, partner)
3. Acquisition Lineage
4. Team Lineage (parent_team_id for mergers/splits)
5. Operational Status (active, inactive, sunset, transitioning)
6. Governance Alignment (internal, shared, external)

**See**: `ENTERPRISE_TEAM_MODEL_V1.1.md` for complete team documentation.

---

## 🧑‍💼 Tier 3: Users (Employment Intelligence)

### Dimensions

#### **Dimension 1: User Origin**
Tracks how the user joined the organization.

| origin | Meaning | Use Case |
|--------|---------|----------|
| `native` | Hired directly | Normal employee hire |
| `acquired` | Came via M&A | Employee from acquired company |
| `contractor` | Temporary engagement | 1099 contractor, corp-to-corp |
| `partner` | External collaborator | Partner company employee |
| `intern` | Student/trainee | Internship program |

#### **Dimension 2: Employment Status**
Current employment lifecycle state.

| employment_status | Meaning | Use Case |
|-------------------|---------|----------|
| `active` | Currently employed/engaged | Normal working status |
| `on_leave` | Temporarily away | Sabbatical, parental, medical leave |
| `offboarded` | Terminated/resigned | Former employee (recent) |
| `alumni` | Former employee (historical) | Maintain for records, rehire pool |
| `contractor_expired` | Contract ended | Expired engagement |

#### **Dimension 3: Employment Type**
Classification of employment relationship.

| employment_type | Meaning | Use Case |
|-----------------|---------|----------|
| `full_time` | FTE, W2 employee | Standard employment |
| `part_time` | PT employee | Reduced hours |
| `contractor` | 1099/corp-to-corp | Temporary contractor |
| `intern` | Student program | Internship |
| `consultant` | Advisory role | Short-term expert |

#### **Dimension 4: Employment Governance**
Legal/HR classification of the relationship.

| employment_governance | Meaning | Use Case |
|-----------------------|---------|----------|
| `employee` | W2 employee | Standard employment |
| `contractor` | 1099 contractor | Independent contractor |
| `partner` | External collaborator | Partner company staff |
| `consultant` | Advisory engagement | Expert consultant |

#### **Employment Lineage & Hierarchy**

**Fields**:
- `acquired_from_organization_id` - Original company (for M&A employees)
- `acquisition_date` - When they joined via M&A
- `vendor_organization_id` - Contracting firm (for contractors)
- `hire_date` - Original hire date
- `termination_date` - When employment ended
- `contract_start_date` / `contract_end_date` - Contract duration
- `manager_id` - Direct manager (reporting hierarchy)
- `primary_organization_id` - Main org affiliation
- `full_reporting_chain` - Array of UUIDs from CEO to user

### Real-World Examples

#### Example 1: Acquired Employee (M&A Integration)

```python
acquired_employee = User(
    name="Sarah Johnson",
    email="sarah.johnson@megacorp.com",
    origin="acquired",
    acquired_from_organization_id=techstartup_ai_uuid,
    acquisition_date=datetime(2024, 9, 1),

    employment_status="active",
    employment_type="full_time",
    employment_governance="employee",

    hire_date=datetime(2020, 3, 15),  # Original hire at TechStartup
    primary_organization_id=megacorp_uuid,  # Now part of MegaCorp
    manager_id=integration_manager_uuid,

    employment_metadata={
        "original_company": "TechStartup AI",
        "original_title": "Senior ML Engineer",
        "current_title": "Staff ML Engineer",
        "retention_bonus": True,
        "retention_bonus_date": "2025-09-01",
        "integration_cohort": "2024-Q3",
        "relocation_package": True,
        "visa_status": "H1B",
        "original_salary_band": "L5",
        "current_salary_band": "L6"
    }
)
```

#### Example 2: Contractor (External Vendor)

```python
contractor = User(
    name="Mike Consultant",
    email="mike@acmeconsulting.com",
    origin="contractor",

    employment_status="active",
    employment_type="contractor",
    employment_governance="contractor",

    vendor_organization_id=acme_consulting_uuid,
    contract_start_date=datetime(2024, 1, 1),
    contract_end_date=datetime(2024, 12, 31),
    primary_organization_id=megacorp_uuid,
    manager_id=project_manager_uuid,

    employment_metadata={
        "vendor": "Acme Consulting LLC",
        "contract_type": "corp_to_corp",
        "hourly_rate": 200,
        "max_hours_per_week": 40,
        "project": "Digital Transformation",
        "cost_center": "IT-PROJECTS",
        "purchase_order": "PO-2024-0156",
        "badge_access": "limited",
        "email_access": "vendor_domain"
    }
)
```

#### Example 3: Employee On Leave

```python
employee_on_leave = User(
    name="Jennifer Lee",
    email="jennifer.lee@megacorp.com",
    origin="native",

    employment_status="on_leave",
    employment_type="full_time",
    employment_governance="employee",

    hire_date=datetime(2018, 7, 10),
    primary_organization_id=megacorp_uuid,
    manager_id=dept_manager_uuid,

    employment_metadata={
        "leave_type": "parental",
        "leave_start_date": "2024-10-01",
        "leave_end_date": "2025-01-15",
        "return_to_work_date": "2025-01-20",
        "coverage_plan": "temp_backfill",
        "benefits_continue": True,
        "contact_preference": "emergency_only"
    }
)
```

#### Example 4: Alumni (Former Employee)

```python
alumni_user = User(
    name="David Kim",
    email="david.kim@alumni.megacorp.com",
    origin="native",

    employment_status="alumni",
    employment_type="full_time",  # Was full-time
    employment_governance="employee",

    hire_date=datetime(2015, 2, 20),
    termination_date=datetime(2024, 6, 30),
    primary_organization_id=megacorp_uuid,

    employment_metadata={
        "departure_reason": "resignation",
        "exit_type": "voluntary",
        "eligible_for_rehire": True,
        "final_title": "Senior Engineering Manager",
        "years_of_service": 9.3,
        "alumni_program": True,
        "linkedin_profile": "davidkim-tech",
        "new_company": "Startup XYZ",
        "farewell_message": "Moving to CTO role at startup"
    }
)
```

---

## 🔗 Inter-Tier Relationships

### Organization → Teams
```sql
SELECT * FROM teams WHERE organization_id = $org_id AND status = 'active';
```

### Organization → Users
```sql
SELECT * FROM users WHERE primary_organization_id = $org_id AND employment_status = 'active';
```

### Teams → Users (via TeamMembership)
```sql
SELECT u.* FROM users u
JOIN team_memberships tm ON tm.user_id = u.id
WHERE tm.team_id = $team_id AND tm.status = 'active';
```

### Reporting Hierarchy (User → Manager Chain)
```sql
SELECT * FROM users WHERE $user_id = ANY(full_reporting_chain);
```

### Corporate Hierarchy (Organization → Parent Chain)
```sql
SELECT * FROM organizations WHERE $org_id = ANY(full_corporate_hierarchy);
```

---

## 📈 Analytics Queries

### Query 1: M&A Integration Dashboard
```sql
-- All acquired employees still active
SELECT
    u.name,
    u.email,
    o_from.name AS original_company,
    u.acquisition_date,
    u.hire_date AS original_hire_date,
    EXTRACT(YEAR FROM AGE(NOW(), u.hire_date)) AS years_of_service,
    u.employment_metadata->>'retention_bonus' AS has_retention_bonus
FROM users u
JOIN organizations o_from ON o_from.id = u.acquired_from_organization_id
WHERE u.origin = 'acquired'
  AND u.employment_status = 'active'
ORDER BY u.acquisition_date DESC;
```

### Query 2: Contractor Management
```sql
-- All active contractors with expiring contracts (next 90 days)
SELECT
    u.name,
    u.email,
    vendor_org.name AS vendor,
    u.contract_start_date,
    u.contract_end_date,
    u.contract_end_date - CURRENT_DATE AS days_remaining,
    u.employment_metadata->>'project' AS project
FROM users u
JOIN organizations vendor_org ON vendor_org.id = u.vendor_organization_id
WHERE u.employment_governance = 'contractor'
  AND u.employment_status = 'active'
  AND u.contract_end_date BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '90 days')
ORDER BY u.contract_end_date;
```

### Query 3: Org Chart (Reporting Hierarchy)
```sql
-- Full reporting chain for a user
SELECT
    u.name,
    u.email,
    u.employment_metadata->>'current_title' AS title,
    array_length(u.full_reporting_chain, 1) AS levels_from_ceo
FROM users u
WHERE u.id = $user_id;

-- All direct reports
SELECT
    u.name,
    u.email,
    u.employment_metadata->>'current_title' AS title
FROM users u
WHERE u.manager_id = $manager_id
  AND u.employment_status = 'active'
ORDER BY u.name;
```

### Query 4: Corporate Structure Audit
```sql
-- All subsidiaries under a parent org
SELECT
    o.name,
    o.legal_name,
    o.origin,
    o.organization_status,
    o.acquisition_date,
    o.employee_count_range,
    o.headquarters_location
FROM organizations o
WHERE o.parent_organization_id = $parent_org_id
  AND o.organization_status IN ('active', 'acquired')
ORDER BY o.acquisition_date DESC NULLS LAST;
```

### Query 5: Alumni Rehire Pool
```sql
-- Former employees eligible for rehire
SELECT
    u.name,
    u.email,
    u.termination_date,
    EXTRACT(MONTH FROM AGE(NOW(), u.termination_date)) AS months_since_departure,
    u.employment_metadata->>'final_title' AS last_title,
    u.employment_metadata->>'departure_reason' AS departure_reason
FROM users u
WHERE u.employment_status = 'alumni'
  AND u.employment_metadata->>'eligible_for_rehire' = 'true'
  AND u.termination_date > (CURRENT_DATE - INTERVAL '3 years')
ORDER BY u.termination_date DESC;
```

---

## 🛡️ Data Integrity

### Triggers (Auto-Maintained Fields)

1. **`update_org_corporate_hierarchy()`** - Auto-maintains `full_corporate_hierarchy` array
2. **`update_user_reporting_chain()`** - Auto-maintains `full_reporting_chain` array
3. **`update_team_lineage_path()`** - Auto-maintains `full_lineage_path` array

### Constraints (Business Rules Enforcement)

**Organizations**:
- Acquired orgs must have `acquired_by_organization_id`
- Subsidiaries must have `parent_organization_id`
- No self-parenting (prevent cycles)

**Users**:
- Acquired users must have `acquired_from_organization_id`
- Contractors must have `vendor_organization_id`
- No self-management (prevent cycles)

**Teams**:
- Acquired teams must have `acquired_from_organization_id`
- Ad-hoc teams can't be "acquired" origin
- No self-parenting (prevent cycles)

---

## 📋 Migration History

| Migration | Target | What It Added |
|-----------|--------|---------------|
| `0115_user_columns` | Users | Basic missing fields (username, contexts_limit, etc.) |
| `0116_teams_org_id` | Teams | organization_id for affiliation |
| `0117_team_provenance` | Teams | M&A provenance (origin, acquisition lineage, team lineage) |
| `0118_team_intelligence` | Teams | Status, governance, lineage_path, triggers, constraints |
| `0119_user_provenance` | Users | ✨ Employment provenance, status, governance, reporting chain |
| `0120_org_provenance` | Organizations | ✨ Corporate provenance, structure, hierarchy, triggers |

---

## ✅ Verification Checklist

**Organizations**:
- ✅ Origin tracking (founding, acquired, merger, etc.)
- ✅ Corporate hierarchy (`parent_organization_id`, `full_corporate_hierarchy`)
- ✅ M&A tracking (`acquired_by_organization_id`, `acquisition_date`)
- ✅ Status lifecycle (active, acquired, dissolved, etc.)
- ✅ Operational metadata (legal_name, tax_id, headquarters, etc.)
- ✅ Trigger auto-maintaining hierarchy
- ✅ Constraints preventing invalid states

**Teams**:
- ✅ All 6 dimensions operational
- ✅ Trigger auto-maintaining lineage_path
- ✅ Constraints enforcing business rules

**Users**:
- ✅ Origin tracking (native, acquired, contractor, etc.)
- ✅ Employment status lifecycle (active, on_leave, alumni, etc.)
- ✅ Employment governance (employee, contractor, partner, etc.)
- ✅ Reporting hierarchy (`manager_id`, `full_reporting_chain`)
- ✅ M&A tracking (`acquired_from_organization_id`)
- ✅ Vendor tracking (`vendor_organization_id`)
- ✅ Trigger auto-maintaining reporting chain
- ✅ Constraints preventing invalid states

---

## 🚀 Production Ready

**API Status**: ✅ Healthy and operational
**Database**: ✅ All migrations applied
**Models**: ✅ Fully synchronized with database schema
**Relationships**: ✅ No circular dependencies
**Triggers**: ✅ Auto-maintaining derived fields
**Constraints**: ✅ Enforcing business rules
**Indexes**: ✅ Performance-optimized for common queries

---

## 🎉 What This Enables

**For HR/People Ops**:
- Complete employee lifecycle tracking
- M&A integration management
- Contractor/vendor management
- Alumni rehire pool
- Org chart generation
- Leave management

**For Finance/Legal**:
- Corporate structure tracking
- Subsidiary management
- M&A deal tracking
- Contractor spend analysis
- Cost center allocation
- Tax jurisdiction mapping

**For IT/Security**:
- Access provisioning by employment status
- Offboarding automation
- Contractor access expiration
- Partner collaboration scoping
- Audit trail for compliance

**For Business Intelligence**:
- Workforce composition analytics
- M&A integration metrics
- Contractor vs FTE ratios
- Team evolution tracking
- Corporate structure visualization
- Retention analysis

---

**🏆 The ninaivalaigal platform now has enterprise-grade intelligence across all organizational entities with complete provenance tracking, lifecycle management, and analytical capabilities suitable for Fortune 500 companies.**
