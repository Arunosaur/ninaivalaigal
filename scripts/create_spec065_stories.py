#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""
Create Taiga user stories for SPEC-065: Advanced Security & Compliance.

Usage:
    python3 scripts/create_spec065_stories.py
"""

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

PROJECT_SLUG = "ninaivalaigal"
SPEC_NUMBER = "065"
SPEC_TITLE = "Advanced Security & Compliance"
DEVELOPER_C_USERNAME = "developer-c"


def authenticate():
    """Authenticate and get auth token."""
    print("\n1️⃣  Authenticating...")
    response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if response.status_code == 200:
        auth_token = response.json()["auth_token"]
        print("✅ Authenticated")
        return {"Authorization": f"Bearer {auth_token}"}
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        sys.exit(1)


def get_project_id(headers, project_slug):
    """Get project ID by slug."""
    response = requests.get(
        f"{API_ENDPOINT}/projects/by_slug",
        headers=headers,
        params={"slug": project_slug},
    )
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"❌ Failed to get project {project_slug}: {response.status_code}")
        sys.exit(1)


def get_user_id(headers, username):
    """Get user ID by username."""
    response = requests.get(f"{API_ENDPOINT}/users/me", headers=headers)
    if response.status_code == 200:
        me = response.json()
        if me.get("username") == username:
            return me.get("id")

    # Try to get all users
    project_id = get_project_id(headers, PROJECT_SLUG)
    response = requests.get(f"{API_ENDPOINT}/users", headers=headers, params={"project": project_id})
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("username") == username:
                return user.get("id")

    return None


def get_status_id(headers, project_id, status_name):
    """Get status ID by name."""
    response = requests.get(
        f"{API_ENDPOINT}/userstory-statuses",
        headers=headers,
        params={"project": project_id},
    )
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name") == status_name:
                return status.get("id")
    return None


def create_story(headers, project_id, subject, description, assignee_id, status_id=None):
    """Create a user story."""
    payload = {
        "project": project_id,
        "subject": subject,
        "description": description,
        "tags": [f"SPEC-{SPEC_NUMBER}"],
    }

    if assignee_id:
        payload["assigned_to"] = assignee_id

    if status_id:
        payload["status"] = status_id

    response = requests.post(
        f"{API_ENDPOINT}/userstories",
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
    )

    if response.status_code == 201:
        return response.json()
    else:
        print(f"❌ Failed to create story: {response.status_code} - {response.text[:200]}")
        return None


def main():
    """Main function."""
    print("=" * 80)
    print(f"📋 Creating Taiga Stories for SPEC-{SPEC_NUMBER}")
    print(f"   Project: {PROJECT_SLUG}")
    print(f"   SPEC: {SPEC_TITLE}")
    print("=" * 80)

    # Authenticate
    headers = authenticate()

    # Get project ID
    print("\n2️⃣  Getting project...")
    project_id = get_project_id(headers, PROJECT_SLUG)
    print(f"✅ Project ID: {project_id}")

    # Get user ID for Developer C
    print(f"\n3️⃣  Getting user ID for {DEVELOPER_C_USERNAME}...")
    assignee_id = get_user_id(headers, DEVELOPER_C_USERNAME)
    if assignee_id:
        print(f"✅ Developer C ID: {assignee_id}")
    else:
        print("⚠️  Developer C not found, stories will be unassigned")
        assignee_id = None

    # Get status IDs
    print("\n4️⃣  Getting status IDs...")
    new_status_id = get_status_id(headers, project_id, "New")
    print(f"✅ New status ID: {new_status_id}")

    # Define stories based on SPEC-065 remaining deliverables
    stories = [
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Current Security Foundation - Complete",
            "description": """**Objective**: Document completion of basic security foundation.

**Status**: ✅ **COMPLETE**

