"""
SPEC-049: Memory Sharing Audit Logger
Comprehensive audit trails and transfer logs for memory sharing operations
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from .sharing_contracts import MemoryLinkContract, ScopeIdentifier

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""

    # Contract events
    CONTRACT_CREATED = "contract_created"
    CONTRACT_ACTIVATED = "contract_activated"
    CONTRACT_REVOKED = "contract_revoked"
    CONTRACT_EXPIRED = "contract_expired"
    CONTRACT_MODIFIED = "contract_modified"

    # Access events
    MEMORY_ACCESSED = "memory_accessed"
    MEMORY_DOWNLOADED = "memory_downloaded"
    MEMORY_SHARED = "memory_shared"
    MEMORY_RESHARED = "memory_reshared"

    # Consent events
    CONSENT_REQUESTED = "consent_requested"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_DENIED = "consent_denied"
    CONSENT_REVOKED = "consent_revoked"

    # Transfer events
    MEMORY_TRANSFERRED = "memory_transferred"
    OWNERSHIP_CHANGED = "ownership_changed"
    SCOPE_TRANSFERRED = "scope_transferred"

    # Security events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"

    # Administrative events
    ADMIN_OVERRIDE = "admin_override"
    POLICY_CHANGE = "policy_change"
    BULK_OPERATION = "bulk_operation"


class AuditSeverity(Enum):
    """Severity levels for audit events"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Individual audit event record"""

    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime

    # Core identifiers
    memory_id: Optional[str] = None
    contract_id: Optional[str] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None

    # Scope information
    source_scope: Optional[ScopeIdentifier] = None
    target_scope: Optional[ScopeIdentifier] = None

    # Event details
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    # Context information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None

    # Security context
    authentication_method: Optional[str] = None
    authorization_level: Optional[str] = None

    # Data integrity
    checksum: Optional[str] = None
    signature: Optional[str] = None


