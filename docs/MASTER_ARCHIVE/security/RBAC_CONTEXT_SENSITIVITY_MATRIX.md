# RBAC Context Sensitivity Matrix

## Overview
This document expands the RBAC permission matrix to include per-context "sensitivity tiers" and unit tests for retention/export functionality as requested in the additional notes.

## Context Sensitivity Tiers

### Tier 1: Public/Low Sensitivity
- **Data Types**: General documentation, public information
- **Retention**: Standard retention policies
- **Export**: Unrestricted for authorized users
- **Access**: All roles (VIEWER and above)

### Tier 2: Internal/Medium Sensitivity
- **Data Types**: Internal communications, project data
- **Retention**: Extended retention with audit trail
- **Export**: Requires MEMBER role or above
- **Access**: MEMBER role minimum

### Tier 3: Confidential/High Sensitivity
- **Data Types**: Personal data, financial information, strategic plans
- **Retention**: Long-term retention with encryption
- **Export**: Requires MAINTAINER role or above
- **Access**: MAINTAINER role minimum

### Tier 4: Restricted/Critical Sensitivity
- **Data Types**: Security credentials, legal documents, compliance data
- **Retention**: Permanent retention with strict access controls
- **Export**: Requires ADMIN role or above
- **Access**: ADMIN role minimum

## Enhanced Permission Matrix

| Resource | Action | VIEWER | MEMBER | MAINTAINER | ADMIN | OWNER | Context Sensitivity |
|----------|--------|--------|--------|------------|-------|-------|-------------------|
| MEMORY   | READ   | T1     | T1-T2  | T1-T3      | T1-T4 | ALL   | Tier-based access |
| MEMORY   | CREATE | -      | T1-T2  | T1-T3      | T1-T4 | ALL   | Creation limits   |
| MEMORY   | EXPORT | T1     | T1-T2  | T1-T3      | T1-T4 | ALL   | Export restrictions|
| CONTEXT  | READ   | T1     | T1-T2  | T1-T3      | T1-T4 | ALL   | Context visibility |
| CONTEXT  | CREATE | -      | T1-T2  | T1-T3      | T1-T4 | ALL   | Scope limitations  |
| BACKUP   | CREATE | -      | -      | T1-T2      | T1-T4 | ALL   | Backup permissions |
| BACKUP   | RESTORE| -      | -      | T1-T2      | T1-T4 | ALL   | Restore permissions|
| AUDIT    | READ   | -      | -      | T1-T2      | T1-T4 | ALL   | Audit access      |

*Legend: T1-T4 = Tier 1 through Tier 4 access, - = No access, ALL = All tiers*

## Retention Policies by Sensitivity Tier

### Tier 1 (Public/Low)
- **Retention Period**: 1 year
- **Archive After**: 6 months
- **Deletion Policy**: Automatic after retention period
- **Backup Frequency**: Weekly
- **Export Format**: JSON, CSV, PDF

### Tier 2 (Internal/Medium)
- **Retention Period**: 3 years
- **Archive After**: 1 year
- **Deletion Policy**: Manual review required
- **Backup Frequency**: Daily
- **Export Format**: Encrypted JSON, PDF with watermarks

### Tier 3 (Confidential/High)
- **Retention Period**: 7 years
- **Archive After**: 2 years
- **Deletion Policy**: Legal review required
- **Backup Frequency**: Real-time replication
- **Export Format**: Encrypted archives with audit trail

### Tier 4 (Restricted/Critical)
- **Retention Period**: Permanent
- **Archive After**: 1 year (encrypted)
- **Deletion Policy**: Prohibited without court order
- **Backup Frequency**: Real-time with geographic distribution
- **Export Format**: Highly encrypted with multi-factor authentication

## Implementation Guidelines

### Context Classification
```python
class ContextSensitivity(Enum):
    PUBLIC = "tier1"
    INTERNAL = "tier2"
    CONFIDENTIAL = "tier3"
    RESTRICTED = "tier4"

def classify_context(context_data):
    """Automatically classify context based on content analysis"""
    sensitivity_keywords = {
        "tier4": ["password  # pragma: allowlist secret", "secret", "credential", "ssn", "credit_card"],
        "tier3": ["confidential", "personal", "financial", "strategic"],
        "tier2": ["internal", "project", "team", "business"],
        "tier1": ["public", "general", "documentation"]
    }
    # Implementation logic here
    return ContextSensitivity.INTERNAL  # Default
```

