"""
SPEC-049: Memory Consent & Visibility Manager
Advanced consent tracking and visibility flag management for memory sharing
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from .sharing_contracts import MemoryLinkContract, ScopeIdentifier, ScopeType

logger = logging.getLogger(__name__)


class ConsentType(Enum):
    """Types of consent for memory sharing"""

    EXPLICIT = "explicit"  # User explicitly granted consent
    IMPLICIT = "implicit"  # Consent implied by action (e.g., joining team)
    DELEGATED = "delegated"  # Consent given by authorized delegate
    INHERITED = "inherited"  # Consent inherited from parent scope
    AUTOMATIC = "automatic"  # Automatic consent based on rules


class VisibilityFlag(Enum):
    """Visibility control flags for memories"""

    DISCOVERABLE = "discoverable"  # Can be found in searches
    LINKABLE = "linkable"  # Can be linked/referenced
    DOWNLOADABLE = "downloadable"  # Can be downloaded/exported
    COMMENTABLE = "commentable"  # Can receive comments
    SHAREABLE = "shareable"  # Can be reshared by recipients
    INDEXABLE = "indexable"  # Can be indexed by search engines
    TRACKABLE = "trackable"  # Usage can be tracked/analyzed
    NOTIFIABLE = "notifiable"  # Owners get notifications on access


class ConsentScope(Enum):
    """Scope of consent application"""

    MEMORY_SPECIFIC = "memory_specific"  # Consent for specific memory
    CATEGORY_WIDE = "category_wide"  # Consent for memory category
    SCOPE_WIDE = "scope_wide"  # Consent for entire scope
    GLOBAL = "global"  # Global consent preferences


@dataclass
class ConsentPreference:
    """User consent preferences for different scenarios"""

    user_id: int
    scope: ScopeIdentifier
    consent_scope: ConsentScope
    consent_type: ConsentType
    auto_grant: bool = False
    require_notification: bool = True
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class VisibilityProfile:
    """Visibility profile for memory or scope"""

    profile_id: str
    owner_scope: ScopeIdentifier
    visibility_flags: Set[VisibilityFlag]
    restrictions: Dict[str, Any] = field(default_factory=dict)
    exceptions: Dict[str, Set[VisibilityFlag]] = field(
        default_factory=dict
    )  # scope -> flags
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConsentRequest:
    """Request for consent to access memory"""

    request_id: str
    memory_id: str
    requesting_scope: ScopeIdentifier
    target_scope: ScopeIdentifier
    requested_permissions: Set[str]
    justification: Optional[str] = None
    urgency_level: str = "normal"  # "low", "normal", "high", "urgent"
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConsentDecision:
    """Decision on a consent request"""

    request_id: str
    deciding_user_id: int
    decision: bool  # True = granted, False = denied
    decision_timestamp: datetime
    decision_reason: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    valid_until: Optional[datetime] = None


class MemoryConsentManager:
    """
    SPEC-049: Memory Consent & Visibility Manager

    Manages consent preferences, visibility flags, and consent request workflows
    for memory sharing across different scopes.
    """

    def __init__(self):
        self.consent_preferences: Dict[str, List[ConsentPreference]] = (
            {}
        )  # user_id -> preferences
        self.visibility_profiles: Dict[str, VisibilityProfile] = (
            {}
        )  # profile_id -> profile
        self.consent_requests: Dict[str, ConsentRequest] = {}  # request_id -> request
        self.consent_decisions: Dict[str, ConsentDecision] = (
            {}
        )  # request_id -> decision

        # Default visibility profiles
        self.default_profiles = self._initialize_default_profiles()

    async def set_consent_preference(
        self,
        user_id: int,
        scope: ScopeIdentifier,
        consent_scope: ConsentScope,
        consent_type: ConsentType,
        auto_grant: bool = False,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> ConsentPreference:
        """Set user consent preferences for a scope"""
        try:
            preference = ConsentPreference(
                user_id=user_id,
                scope=scope,
                consent_scope=consent_scope,
                consent_type=consent_type,
                auto_grant=auto_grant,
                conditions=conditions or {},
            )

            user_key = str(user_id)
            if user_key not in self.consent_preferences:
                self.consent_preferences[user_key] = []

            # Remove existing preference for same scope/type
            self.consent_preferences[user_key] = [
                p
                for p in self.consent_preferences[user_key]
                if not (
                    p.scope.scope_type == scope.scope_type
                    and p.scope.scope_id == scope.scope_id
                    and p.consent_scope == consent_scope
                )
            ]

            # Add new preference
            self.consent_preferences[user_key].append(preference)

            logger.info(
                f"Set consent preference for user {user_id} in scope {scope.scope_type.value}:{scope.scope_id}"
            )
            return preference

        except Exception as e:
            logger.error(f"Failed to set consent preference: {e}")
            raise

    async def create_visibility_profile(
        self,
        owner_scope: ScopeIdentifier,
        visibility_flags: Set[VisibilityFlag],
        restrictions: Optional[Dict[str, Any]] = None,
        exceptions: Optional[Dict[str, Set[VisibilityFlag]]] = None,
    ) -> VisibilityProfile:
        """Create a visibility profile for a scope"""
        try:
            profile_id = (
                f"profile_{owner_scope.scope_type.value}_{owner_scope.scope_id}"
            )

            profile = VisibilityProfile(
                profile_id=profile_id,
                owner_scope=owner_scope,
                visibility_flags=visibility_flags,
                restrictions=restrictions or {},
                exceptions=exceptions or {},
            )

            self.visibility_profiles[profile_id] = profile

            logger.info(f"Created visibility profile {profile_id}")
            return profile

        except Exception as e:
            logger.error(f"Failed to create visibility profile: {e}")
            raise

    async def check_consent_required(
        self,
        memory_id: str,
        requesting_scope: ScopeIdentifier,
        target_scope: ScopeIdentifier,
        requested_permissions: Set[str],
    ) -> bool:
        """Check if consent is required for memory access"""
        try:
            # Check if target scope has consent preferences
            target_users = await self._get_scope_users(target_scope)

            for user_id in target_users:
                preferences = self.consent_preferences.get(str(user_id), [])

                for preference in preferences:
                    # Check if preference applies to this scenario
                    if self._preference_applies(
                        preference,
                        requesting_scope,
                        target_scope,
                        requested_permissions,
                    ):
                        if preference.consent_type == ConsentType.AUTOMATIC:
                            return False  # No consent required
                        elif preference.auto_grant:
                            return False  # Auto-granted
                        else:
                            return True  # Explicit consent required

            # Default: require consent for cross-scope access
            return requesting_scope.scope_type != target_scope.scope_type

        except Exception as e:
            logger.error(f"Failed to check consent requirement: {e}")
            return True  # Default to requiring consent

    async def request_consent(
        self,
        memory_id: str,
        requesting_scope: ScopeIdentifier,
        target_scope: ScopeIdentifier,
        requested_permissions: Set[str],
        justification: Optional[str] = None,
        urgency_level: str = "normal",
    ) -> ConsentRequest:
        """Create a consent request"""
        try:
            request_id = f"consent_req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{requesting_scope.scope_id}"

            request = ConsentRequest(
                request_id=request_id,
                memory_id=memory_id,
                requesting_scope=requesting_scope,
                target_scope=target_scope,
                requested_permissions=requested_permissions,
                justification=justification,
                urgency_level=urgency_level,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=7),  # Default 7-day expiry
            )

            self.consent_requests[request_id] = request

            # Send notifications to target scope users
            await self._send_consent_notifications(request)

            logger.info(f"Created consent request {request_id}")
            return request

        except Exception as e:
            logger.error(f"Failed to create consent request: {e}")
            raise

    async def process_consent_decision(
        self,
        request_id: str,
        deciding_user_id: int,
        decision: bool,
        reason: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        valid_until: Optional[datetime] = None,
    ) -> ConsentDecision:
        """Process a consent decision"""
        try:
            request = self.consent_requests.get(request_id)
            if not request:
                raise ValueError(f"Consent request {request_id} not found")

            # Verify user can make decision for target scope
            if not await self._can_user_decide_consent(
                deciding_user_id, request.target_scope
            ):
                raise PermissionError(
                    "User cannot make consent decisions for target scope"
                )

            decision_obj = ConsentDecision(
                request_id=request_id,
                deciding_user_id=deciding_user_id,
                decision=decision,
                decision_timestamp=datetime.now(timezone.utc),
                decision_reason=reason,
                conditions=conditions or {},
                valid_until=valid_until,
            )

            self.consent_decisions[request_id] = decision_obj

            # Send notification to requesting scope
            await self._send_decision_notification(request, decision_obj)

            logger.info(
                f"Processed consent decision for request {request_id}: {'granted' if decision else 'denied'}"
            )
            return decision_obj

        except Exception as e:
            logger.error(f"Failed to process consent decision: {e}")
            raise

    async def check_visibility_permission(
        self,
        memory_id: str,
        accessing_scope: ScopeIdentifier,
        visibility_flag: VisibilityFlag,
    ) -> bool:
        """Check if scope has specific visibility permission for memory"""
        try:
            # Get visibility profile for memory owner
            owner_scope = await self._get_memory_owner_scope(memory_id)
            if not owner_scope:
                return False

            profile_id = (
                f"profile_{owner_scope.scope_type.value}_{owner_scope.scope_id}"
            )
            profile = self.visibility_profiles.get(profile_id)

            if not profile:
                # Use default profile
                profile = self.default_profiles.get(owner_scope.scope_type.value)

            if not profile:
                return False

            # Check exceptions first
            scope_key = f"{accessing_scope.scope_type.value}:{accessing_scope.scope_id}"
            if scope_key in profile.exceptions:
                return visibility_flag in profile.exceptions[scope_key]

            # Check general visibility flags
            return visibility_flag in profile.visibility_flags

        except Exception as e:
            logger.error(f"Failed to check visibility permission: {e}")
            return False

    async def get_pending_consent_requests(
        self, target_scope: ScopeIdentifier, user_id: int
    ) -> List[Dict[str, Any]]:
        """Get pending consent requests for a scope"""
        try:
            # Verify user can view requests for target scope
            if not await self._can_user_decide_consent(user_id, target_scope):
                raise PermissionError(
                    "User cannot view consent requests for target scope"
                )

            pending_requests = []

            for request in self.consent_requests.values():
                # Check if request targets this scope
                if not self._scope_matches(request.target_scope, target_scope):
                    continue

                # Check if request is still pending
                if request_id in self.consent_decisions:
                    continue

                # Check if request has expired
                if (
                    request.expires_at
                    and datetime.now(timezone.utc) > request.expires_at
                ):
                    continue

                request_info = {
                    "request_id": request.request_id,
                    "memory_id": request.memory_id,
                    "requesting_scope": {
                        "type": request.requesting_scope.scope_type.value,
                        "id": request.requesting_scope.scope_id,
                        "display_name": request.requesting_scope.display_name,
                    },
                    "requested_permissions": list(request.requested_permissions),
                    "justification": request.justification,
                    "urgency_level": request.urgency_level,
                    "created_at": request.created_at.isoformat(),
                    "expires_at": (
                        request.expires_at.isoformat() if request.expires_at else None
                    ),
                }

                pending_requests.append(request_info)

            return pending_requests

        except Exception as e:
            logger.error(f"Failed to get pending consent requests: {e}")
            return []

    async def get_consent_statistics(
        self, scope: ScopeIdentifier, user_id: int
    ) -> Dict[str, Any]:
        """Get consent statistics for a scope"""
        try:
            # Verify user can access scope statistics
            if not await self._can_user_decide_consent(user_id, scope):
                raise PermissionError("User cannot access consent statistics for scope")

            stats = {
                "scope": {
                    "type": scope.scope_type.value,
                    "id": scope.scope_id,
                    "display_name": scope.display_name,
                },
                "pending_requests": 0,
                "granted_requests": 0,
                "denied_requests": 0,
                "expired_requests": 0,
                "auto_granted": 0,
                "consent_preferences": 0,
            }

            now = datetime.now(timezone.utc)

            # Count requests
            for request in self.consent_requests.values():
                if not self._scope_matches(request.target_scope, scope):
                    continue

                decision = self.consent_decisions.get(request.request_id)

                if not decision:
                    if request.expires_at and now > request.expires_at:
                        stats["expired_requests"] += 1
                    else:
                        stats["pending_requests"] += 1
                elif decision.decision:
                    stats["granted_requests"] += 1
                else:
                    stats["denied_requests"] += 1

            # Count consent preferences
            scope_users = await self._get_scope_users(scope)
            for user_id in scope_users:
                user_prefs = self.consent_preferences.get(str(user_id), [])
                stats["consent_preferences"] += len(user_prefs)
                stats["auto_granted"] += sum(1 for p in user_prefs if p.auto_grant)

            return stats

        except Exception as e:
            logger.error(f"Failed to get consent statistics: {e}")
            return {}

    # Private helper methods
    def _preference_applies(
        self,
        preference: ConsentPreference,
        requesting_scope: ScopeIdentifier,
        target_scope: ScopeIdentifier,
        requested_permissions: Set[str],
    ) -> bool:
        """Check if consent preference applies to this scenario"""
        # Check scope match
        if not self._scope_matches(preference.scope, target_scope):
            return False

        # Check conditions
        if "allowed_scopes" in preference.conditions:
            allowed_scopes = preference.conditions["allowed_scopes"]
            scope_key = (
                f"{requesting_scope.scope_type.value}:{requesting_scope.scope_id}"
            )
            if scope_key not in allowed_scopes:
                return False

        if "allowed_permissions" in preference.conditions:
            allowed_perms = set(preference.conditions["allowed_permissions"])
            if not requested_permissions.issubset(allowed_perms):
                return False

        return True

    def _scope_matches(self, scope1: ScopeIdentifier, scope2: ScopeIdentifier) -> bool:
        """Check if two scopes match"""
        return (
            scope1.scope_type == scope2.scope_type
            and scope1.scope_id == scope2.scope_id
        )

    async def _get_scope_users(self, scope: ScopeIdentifier) -> Set[int]:
        """Get all users in a scope"""
        # This would integrate with your user/team/org management system
        # For now, return mock data
        if scope.scope_type == ScopeType.USER:
            return {int(scope.scope_id)}
        else:
            # Mock: return some users for team/org scopes
            return {1, 2, 3}  # Replace with actual implementation

    async def _can_user_decide_consent(
        self, user_id: int, scope: ScopeIdentifier
    ) -> bool:
        """Check if user can make consent decisions for a scope"""
        if scope.scope_type == ScopeType.USER:
            return scope.scope_id == str(user_id)

        # For team/org scopes, check if user is admin/owner
        scope_users = await self._get_scope_users(scope)
        return user_id in scope_users  # Simplified - would check admin role

    async def _get_memory_owner_scope(
        self, memory_id: str
    ) -> Optional[ScopeIdentifier]:
        """Get the owner scope for a memory"""
        # This would integrate with your memory management system
        # For now, return mock data
        return ScopeIdentifier(
            scope_type=ScopeType.USER, scope_id="1", display_name="Mock User"
        )

    async def _send_consent_notifications(self, request: ConsentRequest) -> None:
        """Send notifications about consent request"""
        # This would integrate with your notification system
        logger.info(f"Sending consent notification for request {request.request_id}")

    async def _send_decision_notification(
        self, request: ConsentRequest, decision: ConsentDecision
    ) -> None:
        """Send notification about consent decision"""
        # This would integrate with your notification system
        logger.info(f"Sending decision notification for request {request.request_id}")

    def _initialize_default_profiles(self) -> Dict[str, VisibilityProfile]:
        """Initialize default visibility profiles"""
        return {
            "user": VisibilityProfile(
                profile_id="default_user",
                owner_scope=ScopeIdentifier(ScopeType.USER, "default"),
                visibility_flags={
                    VisibilityFlag.DISCOVERABLE,
                    VisibilityFlag.LINKABLE,
                    VisibilityFlag.COMMENTABLE,
                    VisibilityFlag.NOTIFIABLE,
                },
            ),
            "team": VisibilityProfile(
                profile_id="default_team",
                owner_scope=ScopeIdentifier(ScopeType.TEAM, "default"),
                visibility_flags={
                    VisibilityFlag.DISCOVERABLE,
                    VisibilityFlag.LINKABLE,
                    VisibilityFlag.DOWNLOADABLE,
                    VisibilityFlag.COMMENTABLE,
                    VisibilityFlag.SHAREABLE,
                    VisibilityFlag.TRACKABLE,
                    VisibilityFlag.NOTIFIABLE,
                },
            ),
            "organization": VisibilityProfile(
                profile_id="default_org",
                owner_scope=ScopeIdentifier(ScopeType.ORGANIZATION, "default"),
                visibility_flags={
                    VisibilityFlag.DISCOVERABLE,
                    VisibilityFlag.LINKABLE,
                    VisibilityFlag.DOWNLOADABLE,
                    VisibilityFlag.COMMENTABLE,
                    VisibilityFlag.SHAREABLE,
                    VisibilityFlag.INDEXABLE,
                    VisibilityFlag.TRACKABLE,
                    VisibilityFlag.NOTIFIABLE,
                },
            ),
        }


# Global consent manager instance
_consent_manager: Optional[MemoryConsentManager] = None


async def get_consent_manager() -> MemoryConsentManager:
    """Get the global consent manager instance"""
    global _consent_manager
    if _consent_manager is None:
        _consent_manager = MemoryConsentManager()
    return _consent_manager


async def reset_consent_manager() -> None:
    """Reset the global consent manager (useful for testing)"""
    global _consent_manager
    _consent_manager = None
