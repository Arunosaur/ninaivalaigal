"""
SPEC-049: Memory Sharing Contracts
Memory link contracts between user/org/agent scopes with consent and visibility management
"""

import asyncio
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class ScopeType(Enum):
    """Memory scope types for sharing contracts"""

    USER = "user"
    TEAM = "team"
    ORGANIZATION = "organization"
    AGENT = "agent"
    PUBLIC = "public"


class SharePermission(Enum):
    """Sharing permissions for memory contracts"""

    VIEW = "view"  # Read-only access
    COMMENT = "comment"  # View + add comments
    EDIT = "edit"  # View + comment + modify
    SHARE = "share"  # View + comment + edit + reshare
    ADMIN = "admin"  # Full control including delete


class ContractStatus(Enum):
    """Contract lifecycle status"""

    PENDING = "pending"  # Awaiting acceptance
    ACTIVE = "active"  # Currently active
    EXPIRED = "expired"  # Time-based expiry
    REVOKED = "revoked"  # Manually revoked
    REJECTED = "rejected"  # Declined by recipient


class VisibilityLevel(Enum):
    """Memory visibility levels"""

    PRIVATE = "private"  # Only owner can see
    SHARED = "shared"  # Shared with specific entities
    TEAM = "team"  # Visible to team members
    ORG = "org"  # Visible to organization
    PUBLIC = "public"  # Publicly visible


@dataclass
class ScopeIdentifier:
    """Identifies a scope (user, team, org, agent)"""

    scope_type: ScopeType
    scope_id: str
    display_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryLinkContract:
    """Contract for sharing memory between scopes"""

    contract_id: str
    memory_id: str
    owner_scope: ScopeIdentifier
    target_scope: ScopeIdentifier
    permissions: Set[SharePermission]
    visibility_level: VisibilityLevel
    status: ContractStatus
    created_at: datetime
    created_by: int

    # Optional constraints
    expires_at: Optional[datetime] = None
    usage_limit: Optional[int] = None
    usage_count: int = 0

    # Consent tracking
    consent_required: bool = True
    consent_given_at: Optional[datetime] = None
    consent_given_by: Optional[int] = None

    # Audit trail
    last_accessed_at: Optional[datetime] = None
    last_accessed_by: Optional[int] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[int] = None
    revoked_reason: Optional[str] = None

    # Metadata
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShareRequest:
    """Request to share memory with another scope"""

    memory_id: str
    target_scope: ScopeIdentifier
    permissions: Set[SharePermission]
    visibility_level: VisibilityLevel
    expires_at: Optional[datetime] = None
    usage_limit: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    require_consent: bool = True


@dataclass
class ConsentRecord:
    """Record of consent for memory sharing"""

    contract_id: str
    consenting_user_id: int
    consenting_scope: ScopeIdentifier
    consent_given: bool
    consent_timestamp: datetime
    consent_method: str  # "explicit", "implicit", "delegated"
    consent_metadata: Dict[str, Any] = field(default_factory=dict)