@dataclass
class TransferRecord:
    """Record of memory ownership or scope transfer"""

    transfer_id: str
    memory_id: str
    transfer_type: str  # "ownership", "scope", "delegation"

    # Transfer parties
    from_scope: ScopeIdentifier
    to_scope: ScopeIdentifier
    initiated_by: int
    approved_by: Optional[int] = None

    # Transfer details
    transfer_reason: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    initiated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Status
    status: str = (
        "pending"  # "pending", "approved", "completed", "rejected", "cancelled"
    )

    # Audit trail
    approval_chain: List[Dict[str, Any]] = field(default_factory=list)
    verification_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditQuery:
    """Query parameters for audit log searches"""

    event_types: Optional[Set[AuditEventType]] = None
    severity_levels: Optional[Set[AuditSeverity]] = None
    memory_ids: Optional[Set[str]] = None
    user_ids: Optional[Set[int]] = None
    scopes: Optional[Set[ScopeIdentifier]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class MemorySharingAuditLogger:
    """
    SPEC-049: Memory Sharing Audit Logger

    Comprehensive audit logging system for memory sharing operations
    with transfer tracking, compliance reporting, and security monitoring.
    """

    def __init__(self, retention_days: int = 2555):  # 7 years default
        self.audit_events: List[AuditEvent] = []
        self.transfer_records: Dict[str, TransferRecord] = {}
        self.retention_days = retention_days

        # Indexing for fast queries
        self.event_index: Dict[str, Set[int]] = {}  # field_value -> event_indices
        self.memory_index: Dict[str, List[int]] = {}  # memory_id -> event_indices
        self.user_index: Dict[int, List[int]] = {}  # user_id -> event_indices

        # Compliance tracking
        self.compliance_reports: Dict[str, Dict[str, Any]] = {}

        # Security monitoring
        self.security_alerts: List[Dict[str, Any]] = []
        self.suspicious_patterns: Dict[str, int] = {}

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start_services(self) -> None:
        """Start background services"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Audit logger services started")

    async def stop_services(self) -> None:
        """Stop background services"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Audit logger services stopped")

    async def log_event(
        self,
        event_type: AuditEventType,
        description: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        **kwargs,
    ) -> AuditEvent:
        """Log an audit event"""
        try:
            event_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.audit_events)}"

            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                severity=severity,
                timestamp=datetime.now(timezone.utc),
                description=description,
                **kwargs,
            )

            # Generate checksum for integrity
            event.checksum = self._generate_event_checksum(event)

            # Add to audit log
            event_index = len(self.audit_events)
            self.audit_events.append(event)

            # Update indices
            await self._update_indices(event, event_index)

            # Check for security patterns
            await self._check_security_patterns(event)

            # Log to system logger for external monitoring
            log_level = {
                AuditSeverity.INFO: logging.INFO,
                AuditSeverity.WARNING: logging.WARNING,
                AuditSeverity.ERROR: logging.ERROR,
                AuditSeverity.CRITICAL: logging.CRITICAL,
            }.get(severity, logging.INFO)

            logger.log(log_level, f"AUDIT: {event_type.value} - {description}")

            return event

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            raise

    async def log_contract_event(
        self,
        contract: MemoryLinkContract,
        event_type: AuditEventType,
        user_id: int,
        description: str,
        **kwargs,
    ) -> AuditEvent:
        """Log a contract-related audit event"""
        return await self.log_event(
            event_type=event_type,
            description=description,
            memory_id=contract.memory_id,
            contract_id=contract.contract_id,
            user_id=user_id,
            source_scope=contract.owner_scope,
            target_scope=contract.target_scope,
            details={
                "permissions": [p.value for p in contract.permissions],
                "visibility_level": contract.visibility_level.value,
                "contract_status": contract.status.value,
                **kwargs,
            },
        )

    async def log_access_event(
        self,
        memory_id: str,
        user_id: int,
        accessing_scope: ScopeIdentifier,
        access_type: str,
        success: bool,
        **kwargs,
    ) -> AuditEvent:
        """Log a memory access event"""
        event_type = AuditEventType.MEMORY_ACCESSED
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING

        if not success:
            event_type = AuditEventType.UNAUTHORIZED_ACCESS
            severity = AuditSeverity.ERROR

        return await self.log_event(
            event_type=event_type,
            severity=severity,
            description=f"Memory {access_type} {'successful' if success else 'failed'}",
            memory_id=memory_id,
            user_id=user_id,
            source_scope=accessing_scope,
            details={"access_type": access_type, "success": success, **kwargs},
        )

    async def create_transfer_record(
        self,
        memory_id: str,
        transfer_type: str,
        from_scope: ScopeIdentifier,
        to_scope: ScopeIdentifier,
        initiated_by: int,
        transfer_reason: str = "",
        conditions: Optional[Dict[str, Any]] = None,
    ) -> TransferRecord:
        """Create a memory transfer record"""
        try:
            transfer_id = (
                f"transfer_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{memory_id}"
            )

            transfer = TransferRecord(
                transfer_id=transfer_id,
                memory_id=memory_id,
                transfer_type=transfer_type,
                from_scope=from_scope,
                to_scope=to_scope,
                initiated_by=initiated_by,
                transfer_reason=transfer_reason,
                conditions=conditions or {},
            )

            self.transfer_records[transfer_id] = transfer

            # Log audit event
            await self.log_event(
                event_type=AuditEventType.MEMORY_TRANSFERRED,
                description=f"Memory transfer initiated: {transfer_type}",
                memory_id=memory_id,
                user_id=initiated_by,
                source_scope=from_scope,
                target_scope=to_scope,
                details={
                    "transfer_id": transfer_id,
                    "transfer_type": transfer_type,
                    "reason": transfer_reason,
                },
            )

            logger.info(f"Created transfer record {transfer_id}")
            return transfer

        except Exception as e:
            logger.error(f"Failed to create transfer record: {e}")
            raise

    async def complete_transfer(
        self,
        transfer_id: str,
        approved_by: int,
        verification_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Complete a memory transfer"""
        try:
            transfer = self.transfer_records.get(transfer_id)
            if not transfer:
                raise ValueError(f"Transfer record {transfer_id} not found")

            transfer.status = "completed"
            transfer.completed_at = datetime.now(timezone.utc)
            transfer.approved_by = approved_by
            transfer.verification_data = verification_data or {}

            # Log completion
            await self.log_event(
                event_type=AuditEventType.OWNERSHIP_CHANGED,
                description=f"Memory transfer completed: {transfer.transfer_type}",
                memory_id=transfer.memory_id,
                user_id=approved_by,
                source_scope=transfer.from_scope,
                target_scope=transfer.to_scope,
                details={
                    "transfer_id": transfer_id,
                    "initiated_by": transfer.initiated_by,
                    "approved_by": approved_by,
                },
            )

            return True

        except Exception as e:
            logger.error(f"Failed to complete transfer: {e}")
            raise

    async def query_audit_log(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit log with filters"""
        try:
            matching_events = []

            for i, event in enumerate(self.audit_events):
                # Apply filters
                if query.event_types and event.event_type not in query.event_types:
                    continue

                if (
                    query.severity_levels
                    and event.severity not in query.severity_levels
                ):
                    continue

                if query.memory_ids and event.memory_id not in query.memory_ids:
                    continue

                if query.user_ids and event.user_id not in query.user_ids:
                    continue

                if query.start_time and event.timestamp < query.start_time:
                    continue

                if query.end_time and event.timestamp > query.end_time:
                    continue

                if query.scopes:
                    scope_match = False
                    for scope in query.scopes:
                        if (
                            event.source_scope
                            and self._scope_matches(event.source_scope, scope)
                        ) or (
                            event.target_scope
                            and self._scope_matches(event.target_scope, scope)
                        ):
                            scope_match = True
                            break
                    if not scope_match:
                        continue

                matching_events.append(event)

            # Sort by timestamp (newest first)
            matching_events.sort(key=lambda e: e.timestamp, reverse=True)

            # Apply pagination
            start_idx = query.offset
            end_idx = start_idx + query.limit

            return matching_events[start_idx:end_idx]

        except Exception as e:
            logger.error(f"Failed to query audit log: {e}")
            return []

    async def generate_compliance_report(
        self,
        scope: ScopeIdentifier,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "full",
    ) -> Dict[str, Any]:
        """Generate compliance report for a scope"""
        try:
            query = AuditQuery(
                scopes={scope}, start_time=start_date, end_time=end_date, limit=10000
            )

            events = await self.query_audit_log(query)

            report = {
                "scope": {
                    "type": scope.scope_type.value,
                    "id": scope.scope_id,
                    "display_name": scope.display_name,
                },
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "summary": {
                    "total_events": len(events),
                    "event_types": {},
                    "severity_breakdown": {},
                    "unique_memories": set(),
                    "unique_users": set(),
                },
                "security_events": [],
                "transfer_events": [],
                "access_patterns": {},
                "compliance_status": "compliant",
            }

            # Analyze events
            for event in events:
                # Count event types
                event_type = event.event_type.value
                report["summary"]["event_types"][event_type] = (
                    report["summary"]["event_types"].get(event_type, 0) + 1
                )

                # Count severity levels
                severity = event.severity.value
                report["summary"]["severity_breakdown"][severity] = (
                    report["summary"]["severity_breakdown"].get(severity, 0) + 1
                )

                # Track unique entities
                if event.memory_id:
                    report["summary"]["unique_memories"].add(event.memory_id)
                if event.user_id:
                    report["summary"]["unique_users"].add(event.user_id)

                # Collect security events
                if event.event_type in [
                    AuditEventType.UNAUTHORIZED_ACCESS,
                    AuditEventType.SUSPICIOUS_ACTIVITY,
                    AuditEventType.SECURITY_VIOLATION,
                ]:
                    report["security_events"].append(
                        {
                            "event_id": event.event_id,
                            "type": event.event_type.value,
                            "timestamp": event.timestamp.isoformat(),
                            "description": event.description,
                            "severity": event.severity.value,
                        }
                    )

                # Collect transfer events
                if event.event_type in [
                    AuditEventType.MEMORY_TRANSFERRED,
                    AuditEventType.OWNERSHIP_CHANGED,
                ]:
                    report["transfer_events"].append(
                        {
                            "event_id": event.event_id,
                            "type": event.event_type.value,
                            "timestamp": event.timestamp.isoformat(),
                            "memory_id": event.memory_id,
                            "description": event.description,
                        }
                    )

            # Convert sets to counts
            report["summary"]["unique_memories"] = len(
                report["summary"]["unique_memories"]
            )
            report["summary"]["unique_users"] = len(report["summary"]["unique_users"])

            # Determine compliance status
            if report["security_events"]:
                report["compliance_status"] = "needs_review"

            # Store report
            report_id = f"report_{scope.scope_type.value}_{scope.scope_id}_{start_date.strftime('%Y%m%d')}"
            self.compliance_reports[report_id] = report

            return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {}

    async def get_security_alerts(
        self, severity_filter: Optional[AuditSeverity] = None, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent security alerts"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            security_events = [
                event
                for event in self.audit_events
                if (
                    event.timestamp >= cutoff_time
                    and event.event_type
                    in [
                        AuditEventType.UNAUTHORIZED_ACCESS,
                        AuditEventType.SUSPICIOUS_ACTIVITY,
                        AuditEventType.SECURITY_VIOLATION,
                    ]
                    and (not severity_filter or event.severity == severity_filter)
                )
            ]

            alerts = []
            for event in security_events:
                alert = {
                    "event_id": event.event_id,
                    "type": event.event_type.value,
                    "severity": event.severity.value,
                    "timestamp": event.timestamp.isoformat(),
                    "description": event.description,
                    "memory_id": event.memory_id,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "details": event.details,
                }
                alerts.append(alert)

            return alerts

        except Exception as e:
            logger.error(f"Failed to get security alerts: {e}")
            return []

    # Private helper methods
    def _generate_event_checksum(self, event: AuditEvent) -> str:
        """Generate checksum for event integrity"""
        try:
            # Create deterministic string representation
            data = {
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "memory_id": event.memory_id,
                "user_id": event.user_id,
                "description": event.description,
            }

            data_str = json.dumps(data, sort_keys=True)
            return hashlib.sha256(data_str.encode()).hexdigest()

        except Exception as e:
            logger.error(f"Failed to generate event checksum: {e}")
            return ""

    async def _update_indices(self, event: AuditEvent, event_index: int) -> None:
        """Update search indices"""
        try:
            # Memory index
            if event.memory_id:
                if event.memory_id not in self.memory_index:
                    self.memory_index[event.memory_id] = []
                self.memory_index[event.memory_id].append(event_index)

            # User index
            if event.user_id:
                if event.user_id not in self.user_index:
                    self.user_index[event.user_id] = []
                self.user_index[event.user_id].append(event_index)

        except Exception as e:
            logger.error(f"Failed to update indices: {e}")

    async def _check_security_patterns(self, event: AuditEvent) -> None:
        """Check for suspicious security patterns"""
        try:
            # Track failed access attempts
            if event.event_type == AuditEventType.UNAUTHORIZED_ACCESS:
                key = f"failed_access_{event.user_id}_{event.memory_id}"
                self.suspicious_patterns[key] = self.suspicious_patterns.get(key, 0) + 1

                # Alert on multiple failures
                if self.suspicious_patterns[key] >= 5:
                    await self.log_event(
                        event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                        severity=AuditSeverity.WARNING,
                        description=f"Multiple failed access attempts detected",
                        user_id=event.user_id,
                        memory_id=event.memory_id,
                        details={"failure_count": self.suspicious_patterns[key]},
                    )

        except Exception as e:
            logger.error(f"Failed to check security patterns: {e}")

    def _scope_matches(self, scope1: ScopeIdentifier, scope2: ScopeIdentifier) -> bool:
        """Check if two scopes match"""
        return (
            scope1.scope_type == scope2.scope_type
            and scope1.scope_id == scope2.scope_id
        )

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop"""
        while True:
            try:
                await self._cleanup_old_events()
                await asyncio.sleep(86400)  # Daily cleanup

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(86400)

    async def _monitoring_loop(self) -> None:
        """Background security monitoring loop"""
        while True:
            try:
                await self._monitor_security_patterns()
                await asyncio.sleep(300)  # Check every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(300)

    async def _cleanup_old_events(self) -> None:
        """Clean up old audit events"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(
                days=self.retention_days
            )

            # Count events to remove
            old_events = sum(
                1 for event in self.audit_events if event.timestamp < cutoff_date
            )

            if old_events > 0:
                # Keep only recent events
                self.audit_events = [
                    event
                    for event in self.audit_events
                    if event.timestamp >= cutoff_date
                ]

                # Rebuild indices
                self.memory_index.clear()
                self.user_index.clear()

                for i, event in enumerate(self.audit_events):
                    await self._update_indices(event, i)

                logger.info(f"Cleaned up {old_events} old audit events")

        except Exception as e:
            logger.error(f"Failed to cleanup old events: {e}")

    async def _monitor_security_patterns(self) -> None:
        """Monitor for security patterns and generate alerts"""
        try:
            # Reset counters older than 1 hour
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)

            # This is a simplified version - in production you'd have more sophisticated pattern detection

        except Exception as e:
            logger.error(f"Failed to monitor security patterns: {e}")


# Global audit logger instance
_audit_logger: Optional[MemorySharingAuditLogger] = None


async def get_audit_logger() -> MemorySharingAuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = MemorySharingAuditLogger()
        await _audit_logger.start_services()
    return _audit_logger


async def reset_audit_logger() -> None:
    """Reset the global audit logger (useful for testing)"""
    global _audit_logger
    if _audit_logger:
        await _audit_logger.stop_services()
    _audit_logger = None