**Completed Work**:
- ✅ JWT Authentication: Secure token-based authentication (`server/enhanced_auth_middleware.py`)
- ✅ UUID Schema: Non-sequential, secure identifiers throughout database
- ✅ Secret Scanning: Automated secret detection in codebase (bandit, npm audit in CI/CD)
- ✅ Environment Hygiene: Secure configuration management
- ✅ Security Middleware: Headers, rate limiting, input/output sanitization (SPEC-008, SPEC-009)
- ✅ TLS 1.3: Encryption in transit for all communications
- ✅ Security Redaction: Pre-persistence and pre-logging redaction (SPEC-008)
- ✅ Vulnerability Scanning: CI/CD integration (bandit, npm audit)

**Key Features**:
- Secure authentication and authorization
- Security middleware stack
- Data protection in transit
- Automated security scanning

**Deliverables**:
- ✅ JWT authentication system
- ✅ Security middleware
- ✅ TLS 1.3 encryption
- ✅ Secret scanning
- ✅ Security redaction""",
            "status": "Done",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Multi-Factor Authentication (MFA) Implementation",
            "description": """**Objective**: Implement multi-factor authentication to enhance account security.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Implement TOTP-based 2FA:
  - TOTP setup and verification endpoints
  - QR code generation for authenticator apps
  - Backup codes for account recovery
- [ ] SMS-based 2FA (optional):
  - SMS verification code delivery
  - Rate limiting for SMS requests
  - Cost management
- [ ] Hardware key support (WebAuthn/FIDO2):
  - WebAuthn API integration
  - Hardware key registration
  - Authentication with hardware keys
- [ ] MFA enforcement:
  - Require MFA for administrative actions
  - Optional MFA for regular users
  - MFA bypass for trusted devices

**Acceptance Criteria**:
- [ ] TOTP 2FA functional
- [ ] QR codes generate correctly
- [ ] Backup codes work for recovery
- [ ] Hardware keys supported (optional)
- [ ] MFA enforcement configurable

**Deliverables**:
- MFA setup API endpoints
- TOTP implementation
- Backup code system
- WebAuthn integration (optional)
- MFA enforcement middleware

**Priority**: High - Enterprise security requirement""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Single Sign-On (SSO) Integration",
            "description": """**Objective**: Implement SSO support for enterprise authentication.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] SAML 2.0 integration:
  - SAML authentication flow
  - Identity provider (IdP) configuration
  - SAML assertion validation
- [ ] OAuth2/OpenID Connect integration:
  - OAuth2 authorization flow
  - OpenID Connect user info
  - Multiple provider support (Google, Microsoft, Okta, etc.)
- [ ] SSO configuration management:
  - IdP metadata import
  - Certificate management
  - Attribute mapping
- [ ] Session management:
  - SSO session handling
  - Token refresh and renewal
  - Logout from all services

**Acceptance Criteria**:
- [ ] SAML authentication works
- [ ] OAuth2/OpenID Connect works
- [ ] Multiple providers supported
- [ ] Session management functional
- [ ] Proper logout handling

**Deliverables**:
- SAML 2.0 implementation
- OAuth2/OpenID Connect integration
- SSO configuration UI/API
- Session management

**Priority**: High - Enterprise requirement""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Biometric Authentication Support",
            "description": """**Objective**: Add biometric authentication for enhanced user experience.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Fingerprint recognition:
  - Browser WebAuthn API for fingerprint
  - Mobile device fingerprint support
  - Secure biometric storage
- [ ] Face recognition:
  - Face ID / Touch ID integration
  - Secure biometric authentication flow
- [ ] Biometric fallback:
  - Password/MFA fallback when biometric unavailable
  - Device capability detection
- [ ] Security considerations:
  - Biometric data never stored on server
  - Local device authentication only
  - Encrypted biometric templates

**Acceptance Criteria**:
- [ ] Fingerprint authentication works
- [ ] Face recognition works (where supported)
- [ ] Fallback mechanisms functional
- [ ] Biometric data secure

**Deliverables**:
- WebAuthn biometric integration
- Mobile biometric support
- Fallback mechanisms
- Security documentation

