# Spec 011: Data Lifecycle Management

## Overview
Implement comprehensive data lifecycle management with tier-based retention policies, automated archival, encrypted exports, and compliance reporting to ensure regulatory compliance while optimizing storage costs.

## Objectives
- Define and enforce tier-based retention policies with 1-year default
- Implement automated data archival and purging workflows
- Create encrypted export system for compliance requirements
- Build GDPR/HIPAA compliance reporting tools
- Establish data classification and lifecycle automation
- Provide audit trails for all data lifecycle events

## Architecture

### Data Lifecycle Components
```
server/data_lifecycle/
├── __init__.py
├── retention/
│   ├── __init__.py
│   ├── policies.py          # Retention policy definitions
│   ├── enforcement.py       # Policy enforcement engine
│   └── scheduler.py         # Automated retention tasks
├── archival/
│   ├── __init__.py
│   ├── archiver.py          # Data archival system
│   ├── storage_backends.py  # S3, Azure, GCS backends
│   └── compression.py       # Data compression utilities
├── export/
│   ├── __init__.py
│   ├── exporters.py         # Data export systems
│   ├── encryption.py        # Export encryption
│   └── formats.py           # Export format handlers
├── compliance/
│   ├── __init__.py
│   ├── gdpr.py             # GDPR compliance tools
│   ├── hipaa.py            # HIPAA compliance tools
│   └── reporting.py        # Compliance reporting
└── audit/
    ├── __init__.py
    ├── lifecycle_audit.py   # Lifecycle event auditing
    └── retention_reports.py # Retention compliance reports
```

## Technical Specifications

### 1. Retention Policy Framework

#### Tier-Based Retention Policies
```python
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Optional

class RetentionTier(Enum):
    """Data retention tiers based on sensitivity and business value"""
    PERMANENT = "permanent"      # Never delete (legal holds, compliance)
    LONG_TERM = "long_term"     # 7 years (financial, audit records)
    STANDARD = "standard"       # 1 year default (business data)
    SHORT_TERM = "short_term"   # 90 days (logs, temporary data)
    EPHEMERAL = "ephemeral"     # 30 days (session data, caches)

@dataclass
class RetentionPolicy:
    """Retention policy configuration"""
    tier: RetentionTier
    retention_days: int
    archive_after_days: Optional[int] = None
    encryption_required: bool = True
    compliance_tags: List[str] = None
    auto_purge: bool = True
    legal_hold_exempt: bool = False

class RetentionPolicyManager:
    """Manage retention policies by sensitivity tier"""
    
    DEFAULT_POLICIES = {
        ContextSensitivity.PUBLIC: RetentionPolicy(
            tier=RetentionTier.STANDARD,
            retention_days=365,  # 1 year default
            archive_after_days=90,
            encryption_required=False,
            compliance_tags=['public_data'],
            auto_purge=True
        ),
        ContextSensitivity.INTERNAL: RetentionPolicy(
            tier=RetentionTier.STANDARD,
            retention_days=365,
            archive_after_days=180,
            encryption_required=True,
            compliance_tags=['internal_data'],
            auto_purge=True
        ),
        ContextSensitivity.CONFIDENTIAL: RetentionPolicy(
            tier=RetentionTier.LONG_TERM,
            retention_days=2555,  # 7 years
            archive_after_days=365,
            encryption_required=True,
            compliance_tags=['confidential_data', 'gdpr'],
            auto_purge=False  # Manual review required
        ),
        ContextSensitivity.RESTRICTED: RetentionPolicy(
            tier=RetentionTier.LONG_TERM,
            retention_days=2555,
            archive_after_days=90,
            encryption_required=True,
            compliance_tags=['restricted_data', 'hipaa', 'gdpr'],
            auto_purge=False,
            legal_hold_exempt=True
        ),
        ContextSensitivity.SECRETS: RetentionPolicy(
            tier=RetentionTier.EPHEMERAL,
            retention_days=1,  # Secrets should be ephemeral
            archive_after_days=None,
            encryption_required=True,
            compliance_tags=['secrets', 'pii'],
            auto_purge=True
        )
    }
    
    def get_retention_policy(self, sensitivity: ContextSensitivity, 
                           custom_policy: Optional[RetentionPolicy] = None) -> RetentionPolicy:
        """Get retention policy for sensitivity tier"""
        if custom_policy:
            return custom_policy
        return self.DEFAULT_POLICIES.get(sensitivity, self.DEFAULT_POLICIES[ContextSensitivity.INTERNAL])
    
    def calculate_expiry_date(self, created_at: datetime, 
                            sensitivity: ContextSensitivity) -> datetime:
        """Calculate data expiry date based on retention policy"""
        policy = self.get_retention_policy(sensitivity)
        return created_at + timedelta(days=policy.retention_days)
    
    def should_archive(self, created_at: datetime, 
                      sensitivity: ContextSensitivity) -> bool:
        """Check if data should be archived"""
        policy = self.get_retention_policy(sensitivity)
        if not policy.archive_after_days:
            return False
        
        archive_date = created_at + timedelta(days=policy.archive_after_days)
        return datetime.utcnow() >= archive_date
```