### Permission Checking with Sensitivity
```python
def check_context_permission(user_role, action, context_sensitivity):
    """Check if user role can perform action on context with given sensitivity"""
    permission_matrix = {
        Role.VIEWER: [ContextSensitivity.PUBLIC],
        Role.MEMBER: [ContextSensitivity.PUBLIC, ContextSensitivity.INTERNAL],
        Role.MAINTAINER: [ContextSensitivity.PUBLIC, ContextSensitivity.INTERNAL, ContextSensitivity.CONFIDENTIAL],
        Role.ADMIN: [ContextSensitivity.PUBLIC, ContextSensitivity.INTERNAL, ContextSensitivity.CONFIDENTIAL, ContextSensitivity.RESTRICTED],
        Role.OWNER: [ContextSensitivity.PUBLIC, ContextSensitivity.INTERNAL, ContextSensitivity.CONFIDENTIAL, ContextSensitivity.RESTRICTED],
        Role.SYSTEM: [ContextSensitivity.PUBLIC, ContextSensitivity.INTERNAL, ContextSensitivity.CONFIDENTIAL, ContextSensitivity.RESTRICTED]
    }

    allowed_sensitivities = permission_matrix.get(user_role, [])
    return context_sensitivity in allowed_sensitivities
```

### Export Restrictions
```python
def validate_export_request(user_role, context_sensitivity, export_format):
    """Validate export request based on role and context sensitivity"""
    export_permissions = {
        ContextSensitivity.PUBLIC: {
            Role.VIEWER: ["json", "csv", "pdf"],
            Role.MEMBER: ["json", "csv", "pdf", "xml"]
        },
        ContextSensitivity.INTERNAL: {
            Role.MEMBER: ["json", "csv"],
            Role.MAINTAINER: ["json", "csv", "pdf", "encrypted_json"]
        },
        ContextSensitivity.CONFIDENTIAL: {
            Role.MAINTAINER: ["encrypted_json"],
            Role.ADMIN: ["encrypted_json", "encrypted_pdf"]
        },
        ContextSensitivity.RESTRICTED: {
            Role.ADMIN: ["encrypted_archive"],
            Role.OWNER: ["encrypted_archive", "secure_transfer"]
        }
    }

    allowed_formats = export_permissions.get(context_sensitivity, {}).get(user_role, [])
    return export_format in allowed_formats
```

## Unit Tests for Retention/Export

### Test Cases
1. **Retention Policy Enforcement**
   - Test automatic archival based on sensitivity tier
   - Test deletion policy compliance
   - Test backup frequency adherence

2. **Export Permission Validation**
   - Test role-based export restrictions
   - Test format limitations by sensitivity
   - Test audit trail generation

3. **Context Sensitivity Classification**
   - Test automatic classification algorithms
   - Test manual override capabilities
   - Test sensitivity escalation workflows

4. **Cross-Tier Operations**
   - Test data movement between sensitivity tiers
   - Test permission inheritance
   - Test audit requirements

### Performance Considerations
- **Caching**: Cache permission checks for frequently accessed contexts
- **Indexing**: Create database indexes on sensitivity and role columns
- **Batch Operations**: Optimize bulk export/retention operations
- **Monitoring**: Track performance metrics for permission checks

## Compliance Integration

### Regulatory Frameworks
- **GDPR**: Right to erasure, data portability
- **HIPAA**: Healthcare data protection
- **SOX**: Financial data retention
- **PCI DSS**: Payment card data security

### Audit Requirements
- Log all access attempts with context sensitivity
- Track data lineage across sensitivity tiers
- Generate compliance reports by tier
- Maintain immutable audit trails

## Migration Strategy

### Phase 1: Classification
- Implement context sensitivity classification
- Migrate existing contexts to appropriate tiers
- Update permission checking logic

### Phase 2: Retention Policies
- Implement tier-based retention policies
- Create automated archival processes
- Set up compliance monitoring

### Phase 3: Export Controls
- Implement export restrictions by tier
- Add encryption for sensitive exports
- Create audit trails for all exports

### Phase 4: Testing & Validation
- Run comprehensive unit tests
- Perform security penetration testing
- Validate compliance requirements

## Monitoring and Alerting

### Key Metrics
- Permission denial rates by tier
- Export request patterns
- Retention policy compliance
- Performance impact of sensitivity checks

### Alerts
- Unauthorized access attempts to high-sensitivity contexts
- Retention policy violations
- Unusual export patterns
- Performance degradation in permission checks

This expanded RBAC matrix provides fine-grained control over data access, retention, and export based on context sensitivity while maintaining performance and compliance requirements.