**Priority**: Medium - Enhanced UX feature""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Risk-Based Authentication",
            "description": """**Objective**: Implement adaptive authentication based on user behavior and risk factors.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Risk scoring engine:
  - Device fingerprinting
  - Location-based risk analysis
  - Behavior pattern analysis
  - Time-based risk factors
- [ ] Adaptive authentication:
  - Adjust authentication requirements based on risk
  - Challenge additional factors for high-risk attempts
  - Streamline low-risk authentication
- [ ] Risk factors:
  - New device detection
  - Unusual location
  - Unusual time patterns
  - Suspicious activity patterns
- [ ] Configuration and tuning:
  - Risk threshold configuration
  - Risk factor weighting
  - Learning from false positives/negatives

**Acceptance Criteria**:
- [ ] Risk scoring functional
- [ ] Adaptive challenges work
- [ ] Risk factors detected
- [ ] Configuration manageable

**Deliverables**:
- Risk scoring engine
- Adaptive authentication flow
- Risk factor detection
- Configuration system

**Priority**: Medium - Advanced security feature""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Anomaly Detection System",
            "description": """**Objective**: Implement ML-based anomaly detection for unusual activity identification.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Anomaly detection models:
  - ML model training on user behavior
  - Pattern recognition for unusual activities
  - Real-time anomaly scoring
- [ ] Activity monitoring:
  - User login patterns
  - API usage patterns
  - Data access patterns
  - Resource consumption patterns
- [ ] Alert generation:
  - Threshold-based alerts
  - Severity classification
  - Alert notification system
- [ ] Model training and updates:
  - Continuous learning from new data
  - Model retraining pipeline
  - False positive reduction

**Acceptance Criteria**:
- [ ] Anomaly detection models functional
- [ ] Real-time monitoring works
- [ ] Alerts generated appropriately
- [ ] Model training automated

**Deliverables**:
- ML-based anomaly detection
- Activity monitoring system
- Alert generation
- Model training pipeline

**Priority**: High - Security threat detection""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Intrusion Detection System (IDS)",
            "description": """**Objective**: Implement real-time intrusion detection and security event monitoring.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Intrusion detection engine:
  - Network traffic analysis
  - API request pattern analysis
  - Attack signature detection
  - Behavioral baseline establishment
- [ ] Security event monitoring:
  - Real-time event collection
  - Event correlation
  - Attack pattern recognition
- [ ] Response automation:
  - Automatic threat blocking
  - Rate limiting on suspicious activity
  - Account lockout on intrusion attempts
- [ ] Integration with SIEM:
  - Event export to SIEM systems
  - Standard log formats (Syslog, JSON)
  - Real-time streaming

**Acceptance Criteria**:
- [ ] Intrusion detection functional
- [ ] Real-time monitoring works
- [ ] Automatic responses triggered
- [ ] SIEM integration works

**Deliverables**:
- Intrusion detection engine
- Security event monitoring
- Response automation
- SIEM integration

**Priority**: High - Security threat detection""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Behavioral Analysis System",
            "description": """**Objective**: Implement user behavior pattern analysis for security and fraud detection.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Behavior profiling:
  - User activity profiling
  - Normal behavior baseline establishment
  - Pattern recognition and learning
- [ ] Behavioral anomaly detection:
  - Deviation from normal patterns
  - Suspicious behavior identification
  - Fraud detection algorithms
- [ ] Data collection:
  - Activity logging
  - Behavioral metrics collection
  - Privacy-compliant data handling
- [ ] Analytics and insights:
  - Behavioral analytics dashboard
  - Pattern visualization
  - Risk assessment reports

**Acceptance Criteria**:
- [ ] Behavior profiling functional
- [ ] Anomaly detection works
- [ ] Data collection privacy-compliant
- [ ] Analytics dashboard available

**Deliverables**:
- Behavior profiling system
- Anomaly detection algorithms
- Data collection system
- Analytics dashboard