### 2. Automated Archival System

#### Data Archival Engine
```python
class DataArchiver:
    """Automated data archival system with multiple storage backends"""
    
    def __init__(self):
        self.storage_backends = {
            'aws_s3': S3StorageBackend(),
            'azure_blob': AzureBlobBackend(),
            'gcs': GoogleCloudStorageBackend(),
            'local': LocalStorageBackend()
        }
        
        self.compression_engine = CompressionEngine()
        self.encryption_engine = EncryptionEngine()
    
    async def archive_expired_data(self):
        """Archive data that has reached archival threshold"""
        archival_candidates = await self._find_archival_candidates()
        
        for candidate in archival_candidates:
            try:
                await self._archive_data_item(candidate)
                await self._update_archival_status(candidate)
                
                # Log archival event
                await self._log_archival_event(
                    data_id=candidate.id,
                    data_type=candidate.__class__.__name__,
                    sensitivity=candidate.sensitivity_tier,
                    archive_location=candidate.archive_location
                )
                
            except Exception as e:
                logger.error(f"Failed to archive {candidate.id}: {e}")
                await self._log_archival_failure(candidate, str(e))
    
    async def _archive_data_item(self, data_item):
        """Archive individual data item"""
        # Serialize data
        serialized_data = await self._serialize_data(data_item)
        
        # Compress data
        compressed_data = await self.compression_engine.compress(
            serialized_data,
            algorithm='gzip'  # or 'lz4' for speed, 'brotli' for size
        )
        
        # Encrypt if required
        policy = retention_policy_manager.get_retention_policy(data_item.sensitivity_tier)
        if policy.encryption_required:
            encrypted_data = await self.encryption_engine.encrypt(
                compressed_data,
                key_id=f"retention_{data_item.sensitivity_tier.value}"
            )
        else:
            encrypted_data = compressed_data
        
        # Store in archive
        archive_key = self._generate_archive_key(data_item)
        storage_backend = self._select_storage_backend(data_item.sensitivity_tier)
        
        await storage_backend.store(
            key=archive_key,
            data=encrypted_data,
            metadata={
                'original_id': data_item.id,
                'sensitivity_tier': data_item.sensitivity_tier.value,
                'archived_at': datetime.utcnow().isoformat(),
                'retention_policy': policy.tier.value,
                'compliance_tags': policy.compliance_tags
            }
        )
        
        # Update database with archive location
        data_item.archived = True
        data_item.archive_location = f"{storage_backend.name}://{archive_key}"
        data_item.archived_at = datetime.utcnow()

class CompressionEngine:
    """Data compression utilities"""
    
    async def compress(self, data: bytes, algorithm: str = 'gzip') -> bytes:
        """Compress data using specified algorithm"""
        if algorithm == 'gzip':
            return gzip.compress(data)
        elif algorithm == 'lz4':
            return lz4.frame.compress(data)
        elif algorithm == 'brotli':
            return brotli.compress(data)
        else:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")
    
    async def decompress(self, data: bytes, algorithm: str = 'gzip') -> bytes:
        """Decompress data"""
        if algorithm == 'gzip':
            return gzip.decompress(data)
        elif algorithm == 'lz4':
            return lz4.frame.decompress(data)
        elif algorithm == 'brotli':
            return brotli.decompress(data)
        else:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")
```

### 3. Encrypted Export System

