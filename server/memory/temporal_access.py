"""
SPEC-049: Temporal Access Manager
Session-based and time-limited memory sharing with revocation capabilities
"""

import asyncio
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from .sharing_contracts import ContractStatus, MemoryLinkContract, ScopeIdentifier

logger = logging.getLogger(__name__)


class AccessType(Enum):
    """Types of temporal access"""

    SESSION_BASED = "session_based"  # Access tied to user session
    TIME_LIMITED = "time_limited"  # Fixed time duration
    USAGE_LIMITED = "usage_limited"  # Limited number of accesses
    CONDITIONAL = "conditional"  # Access based on conditions
    RECURRING = "recurring"  # Recurring access windows


class AccessStatus(Enum):
    """Status of temporal access"""

    ACTIVE = "active"  # Currently accessible
    EXPIRED = "expired"  # Time/usage expired
    REVOKED = "revoked"  # Manually revoked
    SUSPENDED = "suspended"  # Temporarily suspended
    PENDING = "pending"  # Awaiting activation


class RevocationReason(Enum):
    """Reasons for access revocation"""

    USER_REQUEST = "user_request"  # User requested revocation
    SECURITY_BREACH = "security_breach"  # Security incident
    POLICY_VIOLATION = "policy_violation"  # Policy violation detected
    ADMIN_ACTION = "admin_action"  # Administrative action
    AUTO_CLEANUP = "auto_cleanup"  # Automatic cleanup
    CONTRACT_CHANGE = "contract_change"  # Contract terms changed


@dataclass
class TemporalAccessGrant:
    """Temporal access grant for memory sharing"""

    grant_id: str
    memory_id: str
    contract_id: str
    grantee_scope: ScopeIdentifier
    access_type: AccessType
    status: AccessStatus
    created_at: datetime
    created_by: int

    # Time-based controls
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    # Usage-based controls
    usage_limit: Optional[int] = None
    usage_count: int = 0

    # Session-based controls
    session_id: Optional[str] = None
    session_expires_at: Optional[datetime] = None

    # Conditional controls
    conditions: Dict[str, Any] = field(default_factory=dict)

    # Access tracking
    first_accessed_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    access_history: List[Dict[str, Any]] = field(default_factory=list)

    # Revocation info
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[int] = None
    revocation_reason: Optional[RevocationReason] = None
    revocation_note: Optional[str] = None


@dataclass
class AccessSession:
    """Session for temporal access tracking"""

    session_id: str
    user_id: int
    scope: ScopeIdentifier
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessWindow:
    """Recurring access window definition"""

    window_id: str
    grant_id: str
    start_time: str  # Time of day (HH:MM)
    end_time: str  # Time of day (HH:MM)
    days_of_week: Set[int]  # 0=Monday, 6=Sunday
    timezone: str = "UTC"
    is_active: bool = True