**Priority**: Medium - Advanced security feature""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Threat Intelligence Integration",
            "description": """**Objective**: Integrate with security feeds and threat intelligence databases.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Threat feed integration:
  - Integration with threat intelligence feeds
  - Known attack pattern databases
  - IP reputation services
  - Malware signature databases
- [ ] Real-time threat checking:
  - IP address reputation checking
  - Domain reputation checking
  - Known attack pattern matching
  - Malware detection
- [ ] Threat intelligence updates:
  - Automatic feed updates
  - Threat signature updates
  - Database synchronization
- [ ] Response integration:
  - Automatic blocking of known threats
  - Alert generation on threat matches
  - Integration with IDS

**Acceptance Criteria**:
- [ ] Threat feeds integrated
- [ ] Real-time checking works
- [ ] Automatic updates functional
- [ ] Response integration works

**Deliverables**:
- Threat feed integrations
- Real-time threat checking
- Update mechanisms
- Response integration

**Priority**: Medium - Enhanced threat detection""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: GDPR Compliance Framework",
            "description": """**Objective**: Complete GDPR compliance implementation for EU data protection.

**Status**: 🟡 **PARTIAL** (Documentation exists, full implementation pending)

**Tasks**:
- [ ] Data privacy features:
  - Right to access: User data export functionality ✅ (partially exists)
  - Right to deletion: Complete user data removal ✅ (partially exists)
  - Right to rectification: Data correction mechanisms
  - Right to portability: Data export in standard formats
- [ ] Consent management:
  - Consent tracking and storage
  - Consent withdrawal mechanisms
  - Consent audit trail
- [ ] Data processing transparency:
  - Clear data usage policies
  - Data processing logs
  - User notification system
- [ ] Privacy by design:
  - Data minimization
  - Purpose limitation
  - Storage limitation

**Acceptance Criteria**:
- [ ] All GDPR rights implemented
- [ ] Consent management functional
- [ ] Transparency mechanisms in place
- [ ] Privacy by design principles followed

**Deliverables**:
- GDPR rights implementation
- Consent management system
- Transparency features
- Privacy documentation

**Priority**: High - Legal compliance requirement""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: SOC 2 Type II Compliance Framework",
            "description": """**Objective**: Complete SOC 2 Type II compliance with security \
controls and audit readiness.

**Status**: 🟡 **PARTIAL** (Audit logging exists, full compliance pending)

**Tasks**:
- [ ] Security controls:
  - Access controls and monitoring ✅ (partially exists)
  - Encryption controls ✅ (TLS 1.3 exists)
  - Network security controls
  - System operations controls
- [ ] Audit readiness:
  - Comprehensive audit logging ✅ (partially exists)
  - Audit trail completeness
  - Log retention policies
  - Audit log access controls
- [ ] Control testing:
  - Automated control testing
  - Control effectiveness monitoring
  - Remediation workflows
- [ ] Compliance documentation:
  - Control documentation
  - Evidence collection
  - Compliance reporting

**Acceptance Criteria**:
- [ ] All SOC 2 controls implemented
- [ ] Audit logging comprehensive
- [ ] Control testing automated
- [ ] Documentation complete

**Deliverables**:
- SOC 2 control implementation
- Audit logging enhancement
- Control testing framework
- Compliance documentation

**Priority**: High - Enterprise compliance requirement""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: HIPAA Compliance (If Applicable)",
            "description": """**Objective**: Implement HIPAA compliance for healthcare data protection (if applicable).

**Status**: ❌ **NOT IMPLEMENTED** (Optional - if healthcare data is handled)

**Tasks**:
- [ ] HIPAA security controls:
  - Administrative safeguards
  - Physical safeguards
  - Technical safeguards
- [ ] Protected Health Information (PHI) handling:
  - PHI identification and classification
  - PHI encryption requirements
  - PHI access controls
  - PHI audit logging
- [ ] Business Associate Agreements (BAA):
  - BAA template and management
  - Third-party compliance verification
- [ ] Breach notification:
  - Breach detection mechanisms
  - Notification procedures
  - Documentation requirements

**Acceptance Criteria**:
- [ ] HIPAA controls implemented (if applicable)
- [ ] PHI handling compliant
- [ ] BAA management functional
- [ ] Breach notification ready

**Deliverables**:
- HIPAA control implementation
- PHI handling system
- BAA management
- Breach notification system