#### Data Export Engine
```python
class DataExportEngine:
    """Secure data export system for compliance requirements"""
    
    def __init__(self):
        self.export_formats = {
            'json': JSONExporter(),
            'csv': CSVExporter(),
            'xml': XMLExporter(),
            'parquet': ParquetExporter()
        }
        
        self.encryption_engine = EncryptionEngine()
    
    async def export_user_data(self, user_id: int, export_request: DataExportRequest) -> DataExportResult:
        """Export all user data for GDPR compliance"""
        
        # Validate export request
        await self._validate_export_request(export_request)
        
        # Collect user data across all tables
        user_data = await self._collect_user_data(user_id, export_request.data_types)
        
        # Apply data minimization if requested
        if export_request.minimize_data:
            user_data = await self._apply_data_minimization(user_data, export_request.fields)
        
        # Export to requested format
        exporter = self.export_formats[export_request.format]
        exported_data = await exporter.export(user_data)
        
        # Encrypt export
        encrypted_export = await self.encryption_engine.encrypt_export(
            exported_data,
            export_request.encryption_key or self._generate_export_key()
        )
        
        # Store export securely
        export_location = await self._store_export(encrypted_export, export_request)
        
        # Log export event
        await self._log_export_event(
            user_id=user_id,
            export_request=export_request,
            export_location=export_location
        )
        
        return DataExportResult(
            export_id=export_request.id,
            user_id=user_id,
            export_location=export_location,
            encryption_key=export_request.encryption_key,
            expires_at=datetime.utcnow() + timedelta(days=30)  # Export link expires
        )
    
    async def _collect_user_data(self, user_id: int, data_types: List[str]) -> Dict[str, Any]:
        """Collect user data from all relevant tables"""
        user_data = {}
        
        if 'profile' in data_types:
            user_data['profile'] = await self._get_user_profile(user_id)
        
        if 'memories' in data_types:
            user_data['memories'] = await self._get_user_memories(user_id)
        
        if 'contexts' in data_types:
            user_data['contexts'] = await self._get_user_contexts(user_id)
        
        if 'audit_logs' in data_types:
            user_data['audit_logs'] = await self._get_user_audit_logs(user_id)
        
        if 'rbac_assignments' in data_types:
            user_data['rbac_assignments'] = await self._get_user_rbac_assignments(user_id)
        
        return user_data

@dataclass
class DataExportRequest:
    """Data export request configuration"""
    id: str
    user_id: int
    data_types: List[str]  # ['profile', 'memories', 'contexts', 'audit_logs']
    format: str  # 'json', 'csv', 'xml', 'parquet'
    encryption_key: Optional[str] = None
    minimize_data: bool = False
    fields: Optional[List[str]] = None
    requested_by: int = None
    reason: str = "user_request"
    expires_after_days: int = 30
```

### 4. Compliance Reporting

#### GDPR Compliance Tools
```python
class GDPRComplianceManager:
    """GDPR compliance tools and reporting"""
    
    async def generate_data_processing_report(self, organization_id: int) -> GDPRReport:
        """Generate GDPR Article 30 data processing report"""
        
        # Collect data processing activities
        processing_activities = await self._collect_processing_activities(organization_id)
        
        # Analyze data flows
        data_flows = await self._analyze_data_flows(organization_id)
        
        # Check retention compliance
        retention_compliance = await self._check_retention_compliance(organization_id)
        
        # Generate report
        report = GDPRReport(
            organization_id=organization_id,
            processing_activities=processing_activities,
            data_flows=data_flows,
            retention_compliance=retention_compliance,
            legal_basis_analysis=await self._analyze_legal_basis(organization_id),
            data_subject_rights_log=await self._get_data_subject_rights_log(organization_id),
            generated_at=datetime.utcnow()
        )
        
        return report
    
    async def handle_data_subject_request(self, request: DataSubjectRequest) -> DataSubjectResponse:
        """Handle GDPR data subject requests"""
        
        if request.request_type == 'access':
            return await self._handle_access_request(request)
        elif request.request_type == 'rectification':
            return await self._handle_rectification_request(request)
        elif request.request_type == 'erasure':
            return await self._handle_erasure_request(request)
        elif request.request_type == 'portability':
            return await self._handle_portability_request(request)
        elif request.request_type == 'restriction':
            return await self._handle_restriction_request(request)
        else:
            raise ValueError(f"Unsupported request type: {request.request_type}")
    
    async def _handle_erasure_request(self, request: DataSubjectRequest) -> DataSubjectResponse:
        """Handle right to erasure (right to be forgotten)"""
        
        # Validate erasure request
        await self._validate_erasure_request(request)
        
        # Check for legal obligations to retain data
        retention_obligations = await self._check_retention_obligations(request.user_id)
        
        if retention_obligations:
            return DataSubjectResponse(
                request_id=request.id,
                status='partial_erasure',
                message='Some data retained due to legal obligations',
                retained_data_categories=retention_obligations,
                completed_at=datetime.utcnow()
            )
        
        # Perform erasure
        erasure_result = await self._perform_data_erasure(request.user_id)
        
        return DataSubjectResponse(
            request_id=request.id,
            status='completed',
            message='Data successfully erased',
            erasure_summary=erasure_result,
            completed_at=datetime.utcnow()
        )

class HIPAAComplianceManager:
    """HIPAA compliance tools for healthcare data"""
    
    async def generate_hipaa_audit_report(self, covered_entity_id: int) -> HIPAAReport:
        """Generate HIPAA compliance audit report"""
        
        # Check access controls
        access_controls = await self._audit_access_controls(covered_entity_id)
        
        # Audit PHI access logs
        phi_access_logs = await self._audit_phi_access(covered_entity_id)
        
        # Check encryption compliance
        encryption_compliance = await self._check_encryption_compliance(covered_entity_id)
        
        # Verify business associate agreements
        baa_compliance = await self._check_baa_compliance(covered_entity_id)
        
        return HIPAAReport(
            covered_entity_id=covered_entity_id,
            access_controls=access_controls,
            phi_access_audit=phi_access_logs,
            encryption_compliance=encryption_compliance,
            baa_compliance=baa_compliance,
            risk_assessment=await self._perform_risk_assessment(covered_entity_id),
            generated_at=datetime.utcnow()
        )
```