class MemorySharingContractManager:
    """
    SPEC-049: Memory Sharing Contract Manager

    Manages memory link contracts between different scopes with consent tracking,
    visibility controls, and comprehensive audit trails.
    """

    def __init__(self):
        self.contracts: Dict[str, MemoryLinkContract] = {}
        self.consent_records: Dict[str, List[ConsentRecord]] = {}
        self.scope_memberships: Dict[str, Set[int]] = {}  # scope_id -> user_ids
        self.user_scopes: Dict[int, Set[ScopeIdentifier]] = {}  # user_id -> scopes

        # Contract templates for different sharing patterns
        self.contract_templates = self._initialize_contract_templates()

    async def create_sharing_contract(
        self,
        share_request: ShareRequest,
        owner_scope: ScopeIdentifier,
        creator_user_id: int,
    ) -> MemoryLinkContract:
        """Create a new memory sharing contract"""
        try:
            # Generate contract ID
            contract_id = f"contract_{secrets.token_urlsafe(16)}"

            # Validate sharing permissions
            await self._validate_sharing_permissions(
                owner_scope, share_request.target_scope, share_request.permissions
            )

            # Create contract
            contract = MemoryLinkContract(
                contract_id=contract_id,
                memory_id=share_request.memory_id,
                owner_scope=owner_scope,
                target_scope=share_request.target_scope,
                permissions=share_request.permissions,
                visibility_level=share_request.visibility_level,
                status=(
                    ContractStatus.PENDING
                    if share_request.require_consent
                    else ContractStatus.ACTIVE
                ),
                created_at=datetime.now(timezone.utc),
                created_by=creator_user_id,
                expires_at=share_request.expires_at,
                usage_limit=share_request.usage_limit,
                consent_required=share_request.require_consent,
                title=share_request.title,
                description=share_request.description,
            )

            # Store contract
            self.contracts[contract_id] = contract

            # If no consent required, activate immediately
            if not share_request.require_consent:
                contract.status = ContractStatus.ACTIVE
                contract.consent_given_at = datetime.now(timezone.utc)
                contract.consent_given_by = creator_user_id

            logger.info(
                f"Created sharing contract {contract_id} for memory {share_request.memory_id}"
            )
            return contract

        except Exception as e:
            logger.error(f"Failed to create sharing contract: {e}")
            raise

    async def grant_consent(
        self,
        contract_id: str,
        consenting_user_id: int,
        consent_method: str = "explicit",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Grant consent for a sharing contract"""
        try:
            contract = self.contracts.get(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            if contract.status != ContractStatus.PENDING:
                raise ValueError(f"Contract {contract_id} is not pending consent")

            # Verify user has authority to consent for target scope
            if not await self._can_user_consent_for_scope(
                consenting_user_id, contract.target_scope
            ):
                raise PermissionError("User cannot consent for target scope")

            # Record consent
            consent_record = ConsentRecord(
                contract_id=contract_id,
                consenting_user_id=consenting_user_id,
                consenting_scope=contract.target_scope,
                consent_given=True,
                consent_timestamp=datetime.now(timezone.utc),
                consent_method=consent_method,
                consent_metadata=metadata or {},
            )

            if contract_id not in self.consent_records:
                self.consent_records[contract_id] = []
            self.consent_records[contract_id].append(consent_record)

            # Activate contract
            contract.status = ContractStatus.ACTIVE
            contract.consent_given_at = datetime.now(timezone.utc)
            contract.consent_given_by = consenting_user_id

            logger.info(
                f"Consent granted for contract {contract_id} by user {consenting_user_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to grant consent for contract {contract_id}: {e}")
            raise

    async def revoke_contract(
        self, contract_id: str, revoking_user_id: int, reason: Optional[str] = None
    ) -> bool:
        """Revoke a sharing contract"""
        try:
            contract = self.contracts.get(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            # Verify user has authority to revoke
            if not await self._can_user_revoke_contract(revoking_user_id, contract):
                raise PermissionError("User cannot revoke this contract")

            # Revoke contract
            contract.status = ContractStatus.REVOKED
            contract.revoked_at = datetime.now(timezone.utc)
            contract.revoked_by = revoking_user_id
            contract.revoked_reason = reason

            logger.info(f"Contract {contract_id} revoked by user {revoking_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke contract {contract_id}: {e}")
            raise

    async def check_memory_access(
        self,
        memory_id: str,
        accessing_user_id: int,
        accessing_scope: ScopeIdentifier,
        required_permission: SharePermission,
    ) -> bool:
        """Check if user/scope has access to memory through contracts"""
        try:
            # Find active contracts for this memory
            active_contracts = [
                contract
                for contract in self.contracts.values()
                if (
                    contract.memory_id == memory_id
                    and contract.status == ContractStatus.ACTIVE
                    and self._is_contract_valid(contract)
                )
            ]

            for contract in active_contracts:
                # Check if accessing scope matches target scope
                if self._scope_matches(accessing_scope, contract.target_scope):
                    # Check if user is member of target scope
                    if await self._is_user_member_of_scope(
                        accessing_user_id, contract.target_scope
                    ):
                        # Check if contract grants required permission
                        if required_permission in contract.permissions:
                            # Update access tracking
                            contract.last_accessed_at = datetime.now(timezone.utc)
                            contract.last_accessed_by = accessing_user_id
                            contract.usage_count += 1

                            return True

            return False

        except Exception as e:
            logger.error(f"Failed to check memory access: {e}")
            return False

    async def list_contracts_for_memory(
        self, memory_id: str, requesting_user_id: int
    ) -> List[Dict[str, Any]]:
        """List all contracts for a specific memory"""
        try:
            contracts = []

            for contract in self.contracts.values():
                if contract.memory_id != memory_id:
                    continue

                # Check if user can view this contract
                if not await self._can_user_view_contract(requesting_user_id, contract):
                    continue

                contract_info = {
                    "contract_id": contract.contract_id,
                    "target_scope": {
                        "type": contract.target_scope.scope_type.value,
                        "id": contract.target_scope.scope_id,
                        "display_name": contract.target_scope.display_name,
                    },
                    "permissions": [p.value for p in contract.permissions],
                    "visibility_level": contract.visibility_level.value,
                    "status": contract.status.value,
                    "created_at": contract.created_at.isoformat(),
                    "expires_at": (
                        contract.expires_at.isoformat() if contract.expires_at else None
                    ),
                    "usage_count": contract.usage_count,
                    "usage_limit": contract.usage_limit,
                    "title": contract.title,
                    "description": contract.description,
                }

                contracts.append(contract_info)

            return contracts

        except Exception as e:
            logger.error(f"Failed to list contracts for memory {memory_id}: {e}")
            return []

    async def list_contracts_for_scope(
        self,
        scope: ScopeIdentifier,
        requesting_user_id: int,
        status_filter: Optional[ContractStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List all contracts where scope is owner or target"""
        try:
            contracts = []

            for contract in self.contracts.values():
                # Check if scope is involved in contract
                if not (
                    self._scope_matches(scope, contract.owner_scope)
                    or self._scope_matches(scope, contract.target_scope)
                ):
                    continue

                # Apply status filter
                if status_filter and contract.status != status_filter:
                    continue

                # Check if user can view this contract
                if not await self._can_user_view_contract(requesting_user_id, contract):
                    continue

                contract_info = {
                    "contract_id": contract.contract_id,
                    "memory_id": contract.memory_id,
                    "owner_scope": {
                        "type": contract.owner_scope.scope_type.value,
                        "id": contract.owner_scope.scope_id,
                        "display_name": contract.owner_scope.display_name,
                    },
                    "target_scope": {
                        "type": contract.target_scope.scope_type.value,
                        "id": contract.target_scope.scope_id,
                        "display_name": contract.target_scope.display_name,
                    },
                    "permissions": [p.value for p in contract.permissions],
                    "status": contract.status.value,
                    "created_at": contract.created_at.isoformat(),
                    "role": (
                        "owner"
                        if self._scope_matches(scope, contract.owner_scope)
                        else "target"
                    ),
                }

                contracts.append(contract_info)

            return contracts

        except Exception as e:
            logger.error(f"Failed to list contracts for scope: {e}")
            return []

    async def get_sharing_statistics(
        self, scope: ScopeIdentifier, requesting_user_id: int
    ) -> Dict[str, Any]:
        """Get sharing statistics for a scope"""
        try:
            # Verify user can access scope statistics
            if not await self._is_user_member_of_scope(requesting_user_id, scope):
                raise PermissionError("User cannot access scope statistics")

            stats = {
                "scope": {
                    "type": scope.scope_type.value,
                    "id": scope.scope_id,
                    "display_name": scope.display_name,
                },
                "contracts_as_owner": 0,
                "contracts_as_target": 0,
                "active_shares": 0,
                "pending_consents": 0,
                "total_usage": 0,
                "permissions_granted": {},
                "visibility_levels": {},
            }

            for contract in self.contracts.values():
                if self._scope_matches(scope, contract.owner_scope):
                    stats["contracts_as_owner"] += 1
                    if contract.status == ContractStatus.ACTIVE:
                        stats["active_shares"] += 1
                        stats["total_usage"] += contract.usage_count

                elif self._scope_matches(scope, contract.target_scope):
                    stats["contracts_as_target"] += 1
                    if contract.status == ContractStatus.PENDING:
                        stats["pending_consents"] += 1

                # Count permissions and visibility levels
                if contract.status == ContractStatus.ACTIVE:
                    for perm in contract.permissions:
                        stats["permissions_granted"][perm.value] = (
                            stats["permissions_granted"].get(perm.value, 0) + 1
                        )

                    vis_level = contract.visibility_level.value
                    stats["visibility_levels"][vis_level] = (
                        stats["visibility_levels"].get(vis_level, 0) + 1
                    )

            return stats

        except Exception as e:
            logger.error(f"Failed to get sharing statistics: {e}")
            return {}

    # Private helper methods
    async def _validate_sharing_permissions(
        self,
        owner_scope: ScopeIdentifier,
        target_scope: ScopeIdentifier,
        permissions: Set[SharePermission],
    ) -> None:
        """Validate that sharing permissions are allowed"""
        # Prevent sharing with self
        if self._scope_matches(owner_scope, target_scope):
            raise ValueError("Cannot share with self")

        # Validate permission hierarchy
        if SharePermission.ADMIN in permissions:
            # Admin permission requires special validation
            if owner_scope.scope_type != ScopeType.ORGANIZATION:
                raise ValueError("Only organizations can grant admin permissions")

    async def _can_user_consent_for_scope(
        self, user_id: int, scope: ScopeIdentifier
    ) -> bool:
        """Check if user can consent for a scope"""
        if scope.scope_type == ScopeType.USER:
            return scope.scope_id == str(user_id)

        # For team/org scopes, check membership
        return await self._is_user_member_of_scope(user_id, scope)

    async def _can_user_revoke_contract(
        self, user_id: int, contract: MemoryLinkContract
    ) -> bool:
        """Check if user can revoke a contract"""
        # Owner can always revoke
        if await self._is_user_member_of_scope(user_id, contract.owner_scope):
            return True

        # Target can revoke their own access
        if await self._is_user_member_of_scope(user_id, contract.target_scope):
            return True

        return False

    async def _can_user_view_contract(
        self, user_id: int, contract: MemoryLinkContract
    ) -> bool:
        """Check if user can view a contract"""
        # Members of owner or target scope can view
        return await self._is_user_member_of_scope(
            user_id, contract.owner_scope
        ) or await self._is_user_member_of_scope(user_id, contract.target_scope)

    async def _is_user_member_of_scope(
        self, user_id: int, scope: ScopeIdentifier
    ) -> bool:
        """Check if user is member of a scope"""
        if scope.scope_type == ScopeType.USER:
            return scope.scope_id == str(user_id)

        # Check scope memberships
        scope_key = f"{scope.scope_type.value}:{scope.scope_id}"
        members = self.scope_memberships.get(scope_key, set())
        return user_id in members

    def _scope_matches(self, scope1: ScopeIdentifier, scope2: ScopeIdentifier) -> bool:
        """Check if two scopes match"""
        return (
            scope1.scope_type == scope2.scope_type
            and scope1.scope_id == scope2.scope_id
        )

    def _is_contract_valid(self, contract: MemoryLinkContract) -> bool:
        """Check if contract is currently valid"""
        now = datetime.now(timezone.utc)

        # Check expiration
        if contract.expires_at and now > contract.expires_at:
            contract.status = ContractStatus.EXPIRED
            return False

        # Check usage limit
        if contract.usage_limit and contract.usage_count >= contract.usage_limit:
            return False

        return True

    def _initialize_contract_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize contract templates for common sharing patterns"""
        return {
            "team_collaboration": {
                "permissions": {
                    SharePermission.VIEW,
                    SharePermission.COMMENT,
                    SharePermission.EDIT,
                },
                "visibility_level": VisibilityLevel.TEAM,
                "consent_required": False,
                "expires_at": None,
            },
            "external_review": {
                "permissions": {SharePermission.VIEW, SharePermission.COMMENT},
                "visibility_level": VisibilityLevel.SHARED,
                "consent_required": True,
                "expires_at": lambda: datetime.now(timezone.utc) + timedelta(days=7),
            },
            "public_showcase": {
                "permissions": {SharePermission.VIEW},
                "visibility_level": VisibilityLevel.PUBLIC,
                "consent_required": False,
                "expires_at": None,
            },
        }


# Global contract manager instance
_contract_manager: Optional[MemorySharingContractManager] = None


async def get_contract_manager() -> MemorySharingContractManager:
    """Get the global contract manager instance"""
    global _contract_manager
    if _contract_manager is None:
        _contract_manager = MemorySharingContractManager()
    return _contract_manager


async def reset_contract_manager() -> None:
    """Reset the global contract manager (useful for testing)"""
    global _contract_manager
    _contract_manager = None