**Priority**: Low - Only if healthcare data is handled""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: ISO 27001 Compliance Framework",
            "description": """**Objective**: Implement ISO 27001 Information Security Management System (ISMS).

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] ISMS framework:
  - Information security policy
  - Risk assessment and treatment
  - Security objectives and planning
- [ ] ISO 27001 controls:
  - A.9 Access Control
  - A.10 Cryptography
  - A.12 Operations Security
  - A.14 System Acquisition, Development, and Maintenance
  - A.17 Information Security Aspects of Business Continuity
  - A.18 Compliance
- [ ] Documentation and records:
  - ISMS documentation
  - Control implementation evidence
  - Management review records
- [ ] Continuous improvement:
  - Regular security assessments
  - Control effectiveness reviews
  - Corrective action management

**Acceptance Criteria**:
- [ ] ISMS framework established
- [ ] ISO 27001 controls implemented
- [ ] Documentation complete
- [ ] Continuous improvement process active

**Deliverables**:
- ISMS framework
- ISO 27001 control implementation
- Documentation system
- Continuous improvement process

**Priority**: Medium - International standard compliance""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Security Information and Event Management (SIEM) Enhancement",
            "description": """**Objective**: Enhance SIEM capabilities with centralized logging and advanced analytics.

**Status**: 🟡 **PARTIAL** (Structured logging exists, full SIEM pending)

**Tasks**:
- [ ] Centralized logging:
  - Enhanced structured logging ✅ (exists but needs enhancement)
  - Log aggregation and collection
  - Log storage and retention
  - Log search and analysis
- [ ] Security event correlation:
  - Event correlation engine
  - Pattern recognition
  - Incident detection
- [ ] Real-time monitoring:
  - Real-time event streaming
  - Dashboards and visualization
  - Alerting and notification
- [ ] Integration capabilities:
  - Integration with external SIEM systems
  - Standard log formats (Syslog, CEF, JSON)
  - API for log export

**Acceptance Criteria**:
- [ ] Centralized logging operational
- [ ] Event correlation functional
- [ ] Real-time monitoring works
- [ ] External integrations functional

**Deliverables**:
- Enhanced logging system
- Event correlation engine
- Monitoring dashboards
- Integration capabilities

**Priority**: High - Security operations requirement""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Penetration Testing Framework",
            "description": """**Objective**: Establish regular penetration testing framework \
and automated security assessment.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Automated penetration testing:
  - Integration with OWASP ZAP or similar tools
  - Automated vulnerability scanning
  - Security test automation
- [ ] Testing schedule:
  - Regular automated testing
  - Manual penetration testing schedule
  - Post-deployment testing
- [ ] Test coverage:
  - Authentication and authorization testing
  - API security testing
  - Infrastructure security testing
  - Application security testing
- [ ] Remediation workflow:
  - Vulnerability reporting
  - Remediation tracking
  - Retesting after fixes

**Acceptance Criteria**:
- [ ] Automated testing functional
- [ ] Testing schedule established
- [ ] Comprehensive test coverage
- [ ] Remediation workflow operational

**Deliverables**:
- Penetration testing framework
- Automated testing integration
- Testing schedules and procedures
- Remediation workflow

**Priority**: High - Security validation requirement""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Incident Response Automation",
            "description": """**Objective**: Implement automated incident detection and response capabilities.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Incident detection:
  - Automated threat detection
  - Incident classification
  - Severity assessment
- [ ] Response automation:
  - Automatic threat containment
  - Account lockout on attacks
  - IP blocking mechanisms
  - Rate limiting on suspicious activity
- [ ] Incident workflow:
  - Incident creation and tracking
  - Escalation procedures
  - Response playbooks
  - Post-incident review
- [ ] Notification and alerting:
  - Security team notifications
  - User notifications (if required)
  - Management reporting

**Acceptance Criteria**:
- [ ] Incident detection automated
- [ ] Response automation functional
- [ ] Workflow operational
- [ ] Notifications working

**Deliverables**:
- Incident detection system
- Response automation
- Incident workflow
- Notification system