### 5. Automated Lifecycle Scheduler

#### Retention Scheduler
```python
class DataLifecycleScheduler:
    """Automated data lifecycle management scheduler"""
    
    def __init__(self):
        self.retention_policy_manager = RetentionPolicyManager()
        self.data_archiver = DataArchiver()
        self.purge_engine = DataPurgeEngine()
    
    async def run_daily_lifecycle_tasks(self):
        """Run daily data lifecycle management tasks"""
        
        # Archive eligible data
        await self._run_archival_tasks()
        
        # Purge expired data
        await self._run_purge_tasks()
        
        # Update retention metadata
        await self._update_retention_metadata()
        
        # Generate compliance reports
        await self._generate_daily_compliance_reports()
        
        # Clean up temporary exports
        await self._cleanup_expired_exports()
    
    async def _run_archival_tasks(self):
        """Run data archival tasks"""
        logger.info("Starting daily archival tasks")
        
        # Find data eligible for archival
        archival_candidates = await self._find_archival_candidates()
        
        for candidate in archival_candidates:
            try:
                await self.data_archiver.archive_data_item(candidate)
                logger.info(f"Archived {candidate.__class__.__name__} {candidate.id}")
            except Exception as e:
                logger.error(f"Failed to archive {candidate.id}: {e}")
    
    async def _run_purge_tasks(self):
        """Run data purge tasks"""
        logger.info("Starting daily purge tasks")
        
        # Find data eligible for purging
        purge_candidates = await self._find_purge_candidates()
        
        for candidate in purge_candidates:
            policy = self.retention_policy_manager.get_retention_policy(candidate.sensitivity_tier)
            
            if policy.auto_purge:
                try:
                    await self.purge_engine.purge_data_item(candidate)
                    logger.info(f"Purged {candidate.__class__.__name__} {candidate.id}")
                except Exception as e:
                    logger.error(f"Failed to purge {candidate.id}: {e}")
            else:
                # Queue for manual review
                await self._queue_for_manual_review(candidate)

class DataPurgeEngine:
    """Secure data purging system"""
    
    async def purge_data_item(self, data_item):
        """Securely purge data item"""
        
        # Create purge audit record before deletion
        purge_record = await self._create_purge_audit_record(data_item)
        
        # Remove from archive if archived
        if hasattr(data_item, 'archived') and data_item.archived:
            await self._purge_from_archive(data_item.archive_location)
        
        # Remove from database
        await self._purge_from_database(data_item)
        
        # Update purge audit record
        purge_record.purged_at = datetime.utcnow()
        purge_record.status = 'completed'
        
        logger.info(f"Successfully purged {data_item.__class__.__name__} {data_item.id}")
```

## Database Schema Changes