class TemporalAccessManager:
    """
    SPEC-049: Temporal Access Manager

    Manages time-limited, session-based, and conditional access to memories
    with comprehensive revocation and audit capabilities.
    """

    def __init__(self):
        self.access_grants: Dict[str, TemporalAccessGrant] = {}
        self.active_sessions: Dict[str, AccessSession] = {}
        self.access_windows: Dict[str, List[AccessWindow]] = {}  # grant_id -> windows
        self.revocation_callbacks: List[Callable[[str], None]] = []

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 300  # 5 minutes

    async def start_cleanup_service(self) -> None:
        """Start the cleanup service for expired access"""
        if self._cleanup_task:
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Temporal access cleanup service started")

    async def stop_cleanup_service(self) -> None:
        """Stop the cleanup service"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Temporal access cleanup service stopped")

    async def create_temporal_access(
        self,
        memory_id: str,
        contract_id: str,
        grantee_scope: ScopeIdentifier,
        access_type: AccessType,
        creator_user_id: int,
        **kwargs,
    ) -> TemporalAccessGrant:
        """Create a new temporal access grant"""
        try:
            grant_id = f"grant_{secrets.token_urlsafe(16)}"

            # Create base grant
            grant = TemporalAccessGrant(
                grant_id=grant_id,
                memory_id=memory_id,
                contract_id=contract_id,
                grantee_scope=grantee_scope,
                access_type=access_type,
                status=AccessStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                created_by=creator_user_id,
            )

            # Configure based on access type
            if access_type == AccessType.TIME_LIMITED:
                grant.duration_minutes = kwargs.get("duration_minutes", 60)
                grant.expires_at = kwargs.get("expires_at")
                if not grant.expires_at and grant.duration_minutes:
                    grant.expires_at = datetime.now(timezone.utc) + timedelta(
                        minutes=grant.duration_minutes
                    )

            elif access_type == AccessType.USAGE_LIMITED:
                grant.usage_limit = kwargs.get("usage_limit", 1)

            elif access_type == AccessType.SESSION_BASED:
                session_duration = kwargs.get(
                    "session_duration_minutes", 480
                )  # 8 hours default
                grant.session_expires_at = datetime.now(timezone.utc) + timedelta(
                    minutes=session_duration
                )

            elif access_type == AccessType.CONDITIONAL:
                grant.conditions = kwargs.get("conditions", {})

            elif access_type == AccessType.RECURRING:
                # Create access windows
                windows_config = kwargs.get("access_windows", [])
                await self._create_access_windows(grant_id, windows_config)

            # Set start time
            grant.starts_at = kwargs.get("starts_at", datetime.now(timezone.utc))

            # Activate if start time is now or past
            if grant.starts_at <= datetime.now(timezone.utc):
                grant.status = AccessStatus.ACTIVE

            # Store grant
            self.access_grants[grant_id] = grant

            logger.info(
                f"Created temporal access grant {grant_id} for memory {memory_id}"
            )
            return grant

        except Exception as e:
            logger.error(f"Failed to create temporal access: {e}")
            raise

    async def check_access_permission(
        self,
        memory_id: str,
        accessing_user_id: int,
        accessing_scope: ScopeIdentifier,
        session_id: Optional[str] = None,
    ) -> Optional[TemporalAccessGrant]:
        """Check if access is permitted and return active grant"""
        try:
            current_time = datetime.now(timezone.utc)

            # Find grants for this memory and scope
            matching_grants = [
                grant
                for grant in self.access_grants.values()
                if (
                    grant.memory_id == memory_id
                    and self._scope_matches(grant.grantee_scope, accessing_scope)
                )
            ]

            for grant in matching_grants:
                # Check if grant is active
                if grant.status != AccessStatus.ACTIVE:
                    continue

                # Check time-based constraints
                if grant.starts_at and current_time < grant.starts_at:
                    continue

                if grant.expires_at and current_time > grant.expires_at:
                    grant.status = AccessStatus.EXPIRED
                    continue

                # Check usage limits
                if grant.usage_limit and grant.usage_count >= grant.usage_limit:
                    grant.status = AccessStatus.EXPIRED
                    continue

                # Check session-based access
                if grant.access_type == AccessType.SESSION_BASED:
                    if not session_id:
                        continue

                    session = self.active_sessions.get(session_id)
                    if not session or not session.is_active:
                        continue

                    if current_time > session.expires_at:
                        session.is_active = False
                        continue

                    grant.session_id = session_id

                # Check recurring access windows
                if grant.access_type == AccessType.RECURRING:
                    if not await self._is_in_access_window(
                        grant.grant_id, current_time
                    ):
                        continue

                # Check conditional access
                if grant.access_type == AccessType.CONDITIONAL:
                    if not await self._check_access_conditions(
                        grant, accessing_user_id
                    ):
                        continue

                # Access granted - update tracking
                await self._track_access(grant, accessing_user_id)
                return grant

            return None

        except Exception as e:
            logger.error(f"Failed to check access permission: {e}")
            return None

    async def revoke_access(
        self,
        grant_id: str,
        revoking_user_id: int,
        reason: RevocationReason,
        note: Optional[str] = None,
    ) -> bool:
        """Revoke temporal access"""
        try:
            grant = self.access_grants.get(grant_id)
            if not grant:
                raise ValueError(f"Access grant {grant_id} not found")

            # Update grant status
            grant.status = AccessStatus.REVOKED
            grant.revoked_at = datetime.now(timezone.utc)
            grant.revoked_by = revoking_user_id
            grant.revocation_reason = reason
            grant.revocation_note = note

            # Notify callbacks
            for callback in self.revocation_callbacks:
                try:
                    callback(grant_id)
                except Exception as e:
                    logger.error(f"Revocation callback failed: {e}")

            logger.info(f"Revoked access grant {grant_id} by user {revoking_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke access: {e}")
            raise

    async def create_access_session(
        self,
        user_id: int,
        scope: ScopeIdentifier,
        duration_minutes: int = 480,  # 8 hours default
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AccessSession:
        """Create a new access session"""
        try:
            session_id = f"session_{secrets.token_urlsafe(16)}"

            session = AccessSession(
                session_id=session_id,
                user_id=user_id,
                scope=scope,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc)
                + timedelta(minutes=duration_minutes),
                last_activity_at=datetime.now(timezone.utc),
                metadata=metadata or {},
            )

            self.active_sessions[session_id] = session

            logger.info(f"Created access session {session_id} for user {user_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create access session: {e}")
            raise

    async def extend_access(
        self,
        grant_id: str,
        extending_user_id: int,
        additional_minutes: Optional[int] = None,
        additional_usage: Optional[int] = None,
    ) -> bool:
        """Extend temporal access duration or usage"""
        try:
            grant = self.access_grants.get(grant_id)
            if not grant:
                raise ValueError(f"Access grant {grant_id} not found")

            if grant.status not in [AccessStatus.ACTIVE, AccessStatus.EXPIRED]:
                raise ValueError(f"Cannot extend access in status {grant.status.value}")

            # Extend time-based access
            if additional_minutes and grant.expires_at:
                grant.expires_at += timedelta(minutes=additional_minutes)
                if grant.status == AccessStatus.EXPIRED:
                    grant.status = AccessStatus.ACTIVE

            # Extend usage-based access
            if additional_usage and grant.usage_limit:
                grant.usage_limit += additional_usage
                if grant.status == AccessStatus.EXPIRED:
                    grant.status = AccessStatus.ACTIVE

            logger.info(f"Extended access grant {grant_id} by user {extending_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to extend access: {e}")
            raise

    async def list_active_grants(
        self,
        memory_id: Optional[str] = None,
        scope: Optional[ScopeIdentifier] = None,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List active temporal access grants"""
        try:
            grants = []

            for grant in self.access_grants.values():
                # Apply filters
                if memory_id and grant.memory_id != memory_id:
                    continue

                if scope and not self._scope_matches(grant.grantee_scope, scope):
                    continue

                if user_id and grant.created_by != user_id:
                    continue

                # Only include active or recently expired grants
                if grant.status not in [AccessStatus.ACTIVE, AccessStatus.EXPIRED]:
                    continue

                grant_info = {
                    "grant_id": grant.grant_id,
                    "memory_id": grant.memory_id,
                    "contract_id": grant.contract_id,
                    "grantee_scope": {
                        "type": grant.grantee_scope.scope_type.value,
                        "id": grant.grantee_scope.scope_id,
                        "display_name": grant.grantee_scope.display_name,
                    },
                    "access_type": grant.access_type.value,
                    "status": grant.status.value,
                    "created_at": grant.created_at.isoformat(),
                    "starts_at": (
                        grant.starts_at.isoformat() if grant.starts_at else None
                    ),
                    "expires_at": (
                        grant.expires_at.isoformat() if grant.expires_at else None
                    ),
                    "usage_count": grant.usage_count,
                    "usage_limit": grant.usage_limit,
                    "last_accessed_at": (
                        grant.last_accessed_at.isoformat()
                        if grant.last_accessed_at
                        else None
                    ),
                }

                grants.append(grant_info)

            return grants

        except Exception as e:
            logger.error(f"Failed to list active grants: {e}")
            return []

    async def get_access_statistics(
        self, scope: Optional[ScopeIdentifier] = None, time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get temporal access statistics"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_window_hours
            )

            stats = {
                "total_grants": 0,
                "active_grants": 0,
                "expired_grants": 0,
                "revoked_grants": 0,
                "total_accesses": 0,
                "unique_memories": set(),
                "access_types": {},
                "revocation_reasons": {},
            }

            for grant in self.access_grants.values():
                # Apply scope filter
                if scope and not self._scope_matches(grant.grantee_scope, scope):
                    continue

                # Apply time window filter
                if grant.created_at < cutoff_time:
                    continue

                stats["total_grants"] += 1
                stats["unique_memories"].add(grant.memory_id)
                stats["total_accesses"] += grant.usage_count

                # Count by status
                if grant.status == AccessStatus.ACTIVE:
                    stats["active_grants"] += 1
                elif grant.status == AccessStatus.EXPIRED:
                    stats["expired_grants"] += 1
                elif grant.status == AccessStatus.REVOKED:
                    stats["revoked_grants"] += 1

                # Count by access type
                access_type = grant.access_type.value
                stats["access_types"][access_type] = (
                    stats["access_types"].get(access_type, 0) + 1
                )

                # Count revocation reasons
                if grant.revocation_reason:
                    reason = grant.revocation_reason.value
                    stats["revocation_reasons"][reason] = (
                        stats["revocation_reasons"].get(reason, 0) + 1
                    )

            stats["unique_memories"] = len(stats["unique_memories"])
            return stats

        except Exception as e:
            logger.error(f"Failed to get access statistics: {e}")
            return {}

    def add_revocation_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for access revocation events"""
        self.revocation_callbacks.append(callback)

    def remove_revocation_callback(self, callback: Callable[[str], None]) -> None:
        """Remove revocation callback"""
        if callback in self.revocation_callbacks:
            self.revocation_callbacks.remove(callback)

    # Private helper methods
    async def _track_access(self, grant: TemporalAccessGrant, user_id: int) -> None:
        """Track access to memory"""
        try:
            current_time = datetime.now(timezone.utc)

            if not grant.first_accessed_at:
                grant.first_accessed_at = current_time

            grant.last_accessed_at = current_time
            grant.usage_count += 1

            # Add to access history
            access_record = {
                "timestamp": current_time.isoformat(),
                "user_id": user_id,
                "session_id": grant.session_id,
            }

            grant.access_history.append(access_record)

            # Limit history size
            if len(grant.access_history) > 1000:
                grant.access_history = grant.access_history[-1000:]

        except Exception as e:
            logger.error(f"Failed to track access: {e}")

    async def _create_access_windows(
        self, grant_id: str, windows_config: List[Dict[str, Any]]
    ) -> None:
        """Create recurring access windows"""
        try:
            windows = []

            for config in windows_config:
                window = AccessWindow(
                    window_id=f"window_{secrets.token_urlsafe(8)}",
                    grant_id=grant_id,
                    start_time=config["start_time"],
                    end_time=config["end_time"],
                    days_of_week=set(config["days_of_week"]),
                    timezone=config.get("timezone", "UTC"),
                )
                windows.append(window)

            self.access_windows[grant_id] = windows

        except Exception as e:
            logger.error(f"Failed to create access windows: {e}")
            raise

    async def _is_in_access_window(self, grant_id: str, check_time: datetime) -> bool:
        """Check if current time is within any access window"""
        try:
            windows = self.access_windows.get(grant_id, [])

            for window in windows:
                if not window.is_active:
                    continue

                # Check day of week (0=Monday, 6=Sunday)
                if check_time.weekday() not in window.days_of_week:
                    continue

                # Check time of day
                time_str = check_time.strftime("%H:%M")
                if window.start_time <= time_str <= window.end_time:
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to check access window: {e}")
            return False

    async def _check_access_conditions(
        self, grant: TemporalAccessGrant, user_id: int
    ) -> bool:
        """Check conditional access requirements"""
        try:
            conditions = grant.conditions

            # Check IP restrictions
            if "allowed_ips" in conditions:
                # Would check user's current IP
                pass

            # Check user attributes
            if "required_attributes" in conditions:
                # Would check user attributes
                pass

            # Check time-based conditions
            if "time_restrictions" in conditions:
                current_hour = datetime.now(timezone.utc).hour
                allowed_hours = conditions["time_restrictions"].get("allowed_hours", [])
                if allowed_hours and current_hour not in allowed_hours:
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to check access conditions: {e}")
            return False

    def _scope_matches(self, scope1: ScopeIdentifier, scope2: ScopeIdentifier) -> bool:
        """Check if two scopes match"""
        return (
            scope1.scope_type == scope2.scope_type
            and scope1.scope_id == scope2.scope_id
        )

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop for expired access"""
        while True:
            try:
                await self._cleanup_expired_access()
                await asyncio.sleep(self._cleanup_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(self._cleanup_interval)

    async def _cleanup_expired_access(self) -> None:
        """Clean up expired access grants and sessions"""
        try:
            current_time = datetime.now(timezone.utc)

            # Clean up expired grants
            for grant in self.access_grants.values():
                if grant.status == AccessStatus.ACTIVE:
                    if grant.expires_at and current_time > grant.expires_at:
                        grant.status = AccessStatus.EXPIRED
                    elif grant.usage_limit and grant.usage_count >= grant.usage_limit:
                        grant.status = AccessStatus.EXPIRED

            # Clean up expired sessions
            expired_sessions = [
                session_id
                for session_id, session in self.active_sessions.items()
                if current_time > session.expires_at
            ]

            for session_id in expired_sessions:
                self.active_sessions[session_id].is_active = False

            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        except Exception as e:
            logger.error(f"Failed to cleanup expired access: {e}")


# Global temporal access manager instance
_temporal_access_manager: Optional[TemporalAccessManager] = None


async def get_temporal_access_manager() -> TemporalAccessManager:
    """Get the global temporal access manager instance"""
    global _temporal_access_manager
    if _temporal_access_manager is None:
        _temporal_access_manager = TemporalAccessManager()
        await _temporal_access_manager.start_cleanup_service()
    return _temporal_access_manager


async def reset_temporal_access_manager() -> None:
    """Reset the global temporal access manager (useful for testing)"""
    global _temporal_access_manager
    if _temporal_access_manager:
        await _temporal_access_manager.stop_cleanup_service()
    _temporal_access_manager = None