**Priority**: High - Security operations requirement""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Encryption at Rest Implementation",
            "description": """**Objective**: Implement database and file system encryption at rest for sensitive data.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Database encryption:
  - PostgreSQL transparent data encryption (TDE)
  - Field-level encryption for sensitive data
  - Encryption key management
- [ ] File system encryption:
  - Volume encryption
  - Backup encryption
  - Storage encryption
- [ ] Key management:
  - Encryption key rotation
  - Key storage and access
  - Key backup and recovery
- [ ] Performance optimization:
  - Encryption overhead minimization
  - Caching strategies
  - Query optimization with encryption

**Acceptance Criteria**:
- [ ] Database encryption functional
- [ ] File system encryption operational
- [ ] Key management secure
- [ ] Performance acceptable

**Deliverables**:
- Database encryption
- File system encryption
- Key management system
- Performance optimization

**Priority**: High - Data protection requirement""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Hardware Security Module (HSM) Integration",
            "description": """**Objective**: Integrate Hardware Security Module for enhanced \
key management and cryptographic operations.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] HSM integration:
  - HSM provider integration (AWS CloudHSM, Azure Key Vault, etc.)
  - Cryptographic operation offloading
  - Key generation and storage in HSM
- [ ] Key management:
  - Master key management
  - Key rotation using HSM
  - Key backup and recovery
- [ ] Cryptographic operations:
  - Signing operations in HSM
  - Encryption key operations
  - Token signing with HSM
- [ ] High availability:
  - HSM redundancy
  - Failover mechanisms
  - Performance optimization

**Acceptance Criteria**:
- [ ] HSM integration functional
- [ ] Key management uses HSM
- [ ] Cryptographic operations secure
- [ ] High availability ensured

**Deliverables**:
- HSM integration
- Key management with HSM
- Cryptographic operation support
- High availability setup

**Priority**: Medium - Enhanced key security (optional for most deployments)""",
            "status": "New",
        },
        {
            "subject": f"SPEC-{SPEC_NUMBER}: Data Loss Prevention (DLP) System",
            "description": """**Objective**: Implement sensitive data identification and protection mechanisms.

**Status**: ❌ **NOT IMPLEMENTED**

**Tasks**:
- [ ] Sensitive data detection:
  - PII detection and classification
  - Credit card number detection
  - API key detection ✅ (exists in redaction)
  - Custom pattern detection
- [ ] Data protection policies:
  - Policy definition and management
  - Policy enforcement rules
  - Policy violation handling
- [ ] Data protection mechanisms:
  - Automatic data redaction ✅ (exists in SPEC-008)
  - Data masking
  - Access restrictions
  - Data encryption for sensitive fields
- [ ] Monitoring and alerting:
  - Policy violation alerts
  - Data access monitoring
  - Compliance reporting

**Acceptance Criteria**:
- [ ] Sensitive data detected
- [ ] Policies enforced
- [ ] Protection mechanisms functional
- [ ] Monitoring and alerting operational

**Deliverables**:
- Sensitive data detection
- Policy management system
- Data protection mechanisms
- Monitoring and alerting

**Priority**: High - Data protection requirement""",
            "status": "New",
        },
    ]

    # Create stories
    print("\n5️⃣  Creating stories...")
    created_stories = []
    failed_stories = []

    for idx, story_data in enumerate(stories, 1):
        print(f"\n   Creating story {idx}/{len(stories)}: {story_data['subject'][:60]}...")

        status_id = None
        if story_data["status"] == "Done":
            done_status_id = get_status_id(headers, project_id, "Done")
            status_id = done_status_id
        else:
            status_id = new_status_id

        created = create_story(
            headers,
            project_id,
            story_data["subject"],
            story_data["description"],
            assignee_id,
            status_id,
        )

        if created:
            ref = created.get("ref")
            created_stories.append((ref, story_data["subject"]))
            print(f"   ✅ Created US#{ref}")
        else:
            failed_stories.append(story_data["subject"])
            print("   ❌ Failed to create story")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"✅ Successfully created: {len(created_stories)}")
    if failed_stories:
        print(f"❌ Failed to create: {len(failed_stories)}")

    if created_stories:
        print("\nCreated stories:")
        for ref, subject in created_stories:
            print(f"  US#{ref}: {subject[:65]}")

    print("=" * 80)


if __name__ == "__main__":
    main()