### Data Lifecycle Tables
```sql
-- Retention metadata
ALTER TABLE memories ADD COLUMN retention_tier VARCHAR(50) DEFAULT 'standard';
ALTER TABLE memories ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE memories ADD COLUMN archived BOOLEAN DEFAULT FALSE;
ALTER TABLE memories ADD COLUMN archive_location VARCHAR(500);
ALTER TABLE memories ADD COLUMN archived_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE contexts ADD COLUMN retention_tier VARCHAR(50) DEFAULT 'standard';
ALTER TABLE contexts ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE contexts ADD COLUMN archived BOOLEAN DEFAULT FALSE;
ALTER TABLE contexts ADD COLUMN archive_location VARCHAR(500);
ALTER TABLE contexts ADD COLUMN archived_at TIMESTAMP WITH TIME ZONE;

-- Data lifecycle audit table
CREATE TABLE data_lifecycle_audits (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_type VARCHAR(100) NOT NULL,
    data_id VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'archived', 'purged', 'exported'
    sensitivity_tier VARCHAR(50),
    retention_policy VARCHAR(100),
    user_id INTEGER REFERENCES users(id),
    reason VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data export requests
CREATE TABLE data_export_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    requested_by INTEGER REFERENCES users(id),
    data_types JSONB NOT NULL,
    format VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    export_location VARCHAR(500),
    encryption_key_hash VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- GDPR data subject requests
CREATE TABLE data_subject_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    request_type VARCHAR(50) NOT NULL, -- 'access', 'rectification', 'erasure', 'portability', 'restriction'
    status VARCHAR(50) DEFAULT 'pending',
    reason TEXT,
    response_data JSONB,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_data_lifecycle_audits_timestamp ON data_lifecycle_audits(timestamp);
CREATE INDEX idx_data_lifecycle_audits_data_type ON data_lifecycle_audits(data_type);
CREATE INDEX idx_data_export_requests_user_id ON data_export_requests(user_id);
CREATE INDEX idx_data_subject_requests_user_id ON data_subject_requests(user_id);
CREATE INDEX idx_memories_expires_at ON memories(expires_at);
CREATE INDEX idx_contexts_expires_at ON contexts(expires_at);
```

## Implementation Plan

### Phase 1: Retention Framework (Week 7)
1. Implement retention policy framework
2. Add retention metadata to existing tables
3. Create data lifecycle scheduler
4. Implement basic archival system
5. Add retention policy enforcement

### Phase 2: Export & Compliance (Week 8)
1. Build encrypted export system
2. Implement GDPR compliance tools
3. Add HIPAA compliance reporting
4. Create data subject request handling
5. Build compliance dashboards

## Configuration

### Environment Variables
```bash
# Data Lifecycle Configuration
DATA_LIFECYCLE_ENABLED=true
DEFAULT_RETENTION_DAYS=365
ARCHIVAL_STORAGE_BACKEND=aws_s3
ENCRYPTION_KEY_ID=retention_encryption_key

# Storage Backend Configuration
AWS_S3_BUCKET=ninaivalaigal-archives
AWS_S3_REGION=us-east-1
AZURE_STORAGE_ACCOUNT=ninaivalaigalarchives
GCS_BUCKET=ninaivalaigal-archives

# Compliance Configuration
GDPR_COMPLIANCE_ENABLED=true
HIPAA_COMPLIANCE_ENABLED=false
DATA_EXPORT_ENCRYPTION_REQUIRED=true
EXPORT_LINK_EXPIRY_DAYS=30

# Scheduler Configuration
LIFECYCLE_SCHEDULER_ENABLED=true
DAILY_ARCHIVAL_TIME=02:00
DAILY_PURGE_TIME=03:00
```

## Success Criteria

### Compliance Requirements
- [ ] 100% of data has defined retention policies with 1-year default
- [ ] Automated archival reduces active storage by 70% after 6 months
- [ ] GDPR data subject requests processed within 30 days
- [ ] All data exports encrypted and access-controlled
- [ ] Complete audit trail for all lifecycle events

### Operational Requirements
- [ ] Archival process completes within 4-hour maintenance window
- [ ] Export generation completes within 24 hours
- [ ] Storage costs reduced by 60% through archival
- [ ] Zero data loss during lifecycle transitions
- [ ] Compliance reports generated automatically

This data lifecycle management system ensures regulatory compliance while optimizing storage costs and providing comprehensive audit capabilities.
